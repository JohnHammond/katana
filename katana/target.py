#!/usr/bin/env python
"""

The :class:`Target` class abstracts away interactions with raw target data by first evaluating
what kind target the data is, and providing convenience methods for accessing raw data, files,
or URLs from the data.

"""
from __future__ import annotations
from typing import Any, List, BinaryIO
from io import StringIO, BytesIO
import tempfile
import requests
import hashlib
import enchant
import string
import magic
import mmap
import regex as re
import os
import time
import configparser


# Suppress only the single warning from urllib3 needed.
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

import katana.util

ADDRESS_PATTERN = (
    rb"^((?P<protocol>http|https):\/\/)(?P<host>[a-zA-Z0-9][a-zA-Z0-9\-_.]*)(:(?P<port>[0-9]{1,"
    rb"5}))?(\/(?P<uri>[^?]*))?(\?(?P<query>.*))?$"
)
BASE64_PATTERN = rb"^[a-zA-Z0-9+/]+={0,2}$"
LETTER_PATTERN = rb"[A-Za-z]+"
LETTER_REGEX = re.compile(LETTER_PATTERN, re.DOTALL | re.MULTILINE)
BASE64_REGEX = re.compile(BASE64_PATTERN, re.DOTALL | re.MULTILINE)
ADDRESS_REGEX = re.compile(ADDRESS_PATTERN, re.DOTALL | re.MULTILINE)
DICTIONARY = enchant.Dict()
DICTIONARY_THRESHOLD = 1
PRINTABLE_BYTES = bytes(string.printable, "utf-8")
BASE64_BYTES = bytes(string.ascii_letters + string.digits + "=", "utf-8")


class BadTarget(Exception):
    """ Indicates that we don't want to evaluate this target. This is normally due
    to a target that is too short """

    pass


