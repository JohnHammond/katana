import binascii

import magic
from katana import utilities
from katana.unit import BaseUnit
from katana.units import NotApplicable
from pwn import *

DECIMAL_PATTERN = rb'[0-9]{1,3}'
DECIMAL_REGEX = re.compile(DECIMAL_PATTERN, flags=re.MULTILINE | \
                                                  re.DOTALL | re.IGNORECASE)


class Unit(BaseUnit):
    PRIORITY = 25

    def __init__(self, katana, target):
        super(Unit, self).__init__(katana, target)

        # We don't need to operate on files
        if not self.target.is_printable or self.target.is_file or self.target.is_english:
            raise NotApplicable("is a file")

        self.matches = DECIMAL_REGEX.findall(self.target.raw)

        if self.matches is None:
            raise NotApplicable("no decimal values found")

        for decimal in self.matches:
            if int(decimal) not in range(255):
                raise NotApplicable("decimal value larger than 255 was found")

    def evaluate(self, katana, case):

        try:
            result = ''.join(chr(int(d)) for d in self.matches)
        # If this fails, it's probably not decimal we can deal with...
        except (UnicodeDecodeError, binascii.Error):
            return None

        # JOHN: The question of whether or not we should only handle
        #       printables came up when we worked on XOR...
        #       ... but we left it raw, because what if it uncovers a file?
        # if new_result.replace('\n', '').isprintable():
        if utilities.isprintable(result):
            katana.recurse(self, result)
            katana.add_results(self, result)

        # if it's not printable, we might only want it if it is a file...
        else:
            magic_info = magic.from_buffer(result)
            if utilities.is_good_magic(magic_info):
                katana.add_results(self, result)

                filename, handle = katana.create_artifact(self, "decoded", mode='wb', create=True)
                handle.write(bytes(result, 'utf-8'))
                handle.close()
                katana.recurse(self, filename)
