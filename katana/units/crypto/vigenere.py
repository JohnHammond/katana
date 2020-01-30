"""
ROT47 decoder

The gist of this code is ripped from 
https://rot47.net/_py/rot47.txt. The unit takes the target, and
if it does not look English text but it is clearly printable characters, it
attempts to rot47 the data. 

"""

import io
from typing import Any
import string

from katana.unit import NotEnglishAndPrintableUnit, NotApplicable


def vigenere(plaintext, key):
    plaintext = plaintext.upper()
    key = bytes(key.upper(), "ascii")

    valid_chars = bytes(string.ascii_uppercase, "ascii")

    idx = 0
    ciphertext = ""

    for c in bytes(plaintext, "ascii"):
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


class Unit(NotEnglishAndPrintableUnit):

    # Fill in your groups
    GROUPS = ["crypto"]
    BLOCKED_GROUPS = ["crypto"]
    # Default priority is 50
    PRIORITY = 60
    # Do not recurse into self
    RECURSE_SELF = False

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        self.vignere_key = self.get("key")
        if not self.vignere_key:
            return NotApplicable("empty vigenere key passed")

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by enumerate
        :return: None
        """

        result = vigenere(self.target.stream.read().decode("utf-8"), self.vignere_key)
        self.manager.register_data(self, result)
