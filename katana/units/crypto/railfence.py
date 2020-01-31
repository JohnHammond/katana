"""
Railfence Cipher decoder

This takes arguments "rails" and "offset" which you can set, 
but they will be bruteforce within the range of 2-10 and 0-10 
respectively.

The code for this is shamelessly stolen from
https://github.com/tothi/railfence

"""

import io
from typing import Any
import string

from katana.unit import NotEnglishAndPrintableUnit, NotApplicable
from katana.units.crypto import CryptoUnit

# Stolen from https://github.com/tothi/railfence
def encryptFence(plain, rails, offset=0, debug=False):
    cipher = ""

    # offset
    plain = "#" * offset + plain

    length = len(plain)
    fence = [["#"] * length for _ in range(rails)]

    # build fence
    rail = 0
    for x in range(length):
        fence[rail][x] = plain[x]
        if rail >= rails - 1:
            dr = -1
        elif rail <= 0:
            dr = 1
        rail += dr

    # print pretty fence
    if debug:
        printFence(fence)

    # read fence
    for rail in range(rails):
        for x in range(length):
            if fence[rail][x] != "#":
                cipher += fence[rail][x]
    return cipher


# Stolen from https://github.com/tothi/railfence
def decryptFence(cipher, rails, offset=0):
    plain = ""

    # offset
    if offset:
        t = encryptFence("o" * offset + "x" * len(cipher), rails)
        for i in range(len(t)):
            if t[i] == "o":
                cipher = cipher[:i] + b"#" + cipher[i:]

    length = len(cipher)
    fence = [["#"] * length for _ in range(rails)]

    # build fence
    i = 0
    for rail in range(rails):
        p = rail != (rails - 1)
        x = rail
        while x < length and i < length:
            fence[rail][x] = cipher[i]
            if p:
                x += 2 * (rails - rail - 1)
            else:
                x += 2 * rail
            if (rail != 0) and (rail != (rails - 1)):
                p = not p
            i += 1

    # read fence
    for i in range(length):
        for rail in range(rails):
            if fence[rail][i] != "#":
                plain += chr(fence[rail][i])
    return plain


class Unit(NotEnglishAndPrintableUnit, CryptoUnit):

    # Fill in your groups
    GROUPS = ["crypto"]
    BLOCKED_GROUPS = ["crypto"]
    # Default priority is 50
    PRIORITY = 60
    # Do not recurse into self
    RECURSE_SELF = False

    # Inheriting from a CryptoUnit will ensure this will not run on URLs
    # or files that could be anything useful (image, document, audio, etc.)

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        self.rails = self.geti("rails")
        self.offset = self.geti("offset")

        self.raw_target = self.target.stream.read()

    def enumerate(self):

        # If they do not supply any offset, bruteforce it
        if self.offset is None:
            offsets = range(0, 10)
        else:
            offsets = [self.offset]

        if self.rails is None:
            rails = range(2, 10)
        else:
            rails = [self.rails]

        # Now permutate through all of these and run them!
        for offset in offsets:
            for rail in rails:
                yield (rail, offset)

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by enumerate
        :return: None
        """

        result = decryptFence(self.target.raw, case[0], case[1])
        self.manager.register_data(self, result)
