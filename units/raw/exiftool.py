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

	def evaluate(self, katana, case):
	
		p = subprocess.Popen(['exiftool', self.target ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		
		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			# katana.locate_flags(str(response['stdout']))
			for line in response['stdout']:
				delimited = line.split(':')
				metadata = delimited[0].strip()
				value = ':'.join(delimited[1:]).strip()
				
				katana.locate_flags(self,value)
				katana.locate_flags(self,metadata)
			
				# JOHN: We do NOT recurse on the metadata, because that is probably
				#       NOT going to contain a flag
				# katana.recurse(self, metadata)
				if metadata in ['Comment', 'Album', 'Artist', 'Title']:
					katana.recurse(self, value)

		if 'stderr' in response:
			katana.locate_flags(self, str(response['stderr']))

		katana.add_results(self, response)
