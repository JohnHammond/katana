import os
import importlib
import argparse
import pkgutil
import sys
from pwn import *
import magic
import json
import re
import html
import threading
import enchant
import traceback
import string

dictionary = enchant.Dict()
english_words_threshold = 1

def isprintable(data):
	if type(data) is not bytes:
		data = data.encode('utf-8')
	for c in data:
		if c not in bytes(string.printable,'ascii'):
			return False

	return True

# This subclass of argparse will print the help whenever there
# is a syntactic error in the options parsing
class ArgumentParserWithHelp(argparse.ArgumentParser):
	def error(self, message):
		print('{0}: error: {1}'.format(self.prog, message))
		self.print_help()
		sys.exit(2)

# argparse type to automatically verify that the specified path
# exists and is a directory
def DirectoryArgument(name):
	fullpath = os.path.abspath(os.path.expanduser(name))
	if not os.path.isdir(fullpath):
		raise argparse.ArgumentTypeError('{0} is not a directory'.format(name))
	return fullpath

# argparse type to automatically verify module existence and load it
def PythonModule(name):
	try:
		log.info('loading unit: {0}'.format(name))
		module = importlib.import_module(name)
	except Exception as e:
		print(e)
		raise argparse.ArgumentTypeError('{0} is not a valid module name'.format(name))
	return module

# This is dumb, but it makes the code more expressive...
def GetUnitName(unit):
	return unit.__module__

# Gets a fully qualified class name
def GetFullyQualifiedClassName(o):
	module = o.__class__.__module__
	if module is None or module == str.__class__.__module__:
		return o.__class__.__name__  # Avoid reporting __builtin__
	else:
		return module + '.' + o.__class__.__name__

def find_modules_recursively(path, prefix):
	""" Locate all modules under a path """
	log.warning('calling pkgutil.iter_modules({0},\'{1}\')'.format([path], prefix))
	for importer, name, ispkg in pkgutil.iter_modules([path], prefix):
		log.failure('looking at {0}'.format(name))
		module_path = os.path.join(path, name.replace('.','/'))
		if ispkg:
			
			for s in find_modules_recursively(module_path, name + '.'):
				yield s
		else:
			
			yield name

def is_english(string):
	# Filter out words that are only two letters long...
	all_words = list(filter(lambda word : len(word)>2, re.findall('[A-Za-z]+', string)))
	english_words = list(filter(lambda word : len(word)>2, [ word for word in all_words if dictionary.check(word) ]))

	return len(english_words) >= (len(all_words) - english_words_threshold) and len(english_words) != 0


def jinja_pretty_json(value):
	return json.dumps(value, sort_keys=True, indent=4, separators=(',', ': '))

# -------------------------------------------------------------------

# These are utility functions that may be used in more than one module.

def process_output(popen_object):

	result = {
		"stdout": [],
		"stderr": [],
	}

	output = bytes.decode(popen_object.stdout.read(),'latin-1')
	error = bytes.decode(popen_object.stderr.read(),'latin-1')
	
	for line in [ l.strip() for l in error.split('\n') if l ]:
		result["stderr"].append(line)
	for line in [ l.strip() for l in output.split('\n') if l ]:
		result["stdout"].append(line)

	if not len(result['stderr']):
		result.pop('stderr')
	if not len(result['stdout']):
		result.pop('stdout')
	
	if result != {}:
		return result

def is_image(filename):
	# Ensure it's a file, and get it's mime type
	try:
		t = magic.from_file(filename).lower()
	except (FileNotFoundError, IsADirectoryError, ValueError, OSError):
		return False
	
	return bool( ' image ' in t )
