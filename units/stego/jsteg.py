from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import os
import units.stego
import utilities
import units

DEPENDENCIES = [ 'jsteg' ]

class Unit(units.FileUnit):

	def __init__(self, katana, parent, target):
		# This ensures it is a JPG
		super(Unit, self).__init__(katana, parent, target, keywords=['jpg image', 'jpeg image'])

	def evaluate(self, katana, case):

		try:
			p = subprocess.Popen(['jsteg', 'reveal', self.target ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		except FileNotFoundError as e:
			if "No such file or directory: 'jsteg'" in e.args:
				log.failure("jsteg is not in the PATH (not installed)? Cannot run the stego.jsteg unit!")
				return None

		# Look for flags, if we found them...
		response = utilities.process_output(p)
		
		if 'stdout' in response:
			for line in response['stdout']:
				katana.recurse(self, line)
				katana.locate_flags(self, str(response['stdout']))
				
		if 'stderr' in response:
			katana.locate_flags(self, str(response['stderr']))
		
		katana.add_results(self, response)