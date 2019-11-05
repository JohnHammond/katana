#!/usr/bin/env python3
from typing import Any
import binascii
import base64
import magic
import regex as re

from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable
from katana.manager import Manager
from katana.target import Target
import katana.util

BASE32_PATTERN = rb"[A-Z2-7+/]+={0,6}"
BASE32_REGEX = re.compile(BASE32_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)


class Unit(BaseUnit):

    # Low priority
    PRIORITY = 60

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

        # Ensure this is printable data
        if not self.target.is_printable:
            raise NotApplicable("not printable data")

        # Ensure this is not english data
        if self.target.is_english:
            raise NotApplicable("seemingly english")

        # Are there base32 chunks in the data?
        self.matches = BASE32_REGEX.findall(self.target.raw)
        if self.matches is None:
            raise NotApplicable("no base32 text found")

    def evaluate(self, case):

        # Iterate over all matched chunks
        for match in self.matches:
            try:
                # Attempt decode
                result = base64.b32decode(match)

                # Keep it if it is printable
                if katana.util.isprintable(result):
                    self.manager.register_data(self, result)
                else:
                    # if it's not printable, we might only want it if it is a file...
                    magic_info = magic.from_buffer(result)
                    if katana.util.is_good_magic(magic_info):
                        # Generate a new artifact
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
