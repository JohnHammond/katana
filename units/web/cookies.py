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

        # View the page
        r = requests.get(target)
        
   		# Return the cookies
        result = [ vars(cookie) for cookie in r.cookies if cookie ]
        
        # Hunt for flags...
        for key, value in result:
            self.find_flags(key)
            self.find_flags(value)

        return result