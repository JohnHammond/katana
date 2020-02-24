"""
Railfence Cipher decoder

This takes arguments ``rails`` and ``offset`` which you can set, 
but they will be bruteforce within the range of 2-10 and 0-10 
respectively.

This unit inherits from the 
:class:`katana.unit.NotEnglishAndPrintableUnit` class, as we can expect
the data to still be printable characters (letters, numbers and punctuation)
but not readable English. It also inherits from the 
:class:`katana.units.crypto.CryptoUnit` class to ensure it is not a viable
URL or potentially useful file.

The code for this is shamelessly stolen from
https://github.com/tothi/railfence

"""

import io
from typing import Any
import string

from katana.unit import NotEnglishAndPrintableUnit, NotApplicable
from katana.units.crypto import CryptoUnit


def encryptFence(plain, rails, offset=0):
    """
    Stolen from https://github.com/tothi/railfence.

    This is a convenience function to encrypt data with the Railfence
    cipher.

    :param plain: The plaintext as a string.

    :param rails: The integer number of rails to use in the Railfence cipher \
    operations.

    :param offset: The integer offset number to use in the Railfence cipher \
    operations.
    """

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

    # read fence
    for rail in range(rails):
        for x in range(length):
            if fence[rail][x] != "#":
                cipher += fence[rail][x]
    return cipher


def decryptFence(cipher, rails, offset=0):
    """
    Stolen from https://github.com/tothi/railfence.

    This is a convenience function to decrypt data with the Railfence
    cipher.

    :param cipher: The ciphertext as a string.

    :param rails: The integer number of rails to use in the Railfence cipher \
    operations.

    :param offset: The integer offset number to use in the Railfence cipher \
    operations.

    """
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

    GROUPS = ["crypto", "railfence"]
    """
    These are "tags" for a unit. Considering it is a Crypto unit, "crypto"
    is included, and the name of the unit, "railfence".
    """

    BLOCKED_GROUPS = ["crypto"]
    """
    These are tags for groups to not recurse into. Recursing into other crypto units
    would be silly.
    """

    PRIORITY = 60
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a slightly
    lower priority.
    """

    RECURSE_SELF = False
    """
    This unit does not recurse into itself. That would be silly.
    """

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        # Grab the supplied arguments
        self.rails = self.geti("rails")
        self.offset = self.geti("offset")

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
        Evaluate the target. This simply attemptes to decrypt the \
        target with the Railfence cipher, using the ``rails`` and \
        ``offset`` values returned by `enumerate``. 
        
        :param case: A case returned by ``enumerate``. In this case, \
        it is a tuple containing a rail value and offset value \
        to be used for the Railfence cipher operations.
        
        :return: None
        """

        result = decryptFence(self.target.raw, case[0], case[1])
        self.manager.register_data(self, result)
