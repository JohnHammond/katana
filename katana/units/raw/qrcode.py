import warnings

from katana.units import NotApplicable

warnings.simplefilter("ignore", UserWarning)
from PIL import Image
from pyzbar import pyzbar
from katana import units


class Unit(units.FileUnit):
    PRIORITY = 25

    def __init__(self, katana, target):
        super(Unit, self).__init__(katana, target, keywords='image')

        try:
            self.image = Image.open(self.target.path)
        except OSError:
            raise NotApplicable("not an image")

    def evaluate(self, katana, case):

        decoded = pyzbar.decode(self.image)
        for each_decoded_item in decoded:
            decoded_data = each_decoded_item.data.decode('latin-1')

            result = {
                'type': each_decoded_item.type,
                'data': decoded_data
            }

            katana.recurse(self, decoded_data)
            katana.add_results(self, result)
