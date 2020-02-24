"""
Convert PDF to Text

This unit retrieves the text included in a PDF document, using the 
"pdftotext" Python library.

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a PDF file.
"""

import io
from typing import Any
import pdftotext

from katana.unit import FileUnit


class Unit(FileUnit):

    GROUPS = ["pdf", "pdftotext", "pdf2text"]
    """
    These are "tags" for a unit. Considering it is a pdf unit, "pdf"
    is included, and the name of the unit, "pdftotext"
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

        try:
            self.pdf = pdftotext.PDF(self.target.stream)
        except (AttributeError, pdftotext.Error):
            raise NotApplicable("cannot read pdf file")

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target. Extract the text out of the PDF document and
        recurse on any newfound text.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        for page in self.pdf:
            lines = page.split("\n")
            for line in lines:
                self.manager.register_data(self, line)
