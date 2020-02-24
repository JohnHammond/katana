"""

Attempt to crack an MD5 hash.

This unit finds potential MD5 hashes matching the defined regular expression:

.. code-block:: python

    MD5_PATTERN = re.compile(rb"[a-fA-F0-9]{32}", re.DOTALL | re.MULTILINE)

This unit cracks the MD5 hash by using a supplied password or dictionary
file. Currently it does not support reaching out to an online cracker,
though this would be ideal.

"""
from typing import Generator, Any
import hashlib
import regex as re

from katana.manager import Manager
from katana.target import Target
from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable

MD5_PATTERN = re.compile(rb"[a-fA-F0-9]{32}", re.DOTALL | re.MULTILINE)


class Unit(BaseUnit):

    # Fill in your groups
    GROUPS: list = ["crack", "bruteforce"]

    # Default priority is 50
    PRIORITY: int = 75

    # Disable all recursion
    NO_RECURSE: bool = True

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        # Find matches in the target
        self.matches: list = MD5_PATTERN.findall(self.target.raw)

        if self.matches is None or len(self.matches) == 0:
            raise NotApplicable("No md5 hashes found")

    def enumerate(self) -> Generator[Any, None, None]:
        """
        Yield unit cases. This will read in the supplied password or
        a given dictionary file to generate new MD5 hashes and test
        them against the supplied MD5 hash target.

        :return: Generator of target cases, in this case a byte string.

        """

        # Manually specified passwords first
        passwords = self.manager.get(str(self), "password", fallback="")
        if passwords != "":
            for p in passwords.split(","):
                yield bytes(p, "utf-8")

        # Dictionary passwords next
        dictionary = self.manager.get(str(self), "dict", fallback=None)
        if dictionary is not None:
            with open(dictionary, "rb") as f:
                for line in f:
                    yield line.rstrip(b"\n")

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target. This will take the current ``case`` supplied by
        the ``enumerate`` function, generate an MD5 hash with it and compare
        it to the supplied target. If it is a match, we have successfully
        cracked the hash and that ``case`` value is registered as new data.


        :param case: A case returned by ``enumerate``

        :return: None. This function should not return any data.
        """

        new_hash: bytes = bytes(hashlib.md5(case).hexdigest(), "utf-8")
        for match in self.matches:
            if new_hash == match:
                self.manager.register_data(
                    self, {match.decode("utf-8"): repr(case)[2:-1]}, recurse=False
                )

                # Now that we have a match, stop this function
                return
