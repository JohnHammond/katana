from tests import KatanaTest


class TestExiftool(KatanaTest):
    """ Test katana.units.raw.exiftool """

    def test_woof64(self):
        self.katana_test(
            config=r"""
        [manager]
        flag-format=USCGA{.*?}
        units=exiftool
        auto=yes
        """,
            target="./tests/cases/woof64.jpg",
            correct_flag="USCGA{the_best_base_is_the_base64}",
        )
