#!/usr/bin/env python3
from pwn import *
import requests
from web import WebUnit

class Unit(WebUnit):

    def __init__(self, config):
        super(Unit, self).__init__(config)

    def check(self, target):
        try:
            self.explode_url(target)
        except:
            return False
        return True
    
    def evaluate(self, target):

        # Strip trailing slashes
        target = target.rstrip('/').rstrip('\\')

        # Create a session
        r = requests.get(target)
        
        # Result
        result = [ vars(cookie) for cookie in r.cookies if cookie ]
           
        return result