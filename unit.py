from pwn import *
import hashlib
import re
import base64
import binascii

class BaseUnit(object):

	# Set this to True to protect this unit from recursing into another
	# protected unit
	PROTECTED_RECURSE = False

	# The unit priority. 50 is default. 1 is highest. 100 is lowest.
	PRIORITY = 50

	@classmethod
	def add_arguments(cls, katana, parser):
		""" Add whatever arguments are needed by this unit to the given
			parser
		"""
		return

	# Unit constructor (saves the config)
	def __init__(self, katana, parent, target):
		self._completed = False
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
	
	@property
	def completed(self):
		return self._completed

	@completed.setter
	def completed(self, v):
		if v != True:
			raise ValueError
		parent = self.parent
		while parent is not None:
			parent._completed = True
			parent = parent.parent
		self._completed = True
