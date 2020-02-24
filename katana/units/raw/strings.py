"""
Parse plaintext strings from a file with the ``strings`` command-line tool.

You can supply a minimum length of the data that ``strings`` will return
as an argument ``length``. The syntax of the command being run is::

    strings <target_path> -n <length_argument>

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a file.

"""

from typing import Any
import subprocess

from katana.unit import FileUnit, NotApplicable
from katana.manager import Manager
from katana.target import Target


class Unit(FileUnit):

    DEPENDENCIES = ["strings"]
    """
    Required depenencies for this unit "strings"
    """

    PRIORITY = 50
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a moderately
    high priority due to speed and broadness of applicability
    """

    GROUPS = ["raw", "strings"]
    """
    These are "tags" for a unit. Considering it is a Raw unit, "raw"
    is included, and the name of this unit itself "strings".
    """

    BLOCKED_GROUPS = ["decode"]
    """
    THis unit does not recurse to "decode" units, since they are capable of 
    finding their targets within a file by regular expression
    """

    def evaluate(self, case: Any):
        """
        Evaluate the target. Run ``strings`` on the target and
        recurse on any newfound information.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        # Run the process.
        command = ["strings", self.target.path, "-n", self.get("length", "10")]
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Queuing recursion and registering data can be slow on large files.
        # Look for flags first
        lines = []
        for line in p.stdout:
            self.manager.find_flag(self, line)
            lines.append(line)

        for line in lines:
            self.manager.register_data(self, line.rstrip(b"\n"))
