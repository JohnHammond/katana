from tests import KatanaTest
from base64 import b32encode


class TestBase32(KatanaTest):
    """ Test katana.units.raw.strings """

    def test_base32(self):
        self.katana_test(
            config=r"""
        [manager]
        flag-format=FLAG{.*?}
        auto=yes
        """,
            target=b32encode(b"FLAG{base32}"),
            correct_flag="FLAG{base32}",
        )
