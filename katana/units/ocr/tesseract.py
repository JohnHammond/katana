import traceback

import pytesseract
from PIL import Image
from katana import units
from katana.units import NotApplicable

DEPENDENCIES = ['tesseract']


def attempt_ocr(image_path):
    try:
        ocr_data = pytesseract.image_to_string(Image.open(image_path))

    # This is function is meant to run as a standalone, so catch this exception
    # in case we aren't doing dependency checking...
    except pytesseract.pytesseract.TesseractNotFoundError:
        ocr_data = None

    # JOHN: I don't know when this will go wrong, but when it does....
    # except pytesseract.pytesseract.TesseractError:

    except:
        traceback.print_exc()
        ocr_data = None

    return ocr_data


class Unit(units.FileUnit):
    # JOHN: This MUST be in the class...
    PROTECTED_RECURSE = True
    PRIORITY = 25

    def __init__(self, katana, target):
        super(Unit, self).__init__(katana, target)

        self.completed = True
        if not 'image' in self.target.magic:
            raise NotApplicable("not an image")

    def evaluate(self, katana, case):

        ocr_data = attempt_ocr(self.target.path)

        if ocr_data:
            # We don't locate flags any more because recurse does this for us.
            katana.recurse(self, ocr_data)
            katana.add_results(self, ocr_data)

        return
