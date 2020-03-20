"""
ltrace extraction for strcmp and other functions

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a ELF binary.

"""
from typing import Any

import os
import stat

from katana.unit import FileUnit
import subprocess
import shlex


class Unit(FileUnit):

    GROUPS = ["elf", "rev", "reverse", "reversing", "ltrace"]
    """
    The constructor is included just to provide a keyword for the
    ``FileUnit``, ensuring the provided target is in fact a TAR archive.
    """

    RECURSE_SELF = False
    """
    In case we have nested TARs, we CAN recurse into ourselves.
    """

    PRIORITY = 20
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a
    moderately high priority due to speed and specific applicability
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor is included just to provide a keyword for the
        ``FileUnit``, ensuring the provided target is in fact an ELF executable.
        """
        super(Unit, self).__init__(*args, **kwargs, keywords=["ELF"])

    def evaluate(self, case: str):
        """
        Evaluate the target. Extract the target with TAR and
        recurse on any new found files.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        # Force the target executable
        st = os.stat(self.target.path)
        os.chmod(self.target.path, st.st_mode | stat.S_IEXEC)

        # Run ltrace on the target
        p = subprocess.Popen(
            ["ltrace", shlex.quote(self.target.path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Send garbage input to the program
        info = p.communicate(b"anything\n", timeout=1)

        # Recurse on and search for flags in the result
        for line in info:
            self.manager.register_data(self, line)
