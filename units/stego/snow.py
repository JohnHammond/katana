from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.stego
import utilities

dependancy_command = 'snow'

class Unit(units.stego.StegoUnit):


	def evaluate(self, katana, case):

		p = subprocess.Popen([dependancy_command, self.target ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)

		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			
			# If we see anything interesting in here... scan it again!
			for line in response['stdout']:
				katana.locate_flags(line)
				katana.recurse(self, line)

		if 'stderr' in response:
			katana.locate_flags(str(response['stderr']))

		katana.add_results(self, response)


# Ensure the system has the required binaries installed. This will prevent the module from running on _all_ targets
try:
	subprocess.check_output(['which',dependancy_command])
except (FileNotFoundError, subprocess.CalledProcessError) as e:
	raise units.DependancyError(dependancy_command)