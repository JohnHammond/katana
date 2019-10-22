from tests import KatanaTest
from binascii import hexlify


class TestUnhexlify(KatanaTest):
    """ Test katana.units.raw.strings """

    def test_unhexlify(self):
        flag = b"FLAG{unhexlify}"
        self.katana_test(
            config=r"""
        [manager]
        flag-format=FLAG{.*?}
        auto=yes
        """,
            target=hexlify(flag),
            correct_flag=flag,
        )
