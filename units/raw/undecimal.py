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

DECIMAL_PATTERN = rb'[0-9]{1,3}'
DECIMAL_REGEX   = re.compile( DECIMAL_PATTERN, flags=re.MULTILINE | \
								re.DOTALL | re.IGNORECASE  )

class Unit(BaseUnit):

	PRIORITY = 25

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		# We don't need to operate on files
		if not self.target.is_printable or self.target.is_file or self.target.is_english:
			raise NotApplicable("is a file")

		self.matches = DECIMAL_REGEX.findall(self.target.raw)

		if self.matches is None:
			raise NotApplicable("no decimal values found")

		for decimal in self.matches:
			if int(decimal) not in range(255):
				raise NotApplicable("decimal value larger than 255 was found")

	def evaluate(self, katana, case):
	
		try:
			new_result = ''.join(chr(int(d)) for d in self.matches)
		# If this fails, it's probably not decimal we can deal with...
		except (UnicodeDecodeError, binascii.Error):
			return None

		# JOHN: The question of whether or not we should only handle
		#       printables came up when we worked on XOR...
		#       ... but we left it raw, because what if it uncovers a file?
		# if new_result.replace('\n', '').isprintable():
		katana.recurse(self, new_result)
		katana.add_results(self, new_result )
