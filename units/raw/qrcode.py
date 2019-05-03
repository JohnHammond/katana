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
import warnings
warnings.simplefilter("ignore", UserWarning)
from PIL import Image
from pyzbar import pyzbar
import json

class Unit(units.FileUnit):

	PRIORITY = 25

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target, keywords = 'image')

		try:
			self.image = Image.open(self.target.path)
		except OSError:
			raise NotApplicable("not an image")


	def evaluate(self, katana, case):

		decoded = pyzbar.decode(self.image)

		for each_decoded_item in decoded:
			
			decoded_data = each_decoded_item.data.decode('latin-1')

			result = {
				'type': each_decoded_item.type,
				'data' : decoded_data
			}
			
			katana.recurse(self, decoded_data)
			katana.add_results(self, result)
