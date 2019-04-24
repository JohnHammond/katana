#!/usr/bin/env python3
from pwn import *
import requests
from web import WebUnit
from units import NotApplicable
from hashlib import md5

class Unit(WebUnit):

	def __init__(self, katana, parent, target):

		# Run the parent constructor, to ensure this is a valid URL
		super(Unit, self).__init__(katana, parent, target)

		# Check if this is an web address we can reach...
		try:
			# JOHN: I tinker with cookies and user-agent here, cuz why not?
			self.response = requests.get(target, cookies = {"admin": "1"}, headers = { 'User-Agent': 'Googlebot/2.1' })
		except requests.exceptions.ConnectionError:
			raise NotApplicable

		# Check if the request succeeded
		if self.response.status_code != 200:
			# Completely fail if there is nothing there.
			raise NotApplicable

	def evaluate(self, katana, url):

		katana.locate_flags(self, self.response.text)

		# JOHN: I do not recurse in here, because this is a whole new page I am retrieving...
		#       And I do not add results, because that is done in the `enumerate` function
		#       in this case, interestingly enough.
		# katana.recurse(self, line)
		# katana.add_results(self, line)
