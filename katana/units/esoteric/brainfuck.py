#!/usr/bin/env python3
from typing import Generator, Any
import time
import traceback

from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable

BRAINFUCK_CMDS = b".,[]<>+-"


def cleanup(code):
    code = [x.encode("utf-8") for x in code]
    return (
        b"".join(
            filter(
                lambda x: x in [b".", b",", b"[", b"]", b"<", b">", b"+", b"-"], code
            )
        )
    ).decode("utf-8")


def buildbracemap(code):

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


def evaluate_brainfuck(code, input_file, timeout=1):

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

    # Fill in your groups
    GROUPS = ["esoteric", "brainfuck"]

    # Default priority is 50
    PRIORITY = 50

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """

        output = evaluate_brainfuck(
            self.target.raw,
            self.get("input_file", default=None),
            self.geti("bf_timeout", default=1),
        )

        if output:
            self.manager.register_data(self, output)
