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

def generate_table(alphabet = 'ABCDEFGHIKLMNOPQRSTUVWXYZ'):
	
	table = [[0] * 5 for row in range(5)]

	counter = 0
	for y in range(5):
		for x in range(5):
			table[x][y] = alphabet[counter]
			counter += 1
	return table

def decrypt(table, numbers):
	text = ''
	for index in range(0, len(numbers), 2):
		try:
			x = int(numbers[index]) - 1
			y = int(numbers[index + 1]) - 1
			text += table[y][x]
		except:
			# Not an issue if we can't find it... just don't add the text.
			pass
	return text

class Unit(units.PrintableDataUnit):

	PROTECTED_RECURSE = True
	PRIORITY = 40

	ARGUMENTS = [
		{ 'name': 		'polybius_alphabet', 
		  'type': 		str, 
		  'default': 	"ABCDEFGHIKLMNOPQRSTUVWXYZ", 
		  'required': 	False,
		  'help': 		'key to use for the polybius square cipher'
		},
	]

	def __init__( self, katana, target ):
		super(Unit, self).__init__(katana, target)

		no_spaces = target.stream.read().decode('utf-8').replace(' ','')
		if not no_spaces.isdecimal():
			raise NotApplicable("not just decimal numbers")

	# JOHN: This SHOULD be removed following the new unit argument restructure
	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--polybius-alphabet', type=str,
			help='key to use for the polybius square cipher',
			default='ABCDEFGHIKLMNOPQRSTUVWXYZ', required = False)

	# Shamelessly stolen from https://rot47.net/_py/rot47.txt
	
	def evaluate(self, katana, case):

		table = generate_table(katana.config['polybius_alphabet'])

		no_spaces = self.target.stream.read().decode('utf-8').replace(' ','')
		content = decrypt(table, no_spaces)
		
		katana.recurse(self,content)
		katana.locate_flags(self, content)
		katana.add_results(self, content)