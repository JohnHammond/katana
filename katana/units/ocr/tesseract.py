#!/usr/bin/env python3
from typing import Generator, Any

from katana.manager import Manager
from katana.target import Target
from katana.unit import FileUnit
from katana.unit import NotApplicable

import pytesseract
from PIL import Image


def attempt_ocr(image_path):
    """ Run tesseract against an image file and return the string found"""
    try:
        ocr_data = pytesseract.image_to_string(Image.open(image_path))

    # This function is meant to ran as a standalone, so catch this exception
    # in case we aren't doing any dependency checking
    except pytesseract.pytesseract.TesseractNotFoundError:
        ocr_data = None

    return ocr_data


class Unit(FileUnit):
    # Fill in your groups
    GROUPS = ["unknown"]
    # Set higher priority because this is lightweight
    PRIORITY = 25
    # Do not recurse into new things
    RECURSE_SELF = False

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target, keywords=["image"])

    def enumerate(self) -> Generator[Any, None, None]:
        """
        Yield unit cases
        :return: Generator of target cases
        """

        yield None

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """

        ocr_data = attempt_ocr(self.target.path)

        if ocr_data:
            self.manager.register_data(self, ocr_data)

    @classmethod
    def validate(cls, manager: Manager) -> None:
        """
        Stub to validate configuration parameters
        :param manager: Katana manager
        :return: None
        """
        super(Unit, cls).validate(manager)
