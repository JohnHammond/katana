"""

DNA/Codon Cipher.

This unit will translate groupings of letters (A,T,C,G,U) into 
22 out of 26 possible English characters.

"""

from typing import Any
import string

from katana.unit import PrintableDataUnit, NotApplicable

# JOHN: This method is not needed, but I am keeping the mapping
#       here in case it is ever needed...
# DNA_mapping = {
#     "AAA": "a",
#     "AAC": "b",
#     "AAG": "c",
#     "AAT": "d",
#     "ACA": "e",
#     "ACC": "f",
#     "ACG": "g",
#     "ACT": "h",
#     "AGA": "i",
#     "AGC": "j",
#     "AGG": "k",
#     "AGT": "l",
#     "ATA": "m",
#     "ATC": "n",
#     "ATG": "o",
#     "ATT": "p",
#     "CAA": "q",
#     "CAC": "r",
#     "CAG": "s",
#     "CAT": "t",
#     "CCA": "u",
#     "CCC": "v",
#     "CCG": "w",
#     "CCT": "x",
#     "CGA": "y",
#     "CGC": "z",
#     "CGG": "A",
#     "CGT": "B",
#     "CTA": "C",
#     "CTC": "D",
#     "CTG": "E",
#     "CTT": "F",
#     "GAA": "G",
#     "GAC": "H",
#     "GAG": "I",
#     "GAT": "J",
#     "GCA": "K",
#     "GCC": "L",
#     "GCG": "M",
#     "GCT": "N",
#     "GGA": "O",
#     "GGC": "P",
#     "GGG": "Q",
#     "GGT": "R",
#     "GTA": "S",
#     "GTC": "T",
#     "GTG": "U",
#     "GTT": "V",
#     "TAA": "W",
#     "TAC": "X",
#     "TAG": "Y",
#     "TAT": "Z",
#     "TCA": "1",
#     "TCC": "2",
#     "TCG": "3",
#     "TCT": "4",
#     "TGA": "5",
#     "TGC": "6",
#     "TGG": "7",
#     "TGT": "8",
#     "TTA": "9",
#     "TTC": "0",
#     "TTG": " ",
#     "TTT": ".",
# }


class Unit(PrintableDataUnit):
    """
    This unit inherits from the :class:`katana.units.PrintableDataUnit` class, 
    as the target that is necessary for this class needs to just be containing 
    A, T, C, G or U.
    """

    # Fill in your groups
    GROUPS = ["crypto"]
    BLOCKED_GROUPS = ["crypto"]
    # Default priority is 50
    PRIORITY = 50
    # Do not recurse into self
    RECURSE_SELF = False

    def __init__(self, *args, **kwargs):

        """
        The constructor verifies that that only DNA letters (A, T, C, G) 
        are found in the target.
        """

        super(Unit, self).__init__(*args, **kwargs)

        self.raw_target = self.target.stream.read().decode("utf-8").upper()
        self.raw_target = self.raw_target.replace(" ", "").replace("U", "T").strip()

        if (
            not all(c in "ACGT" for c in self.raw_target)
            or len(self.raw_target) % 3 != 0
        ):

            raise NotApplicable("more than DNA letters (A, T, C, G) found")

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.
        
        Read individual Codon groupings and replace them
        with the corresponding English character.

        :param case: A case returned by evaluate
        :return: None
        """

        # Try the first technique....
        all_characters: str = string.ascii_lowercase + string.ascii_uppercase + string.digits[
            1:10
        ] + "0 ."
        result: list = []

        for codon in [
            self.raw_target[i : i + 3] for i in range(0, len(self.raw_target), 3)
        ]:
            index = 0
            index += (
                0
                if codon[2] == "A"
                else (1 if codon[2] == "C" else (2 if codon[2] == "G" else 3))
            )
            index += (
                0
                if codon[1] == "A"
                else (4 if codon[1] == "C" else (8 if codon[1] == "G" else 12))
            )
            index += (
                0
                if codon[0] == "A"
                else (16 if codon[0] == "C" else (32 if codon[0] == "G" else 48))
            )
            result.append(all_characters[index])

        # Compile the new string, add and recurse
        result: str = "".join(result)
        self.manager.register_data(self, result)

        # JOHN: This method uses the above mapping, though it
        #       seems to wokr just fine with the method just above
        # # Now try the second technique...
        # result = []

        # for i in range(0, len(self.raw_target), 3):
        #     chunk = self.raw_target[i : i + 3]
        #     if chunk in DNA_mapping:
        #         result.append(DNA_mapping[chunk])

        # # Compile the new string, add and recurse
        # result: str = "".join(result)
        # print(result)
        # self.manager.register_data(self, result)
