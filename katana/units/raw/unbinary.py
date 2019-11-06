#!/usr/bin/env python3
from typing import List
import regex as re

from katana.unit import RegexUnit


class Unit(RegexUnit):

    # Unit priority
    PRIORITY = 50
    # Groups we belong to
    GROUPS = ["raw", "decode"]
    # The pattern we are searching for
    PATTERN = re.compile(rb"(([01]{7,8}( ([01]{7,8})){3,}|[01]{32,}))")

    def evaluate(self, match):

        match: List[bytes] = match.group().split(b" ")
        result = b""

        # Convert all the bits into bytes (little endian)
        for m in match:
            result += int(m, 2).to_bytes((len(m) + 7) // 8, byteorder="little")

        # Register data
        self.manager.register_data(self, result)

        result = b""
        for m in match:
            result += int(m, 2).to_bytes((len(m) + 7) // 8, byteorder="big")

        # Register data
        self.manager.register_data(self, result)
