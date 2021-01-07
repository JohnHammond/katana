"""
Substituion cipher solver, by outsourcing to https://quipqiup.com/.

The gist of this code is ripped from 
https://github.com/rallip/substituteBreaker. The unit takes the target, and
if it does not look English text but it is clearly printable characters, it
offers it to quipqiup online. 

This unit inherits from the 
:class:`katana.unit.NotEnglishAndPrintableUnit` class, as we can expect
the data to still be printable characters (letters, numbers and punctuation)
but not readable English. It also inherits from the 
:class:`katana.units.crypto.CryptoUnit` class to ensure it is not a viable
URL or potentially useful file.

.. note::

    This unit **does not recurse**. It simply looks for flags in the output of
    quipqiup's best potential solution. Note that Katana might find flags
    that are not in the specific flag format, but also denoted in a 
    "the flag is:" structure.

"""


import json  # json is used for communicating with quipqiup.com
import requests
import io
from typing import Any
from time import sleep

from katana.unit import NotEnglishAndPrintableUnit, NotApplicable
from katana.units.crypto import CryptoUnit


def decodeSubstitute(cipher: str, time=3) -> str:
    """
    This is based on https://github.com/rallip/substituteBreaker
    All it does is use the ``requests`` module to send the ciphertext to
    quipqiup and returns the results as a string.
    """
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
    }
    
    clues = ""
    url = "https://quipqiup.com/solve"
    data = {"ciphertext":cipher,"clues":clues,"mode":"auto","was_auto":True,"was_clue":False}

    response = json.loads( requests.post(url, data=json.dumps(data), headers=headers, verify=False).text )

    sleep( min(response["max_time"], time) )
    
    url = "https://quipqiup.com/status"
    data = {"id":response["id"]}

    return requests.post(url, data=json.dumps(data), headers=headers, verify=False).text


class Unit(NotEnglishAndPrintableUnit, CryptoUnit):

    GROUPS = ["crypto", "quipquip", "substitution"]
    """
    These are "tags" for a unit. Considering it is a Crypto unit, "crypto"
    is included, and the name of the unit and some other related topics.
    """

    BLOCKED_GROUPS = ["crypto"]
    """
    These are tags for groups to not recurse into. Recursing into other crypto units
    would be silly.
    """

    PRIORITY = 60
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a slightly
    lower priority.
    """

    RECURSE_SELF = False
    """
    This unit **does not recurse**. It simply looks for flags in the output of
    quipqiup's best potential solution.
    """

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)
        try:
            self.raw_target = self.target.stream.read().decode("utf-8")
        except UnicodeDecodeError:
            raise units.NotApplicable("unicode error, unlikely usable cryptogram")

        try:
            requests.get(
                "https://quipqiup.com/", verify=False
            )
        except requests.exceptions.ConnectionError:
            raise NotApplicable("cannot reach quipqiup solver")

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.

        :param case: A case returned by ``enumerate``. For this unit, the \
        ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        with io.TextIOWrapper(self.target.stream, encoding="utf-8") as stream:

            j = json.loads(decodeSubstitute(stream.read()))

            found_solution = ""
            best_score = -10
            for sol in j["solutions"]:
                if sol["logp"] > best_score:
                    found_solution = sol["plaintext"]
                    best_score = sol["logp"]

            self.manager.register_data(self, found_solution)
