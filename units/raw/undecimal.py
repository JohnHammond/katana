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

class Unit(units.raw.RawUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		PATTERN = re.compile( '[0-9]{1,3}' , flags=re.MULTILINE | \
								re.DOTALL | re.IGNORECASE  )
		decimal_result = PATTERN.findall(str(self.target))

		if decimal_result is None or decimal_result == []:
			raise NotApplicable()
		else:

			for decimal in decimal_result:
				if int(decimal) not in range(255):

					raise NotApplicable
			self.decimal_result = decimal_result

	def evaluate(self, katana, case):
		
	
		try:
			new_result = ''.join(chr(int(d)) for d in self.decimal_result)

		# If this fails, it's probably not binary we can deal with...
		except (UnicodeDecodeError, binascii.Error):
			return None

		katana.recurse(self, new_result)
		katana.locate_flags(self, new_result )
		katana.add_results(self, new_result )
