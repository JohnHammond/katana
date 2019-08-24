# -*- coding: utf-8 -*-
r"""
This is the heart and soul of Katana. The units define how Katana evaluates
targets and what data is returned in the results. A unit is a generic "scanner"
which can take a target and evaluate it based on some specific type of
challenge/obfuscation/vulnerability.

For example, a unit may look for base64 encoded text, scrape a webpage, or
perform basic SQL inject attacks on a URL. The unit interface allows the writer
to abstract away the processing of targets, and focus solely on the evaluation
of a specific and small subset of CTF challenges.

At it's core, a unit simply needs to exist under the :mod:`units` package
and implement a class named `Unit` which inherits from the :class:`BaseUnit`.
In practice, most units will inherit directly from one of the helper units such
as :class:`FileUnit`, :class:`PrintableDataUnit`, etc. in order to further
abstract target error checking.

For detailed examples of subclassing the :class:`BaseUnit` class, see it's
definition. Examples of using the specialized units are given below.

"""
import importlib
import pkgutil
import subprocess
from dataclasses import dataclass, field
from typing import Any
import hashlib
import re
import base64

import katana.units

class BaseUnit(object):

	# Set this to True to protect this unit from recursing into another
	# protected unit
	PROTECTED_RECURSE = False

	# The unit priority. 50 is default. 1 is highest. 100 is lowest.
	PRIORITY = 50

	# Recursion is fine
	NO_RECURSE = False

	def __lt__(self, other):
		return self.PRIORITY < other.PRIORITY

	@classmethod
	def add_arguments(cls, katana, parser):
		""" Add whatever arguments are needed by this unit to the given
			parser
		"""
		return

	# Unit constructor (saves the config)
	def __init__(self, katana, target):
		
		
		if target.parent is not None and self.PROTECTED_RECURSE and target.parent.PROTECTED_RECURSE:
			# Protected recursion means that two protected recurse units
			# can't follow one another. This protects recurse swapping
			# in things like crypto modules or strings modules.
			raise NotApplicable('protected recurse violation')
		elif self.NO_RECURSE:
			# No recurse means that a unit cannot recurse into itself.
			
			unit = target.parent
			while unit is not None:
				if isinstance(unit, type(self)):
					raise NotApplicable('no recurse')
				unit = unit.target.parent

		if not self.unit_name.startswith('katana.units.web.') and target.is_url:
			raise NotApplicable('target is a URL')
			
		self._completed = False
		self.target = target

	# By default, the only test case is the target itself
	def enumerate(self, katana):
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
		
		yield None

	@property
	def unit_name(self):
		return self.__class__.__module__

	def evaluate(self, case):
		raise RuntimeError('{0}: no evaluate implemented: bad unit'.format(self.unit_name))
	
	@property
	def family_tree(self):
		parents = []
		parent = self.target.parent
		# Are you my mother
		while parent is not None:
			parents.append(parent)
			parent = parent.target.parent
		return parents[::-1]
	
	@property
	def completed(self):
		return self._completed

	@completed.setter
	def completed(self, v):
		if v != True:
			raise ValueError
		parent = self.target.parent
		while parent is not None:
			parent._completed = True
			parent = parent.target.parent
		self._completed = True

@dataclass(order=True)
class UnitWorkWrapper(object):
	r""" This is the object which is tracked in the work queue by katana. It is
	never used by units themselves. Only the expanded :data:`item` field is
	passed to the :func:`BaseUnit.evaluate` method.
	"""
	priority: int
	action: Any = field(compare=False)
	item: Any = field(compare=False)


class NotApplicable(Exception):
	r"""
	This exception is raised by the Unit constructor to signal to Katana
	that the given target is not applicable to this unit. It will stop the
	loading of this unit.
	"""
	pass


class DependancyError(Exception):
	r"""
	This exception is used internally by Katana to signal when a specified
	unit dependancy is not satisfied on the current system. Dependancies are
	specified by defining a module-scope global variable in your unit source
	named `DEPENDENCIES` which is an array of strings naming binaries which
	must be available within the system path.
	"""
	def __init__(self, unit, dep):
		self.unit = unit
		self.dependancy = dep


class FileUnit(BaseUnit):
	r""" This unit base class requires that the given target be a file, and also
	optionally have a libmagic signature which contains one of a specified set
	of keywords. To use this unit, you simply pass a special `keywords`
	argument to its constructor in your unit subclass:

	.. code-block:: python
		
		# A unit that requires a file containing some sort of image
		class Unit(units.FileUnit):
			def __init__(self, katana, target):
				super(Unit, self).__init__(katana, target, keywords=['image'])
	"""

	def __init__(self, katana, target, keywords=None):
		super(FileUnit, self).__init__(katana, target)

		if keywords is None:
			keywords = []
		if not self.target.is_file:
			raise NotApplicable("not a file")

		# JOHN: I do this so only ONE of the supplied keywords needs to be there.
		#	   This is to handle things like "jpg" or "jpeg" and other cases
		if keywords:
			keyword_found = False
			for k in keywords:
				if k.lower() in self.target.magic.lower():
					keyword_found = True
			if not keyword_found:
				raise NotApplicable("no matching magic keywords")


