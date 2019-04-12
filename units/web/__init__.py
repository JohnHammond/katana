# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-04-11 23:17:06

from pwn import *
from unit import BaseUnit
import units
import os

class WebUnit(BaseUnit):
	
	def __init__(self, katana, parent, target):

		# Web units should only operate if given a URL.
		if target.startswith('http://') or target.startswith('https://'):
			target = target.rstrip('/').rstrip('\\')
			super(WebUnit, self).__init__(katana, parent, target)
		else:
			raise NotApplicable