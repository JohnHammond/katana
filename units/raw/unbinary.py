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

		try:
			raw = ''.join([ chr(int(x,2)) for x in self.binary_result])

			# JOHN: The question of whether or not we should only handle
			#       printables came up when we worked on XOR...
			#       ... but we left it raw, because what if it uncovers a file?
			# if raw.replace('\n', '').isprintable():
			katana.recurse(self, raw)
			katana.locate_flags(self, raw )
			katana.add_results(self, raw )

		except:
			pass

		for result in self.binary_result:
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
			katana.locate_flags(self, new_result )
			katana.add_results(self, new_result )