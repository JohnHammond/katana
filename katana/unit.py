#!/usr/bin/env python3
""" Classes pertaining to defining custom unit implementations and locating
units for evaluation """
from __future__ import annotations
from typing import Any, List, Type, Tuple, IO, Generator
import subprocess
import importlib
import logging
import pkgutil
import hashlib
import base64
import uuid
import re
import os

import katana

logger = logging.getLogger(__name__)


class NotApplicable(Exception):
    r""" Indicates the Unit which was created is not applicable to the given
    target, and the unit is in an undefined state. """
    pass


class MissingDependency(Exception):
    r""" Indicates the unit was missing a dependency, and cannot be loaded. The
    message content is the name of the missing dependency """
    pass


class Unit(object):
    r""" Abstract the interface with a specific unit of evaluation for CTF
    challenges. This class must implement the `evaluate` and `validate` methods
    in order to be used with Katana.

    Units attempt to solve very basic and targeted CTF challenges and provide
    data which could either contain a flag or another challenge. If the data
    contains a flag, evaluation will be halted. If it doesn't, the data may be
    used to bootstrap further Unit scanning.
    """

    # Default unit priority
    PRIORITY: float = 50
    # Allow self-recursion
    RECURSE_SELF: bool = False
    # Whether this unit is allowed to recurse into itself
    NO_RECURSE: bool = False
    # Whether this unit is allowed to recurse from other protected recurse
    # units
    PROTECTED_RECURSE: bool = False
    # Standard dependency checking will use this
    DEPENDENCIES: List[str] = []
    # If set, flags for this unit must be alone on a line with the data being
    # analyzed
    STRICT_FLAGS: bool = False
    # Groups this unit belongs to (e.g. 'crypto', 'bruteforce', 'stego', etc)
    GROUPS = []
    # Groups this unit is not allowed to recurse into
    BLOCKED_GROUPS = []

    def __init__(self, manager: katana.manager.Manager, target: katana.target.Target):
        super(Unit, self).__init__()

        # Enforce recursion restrictions for this unit
        if (
            target.parent is not None
            and self.PROTECTED_RECURSE
            and target.parent.PROTECTED_RECURSE
        ):
            raise NotApplicable("protected recurse violation")
        elif self.NO_RECURSE:
            parent = target.parent
            while unit is not None:
                if isinstance(unit, type(self)):
                    raise NotApplicable("no recurse violation")
                unit = unit.target.parent

        # Save target and manager references
        self.target: katana.manager.Target = target
        self.manager = manager
        self.output_dir = None  # We calculate this at runtime when needed
        self.completed = False
        self.depth = 0

        # Save origin target
        self.origin = target
        if target.parent is not None:
            self.origin = target.parent.origin
            self.depth = target.parent.depth + 1

    def __str__(self) -> str:
        """ Default string conversion reports the module name for this unit """
        return self.__class__.get_name()

    def __repr__(self) -> str:
        return f"{str(self)}({str(self.target)})"

    @classmethod
    def get_name(cls) -> str:
        return cls.__module__.split(".")[-1]

    @classmethod
    def validate(cls, manager):
        """ Checks that required configuration values are available in the
        manager configuration file. This should be called via `super` prior to
        subclass implementation, as it ensures the section for this unit is
        added. """

        # If a section for this unit is not present, add an empty one so
        # defaults can propagate
        if cls.get_name() not in manager:
            manager[cls.get_name()] = {}

    def can_recurse(
        self, unit_class: Type[katana.unit.Unit], direct: bool = True
    ) -> bool:
        """ Checks recursion rules and returns whether or not recursion is
        allowed into the given unit class. This unit has already been matched
        to a given recursion target from this unit.

        Direct indicates whether this is the direct child or an ancestor of
        self. """

        # Can we recurse into ourselves?
        if unit_class is self.__class__ and not self.RECURSE_SELF:
            return False

        # Is this unit name in the blocked groups list?
        if unit_class.get_name() in self.BLOCKED_GROUPS:
            return False

        # Check that we haven't blocked this group
        for group in self.BLOCKED_GROUPS:
            if group in unit_class.GROUPS:
                return False

        return True

    def is_complete(self) -> bool:
        return self.completed or self.origin.completed

    def enumerate(self):
        r""" Yield cases for evaluation given the target and manager
        configuration. This allows units with multiple possible evaluations
        (such as password guesser's) to take advantage of the parallelism of
        Katana without further coding. By default, this method yields a single
        `None` value which will be passed as `case` in the `Unit.evaluate`
        method below. """

        yield None

    def evaluate(self, case: Any):
        r""" Run unit tasks given `case` which was returned from
        `Unit.enumerate`. This could happen in any thread or process of
        execution and should be stateless. """
        raise RuntimeError("{0}: malformed unit: no evaluate".format(self))

    def get_output_dir(self):
        """ Find the output directory for this unit """

        # No need to do this more than once
        if self.output_dir is not None:
            return self.output_dir

        if self.target.parent is not None:
            # We have a parent, we will situate ourselves underneath it
            path = os.path.join(self.target.parent.get_output_dir(), "children")
        else:
            # No parent, we go underneath the main output directory
            path = os.path.join(self.manager["manager"]["outdir"])

        # We situate ourselves underneath the target
        path = os.path.join(path, self.target.hash.hexdigest())

        # Build final path, and create if necessary
        path = os.path.join(path, str(self))
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)

        # Save for future runs
        self.output_dir = path

        # Return the path
        return path

    def generate_artifact(
        self,
        name: str = None,
        mode: str = "w",
        create: bool = True,
        asdir: bool = False,
    ) -> Tuple[str, IO]:
        """ Generate a new artifact, and return the path and open file handle.
        The artifact is not automatically registered with the manager, since it
        is initially empty. You should register any artifacts which contain
        useful data based on your unit (using `self.manager.register_artifact`)
        """

        # Generate a random file name
        if name is None:
            name = str(uuid.uuid4())

        # Find the path to this artifact
        path = os.path.join(self.get_output_dir(), name)

        # Create file if needed
        fh = None
        if create:
            n = 0
            name, ext = os.path.splitext(path)
            # We try to create the original file, but default to appending
            # numbers if needed
            while True:
                if asdir:
                    # Create a directory
                    os.makedirs(path, exist_ok=True)
                    break
                else:
                    # Create the file if possible
                    if not os.path.exists(path):
                        fh = open(path, mode)
                    else:
                        # Increment counter and try again
                        n += 1
                        path = "{0}-{1}{2}".format(name, n, ext)

        # Return the full path and file handle (if any)
        return (path, fh)

    def family_tree(self) -> Generator["Unit", None, None]:
        r""" A generator which yields all parent units """

        # Grab the first parent
        parent = self.target.parent

        # Iterate over all parents
        while parent is not None:
            yield parent
            parent = parent.target.parent

    @classmethod
    def check_deps(cls):
        """ The default dependency check will make sure that every item in
        self.DEPENDENCIES exists as an external executable in the current
        environment, and raise a NotApplicable exception otherwise. """

        # Check that all the given binary dependencies exist
        try:
            for dep in cls.DEPENDENCIES:
                subprocess.check_output(["/usr/bin/which", dep])
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Ignore modules with bad dependencies
            raise MissingDependency(dep)


