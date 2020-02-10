import requests
from katana.unit import NotApplicable
from katana.units import web

import re

from typing import Any


class Unit(web.WebUnit):
    PRIORITY = 20

    def __init__(self, *args, **kwargs):

        # Run the parent constructor, to ensure this is a valid URL
        super(Unit, self).__init__(*args, **kwargs)

        self.action = re.findall(
            rb'<\s*form.*action\s*=\s*[\'"](.+?)[\'"]',
            self.target.content,
            flags=re.IGNORECASE,
        )
        self.method = re.findall(
            rb'<\s*form.*method\s*=\s*[\'"](.+?)[\'"]',
            self.target.content,
            flags=re.IGNORECASE,
        )

        # Sometimes, a form might not have an explicit location. Assume the current page!
        if self.action == []:
            self.action = [b"#"]

        # Only run this if we have potential information...
        if not (self.action and self.method):
            raise NotApplicable("no form detected")

    def evaluate(self, case: Any):

        if self.action and self.method:
            if self.action:
                action = self.action[0].decode("utf-8")
            if self.method:
                method = self.method[0].decode("utf-8")
            try:
                method = vars(requests)[method.lower()]
            except IndexError:
                # Could not find a valid method... default to POST
                method = requests.post

        # if this is a relative path, get the furthermost directory location
        url_form = self.target.upstream.decode("utf-8").split("/")
        if len(url_form) > 3:
            last_location = "/".join(url_form[:-1]) + "/"
        else:
            last_location = self.target.upstream.decode("utf-8") + "/"
        r = method(last_location + action, allow_redirects=True)

        # Keep hunting on the new location...
        self.manager.register_data(self, r.text)
