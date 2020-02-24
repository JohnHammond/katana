"""
Unit for Cow esoteric language.

Given target data, this unit will ignore everything that is NOT valid
Cow characters and exclude them. 

"""

#!/usr/bin/env python3

from typing import Any
import time
import traceback

from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable

command_list = [
    "moo",
    "mOo",
    "moO",
    "mOO",
    "Moo",
    "MOo",
    "MoO",
    "MOO",
    "OOO",
    "MMM",
    "OOM",
    "oom",
]


def cleanup(code: bytes) -> bytes:
    """
    This is used for the Cow operations. It will clean the
    provided code to only find the appropriate Cow operators.

    :param code: A byte string of the Cow code.

    :return: Only the bytes of appropriate Cow operators.
    """

    clean_code = []
    for c in code:
        if c in b"oOmM":
            clean_code.append(c)

    return clean_code


def build_jumpmap(code: bytes) -> dict:
    """
    This is used for the Cow operations. It will match
    opening and closing braces for use within the Cow program.

    :param code: A byte string of the Cow code.

    :return: a jumpmap dictionary
    """
    jumpmap = {}

    for pointer in range(0, len(code), 3):

        if code[pointer : pointer + 3] == b"MOO":
            pointer2 = pointer + 6
            while code[pointer2 : pointer2 + 3] != b"moo":
                pointer2 += 3

            jumpmap[pointer] = pointer2
            jumpmap[pointer2] = pointer

        elif code[pointer : pointer + 3] == b"moo" and jumpmap.get(pointer, -1) == -1:
            raise SyntaxError("Unmatched moo")
    return jumpmap


def evaluate_cow(code, input_file, timeout=-1):
    """
    This function actually runs the provided Cow operations and
    returns the standard output.

    :param code: The code to run as Cow.

    :param input_file: A file to for the Cow program to read as \
    standard input. If this is not provided, it will yield a newline.

    :param timeout: A timeout value in seconds. After this time \
    has elapsed, the Cow code will stop executing.

    :return: The standard output for the Cow program,
    """

    output = []
    code = b"".join([c.strip() for c in code])
    try:
        code = cleanup(list(code))
        jumpmap = build_jumpmap(code)
    except:
        traceback.print_exc()
        return ""
    if not code:
        return
    cells, codeptr, cellptr, register = [0], 0, 0, None

    start_time = time.time()

    # by default, timeout is -1 and the code runs for as long as possible
    while codeptr < len(code) and (timeout < 0 or time.time() < (start_time + timeout)):
        if codeptr < 0:
            # weird behavior here
            # if we encounter a mOO, we make the pointer negative and continue
            # now we know that if the code pointer is negative, mOO was called
            # so we need to make the command be what is pointed at in memory
            command = command_list[cells[cellptr]]
            codeptr = -codeptr
        else:
            command = code[codeptr : codeptr + 3]

        # convert the command to bytes
        command = bytes(command)

        if command == b"moO":  # moO-ve memory pointer forward
            cellptr += 1
            if cellptr == len(cells):
                cells.append(0)

        if command == b"mOo":  # mOo-ve memory pointer backward
            cellptr = 0 if cellptr <= 0 else cellptr - 1
        try:
            if command == b"MoO":
                cells[cellptr] = cells[cellptr] + 1 if cells[cellptr] < 255 else 0

            if command == b"MOo":
                cells[cellptr] = cells[cellptr] - 1 if cells[cellptr] > 0 else 255

            if command == b"MOO" and cells[cellptr] == 0:
                nextptr = jumpmap.get(codeptr, -1)

                if nextptr < 0:
                    nextptr = codeptr + 6
                    while code[nextptr : nextptr + 3] != b"moo":
                        nextptr += 3

                codeptr = nextptr

            if command == b"moo":
                nextptr = jumpmap.get(codeptr, -1)

                if nextptr < 0:
                    nextptr = codeptr - 6
                    while code[nextptr : nextptr + 3] != b"MOO":
                        nextptr -= 3
                else:
                    nextptr -= 3

                codeptr = nextptr

            if command == b"Moo":
                if cells[cellptr] == 0:
                    # cells[cellptr] = input_file.read(1)
                    cells[cellptr] = b"\n"
                else:
                    output.append(chr(cells[cellptr]))

            if command == b"mOO":
                codeptr = -codeptr - 3

            if command == b"OOO":
                cells[cellptr] = 0

            if command == b"MMM":
                if register is None:
                    register = cells[cellptr]
                else:
                    cells[cellptr] = register
                    register = None

            if command == b"OOM":
                output.append(cells[cellptr])

            if command == b"oom":
                # cells[cellptr] = input_file.read(1)
                cells[cellptr] = b"\n"

            if len(command) < 3:
                return None

        except (KeyError, TypeError):

            return None

        codeptr += 3

    output = "".join(output)
    return output


class Unit(BaseUnit):

    GROUPS = ["esoteric", "cow"]
    """
    These are "tags" for a unit. Considering it is a Esoteric unit,
    "esoteric" is included, as well as the unit name "cow".
    """

    RECURSE_SELF = False
    """
    There is no reason to recurse into yourself. We shouldn't get cow out.
    """

    PRIORITY = 50
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a defualt
    priority.
    """

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        if b"moo" not in self.target.stream:
            raise NotApplicable("no moo in target, must not be cow esolang")

        # We don't run this on URLs
        if self.target.is_url and not self.target.url_accessible:
            raise NotApplicable("URL")

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target. Run the target as Cow code and
        give the standard output results to Katana.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        output = evaluate_cow(
            self.target.stream,
            self.get("input_file", default=None),
            self.geti("cow_timeout", default=1),
        )

        if output:
            self.manager.register_data(self, output)
