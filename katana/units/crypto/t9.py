"""
T9 Phone keypad Cipher 

This unit will decode a T9 cipher and look for flags.
This code relies on there being spaces between the T9 ciphers. 
It can be made cleaner with some regular expression processing, but it
has not yet been done...
"""

import io
from typing import Any

from katana.unit import PrintableDataUnit, NotApplicable

# JOHN: I do NOT use a dictionary for this, because the sorting and order would
#       get all messed up, Instead, a force an ordered list.
t9_mappings = [
    (b"7777", b"s"),
    (b"9999", b"z"),
    (b"222", b"c"),
    (b"111", b"@"),
    (b"333", b"f"),
    (b"444", b"i"),
    (b"555", b"l"),
    (b"666", b"o"),
    (b"777", b"r"),
    (b"888", b"v"),
    (b"999", b"y"),
    (b"22", b"b"),
    (b"33", b"e"),
    (b"44", b"h"),
    (b"55", b"k"),
    (b"66", b"n"),
    (b"77", b"q"),
    (b"88", b"u"),
    (b"99", b"x"),
    (b"11", b","),
    (b"2", b"a"),
    (b"3", b"d"),
    (b"4", b"g"),
    (b"5", b"j"),
    (b"6", b"m"),
    (b"7", b"p"),
    (b"8", b"t"),
    (b"9", b"w"),
    (b"1", b"_"),
    (b"0", b" "),
    (b"*", b" "),
]


class Unit(PrintableDataUnit):

    # Fill in your groups
    GROUPS = ["crypto"]
    BLOCKED_GROUPS = ["crypto"]
    # Default priority is 50
    PRIORITY = 50
    # Do not recurse into self
    RECURSE_SELF = False

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """
        return
        # Replace the mappings
        result = self.target.stream.read()
        for mapping in t9_mappings:
            result = result.replace(mapping[0], mapping[1])

        result = "".join(result.decode("latin-1"))

        # Quickly hotswap spaces
        # This can be made better with a regex at some point...?
        result = result.replace("  ", "@@DELIM@@")
        result = result.replace(" ", "")
        result = result.replace("@@DELIM@@", " ")

        self.manager.register_data(self, result)
