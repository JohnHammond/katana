# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-03-24 17:05:05

from pwn import *
from unit import BaseUnit
import os

class RawUnit(BaseUnit):

    @classmethod
    def prepare_parser(cls, config, parser):
        # Nothing to really do with this "raw file" unit...
        # At least that I can think of at the moment.
        pass


    def __init__(self, config):
        super(RawUnit, self).__init__(config)


    def process_output(self, popen_object):

        result = {
            "stdout": [],
            "stderr": [],
        }

        output = bytes.decode(popen_object.stdout.read(),'ascii')
        error = bytes.decode(popen_object.stderr.read(),'ascii')
        
        for line in [ l.strip() for l in error.split('\n') if l ]:
            result["stderr"].append(line)
        for line in [ l.strip() for l in output.split('\n') if l ]:
            result["stdout"].append(line)

        if not len(result['stderr']):
            result.pop('stderr')
        if not len(result['stdout']):
            result.pop('stdout')
        
        return result


    # The sub-class should define this, to see if the action is feasible...
    def check(self, target):
        if ( os.path.exists(target) ):
            return True
        else:
            log.failure("%s does not exist!" % target )
            return False


    # The sub-class should define this, to actually perform the action...
    def evaluate(self, target):
        log.warning('you didn\'t specify an action for this RawUnit')