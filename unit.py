from pwn import *
import hashlib
import re
import base64
import binascii

class BaseUnit(object):

	# Unit constructor (saves the config)
	def __init__(self, katana, parent, target):
		self.completed = False
		self.parent = parent
		self.target = target

	# By default, the only test case is the target itself
	def enumerate(self, katana):
		"""
			This function yields the test cases needed for this
			unit. This is how we inform the parent how many test cases we have
			to complete, and let the architecture handle threading of those
			test cases. This function simply returns the target as the only test
			case, but could return more information.

			For example, it may decide to open a wordlist, and return a tuple
			containing both the target, and an associated word from the word list.
			This allows Unit writer to utilize the threading functionality implemented
			in Katana, without special consideration.

			The value returned from this function is passed directly to the evaluate
			method in order to evaluate that test case. By default, this just the name
			of the target for simple tests.
		"""
		
		yield None

	@property
	def unit_name(self):
		return self.__class__.__module__

	def evaluate(self, case):
		log.error('{0}: no evaluate implemented: bad unit'.format(self.unit_name))
	
	@property
	def family_tree(self):
		parents = []
		parent = self.parent
		# Are you my mother
		while parent is not None:
			parents.append(parent)
			parent = parent.parent
		return parents[::-1]

	def get_artifact_path(self, katana, create=True):
		directory = os.path.join(katana.config['outdir'], *[u.unit_name for u in self.family_tree], self.unit_name)
		if os.path.exists(directory) and not os.path.isdir(directory):
			log.error('{0}: name overlap between unit and result!'.format(directory))
		elif not os.path.exists(directory) and create:
			os.makedirs(directory, exist_ok=True)
		return directory

	# Create a new artifact for this target/unit and
	def artifact(self, katana, name, mode='w', create=True):
		path = os.path.join(self.get_artifact_path(katana), name)
		if not create:
			return path
		return open(path, mode), path

	# Create an artifact directory
	def artifact_dir(self, katana, name, create=True):
		path = os.path.join(self.get_artifact_path(katana), name)
		if not create:
				return path
		try:
			os.mkdir(path)
		except OSError:
			if ( "File exists" in e.args ):
				log.error("{0}: directory exists".format(path))
			else:
				# We don't know what went wrong yet.
				# Raise this because it might be another bug to squash
				raise e

		return path
