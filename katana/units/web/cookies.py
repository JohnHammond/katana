"""
View HTTP cookies

This unit will look through all of the different cookies on a website
and look for a flag.

This unit inherits from :class:`katana.units.web.WebUnit` as that contains
lots of predefined variables that can be used throughout multiple web units.
"""

from katana.unit import NotApplicable
from katana.units.web import WebUnit


class Unit(WebUnit):

    GROUPS = ["web", "cookies"]
    """
    These are "tags" for a unit. Considering it is a Web unit, "web"
    is included, as well as the name of the unit, "cookies".
    """

    RECURSE_SELF = False
    """
    This unit should not recurse into itself. It would not make
    sense to recurse on cookies.
    """

    PRIORITY = 30
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a 
    moderately high priority due to speed and broadness of applicability
    """

    def enumerate(self):
        """
        Yield cases. This function will look at the cookies in the requested
        page and yield each one, to be examined by the ``evaluate`` function.

        :return: A generator, yielding a dictionary with the cookie \
        information (i.e, name=value dictionary).
        """

        # Return the cookies
        for cookie in self.target.request.cookies:
            if cookie:
                yield vars(cookie)

    def evaluate(self, case):

        # Grab case passed by enumerate: this is a cookie, name and value dict
        cookie = case

        for cookie_name, cookie_value in cookie.items():

            ## I cast this to a string because it may be a number or a bool
            # We will recurse on each value...
            self.manager.register_data(self, str(cookie_value))
            self.manager.register_data(self, cookie_name)
