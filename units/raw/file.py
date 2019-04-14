from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import os
import units.raw
import utilities
import magic
from units import NotApplicable

class Unit(units.FileUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)
		# We can only handle this if it is a file!
		if not os.path.isfile(target):
			raise NotApplicable()

	def evaluate(self, katana, case):

		# Look for flags, if we found them...
		response = magic.from_file(self.target)
		
		# JOHN: We have the issue of recursing on this output, and potentially
		#       caesar ciphering, reversing, atbashing, etc...
		#       ... So, we do NOT recurse because we PROBABLY do not have a flag here.
		# katana.recurse(self, response)

		katana.locate_flags(self, response)
		katana.add_results(self, response)
