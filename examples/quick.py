#!/usr/bin/env python3
import logging

from katana.manager import Manager
from katana.monitor import LoggingMonitor

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# Create a basic monitor which will log results
monitor = LoggingMonitor()

# Create a manager with a default unit finder and default monitor
# and load all default units. The default monitor will using the python logging
# module to log important events to the console (or log file)
manager = Manager(monitor=monitor, config_path="./examples/example.ini")

# Begin the background work monitor
manager.start()

# Queue the target
manager.queue_target("./tests/qrcode.png")

# Wait for completion (with a 10-second timeout)
if not manager.join(timeout=10):
    logging.warning("evaluation timed out")
