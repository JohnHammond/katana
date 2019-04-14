from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.forensics
import utilities
import os

DEPENDENCIES = [ 'binwalk' ]

class Unit(units.forensics.ForensicsUnit):

	def evaluate(self, target):

		# Find/create the output artifact directory
		binwalk_directory = katana.get_artifact_path(self)

		# Run binwalk on the target
		p = subprocess.Popen(['binwalk', '-e', target, '--directory', binwalk_directory ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)

		results = utilities.process_output(p)
		results['artifact'] = binwalk_directory

		# Inspect all the resulting files
		for root, dirs, files in os.walk(binwalk_directory):


		return results
