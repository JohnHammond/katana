from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
import os
import units.raw
import util

class Unit(units.raw.RawUnit):

	@classmethod
	def prepare_parser(cls, config, parser):
		pass

	def evaluate(self, target):

		p = subprocess.Popen(['file', target], stdout = subprocess.PIPE, stderr = subprocess.PIPE)		
		return util.process_output(p)