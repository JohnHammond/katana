from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.stego
import utilities

class Unit(units.stego.StegoUnit):

	@classmethod
	def prepare_parser(cls, config, parser):
		parser.add_argument('--userpassword', '-up', default="", type=str, help='user password for the given PDF')
		parser.add_argument('--ownerpassword', '-op', default="", type=str, help='owner password for the given PDF')

	def evaluate(self, target):

		try:
			p = subprocess.Popen(['pdfinfo', target, '-upw', self.config['userpassword'], '-opw', self.config['ownerpassword'] ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		except FileNotFoundError as e:
			if "No such file or directory: 'pdfinfo'" in e.args:
				log.failure("pdfinfo is not in the PATH (not installed)? Cannot run the pdf.pdfinfo unit!")
				return None

		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			self.find_flags(str(response['stdout']))
		if 'stderr' in response:
			self.find_flags(str(response['stderr']))
		
		return response
