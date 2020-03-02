"""
Extract hidden data with ``zsteg``

This unit will extract hidden data file using the ``zsteg``
command-line utility. The syntax runs as::

    zsteg <arguments> <target_path>

This unit will use only preselected arguments to search with ``zsteg``. 
This saves processing time, and still seems to find the majority of flags.

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a PNG file.

.. note::
    
    ``zsteg`` only works with PNG files!

"""

from typing import Generator, Any

from katana.unit import FileUnit

import subprocess


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
"""
This is a pre-defined list of argument to use with ``zsteg``. These options
tend to find flags hidden with the LSB steganography technique. 
"""


class Unit(FileUnit):

    DEPENDENCIES = ["zsteg"]
    """
    Depends on the binary "zsteg". This must be in your PATH for this unit
    to run.
    """

    GROUPS = ["stego", "image", "zsteg"]
    """
    These are "tags" for a unit. Considering it is a Stego unit, "stego"
    is included, as well as the tag "image", and the name of the unit itself,
    "zsteg".
    """

    PRIORITY = 40
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a slightly
    higher priority of 40.
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor is included just to provide a keyword for the
        ``FileUnit``, ensuring the provided target is in fact a PNG file.
        """
        super(Unit, self).__init__(*args, **kwargs, keywords=["png"])

    def enumerate(self) -> Generator[Any, None, None]:
        """
        This will loop through a set of pre-defined arguments for 
        ``zsteg`` to run with.
        
        :return: Generator of ``zsteg`` arguments
        """

        for args in permutations:
            yield args

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target. Run ``zsteg`` on the target and
        recurse on any newfound information.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``case`` is an argument to use for ``zsteg``. 

        :return: None. This function should not return any data.
        """

        # Run zsteg with the given arguments
        p = subprocess.Popen(
            ["zsteg", self.target.path, case],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Create a variable to store the results in
        result = {"stdout": [], "stderr": []}

        # Capture the results from the process
        # output = bytes.decode(p.stdout.read(), "ascii")
        # error = bytes.decode(p.stderr.read(), "ascii")
        output = p.stdout.read()
        error = p.stderr.read()

        # zsteg does buffers output, so we need to clean those
        # unused status lines. The code below removes them.
        delimeter = b"\r"
        cleaned_output = [line.strip() for line in output.split(b"\n") if line]
        cleaned_errors = [line.strip() for line in error.split(b"\n") if line]

        # First, clean out the actual stdout results
        for line in cleaned_output:

            status_lines = [
                segment + delimeter for segment in line.split(delimeter) if segment
            ]

            for temp_line in status_lines:
                # this conditions determines whether or not if it was actually
                # a bad status output
                if not temp_line.endswith(b".. \r"):

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
        if not len(result["stdout"]) or b"[=] nothing :(\r" in result["stdout"]:
            result.pop("stdout")

        # Report the results
        self.manager.register_data(self, result)
