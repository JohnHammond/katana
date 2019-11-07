#!/usr/bin/env python3
import regex
import re

from katana.unit import RegexUnit


class Unit(RegexUnit):
    # Fill in your groups
    GROUPS = ["unknown"]
    # Default priority is 50
    PRIORITY = 50
    # Pattern to match
    PATTERN = regex.compile(rb"", re.DOTALL | re.MULTILINE)

    def evaluate(self, match: re.Match) -> None:
        """
        Evaluate the target.
        :param match: A single regular expression match
        :return: None
        """
        raise RuntimeError("No evaluate method defined!")
