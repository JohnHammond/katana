"""
Extract hidden data with ``steghide``

This unit will extract hidden data file using the ``steghide``
command-line utility. First the unit will try with an empty
password, and then it will try with the user-supplied password argument. 
Finally, it will bruteforce with a upplied dictionary file. 
The syntax runs as::

    steghide extract -sf <target_path> -p <password> -xf <steghide_directory>


The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a JPG file.

.. note::
    
    ``steghide`` only works on JPG files!

"""
import base64
import subprocess
import threading

from katana.unit import FileUnit


class Unit(FileUnit):

    DEPENDENCIES = ["steghide"]
    """
    Required depenencies for this unit "steghide"
    """

    PRIORITY = 20
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a high
    priority for matching files
    """

    GROUPS = ["stego", "image"]
    """
    These are "tags" for a unit. Considering it is a Stego unit, "stego"
    is included, as well as the tag "image".
    """

    def __init__(self, *args, **kwargs):

        super(Unit, self).__init__(katana, *args, **kwargs, keywords=["jpg ", "jpeg "])

        # Keep track of how many passwords we find (protected by lock)
        self.count_lock = threading.Lock()
        self.npasswords = 0
        self.max_passwords = self.geti("npasswd", 1)

    def enumerate(self):
        """
        This function will first yield an empty password, then the
        supplied password argument, then loop through each line of
        a provided dictionary file. The password will then be used by
        the ``evaluate`` function to try and open the encrypted PDF.
        """

        # The default is to check an empty password
        yield b""

        # Check a passed password
        if self.get("password") is not None:
            yield bytes(self.get("password"), "utf-8")

        # Check other passwords specified explicitly
        if self.get("passwords") is not None:
            for p in self.get("passwords", "").split(","):
                yield bytes(p, "utf-8")

        # Add all the passwords from the dictionary file
        if self.get("dict") is not None:
            # Read all of the dict
            with open(self.get("dict"), "rb") as fh:
                for line in fh:
                    line = line.rstrip(b"\n")
                    yield line

    def evaluate(self, password):
        """
        Evaluate the target. Extract any info with steghide and
        recurse on any new found files.

        :param case: A case returned by ``enumerate``. For this unit, \
        ``case`` will first be an empty password, then the password supplied \
        as an argument, then the contents of a provided dictionary file. 

        :return: None. This function should not return any data.
        """

        # Grab the output path for this target and password
        # CALEB: This is a race condition. Someone could create the file
        # before steghide does! We should pass create=True,
        # and then force steghide to overwrite
        if password == b"":
            output_path, _ = self.generate_artifact("no_password", create=False)
        else:
            output_path, _ = self.generate_artifact(
                base64.b64encode(password).decode("utf-8"), create=False
            )

        # Run steghide
        p = subprocess.Popen(
            [
                b"steghide",
                b"extract",
                b"-sf",
                self.target.path,
                b"-p",
                password,
                b"-xf",
                output_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for process completion
        p.wait()

        # Grab the output
        output = bytes.decode(p.stdout.read(), "ascii")
        error = bytes.decode(p.stderr.read(), "ascii")

        # Check if it succeeded
        if p.returncode != 0:
            return

        # Increment the number of found passwords
        with self.count_lock:
            self.npasswords += 1
            if self.npasswords > self.max_passwords:
                return

        # Register the new file with the manager
        self.manager.register_artifact(self, output_path)

        self.manager.register_data(
            self, {"password": repr(password)[2:-1]}, recurse=False
        )
