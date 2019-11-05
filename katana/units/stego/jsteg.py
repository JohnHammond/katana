#!/usr/bin/env python3
import subprocess

from katana.manager import Manager
from katana.unit import FileUnit
from katana.target import Target
import katana.util


class Unit(FileUnit):

    # Binary dependencies
    DEPENDENCIES = ["jsteg"]
    # Higher priorities for matching units
    PRIORITY = 30
    # Groups we belong to
    GROUPS = ["stego", "image"]

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target, keywords=["jpg", "jpeg"])

    def evaluate(self, case):

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
