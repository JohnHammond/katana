# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-04-11 23:05:05
from unit import BaseUnit
import os
import magic

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