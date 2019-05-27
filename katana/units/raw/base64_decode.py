from katana.unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
from katana.units import raw
from katana import utilities
import os
import re
from katana.units import NotApplicable
from katana import units
import traceback
import base64
import binascii
import magic
from katana import units

BASE64_PATTERN = rb'[a-zA-Z0-9+/]+={0,2}'
BASE64_REGEX = re.compile(BASE64_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)

class Unit(BaseUnit):

	PRIORITY = 25

	def __init__(self, katana, target):
		super(Unit, self).__init__(katana, target)

		if not self.target.is_printable:
			raise NotApplicable("not printable data")

		if self.target.is_english:
			raise NotApplicable("seemingly english")

		self.matches = BASE64_REGEX.findall(self.target.raw)
		if self.matches is None:
			raise NotApplicable("no base64 text found")

	def evaluate(self, katana, case):
		for match in self.matches:
			try:
				decoded = base64.b64decode(match)

				# We want to know about this if it is printable!
				if utilities.isprintable(decoded):
					katana.recurse(self, decoded)
					katana.add_results(self, decoded)

				# if it's not printable, we might only want it if it is a file...
				else:
					magic_info = magic.from_buffer(decoded)
					if utilities.is_good_magic(magic_info):

						
						katana.add_results(self, decoded)

						filename, handle = katana.create_artifact(self, "decoded", mode='wb', create=True)
						handle.write(decoded)
						handle.close()
						katana.recurse(self, filename)
						if 'image' in magic_info:
							print(magic_info, filename)
				
			except (UnicodeDecodeError, binascii.Error, ValueError):
				
				# This won't decode right... must not be right! Ignore it.				
				# I pass here because there might be more than one string to decode
				pass
