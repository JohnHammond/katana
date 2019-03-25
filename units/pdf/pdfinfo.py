from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.stego
import util

class Unit(units.stego.StegoUnit):

	@classmethod
	def prepare_parser(cls, config, parser):
		parser.add_argument('--userpassword', default=4, type=int, help='minimum length of strings to be returned')

	def evaluate(self, target):

		try:
			p = subprocess.Popen(['pdfinfo', target, '' ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		except FileNotFoundError as e:
			if "No such file or directory: 'pdfinfo'" in e.args:
				log.failure("pdfinfo is not in the PATH (not installed)? Cannot run the pdf.pdfinfo unit!")
				return None

		result = util.process_output(p)
		return result