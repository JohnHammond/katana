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
permutations = [ "b1,r,lsb,xy", "b1,rgb,msb,yx", "b2,r,msb,yx", "b2,g,lsb,yx", "b2,b,lsb,yx", "b2,b,msb,yx", "b2,rgb,lsb,yx", "b2,rgb,msb,yx", "b2,bgr,lsb,yx", "b2,bgr,msb,yx", "b3,r,lsb,yx", "b3,r,msb,yx", "b4,g,lsb,yx", "b4,b,lsb,yx", "b4,rgb,lsb,yx", "b6,b,lsb,yx", "b7,g,msb,yx", "b8,g,msb,yx", "b2,bgr,lsb,yx,prime", "b3,r,lsb,yx,prime", "b4,bgr,lsb,yx,prime", "b5,r,lsb,yx,prime", "b8,g,lsb,yx,prime", "b2,r,msb,XY", "b2,g,lsb,XY", "b2,g,msb,XY", "b2,b,lsb,XY", "b2,b,msb,XY", "b2,rgb,lsb,XY", "b2,rgb,msb,XY", "b2,bgr,lsb,XY", "b2,bgr,msb,XY", "b3,r,lsb,XY", "b4,g,lsb,XY", "b4,b,lsb,XY", "b4,rgb,lsb,XY", "b8,b,lsb,XY", "b8,bgr,lsb,XY", "b1,r,msb,XY,prime", "b1,g,msb,XY,prime", "b2,r,msb,XY,prime", "b2,g,lsb,XY,prime", "b2,g,msb,XY,prime", "b2,b,lsb,XY,prime", "b2,b,msb,XY,prime", "b2,rgb,lsb,XY,prime", "b2,rgb,msb,XY,prime", "b2,bgr,lsb,XY,prime", "b2,bgr,msb,XY,prime", "b3,r,lsb,XY,prime", "b4,rgb,lsb,XY,prime", "b4,bgr,lsb,XY,prime", "b5,r,lsb,XY,prime", "b2,r,msb,YX", "b2,g,lsb,YX", "b2,g,msb,YX", "b2,b,lsb,YX", "b2,b,msb,YX", "b2,rgb,lsb,YX", "b2,rgb,msb,YX", "b2,bgr,lsb,YX", "b2,bgr,msb,YX", "b3,r,lsb,YX", "b4,r,msb,YX", "b4,g,msb,YX", "b4,b,msb,YX", "b4,rgb,msb,YX", "b4,bgr,lsb,YX", "b5,r,lsb,YX", "b8,g,lsb,YX", "b8,b,lsb,YX", "b8,rgb,lsb,YX", "b8,bgr,lsb,YX", "b1,r,lsb,YX,prime", "b1,rgb,msb,YX,prime", "b1,bgr,msb,YX,prime", "b2,rgb,msb,YX,prime", "b2,bgr,lsb,YX,prime", "b2,bgr,msb,YX,prime", "b3,r,lsb,YX,prime", "b1,r,msb,Xy,prime", "b1,g,msb,Xy,prime", "b1,b,msb,Xy,prime", "b4,r,msb,yX", "b4,g,msb,yX", "b4,b,msb,yX", "b2,r,msb,xY", "b2,g,lsb,xY", "b2,g,msb,xY", "b2,b,lsb,xY", "b2,b,msb,xY", "b2,rgb,lsb,xY", "b2,rgb,msb,xY", "b2,bgr,lsb,xY", "b2,bgr,msb,xY", "b3,r,lsb,xY", "b4,g,lsb,xY", "b4,b,lsb,xY", "b4,rgb,lsb,xY", "b4,bgr,lsb,xY", "b8,b,lsb,xY", "b2,r,msb,xY,prime", "b2,rgb,msb,xY,prime", "b2,bgr,lsb,xY,prime", "b2,bgr,msb,xY,prime", "b3,r,lsb,xY,prime", "b4,g,lsb,xY,prime", "b4,b,lsb,xY,prime", "b4,rgb,lsb,xY,prime", "b4,bgr,lsb,xY,prime", "b5,r,lsb,xY,prime", "b2,r,lsb,Yx", "b2,g,lsb,Yx", "b2,b,lsb,Yx", "b2,rgb,lsb,Yx", "b2,bgr,lsb,Yx", "b3,r,lsb,Yx", "b4,g,lsb,Yx", "b4,b,lsb,Yx", "b4,rgb,lsb,Yx", "b4,bgr,lsb,Yx", "b2,r,msb,Yx,prime", "b2,g,msb,Yx,prime", "b2,b,msb,Yx,prime", "b2,bgr,lsb,Yx,prime", "b3,r,lsb,Yx,prime", "b3,bgr,lsb,Yx,prime", "b4,r,lsb,Yx,prime", "b4,g,lsb,Yx,prime", "b4,b,lsb,Yx,prime", "b4,rgb,lsb,Yx,prime", "b4,bgr,lsb,Yx,prime", "b5,r,lsb,Yx,prime", ]

class Unit(units.FileUnit):

	def __init__(self, katana, parent, target):
		# This ensures it is a PNG
		super(Unit, self).__init__(katana, parent, target, keywords=['png image'])


	def enumerate(self, katana):

		for p in permutations:
			yield p

	def evaluate(self, katana, case):
		p = subprocess.Popen(['zsteg', self.target, case ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)

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
