"""
Attempt to decrypt a Vigenere cipher.

You can supply a ``key`` argument to use for the Vigenere cipher operation.
With the current implementation, if the key is not provided, this unit does
not run (it does not attempt to bruteforce it or determine a key on its own).

This unit inherits from the 
:class:`katana.unit.NotEnglishAndPrintableUnit` class, as we can expect
the data to still be printable characters (letters, numbers and punctuation)
but not readable English. It also inherits from the 
:class:`katana.units.crypto.CryptoUnit` class to ensure it is not a viable
URL or potentially useful file.

"""

import io
from typing import Any
import string

from katana.unit import NotEnglishAndPrintableUnit, NotApplicable
from katana.units.crypto import CryptoUnit


def vigenere(plaintext, key):
    """
    Perform a vigenere cipher.

    :param plaintext: The plaintext message to use for the Vigenere cipher.

    :param key: The key to use for the Vigenere cipher.

    :return: The resulting ciphertext from the Vignere cipher operation
    """
    plaintext = plaintext.upper()
    key = bytes(key.upper(), "ascii")

    valid_chars = bytes(string.ascii_uppercase, "ascii")

    idx = 0
    ciphertext = ""

    for c in plaintext:
        if c not in valid_chars:
            ciphertext += chr(c)
        else:
            if key[idx] not in valid_chars:
                idx = (idx + 1) % len(key)
            # v1 = ord(c) - ord('A')
            # v2 = ord(key[idx]) - ord('A')
            v1 = c - ord("A")
            v2 = key[idx] - ord("A")
            ciphertext += chr(((v1 - v2) % 26) + ord("A"))
            idx = (idx + 1) % len(key)

    return ciphertext


class Unit(NotEnglishAndPrintableUnit, CryptoUnit):

    GROUPS = ["crypto", "vigenere"]
    """
    These are "tags" for a unit. Considering it is a Crypto unit, "crypto"
    is included, and the name of the unit, "vigenere".
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
    Do not recurse into self.
    """

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        self.vignere_key = self.get("key")
        if not self.vignere_key:
            raise NotApplicable("empty vigenere key passed")

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.

        :param case: A case returned by ``enumerate``. For this unit, \
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        result = vigenere(self.target.raw, self.vignere_key)
        self.manager.register_data(self, result)
