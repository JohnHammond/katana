"""
XOR decoder

You can supply a ``key`` argument to use for the XOR operation.
With the current implementation, if the key is not provided, this unit will
attempt to bruteforce the XOR with a single-byte range (1-255).

"""

import io
from typing import Any

import binascii

from katana.unit import Unit as BaseUnit
from katana.units.crypto import CryptoUnit


def xor(data, key):
    """
    Perform an XOR operation across the provided data with a given key.

    :param data: A byte string to use as the data for the XOR operation.

    :param key: The key to use the for the XOR operation.

    :return: The result of the XOR operation as a byte string.
    """

    # Handle a single byte key gracefully
    if type(key) is int:
        key = bytes([key])
    elif type(key) is str:
        key = key.encode("utf-8")

    result = []

    # XOR with repeating key
    for i, b in enumerate(data):
        if type(b) is bytes:
            b = b[0]
        result.append(b ^ key[i % len(key)])

    # Return bytes result
    return bytes(result)


class Unit(CryptoUnit):

    GROUPS = ["crypto", "xor"]
    """
    These are "tags" for a unit. Considering it is a Crypto unit, "crypto"
    is included, and the name of the unit itself, "xor".
    """

    BLOCKED_GROUPS = ["crypto"]
    """
    These are tags for groups to not recurse into. Recursing into other crypto units
    would be silly.
    """

    PRIORITY = 70
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a lower
    priority.
    """

    RECURSE_SELF = False
    """
    Do not recurse into self.
    """

    VERY_SPECIAL_KEYS = [
        bytes( [i*i % 256 for i in range(128)] ), # i^2
        bytes( [i % 256 for i in range(256)] ), # i
        bytes( [2*i % 256 for i in range(128)] ), # 2i
    ]

    # Inheriting from a CryptoUnit will ensure this will not run on URLs
    # or files that could be anything useful (image, document, audio, etc.)

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target. Perform the XOR operation with the provided
        ``key`` argument. If no key is provided, it will bruteforce a
        single-byte XOR within the range of 1-255.

        :param case: A case returned by ``enumerate``. For this unit, \
        the ``enumerate`` function is not used.


        :return: None. This function should not return any data.
        """

        # Get the value passed
        xor_key = self.get("key")

        if xor_key:
            # if a value was actually passed, use it in a loop
            xor_key = [xor_key]
        else:
            # if a value is not supplied, bruteforce in the single-byte range
            xor_key = list(range(1, 255))
            xor_key.extend(self.VERY_SPECIAL_KEYS)

        for each_key in xor_key:
            try:
                result = xor(self.target.raw, each_key).decode("latin-1")

                if result.isprintable():
                    self.manager.register_data(self, result)

            except (UnicodeDecodeError, binascii.Error):
                # if we cannot decode it, stop trying!
                pass
