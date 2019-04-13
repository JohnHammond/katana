# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-04-13 17:02:22

from pwn import *
from unit import BaseUnit
import units
import os
from units import NotApplicable


ADDRESS_PATTERN = r'^((?P<proto>[a-zA-Z][a-zA-Z0-9]*):\/\/)(?P<host>[a-zA-Z0-9][a-zA-Z0-9\-_.]*)(:(?P<port>[0-9]{1,5}))?(\/(?P<uri>[^?]*))?(\?(?P<query>.*))?$'

class WebUnit(BaseUnit):
	
	def __init__(self, katana, parent, target):

		super(WebUnit, self).__init__(katana, parent, target)
		
		self.regex = re.compile(ADDRESS_PATTERN)
		match = self.regex.match(target)
		# print(match)
		if match is None:
			raise NotApplicable