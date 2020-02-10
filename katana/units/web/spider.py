#!/usr/bin/env python3

import requests
from typing import Any

import re
from katana.units.web import WebUnit
from katana.unit import NotApplicable

# Avoid inline JavaScript, anchors, and external links
bad_starting_links = [b"#", b"javascript:", b"https://", b"http://", b"//"]


# This is a convenience function just to avoid bad links above
def has_a_bad_start(link):
    for bad_start in bad_starting_links:
        if link.startswith(bad_start):
            return False
    else:
        return True


class Unit(WebUnit):

    PRIORITY = 20

    # We don't really want to spider on EVERYTHING and start an infinite loop..
    # We can protect against this once we create a target object
    # and start to "keep track" of links we find in one specific website target
    PROTECTED_RECURSE = True

    # If find a downloadable file, uh, just leave it alone
    BAD_MIME_TYPES = ["application/octet-stream"]

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        # avoid attachments
        if "Content-Disposition" in self.target.request.headers:
            if "attachment" in self.target.request.headers["Content-Disposition"]:
                raise NotApplicable("spider cannot handle attachments")

        # avoid bad mime types
        if "Content-Type" in self.target.request.headers:
            content_type = self.target.request.headers["Content-Type"].lower()
            for bad_type in self.BAD_MIME_TYPES:
                if bad_type in content_type:
                    raise NotApplicable(
                        "spider does not support {0} files".format(bad_type)
                    )

    def evaluate(self, case: Any):

        # Look for links inside the page
        links = re.findall(
            rb'href=[\'"](.+?)[\'"]', self.target.content, flags=re.IGNORECASE
        )

        # Remove anything that might not be local (remove all bad links)
        links = list(filter(has_a_bad_start, links))

        # if this is a relative path, get the furthermost directory location
        url_form = self.target.upstream.decode("utf-8").split("/")
        if len(url_form) > 3:
            last_location = "/".join(url_form[:-1])
        else:
            last_location = self.target.upstream.decode("utf-8").rstrip("/")

        # All this does is find is new links.
        # It won't contain flags and they don't need to be considered results.
        for link in links:
            new_link = "{0}/{1}".format(last_location, link.decode("utf-8").lstrip("/"))

            # If we found a new link, add it as as a result, recurse on it, and hunt for flags
            if new_link:
                self.manager.register_data(self, new_link)
                # katana.recurse(self, new_link)
                # katana.add_results(self, new_link)
