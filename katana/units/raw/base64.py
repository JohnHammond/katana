#!/usr/bin/env python3
from typing import Any
import binascii
import base64
import magic
import re

from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable
from katana.manager import Manager
from katana.target import Target
import katana.util

BASE64_PATTERN = rb"[a-zA-Z0-9+/]+={0,2}"
BASE64_REGEX = re.compile(BASE64_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)


class Unit(BaseUnit):

    # High priority. Base64 is quick and common and matches fairly unilaterally
    PRIORITY = 25
    # Groups this unit belongs
    GROUPS = ["raw", "decode"]

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

        if self.target.is_file:
            raise NotApplicable("is a file")

        # Must be printable
        # if not self.target.is_printable:
        #    raise NotApplicable("not printable data")

        # Must not be english text
        # if self.target.is_english:
        # 	raise NotApplicable("seemingly english")

        # Find matching base64 chunks
        self.matches = BASE64_REGEX.findall(self.target.raw)
        if self.matches is None or len(self.matches) == 0:
            raise NotApplicable("no base64 text found")

    def evaluate(self, case):
        # Iterate over matches
        for match in self.matches:
            try:
                # Decode chunk
                result = base64.b64decode(match)

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
