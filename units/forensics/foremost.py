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

DEPENDENCIES = [ 'foremost' ]
PROTECTED_RECURSE = True

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

		target_hash = md5(open(self.target, 'rb').read()).hexdigest()

		for (directory, _, files) in os.walk(foremost_directory):
			for filename in files:

				# Get the relative path
				file_path = os.path.join(directory, filename)
				path_hash = md5(open(file_path, 'rb').read()).hexdigest()

				# Don't recurse on the same file, or the foremost report
				if filename != 'audit.txt' and target_hash != path_hash:
					katana.recurse(self, file_path)
					results["extracted_files"].append(filename)


		if results['extracted_files']:
			results['artifact_directory'] = foremost_directory
			katana.add_results(self, results)