"""
Extract metadata with ``exiftool``

This unit will extract metadata file using the ``exiftool``
command-line utility. The syntax runs as::

    exiftool <target_path>

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a file.

"""

from typing import Any
import subprocess
import logging

from katana.unit import FileUnit, NotApplicable
from katana.manager import Manager
from katana.target import Target
import katana.util


class Unit(FileUnit):

    DEPENDENCIES = ["exiftool"]
    """
    This unit needs the ``exiftool`` command-line tool to run.
    """

    PRIORITY = 40
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a
    moderate-to-high priority
    """

    GROUPS = ["raw", "file", "exiftool"]
    """
    These are "tags" for a unit. Considering it is a Raw unit, "raw" is 
    included, as well as the tag "file", and the name of the unit "exiftool".
    """

    def evaluate(self, case):
        """
        Evaluate the target. Run ``exiftool`` on the target and
        recurse on any newfound information.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        # Run exiftool on the target file
        p = subprocess.Popen(
            ["exiftool", self.target.path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Look for flags, if we found them...
        response = katana.util.process_output(p)
        if response:
            if "stdout" in response:
                for line in response["stdout"]:
                    delimited = line.split(":")
                    metadata = delimited[0].strip()
                    value = ":".join(delimited[1:]).strip()

                    # Most metadata won't have useful recursion data
                    # but these commonly do (e.g. Base64, caeser, etc)
                    if metadata in ["Comment", "Album", "Artist", "Title"]:
                        self.manager.queue_target(value, parent=self)

            # Don't recurse on this data, just save it for review and check
            # for flags
            self.manager.register_data(self, response, recurse=False)
