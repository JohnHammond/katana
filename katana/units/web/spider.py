"""
Spider web pages

This unit will look through all of the different links on a website and
queue each of them as a new target, or link to explore.

This unit inherits from :class:`katana.units.web.WebUnit` as that contains
lots of predefined variables that can be used throughout multiple web units.

.. warning::
    
    This unit automatically attempts to perform malicious actions on the 
    target. **DO NOT** use this in any circumstances where you do not have the
    authority to operate!

"""

import requests
from typing import Any

import re
from katana.units.web import WebUnit
from katana.unit import NotApplicable


bad_starting_links = [b"#", b"javascript:", b"https://", b"http://", b"//"]
"""
Avoid inline JavaScript, anchors, and external links
"""


def has_a_bad_start(link):
    """
    This is a convenience function just to avoid bad links above
    """
    for bad_start in bad_starting_links:
        if link.startswith(bad_start):
            return False
    else:
        return True


class Unit(WebUnit):

    PRIORITY = 20
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a somewhat
    higher priority.
    """

    PROTECTED_RECURSE = True
    """
    We don't really want to spider on EVERYTHING and start an infinite loop..
    We can protect against this once we create a target object
    and start to "keep track" of links we find in one specific website target
    """

    BAD_MIME_TYPES = ["application/octet-stream"]
    """
    Avoid mime types that are downloadable files.
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor is included to first determine if a found target
        is an attachment or a bad MIME type. If this is the case, the unit
        will abort.
        """
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
        """
        Evaluate the target. Look for links inside of the target web page and
        reach out to each of them, queueing them as a new target.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        # Look for links inside the page
        links = re.findall(
            rb'href=[\'"](.+?)[\'"]', self.target.raw, flags=re.IGNORECASE
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

            # If we found a new link, add as as a result, recurse on it, and
            # hunt for flags
            if new_link:
                self.manager.register_data(self, new_link)
