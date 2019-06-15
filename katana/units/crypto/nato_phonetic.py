from katana.unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import os
from katana.units import crypto
from katana.units import NotApplicable
from katana import units

import string
import collections

# Duplicate entries for things that may be represented 
# in multiple ways
nato_mappings = [
	"alfa", "bravo","charlie", 'delta', 'echo', 'foxtrot','golf',
	'hotel', 'india', 'juliett', 'juliet',  'kilo', 'lima', 'mike', 'november',
	'oscar', 'papa', 'quebec', 'romeo', 'sierra', 'tango', 'uniform',
	'victor', 'whiskey', 'x-ray', 'xray', 'yankee', 'zulu'
]

class Unit(units.PrintableDataUnit):
# class Unit(units.NotEnglishUnit):

	PRIORITY = 50

	def __init__(self, katana, target, keywords=[]):
		super(Unit, self).__init__(katana, target)

		try:
			self.raw_target = self.target.stream.read().decode('utf-8').lower()
			self.raw_target = self.raw_target.replace(' ', '')
		except UnicodeDecodeError:
			raise NotApplicable("seemingly binary data")


	def evaluate(self, katana, case):

		result = self.raw_target
		for mapping in nato_mappings:
			result = result.replace(mapping, mapping[0])

		katana.recurse(self, result)
		katana.add_results(self, result)