"""
Piet esoteric language

This unit inherits from the :class:`katana.unit.FileUnit` to ensure
that the target is in fact an image file.

This unit will extract the text returned by a given
Piet language image using the ``npiet`` command-line
utility. The syntax is::

    npiet -e 1000000 <target_path>

"""


import subprocess
from typing import Any

from katana.unit import FileUnit, NotApplicable


class Unit(FileUnit):

    GROUPS = ["esoteric", "npiet", "piet"]
    """
    These are "tags" for a unit. Considering it is a Esoteric unit,
    "esoteric" is included, as well as the unit name "npiet".
    """

    RECURSE_SELF = False
    """
    It would not make sense to recurse into ourself
    """

    DEPENDENCIES = ["npiet"]
    """
    Required depenencies for this unit "npiet"
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
        ``FileUnit``, ensuring the provided target is in fact an image.
        """
        super(Unit, self).__init__(*args, **kwargs, keywords=["image"])

    def evaluate(self, case: Any):
        """
        Evaluate the target. Run the ``npiet`` code and
        give the standard output results to Katana.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        # Run npiet against the image
        p = subprocess.Popen(
            ["npiet", "-e", "1000000", self.target.path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for the program to finish, or bail after 1 seconds
        try:
            p.wait(timeout=1)
        except subprocess.TimeoutExpired:
            # if the timeout happened, that's fine -- stop the process and continue
            p.kill()

        # Look for flags, add the results, and recurse on all output
        for line in p.stdout:
            self.manager.register_data(self, line)
