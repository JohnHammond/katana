#!/usr/bin/env python
"""
Classes and methods wrapping arbitrary files and data into a common Target
interface for units.
"""
from __future__ import annotations
from typing import Any, List, BinaryIO
from io import StringIO, BytesIO
import requests
import hashlib
import enchant
import string
import magic
import mmap
import re
import os


ADDRESS_PATTERN = rb'^((?P<protocol>http|https):\/\/)(?P<host>[a-zA-Z0-9][a-zA-Z0-9\-_.]*)(:(?P<port>[0-9]{1,5}))?(\/(?P<uri>[^?]*))?(\?(?P<query>.*))?$'
BASE64_PATTERN = rb'^[a-zA-Z0-9+/]+={0,2}$'
LETTER_PATTERN = rb'[A-Za-z]+'
LETTER_REGEX = re.compile(LETTER_PATTERN, re.DOTALL | re.MULTILINE)
BASE64_REGEX = re.compile(BASE64_PATTERN, re.DOTALL | re.MULTILINE)
ADDRESS_REGEX = re.compile(ADDRESS_PATTERN, re.DOTALL | re.MULTILINE)
DICTIONARY = enchant.Dict()
DICTIONARY_THRESHOLD = 1
PRINTABLE_BYTES = bytes(string.printable, 'utf-8')
BASE64_BYTES = bytes(string.ascii_letters+string.digits+'=', 'utf-8')

class Target(object):

	def __init__(self, manager: katana.manager.Manager, upstream: bytes,
			parent: katana.unit.Unit = None):

		# The target class expects the upstream to be bytes
		if isinstance(upstream, str):
			upstream = upstream.encode('utf-8')

		# Initialize local variables
		self.upstream = upstream
		self.parent = parent
		self.is_printable = True
		self.is_english = True
		self.is_image = False
		self.is_base64 = False
		self.path = False
		self.completed = False

		# Parse out URL pieces (also decide if this is a URL)
		self.url_pieces = ADDRESS_REGEX.match(self.upstream)
		self.is_url = self.url_pieces is not None
		# This zero test is here because os.path.isfile chokes on a null-byte
		self.is_file = 0 not in self.upstream and os.path.isfile(self.upstream)
		
		# Initial assumed libmagic file type is just "data"
		self.magic = 'data'

		# Analyze a file target
		if self.is_file:

			# Assume initially that it is not a file on this system
			is_sub_target = True
			is_sub_results = True

			# Grab the full path to the output/artifacts directory
			results_path = os.path.realpath(manager['manager']['outdir'])

			# Check if this is a subdirectory of the origin/base target in this
			# chain, if there is a chain
			if parent is not None:
				origin = parent.origin
				if origin.is_file:
					base_target_path = os.path.dirname(origin.path)
					base_target_path = os.path.realpath(base_target_path)
					if not upstream.startswith(bytes(str(base_target_path), 'utf-8')+b'/'):
						is_sub_target = False
			else:
				is_sub_target = True

			# Is this a sub-directory of the base results/output directory?
			if not upstream.startswith(bytes(results_path+'/', 'utf-8')):
				is_sub_results = False

			# We only analyze things as files if they are either
			# sub-directories/files of the original target or of the results
			# directory itself
			if not is_sub_results and not is_sub_target:
				self.is_file = False
			

		# Download the target of a URL
		if self.is_url:
			self.url_root = '/'.join(upstream.decode('utf-8').split('/')[:3]) + '/'
			if manager['manager'].getboolean('download'):
				try:
					url_accessible = True
					self.request = requests.get(upstream)
				except requests.exceptions.ConnectionError:
					url_accessible = False
					self.is_url = False
					self.content = self.upstream
				else:	
					self.content = self.request.content
					self.path, filp = katana.create_artifact(parent,
							hashlib.md5(upstream).hexdigest(),
							mode='wb', create=True
						)
					# JOHN: This used to happen in web.request but it was silly
					katana.locate_flags(parent, self.content)
					with filp:
						filp.write(self.content)
					self.is_file = True
					# Carve out the root of the URL
			else:
				# We were asked not to download URLs
				self.content = self.upstream
				try:
					# CALEB: I don't know why we are ignoring the download
					# option here...
					self.request = requests.get(self.upstream)
				except requests.exceptions.ConnectionError:
					self.is_url = False

		# Save the path to the file
		elif self.is_file:
			self.content = None
			self.path = self.upstream
		else:
			# This is raw data. There is no file/path associated.
			self.path = None
			self.content = upstream

		if isinstance(self.path, bytes):
			self.path = self.path.decode('utf-8')

		# Grab the file type from libmagic (both for files and raw buffers)
		if self.is_file:
			self.magic = magic.from_file(self.path)
		else:
			self.magic = magic.from_buffer(self.content)

		# JOHN: Add a test to determine if this is in fact an image
		if 'image' in self.magic.lower():
			# CALEB: Not sure how I want to handle this in the new version...
