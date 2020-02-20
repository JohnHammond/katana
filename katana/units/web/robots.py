"""
Check robots.txt

This unit will look through all of the different robots.txt entries on a webpage
and look for a flag.
"""

import requests

from katana.unit import NotApplicable
from katana.units.web import WebUnit

# Assume that you are in fact the Google crawler.
headers = {"User-Agent": "Googlebot/2.1"}


class Unit(WebUnit):

    # Groups we belong to
    GROUPS = ["web", "robots", "robots.txt"]

    # No need to recurse into yourself here.. that would just be weird
    RECURSE_SELF = False

    # Moderately high priority due to speed and broadness of applicability
    PRIORITY = 30

    def __init__(self, *args, **kwargs):

        # Run the parent constructor, to ensure this is a valid URL
        super(Unit, self).__init__(*args, **kwargs)

        # Try to get the robots.txt file
        try:
            r = requests.get(
                "{0}/{1}".format(self.target.url_root.rstrip("/"), "robots.txt"),
                headers=headers,
            )
        except requests.exceptions.ConnectionError:

            raise NotApplicable("cannot reach url")

        # Check if the request succeeded
        if r.status_code != 200:
            # Completely fail if there is nothing there.
            raise NotApplicable("no http 200 response from /robots.txt")

        # Keep track of the response variable for later use
        self.response = r

        # Look for flags in the robots.txt file itself, just in case!
        self.manager.find_flag(self, r.text)

    def enumerate(self):

        robots_data = self.response.text
        disallowed_entries = {}

        # Look for disallow entries and add them to the findings
        for line in robots_data.split("\n"):
            pieces = line.strip().split(":")
            action, url = pieces[0], ":".join(pieces[1:]).strip()

            # Ignore comments and empty lines
            if action.strip().startswith("#") or len(pieces) == 1:
                continue

            # Since these are typically URLs, do not bother to recurse on them...
            # but add the entries into the results!
            self.manager.register_data(self, line, recurse=False)
            if action.lower().startswith("disallow"):
                yield url

    def evaluate(self, case):

        # Grab the case passed by enumerate -- this will be a relative URL, usually
        url = case

        # Fix the new URL and access the page
        new_url = "{0}/{1}".format(self.target.url_root.rstrip("/"), url.lstrip("/"))

        r = requests.get(new_url, headers=headers)

        # I DO recurse on this, in case there are base64 things to catch...
        # Might be dangerous, but fuck it
        self.manager.register_data(self, r.text)
