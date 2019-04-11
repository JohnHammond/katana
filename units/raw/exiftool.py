from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.raw
import utilities
from units import NotApplicable

class Unit(units.raw.RawUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		if not os.path.isfile(target):
			raise NotApplicable

	def evaluate(self, katana, case):

		try:
			p = subprocess.Popen(['exiftool', self.target ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		except FileNotFoundError as e:
			if "No such file or directory: 'exiftool'" in e.args:
				log.failure("exiftool is not in the PATH (not installed)? Cannot run the stego.exiftool unit!")
				return None

		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			katana.locate_flags(str(response['stdout']))
			katana.add_result( self, 'stdout', response['stdout'] )
		if 'stderr' in response:
			katana.locate_flags(str(response['stderr']))
			katana.add_result( self, 'stderr', response['stderr'] )