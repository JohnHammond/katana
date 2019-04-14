from unit import BaseUnit
from units import NotApplicable
from units import PrintableDataUnit
import string

def vigenere(plaintext, key):
        plaintext = plaintext.upper()
        key = key.upper()

        valid_chars = string.ascii_uppercase

        idx = 0
        ciphertext = ''

        for c in plaintext:
                if c not in valid_chars:
                        ciphertext += c
                else:
                        if key[idx] not in valid_chars:
                                idx = (idx + 1) % len(key)
                        v1 = ord(c) - ord('A')
                        v2 = ord(key[idx]) - ord('A')
                        ciphertext += chr(((v1 - v2) % 26)+ord('A'))
                        idx = (idx + 1) % len(key)

        return ciphertext

class Unit(PrintableDataUnit):

	PROTECTED_RECURSE = True

	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--vigenere-password', type=str,
			action='append', help='a password for {0} files',
			default=[]
		)
		return	

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)

	def enumerate(self, katana):
		# Check each given password
		for p in katana.config['vigenere_password']:
			yield p

		# Add all passwords from the dictionary file
		if 'dict' in katana.config and katana.config['dict'] is not None:
			katana.config['dict'].seek(0)
			for line in katana.config['dict']:
				yield line.rstrip('\n')

	def evaluate(self, katana, case):
		result = vigenere(self.target, case)
		katana.locate_flags(self, result)
		katana.add_results(self, result)
		katana.recurse(self, result)
	
