from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.stego
import utilities
from hashlib import md5
from units import NotApplicable
import re

def encode_to_whitespace(f):
	h = binascii.hexlify(f)
	d = int(h, 16)
	b = bin(d)[2:]
	m = b.replace('0', ' ')
	m = m.replace('1', '\t')
	return m

class Unit(units.FileUnit):

	PRIORITY = 30

	def __init__(self, katana, target, keywords=[]):
		super(Unit, self).__init__(katana, target)

		self.space_pieces = re.findall(b'[ \t]+', self.target.stream)
		
		if target.is_url:
			raise NotApplicable('target is a URL')

	def evaluate(self, katana, case):
		print(self.space_pieces)
		pass
		# p = subprocess.Popen(['snow', self.target.path ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)

		# # Look for flags, if we found them...
		# try:
		# 	response = utilities.process_output(p)
		# except UnicodeDecodeError:
			
		# 	# This probably isn't plain text....
		# 	p.stdout.seek(0)
		# 	response = p.stdout.read()
			
		# 	# So consider it is some binary output and try and handle it.
		# 	artifact_path, artifact = katana.artifact(self, 'output_%s' % md5(self.target).hexdigest() )
		# 	artifact.write(response)
		# 	artifact.close()

		# 	katana.recurse(self, artifact_path)


		# if response is not None:
		# 	if 'stdout' in response:
				
		# 		# If we see anything interesting in here... scan it again!
		# 		for line in response['stdout']:
		# 			katana.recurse(self, line)

		# 	if 'stderr' in response:
		# 		return
			
		# 	katana.add_results(self, response)
