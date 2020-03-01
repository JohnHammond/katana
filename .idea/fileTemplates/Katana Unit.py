#!/usr/bin/env python3
from typing import Generator, Any

from katana.manager import Manager
from katana.target import Target
from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable


class Unit(BaseUnit):

    # Fill in your groups
    GROUPS = [ "unknown" ]
    # Default priority is 50
    PRIORITY = 50

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

    def enumerate(self) -> Generator[Any, None, None]:
        """
        Yield unit cases
        :return: Generator of target cases
        """

        yield None

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """
        raise RuntimeError("No evaluate method defined!")

    @classmethod
    def validate(cls, manager: Manager) -> None:
        """
        Stub to validate configuration parameters
        :param manager: Katana manager
        :return: None
        """
        super(Unit, cls).validate(manager)
