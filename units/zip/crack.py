from units.zip import ZipUnit
import zipfile
import argparse
from pwn import *

class Unit(ZipUnit):

	@classmethod
	def prepare_parser(cls, config, parser):
		#try:
		parser.add_argument('--dict', '-d', type=argparse.FileType('r', encoding='latin-1'),
					help='Dictionary for bruteforcing')
		parser.add_argument('--password', '-p', type=str,
					help='A password to try on the file', action='append',
					default=[])
		#except:
		#	pass
		return

	def check(self, target):
		return super(Unit, self).check(target[0])

	def get_cases(self, target):
		yield 'no password',(target, '')
		
		for p in self.config['password']:
			yield p,(target, p)

		if 'dict' in self.config and self.config['dict'] is not None:
			self.config['dict'].seek(0)
			for line in self.config['dict']:
				yield line.rstrip('\n'), (target, line.rstrip('\n'))

	def evaluate(self, target):
		zipname, password = target
		result = {
			'password': '',
			'namelist': []
		}

		with zipfile.ZipFile(zipname) as z:
			name = z.namelist()[0]

			# Try to extract the file
			try:
				with z.open(name, 'r', bytes(password, 'utf-8')) as f:
					pass
			except RuntimeError:
				# Pw didn't work
				return None

			# We found the password
			self.completed = True
			
			# Look for flags in the extracted data
			for info in z.infolist():
				data = z.read(info, bytes(password, 'utf-8')).decode('utf-8')
				self.find_flags(data)

			return True

