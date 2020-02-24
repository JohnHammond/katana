"""
Pikalang esoteric decoder

This unit will map the Pikalang operations to their Brainfuck equivalant,
and then pass along the actual execution to the Brainfuck unit's
``evaluate_brainfuck`` function.

In the previous framework of Katana, this unit attempted to decode
Pikalang in seemingly TWO different variations. One was a literal mapping
to Brainfuck code, the other did something different that required much more 
code (https://github.com/joelsmithjohnson/pikachu-interpreter)

I have not translated that other code to use bytes, and I do not see the need
to do so currently, considering how obscure Pikalang is to begin with.
"""


from katana.unit import PrintableDataUnit, NotApplicable
from katana.units.esoteric.brainfuck import evaluate_brainfuck

import re

from typing import Any

p_mappings = [
    "pikachu",
    "pikapi",
    "pichu",
    "pika",
    "pipi",
    "chu",
    "ka",
    "pi",
]

r_mappings = [b".", b",", b"<", b"[", b">", b"]", b"-", b"+"]

regex_finder = "({})".format("|".join([x for x in p_mappings]))


class Unit(PrintableDataUnit):

    GROUPS = ["esoteric", "pikalang"]
    """
    These are "tags" for a unit. Considering it is a Esoteric unit,
    "esoteric" is included, as well as the unit name "pikalang".
    """

    PRIORITY = 40
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. Has a slightly higher
    priority
    """

    def __init__(self, *args, **kwargs):
        super(PrintableDataUnit, self).__init__(*args, **kwargs)

        # Grab the pikalang commands from the targets
        self.pika_commands = re.findall(bytes(regex_finder, "utf-8"), self.target.raw)

        if len(self.pika_commands) <= 5:
            raise NotApplicable("not enough pikalang")

    def evaluate(self, case: Any):
        """
        Evaluate the target. Run the target as Pikalang code and
        give the standard output results to Katana.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        # Convert the found pikalang commands to brainfuck
        new_brainfuck = []
        for p in self.pika_commands:
            new_brainfuck.append(r_mappings[p_mappings.index(p.decode("utf-8"))])

        # Try to run the brainfuck code
        try:
            output = evaluate_brainfuck(new_brainfuck, None)
        except (ValueError, TypeError):
            return  # if it fails, give up!

        if output:
            self.manager.register_data(self, output)
