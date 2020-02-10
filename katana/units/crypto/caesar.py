#!/usr/bin/env python3
from typing import Generator, Any
import string
import io

from katana.manager import Manager
from katana.target import Target
from katana.unit import NotApplicable, NotEnglishAndPrintableUnit


def shift_char(c: str, shift: int, alphabet: str) -> str:
    idx = alphabet.find(c)
    if idx == -1:
        return None
    return alphabet[(idx + shift) % len(alphabet)]


class Unit(NotEnglishAndPrintableUnit):
    # Fill in your groups
    GROUPS = ["crypto"]
    BLOCKED_GROUPS = ["crypto"]
    # Default priority is 50
    PRIORITY = 40
    # No recursing into self
    RECURSE_SELF = False

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        # We don't run Caesar on URLs
        if self.target.is_url and not self.target.url_accessible:
            raise NotApplicable("URL")

    def enumerate(self) -> Generator[Any, None, None]:
        """
        Yield unit cases
        :return: Generator of target cases
        """

        # We either guess all, or a specific shift depending on config
        if self.geti("shift", None) is None:
            for shift in range(1, len(string.ascii_lowercase)):
                yield shift
        else:
            yield self.geti("shift")

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """
        result = []

        with io.TextIOWrapper(self.target.stream, encoding="utf-8") as stream:
            for c in iter(lambda: stream.read(1), ""):
                new_c = shift_char(c, case, string.ascii_uppercase)
                if new_c is None:
                    new_c = shift_char(c, case, string.ascii_lowercase)
                if new_c is None:
                    new_c = c
                result.append(new_c)

        result = "".join(result)
        self.manager.register_data(self, result)
