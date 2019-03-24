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

		try:
			p = subprocess.Popen(['jsteg', 'reveal', target ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		except FileNotFoundError as e:
			if "No such file or directory: 'jsteg'" in e.args:
				log.failure("jsteg is not in the PATH (not installed)? Cannot run the stego.jsteg unit!")
				return None

		stdout = []
		stderr = []

		result = {
			"stdout": [],
			"stderr": [],
		}

		output = bytes.decode(p.stdout.read(),'ascii')
		error = bytes.decode(p.stderr.read(),'ascii')
		
		for line in [ l.strip() for l in output.split('\n') if l ]:
			result["stdout"].append(line)
		
		for line in [ l.strip() for l in error.split('\n') if l ]:
			result["stderr"].append(line)

		if not len(result['stderr']):
			result.pop('stderr')
		if not len(result['stdout']):
			result.pop('stdout')
		
		return result