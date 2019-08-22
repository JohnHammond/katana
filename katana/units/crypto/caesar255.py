"""
Classic Caesar Cipher shift, within the full ASCII set of characters (modulus 255).

This unit will bruteforce all 255 possible shifts of the 
target and recurse on each result **if it is printable data, or a potential
file.** 
"""

import magic
from katana import units
from katana import utilities


class Unit(units.NotEnglishUnit):
    """
    This unit inherits from the :class:`katana.units.NotEnglishUnit` class, as
    we will likely only test for caesar cipher permutations on data that is
    not already seemingly English text.

    :data:`PROTECTED_RECURSE` is ``True`` for this unit, because we do not
    want results that come from this unit being processed *yet again* by this
    unit. That would make for pointless computation and potentially an
    infinite loop.

    :data:`PRIORITY` is set to 60, as this has potential to be a long and
    time-consuming operation.
    """

    PROTECTED_RECURSE: bool = True
    PRIORITY: int = 60

    def evaluate(self, katana, case):
        """
        Loop through all 255 characters in the ASCII table and shift
        accordingly.
        """

        # These reads as bytes, so we don't need to use ord() later on
        contents: bytes = self.target.stream.read()

        for i in range(256):
            result: list = []
            for c in contents:
                result.append(chr((c + i) % 255))

            result: str = ''.join(result)

            # We want to know about this if it is printable!
            # We use the utilities.isprintable test here, because that
            # DOES include newlines and tabs.
            if utilities.isprintable(result):
                katana.recurse(self, result)
                katana.add_results(self, result)

            # if it's not printable, we might only want it if it is a file...
            else:
                magic_info = magic.from_buffer(result)
                if magic_info != 'data' \
                        and 'UTF-8 Unicode text' not in magic_info \
                        and 'International EBCDIC text' not in magic_info:
                    katana.recurse(self, result)
                    katana.add_results(self, result)
