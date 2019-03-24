from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import os
import units.stego

class Unit(units.stego.StegoUnit):

	@classmethod
	def prepare_parser(cls, config, parser):
		pass

	def evaluate(self, target):

		p = subprocess.Popen(['steghide', 'extract', '-sf', target, '-p', '', '-f'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		
		stdout = []
		stderr = []

		result = {
			"stdout": [],
			"stderr": [],
		}

		output = bytes.decode(p.stdout.read(),'ascii')
		error = bytes.decode(p.stderr.read(),'ascii')
		
		d = "\r"
		for line in output:
		    s =  [e+d for e in line.split(d) if e]

		for line in [ l.strip() for l in output.split('\n') if l ]:
			result["stdout"].append(line)
		
		for line in [ l.strip() for l in error.split('\n') if l ]:
			result["stderr"].append(line)
		
		if not len(result['stderr']):
			result.pop('stderr')
		if not len(result['stdout']):
			result.pop('stdout')

		return result
