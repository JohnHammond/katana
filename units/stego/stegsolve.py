from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import os
import units.raw
import re
import units.stego
import magic
import traceback
import units
from PIL import Image
import PIL.ImageOps

def get_plane(img, channel, index = 0):

	if channel in img.mode:
		new_image = Image.new('L', img.size)
		new_image_data = new_image.load()

		img_data = img.load()
	
		channel_index = img.mode.index(channel)
		for x in range(img.size[0]):
			for y in range(img.size[1]):
				color = img_data[x, y]

				channel = color[channel_index]

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

	@classmethod
	def add_arguments(cls, katana, parser):

		parser.add_argument('--stegsolve-channel', type=str,
			help="a channel to scrape out in stegsolve, R, G, B, or A", action="append",
			default=None)
		parser.add_argument('--stegsolve-max', type=int,
			help="maximum number of bits to bruteforce (without specifying --stegsolve-plane), default 1", action="append",
			default=1)
		parser.add_argument('--stegsolve-plane', type=int,
			help="a bit number to scrape out in stegsolve, in range 0 to 7.", action="append",
			default=None)

	def __init__(self, katana, parent, target):
		# Call the parent constructor to ensure that this an image file!
		super(Unit, self).__init__(katana, parent, target, keywords=[' image '])


		try:
			self.img = Image.open(self.target.path)

		# If we don't know what this is, don't bother with it.
		except OSError:
			raise units.NotApplicable

		except Exception:
			# JOHN: I don't know what errors this could produce... but it COULD!

			traceback.print_exc()
			raise units.NotApplicable


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
					yield (channel, katana.config['stegsolve_plane'])
			else:
				for plane in range(katana.config['stegsolve_max']):
					# for channel in [ 'R', 'G', 'B', 'A' ]:
					for channel in [ 'R' ]:
						yield ( channel, plane )

	def evaluate(self, katana, information):

		# Grab the current case
		channel, plane = information
		
		# Carve out the needed plane
		image = get_plane(self.img, channel, plane)
		if image:
			output_path, _ = katana.create_artifact(self, f"channel_{channel}_plane_{plane}.png", create=True)
			image.save(output_path)

			# JOHN:  Because this is our generated image. we will NOT recurse and NOT hunt for flags! 
			# katana.add_image(self, os.path.abspath(output_path))
			katana.add_image(os.path.abspath(output_path))