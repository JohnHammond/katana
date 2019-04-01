from unit import BaseUnit
import magic
import zipfile

class ZipUnit(BaseUnit):

	def __init__(self, *args, **kwargs):
		super(ZipUnit, self).__init__(*args, **kwargs)

	def check(self, target):
		if not zipfile.is_zipfile(target):
			return False
		
		return True
