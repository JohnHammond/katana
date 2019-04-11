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
		pass

	def evaluate(self, target):

		if os.path.isfile(target):
			try:
				source = open(target).read()
			# If this is a binary object, we probably can't read it...
			except UnicodeDecodeError:
				return None
		else:
			source = target

		new_string = []
		reverse_upper = string.ascii_uppercase[::-1]
		reverse_lower = string.ascii_lowercase[::-1]
		for character in source:
			if character in string.ascii_uppercase:
				new_string.append(reverse_upper[string.ascii_uppercase.index(character)])
			elif character in string.ascii_lowercase:
				new_string.append(reverse_lower[string.ascii_lowercase.index(character)])
			else:
				new_string.append(character)

		return ''.join(new_string)