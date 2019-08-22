"""

NATO phonetic alphabet translater.

This unit will translate the code words found in the NATO phonetic alphabet to 
their corresponding letter mapping.

"""

from katana.units import NotApplicable
from katana import units

# Duplicate entries for things that may be represented 
# in multiple ways
nato_mappings = [
	"alfa", "bravo","charlie", 'delta', 'echo', 'foxtrot','golf',
	'hotel', 'india', 'juliett', 'juliet',  'kilo', 'lima', 'mike', 'november',
	'oscar', 'papa', 'quebec', 'romeo', 'sierra', 'tango', 'uniform',
	'victor', 'whiskey', 'x-ray', 'xray', 'yankee', 'zulu'
]


class Unit(units.PrintableDataUnit):
	'''
	This unit inherits from the :class:`katana.units.PrintableDataUnit` class, 
	as the target will have to be printable if it were to contain
	the NATO phonetic words like Alfa, Bravo, Charlie, etc.
	'''

	PRIORITY = 50

	def __init__(self, katana, target, keywords=[]):
		"""
		The constructor removes spaces from the text and quits if it fails to
		decode the target.
		"""
		
		super(Unit, self).__init__(katana, target)

		if keywords is None:
			keywords = []
		try:
			self.raw_target = self.target.stream.read().decode('utf-8').lower()
			self.raw_target = self.raw_target.replace(' ', '')
		except UnicodeDecodeError:
			raise NotApplicable("seemingly binary data")


	def evaluate(self, katana, case):
		'''
		Perform a simple ``replace()`` call on the target with the NATO
		alphabet, and both add and recurse on the new result.
		'''

		result = self.raw_target
		for mapping in nato_mappings:
			result = result.replace(mapping, mapping[0])

		katana.recurse(self, result)
		katana.add_results(self, result)