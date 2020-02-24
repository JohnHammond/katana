"""
Unit for the Ook esoteric language.

This unit will map the Ook operations to their Brainfuck equivalant,
and then pass along the actual execution to the Brainfuck unit's
``evaluate_brainfuck`` function.

"""


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
    """
    This function will actually evaluate the Ook code, by translating
    it to Brainfuck character mapping and then passing it to
    the ``evaluate_brainfuck`` unit.

    This function also verifies that the Ook code is not an
    odd-length string. That would result in improper Ook code.

    :param code: A byte string of the Ook code.

    :param input_file: A file to for the Ook program to read as \
    standard input. If this is not provided, it will yield a newline.

    :param timeout: A timeout value in seconds. After this time \
    has elapsed, the Ook code will stop executing.

    :return: The standard output for the Ook program,
    """

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
            return

    return evaluate_brainfuck(bf_code, input_file, timeout)


class Unit(NotEnglishUnit):

    GROUPS = ["esoteric", "ook"]
    """
    These are "tags" for a unit. Considering it is a Esoteric unit,
    "esoteric" is included, as well as the unit name "ook".
    """

    PRIORITY = 50
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has default
    priority
    """

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        matches = OOK_REGEX.findall(self.target.raw)

        if matches is None or matches == []:
            raise NotApplicable("no ook potential found")
        else:
            self.code = b"".join([m[-1] for m in matches])

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target. Run the target as Ook code and
        give the standard output results to Katana.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        output = evaluate_ook(
            self.code,
            self.get("input_file", default=None),
            self.geti("ook_timeout", default=1),
        )

        if output:
            self.manager.register_data(self, output)
