from unit import BaseUnit
from units import NotEnglishUnit, NotApplicable
from units.esoteric.brainfuck import evaluate_brainfuck

from collections import Counter
from io import StringIO
from pwn import *

import argparse
import os
import threading
import time
import traceback
import sys

translate_table = {
	"Ook. Ook?": ">",
	"Ook? Ook.": "<",
	"Ook. Ook.": "+",
	"Ook! Ook!": "-",
	"Ook! Ook.": ".",
	"Ook. Ook!": ",",
	"Ook! Ook?": "[",
	"Ook? Ook!": "]",
}

def evaluate_ook(code, input_file, timeout = 1):
	if "\n" in code:
		code = code.replace("\n", " ")
	
	code = code.replace(" ", "")

	if len(code) % 4 != 0 and len(code) % 2 != 0:
		return None

	bf_code = ""

	for idx in range(0, len(code), 8):
		bf_code += translate_table[f"{code[idx:idx+4]} {code[idx+4:idx+8]}"]

	return evaluate_brainfuck(bf_code, input_file, timeout)


class Unit(NotEnglishUnit):

	PRIORITY = 60

	ARGUMENTS = [
		{ 'name': 		'ook_input', 
		  'type': 		str, 
		  'default': 	None, 
		  'required': 	False,
		  'help': 		'file to be read as input to ook program'
		},

		{ 'name': 		'ook_timeout', 
		  'type': 		int, 
		  'default': 	1, 
		  'required': 	False,
		  'help': 		'timeout in seconds to run ook program'
		},
	]

	def __init__(self, katana, parent, target, keywords=[]):
		super(Unit, self).__init__(katana, parent, target)

		try:
			self.raw_target=self.target.stream.read().decode('utf-8').lower()
			if ( self.raw_target.count('ook') < 10 ):
				raise NotApplicable("less than 10 occurences of 'ook'")
		except UnicodeDecodeError:
			raise NotApplicable("unicode error, unlikely ook syntax")

	# JOHN: This SHOULD be removed following the new unit argument restructure
	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--ook-input',  action='store_true', default=None, help='file to be read as input to ook program')
		parser.add_argument('--ook-timeout',  action='store_true', default=1, help='timeout in seconds to run ook program')

	def evaluate(self, katana, case):

		try:
			output = evaluate_ook(self.target.stream.read().decode('utf-8'), 
								  katana.config['ook_input'], 
								  katana.config['ook_timeout'])

		except (ValueError, TypeError):
			traceback.print_exc()
			return None

		if output:
			katana.recurse(self, output)
			katana.add_results(self, output)