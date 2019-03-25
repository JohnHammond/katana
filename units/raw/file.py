from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import os
import units.raw
import utilities

class Unit(units.raw.RawUnit):

	@classmethod
	def prepare_parser(cls, config, parser):
		pass

	def evaluate(self, target):

		p = subprocess.Popen(['file', target], stdout = subprocess.PIPE, stderr = subprocess.PIPE)		
		
		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			self.find_flags(str(response['stdout']))
		if 'stderr' in response:
			self.find_flags(str(response['stderr']))
		
		return response