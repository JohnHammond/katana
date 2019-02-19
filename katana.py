#!/usr/bin/env python3
from pwn import *
import argparse
import json
import sys
import importlib
import queue
import threading

# Global Work Queue
WORKQ = queue.Queue()
RESULTS = []
CONFIG = {}

def DirectoryArgument(name):
    fullpath = os.path.abspath(os.path.expanduser(name))
    if not os.path.isdir(fullpath):
        raise argparse.ArgumentTypeError('{0} is not a directory'.format(name))
    return fullpath

def PythonModule(name):
    try:
        module = importlib.import_module(name)
    except:
        raise argparse.ArgumentTypeError('{0} is not a valid module name'.format(name))
    return module

def get_full_classname(o):
    module = o.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return o.__class__.__name__  # Avoid reporting __builtin__
    else:
        return module + '.' + o.__class__.__name__

class WorkerThread(threading.Thread):
    def __init__(self):
        super(WorkerThread, self).__init__()

    def run(self):
        while True:
            work = WORKQ.get()
            if 'done' in work:
                break
            RESULTS.append(work['unit'].evaluate(CONFIG, work['target']))
            WORKQ.task_done()

# Make sure we find the local packages (first current directory)
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.getcwd())

# Parse command-line arguments
parser = argparse.ArgumentParser(
    description='Low-hanging fruit checker for CTF problems',
    add_help=False,
    allow_abbrev=False
)
parser.add_argument('--unitdir', type=DirectoryArgument, default='./units', help='the configuration file')
parser.add_argument('--list', '-l', action='store_true', default=False, help='list the tests available')
args, remaining = parser.parse_known_args()

# Insert the unit directory module into th epath
sys.path.insert(0, args.unitdir)

# Setup initial configuration block
config = {}
config['units'] = []

parser = argparse.ArgumentParser(parents = [parser], add_help=False)
parser.add_argument('--unit', action='append', type=PythonModule, required=True, help='the units to run on the targets')
args, remaining = parser.parse_known_args()

# Save these for later
unit_modules = args.unit

# Create the next (and last) argument parser
parser = argparse.ArgumentParser(parents = [parser], add_help=True)

# Attempt to load specified units
for unit_module in unit_modules:
    unit_module.Unit.prepare_parser(config, parser)

# Make sure we have targets
parser.add_argument('--threads', '-t', type=int, default=10, help='number of threads to use')
parser.add_argument('--force', '-f', action='store_true', default=False, help='skip the checks')
parser.add_argument('target', nargs='+', type=str, help='the target file/url/IP/etc')
args = parser.parse_args()

# Update the configuration with the arguments
config.update(vars(args))

# Initialize the units array
config['units'] = []

# Create the unit objects, and add them to the list
for unit_module in unit_modules:
    unit = unit_module.Unit(config)
    config['units'].append(unit)

print(type(args.threads))

# Create all the threads
config['threads'] = []
for i in range(args.threads):
    config['threads'].append(WorkerThread())
    config['threads'][-1].start()

# Add all the target/unit pairs to the work queue
for target in args.target:
    for unit in config['units']:
        if args.force or unit.check(config, target):
            WORKQ.put({
                'unit': unit,
                'target': target
            })
        elif not args.force:
            log.info('{0}: invalid target: \'{1}\''.format(unit.__class__.__module__, target))

# Signal all threads that we have finished
for i in range(args.threads):
    WORKQ.put({'done': True})

# Ensure they got the message
WORKQ.join()
