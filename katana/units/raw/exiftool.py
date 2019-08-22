import subprocess

from katana import utilities
from katana.units import FileUnit

DEPENDENCIES = ['exiftool']


class Unit(FileUnit):
    PRIORITY = 25

    def __init__(self, katana, target):
        super(Unit, self).__init__(katana, target)

    def evaluate(self, katana, case):

        p = subprocess.Popen(['exiftool', self.target.path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Look for flags, if we found them...
        response = utilities.process_output(p)
        if response:
            if 'stdout' in response:
                for line in response['stdout']:
                    delimited = line.split(':')
                    metadata = delimited[0].strip()
                    value = ':'.join(delimited[1:]).strip()

                    # JOHN: We do NOT recurse on the metadata, because that is probably
                    #       NOT going to contain a flag
                    # katana.recurse(self, metadata)
                    if metadata in ['Comment', 'Album', 'Artist', 'Title']:
                        katana.recurse(self, value)

            katana.add_results(self, response)
