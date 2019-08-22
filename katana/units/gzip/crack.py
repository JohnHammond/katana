from katana import units

import gzip


class Unit(units.FileUnit):
    PRIORITY = 40

    def __init__(self, katana, target):
        # This ensures it is a GZIP
        super(Unit, self).__init__(katana, target, keywords=['gzip compressed'])

    def evaluate(self, katana, case):

        if isinstance(self.target.path, str):
            path = self.target.path
        else:
            path = self.target.path.decode('utf-8')

        # JOHN: The actual extraction process...
        with gzip.open(path, 'rb') as gz:
            name, f = katana.create_artifact(self, 'gunzip_data', 'wb')

            with f:
                for chunk in iter(lambda: gz.read(4096), b""):
                    f.write(chunk)

            katana.recurse(self, name)
            katana.add_artifact(self, 'gunzip_data')
