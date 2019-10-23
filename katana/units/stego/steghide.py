#!/usr/bin/env python3
import subprocess
import base64
import magic
import logging

from katana.unit import FileUnit, NotApplicable
from katana.manager import Manager
from katana.target import Target


class Unit(FileUnit):

    # Binary dependencies
    DEPENDENCIES = ["steghide"]
    # High priority for matching files
    PRIORITY = 20
    # Groups we're a member of
    GROUPS = ["stego", "image"]

    def __init__(self, katana, target):
        super(Unit, self).__init__(katana, target, keywords=["jpg ", "jpeg "])

        self.npasswords = 0
        self.max_passwords = self.manager[str(self)].getint("npasswd", 1)

    def enumerate(self):
        # The default is to check an empty password
        yield b""

        # Check other passwords specified explicitly
        if self.manager[str(self)].get("passwords") is not None:
            for p in self.manager[str(self)].get("passwords", "").split(","):
                yield bytes(p, "utf-8")

        # Add all the passwords from the dictionary file
        if self.manager[str(self)].get("dict") is not None:
            # Read all of the dict
            with open(self.manager[str(self)].get("dict"), "rb") as fh:
                for line in fh:
                    yield line.rstrip(b"\n")

    def evaluate(self, password):

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
        self.npasswords += 1
        if self.npasswords >= self.max_passwords:
            self.completed = True

        # Register the new file with the manager
        self.manager.register_artifact(self, output_path)
        self.manager.register_data(
            self, {"password": repr(password)[2:-1]}, recurse=False
        )
