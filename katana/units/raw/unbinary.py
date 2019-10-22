#!/usr/bin/env python3
from typing import Any
import binascii
import magic
import re

from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable
from katana.manager import Manager
from katana.target import Target
import katana.util

BINARY_PATTERN = rb'[01]{8,}'
BINARY_REGEX = re.compile(BINARY_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)

class Unit(BaseUnit):
	PRIORITY = 25

	def __init__(self, manager: Manager, target: Target):
		super(Unit, self).__init__(manager, target)

		self.matches = BINARY_REGEX.findall(self.target.raw)

		if self.matches is None:
			raise NotApplicable("no binary data found")

	def evaluate(self, case: Any):

		# Next, attempt decode with 8-bit integers
		binary = b''.join(self.matches)
		raw = []
		for i in range(0, len(binary), 8):
			raw.append(chr(int(binary[i:i+8], 2)))
		raw = ''.join(raw)

		# Register the data
		self.manager.register_data(self, raw)
		
		# Next, with 7-bit
		binary = b''.join(self.matches)
		raw = []
		for i in range(0, len(binary), 7):
			raw.append(chr(int(binary[i:i+7], 2)))
		raw = ''.join(raw)
		
		# Register the data
		self.manager.register_data(self, raw)

		for result in self.matches:
			# Decode it!!!!
			decimal = int(result, 2)
			try:
				# Get a binary representation of the data
				result = binascii.unhexlify(hex(decimal)[2:])
			# If this fails, it's probably not binary we can deal with...
			except (UnicodeDecodeError, binascii.Error):
				return

			if katana.util.isprintable(result):
				# If it's printable save the results
				self.manager.register_data(self, result)
			else:
				# if it's not printable, we might only want it if it is a file...
				magic_info = magic.from_buffer(result)
				if katana.util.is_good_magic(magic_info):
					# Generate a new artifact
					filename, handle = self.generate_artifact("decoded",
							mode='wb', create=True)
					handle.write(result)
					handle.close()
					# Register the artifact
					self.manager.register_artifact(self, filename)
