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

# JOHN: I do NOT use a dictionary for this, because the sorting and order would 
#       get all messed up, Instead, a force an ordered list.
t9_mappings = [
	('7777','s'),
	('9999','z'),
	('222','c'),
	('111','@'),
	('333','f'),
	('444','i'),
	('555','l'),
	('666','o'),
	('777','r'),
	('888','v'),
	('999','y'),
	('22','b'),
	('33','e'),
	('44','h'),
	('55','k'),
	('66','n'),
	('77','q'),
	('88','u'),
	('99','x'),
	('11',','),
	('2','a'),
	('3','d'),
	('4','g'),
	('5','j'),
	('6','m'),
	('7','p'),
	('8','t'),
	('9','w'),
	('1','_'),
	('0',' '),
	('*',' ')
]

class Unit(units.PrintableDataUnit):
# class Unit(units.NotEnglishUnit):

	PRIORITY = 50

	def __init__(self, katana, target, keywords=[]):
		super(Unit, self).__init__(katana, target)

		self.raw_target = self.target.stream.read().decode('utf-8').upper()

		# JOHN: Just do a cursory test if there are any numbers to begin with
		try:
			with io.TextIOWrapper(self.target.stream, encoding='utf-8') as stream:
				for c in iter(lambda: stream.read(1), ''):
					if c in "1234567890*":
						# This should be a good candidate. We can
						# completely break out of this loop and evaluate
						return
		except UnicodeDecodeError:
			raise NotApplicable("seemingly binary data")
	
		# If we don't return earlier, then we know we are a bad candidate!	
		raise NotApplicable("no phone keypad digits found at all")


	def evaluate(self, katana, case):

		result = self.raw_target
		for mapping in t9_mappings:
			result = result.replace(mapping[0], mapping[1])

		result = ''.join(result)

		# Quickly hotswap spaces
		result = result.replace('  ',"@@DELIM@@")
		result = result.replace(' ',"")
		result = result.replace("@@DELIM@@", " ")

		katana.recurse(self, result)
		katana.add_results(self, result)