#			if self.path:
#				katana.add_image(os.path.abspath(self.path))
			self.is_image = True
		
		# CALEB: if we do this, do we need strings?
		#katana.locate_flags(parent, self.raw)

		# CALEB: This used to happen in a separate unit but it was silly
		# ALSO CALEB: But... why? How would there be a flag in the magic
		# results? :?
		#katana.locate_flags(parent, self.magic)

		all_words = 0
		english_words = 0

		# Hash the target content for comparison to previous
		# targets by Katana. This prevents recursion on the
		# same target type.
		self.hash = hashlib.md5()
		with self.stream as st:
			for chunk in iter(lambda: st.read(4096), b''):
				# Update the hash with this chunk
				self.hash.update(chunk)
				
				# Did we already rule out printable?
				if not self.is_printable:
					continue

				# Check if this chunk is printabale
				for c in chunk:
					if not c in PRINTABLE_BYTES:
						self.is_printable = False
						self.is_base64 = False
						self.is_english = False
						break
					elif c not in BASE64_BYTES:
						self.is_base64 = False

				# If we found a non-printable character, abort
				if not self.is_printable or not self.is_english:
					continue

				# Check how many english words this chunk contains
				word_list = list(filter(lambda word : len(word)>2, LETTER_REGEX.findall(chunk)))
				all_words += len(word_list)
				english_words += len(list(filter(
					lambda word : len(word)>2, [word for word in word_list if DICTIONARY.check(word.decode('utf-8'))]
				)))

		# If we haven't already decided, check if we think this is english
		if self.is_english:
			self.is_english = english_words >= (all_words - DICTIONARY_THRESHOLD) and english_words != 0

		# JOHN: This is a patch to handle relative file paths, because apparently
		#       we didn't....
		if self.path and self.path.startswith('./'):
			self.path = os.path.abspath(self.path)

	def __repr__(self):
		""" Create a representation of this object based on it's upstream path
		"""
		try:
			return self.upstream.decode('utf-8')
		except:
			return repr(self.upstream)
	
	def __getitem__(self, key):
		""" Get a slice of the upstream... this seems very inneficient, but it
		was in the old version, and I don't want to break too much... """

		if isinstance(key, slice):
			try:
				return ''.join([ self.upstream.decode('utf-8')[ii] for ii in
						range(*key.indices(len(self.upstream.decode('utf-8')))) ])
			except UnicodeDecodeError:
				return ''.join([ self.upstream.decode('latin-1')[ii] for ii in
						range(*key.indices(len(self.upstream.decode('latin-1')))) ])

	@property
	def raw(self) -> str:
		""" Return a bytes-like object for any given target type:

			- Files/content already in memory: return self.content
			- Files already written to disk: return a mmap object
			- For all other unknown data: return self.upstream directly
		"""
		if self.content is not None:
			return self.content
		elif self.path is not None:
			with open(self.path, 'rb') as f:
				try:
					return mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
				except ValueError:
					return self.upstream
		else:
			return self.upstream
	
	@property
	def stream(self) -> BinaryIO:
		""" Return a file-like object for any given target type:

			- Files/content already in memory: return a BytesIO object
			- Files already written to disk: return an binary file handle
			- For all other unknown data: return a BytesIO object of upstream
		"""
		if self.content is not None:
			return BytesIO(self.content)
		elif self.is_file:
			return open(self.path, 'rb')
		else:
			return BytesIO(self.upstream)

	@property
	def web_protocol(self) -> str:
		""" if this is a URL, return the protocol """
		if self.is_url:
			val = self.url_pieces.groupdict()['protocol']
			return val.decode() if isinstance(val, bytes) else val
		else:
			return None

	@property
	def web_host(self) -> str:
		""" if this is a URL, return the hostname """
		if self.is_url:
			val = self.url_pieces.groupdict()['host']
			return val.decode('utf-8') if isinstance(val, bytes) else val
		else:
			return None

	@property
	def web_port(self) -> str:
		""" if this is a URL, return the port number """
		if self.is_url:
			val = self.url_pieces.groupdict()['port']
			return val.decode('utf-8') if isinstance(val, bytes) else val
		else:
			return None

	@property
	def web_uri(self) -> str:
		""" if this is a url, return the URI """
		if self.is_url:
			val = self.url_pieces.groupdict()['uri']
			return val.decode('utf-8') if isinstance(val, bytes) else val
		else:
			return None

	@property
	def web_query(self) -> str:
		""" if this is a url, return the query string """
		if self.is_url:
			val = self.url_pieces.groupdict()['query']
			return val.decode('utf-8') if isinstance(val, bytes) else val
		else:
			return None

	@property
	def website_root(self) -> str:
		""" if this is a url, return the root of the URL (without any URI) """
		if self.is_url:
			if self.web_port:
				return f"{self.web_protocol}://{self.web_host}:{self.web_port}/"
			else:
				return f"{self.web_protocol}://{self.web_host}/"

	@property
	def is_website_root(self) -> bool:
		""" if this is a URL, return whether we are at the root of the URL """
		return self.upstream.decode('utf-8') == self.website_root \
			and not self.web_uri and not self.web_query

	@property
	def is_webpage(self) -> bool:
		""" Opposite of is_website_root? """
		return bool(self.upstream.decode('utf-8') != self.website_root \
			and self.web_uri)
