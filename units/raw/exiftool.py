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
		pass

	def evaluate(self, target):

		try:
			p = subprocess.Popen(['exiftool', target ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		except FileNotFoundError as e:
			if "No such file or directory: 'exiftool'" in e.args:
				log.failure("exiftool is not in the PATH (not installed)? Cannot run the stego.exiftool unit!")
				return None

		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			self.find_flags(str(response['stdout']))
		if 'stderr' in response:
			self.find_flags(str(response['stderr']))
		
		return response