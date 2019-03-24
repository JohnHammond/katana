from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import os
import units.raw
import re

class Unit(units.raw.RawUnit):

	@classmethod
	def prepare_parser(cls, config, parser):
		parser.add_argument('--dict', '-d', type=argparse.FileType('r', encoding='latin-1'),
			help="Dictionary for bruteforcing")
		parser.add_argument('--password', '-p', type=str,
		help="A password to try on the file", action="append",
			default=[])
		parser.add_argument('--pattern', type=str,
			help="Pattern which the result should match",
			default=None)
		parser.add_argument('--stop', default=True,
			help="Stop processing on matching password",
			action="store_false")
		return

	def __init__(self, config):
		super(Unit, self).__init__(config)
		if self.config['pattern'] is not None:
			self.config['pattern'] = re.compile(self.config['pattern'])
	
	def check(self, target):
		return super(Unit, self).check(target[0])

	def get_cases(self, target):
		# The default is to check an empty password
		yield 'empty password',(target, '')

		# Check other passwords specified explicitly
		for p in self.config['password']:
			yield p,(target,p)

		# Add all the passwords from the dictionary file
		if 'dict' in self.config and self.config['dict'] is not None:
			self.config['dict'].seek(0)
			for line in self.config['dict']:
				yield line.rstrip('\n'),(target, line.rstrip('\n'))

	def evaluate(self, target):

		# Split up the target (see get_cases)
		target_file, password = target

		# Grab the output path for this target and password
		output_path = self.artifact(target_file, password, create=False)

		# This file exists, we already tried this password
		if os.path.exists(output_path):
			return None
			
		# Run steghide
		p = subprocess.Popen(
			['steghide', 'extract', '-sf', target_file, '-p', password, '-xf', output_path],
			stdout = subprocess.PIPE, stderr = subprocess.PIPE
		)

		# Grab the output
		output = bytes.decode(p.stdout.read(),'ascii')
		error = bytes.decode(p.stderr.read(),'ascii')
		
		if 'wrote extracted data to' not in error:
			return None

		if self.config['pattern'] is not None:
			if self.config['pattern'].match(error) is None:
				return None

		if self.config['stop']:
			self.completed = True
		
		return error
