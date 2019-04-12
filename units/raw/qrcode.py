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

	# We do not need to define the constructor in this case.
	# Because we are working with something "raw", we can essentially accept everything.
	# No need to "check" if this applicable.

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)
		# We can only handle this if it is a file!
		if not os.path.isfile(target):
			raise NotApplicable


	def evaluate(self, katana, case):

		try:
			p = subprocess.Popen(['zbarimg', self.target ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		except FileNotFoundError as e:
			if "No such file or directory: 'zbarimg'" in e.args:
				log.failure("zbarimg is not in the PATH (not installed)? Cannot run the raw.qrcode unit!")
				return None

		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			
			# If we see anything interesting in here... scan it again!
			for line in response['stdout']:
				katana.recurse(self, line)

			self.locate_flags(katana,str(response['stdout']))

		if 'stderr' in response:
			self.locate_flags(katana, str(response['stderr']))

		katana.add_results(self, response)
