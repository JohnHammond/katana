"""
Perform a Keyed Caesar cipher on the target.

You can read moer about the Caesar cipher here:
http://rumkin.com/tools/cipher/caesar-keyed.php

This unit inherits from the 
:class:`katana.unit.NotEnglishAndPrintableUnit` class, as we can expect
the data to still be printable characters (letters, numbers and punctuation)
but not readable English. It also inherits from the 
:class:`katana.units.crypto.CryptoUnit` class to ensure it is not a viable
URL or potentially useful file.

"""

from typing import Generator, Any
import string
import io

from katana.manager import Manager
from katana.target import Target
from katana.unit import NotApplicable, NotEnglishAndPrintableUnit
from katana.units.crypto import CryptoUnit


def shift_char(c: str, shift: int, alphabet: str) -> str:
    """
    This is a convenience function that will perform the most primitive
    operation of the Caesar Cipher -- shifting one character by a given
    amount within the given alphabet.
    """
    idx = alphabet.find(c)
    if idx == -1:
        return None
    return alphabet[(idx + shift) % len(alphabet)]


class Unit(NotEnglishAndPrintableUnit, CryptoUnit):

    GROUPS = ["crypto", "caesar"]
    """
    These are "tags" for a unit. Considering it is a Crypto unit, "crypto"
    is included, as well as the name of the unit, "caesar". 
    """

    BLOCKED_GROUPS = ["crypto"]
    """
    This unit does not recurse into other Crypto units because that might
    spiral into a disaster.
    """

    PRIORITY = 40
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a somewhat 
    higher priority due to how common this is within CTFs.
    """

    RECURSE_SELF = False
    """
    This unit should not recurse into itself. That could spiral in to an 
    infinite loop.
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor collects the supplied key and creates the 
        appropriate alphabets.
        """

        super(Unit, self).__init__(*args, **kwargs)

        # First, ensure a key has been supplied to the unit.
        self.key = self.get("key", default=None)
        if self.key is None:
            raise NotApplicable("no key is supplied to run keyed caesar")

        # Now begin to prepare the alphabets.
        self.lower_alphabet = string.ascii_lowercase
        self.upper_alphabet = string.ascii_uppercase

        # Remove the seen letters in the alphabets
        for letter in self.key[::-1]:
            # Do this for the lower-case rendition of the key and alphabet
            if letter.lower() in self.lower_alphabet:
                self.lower_alphabet = self.lower_alphabet.replace(letter.lower(), "")
                self.lower_alphabet = letter.lower() + self.lower_alphabet

            # Also for the upper-case rendition of the key and alphabet
            if letter.upper() in self.upper_alphabet:
                self.upper_alphabet = self.upper_alphabet.replace(letter.upper(), "")
                self.upper_alphabet = letter.upper() + self.upper_alphabet

    def enumerate(self) -> Generator[Any, None, None]:
        """
        Yield unit cases. The end-user can either supply a ``shift`` value
        as an argument, or it will bruteforce all the possible shift
        values within in the English alphabet (i.e. try the numbers 1-25).

        :return: Generator of target cases, in this case an integer \
        for the shift value (provided, or range 1-25).

        """

        # We either guess all, or a specific shift depending on config
        if self.geti("shift", None) is None:
            for shift in range(0, len(self.lower_alphabet)):
                yield shift
        else:
            yield self.geti("shift")

    def evaluate(self, case: Any) -> None:
        """
        Perform the keyed caesar cipher on the target.

        :param case: A case returned by ``enumerate``, in this case, the shift \
        value to use for the Caesar Cipher operation.

        :return: None. This function should not return any data.

        """

        # Create a variable to store the new data
        result: list = []

        # Perform the caesar cipher operation, character by character
        with io.TextIOWrapper(self.target.stream, encoding="utf-8") as stream:

            for c in iter(lambda: stream.read(1), ""):

                # Perform the mapping for a keyed caesar
                if c in self.upper_alphabet:
                    c = string.ascii_uppercase[self.upper_alphabet.index(c)]
                if c in self.lower_alphabet:
                    c = string.ascii_lowercase[self.lower_alphabet.index(c)]

                # Now shift as you would a typical caesar cipher
                new_c = shift_char(c, case, self.upper_alphabet)
                if new_c is None:
                    new_c = shift_char(c, case, self.lower_alphabet)
                if new_c is None:
                    new_c = c
                result.append(new_c)

        # Join together the new data
        result: str = "".join(result)

        # Give the data to Katana!
        self.manager.register_data(self, result)
