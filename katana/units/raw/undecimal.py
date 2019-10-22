#!/usr/bin/env python3
from typing import Any
import binascii
import magic
import re

from katana.unit import Unit as BaseUnit
from katana.unit import NotApplicable
from katana.manager import Manager
from katana.target import Target
import katana.util

DECIMAL_PATTERN = rb'[0-9]{1,3}'
DECIMAL_REGEX = re.compile(DECIMAL_PATTERN, flags=re.MULTILINE | \
                                                  re.DOTALL | re.IGNORECASE)


class Unit(BaseUnit):
    # Moderate-high unit priority
    PRIORITY = 25
    
    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target)
        
        # We don't need to operate on files
        if self.target.is_file:
            raise NotApplicable("is a file")
        
        # We want printable
        if not self.target.is_printable:
            raise NotApplicable("not printable data")
        
        # We don't want english text
        if self.target.is_english:
            raise NotApplicable("english data; expected decimal numbers")
        
        # Find matching data
        self.matches = DECIMAL_REGEX.findall(self.target.raw)
        
        # Ensure we have something to work with
        if self.matches is None:
            raise NotApplicable("no decimal values found")
        
        # CALEB: Um.... I feel like this could be an issue, but whatever
        for decimal in self.matches:
            if int(decimal) not in range(255):
                raise NotApplicable("decimal value larger than 255 was found")
    
    def evaluate(self, case):
        
        try:
            # Decode all matches as one string
            result = ''.join(chr(int(d)) for d in self.matches)
        # If this fails, it's probably not decimal we can deal with...
        except (UnicodeDecodeError, binascii.Error):
            return None
        
        if katana.util.isprintable(result):
            # If it's printable save the results
            self.manager.register_data(self, result)
        else:
            # if it's not printable, we might only want it if it is a file...
            magic_info = magic.from_buffer(result)
            if katana.util.is_good_magic(magic_info):
                # Generate a new artifact
                filename, handle = self.generate_artifact("decoded",
                                                          mode='wb', create=True)
                handle.write(result)
                handle.close()
                # Register the artifact
                self.manager.register_artifact(self, filename)
