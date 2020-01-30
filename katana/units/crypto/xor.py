"""
XOR decoder

This unit takes one argument "key" that can be used 

"""

import io
from typing import Any

import binascii

from katana.unit import Unit as BaseUnit


def xor(thing, key):

    # Handle a single byte key gracefully
    if type(key) is int:
        key = bytes([key])
    elif type(key) is str:
        key = key.encode("utf-8")

    result = []

    # XOR with repeating key
    for i, b in enumerate(thing):
        if type(b) is bytes:
            b = b[0]
        result.append(b ^ key[i % len(key)])

    # Return bytes result
    return bytes(result)


class Unit(BaseUnit):

    # Fill in your groups
    GROUPS = ["crypto"]
    BLOCKED_GROUPS = ["crypto"]
    # Default priority is 50
    PRIORITY = 70
    # Do not recurse into self
    RECURSE_SELF = False

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """

        # Get the value passed
        xor_key = self.get("key")

        if xor_key:
            # if a value was actually passed, use it in a loop
            xor_key = [xor_key]
        else:
            # if a value is not supplied, bruteforce in the single-byte range
            xor_key = range(255)

        for each_key in xor_key:
            try:
                result = xor(self.target.raw, each_key).decode("latin-1")

                if result.isprintable():
                    self.manager.register_data(self, result)

            except (UnicodeDecodeError, binascii.Error):
                # if we cannot decode it, stop trying!
                pass
