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
import magic

BASE32_PATTERN = rb'[A-Z2-7+/]+={0,6}'
BASE32_REGEX = re.compile(BASE32_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)

class Unit(BaseUnit):

	PRIORITY = 60

	def __init__(self, katana, target):
		super(Unit, self).__init__(katana, target)

		if not self.target.is_printable:
			raise NotApplicable("not printable data")
			
		if self.target.is_english:
			raise NotApplicable("seemingly english")

		self.matches = BASE32_REGEX.findall(self.target.raw)
		if self.matches is None:
			raise NotApplicable("no base32 text found")

	def evaluate(self, katana, case):
		for match in self.matches:
			try:
				result = base64.b32decode(match)

				if utilities.isprintable(result):
					katana.recurse(self, result)
					katana.add_results(self, result)

				# if it's not printable, we might only want it if it is a file...
				else:
					magic_info = magic.from_buffer(result)
					if utilities.is_good_magic(magic_info):
						
						katana.add_results(self, result)

						filename, handle = katana.create_artifact(self, "decoded", mode='wb', create=True)
						handle.write(result)
						handle.close()
						katana.recurse(self, filename)
			
			except (UnicodeDecodeError, binascii.Error, ValueError):
				# This won't decode right... must not be right! Ignore it.				
				# I pass here because there might be more than one string to decode
				pass