import os

from katana.units import NotEnglishUnit, NotApplicable
from pwn import *

DEPENDENCIES = ['node']


class Unit(NotEnglishUnit):
    PRIORITY = 60

    def __init__(self, katana, target, keywords=None):
        super(Unit, self).__init__(katana, target)

        if keywords is None:
            keywords = []
        try:
            self.jsfuck = re.findall(rb"[\\[\\(\\)\\+!\]]{5,}", self.target.stream.read())
            if not self.jsfuck:
                raise NotApplicable("no jsfuck code found")
        except UnicodeDecodeError:
            raise NotApplicable("unicode error, unlikely jsfuck syntax")

    def evaluate(self, katana, case):

        # First, get the location of the JS library that handles JSFuck...
        this_folder = os.path.dirname(os.path.realpath(__file__))
        jsfuck_lib = os.path.join(this_folder, '__jsfuck.js')

        # Now, process all of the JSFuck with node.
        for jsfuck in self.jsfuck:

            jsfuck = jsfuck.decode('utf-8')

            output = subprocess.Popen(['node', '-e', "var lib = require('{0}'); lib.decode('{1}')".format(
                jsfuck_lib, jsfuck)], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

            response = output.communicate()

            if response[0] != b'':
                response = response[0].decode('utf-8')
                katana.recurse(self, response)
                katana.add_results(self, response)
