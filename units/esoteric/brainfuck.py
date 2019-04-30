from unit import BaseUnit
from units import NotEnglishUnit
from collections import Counter
import sys
from io import StringIO
import argparse
import os
from pwn import *
import threading
import time
import traceback

# JOHN: Below is part of Caleb's old code. I am keeping it here for
#	   preservation's sake.
#
# def BrainfuckMap(m):
#	 if len(m) != 8:
#		 raise argparse.ArgumentTypeError('{0}: not a valid brainfuck mapping (expected 8 commands)')
#	 if len(Counter(m)) != len(m):
#		 raise argparse.ArgumentTypeError('{0}: repeating characters are not allowed in brainfuck mapping')
#	 return m

def cleanup(code):
	code = [ x.encode('utf-8') for x in code ]
	return (b''.join(filter(lambda x: x in [b'.', b',', b'[', b']', b'<', b'>', b'+', b'-'], code))).decode('utf-8')


def buildbracemap(code):
	temp_bracestack, bracemap = [], {}

	for position, command in enumerate(code):
		if command == "[": 
			temp_bracestack.append(position)
		if command == "]":
			try:
				start = temp_bracestack.pop()
				bracemap[start] = position
				bracemap[position] = start
			except IndexError as error:
				pass
	return bracemap


def evaluate_brainfuck(code, input_file, timeout = 1):

	output = []

	try:
		code	= cleanup(list(code))
		bracemap = buildbracemap(code)
	except:
		traceback.print_exc()
		return ""

	cells, codeptr, cellptr = [0], 0, 0

	start_time = time.time()

	# while codeptr < len(code) and time.time() < (start_time + timeout ):
	while codeptr < len(code):
		command = code[codeptr]

		if command == ">":
			cellptr += 1
			if cellptr == len(cells): cells.append(0)

		if command == "<":
			cellptr = 0 if cellptr <= 0 else cellptr - 1
		try:
			if command == "+":
				cells[cellptr] = cells[cellptr] + 1 if cells[cellptr] < 255 else 0

			if command == "-":
				cells[cellptr] = cells[cellptr] - 1 if cells[cellptr] > 0 else 255

			if command == "[" and cells[cellptr] == 0: codeptr = bracemap[codeptr]
			if command == "]" and cells[cellptr] != 0: codeptr = bracemap[codeptr]
			
			if command == ".": output.append(chr(int(cells[cellptr])))

			if command == ",": 
				if input_file == None:
					cells[cellptr] = '\n'

				else:
					cells[cellptr] = input_file.read(1)

		except KeyError:
			return None

		codeptr += 1

	return ''.join(output)


class Unit(NotEnglishUnit):

	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--brainfuck-input',  action='store_true', default=None, help='file to be read as input to brainfuck program')
		parser.add_argument('--brainfuck-timeout',  action='store_true', default=1, help='timeout in seconds to run brainfuck program')

	def evaluate(self, katana, case):

		try:
			output = evaluate_brainfuck(self.target.stream.read().decode('utf-8'), katana.config['brainfuck_input'], katana.config['brainfuck_timeout'])

			# JOHN: Again, this is from Caleb's old code.
			# output = evaluate_brainfuck(target, self.config['bf_map'], self.config['bf_input'])
		except (ValueError, TypeError):
			traceback.print_exc()
			return None

		if output:
			katana.recurse(self, output)
			katana.add_results(self, output)
