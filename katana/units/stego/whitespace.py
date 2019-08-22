import binascii
import re

from katana import units
from katana.units import NotApplicable


# def encode_to_whitespace(f):
# 	h = binascii.hexlify(f)
# 	d = int(h, 16)
# 	b = bin(d)[2:]
# 	m = b.replace('0', ' ')
# 	m = m.replace('1', '\t')
# 	return m

def decode_from_whitespace(binary_sequence):
    decoded = int(binary_sequence, 2)
    decoded = hex(decoded)[2:].replace('L', '')
    try:
        decoded = binascii.unhexlify(decoded).decode('utf-8')
    except binascii.Error:
        decoded = binascii.unhexlify('0' + decoded).decode('utf-8')
    except UnicodeDecodeError:
        return None

    return decoded


class Unit(units.FileUnit):
    PRIORITY = 30

    def __init__(self, katana, target, keywords=None):
        super(Unit, self).__init__(katana, target)

        if keywords is None:
            keywords = []
        if target.is_url:
            raise NotApplicable('target is a URL')

        try:
            self.space_pieces = re.findall('[ \t]+', self.target.stream.read().decode('utf-8'))
        except (UnicodeDecodeError, AttributeError):
            raise NotApplicable("unable to decode, might be binary")

        if self.space_pieces is None or self.space_pieces == []:
            raise NotApplicable("no spaces found")

    def evaluate(self, katana, case):

        # First, retrieve all the spaces and put them together in a binary sequence.
        pieces = []
        for piece in self.space_pieces:
            string_piece = piece
            binary = string_piece.replace('\t', '1')
            binary = binary.replace(' ', '0')

            pieces.append(binary)

        # Decode the first method, and recurse/add_results on those...
        final_binary = ''.join(pieces)
        decoded = decode_from_whitespace(final_binary)

        if decoded:
            katana.add_results(self, decoded)
            katana.recurse(self, decoded)

        # Then try again, hotswapping the 1's and 0's.
        final_binary.replace('0', "@")
        final_binary.replace('1', "0")
        final_binary.replace('@', "1")

        decoded = decode_from_whitespace(final_binary)
        if decoded:
            katana.add_results(self, decoded)
            katana.recurse(self, decoded)
