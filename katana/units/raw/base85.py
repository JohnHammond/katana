#!/usr/bin/env python3
from typing import Any
import binascii
import base64
import magic
import regex as re

from katana.unit import RegexUnit
from katana.unit import NotApplicable
from katana.manager import Manager
from katana.target import Target
import katana.util


class Unit(RegexUnit):

    # Low priority, uncommon
    PRIORITY = 60
    # Groups
    GROUPS = ["raw", "decode"]
    # REGEX matching base58
    PATTERN = re.compile(rb"[\x21-\x75]{4,}", re.DOTALL | re.MULTILINE)

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

    def evaluate(self, match):
        try:
            # Attempt decode
            result = base64.b85decode(match.group())

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
