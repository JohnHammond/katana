"""
ROT47 decoder

The gist of this code is ripped from 
https://rot47.net/_py/rot47.txt. 

This unit inherits from the 
:class:`katana.unit.NotEnglishAndPrintableUnit` class, as we can expect
the data to still be printable characters (letters, numbers and punctuation)
but not readable English. It also inherits from the 
:class:`katana.units.crypto.CryptoUnit` class to ensure it is not a viable
URL or potentially useful file.

"""

import io
from typing import Any

from katana.unit import NotEnglishAndPrintableUnit
from katana.units.crypto import CryptoUnit


class Unit(NotEnglishAndPrintableUnit, CryptoUnit):

    GROUPS = ["crypto", "rot47"]
    """
    These are "tags" for a unit. Considering it is a Crypto unit, "crypto"
    is included, and the name of the unit, "rot47".
    """

    BLOCKED_GROUPS = ["crypto"]
    """
    These are tags for groups to not recurse into. Recursing into other 
    crypto units would be silly.
    """

    PRIORITY = 45
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a slightly
    higher priority.
    """

    RECURSE_SELF = False
    """
    Do not recurse into self
    """

    def do_rot47(self, s):
        """
        Shamelessly stolen from https://rot47.net/_py/rot47.txt

        This function takes a string and performs the ROT47 operation 
        on it.

        :param s: The byte string to perform the ROT47 operation on.
        """
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

        :param case: A case returned by ``enumerate``. For this unit, \
        the ``enumerate`` function is not used.

        :return: None
        """

        result = self.do_rot47(self.target.raw)
        self.manager.register_data(self, result)
