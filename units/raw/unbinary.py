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

		PATTERN = re.compile( '[01]{8,}' , flags=re.MULTILINE | \
								re.DOTALL | re.IGNORECASE  )
		binary_result = PATTERN.findall(str(self.target))

		if binary_result is None or binary_result == []:
			raise NotApplicable()
		else:
			self.binary_result = binary_result

	def evaluate(self, katana, case):
		
		for result in self.binary_result:
			
			decimal = int(result,2)
			try:
				new_result = binascii.unhexlify(hex(decimal)[2:]).decode('utf-8')

			# If this fails, it's probably not binary we can deal with...
			except (UnicodeDecodeError, binascii.Error):
				return None

			katana.recurse(self, new_result)
			katana.locate_flags(self, new_result )
			katana.add_results(self, new_result )
