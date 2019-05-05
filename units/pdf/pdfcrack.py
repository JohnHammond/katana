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
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import *

# DEPENDENCIES = [ 'qpdf' ]

class Unit(units.FileUnit):

	def __init__(self, katana, parent, target):
		# This ensures it is a PDF
		super(Unit, self).__init__(katana, parent, target, keywords=['pdf document'])

	def enumerate(self, katana):
		# The default is to check an empty password
		yield ''

		# Check other passwords specified explicitly
		for p in katana.config['password']:
			yield p

		# Add all the passwords from the dictionary file
		if 'dict' in katana.config and katana.config['dict'] is not None:
			# CALEB: Possible race condition if two units use the 'dict' argument for the same purpose...
			katana.config['dict'].seek(0)
			for line in katana.config['dict']:
				yield line.rstrip('\n')

	def evaluate(self, katana, password):
		
		# output_path, _ = katana.create_artifact(self, f'{password}.pdf', create=False)
		
		f = open(self.target.path, 'rb')
		parser = PDFParser(f)

		try:
			document = PDFDocument(parser, password)
			del document
			print(repr(password))

			self.completed = True
			return
		
		except PDFPasswordIncorrect:
			pass
			# print("incorrect password")

		# p = subprocess.Popen([ 'qpdf', '--password={}'.format(password), self.target.path.decode('utf-8'), '--decrypt', output_path ], shell =False)
		# p.wait()
		# if p.stderr.read() == b'':
			# print("we got it")
		# output_path = '/home/john/poop'
		# with subprocess.Popen([ 'qpdf', '--password={}'.format(password), self.target.path.decode('utf-8'), '--decrypt', output_path ],stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell =False) as process:
		# 	try:
		# 		stdout, stderr = process.communicate()
		# 	except JobTimeoutException:
		# 		# logger.error('Process was killed by timeout.')
		# 		raise
		# 	finally:
		# 		if process.poll() is None:
		# 			process.kill()
		# 			stdout, stderr = process.communicate()
		# 	# print(stdout)

		# # p = subprocess.Popen([ 'qpdf', '--password={}'.format(password), self.target.path.decode('utf-8'), '--decrypt', output_path ],
		# 	# stdout = tempfile.TemporaryFile(), stderr = tempfile.TemporaryFile(), shell =False)
		# 		# Run steghide
		# # p.wait()
		# # p.kill()
		# # Grab the output
		# # output = bytes.decode(p.stdout.read(),'ascii')
		# # error = bytes.decode(p.stderr.read(),'ascii')
		# # print(p)
		# # Check if it succeeded
		# if (process.returncode != 2):
		# 	print('as')
		# 	katana.add_results(self, "success")
		# 	katana.locate_flags(self, "hello")
		# 	self.completed = True
		# 	return
		# if ( b'invalid password' not in stderr ):
		# # 	# print("right password")
		# if os.path.exists(output_path):
		# 	sys.stdout.write('yes')
		# 	self.completed = True
		# 	return
		

		# # # if ( os.path.exists(output_path) ):
		# # 	print('We got it!', password)
		# # 	self.completed = False
		# # 	return


		# # Grab the output
		# # output = bytes.decode(p.stdout.read(),'ascii')
		# # error = bytes.decode(p.stderr.read(),'ascii')

		# # # Check if it succeeded
		# # if p.returncode != 0:
		# # 	return None

		# # katana.add_artifact(self, output_path)
	
		# # # Grab the file type
		# # typ = magic.from_file(output_path)
		# # thing = '<BINARY_DATA>'
		
		# # with open(output_path, 'r') as f:
		# # 	thing = f.read()

		# # katana.locate_flags(self, thing)

		# # katana.recurse(self, output_path)

		# # katana.add_results(self, {
		# # 	'file': output_path,
		# # 	'type': typ
		# # })
