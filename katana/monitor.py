#!/usr/bin/env python3
from __future__ import annotations
from typing import BinaryIO, Any
import logging
import os

logger = logging.getLogger(__name__)

class Monitor(object):
	""" A monitor object recieves notifications from units whenever data,
	artifacts or flags are found while processing a target. The default monitor
	simply saves all artifacts to the artifact directory, and recurses on all
	data. It will also print flags to the console via it's logger. """

	def __init__(self):
		return

	def on_depth_limit(self, manager: katana.manager.Manager,
			target: katna.target.Target, unit: katana.unit.Unit) -> None:
		""" This means we reached the manager['manager']['max-depth'] limit
		during recursion. """

		logger.warning(f" {target}: reached max depth of \
				{manager['manager']['max-depth']}")

		return

	def on_data(self, manager: katana.manager.Manager,
			unit: katana.unit.Unit, data: Any) -> bool:
		""" Notify the monitor of arbitrary data returned by a unit. The data
		could be of any type, but is likely `bytes` and should never be `str`
		(for complient units). The return value should indicate whether the
		given data should be recursed on (or re-evaluated for further unit
		processing). By default, all data is recursed on """
		return True
	
	def on_artifact(self, manager: katana.manager.Manager,
			unit: katana.unit.Unit, data: BinaryIO, name: str = None) -> bool:
		""" Notify the monitor that an artifact was found and may be of
		interest to store in a file. This may be a temporary file already open
		(which will be lost after the unit ends) or some data which appears
		to be a file. By default, this file is saved under the `outdir`
		directory of the Manager. The return value indicates whether a new
		target should be queued for recursion with this artifact as an upstream
		"""
		
		# Open a new artifact under the manager
		with manager.artifact(unit, name) as fh:
			# read first block
			block = data.read(4096)
			# Continue while there is data
			while block is not None:
				# Write block
				fh.write(block)
				# Read next
				block = data.read(4096)

		return True
	
	def on_flag(self, manager: katana.manager.Manager,
			unit: katana.unit.Unit, flag: str) -> None:
		""" Notify the monitor that a flag was found """

		chain = []

		# Build the solution chain
		link = unit
		while link is not None:
			chain.append(link)
			link = unit.target.parent

		# Reverse the chain
		chain = chain[::-1]

		# Solution string
		solution = ''
		for link in chain:
			solution += '{0}({1})->'.format(link, link.target)

		# Append flag to solution
		solution += flag

		logger.info(' solution: {0}'.format(solution))

	def on_exception(self, manager: katana.manager.Manager,
			unit: katana.unit.Unit, exc: Exception) -> None:
		""" Notify the monitor that an exception occurred while processing a
		given unit. The exception is passed as the `exc` parameter """
		logger.warning(' {0}: exception: {1}'.format(unit, exc))
