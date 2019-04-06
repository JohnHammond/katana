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

	def __init__(self, katana):

		super(Unit, self).__init__(katana)

		# We can only handle this if it is a file!
		if not os.path.isfile(katana.target):
			raise NotApplicable


	def evaluate(self, katana, case):

		try:
			p = subprocess.Popen(['zbarimg', katana.target ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		except FileNotFoundError as e:
			if "No such file or directory: 'zbarimg'" in e.args:
				log.failure("zbarimg is not in the PATH (not installed)? Cannot run the stego.qrcode unit!")
				return None

		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			
			# If we see anything interesting in here... scan it again!
			for line in response['stdout']:
				katana.pass_back(line)

			katana.locate_flags(str(response['stdout']))
			katana.add_result( 'stdout', response['stdout'] )

		if 'stderr' in response:
			katana.locate_flags(str(response['stderr']))
			katana.add_result( 'stderr', response['stderr'] )