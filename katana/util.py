#!/usr/bin/env python3
import string


def isprintable(data) -> bool:
    """
    This is a convenience function to be used rather than the usual 
    ``str.printable`` boolean value, as that built-in **DOES NOT** consider
    newlines to be part of the printable data set (weird!)
    """

    if type(data) is str:
        data = data.encode("utf-8")
    for c in data:
        if c not in bytes(string.printable, "ascii"):
            return False

    return True


def is_good_magic(magic: str) -> bool:
    """ Checks if the magic type is in a list of known interesting file types
    """
    interesting_types = [
        "image",
        "document",
        "archive",
        "file",
        "database",
        "package",
        "binary",
        "video",
        "executable",
        "format",
        "certificate",
        "bytecode",
    ]

    for each_type in interesting_types:
        if each_type in magic:
            return True
    else:
        return False


def ellipsize(data: str, length: int = 64) -> str:
    """ Ellipsize the string with a max-length of 64 characters """
    if isinstance(data, bytes):
        data = repr(data)[2:-1]
    data = data.split("\n")[0]
    if len(data) > (length - 3):
        data = data[: length - 3] + "..."
    return data


def process_output(popen_object) -> dict:
    """
    This function expects a ``subprocess.Popen`` object, to read the standard
    output and standard error streams. It reads these line-by-line, stripping
    whitespace, and adds them to a ``results`` dictionary so it could be
    easily given back to Katana.
    """

    result = {"stdout": [], "stderr": []}

    output = bytes.decode(popen_object.stdout.read(), "latin-1")
    error = bytes.decode(popen_object.stderr.read(), "latin-1")

    for line in [l.strip() for l in error.split("\n") if l]:
        result["stderr"].append(line)
    for line in [l.strip() for l in output.split("\n") if l]:
        result["stdout"].append(line)

    if not len(result["stderr"]):
        result.pop("stderr")
    if not len(result["stdout"]):
        result.pop("stdout")

    if result != {}:
        return result
