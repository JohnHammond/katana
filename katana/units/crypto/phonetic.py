#!/usr/bin/env python3
import regex
import re

from katana.unit import RegexUnit

phonetic_names = (
    "("
    + "|".join(
        [
            "alfa",
            "alpha",
            "bravo",
            "charlie",
            "delta",
            "echo",
            "foxtrot",
            "golf",
            "hotel",
            "india",
            "juliet",
            "kilo",
            "lima",
            "mike",
            "november",
            "oscar",
            "papa",
            "quebec",
            "romeo",
            "sierra",
            "tango",
            "uniform",
            "victor",
            "whiskey",
            "xray",
            "x-ray",
            "yankee",
            "zulu",
        ]
    )
    + ")"
)


class Unit(RegexUnit):
    # Fill in your groups
    GROUPS = ["unknown"]
    # Default priority is 50
    PRIORITY = 50
    # Pattern to match
    PATTERN = regex.compile(
        bytes(rf"{phonetic_names} ?({phonetic_names} ?){{5,}}", "utf-8"),
        re.DOTALL | re.MULTILINE | re.IGNORECASE,
    )

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

    def evaluate(self, match: re.Match) -> None:
        """
        Evaluate the target.
        :param match: A single regular expression match
        :return: None
        """

        # Decode the data
        result = []
        for word in match.group().split(b" "):
            result.append(word[0])

        # Register data
        self.manager.register_data(self, bytes(result))
