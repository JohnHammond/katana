#!/usr/bin/env python3
import logging
import sys
import os

logging.basicConfig(level=logging.INFO)
sys.path.insert(0, os.path.abspath(os.getcwd()))

from katana.manager import Manager

# Create a manager with a default unit finder and default monitor
# and load all default units. The default monitor will using the python logging
# module to log important events to the console (or log file)
manager = Manager(config_path='./examples/example.ini')

manager['manager']['flag-format'] = 'USCGA{.*?}'

# Begin the background work monitor
manager.start()

# Queue targets while processing previous targets
manager.queue_target('./tests/qrcode.png')

# Wait for completion (with timeout)
if not manager.join(timeout=10):
	logging.warning('evaluation timed out')
