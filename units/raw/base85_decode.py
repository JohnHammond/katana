from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.raw
import utilities
import os
import re
from units import NotApplicable
import units
import traceback
import base64
import binascii
import magic

class Unit(BaseUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		if not self.target.is_printable:
			raise NotApplicable("not printable data")

	def evaluate(self, katana, case):
		try:
			decoded = base64.b85decode(self.target.raw)

			# We want to know about this if it is printable!
			if utilities.isprintable(decoded):
				katana.recurse(self, decoded)
				katana.add_results(self, decoded)

			# if it's not printable, we might only want it if it is a file...
			else:
				magic_info = magic.from_buffer(decoded)
				if magic_info != 'data':
					katana.recurse(self, decoded)
					katana.add_results(self, decoded)
		
		except (UnicodeDecodeError, binascii.Error, ValueError):
			# This won't decode right... must not be right! Ignore it.				
			return 