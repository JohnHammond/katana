"""
PDFInfo

This unit checks the PDF information of a given target, using the 
"pdfinfo" command-line tool. You can optionally pass in arguments,
"user_password" and "owner_password" to use with the utility.

"""

import io
from typing import Any
import subprocess

from katana.unit import FileUnit


class Unit(FileUnit):

    # Fill in your groups
    GROUPS = ["pdf"]
    BLOCKED_GROUPS = ["pdf"]
    # Default priority is 50
    PRIORITY = 60
    # Do not recurse into self
    RECURSE_SELF = False

    # This requires the pdfinfo tool
    DEPENDENCIES = ["pdfinfo"]

    def __init__(self, *args, **kwargs):
        # This ensures it is a PDF
        super(Unit, self).__init__(*args, **kwargs, keywords=["pdf document"])

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """

        # Get passwords by the arguments, if they are passed in...
        user_password = self.get("user_password", default="")
        owner_password = self.get("owner_password", default="")

        # Run the utility
        p = subprocess.Popen(
            [
                "pdfinfo",
                self.target.path,
                "-upw",
                user_password,
                "-opw",
                owner_password,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for the process to finish
        p.wait()

        for line in p.stdout.readlines():
            self.manager.register_data(self, line.rstrip(b"\n"))
