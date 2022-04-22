"""
Perform a Caesar cipher, with the key mapping in the range of all 255 ASCII
 characters, on the target.

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

from katana.unit import NotEnglishAndPrintableUnit
from katana.unit import NotApplicable
from katana.units.crypto import CryptoUnit
from katana import util


class Unit(NotEnglishAndPrintableUnit, CryptoUnit):

    GROUPS = ["crypto", "caesar255"]
    """
    These are "tags" for a unit. Considering it is a Crypto unit, "crypto"
    is included, as well as the name of the unit, "caesar255". 
    """

    BLOCKED_GROUPS = ["crypto"]
    """
    This unit does not recurse into other Crypto units because that might
    spiral into a disaster.
    """

    PRIORITY = 80
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. 
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
        values within in the ASCII range (i.e. try the numbers 1-255).

        :return: Generator of target cases, in this case an integer \
        for the shift value (provided, or range 1-255).

        """

        if self.geti("shift", None) is None:
            for shift in range(1, 255):
                yield shift
        else:
            yield self.geti("shift")

    def evaluate(self, shift: int) -> None:
        """
        Perform the caesar cipher on the target.

        :param case: A case returned by ``enumerate``, in this case, the \
        shift value to use for the Caesar Cipher operation.

        :return: None. This function should not return any data.

        """

        # Create a variable to store the new data
        result: list = []

        # Perform the caesar cipher operation, character by character
        for c in self.target.raw:
            if type(c) is int:
                result.append((c + shift) % 255)
            elif type(c) is bytes:
                result.append((ord(c) + shift) % 255)

        # Register the data
        if util.is_interesting:
            self.manager.register_data(self, bytes(result))
