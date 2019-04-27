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

class Unit(units.NotEnglishUnit):

	PROTECTED_RECURSE = True

	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--caesar-shift', default=-1, type=int, help='number to shift by for caesar cipher')

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		# DO NOT run this if the string does not contain any letters.
		with io.TextIOWrapper(self.target.stream, encoding='utf-8') as stream:
			for c in iter(lambda: stream.read(1), ''):
				if c in string.ascii_letters:
					return

		raise NotApplicable

	def caesar(self, rotate_string, number_to_rotate_by):
		upper = collections.deque(string.ascii_uppercase)
		lower = collections.deque(string.ascii_lowercase)

		upper.rotate(number_to_rotate_by)
		lower.rotate(number_to_rotate_by)

		upper = ''.join(list(upper))
		lower = ''.join(list(lower))

		return rotate_string.translate(rotate_string.maketrans(string.ascii_uppercase, upper)).translate(rotate_string.maketrans(string.ascii_lowercase, lower))

	def enumerate(self, katana):
		if katana.config['caesar_shift'] == -1:
			for shift in range(1, len(string.ascii_lowercase)):
				yield shift
		else:
			yield katana.config['caesar_shift']

	def evaluate(self, katana, case):

		result = []

		with io.TextIOWrapper(self.target.stream, encoding='utf-8') as stream:
			for c in iter(lambda: stream.read(1), ''):
				idx = string.ascii_uppercase.find(c)
				if c != -1:
					result.append(string.ascii_uppercase[(idx+case) % len(string.ascii_uppercase)])
				else:
					idx = string.ascii_lowercase.find(c)
					if idx != -1:
						result.append(string.ascii_lowercase[(idx+case) % len(string.ascii_lowercase)])
					else:
						result.append(c)

		result = ''.join(result)
		katana.recurse(self, result)
		katana.add_results(self, result)

