from katana.unit import BaseUnit
from collections import Counter
import sys
import io
import argparse
from pwn import *
import os
from katana.units import crypto
from katana.units import NotApplicable
import string
import collections
from katana import units

class Unit(units.NotEnglishUnit):

	PROTECTED_RECURSE = True
	PRIORITY = 60
	ARGUMENTS = [
		{ 'name': 		'caesar_shift', 
		  'type': 		int, 
		  'default': 	-1, 
		  'required': 	False,
		  'help': 		'number to shift by for caesar cipher'
		},
	]

	# JOHN: This SHOULD be removed following the new unit argument restructure
	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--caesar-shift', default=-1, type=int, help='number to shift by for caesar cipher')

	def __init__(self, katana, target):
		super(Unit, self).__init__(katana, target)

		if target.is_url:
			raise NotApplicable('target is a URL')

		# DO NOT run this if the string does not contain any letters.
		try:
			with io.TextIOWrapper(self.target.stream, encoding='utf-8') as stream:
				for c in iter(lambda: stream.read(1), ''):
					if c in string.ascii_letters:
						# We found a letter -- that means we're good, we can run this unit.
						return
		except UnicodeDecodeError:
			raise NotApplicable("seemingly binary data")

		# We should only reach this if we did not return from that loop above.
		raise NotApplicable("no english letters")

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
				if idx != -1:
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
