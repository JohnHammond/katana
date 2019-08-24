import binascii

import magic
from katana import utilities
from katana.units import BaseUnit
from katana.units import NotApplicable
from pwn import *

BINARY_PATTERN = rb'[01]{8,}'
BINARY_REGEX = re.compile(BINARY_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)


class Unit(BaseUnit):
    PRIORITY = 25

    def __init__(self, katana, target):
        super(Unit, self).__init__(katana, target)

        self.matches = BINARY_REGEX.findall(self.target.raw)

        if self.matches is None:
            raise NotApplicable("no binary data found")

    def evaluate(self, katana, case):

        try:
            raw = ''.join([chr(int(x, 2)) for x in self.matches])

            # JOHN: The question of whether or not we should only handle
            #       printables came up when we worked on XOR...
            #       ... but we left it raw, because what if it uncovers a file?
            # if raw.replace('\n', '').isprintable():
            katana.recurse(self, raw)
            katana.add_results(self, raw)

        except:
            pass

        for result in self.matches:
            decimal = int(result, 2)
            try:
                result = binascii.unhexlify(hex(decimal)[2:])
            # If this fails, it's probably not binary we can deal with...
            except (UnicodeDecodeError, binascii.Error):
                return None

            # JOHN: The question of whether or not we should only handle
            #       printables came up when we worked on XOR...
            #       ... but we left it raw, because what if it uncovers a file?
            # if new_result.replace('\n','').isprintable():
            if utilities.isprintable(result):
                katana.recurse(self, result)
                katana.add_results(self, result)

            # if it's not printable, we might only want it if it is a file...
            else:
                magic_info = magic.from_buffer(result)
                if utilities.is_good_magic(magic_info):
                    katana.add_results(self, result)

                    filename, handle = katana.create_artifact(self, "decoded", mode='wb', create=True)
                    handle.write(result)
                    handle.close()
                    katana.recurse(self, filename)
