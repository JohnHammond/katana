from katana.unit import BaseUnit
from katana.units import NotEnglishUnit, NotApplicable
from katana.units.esoteric.brainfuck import evaluate_brainfuck
from katana import units

from collections import Counter
from io import StringIO
from pwn import *

import argparse
import os
import threading
import time
import traceback
import sys

OOK_PATTERN = rb'((Ook)?(\.|!|\?))'
OOK_REGEX = re.compile(OOK_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)

# translate_table = {
# 	"Ook. Ook?": ">",
# 	"Ook? Ook.": "<",
# 	"Ook. Ook.": "+",
# 	"Ook! Ook!": "-",
# 	"Ook! Ook.": ".",
# 	"Ook. Ook!": ",",
# 	"Ook! Ook?": "[",
# 	"Ook? Ook!": "]",
# }
translate_table = {
	".?": ">",
	"?.": "<",
	"..": "+",
	"!!": "-",
	"!.": ".",
	".!": ",",
	"!?": "[",
	"?!": "]",
}

def evaluate_ook(code, input_file, timeout = 1):
	if "\n" in code:
		code = code.replace("\n", " ")
	
	code = code.replace(" ", "")

	if len(code) % 4 != 0 and len(code) % 2 != 0:
		return None

	bf_code = []

	for idx in range(0, len(code), 2):
		try:
			bf_code.append(translate_table[f"{code[idx:idx+2]}"])
		except KeyError:
			return

	bf_code = ''.join(bf_code)

	return evaluate_brainfuck(bf_code, input_file, timeout)


class Unit(NotEnglishUnit):

	PRIORITY = 20

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

	def __init__(self, katana, target, keywords=[]):
		super(Unit, self).__init__(katana, target)

		try:
			self.raw_target=self.target.stream.read()
		except UnicodeDecodeError:
			raise NotApplicable("unicode error, unlikely ook syntax")
		
		self.matches = OOK_REGEX.findall(self.raw_target)
		
		if self.matches is None or self.matches == []:
			raise NotApplicable("no ook potential found")


	def evaluate(self, katana, case):

		value = ''.join( [ x[-1].decode('utf-8') for x in self.matches ] )

		try:
			output = evaluate_ook(value, 
								  katana.config['ook_input'], 
								  katana.config['ook_timeout'])

		except (ValueError, TypeError):
			traceback.print_exc()
			return None

		if output:
			katana.recurse(self, output)
			katana.add_results(self, output)