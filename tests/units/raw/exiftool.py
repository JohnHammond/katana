from tests import KatanaTest


class TestStrings(KatanaTest):
    """ Test katana.units.raw.strings """
    
    def test_orchestra(self):
        self.katana_test(config=r"""
        [manager]
        flag-format=USCGA{.*?}
        auto=yes
        """, target='./tests/cases/woof64.jpg', correct_flag='USCGA{the_best_base_is_the_base64}')
