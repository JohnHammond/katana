#!/usr/bin/env python3
from typing import Generator, Any
import time
import traceback
import re

from katana.unit import NotEnglishUnit
from katana.unit import NotApplicable
from katana.units.esoteric.brainfuck import evaluate_brainfuck

OOK_PATTERN = rb"((Ook)?(\.|!|\?))"
OOK_REGEX = re.compile(OOK_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)

translate_table = {
    b".?": b">",
    b"?.": b"<",
    b"..": b"+",
    b"!!": b"-",
    b"!.": b".",
    b".!": b",",
    b"!?": b"[",
    b"?!": b"]",
}


def evaluate_ook(code, input_file, timeout=1):

    # Ook should never be an odd-length string
    if len(code) % 2 != 0:
        return None

    # Now we need to translate this to Brainfuck
    bf_code = []

    for idx in range(0, len(code), 2):
        try:
            command = code[idx : idx + 2]
            bf_code.append(translate_table[command])
        except KeyError as e:
            traceback.print_exc()
            return

    return evaluate_brainfuck(bf_code, input_file, timeout)


class Unit(NotEnglishUnit):

    # Fill in your groups
    GROUPS = ["esoteric", "ook"]

    # Default priority is 50
    PRIORITY = 50

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        matches = OOK_REGEX.findall(self.target.raw)

        if matches is None or matches == []:
            raise NotApplicable("no ook potential found")
        else:
            self.code = b"".join([m[-1] for m in matches])

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """

        output = evaluate_ook(
            self.code,
            self.get("input_file", default=None),
            self.geti("ook_timeout", default=1),
        )

        if output:
            self.manager.register_data(self, output)
