#!/usr/bin/env python3
from typing import Generator, Any

from katana.manager import Manager
from katana.target import Target
from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable


class Unit(BaseUnit):
    # Fill in your groups
    GROUPS = ["crypto"]
    BLOCKED_GROUPS = ["crypto"]
    # Default priority is 50
    PRIORITY = 50

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

        if self.target.is_url and not self.target.url_accessible:
            raise NotApplicable("URL")

    def enumerate(self) -> Generator[Any, None, None]:
        """
        Yield unit cases
        :return: Generator of target cases
        """

        if self.geti("shift", None) is None:
            for shift in range(1, 256):
                yield shift
        else:
            yield self.geti("shift")

    def evaluate(self, shift: int) -> None:
        """
        Evaluate the target.
        :param shift: How much to shift each character by
        :return: None
        """

        # Our result array
        result = []

        # Build the new data
        for c in self.target.raw:
            if type(c) is int:
                result.append((c + shift) % 255)
            elif type(c) is bytes:
                result.append((ord(c) + shift) % 255)

        # Register the data
        self.manager.register_data(self, bytes(result))
