"""
tcpflow 

This unit will carve out files from a given PCAP file using the ``tcpflow``
command-line utility. The syntax runs as::

    tcpflow -r <target_path> -o <tcpflow_directory>

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a PCAP file.

"""
from typing import Any
import subprocess
import os
import hashlib

from katana.unit import FileUnit


class Unit(FileUnit):

    GROUPS = ["network", "pcap", "tcpflow"]
    """
    These are "tags" for a unit. Considering it is a pcap unit, "pcap"
    is included, as well as the tag "network", and unit name "tcpflow"
    """

    RECURSE_SELF = True
    """
    In case we have extract other PCAPs for some reason, we CAN recurse into 
    ourselves.    
    """

    DEPENDENCIES = ["tcpflow"]
    """
    Required depenencies for this unit "tcpflow"
    """

    PRIORITY = 30
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a moderately
    high priority due to speed and broadness of applicability
    """

    # Verify this is not a URL..
    def __init__(self, *args, **kwargs):
        """
        The constructor is included just to provide a keyword for the
        ``FileUnit``, ensuring the provided target is in fact a PCAP file.
        """
        super(Unit, self).__init__(*args, **kwargs, keywords=["capture file", "pcap"])

        if self.target.is_url and not self.target.url_accessible:
            raise NotApplicable("URL")

    def evaluate(self, case: Any):
        """
        Evaluate the target. Run ``tcpflow`` on the target and
        recurse on any new found files.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        # Grab the directory to store results
        tcpflow_directory = self.get_output_dir()

        # Run tcpflow on the target
        p = subprocess.Popen(
            ["tcpflow", "-r", self.target.path, "-o", tcpflow_directory],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for tcpflow to finish
        p.wait()

        # Create a dictionary to keep track of our results
        results = {"extracted_files": []}

        # Loop through the extracted files
        for (directory, _, files) in os.walk(tcpflow_directory):
            for filename in files:

                # Get the relative path
                file_path = os.path.join(directory, filename)

                # Don't recurse on the same file, or the tcpflow report
                if filename != "report.xml":
                    self.manager.register_artifact(self, file_path)
                    results["extracted_files"].append(filename)

        # If we did get any results, add the data to tell the user
        if results["extracted_files"]:
            results["artifact_directory"] = tcpflow_directory
            self.manager.register_data(self, results)
