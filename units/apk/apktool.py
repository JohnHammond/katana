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
from hashlib import md5

DEPENDENCIES = [ 'apktool' ]

class Unit(units.FileUnit):

	PRIORITY = 40

	# JOHN: This MUST be in the class... 
	PROTECTED_RECURSE = True
	
	# We do not need to include the constructor here 
	# because the ForensicsUnit parent will pull from FileUnit, 
	# to ensure the target is in fact a file.

	def evaluate(self, katana, case):

		def __init__(self, katana, target):
			# This ensures it is a PDF
			super(Unit, self).__init__(katana, target, keywords=['zip archive', 'java archive'])

		# Find/create the output artifact directory
		apktool_directory = katana.get_artifact_path(self)

		p = subprocess.Popen(['apktool', 'decode', '-f', self.target.path, '-o', apktool_directory ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		p.wait()
		
		results = {
			"extracted_files" : []
		}

		target_hash = md5()
		with open(self.target.path, 'rb') as st:
			for chunk in iter(lambda: st.read(4096), b''):
				# Update the hash with this chunk
				target_hash.update(chunk)

		for (directory, dirs, files) in os.walk(apktool_directory):
			dirs[:] = [d for d in dirs if d not in ['android']]
			for filename in files:
				# print('starting to loop')
				# Get the relative path
				file_path = os.path.join(directory, filename)
				# print(file_path)
				
				path_hash = md5()
				with open(file_path, 'rb') as st:
					for chunk in iter(lambda: st.read(4096), b''):
						# Update the hash with this chunk
						path_hash.update(chunk)

				# Don't recurse on the same file, or the report
				if filename != 'apktool.yml' and target_hash != path_hash:
					katana.recurse(self, file_path)
					results["extracted_files"].append(filename)


		if results['extracted_files']:
			results['artifact_directory'] = apktool_directory
			katana.add_results(self, results)