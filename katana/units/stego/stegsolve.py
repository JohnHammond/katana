from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import os
import re
import magic
import traceback
from PIL import Image
import PIL.ImageOps

from katana.unit import BaseUnit
from katana.units.ocr.tesseract import attempt_ocr
from katana import units
from katana.units import stego
from katana.units import raw

def get_plane(img, data, channel, index = 0):

	if channel in img.mode:
		new_image = Image.new('L', img.size)
		new_image_data = new_image.load()

		# JOHN: I pass in the data now, so it is not loaded every time.
		img_data = data
	
		channel_index = img.mode.index(channel)
		for x in range(img.size[0]):
			for y in range(img.size[1]):
				color = img_data[x, y]

				try:
					channel = color[channel_index]
				except TypeError:
					channel = color

				plane = bin(channel)[2:].zfill(8)
				try:
					new_color = 255*int(plane[abs(index-7)])
					new_image_data[x, y] = 255*int(plane[abs(index-7)])
				except IndexError:
					pass
		return new_image
	else:
		return 

class Unit(units.FileUnit):

	PRIORITY = 70
	ARGUMENTS = [
		{ 'name': 		'stegsolve_channel', 
		  'type': 		str, 
		  'default': 	"", 
		  'required': 	False,
		  'help': 		'a channel to scrape out in stegsolve, R, G, B, or A'
		},

		{ 'name': 		'stegsolve_max', 
		  'type': 		int, 
		  'default': 	8, 
		  'required': 	False,
		  'help': 		'maximum number of bits to bruteforce (without specifying --stegsolve-plane), default 1'
		},

		{ 'name': 		'stegsolve_plane', 
		  'type': 		int, 
		  'default': 	None, 
		  'required': 	False,
		  'help': 		'a bit number to scrape out in stegsolve, in range 0 to 7'
		},
	]

	# JOHN: This SHOULD be removed following the new unit argument restructure
	@classmethod
	def add_arguments(cls, katana, parser):

		parser.add_argument('--stegsolve-channel', type=str,
			help="a channel to scrape out in stegsolve, R, G, B, or A", action="append",
			default=None)
		parser.add_argument('--stegsolve-max', type=int,
			help="maximum number of bits to bruteforce (without specifying --stegsolve-plane), default 1", action="append",
			default=8)
		parser.add_argument('--stegsolve-plane', type=int,
			help="a bit number to scrape out in stegsolve, in range 0 to 7", action="append",
			default=None)

	def __init__(self, katana, target):
		# Call the parent constructor to ensure that this an image file!
		super(Unit, self).__init__(katana, target, keywords=[' image '])

		try:
			self.img = Image.open(self.target.path)

			resizing = False
			new_size = list(self.img.size)
			if self.img.size[0] > 1000:
				resizing = True
				new_size[0] = 500
			if self.img.size[1] > 1000:
				resizing = True
				new_size[1] = 500
			if resizing:
				self.img = self.img.resize(tuple(new_size), Image.ANTIALIAS)

			self.data = self.img.load()

		# If we don't know what this is, don't bother with it.
		except OSError:
			raise units.NotApplicable("cannot read file")

		except Exception:
			# JOHN: I don't know what errors this could produce... but it COULD!

			traceback.print_exc()
			raise units.NotApplicable("unknown error occured")


	def enumerate(self, katana):
		
		# Iterate through all possibilities if they supplied info for 
		# the stegsolve operation...
		if katana.config['stegsolve_channel'] is not None:
			if katana.config['stegsolve_plane'] is not None:
				yield ( katana.config['stegsolve_channel'], katana.config['stegsolve_plane'] )

			else:
				for plane in range(katana.config['stegsolve_max']):
					yield (katana.config['stegsolve_channel'], plane)
		else:
			if katana.config['stegsolve_plane'] is not None:
				for channel in [ 'R', 'G', 'B', 'A' ]:
					for given_plane in katana.config['stegsolve_plane']:
						yield (channel, given_plane)
			else:
				for plane in range(katana.config['stegsolve_max']):
					# By default, check every channel...
					for channel in [ 'R', 'G', 'B', 'A' ]:
						yield ( channel, plane )

	def evaluate(self, katana, case):
		# Grab the current case
		channel, plane = case
		
		# Carve out the needed plane
		image = get_plane(self.img, self.data, channel, plane)

		if image:
			output_path, _ = katana.create_artifact(self, f"channel_{channel}_plane_{plane}.png", create=True)
			image.save(output_path)

			# We won't recurse on this, because it does too much stuff..
			# But we can still try and hunt for flags in any found text
			# I replace newlines in here incase the flag spans multiple lines
			ocr_text = attempt_ocr(os.path.abspath(output_path))
			if ocr_text:
				if katana.locate_flags(self, ocr_text.replace('\n', '')):
				# If we do find a flag, stop this unit!!
					self.completed = True
				
			katana.add_image(os.path.abspath(output_path))