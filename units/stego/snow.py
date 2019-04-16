from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.stego
import utilities
from hashlib import md5

DEPENDENCIES = [ 'snow' ]

class Unit(units.FileUnit):


	def evaluate(self, katana, case):

		p = subprocess.Popen(['snow', self.target ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)

		# Look for flags, if we found them...
		try:
			response = utilities.process_output(p)
		except UnicodeDecodeError:
			
			# This probably isn't plain text....
			p.stdout.seek(0)
			response = p.stdout.read()
			
			# So consider it is some binary output and try and handle it.
			artifact_path, artifact = katana.artifact(self, 'output_%s' % md5(self.target).hexdigest() )
			artifact.write(response)
			artifact.close()

			katana.recurse(self, artifact_path)


		if response is not None:
			if 'stdout' in response:
				
				# If we see anything interesting in here... scan it again!
				for line in response['stdout']:
					katana.locate_flags(self,line)
					katana.recurse(self, line)

			if 'stderr' in response:
				return
			
			katana.add_results(self, response)
