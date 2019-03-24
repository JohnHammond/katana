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
		parser.add_argument('--shift', default=-1, type=int, help='number to shift by for caesar cipher')


	def caesar(self, rotate_string, number_to_rotate_by):
		upper = collections.deque(string.ascii_uppercase)
		lower = collections.deque(string.ascii_lowercase)

		upper.rotate(number_to_rotate_by)
		lower.rotate(number_to_rotate_by)

		upper = ''.join(list(upper))
		lower = ''.join(list(lower))

		return rotate_string.translate(rotate_string.maketrans(string.ascii_uppercase, upper)).translate(rotate_string.maketrans(string.ascii_lowercase, lower))

	def evaluate(self, target):

		if os.path.isfile(target):
			try:
				source = open(target).read()

			# If this is a binary object, we probably can't read it...
			except UnicodeDecodeError:
				return None
		else:
			source = target

		if ( self.config['shift'] == -1 ):
			results = []

			for shift_value in range(len(string.ascii_lowercase)):
				results.append( self.caesar(source, shift_value) )

			return results
		else:
			return self.caesar(source, self.config['shift'])






	