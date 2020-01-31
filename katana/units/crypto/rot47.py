"""
ROT47 decoder

The gist of this code is ripped from 
https://rot47.net/_py/rot47.txt. The unit takes the target, and
if it does not look English text but it is clearly printable characters, it
attempts to rot47 the data. 

"""

import io
from typing import Any

from katana.unit import NotEnglishAndPrintableUnit
from katana.units.crypto import CryptoUnit


class Unit(NotEnglishAndPrintableUnit, CryptoUnit):

    # Fill in your groups
    GROUPS = ["crypto"]
    BLOCKED_GROUPS = ["crypto"]
    # Default priority is 50
    PRIORITY = 45
    # Do not recurse into self
    RECURSE_SELF = False

    # Inheriting from a CryptoUnit will ensure this will not run on URLs
    # or files that could be anything useful (image, document, audio, etc.)

    # Shamelessly stolen from https://rot47.net/_py/rot47.txt
    def do_rot47(self, s):
        x = []
        for i in range(len(s)):
            j = s[i]
            if 33 <= j <= 126:
                x.append(33 + ((j + 14) % 94))
            else:
                x.append(s[i])
        return b"".join([chr(z).encode("latin-1") for z in x])

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """

        result = self.do_rot47(self.target.raw)
        self.manager.register_data(self, result)
