import requests
import magic

class Target(object):
	""" A Katana target.

		This class encapsulates all interactions that units should
		have with a target while abstracting away the details.

		For example, a unit may look at only the upstream, but want
		to ensure that it is a URL or a file. Similarly, a unit may
		not care what type of target it was, but simply want a file-
		like object to use for processing.
	"""

	def __init__(self, katana, upstream):
		self.known_types = {}
		self.katana = katana
		self.upstream = upstream
		self.types = []

		# Download the target of a URL
		if self.is_url:
			self._content = requests.get(upstream).content
			filp, self._path = katana.create_artifact(None,
					hashlib.md5(upstream).hexdigest(),
					mode='wb', create=True
				)
			with filp:
				filp.write(self._content)
		# Save the path to the file
		elif self.is_file:
			self._content = None
			self._path = self.upstream
		else:
			# This is raw data. There is no file/path associated.
			self._path = None
			self._content = upstream

		# Hash the target content for comparison to previous
		# targets by Katana. This prevents recursion on the
		# same target type.
		self.hash = hashlib.md5()
		with self.stream as st:
			for chunk in iter(lambda: st.read(4096)):
				self.hash.update(chunk)
	
	@property
	def is_url(self):
		""" Check if the upstream refers to a URL """
		# Match with REGEX
		return False
	
	@property
	def is_file(self):
		""" This is used internally. If you want to know if the target has
			a local file that represents its content, you should use
			is_artifact. Further, `stream` will return an open stream
			on the data no matter the type (web URL, file or raw data)
		"""
		if os.path.isfile(self.upstream):
			return True
		return False

	@property
	def is_artifact(self):
		""" Identify whether this file is backed with some sort of artifact
			This could either be the original target name or an artifact
			created by katana.
		"""
		return self._path is not None

	@property
	def raw(self):
		if self._content is not None:
			return self._content
		elif self._path is not None:
			with open(self._path, 'rb') as f:
				return f.read()
		else:
			return self._upstream
	
	@property
	def stream(self):
		if self._content is not None:
			if isinstance(self._content, bytes):
				return BytesIO(self._content)
			else:
				return StringIO(self._content)
		elif self._path is not None:
			return open(self._path, 'rb')
		else:
			if isinstance(self.upstream, bytes):
				return BytesIO(self.upstream)
			else:
				return StringIO(self.upstream)


