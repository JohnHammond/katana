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
import base64

class Unit(units.FileOrDataUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		PATTERN = re.compile( '[a-zA-Z0-9+/]+={0,2}', flags=re.MULTILINE | \
								re.DOTALL | re.IGNORECASE  )
		base64_result = PATTERN.search(str(self.target))

		if base64_result is None:
			raise NotApplicable()
		else:
			self.base64_result = base64_result


	def evaluate(self, katana, case):
		try:
			decoded = base64.b64decode(self.base64_result.group()).decode('utf-8')
		except:
			# This won't decode right... must not be right!
			return

		katana.recurse(self, decoded)

		katana.locate_flags( decoded )
		katana.add_results( self, decoded )
