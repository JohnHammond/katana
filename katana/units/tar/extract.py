"""
TAR archive extraction

Note that TAR files do not have support for passwords, so that is not implemented here.
"""
from typing import Any

import tarfile
import os

from katana.unit import FileUnit


class Unit(FileUnit):

    # Groups we belong to
    GROUPS = ["tar", "archive"]

    # In case we have nested TARs, we CAN recurse into ourselves.
    RECURSE_SELF = True

    # Moderately high priority due to speed and broadness of applicability
    PRIORITY = 30

    def __init__(self, *args, **kwargs):
        # This ensures it is a tar file. The leading space helps mitigate conflicts.
        super(Unit, self).__init__(*args, **kwargs, keywords=[" tar archive"])

    def evaluate(self, case: str):

        # Retrieve the directory to store these in
        tar_directory = self.get_output_dir()

        # Open the tar file for reading
        tar = tarfile.open(self.target.path)

        # Extract all the files and recurse on them!
        for tarinfo in tar:
            tar.extract(tarinfo.name, path=tar_directory)
            abs_path = os.path.join(tar_directory, tarinfo.name)
            self.manager.register_artifact(self, abs_path)
