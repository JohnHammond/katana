"""
Extract PDF images

This unit retrieves the images included in a PDF document, 
using the "pdfimages" command-line tool.

"""

import os
import subprocess
from typing import Any

from katana.unit import FileUnit


class Unit(FileUnit):

    # Fill in your groups
    GROUPS = ["pdf"]
    BLOCKED_GROUPS = ["pdf"]
    # High priority if this is detected...
    PRIORITY = 25
    # Do not recurse into self
    RECURSE_SELF = False

    def __init__(self, *args, **kwargs):
        # This ensures it is a PDF
        super(Unit, self).__init__(*args, **kwargs, keywords=["pdf document"])

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
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
