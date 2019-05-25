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
from collections import deque
import time
from imagegui import GUIKatana

class Katana(object):

	def __init__(self, config, finder):
		self.results = {}
		self.config = {}
		self.parsers = []
		self.units = []
		self.threads = []
		self.threads_done = []
		self.completed = False
		self.results = { }
		self.results_lock = threading.RLock()
		self.total_work = 0
		self.all_units = []
		self.requested_units = []
		self.depth_lock = threading.Lock()
		self.target_hashes = []
		self.completed = False
		self.recurse_queue = deque()
		self.lost_queue = deque()
		self.result_queue = deque()
		self.artifact_queue = deque()
		self.image_queue = deque()
		self.flag_queue = deque()
		self.gui = None
		self.config = config
		self.finder = finder

		# Create the progress line for katana
		self.progress = log.progress('katana')

		# Notify the user if the requested units are overridden by recursion
		if self.config['auto'] and len(self.config['unit']) > 0 and not self.config['recurse']:
			log.warning('ignoring --unit options in favor of --auto')

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
		if self.config['target'] == '-':
			self.config['target'] = sys.stdin.read()

		# Compile the flag format if given
		if self.config['flag_format']:
			self.flag_pattern = re.compile(bytes('({0})'.format(self.config['flag_format']), 'utf-8'),
					flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
		else:
			self.flag_pattern = None

		# Setup the work queue
		if self.config['no_priority']:
			log.info('disabling prioritized work queue')
			self.work = queue.Queue(maxsize=500)
		else:
			self.work = queue.PriorityQueue(maxsize=500)

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

	@property
	def original_target(self):
		""" Shorthand for grabbing the target """
		if isinstance(self.config['target'], str):
			return None
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

			NOTE 2: The number appending only works if `create` is True. if it isn't,
				then no existence checks are performed. You should handle this on
				your own during creation...
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

			# We don't add directories to the artifact list by default...
			# CALEB: But should we? :?
			if not asdir:
				self.add_artifact(unit, path)
		
		# Return both the open file handle (if created) and the path
		return (path, file_handle)

	# Register an artifact with the results
	def add_artifact(self, unit, path):
		self.artifact_queue.append((unit, path))

	# Add some results to the result object
	def add_results(self, unit, d):
		# Clean the results
		d = self.clean_result(d)
		
		# Only add if the clean didn't demolish it
		if d is None or not d:
			return

		# Add it to the queue to be added lattteeerrrrr
		self.result_queue.append((unit, d))
	
	# Queue an image to be added to the final results
	def add_image(self, image):
		# Display the image if the user asked to
		if ( self.config['display_images'] ) and self.gui is not None:
			try:
				self.gui.insert(image)
			except RuntimeError:
				# The user must have closed the window.. that's fine!
				pass

		# Add the image to the queue
		self.image_queue.append(image)
	
	# Add a potential flag to the flag queue
	def add_flag(self, flag):

		# Technically a race condition, but will be handled by "set" below in build_results
		if self.flag_queue.count(flag) > 0:
			return

		# CALEB: This is a race condition... but it's not a big deal...
		# CALEB: Also, this is fucking disgusting...
		log.success((f'({round(time.time()-self.start,2)}s) potential flag found ' + 
			'(copied)'*(len(self.flag_queue) == 0) +': {0}').format('\u001b[32;1m' +
			flag + '\u001b[0m')
		)

		# Copy the flag to the clipboard, if it's the first flag
		if len(self.flag_queue) == 0:
			clipboard.copy(flag)

		# Add to list of found flags
		self.flag_queue.append(flag)

	def build_results(self):
		""" This should run after exiting the main loop. It will take the contents of the
			`flag_queue`, `image_queue`, `result_queue`, and `artifact_queue` then consolidate
			them into a nice dictionary suitable for output as JSON and formatting into the
			HTML output with Jinja2.
		"""

		# Build initial results structure
		self.results = {
			'flags': list(set(list(self.flag_queue))),
			'images': list(set(list(self.image_queue))),
			'children': {}
		}

		# Find images with duplicate hashes 
		image_hashes = []
		for i in range(len(self.results['images'])):
			h = md5()
			with open(self.results['images'][i], 'rb') as f:
				for chunk in iter(lambda: f.read(4096), b''):
					h.update(chunk)
				if h.hexdigest() in image_hashes:
					self.results['images'][i] = None
				else:
					image_hashes.append(h.hexdigest())

		# Remove bad items
		self.results['images'] = [ img for img in self.results['images'] if img is not None ]

		# Add unit reuslts
		for unit,d in self.result_queue:
			r = self.get_unit_result(unit)
			if d not in r['results']:
				r['results'].append(d)

		# Add unit artifacts
		for unit,path in self.artifact_queue:
			r = self.get_unit_result(unit)
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

			# Iterate through parents to find the correct
			# results item in the dictionary
			for p in parents:
				# Create the children entry if it doesn't exist
				if not 'children' in r:
					r['children'] = {
						p.unit_name: {
							'uuid': str(uuid.uuid4()),
							'results': []
						}
					}
				# Create this child if it doesn't exist
				elif p.unit_name not in r['children']:
					r['children'][p.unit_name] = {
						'uuid': str(uuid.uuid4()),
						'results': []
					}
				# We found it! We found the last parent!
				r = r['children'][p.unit_name]

			# Add the children if needed
			if 'children' not in r:
				r['children'] = {
					unit.unit_name: {
						'uuid': str(uuid.uuid4()),
						'results': [] 
					}
				}
			# Add this child if needed
			elif unit.unit_name not in r['children']:
				r['children'][unit.unit_name] = {
					'uuid': str(uuid.uuid4()),
					'results': []
				}

			# Create this child
			r = r['children'][unit.unit_name]

		# Return the result reference
		return r

	def clean_result(self, d):
		""" Remove results we don't want, and normalize the format. 

			This function will ensure that the string results are greater
			than `data_length` characters. Also, it ensures there are no bytes
			strings in the result (either decoding with utf-8 or using repr)
		"""

		if isinstance(d, str):
			# Only allow strings of at least `data_length` length.
			if len(d) < self.config['data_length']:
				return None
			return d
		elif isinstance(d, list) or isinstance(d, tuple):
			# Recurse through tuples and lists
			r = []
			for i in d:
				x = self.clean_result(i)
				if x is not None:
					r.append(x)
			# Ignore the tuple if it is empty after cleaning
			if len(r) == 0:
				r = None
		elif isinstance(d, dict):
			# Recurse through dictionaries
			r = {}
			for name in d:
				x = self.clean_result(d[name])
				if x is not None:
					r[name] = x
			# Ignore the dict if it is empty after cleaning
			if len(r) == 0:
				r = None
		elif isinstance(d, bytes):
			# Attempt to decode the bytes array
			try:
				r = d.decode('utf-8')
			except UnicodeError:
				# Fall back to `repr`, and remove the `b'{0}'` bullshit
				r = repr(d)[2:-1]
			# Ensure it is long enough
			if len(r) < self.config['data_length']:
				return None
		else:
			# For all other types, just use as-is.
			r = d
		return r

	def render(self):
		""" Render the results dictionary to a nice HTML view via Jinja2
			templating. The templates are stored in `./templates`, and 
			the specific template to use is specified via the `template`
			argument
		"""

		# Create a new Jinja2 environment from the templates.
		# Specify html/xml processing.
		env = jinja2.Environment(loader=jinja2.FileSystemLoader('./templates'),
				autoescape=jinja2.select_autoescape(['html', 'xml'])
			)

		# Expose a custom JSON pretty printing filter
		env.filters['pretty_json'] = utilities.jinja_pretty_json

		# Load the template specified in the configuration
		template = env.get_template(self.config['template']+'.html')

		# Ensure the CSS file is available in the output directory
		shutil.copyfile(
			os.path.join('./templates', self.config['template']+'.css'),
			os.path.join(self.config['outdir'], self.config['template']+'.css')
		)

		# Render the template with our results and initial target data
		stream = template.stream(
			results=self.results,
			target=self.original_target
		)

		# Dump the rendered view to the output directory
		stream.dump(os.path.join(self.config['outdir'], 'katana.html'))

	def evaluate(self):
		""" Start processing all units """
		self.start = time.time()

		# Evaluate the given target as a target object
		try:
			self.config['target'] = Target(self,self.config['target'])
		except utilities.FoundFlag:
			pass
		else:

			# Find units which match this target
			units, ignored = self.finder.find(self, self.config['target'], requested=self.config['unit'])

			# Notify user of requested units that weren't applicable/found
			if len(self.config['unit']) > 0:
				for cls,exc in ignored:
					log.warning('{0}: not applicable: {1}'.format(cls.name, exc.args))
			
			# Did we match any units
			if len(units) == 0:
				self.progress.failure('no applicable units found')
				return

			if not self.config['flag_format']:
				log.warn("no flag format was specified, advise looking at saved results")

			self.progress.status('starting threads')

			# Create all the threads
			for n in range(self.config['threads']):
				self.progress.status('starting thread {0}'.format(n))
				thread = threading.Thread(target=self.worker, args=(n,))
				thread.start()
				self.threads.append(thread)
				self.threads_done.append(False)

			status_done = threading.Event()
			status_thread = threading.Thread(target=self.progress_worker, args=(status_done,))
			status_thread.start()

			# Add the known units to the work queue
			try:
				self.add_to_work(self.units)
				self.work.join()
			except KeyboardInterrupt:
				self.completed = True
				log.failure("aborting early... ({} tasks not yet completed)".format(self.work.qsize()))
				# Build the results dictionary from the queues
				self.build_results()

				# Make sure we can create the results file
				results = json.dumps(self.results, indent=4, sort_keys=True)

				if results != "{}":
					with open(os.path.join(self.config['outdir'], 'katana.json'), 'w') as f:
						f.write(results)
					if self.config['show']:
						print(results)

					# Use the raw json to process out HTML
					self.render()

			status_done.set()
			status_thread.join()

			self.progress.status('all units complete. waiting for thread exit')

			# Wait for threads to exit
			try:
				# Notify threads of completion (highest priority!)
				for n in range(self.config['threads']):
					self.work.put(UnitWorkWrapper(-10000,'done',(None, None)))

				# Ask the threads to exit
				for t in self.threads:
					t.join()
			except KeyboardInterrupt:
				# Kill the threads forceably... this is not nice...
				for t in self.threads:
					try:
						utilities.async_raise(t.ident, SystemExit)
					except ValueError:
						# This thread didn't exit
						pass

			finish = time.time()
			self.progress.success(f'threads exited in {round(finish-self.start,1)}s. evaluation complete')

		# Build the results dictionary from the queues
		self.build_results()

		# Make sure we can create the results file
		results = json.dumps(self.results, indent=4, sort_keys=True)

		if results != "{}":
			with open(os.path.join(self.config['outdir'], 'katana.json'), 'w') as f:
				f.write(results)
			if self.config['show']:
				print(results)

			# Use the raw json to process out HTML
			self.render()
			
			# Close out the progress object
			log.success('wrote output to {0}, note minimum data length is {1}'.format(
				os.path.join(self.config['outdir'], 'katana.json and html'),
				self.config['data_length']
			))
		else:
			log.failure("no units returned results")

	def add_to_work(self, units):
		# Add all the cases to the work queue
		for unit in units:
			if self.completed:
				break
			for case in unit.enumerate(self):
				if self.completed or unit.completed:
					break
				self.work.put(UnitWorkWrapper(
					unit.PRIORITY,
					'unit',
					(unit, case)
				))
				self.total_work += 1
	
	def locate_flags(self, unit, output, stop=True, strict=False, rotate = True):
		""" Look for flags in the given data/output """

		if isinstance(output, list) or isinstance(output, tuple):
			count = 0
			for item in output:
				count += int(self.locate_flags(unit, item, stop, strict))
			return count > 0

		# If the user didn't supply a pattern, there's nothing to do.
		if self.flag_pattern == None:
			return False

		if isinstance(output, str):
			output = output.encode('utf-8')

		# CALEB: this is a hack to remove XML from flags, and check that as well
		no_xml = re.sub(b'<[^<]+>', b'', output)
		if no_xml != output:
			self.locate_flags(unit, no_xml, stop=stop)

		# JOHN: Check to see if the flag is found VERTICALLY...
		if rotate:
			# Set "rotate" to false so we don't do this forever...
			self.locate_flags(utilities.rotate_text(unit), rotate = False)

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
			if stop and unit is not None:
				unit.completed = True

			# Stop everything if we have requested that
			if not self.config['continue']:
				self.completed = True

			raise utilities.FoundFlag

			return True

		return False

	def recurse(self, parent, data, verify_length = True):
		# JOHN: If this `recurse` is set to True, it will recurse 
		#       WITH EVERYTHING even IF you specify a single unit.
		#       This is the intent, but should be left to "False" for testing
	
		if (data is None or data == "" ):
			return

		# Obey max depth input by user
		if len(parent.family_tree) >= self.config['recurse']:
			if self.depth_lock.acquire(blocking=False):
				log.warning('depth limit reached. if this is a recursive problem, consider increasing --depth')
			# Stop the chain of events
			parent.completed = True
			return

		try:
			if not os.path.isfile(data) and len(data) < self.config['data_length']:
				return
		except ValueError:
			pass

		# If the data is not a flag, go ahead and recurse on it!
		if not self.locate_flags(parent, data):

			# Build a target object for this data
			target = Target(self, data, parent=parent)

			# Locate matching units
			units, _ = self.finder.find(self, target)

			# Add them to the recurse queue
			for u in units:
				self.recurse_queue.append((u, None))	

	def progress_worker(self, done_event):
		""" This is the thread that monitors status, and prints a nice message """

		while not self.completed:
			if self.total_work > 0:
				left = self.work.qsize()
				done = self.total_work - left
				self.progress.status('{0:.2f}% work queue utilization; {1} total items queued'.format((float(self.work.qsize())/float(self.config['threads']*4))*100, self.total_work, done))
			time.sleep(1.0)
	
	def unit_worker(self, progress, unit, case):

		# Check if this unit is done
		if unit.completed:
			return False
		
		# Show progress if debug
		progress.status('{0} -> {1}... ({2})'.format(
			'\u001b[33;1m' + unit.unit_name + '\u001b[0m',
			'\u001b[34;1m' + unit.target[:60].replace('\n','') + '\u001b[0m',
			unit.PRIORITY))
		
		try:
			# Evaluate the target
			result = unit.evaluate(self, case)
		except utilities.FoundFlag:
			pass
		except:
			traceback.print_exc()

	def worker(self, thread_number):
		""" Katana worker thread to process unit execution """

		# Create progress montiro
		with log.progress('thread {0}'.format(thread_number)) as progress:
			while True:
				
				# Grab the next work item from the queue
				work = self.work.get()

				# Exit cleanly when the parent asks us to
				if work.action == 'done':
					self.work.task_done()
					break

				# Process the request if we are still running
				if not self.completed:
					if work.action == 'unit':
						self.unit_worker(progress, *work.item)
					else:
						log.warning('bad work action: {0}'.format(work.action))

				# Try to grab the orphaned unit case combos
				full = False
				try:
					for unit,case in iter(lambda: self.lost_queue.popleft(), None):
						try:
							self.work.put(UnitWorkWrapper(
								unit.PRIORITY, 'unit', (unit, case)
							), block=False)
							self.total_work += 1
						except queue.Full:
							self.lost_queue.appendleft((unit, case))
							full = True
				except IndexError:
					pass
				
				# We won't try if we just saw it as full (could technically be room, but
				# not worth it IMHO)
				if not full:
					# Try to grab the recursed items if there is space available
					try:
						for unit,gen in iter(lambda: self.recurse_queue.popleft(), None):
							if gen is None:
								gen = unit.enumerate(self)
							for case in gen:
								try:
									self.work.put(UnitWorkWrapper(
										unit.PRIORITY, 'unit', (unit, case)
									), block=False)
									self.total_work += 1
								except queue.Full:
									self.lost_queue.append((unit, case))
									self.recurse_queue.appendleft((unit, gen))
									gen = None
									break
							if gen is None:
								break
					except IndexError:
						pass

				# Notify parent we are done
				self.work.task_done()

# Make sure we find the local packages (first current directory)
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.getcwd())

