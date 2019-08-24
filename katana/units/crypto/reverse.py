from katana.units import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import os
from katana.units import crypto
from katana import units


import string
import collections


# class Unit(units.PrintableDataUnit):
class Unit(units.NotEnglishUnit):

	PROTECTED_RECURSE = True
	PRIORITY = 70

	def evaluate(self, katana, case):

		result = self.target.raw[::-1]
		katana.locate_flags(self, result)
		katana.recurse(self, result)
		katana.add_results(self, result)

	

