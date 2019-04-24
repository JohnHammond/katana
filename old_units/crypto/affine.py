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
import traceback
from math import gcd

from string import ascii_uppercase as alphabet
from Crypto.Util.number import inverse

def affine(letter, a, b):
	if letter in alphabet:
		return alphabet[ (a*alphabet.index(letter) + b) % len(alphabet) ] 
	else:
		return letter

# JOHN: This is not needed for the purposes of Katana, but I have left it here
#       for preservation's sake
# def encrypt( plaintext, a = 1, b = 1 ):
# 	ciphertext = []
# 	for letter in plaintext:
# 		ciphertext.append( affine(letter.upper(), a, b) )

# 	return "".join(ciphertext)

def decrypt( ciphertext, a = 1, b = 1, alphabet = alphabet):

	plaintext = []
	new_b = abs(b - len(alphabet))
	new_a = inverse( a, len(alphabet) )
	new_b = (new_a * new_b) % len(alphabet)

	for letter in ciphertext:
		plaintext.append( affine(letter.upper(), new_a, new_b) )

	return "".join(plaintext)

# class Unit(units.PrintableDataUnit):
class Unit(units.NotEnglishUnit):

	# JOHN: We do not need the constructor, because we will inherit the parent!
	
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
		try:
			plaintext = decrypt( self.target, a, b, katana.config['affine_alphabet'] )
			if plaintext != self.target.upper():
				katana.recurse(self, plaintext)
				katana.locate_flags(self, plaintext)
				katana.add_results(self, plaintext)
		except Exception:
			# JOHN: I don't know if or when or why this will error, but when IT DOES... we 
			#       we should see it so we can support it.
			traceback.print_exc()