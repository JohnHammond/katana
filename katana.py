#!/usr/bin/env python3
from pwn import *
import argparse
import json
import sys
import importlib
import queue
import threading
import time
import traceback
import os
import utilities
from utilities import ArgumentParserWithHelp, find_modules_recursively
import pkgutil
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import tempfile
import re
import binascii
import base64
import subprocess
import units
from units import UnitWorkWrapper
import clipboard
import jinja2
import shutil
import uuid
from PIL import Image
from hashlib import md5
import signal
from target import Target
from unit import BaseUnit

class Katana(object):

	def __init__(self):
		self.results = {}
		self.config = {}
		self.parsers = []
		self.units = []
		self.threads = []
		self.completed = False
		self.results = { }
		self.results_lock = threading.RLock()
		self.total_work = 0
		self.all_units = []
		self.requested_units = []
		self.depth_lock = threading.Lock()
		self.target_hashes = []
		self.completed = False

		# Initial parser is for unit directory. We need to process this argument first,
		# so that the specified unit may be loaded
		parser = ArgumentParserWithHelp(
			description='Low-hanging fruit checker for CTF problems',
			add_help=True,
			allow_abbrev=True)
		parser.add_argument('--unitdir', type=utilities.DirectoryArgument,
			default='./units', help='the directory where available units are stored')
		parser.add_argument('--unit', action='append',
			required=False, default = [], help='the units to run on the targets')
		parser.add_argument('--unit-help', action='store_true',
			default=False, help='display help on unit selection')
		# The number of threads to use
		parser.add_argument('--threads', '-t', type=int, default=len(os.sched_getaffinity(0)),
			help='number of threads to use')
		# The list of targets to scan
		parser.add_argument('target', type=str,
			help='the target file/url/IP/etc') 
		# The output directory for this scan
		parser.add_argument('--outdir', '-o', default='./results',
			help='directory to house results')
		# A Regular Expression patter for units to match
		parser.add_argument('--flag-format', '-ff', default=None,
			help='regex pattern for output (e.g. "FLAG{.*}")')
		parser.add_argument('--auto', '-a', default=False,
			action='store_true', help='automatically search for matching units in unitdir')
		parser.add_argument('--recurse', '-r', type=int, default=5,
				help='the maximum depth which the units may recurse')
		parser.add_argument('--exclude', action='append',
			required=False, default = [], help='units to exclude in a recursive case')
		parser.add_argument('--verbose', '-v', action='store_true',
			default=False, help='show the running threads')
		parser.add_argument('--dict', type=argparse.FileType('r'),
				required=False, default=None, help='dictionary for brute forcing tasks')
		parser.add_argument('--data-length', '-l', default=10, type=int,
			help="minimum number of characters for units results to be displayed")
		parser.add_argument('--show', '-s', default=False, action="store_true",
			help="print the results on stdout as well as save to file")
		parser.add_argument('--download', '-d', action="store_true", default=False,
				help='consider the argument to be a download link and pull it down')
		parser.add_argument('--template', default='default',
				help='Jinja2 template for html results output')
		parser.add_argument('--functions', default='win,get_flag,print_flag,show_flag,flag',
				help='comma separated list of function name that may print a flag')
		parser.add_argument('--timeout', default=0.1, type=float, 
				help='suggested timeout for long running unit tests')
		parser.add_argument('--exec', '-e', default=False,
				action='store_true', help='run units which may execute arbitrary code')
		parser.add_argument('--input', default='%s',
				help='a format string used to create payloads for pwn challenges')
		parser.add_argument('--display-images', '-i', action="store_true", default=False,
				help='display images as katana finds them')
		parser.add_argument('--continue', '-c', action="store_true", default=False,
				help='continue after finding a flag')
		parser.add_argument('--password', '-p', action='append', default=[],
				help='specify a possible password for units that may need it')

		args, remaining = parser.parse_known_args()

		# Add current arguments to the config
		self.config.update(vars(args))

		# Create the progress line for katana
		self.progress = log.progress('katana')

		# Add the units directory the system path
		sys.path.insert(0, self.config['unitdir'])

		# CALEB: This is a hacky way to keep track of unit findings...
		units_found = [False]*len(self.config['unit'])

		# Load all units under the unit directory
		for importer, name, ispkg in pkgutil.walk_packages([self.config['unitdir']], ''):

			# Exclude packages/units that were excluded from loading
			try:
				for exclude in self.config['exclude']:
					if name == exclude or name.startswith(exclude.rstrip('.') + '.'):
						raise Exception
			except:
				continue

			self.progress.status('loading unit {0}'.format(name))
		
			# Attempt to load the module
			try:
				module = importlib.import_module(name)
			except:
				self.progress.failure('{0}: failed to load module'.format(name))
				traceback.print_exc()
				exit()

			# Check if this module requires dependencies
			try:
				dependencies = module.DEPENDENCIES
				assert isinstance(dependencies, list), "Dependencies must be given as a list!" 
			except AttributeError:
				dependencies = []

			# Ensure the dependencies exist
			try:
				for dependency in dependencies:
					subprocess.check_output(['which',dependency])
			except (FileNotFoundError, subprocess.CalledProcessError):
				log.failure('{0}: dependancy not satisfied: {1}'.format(
					name, dependency
				))
				continue
			else:
				# Dependencies are good, ensure the unit class exists
				try:
					unit_class = module.Unit
				except AttributeError:
					continue

			# Add any arguments we need
			unit_class.add_arguments(self, parser)

			# Check if this was a requested unit
			for i in range(len(self.config['unit'])):
				if isinstance(self.config['unit'][i],str) and \
					( name == self.config['unit'][i] or  name.startswith(self.config['unit'][i].rstrip('.') + '.') ):
					units_found[i] = True
					self.requested_units.append(unit_class)
	
			# Keep total list for blind recursion
			self.all_units.append(unit_class)

		# Notify user of failed unit loads
		for i in range(len(self.config['unit'])):
			if not units_found[i]:
				log.failure('{0}: unit not found'.format(self.config['unit'][i]))

		# Ensure we have something to do
		if len(self.config['unit']) != sum(units_found) and not self.config['auto']:
			self.progress.failure('no units loaded. aborting.')
			exit()

		# Notify the user if the requested units are overridden by recursion
		if self.config['auto'] and len(self.requested_units) > 0 and not recurse:
			log.warning('ignoring --unit options in favor of --auto')

		# Final argument parsing. This includes all unit arguments
		args = parser.parse_args()
		self.config.update(vars(args))

		# Download the target, if that is specified
		if self.config['download']:
			try:
				temp_filename = self.config['target'].rsplit('/', 1)[1]
				temp_folder = tempfile.gettempdir()
				temp_path = os.path.join(temp_folder, temp_filename)
	
				self.progress.status(f'downloading and setting target to {temp_path}...')
			except IndexError:
				temp_path = self.config['target']


			try:
				r = requests.get(self.config['target'], verify = False)
				with open(temp_path, 'wb') as f:
					f.write(r.content)
			except requests.exceptions.MissingSchema:
				pass
			except:
				traceback.print_exc()

			self.config['target'] = temp_path

		# We want the "-" target to signify stdin
		if len(self.original_target) == 1 and self.original_target[0] == '-':
			self.config['target'] = sys.stdin.read()

		# Compile the flag format if given
		if self.config['flag_format']:
			self.flag_pattern = re.compile(bytes('({0})'.format(self.config['flag_format']), 'utf-8'),
					flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
		else:
			self.flag_pattern = None

		# Setup the work queue
		self.work = queue.Queue() #queue.PriorityQueue(maxsize=self.config['threads']*4)

		# Don't run if the output directory exists
		if os.path.exists(self.config['outdir']):
			self.progress.failure('{0}: directory exists'.format(self.config['outdir']))
			exit()
		elif not os.path.exists(self.config['outdir']):
			# Create the directory if needed
			try:
				os.mkdir(self.config['outdir'])
			except:
				self.progress.failure('{0}: unable to create directory'.format(self.config['outdir']))
				exit()

		self.progress.status('initialization complete')

		# Evaluate the given target as a target object
		self.config['target'] = Target(self,self.config['target'])

		# Find units which match this target
		self.units = self.locate_units(self.config['target'])

	@property
	def original_target(self):
		""" Shorthand for grabbing the target """
		return self.config['target']

	def get_artifact_path(self, unit):
		if unit is None:
			return self.config['outdir']

		# Compute the correct directory for this unit based on the parent tree
		path = os.path.join(self.config['outdir'], *[u.unit_name for u in unit.family_tree], unit.unit_name)

		# Ensure it is a directory if it already exists
		if os.path.exists(path) and not os.path.isdir(path):
			log.error('{0}: name overlap between unit and result!'.format(path))

		# Ensure the entire path chain exists
		os.makedirs(path, exist_ok=True)

		return path

	def create_artifact(self, unit, name, mode='w', create=True, asdir=False):
		""" Create a new artifact for the given unit. The artifact will be
			tracked in the results, so the unit doesn't need to dump that out.

			NOTE: The created artifact may have a different name than provided. 
				If the requested name already exists, the name will have a number
				appended between the name and the extension. The actual path created
				is returned along with the open file reference for created files.
		"""

		# Add the name of the artifact
		path = os.path.join(self.get_artifact_path(unit), name)

		# Create the file if needed
		file_handle = None
		if create:
			n = 0
			name, ext = os.path.splitext(path)
			# This will create a different file than requested, if needed by appending a 
			# "-#" to the filename _BEFORE THE EXTENSION_. The returned path will be
			# correct
			while True:
				if asdir:
					os.makedirs(path, exist_ok = True)
					break
				else:
					if ( not os.path.exists(path) ):
						file_handle = open(path, mode)
						break
					else:
						n += 1
						path = '{0}-{1}{2}'.format(name, n, ext)
				# try:
				# 	if asdir:
				# 		os.mkdir(path)
				# 	else:
				# 		file_handle = open(path, mode)
				# except OSError:
				# 	n += 1
				# 	path = '{0}-{1}{2}'.format(name, n, ext)
				# else:
				# 	break

			if not asdir:
				self.add_artifact(unit, path)
		
		return (path, file_handle)

	def add_artifact(self, unit, path):
		# Add the artifact to the results for tracking
		r = self.get_unit_result(unit)
		with self.results_lock:
			if 'artifacts' not in r:
				r['artifacts'] = []
			r['artifacts'].append(path)
		
	def get_unit_result(self, unit):
		if unit is None:
			return self.results

		parents = unit.family_tree
		with self.results_lock:
			# Start at the global results
			r = self.results
			for p in parents:
				if not 'children' in r:
					r['children'] = { p.unit_name: { 'uuid': str(uuid.uuid4()), 'results': [] } }
				elif p.unit_name not in r['children']:
					r['children'][p.unit_name] = { 'uuid': str(uuid.uuid4()), 'results': [] }
				r = r['children'][p.unit_name]
			if 'children' not in r:
				r['children'] = { unit.unit_name: { 'uuid': str(uuid.uuid4()), 'results': [] } }
			elif unit.unit_name not in r['children']:
				r['children'][unit.unit_name] = {'uuid': str(uuid.uuid4()), 'results': []}
			r = r['children'][unit.unit_name]

		return r

	def clean_result(self, d):
		if isinstance(d, str):
			if len(d) < self.config['data_length']:
				return None
			return d
		elif isinstance(d, list) or isinstance(d, tuple):
			r = []
			for i in d:
				x = self.clean_result(i)
				if x is not None:
					r.append(x)
			if len(r) == 0:
				r = None
		elif isinstance(d, dict):
			r = {}
			for name in d:
				x = self.clean_result(d[name])
				if x is not None:
					r[name] = x
			if len(r) == 0:
				r = None
		elif isinstance(d, bytes):
			try:
				r = d.decode('utf-8')
			except UnicodeError:
				r = repr(d)
			if len(r) < self.config['data_length']:
				return None
		else:
			r = d
		return r

	def add_results(self, unit, d):
		""" Update the results dict with the given dict """

		# Strip out results which don't meet the threshold
		d = self.clean_result(d)
		if d is None or not(d):
			return

		r = self.get_unit_result(unit)
		if d not in r['results']:
			r['results'].append(d)

		return

		parents = unit.family_tree
		with self.results_lock:
			# Start at the global results
			r = self.results
			# Recurse through parent units
			for p in parents:
				# If we have not seen results from this parent,
				# THAT'S FINE.... just be ready for it
				if not p.unit_name in r:
					r[p.unit_name] = { 'results': [] }	
			if unit.unit_name not in r:
				r[unit.unit_name] = { 'results': [] }

			if d != {} and d not in r[unit.unit_name]['results']:
				r[unit.unit_name]['results'].append(d)

	def render(self):
		""" Normalize and render results using the specified jinja2 template """
		env = jinja2.Environment(loader=jinja2.FileSystemLoader('./templates'),
				autoescape=jinja2.select_autoescape(['html', 'xml'])
			)
		env.filters['pretty_json'] = utilities.jinja_pretty_json
		template = env.get_template(self.config['template']+'.html')
		shutil.copyfile(os.path.join('./templates', self.config['template']+'.css'), os.path.join(self.config['outdir'], self.config['template']+'.css'))
		template.stream(results=self.results, target=self.original_target).dump(os.path.join(self.config['outdir'], 'katana.html'))

	def evaluate(self):
		""" Start processing all units """

		def show_status(signal_number, frame):
			log.info("working \u001b[33;01m{0}\u001b[0m->\u001b[34;01m{1}\u001b[0m".format(*self.threads[0].getName().split('->')))

		signal.signal(signal.SIGTSTP, show_status)

		if not self.config['flag_format']:
			log.warn("no flag format was specified, advise looking at saved results")

		self.progress.status('starting threads')

		# Create all the threads
		for n in range(self.config['threads']):
			self.progress.status('starting thread {0}'.format(n))
			thread = threading.Thread(target=self.worker)
			thread.start()
			self.threads.append(thread)

		status_done = threading.Event()
		status_thread = threading.Thread(target=self.progress_worker, args=(status_done,))
		status_thread.start()

		# Add the known units to the work queue
		try:
			self.add_to_work(self.units)
			self.work.join()
		except KeyboardInterrupt:
			self.work.join()
			log.failure("aborting early... ({} units not yet run)".format(self.recurse_queue.qsize()))

		status_done.set()
		status_thread.join()

		self.progress.status('all units complete. waiting for thread exit')

		# GO AWAY
		while not self.work.empty():
			self.work.get()

		# Notify threads of completion
		for n in range(self.config['threads']):
			self.work.put(UnitWorkWrapper(-10000,(None, None, None)))

		# Wait for threads to exit
		for t in self.threads:
			t.join()

		self.progress.success('threads exited. evaluation complete')

		# Make sure we can create the results file
		results = json.dumps(self.results, indent=4, sort_keys=True)

		if results != "{}":
			with open(os.path.join(self.config['outdir'], 'katana.json'), 'w') as f:
				f.write(results)
			if self.config['show']:
				print(results)

			# Use the raw json to process out HTML
			self.render()
			
			# JOHN: Maybe this defeats the purpose of --show, but I like it anyway...
			log.success('wrote output to {0}, note minimum data length is {1}'.format(os.path.join(self.config['outdir'], 'katana.json and html'), self.config['data_length']))
		else:
			log.failure("no units returned results")

	def add_to_work(self, units):
		# Add all the cases to the work queue
		for unit in units:
			if self.completed:
				break
			self.work.put(UnitWorkWrapper(
				unit.PRIORITY,
				(unit, None, None)
			))
			self.total_work += 1

	def add_flag(self, flag):

		with self.results_lock:
			if 'flags' not in self.results:
				self.results['flags'] = []

			if flag not in self.results['flags']:
				log.success(str('potential flag found '+ '(copied)' *bool(not len(self.results['flags']))+': {0}').format('\u001b[32;1m' + flag + '\u001b[0m') )

				if len(self.results['flags']) == 0:
					clipboard.copy(flag)
				self.results['flags'].append(flag)

	# JOHN: I originally did not have the unit included.
	def add_image(self, image):

		with self.results_lock:
			if 'images' not in self.results:
				self.results['images'] = {}

			if image not in self.results['images'].keys():

				image_hash = md5(open(image,'rb').read()).hexdigest()
				if image_hash not in self.results['images'].values():
					if self.config['display_images']:
						Image.open(image).show()
					self.results['images'][image] = image_hash


	
	def locate_flags(self, unit, output, stop=True, strict=False):
		""" Look for flags in the given data/output """

		# If the user didn't supply a pattern, there's nothing to do.
		if self.flag_pattern == None:
			return False

		if isinstance(output, str):
			output = output.encode('utf-8')

		# CALEB: this is a hack to remove XML from flags, and check that as well
		no_xml = re.sub(b'<[^<]+>', b'', output)
		if no_xml != output:
			self.locate_flags(unit, no_xml, stop=stop)

		match = self.flag_pattern.search(output)
		if match:

			# JOHN: This test is here because we had an issue with esoteric languages.
			#       We MORE THAN LIKELY will not have a flag without printable chars...
			found = match.group().decode('utf-8')
			if found.isprintable():

				# JOHN:
				if strict:
					if len(found) == len(output):
						self.add_flag(found)
				else:
					self.add_flag(found)
			
			# Stop the unit if they asked
			if stop:
				unit.completed = True

			# Stop everything if we have requested that
			if not self.config['continue']:
				self.completed = True

			return True

		return False

	def recurse(self, unit, data, verify_length = True):
		# JOHN: If this `recurse` is set to True, it will recurse 
		#       WITH EVERYTHING even IF you specify a single unit.
		#       This is the intent, but should be left to "False" for testing
	
		if (data is None or data == "" ):
			return

		# Obey max depth input by user
		if len(unit.family_tree) >= self.config['recurse']:
			if self.depth_lock.acquire(blocking=False):
				log.warning('depth limit reached. if this is a recursive problem, consider increasing --depth')
			# Stop the chain of events
			unit.completed = True
			return

		try:
			if os.path.isfile(data):
				verify_length = False
		except ValueError:
			pass

		if verify_length and len(data) < self.config['data_length']:
			return
	
		# If the data is not a flag, go ahead and recurse on it!
		if not self.locate_flags(unit, data):
			self.work.put(UnitWorkWrapper(
				100, (data, unit, None)
			))


	def locate_units(self, target, parent=None, recurse=False):

		units_so_far = []
		
		if target.hash.hexdigest() in self.target_hashes:
			return units_so_far
		else:
			self.target_hashes.append(target.hash.hexdigest())

		if not self.config['auto'] and not recurse:
			just_added = False
			for unit_class in self.requested_units:
				try:
					# Run this if we HAVE NOT seen it before...
					unit = unit_class(self, parent, target)
					units_so_far.append(unit)
				except units.NotApplicable as error:
					log.failure('{0}: target not applicable {1}'.format(
						unit_class.__module__,
						'({0})'.format(error.args[0]) if error.args else ''
					))
		else:
			for unit_class in self.all_units:
				try:
					# Climb the family tree to see if THE MOST RECENT ancester 
					# is not allowed to recurse.. don't bother with this unit
					if unit_class.PROTECTED_RECURSE and parent is not None:
						if parent.PROTECTED_RECURSE:
							raise units.NotApplicable()
#						for p in ([ parent ] + parent.family_tree):
#							if p.PROTECTED_RECURSE:
#								raise units.NotApplicable

					# Run this if we HAVE NOT seen it before...
					unit = unit_class(self, parent, target)
					units_so_far.append(unit)
				except units.NotApplicable:
					pass

		return units_so_far

	def progress_worker(self, done_event):
		while not done_event.is_set():
			if self.total_work > 0:
				left = self.work.qsize()
				done = self.total_work - left
				self.progress.status('{0:.2f}% work queue utilization; {1} total items queued'.format((float(self.work.qsize())/float(self.config['threads']*4))*100, self.total_work, done))
			time.sleep(0.5)

	def worker(self):
		""" Katana worker thread to process unit execution """
		
		if self.config['verbose']:
			progress = log.progress('thread-{0} '.format(threading.get_ident()))
		else:
			progress = None

		while True:
			# Grab the next item
			work = self.work.get()
			unit,name,generator = work.item # extract the data from the priority wrapper

			# This means we are done. It's a signal from the 
			# main thread to exit.
			if unit is None and name is None and generator is None:
				break

			# if this isn't a unit object, it must be a target
			if not isinstance(unit, BaseUnit):
				# extract data and parent information
				data = unit
				parent = name
				# Build target object
				target = Target(self, data, parent=parent)
				# Enumerate valid units
				units = self.locate_units(target, parent=parent, recurse=True)
				# Add units to work queue
				self.add_to_work(units)
				# Keep track of images if we see them as a target.
				if target.is_image and target.path is not None: 
					self.add_image(os.path.abspath(target.path.decode('utf-8')))
				# Signal task completion
				self.work.task_done()
				continue

			# Check if this unit (or katana) is already completed (by another thread)
			if self.completed or unit.completed:
				self.work.task_done()
				continue
			
			# Create the generator if needed
			if generator is None:
				generator = unit.enumerate(self)

			# Grab the next unit case
			try:
				case = next(generator)
			except StopIteration:
				self.work.task_done()
				continue

			# There are still cases left in this unit
			work.item = (unit, name, generator)
			self.work.put(work)

			# Set the thread description base on target representation
			target_repr = repr(unit.target)
			threading.current_thread().setName('{0} -> {1}...'.format(
				unit.unit_name,
				target_repr[:62]+'...' if len(target_repr) > 65 else target_repr
			))	

			#for case in generator:
			if self.completed or unit.completed:
				break
			# Perform the evaluation
			if progress is not None:
				progress.status('entering {0}'.format(unit.unit_name))
			try:
				result = unit.evaluate(self, case)
			except:
				traceback.print_exc()
			if progress is not None:
				progress.status('exiting {0}'.format(unit.unit_name))

			# Notify boss that we are done
			self.work.task_done()

		if progress is not None:
			progress.success('complete. exiting')


# Make sure we find the local packages (first current directory)
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.getcwd())

if __name__ == '__main__':

	# Create the katana
	katana = Katana()

	# Run katana against all units
	
	katana.evaluate()
