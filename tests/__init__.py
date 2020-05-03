"""
Katana Unit tests are designed to test the individual katana units. Confusingly,
we are also utilizing the Python UnitTest module. Each Python Unit Test should
correspond to a single Katana Unit. The unit test will run katana with a target,
and ensure that it finds the known flag. You should create multiple tests per
unit to cover all valid forms of the specific challenge you are attempting to
solve.

To ease the process of creating units, there is a base test class named
`KatanaTest`. Your tests should inherit from this class. The directory structure
for tests is the same as the `units` directory (e.g. `tests/units/category/unit`)

A Katana Unit test must implement one or more `test_*` methods which will be
executed by the `unittest` module. The base `KatanaTest` module contains `setUp`
and `tearDown` methods to setup the Katana monitor and manager objects. Inside
of the individual tests, you can call the `KatanaTest.katana_test` method to
initiate the analysis of a single test target. This method takes the following
parameters:

    - config: A string containing the `ini` configuration loaded by the manager.
    - target: A string representing the target for analysis (raw data or file
      path)
    - correct_flag: A string containing the correct flag
    - timeout: A timeout in seconds for the test. default: 10 seconds

That's it! A Katana Unit Test only requires that single call, however your test
method can also be used to generate a unique or special target (for example,
creating a temporary file containing an image to pass to stego unit).
"""
from unittest import TestCase
import warnings
import os
import io

from katana.monitor import Monitor
from katana.manager import Manager


class KatanaTest(TestCase):

    FLAG_FORMAT = "FLAG{.*?}"

    def setUp(self):
        """ Setup a Manager and Monitor object

            The Katana Unit Tests can override this method, but must call the
            parent. You can use this to create special temporary target files,
            start a web server, or anything else needed to evaluate your target.
        """

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
        """ Tear down any artifacts from the last run

            The Katana Unit Tests can override this method, but must call the
            parent. You can use this method to clean up any extra temporary files
            that may have been created for the target or any threads/services 
            started for unit testing.
        """

        # Tear down our object tree
        del self.monitor
        del self.manager

        # This is a nasty hack
        os.system("rm -rf ./results 2>&1 >/dev/null")

    def katana_test(
        self, config: str, target: str, correct_flag: str, timeout: float = 10
    ):
        """ Perform a test with the given configuration, target and flag

        :param config: Katana configuration file
        :type config: str
        :param target: The target for this katana test (url, filename, raw data, etc)
        :type target: str
        :param correct_flag: The correct flag which katana should find.
        :type correct_flag: str
        :param timeout: The timeout in seconds for this test, defaults to 10
        :type timeout: float, optional

        """

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
