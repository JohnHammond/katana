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

		return source[::-1]






	