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
import units.stego
import magic

class Unit(units.stego.StegoUnit):

	@classmethod
	def prepare_parser(cls, config, parser):
		parser.add_argument('--dict', '-d', type=argparse.FileType('r', encoding='latin-1'),
			help="Dictionary for bruteforcing")
		parser.add_argument('--password', '-p', type=str,
		help="A password to try on the file", action="append",
			default=[])
		parser.add_argument('--stop', default=True,
			help="Stop processing on matching password",
			action="store_false")
		return

	def __init__(self, config):
		super(Unit, self).__init__(config)
	
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
		if ( password == "" ):
			output_path = self.artifact(target_file, "no_password", create=False)	
		else:
			output_path = self.artifact(target_file, password, create=False)

		# This file exists, we already tried this password
		if os.path.exists(output_path):
			log.failure(output_path)
			return None
			

		# Run steghide
		p = subprocess.Popen(
			['steghide', 'extract', '-sf', target_file, '-p', password, '-xf', output_path],
			stdout = subprocess.PIPE, stderr = subprocess.PIPE
		)

		# Wait for process completion
		p.wait()

		# Grab the output
		output = bytes.decode(p.stdout.read(),'ascii')
		error = bytes.decode(p.stderr.read(),'ascii')

		# Check if it succeeded
		if p.returncode != 0:
			return None
	
		# Grab the file type
		typ = magic.from_file(output_path)
		thing = '<BINARY_DATA>'
		
		# If the type is text, then we can display it in katana.json
		if typ == 'text/plain' or 'ASCII text' in typ:
			with open(output_path, 'r') as f:
				thing = f.read()

		# Check if it matches the pattern
		self.find_flags(thing)

		# Stop processing this unit if we only expect on success
		if self.config['stop']:
			self.completed = True
	
		return {
			'file': output_path,
			'type': typ,
			'content': thing
		}
