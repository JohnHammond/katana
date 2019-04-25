#!/usr/bin/env python
import sys
import subprocess
import json
import shutil
import os
from pwn import *

if __name__ == "__main__":

	try:
		with open('./test.json', 'rb') as fp:
			tests = json.load(fp)
	except:
		log.failure('./test.json: failed to load unit tests')
		sys.exit(-1)

	try:
		shutil.rmtree('./test-results')
	except:
		# We don't care if it didn't exis
		pass

	os.mkdir('./test-results')
	
	for test in tests:
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

		# Run the test
		try:
			prog.status('executing katana')
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

