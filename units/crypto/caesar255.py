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

	def evaluate(self, katana, case):

		# These reads as bytes, so we don't need to use ord() later on
		contents = self.target.stream.read()

		for i in range(256):
			result = []
			for c in contents:
				result.append( chr((c + i) % 255) )

			result = ''.join(result)
			katana.recurse(self, result)
			katana.add_results(self, result)