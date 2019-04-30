# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-04-30 18:19:02

from pwn import *
from unit import BaseUnit
import units
import os
from units import NotApplicable

class WebUnit(BaseUnit):
	
	def __init__(self, katana, parent, target):

		super(WebUnit, self).__init__(katana, parent, target)
		
		if not self.target.is_url:
			raise NotApplicable("not a web url")
