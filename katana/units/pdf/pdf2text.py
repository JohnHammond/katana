"""
Convert PDF to Text

This unit retrieves the text included in a PDF document, using the 
"pdftotext" Python library.

"""

import io
from typing import Any
import pdftotext

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

        try:
            self.pdf = pdftotext.PDF(self.target.stream)
        except (AttributeError, pdftotext.Error):
            raise NotApplicable("cannot read pdf file")

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """

        for page in self.pdf:
            lines = page.split("\n")
            for line in lines:
                self.manager.register_data(self, line)
