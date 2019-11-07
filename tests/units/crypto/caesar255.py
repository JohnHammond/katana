#!/usr/bin/env python3
from tests import KatanaTest


def shift(data: bytes, n: int, start: int = 0, end: int = 256):
    result = []
    for c in data:
        result.append(((c + n - start) % (end - start)) + start)
    print(result)
    return bytes(result)


class TestCaesar255(KatanaTest):
    """ Test {unit} functionality """

    FLAG = b"FLAG{caesar255}"

    def test_caesar255(self):
        self.katana_test(
            config=r"""
        [manager]
        flag-format=FLAG{.*?}
        units=caesar255
        auto=yes
        """,
            target=shift(self.FLAG, 42),
            correct_flag=self.FLAG.decode("utf-8"),
        )
