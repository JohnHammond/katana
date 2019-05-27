# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-05-24 22:43:31

from pwn import *
from katana.unit import BaseUnit
from katana import units
import os

class PcapUnit(units.FileUnit):
	
	def __init__(self, katana, target):
		# This ensures that it is a file
		super(PcapUnit, self).__init__(katana, target, keywords = 'pcap')