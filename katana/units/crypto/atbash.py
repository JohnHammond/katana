"""
Classic atbash cipher.
"""

from katana import units

from pwn import *
import string
import io

class Unit(units.NotEnglishAndPrintableUnit):
	'''
	This unit inherits from the :class:`katana.units.NotEnglishUnit` class, as
	we will likely only perform atbash ciphers on data that is 
	printable but does not look English plaintext already.

	:data:`PROTECTED_RECURSE` is ``True`` for this unit, because we do not 
	want results that come from this unit being processed *yet again* by this 
	unit. That would make for pointless computation and potentially an 
	infinite loop.

	:data:`PRIORITY` is set to 60, as this has potential to be a long and 
	time-consuming operation. 
	'''

	PROTECTED_RECURSE :bool = True
	PRIORITY :int = 60	

	def evaluate(self, katana, case):
		'''
		Perform the atbash operation on the given target.
		'''

		new_string :list = []
		reverse_upper :str = string.ascii_uppercase[::-1]
		reverse_lower :str = string.ascii_lowercase[::-1]

		# For each character, grab and add its corresponding one in the atbash 
		# alphabet.
		with io.TextIOWrapper(self.target.stream, encoding='utf-8') as stream:
			try: 
				for character in iter(lambda: stream.read(1), ''):
					if character in string.ascii_uppercase:
						new_string.append(reverse_upper[string.ascii_uppercase.index(character)])
					elif character in string.ascii_lowercase:
						new_string.append(reverse_lower[string.ascii_lowercase.index(character)])
					else:
						new_string.append(character)
			except UnicodeDecodeError:
				# We can't decode this character. Ignore it.
				pass

		result :str = ''.join(new_string)

		katana.recurse(self, result)
		katana.add_results(self, result)