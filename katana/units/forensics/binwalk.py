"""
Binwalk file carving

This unit will run binwalk to extract other files out of one given file

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
    GROUPS = ["forensics", "binwalk"]

    # In case we have nested ZIPs, we CAN recurse into ourselves.
    RECURSE_SELF = True

    # Binary dependencies
    DEPENDENCIES = ["binwalk"]

    # Moderately high priority due to speed and broadness of applicability
    PRIORITY = 30

    # Verify this is not a URL..
    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        if self.target.is_url and not self.target.url_accessible:
            raise NotApplicable("URL")

    def evaluate(self, case: str):

        binwalk_directory = self.get_output_dir()

        # Run binwalk on the target
        parms = [
            "binwalk",
            "-e",
            self.target.path,
            "--directory",
            binwalk_directory,
            "--dd=.*",
            "-M",
        ]
        p = subprocess.Popen(parms, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Wait for binwalk to finish
        if p.wait() != 0:
            # if it failed, clean and give up
            shutil.rmtree(binwalk_directory)
            return

        # Inspect all the resulting files
        for root, dirs, files in os.walk(binwalk_directory):
            for name in files:
                path = os.path.join(root, name)
                path = os.path.abspath(path)
                md5 = md5sum(path)
                # if this is a duplicate of the target, ignore and remove it
                if md5.hexdigest() == self.target.hash:
                    os.remove(os.path.join(root, name))
                else:
                    # Otherwise, check the new file that was created!
                    self.manager.register_artifact(self, path)
