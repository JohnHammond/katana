"""
Decode Ascii85 encoded text

This is done by the Python3 ``base64`` module which has the
``a85decode`` function.

"""


from typing import Any
import binascii
import base64
import magic

from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable
from katana.manager import Manager
from katana.target import Target
from katana.util import is_good_magic
import katana.util


class Unit(BaseUnit):

    GROUPS = ["raw", "decode", "ascii85"]
    """
    These are "tags" for a unit. Considering it is a Raw unit, "raw"
    is included, as well as the tag "decode", and the unit name "ascii85"
    """

    PRIORITY = 60
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a low
    priority unit, because it is uncommon and highly matching.
    """

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

        # Ensure the target is printable data
        if not self.target.is_printable:
            raise NotApplicable("not printable data")

        # Ensure the target is not english
        if self.target.is_english:
            raise NotApplicable("seemingly english")

        # if this was a given file, make sure it's not an image or anything useful
        if self.target.path:
            if is_good_magic(magic.from_file(self.target.path)):
                raise NotApplicable("potentially useful file")

    def evaluate(self, case: Any):
        """
        Evaluate the target. Run ``base64.a85decode`` on the target and
        recurse on any new found information.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        try:
            # Attempt a85decode of raw data
            result = base64.a85decode(self.target.raw)

            # Check that the result is printable data
            if katana.util.isprintable(result):
                self.manager.register_data(self, result)
            else:
                # if it's not printable, we might only want it if it is a file...
                magic_info = magic.from_buffer(result)
                if katana.util.is_good_magic(magic_info):
                    # Create the artifact and dump the data
                    filename, handle = self.generate_artifact(
                        "decoded", mode="wb", create=True
                    )
                    handle.write(result)
                    handle.close()
                    # Register the artifact with the manager
                    self.manager.register_artifact(self, filename)

        except (UnicodeDecodeError, binascii.Error, ValueError):
            # This won't decode right... must not be right! Ignore it.
            # I return here because we are only trying to decode ONE string
            return
