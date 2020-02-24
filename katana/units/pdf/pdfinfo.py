"""
PDFInfo

This unit checks the PDF information of a given target, using the 
``pdfinfo`` command-line tool. You can optionally pass in arguments,
``user_password`` and ``owner_password`` to use with the utility.
The syntax is::

    pdfinfo <target_path> -upw <user_password> -opw <owner_password>

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a PDF file.

"""

import io
from typing import Any
import subprocess

from katana.unit import FileUnit


class Unit(FileUnit):

    GROUPS = ["pdf"]
    """
    These are "tags" for a unit. Considering it is a pdf unit, "pdf"
    is included.
    """

    BLOCKED_GROUPS = ["pdf"]
    """
    PDFs shouldn't come out of this. So no reason to look.
    """

    PRIORITY = 60
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a priority
    of 60.
    """

    RECURSE_SELF = False
    """
    Again no PDF from this. So recursion is silly.
    """

    DEPENDENCIES = ["pdfinfo"]
    """
    Required depenencies for this unit "pdfinfo"
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor is included just to provide a keyword for the
        ``FileUnit``, ensuring the provided target is in fact a PDF file.
        """

        super(Unit, self).__init__(*args, **kwargs, keywords=["pdf document"])

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target. Run ``pdfinfo`` on the target and
        recurse on any new found information.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
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
