#!/usr/bin/env python3
from tests import KatanaTest


class TestPhonetic(KatanaTest):
    """ Test {unit} functionality """

    def test_phonetic(self):
        self.katana_test(
            config=r"""
        [manager]
        flag-format=FLAG.*
        units=phonetic
        auto=no
        """,
            target=b"FOXTROT LIMA ALFA GOLF INDIA SIERRA HOTEL ECHO ROMEO ECHO",
            correct_flag="FLAGISHERE",
        )
