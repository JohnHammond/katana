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

BASE64_PATTERN = rb'[a-zA-Z0-9+/]+={0,2}'
BASE64_REGEX = re.compile(BASE64_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)

class Unit(BaseUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

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

				katana.recurse(self, decoded)
				katana.add_results(self, decoded)
			
			except (UnicodeDecodeError, binascii.Error, ValueError):
				# This won't decode right... must not be right! Ignore it.				
				# I pass here because there might be more than one string to decode
				pass
