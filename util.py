import os
import importlib

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