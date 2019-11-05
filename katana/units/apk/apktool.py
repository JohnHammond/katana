#!/usr/bin/env python3
import os
import subprocess
from typing import Any

from katana.manager import Manager
from katana.target import Target
from katana.unit import FileUnit


class Unit(FileUnit):
    # Fill in your groups
    GROUPS = ["apk"]
    # Default priority is 50
    PRIORITY = 40
    # We depend on `apktool`
    DEPENDENCIES = ["apktool"]

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target, keywords=["archive"])

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """

        # Run APK Tool
        path: str = self.get_output_dir()
        p = subprocess.Popen(
            ["apktool", "decode", "-f", self.target.path, "-o", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for completion
        p.wait()

        for (directory, dirs, files) in os.walk(os.path.join(path, "res")):
            dirs[:] = [d for d in dirs if d not in ["android"]]
            for filename in files:
                # Don't recurse on the apktool report
                if filename == "apktool.yml":
                    continue
                # Build the full path
                file_path = os.path.join(directory, filename)
                # Recurse on this target
                self.manager.queue_target(file_path, parent=self)
