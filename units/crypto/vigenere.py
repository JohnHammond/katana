from unit import BaseUnit
from units import NotApplicable
from units import PrintableDataUnit
from units import NotEnglishUnit
import utilities
import string

def vigenere(plaintext, key):
	plaintext = plaintext.upper()
	key = key.upper()

	valid_chars = string.ascii_uppercase

	idx = 0
	ciphertext = []

	for i, c in enumerate(plaintext):
		if c not in valid_chars:
			ciphertext.append(c)
		else:
			try:
				if key[idx] not in valid_chars:
					idx = (idx + 1) % len(key)
			except IndexError:
				continue
			v1 = ord(c) - ord('A')
			v2 = ord(key[idx]) - ord('A')
			ciphertext.append(chr(((v1 - v2) % 26)+ord('A')))
			idx = (idx + 1) % len(key)

	return ''.join(ciphertext)

# class Unit(PrintableDataUnit):
class Unit(NotEnglishUnit):

	PROTECTED_RECURSE = True

	@classmethod
	def add_arguments(cls, katana, parser):
		parser.add_argument('--vigenere-password', type=str,
			action='append', help='a password for {0} files',
			default=[]
		)
		return	


	def enumerate(self, katana):
		# Check each given password
		for p in katana.config['vigenere_password']:
			yield p

		# Add all passwords from the dictionary file
		if 'dict' in katana.config and katana.config['dict'] is not None:
			katana.config['dict'].seek(0)
			try:
				for line in katana.config['dict']:
					yield line.rstrip('\n')
			except UnicodeDecodeError:
				# JOHN: This happens sometimes on line 54 and I DON'T KNOW WHY
				return

	def evaluate(self, katana, case):

		result = vigenere(self.target, case)

		if result:
			katana.locate_flags(self, result)
			katana.add_results(self, result)

			if utilities.is_english(result):
				katana.recurse(self, result)
	
