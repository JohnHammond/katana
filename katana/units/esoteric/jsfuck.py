"""
JSFuck decoder

This unit will attempt to execute JSFuck and
look for flags in the result.



"""


import os
import subprocess
import re
from typing import Any

from katana.unit import NotEnglishUnit, NotApplicable


class Unit(NotEnglishUnit):

    GROUPS = ["esoteric", "jsfuck", "javascript"]
    """
    These are "tags" for a unit. Considering it is a Esoteric unit,
    "esoteric" is included, as well as the unit name "jsfuck", and
    the tag "javascript".
    """

    RECURSE_SELF = False
    """
    It would not make sense to recurse into ourself. We shouldn't get JSFuck 
    out.
    """

    DEPENDENCIES = ["node"]
    """
    Because this requires JavaScript code, ``node`` is a necessary binary
    dependency. 
    """

    PRIORITY = 60
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a moderately
    low priority because it requires an external tool.
    """

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        self.jsfuck = re.findall(rb"[\\[\\(\\)\\+!\]]{5,}", self.target.raw)
        if not self.jsfuck:
            raise NotApplicable("no jsfuck code found")

    def evaluate(self, case: Any):
        """
        Evaluate the target. Run the target as JSFuck code and
        return the evaluated source code to Katana.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        # First, get the location of the JS library that handles JSFuck...
        this_folder = os.path.dirname(os.path.realpath(__file__))
        jsfuck_lib = os.path.join(this_folder, "__jsfuck.js")

        # Now, process all of the JSFuck with node.
        for jsfuck in self.jsfuck:

            jsfuck = jsfuck.decode("utf-8")

            try:
                output = subprocess.Popen(
                    [
                        "node",
                        "-e",
                        "var lib = require('{0}'); lib.decode('{1}')".format(
                            jsfuck_lib, jsfuck
                        ),
                    ],
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                )
            except OSError:
                # This cannot run the command. Stop trying this unit!!
                return

            response = output.communicate()

            # If we got anything, add it as data!
            if response[0] != b"":
                response = response[0].decode("utf-8")
                self.manager.register_data(self, response)
