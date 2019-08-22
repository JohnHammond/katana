import subprocess

from katana import units
from katana import utilities

DEPENDENCIES = ['jsteg']


class Unit(units.FileUnit):
    PRIORITY = 30

    def __init__(self, katana, target):
        # This ensures it is a JPG
        super(Unit, self).__init__(katana, target, keywords=['jpg image', 'jpeg image'])

    def evaluate(self, katana, case):

        p = subprocess.Popen(['jsteg', 'reveal', self.target.path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Look for flags, if we found them...
        response = utilities.process_output(p)

        if 'stdout' in response:
            for line in response['stdout']:
                katana.recurse(self, line)

        if 'stderr' in response:
            return

        katana.add_results(self, response)
