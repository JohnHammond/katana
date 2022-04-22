"""
Decode data represented as binary values.

This unit will return the data represented in both little-endian notation
and in big-endian notation.
"""

from typing import List
import regex as re

from katana.unit import RegexUnit


class Unit(RegexUnit):

    PRIORITY = 50
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has the default
    priority.
    """

    GROUPS = ["raw", "decode"]
    """
    These are "tags" for a unit. Considering it is a Raw unit, "raw"
    is included, as well as the tag "decode", and the name of the unit itself,
    "unbinary".
    """

    PATTERN = re.compile(rb"(([01]{7,8}( ([01]{7,8})){3,}|[01]{32,}))")
    """
    The pattern to match for binary data.
    """

    def evaluate(self, match):
        """
        Evaluate the target. Convert the binary data found within the target
        and recurse on any new found information.

        :param match: A match returned by the ``RegexUnit``.

        :return: None. This function should not return any data.
        """

        match = match.group()
        if len(match) < 40:
            return

        match: List[bytes] = match.split(b" ")
        result = b""

        # Convert all the bits into bytes (little endian)
        for m in match:
            result += int(m, 2).to_bytes((len(m) + 7) // 8, byteorder="little")

        self.register_result(result)

        result = b""
        for m in match:
            result += int(m, 2).to_bytes((len(m) + 7) // 8, byteorder="big")

        self.register_result(result)