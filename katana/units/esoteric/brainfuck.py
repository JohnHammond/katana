#!/usr/bin/env python3
from typing import Generator, Any
import time

from katana.manager import Manager
from katana.target import Target
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
        if command == "[":
            temp_bracestack.append(position)
        if command == "]":
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

    # Only grab the valid brainfuck code
    code = bytes([c for c in code if c in BRAINFUCK_CMDS])

    # Build a tracemap of all jumps/calls
    bracemap = buildbracemap(code)

    # Initialize stack, PC, and SP
    cells, codeptr, cellptr = [0], 0, 0

    # Track time for timeout
    start_time = time.time()

    while codeptr < len(code) and time.time() < (start_time + timeout):
        command = code[codeptr]

        if command == ">":
            cellptr += 1
            if cellptr == len(cells):
                cells.append(0)

        if command == "<":
            cellptr = 0 if cellptr <= 0 else cellptr - 1
        try:
            if command == "+":
                cells[cellptr] = (cells[cellptr] + 1) % 256

            if command == "-":
                cells[cellptr] = (cells[cellptr] - 1) % 256

            if command == "[" and cells[cellptr] == 0:
                codeptr = bracemap[codeptr]
            if command == "]" and cells[cellptr] != 0:
                codeptr = bracemap[codeptr]

            if command == ".":
                output.append(chr(cells[cellptr]))

            if command == ",":
                if not input_file:
                    cells[cellptr] = 10

                else:
                    cells[cellptr] = input_file.read(1)

        except (KeyError, TypeError):
            return None

        codeptr += 1

    return "".join(output)


class Unit(BaseUnit):
    # Fill in your groups
    GROUPS = ["esoteric"]
    # Default priority is 50
    PRIORITY = 50

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

        if self.target.raw.count(b"+") < self.geti("threshold", default=5):
            raise NotApplicable("threshold not met")

    def enumerate(self) -> Generator[Any, None, None]:
        """
        Yield unit cases
        :return: Generator of target cases
        """

        yield None

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """
        raise RuntimeError("No evaluate method defined!")

    @classmethod
    def validate(cls, manager: Manager) -> None:
        """
        Stub to validate configuration parameters
        :param manager: Katana manager
        :return: None
        """
        super(Unit, cls).validate(manager)
