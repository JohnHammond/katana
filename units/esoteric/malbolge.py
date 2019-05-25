from unit import BaseUnit
from units import NotEnglishUnit
from collections import Counter
import sys
from io import StringIO
import argparse
import os
from pwn import *
import math

# JOHN: This code is shamelessly stolen from 
# https://github.com/kmyk/malbolge-interpreter

def isword(x):
	return 0 <= x < 3**10
def unword(x):
	assert isword(x)
	y = []
	for _ in range(10):
		y += [ x % 3 ]
		x //= 3
	return list(reversed(y))
def word(ys):
	x = 0
	for i, y in enumerate(ys):
		assert 0 <= y < 3
		x = x * 3 + y
	assert i+1 == 10
	return x
def tri(x):
	return '0t' + ''.join(map(str, unword(x)))
def rotr(x):
	assert isword(x)
	return (x // 3) + (x % 3 * 3**9)
def crz(xs, ys):
	table = [
		[ 1, 0, 0 ],
		[ 1, 0, 2 ],
		[ 2, 2, 1 ] ]
	return word(map(lambda x, y: table[y][x], unword(xs), unword(ys)))

xlat1 =  "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`"
xlat1 += "_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha"
xlat2 =  "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.T"
xlat2 += "Vac`uY*MK'X~xDl}REokN:#?G\"i@"

assert len(xlat1) == len(xlat2) == 94

def crypt1(i, m):
	assert 32 < ord(m) < 127
	return xlat1[(ord(m) - 33 + i) % 94]
def crypt2(m):
	assert 32 < ord(m) < 127
	return xlat2[ord(m) - 33]
def decrypt1(i, c):
	return chr((xlat1.index(c) - i) % 94 + 33)

def initial_memory(code, allow_not_isprint=False):
	mem = [ 0 ] * (3**10)
	i = 0
	for c in code:
		c = ord(c)
		if chr(c).isspace():
			continue
		if 32 < c < 127:
			# 'invalid character in source file'
			assert crypt1(i, chr(c)) in 'ji*p</vo' 
		else:
			assert allow_not_isprint
		assert i <= 3**10
		mem[i] = c
		i += 1
	return mem
def execute_step(a, c, d, mem, inf=sys.stdin.buffer, outf=sys.stdout.buffer):
	output = []
	if not (32 < mem[c] < 127):
		raise StopIteration # loop
	m = crypt1(c, chr(mem[c]))
	if   m == 'j':
		d = mem[d]
	elif m == 'i':
		c = mem[d]
	elif m == '*':
		a = mem[d] = rotr(mem[d])
	elif m == 'p':
		a = mem[d] = crz(a, mem[d])
	elif m == '<':
		# outf.write(bytes([ a % 256 ]))
		output.append(chr( a % 256 ))
	elif m == '/':
		if not inf:
			x = "\n"
		else:
			x = inf.read(1)

		if x:
			a, = x
		else:
			a = (-1) % (3**10)
	elif m == 'v':
		raise StopIteration
	mem[c] = ord(crypt2(chr(mem[c])))
	c = (c + 1) % (3**10)
	d = (d + 1) % (3**10)

	return a, c, d, mem, output
def execute(code, inf=sys.stdin.buffer, allow_not_isprint=False, debug=False):
	output = []
	try:
		mem = initial_memory(code, allow_not_isprint=allow_not_isprint)
	except:
		# If this fails, it is probably not Malbolge. Stop trying.
		return None
		pass
	a, c, d = 0, 0, 0
	while True:
		try:
			a, c, d, mem, one_output = execute_step(a, c, d, mem, inf=inf)
			output += one_output
		except StopIteration:
			return ''.join(output)
			break
	
class Unit(NotEnglishUnit):

	PRIORITY = 65

	ARGUMENTS = [
		{ 'name': 		'malbolge_input', 
		  'type': 		str, 
		  'default': 	None, 
		  'required': 	False,
		  'help': 		'file to be read as input to malbolge program'
		},
	]

	# JOHN: This SHOULD be removed following the new unit argument restructure
	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--malbolge-input', action='store_true', default=None, help='file to be read as input to malbolge program')

	def evaluate(self, katana, case):
		
		try:
			output = execute(self.target.stream.read().decode('utf-8'), 
							 katana.config['malbolge_input'])

		except (ValueError, AssertionError):
			return None

		if output:
			katana.locate_flags(self, output)
			katana.recurse(self, output)
			katana.add_results(self, output)