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
import pkgutil

# Global Work Queue
WORKQ = None
# Results dictionary
RESULTS = {}
# The configuration (arguments, really)
CONFIG = {}
# Lock for results access
RESULT_LOCK = threading.RLock()

# This is the thread which actually runs the unit checks and stores
# the results in the RESULT array
class WorkerThread(threading.Thread):
	def __init__(self):
		super(WorkerThread, self).__init__()

	def run(self):
		while True:
			# Grab the next item
			unit,name,case = WORKQ.get()
			# The boss says NO.
			if unit is None and case is None and name is None:
					break

			if not unit.completed:
				if ( args.force or unit.check(case) ):
					# Perform the evaluation
					result = unit.evaluate(case)
					# Grab the lock for saving the results
					if result is not None:
						with RESULT_LOCK:
							# Build the structure if needed
							if unit.unit_name not in RESULTS[target] or \
									RESULTS[target][unit.unit_name] == None:
								RESULTS[target][unit.unit_name] = {}
							RESULTS[target][unit.unit_name][name] = result
							
							# JOHN: I wanted to use this hide entries with no results...
							# if result:
							# 	RESULTS[target][unit.unit_name][name] = result
							# else:
							# 	RESULTS[target].pop(unit.unit_name)
			
			# Notify boss that we are done
			WORKQ.task_done()

# This subclass of argparse will print the help whenever there
# is a syntactic error in the options parsing
class ArgumentParserWithHelp(argparse.ArgumentParser):
	def error(self, message):
		print('{0}: error: {1}'.format(self.prog, message))
		self.print_help()
		sys.exit(2)

def load_modules_recursive(path, prefix=''):
	for importer, name, ispkg in pkgutil.iter_modules(path, prefix):
		module = importlib.import_module(name)
	
		if ispkg:
			for s in load_modules_recursive(module.__path__, module.__name__ + '.'):
				yield s
		else:
			yield module

# Make sure we find the local packages (first current directory)
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.getcwd())

if __name__ == '__main__':
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
	args, remaining = parser.parse_known_args()

	# Insert the unit directory module into th epath
	sys.path.insert(0, args.unitdir)
	
	# Setup initial configuration block
	CONFIG['modules'] = []
	
	# Create the next (and last) argument parser
	parser = argparse.ArgumentParser(parents=[parser], add_help=True)
	
	# Attempt to load specified units
	for name in args.unit:
		try:
			# import the module
			module = importlib.import_module(name)
			# We don't load units from packages
			if module.__name__ != module.__package__:
				try:
					# initialize any module specific arguments
					module.Unit.prepare_parser(CONFIG, parser)
					# add to unit list
					CONFIG['modules'].append(module)
				except:
					print("this one")
					log.info('{0}: no Unit class found'.format(module.__name__))
			else:
				# Load children, if there are any
				for m in load_modules_recursive(module.__path__, module.__name__+'.'):
					try:
						m.Unit.prepare_parser(CONFIG, parser)
						CONFIG['modules'].append(m)
					except Exception as e:
						print(e.args)
						log.info('{0}: no Unit class found'.format(module.__name__))
		except ModuleNotFoundError as e:
			log.failure('unit {0} does not exist'.format(name))
			exit()
		except Exception as e:
			traceback.print_exc()
			log.failure('unknown error when loading {0}: {1}'.format(name, e))
			exit()
	
	# The number of threads to use
	parser.add_argument('--threads', '-t', type=int, default=10,
		help='number of threads to use')
	# Whether or not to use the built-in module checks
	parser.add_argument('--force', '-f', action='store_true',
		default=False, help='skip the checks')
	# The list of targets to scan
	parser.add_argument('target', nargs='+', type=str, default='-',
		help='the target file/url/IP/etc')
	# The output directory for this scan
	parser.add_argument('--outdir', '-o', default='./results',
		help='directory to house results')
	# A Regular Expression patter for units to match
	parser.add_argument('--flag-format', '-ff', default=None,
		help='regex pattern for output (e.g. "FLAG{.*}")')
	args = parser.parse_args()

	# Check if the file exists and isn't a directory... that's bad
	if os.path.exists(args.outdir):
		log.failure('{0}: directory exists'.format(args.outdir))
		exit()
	elif not os.path.exists(args.outdir):
		# Create the directory if needed
		try:
			os.mkdir(args.outdir)
		except:
			log.failure('{0}: unable to create directory'.format(args.outdir))
			exit()

	# Create a work queue twice the size of the number of threads
	WORKQ = queue.Queue(maxsize=args.threads*2)
	
	# Update the configuration with the arguments
	CONFIG.update(vars(args))

	# We want the "-" target to signify stdin
	if len(args.target) == 1 and args.target[0] == '-':
		args.target = []
		for line in sys.stdin.read().split('\n'):

			args.target.append(line)
	
	# Initialize the units array
	CONFIG['units'] = []
	
	# Build unit objects from loaded modules
	for module in CONFIG['modules']:
		unit = module.Unit(CONFIG)
		CONFIG['units'].append(unit)
	
	# Begin a progress output for the units
	p = log.progress('processing')
	
	# Create all the worker threads
	CONFIG['threads'] = []
	for i in range(args.threads):
		thread = WorkerThread()
		thread.start()
		CONFIG['threads'].append(thread)

	p.status('filling work queue')

	RESULTS = { t: {} for t in args.target }
	
	total = 0
	
	# Add all the target/unit pairs to the work queue
	for target in args.target:
		# Add each unit to the work queue
		for unit in CONFIG['units']:
			for name,case in unit.get_cases(target):
				# The threads are working now, stop adding if it's done.
				if not unit.completed:
					p.status('adding {0} to work queue (size: {1}, n: {2})'.format(name, WORKQ.qsize(),total))
					WORKQ.put((unit,name,case))
					total += 1
				else:
					break

	# Monitor the work queue and update the progress
	while True:
		# Grab the numer of items in the queue
		n = WORKQ.qsize()
		# End if we are done
		if n == 0:
			break
		# Print a nice percentage compelte
		p.status('{0:.2f}% complete'.format((float(len(args.target)-n)/len(args.target))*100.0))
		# We want to give the threads time to execute
		time.sleep(0.5)

	# Notify the threads that we are done
	for i in range(args.threads):
		WORKQ.put((None,None,None))
	# Wait for them to exit
	for i in range(args.threads):
		CONFIG['threads'][i].join()

	if CONFIG['flag_format']:
		RESULTS['flags'] = []

		for unit in CONFIG['units']:
			RESULTS['flags'] += unit.flags
		RESULTS['flags'] = list(set(RESULTS['flags']))
		
	p.success('all units complete')

	# Make sure we can create the results file
	with open(os.path.join(args.outdir, 'katana.json'), 'w') as f:
		json.dump(RESULTS, f, indent=4, sort_keys=True)

	# Cleanly display the results of each unit
	print(json.dumps({ x: RESULTS[x] for x in RESULTS if RESULTS[x] != {} }, indent=4, sort_keys=True))

	if CONFIG['flag_format']:
		# Dump the flags we found
		for flag in RESULTS['flags']:
			log.success('Found flag: {0}'.format(flag))
