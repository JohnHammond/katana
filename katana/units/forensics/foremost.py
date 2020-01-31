"""
Foremost file carving

This unit will run foremost to extract other files out of one given file

"""
from typing import Any
import subprocess
import zipfile
import os
import hashlib

from katana.unit import FileUnit

# Quick function to get the MD5 hash of a file
def md5sum(path):
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5


class Unit(FileUnit):

    # Groups we belong to
    GROUPS = ["forensics", "foremost"]

    # In case we have nested ZIPs, we CAN recurse into ourselves.
    RECURSE_SELF = True

    # Binary dependencies
    DEPENDENCIES = ["foremost"]

    # Moderately high priority due to speed and broadness of applicability
    PRIORITY = 30

    # Verify this is not a URL..
    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        if self.target.is_url and not self.target.url_accessible:
            raise NotApplicable("URL")

    def evaluate(self, case: str):

        # Grab the directory to store results
        foremost_directory = self.get_output_dir()

        # Run foremost on the given target
        p = subprocess.Popen(
            ["foremost", self.target.path, "-o", foremost_directory],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for foremost to finish
        p.wait()

        # Create a dictionary to keep track of the files
        results = {"extracted_files": []}

        # Inspect all the resulting files
        for (directory, _, files) in os.walk(foremost_directory):
            for filename in files:

                # Get the relative path
                file_path = os.path.join(directory, filename)
                path_hash = md5sum(file_path).hexdigest()

                # Don't recurse on the same file, or the foremost report
                if filename != "audit.txt" and self.target.hash != path_hash:
                    file_path = os.path.abspath(file_path)
                    self.manager.register_artifact(self, file_path)
                    results["extracted_files"].append(filename)

        # If we did extract things, save the filenames as part of our results
        if results["extracted_files"]:
            results["artifact_directory"] = foremost_directory
            self.manager.register_data(self, results)
