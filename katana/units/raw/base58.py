"""
Decode Base58 encoded text

This is done by the Python3 ``base58`` module which has the
``b58decode`` function.

"""
import binascii
import base58
import magic
import regex as re

from katana.unit import RegexUnit
from katana.unit import NotApplicable
from katana.util import is_good_magic
import katana.util


class Unit(RegexUnit):

    PRIORITY = 60
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a low
    priority.
    """

    GROUPS = ["raw", "decode", "base58"]
    """
    These are "tags" for a unit. Considering it is a Raw unit, "raw"
    is included, as well as the tag "decode", and the unit name "base58".
    """

    # What are we looking for?
    PATTERN = re.compile(rb"[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]+", re.MULTILINE | re.DOTALL)

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        # if this was a file, ensure it's not an image or anything useful
        if self.target.path:
            if is_good_magic(magic.from_file(self.target.path)):
                raise NotApplicable("potentially useful file")

    def evaluate(self, match):
        """
        Evaluate the target. Run ``base58.b58decode`` on the target and
        recurse on any new found information.

        :param match: A match returned by the ``RegexUnit``.

        :return: None. This function should not return any data.
        """

        try:
            # Decode chunk
            result = base58.b58decode(match.group())
            self.register_result(result)

        except (UnicodeDecodeError, binascii.Error, ValueError):
            # This won't decode right... must not be right! Ignore it.
            # I pass here because there might be more than one string to decode
            pass

        # Base58 can also include error checking... so try to "check" as well!
        try:
            result = base58.b58decode_check(match.group())
            self.register_result(result)

        except (UnicodeDecodeError, binascii.Error, ValueError):
            # This won't decode right... must not be right! Ignore it.
            # I pass here because there might be more than one string to decode
            pass
