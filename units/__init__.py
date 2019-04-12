# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-04-12 19:38:11
from unit import BaseUnit
from pwn import *
import os
import magic
import string

class NotApplicable(Exception):
	pass

class DependancyError(Exception):
	def __init__(self, dep):
		self.dependancy = dep

class FileOrDataUnit(BaseUnit):
	
	def __init__(self, katana, parent, target):

		# Assume that if the target opens properly as a file, that it is 
		# meant to be a file
		try:
			target = open(target, 'r').read()
		except:
			pass

		# We do that before super, so that self.target always refers to
		# the correct target
		super(FileOrDataUnit, self).__init__(katana, parent, target)
	
class FileUnit(BaseUnit):
	
	def __init__(self, katana, parent, target, keywords=[]):
		super(FileUnit, self).__init__(katana, parent, target)
		
		# Ensure it's a file, and get it's mime type
		try:
			t = magic.from_file(target).lower()
		except FileNotFoundError:
			raise NotApplicable()
		
		# Check for the keywords
		n = 0
		for kw in keywords:
			if kw not in t:
				n += 1

		# If no keywords were found, it doesn't match
		if n == len(keywords) and n != 0:
			raise NotApplicable()

class PrintableDataUnit(BaseUnit):
	
	def __init__(self, katana, parent, target):
	
		# Similar to FileOrDataUnit, use file if it exists
		try:
			target = open(target, 'r').read()
		except:
			pass

		super(PrintableDataUnit, self).__init__(katana, parent, target)

		# If this is a bytes object, attempt to decode it as utf-8
		if type(self.target) is bytes:
			try:
				self.target = self.target.decode('utf-8')
			except UnicodeError:
				raise NotApplicable()
		
		# Ensure the string is printable
		for c in self.target:
			if c not in string.printable:
				raise NotApplicable()

