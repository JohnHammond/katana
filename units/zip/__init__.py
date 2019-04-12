# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-04-12 01:53:49

from pwn import *
from unit import BaseUnit
import units
import os

class ZipUnit(units.FileUnit):
	
	def __init__(self, katana, parent, target):
		# This ensures it is a ZIP
		super(ZipUnit, self).__init__(katana, parent, target, keywords=['zip archive'])