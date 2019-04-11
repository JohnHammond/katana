# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
<<<<<<< HEAD
# @Last Modified time: 2019-03-31 17:30:48
=======
# @Last Modified time: 2019-04-10 23:49:45
>>>>>>> f024ae6a2622428ffea39a314b0237e9e8184ea2

from pwn import *
from unit import BaseUnit
import units
import os

class StegoUnit(BaseUnit):
	def __init__(self, katana, parent, target):
		super(StegoUnit, self).__init__(katana, parent, target)
		
		try:
			if not os.path.isfile(target):
				raise NotApplicable

		# JOHN: These apparently happen in Python 3 if you pass
		#       a filename that contains a null-byte... 
		except ValueError:
			raise NotApplicable
