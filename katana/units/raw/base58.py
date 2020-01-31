#!/usr/bin/env python3
import binascii
import base58
import magic
import regex as re

from katana.unit import RegexUnit
from katana.unit import NotApplicable
from katana.manager import Manager
from katana.target import Target
from katana.util import is_good_magic
import katana.util


class Unit(RegexUnit):

    # Low priority
    PRIORITY = 60
    # Group settings
    GROUPS = ["raw", "decode"]
    # What are we looking for?
    PATTERN = re.compile(rb"[a-zA-Z0-9+/]+", re.MULTILINE | re.DOTALL)

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

        # if this was a given file, make sure it's not an image or anything useful
        if self.target.path:
            if is_good_magic(magic.from_file(self.target.path)):
                raise NotApplicable("potentially useful file")

    def evaluate(self, match):

        try:
            # Decode chunk
            result = base58.b58decode(match.group())

            # We want to know about this if it is printable!
            if katana.util.isprintable(result):
                self.manager.register_data(self, result)
            else:
                # if it's not printable, we might only want it if it is a file...
                magic_info = magic.from_buffer(result)
                if katana.util.is_good_magic(magic_info):
                    # Generate an artifact and dump the data
                    filename, handle = self.generate_artifact(
                        "decoded", mode="wb", create=True
                    )
                    handle.write(result)
                    handle.close()
                    # Register the artifact with the manager
                    self.manager.register_artifact(self, filename)

        except (UnicodeDecodeError, binascii.Error, ValueError):
            # This won't decode right... must not be right! Ignore it.
            # I pass here because there might be more than one string to decode
            pass

        # Base58 can also include error checking... so try to "check" as well!
        # -----------------------------------------------------------------------

        try:
            result = base58.b58decode_check(match.group())

            if katana.util.isprintable(result):
                self.manager.register_data(self, result)
            else:
                # if it's not printable, we might only want it if it is a file...
                magic_info = magic.from_buffer(result)
                if katana.util.is_good_magic(magic_info):
                    # Create an artifact and dump data
                    filename, handle = katana.create_artifact(
                        self, "decoded", mode="wb", create=True
                    )
                    handle.write(result)
                    handle.close()
                    # Register artifact
                    self.manager.register_artifact(filename)
        except (UnicodeDecodeError, binascii.Error, ValueError):
            # This won't decode right... must not be right! Ignore it.
            # I pass here because there might be more than one string to decode
            pass
