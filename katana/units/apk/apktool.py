"""

Decompile an APK file with ``apktool``.

This unit depends on the ``apktool`` external dependencies. It must
be within your ``$PATH`` for Katana to use it properly.

All this unit does is call the command

.. code-block:: bash

    apktool decode -f <the_target> -o <artifact_path>


It then looks through the results and queues each new file as targets 
to recurse on.

"""


import os
import subprocess
from typing import Any

from katana.manager import Manager
from katana.target import Target
from katana.unit import FileUnit


class Unit(FileUnit):

    # Fill in your groups
    GROUPS: list = ["apk"]

    # Default priority is 50
    PRIORITY: int = 40

    # We depend on `apktool`
    DEPENDENCIES: list = ["apktool"]

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target, keywords=["archive"])

    def evaluate(self, case: Any) -> None:
        """
        This ``evaluate`` function calls the command::

           apktool decode -f <the_target> -o <artifact_path>

        and loops through the results, queuing each new file as 
        a new target to recurse on.
        
        :param case: A case returned by ``enumerate``. For this unit, 
         the enumerate function is not used.
         
        :return: None. This function should not return any data.
        """

        # Grab the location to save results
        path: str = self.get_output_dir()

        # Run apktool
        p = subprocess.Popen(
            ["apktool", "decode", "-f", self.target.path, "-o", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for completion
        p.wait()

        # Loop through all the new files
        for (directory, dirs, files) in os.walk(os.path.join(path, "res")):
            dirs[:] = [d for d in dirs if d not in ["android"]]
            for filename in files:

                # Don't recurse on the apktool report
                if filename == "apktool.yml":
                    continue

                # Build the full path
                file_path: str = os.path.join(directory, filename)
                # Recurse on this target
                self.manager.queue_target(file_path, parent=self)
