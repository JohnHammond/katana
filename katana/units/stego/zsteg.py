#!/usr/bin/env python3

from typing import Generator, Any

from katana.manager import Manager
from katana.target import Target
from katana.unit import FileUnit

import subprocess

# Use this listing for zsteg arguments.
permutations = [
    "b1,rgb,lsb,xy",
    "b1,r,lsb,xy",
    "b1,rgb,msb,yx",
    "b2,rgb,lsb,yx",
    "b2,rgb,lsb,xy",
    "b1,rgba,lsb,xy",
    "b1,r,lsb,xy",
    "b1,rgba,msb,yx",
    "b2,rgba,lsb,yx",
    "b2,rgba,lsb,xy",
    "b1,rgb,lsb,xy",
]


class Unit(FileUnit):

    # Binary dependencies
    DEPENDENCIES = ["zsteg"]
    # Fill in your groups
    GROUPS = ["stego", "image"]
    # Default priority is 50
    PRIORITY = 40

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target, keywords=["png"])

    def enumerate(self) -> Generator[Any, None, None]:
        """
        Yield unit cases
        :return: Generator of target cases
        """

        for args in permutations:
            yield args

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        :param case: A case returned by evaluate
        :return: None
        """

        # Run zsteg with the given arguments
        p = subprocess.Popen(
            ["zsteg", self.target.path, case],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Create a variable to store the results in
        result = {
            "stdout": [],
            "stderr": [],
        }

        # Capture the results from the process
        output = bytes.decode(p.stdout.read(), "ascii")
        error = bytes.decode(p.stderr.read(), "ascii")

        # zsteg does buffers output, so we need to clean those
        # unused status lines. The code below removes them.
        delimeter = "\r"
        cleaned_output = [line.strip() for line in output.split("\n") if line]
        cleaned_errors = [line.strip() for line in error.split("\n") if line]

        # First, clean out the actual stdout results
        for line in cleaned_output:

            status_lines = [
                segment + delimeter for segment in line.split(delimeter) if segment
            ]

            for temp_line in status_lines:
                # this conditions determines whether or not if it was actually
                # a bad status output
                if not temp_line.endswith(".. \r"):

                    # for this unit. we look for flags manually DURING the
                    # execution and processing, just in case something comes
                    # up and the rest of the code takes a long time to run.
                    if self.manager.find_flag(self, temp_line):
                        return
                    result["stdout"].append(temp_line)

        # Second, clean out the stderr results
        for line in cleaned_errors:
            if self.manager.find_flag(self, line):
                return
            result["stderr"].append(line)

        # Finally, if THERE WERE NOT results found in a specific stream
        # (stdout or stderr), remove those keys from the results dictionary
        if not len(result["stderr"]):
            result.pop("stderr")
        if not len(result["stdout"]) or "[=] nothing :(\r" in result["stdout"]:
            result.pop("stdout")

        # Report the output of the file.
        self.manager.register_data(self, result)

    # raise RuntimeError("No evaluate method defined!")

    @classmethod
    def validate(cls, manager: Manager) -> None:
        """
        Stub to validate configuration parameters
        :param manager: Katana manager
        :return: None
        """
        super(Unit, cls).validate(manager)
