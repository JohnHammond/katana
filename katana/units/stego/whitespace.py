"""
Extract hidden data with Whitespace steganography.

This unit will extract hidden data file treating spaces as a binary 0,
tabs as a binary 1, and vice versa.

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is a file.

"""
import binascii
import regex as re

from katana.unit import FileUnit, NotApplicable
import katana.util


def decode_from_whitespace(binary_sequence: str) -> str:
    """
    This is a convenience function to decode a binary sequence.

    :param binary_sequence: A string of 1's and 0's.

    :return: The converted data
    """
    decoded = int(binary_sequence, 2)
    decoded = hex(decoded)[2:].replace("L", "")
    try:
        decoded = binascii.unhexlify(decoded)
    except binascii.Error:
        decoded = binascii.unhexlify("0" + decoded)
    except UnicodeDecodeError:
        return None

    return decoded


class Unit(FileUnit):

    PRIORITY = 75
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a moderate
    priority.
    """

    GROUPS = ["stego", "whitespace"]
    """
    These are "tags" for a unit. Considering it is a Stego unit, "stego"
    is included, and the name of the unit itself, "whitespace".
    """

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)
        """
        The constructor is included just to provide a keyword for the
        ``FileUnit``, ensuring the provided target is a file. This
        also validates if there tabs or spaces found inside the target.
        """

        self.space_pieces = re.findall(b"[ \t]+", self.target.raw)

        if self.space_pieces is None or self.space_pieces == []:
            raise NotApplicable("no spaces found")

    def evaluate(self, case):
        """
        Evaluate the target. Convert anything that could potentially be
        whitespace steganography and pass it to Katana.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.

        """

        # First, retrieve all the spaces and make them in a binary sequence.
        pieces = []
        for piece in self.space_pieces:
            string_piece = piece
            binary = string_piece.replace(b"\t", b"1")
            binary = binary.replace(b" ", b"0")

            pieces.append(binary)

        # Decode the first method, and recurse/add_results on those...
        final_binary = b"".join(pieces)

        decoded = decode_from_whitespace(final_binary)
        if decoded:
            self.manager.register_data(self, decoded)

        # Then try again, hotswapping the 1's and 0's.
        final_binary.replace(b"0", b"@")
        final_binary.replace(b"1", b"0")
        final_binary.replace(b"@", b"1")

        decoded = decode_from_whitespace(final_binary)
        if decoded:
            self.manager.register_data(self, decoded)
