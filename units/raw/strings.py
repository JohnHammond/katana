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

class Unit(units.raw.RawUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		if not os.path.isfile(target):
			raise NotApplicable
	
		# Create a new katana argument parser
		#parser = katana.ArgumentParser()
		try:
			katana.parser.add_argument('--strings-length', '-sl', type=int,
				help="minimum length of strings to return", default=4)
		except:
			# If we recurse, we have already seen this argument. Ignore it.
			pass

		katana.parse_args()
		

	def evaluate(self, katana, case):

		# Run the process.
		try:
			p = subprocess.Popen(['strings', self.target, '-n', str(katana.config['strings_length'])], 
				stdout = subprocess.PIPE, stderr=subprocess.PIPE )
		except FileNotFoundError as e:
			if "No such file or directory: 'strings'" in e.args:
				log.failure("strings is not in the PATH (not installed)? Cannot run the raw.strings unit!")
				return None

		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			
			# If we see anything interesting in here... scan it again!
			for line in response['stdout']:
				katana.recurse(self, line)
				katana.locate_flags(line)

			katana.add_result( self, 'stdout', response['stdout'] )

		if 'stderr' in response:
			katana.locate_flags(str(response['stderr']))
			katana.add_result( self, 'stderr', response['stderr'] )
		
		