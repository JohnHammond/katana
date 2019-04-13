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
import magic
from units import NotApplicable
from PIL import Image
from pyzbar.pyzbar import decode
import json

class Unit(units.FileUnit):

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target, keywords = 'image')

		try:
			self.decoded = decode(Image.open(self.target))
		except OSError:
			raise NotApplicable


	def evaluate(self, katana, case):


		for each_decoded_item in self.decoded:
			result = {
				'type': each_decoded_item.type,
				'data' : each_decoded_item.data.decode('latin-1')
			}
			
			katana.add_results(self, result)