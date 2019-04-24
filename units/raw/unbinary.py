from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.raw
import units
import utilities
import os
from units import NotApplicable
import binascii
import traceback

BINARY_PATTERN = rb'[01]{8,}'
BINARY_REGEX = re.compile(BINARY_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)

class Unit(BaseUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		self.matches = BINARY_REGEX.findall(self.target.raw)

		if self.matches is None:
			raise NotApplicable

	def evaluate(self, katana, case):

		try:
			raw = ''.join([ chr(int(x,2)) for x in self.matches])

			# JOHN: The question of whether or not we should only handle
			#       printables came up when we worked on XOR...
			#       ... but we left it raw, because what if it uncovers a file?
			# if raw.replace('\n', '').isprintable():
			katana.recurse(self, raw)
			katana.add_results(self, raw )

		except:
			pass

		for result in self.matches:
			decimal = int(result,2)
			try:
				new_result = binascii.unhexlify(hex(decimal)[2:]).decode('utf-8')
			# If this fails, it's probably not binary we can deal with...
			except (UnicodeDecodeError, binascii.Error):
				return None

			# JOHN: The question of whether or not we should only handle
			#       printables came up when we worked on XOR...
			#       ... but we left it raw, because what if it uncovers a file?
			# if new_result.replace('\n','').isprintable():
			katana.recurse(self, new_result)
			katana.add_results(self, new_result )
