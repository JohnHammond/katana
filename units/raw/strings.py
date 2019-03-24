from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.raw

class Unit(units.raw.RawUnit):

	@classmethod
	def prepare_parser(cls, config, parser):
		pass

	def evaluate(self, target):

		p = subprocess.Popen(['strings', target], stdout = subprocess.PIPE)

		result = {
			'strings': []
		}

		for line in [ bytes.decode(l,'ascii').replace("\n","") \
					  for l in p.stdout.readlines() ]:
			result['strings'].append(line)
		
		return result