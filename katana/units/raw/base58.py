#!/usr/bin/env python3
import binascii
import base58
import magic
import regex as re

from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable
from katana.manager import Manager
from katana.target import Target
import katana.util

BASE58_PATTERN = rb"[a-zA-Z0-9+/]+"
BASE58_REGEX = re.compile(BASE58_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)


class Unit(BaseUnit):

    # Low priority
    PRIORITY = 60
    # Group settings
    GROUPS = ["raw", "decode"]

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

        # Printable
        if not self.target.is_printable:
            raise NotApplicable("not printable data")

        # Not english
        if self.target.is_english:
            raise NotApplicable("seemingly english")

        # Matching Base58 chunks
        self.matches = BASE58_REGEX.findall(self.target.raw)
        if self.matches is None:
            raise NotApplicable("no base58 text found")

    def evaluate(self, case):
        # Iterate over chunks
        for match in self.matches:
            try:
                # Decode chunk
                result = base58.b58decode(match)

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
                result = base58.b58decode_check(match)

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
