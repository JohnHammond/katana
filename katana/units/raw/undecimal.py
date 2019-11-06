#!/usr/bin/env python3
import regex as re

from katana.unit import RegexUnit


class Unit(RegexUnit):

    # Moderate-high unit priority
    PRIORITY = 50
    # Grousp we belong to
    GROUPS = ["raw", "decode"]
    # Pattern we're looking for
    PATTERN = re.compile(rb"[0-9]+( ([0-9]+))*")

    def evaluate(self, match):

        match = match.group().split(b" ")

        # Decode big endian
        result = b""
        for m in match:
            v = int(m)
            result += v.to_bytes((v.bit_length() + 7) // 8, byteorder="little")

        self.manager.register_data(self, result)

        # Decode little endian
        result = b""
        for m in match:
            v = int(m)
            result += v.to_bytes((v.bit_length() + 7) // 8, byteorder="big")

        self.manager.register_data(self, result)
