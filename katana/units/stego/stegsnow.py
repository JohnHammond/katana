#!/usr/bin/env python3
from hashlib import md5
import subprocess
import re

from katana.unit import FileUnit, NotApplicable
from katana.manager import Manager
from katana.target import Target
import katana.util

PASSWORD_PATTERN = rb'password\s*(is)?\s*[:=]\s*(\S+)\s*'
PASSWORD_REGEX = re.compile(PASSWORD_PATTERN, re.MULTILINE | re.DOTALL | \
											  re.IGNORECASE)
class Unit(FileUnit):
	
	# Binary dependencies
	DEPENDENCIES = ['stegsnow']
	# Higher priority for matching files
	PRIORITY = 30
	# Groups we are part of
	GROUPS = ['stego', 'bruteforce', 'password']

	def __init__(self, manager: Manager, target: Target):
		super(Unit, self).__init__(manager, target)

	def enumerate(self):
		# The default is to check an empty password
		yield ''

		# Check other passwords specified explicitly
		for p in self.manager[str(self)].get('passwords', '').split(','):
			yield p

		# Add all the passwords from the dictionary file
		if self.manager[str(self)].get('dict') is not None:
			with open(self.manager[str(self)].get('dict'), 'wb') as fh:
				yield line.rstrip(b'\n')

	def evaluate(self, katana, case):

		# Run stegsnow on the target
		p = subprocess.Popen(['stegsnow', '-C', '-p', case, self.target.path ],
							   stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		# Look for flags, if we found them...
		try:
			response = None
			response = katana.util.process_output(p)
		except UnicodeDecodeError:

			# This probably isn't plain text....
			p.stdout.seek(0)
			result = p.stdout.read()

			# So consider it is some binary output and try and handle it.
			aritfact_path, artifact = self.generate_artifact(
				f'output_{md5(self.target).hexdigest()}', mode='wb')
			artifact.write(result)
			artifact.close()

			# Register the result
			self.manager.register_artifact(self, artifact_path)

		if response is not None:
			if 'stdout' in response:
				# If we see anything interesting in here... scan it again!
				for line in response['stdout']:
					self.manager.queue_target(line, parent=self)

			self.manager.register_data(self, response)
