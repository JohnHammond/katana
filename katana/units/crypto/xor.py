import binascii

from katana import units
from katana.units import NotApplicable
from pwn import *

# DO NOT recurse this... it will bottleneck Katana
PROTECTED_RECURSE = True


# JOHN: I inherit from FileOrData unit, because this may very well not be printable text!
class Unit(units.BaseUnit):
    PRIORITY = 70
    ARGUMENTS = [
        {'name': 'xor_key',
         'type': str,
         'default': None,
         'required': False,
         'help': 'key to use for XOR operations'
         },
    ]

    # JOHN: This SHOULD be removed following the new unit argument restructure
    @classmethod
    def add_arguments(cls, katana, parser):
        parser.add_argument('--xor-key', type=str,
                            help="key to use for XOR operations",
                            default=None)

    def __init__(self, katana, target):
        super(Unit, self).__init__(katana, target)

        # JOHN: We actually DON'T want printable characters in this case!
        self.completed = True
        try:
            self.raw_target = target.stream.read().decode('utf-8').replace('\n', '').replace('\t', '')
        except UnicodeDecodeError:
            raise NotApplicable("unicode decode error")
        if self.raw_target.isprintable():
            raise NotApplicable("seemingly printable")
        else:
            if self.raw_target.count('\x00') > len(self.raw_target) / 2:
                raise NotApplicable("more than half null-bytes")

    def evaluate(self, katana, case):

        if katana.config['xor_key']:
            key = [katana.config['xor_key']]
        else:
            key = range(255)

        # key = case
        for k in key:
            try:
                result = xor(self.raw_target, k).decode('latin-1')

                if result.isprintable():
                    # JOHN: Recursing on this dangerous, admittedly...
                    #       But sometimes it must be done (!!??!?!)
                    # katana.recurse(self, result)
                    katana.add_results(self, result)
                    # If we find the flag, STOP doing this!!
                    if katana.locate_flags(self, result):
                        pass

                else:
                    return None

            # If this fails, it's probably not binary we can deal with...
            except (UnicodeDecodeError, binascii.Error):
                return None
