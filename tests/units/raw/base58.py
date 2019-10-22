from tests import KatanaTest
from base58 import b58encode

class TestBase58(KatanaTest):
    """ Test katana.units.raw.strings """
    
    def test_orchestra(self):
        self.katana_test(config=r"""
        [manager]
        flag-format=FLAG{.*?}
        auto=yes
        """, target=b58encode(b'FLAG{base58}'), correct_flag='FLAG{base58}')
