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
class Unit(units.BaseUnit):

	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--xor-key', type=str,
			help="key to use for XOR operations",
			default=None)

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		# JOHN: We actually DON'T want printable characters in this case!
		try:
			self.raw_target = target.stream.read().decode('utf-8').replace('\n','').replace('\t','')
		except UnicodeDecodeError:
			raise NotApplicable("unicode decode error")
		if self.raw_target.isprintable():
			raise NotApplicable("seemingly printable")
		else:
			if self.raw_target.count('\x00') > len(self.raw_target)/2:
				raise NotApplicable("more than half null-bytes")


	def evaluate(self, katana, case):
	
		if ( katana.config['xor_key'] ):
			key = [ katana.config['xor_key'] ]
		else:
			key = range(255)

		# key = case
		for k in key:
			try:
				result = xor(self.raw_target, k).decode('latin-1')

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