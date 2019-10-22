from tests import KatanaTest


class TestUndecimal(KatanaTest):
    """ Test katana.units.raw.strings """

    def test_undecimal(self):
        flag = "FLAG{unbinary}"
        self.katana_test(
            config=r"""
        [manager]
        flag-format=FLAG{.*?}
        auto=yes
        """,
            target=" ".join(str(ord(x)) for x in flag),
            correct_flag=flag,
        )
