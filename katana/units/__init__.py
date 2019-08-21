# -*- coding: utf-8 -*-
r"""
Base unit class definitions

Defining a new Unit Class
-----------------------------------

	A new unit is defined within the directory tree underneath "units." They
	should be organized by the type of problem they are trying to solve. For
	example, units which solve cryptography problems would be placed under the
	`katana/units/crypto` directory.

	Each unit must contain at least a single class named `Unit`, which must 
	inherit from the `BaseUnit` class. There are some other helper classes
	defined below which do some basic target checks and will signal 
	NotApplicable in common cases (such as a unit requiring a file, or a 
	unit requiring printable data).

"""
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-05-27 00:18:23
import os
import magic
import traceback
import string
import re
from dataclasses import dataclass, field
from typing import Any
import pkgutil
import importlib
import subprocess

from katana import utilities
from katana.unit import BaseUnit
import katana.units

@dataclass(order=True)
class UnitWorkWrapper(object):
	priority: int
	action: Any=field(compare=False)
	item: Any=field(compare=False)

class NotApplicable(Exception):
	pass

class DependancyError(Exception):
	def __init__(self, unit, dep):
		self.unit = unit
		self.dependancy = dep

class FileUnit(BaseUnit):

	def __init__(self, katana, target, keywords=[]):
		super(FileUnit, self).__init__(katana, target)
		
		if not self.target.is_file:
			raise NotApplicable("not a file")

		# JOHN: I do this so only ONE of the supplied keywords needs to be there.
		#       This is to handle things like "jpg" or "jpeg" and other cases
		if keywords:
			keyword_found = False
			for k in keywords:
				if k.lower() in self.target.magic.lower():
					keyword_found = True
			if not keyword_found: 
				raise NotApplicable("no matching magic keywords")

class PrintableDataUnit(BaseUnit):
	
	def __init__(self, katana, target):
		super(PrintableDataUnit, self).__init__(katana, target)

		if not self.target.is_printable:
			raise NotApplicable("not printable data")

class NotEnglishUnit(BaseUnit):
	
	def __init__(self, katana, target):
		super(NotEnglishUnit, self).__init__(katana, target)
		
		if self.target.is_english:
			raise NotApplicable("potential english text")

class NotEnglishAndPrintableUnit(BaseUnit):
	
	def __init__(self, katana, target):
		super(NotEnglishAndPrintableUnit, self).__init__(katana, target)
		
		if self.target.is_english and not self.target.is_printable:
			raise NotApplicable("not english and not printable")

class UnitFinder(object):
	""" The unit finder will use the given unit path and exclusion list to
		locate valid units for a given target. It also has helper functions
		to validate configuration dicts and produce valid argparse parsers
		given a list of units.
	"""

	def __init__(self, exclusions):
		self.units = []
		self.exclusions = ['katana.units.'+e for e in exclusions]
	
		#self.load_units(unit_path, exclusions)
	
	def load_units(self):
		""" Load all units in the unit path, and ensure they are valid """
		# This is bad, but I need to not import it at the global level here :(
		import pwnlib.log
		log = pwnlib.log.getLogger(__name__)

		for importer, name, ispkg in pkgutil.walk_packages(katana.units.__path__, 'katana.units.'):	

			# Check the exclusion list to see if this unit matches
			try:
				for exclude in self.exclusions:
					if name == exclude or name.startswith(exclude.rstrip('.')+'.'):
						raise NotApplicable
			except NotApplicable:
				# Ignore excluded modules
				continue
			
			# Load the module
			module = importlib.import_module(name)

			# Grab the dependencies list if defined
			try:
				deps = module.DEPENDENCIES
			except AttributeError:
				deps = []

			# dependencies should be a list
			if not isinstance(deps, list):
				deps = []

			# Check all dependencies
			try:
				for dep in deps:
					subprocess.check_output(['which', dep])
			except (FileNotFoundError, subprocess.CalledProcessError):
				log.failure('{0}: dependancy not satisfied: {1}'.format(
					name, dep
				))
				continue
				# raise DependancyError(name, dep) # JOHN: This is now longer caught, so...
			
			# Grab the unit class
			try:
				unit_class = module.Unit
			except AttributeError:
				# We are blindly loading all python modules, some might not be
				# units...
				continue
		
			# Track the module list
			self.units.append(unit_class)

			# This allows the caller to track progress. This can take a while.
			yield unit_class
	
	def construct_parser(self, parser):
		""" Build a argparse parser based on loaded unit config requirements
			
			This function may raise argparse exceptions for duplicate names.
		"""

		for unit in self.units:
			# Grab the argument array
			try:
				args = unit.ARGUMENTS
			except AttributeError:
				# We don't care if units don't define arguments
				continue

			# Iterate through each argument
			for arg in args:
				parser.add_argument('--{0}'.format(arg['name'].replace('_', '-')), type=arg['type'], default=arg['default'], help=arg['help'])
	
	def validate_config(self, config):
		""" Validate the configuration dictionary based on the loaded units """

		for unit in self.units:
			# Grab argument array
			try:
				args = unit.ARGUMENTS
			except AttributeError:
				# That's fine
				continue
			
			# Iterate over arguments
			for arg in args:
				# Ensure it exists
				if arg['name'] not in config:
					if 'default' in arg:
						config[arg['name']] = arg['default']
					else:
						raise RuntimeError('{0}: missing argument'.format(arg['name']))
				# Ensure it's the right type
				#elif not isinstance(config[arg['name']], arg['type']):
				#	raise RuntimeError('{0}: invalid type'.format(arg['name']))
		
		return config

	def find(self, katana, target, requested = None):
		""" Use the specified katana object to locate units applicable to the
			given target. `target` is a Target object. `katana` is a Katana
			object with a validated config.
		"""

		valid_units = []
		ignored_units = []

		# This is only used in this function. It just says this unit isn't used.
		class NotRequested(Exception):
			pass

		# These are synonymous 
		if requested == []:
			requested = None

		if requested is not None:
			requested = ['katana.units.'+r for r in requested]

		# Iterate through known units to find ones we are interested in
		for unit_class in self.units:
			try:
				# Check if this was a requested unit
				if requested is not None:
					try:
						for name in requested:
							if name == unit_class.__module__ or unit_class.__module__.startswith(name.rstrip('.')+'.'):
								# It matched one of the requested
								raise StopIteration
					except StopIteration:
						# We found a matching requested unit, so we can continue
						pass
					else:
						# We didn't find a matching requested unit, so this isn't applicable
						raise NotRequested

				# Adhere to protected recurse
				if unit_class.PROTECTED_RECURSE and target.parent is not None:
					if target.parent.PROTECTED_RECURSE:
						raise NotApplicable

				unit = unit_class(katana, target)
				valid_units.append(unit)
			except NotApplicable as e:
				# Return the not applicable exception so
				ignored_units.append((unit_class, e))
			except NotRequested:
				# Just ignore these
				pass

		if not katana.config['no_priority']:
			valid_units = sorted(valid_units)

		# We return a list of units that were not applicable
		# if requested was specified, ignored_units will only
		# contain units that were not applicable that appeared
		# in the requested list.
		return valid_units, ignored_units

