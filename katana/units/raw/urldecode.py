import binascii
import urllib.request

from katana import units


class Unit(units.PrintableDataUnit):
    PRIORITY = 25

    def evaluate(self, katana, case):

        try:
            new_result = urllib.request.unquote(self.target.upstream.decode('utf-8'))

        # If this fails, it's probably not something we can deal with...
        except (UnicodeDecodeError, binascii.Error):
            print("we failed lol")
            return None

        # We only want to work with this if it something new.
        if new_result.encode('utf-8') != self.target.raw:
            katana.recurse(self, new_result)
            katana.locate_flags(self, new_result)
            katana.add_results(self, new_result)
