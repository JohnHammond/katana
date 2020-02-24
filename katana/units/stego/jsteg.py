"""
Extract hidden data with ``jsteg``

This unit will extract hidden data file using the ``jsteg``
command-line utility. The syntax runs as::

    jsteg reveal <target_path>

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a JPG file.

"""

import subprocess

from katana.manager import Manager
from katana.unit import FileUnit
from katana.target import Target
import katana.util


class Unit(FileUnit):

    DEPENDENCIES = ["jsteg"]
    """
    Required depenencies for this unit "jsteg"
    """

    PRIORITY = 30
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a higher
    priority for matching units
    """

    GROUPS = ["stego", "image", "jsteg"]
    """
    These are "tags" for a unit. Considering it is a Stego unit, "stego"
    is included, as well as the tag "image", and the unit name itself, 
    "jsteg".
    """

    def __init__(self, manager: Manager, target: Target):
        """
        The constructor is included just to provide a keyword for the
        ``FileUnit``, ensuring the provided target is in fact a JPG file.
        """
        super(Unit, self).__init__(manager, target, keywords=["jpg", "jpeg"])

    def evaluate(self, case):
        """
        Evaluate the target. Run ``jsteg`` on the target and
        recurse on any newfound information.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        # Run jsteg with our target
        p = subprocess.Popen(
            ["jsteg", "reveal", self.target.path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Look for flags, if we found them...
        response = katana.util.process_output(p)

        # Recurse on the individual lines
        if "stdout" in response:
            for line in response["stdout"]:
                self.manager.queue_target(line, parent=self)

        # Register the results as data for the output
        self.manager.register_data(self, response, recurse=False)
