"""
Decode Base32 encoded text

This is done by the Python3 ``base64`` module which has the
``b32decode`` function.

"""
from typing import Any
import binascii
import base64
import magic
import regex as re

from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable
from katana.util import is_good_magic
import katana.util

BASE32_PATTERN = rb"[A-Z2-7+/]+={0,6}"
BASE32_REGEX = re.compile(BASE32_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)


class Unit(BaseUnit):

    GROUPS = ["raw", "decode", "base32"]
    """
    These are "tags" for a unit. Considering it is a Raw unit, "raw"
    is included, as well as the tag "decode", and the unit name "base32".
    """

    PRIORITY = 60
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a low
    priority.
    """

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        # Ensure this is printable data
        if not self.target.is_printable:
            raise NotApplicable("not printable data")

        # Ensure this is not english data
        if self.target.is_english:
            raise NotApplicable("seemingly english")

        # if this was a file, ensure it's not an image or anything useful
        if self.target.path:
            if is_good_magic(magic.from_file(self.target.path)):
                raise NotApplicable("potentially useful file")

        # Are there base32 chunks in the data?
        self.matches = BASE32_REGEX.findall(self.target.raw)
        if self.matches is None:
            raise NotApplicable("no base32 text found")

    def evaluate(self, case):
        """
        Evaluate the target. Run ``base64.b32ecode`` on the target and
        recurse on any new found information.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        # Iterate over all matched chunks
        for match in self.matches:
            try:
                if len(match) < 16:
                    continue
                # Attempt decode
                result = base64.b32decode(match)
                self.register_result(result)
            except (UnicodeDecodeError, binascii.Error, ValueError):
                # This won't decode right... must not be right! Ignore it.
                # `pass` because there might be more than one string to decode
                pass
