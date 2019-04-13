from units.zip import ZipUnit
import zipfile
import argparse
from pwn import *

class Unit(ZipUnit):

	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--zip-password', type=str,
					help='A password to try on the file', action='append',
					default=[])


	def __init__( self, katana, parent, target ):
		super(Unit, self).__init__(katana, parent, target)

	def enumerate(self, katana):
		yield ''
		
		for password in katana.config['zip_password']:
			yield password

		if 'dict' in katana.config and katana.config['dict'] is not None:
			katana.config['dict'].seek(0)
			for line in katana.config['dict']:
				yield line.rstrip('\n')

	def evaluate(self, katana, case):
		password = case
		result = {
			'password': '',
			'namelist': []
		}

		with zipfile.ZipFile(self.target) as z:
			name = z.namelist()[0]
			self.artificate_dir()
			# Try to extract the file
			try:
				with z.open(name, 'r', bytes(password, 'utf-8')) as f:
					pass
			except RuntimeError:
				# Password didn't work
				return None

			# We found the password
			self.completed = True
			
			# Look for flags in the extracted data
			for info in z.infolist():
				data = z.read(info, bytes(password, 'utf-8')).decode('utf-8')

				katana.locate_flags(self, data)
				katana.add_results(self, data)

			return True

