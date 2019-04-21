# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-04-21 15:14:19

from pwn import *
from unit import BaseUnit
import units
import os

class PdfUnit(units.FileUnit):
	
	def __init__(self, katana, parent, target):
		# This ensures it is a PDF
		super(PdfUnit, self).__init__(katana, parent, target, keywords=['pdf document', 'data'])