#!/usr/bin/env python3
from __future__ import annotations
from typing import BinaryIO, Any
import logging
import os

logger = logging.getLogger(__name__)

def ellipsize(s: str, length=64):
	s = s.split('\n')[0]
	if len(s) >= (length-3):
		s = s[:length-3] + '...'
	return s

class Monitor(object):
	""" A monitor object recieves notifications from units whenever data,
	artifacts or flags are found while processing a target. The default monitor
	simply saves all artifacts to the artifact directory, and recurses on all
	data. It will also print flags to the console via it's logger. """

	def __init__(self):
		self.flags = []
		self.data = []
		self.artifacts = []
		self.exceptions = []
		return

	def on_depth_limit(self, manager: katana.manager.Manager,
			target: katna.target.Target, unit: katana.unit.Unit) -> None:
		""" This means we reached the manager['manager']['max-depth'] limit
		during recursion. """
		return

	def on_data(self, manager: katana.manager.Manager,
			unit: katana.unit.Unit, data: Any) -> bool:
		""" Notify the monitor of arbitrary data returned by a unit. The data
		could be of any type, but is likely `bytes` and should never be `str`
		(for complient units). The return value should indicate whether the
		given data should be recursed on (or re-evaluated for further unit
		processing). By default, all data is recursed on """
		self.data.append((unit, data))
		return True
	
	def on_artifact(self, manager: katana.manager.Manager,
			unit: katana.unit.Unit, path: str = None) -> bool:
		""" Notify the monitor that an artifact was found and may be of
		interest to store in a file. This may be a temporary file already open
		(which will be lost after the unit ends) or some data which appears
		to be a file. By default, this file is saved under the `outdir`
		directory of the Manager. The return value indicates whether a new
		target should be queued for recursion with this artifact as an upstream
		"""

		self.artifacts.append((unit, path))
		
		return True
	
	def on_flag(self, manager: katana.manager.Manager,
			unit: katana.unit.Unit, flag: str) -> None:
		""" Notify the monitor that a flag was found """
		self.flags.append((unit, flag))

	def on_exception(self, manager: katana.manager.Manager,
			unit: katana.unit.Unit, exc: Exception) -> None:
		""" Notify the monitor that an exception occurred while processing a
		given unit. The exception is passed as the `exc` parameter """
		self.exceptions.append((unit, exc))
	
	def on_completion(self, manager: katana.manager.Manager,
			timed_out: bool) -> None:
		""" This is called upon completion of evaluation (after manager.join()
		is complete). `timed_out` indicates if we reached a timeout. """

class LoggingMonitor(Monitor):

	logger = logging.getLogger('monitor')

	def __init__(self, *args, **kwargs):
		super(LoggingMonitor, self).__init__(*args, **kwargs)
	
	def on_flag(self, manager: katana.manager.Manager,
			unit: katana.unit.Unit, flag: str):
		""" Log the solution chain of units which resulted in the given flag
		"""
		super(LoggingMonitor, self).on_flag(manager, unit, flag)

		log_entry = ' new flag found:\n'
	
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
			log_entry += '  {0}{1}({2})->\n'.format(' '*n,
					chain[n], ellipsize(str(chain[n].target)))
		log_entry += '  {0}{1}'.format(' '*len(chain), flag)

		# Log the solution chain
		logger.info(log_entry)
	
	def on_artifact(self, manager: katana.manager.Manager,
			unit: katana.unit.Unit, path: str) -> None:
		""" Log a new artifact """
		super(LoggingMonitor, self).on_artifact(manager, unit, path)

		logger.info(f' {unit}({unit.target}): new artifact: {path}')
	
	def on_exception(self, manager: katana.manager.Manager,
			unit: katana.unit.Unit, exception: Exception) -> None:
		super(LoggingMonitor, self).on_exception(manager, unit, exception)
		logger.warning(f' {unit}({unit.target}): exception: {exception}')
