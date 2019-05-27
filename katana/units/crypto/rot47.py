from katana.unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import os
from katana.units import crypto
from katana import units

import string
import collections


# class Unit(units.PrintableDataUnit):
class Unit(units.NotEnglishAndPrintableUnit):

	PROTECTED_RECURSE = True
	PRIORITY = 45

	def __init__(self, katana, target, keywords=[]):
		super(Unit, self).__init__(katana, target)

		try:
			self.raw_target = self.target.stream.read().decode('utf-8')
		except UnicodeDecodeError:
			raise units.NotApplicable("unicode error, unlikely usable cryptogram")

	# Shamelessly stolen from https://rot47.net/_py/rot47.txt
	def do_rot47(self, s):
		x = []
		for i in range(len(s)):
			j = ord(s[i])
			if j >= 33 and j <= 126:
				x.append(chr(33 + ((j + 14) % 94)))
			else:
				x.append(s[i])
		return ''.join(x)

	def evaluate(self, katana, case):

		content = self.do_rot47(self.raw_target)
		katana.recurse(self,content)
		katana.locate_flags(self, content)
		katana.add_results(self, content)
