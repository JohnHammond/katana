from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.raw
import utilities
import os
from units import NotApplicable
import binascii

class Unit(units.raw.RawUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)
		print("we tryings", target)

		hex_characters = 'abcdef1234567890'
		if self.target.lower().startswith('0x'):
			self.target = self.target[2:]

		for character in self.target.lower():
			if character not in hex_characters:
				raise NotApplicable


	def evaluate(self, katana, case):
		# print("evaling")
		print(self.target)
		try:
			result = binascii.unhexlify(self.target).decode('utf-8')
			print(result)
		except binascii.Error:
			# This won't decode right... must not be right!
			return

		katana.recurse(self, result)

		katana.locate_flags( result )
		katana.add_result( self, 'result', result )
