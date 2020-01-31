"""
tcpflow 

This unit will carve out files from a given PCAP file using the "tcpflow"
command-line utility.

"""
from typing import Any
import subprocess
import os
import hashlib

from katana.unit import FileUnit


class Unit(FileUnit):

    # Groups we belong to
    GROUPS = ["network", "pcap", "tcpflow"]

    # In case we have extract other PCAPs for some reason, we CAN recurse into ourselves.
    RECURSE_SELF = True

    # Binary dependencies
    DEPENDENCIES = ["tcpflow"]

    # Moderately high priority due to speed and broadness of applicability
    PRIORITY = 30

    # Verify this is not a URL..
    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs, keyword=["capture file", "pcap"])

        if self.target.is_url and not self.target.url_accessible:
            raise NotApplicable("URL")

    def evaluate(self, case: str):

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
