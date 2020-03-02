"""
ZIP file extraction

This unit attempt to extract a ZIP file. First the unit will try with an empty
password, and then it will try with the user-supplied password argument. 
Finally, it will bruteforce with a upplied dictionary file. 
The process is done with a dependency, using the ``unzip`` command like so::

    unzip -P <password> <target_path>

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a ZIP file.

"""
from typing import Any
import subprocess
import zipfile
import os

from katana.unit import FileUnit


class Unit(FileUnit):

    GROUPS = ["zip", "office", "archive"]
    """
    These are "tags" for a unit. Considering it is a zip unit, "zip"
    is included, as well as a few other key words. 
    """

    RECURSE_SELF = True
    """
    In can case we have nested ZIPs, we can recurse into ourselves
    """

    DEPENDENCIES = ["unzip"]
    """
    This process is done with the ``unzip`` command because the Python
    method bottlenecks.
    """

    PRIORITY = 25
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a 
    moderately high priority due to speed and broadness of applicability
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor is included just to provide a keyword for the
        ``FileUnit``, ensuring the provided target is in fact a ZIP archive.
        """

        super(Unit, self).__init__(
            *args, **kwargs, keywords=["zip archive", "OpenDocument"]
        )

    def enumerate(self):
        """
        This function will first yield an empty password, then the
        supplied password argument, then loop through each line of
        a provided dictionary file. The password will then be used by
        the ``evaluate`` function to try and extract the ZIP fike.
        """

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
        """
        Evaluate the target. Extract the target with ZIP and
        recurse on any new found files.

        :param case: A case returned by ``enumerate``. For this unit, \
        ``case`` will first be an empty password, then the password supplied \
        as an argument, then the contents of a provided dictionary file. 

        :return: None. This function should not return any data.
        """

        password = case

        result = {"password": "", "namelist": []}

        # Create a directory to store the files in
        directory_path = self.get_output_dir()

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
