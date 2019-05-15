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
import traceback
from math import gcd

from string import ascii_uppercase as alphabet
from Crypto.Util.number import inverse

BYTES_ALPHABET = bytes(alphabet, 'utf-8')

def affine(letter, a, b):
	if letter in BYTES_ALPHABET:
		return BYTES_ALPHABET[ (a*BYTES_ALPHABET.index(letter) + b) % len(alphabet) ] 
	else:
		return letter

def decrypt( ciphertext, a = 1, b = 1, alphabet = alphabet):

	plaintext = []
	new_b = abs(b - len(alphabet))
	new_a = inverse( a, len(alphabet) )
	new_b = (new_a * new_b) % len(alphabet)

	for letter in ciphertext.upper():
		plaintext.append( affine(letter, new_a, new_b) )

	return bytes(plaintext)

# class Unit(units.PrintableDataUnit):
class Unit(units.NotEnglishUnit):

	PRIORITY = 65

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		# We won't have non-printable characters in an affine cipher...
		if not self.target.is_printable:
			raise NotApplicable("not printable characters")
	
	PROTECTED_RECURSE = True

	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--affine-a', default=-1, type=int, help='coefficient a for affine cipher')
		parser.add_argument('--affine-b', default=-1, type=int, help='coefficient b for affine cipher')
		parser.add_argument('--affine-alphabet', default=alphabet, type=str, help='alphabet for affine cipher')

	# JOHN: We should enumerate all the potential iterations of this code.
	def enumerate(self, katana):

		if ( katana.config['affine_a'] == -1 and katana.config['affine_b'] == -1 ):
			for a in range(len(katana.config['affine_alphabet'])):
				for b in range(len(katana.config['affine_alphabet'])):
					if gcd(a, len(katana.config['affine_alphabet'])):
						yield (a, b)
		elif ( katana.config['affine_a'] != -1 and katana.config['affine_b'] == -1 ):
			for b in range(len(katana.config['affine_alphabet'])):
				if gcd(a, len(katana.config['affine_alphabet'])):
					yield (katana.config['affine_a'] % len(katana.config['affine_alphabet']), b)
		elif ( katana.config['affine_b'] != -1 and katana.config['affine_a'] == -1 ):
			for a in range(len(katana.config['affine_alphabet'])):
				if gcd(a, len(katana.config['affine_alphabet'])):
					yield (a, katana.config['affine_b'] % len(katana.config['affine_alphabet']))
		else:
			if ( katana.config['affine_a'] != -1 and katana.config['affine_b'] != -1 ):
				if gcd(a, len(katana.config['affine_alphabet'])):
					yield katana.config['affine_a'], katana.config['affine_b']

	def evaluate(self, katana, case):
		a, b = case
		raw_target = self.target.stream.read()
		
		plaintext = decrypt( raw_target, a, b, katana.config['affine_alphabet'] )
		if plaintext != raw_target:
			katana.recurse(self, plaintext)
			katana.add_results(self, plaintext)
	
