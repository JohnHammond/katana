"""
Unit to run code in the Malbolge esoteric language.

This code is shamelessly stolen from
https://github.com/kmyk/malbolge-interpreter. 
We do not claim to know everything that it does... it is Malbolge,
after all.


"""

from katana.unit import NotEnglishUnit

from typing import Any
import sys


def isword(x):
    """
    This function is used as part of Malbolge's operations.
    """
    return 0 <= x < 3 ** 10


def unword(x):
    """
    This function is used as part of Malbolge's operations.
    """
    assert isword(x)
    y = []
    for _ in range(10):
        y += [x % 3]
        x //= 3
    return list(reversed(y))


def word(ys):
    """
    This function is used as part of Malbolge's operations.
    """
    x = 0
    for i, y in enumerate(ys):
        assert 0 <= y < 3
        x = x * 3 + y
    assert i + 1 == 10
    return x


def tri(x):
    """
    This function is used as part of Malbolge's operations.
    """
    return "0t" + "".join(map(str, unword(x)))


def rotr(x):
    """
    This function is used as part of Malbolge's operations.
    """
    assert isword(x)
    return (x // 3) + (x % 3 * 3 ** 9)


def crz(xs, ys):
    """
    This function is used as part of Malbolge's operations.
    """
    table = [[1, 0, 0], [1, 0, 2], [2, 2, 1]]
    return word(map(lambda x, y: table[y][x], unword(xs), unword(ys)))


xlat1 = '+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA"lI.v%{gJh4G\\-=O@5`'
xlat1 += "_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha"
xlat2 = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.T"
xlat2 += "Vac`uY*MK'X~xDl}REokN:#?G\"i@"

assert len(xlat1) == len(xlat2) == 94


def crypt1(i, m):
    """
    This function is used as part of Malbolge's operations.
    """

    return xlat1[(ord(m) - 33 + i) % 94]


def crypt2(m):
    """
    This function is used as part of Malbolge's operations.
    """

    return xlat2[(ord(m) - 33) % len(xlat2)]


def decrypt1(i, c):
    """
    This function is used as part of Malbolge's operations.
    """
    return chr((xlat1.index(c) - i) % 94 + 33)


def initial_memory(code, allow_not_isprint=False):
    """
    This function is used as part of Malbolge's operations.
    """
    mem = [0] * (3 ** 10)
    i = 0
    for c in code:
        c = ord(c)
        if chr(c).isspace():
            continue
        if 32 < c < 127:
            # 'invalid character in source file'
            assert crypt1(i, chr(c)) in "ji*p</vo"
        else:
            assert allow_not_isprint
        assert i <= 3 ** 10
        mem[i] = c
        i += 1
    return mem


def execute_step(a, c, d, mem, inf=sys.stdin.buffer, outf=sys.stdout.buffer):
    """
    This function is used as part of Malbolge's operations.
    """
    output = []
    if not (32 < mem[c] < 127):
        raise StopIteration  # loop
    m = crypt1(c, chr(mem[c]))
    if m == "j":
        d = mem[d]
    elif m == "i":
        c = mem[d]
    elif m == "*":
        a = mem[d] = rotr(mem[d])
    elif m == "p":
        a = mem[d] = crz(a, mem[d])
    elif m == "<":
        # outf.write(bytes([ a % 256 ]))
        output.append(chr(a % 256))
    elif m == "/":
        if not inf:
            x = "\n"
        else:
            x = inf.read(1)

        if x:
            (a,) = x
        else:
            a = (-1) % (3 ** 10)
    elif m == "v":
        raise StopIteration
    mem[c] = ord(crypt2(chr(mem[c])))

    c = (c + 1) % (3 ** 10)
    d = (d + 1) % (3 ** 10)

    return a, c, d, mem, output


def execute(code, inf=sys.stdin.buffer, allow_not_isprint=False, debug=False):
    """
    This function is execute Malbolge code. 
    """
    output = []
    try:
        mem = initial_memory(code, allow_not_isprint=allow_not_isprint)

    except:
        # If this fails, it is probably not Malbolge. Stop trying.
        return None
        pass
    a, c, d = 0, 0, 0
    while True:
        try:
            a, c, d, mem, one_output = execute_step(a, c, d, mem, inf=inf)
            output += one_output
        except StopIteration:
            return "".join(output)


class Unit(NotEnglishUnit):

    GROUPS = ["esoteric", "malbolge"]
    """
    These are "tags" for a unit. Considering it is a Esoteric unit,
    "esoteric" is included, as well as the unit name "malbolge".
    """

    PRIORITY = 10
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a high
    priority.
    """

    def evaluate(self, case: Any):
        """
        Evaluate the target. Run the target as Malbolge code and
        return the standard output to Katana.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        try:
            output = execute(self.target.raw, self.get("input_file", default=None),)
        except (ValueError, AssertionError):
            return None

        if output:
            self.manager.register_data(self, output)
