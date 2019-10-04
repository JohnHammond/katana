'''
This unit runs ``stegsnow`` on the target. 

It will automatically hunt for a password in the given file, but any can be
supplied as arguments as usual.
'''

import re
import subprocess
from hashlib import md5

from katana import units
from katana import utilities
from katana.units import NotApplicable

DEPENDENCIES = ['stegsnow']


PASSWORD_PATTERN = rb'password\s*(is)?\s*[:=]\s*(\S+)\s*'
PASSWORD_REGEX = re.compile(PASSWORD_PATTERN, re.MULTILINE | re.DOTALL | \
							                  re.IGNORECASE)
class Unit(units.FileUnit):
	PRIORITY = 30

	ARGUMENTS = [
		{'name': 'stegsnow_password',
		 'type': str,
		 'default': "",
		 'required': False,
		 'help': 'a password to give to stegsnow'
		 },
	]

	def __init__(self, katana, target, keywords=None):
		super(Unit, self).__init__(katana, target)

		if target.is_url:
			raise NotApplicable('target is a URL')

		katana.config['stegsnow_password'] = [ katana.config['stegsnow_password'] ]

		passwords_found = PASSWORD_REGEX.findall(self.target.raw)
		if passwords_found:
			for each in passwords_found:
				potential_password = each[-1].decode('utf-8')
				katana.config['stegsnow_password'].append(potential_password)


	def enumerate(self, katana):
		'''
		This function will offer potential password cases to be given
		to the stegsnow program. First it will try an empty password,
		then any passwords passed to Katana as an argument, and then
		any potential passwords it found within the original target itself.
		Finally, it will work through a dictionary file if one is supplied
		to Katana.
		'''


		# The default is to check an empty password
		yield ''

		# Check other passwords specified explicitly
		for p in katana.config['stegsnow_password']:
			yield p

		# Add all the passwords from the dictionary file
		if 'dict' in katana.config and katana.config['dict'] is not None:
			# CALEB: Possible race condition if two units use the 'dict' 
			#        argument for the same purpose...
			katana.config['dict'].seek(0)
			for line in katana.config['dict']:
				yield line.rstrip(b'\n')


	def evaluate(self, katana, case):
		'''
		This function runs the ``stegsnow`` utility, with the `-C` argument
		to uncompress any data it finds. It also supplies the passwords 
		given by the ``enumerate`` function.
		'''


		p = subprocess.Popen(['stegsnow', '-C', '-p', case, self.target.path ],
							   stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		# Look for flags, if we found them...
		try:
			response = utilities.process_output(p)
		except UnicodeDecodeError:

			# This probably isn't plain text....
			p.stdout.seek(0)
			response = p.stdout.read()

			# So consider it is some binary output and try and handle it.
			artifact_path, artifact = katana.artifact(self, 'output_%s' % 
											md5(self.target).hexdigest())
			artifact.write(response)
			artifact.close()

			katana.recurse(self, artifact_path)


		if response is not None:
			if 'stdout' in response:

				# If we see anything interesting in here... scan it again!
				for line in response['stdout']:
					katana.recurse(self, line)

			if 'stderr' in response:
				return

			katana.add_results(self, response)
