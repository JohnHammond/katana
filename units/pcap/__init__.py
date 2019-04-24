# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-04-23 20:23:40

from pwn import *
from unit import BaseUnit
import units
import os

class PcapUnit(units.FileUnit):
	
	def __init__(self, katana, parent, target):
		# This ensures that it is a file
		super(PcapUnit, self).__init__(katana, parent, target, keywords = 'pcap')