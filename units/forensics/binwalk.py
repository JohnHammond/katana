from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.forensics
import utilities

class Unit(units.forensics.ForensicsUnit):

	@classmethod
	def prepare_parser(cls, config, parser):
		pass

	def evaluate(self, target):

		binwalk_directory = self.artifact_dir(target, "extracted_files" )
		try:
			p = subprocess.Popen(['binwalk', '-e', target, '--directory', binwalk_directory ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		except FileNotFoundError as e:
			if "No such file or directory: 'binwalk'" in e.args:
				log.failure("binwalk is not in the PATH (not installed)? Cannot run the forensics.binwalk unit!")
				return None

		results = utilities.process_output(p)
		results['artifact'] = binwalk_directory

		return results