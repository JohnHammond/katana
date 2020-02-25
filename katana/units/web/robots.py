"""
Check robots.txt

This unit will look through all of the different robots.txt entries on a 
webpage and look for a flag.

It passes a User-Agent to act as a Google-bot crawler.

This unit inherits from :class:`katana.units.web.WebUnit` as that contains
lots of predefined variables that can be used throughout multiple web units.

.. warning::
    
    This unit automatically attempts to perform malicious actions on the 
    target. **DO NOT** use this in any circumstances where you do not have the
    authority to operate!

"""

import requests

from katana.unit import NotApplicable
from katana.units.web import WebUnit


headers = {"User-Agent": "Googlebot/2.1"}
"""
Include these headers in the unit, to simulate action as the Googlebot 
crawler.
"""


class Unit(WebUnit):

    GROUPS = ["web", "robots", "robots.txt"]
    """
    These are "tags" for a unit. Considering it is a Web unit, "web"
    is included, as well as the name of the unit, "robots".
    """

    RECURSE_SELF = False
    """
    This unit should not recurse into itself. That would be silly.
    """

    PRIORITY = 30
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a somewhat
    higher priority.
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor is included to first determine if there is a 
        robots.txt file present on the website. If that is not found, this
        unit will abort.
        """

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
        """
        Yield cases. This function will look at robots.txt page and return
        each page, to be examined by the ``evaluate`` function.

        :return: A generator, yielding a string for each URL in robots.txt.
        """

        robots_data = self.response.text
        disallowed_entries = {}

        # Look for disallow entries and add them to the findings
        for line in robots_data.split("\n"):
            pieces = line.strip().split(":")
            action, url = pieces[0], ":".join(pieces[1:]).strip()

            # Ignore comments and empty lines
            if action.strip().startswith("#") or len(pieces) == 1:
                continue

            # Since these are typically URLs, do not bother to recurse on
            # them but add the entries into the results!
            self.manager.register_data(self, line, recurse=False)
            if action.lower().startswith("disallow"):
                yield url

    def evaluate(self, case):
        """
        Evaluate the target. Reach out to every entry in the robots.txt file
        and look for flags.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function will yield each URL in the robots.txt file

        :return: None. This function should not return any data.
        """

        # Grab the case passed by enumerate -- this is a relative URL, usually
        url = case

        # Fix the new URL and access the page
        new_url = "{0}/{1}".format(self.target.url_root.rstrip("/"), url.lstrip("/"))

        r = requests.get(new_url, headers=headers)

        # I DO recurse on this, in case there are base64 things to catch...
        self.manager.register_data(self, r.text)
