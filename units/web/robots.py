#!/usr/bin/env python3
from pwn import *
import requests
from web import WebUnit
from katana import RESULTS 

class Unit(WebUnit):

    def __init__(self, config):
        super(Unit, self).__init__(config)

    def check(self, target):
        try:
            self.explode_url(target)
        except:
            return False
        return True

    def prepare_parser(config, parser):
        pass

    def get_cases(self, target):

        # This should "yield 'name', (params,to,pass,to,evaluate)"
        # evaluate will see this second argument as only one variable and you will need to parse them out

        stripped_target = target.rstrip('/').rstrip('\\')

        # Assume that you are in fact the Google crawler.
        headers = { 'User-Agent': 'Googlebot/2.1' }

        # Try to get the robots.txt file
        r = requests.get('{0}/{1}'.format(stripped_target, 'robots.txt'), headers = headers)

        # Check if the request succeeded
        if r.status_code != 200:
            # Completely fail if there is nothing there.
            return None

        f,name = self.artifact(target, 'robots.txt')
        self.find_flags(r.text)
        with f:
            f.write(r.text)

        RESULTS.update({ target : {} })
        
        RESULTS[target][self.unit_name] = {
            'findings': [],
            'artifact': name
        }

        # Look for disallow entries and add them to the findings
        for line in r.text.split('\n'):
            line = line.strip().split(':')
            if line[0].strip().startswith('#'):
                # This is a comma
                continue
            elif len(line) == 1:
                # This line is empty for some reason
                continue
            
            RESULTS[target][self.unit_name]['findings'].append(':'.join(line))

            # Yield each link, so we can retrieve it and hunt for flags inside of evaluate()
            yield line[1], '{0}/{1}'.format(stripped_target, line[1]) 
    
    def evaluate(self, target):

        # Assume that you are in fact the Google crawler.
        headers = { 'User-Agent': 'Googlebot/2.1' }

        # Retrieve the listed location and hunt for flags.
        r = requests.get(target, headers = headers)
        
        # Hunt!
        self.find_flags(r.text)

        # We've been doing weird stuff with the RESULTS dictionary...
        # So if twe
        try:
            return RESULTS[target][self.unit_name]
        except KeyError:
            pass