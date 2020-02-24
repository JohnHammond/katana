"""
RSA decryptor

This takes arguments "e", "n", "q", "p", "dq", "dp", "d", "c", "phi",
though they will potentially be automatically decoded by the program
if a plaintext file is supplied.

"""

import io
from typing import Any

import binascii
import decimal

import primefac
import gmpy
from Crypto.Util.number import inverse, long_to_bytes
from OpenSSL import crypto
import re

from katana import util
from katana.unit import NotEnglishUnit, NotApplicable


def rational_to_contfrac(x: int, y: int) -> list:
    """
    This function is used for the Weiner's Little D attack.

    Converts a rational x/y fraction into a list of partial quotients [a0, ..., an]

    :param x: The numerator of the provided fraction.

    :param y: The denominator of the provided fraction.

    :return: a list of partial quotients.
    """

    a = x // y
    pquotients = [a]
    while a * y != x:
        x, y = y, x - a * y
        a = x // y
        pquotients.append(a)
    return pquotients


def convergents_from_contfrac(frac: list) -> list:
    """
    This function is used for the Weiner's Little D attack.

    Computes the list of convergents using the list of partial quotients

    :param frac: Fractions represented by a list

    :return: A list of convergents
    """

    convs = []
    for i in range(len(frac)):
        convs.append(contfrac_to_rational(frac[0:i]))
    return convs


def contfrac_to_rational(frac: list):
    """
    This function is used for the Weiner's Little D attack.

    Converts a finite continued fraction ``[a0, ..., an]`` to an x/y rational.
    """

    if len(frac) == 0:
        return 0, 1
    num = frac[-1]
    denom = 1
    for _ in range(-2, -len(frac) - 1, -1):
        num, denom = frac[_] * num + denom, num
    return num, denom


