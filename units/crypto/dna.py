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
# class Unit(units.NotEnglishUnit):

	PRIORITY = 50

	def __init__(self, katana, parent, target, keywords=[]):
		super(Unit, self).__init__(katana, parent, target)

		self.raw_target = self.target.stream.read().decode('utf-8').upper()
		if not all(c in "ACGTU" for c in self.raw_target) or \
			len(self.raw_target.upper().replace(" ", "").replace("U", "T")) % 3 != 0:

			raise NotApplicable("more than DNA letters (A, T, C, G) found")

	def evaluate(self, katana, case):

		all_characters = string.ascii_lowercase + string.ascii_uppercase +string.digits[1:10] + "0 ."
		result = []

		for codon in [dna.upper().replace(" ", "").replace("U", "T")[i:i+3] for i in range(0, len(dna.upper().replace(" ", "").replace("U", "T")), 3)]:
			index = 0
			index += (0 if codon[2] == 'A' else (1 if codon[2] == 'C' else (2 if codon[2] == 'G' else 3)))
			index += (0 if codon[1] == 'A' else (4 if codon[1] == 'C' else (8 if codon[1] == 'G' else 12)))
			index += (0 if codon[0] == 'A' else (16 if codon[0] == 'C' else (32 if codon[0] == 'G' else 48)))
			result.append(all_characters[index])

			
		result = ''.join(result)
		katana.locate_flags(self, result)
		katana.recurse(self, result)
		katana.add_results(self, result)

	

