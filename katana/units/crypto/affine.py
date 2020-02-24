"""

Attempt to decrypt a target with the classic Affine cipher.

You can read more about the Affine cipher here:
https://en.wikipedia.org/wiki/Affine_cipher

This unit inherits from the 
:class:`katana.unit.NotEnglishAndPrintableUnit` class, as we can expect
the data to still be printable characters (letters, numbers and punctuation)
but not readable English.

You can supply and customize the given A and B values as well as the
alphabet to be used in the Affine cipher operation, though by default
this will bruteforce and use the range provided with the English alphabet,
letters A-Z.
"""

from typing import Generator, Any
from math import gcd
from string import ascii_uppercase
from Crypto.Util.number import inverse

from katana.unit import NotApplicable, NotEnglishAndPrintableUnit
from katana.units.crypto import CryptoUnit


def affine(c: int, a: int, b: int, alphabet: bytes) -> str:
    """ 
    Perform the affine cipher for a single letter. 

    :c: An integer value for the given letter (its location within the alphabet)

    :a: An integer value for the A value used in the Affine cipher operation.

    :b: An integer value for the B value used in the Affine cipher operation.

    :alphabet: A bytes string for the supplied alphabet.

    """

    if isinstance(c, int):
        c = bytes([c])

    c = c.upper()[0]

    if c in alphabet:
        return alphabet[(a * alphabet.index(c) + b) % len(alphabet)]
    else:
        return c


class Unit(NotEnglishAndPrintableUnit, CryptoUnit):

    GROUPS: list = ["crypto", "affine"]
    """
    These are "tags" for a unit. Considering it is a Crypto unit, "crypto"
    is included, as well as the name of the unit, "affine". 
    """

    BLOCKED_GROUPS: list = ["crypto"]
    """
    This unit does not recurse into other Crypto units because that might
    spiral into a disaster.
    """

    PRIORITY: int = 65
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

    def enumerate(self) -> Generator[Any, None, None]:
        """
        Yield unit cases. This will check if any given ``A`` or ``B`` 
        values are supplied to the unit. If a value is not supplied,
        it will use all numbers up the length of the alphabet
        (which can also be supplied), by default, the English letters
        A-Z. The corresponding value will be the greatest common
        denominator between that in the length, as that is the
        only correspondent value that is mathematically 
        required for the Affine cipher to work.

        :return: Generator of target cases, in this case  a tuple of\
         ``A`` and ``B`` values.

        """

        # Retrive the values supplied from the unit,
        # or inherit the defaults if none are supplied.
        affine_alphabet: str = self.get("alphabet", default=ascii_uppercase)

        affine_a: int = self.geti("a", default=-1)
        affine_b: int = self.geti("b", default=-1)

        # Determine if the values were supplied... if
        # they were not, bruteforce possible values via
        # the supplied alphabet (English A-Z by default)
        if affine_a == -1 and affine_b == -1:
            for a in range(len(affine_alphabet)):
                for b in range(len(affine_alphabet)):
                    if gcd(a, len(affine_alphabet)):
                        yield (a, b)

        elif affine_a != -1 and affine_b == -1:
            for b in range(len(affine_alphabet)):
                if gcd(affine_a, len(affine_alphabet)):
                    yield (affine_a % len(affine_alphabet), b)

        elif affine_b != -1 and affine_a == -1:
            for a in range(len(affine_alphabet)):
                if gcd(a, len(affine_alphabet)):
                    yield (a, affine_b % len(affine_alphabet))
        else:
            if affine_a != -1 and affine_b != -1:
                if gcd(affine_a, len(affine_alphabet)):
                    yield affine_a, affine_b

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target. This will perform
        
        :param case: A case returned by ``enumerate``, in this case a tuple of\
        ``A`` and ``B`` values.
        
        :return: None. This function should not return any data.

        """

        # Extract out the values from the given case
        a, b = case

        alphabet: bytes = bytes(self.get("alphabet", ascii_uppercase), "utf-8")

        # Use an empty list to keep track of the new decrypted string
        result: list = []

        # Perform the affine cipher operation to decrypt
        new_b: int = abs(b - len(alphabet))
        new_a: int = inverse(a, len(alphabet))
        new_b: int = (new_a * new_b) % len(alphabet)

        for letter in self.target.raw:
            # Attempt to inverse the affine cipher
            result.append(affine(letter, new_a, new_b, alphabet))

        # Put it back together
        result: bytes = bytes(result)

        # If we found a result that was not as we saw it before,
        # register it as data and look for flags!
        if result != self.target.raw:
            self.manager.register_data(
                self, {f"{a},{b}": result.decode("utf-8")}, recurse=False
            )
