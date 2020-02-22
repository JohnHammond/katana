"""
Crypto units are often applicable to lots of targets, and considering they
can do some brute-force operations, they often take up a lot of processing
and can waste time for Katana's operations.

For this reason, we implemented a commonly used 
:class:`katana.units.crypto.CryptoUnit` that checks to ensure the target
is not a viable URL (to not clobber web units) and it is not a potentially
useful file (like an image, document, or something else specific).

"""

from katana.unit import NotApplicable
from katana.unit import Unit as BaseUnit
from katana.util import is_good_magic
import magic


class CryptoUnit(BaseUnit):
    """
    This Unit will raise :class:`katana.unit.NotApplicable` if the
    unit is a URL or a potentially useful file.
    """

    def __init__(self, *args, **kwargs):

        super(CryptoUnit, self).__init__(*args, **kwargs)

        # if this is a URL, and we can reach it, don't try to mangle anything
        if self.target.is_url and not self.target.url_accessible:
            raise NotApplicable("this is a URL")

        # if this is a given file, ensure it's not an image or anything useful
        if self.target.path:
            if is_good_magic(magic.from_file(self.target.path)):
                raise NotApplicable("potentially useful file")
