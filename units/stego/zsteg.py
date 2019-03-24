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
			p = subprocess.Popen(['zsteg', '-a', ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		except FileNotFoundError as e:
			if "No such file or directory: 'zsteg'" in e.args:
				log.failure("zsteg is not in the PATH (not installed)?")
				return None

		output = bytes.decode(p.stdout.read(),'ascii')
		error = bytes.decode(p.stderr.read(),'ascii')
		result = {
			"stdout": output,
			"stderr": error,
		}
		
		return result
