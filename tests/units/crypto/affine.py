from tests import KatanaTest
from base64 import b85encode


class TestAffine(KatanaTest):
    """ Test katana.units.crypto.affine """

    def test_affine(self):
        self.katana_test(
            config=r"""
        [manager]
        flag-format=FLAG{.*?}
        units=affine
        auto=yes
        """,
            target=b"HLIM{HLIM}",
            correct_flag="FLAG{FLAG}",
        )
