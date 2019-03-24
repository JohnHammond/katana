from pwn import *
from unit import BaseUnit
import socket
import re

class CryptoUnit(BaseUnit):

    @classmethod
    def prepare_parser(cls, config, parser):
        # Nothing to do in this case...
        pass

    def __init__(self, config):
        super(CryptoUnit, self).__init__(config)

    # The sub-class should define this...
    def check(self, target):

        return True

    # The sub-class should define this...
    def evaluate(self, target):
        log.warning('you didn\'t specify an action for this WebUnit')