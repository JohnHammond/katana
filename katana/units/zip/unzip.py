#!/usr/bin/env python3
from typing import Any
import subprocess
import zipfile

from katana.unit import FileUnit

# JOHN: I started to work on converting this, but didn't get any where
#       because I could not seem to test it well.
#       At the time of writing, (Dec 1st 2019) it seems that specifying
#       a specific unit from the command-line would not work...?

class Unit(FileUnit):

	# Binary dependencies
	DEPENDENCIES = ["unzip"]

    # Moderately high priority due to speed and broadness of applicability
    PRIORITY = 40

    # Groups we belong to
    GROUPS = ["zip", "office", "archive"]

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target, keywords = ["zip archive", "OpenDocument"])

    def enumerate(self):
    	# the default is to try with no password
        yield ""

        for password in katana.config["zip_password"]:
            yield password

        if "dict" in katana.config and katana.config["dict"] is not None:
            katana.config["dict"].seek(0)
            for line in katana.config["dict"]:
                yield line.rstrip("\n")


    def evaluate(self, case: str):

        password = case
        result = {"password": "", "namelist": []}

        if isinstance(self.target.path, str):
            path = self.target.path
        else:
            path = self.target.path.decode("utf-8")
        directory_path, _ = katana.create_artifact(
            self, os.path.basename(path), create=True, asdir=True
        )

        p = subprocess.Popen(
            ["unzip", "-P", password, self.target.path],
            cwd=directory_path,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        p.wait()

        for root, dirs, files in os.walk(directory_path):
            for name in files:
                path = os.path.join(root, name)
                katana.add_artifact(self, path)
                katana.recurse(self, path)
                self.completed = True

        return