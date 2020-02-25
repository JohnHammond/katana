"""
Binwalk file carving

This unit will run ``foremost`` to extract other files out of one given file.
The syntax runs as::

    foremost <target_path> -o <foremost_directory>

"""

from typing import Any
import subprocess
import os
import hashlib

from katana.unit import FileUnit


def md5sum(path):
    """
    Quick convenience function to get the MD5 hash of a file
    """
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5


class Unit(FileUnit):

    GROUPS = ["forensics", "foremost"]
    """
    These are "tags" for a unit. Considering it is a Forensics unit,
    "forensics" is included, as well as the unit name "foremost".
    """

    RECURSE_SELF = False
    """
    Don't recurse into any of the extract objects. Binwalk should
    have carved them out already.
    """

    DEPENDENCIES = ["foremost"]
    """
    Required depenencies for this unit "foremost". This must be in
    your PATH to be executed.
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

    def evaluate(self, case: str):
        """
        Evaluate the target. Run ``foremost`` on the target and
        recurse on any new found files.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

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
