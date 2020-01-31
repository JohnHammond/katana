"""
These are used throughout the web units, so I have placed 
them here so they are all accessible.
"""

from katana.unit import NotApplicable
from katana.unit import Unit as BaseUnit
from katana.util import is_good_magic
import magic


class CryptoUnit(BaseUnit):
    def __init__(self, *args, **kwargs):

        super(CryptoUnit, self).__init__(*args, **kwargs)

        # if this is a URL, and we can reach it, don't try to mangle anything
        if self.target.is_url and not self.target.url_accessible:
            raise NotApplicable("this is a URL")

        # if this was a given file, make sure it's not an image or anything useful
        if self.target.path:
            if is_good_magic(magic.from_file(self.target.path)):
                raise NotApplicable("potentially useful file")
