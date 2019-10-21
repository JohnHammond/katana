#!/usr/bin/env python3
import unittest
import warnings
import os

from katana.manager import Manager
from katana.target import Target
from katana.monitor import JsonMonitor, LoggingMonitor


class TestKatanaUnits(unittest.TestCase):

    def setUp(self) -> None:
        warnings.simplefilter('ignore', category=ResourceWarning)
        os.system("rm -rf ./results")
        self.monitor = LoggingMonitor()
        self.manager = Manager(monitor=self.monitor)
        self.manager['manager']['auto'] = 'yes'

    def tearDown(self) -> None:
        del self.monitor
        del self.manager

    def test_steghide_nopass(self):
        self.manager['manager']['flag-format'] = 'USCGA{.*?}'
        self.manager.start()
        self.manager.queue_target('./tests/rubber_ducky.jpg')
        self.assertTrue(self.manager.join(timeout=10))
        self.assertGreater(len(self.monitor.flags), 0)
        self.assertEqual(self.monitor.flags[0][1], 'USCGA{hidden_in_the_bathtub}')
    
    def test_steghide_with_pass(self):
        self.manager['manager']['flag-format'] = 'USCGA{.*?}'
        self.manager['DEFAULT']['dict'] = '/home/caleb/ctf/tools/rockyou.txt'
        self.manager.queue_target('./tests/evil_ducky.jpg')
        self.manager.start()
        self.assertTrue(self.manager.join(timeout=45))
        self.assertGreater(len(self.monitor.flags), 0)
        self.assertEqual(self.monitor.flags[0][1], 'USCGA{we_finally_found_the_the_flag}')

if __name__ == '__main__':
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=ResourceWarning)
        unittest.main()
