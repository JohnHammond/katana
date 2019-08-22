"""
Classic affine cipher.

This unit bruteforces the potential ``a`` and ``a`` values in the affine 
cipher equation based off of the length of the given ``affine_alphabet``.
Typically, this is just the English alphabet, so this means 1-26 for each.

You can of course modify these variables as given arguments.
"""

from katana.units import NotApplicable
from katana import units

from string import ascii_uppercase as alphabet
from Crypto.Util.number import inverse
from math import gcd
from pwn import *


BYTES_ALPHABET = bytes(alphabet, 'utf-8')


def affine(letter :str, a :int, b :int) -> bytes:
	'''
	Perform the affine cipher operation per letter with the given ``a`` and 
	``b`` values.
	'''

	if letter in BYTES_ALPHABET:
		return BYTES_ALPHABET[ (a*BYTES_ALPHABET.index(letter) + b) % \
								len(alphabet) ] 
	else:
		return letter


def decrypt( ciphertext :str, a :int = 1, b :int = 1, alphabet :str = alphabet) ->bytes:
	'''
	Decrypt potential ciphertext with the affine cipher.
	'''

	plaintext :list = []
	new_b :int = abs(b - len(alphabet))
	new_a :int = inverse( a, len(alphabet) )
	new_b :int  = (new_a * new_b) % len(alphabet)

	for letter in ciphertext.upper():
		plaintext.append( affine(letter, new_a, new_b) )

	return bytes(plaintext)


class Unit(units.NotEnglishUnit):
	'''
	This unit inherits from the :class:`katana.units.NotEnglishUnit` class, as
	we will likely only test for affine ciphers on data that is 
	printable but does not look English plaintext already.

	:data:`PROTECTED_RECURSE` is ``True`` for this unit, because we do not 
	want results that come from this unit being processed *yet again* by this 
	unit. That would make for pointless computation and potentially an 
	infinite loop.

	:data:`PRIORITY` is set to 65, as this has potential to be a long and 
	time-consuming operation. 
	'''

	PRIORITY = 65
	PROTECTED_RECURSE = True
	
	ARGUMENTS = [
		{ 'name': 		'affine_a', 
		  'type': 		int, 
		  'default': 	-1, 
		  'required': 	False,
		  'help': 		'coefficient a for affine cipher'
		},

		{ 'name': 		'affine_b', 
		  'type': 		int, 
		  'default': 	-1, 
		  'required': 	False,
		  'help': 		'coefficient b for affine cipher'
		},

		{ 'name': 		'affine_alphabet', 
		  'type': 		str, 
		  'default': 	"ABCDEFGHIJKLMNOPQRSTUVWXYZ", 
		  'required': 	False,
		  'help': 		'alphabet for affine cipher'
		},
	]


	def __init__(self, katana, target):
		'''
		In the constructor we ensure all of the data in the given target is 
		printable.
		'''
		super(Unit, self).__init__(katana, target)

		# We won't have non-printable characters in an affine cipher...
		if not self.target.is_printable:
			raise NotApplicable("not printable characters")
	

	def enumerate(self, katana):
		'''
		Enumerate all the potential A and B values for the 
		affine cipher if one is not supplied (1-26).
		'''

		if ( katana.config['affine_a'] == -1 and \
			 katana.config['affine_b'] == -1 ):
			for a in range(len(katana.config['affine_alphabet'])):
				for b in range(len(katana.config['affine_alphabet'])):
					if gcd(a, len(katana.config['affine_alphabet'])):
						yield (a, b)

		elif ( katana.config['affine_a'] != -1 and \
			   katana.config['affine_b'] == -1 ):
			for b in range(len(katana.config['affine_alphabet'])):
				if gcd(a, len(katana.config['affine_alphabet'])):
					yield (katana.config['affine_a'] % \
						   len(katana.config['affine_alphabet']), b)

		elif ( katana.config['affine_b'] != -1 and \
			   katana.config['affine_a'] == -1 ):
			for a in range(len(katana.config['affine_alphabet'])):
				if gcd(a, len(katana.config['affine_alphabet'])):
					yield (a, katana.config['affine_b'] % \
						   len(katana.config['affine_alphabet']))
		else:
			if ( katana.config['affine_a'] != -1 and \
				 katana.config['affine_b'] != -1 ):
				if gcd(a, len(katana.config['affine_alphabet'])):
					yield katana.config['affine_a'], katana.config['affine_b']


	def evaluate(self, katana, case):
		'''
		Decrypt the target with the given ``a`` and ``b`` values, and 
		add and recurse on each result.
		'''
		a, b = case
		raw_target = self.target.stream.read()
		
		plaintext = decrypt( raw_target, a, b, 
							 katana.config['affine_alphabet'] )
		
		if plaintext != raw_target:
			katana.recurse(self, plaintext)
			katana.add_results(self, plaintext)
	
