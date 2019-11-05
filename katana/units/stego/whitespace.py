#!/usr/bin/env python3
import binascii
import regex as re

from katana.unit import FileUnit, NotApplicable
from katana.manager import Manager
from katana.target import Target
import katana.util


def decode_from_whitespace(binary_sequence):
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

    # Moderate priority
    PRIORITY = 75
    # Groups we're part of
    GROUPS = ["stego"]

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)

        self.space_pieces = re.findall(b"[ \t]+", self.target.raw)

        if self.space_pieces is None or self.space_pieces == []:
            raise NotApplicable("no spaces found")

    def evaluate(self, case):

        # First, retrieve all the spaces and put them together in a binary sequence.
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
