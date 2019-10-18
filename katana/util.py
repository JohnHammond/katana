#!/usr/bin/env python3
import string

def isprintable(data) -> bool:
	'''
	This is a convenience function to be used rather than the usual 
	``str.printable`` boolean value, as that built-in **DOES NOT** consider
	newlines to be part of the printable data set (weird!)
	'''
	
	if type(data) is str:
		data = data.encode('utf-8')
	for c in data:
		if c not in bytes(string.printable,'ascii'):
			return False

	return True

def is_good_magic(magic: str) -> bool:
	""" Checks if the magic type is in a list of known interesting file types
	"""
	interesting_types = ['image', 'document', 'archive', 'file', 'database',
		'package', 'binary', 'video', 'executable', 'format',
		'certificate', 'bytecode']
	return magic in interesting_types
