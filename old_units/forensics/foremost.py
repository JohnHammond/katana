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

class Unit(units.forensics.ForensicsUnit):

	@classmethod
	def prepare_parser(cls, config, parser):
		pass

	def evaluate(self, target):

		foremost_directory = self.artifact_dir(target, "extracted_files", False)
		try:
			p = subprocess.Popen(['foremost', target, '-o', foremost_directory ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		except FileNotFoundError as e:
			if "No such file or directory: 'foremost'" in e.args:
				log.failure("foremost is not in the PATH (not installed)? Cannot run the forensics.foremost unit!")
				return None

		p.wait()
		results = {
			"extracted_files" : []
		}

		for (directory, _, files) in os.walk(foremost_directory):
			for each_file in files:
				path = os.path.join(directory, each_file)[len(foremost_directory)+ 1 :] 
				results["extracted_files"].append(path)

		results['artifact_directory'] = foremost_directory

		return results