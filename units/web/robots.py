#!/usr/bin/env python3
from pwn import *
import requests
from web import WebUnit

class Unit(WebUnit):

    def __init__(self, config):
        super(Unit, self).__init__(config)
        log.info('initializing the robots module')

    def evaluate(self, config, target):
        log.info('evaluating {0} for robots.txt'.format(target))
        return {}