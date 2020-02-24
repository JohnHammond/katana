"""
Decode URL-encoded/percent-ecoded data.

This unit will return the data represented in both little-endian notation
and in big-endian notation.

This unit inherits from :class:`katana.unit.PrintableDataUnit` as the targets
for this should include data that is often part of a URL.
"""

from typing import Any
import urllib.request
import binascii
import magic

from katana.unit import NotApplicable, PrintableDataUnit
from katana.manager import Manager
from katana.target import Target
import katana.util
import regex as re

URL_DATA = re.compile(rb"%[0-9A-Fa-f]{1,2}", re.IGNORECASE | re.MULTILINE | re.DOTALL)
"""
The pattern to match for URL encoded data.
"""


class Unit(PrintableDataUnit):

    PRIORITY = 25
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a higher
    priority.
    """

    GROUPS = ["raw", "decode", "urldecode"]
    """
    These are "tags" for a unit. Considering it is a Raw unit, "raw"
    is included, as well as the tag "decode", and the name of the unit itself,
    "urldecode".
    """

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        if URL_DATA.search(target.raw) is None:
            raise NotApplicable("No URL encoded parts")

    def evaluate(self, case):
        """
        Evaluate the target. URL decode the  
        target and recurse on any new found information.

        :param match: A match returned by the ``RegexUnit``.

        :return: None. This function should not return any data.
        """

        try:
            # Attempt to urldecode the data
            new_result = urllib.request.unquote(self.target.upstream.decode("utf-8"))
        except (UnicodeDecodeError, binascii.Error):
            # If this fails, it's probably not something we can deal with...
            return

        # We only want to work with this if it something new.
        if new_result.encode("utf-8") != self.target.raw:
            self.manager.register_data(self, new_result)
