"""
View cookies

This unit will look through all of the different cookies on a website
and look for a flag.
"""

from katana.unit import NotApplicable
from katana.units.web import WebUnit


class Unit(WebUnit):

    # Groups we belong to
    GROUPS = [
        "web",
        "cookies",
    ]

    # It would not make sense to recurse on cookies
    RECURSE_SELF = False

    # Moderately high priority due to speed and broadness of applicability
    PRIORITY = 30

    # We do not need to include the constructor here because
    # the WebUnit parent will already ensure this is a
    # URL beginning with either http:// or https://

    def enumerate(self):

        # Return the cookies
        for cookie in self.target.request.cookies:
            if cookie:
                yield vars(cookie)

    def evaluate(self, case):

        # Grab the case passed by enumerate -- this will be a cookie, name and value dict
        cookie = case

        for cookie_name, cookie_value in cookie.items():

            ## I cast this to a string because it may be a number or a bool
            # We will recurse on each value...
            self.manager.register_data(self, str(cookie_value))
            self.manager.register_data(self, cookie_name)
