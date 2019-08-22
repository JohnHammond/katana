"""

Run ``apktool`` on the host system. For this unit to work, it depends on the 
``apktool`` program to be in the system ``PATH`` environment variable.

This unit hashes each file it detects, so it does not recursively process 
itself.

"""

from katana import units

from hashlib import md5
from io import StringIO
from pwn import *
import subprocess
import os


DEPENDENCIES :list = [ 'apktool' ]


class Unit(units.FileUnit):
	""" 
	This unit inherits from the ``unit.NotEnglishUnit`` because it must be 
	working with a ``.apk`` file. 

	This unit hashes its findings, so it will not recurse on duplicate data.
	"""

	PRIORITY :int = 40

	PROTECTED_RECURSE :bool = True
	
	def __init__(self, katana, target):
		'''
		The constructor is in included, so we can specify that this file
		type magic string must include the word "archive", as that is 
		generally part of an APK file's description.
		'''
		super(Unit, self).__init__(katana, target, keywords=['archive'])	


	def evaluate(self, katana, case):
		'''
		Run the ``apktool`` command on the target, and add results.
		'''

		# Find/create the output artifact directory
		apktool_directory :str = katana.get_artifact_path(self)

		# Run the apktool command outputting to the artifact directory
		p = subprocess.Popen(['apktool', 'decode', '-f', self.target.path, 
							  '-o', apktool_directory ], 
							  stdout = subprocess.PIPE, 
							  stderr = subprocess.PIPE)
		p.wait()
		
		# Keep track of the results in a dictionary, so we can add the 
		# appropriate artifact directory to each. 
		results :dict = {
			"extracted_files" : []
		}

		# Hash the target, so we know not to recurse on that in the future.
		target_hash = md5()
		with open(self.target.path, 'rb') as st:
			for chunk in iter(lambda: st.read(4096), b''):
				target_hash.update(chunk) # Update the hash with this chunk

		# After all the files have been extract with apktool, 
		# loop through them, keeping track of their hashes
		for (directory, dirs, files) in os.walk(apktool_directory):
			dirs[:] = [d for d in dirs if d not in ['android']]
			for filename in files:
				file_path = os.path.join(directory, filename)
				
				path_hash = md5()
				with open(file_path, 'rb') as st:
					for chunk in iter(lambda: st.read(4096), b''):
						path_hash.update(chunk) # Update the hash

				# Don't recurse on the same file, or the report
				if filename != 'apktool.yml' and target_hash != path_hash:
					katana.recurse(self, file_path)
					results["extracted_files"].append(filename)

		# If we actually extracted anything, add them to Katana's results.
		if results['extracted_files']:
			results['artifact_directory'] = apktool_directory
			katana.add_results(self, results)
