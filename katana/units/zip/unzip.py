"""
ZIP file extraction

This unit can take an argument, "password", which can be used to
extract the zip file if it is known. 

"""
from typing import Any
import subprocess
import zipfile
import os

from katana.unit import FileUnit


class Unit(FileUnit):

    # Groups we belong to
    GROUPS = ["zip", "office", "archive"]

    # In case we have nested ZIPs, we CAN recurse into ourselves.
    RECURSE_SELF = True

    # Binary dependencies
    DEPENDENCIES = ["unzip"]

    # Moderately high priority due to speed and broadness of applicability
    PRIORITY = 40

    def __init__(self, *args, **kwargs):

        super(Unit, self).__init__(
            *args, **kwargs, keywords=["zip archive", "OpenDocument"]
        )

    def enumerate(self):

        # the default is to try with no password
        yield ""

        # if they supply a password, use it
        if self.get("password"):
            yield self.get("password")

        # if they supply a dictionary to look through, use each of those!
        if self.get("dict"):
            with open(self.get("dict"), "rb") as handle:
                for line in handle:
                    yield line.rstrip(b"\n")

    def evaluate(self, case: str):

        password = case

        result = {"password": "", "namelist": []}

        if isinstance(self.target.path, str):
            path = self.target.path

        else:
            path = self.target.path.decode("utf-8")

        directory_path, _ = self.generate_artifact(
            name=os.path.basename(path), mode="w", create=True, asdir=True
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
                result["namelist"].append(name)
                path = os.path.join(root, name)
                self.manager.register_artifact(self, path)

        self.manager.register_data(self, result)
