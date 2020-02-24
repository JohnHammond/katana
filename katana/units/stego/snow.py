"""
Extract hidden data with ``snow``

This unit will extract hidden data file using the ``snow``
command-line utility. The syntax runs as::

    snow <target_path>

You can read more about the ``snow`` tool at the homepage, here: 
http://www.darkside.com.au/snow/

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a file.

"""


from hashlib import md5
import subprocess

from katana.unit import NotApplicable, FileUnit
import katana.units


class Unit(FileUnit):

    DEPENDENCIES = ["snow"]
    """
    Required depenencies for this unit "snow"
    """

    PRIORITY = 30
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a higher
    priority for matching files
    """

    GROUPS = ["stego", "text", "snow"]
    """
    These are "tags" for a unit. Considering it is a Stego unit, "stego"
    is included, as well as the tag "text" and the name of unit itself,
    "snow".
    """

    def evaluate(self, case):
        """
        Evaluate the target. Run ``snow`` on the target and
        recurse on the standard output.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

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
