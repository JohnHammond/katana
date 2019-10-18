#!/usr/bin/env python3
import argparse
import logging
import sys

from katana.manager import Manager
from katana.monitor import Monitor, LoggingMonitor
from katana.target import Target
from katana.unit import Unit

class ConsoleMonitor(Monitor):

	logger = logging.getLogger('monitor')

	def __init__(self, *args, **kwargs):
		super(ConsoleMonitor, self).__init__(*args, **kwargs)

		self.flags = []

	def on_flag(self, manager: Manager, unit: Unit, flag: str) -> None:

		chain = []

		# Build chain in reverse direction
		link = unit
		while link is not None:
			chain.append(link)
			link = link.target.parent

		# Reverse the chain
		chain = chain[::-1]

		# Print the chain
		for n in range(len(chain)):
			print('{0}{1}({2})->'.format(' '*n, chain[n], ellipsize(str(chain[n].target))))
		print('{0}{1}'.format(' '*len(chain), flag))

		# Save for in depth display at completion
		self.flags.append((unit,flag))
	
	def on_exception(self, manager: Manager, unit: Unit, e: Exception) -> None:
		raise e

def ellipsize(s: str, length=64):
	s = s.split('\n')[0]
	if len(s) >= (length-3):
		s = s[:length-3] + '...'
	return s

def main():

	# Setup basic logging
	logging.basicConfig(level=logging.INFO)

	# Build the argument parse object
	parser = argparse.ArgumentParser(prog='katana',
			description='Automatically identify and solve basic Capture the Flag challenges',
			add_help=False)

	# Parse config option first
	parser.add_argument('--config', '-c', help='configuration file',
			default=None)
	args, remaining_args = parser.parse_known_args()

	# Build our katana monitor
	monitor = LoggingMonitor()

	# Create our katana manager
	manager = Manager(monitor=monitor, config_path=args.config)

	# Build final parser
	parser = argparse.ArgumentParser(prog='katana',
			description='Automatically identify and solve basic Capture the Flag challenges',
			add_help=False)

	# Add global arguments
	parser.add_argument('--config', '-c', help='configuration file',
			default=None)
	parser.add_argument('--manager', '-m', default=None,
			help='comma separated manager configurations (e.g. flag-format=FLAG{.*?})')
	parser.add_argument('--timeout', '-t', type=float,
			help='timeout for all unit evaluations in seconds')
	parser.add_argument('targets', nargs='+', help='targets to evaluate')
	
	# Add options for all the unit specific configurations
	for unit in manager.finder.units:
		parser.add_argument('--'+unit.get_name(), default=None,
			help='comma separated unit configuration')
	
	# Parse arguments
	args = parser.parse_args(remaining_args)

	# Load configuration file
	if args.config is not None:
		result = manager.read(args.config)
		if len(result) == 0:
			logging.error(' {0}: no such file or directory'.format(
				args.config
			))
			sys.exit(1)
	
	# Apply configurations
	if args.manager is not None:
		params = args.manager.split(',')
		for param in params:
			name, value = param.split('=')
			manager['manager'][name] = value
	
	# Apply unit configurations
	args_dict = vars(args) # We need this because configs have '.'
	for unit in manager.finder.units:
		# Ignore if nothing was specified
		if args_dict[unit.get_name()] is None:
			continue

		# Initialize the unit if needed
		if unit.get_name() not in manager:
			manager[unit.get_name()] = {}

		# Parse params
		params = args_dict[unit.get_name()].split(',')
		for param in params:
			name, value = param.split('=')
			manager[unit.get_name()][name] = value

	# Start the manager processing threads
	logging.info('starting manager threads')
	manager.start()

	# Queue the specified targets
	for target in args.targets:
		logging.info('queuing target {0}'.format(target))
		manager.queue_target(target)

	logging.info('waiting for evaluation completion (timeout={0})'.format(
		args.timeout))
	if not manager.join(timeout=args.timeout):
		logging.warning('evaluation timed out prior to completion!')

if __name__ == '__main__':
	main()
