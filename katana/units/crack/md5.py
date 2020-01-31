#!/usr/bin/env python3
from typing import Generator, Any
import hashlib
import regex as re

from katana.manager import Manager
from katana.target import Target
from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable

MD5_PATTERN = re.compile(rb"[a-fA-F0-9]{32}", re.DOTALL | re.MULTILINE)


class Unit(BaseUnit):
    # Fill in your groups
    GROUPS = ["crack", "bruteforce"]
    # Default priority is 50
    PRIORITY = 75
    # Disable all recursion

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

        # Find matches in the target
        self.matches = MD5_PATTERN.findall(self.target.raw)

        if self.matches is None or len(self.matches) == 0:
            raise NotApplicable("No md5 hashes found")

    def enumerate(self) -> Generator[Any, None, None]:
        """
        Yield unit cases
        :return: Generator of target cases
        """

        # Manually specified passwords first
        passwords = self.manager.get(str(self), "password", fallback="")
        if passwords != "":
            for p in passwords.split(","):
                yield bytes(p, "utf-8")

        # Dictionary passwords next
        dictionary = self.manager.get(str(self), "dict", fallback=None)
        if dictionary is not None:
            with open(dictionary, "rb") as f:
                for line in f:
                    yield line.rstrip(b"\n")

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """

        hash = bytes(hashlib.md5(case).hexdigest(), "utf-8")
        for match in self.matches:
            if hash == match:
                self.manager.register_data(
                    self, {match.decode("utf-8"): repr(case)[2:-1]}, recurse=False
                )
                return

    @classmethod
    def validate(cls, manager: Manager) -> None:
        """
        Stub to validate configuration parameters
        :param manager: Katana manager
        :return: None
        """
        super(Unit, cls).validate(manager)
