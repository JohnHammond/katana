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
import units

class Unit(units.stego.StegoUnit):


	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		if not os.path.isfile(target):
			raise units.NotApplicable()
	
		# Create a new katana argument parser
		katana.add_argument('--dict', '-d', type=argparse.FileType('r', encoding='latin-1'),
			help="Dictionary for bruteforcing")
		katana.add_argument('--password', '-p', type=str,
			help="A password to try on the file", action="append",
			default=[])
		katana.add_argument('--stop', default=True,
			help="Stop processing on matching password",
			action="store_false")

		# Parse the arguments
		katana.parse_args()	

	def enumerate(self, katana):
		# The default is to check an empty password
		yield ''

		# Check other passwords specified explicitly
		for p in katana.config['password']:
			yield p

		# Add all the passwords from the dictionary file
		if 'dict' in katana.config and katana.config['dict'] is not None:
			katana.config['dict'].seek(0)
			for line in katana.config['dict']:
				yield line.rstrip('\n')

	def evaluate(self, katana, password):

		# Grab the output path for this target and password
		if ( password == "" ):
			output_path = self.artifact(katana, "no_password", create=False)	
		else:
			output_path = self.artifact(katana, password, create=False)

		# This file exists, we already tried this password
		if os.path.exists(output_path):
			log.failure(output_path)

		# Run steghide
		p = subprocess.Popen(
			['steghide', 'extract', '-sf', self.target, '-p', password, '-xf', output_path],
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
		
		with open(output_path, 'r') as f:
			thing = f.read()

		# Check if it matches the pattern
		if katana.locate_flags(thing) and katana.config['stop']:
			self.completed = True

		katana.recurse(self, output_path)

		katana.add_results(self, {
			'file': output_path,
			'type': typ,
			'content': thing
		})
