import requests
import magic
import re
import os
import hashlib
from io import StringIO, BytesIO
import string
import enchant
import mmap

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
		self.parent = parent
		self.upstream = upstream
		self.is_printable = True
		self.is_english = True
		self.is_image = False
		self.is_base64 = False
		self.is_url = ADDRESS_REGEX.match(self.upstream) is not None
		# This zero test is here because os.path.isfile chokes on a null-byte
		self.is_file = 0 not in self.upstream and os.path.isfile(self.upstream)
		
		self.magic = 'data'

		if self.is_file:
			is_sub_target = True
			is_sub_results = True
			results_path = os.path.realpath(katana.config['outdir'])
			if katana.original_target is not None and katana.original_target.is_file:
				base_target_path = os.path.dirname(katana.original_target.path)
				base_target_path = os.path.realpath(base_target_path)
				if not upstream.startswith(bytes(str(base_target_path), 'utf-8')+b'/'):
					is_sub_target = False

			if not upstream.startswith(bytes(results_path+'/', 'utf-8')):
				is_sub_results = False

			if not is_sub_results and not is_sub_target:
				self.is_file = False
			

		# Download the target of a URL
		if self.is_url:
			self.url_root = '/'.join(upstream.decode('utf-8').split('/')[:3]) + '/'
			if not katana.config['no_download']:
				try:
					url_accessible = True
					self.request = requests.get(upstream)
				except requests.exceptions.ConnectionError:
					url_accessible = False
					self.is_url = False
				
				self.url_root = '/'.join(upstream.decode('utf-8').split('/')[:3]) + '/'
				
				if url_accessible:
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
					# This is if we COULDN'T download the page...
					# we just treat the content as the upstream
					self.content = self.upstream
			else:
				self.content = self.upstream
				try:
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
			if self.path:
				katana.add_image(os.path.abspath(self.path))
			self.is_image = True
		
		# CALEB: if we do this, do we need strings?
		#katana.locate_flags(parent, self.raw)

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
	
	def __repr__(self):
		try:
			return self.upstream.decode('utf-8')
		except:
			return repr(self.upstream)

	def __getitem__(self, key):
		if isinstance(key, slice):
			try:
				return ''.join([ self.upstream.decode('utf-8')[ii] for ii in
						range(*key.indices(len(self.upstream.decode('utf-8')))) ])
			except UnicodeDecodeError:
				return ''.join([ self.upstream.decode('latin-1')[ii] for ii in
						range(*key.indices(len(self.upstream.decode('latin-1')))) ])

	@property
	def raw(self):
		""" This will return a bytes-like object. For small objects already
			in memory, it will return the bytes object. For files or larger
			objects not in memory, it will return an mmap object, which will
			act the same as a bytes object in most situations.
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
	def stream(self):
		if self.content is not None:
			return BytesIO(self.content)
		elif self.is_file:
			return open(self.path, 'rb')
		else:
			return BytesIO(self.upstream)
