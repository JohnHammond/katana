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

dependancy_command = 'foremost'

class Unit(units.forensics.ForensicsUnit):

	# We do not need to include the constructor here 
	# because the ForensicsUnit parent will pull from FileUnit, 
	# to ensure the target is in fact a file.

	def evaluate(self, target):

		foremost_directory = katana.artifact_dir(target, "extracted_files", False)
		p = subprocess.Popen([dependancy_command, target, '-o', foremost_directory ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		
		p.wait()
		results = {
			"extracted_files" : []
		}

		for (directory, _, files) in os.walk(foremost_directory):
			for each_file in files:
				path = os.path.join(directory, each_file)[len(foremost_directory)+ 1 :] 
				
				katana.recurse(self, path)
				results["extracted_files"].append(path)

		results['artifact_directory'] = foremost_directory

		katana.add_results(self, results)

# Ensure the system has the required binaries installed. This will prevent the module from running on _all_ targets
try:
	subprocess.check_output(['which',dependancy_command])
except (FileNotFoundError, subprocess.CalledProcessError) as e:
	raise units.DependancyError(dependancy_command)