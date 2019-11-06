#!/usr/bin/env python3
from typing import Generator, Any
from math import gcd
from string import ascii_uppercase
from Crypto.Util.number import inverse

from katana.manager import Manager
from katana.target import Target
from katana.unit import NotApplicable, NotEnglishAndPrintableUnit


def affine(c: int, a: int, b: int, alphabet: bytes):
    """ Perform the affine cipher for a single letter """
    if isinstance(c, int):
        c = bytes([c])
    c = c.upper()[0]
    if c in alphabet:
        return alphabet[(a * alphabet.index(c) + b) % len(alphabet)]
    else:
        return c


class Unit(NotEnglishAndPrintableUnit):
    # Fill in your groups
    GROUPS = ["crypto"]
    BLOCKED_GROUPS = ["crypto"]
    # Default priority is 50
    PRIORITY = 65
    # Prevent recursion into itself
    RECURSE_SELF = False

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

        if not self.target.is_printable:
            raise NotApplicable("Not printable")

    def enumerate(self) -> Generator[Any, None, None]:
        """
        Yield unit cases
        :return: Generator of target cases
        """
        affine_alphabet = self.get("alphabet", default=ascii_uppercase)
        affine_a = self.geti("a", default=-1)
        affine_b = self.geti("b", default=-1)

        if affine_a == -1 and affine_b == -1:
            for a in range(len(affine_alphabet)):
                for b in range(len(affine_alphabet)):
                    if gcd(a, len(affine_alphabet)):
                        yield (a, b)

        elif affine_a != -1 and affine_b == -1:
            for b in range(len(affine_alphabet)):
                if gcd(affine_a, len(affine_alphabet)):
                    yield (affine_a % len(affine_alphabet), b)

        elif affine_b != -1 and affine_a == -1:
            for a in range(len(affine_alphabet)):
                if gcd(a, len(affine_alphabet)):
                    yield (a, affine_b % len(affine_alphabet))
        else:
            if affine_a != -1 and affine_b != -1:
                if gcd(affine_a, len(affine_alphabet)):
                    yield affine_a, affine_b

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """

        a, b = case
        alphabet = bytes(self.get("alphabet", ascii_uppercase), "utf-8")
        result = []

        new_b = abs(b - len(alphabet))
        new_a = inverse(a, len(alphabet))
        new_b = (new_a * new_b) % len(alphabet)

        for letter in self.target.raw:
            # Attempt to inverse the affine cipher
            result.append(affine(letter, new_a, new_b, alphabet))

        # Put it back together
        plaintext = bytes(result)
        if plaintext != self.target.raw:
            self.manager.register_data(
                self, {f"{a},{b}": plaintext.decode("utf-8")}, recurse=False
            )
