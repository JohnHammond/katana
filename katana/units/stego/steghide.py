import base64
import subprocess

import magic
from katana import units

DEPENDENCIES = ['steghide']


class Unit(units.FileUnit):
    PRIORITY = 20

    def __init__(self, katana, target):
        super(Unit, self).__init__(katana, target, keywords=['jpg ', 'jpeg '])

    def enumerate(self, katana):
        # The default is to check an empty password
        yield ''

        # Check other passwords specified explicitly
        for p in katana.config['password']:
            yield p

        # Add all the passwords from the dictionary file
        if 'dict' in katana.config and katana.config['dict'] is not None:
            # CALEB: Possible race condition if two units use the 'dict' argument for the same purpose...
            katana.config['dict'].seek(0)
            for line in katana.config['dict']:
                yield line.rstrip(b'\n')

    def evaluate(self, katana, password):

        # Grab the output path for this target and password
        # CALEB: This is a race condition. Someone could create the file
        #			before steghide does! We should pass create=True,
        #			and then force steghide to overwrite
        if password == "":
            output_path, _ = katana.create_artifact(self, "no_password", create=False)
        else:
            output_path, _ = katana.create_artifact(self, base64.b64encode(password).decode('utf-8'), create=False)

        # Run steghide
        p = subprocess.Popen(
            [b'steghide', b'extract', b'-sf', self.target.path, b'-p', password, b'-xf', output_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Wait for process completion
        p.wait()

        # Grab the output
        output = bytes.decode(p.stdout.read(), 'ascii')
        error = bytes.decode(p.stderr.read(), 'ascii')

        # Check if it succeeded
        if p.returncode != 0:
            return None

        katana.add_artifact(self, output_path)

        # Grab the file type
        typ = magic.from_file(output_path)
        thing = '<BINARY_DATA>'

        with open(output_path) as f:
            thing = f.read()

        katana.locate_flags(self, thing)

        katana.recurse(self, output_path)

        katana.add_results(self, {
            'file': output_path,
            'type': typ
        })
