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
import magic
from units import NotApplicable

DEPENDENCIES = [ 'zbarimg' ]

class Unit(units.raw.RawUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)
		# We can only handle this if it is a file!
		if not os.path.isfile(target) or 'image' not in magic.from_file(target):
			raise NotApplicable


	def evaluate(self, katana, case):

		p = subprocess.Popen([dependancy_command, self.target ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)

		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			
			# If we see anything interesting in here... scan it again!
			for line in response['stdout']:
				katana.recurse(self, line)

			katana.locate_flags(self,str(response['stdout']))

		if 'stderr' in response:
			katana.locate_flags(self, str(response['stderr']))

		katana.add_results(self, response)