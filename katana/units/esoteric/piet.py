from katana.unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
from katana import utilities
from hashlib import md5
from katana.units import NotApplicable
from katana import units

DEPENDENCIES = [ 'npiet' ]

class Unit(units.FileUnit):

	PRIORITY = 30

	def __init__(self, katana, target, keywords=[]):
		super(Unit, self).__init__(katana, target, keywords=['image'])
		
		if target.is_url:
			raise NotApplicable('target is a URL')

	def evaluate(self, katana, case):

		p = subprocess.Popen(['npiet', self.target.path ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)

		lines = []
		for line in p.stdout:
			katana.locate_flags(self, line)
			lines.append(line)

		for line in lines:
			katana.recurse(self, line)
