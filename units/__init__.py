# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-04-29 21:16:14
from unit import BaseUnit
from pwn import *
import os
import magic
import traceback
import string
import re
import utilities

class NotApplicable(Exception):
	pass

class DependancyError(Exception):
	def __init__(self, dep):
		self.dependancy = dep

class FileUnit(BaseUnit):

	def __init__(self, katana, parent, target, keywords=[]):
		super(FileUnit, self).__init__(katana, parent, target)
		
		if not self.target.is_file:
			raise NotApplicable("not a file")

		# JOHN: I do this so only ONE of the supplied keywords needs to be there.
		#       This is to handle things like "jpg" or "jpeg" and other cases
		if keywords:
			keyword_found = False
			for k in keywords:
				if k.lower() in self.target.magic.lower():
					keyword_found = True
			if not keyword_found: 
				raise NotApplicable("no matching magic keywords")

class PrintableDataUnit(BaseUnit):
	
	def __init__(self, katana, parent, target):
		super(PrintableDataUnit, self).__init__(katana, parent, target)

		if not self.target.is_printable:
			raise NotApplicable("not printable data")

class NotEnglishUnit(BaseUnit):
	
	def __init__(self, katana, parent, target):
		super(NotEnglishUnit, self).__init__(katana, parent, target)
		
		if not self.target.is_printable or self.target.is_english:
			raise NotApplicable("potential english text")
