"""
Decode Base64 encoded text

This is done by the Python3 ``base64`` module which has the
``b64decode`` function.

"""
from typing import Any
import binascii
import base64
import magic
import regex as re

from katana.unit import RegexUnit
from katana.unit import NotApplicable
from katana.manager import Manager
from katana.target import Target
from katana.util import is_good_magic
import katana.util

BASE64_PATTERN = rb"[a-zA-Z0-9+/\n]+={0,2}"
BASE64_REGEX = re.compile(BASE64_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)


class Unit(RegexUnit):

    PRIORITY = 25
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a high
    priority. Base64 is quick and common and matches fairly unilaterally
    """

    GROUPS = ["raw", "decode", "base64"]
    """
    These are "tags" for a unit. Considering it is a Raw unit, "raw"
    is included, as well as the tag "decode", and the unit name "base64".
    """

    # Regular expression pattern
    PATTERN = re.compile(rb"[a-zA-Z0-9+/\n]{4,}={0,2}", re.MULTILINE | re.DOTALL)

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

        # if this was a file, ensure it's not an image or anything useful
        if self.target.path:
            if is_good_magic(magic.from_file(self.target.path)):
                raise NotApplicable("potentially useful file")

    def evaluate(self, match):
        """
        Evaluate the target. Run ``base64.b64decode`` on the target and
        recurse on any new found information.

        :param match: A match returned by the ``RegexUnit``.

        :return: None. This function should not return any data.
        """

        try:
            match = match.group().replace(b"\n",b'')

            if len(match) < 8:
                return
            # Decode chunk
            result = base64.b64decode(match)
            self.register_result(result)

        except (UnicodeDecodeError, binascii.Error, ValueError):
            # This won't decode right... must not be right! Ignore it.
            # I pass here because there might be more than one string to decode
            pass
