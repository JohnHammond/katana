"""
Perform the classic Atbash cipher on the given target.

You can read more about the Atbash cipher here:
https://en.wikipedia.org/wiki/Atbash

This unit inherits from the 
:class:`katana.unit.NotEnglishAndPrintableUnit` class, as we can expect
the data to still be printable characters (letters, numbers and punctuation)
but not readable English. It also inherits from the 
:class:`katana.units.crypto.CryptoUnit` class to ensure it is not a viable
URL or potentially useful file.


The gist of the Atbash cipher is that it will perform a substitution cipher
with the key being the typical English alphabet, just reversed. Basically,
A-Z maps to Z-A.

"""
import io
import string
from typing import Any

from katana.unit import NotEnglishAndPrintableUnit
from katana.units.crypto import CryptoUnit


class Unit(NotEnglishAndPrintableUnit, CryptoUnit):

    GROUPS: list = ["crypto", "atbash"]
    """
    These are "tags" for a unit. Considering it is a Crypto unit, "crypto"
    is included, as well as the name of the unit, "atbash". 
    """

    BLOCKED_GROUPS: list = ["crypto"]
    """
    This unit does not recurse into other Crypto units because that might
    spiral into a disaster.
    """

    PRIORITY: int = 60
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a somewhat
    lower priority due to how uncommon this is within CTFs.
    """

    RECURSE_SELF: bool = False
    """
    This unit should not recurse into itself. That could spiral in to an 
    infinite loop.
    """

    def evaluate(self, case: Any) -> None:
        """
        This ``evaluate`` function performs the Atbash cipher on the target.
        
        :param case: A case returned by ``enumerate``. For this unit, 
         the enumerate function is not used.
         
        :return: None. This function should not return any data.
        """

        # Create a list to store the new information in.
        new_string: list = []

        # Reverse the alphabet, to be used as the mapping key
        reverse_upper: str = string.ascii_uppercase[::-1]
        reverse_lower: str = string.ascii_lowercase[::-1]

        # Perform the actual mapping translation/atbash cipher
        with io.TextIOWrapper(self.target.stream, encoding="utf-8") as stream:
            try:
                for ch in iter(lambda: stream.read(1), ""):
                    if ch in string.ascii_uppercase:
                        new_string.append(
                            reverse_upper[string.ascii_uppercase.index(ch)]
                        )
                    elif ch in string.ascii_lowercase:
                        new_string.append(
                            reverse_lower[string.ascii_lowercase.index(ch)]
                        )
                    else:
                        new_string.append(ch)
            except UnicodeDecodeError:
                pass

        # Join together the final result as a complete string
        result: str = "".join(new_string)

        # Register the data!
        self.register_result(bytes(result, 'utf-8'))
