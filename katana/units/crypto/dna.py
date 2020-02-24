"""

DNA/Codon Cipher.

This unit will translate groupings of letters (A,T,C,G,U) into 
22 out of 26 possible English characters.

This unit inherits from the 
:class:`katana.unit.NotEnglishAndPrintableUnit` class, as we can expect
the data to still be printable characters (letters, numbers and punctuation)
but not readable English. It also inherits from the 
:class:`katana.units.crypto.CryptoUnit` class to ensure it is not a viable
URL or potentially useful file.

"""

from typing import Any
import string

from katana.unit import NotEnglishAndPrintableUnit, NotApplicable
from katana.units.crypto import CryptoUnit


class Unit(NotEnglishAndPrintableUnit, CryptoUnit):

    GROUPS = ["crypto", "dna"]
    """
    These are "tags" for a unit. Considering it is a Crypto unit, "crypto"
    is included, as well as the name of the unit, "dna". 
    """

    BLOCKED_GROUPS = ["crypto"]
    """
    This unit does not recurse into other Crypto units because that might
    spiral into a disaster.
    """

    PRIORITY = 50
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. 
    """

    RECURSE_SELF = False
    """
    This unit should not recurse into itself. That could spiral in to an 
    infinite loop.
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor verifies that that only DNA letters (A, T, C, G) 
        are found in the target.
        """

        super(Unit, self).__init__(*args, **kwargs)

        self.raw_target = self.target.stream.read().decode("utf-8").upper()
        self.raw_target = self.raw_target.replace(" ", "").replace("U", "T").strip()

        if (
            not all(c in "ACGT" for c in self.raw_target)
            or len(self.raw_target) % 3 != 0
        ):

            raise NotApplicable("more than DNA letters (A, T, C, G) found")

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        
        Read individual Codon groupings and replace them
        with the corresponding English character.

        :param case: A case returned by ``enumerate``. In this case, the \
        ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        # Try the first technique....
        all_characters: str = string.ascii_lowercase + string.ascii_uppercase + string.digits[
            1:10
        ] + "0 ."
        result: list = []

        for codon in [
            self.raw_target[i : i + 3] for i in range(0, len(self.raw_target), 3)
        ]:
            index = 0
            index += (
                0
                if codon[2] == "A"
                else (1 if codon[2] == "C" else (2 if codon[2] == "G" else 3))
            )
            index += (
                0
                if codon[1] == "A"
                else (4 if codon[1] == "C" else (8 if codon[1] == "G" else 12))
            )
            index += (
                0
                if codon[0] == "A"
                else (16 if codon[0] == "C" else (32 if codon[0] == "G" else 48))
            )
            result.append(all_characters[index])

        # Compile the new string, add and recurse
        result: str = "".join(result)
        self.manager.register_data(self, result)
