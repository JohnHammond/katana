import json

import requests
from katana import units


# JOHN: This is stolen from https://github.com/rallip/substituteBreaker
#       All it does is pass the ciphertext to quipiqiup.com
def decodeSubstitute(cipher, time=3, spaces=True):
    url = "https://6n9n93nlr5.execute-api.us-east-1.amazonaws.com/prod/solve"
    clues = ''
    data = {
        'ciphertext': cipher,
        'clues': clues,
        'solve-spaces': spaces,
        'time': time
    }
    headers = {
        'Content-type': 'application/x-www-form-urlencoded',
    }

    return requests.post(url, data=json.dumps(data), headers=headers).text


# class Unit(units.PrintableDataUnit):
class Unit(units.NotEnglishAndPrintableUnit):
    PROTECTED_RECURSE = True
    PRIORITY = 60

    def __init__(self, katana, target, keywords=None):
        super(Unit, self).__init__(katana, target)

        if keywords is None:
            keywords = []
        try:
            self.raw_target = self.target.stream.read().decode('utf-8')
        except UnicodeDecodeError:
            raise units.NotApplicable("unicode error, unlikely usable cryptogram")
        try:
            requests.get('https://6n9n93nlr5.execute-api.us-east-1.amazonaws.com/prod/solve')
        except requests.exceptions.ConnectionError:
            raise units.NotApplicable("cannot reach quipqiup solver")

    def evaluate(self, katana, case):

        j = json.loads(decodeSubstitute(self.raw_target))

        found_solution = ""
        best_score = -10
        for sol in j['solutions']:
            if sol['logp'] > best_score:
                found_solution = sol['plaintext']
                best_score = sol['logp']

        # katana.recurse(self, found_solution)
        if katana.locate_flags(self, found_solution):
            pass

        katana.add_results(self, found_solution)
