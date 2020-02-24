"""
GZIP file extraction

This unit works via the built-in Python library ``gzip``, so there is
no need for an external binary dependency.

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a GZIP file.

Note that GZIP files do not have support for passwords, so that is not implemented here.
"""
from typing import Any

import gzip
import os

from katana.unit import FileUnit


class Unit(FileUnit):

    GROUPS = ["gzip", "archive"]
    """
    These are "tags" for a unit. Considering it is a GZIP unit, "gzip"
    is included, as well as the tag "archive".
    """

    RECURSE_SELF = True
    """
    This unit can recurse into itself because we can end up with nested
    GZIPS.
    """

    PRIORITY = 30
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a moderately
    high priority due to speed and broadness of applicability
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor is included just to provide a keyword for the
        ``FileUnit``, ensuring the provided target is in fact a GZIP archive.
        """
        super(Unit, self).__init__(*args, **kwargs, keywords=["gzip compressed"])

    def evaluate(self, case: str):
        """
        Evaluate the target. Extract the target with GZIP and
        recurse on any new found files.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

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
