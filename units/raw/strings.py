from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.raw
import utilities
import os
from units import NotApplicable
from unit import BaseUnit

DEPENDENCIES = [ 'strings' ]

class Unit(BaseUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		try:
			if not os.path.isfile(target):
				raise NotApplicable

		# JOHN: These apparently happen in Python 3 if you pass
		#       a filename that contains a null-byte... 
		except ValueError:
			raise NotApplicable
			
		katana.add_argument('--strings-length', '-sl', type=int,
				help="minimum length of strings to return", default=4)
		katana.parse_args()
		
	def evaluate(self, katana, case):

		# Run the process.
		p = subprocess.Popen(['strings', self.target, '-n', str(katana.config['strings_length'])], 
			stdout = subprocess.PIPE, stderr=subprocess.PIPE )

		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			
			# If we see anything interesting in here... scan it again!
			for line in response['stdout']:
				katana.locate_flags(self, line)
				katana.recurse(self, line)

		if 'stderr' in response:
			katana.locate_flags(self, str(response['stderr']))

		katana.add_results(self, response)
		