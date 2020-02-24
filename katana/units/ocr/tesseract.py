"""
Unit to perform Optical Character Recognition with Tesseract.

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is an image.

This unit uses the Python library for Tesseract, which must be installed
for this to run.
"""

from typing import Generator, Any

from katana.manager import Manager
from katana.target import Target
from katana.unit import FileUnit
from katana.unit import NotApplicable

import pytesseract
from PIL import Image


def attempt_ocr(image_path: str) -> str:
    """
    Run tesseract against an image file and return the string found

    :param image_path: The path to an image file.

    :return: The string determined by Tesseract's OCR efforts.
    """
    try:
        ocr_data = pytesseract.image_to_string(Image.open(image_path))

    # This function is meant to ran as a standalone, so catch this exception
    # in case we aren't doing any dependency checking
    except (pytesseract.pytesseract.TesseractNotFoundError, OSError):
        ocr_data = None

    return ocr_data


class Unit(FileUnit):

    GROUPS = ["ocr", "tesseract"]
    """
    These are "tags" for a unit. Considering it is a Ocr unit, "ocr"
    is included, as well as the unit name "tesseract".
    """

    PRIORITY = 25
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a higher
    priority because this is lightweight.
    """

    RECURSE_SELF = False
    """
    Do not recurse into itself, since it will not provide another image.
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor is included just to provide a keyword for the
        ``FileUnit``, ensuring the provided target is in fact an image.
        """
        super(Unit, self).__init__(*args, **kwargs, keywords=["image"])

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target. Attempt OCR on the target and
        recurse on any newfound data.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        ocr_data = attempt_ocr(self.target.path)

        if ocr_data:
            self.manager.register_data(self, ocr_data)
