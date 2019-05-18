from unit import BaseUnit
from units import NotEnglishUnit, NotApplicable
from collections import Counter
import sys
from io import StringIO
import argparse
import os
from pwn import *
import threading
import time
import traceback

def cleanup(code):
	code = [ x.encode('utf-8') for x in code ]
	return (b''.join(filter(lambda x: x in b'oOmM', code))).decode('utf-8')
	
def build_jumpmap(code):
	
	jumpmap = {}
	
	for pointer in range(0, len(code), 3):
		
		if code[pointer:pointer+3] == "MOO":
			pointer2 = pointer+6
			while code[pointer2:pointer2+3] != "moo":
				pointer2+=3
			
			jumpmap[pointer] = pointer2
			jumpmap[pointer2] = pointer
		
		elif code[pointer:pointer+3] == "moo" and jumpmap.get(pointer, -1) == -1:
			raise SyntaxError('Unmatched moo')
	
	return jumpmap
			

def evaluate_cow(code, input_file, timeout = -1):

	command_list = ['moo', 'mOo', 'moO', 'mOO', 'Moo', 'MOo', 'MoO', 'MOO', 'OOO', 'MMM', 'OOM', 'oom']

	output = []
	code = code.strip()
	try:
		code	= cleanup(list(code))
		jumpmap = build_jumpmap(code)
	except:
		traceback.print_exc()
		return ""

	cells, codeptr, cellptr, register = [0], 0, 0, None

	start_time = time.time()

	# by default, timeout is -1 and the code runs for as long as possible
	while codeptr < len(code) and (timeout < 0 or time.time() < (start_time + timeout)):
		
		if codeptr < 0:
			# weird behavior here
			# if we encounter a mOO, we make the pointer negative and continue execution
			# now we know that if the code pointer is negative, mOO was called, so we need to make the command be whatever's pointed at in memory
			command = command_list[cells[cellptr]]
			codeptr = -codeptr 
		else:
			command = code[codeptr:codeptr+3]

		if command == "moO": # moO-ve memory pointer forward
			cellptr += 1
			if cellptr == len(cells): cells.append(0)

		if command == "mOo": # mOo-ve memory pointer backward
			cellptr = 0 if cellptr <= 0 else cellptr - 1
		try:
			if command == "MoO":
				cells[cellptr] = cells[cellptr] + 1 if cells[cellptr] < 255 else 0

			if command == "MOo":
				cells[cellptr] = cells[cellptr] - 1 if cells[cellptr] > 0 else 255

			if command == "MOO" and cells[cellptr] == 0: 
				nextptr = jumpmap.get(codeptr, -1)
				
				if nextptr < 0:
					nextptr = codeptr + 6
					while code[nextptr:nextptr+3] != "moo":
						nextptr +=3
				
				codeptr = nextptr
				
			if command == "moo":
				nextptr = jumpmap.get(codeptr, -1)
				
				if nextptr < 0:
					nextptr = codeptr-6
					while code[nextptr:nextptr+3] != "MOO":
						nextptr -= 3
				else:
					nextptr -=3
				
				codeptr = nextptr
			
			if command == "Moo":
				if cells[cellptr] == 0:
					cells[cellptr] = input_file.read(1)
				else:
					output.append(chr(cells[cellptr]))
			
			if command == "mOO":
				codeptr = -codeptr -3
				
			if command == "OOO":
				cells[cellptr] = 0
				
			if command == "MMM":
				if register == None:
					register = cells[cellptr]
				else:
					cells[cellptr] = register
					register = None
			
			if command == "OOM":
				output.append(cells[cellptr])
			
			if command == "oom":
				cells[cellptr] = input_file.read(1)

		except (KeyError, TypeError):
			return None

		codeptr += 3

	return ''.join(output)


class Unit(NotEnglishUnit):

	PRIORITY = 60

	def __init__(self, katana, parent, target, keywords=[]):
		super(Unit, self).__init__(katana, parent, target)

		self.raw_target = self.target.stream.read().decode('utf-8').lower()
		if ( self.raw_target.count('moo') < 10 ):
			raise NotApplicable("less than 10 occurences of 'moo'")

	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--cow-input',  action='store_true', default=None, help='file to be read as input to cow program')
		parser.add_argument('--cow-timeout',  action='store_true', default=1, help='timeout in seconds to run cow program')

	def evaluate(self, katana, case):

		try:
			output = evaluate_cow(self.target.stream.read().decode('utf-8'), katana.config['cow_input'], katana.config['cow_timeout'])

		except (ValueError, TypeError):
			traceback.print_exc()
			return None

		if output:
			katana.recurse(self, output)
			katana.add_results(self, output)
