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

DEPENDENCIES = 'foremost'

class Unit(units.forensics.ForensicsUnit):

	# We do not need to include the constructor here 
	# because the ForensicsUnit parent will pull from FileUnit, 
	# to ensure the target is in fact a file.

	def evaluate(self, katana, case):

		# Find/create the output artifact directory
		foremost_directory = katana.get_artifact_path(self)
		# foremost_directory = katana.create_artifact(self, "extracted_files", False)
		p = subprocess.Popen(['foremost', self.target, '-o', foremost_directory ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		p.wait()
		
		results = {
			"extracted_files" : []
		}

		target_hash = md5(open(target, 'rb').read()).hexdigest()

		for (directory, _, files) in os.walk(foremost_directory):
			for each_file in files:
				# Get the relative path
				path = os.path.join(directory, each_file)[len(foremost_directory)+ 1 :]
				
				path_hash = md5(open(path, 'rb').read()).hexdigest()
				print('target_hash', target_hash, 'path_hash',path_hash)

				katana.recurse(self, path)
				results["extracted_files"].append(path)

		results['artifact_directory'] = foremost_directory

		katana.add_results(self, results)