"""
Extract PDF images

This unit retrieves the images included in a PDF document, 
using the ``pdfimages`` command-line tool. The syntax is::

    pdfimage -png <target_path> <pdfimages_directory>

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a PDF file.

"""

import os
import subprocess
from typing import Any

from katana.unit import FileUnit


class Unit(FileUnit):

    GROUPS = ["pdf", "pdfimages"]
    """
    These are "tags" for a unit. Considering it is a pdf unit, "pdf"
    is included, and the name of this unit "pdfimages".
    """

    BLOCKED_GROUPS = ["pdf"]
    """
    PDFs shouldn't come out of this. So no reason to look.
    """

    PRIORITY = 25
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a high
    priority if this is detected...
    """

    RECURSE_SELF = False
    """
    Again no PDF from this. So recursion is silly.    
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor is included just to provide a keyword for the
        ``FileUnit``, ensuring the provided target is in fact a PDF file.
        """

        super(Unit, self).__init__(*args, **kwargs, keywords=["pdf document"])

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target. Run ``pdfimages`` on the target and
        recurse on any new found files.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        # Get the path name of the target
        if isinstance(self.target.path, str):
            path = self.target.path

        else:
            path = self.target.path.decode("utf-8")

        # Create a directory to store the images in
        directory_path = self.get_output_dir()

        # Run the tool to carve out the images
        p = subprocess.Popen(
            [
                "pdfimages",
                "-png",
                self.target.path,
                os.path.join(directory_path, "image"),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for the tool to finish
        p.wait()

        # Loop through the files and recurse on them
        for (directory, _, files) in os.walk(directory_path):
            for filename in files:
                file_path = os.path.join(directory, filename)
                self.manager.register_artifact(self, file_path)
