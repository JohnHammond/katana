#!/usr/bin/env python
import sys
import subprocess
import json
import shutil
import os
from pwn import *
import argparse
import traceback

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument('--test', '-t', action='append', required=False, default=[],
			help='a specific test to run')
	parser.add_argument('--all', '-a', action='store_true', required=False, default=False,
			help='run all tests')
	parser.add_argument('--data', '-d', default='./test.json',
			help='the unit test data to use')
	parser.add_argument('--list', '-l', action='store_true', default=False,
			help='list all available unit tests')
	parser.add_argument('--output', '-o', type=str, default="./test-results",
			help='directory to store all test results')
	args = parser.parse_args()

	# Read in the test data
	try:
		with open('./test.json', 'rb') as fp:
			tests = json.load(fp)
	except:
		log.failure('./test.json: failed to load unit tests')
		traceback.print_exc()
		sys.exit(-1)

	# List units if requested
	if args.list:
		log.info('Availabe Unit Tests:')
		for test in tests:
			print(f'\t- {test["name"]}')
		sys.exit(0)

	# Remove old results tree if it exists
	try:
		shutil.rmtree(args.output)
	except:
		# We don't care if it didn't exis
		pass

	# Create results tree
	os.mkdir(args.output)

	# Make a map of test name -> test data
	required_tests = []
	test_map = { t['name']: t for t in tests }

	if args.all:
		# Run all tests
		required_tests = tests
		if len(args.test) != 0:
			log.warning('ignoring "--test" in favor of "--all"')
	else:
		# Grab each specified test, and ensure it exists
		for t in args.test:
			if t not in test_map:
				log.warning(f'{t}: test does not exist')
			else:
				required_tests.append(test_map[t])

	# Ensure we have something to do	
	if len(required_tests) == 0:
		log.failure('no tests specified; aborting!')
		sys.exit(-1)
	
	for test in required_tests:
		prog = log.progress(test['name'])

		# Build arguments
		prog.status('building arguments')
		prog_args = [ './katana.py', '--outdir', os.path.join(args.output, test['name']) ]
		for item, value in test.items():
			if item == 'name' or item == 'flag' or item == 'test_timeout':
				continue
			elif item == 'unit':
				for unit in value:
					prog_args.append('--unit')
					prog_args.append(unit)
			elif item == 'auto':
				prog_args.append('--auto')
			elif item == 'target':
				prog_args.append(value)
			else:
				prog_args.append('--' + item.replace('_', '-'))
				prog_args.append(value)

		if 'test_timeout' in test:
			timeout = test['test_timeout']
		else:
			timeout = 30

		prog.status('executing test')

		# Run the test
		try:
			with open(os.path.join(args.output, test['name']+'.txt'), 'wb') as f:
				f.write(('command: ' + ' '.join(prog_args)+'\n').encode('utf-8'))
				f.flush()
				result = subprocess.run(prog_args, stdout=f, stderr=f, timeout=timeout)
		except subprocess.TimeoutExpired:
			prog.failure('test timeout expired!')
			continue

		# Check the result
		if result.returncode != 0:
			prog.failure('non-zero return code: {0}'.format(result.returncode))
			continue

		ellapsed = 'unknown'
		with open(os.path.join(args.output, test['name']+'.txt'), 'rb') as f:
			for line in f:
				if b'threads exited in' in line:
					ellapsed = float(line.split(b'in ')[1].split(b's.')[0])

		# Load test results
		try:
			with open(os.path.join(args.output, test['name'], 'katana.json')) as f:
				results = json.load(f)
		except:
			prog.failure('no results found')
		else:
			if 'flags' not in results or len(results['flags']) == 0:
				prog.failure('flag not found in output (run time: {0}s)'.format(ellapsed))
			elif 'flag' not in test:
				prog.success('flags found, but no correct flag specified; check results (runtime: {0}s)'.format(ellapsed))
			elif test['flag'] in results['flags']:
				prog.success('flag found (runtime: {0}s)'.format(ellapsed))
			else:
				prog.failure('flags found, but correct flag not found (runtime: {0}s)'.format(ellapsed))

