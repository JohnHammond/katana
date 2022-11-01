#!/usr/bin/env python3
import string
import magic
from collections import Counter

def freq_analysis(content):
    c = Counter(content)
    return c.most_common()
    
def maybe_text(content, freq=None):
    if freq is None:
        freq = freq_analysis(content)
    s = set([e[0].lower() for e in freq[:20]])
    tf = {'r', '\n', 'n', 'y', 'd', 'c', 'i', 'l', 'f', 'u', 'g', 'p', ' ', 't', 'o', 'h', 'a', 's', 'm', 'e'}
    return len(s & tf) > len(tf) / 0.5

def maybe_l33t(content, freq=None):
    if freq is None:
        freq = freq_analysis(content)
    s = set([e[0].lower() for e in freq[:20]])
    tf = {'r', 'n', 'y', 'd', 'c', '1', 'l', 'f', 'u', 'g', 'p', '_', 't', '0', 'h', '4', 's', 'm', '3'}
    return len(s & tf) > len(tf) / 0.5


def isprintable(data) -> bool:
    """
    This is a convenience function to be used rather than the usual 
    ``str.printable`` boolean value, as that built-in **DOES NOT** consider
    newlines to be part of the printable data set (weird!)
    """

    if type(data) is str:
        data = data.encode("utf-8")
    for c in set(data):
        if chr(c) not in string.printable:
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
        if each_type in magic.lower():
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

def is_interesting(data: str):
    # longer than flg{}
    if len(data) < 6:
        return False

    # Keep it if it is printable
    if isprintable(data):
        return True

    # Only check if file at least half a Kb
    elif len(data) > 512:
        # if not printable, we might only want it if it is a file.
        magic_info = magic.from_buffer(data)
        if is_good_magic(magic_info):
            return True
    return False