def egcd(a, b):
    """
    This function is used for the Weiner's Little D attack.

    Determines the Euclidean Greatest Common Denominator between 
    given values.

    :param a: One value to be used to find the GCD for.

    :param b: Another value to be used to find the GCD for.

    :return: 
    """

    if a == 0:
        return b, 0, 1
    g, x, y = egcd(b % a, a)
    return g, y - (b // a) * x, x


def mod_inv(a, m):
    """
    This function is used for the Weiner's Little D attack.

    Deterine the modular inverse, given a base and the modulus.

    :param a: The base to use for the modular inverse operation.

    :param m: The modulus to use for the modular inverse operation.

    :return: An integer as the result of the modular inverse.

    """
    g, x, _ = egcd(a, m)
    return (x + m) % m


def isqrt(n):
    """
    This function is used for the Weiner's Little D attack.

    Determines the integer square root of a nunber.

    :param n: The number to determine the integer square root of.

    :return: The resulting integer square root.

    """
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


def find_cube_root(n):
    """
    This function is used for the Cube Root attack.

    Determines the cube root of a number.

    :param n: The number to determine the cube root of.

    :return: The resulting cube root.

    """
    lo = 0
    hi = n
    while lo < hi:
        mid = (lo + hi) // 2
        if mid ** 3 < n:
            lo = mid + 1
        else:
            hi = mid
    return lo


def weiners_little_d(e, n):
    """
    This function is used for the Weiner's Little D attack.

    Actually 

    :param e: The RSA e-value (exponent).

    :param n: The RSA N-value (modulus).

    :return: The determined RSA d-value (private key) after the \
    Weiner's Little D attack.

    """
    frac = rational_to_contfrac(e, n)
    convergents = convergents_from_contfrac(frac)

    for (k, d) in convergents:
        if k != 0 and (e * d - 1) % k == 0:
            phi = (e * d - 1) // k
            s = n - phi + 1
            # check if x*x - s*x + n = 0 has integer roots
            D = s * s - 4 * n
            if D >= 0:
                sq = isqrt(D)
                if sq * sq == D and (s + sq) % 2 == 0:
                    return d


# ---------------------------------------


def find_variables(text):
    """
    This is used to detect variables in a given file, or handle a given \
    pubkey. 

    :param text: The string to pull the variables from.

    :return: A Generator for an RSA letter variable and its value.

    """

    # First, check if this is a public key file.
    beginning_pubkey = re.search(
        "^-----BEGIN.*?-----\s", text, re.MULTILINE | re.DOTALL
    )
    ending_pubkey = re.search("-----END.*?-----\s*$", text, re.MULTILINE | re.DOTALL)

    if beginning_pubkey and ending_pubkey:
        pubkey = text[beginning_pubkey.start() : ending_pubkey.end()]

        pubkey = crypto.load_publickey(crypto.FILETYPE_PEM, pubkey)
        rsakey = pubkey.to_cryptography_key().public_numbers()
        values = (["n", rsakey.n], ["e", rsakey.e])
        for letter, value in values:
            yield letter, value

        return  # We can assume we won't find any other variables....

    matches = [
        "N",
        "exponent",
        "ciphertext",
        "ct",
        "message",
        "dq",
        "dp",
        "d",
        "p",
        "phi",
        "q",
        "totient",
    ]
    for m in matches:
        match = re.search(
            r"({0})({1})?\)?\s*[=:]\s*(.*)".format(m[0], m[1:]), text, re.IGNORECASE
        )

        if match:
            letter = match.groups()[0].lower()
            middle = match.groups()[1]
            value = match.groups()[-1]

            if middle:
                middle = middle.lower()
                if letter.startswith("m") and middle.startswith("odulus"):
                    letter = "n"
                if letter.startswith("p") and middle.startswith("hi"):
                    letter = "phi"
                if letter.startswith("d") and middle.startswith("p"):
                    letter = "dp"
                if letter.startswith("d") and middle.startswith("q"):
                    letter = "dq"

            yield letter, value


def parse_int(given):
    """
    This function will parse out a Python value regardless of the
    representation a number is given in the provided string. It will
    detect hex or an integer form.

    :param given: The string information that potentially includes a \
    number.

    :return: The Python integer value found.
    """

    found = -1

    # If they did not set a value, just use -1 to say no real value
    if given is None:
        return found

    # If this is already a decimal integer, return it
    if isinstance(given, int):
        return given

    # Remove the trailing L if that is still present in the string
    if given.endswith("L"):
        given = given.rstrip("L")

    if not util.isprintable(given):
        given = binascii.hexlify(given)
    if given == "":
        return found
    try:
        found = int(given)
    except ValueError:
        try:
            found = int(given, 16)
        except (ValueError, TypeError):
            pass
    return found


class Unit(NotEnglishUnit):

    GROUPS = ["crypto", "rsa"]
    """
    These are "tags" for a unit. Considering it is a Crypto unit, "crypto"
    is included, and the name of the unit, "rsa".
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
    Do not recurse into self
    """

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        self.c = -1
        self.e = parse_int(self.get("e"))
        self.n = parse_int(self.get("n"))
        self.q = parse_int(self.get("q"))
        self.p = parse_int(self.get("p"))
        self.d = parse_int(self.get("d"))
        self.dq = parse_int(self.get("dq"))
        self.dp = parse_int(self.get("dp"))
        self.phi = parse_int(self.get("phi"))

        if self.get("c"):
            try:
                handle = open(self.get("c"), "rb")
                is_file = True
            except OSError:
                is_file = False

            if is_file:
                ciphertext_data = handle.read()
                self.c = parse_int(ciphertext_data)
                if self.c == -1:
                    raise NotApplicable("could not determine ciphertext from file")
            else:
                self.c = parse_int(self.get("c"))

        if self.target.is_file:
            try:
                self.raw_target = self.target.stream.read().decode("utf-8")
            except UnicodeDecodeError:
                raise NotApplicable("unicode error, must not be potential ciphertext")

            for finding in find_variables(self.raw_target):
                if finding:
                    vars(self)[finding[0]] = parse_int(finding[1])

        if self.c == -1:
            raise NotApplicable("no ciphertext determined")

    def evaluate(self, case: Any) -> None:
        """
        Evaluate the target.

        :param case: A case returned by ``enumerate``. For this unit, \
        the ``enumerate`` function is not used.

        :return: None. This function should return any data.
        """

        def factor_n():
            # if n is given but p and q are not, try TO factor n.
            if self.p == -1 and self.q == -1 and self.n != -1:
                factors = list([int(x) for x in primefac.factorint(self.n)])
                if len(factors) == 2:
                    self.p, self.q = factors
                elif len(factors) == 1:
                    raise NotImplemented("factordb could not factor this!")
                else:
                    raise NotImplemented("We need support for multifactor RSA!")

        # If we have d, c, and n, just decrypt!
        if self.d != -1 and self.c != -1 and self.n != -1:
            self.m = pow(self.c, self.d, self.n)
            result = long_to_bytes(self.m).decode()

            self.manager.register_data(self, result)
            return

        # If e is not given, assume it is the standard 65537
        if self.e == -1:
            self.e = 0x10001

        # if n is NOT given but p and q are, multiply them to get n
        if self.n == -1 and self.p != -1 and self.q != -1:
            self.n = self.p * self.q

        # if we have a differential RSA problem, try that first.
        if self.dp != -1 and self.dq != -1:
            # if we have n, but not p and q, try and factor n
            if self.n == -1 and self.p != -1 and self.q != -1:
                factor_n()

            # if we have p and q and dp and dq, we can try this attack.
            if self.q != -1 and self.p != -1:

                qinv = inverse(self.q, self.p)

                m1 = pow(self.c, self.dp, self.p)
                m2 = pow(self.c, self.dq, self.q)
                h = qinv * (m1 - m2)
                self.m = m2 + h * self.q

                result = long_to_bytes(self.m).decode()

                self.manager.register_data(self, result)
                return

        # If e is large, we might have a Weiner's Little D attack!
        if self.e > 0x10001 and self.n != -1:
            self.d = weiners_little_d(self.e, self.n)

            # Attempt to decrypt!!!
            self.m = pow(self.c, self.d, self.n)
            result = long_to_bytes(self.m).decode()

            self.manager.register_data(self, result)
            return

        # If e is 3, we can use a use a cubed root attack!
        if self.e == 3 and self.n != -1:
            self.m = find_cube_root(self.c)

            result = long_to_bytes(self.m).decode()

            self.manager.register_data(self, result)
            return

        factor_n()  # set self.p, and self.q

        # Now that all the given values are found, try to calcuate phi
        if self.phi == -1:
            self.phi = (self.q - 1) * (self.p - 1)

        # If d is not supplied (which is normal) calculate it
        if self.d == -1:
            self.d = inverse(self.e, self.phi)

        # Calculate message
        self.m = pow(self.c, self.d, self.n)

        result = long_to_bytes(self.m).decode()

        self.manager.register_data(self, result)
        return
