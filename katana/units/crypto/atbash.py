#!/usr/bin/env python3
import io
import string
from typing import Any

from katana.unit import NotEnglishAndPrintableUnit


class Unit(NotEnglishAndPrintableUnit):
    # Fill in your groups
    GROUPS = ["crypto"]
    # Default priority is 50
    PRIORITY = 60
    # Do not recurse into self
    RECURSE_SELF = False

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
            try:
                for ch in iter(lambda: stream.read(1), ""):
                    if ch in string.ascii_uppercase:
                        new_string.append(
                            reverse_upper[string.ascii_uppercase.index(ch)]
                        )
                    elif ch in string.ascii_lowercase:
                        new_string.append(
                            reverse_lower[string.ascii_lowercase.index(ch)]
                        )
                    else:
                        new_string.append(ch)
            except UnicodeDecodeError:
                pass

        result = "".join(new_string)
        self.manager.register_data(self, result)
