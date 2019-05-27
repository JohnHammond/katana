from katana.unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
from katana.units import pdf
from katana import utilities
from katana import units

DEPENDENCIES = [ 'pdfinfo' ]

class Unit(units.FileUnit):

	PRIORITY = 60
	ARGUMENTS = [
		{ 'name': 		'pdf_user_password', 
		  'type': 		str, 
		  'default': 	"", 
		  'required': 	False,
		  'help': 		'user password for the given PDF'
		},

		{ 'name': 		'pdf_owner_password', 
		  'type': 		str, 
		  'default': 	"", 
		  'required': 	False,
		  'help': 		'owner password for the given PDF'
		},
	]

	def __init__(self, katana, target):
		# This ensures it is a PDF
		super(Unit, self).__init__(katana, target, keywords=['pdf document'])

	# JOHN: This SHOULD be removed following the new unit argument restructure
	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--pdf-user-password', '-up', default="", type=str, help='user password for the given PDF')
		parser.add_argument('--pdf-owner-password', '-op', default="", type=str, help='owner password for the given PDF')

	def __init__( self, katana, target ):
		super(Unit, self).__init__(katana, target)

	def evaluate(self, katana, case):

		p = subprocess.Popen(['pdfinfo', self.target.path, '-upw', katana.config['pdf_user_password'], '-opw', katana.config['pdf_owner_password'] ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		
		# Look for flags, if we found them...
		response = utilities.process_output(p)
		if response:
			if 'stdout' in response:
				for line in response['stdout']:
					katana.locate_flags(self, line)
				katana.add_results(self, response)