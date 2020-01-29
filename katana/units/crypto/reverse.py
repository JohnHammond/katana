"""
Reverse ciphertext

This will simply reverse the text and look for a flag.

"""

import io
from typing import Any

from katana.unit import NotEnglishUnit, NotApplicable


class Unit(NotEnglishUnit):

    # Fill in your groups
    GROUPS = ["crypto"]
    BLOCKED_GROUPS = ["crypto"]
    # Default priority is 50
    PRIORITY = 70
    # Do not recurse into self
    RECURSE_SELF = False

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """

        with io.TextIOWrapper(self.target.stream, encoding="utf-8") as stream:

            # Reverse the given data.
            self.manager.register_data(self, (stream.read()[::-1]))
