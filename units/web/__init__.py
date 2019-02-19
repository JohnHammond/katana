from pwn import *
import socket
import re

class WebUnit(object):

    ADDRESS_PATTERN = r'^((?P<proto>[a-zA-Z][a-zA-Z0-9]*):\/\/)?(?P<host>[a-zA-Z0-9][a-zA-Z0-9\-_.]*)(:(?P<port>[0-9]{1,5}))?(\/(?P<uri>[^?]*))?(\?(?P<query>.*))?$'
    @classmethod
    def prepare_parser(cls, config, parser):
        parser.add_argument('--proxy', default=None, help='proxy (host:port) to use for web connections')
        parser.add_argument('--dns', default=None, help='custom dns server to use')

    def __init__(self, config):
        super(WebUnit, self).__init__()
        self.regex = re.compile(WebUnit.ADDRESS_PATTERN)

    # Explode a URL into it's protocol, host, port, uri, and query string
    def explode_url(self, target):
        match = self.regex.match(target)
        
        if match is None:
            raise ValueError('{0}: not a valid url'.format(target))

        return match.groupdict(default='')

    # Check that the target is a web address of some kind
    def check(self, config, target):
        # It appears to be okay
        return True

    # The sub-class should define this...
    def evaluate(self, config, target):
        log.warning('you didn\'t specify an action for this WebUnit')