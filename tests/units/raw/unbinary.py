from tests import KatanaTest


class TestUnbinary(KatanaTest):
    """ Test katana.units.raw.strings """
    
    def test_7bit(self):
        flag = 'FLAG{unbinary}'
        self.katana_test(config=r"""
        [manager]
        flag-format=FLAG{.*?}
        auto=yes
        """, target=''.join(format(ord(x), 'b') for x in flag), correct_flag=flag)
    
    def test_8bit(self):
        flag = 'FLAG{unbinary}'
        self.katana_test(config=r"""
        [manager]
        flag-format=FLAG{.*?}
        auto=yes
        """, target=''.join(format(ord(x), 'b').rjust(8, '0') for x in flag), correct_flag=flag)
