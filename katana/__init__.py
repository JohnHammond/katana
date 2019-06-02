#!/usr/bin/env python3
# from pwn import *
import pwnlib.log
import argparse
import json
import sys
import importlib
import queue
import threading
import time
import traceback
import os
import pkgutil
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import tempfile
import re
import binascii
import base64
import subprocess
import clipboard
import jinja2
import shutil
import uuid
from PIL import Image
from hashlib import md5
import signal
from collections import deque
import time
import signal
import warnings
warnings.simplefilter("ignore")

from katana import units
from katana.units import UnitWorkWrapper
from katana.target import Target
from katana.imagegui import GUIKatana
from katana import hook
from katana import utilities
from katana.utilities import ArgumentParserWithHelp
from katana.unit import BaseUnit

log = pwnlib.log.getLogger(__name__)

class Katana(object):

	def __init__(self, config, finder, hook):
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
		self.gui = None
		self.config = config
		self.finder = finder
		self.hook = hook
		self._completed = False

		# Set the katana reference in our hook object
		self.hook.katana = self

		# Notify the user if the requested units are overridden by recursion
		if self.config['auto'] and len(self.config['unit']) > 0 and not self.config['recurse']:
			self.hook.warning('ignoring --unit options in favor of --auto')

		# Download the target, if that is specified
		if self.config['download']:
			try:
				temp_filename = self.config['target'].rsplit('/', 1)[1]
				temp_folder = tempfile.gettempdir()
				temp_path = os.path.join(temp_folder, temp_filename)
	
				self.hook.status(f'downloading and setting target to {temp_path}...')
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
			# If they don't make the last character optional, do it for them...
			if self.config['flag_format'].endswith('}'):
				self.config['flag_format'] += '?'
				
			self.flag_pattern = re.compile(bytes('({0}|flag ?is:?.*|flag:?.*)'.format(self.config['flag_format']), 'utf-8'),
				flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
		else:
			self.flag_pattern = re.compile(bytes('(flag ?is:?.*|flag:?.*)', 'utf-8'),
				flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)

		# Setup the work queue
		if self.config['no_priority']:
			self.hook.status('disabling prioritized work queue')
			self.work = queue.Queue(maxsize=500)
		else:
			self.work = queue.PriorityQueue(maxsize=500)

		# Don't run if the output directory exists
		if os.path.exists(self.config['outdir']):
			self.hook.failure('{0}: directory exists'.format(self.config['outdir']))
			raise RuntimeError('output directory exists')
		elif not os.path.exists(self.config['outdir']):
			# Create the directory if needed
			try:
				# Make parent directories if they do not exist.
				os.makedirs(self.config['outdir'], exist_ok=True)
			except:
				self.hook.failure('{0}: unable to create directory'.format(self.config['outdir']))
				raise RuntimeError('unable to create output directory')

		if self.config['dict'] is not None and isinstance(self.config['dict'], str):
			try:
				self.config['dict'] = open(self.config['dict'], 'rb')
			except OSError:
				self.hook.failure('{0}: dictionary does not exist'.format(
					self.config['dict']
				))
				raise RuntimeError('dictionary does not exist')

		self.hook.status('initialization complete')

	@property
	def completed(self):
		return self._completed

	@completed.setter
	def completed(self, v):
		if not v:
			return
		self._completed = True

		# CALEB: This a gross __hack__. There's no way to clear the queue in the python standard library
		with self.work.all_tasks_done:
			self.work.queue.clear()
			self.work.unfinished_tasks = 0
			self.work.all_tasks_done.notify_all()
		with self.work.not_full:
			self.work.not_full.notify_all()

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
			self.failure('{0}: name overlap between unit and result!'.format(path))
			sys.exit(1)

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
			self.hook.artifact(unit, path, asdir)
		
		# Return both the open file handle (if created) and the path
		return (path, file_handle)

	def add_artifact(self, unit, path):
		self.hook.artifact(unit, path, False)

	# Add some results to the result object
	def add_results(self, unit, d):
		self.hook.result(unit, d)
	
	# Queue an image to be added to the final results
	def add_image(self, image):
		self.hook.image(image)
		return
	
	# Add a potential flag to the flag queue
	def add_flag(self, flag):
		self.hook.flag(flag)
		return

	def evaluate(self):
		""" Start processing all units """
		self.start = time.time()

		# Evaluate the given target as a target object
		try:
			self.config['target'] = Target(self,self.config['target'])
		except utilities.FoundFlag:
			pass
		else:

			self.hook.begin()

			# Find units which match this target
			units, ignored = self.finder.find(self, self.config['target'], requested=self.config['unit'])

			# Notify user of requested units that weren't applicable/found
			if len(self.config['unit']) > 0:
				for cls,exc in ignored:
					self.hook.warning('{0}: not applicable: {1}'.format(cls.__module__, exc.args))
			
			# Did we match any units
			if len(units) == 0:
				self.hook.failure('no applicable units found')
				return

			if not self.config['flag_format']:
				self.hook.warning("no flag format was specified, advise looking at saved results")

			self.hook.status('starting threads')

			# Create all the threads
			for n in range(self.config['threads']):
				self.hook.status('starting thread {0}'.format(n))
				thread = threading.Thread(target=self.worker, args=(n,))
				thread.start()
				self.threads.append(thread)
				self.threads_done.append(False)

			status_done = threading.Event()
			status_thread = threading.Thread(target=self.progress_worker, args=(status_done,))
			status_thread.start()

			# Add the known units to the work queue
			try:
				self.add_to_work(units)
				self.work.join()
			except KeyboardInterrupt:
				self.completed = True
				self.hook.failure("aborting early... ({} tasks not yet completed)".format(self.work.qsize()))
			except utilities.FoundFlag:
				log.info('wat')

			status_done.set()
			status_thread.join()

			self.hook.status('all units complete. waiting for thread exit')

			# Wait for threads to exit
			try:
				# Notify threads of completion (highest priority!)
				for n in range(self.config['threads']+1):
					while True:
						try:
							self.work.put_nowait(UnitWorkWrapper(-10000,'done',(None, None)))
						except queue.Full:
							try:
								self.work.get_nowait()
							except queue.Empty:
								pass
						else:
							break

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
			self.hook.status(f'threads exited in {round(finish-self.start,1)}s. evaluation complete')

		self.hook.complete()

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
	
	def locate_flags(self, unit, output, stop=True, strict=False):
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

		match = self.flag_pattern.search(output)
		if match:

			# JOHN: This test is here because we had an issue with esoteric languages.
			#       We MORE THAN LIKELY will not have a flag without printable chars...
			found = match.group().decode('utf-8')
			# if found.isprintable():
			if utilities.isprintable(found):

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
				self.hook.warning('depth limit reached. if this is a recursive problem, consider increasing --depth')
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
				self.hook.status('{0:.2f}% work queue utilization; {1} total items queued'.format((float(self.work.qsize())/float(self.config['threads']*4))*100, self.total_work, done))
			time.sleep(1.0)
	
	def unit_worker(self, ident, unit, case):

		# Check if this unit is done
		if unit.completed:
			return False
		
		# Show progress if debug
		self.hook.work_status(ident, '{0} -> {1}... ({2})'.format(
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

		class WorkDone(Exception):
			pass
		class AllDone(Exception):
			pass

		while True:
			try:
				# Grab the next work item from the queue
				work = self.work.get()

				# Exit cleanly when the parent asks us to
				if work.action == 'done': 
					raise AllDone

				# Process the request if we are still running
				if not self.completed:
					if work.action == 'unit':
						self.unit_worker(thread_number, *work.item)
					else:
						self.hook.warning('bad work action: {0}'.format(work.action))

				if self.completed:
					raise WorkDone

				# Try to grab the orphaned unit case combos
				full = False
				try:
					for unit,case in iter(lambda: self.lost_queue.popleft(), None):
						if self.completed or unit.completed:
							raise WorkDone
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
							if self.completed or unit.completed:
								raise WorkDone
							if gen is None:
								gen = unit.enumerate(self)
							for case in gen:
								if self.completed or unit.completed:
									raise WorkDone
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
			except WorkDone:
				pass	
			except AllDone:
				break
			try:
				self.work.task_done()
			except ValueError:
				pass
		
		self.hook.work_status(thread_number, 'exiting')

def main():
	# Initial parser is for unit directory. We need to process this argument first,
	# so that the specified unit may be loaded
	parser = ArgumentParserWithHelp(
		description='Low-hanging fruit checker for CTF problems',
		add_help=True,
		allow_abbrev=True)
#	parser.add_argument('--unitdir', type=utilities.DirectoryArgument,
#		default='./units', help='the directory where available units are stored')
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
	finder = units.UnitFinder(args.exclude)

	# Let the user know what we're doing (this takes a couple seconds)
	with log.progress('loading units') as p:
		for unit in finder.load_units():
			p.status('loaded {0}'.format(unit.__module__))
		p.success('complete')

	# Add all unit arguments to our parser
	finder.construct_parser(parser)

	# Parse remaining arguments
	args = parser.parse_args()

	# Convert args namespace to a dictionary
	config = vars(args)

	# Validate config
	config = finder.validate_config(config)

	# Create the Katana
	katana = Katana(config, finder, hook.LoggingKatanaHook())

	if katana.config['display_images']:
		# Create a Tkinter window to show images
		gui_katana = GUIKatana(katana)
		gui_katana.evaluate()
	else:
		# Run katana against all units
		katana.evaluate()
