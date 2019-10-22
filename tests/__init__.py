from unittest import TestCase
import warnings
import os
import io

from katana.monitor import Monitor
from katana.manager import Manager


class KatanaTest(TestCase):

    FLAG_FORMAT = "FLAG{.*?}"

    def setUp(self):
        """ Setup a Manager and Monitor object """

        # This is a nasty hack
        os.system("rm -rf ./results 2>&1 >/dev/null")

        # Create the monitor and set the flag format
        self.monitor = Monitor()
        self.manager = Manager(monitor=self.monitor)
        self.manager["manager"]["flag-format"] = self.FLAG_FORMAT
        self.manager["manager"]["auto"] = "yes"

        # Ignore annoying resource warnings
        warnings.simplefilter("ignore", ResourceWarning)

    def tearDown(self):
        """ Tear down any artifacts from the last run """

        # Tear down our object tree
        del self.monitor
        del self.manager

        # This is a nasty hack
        os.system("rm -rf ./results 2>&1 >/dev/null")

    def katana_test(self, config: str, target: str, correct_flag: str, timeout=10):
        """ Perform a test with the given configuration, target and flag """

        if isinstance(correct_flag, bytes):
            correct_flag = correct_flag.decode("utf-8")

        # Load given configuration
        self.manager.read_file(io.StringIO(config))

        # Queue the target and begin processing
        self.manager.queue_target(target)
        self.manager.start()

        # Ensure wait for completion. Error if we time out
        self.assertTrue(self.manager.join(timeout=timeout), "manager timed out")

        # Ensure we have at least 1 flag
        self.assertGreater(len(self.monitor.flags), 0, "no flags found")

        # Ensure the flag matches expected output
        for flag in self.monitor.flags:
            if flag[1] == correct_flag:
                return

        # Fail otherwise
        self.fail(f"correct flag not found (found: {self.monitor.flags})")
