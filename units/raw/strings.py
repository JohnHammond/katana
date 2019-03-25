from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.raw
import utilities

class Unit(units.raw.RawUnit):

	@classmethod
	def prepare_parser(cls, config, parser):
		parser.add_argument('--length', default=4, type=int, help='minimum length of strings to be returned')

	def evaluate(self, target):

		p = subprocess.Popen(['strings', target, '-n', str(self.config['length'])], 
			stdout = subprocess.PIPE, stderr=subprocess.PIPE )

		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			self.find_flags(str(response['stdout']))
		if 'stderr' in response:
			self.find_flags(str(response['stderr']))
		
		return response