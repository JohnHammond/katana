"""
Crack a password-protected PDF

This unit attempt to unlock a password-protected PDF file. This is done
with the `PyPDF2` module in Python, which must be installed for this work.
First the unit will try with an empty password, and then it will try with
the user-supplied password argument. Finally, it will bruteforce with a 
supplied dictionary file. 

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a PDF file.

.. note::

    Note that it only (potentially) determines the password, but does nothing
    else with the file.

"""


from typing import Any
from PyPDF2 import PdfFileReader

from katana.unit import FileUnit, NotApplicable


class Unit(FileUnit):

    GROUPS = ["pdf", "pdfcrack"]
    """
    These are "tags" for a unit. Considering it is a pdf unit, "pdf"
    is included.
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

        # Check to see if this PDF is even password protected
        try:
            with open(self.target.path, "rb") as f:
                pdf = PdfFileReader(f)
                if not pdf.isEncrypted:
                    raise NotApplicable("pdf is not encrypted")
        except NotApplicable as e:
            # This is here to raise this NotApplicable up, in case it fails
            # before by opening the PDF file
            raise e
        except:
            raise NotApplicable("failed to open/read file")

    def enumerate(self):
        """
        This function will first yield an empty password, then the
        supplied password argument, then loop through each line of
        a provided dictionary file. The password will then be used by
        the ``evaluate`` function to try and open the encrypted PDF.
        """

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
        Evaluate the target. Attempt to open the PDF document with a supplied
        password given by ``enumerate``.

        :param case: A case returned by ``enumerate``. In this case, this \
        will be a string value supplied as an argument or bruteforce via \
        a supplied dictionary file.

        :return: None. This function should not return any data.
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
