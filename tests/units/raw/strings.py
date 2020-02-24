from tests import KatanaTest


class TestStrings(KatanaTest):
    """ Test katana.units.raw.strings """

    def test_orchestra(self):
        self.katana_test(
            config=r"""
        [manager]
        flag-format=USCGA{.*?}
        auto=yes
        """,
            target="./tests/cases/orchestra",
            correct_flag="USCGA{strings}",
        )
