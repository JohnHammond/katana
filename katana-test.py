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
	args = parser.parse_args()

	# Read in the test data
	try:
		with open('./test.json', 'rb') as fp:
			tests = json.load(fp)
	except:
		log.failure('./test.json: failed to load unit tests')
		traceback.print_exc()
		sys.exit(-1)

	# Remove old results tree if it exists
	try:
		shutil.rmtree('./test-results')
	except:
		# We don't care if it didn't exis
		pass

	# Create results tree
	os.mkdir('./test-results')

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
		args = [ './katana.py', '--outdir', os.path.join('./test-results', test['name']) ]
		for item, value in test.items():
			if item == 'name' or item == 'flag' or item == 'test_timeout':
				continue
			elif item == 'unit':
				for unit in value:
					args.append('--unit')
					args.append(unit)
			elif item == 'auto':
				args.append('--auto')
			elif item == 'target':
				args.append(value)
			else:
				args.append('--' + item.replace('_', '-'))
				args.append(value)

		if 'test_timeout' in test:
			timeout = test['test_timeout']
		else:
			timeout = 30

		prog.status('executing test')

		# Run the test
		try:
			result = subprocess.run(args, capture_output=True, timeout=timeout)
		except subprocess.TimeoutExpired:
			prog.failure('test timeout expired!')
			continue

		# Check the result
		#if result.returncode != 0:
			#prog.failure('non-zero return code: {0}'.format(result.returncode))
			#continue

		if 'flag' not in test:
			prog.success('test completed. correct flag unknown; check results')
		elif test['flag'] not in result.stdout.decode('utf-8'):
			prog.failure('test failed: flag not found in output!')
		else:
			prog.success('flag found')

