#!/usr/bin/env python3
from tests import KatanaTest

class Test(KatanaTest):
    """ Test {unit} functionality """
    
    def test_unit(self):
        self.katana_test(
            config=r"""
        [manager]
        flag-format=FLAG{.*?}
        units=UNITNAME
        auto=yes
        """,
            target=b"Encoded Target",
            correct_flag="FLAG{FLAG}",
        )