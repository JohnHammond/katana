#!/usr/bin/env python3
from PIL import Image
import traceback
import os

from katana.unit import FileUnit, NotApplicable
from katana.manager import Manager
from katana.target import Target

def get_plane(img, data, channel, index=0):
	""" Get a plane of an image? I don't know. I didn't write this. """
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
					new_color = 255 * int(plane[abs(index - 7)])
					new_image_data[x, y] = 255 * int(plane[abs(index - 7)])
				except IndexError:
					pass
		return new_image
	else:
		return

class Unit(FileUnit):

	# Low priority
	PRIORITY = 70
	# Prevent recursion into self
	RECURSE_SELF = False
	# Groups we belong to
	GROUPS = ['stego', 'image']
	# Blocked groups
	BLOCKED_GROUPS = ['stego']

	def __init__(self, manager: Manager, target: Target):
		# Call the parent constructor to ensure that this an image file!
		super(Unit, self).__init__(manager, target, keywords=[' image '])

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
			raise units.NotApplicable("unknown error occured")

	def enumerate(self):
		channel = self.manager[str(self)].get('channel', '')
		plane = self.manager[str(self)].get('plane', '')
		# Default to 4 planes
		max_plane = self.manager[str(self)].getint('max-plane', 4)

		# Try to decode planes
		try:
			planes = [int(x) for x in plane.split(',')]
		except (ValueError, AttributeError):
			# By default select up to max-plane planes
			planes = range(max_plane)

		# Try to decode channels
		channels = channel.upper()
		channels = ''.join([c for c in channels if c in 'RGBA'])

		# By default, select all channels
		if len(channels) == 0:
			channels = 'RGBA'

		# Yield all plane options
		for plane in planes:
			for channel in channels:
				yield (channel, plane)


	def evaluate(self, case):
		# Grab the current case
		channel, plane = case

		# Carve out the needed plane
		image = get_plane(self.img, self.data, channel, plane)

		if image:
			# Create the artifact
			output_path, _ = self.generate_artifact(f"channel_{channel}_plane_{plane}.png",
					create=True)
			image.save(output_path)

			# Register the artifact with the manager
			self.manager.register_artifact(self, artifact_path)
