#!/usr/bin/env python3
from pwn import *
import requests
from units import NotApplicable
from web import WebUnit

# JOHN: March 24th
# I'm not going to finish implementing the actual download
# of a github repo right now -- but will check to see if
# one exists
# Code ideas come from: https://github.com/internetwache/GitTools/

class Unit(WebUnit):

	def __init__(self, katana, parent, target):

		# Run the parent constructor, to ensure this is a valid URL
		super(Unit, self).__init__(katana, parent, target)

		# Try to get see if there is a .git directory
		url = '{0}/{1}'.format(self.target.url_root.rstrip('/'), '.git/HEAD')

		try:
			r = requests.get(url, allow_redirects=False)
		except (requests.exceptions.ConnectionError,):
			raise NotApplicable('cannot reach server')

		# If the response is anything other than a "Not Found",
		# we might have something here...
		if r.status_code == 404:
			raise NotApplicable('http response 404 at /.git/HEAD')
		else:
			self.response = r
	
	def evaluate(self, katana, case):

		# JOHN: I do still need to add the functionality to download
		#	   the repo. Right now, if it sees that it exists, though
		#	   just tell the user.

		katana.add_results( self,  self.target.url_root.rstrip('/') + '/.git' )