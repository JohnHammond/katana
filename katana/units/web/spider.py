#!/usr/bin/env python3
from pwn import *
import requests
from katana.units.web import WebUnit
from katana.units import NotApplicable
from hashlib import md5

bad_starting_links = [
	b'#', b'javascript:', b'https://', b'http://', b'//'
]

def has_a_bad_start(link):
	for bad_start in bad_starting_links:
		if link.startswith(bad_start):
			return False
	else:
		return True

class Unit(WebUnit):

	PRIORITY = 20

	# We don't really want to spider on EVERYTHING and start an infinite loop..
	# We can protect against this once we create a target object
	# and start to "keep track" of links we find in one specific website target
	PROTECTED_RECURSE = True

	BAD_MIME_TYPES = [ 'application/octet-stream' ]

	def __init__(self, katana, target):
		super(Unit, self).__init__(katana, target)

		if 'Content-Disposition' in self.target.request.headers:
			if 'attachment' in self.target.request.headers['Content-Disposition']:
				raise NotApplicable('spider cannot handle attachments')

		if 'Content-Type' in self.target.request.headers:
			content_type = self.target.request.headers['Content-Type'].lower()
			for bad_type in self.BAD_MIME_TYPES:
				if bad_type in content_type:
					raise NotApplicable(
							'spider does not support {0} files'.format(bad_type)
						)

	def evaluate(self, katana, url):

		links = re.findall(rb'href=[\'"](.+?)[\'"]',
				self.target.content, flags = re.IGNORECASE)
		
		# Remove anything that might not be local
		links = list(filter(has_a_bad_start, links))
		
		url_form = self.target.upstream.decode('utf-8').split('/')
		if len(url_form) > 3:
			last_location = '/'.join(url_form[:-1])
		else:
			last_location = self.target.upstream.decode('utf-8').rstrip('/')

		for link in links:
			new_link = '{0}/{1}'.format(last_location, link.decode('utf-8').lstrip('/'))
			
			# All this does is find is new links. 
			# It won't contain flags and they don't need to be considered results.
			if new_link:
				katana.recurse(self, new_link)
				katana.add_results(self, new_link)
