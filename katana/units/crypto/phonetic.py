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

    GROUPS = ["crypto", "phonetic"]
    """
    These are "tags" for a unit. Considering it is a Crypto unit, "crypto"
    is included, as well as the name of the unit, "phonetic". 
    """

    BLOCKED_GROUPS = ["crypto"]
    """
    This unit does not recurse into other Crypto units because that might
    spiral into a disaster.
    """

    PRIORITY = 50
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. 
    """

    PATTERN = regex.compile(
        bytes(rf"{phonetic_names} ?({phonetic_names} ?){{5,}}", "utf-8"),
        re.DOTALL | re.MULTILINE | re.IGNORECASE,
    )
    """
    This pattern is used specifically for this unit to detect the NATO
    phonetic alphabet. 
    """

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
