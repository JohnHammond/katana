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
import binascii

class Unit(units.raw.RawUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		katana.add_argument('--hex-threshold', default=5, type=int,
			help="minimum number of hex characters for hex detection")

		# Parse the arguments
		katana.parse_args()	

		if self.target.lower().startswith('0x'):
			self.target = self.target[2:]

		PATTERN = re.compile( '[abcdef1234567890]{%d,}' % katana.config['hex_threshold'], flags=re.MULTILINE | \
								re.DOTALL | re.IGNORECASE  )
		hex_result = PATTERN.findall(str(self.target))


		if hex_result is None or hex_result == []:
			raise NotApplicable()
		else:
			self.hex_result = hex_result

	def evaluate(self, katana, case):
		
		for result in self.hex_result:
			try:
				result = binascii.unhexlify(result).decode('utf-8')

				katana.recurse(self, result)

				katana.locate_flags(self, result )
				katana.add_results(self, result )
			
			except (binascii.Error, UnicodeDecodeError):
				# This won't decode right... must not be right!
				pass

