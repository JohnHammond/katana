#!/usr/bin/env python3
from typing import Any
import subprocess
import logging

from katana.unit import FileUnit, NotApplicable
from katana.manager import Manager
from katana.target import Target
import katana.util


class Unit(FileUnit):
    # We depend on the system tool `exiftool`
    DEPENDENCIES = ["exiftool"]
    # Moderate-to-high priority
    PRIORITY = 40
    # Groups we belong to
    GROUPS = ["raw", "file"]

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

    def evaluate(self, case):

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

            # Don't recurse on this data, just save it for review and check for
            # flags
            self.manager.register_data(self, response, recurse=False)
