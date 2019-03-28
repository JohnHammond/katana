#!/usr/bin/env python3
from pwn import *
import requests
from web import WebUnit

# JOHN: March 24th
# I'm not going to finish implementing the actual download
# of a github repo right now -- but will check to see if
# one exists
# Code ideas come from: https://github.com/internetwache/GitTools/

class Unit(WebUnit):

    def __init__(self, config):
        super(Unit, self).__init__(config)

    def prepare_parser(config, parser):
        pass

    def check(self, target):
        try:
            self.explode_url(target)
        except:
            return False
        return True
    
    def evaluate(self, target):

        # Strip trailing slashes
        target = target.rstrip('/').rstrip('\\')

        # Try to get see if there is a .git directory
        url = '{0}/{1}'.format(target, '.git/HEAD')
        r = requests.get(url)


        # If the response is anything other than a "Not Found",
        # we might have something here...
        if r.status_code == 404:
            return None
        else:
            result = {
                'git_repo': url,
            }
    
            return result
