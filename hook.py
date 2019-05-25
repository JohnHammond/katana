#!/usr/bin/env python
from collections import deque
from pwn import *
import utilities
import jinja2
import shutil
from hashlib import md5
import clipboard
import uuid
import json

class KatanaHook(object):

	def __init__(self, katana):
		self.katana = katana
	
	def flag(self, flag):
		""" Notified when a unit locates a flag """
		pass
	
	def result(self, unit, result):
		""" Notified when a unit produces some result dict from a target """
		pass
	
	def artifact(self, unit, artifact, isdir):
		""" Notified when a unit produces a file. `artifact` is the path
			to the new artifact under the results directory. """
		pass

	def image(self, image):
		""" If an artifact is an image, receive a notification. Useful for
			displaying real-time results as needed """
		pass

	def recurse(self, target):
		""" Notified when a unit returns data that can be recursed on """
		pass
	
	def begin(self):
		""" Notified when katana begins processing units for the base target """
		pass
	
	def complete(self):
		""" Notified when katana has finished running all applicable units, and
			the results have been written (in both HTML and JSON) in the output
			directory """
		pass

	def failure(self, message):
		""" Notified when some failure condition was met. `message` describes
			the failure in text for the user. `results` is True if there were
			any results to write to a file. """
		pass
	
	def status(self, status):
		""" Notified when the status thread posts an update """
		pass
	
	def work_status(self, ident, status):
		""" Notified when a thread posts an update
			_NOTE_ This happens very often for short units. You shouldn't do
			any intense processing here. Log a quick message if needed, and
			that's it.
		"""
		pass

	def warning(self, warning):
		""" Notified when there is some abnormal condition that doesn't
			threaten the execution of katana """
		pass

class DefaultKatanaHook(KatanaHook):
	""" The default Katana results hook will recieve all flags, results,
		artifacts, and images in queues. Upon completion or failure,
		the known results are compiled into a clean JSON object and saved
		to `outdir`/katana.json. These results are also stored in
		`self.results` so that subclasses can use them for other output
		format generation if needed/wanted.

		This hook makes no console output.
	"""

	def __init__(self, *args, **kwargs):
		super(DefaultKatanaHook, self).__init__(*args, **kwargs)
		self.results = deque()
		self.flags = deque()
		self.artifacts = deque()
		self.images = deque()

	def flag(self, flag):

		# CALEB: technically a race condition, but as long as it makes it in
		#	at least once, then I don't care.
		if self.flags.count(flag) > 0:
			return False

		# Queue the flag to be added to results later
		self.flags.append(flag)

		return True
	
	def result(self, unit, result):

		# Clean the result object
		result = self.clean_result(result)

		# The result might have been completely useless
		if result is None or not result:
			return False

		# Queue the result for later
		self.results.append((unit, result))

		return True
	
	def image(self, image):
		# No special processing needed
		self.images.append(image)
		return True

		# Display the image if the user asked to
		if ( self.config['display_images'] ) and self.gui is not None:
			try:
				self.gui.insert(image)
			except RuntimeError:
				# The user must have closed the window.. that's fine!
				pass


	def artifact(self, unit, path, isdir):
		# No special processing needed
		if not isdir:
			self.artifacts.append((unit, path))
			return True
		return False

	def locate_result(self, results, unit):
		""" This just searches the results dict and returns a reference to the
			results specifically for the specified unit. It has to look for
			and possible create all the parent results objects before it can
			return it. It's kinda gross, but it only happens at the end...
		"""

		# Base result structure if no unit
		if unit is None:
			return results

		# Grab the units family tree (list of parents)
		parents = unit.family_tree

		# Start at the global results
		r = results

		# Iterate through parents to find the correct
		# results item in the dictionary
		for p in parents:
			# Create the children entry if it doesn't exist
			if not 'children' in r:
				r['children'] = {
					p.unit_name: {
						'uuid': str(uuid.uuid4()),
						'results': []
					}
				}
			# Create this child if it doesn't exist
			elif p.unit_name not in r['children']:
				r['children'][p.unit_name] = {
					'uuid': str(uuid.uuid4()),
					'results': []
				}
			# We found it! We found the last parent!
			r = r['children'][p.unit_name]

		# Add the children if needed
		if 'children' not in r:
			r['children'] = {
				unit.unit_name: {
					'uuid': str(uuid.uuid4()),
					'results': [] 
				}
			}
		# Add this child if needed
		elif unit.unit_name not in r['children']:
			r['children'][unit.unit_name] = {
				'uuid': str(uuid.uuid4()),
				'results': []
			}

		# Create this child
		r = r['children'][unit.unit_name]

		# Return the result reference
		return r

	def clean_result(self, d):
		""" Remove results we don't want, and normalize the format. 

			This function will ensure that the string results are greater
			than `data_length` characters. Also, it ensures there are no bytes
			strings in the result (either decoding with utf-8 or using repr)
		"""

		if isinstance(d, str):
			# Only allow strings of at least `data_length` length.
			if len(d) < self.katana.config['data_length']:
				return None
			return d
		elif isinstance(d, list) or isinstance(d, tuple):
			# Recurse through tuples and lists
			r = []
			for i in d:
				x = self.clean_result(i)
				if x is not None:
					r.append(x)
			# Ignore the tuple if it is empty after cleaning
			if len(r) == 0:
				r = None
		elif isinstance(d, dict):
			# Recurse through dictionaries
			r = {}
			for name in d:
				x = self.clean_result(d[name])
				if x is not None:
					r[name] = x
			# Ignore the dict if it is empty after cleaning
			if len(r) == 0:
				r = None
		elif isinstance(d, bytes):
			# Attempt to decode the bytes array
			try:
				r = d.decode('utf-8')
			except UnicodeError:
				# Fall back to `repr`, and remove the `b'{0}'` bullshit
				r = repr(d)[2:-1]
			# Ensure it is long enough
			if len(r) < self.katana.config['data_length']:
				return None
		else:
			# For all other types, just use as-is.
			r = d
		return r


	def write(self):
		""" Write katana output in JSON and HTML """

		# Initial results structure
		results = {
			'flags': list(set(list(self.flags))),
			'images': list(set(list(self.images))),
			'children': {}
		}

		# Find images with duplicate hashes 
		image_hashes = []
		for i in range(len(results['images'])):
			h = md5()
			# Hash the file in chunks because memory efficiency
			with open(results['images'][i], 'rb') as f:
				for chunk in iter(lambda: f.read(4096), b''):
					h.update(chunk)
			# Check for duplicate
			if h.hexdigest() in image_hashes:
				self.results['images'][i] = None
			else:
				image_hashes.append(h.hexdigest())
		
		# Remove duplicate entires
		results['images'] = [ img for img in results['images'] if img is not None ]

		# Store unit results
		for unit,result in self.results:
			r = self.locate_result(results, unit)
			if result not in r['results']:
				r['results'].append(result)

		# Store artifacts
		for unit,path in self.artifacts:
			r = self.locate_result(results, unit)
			if 'artifacts' not in r:
				r['artifacts'] = [ path ]
			else:
				r['artifacts'].append(path)

		self.final_results = results

		# Serialize the results
		json_results = json.dumps(results, indent=4, sort_keys=True)

		# Write the data to the output file
		with open(os.path.join(self.katana.config['outdir'], 'katana.json'), 'w') as f:
			f.write(json_results)

	def complete(self):
		self.write()
	
	def failure(self, reason):
		#self.result(None, { 'failure_reason': reason })
		self.write()

