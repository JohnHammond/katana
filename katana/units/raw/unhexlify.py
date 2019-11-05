#!/usr/bin/env python3
from typing import Any
import binascii
import magic
import mmap
import regex as re

from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable
from katana.manager import Manager
from katana.target import Target
import katana.util

HEX_PATTERN = rb"((0x)?[a-f0-9]{2,})"
HEX_REGEX = re.compile(HEX_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)


class Unit(BaseUnit):

    # Moderate priority
    PRIORITY = 25

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

        # We don't need to operate on files
        if not self.target.is_printable or self.target.is_english:
            raise NotApplicable("not printable text or english text")

        # Check if there is hex in it, remove spaces and commas
        self.raw_target = self.target.raw
        if isinstance(self.raw_target, mmap.mmap):
            self.raw_target = self.target.raw.read()
        self.raw_target = self.raw_target.replace(b" ", b"").replace(b",", b"")
        self.matches = HEX_REGEX.findall(self.raw_target)

        if self.matches is None or self.matches == []:
            raise NotApplicable("no hex found")

    def evaluate(self, case: Any):

        results = []

        # Iterate over regex matches for hex
        for match, _ in self.matches:

            # Remove prefix if present
            if match.lower().startswith(b"0x"):
                match = match[2:]

            # Minimum of 16-bit
            if len(match) < 4:
                continue

            try:
                result = binascii.unhexlify(match)
                results.append(result)
            except binascii.Error as e:
                # We may have an "odd-length string" in the way...
                # try to clean up the ends to see if we get anything
                results.append(binascii.unhexlify(match[0:-1]))
                results.append(binascii.unhexlify(match[1:]))

        # Look for flags in the results
        self.manager.find_flag(self, results)

        for result in results:
            if result:
                # We want to know about this if it is printable!
                if katana.util.isprintable(result):
                    self.manager.register_data(self, result)
                else:
                    # if it's not printable, we might only want it if it is a file...
                    magic_info = magic.from_buffer(result)
                    if katana.util.is_good_magic(magic_info):
                        # Create an artifact
                        path, handle = self.generate_artifact(
                            "decoded", mode="wb", create=True
                        )
                        # Write the data
                        with handle:
                            handle.write(result)
                        # Register the artifact (and recurse if requested)
                        self.manager.register_artifact(self, path)
