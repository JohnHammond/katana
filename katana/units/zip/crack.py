import zipfile

from katana import units
from pwn import *

DEPENDENCIES = ['unzip']


class Unit(units.FileUnit):
    PRIORITY = 40
    ARGUMENTS = [
        {'name': 'zip_password',
         'type': list,
         'help': 'A password to try on a ZIP archive',
         'default': []
         }
    ]

    def __init__(self, katana, target):
        # This ensures it is a ZIP
        super(Unit, self).__init__(katana, target, keywords=['zip archive'])
        self.completed = True

    def enumerate(self, katana):
        yield ''

        for password in katana.config['zip_password']:
            yield password

        if 'dict' in katana.config and katana.config['dict'] is not None:
            katana.config['dict'].seek(0)
            for line in katana.config['dict']:
                yield line.rstrip('\n')

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

        p = subprocess.Popen(['unzip', '-P', password, self.target.path], cwd=directory_path,
                             stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        p.wait()

        for root, dirs, files in os.walk(directory_path):
            for name in files:
                path = os.path.join(root, name)
                katana.add_artifact(self, path)
                katana.recurse(self, path)
                self.completed = True

        return

        with zipfile.ZipFile(self.target.path) as z:
            name = z.namelist()[0]
            # self.artificate_dir()
            # Try to extract the file
            try:
                with z.open(name, 'r', bytes(password, 'utf-8')) as f:
                    pass
            except RuntimeError:
                # Password didn't work
                return None

            # We found the password

            # Look for flags in the extracted data
            for info in z.infolist():
                name, f = katana.create_artifact(self, name)
                with f:
                    with z.read(info, bytes(password, 'utf-8')) as zf:
                        for chunk in iter(lambda: zf.read(4096), b""):
                            f.write(chunk)

                katana.recurse(self, name)

            return True
