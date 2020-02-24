"""
Scan QR codes

This unit works with the ``pyzbar`` module in Python, which is necessary for
it to run.

This unit inherits from the :class:`katana.unit.FileUnit` to ensure
that the target is in fact an image file.
"""

from typing import Any
from pyzbar import pyzbar
from PIL import Image
import warnings

from katana.unit import NotApplicable, FileUnit
from katana.manager import Manager
from katana.target import Target

warnings.simplefilter("ignore", UserWarning)


class Unit(FileUnit):

    PRIORITY = 25
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a moderate
    priority.
    """

    GROUPS = ["raw", "decode", "qrcode", "scan"]
    """
    These are "tags" for a unit. Considering it is a Raw unit, "raw"
    is included, as well as the tag "decode", "scan", and the unit name 
    "qrcode".
    """

    def __init__(self, manager: Manager, target: Target):
        """
        The constructor is included just to provide a keyword for the
        ``FileUnit``, ensuring the provided target is in fact an image. This
        also validates it can open the file with PIL without an issue.
        """

        super(Unit, self).__init__(manager, target, keywords="image")

        try:
            # Attempt to open the image with PIL
            self.image = Image.open(self.target.path)
        except OSError:
            raise NotApplicable("not an image")

    def evaluate(self, case: Any):
        """
        Evaluate the target. Scan the target with ``pyzbar`` and
        recurse on any new found information.

        :param match: A match returned by the ``RegexUnit``.

        :return: None. This function should not return any data.
        """

        # Use pyzbar to decode he qrcode
        decoded = pyzbar.decode(self.image)
        for each_decoded_item in decoded:
            decoded_data = each_decoded_item.data

            result = {"type": each_decoded_item.type, "data": decoded_data}
            self.manager.register_data(self, decoded_data)
