from unit import BaseUnit
from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.raw
import units
import utilities
import os
from units import NotApplicable
import binascii
import traceback

# DO NOT recurse this... it will bottleneck Katana
PROTECTED_RECURSE = True

# JOHN: I inherit from FileOrData unit, because this may very well not be printable text!
class Unit(units.FileOrDataUnit):

	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--xor-key', type=str,
			help="key to use for XOR operations",
			default=None)

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		# JOHN: We actually DON'T want printable characters in this case!
		if self.target.replace('\n','').replace('\t','').isprintable():
			raise NotApplicable
		else:
			if self.target.count('\x00') > len(self.target)/2:
				raise NotApplicable

	def evaluate(self, katana, case):
	
		key = case
		try:
			result = xor(self.target, key).decode('latin-1')

			if result.isprintable():
				# JOHN: Recursing on this dangerous, admittedly... 
				#       But sometimes it must be done (!!??!?!)
				# katana.recurse(self, result)
				katana.add_results(self, result)
				# If we find the flag, STOP doing this!!
				if katana.locate_flags(self, result):
					self.completed = True

			else:
				return None


		# If this fails, it's probably not binary we can deal with...
		except (UnicodeDecodeError, binascii.Error):
			return None

	def evaluate(self, katana, case):
	
		if ( katana.config['xor_key'] ):
			key = [ katana.config['xor_key'] ]
		else:
			key = range(255)

		# key = case
		for k in key:
			try:
				result = xor(self.target, k).decode('latin-1')

				if result.isprintable():
					# JOHN: Recursing on this dangerous, admittedly... 
					#       But sometimes it must be done (!!??!?!)
					# katana.recurse(self, result)
					katana.add_results(self, result)
					# If we find the flag, STOP doing this!!
					if katana.locate_flags(self, result):
						self.completed = True

				else:
					return None

			# If this fails, it's probably not binary we can deal with...
			except (UnicodeDecodeError, binascii.Error):
				return None