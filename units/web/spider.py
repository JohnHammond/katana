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

	PRIORITY = 30

	# We don't really want to spider on EVERYTHING and start an infinite loop..
	# We can protect against this once we create a target object
	# and start to "keep track" of links we find in one specific website target
	PROTECTED_RECURSE = True

	def evaluate(self, katana, url):

		links = re.findall(r'href=[\'"](.+?)[\'"]', self.target.content.decode('utf-8'), flags = re.IGNORECASE)

		# Remove anything that might not be local
		links = list(filter(has_a_bad_start, links))
		
		url_form = self.target.upstream.decode('utf-8').split('/')
		if len(url_form) > 3:
			last_location = '/'.join(url_form[:-1]) + '/'
		else:
			last_location = self.target.upstream.decode('utf-8').rstrip('/')

		for link in links:
			new_link = '{0}/{1}'.format(last_location, link.lstrip('/'))
			
			# All this does is find is new links. 
			# It won't contain flags and they don't need to be considered results.
			if new_link:
				katana.recurse(self, new_link)
				katana.add_results(self, new_link)