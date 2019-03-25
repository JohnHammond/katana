from pwn import *
from unit import BaseUnit
import socket
import re

class PdfUnit(BaseUnit):

    @classmethod
    def prepare_parser(cls, config, parser):
        pass

    def __init__(self, config):
        super(PdfUnit, self).__init__(config)

    # The sub-class should define this to ensure it is actually a feasible attack...
    def check(self, target):
        # It appears to be okay
        return True

    # The sub-class should define this...
    #  def evaluate(self, target):
    #     pass  
    #
    # If you do not include this function, the main unit.py
    # will properly display its name.