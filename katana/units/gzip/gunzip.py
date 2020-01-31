"""
GZIP file extraction

"""
from typing import Any

import gzip
import os

from katana.unit import FileUnit


class Unit(FileUnit):

    # Groups we belong to
    GROUPS = ["gzip", "archive"]

    # In case we have nested GZIPs, we CAN recurse into ourselves.
    RECURSE_SELF = False

    # Moderately high priority due to speed and broadness of applicability
    PRIORITY = 30

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs, keywords=["gzip compressed"])

    def evaluate(self, case: str):

        # Open the gzipped data
        with gzip.open(self.target.path, "rb") as gz:

            # Create a file for it, and write to it!
            name, f = self.generate_artifact("gunzip_data", mode="wb")
            with f:
                for chunk in iter(lambda: gz.read(4096), b""):
                    f.write(chunk)

        # Recurse on the new file
        name = os.path.abspath(name)
        self.manager.register_artifact(self, name)
