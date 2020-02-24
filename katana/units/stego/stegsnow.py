"""
Extract hidden data with ``stegsnow``

This unit will extract hidden data file using the ``steghide``
command-line utility. First the unit will try with an empty
password, and then it will try with the user-supplied password argument. 
Finally, it will bruteforce with a upplied dictionary file. 
The syntax runs as::

    stegsnow -C -p  <password> <target_path>


The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a file.


"""

from hashlib import md5
import subprocess
import regex as re

from katana.unit import FileUnit, NotApplicable
import katana.util

PASSWORD_PATTERN = rb"password\s*(is)?\s*[:=]\s*(\S+)\s*"
PASSWORD_REGEX = re.compile(PASSWORD_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)


class Unit(FileUnit):

    DEPENDENCIES = ["stegsnow"]
    """
    Required depenencies for this unit "stegsnow"
    """

    PRIORITY = 30
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a higher
    priority for matching files
    """

    GROUPS = ["stego", "bruteforce", "password", "stegsnow"]
    """
    These are "tags" for a unit. Considering it is a stego unit, "stego"
    is included, as well as the tags "bruteforce", "password", and the name
    of the unit itself, "stegsnow".
    """

    def enumerate(self):
        """
        This function will first yield an empty password, then the
        supplied password argument, then loop through each line of
        a provided dictionary file. The password will then be used by
        the ``evaluate`` function to try and open the encrypted PDF.
        """

        # The default is to check an empty password
        yield ""

        # Check other passwords specified explicitly
        for p in self.get("passwords", "").split(","):
            yield p

        # Add all the passwords from the dictionary file
        if self.get("dict") is not None:
            with open(self.get("dict"), "wb") as fh:
                yield line.rstrip(b"\n")

    def evaluate(self, case):
        """
        Evaluate the target. Extract any info with steghide and
        recurse on any new found files.

        :param case: A case returned by ``enumerate``. For this unit, \
        ``case`` will first be an empty password, then the password supplied \
        as an argument, then the contents of a provided dictionary file. 

        :return: None. This function should not return any data.
        """

        # Run stegsnow on the target
        p = subprocess.Popen(
            ["stegsnow", "-C", "-p", case, self.target.path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Look for flags, if we found them...
        try:
            response = None
            response = katana.util.process_output(p)
        except UnicodeDecodeError:

            # This probably isn't plain text....
            p.stdout.seek(0)
            result = p.stdout.read()

            # So consider it is some binary output and try and handle it.
            aritfact_path, artifact = self.generate_artifact(
                f"output_{md5(self.target).hexdigest()}", mode="wb"
            )
            artifact.write(result)
            artifact.close()

            # Register the result
            self.manager.register_artifact(self, artifact_path)

        if response is not None:
            if "stdout" in response:
                # If we see anything interesting in here... scan it again!
                for line in response["stdout"]:
                    self.manager.queue_target(line, parent=self)

            self.manager.register_data(self, response)
