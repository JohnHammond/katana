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
import re
from units import NotApplicable
import units
import traceback
import base64
import binascii

class Unit(units.FileOrDataUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		PATTERN = re.compile( '[a-zA-Z0-9+/]+={0,2}', flags=re.MULTILINE | \
								re.DOTALL | re.IGNORECASE  )
		base64_result = PATTERN.findall(str(self.target))

		if base64_result is None or base64_result == []:
			raise NotApplicable()
		else:
			self.base64_result = base64_result


	def evaluate(self, katana, case):
		
		for result in self.base64_result:
			try:
				decoded = base64.b64decode(result).decode('ascii')

				katana.recurse(self, decoded)

				katana.locate_flags(self, decoded )
				katana.add_results( self, decoded )
			
			except (UnicodeDecodeError, binascii.Error):
				# This won't decode right... must not be right! Ignore it.				
				pass