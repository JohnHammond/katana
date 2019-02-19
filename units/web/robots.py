#!/usr/bin/env python3
from pwn import *
import requests
from web import WebUnit

class Unit(WebUnit):

    def __init__(self, config):
        super(Unit, self).__init__(config)

    def check(self, config, target):
        try:
            self.explode_url(target)
        except:
            return False
        return True

    def evaluate(self, config, target):

        # Strip trailing slashes
        target = target.rstrip('/').rstrip('\\')

        # Try to get the robots.txt file
        r = requests.get('{0}/{1}'.format(target, 'robots.txt'))

        # Check if the request succeeded
        if r.status_code != 200:
            return None

        # Result
        result = {
            'unit': self.__class__.__module__,
            'target': target,
            'findings': []
        }

        # Look for disallow entries and add them to the findings
        for line in r.text.split('\n'):
            line = line.strip().split(':')
            if line[0].strip() != 'Disallow':
                # This is not a disallow entry
                continue
            elif len(line) == 1:
                # This disallow is empty for some reason
                continue
            result['findings'].append(':'.join(line[1:]).strip())

        # robots.txt exists, but contains no disallow entries
        if len(result['findings']) == 0:
            return None
            
        return result