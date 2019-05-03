from unit import BaseUnit
from collections import Counter
import sys
import io
import argparse
from pwn import *
import os
import units.crypto
from units import NotApplicable
import string
import collections
import utilities
import magic

class Unit(units.NotEnglishUnit):

	PROTECTED_RECURSE = True

	def evaluate(self, katana, case):

		# These reads as bytes, so we don't need to use ord() later on
		contents = self.target.stream.read()

		for i in range(256):
			result = []
			for c in contents:
				result.append( chr((c + i) % 255) )

			result = ''.join(result)

			# We want to know about this if it is printable!
			if utilities.isprintable(result):
				katana.recurse(self, result)
				katana.add_results(self, result)

			# if it's not printable, we might only want it if it is a file...
			else:
				magic_info = magic.from_buffer(result)
				if magic_info != 'data' \
				and 'UTF-8 Unicode text' not in magic_info \
				and 'International EBCDIC text' not in magic_info:
					print(magic_info, result)
					katana.recurse(self, result)
					katana.add_results(self, result)