#!/usr/bin/env python3
from tests import KatanaTest


class Test(KatanaTest):
    """ Test {unit} functionality """

    def test_single_byte(self):

        self.katana_test(
            config=r"""
        [manager]
        flag-format=FLAG{.*?}
        units=xor
        auto=yes
        """,
            target=b"\x07\r\x00\x06:\x19\x0e\x13<",
            correct_flag="FLAG{XOR}",
        )

    def test_multibyte(self):

        self.katana_test(
            config=r"""
        [manager]
        flag-format=FLAG{.*?}
        units=xor
        auto=yes
        [xor]
        key=flag
        """,
            target=b"    \x1d4.5\x1b",
            correct_flag="FLAG{XOR}",
        )
