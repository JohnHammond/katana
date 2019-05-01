from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.pcap
import os
import utilities
import glob
from hashlib import md5

DEPENDENCIES = [ 'tcpflow' ]

class Unit(units.pcap.PcapUnit):

	# JOHN: This MUST be in the class... 
	PROTECTED_RECURSE = True
	
	# We do not need to include the constructor here 
	# because the ForensicsUnit parent will pull from FileUnit, 
	# to ensure the target is in fact a file.

	def evaluate(self, katana, case):

		# Find/create the output artifact directory
		tcpflow_directory = katana.get_artifact_path(self)
		
		p = subprocess.Popen(['tcpflow', '-r', self.target.path, '-o', tcpflow_directory ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		p.wait()
		
		results = {
			"extracted_files" : []
		}

		for (directory, _, files) in os.walk(tcpflow_directory):
			for filename in files:

				# Get the relative path
				file_path = os.path.join(directory, filename)

				# Don't recurse on the same file, or the foremost report
				if filename != 'report.xml':
					katana.recurse(self, file_path)
					results["extracted_files"].append(filename)


		if results['extracted_files']:
			results['artifact_directory'] = tcpflow_directory
			katana.add_results(self, results)