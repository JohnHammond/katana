#!/usr/bin/env python3
from hashlib import md5
import subprocess

from katana.unit import NotApplicable, FileUnit
from katana.manager import Manager
from katana.target import Target
import katana.units


class Unit(FileUnit):

    # Binary dependencies
    DEPENDENCIES = ["snow"]
    # Higher priority for matching files
    PRIORITY = 30
    # Groups we belong to
    GROUPS = ["stego", "image"]

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

    def evaluate(self, case):

        # Run snow on the target
        p = subprocess.Popen(
            ["snow", self.target.path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Initialize
        response = None

        # Look for flags, if we found them...
        try:
            response = katana.util.process_output(p)
        except UnicodeDecodeError:

            # This probably isn't plain text....
            p.stdout.seek(0)
            output = p.stdout.read()

            # So consider it is some binary output and try and handle it.
            path, fh = self.generate_artifact(
                f"output_{md5(self.target).hexdigest()}", mode="wb"
            )

            # Write data and close descriptor
            with fh:
                fh.write(output)

            # Register the artifact
            self.manager.register_artifact(self, path)

        # Check result for processed output
        if response is not None:
            if "stdout" in response:
                # If we see anything interesting in here... scan it again!
                for line in response["stdout"]:
                    self.manager.queue_target(line, parent=self)

            # Register data as results
            self.manager.register_data(self, response)
