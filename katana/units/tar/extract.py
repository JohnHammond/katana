import tarfile

from katana import units
from pwn import *


class Unit(units.FileUnit):
    PRIORITY = 40

    def __init__(self, katana, target):
        # This ensures it is a TAR file
        super(Unit, self).__init__(katana, target, keywords=[' tar archive'])
        self.completed = True

    def evaluate(self, katana, case):
        password = case
        result = {
            'password': '',
            'namelist': []
        }

        if isinstance(self.target.path, str):
            path = self.target.path
        else:
            path = self.target.path.decode('utf-8')
        directory_path, _ = katana.create_artifact(self, os.path.basename(path), create=True, asdir=True)

        def py_files(members):
            for each_file in members:
                katana.add_artifact(self, os.path.join(directory_path, each_file))
                yield each_file

        tar = tarfile.open(path)
        for tarinfo in tar:
            tar.extract(tarinfo.name, path=directory_path)
            katana.add_artifact(self, path)
            katana.recurse(self, path)

        return
