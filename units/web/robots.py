#!/usr/bin/env python3
from pwn import *
import requests
from web import WebUnit
from units import NotApplicable
from hashlib import md5

# Assume that you are in fact the Google crawler.
headers = { 'User-Agent': 'Googlebot/2.1' }


class Unit(WebUnit):

	def __init__(self, katana, parent, target):

		# Run the parent constructor, to ensure this is a valid URL
		super(Unit, self).__init__(katana, parent, target)
		
		if not self.target.endswith('/'):
			raise NotApplicable

		# Try to get the robots.txt file
		try:
			r = requests.get('{0}/{1}'.format(target, 'robots.txt'), headers = headers)
		except requests.exceptions.ConnectionError:
			raise NotApplicable

		# Check if the request succeeded
		if r.status_code != 200:
			# Completely fail if there is nothing there.
			raise NotApplicable

		self.response = r
		katana.locate_flags(self, r.text)

	def enumerate(self, katana):

		robots_data = self.response.text
		disallowed_entries = {}
		# Look for disallow entries and add them to the findings
		for line in robots_data.split('\n'):
			pieces = line.strip().split(':')
			action, url = pieces[0], ':'.join(pieces[1:]).strip()

			# Ignore comments and empty lines
			if action.strip().startswith('#') or len(pieces) == 1: continue
						
			katana.add_results(self, line)
			if action.lower().startswith('disallow'):
				yield url
	
	def evaluate(self, katana, url):

		new_url = '{0}/{1}'.format(self.target.rstrip('/'), url.lstrip('/'))
		r = requests.get(new_url, headers = headers)

		katana.locate_flags(self, r.text)

		# JOHN: I do not recurse in here, because this is a whole new page I am retrieving...
		#       And I do not add results, because that is done in the `enumerate` function
		#       in this case, interestingly enough.
		# katana.recurse(self, line)
		# katana.add_results(self, line)
