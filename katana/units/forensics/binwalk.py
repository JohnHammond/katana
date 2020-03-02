"""
Binwalk file carving

This unit will run ``binwalk`` to extract other files out of one given file.
The syntax runs as::

    binwalk -e <target_path> --directory <binwalk_directory> --dd=.* -M

"""

from typing import Any
import subprocess
import zipfile
import os
import hashlib
import shutil

from katana.unit import FileUnit


def md5sum(path: str) -> hashlib.md5:
    """
    Quick convenience function to get the MD5 hash of a file
    """
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5


class Unit(FileUnit):

    GROUPS = ["forensics", "binwalk", "carver"]
    """
    These are "tags" for a unit. Considering it is a Forensics unit,
    "forensics" is included, as well as the unit name "binwalk".
    """

    RECURSE_SELF = False
    """
    Don't recurse into any of the extract objects. Binwalk should
    have carved them out already.
    """

    DEPENDENCIES = ["binwalk"]
    """
    Required depenencies for this unit "binwalk". This must be in
    your PATH to be executed.
    """

    BLOCKED_GROUPS = ["carver"]
    """
    Groups which this unit cannot recurse into.
    """

    PRIORITY = 30
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a moderately
    high priority due to speed and broadness of applicability
    """

    # Verify this is not a URL..
    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        if self.target.is_url and not self.target.url_accessible:
            raise NotApplicable("URL")

    def evaluate(self, case: Any):
        """
        Evaluate the target. Run ``binwalk`` on the target and
        recurse on any new found files.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

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
