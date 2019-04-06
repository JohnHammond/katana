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
		self.results = { 'flags': [] }
		self.results_lock = threading.RLock()

		# Parse initial arguments
		self.parse_args()

		# We want the "-" target to signify stdin
		if len(self.target) == 1 and self.target[0] == '-':
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
		self.locate_units()

	@property
	def target(self):
		""" Shorthand for grabbing the target """
		return self.config['target']
	
	def add_result(self, key, val):
		self.add_results({key:val})

	def add_results(self, d):
		with self.results_lock:
			self.results.update(d)

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

		# Add all the cases to the work queue
		nitems = 0
		for unit in self.units:
			if not self.completed:
				case_no = 0
				for case in unit.enumerate(self):
					if not unit.completed:
						prog.status('adding {0}[{1}] to work queue (size: {2}, total: {3})'.format(
							unit.unit_name, case_no, self.work.qsize(), nitems
						))
						self.work.put((unit, case_no, case))
						nitems += 1
						case_no += 1
					else:
						break

		# Monitor the work queue and update the progress
		while True:
			# Grab the numer of items in the queue
			n = self.work.qsize()
			# End if we are done
			if n == 0:
				break
			# Print a nice percentage compelte
			prog.status('{0:.2f}% complete'.format(float(n) / float(nitems)))
			# We want to give the threads time to execute
			time.sleep(0.5)

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

	def add_flag(self, flag):
		with self.results_lock:
			self.results['flags'].append(flag)
	
	def locate_flags(self, output):
		""" Look for flags in the given data/output """

		# If the user didn't supply a pattern, there's nothing to do.
		if self.flag_pattern == None:
			return False
		
		# JOHN: Below is my attempt to search for Base64 encoded flag formats
		special_regex_characters = [
			"\\d", "\\w", '\\s', "\\D", "\\W", '\\S',
			"+", "{", '}', "*", "?", '.', '|', '(', ')', '[', ']',
		]

		# In case someone for some reason includes this...
		# And the 'pattern' is a compiled regex... the 'pattern.pattern' 
		#                                          is the raw regex string
		# Also, we remove the surrounding () parentheses
		raw_flag = self.flag_pattern.pattern.replace('^', '')[1:-1]

		found_regex = 0
		for index in range(len(raw_flag)):
			character = raw_flag[index]
			if character in special_regex_characters:
				# This is as far as we can go in the flag pattern.
				found_regex = 1
				break
		
		index -= 1*found_regex  
		
		# Plus one because this the index is zero-based and slicing is not...
		raw_flag = raw_flag[:index+1]
		
		hex_flag = binascii.hexlify(bytes(raw_flag,'utf-8')).decode('utf-8')

		base64_flag = base64.b64encode(bytes(raw_flag, 'utf-8')).decode('utf-8')
		padding = base64_flag.count('=')
		trustworthy_base64 = base64_flag.replace('=','')[:-padding]
		

		base64_regex = '[a-zA-Z0-9+/]+={0,2}'
		hex_regex = '[a-fA-F0-9]*'

		hex_pattern = re.compile(hex_flag + hex_regex, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
		base64_pattern = re.compile(trustworthy_base64 + base64_regex, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)

		# Look for the pattern in the output
		result = self.flag_pattern.search(output)
		base64_result = base64_pattern.search(output)
		hex_result = hex_pattern.search(output)
		
		# No match
		if result is None and base64_result is None and hex_result is None:
		# if result is None:
			return False

		# add the flag
		for match in [ result, base64_result, hex_result ]:
			if match:
				# We will use this approach, to show the original base64 finding
				self.add_flag(match.group())
				if match == base64_result:
					try:
						# This tries to decode too often. If it tries and fails, it must not be Base64
						self.add_flag(base64.b64decode(match.group()).decode('utf-8'))
					except:
						pass
				if match == hex_result:
					self.add_flag(binascii.unhexlify(match.group()).decode('utf-8'))

		return True

	# JOHN: This still needs to be implemented.
	#       But it will become the entry-point for our recursive functionality
	def pass_back(self, data):
		pass

	def load_unit(self, name, required=True, recurse=True):
		try:
			# import the module
			module = importlib.import_module(name)
			# We don't load units from packages
			if module.__name__ != module.__package__:
				unit_clas = None
				# Try to grab the unit class. Fail if it doesn't exit
				try:
					unit_class = module.Unit
				except AttributeError:
					if required:
						log.info('{0}: no Unit class found'.format(module.__name__))
				try:
					self.units.append(unit_class(self))
				except units.NotApplicable:
					if required:
						log.info('{0}: not applicable to target'.format(module.__name__))
			elif recurse:
				# Load children, if there are any
				for m in find_modules_recursively(module.__path__, module.__name__+'.'):
					self.load_unit(m, required, True)
		except ModuleNotFoundError as e:
			if required:
				log.failure('unit {0} does not exist'.format(name))
				exit()
		except Exception as e:
			if required:
				traceback.print_exc()
				log.failure('unknown error when loading {0}: {1}'.format(name, e))
				exit()

	def locate_units(self):

		# Load explicit units
		for unit in self.config['unit']:
			self.load_unit(unit, required=True, recurse=True)

		# Do we want to search for units automatically?
		if not self.config['auto']:
			return

		# Iterate through all `.py` files in the unitdir directory
		# Grab everything that has a unit, and check if it's valid.
		# if it is, add it to the unit list.
		for name in find_modules_recursively(self.config['unitdir'], ''):
			self.load_unit(name, required=False, recurse=False)

		# This will cause an error for any unknown arguments still in the queue
		parser = self.ArgumentParser()
		parser.parse_args()

	def parse_args(self, parser=None):
		""" Use the given parser to parse the remaining arguments """

		# If no parser was specified, parse with the default parser
		if parser is None:
			# Initial parser is for unit directory. We need to process this argument first,
			# so that the specified unit may be loaded
			parser = ArgumentParserWithHelp(
				description='Low-hanging fruit checker for CTF problems',
				add_help=False,
				allow_abbrev=False)
			parser.add_argument('--unitdir', type=utilities.DirectoryArgument,
				default='./units', help='the directory where available units are stored')
			parser.add_argument('--unit', action='append',
				required=True, help='the units to run on the targets')
			parser.add_argument('--unit-help', action='store_true',
				default=False, help='display help on unit selection')
			# The number of threads to use
			parser.add_argument('--threads', '-t', type=int, default=10,
				help='number of threads to use')
			# Whether or not to use the built-in module checks
			parser.add_argument('--force', '-f', action='store_true',
				default=False, help='skip the checks')
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

		# Parse the arguments
		args, remaining = parser.parse_known_args()

		# Add this parser to a list of parsers for parents
		self.parsers.append(parser)

		# Update the configuration
		self.config.update(vars(args))

		return self.config
	
	# Build an argument parser for katana
	def ArgumentParser(self, *args, **kwargs):
		return argparse.ArgumentParser(parents=self.parsers, *args, **kwargs)

	def worker(self):
		""" Katana worker thread to process unit execution """
		while True:
			# Grab the next item
			unit,name,case = self.work.get()
			target = self.target

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
	for flag in katana.results['flags']:
		log.success('Found flag: {0}'.format(flag))
