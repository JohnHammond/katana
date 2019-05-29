from katana.unit import BaseUnit
from collections import Counter
import sys
import io
import argparse
from pwn import *
import os
from katana.units import crypto
from katana.units import NotApplicable
import string
import collections
import primefac
from Crypto.Util.number import inverse
import traceback
import binascii
from katana import utilities
from katana import units

def find_variables( text ):

	matches = [
		'N',
		'exponent',
		'ciphertext',
		'message',
		'd',
		'p',
		'phi',
		'q',
		'totient',
	]
	for m in matches:
		match = re.search(r'({0})({1})?\s*[=:]\s*(.*)'.format(m[0], m[1:]), text, re.IGNORECASE)

		if match:
			letter = match.groups()[0].lower()
			middle = match.groups()[1]
			value = match.groups()[-1]
			
			if middle:
				middle = middle.lower()
				if letter.startswith('m') and middle.startswith('odulus'):
					letter = 'n'
				if letter.startswith('p') and middle.startswith('hi'):
					letter = 'phi'

			yield letter, value

def parse_int(given):
	found = -1
	if not utilities.isprintable(given):
		given = binascii.hexlify(given)
	if given == '':
		return found
	try:
		found = int(given)
	except ValueError:
		try:
			found = int(given, 16)
		except (ValueError, TypeError):
			pass
	return found


class Unit(units.NotEnglishUnit):

	PROTECTED_RECURSE = True
	PRIORITY = 60

	ARGUMENTS = [
		{ 'name': 		'rsa_e', 
		  'type': 		str, 
		  'default': 	"", 
		  'required': 	False,
		  'help': 		'exponent value for RSA cryptography'
		},

		{ 'name': 		'rsa_n', 
		  'type': 		str, 
		  'default': 	"", 
		  'required': 	False,
		  'help': 		'modulus value for RSA cryptography'
		},

		{ 'name': 		'rsa_q', 
		  'type': 		str, 
		  'default': 	"", 
		  'required': 	False,
		  'help': 		'q factor for RSA cryptography'
		},

		{ 'name': 		'rsa_p', 
		  'type': 		str, 
		  'default': 	"", 
		  'required': 	False,
		  'help': 		'p factor for RSA cryptography'
		},

		{ 'name': 		'rsa_d', 
		  'type': 		str, 
		  'default': 	"", 
		  'required': 	False,
		  'help': 		'd value for RSA cryptography'
		},

		{ 'name': 		'rsa_c', 
		  'type': 		str, 
		  'default': 	"", 
		  'required': 	False,
		  'help': 		'c value for RSA cryptography'
		},
	]

	def __init__(self, katana, target):
		super(Unit, self).__init__(katana, target)

		if target.is_url:
			raise NotApplicable('target is a URL')

		

		# Extract all the variables out from the arguments, if they are supplied.
		# Since we need a ciphertext and that will be tested later, leave that empty.
		self.c = -1
		self.e = parse_int(katana.config['rsa_e'])
		self.n = parse_int(katana.config['rsa_n'])
		self.q = parse_int(katana.config['rsa_q'])
		self.p = parse_int(katana.config['rsa_p'])
		self.d = parse_int(katana.config['rsa_d'])

		if katana.config['rsa_c']:
			try:
				handle = open(katana.config['rsa_c'], 'rb')
				is_file = True
			except OSError:
				is_file = False

			if is_file:
				ciphertext_data = handle.read()
				self.c = parse_int(ciphertext_data)
				if self.c == -1:
					raise NotApplicable('could not determine ciphertext from file')
			else:
				self.c = parse_int(katana.config['rsa_c'])

		if self.target.is_file:
			try:
				self.raw_target = self.target.stream.read().decode('utf-8')
			except UnicodeDecodeError:
				raise NotApplicable('unicode error, must not be potential ciphertext')
				
			for finding in find_variables(self.raw_target):
				if finding:
					vars(self)[finding[0]] = parse_int(finding[1])

		if self.c == -1:
			raise NotApplicable("no ciphertext determined")

	def evaluate(self, katana, case):



		# If e is not given, assume it is the standard 65537
		if self.e == -1:
			self.e = 0x10001


		# if n is given but p and q are not, try TO factor n.
		if self.p == -1 and self.q == -1 and self.n != -1:
			factors = list([ int(x) for x in primefac.factorint(self.n)])
			if len(factors) == 2:
				self.p, self.q = factors
			else:
				raise NotImplemented("We need support for multifactor RSA!")
			pass

		# if n is NOT given but p and q are, multiply them to get n
		if self.n == -1 and self.p != -1 and self.q != -1:
			self.n = self.p * self.q
		
		self.phi = ( self.p - 1 )* ( self.q - 1 )

		# If d is not supplied (which is normal) calculate it
		if self.d == -1:
			self.d = inverse(self.e,self.phi)
		
		self.m = pow( self.c, self.d,self.n )
		try:
			result = binascii.unhexlify(hex(self.m)[2:].rstrip('L'))
		except binascii.Error:
			result = binascii.unhexlify(str('0'+hex(self.m)[2:].rstrip('L')))
		
		katana.add_results(self, result)
		katana.recurse(self, result)
	
