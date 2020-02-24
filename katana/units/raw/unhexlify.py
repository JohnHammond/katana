"""
Decode data represented as hexadecimal values.

This unit will return the data represented in both little-endian notation
and in big-endian notation.
"""


import regex as re

from katana.unit import RegexUnit


class Unit(RegexUnit):

    PRIORITY = 50
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a
    moderate-high unit priority.
    """

    GROUPS = ["raw", "decode", "unhexlify"]
    """
    These are "tags" for a unit. Considering it is a Raw unit, "raw"
    is included, as well as the tag "decode", and the unit name itself,
    "unhexlify".
    """

    PATTERN = re.compile(rb"[0-9a-fA-F]+( ([0-9a-fA-F]+))*")
    """
    The pattern to match for hexadecimal data.
    """

    def evaluate(self, match):
        """
        Evaluate the target. Convert the hexadecimal data found within the 
        target and recurse on any new found information.

        :param match: A match returned by the ``RegexUnit``.

        :return: None. This function should not return any data.
        """

        match = match.group().split(b" ")

        # Decode big endian
        result = b""
        for m in match:
            v = int(m, 16)
            result += v.to_bytes((v.bit_length() + 7) // 8, byteorder="little")

        self.manager.register_data(self, result)

        # Decode little endian
        result = b""
        for m in match:
            v = int(m, 16)
            result += v.to_bytes((v.bit_length() + 7) // 8, byteorder="big")

        self.manager.register_data(self, result)
