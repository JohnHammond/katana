from unit import BaseUnit
from units import FileUnit
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

class Unit(FileUnit):

	PRIORITY = 25

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

	def evaluate(self, katana, case):
	
		p = subprocess.Popen(['exiftool', self.target.path ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		
		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if response:
			if 'stdout' in response:
				for line in response['stdout']:
					delimited = line.split(':')
					metadata = delimited[0].strip()
					value = ':'.join(delimited[1:]).strip()
					
					# JOHN: We do NOT recurse on the metadata, because that is probably
					#       NOT going to contain a flag
					# katana.recurse(self, metadata)
					if metadata in ['Comment', 'Album', 'Artist', 'Title']:
						katana.recurse(self, value)
			
			katana.add_results(self, response)