class Target(object):
    """
    A Target has two main parts:
    
    - Upstream
    - Raw Data
    
    The Upstream is what was passed to the target constructor. In the case of raw data, ``upstream`` and ``raw`` will
    be identical objects. If a URL was passed to the constructor, ``raw`` will take the form of the content of the web
    page. Katana will automatically attempt to fetch the page. In a similar fashion, ``raw`` will return the content of
    a file, if the upstream was a path.
    
    If you don't rely on external tools, you should mostly deal with ``raw`` or ``stream``. ``raw`` will either be a
    bytes object, or a memory mapped file (which acts like a bytes object in most situations). ``stream`` will either
    be an open file handle for file upstreams, or a BytesIO object which will act like a file. This allows you to
    reference the data in an abstract way no matter what the upstream target was. Other useful properties are also
    available which describe the data and are listed below.
    
    :property upstream: A bytes object holding the original target data.
    :property parent: A Unit object describing how this target was created (or None for root targets).
    :property is_printable: Whether the data is mostly printable text
    :property is_english: Whether the data appears to be mostly english
    :property is_image: Whether the data is an image
    :property is_base64: Whether the data looks like base64
    :property path: The path to a file-backed target (URLs are also file-backed by an artifact)
    :property completed: Whether we are done processing this target
    :property url_pieces: A regex Match object containing the URL pieces, if this is a URL.
    :property is_url: True if this appears to be a valid URL
    :property is_file: True if this appears to be a valid file path. This is also true, if ``manager[download]`` is
                        True, and we were able to download the file as an artifact.
    :property magic: libmagic result for the data
    :property hash: A hashlib.md5 object representing the hash of the data
    :property start_time: The time in seconds that this target was started
    :property end_time: When this target completed
    :property units_evaluated: The total number of units evaluated under this target (only root targets)
    
    """

    def __init__(
        self,
        manager: katana.manager.Manager,
        upstream: bytes,
        parent: katana.unit.Unit = None,
        config: configparser.ConfigParser = None,
    ):

        # The target class expects the upstream to be bytes
        if isinstance(upstream, str):
            upstream = upstream.encode("utf-8")

        # Initialize local variables
        self.manager = manager
        self.upstream = upstream
        self.parent = parent
        self.is_printable = True
        self.is_english = True
        self.is_image = False
        self.is_base64 = False
        self.path = False
        self._completed = False
        self.start_time = time.time()
        self.end_time = -1
        self.units_evaluated = 0
        self.mmap = None
        self.units_left = 0
        self.building = True

        # Decide which configuration to use
        if config is not None:
            self.config = config
        elif parent is not None:
            self.config = parent.target.config
        else:
            # Make a copy of the manager configuration
            self.config = configparser.ConfigParser(interpolation=None)
            self.config.read_dict(manager)

    def build_target(self):
        """ This method does the resource intensive part of building the target. It is done in a separate thread to
        decrease the time to return from the `Manager.queue_target` method (e.g. when running w/ a REPL) """

        # Parse out URL pieces (also decide if this is a URL)
        self.url_pieces = ADDRESS_REGEX.match(self.upstream)
        self.is_url = self.url_pieces is not None
        self.url_accessible = False  # assume False until we request it later
        # This zero test is here because os.path.isfile chokes on a null-byte
        self.is_file = 0 not in self.upstream and os.path.isfile(self.upstream)

        # Initial assumed libmagic file type is just "data"
        self.magic = "data"

        # Analyze a file target
        if self.is_file:

            # Assume initially that it is not a file on this system
            is_sub_target = True
            is_sub_results = True

            # Grab the full path to the output/artifacts directory
            results_path = os.path.realpath(self.config["manager"]["outdir"])

            # Check if this is a subdirectory of the origin/base target in this
            # chain, if there is a chain
            if self.parent is not None:
                origin = self.parent.origin
                if origin.is_file:
                    base_target_path = os.path.dirname(origin.path)
                    base_target_path = os.path.realpath(base_target_path)
                    if not self.upstream.startswith(
                        bytes(str(base_target_path), "utf-8") + b"/"
                    ):
                        is_sub_target = False
            else:
                is_sub_target = True

            self.upstream = os.path.realpath(self.upstream)

            # Is this a sub-directory of the base results/output directory?
            if not self.upstream.startswith(bytes(results_path + "/", "utf-8")):
                is_sub_results = False

            # We only analyze things as files if they are either
            # sub-directories/files of the original target or of the results
            # directory itself
            if not is_sub_results and not is_sub_target:
                self.is_file = False
            else:
                self.path = self.upstream

        # Download the target of a URL
        if self.is_url:
            self.url_root = "/".join(self.upstream.decode("utf-8").split("/")[:3]) + "/"
            if self.config["manager"].getboolean("download"):
                try:
                    self.url_accessible = True
                    self.request, gen = self.manager.download(
                        self.upstream, verify=False
                    )
                except requests.exceptions.ConnectionError:
                    self.url_accessible = False
                    self.is_url = False
                    self.content = self.upstream
                else:
                    # self.content = self.request.content
                    fileid, self.path = tempfile.mkstemp()
                    os.close(fileid)
                    with open(self.path, "wb") as filp:
                        for chunk in gen:
                            filp.write(chunk)
                    self.is_file = True
                    self.content = None
                # Carve out the root of the URL
            else:
                # We were asked not to download URLs

                # CALEB: I don't know why we are ignoring the download
                # option here...
                self.request = requests.get(self.upstream, verify=False)
                self.content = self.request.content
                # self.is_url = False # still necessary for URLs or web units

        # Save the path to the file
        elif self.is_file:
            self.content = None
            self.path = self.upstream
        else:
            # This is raw data. There is no file/path associated.
            self.path = None
            self.content = self.upstream

        if isinstance(self.path, bytes):
            self.path = self.path.decode("utf-8")

        # Grab the file type from libmagic (both for files and raw buffers)
        if self.is_file:
            self.magic = magic.from_file(self.path)
        else:
            self.magic = magic.from_buffer(self.content)

        # JOHN: Add a test to determine if this is in fact an image
        if "image" in self.magic.lower():
            # CALEB: Not sure how I want to handle this in the new version...
            #             if self.path:
            #                 katana.add_image(os.path.abspath(self.path))
            self.is_image = True

        # CALEB: if we do this, do we need strings?
        # manager.find_flag(self.parent, self.raw)

        # CALEB: This used to happen in a separate unit but it was silly
        # ALSO CALEB: But... why? How would there be a flag in the magic
        # results? :?
        # katana.locate_flags(parent, self.magic)

        all_words = 0
        english_words = 0

        # Hash the target content for comparison to previous
        # targets by Katana. This prevents recursion on the
        # same target type.
        self.hash = hashlib.md5()
        with self.stream as st:
            for chunk in iter(lambda: st.read(4096), b""):
                # Update the hash with this chunk
                self.hash.update(chunk)

                # Did we already rule out printable?
                if not self.is_printable:
                    continue

                # Check if this chunk is printabale
                for c in chunk:
                    if c not in PRINTABLE_BYTES:
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
                word_list = list(
                    filter(lambda word: len(word) > 2, LETTER_REGEX.findall(chunk))
                )
                all_words += len(word_list)
                english_words += len(
                    list(
                        filter(
                            lambda word: len(word) > 2,
                            [
                                word
                                for word in word_list
                                if DICTIONARY.check(word.decode("utf-8"))
                            ],
                        )
                    )
                )

        # If we haven't already decided, check if we think this is english
        if self.is_english:
            self.is_english = (
                english_words >= (all_words - DICTIONARY_THRESHOLD)
                and english_words != 0
            )

        # JOHN: This is a patch to handle relative file paths, because apparently
        #       we didn't....
        if self.path and self.path.startswith("./"):
            self.path = os.path.abspath(self.path)

        if len(self.raw) < 5:
            raise BadTarget

        # Look for the flag in the raw data
        # manager.find_flag(self.parent, self.raw)

    @property
    def completed(self) -> bool:
        return self._completed

    @completed.setter
    def completed(self, value: bool) -> None:
        if not value:
            return
        self._completed = True
        self.end_time = time.time()

    def add_unit(self):
        """ Add a unit for tracking. This is called by Manager.queue """
        self.units_left += 1

    def rem_unit(self):
        """ Remove a unit for tracking. Also sets completed if all units are done. """
        self.units_left -= 1
        if self.units_left <= 0 and not self.building:
            self.completed = True

    def __repr__(self):
        """ Create a representation of this object based on it's upstream path
        """
        # upstream is always bytes so `repr` puts `b''` around the string.
        return repr(self.upstream)[2:-1]

    def __str__(self):
        """ Create a printable user-readable representation of the target """
        return katana.util.ellipsize(repr(self), length=64)

    def __getitem__(self, key):
        """ Get a slice of the upstream... this seems very inneficient, but it
        was in the old version, and I don't want to break too much... """

        if isinstance(key, slice):
            try:
                return "".join(
                    [
                        self.upstream.decode("utf-8")[ii]
                        for ii in range(
                            *key.indices(len(self.upstream.decode("utf-8")))
                        )
                    ]
                )
            except UnicodeDecodeError:
                return "".join(
                    [
                        self.upstream.decode("latin-1")[ii]
                        for ii in range(
                            *key.indices(len(self.upstream.decode("latin-1")))
                        )
                    ]
                )

    @property
    def raw(self) -> bytes:
        """ Return a bytes-like object for any given target type:

            - Files/content already in memory: return self.content
            - Files already written to disk: return a mmap object
            - For all other unknown data: return self.upstream directly
        """
        if self.content is not None:
            return self.content
        elif self.path is not None:
            if self.mmap is not None:
                return self.mmap
            with open(self.path, "rb") as f:
                try:
                    self.mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
                    return self.mmap
                except ValueError:
                    return self.upstream
                except OSError:
                    # We couldn't memory map the file... we can read it, I guess? This is bad for performance
                    print("I hope this never happens...")
                    return f.read()
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
            return open(self.path, "rb")
        else:
            return BytesIO(self.upstream)

    @property
    def web_protocol(self) -> str:
        """ if this is a URL, return the protocol """
        if self.is_url:
            val = self.url_pieces.groupdict()["protocol"]
            return val.decode() if isinstance(val, bytes) else val
        else:
            return None

    @property
    def web_host(self) -> str:
        """ if this is a URL, return the hostname """
        if self.is_url:
            val = self.url_pieces.groupdict()["host"]
            return val.decode("utf-8") if isinstance(val, bytes) else val
        else:
            return None

    @property
    def web_port(self) -> str:
        """ if this is a URL, return the port number """
        if self.is_url:
            val = self.url_pieces.groupdict()["port"]
            return val.decode("utf-8") if isinstance(val, bytes) else val
        else:
            return None

    @property
    def web_uri(self) -> str:
        """ if this is a url, return the URI """
        if self.is_url:
            val = self.url_pieces.groupdict()["uri"]
            return val.decode("utf-8") if isinstance(val, bytes) else val
        else:
            return None

    @property
    def web_query(self) -> str:
        """ if this is a url, return the query string """
        if self.is_url:
            val = self.url_pieces.groupdict()["query"]
            return val.decode("utf-8") if isinstance(val, bytes) else val
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
        return (
            self.upstream.decode("utf-8") == self.website_root
            and not self.web_uri
            and not self.web_query
        )

    @property
    def is_webpage(self) -> bool:
        """ Opposite of is_website_root? """
        return bool(self.upstream.decode("utf-8") != self.website_root and self.web_uri)
