# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-03-31 17:30:48

from pwn import *
from unit import BaseUnit
import os

class StegoUnit(BaseUnit):

    @classmethod
    def prepare_parser(cls, config, parser):
        try:
            # Add potential argument parsers in here.
            # parser.add_argument('--proxy', default=None, help='proxy (host:port) to use for web connections')
            pass
        except:
            # These arguments will be inherited by the Units...
            # So it may repeatedly conflict. We'll just have to ignore these
            pass


    def __init__(self, config):
        super(StegoUnit, self).__init__(config)


    # The sub-class should define this, to see if the action is feasible...
    def check(self, target):
        if ( os.path.exists(target) ):
            return True
        else:
            log.failure("%s does not exist!" % target )
            return False


    # The sub-class should define this...
    #  def evaluate(self, target):
    #     pass  
    #
    # If you do not include this function, the main unit.py
    # will properly display its name.