class JinjaKatanaHook(DefaultKatanaHook):
	""" This hook inherits the DefaultKatanaHook behavior, but adds
		katana.html output using the specified Jinja2 template and
		the DefaultKatanaHook.results dict.
	"""

	def write(self):
		super(JinjaKatanaHook, self).write()

		# Create a new Jinja2 environment from the templates.
		# Specify html/xml processing.
		env = jinja2.Environment(loader=jinja2.FileSystemLoader('./templates'),
				autoescape=jinja2.select_autoescape(['html', 'xml'])
			)

		# Expose a custom JSON pretty printing filter
		env.filters['pretty_json'] = utilities.jinja_pretty_json

		# Load the template specified in the configuration
		template = env.get_template(self.katana.config['template']+'.html')

		# Ensure the CSS file is available in the output directory
		shutil.copyfile(
			os.path.join('./templates', self.katana.config['template']+'.css'),
			os.path.join(self.katana.config['outdir'], self.katana.config['template']+'.css')
		)

		# Render the template with our results and initial target data
		stream = template.stream(
			results=self.final_results,
			target=self.katana.original_target
		)

		# Dump the rendered view to the output directory
		stream.dump(os.path.join(self.katana.config['outdir'], 'katana.html'))


class LoggingKatanaHook(JinjaKatanaHook):
	""" This katana hook vareity inherits the Default hook behavior
		as well as the HTML hook behavior, and adds console logging.
		This should only be used if the person running your application
		is meant to see the logging messages from katana.
	"""

	def __init__(self, *args, **kwargs):
		super(LoggingKatanaHook, self).__init__(*args, **kwargs)

		self.progress = log.progress('katana')
		self.thread = {}
	
	def flag(self, flag):
		# Only do the logging if we added it to the queue
		if super(LoggingKatanaHook, self).flag(flag):
			# CALEB: This is a race condition... but it's not a big deal...
			# CALEB: Also, this is fucking disgusting...
			log.success((f'({round(time.time()-self.katana.start,2)}s) potential flag found ' + 
				'(copied)'*(len(self.flags) == 1) +': {0}').format('\u001b[32;1m' +
				flag + '\u001b[0m')
			)

			# Copy the flag if it's the first one
			if len(self.flags) == 1:
				clipboard.copy(flag)

			return True
		return False

	def work_status(self, ident, status):
		if not self.katana.config['verbose']:
			return
		if ident not in self.thread:
			self.thread[ident] = log.progress('thread-{0}'.format(ident))
		self.thread[ident].status(status)
	
	def status(self, status):
		super(LoggingKatanaHook, self).status(status)
		self.progress.status(status)

	def begin(self):
		super(LoggingKatanaHook, self).begin()
		self.progress('beginning unit processing')
	
	def complete(self):
		super(LoggingKatanaHook, self).complete()

		finish = time.time()
		self.progress.success('katana completed in {0:.01f}s; output written to {1}'.format(
			finish-self.katana.start,
			self.katana.config['outdir']
		))
	
	def failure(self, reason):
		self.progress.failure(reason)
		# CALEB: I think we should raise a POSIX signal here os it makes it to
		# the main thread vice raising an exception in the current thread.
		# I'm unsure at this point, though.
		raise RuntimeError('I\'m not sure what to do here')
	
