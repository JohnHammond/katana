#!/usr/bin/env python3
import logging
import time

from katana.manager import Manager
from katana.unit import Unit
from katana.monitor import Monitor

# A custom monitor which will recieve notifications about units
# The default monitor prints notifications of flags with logging as well but
# this allows you to do fancier status updates if you are building an interface
# of some kind
class MyMonitor(Monitor):
    def on_flag(self, manager: Manager, unit: Unit, flag: str):
        logging.info("found a flag: {0}".format(flag))


# Create your monitor object
monitor = MyMonitor()

# Create your Manager with your monitor attached
manager = Manager(monitor, config_path="./examples/example.ini")

# Set some custom configuration parameters
manager["auto"] = True
manager["outdir"] = "./example-results-{0}".format(time.strftime("%Y%m%d-%H%M%S"))
manager["exclude"] = ["crypto"]
manager["flag-format"] = r"FLAG{.*?}"

# Optionally, manually register unit classes
# manager.finder.register(CustomChallengeUnit)
# Or load units automatically from a directory
# manager.finder.find('./customunits', 'customunits.')

# Start the manager (empty queue at the moment)
manager.start()

# Create a generic target
target = manager.target("./interesting-file.txt")

# Enumerate units that are applicable and queue them for evaluation
for unit in manager.finder.match(target):
    logging.info("queuing {0} for {1}".format(unit, target))
    manager.queue(unit)

# A short-hand for queuing targets with all matching units:
# target = manager.queue_target('./interesting-file.txt')

# More targets could be queued up until you call `join` at which point the
# queue would be "closed" and would cause an exception if `queue` is called.

# Wait for evaluation to complete with an optional timeout in seconds
try:
    manager.join(timeout=300.0)
except TimeoutError:
    logging.error("evaluation timed out after 5 minutes")
