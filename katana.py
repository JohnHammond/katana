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
import re
import binascii
import base64
import units

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

		# Initial parser is for unit directory. We need to process this argument first,
		# so that the specified unit may be loaded
		self.parser = ArgumentParserWithHelp(
			description='Low-hanging fruit checker for CTF problems',
			add_help=False,
			allow_abbrev=False)
		self.parser.add_argument('--unitdir', type=utilities.DirectoryArgument,
			default='./units', help='the directory where available units are stored')
		self.parser.add_argument('--unit', action='append',
			required=False, default = [], help='the units to run on the targets')
		self.parser.add_argument('--unit-help', action='store_true',
			default=False, help='display help on unit selection')
		# The number of threads to use
		self.parser.add_argument('--threads', '-t', type=int, default=10,
			help='number of threads to use')
		# Whether or not to use the built-in module checks
		self.parser.add_argument('--force', '-f', action='store_true',
			default=False, help='skip the checks')
		# The list of targets to scan
		self.parser.add_argument('target', type=str,
			help='the target file/url/IP/etc') 
		# The output directory for this scan
		self.parser.add_argument('--outdir', '-o', default='./results',
			help='directory to house results')
		# A Regular Expression patter for units to match
		self.parser.add_argument('--flag-format', '-ff', default=None,
			help='regex pattern for output (e.g. "FLAG{.*}")')
		self.parser.add_argument('--auto', '-a', default=False,
			action='store_true', help='automatically search for matching units in unitdir')

		# Parse initial arguments
		self.parse_args()

		# We want the "-" target to signify stdin
		if len(self.original_target) == 1 and self.original_target[0] == '-':
			self.config['target'] = sys.stdin.read()

		# Compile the flag format if given
		if self.config['flag_format']:
			self.flag_pattern = re.compile('({0})'.format(self.config['flag_format']),
					flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
		else:
			self.flag_pattern = None

		# Setup the work queue
		self.work = queue.Queue(maxsize=self.config['threads']*2)

		# Insert the unit directory module into th epath
		sys.path.insert(0, self.config['unitdir'])

		# Don't run if the output directory exists
		if os.path.exists(self.config['outdir']):
			log.error('{0}: directory exists'.format(self.config['outdir']))
		elif not os.path.exists(self.config['outdir']):
			# Create the directory if needed
			try:
				os.mkdir(self.config['outdir'])
			except:
				log.error('{0}: unable to create directory'.format(self.config['outdir']))

		# Find units which match this target
		self.units = self.locate_units(self.config['target'])

	@property
	def original_target(self):
		""" Shorthand for grabbing the target """
		return self.config['target']
	
	def add_result(self, unit, key, val):
		""" Add a single result to the results dict """
		self.add_results(unit, {key:val})

	def add_results(self, unit, d):
		""" Update the results dict with the given dict """
		with self.results_lock:
			parents = []
			parent = unit.parent
			# Are you my mother?
			while parent is not None:
				parents.append(parent)
				parent = parent.parent
			# Start at the global results
			r = self.results
			# Recurse through parent units
			for p in parents[::-1]:
				# If we have not seen results from this parent,
				# THAT'S FINE.... just be ready for it
				if not p.unit_name in r:
					r[p.unit_name] = {}	
				r = r[p.unit_name]
			if unit.unit_name not in r:
				r[unit.unit_name] = {}
			r[unit.unit_name].update(d)

	def evaluate(self):
		""" Start processing all units """

		prog = log.progress('katana')

		prog.status('starting threads')

		# Create all the threads
		for n in range(self.config['threads']):
			prog.status('starting thread {0}'.format(n))
			thread = threading.Thread(target=self.worker)
			thread.start()
			self.threads.append(thread)

		prog.status('filling work queue')

		status_done = threading.Event()
		status_thread = threading.Thread(target=self.progress, args=(prog,status_done))
		status_thread.start()

		# Add the known units to the work queue
		self.add_to_work(self.units)

		# Monitor the work queue and update the progress
		# while True:
		# 	# Grab the numer of items in the queue
		# 	n = self.work.qsize()
		# 	# End if we are done
		# 	if n == 0:
		# 		break
		# 	# Print a nice percentage compelte
		# 	prog.status('{0:.2f}% complete'.format((self.total_work-float(n)) / float(self.total_work)))
		# 	# We want to give the threads time to execute
		# 	time.sleep(0.5)

		self.work.join()

		status_done.set()
		status_thread.join()

		prog.status('all units complete. waiting for thread exit')

		# Notify threads of completion
		for n in range(self.config['threads']):
			self.work.put((None, None, None))

		# Wait for threads to exit
		for t in self.threads:
			t.join()

		# Make sure we can create the results file
		with open(os.path.join(self.config['outdir'], 'katana.json'), 'w') as f:
			json.dump(self.results, f, indent=4, sort_keys=True)

		prog.success('threads exited. evaluation complete')

		log.success('wrote output summary to {0}'.format(os.path.join(self.config['outdir'], 'katana.json')))

	def add_to_work(self, units):
		# Add all the cases to the work queue
		for unit in units:
			if not self.completed:
				case_no = 0
				for case in unit.enumerate(self):
					if not unit.completed:
						#prog.status('adding {0}[{1}] to work queue (size: {2}, total: {3})'.format(
						#	unit.unit_name, case_no, self.work.qsize(), self.total_work
						#))
						self.work.put((unit, case_no, case))
						self.total_work += 1
						case_no += 1
					else:
						break


	def add_flag(self, flag):
		if 'flags' not in self.results:
			self.results['flags'] = []
		with self.results_lock:
			if flag not in self.results['flags']:
				self.results['flags'].append(flag)
	
	def locate_flags(self, output):
		""" Look for flags in the given data/output """

		# If the user didn't supply a pattern, there's nothing to do.
		if self.flag_pattern == None:
			return False

		match = self.flag_pattern.search(output)
		if match:
			self.add_flag(match.group())
			return True

		return False

	def recurse(self, unit, data):
		# JOHN: If this `recurse` is set to True, it will recurse 
		#       WITH EVERYTHING even IF you specify a single unit.
		#       This is the intent, but should be left to "False" for testing
		
		if (data is None or data == "" ):
			return
		units = self.locate_units(data, parent=unit, recurse=True)
		self.add_to_work(units)


	def load_unit(self, target, name, required=True, recurse=True, parent=None):
		try:
			# import the module
			module = importlib.import_module(name)

			# We don't load units from packages
			if module.__name__ != module.__package__:
				unit_class = None
				# Try to grab the unit class. Fail if it doesn't exit
				try:
					unit_class = module.Unit
				except AttributeError:
					if required:
						log.info('{0}: no Unit class found'.format(module.__name__))

				yield unit_class(self, parent, target)

			elif recurse:
				# Load children, if there are any
				for m in find_modules_recursively(os.path.dirname(module.__file__), module.__name__+'.'):
					for unit in self.load_unit(target, m, required, True):
						yield unit

		except ImportError as e:
			if required:
				log.failure('unit {0} does not exist'.format(name))
				exit()

		except units.NotApplicable as e:
			raise e
		except Exception as e:
			if required:
				traceback.print_exc()
				log.failure('unknown error when loading {0}: {1}'.format(name, e))
				exit()
		

	def locate_units(self, target, parent=None, recurse=False):

		units_so_far = []

		if not self.config['auto'] and not recurse:
			# Load explicit units
			for unit in self.config['unit']:
				try:
					for current_unit in self.load_unit(target, unit, required=True, recurse=True, parent=parent):
						units_so_far.append(current_unit)
				except units.NotApplicable:
					# If this unit is NotApplicable, don't try it!
					pass
		else:
			if self.config['auto'] and len(self.config['unit']) > 0:
				log.warning('ignoring --unit options in favor of --auto')

			# Iterate through all `.py` files in the unitdir directory
			# Grab everything that has a unit, and check if it's valid.
			# if it is, add it to the unit list.
			for name in find_modules_recursively(self.config['unitdir'], ''):
				try:
					for current_unit in self.load_unit(target, name, required=False, recurse=False, parent=parent):
						units_so_far.append(current_unit)
				except units.NotApplicable as e:
					# If this unit is NotApplicable, don't try it!
					pass

		return units_so_far

	def add_argument(self, *args, **kwargs):
		""" Add an argument to the argument parser """

		try:
			self.parser.add_argument(*args, **kwargs)
		except argparse.ArgumentError as e:
			return e
	
		return None

	def parse_args(self, final=False):
		""" Use the given parser to parse the remaining arguments """

		# Parse the arguments
		args, remaining = self.parser.parse_known_args()

		# Update the configuration
		self.config.update(vars(args))

		return self.config
	
	# Build an argument parser for katana
	def ArgumentParser(self, *args, **kwargs):
		return argparse.ArgumentParser(parents=self.parsers, add_help = False, *args, **kwargs)

	def progress(self, progress, done_event):
		while not done_event.is_set():
			if self.total_work > 0:
				left = self.work.qsize()
				done = self.total_work - left
				progress.status('{0:.2f}% work queue utilization; {1} total items in queued; {2} completed'.format((float(done)/float(self.total_work))*100, self.total_work, done))
			time.sleep(0.1)

	def worker(self):
		""" Katana worker thread to process unit execution """
		while True:
			# Grab the next item
			unit,name,case = self.work.get()

			# The boss says NO. STAHP.
			if unit is None and case is None and name is None:
					break

			if not unit.completed:
				# Perform the evaluation
				result = unit.evaluate(self, case)
		
			# Notify boss that we are done
			self.work.task_done()

# Make sure we find the local packages (first current directory)
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.getcwd())

if __name__ == '__main__':

	# Create the katana
	katana = Katana()

	# Run katana against all units
	katana.evaluate()

	# Cleanly display the results of each unit to the screen
	print(json.dumps(katana.results, indent=4, sort_keys=True))

	# Dump the flags we found
	if 'flags' in katana.results:
		for flag in katana.results['flags']:
			log.success('Found flag: {0}'.format(flag))
