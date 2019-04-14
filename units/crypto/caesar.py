from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import os
import units.crypto
from units import NotApplicable
import string
import collections


class Unit(units.PrintableDataUnit):

	PROTECTED_RECURSE = True

	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--caesar-shift', default=-1, type=int, help='number to shift by for caesar cipher')

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		odd_characters = 0
		for c in target:
			if c not in string.ascii_uppercase + string.ascii_lowercase:
				odd_characters += 1

		if odd_characters == len(target):
			raise NotApplicable


	def caesar(self, rotate_string, number_to_rotate_by):
		upper = collections.deque(string.ascii_uppercase)
		lower = collections.deque(string.ascii_lowercase)

		upper.rotate(number_to_rotate_by)
		lower.rotate(number_to_rotate_by)

		upper = ''.join(list(upper))
		lower = ''.join(list(lower))

		return rotate_string.translate(rotate_string.maketrans(string.ascii_uppercase, upper)).translate(rotate_string.maketrans(string.ascii_lowercase, lower))

	def evaluate(self, katana, case):

		if ( katana.config['caesar_shift'] == -1 ):
			results = { }

			for shift_value in range(len(string.ascii_lowercase)):
				results[shift_value] = self.caesar(self.target, shift_value)
				katana.recurse(self, results[shift_value])
				katana.locate_flags(self, results[shift_value])

		else:
			results = self.caesar(source, katana.config['caesar_shift'])
			katana.recurse(self, results)
			katana.locate_flags(self, results)

		katana.add_results(self, results)






	
