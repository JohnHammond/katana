"""
Perform a Caesar cipher on the target.

You can read more about the Caesar cipher here:
https://en.wikipedia.org/wiki/Caesar_cipher

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

    PRIORITY = 70
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
            for shift in range(1, len(string.ascii_lowercase)):
                yield shift
        else:
            yield self.geti("shift")

    def evaluate(self, case: Any) -> None:
        """
        Perform the caesar cipher on the target.

        :param case: A case returned by ``enumerate``, in this case, the shift \
        value to use for the Caesar Cipher operation.

        :return: None. This function should not return any data.

        """

        # Create a variable to store the new data
        result: list = []

        # Perform the caesar cipher operation, character by character
        with io.TextIOWrapper(self.target.stream, encoding="utf-8") as stream:
            for c in iter(lambda: stream.read(1), ""):
                new_c = shift_char(c, case, string.ascii_uppercase)
                if new_c is None:
                    new_c = shift_char(c, case, string.ascii_lowercase)
                if new_c is None:
                    new_c = c
                result.append(new_c)

        # Join together the new data
        result: str = "".join(result)

        # Give the data to Katana!
        self.manager.register_data(self, result)
