import requests
import magic
import re
import os
import hashlib
from io import StringIO, BytesIO
import string
import enchant

ADDRESS_PATTERN = rb'^((http|https):\/\/)(?P<host>[a-zA-Z0-9][a-zA-Z0-9\-_.]*)(:(?P<port>[0-9]{1,5}))?(\/(?P<uri>[^?]*))?(\?(?P<query>.*))?$'
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
	""" A Katana target.

		This class encapsulates all interactions that units should
		have with a target while abstracting away the details.

		For example, a unit may look at only the upstream, but want
		to ensure that it is a URL or a file. Similarly, a unit may
		not care what type of target it was, but simply want a file-
		like object to use for processing.
	"""

	def __init__(self, katana, upstream, parent=None):

		# The target class operates entirely off of bytes
		if isinstance(upstream, str):
			upstream = upstream.encode('utf-8')

		# Initialize internal properties
		self.katana = katana
		self.upstream = upstream
		self.is_printable = True
		self.is_english = True
		self.is_base64 = False
		self.is_url = ADDRESS_REGEX.match(self.upstream) is not None
		self.is_file = 0 not in self.upstream and os.path.isfile(self.upstream)
		self.magic = 'data'

		# Download the target of a URL
		if self.is_url:
			self.content = requests.get(upstream).content
			self.path, filp = katana.create_artifact(parent,
					hashlib.md5(upstream).hexdigest(),
					mode='wb', create=True
				)
			with filp:
				filp.write(self.content)
			self.is_file = True
		# Save the path to the file
		elif self.is_file:
			self.content = None
			self.path = self.upstream
		else:
			# This is raw data. There is no file/path associated.
			self.path = None
			self.content = upstream

		# Grab the file type from libmagic (both for files and raw buffers)
		if self.is_file:
			self.magic = magic.from_file(self.path)
		else:
			self.magic = magic.from_buffer(self.content)

		# CALEB: This used to happen in a separate unit but it was silly
		katana.locate_flags(parent, self.magic)

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
	
	@property
	def raw(self):
		if self.content is not None:
			return self.content
		elif self.path is not None:
			with open(self.path, 'rb') as f:
				return f.read()
		else:
			return self.upstream
	
	@property
	def stream(self):
		if self.content is not None:
			return BytesIO(self.content)
		elif self.is_file:
			return open(self.path, 'rb')
		else:
			return BytesIO(self.upstream)


