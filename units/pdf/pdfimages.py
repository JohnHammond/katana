from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import os
import utilities
import units

DEPENDENCIES = [ 'pdfimages' ]


class Unit(units.FileUnit):


	PRIORITY = 40
	
	# JOHN: This MUST be in the class... 
	PROTECTED_RECURSE = True

	def __init__(self, katana, target):
		# This ensures it is a PDF
		super(Unit, self).__init__(katana, target, keywords=['pdf document'])

	def evaluate(self, katana, case):

		# Find/create the output artifact directory
		pdfimages_directory = katana.get_artifact_path(self)
		
		p = subprocess.Popen(['pdfimages', '-png', self.target.path, os.path.join(pdfimages_directory,'image') ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		p.wait()
		
		for (directory, _, files) in os.walk(pdfimages_directory):
			for filename in files:

				file_path = os.path.join(directory, filename)
				katana.recurse(self, file_path)
				katana.add_artifact(self, file_path)