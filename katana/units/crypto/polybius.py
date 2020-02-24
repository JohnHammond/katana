"""
Attempt to decrypt a Polybius Square cipher.

You can read more about the Polybius Square cipher here:
https://en.wikipedia.org/wiki/Polybius_square

This unit will search for numbers and translate them to the proper
mapping within a Polybius square. 
"""

import regex as re

from katana.unit import RegexUnit


class Unit(RegexUnit):

    GROUPS = ["crypto", "polybius"]
    """
    These are "tags" for a unit. Considering it is a Crypto unit, "crypto"
    is included, as well as the name for this unit.
    """

    PRIORITY = 50
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a default
    priority.
    """

    PATTERN = re.compile(rb"([1-5]+ ?)+", re.DOTALL | re.MULTILINE)
    """
    This pattern is used specifically for this unit to detect the data 
    used for the Polybius cipher.
    """

    def evaluate(self, match) -> None:
        """
        Evaluate the target.

        :param match: A single regular expression match. In this case, this \
        should retrieve numbers to be used to map to letters within the \
        Polybius Square.

        :return: None. This function should not return any data.
        """

        # Remove spaces
        data = match.group().replace(b" ", b"")
        # Grab alphabet
        alphabet = self.get("alphabet", "ABCDEFGHIKLMNOPQRSTUVWXYZ")

        # Decode the cipher
        result = []
        # subtract one from the full length so we do not have index errors
        for idx in range(0, len(data) - 1, 2):
            x = int(chr(data[idx])) - 1
            y = int(chr(data[idx + 1])) - 1
            result.append(alphabet[y + x * 5])

        # Register the data
        self.manager.register_data(self, "".join(result))
