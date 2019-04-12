#!/usr/bin/env python3
from pwn import *
import requests
from web import WebUnit
from units import NotApplicable
from hashlib import md5

class Unit(WebUnit):

	def __init__(self, katana, parent, target):

		# Run the parent constructor, to ensure this is a valid URL
		super(WebUnit, self).__init__(katana, parent, target)
		
		# Then check if robots.txt even exists.
		# Assume that you are in fact the Google crawler.
		headers = { 'User-Agent': 'Googlebot/2.1' }

		# Try to get the robots.txt file
		r = requests.get('{0}/{1}'.format(target, 'robots.txt'), headers = headers)

		# Check if the request succeeded
		if r.status_code != 200:
			# Completely fail if there is nothing there.
			raise NotApplicable

		self.response = r


	# ''' ##############################################
	# JOHN:
	#       This code used to 'enumerate' on each result.
	#       This way it would check every page listed in the robots.txt
	#       At the time of writing (11:27 PM April 11th, 2019)
	#       ... I have not yet put this functionality back in
	# ''' ##############################################


	# def enumerate(self, katana):

	# 	# The default is to FIRST check all of robots.txt...
	# 	yield '/robots.txt'

	#     artifact_handle, artifact_path = self.artifact(katana, 'robots_%s' % md5(self.target).hexdigest())
	   
	#     self.find_flags(r.text)
	#     with f:
	#         f.write(r.text)

	#     RESULTS.update({ target : {} })
		
	#     RESULTS[target][self.unit_name] = {
	#         'findings': [],
	#         'artifact': name
	#     }

		# Look for disallow entries and add them to the findings
		# for line in r.text.split('\n'):
		#     line = line.strip().split(':')
		#     if line[0].strip().startswith('#'):
		#         # This is a comma
		#         continue
		#     elif len(line) == 1:
		#         # This line is empty for some reason
		#         continue
			
		#     RESULTS[target][self.unit_name]['findings'].append(':'.join(line))

			# Yield each link, so we can retrieve it and hunt for flags inside of evaluate()
			# yield line[1], '{0}/{1}'.format(stripped_target, line[1]) 
	
	def evaluate(self, katana, case):

		disallowed_entries = {}
		# Look for disallow entries and add them to the findings
		for line in self.response.text.split('\n'):
			pieces = line.strip().split(':')
			if pieces[0].strip().startswith('#'):
				# This is a comment
				continue
			elif len(pieces) == 1:
				# This line is empty for some reason
				continue

			self.locate_flags(katana, line)
			katana.recurse(self, line)
			katana.add_results(self, line)