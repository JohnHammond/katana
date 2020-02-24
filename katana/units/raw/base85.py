"""
Decode Base85 encoded text

This is done by the Python3 ``base64`` module which has the
``b85decode`` function.

"""
from typing import Any
import binascii
import base64
import magic
import regex as re

from katana.unit import RegexUnit
from katana.unit import NotApplicable
from katana.util import is_good_magic
from katana.manager import Manager
from katana.target import Target
import katana.util


class Unit(RegexUnit):

    PRIORITY = 60
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a low 
    priority, uncommon
    """

    GROUPS = ["raw", "decode", "base85"]
    """
    These are "tags" for a unit. Considering it is a Raw unit, "raw"
    is included, as well as the tag "decode", and the unit name "base85".
    """

    # REGEX matching base58
    PATTERN = re.compile(rb"[\x21-\x75]{4,}", re.DOTALL | re.MULTILINE)

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

        # if this was a file, ensure it's not an image or anything useful
        if self.target.path:
            if is_good_magic(magic.from_file(self.target.path)):
                raise NotApplicable("potentially useful file")

    def evaluate(self, match):
        """
        Evaluate the target. Run ``base64.b85decode`` on the target and
        recurse on any new found information.

        :param match: A match returned by the ``RegexUnit``.

        :return: None. This function should not return any data.
        """

        try:
            # Attempt decode
            result = base64.b85decode(match.group())

            # Keep it if it is printable
            if katana.util.isprintable(result):
                self.manager.register_data(self, result)
            else:
                # if not printable, we might only want it if it is a file.
                magic_info = magic.from_buffer(result)
                if katana.util.is_good_magic(magic_info):
                    # Generate a new artifact
                    filename, handle = self.generate_artifact(
                        "decoded", mode="wb", create=True
                    )
                    handle.write(result)
                    handle.close()
                    # Register the artifact with the manager
                    self.manager.register_artifact(self, filename)
        except (UnicodeDecodeError, binascii.Error, ValueError):
            # This won't decode right... must not be right! Ignore it.
            # I pass here because there might be more than one string to decode
            pass
