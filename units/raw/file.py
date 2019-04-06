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

class Unit(units.raw.RawUnit):

	# We do not need to include the constructor in this case.
	# Because we are working with the "raw" unit,
	# we should really expect anything.


	def evaluate(self, katana, case):

		try:
			p = subprocess.Popen(['file', katana.target], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		except FileNotFoundError as e:
			if "No such file or directory: 'file'" in e.args:
				log.failure("file is not in the PATH (not installed)? Cannot run the raw.file unit!")
				return None
		
		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			
			# If we see anything interesting in here... scan it again!
			for line in str(response['stdout']):
				katana.recurse(self, line)

			katana.locate_flags(str(response['stdout']))
			katana.add_result( self, 'stdout', response['stdout'] )

		if 'stderr' in response:
			katana.locate_flags(str(response['stderr']))
			katana.add_result( self, 'stderr', response['stderr'] )