"""
These are used throughout the web units, so I have placed 
them here so they are all accessible.
"""

from katana.unit import NotApplicable
from katana.unit import Unit as BaseUnit

firefox_browser_user_agent = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0'"
)

potential_username_variables = [
    b"username",
    b"user",
    b"uname",
    b"un",
    b"name",
    b"user1",
    b"input1",
    b"uw1",
    b"username1",
    b"uname1",
    b"tbUsername",
    b"usern",
    b"id",
]
potential_password_variables = [
    b"password",
    b"pass",
    b"pword",
    b"pw",
    b"pass1",
    b"input2",
    b"password1",
    b"pw1",
    b"pword1",
    b"tbPassword",
]

potential_file_variables = [
    b"fileToUpload",
    b"file",
    b"upload_file",
    b"file_to_upload",
]


user_regex = rb'<\s*input.*name\s*=\s*[\'"](%s)[\'"]' % b"|".join(
    potential_username_variables
)
pass_regex = rb'<\s*input.*name\s*=\s*[\'"](%s)[\'"]' % b"|".join(
    potential_password_variables
)

potential_cookie_names = ["admin", "is_admin", "isadmin", "administrator", "isAdmin"]

delim = "@@DELIMETER@@"
special = "@@SPECIAL@@"

potential_flag_names = [b"flag", b"flag.txt"]


class WebUnit(BaseUnit):
    def __init__(self, *args, **kwargs):

        super(WebUnit, self).__init__(*args, **kwargs)

        if not self.target.is_url:

            raise NotApplicable("not a web url")
