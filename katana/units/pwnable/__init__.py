from pwn import *
from katana import units

class ElfUnit(units.FileUnit):

	# This module is unsafe in most environments! It will attempt to execute
	# the target!!!!
	EXECUTE_UNSAFE = True

	def __init__(self, katana, target):
		""" Check that this is a valid ELF binary """
		super(ElfUnit, self).__init__(katana, target)
		
		# Load the binary
		try:
			self.elf = ELF(self.target.path, checksec=False)
		except:
			raise units.NotApplicable("not an elf binary")
	
	def rop_chain(self, *args):
		return

class BasicBufferOverflowUnit(ElfUnit):

	def __init__(self, katana, target):
		""" Check that at least one of "--functions" exists """
		super(BasicBufferOverflowUnit, self).__init__(katana, target)

		self.functions = []
		for func in katana.config['functions'].split(','):
			if func.encode('utf-8') in self.elf.symbols:
				self.functions.append(self.elf.symbols[func.encode('utf-8')])

		if len(self.functions) == 0:
			raise units.NotApplicable("no functions found")
	
	def enumerate(self, katana):
		""" Return each function as a case for execution """
		for func in self.functions:
			yield func
