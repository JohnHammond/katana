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
import pdftotext
from units import NotApplicable


class Unit(units.FileUnit):

	PRIORITY = 50

	# JOHN: This MUST be in the class... 
	PROTECTED_RECURSE = True
	
	# We do not need to include the constructor here 
	# because the ForensicsUnit parent will pull from FileUnit, 
	# to ensure the target is in fact a file.

	def __init__(self, katana, target):
		# This ensures it is a PDF
		super(Unit, self).__init__(katana, target, keywords=['pdf document', 'data'])
		
		try:
			self.pdf = pdftotext.PDF(self.target.stream)
		except (AttributeError,pdftotext.Error):
			raise NotApplicable("cannot read pdf file")

	def evaluate(self, katana, case):

		for page in self.pdf:
			lines = page.split('\n')
			for line in lines:
				katana.recurse(self, line)
