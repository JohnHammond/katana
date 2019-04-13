from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.pdf
import utilities

DEPENDENCIES = [ 'pdfinfo' ]

class Unit(units.pdf.PdfUnit):

	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--pdf-user-password', '-up', default="", type=str, help='user password for the given PDF')
		parser.add_argument('--pdf-owner-password', '-op', default="", type=str, help='owner password for the given PDF')	

	def __init__( self, katana, parent, target ):
		super(Unit, self).__init__(katana, parent, target)

	def evaluate(self, katana, case):

		p = subprocess.Popen(['pdfinfo', self.target, '-upw', katana.config['pdf_user_password'], '-opw', katana.config['pdf_owner_password'] ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		
		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if 'stdout' in response:
			for line in response['stdout']:
				katana.locate_flags(self, line)

		katana.add_results(self, response)		