if __name__ == '__main__':

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
	parser.add_argument('--dict', type=argparse.FileType('rb'),
			required=False, default=None, help='dictionary for brute forcing tasks')
	parser.add_argument('--data-length', '-l', default=10, type=int,
		help="minimum number of characters for units results to be displayed")
	parser.add_argument('--show', '-s', default=False, action="store_true",
		help="print the results on stdout as well as save to file")
	parser.add_argument('--download', '-d', action="store_true", default=False,
			help='consider the argument to be a download link and pull it down')
	parser.add_argument('--no-download', '-nd', action="store_true", default=False,
			help='do not download URLs, just treat them as locations')
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
	parser.add_argument('--no-priority', '-np', action="store_true", default=False,
			help='do not use the priority queue')

	# Parse the above arguments
	args, remaining = parser.parse_known_args()

	# Initialize our unit finder
	finder = units.UnitFinder(args.unitdir, args.exclude)

	# Add all unit arguments to our parser
	finder.construct_parser(parser)

	# Parse remaining arguments
	args = parser.parse_args()

	# Convert args namespace to a dictionary
	config = vars(args)

	# Create the Katana
	katana = Katana(config, finder)

	if katana.config['display_images']:
		# Create a Tkinter window to show images
		gui_katana = GUIKatana(katana)
		gui_katana.evaluate()
	else:
		# Run katana against all units
		katana.evaluate()
