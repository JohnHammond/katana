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

class Unit(BaseUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		if not self.target.is_printable:
			raise NotApplicable("not printable data")

		if self.target.is_english:
			raise NotApplicable("seemingly english")

	def evaluate(self, katana, case):
		try:
			result = base64.a85decode(self.target.raw)

			if utilities.isprintable(result):
				katana.recurse(self, result)
				katana.add_results(self, result)

			# if it's not printable, we might only want it if it is a file...
			else:
				magic_info = magic.from_buffer(result)
				if magic_info != 'data':
					
					katana.add_results(self, result)

					filename, handle = katana.create_artifact(self, "decoded", mode='wb', create=True)
					handle.write(result)
					handle.close()
					katana.recurse(self, filename)
		
		except (UnicodeDecodeError, binascii.Error, ValueError):
			# This won't decode right... must not be right! Ignore it.
			# I return here because we are only trying to decode ONE string
			return