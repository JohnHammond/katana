import re
import argparse
from pwn import *
import subprocess
import hashlib
import mmap

from katana.units import NotApplicable 
from katana.unit import BaseUnit
from katana import units


MD5_HASH_REGEX = rb'([a-fA-F0-9]{32})'
MD5_HASH_REGEX = re.compile(MD5_HASH_REGEX, re.MULTILINE | re.DOTALL | re.IGNORECASE)

class Unit(units.PrintableDataUnit):


	def __init__(self, katana, target):
		super(Unit, self).__init__(katana, target)

		# Check if there is hex in it, remove spaces and commas
		if isinstance(self.target.raw, mmap.mmap):
			raise NotApplicable("should not see mmap for md5 strings")

		self.raw_target = self.target.raw.replace(b' ',b'').replace(b',',b'')
		self.matches = MD5_HASH_REGEX.findall(self.raw_target)

		if self.matches is None or self.matches == []:
			raise NotApplicable("no md5 hashes found")
		else:
			self.matches = [ x.decode('utf-8') for x in self.matches ]


	def enumerate(self, katana):
		# The default is to check an empty password
		yield b''

		# Check other passwords specified explicitly
		for p in katana.config['password']:
			yield p

		# Add all the passwords from the dictionary file
		if 'dict' in katana.config and katana.config['dict'] is not None:
			# CALEB: Possible race condition if two units use the 'dict' argument for the same purpose...
			katana.config['dict'].seek(0)
			for line in katana.config['dict']:
				yield line.rstrip(b'\n')

	def evaluate(self, katana, case):

		md5 = hashlib.md5()
		md5.update(case)
		new_hash = md5.hexdigest()

		for target in self.matches:
			if new_hash == target:
				katana.add_flag(case.decode('utf-8'))
				return 
		