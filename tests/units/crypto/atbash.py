from tests import KatanaTest


class TestAtBash(KatanaTest):
    """ Test katana.units.crypto.atbash """

    def test_atbash(self):
        self.katana_test(
            config=r"""
        [manager]
        flag-format=FLAG{.*?}
        units=atbash
        auto=yes
        """,
            target=b"UOZT{UOZT}",
            correct_flag="FLAG{FLAG}",
        )
