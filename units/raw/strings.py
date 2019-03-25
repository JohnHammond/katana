from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.raw
import util

class Unit(units.raw.RawUnit):

	@classmethod
	def prepare_parser(cls, config, parser):
		parser.add_argument('--length', default=4, type=int, help='minimum length of strings to be returned')

	def evaluate(self, target):

		p = subprocess.Popen(['strings', target, '-n', str(self.config['length'])], 
			stdout = subprocess.PIPE, stderr=subprocess.PIPE )

		# Look for flags, if we found them...
		response = util.process_output(p)
		self.find_flags(response['stdout'])
		self.find_flags(response['stderr'])

		return response