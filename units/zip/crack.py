import units
import zipfile
import argparse
from pwn import *

DEPENDENCIES = [ 'unzip' ]

class Unit(units.FileUnit):

	PRIORITY = 40

	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--zip-password', type=str,
					help='A password to try on the file', action='append',
					default=[])

	def __init__(self, katana, parent, target):
		# This ensures it is a ZIP
		super(Unit, self).__init__(katana, parent, target, keywords=['zip archive'])

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

		directory_path, _ = katana.create_artifact(self, os.path.basename(self.target.path.decode('utf-8')), create=True, asdir=True)

		p = subprocess.Popen(['unzip', '-P', password, self.target.path], cwd=directory_path, 
				stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
		
		p.wait()

		for root, dirs, files in os.walk(directory_path):
			for name in files:
				path = os.path.join(root, name)
				katana.add_artifact(self, path)
				katana.recurse(self, path)
				self.completed = True

		return

		with zipfile.ZipFile(self.target.path, allowZip64=True) as z:
			name = z.namelist()[0]
			#self.artificate_dir()
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
				name, f = katana.create_artifact(self, name)
				with f:
					with z.read(info, bytes(password, 'utf-8')) as zf:
						for chunk in iter(lambda: zf.read(4096), b""):
							f.write(chunk)

				katana.recurse(self, name)

			return True