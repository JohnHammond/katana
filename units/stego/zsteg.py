from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import os
import units.stego
import units

class Unit(units.stego.StegoUnit):

	def __init__(self, katana):
		super(Unit, self).__init__(katana)
		if os.system('which zsteg') != 0:
			log.failure('zsteg is not in the PATH (not installed)? Cannot run the stego.zsteg unit!')
			raise units.NotApplicable()

	def evaluate(self, katana, case):

		try:
			p = subprocess.Popen(['zsteg', '-a', katana.target ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		except FileNotFoundError as e:
			if "No such file or directory: 'zsteg'" in e.args:
				log.failure("zsteg is not in the PATH (not installed)? Cannot run the stego.zsteg unit!")
				return

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
			delimeter = '\r'
			lines = [e+d for e in line.split(d) if e]
			for temp_line in lines:
				if (not temp_line.endswith(".. \r")):
					katana.locate_flags(temp_line)
					result["stdout"].append(temp_line)
		
		for line in [ l.strip() for l in error.split('\n') if l ]:
			katana.locate_flags(line)
			result["stderr"].append(line)

		if not len(result['stderr']):
			result.pop('stderr')
		if not len(result['stdout']):
			result.pop('stdout')
		
		katana.add_results(result)
