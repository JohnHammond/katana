"""
Decode data represented as decimal values.

This unit will return the data represented in both little-endian notation
and in big-endian notation.
"""

import regex as re

from katana.unit import RegexUnit


class Unit(RegexUnit):

    PRIORITY = 50
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has the default
    priority.
    """

    GROUPS = ["raw", "decode", "undecimal"]
    """
    These are "tags" for a unit. Considering it is a Raw unit, "raw"
    is included, as well as the tag "decode", and the unit name itself,
    "undecimal"
    """

    PATTERN = re.compile(rb"[0-9]+( ([0-9]+))*")
    """
    The pattern to match for decimal data.
    """

    def evaluate(self, match):
        """
        Evaluate the target. Convert the decimal data found within the target
        and recurse on any new found information.

        :param match: A match returned by the ``RegexUnit``.

        :return: None. This function should not return any data.
        """

        match = match.group()
        if len(match) < 12:
            return

        match = match.split(b" ")

        # Decode big endian
        result = b""
        for m in match:
            v = int(m)
            result += v.to_bytes((v.bit_length() + 7) // 8, byteorder="little")

        self.register_result(result)

        # Decode little endian
        result = b""
        for m in match:
            v = int(m)
            result += v.to_bytes((v.bit_length() + 7) // 8, byteorder="big")

        self.register_result(result)
