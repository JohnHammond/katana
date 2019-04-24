#!/usr/bin/env python3
from pwn import *
import requests
from web import WebUnit
from units import NotApplicable
from hashlib import md5

bad_starting_links = [
	'#', 'javascript:', 'https://', 'http://', '//'
]

def has_a_bad_start(link):
	for bad_start in bad_starting_links:
		if link.startswith(bad_start):
			return False
	else:
		return True

class Unit(WebUnit):

	# We don't really want to spider on EVERYTHING and start an infinite loop..
	# We can protect against this once we create a target object
	# and start to "keep track" of links we find in one specific website target
	PROTECTED_RECURSE = True

	def __init__(self, katana, parent, target):

		# Run the parent constructor, to ensure this is a valid URL
		super(Unit, self).__init__(katana, parent, target)

		# Check if this is an web address we can reach...
		try:
			self.response = requests.get(target)
		except requests.exceptions.ConnectionError:
			raise NotApplicable

		# Check if the request succeeded
		if self.response.status_code != 200:
			# Completely fail if there is nothing there.
			raise NotApplicable

	def evaluate(self, katana, url):

		links = re.findall(r'href=[\'"](.+?)[\'"]', self.response.text, flags = re.IGNORECASE)

		# Remove anything that might not be local
		links = list(filter(has_a_bad_start, links))
		
		for link in links:
			new_link = '{0}/{1}'.format(self.target.rstrip('/'), link.lstrip('/'))

			# All this does is find is new links. 
			# It won't contain flags and they don't need to be considered results
			if new_link:
				katana.recurse(self, new_link)
				katana.add_results(self, new_link)
