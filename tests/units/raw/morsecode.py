from tests import KatanaTest


class TestMorsecode(KatanaTest):
    """ Test katana.units.raw.strings """
    
    def test_moresecode(self):
        self.katana_test(config=r"""
        [manager]
        flag-format=^flag.*$
        auto=yes
        """, target='..-. .-.. .- --. -- --- .-. ... . -.-. --- -.. .', correct_flag='FLAGMORSECODE')
