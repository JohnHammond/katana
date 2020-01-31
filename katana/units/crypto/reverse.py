"""
Reverse ciphertext

This will simply reverse the text and look for a flag.

"""

import io
from typing import Any

from katana.unit import NotEnglishUnit, NotApplicable
from katana.units.crypto import CryptoUnit


class Unit(NotEnglishUnit, CryptoUnit):

    # Fill in your groups
    GROUPS = ["crypto"]
    BLOCKED_GROUPS = ["crypto"]
    # Default priority is 50
    PRIORITY = 70
    # Do not recurse into self
    RECURSE_SELF = False

    # Inheriting from a CryptoUnit will ensure this will not run on URLs
    # or files that could be anything useful (image, document, audio, etc.)

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """

        # Reverse the given data.
        self.manager.register_data(self, (self.target.raw[::-1]))
