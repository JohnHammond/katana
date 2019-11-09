#!/usr/bin/env python3
import regex as re

from katana.unit import RegexUnit


class Unit(RegexUnit):
    # Fill in your groups
    GROUPS = ["crypto"]
    # Default priority is 50
    PRIORITY = 50
    # Pattern to match
    PATTERN = re.compile(rb"([1-5]+ ?)+", re.DOTALL | re.MULTILINE)

    def evaluate(self, match) -> None:
        """
        Evaluate the target.
        :param match: A single regular expression match
        :return: None
        """

        # Remove spaces
        data = match.group().replace(b" ", b"")
        # Grab alphabet
        alphabet = self.get("alphabet", "ABCDEFGHIKLMNOPQRSTUVWXYZ")

        # Decode the cipher
        result = []
        for idx in range(0, len(data), 2):
            x = int(chr(data[idx])) - 1
            y = int(chr(data[idx + 1])) - 1
            result.append(alphabet[y + x * 5])

        # Register the data
        self.manager.register_data(self, "".join(result))
