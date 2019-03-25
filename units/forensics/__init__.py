from pwn import *
from unit import BaseUnit
import socket
import re

class ForensicsUnit(BaseUnit):

    @classmethod
    def prepare_parser(cls, config, parser):
        # Nothing to do in this case...
        pass

    def __init__(self, config):
        super(ForensicsUnit, self).__init__(config)

    # The sub-class should define this...
    def check(self, target):
        return True

    # The sub-class should define this...
    #  def evaluate(self, target):
    #     pass  
    #
    # If you do not include this function, the main unit.py
    # will properly display its name.
    