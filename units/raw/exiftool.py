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

DEPENDENCIES = [ 'exiftool' ]

class Unit(units.FileUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		try:
			if not os.path.isfile(target):
				raise NotApplicable

		# JOHN: These apparently happen in Python 3 if you pass
		#       a filename that contains a null-byte... 
		except ValueError:
			raise NotApplicable

	def evaluate(self, katana, case):

	
		p = subprocess.Popen(['exiftool', self.target ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		
		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			# katana.locate_flags(str(response['stdout']))
			for line in response['stdout']:
				delimited = line.split(':')
				metadata = delimited[0]
				value = ':'.join(delimited[1:]).strip()
				
				katana.locate_flags(self,value)
				katana.locate_flags(self,metadata)
			
				katana.recurse(self, value)
				katana.recurse(self, metadata)

		if 'stderr' in response:
			katana.locate_flags(self, str(response['stderr']))

		katana.add_results(self, response)
