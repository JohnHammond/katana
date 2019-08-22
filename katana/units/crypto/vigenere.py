import string

from katana.units import NotApplicable
from katana.units import NotEnglishUnit


def vigenere(plaintext, key):
    plaintext = plaintext.upper()
    key = bytes(key.upper(), 'ascii')

    valid_chars = bytes(string.ascii_uppercase, 'ascii')

    idx = 0
    ciphertext = ''

    for c in bytes(plaintext, 'ascii'):
        if c not in valid_chars:
            ciphertext += chr(c)
        else:
            if key[idx] not in valid_chars:
                idx = (idx + 1) % len(key)
            # v1 = ord(c) - ord('A')
            # v2 = ord(key[idx]) - ord('A')
            v1 = c - ord('A')
            v2 = key[idx] - ord('A')
            ciphertext += chr(((v1 - v2) % 26) + ord('A'))
            idx = (idx + 1) % len(key)

    return ciphertext


# class Unit(PrintableDataUnit):
class Unit(NotEnglishUnit):
    PROTECTED_RECURSE = True
    PRIORITY = 65
    ARGUMENTS = [
        {'name': 'vigenere_key',
         'type': str,
         'default': '',
         'required': False,
         'help': 'a key for vignere cipher'
         },
    ]

    # JOHN: This SHOULD be removed following the unit argument restructure
    @classmethod
    def add_arguments(cls, katana, parser):
        parser.add_argument('--vigenere-key', type=str,
                            action='append', help='a key for vignere cipher',
                            default=[]
                            )
        return

    def __init__(self, katana, target):
        super(Unit, self).__init__(katana, target)
        if katana.config['vigenere_key'] == [""]:
            raise NotApplicable("empty vignere key passed")

    def enumerate(self, katana):
        # Check each given password
        for p in katana.config['vigenere_key']:
            yield p

    # Add all passwords from the dictionary file
    # if 'dict' in katana.config and katana.config['dict'] is not None:
    # 	katana.config['dict'].seek(0)
    # 	try:
    # 		for line in katana.config['dict']:
    # 			yield line.rstrip(b'\n')
    # 	except UnicodeDecodeError:
    # 		# JOHN: This happens sometimes on line 54 and I DON'T KNOW WHY
    # 		return

    def evaluate(self, katana, case):

        result = vigenere(self.target.stream.read().decode('utf-8'), case)
        # We do not need to locate_flags anymore because recurse this for us
        # katana.locate_flags(self, result)
        katana.add_results(self, result)
        katana.recurse(self, result)
