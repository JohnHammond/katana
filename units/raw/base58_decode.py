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
import binascii
import base58
import magic

BASE58_PATTERN = rb'[a-zA-Z0-9+/]+'
BASE58_REGEX = re.compile(BASE58_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)

class Unit(BaseUnit):

	PRIORITY = 60

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		if not self.target.is_printable:
			raise NotApplicable("not printable data")

		if self.target.is_english:
			raise NotApplicable("seemingly english")

		self.matches = BASE58_REGEX.findall(self.target.raw)
		if self.matches is None:
			raise NotApplicable("no base58 text found")

	def evaluate(self, katana, case):
		for match in self.matches:
			try:
				result = base58.b58decode(match)

				# We want to know about this if it is printable!
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

			# Base58 can also include error checking... so try to "check" as well!
			# -----------------------------------------------------------------------

			try:
				result = base58.b58decode_check(match)

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