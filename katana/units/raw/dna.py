#!/usr/bin/env python3
import regex
import re

from katana.unit import RegexUnit


class Unit(RegexUnit):
    # Fill in your groups
    GROUPS = ["unknown"]
    # Default priority is 50
    PRIORITY = 50
    # Pattern to match
    PATTERN = regex.compile(rb"(([ATCG]{3,4}( ([ATCG]{3,4})){3,}|[ATCG]{16,}))")
    # DNA Mappings
    DNA_MAP = {b"A": b"00", b"T": b"11", b"C": b"01", b"G": b"10"}

    def evaluate(self, match: re.Match) -> None:
        """
        Evaluate the target.
        :param match: A single regular expression match
        :return: None
        """

        results = []

        matches = match.group().split(b" ")
        for match in matches:
            binary = []
            for c in match:
                binary.append(self.DNA_MAP[bytes([c])])
            value = int(b"".join(binary), 2)
            results.append(
                value.to_bytes((value.bit_length() + 7) // 8, byteorder="big")
            )

        self.manager.register_data(self, b"".join(results))
