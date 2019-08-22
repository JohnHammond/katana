import requests
from katana import units
from katana.units import web
from pwn import *


class Unit(web.WebUnit):
    PRIORITY = 20

    def __init__(self, katana, target):

        # Run the parent constructor, to ensure this is a valid URL
        super(Unit, self).__init__(katana, target)

        self.completed = True
        if not katana.config['flag_format']:
            raise units.NotApplicable('no flag format specified')

        # raw_content = self.target.content.decode('utf-8')
        self.action = re.findall(rb'<\s*form.*action\s*=\s*[\'"](.+?)[\'"]', self.target.content, flags=re.IGNORECASE)
        self.method = re.findall(rb'<\s*form.*method\s*=\s*[\'"](.+?)[\'"]', self.target.content, flags=re.IGNORECASE)

        # Sometimes, a form might not have an explicit location. Assume the current page!
        if self.action == []:
            self.action = [b"#"]

        # Only run this if we have potential information...
        if not (self.action and self.method):
            raise units.NotApplicable('no form detected')

    def evaluate(self, katana, case):

        if self.action and self.method:
            if self.action: action = self.action[0].decode('utf-8')
            if self.method: method = self.method[0].decode('utf-8')
            try:
                method = vars(requests)[method.lower()]
            except IndexError:
                log.warning("Could not find an appropriate HTTP method... defaulting to POST!")
                method = requests.post

        url_form = self.target.upstream.decode('utf-8').split('/')
        if len(url_form) > 3:
            last_location = '/'.join(url_form[:-1]) + '/'
        else:
            last_location = self.target.upstream.decode('utf-8') + '/'
        r = method(last_location + action, allow_redirects=True)

        # Keep hunting on the new location...
        katana.recurse(self, r.url)

        # Hunt for flags. If we found one, stop all other requests!
        # I call this because we are NOT recursing on this page...
        # just new ones. But we need to hunt in this page itself.
        hit = katana.locate_flags(self, r.text)

        if hit:
            pass

        # You should ONLY return what is "interesting"
        # Since we cannot gauge the results of this payload versus the others,
        # we will only care if we found the flag.
        return None
