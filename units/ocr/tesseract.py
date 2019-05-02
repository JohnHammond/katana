from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import units.forensics
import os
import utilities
import glob
from hashlib import md5
import pytesseract
from PIL import Image
import traceback

DEPENDENCIES = [ 'tesseract' ]

def attempt_ocr(image_path):

	try:
		ocr_data = pytesseract.image_to_string(Image.open(image_path))

	# This is function is meant to run as a standalone, so catch this exception
	# in case we aren't doing dependency checking...
	except pytesseract.pytesseract.TesseractNotFoundError:
		ocr_data = None

	# JOHN: I don't know when this will go wrong, but when it does....
	except :
		traceback.print_exc()
		ocr_data = None

	return ocr_data


class Unit(units.FileUnit):

	# JOHN: This MUST be in the class... 
	PROTECTED_RECURSE = True
	
	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

		if not 'image' in self.target.magic:
			raise NotApplicable("not an image")

	def evaluate(self, katana, case):

		ocr_data = attempt_ocr(self.target.path)

		if ocr_data:
			# We don't locate flags any more because recurse does this for us.
			katana.recurse(self, ocr_data)
			katana.add_results(self, ocr_data)