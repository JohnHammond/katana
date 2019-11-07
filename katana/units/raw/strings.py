#!/usr/bin/env python3
from typing import Any
import subprocess

from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable
from katana.manager import Manager
from katana.target import Target


class Unit(BaseUnit):

    # This unit depends on the `strings` system binary
    DEPENDENCIES = ["strings"]
    # Moderately high priority due to speed and broadness of applicability
    PRIORITY = 30
    # Groups we belong to
    GROUPS = ["raw"]
    # Groups we can't recurse into
    # We block "decode" units, since they are capable of finding their targets within
    # a file by regular expression
    BLOCKED_GROUPS = ["decode"]

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

        if not self.target.is_file:
            raise NotApplicable("not a file")

    def evaluate(self, case: Any):

        # Run the process.
        command = ["strings", self.target.path, "-n", self.get("length", "10")]
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Queuing recursion and registering data can be slow on large files. Look for flags first
        lines = []
        for line in p.stdout:
            self.manager.find_flag(self, line)
            lines.append(line)

        for line in lines:
            self.manager.register_data(self, line.rstrip(b"\n"))
