"""

The Polybius square cipher.

By default this uses just the English alphabet with J removed to create the 
Polybius square. You can of course change this by supplying a
``polybius_square`` argument as a string of uppercase letters.
"""

from katana.units import NotApplicable
from katana import units

def generate_table(alphabet = 'ABCDEFGHIKLMNOPQRSTUVWXYZ'):
	'''
	Create the 5x5 table for the Polybius square based off the given alphabet.
	By default, use the English alphabet with the letter J removed.
	'''
	
	table = [[0] * 5 for row in range(5)]

	counter = 0
	for y in range(5):
		for x in range(5):
			table[x][y] = alphabet[counter]
			counter += 1
	return table


def decrypt(table, numbers):
	'''
	Based off the given table and a string of numbers, look-up each value on
	the Polybius square and build a new string
	'''

	text = []
	for index in range(0, len(numbers), 2):
		try:
			x = int(numbers[index]) - 1
			y = int(numbers[index + 1]) - 1
			text.append(table[y][x])
		except:
			# Not an issue if we can't find it... just don't add the text.
			pass

	return ''.join(text)

class Unit(units.PrintableDataUnit):
	'''
	This unit inherits from the :class:`katana.units.PrintableDataUnit` class, 
	as the target that is necessary for this class should only contain numbers.

	``RECURSE`` is set to 40, as this is a more specific case that should move
	relatively quickly.
	'''

	PROTECTED_RECURSE = True
	PRIORITY = 40

	ARGUMENTS = [
		{ 'name': 		'polybius_alphabet', 
		  'type': 		str, 
		  'default': 	"ABCDEFGHIKLMNOPQRSTUVWXYZ", 
		  'required': 	False,
		  'help': 		'key to use for the polybius square cipher'
		},
	]

	def __init__( self, katana, target ):
		'''
		The constructor removes spaces and ensure that only decimal numbers are
		given in the target.
		'''
		super(Unit, self).__init__(katana, target)

		self.no_spaces = self.target.stream.read().decode('utf-8').replace(' ','')
		if not self.no_spaces.isdecimal():
			raise NotApplicable("not just decimal numbers")

	
	def evaluate(self, katana, case):
		'''
		Generate a table and decrypt the target based off the Polybius square.
		Add and recurse on the results.
		'''

		table = generate_table(katana.config['polybius_alphabet'])
		content = decrypt(table, self.no_spaces)
		
		katana.recurse(self,content)
		katana.add_results(self, content)
