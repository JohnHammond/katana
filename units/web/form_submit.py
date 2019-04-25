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
import units.web
import requests
import magic
import units

class Unit(units.web.WebUnit):

	def __init__(self, katana, parent, target):

		# Run the parent constructor, to ensure this is a valid URL
		super(Unit, self).__init__(katana, parent, target)
		
		if not katana.config['flag_format']:
			raise units.NotApplicable
		try:
			self.response = requests.get(self.target)
		except requests.exceptions.ConnectionError:
			raise units.NotApplicable

		self.action = re.findall(r"<\s*form.*action\s*=\s*['\"](.+?)['\"]", self.response.text, flags=re.IGNORECASE)
		self.method = re.findall(r"<\s*form.*method\s*=\s*['\"](.+?)['\"]", self.response.text, flags=re.IGNORECASE)

		# Only run this if we have potential information...
		if not (self.action and self.method):
			raise units.NotApplicable


	def evaluate(self, katana, case):

		if self.action and self.method:
			if self.action: action = self.action[0]
			if self.method: method = self.method[0]
			try:
				method = vars(requests)[method.lower()]
			except IndexError:
				log.warning("Could not find an appropriate HTTP method... defaulting to POST!")
				method = requests.post
				
		url_form = self.target.split('/')
		if len(url_form) > 3:
			last_location = '/'.join(self.target.split('/')[:-1]) + '/'
		else:
			last_location = self.target.rstrip('/') + '/'

		r = method(last_location + action, allow_redirects = True)
		
		# Keep hunting on the new location...
		katana.recurse(self, r.url)

		# Hunt for flags. If we found one, stop all other requests!
		hit = katana.locate_flags(self, r.text)

		if hit:
			self.completed = True

		# You should ONLY return what is "interesting" 
		# Since we cannot gauge the results of this payload versus the others,
		# we will only care if we found the flag.
		return None