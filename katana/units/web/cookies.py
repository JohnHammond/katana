#!/usr/bin/env python3

from pwn import *
import requests
from katana.units.web import WebUnit

class Unit(WebUnit):

	PRIORITY = 30

	# We do not need to include the constructor here because
	# the WebUnit parent will already ensure this is a 
	# URL beginning with either http:// or https://
	
	def evaluate(self, katana, case):

		# Return the cookies
		result = [ vars(cookie) for cookie in self.target.request.cookies if cookie ]
		
		# Hunt for flags...
		for cookies in result:
			for cookie_name, cookie_value in cookies.items():

				## I cast this to a string because it may be a number or a bool
				## We do not need to locate flags because the recurse function
				## now does this for us...
				# katana.locate_flags(self, str(cookie_value))
				# katana.locate_flags(self, cookie_name)
				katana.recurse(self, str(cookie_value))
				katana.recurse(self, cookie_name)
				
			katana.add_results(self, cookies)
