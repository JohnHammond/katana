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
import base64

class Unit(units.raw.RawUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		base64_pattern = '[a-zA-Z0-9+/]+={0,2}'
		base64_regex = re.compile(base64_pattern, flags=re.MULTILINE | \
														re.DOTALL |    \
														re.IGNORECASE  )

		base64_result = base64_regex.search(str(self.target))

		if base64_result is None:
			raise NotApplicable
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
		katana.add_result( self, 'result', decoded )
