import subprocess

from katana import units
from katana.units import NotApplicable

DEPENDENCIES = ['npiet']


class Unit(units.FileUnit):
    PRIORITY = 30

    def __init__(self, katana, target, keywords=None):
        super(Unit, self).__init__(katana, target, keywords=['image'])

        if keywords is None:
            keywords = []
        if target.is_url:
            raise NotApplicable('target is a URL')

    def evaluate(self, katana, case):

        p = subprocess.Popen(['npiet', self.target.path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        lines = []
        for line in p.stdout:
            katana.locate_flags(self, line)
            lines.append(line)

        for line in lines:
            katana.recurse(self, line)
