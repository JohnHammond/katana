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

class Unit(units.raw.RawUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		if self.target.lower().startswith('0x'):
			self.target = self.target[2:]

		PATTERN = re.compile( '[abcdef1234567890]+' , flags=re.MULTILINE | \
								re.DOTALL | re.IGNORECASE  )
		hex_result = PATTERN.findall(str(self.target))


		if hex_result is None or hex_result == []:
			raise NotApplicable()
		else:
			self.hex_result = hex_result

	def evaluate(self, katana, case):
		
		for result in self.hex_result:
			try:
				new_result = binascii.unhexlify(result).decode('utf-8')

				katana.recurse(self, new_result)
				katana.locate_flags(self, new_result )
				katana.add_results(self, new_result )

			except binascii.Error:

				# We may have an "odd-length string" in the way...
				# try to clean up the ends to see if we get anything
				try:
					new_result = binascii.unhexlify(result[:-1]).decode('utf-8')

					katana.recurse(self, new_result)
					katana.locate_flags(self, new_result )
					katana.add_results(self, new_result )

					new_result = binascii.unhexlify(result[1:]).decode('utf-8')

					katana.recurse(self, new_result)
					katana.locate_flags(self, new_result )
					katana.add_results(self, new_result )	

				except UnicodeDecodeError:
					# This won't decode right... must not be right!
					pass


			except UnicodeDecodeError:
				# This won't decode right... must not be right!
				pass

