from unit import BaseUnit
from collections import Counter
import sys
import io
import argparse
from pwn import *
import os
import units.crypto

import string
import collections

# class Unit(units.PrintableDataUnit):
class Unit(units.NotEnglishUnit):

	PROTECTED_RECURSE = True

	def evaluate(self, katana, case):

		with io.TextIOWrapper(self.target.stream, encoding='utf-8') as stream:
			result = stream.read()[::-1]
			katana.locate_flags(self, result)
			katana.recurse(self, result)
			katana.add_results(self, result)

	