class FileUnit(Unit):
    r""" This unit base class requires that the given target be a file, and also
    optionally have a libmagic signature which contains one of a specified set
    of keywords. To use this unit, you simply pass a special `keywords`
    argument to its constructor in your unit subclass:

    .. code-block:: python
        
        # A unit that requires a file containing some sort of image
        class Unit(units.FileUnit):
            def __init__(self, manager, target):
                super(Unit, self).__init__(manager, target, keywords=['image'])
    """

    def __init__(
        self,
        manager: katana.manager.Manager,
        target: katana.target.Target,
        keywords=None,
    ):
        super(FileUnit, self).__init__(manager, target)

        # Ensure the target is a file
        if not self.target.is_file:
            raise NotApplicable("not a file")

        if keywords is None or keywords == []:
            return

        # Check keywords against magic type
        for k in keywords:
            if k.lower() in self.target.magic.lower():
                return

        # No keywords matched
        raise NotApplicable("no matching keywords found in magic")


class PrintableDataUnit(Unit):
    r""" This unit base class ensures that the target content contains only
    printable data (that is, data which is not binary/is readable). """

    def __init__(self, manager: katana.manager.Manager, target: katana.target.Target):
        super(PrintableDataUnit, self).__init__(manager, target)

        if not self.target.is_printable:
            raise NotApplicable("not printable data")


class NotEnglishUnit(Unit):
    r""" This unit base class ensures that the target content contains mostly
    non-english text. """

    def __init__(self, manager: katana.manager.Manager, target: katana.target.Target):
        super(NotEnglishUnit, self).__init__(manager, target)

        if self.target.is_english:
            raise NotApplicable("potential english text")


