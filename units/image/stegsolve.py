from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *

class Unit(BaseUnit):

    @classmethod
    def prepare_parser(cls, config, parser):
        parser.add_argument('--dictionary', '-d', type=argparse.FileType('r'),
            default=None, help='a dictionary of possible passwords')

    def evaluate(self, target):

        return output

