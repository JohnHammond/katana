# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-04-12 00:50:43

from pwn import *
from unit import BaseUnit
import units
import os

# This could be either a file or just plain data...
class EsotericUnit(units.PrintableDataUnit):
	
	def __init__(self, katana, parent, target):
		super(EsotericUnit, self).__init__(katana, parent, target)