class NotEnglishAndPrintableUnit(Unit):
    r""" This unit base class ensures that the target content is printable, and
    is also *not* english text (e.g. base64 data, white space, etc.) """

    def __init__(self, manager: katana.manager.Manager, target: katana.target.Target):
        super(NotEnglishAndPrintableUnit, self).__init__(manager, target)

        if self.target.is_english and not self.target.is_printable:
            raise NotApplicable("not english and not printable")


class Finder(object):
    r""" Utilize python dynamic introspection and loading to locate units
    either within the default unit list bundled with Katana or in a custom
    location.

    .. note::
        This code will automatically load all ``*.py`` scripts underneath the
        specified unit directory and look for a ``Unit`` class. This could be
        dangerous. Don't put random scripts in this directory.
    """

    def __init__(self, manager: katana.manager.Manager, use_default: bool = True):
        super(Finder, self).__init__()

        # Default is an empty unit list
        self.units: List[Type[Unit]] = []

        # Store manager reference for later
        self.manager: katana.manager.Manager = manager

        # Load default modules if requested
        if use_default:
            for unit in self.find(
                os.path.join(katana.__path__[0], "units"), "katana.units."
            ):
                self.register(unit)

    def validate(self) -> None:
        """ Validate the manager configuration for each unit. Units without
        proper configuration will raise an exception which will be fed up to
        the user. Each unit accepts configuration items under it's own section
        if required (e.g. [katana.units.crypto.caeser]) """

        # Validate the configuration for each unit
        for unit in self.units:
            try:
                unit.validate(self.manager)
            except Exception as e:
                # Re-raise as RuntimeError with unit name attached for ease of
                # configuration implementation
                raise RuntimeError("{0}: {1}".format(str(unit), e))

    def find(self, directory: str, prefix: str) -> Generator[Type[Unit], None, None]:
        """ Locate units which conform to the Katana unit specification with
        the given directory. All python source file within the directory will
        end up being executed. A valid unit definition contains a ``Unit``
        class which subclasses ``katana.unit.Unit`` and implements
        ``Unit.evaluate`` and ``Unit.validate``. """

        for importer, name, ispkg in pkgutil.walk_packages([directory], prefix):

            # Load the module
            module = importlib.import_module(name)

            # Make sure the unit class exists
            try:
                unit_class = module.Unit
            except AttributeError:
                # Malformed unit
                continue

            # This isn't a unit at all!
            if not issubclass(unit_class, Unit):
                continue

            # Appears to be a valid unit
            yield unit_class

    def register(self, unit: Type[Unit]):
        """ Register a unit to be used during analysis """

        # This should raise a MissingDependency exception if there are any
        # issues
        unit.check_deps()

        # Keep track of registered units
        self.units.append(unit)

    def match(
        self, target: katana.target.Target, scale: float = 1.0
    ) -> Generator[Unit, None, None]:
        """ Match the given target to one or more units that have previously
        been enumerated with the ``Finder.find`` method. This tests that the
        unit itself is applicable to the target in order to find specific
        applicable units """

        class Applicable(Exception):
            """ Helper for aborting inner loops """

            pass

        for unit_class in self.units:

            try:
                # Check if we have excluded this unit
                if self.manager["manager"]["exclude"] != "":
                    for exclude in self.manager["manager"]["exclude"].split(","):
                        if (
                            exclude == unit_class.get_name()
                            or exclude in unit_class.GROUPS
                        ):
                            raise NotApplicable

                # Check if we are looking for specific units
                # There are three modes:
                # - pure auto: no units are specified. auto is set, and katana runs all applicable units.
                # - manual: units are specified and auto is not set. katana runs all units within the specified set that
                #   are applicable.
                # - auto manual: root targets obey specified units. recursive targets run all applicable units.
                if not self.manager["manager"].getboolean("auto") or (
                    target.parent is None and self.manager["manager"]["units"] != ""
                ):
                    # We requested specific units, only match those
                    for unit in self.manager["manager"]["units"].split(","):
                        if unit == unit_class.get_name() or unit in unit_class.GROUPS:
                            raise Applicable
            except NotApplicable:
                # This unit is excluded
                continue
            except Applicable:
                pass

            # Obey recursion rules
            if target.parent is not None and not target.parent.can_recurse(unit_class):
                continue

            try:
                # Attempt to create a new unit for this target
                unit = unit_class(self.manager, target)
            except NotApplicable as e:
                pass
            else:
                unit.PRIORITY *= scale
                yield unit
