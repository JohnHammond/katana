from unit import BaseUnit
from collections import Counter
import sys
import io
import argparse
from pwn import *
import os
import units.crypto
from units import NotApplicable
import string
import collections
import primefac
from Crypto.Util.number import inverse
import traceback
import binascii
import utilities

def parse_int(given):
	found = -1
	if not utilities.isprintable(given):
		given = binascii.hexlify(given)
	if given == '':
		return found
	try:
		found = int(given)
	except ValueError:
		found = int(given, 16)
	return found


class Unit(units.NotEnglishUnit):

	PROTECTED_RECURSE = True
	PRIORITY = 60

	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--rsa-e', default="", type=str, help='exponent value for RSA cryptography')
		parser.add_argument('--rsa-n', default="", type=str, help='modulus value for RSA cryptography')
		parser.add_argument('--rsa-q', default="", type=str, help='q factor for RSA cryptography')
		parser.add_argument('--rsa-p', default="", type=str, help='p factor for RSA cryptography')
		parser.add_argument('--rsa-d', default="", type=str, help='d value for RSA cryptography')

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		if target.is_url:
			raise NotApplicable('target is a URL')

		self.c = parse_int(self.target.raw)
		if self.c == -1:
			return NotApplicable('could not determine ciphertext')
		
	# def enumerate(self, katana):
	# 	if katana.config['caesar_shift'] == -1:
	# 		for shift in range(1, len(string.ascii_lowercase)):
	# 			yield shift
	# 	else:
	# 		yield katana.config['caesar_shift']

	def evaluate(self, katana, case):

		c = self.c
		e = parse_int(katana.config['rsa_e'])
		n = parse_int(katana.config['rsa_n'])
		q = parse_int(katana.config['rsa_q'])
		p = parse_int(katana.config['rsa_p'])
		d = parse_int(katana.config['rsa_d'])

		# If e is not given, assume it is the standard 65537
		if e == -1:
			e = 0x10001


		# if n is given but p and q are not, try TO factor n.
		if p == -1 and q == -1 and n != -1:
			factors = list([ int(x) for x in primefac.factorint(n)])
			if len(factors) == 2:
				p, q = factors
			else:
				raise NotImplemented("We need support for multifactor RSA!")
			pass

		# if n is NOT given but p and q are, multiply them to get n
		if n == -1 and p != -1 and q != -1:
			n = p * q
		
		phi = ( p - 1 )* ( q - 1 )

		# If d is not supplied (which is normal) calculate it
		if d == -1:
			d = inverse(e,phi)
		
		m = pow( c, d, n )
		try:
			result = binascii.unhexlify(hex(m)[2:].rstrip('L'))
		except binascii.Error:
			result = binascii.unhexlify(str('0'+hex(m)[2:].rstrip('L')))
		
		katana.add_results(self, result)
		katana.recurse(self, result)
	