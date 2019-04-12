from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import os
import units.raw
import utilities
from units import NotApplicable

class Unit(units.raw.RawUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)
		# We can only handle this if it is a file!
		if not os.path.isfile(target):
			raise NotApplicable()

	def evaluate(self, katana, case):

		try:
			p = subprocess.Popen(['file', self.target], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		except FileNotFoundError as e:
			if "No such file or directory: 'file'" in e.args:
				log.failure("file is not in the PATH (not installed)? Cannot run the raw.file unit!")
				return None
		
		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			
			# If we see anything interesting in here... scan it again!
			for line in response['stdout']:
				katana.recurse(self, line)

			katana.locate_flags(str(response['stdout']))

		if 'stderr' in response:
			katana.locate_flags(str(response['stderr']))

		katana.add_results(self, response)
