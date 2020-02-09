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

    # Groups we belong to
    GROUPS = ["esoteric", "jsfuck", "javascript"]

    # It would not make sense to recurse into ourself
    RECURSE_SELF = False

    # Binary dependencies
    DEPENDENCIES = ["node"]

    # Moderately high priority due to speed and broadness of applicability
    PRIORITY = 60

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        self.jsfuck = re.findall(rb"[\\[\\(\\)\\+!\]]{5,}", self.target.raw)
        if not self.jsfuck:
            raise NotApplicable("no jsfuck code found")

    def evaluate(self, case: Any):

        # First, get the location of the JS library that handles JSFuck...
        this_folder = os.path.dirname(os.path.realpath(__file__))
        jsfuck_lib = os.path.join(this_folder, "__jsfuck.js")

        # Now, process all of the JSFuck with node.
        for jsfuck in self.jsfuck:

            jsfuck = jsfuck.decode("utf-8")

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

            response = output.communicate()

            # If we got anything, add it as data!
            if response[0] != b"":
                response = response[0].decode("utf-8")
                self.manager.register_data(self, response)
