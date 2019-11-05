#!/usr/bin/env python3
from typing import Any
from pyzbar import pyzbar
from PIL import Image
import warnings

from katana.unit import NotApplicable, FileUnit
from katana.manager import Manager
from katana.target import Target

warnings.simplefilter("ignore", UserWarning)


class Unit(FileUnit):

    # Moderate priority
    PRIORITY = 25

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target, keywords="image")

        try:
            # Attempt to open the image with PIL
            self.image = Image.open(self.target.path)
        except OSError:
            raise NotApplicable("not an image")

    def evaluate(self, case: Any):

        # Use pyzbar to decode he qrcode
        decoded = pyzbar.decode(self.image)
        for each_decoded_item in decoded:
            decoded_data = each_decoded_item.data

            # CALEB: Need better data registration...
            result = {"type": each_decoded_item.type, "data": decoded_data}

            self.manager.register_data(self, decoded_data)
