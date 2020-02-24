from tests import KatanaTest
from base64 import b85encode


class TestAscii85(KatanaTest):
    """ Test katana.units.raw.strings """

    def test_ascii85(self):
        self.katana_test(
            config=r"""
        [manager]
        flag-format=FLAG{.*?}
        auto=yes
        """,
            target=b85encode(b"FLAG{base85}"),
            correct_flag="FLAG{base85}",
        )
