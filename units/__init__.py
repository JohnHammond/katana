# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-04-24 17:31:54
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
			raise NotApplicable

		for k in keywords:
			if k not in self.target.magic:
				raise NotApplicable

class PrintableDataUnit(BaseUnit):
	
	def __init__(self, katana, parent, target):
		super(PrintableDataUnit, self).__init__(katana, parent, target)

		if not self.target.is_printable:
			raise NotApplicable

class NotEnglishUnit(BaseUnit):
	
	def __init__(self, katana, parent, target):
		super(NotEnglishUnit, self).__init__(katana, parent, target)
		
		if not self.target.is_printable or self.target.is_english:
			raise NotApplicable
