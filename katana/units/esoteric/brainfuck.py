"""
Unit for brainfuck esoteric language.

Given target data, this unit will ignore everything that is NOT valid
Brainfuck characters and exclude them. 

This unit includes a ``evaluate_brainfuck`` function that is often
used by other units like Ook and Pikalang. 
"""


from typing import Generator, Any
import time
import traceback

from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable

BRAINFUCK_CMDS = b".,[]<>+-"


def cleanup(code: bytes) -> str:
    """
    This is used for the Brainfuck operations. It will clean the
    provided code to only find the appropriate Brainfuck operators.

    :param code: A byte string of the Brainfuck code.

    :return: Only the bytes of appropriate Brainfuck operators.
    """

    code = [x.encode("utf-8") for x in code]
    return (
        b"".join(
            filter(
                lambda x: x in [b".", b",", b"[", b"]", b"<", b">", b"+", b"-"], code
            )
        )
    ).decode("utf-8")


def buildbracemap(code: bytes) -> dict:
    """
    This is used for the Brainfuck operations. It will match
    opening and closing braces for use within the Brainfuck program.

    :param code: A byte string of the Brainfuck code.

    :return: a bracemap dictionary
    """

    temp_bracestack, bracemap = [], {}

    for position, command in enumerate(code):
        if command == b"[":
            temp_bracestack.append(position)
        if command == b"]":
            try:
                start = temp_bracestack.pop()
                bracemap[start] = position
                bracemap[position] = start
            except IndexError as error:
                pass
    return bracemap


def evaluate_brainfuck(code: bytes, input_file, timeout: int = 1):
    """
    This function actually runs the provided Brainfuck operations and
    returns the standard output.

    :param code: The code to run as Brainfuck.

    :param input_file: A file to for the Brainfuck program to read as \
    standard input. If this is not provided, it will yield a newline.

    :param timeout: A timeout value in seconds. After this time \
    has elapsed, the Brainfuck code will stop executing.

    :return: The standard output for the Brainfuck program.
    """

    # Result from the brainfuck program
    output = []
    code = [c for c in code if c in BRAINFUCK_CMDS]

    # Build a tracemap of all jumps/calls
    bracemap = buildbracemap(code)

    # Initialize stack, PC, and SP
    cells, codeptr, cellptr = [0], 0, 0

    # Track time for timeout
    start_time = time.time()

    while codeptr < len(code) and time.time() < (start_time + timeout):
        command = code[codeptr]

        if command == b">":
            cellptr += 1
            if cellptr == len(cells):
                cells.append(0)

        if command == b"<":
            cellptr = 0 if cellptr <= 0 else cellptr - 1
        try:
            if command == b"+":
                cells[cellptr] = (cells[cellptr] + 1) % 256

            if command == b"-":
                cells[cellptr] = (cells[cellptr] - 1) % 256

            if command == b"[" and cells[cellptr] == 0:
                codeptr = bracemap[codeptr]
            if command == b"]" and cells[cellptr] != 0:
                codeptr = bracemap[codeptr]

            if command == b".":
                output.append(chr(cells[cellptr]))

            if command == b",":
                if not input_file:
                    cells[cellptr] = 10

                else:
                    cells[cellptr] = input_file.read(1)

        except (KeyError, TypeError) as e:
            # traceback.print_exc()
            return None

        codeptr += 1

    return "".join(output)


class Unit(BaseUnit):

    GROUPS = ["esoteric", "brainfuck"]
    """
    These are "tags" for a unit. Considering it is a Esoteric unit,
    "esoteric" is included, as well as the unit name "brainfuck".
    """

    PRIORITY = 50
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a defualt
    priority.
    """

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target. Run the target as Brainfuck code and
        give the standard output results to Katana.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        output = evaluate_brainfuck(
            self.target.raw,
            self.get("input_file", default=None),
            self.geti("bf_timeout", default=1),
        )

        if output:
            self.manager.register_data(self, output)
