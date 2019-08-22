"""

MD5 hash cracker. 

Currently, this is based off of a dictionary file that must be supplied with 
the ``dict`` argument or a singular ``password`` argument as a string. All 
this unit does is bruteforce, and that is very inefficient and time consuming.

A better implementation would be using a look-up table, but this likely needs
to be found online.

**Because hash cracking is usually a very niche thing to do, this unit 
considers any cracked hashes to be a flag!**

.. note::

	This implementation could be done better by using the method 
	@SmellyCharlie used: an online lookup table without a CAPTCHA. 

	https://github.com/SmellyCharlie/CrackTheFlag/blob/hash-checker/mods/crypto/md5.py

"""

from katana.units import NotApplicable 
from katana import units

from pwn import *
import subprocess
import hashlib
import mmap
import re

# Define a regular expression for what an MD5 Hash might look like.
MD5_HASH_REGEX = rb'([a-fA-F0-9]{32})'
MD5_HASH_REGEX = re.compile(MD5_HASH_REGEX, 
									re.MULTILINE | re.DOTALL | re.IGNORECASE)


class Unit(units.PrintableDataUnit):
	'''
	This unit pulls from a ``units.PrintableDataUnit``, as it only
	expects a string to be passed and it will then carve out what looks
	like an MD5 hash.
	'''

	def __init__(self, katana, target):
		super(Unit, self).__init__(katana, target)

		self.raw_target = self.target.raw
		if isinstance(self.raw_target, mmap.mmap):
			self.raw_target = self.target.raw.read()

		# Remove spaces and commas, if they happen to be in place.
		self.raw_target = self.raw_target.replace(b' ',b'').replace(b',',b'')
		self.matches = MD5_HASH_REGEX.findall(self.raw_target)

		if self.matches is None or self.matches == []:
			raise NotApplicable("no md5 hashes found")
		else:
			self.matches = [ x.decode('utf-8') for x in self.matches ]


	def enumerate(self, katana):
		'''
		Loop through the given ``password`` argument, or the ``dict`` file
		that is passed.
		'''

		# Check other passwords specified explicitly
		for p in katana.config['password']:
			yield p

		# Add all the passwords from the dictionary file
		if 'dict' in katana.config and katana.config['dict'] is not None:
			# CALEB: Possible race condition if two units use the 'dict' 
			#        argument for the same purpose...
			katana.config['dict'].seek(0)
			for line in katana.config['dict']:
				yield line.rstrip(b'\n')


	def evaluate(self, katana, case):
		'''
		MD5 hash the current case, check if it matches any hashes that were 
		detected, and if they do, return the plaintext **as a flag**.
		'''

		md5 = hashlib.md5()
		md5.update(case)
		new_hash = md5.hexdigest()

		for target in self.matches:
			if new_hash == target:
				katana.add_flag(case.decode('utf-8'))
				return