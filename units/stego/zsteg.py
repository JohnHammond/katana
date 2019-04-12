from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import os
import units.stego
import magic
import units

DEPENDENCIES = [ 'zsteg' ]

class Unit(units.stego.FileUnit):

	def __init__(self, katana, parent, target):
		# This ensures it is a JPG
		super(Unit, self).__init__(katana, parent, target, keywords=['png image'])


	def evaluate(self, katana, case):


		p = subprocess.Popen(['zsteg', '-a', self.target ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)

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
			delimeter = '\r'
			lines = [e+d for e in line.split(d) if e]
			for temp_line in lines:
				if (not temp_line.endswith(".. \r")):
					katana.locate_flags(self,temp_line)
					result["stdout"].append(temp_line)
		
		for line in [ l.strip() for l in error.split('\n') if l ]:
			katana.locate_flags(self,line)
			result["stderr"].append(line)

		if not len(result['stderr']):
			result.pop('stderr')
		if not len(result['stdout']):
			result.pop('stdout')
		
		katana.add_results(self, result)
