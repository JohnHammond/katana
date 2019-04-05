# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-03-31 17:30:48

from pwn import *
from unit import BaseUnit
import units
import os

class StegoUnit(BaseUnit):
	def __init__(self, katana):
		super(StegoUnit, self).__init__(katana)
		if not os.path.exists(katana.target):
			raise units.NotApplicable()
