from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.forensics
import os
import utilities
import glob

DEPENDENCIES = [ 'pdftotext' ]


class Unit(units.FileUnit):

	PRIORITY = 50

	# JOHN: This MUST be in the class... 
	PROTECTED_RECURSE = True
	
	# We do not need to include the constructor here 
	# because the ForensicsUnit parent will pull from FileUnit, 
	# to ensure the target is in fact a file.

	def __init__(self, katana, parent, target):
		# This ensures it is a PDF
		super(Unit, self).__init__(katana, parent, target, keywords=['pdf document'])

	def evaluate(self, katana, case):

		# Find/create the output artifact directory
		filename = [ str(p) for p in os.path.splitext(self.target.path) ]
		if filename:
			filename = filename[0].split('/')[-1]

		artifact_path, _ = katana.create_artifact(self, f'{filename}.txt', create=False)
		
		p = subprocess.Popen(['pdftotext', self.target.path, artifact_path ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		p.wait()
		
		if os.path.exists(artifact_path):
			katana.recurse(self, artifact_path)