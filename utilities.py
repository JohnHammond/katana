import os
import importlib
import argparse

# This subclass of argparse will print the help whenever there
# is a syntactic error in the options parsing
class ArgumentParserWithHelp(argparse.ArgumentParser):
	def error(self, message):
		print('{0}: error: {1}'.format(self.prog, message))
		self.print_help()
		sys.exit(2)

# argparse type to automatically verify that the specified path
# exists and is a directory
def DirectoryArgument(name):
    fullpath = os.path.abspath(os.path.expanduser(name))
    if not os.path.isdir(fullpath):
        raise argparse.ArgumentTypeError('{0} is not a directory'.format(name))
    return fullpath

# argparse type to automatically verify module existence and load it
def PythonModule(name):
    try:
        log.info('loading unit: {0}'.format(name))
        module = importlib.import_module(name)
    except Exception as e:
        print(e)
        raise argparse.ArgumentTypeError('{0} is not a valid module name'.format(name))
    return module

# This is dumb, but it makes the code more expressive...
def GetUnitName(unit):
    return unit.__module__

# Gets a fully qualified class name
def GetFullyQualifiedClassName(o):
    module = o.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return o.__class__.__name__  # Avoid reporting __builtin__
    else:
        return module + '.' + o.__class__.__name__

def find_modules_recursively(path, prefix):
	""" Locate all modules under a path """
	for importer, name, ispkg in pkgutil.iter_modules(path, prefix):
		if ispkg:
			for s in find_modules_recursively(module.__path__, module.__name__ + '.'):
				yield s
		else:
			yield name

# -------------------------------------------------------------------

# These are utility functions that may be used in more than one module.

def process_output(popen_object):

    result = {
        "stdout": [],
        "stderr": [],
    }

    output = bytes.decode(popen_object.stdout.read(),'ascii')
    error = bytes.decode(popen_object.stderr.read(),'ascii')
    
    for line in [ l.strip() for l in error.split('\n') if l ]:
        result["stderr"].append(line)
    for line in [ l.strip() for l in output.split('\n') if l ]:
        result["stdout"].append(line)

    if not len(result['stderr']):
        result.pop('stderr')
    if not len(result['stdout']):
        result.pop('stdout')
    
    return result