class PrintableDataUnit(BaseUnit):
	r""" This unit base class ensures that the target content contains only
	printable data (that is, data which is not binary/is readable). """

	def __init__(self, katana, target):
		super(PrintableDataUnit, self).__init__(katana, target)

		if not self.target.is_printable:
			raise NotApplicable("not printable data")


class NotEnglishUnit(BaseUnit):
	r""" This unit base class ensures that the target content contains mostly
	english text. """

	def __init__(self, katana, target):
		super(NotEnglishUnit, self).__init__(katana, target)

		if self.target.is_english:
			raise NotApplicable("potential english text")


class NotEnglishAndPrintableUnit(BaseUnit):
	r""" This unit base class ensures that the target content is printable, and
	is also *not* english text (e.g. base64 data, white space, etc.) """

	def __init__(self, katana, target):
		super(NotEnglishAndPrintableUnit, self).__init__(katana, target)

		if self.target.is_english and not self.target.is_printable:
			raise NotApplicable("not english and not printable")


class UnitFinder(object):
	r"""
	The unit finder locates units within the :mod:`units` package and
	dynamically loads them. It will check their dependencies and only load
	units which can be used in the current environment.

	While not strictly necessary, subclassing this object is possible. It is
	created prior to creating the Katana object and passed into the
	:class:`katana.Katana` constructor. If subclassed or reimplemented, you
	must implement the :func:`find` method, as this is what Katana will expect
	to exist.

	Example usage:

	.. code-block:: python
		:linenos:

		# Create a unit finder which excludes all crypto units
		finder = units.UnitFinder(exclusions=['crypto'])

		# Load all matching units
		for unit in finder.load_units():
			print('loaded unit: {0}'.format(unit))

	.. note::
		This code will automatically load all ``*.py`` scripts underneath the
		``units`` directory and look for a ``Unit`` class. This could be
		dangerous. Don't put random scripts in this directory.
	"""

	def __init__(self, exclusions):
		self.units = []
		self.exclusions = ['katana.units.' + e for e in exclusions]

	# self.load_units(unit_path, exclusions)

	def load_units(self):
		r""" Iterate over all modules within the ``units`` directory and look
		for valid units (modules defining a ``Unit`` class).

		For each identified unit, the finder will do the following:

		- Ensure it is not in the exclusion list.
		- Attempt to dynamically load the module
		- Check for the DEPENDENCIES global
			- If the global exists, verify the existence of all binaries
			  defined within the list (using the `which` command)
		- Verify existence of the ``Unit`` class, and store it.
		- yield the unit class to the caller, in order to support incremental
		  progress while loading. For a large list of units, this may take some
		  time which is why it yields after every unit load.
		"""
		# This is bad, but I need to not import it at the global level here :(
		import pwnlib.log
		log = pwnlib.log.getLogger(__name__)

		for importer, name, ispkg in pkgutil.walk_packages(katana.units.__path__, 'katana.units.'):

			# Check the exclusion list to see if this unit matches
			try:
				for exclude in self.exclusions:
					if name == exclude or name.startswith(exclude.rstrip('.') + '.'):
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
		""" Use the defined unit arguments to build augment an existing
		:mod:`argparse` parser. If you defined any arguments which overlap with
		existing unit arguments, this function may throw argparse exceptions.
		See the argparse ``add_argument`` documentation for more details.
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
				parser.add_argument('--{0}'.format(arg['name'].replace('_', '-')), type=arg['type'],
									default=arg['default'], help=arg['help'])

	def validate_config(self, config):
		""" Validate the given configuration values based on the
		defined/required arguments within all the loaded units. If an argument
		is missing, raise a :class:`RuntimeError`.
		"""

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
		# elif not isinstance(config[arg['name']], arg['type']):
		#	raise RuntimeError('{0}: invalid type'.format(arg['name']))

		return config

	def find(self, katana, target, requested=None):
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
		if not requested:
			requested = None

		if requested is not None:
			requested = ['katana.units.' + r for r in requested]

		# Iterate through known units to find ones we are interested in
		for unit_class in self.units:
			try:
				# Check if this was a requested unit
				if requested is not None:
					try:
						for name in requested:
							if name == unit_class.__module__ or unit_class.__module__.startswith(
									name.rstrip('.') + '.'):
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
