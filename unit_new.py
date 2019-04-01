from pwn import *
import hashlib
import re
import base64

class BaseUnit(object):
	# Unit constructor (saves the config)
	def __init__(self, config):
		self.config = config
		self.completed = False
		if config['flag_format'] == None:
			self.pattern = None
		else:
			self.pattern = re.compile('('+config['flag_format']+')', flags=re.MULTILINE | re.DOTALL)
		self.flags = []

	# By default, the only test case is the target itself
	def get_cases(self, target):
		"""
			This function yields the test cases needed for this
			unit. This is how we inform the parent how many test cases we have
			to complete, and let the architecture handle threading of those
			test cases. This function simply returns the target as the only test
			case, but could return more information.

			For example, it may decide to open a wordlist, and return a tuple
			containing both the target, and an associated word from the word list.
			This allows Unit writer to utilize the threading functionality implemented
			in Katana, without special consideration.

			The value returned from this function is passed directly to the evaluate
			method in order to evaluate that test case. By default, this just the name
			of the target for simple tests.
		"""
		
		yield 'default',target

	@property
	def unit_name(self):
		return self.__class__.__module__

	def evaluate(self, case):
		log.error('{0}: no evaluate implemented: bad unit'.format(self.unit_name))

	def find_flags(self, output):
		# If the user didn't supply a pattern, there's nothing to do.
		if self.pattern == None:
			return False

		'''
		# JOHN: Below is my attempt to search for Base64 encoded flag formats
		special_regex_characters = [
			"\\d", "\\w", '\\s', "\\D", "\\W", '\\S',
			"+", "{", '}', "*", "?", '.', '|', '(', ')', '[', ']',
		]

		# In case someone for some reason includes this...
		# And the 'pattern' is a compiled regex... the 'pattern.pattern' 
		#                                          is the raw regex string
		# Also, we remove the surrounding () parentheses
		raw_flag = self.pattern.pattern.replace('^', '')[1:-1]
		# print('raw_flag', raw_flag)

		found_regex = 0
		for index in range(len(raw_flag)):
			character = raw_flag[index]
			if character in special_regex_characters:
				# This is as far as we can go in the flag pattern.
				found_regex = 1
				break
		
		index -= 1*found_regex  
		
		# Plus one because this the index is zero-based and slicing is not...
		raw_flag = raw_flag[:index+1]
		
		base64_flag = base64.b64encode(bytes(raw_flag, 'utf-8')).decode('utf-8')
		
		padding = base64_flag.count('=')
		trustworthy_base64 = base64_flag.replace('=','')[:-padding]
		

		base64_regex = '[a-zA-Z0-9+/]+={0,2}'
		base64_pattern = re.compile(trustworthy_base64 + base64_regex)
		'''

		# Look for the pattern in the output
		result = self.pattern.search(output)
		# base64_result = base64_pattern.search(output)
		
		# No match
		# if result is None and base64_result is None:
		if result is None:
			return False

		# add the flag

		self.flags.append(result.group())
		# for match in [ result, base64_result ]:
		# 	# print("outside if", end = ' ')
		# 	# print(match)
		# 	if match:
		# 		# print("inside if", end = ' ')
		# 		# print(match)
		# 		self.flags.append(match.group())
		# 		if match == base64_result:
		# 			self.flags.append(base64.b64decode(match.group()))

		return True

	# Create a new artifact for this target/unit and
	def artifact(self, target, name, mode='w', create=True):
		path = os.path.join(self.get_output_dir(target), name)
		if not create:
			return path
		return open(path, mode), path

	# Create an artifact directory
	def artifact_dir(self, target, name, create=True):
		path = os.path.join(self.get_output_dir(target), name)
		if not create:
				return path
		try:
			os.mkdir(path)
		except OSError:
			if ( "File exists" in e.args ):
				log.error("Artifact directory '{0}' already exists!".format(path))
			else:
				# We don't know what went wrong yet.
				# Raise this because it might be another bug to squash
				raise e

		return path

	def get_output_dir(self, target):
		# If there's only one target, we don't deal with sha256 sums.
		# Otherwise, the artifacts will be in:
		# $OUTDIR/artifacts/$SHA256(target)/module/unit/artifact_name
		outdir = os.path.join(
			self.config['outdir'],
			'artifacts',
			hashlib.sha256(target.encode('utf-8')).hexdigest()[-8:],
			*self.unit_name.split('.')
		)

		# If this directory doesn't exist, create it
		if not os.path.exists(outdir):
			try:
				os.makedirs(outdir)
			except FileExistsError:
				pass
			except:
				log.error('{0}: failed to create artifact directory'.format(
					self.unit_name
				))

		return outdir

