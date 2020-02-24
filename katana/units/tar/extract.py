"""
TAR archive extraction

This is done with the built-in Python library ``tarfile``, so there is

Note that TAR files do not have support for passwords, so that is not 
implemented here. 

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a TAR archive.

"""
from typing import Any

import tarfile
import os

from katana.unit import FileUnit


class Unit(FileUnit):

    GROUPS = ["tar", "archive"]
    """
    The constructor is included just to provide a keyword for the
    ``FileUnit``, ensuring the provided target is in fact a TAR archive.
    """

    RECURSE_SELF = True
    """
    In case we have nested TARs, we CAN recurse into ourselves.
    """

    PRIORITY = 30
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a
    moderately high priority due to speed and broadness of applicability
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor is included just to provide a keyword for the
        ``FileUnit``, ensuring the provided target is in fact a TAR archive.
        """
        super(Unit, self).__init__(*args, **kwargs, keywords=[" tar archive"])

    def evaluate(self, case: str):
        """
        Evaluate the target. Extract the target with TAR and
        recurse on any new found files.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        # Retrieve the directory to store these in
        tar_directory = self.get_output_dir()

        # Open the tar file for reading
        tar = tarfile.open(self.target.path)

        # Extract all the files and recurse on them!
        for tarinfo in tar:
            tar.extract(tarinfo.name, path=tar_directory)
            abs_path = os.path.join(tar_directory, tarinfo.name)
            self.manager.register_artifact(self, abs_path)
