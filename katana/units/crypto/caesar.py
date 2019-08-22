"""

Classic Caesar Cipher shift, within the typical English alphabet (modulus 26).

By default, this unit will bruteforce all 26 possible shifts of the 
target and recurse on each result. If you need to shift by just one certain
amount, you can include the variable ``caesar_shift`` with an integer value.

.. code-block:: bash

	./katana.py --unit crypto.caesar "Gur synt vf: PnrfneFnirfGurQnl"

"""

import io
import string

from katana import units
from katana.units import NotApplicable


class Unit(units.NotEnglishUnit):
    """
    This unit inherits from the :class:`katana.units.NotEnglishUnit` class, as
    we will likely only test for caesar cipher permutations on data that is
    printable but does not look English plaintext already.

    :data:`PROTECTED_RECURSE` is ``True`` for this unit, because we do not
    want results that come from this unit being processed *yet again* by this
    unit. That would make for pointless computation and potentially an
    infinite loop.

    :data:`PRIORITY` is set to 60, as this has potential to be a long and
    time-consuming operation.
    """

    PROTECTED_RECURSE: bool = True
    PRIORITY: int = 60
    ARGUMENTS: dict = [
        {'name': 'caesar_shift',
         'type': int,
         'default': -1,
         'required': False,
         'help': 'number to shift by for caesar cipher'
         },
    ]

    def __init__(self, katana, target):
        super(Unit, self).__init__(katana, target)

        if target.is_url: raise NotApplicable('target is a URL')

        # DO NOT run this if the string does not contain any letters.
        try:
            with io.TextIOWrapper(self.target.stream, encoding='utf-8') as stream:
                for c in iter(lambda: stream.read(1), ''):
                    if c in string.ascii_letters:
                        return  # We found at least one letter -- we can run!

        except UnicodeDecodeError:
            raise NotApplicable("seemingly binary data")

        # We should only reach this if we did not return from that loop above.
        raise NotApplicable("no english letters")

    def enumerate(self, katana):
        """
        If no ``caesar_shift`` argument is supplied, enumerate all 26 shift
        values.
        """

        if katana.config['caesar_shift'] == -1:
            for shift in range(1, len(string.ascii_lowercase)):
                yield shift
        else:
            yield katana.config['caesar_shift']

    def evaluate(self, katana, case):
        """
        Read and iterate through the target, performing the caesar cipher at
        each viable character within the English alphabet.
        """

        result: list = []

        # Read one character at a time, shift them appropriately, and store
        # in the new result list.
        with io.TextIOWrapper(self.target.stream, encoding='utf-8') as stream:
            for c in iter(lambda: stream.read(1), ''):
                idx = string.ascii_uppercase.find(c)
                if idx != -1:
                    result.append(string.ascii_uppercase[(idx + case) % \
                                                         len(string.ascii_uppercase)])
                else:
                    idx = string.ascii_lowercase.find(c)
                    if idx != -1:
                        result.append(string.ascii_lowercase[(idx + case) % \
                                                             len(string.ascii_lowercase)])
                    else:
                        result.append(c)

        # Build a new string out of the results, and pass it through to Katana
        result: str = ''.join(result)
        katana.recurse(self, result)
        katana.add_results(self, result)
