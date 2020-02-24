from tests import KatanaTest


class TestQRCode(KatanaTest):
    """ Test katana.units.raw.strings """

    def test_qrcode(self):
        self.katana_test(
            config=r"""
        [manager]
        flag-format=USCGA{.*?}
        auto=yes
        """,
            target="./tests/cases/qrcode.png",
            correct_flag="USCGA{is_this_ecoin_from_mr_robot}",
        )
