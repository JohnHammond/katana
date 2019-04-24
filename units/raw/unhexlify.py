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
import traceback

HEX_PATTERN = rb'((0x)?[a-f0-9]+)'
HEX_REGEX = re.compile(HEX_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)

class Unit(BaseUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		# We don't need to operate on files
		if not self.target.is_printable or self.target.is_file or self.target.is_english:
			raise NotApplicable

		# Check if there is hex in it
		self.matches = HEX_REGEX.findall(self.target.raw)
		if self.matches is None:
			raise NotApplicable()

	def evaluate(self, katana, case):	
		for match,_ in self.matches:
			if match.lower().startswith(b'0x'):
				match = match[2:]
			if len(match) < 4:
				continue
			try:
				result = binascii.unhexlify(match)
				katana.recurse(self, result)
				katana.add_results(self, result)
			except binascii.Error as e:
				# We may have an "odd-length string" in the way...
				# try to clean up the ends to see if we get anything
				result = binascii.unhexlify(match[0:-1])
				katana.recurse(self, result)
				katana.add_results(self, result)

				result = binascii.unhexlify(match[1:])
				katana.recurse(self, result)
				katana.add_results(self, result)