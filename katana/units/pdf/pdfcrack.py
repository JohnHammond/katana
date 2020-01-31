"""
Extract PDF images

This unit retrieves the images included in a PDF document, 
using the "pdfimages" command-line tool.

"""


from typing import Any
from PyPDF2 import PdfFileReader

from katana.unit import FileUnit, NotApplicable


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

        # Check to see if this PDF is even password protected
        try:
            with open(self.target.path, "rb") as f:
                pdf = PdfFileReader(f)
                if not pdf.isEncrypted:
                    raise NotApplicable("pdf is not encrypted")
        except NotApplicable as e:
            # This is here to raise this NotApplicable up, in case it fails before by opening the PDF file
            raise e
        except:
            raise NotApplicable("failed to open/read file")

    def enumerate(self, katana):

        # The default is to check an empty password
        yield b""

        # if they supply a password, use it
        if self.get("password"):
            yield self.get("password")

        # if they supply a dictionary to look through, use each of those!
        if self.get("dict"):
            with open(self.get("dict"), "rb") as handle:
                for line in handle:
                    yield line.rstrip(b"\n")

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """

        with open(self.target.path, "rb") as f:
            pdf = PdfFileReader(f)

            try:
                password = password.decode("utf-8")
            except AttributeError:
                pass
            except UnicodeDecodeError:
                # Apparently, pdf can't handle bytes passwords...
                return

            if pdf.decrypt(password):
                self.manager.register_data(
                    self, "{0}: {1}".format(self.target.path, password)
                )
