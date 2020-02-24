"""
Reverse ciphertext

This will simply reverse the text and look for a flag.

This unit inherits from the 
:class:`katana.unit.NotEnglishUnit` class, as we can expect
the data to not be readable English (if it is in fact reverse text). 
It also inherits from the  :class:`katana.units.crypto.CryptoUnit` 
class to ensure it is not a viable URL or potentially useful file.

"""

import io
from typing import Any

from katana.unit import NotEnglishUnit, NotApplicable
from katana.units.crypto import CryptoUnit


class Unit(NotEnglishUnit, CryptoUnit):

    GROUPS = ["crypto", "reverse"]
    """
    These are "tags" for a unit. Considering it is a Crypto unit, "crypto"
    is included.
    """

    BLOCKED_GROUPS = ["crypto"]
    """
    These are tags for groups to not recurse into. Recursing into other crypto units
    would be silly.
    """

    PRIORITY = 70
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a lower
    priority.
    """

    RECURSE_SELF = False
    """
    Do not recurse into self
    """

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target. This simply reverses the target.
        
        :param case: A case returned by enumerate. In this unit, \
        the ``enumerate`` function is not used.
        
        :return: None. This function should not return any data.
        """

        # Reverse the given data.
        self.manager.register_data(self, (self.target.raw[::-1]))
