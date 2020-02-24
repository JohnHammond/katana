from tests import KatanaTest
from base64 import b64encode


class TestBase64(KatanaTest):
    """ Test katana.units.raw.strings """

    def test_orchestra(self):
        self.katana_test(
            config=r"""
        [manager]
        flag-format=FLAG{.*?}
        auto=yes
        """,
            target=b64encode(b"FLAG{base64}"),
            correct_flag="FLAG{base64}",
        )
