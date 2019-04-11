from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import os
import units.crypto

import string
import collections


class Unit(units.crypto.CryptoUnit):

	@classmethod
	def prepare_parser(cls, config, parser):
		# Nothing to do in this case...
		pass		


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

	def evaluate(self, target):

		if os.path.isfile(target):
			try:
				source = open(target).read()

			# If this is a binary object, we probably can't read it...
			except UnicodeDecodeError:
				return None
		else:
			source = target

		content = self.do_rot47(source)
		self.find_flags(content)

		return content






	