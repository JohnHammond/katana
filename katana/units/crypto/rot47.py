"""
ROT47 decoder

The gist of this code is ripped from 
https://rot47.net/_py/rot47.txt. The unit takes the target, and
if it does not look English text but it is clearly printable characters, it
attempts to rot47 the data. 

"""

import io
import string
from typing import Any

from katana.unit import NotEnglishAndPrintableUnit


class Unit(NotEnglishAndPrintableUnit):

    # Fill in your groups
    GROUPS = ["crypto"]
    BLOCKED_GROUPS = ["crypto"]
    # Default priority is 50
    PRIORITY = 45
    # Do not recurse into self
    RECURSE_SELF = False

    # Shamelessly stolen from https://rot47.net/_py/rot47.txt
    def do_rot47(self, s):
        x = []
        for i in range(len(s)):
            j = ord(s[i])
            if 33 <= j <= 126:
                x.append(chr(33 + ((j + 14) % 94)))
            else:
                x.append(s[i])
        return "".join(x)

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """

        new_string = []
        reverse_upper = string.ascii_uppercase[::-1]
        reverse_lower = string.ascii_lowercase[::-1]

        with io.TextIOWrapper(self.target.stream, encoding="utf-8") as stream:

            result = self.do_rot47(stream.read())
            self.manager.register_data(self, result)
