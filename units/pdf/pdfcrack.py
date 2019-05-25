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
import tempfile
from PyPDF2 import PdfFileReader
import time

# DEPENDENCIES = [ 'qpdf' ]

class Unit(units.FileUnit):

	PRIORITY = 70

	def __init__(self, katana, target):
		# This ensures it is a PDF
		super(Unit, self).__init__(katana, target, keywords=['pdf document'])

		try:
			with open(self.target.path, 'rb') as f:
				pdf = PdfFileReader(f)
				if not pdf.isEncrypted:
					raise units.NotApplicable('pdf is not encrypted')
		except units.NotApplicable as e:
			raise e
		except:
			raise NotApplicable('failed to open/read file')

	def enumerate(self, katana):
		
		# The default is to check an empty password
		yield b''

		# Check other passwords specified explicitly
		for p in katana.config['password']:
			yield p.encode('utf-8')

		# Add all the passwords from the dictionary file
		if 'dict' in katana.config and katana.config['dict'] is not None:
			# CALEB: Possible race condition if two units use the 'dict' argument for the same purpose...
			with open(katana.config['dict'].name, 'rb') as f:
				for line in iter(lambda: f.readline(), ''):
					yield line.rstrip(b'\n')

	def evaluate(self, katana, password):
		
		with open(self.target.path, 'rb') as f:
			pdf = PdfFileReader(f)

			try:
				password = password.decode('utf-8')
			except AttributeError:
				pass
			except UnicodeDecodeError:
				# Apparently, pdf can't handle bytes passwords...
				return

			if pdf.decrypt(password):
				katana.add_results(self, '{0}: {1}'.format(self.target.path, password))
				self.completed = True

