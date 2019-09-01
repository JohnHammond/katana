import binascii
import decimal

import primefac
from Crypto.Util.number import inverse
from OpenSSL import crypto
from katana import units
from katana import utilities
from katana.units import NotApplicable
from pwn import *


## JOHN: These are functions for Weiner's Little D attack.
# -------------------------------------------
def rational_to_contfrac(x, y):
    # Converts a rational x/y fraction into a list of partial quotients [a0, ..., an]
    a = x // y
    pquotients = [a]
    while a * y != x:
        x, y = y, x - a * y
        a = x // y
        pquotients.append(a)
    return pquotients


def convergents_from_contfrac(frac):
    # computes the list of convergents using the list of partial quotients
    convs = []
    for i in range(len(frac)): convs.append(contfrac_to_rational(frac[0: i]))
    return convs


def contfrac_to_rational(frac):
    # Converts a finite continued fraction [a0, ..., an] to an x/y rational.
    if len(frac) == 0: return 0, 1
    num = frac[-1]
    denom = 1
    for _ in range(-2, -len(frac) - 1, -1): num, denom = frac[_] * num + denom, num
    return num, denom


def egcd(a, b):
    if a == 0: return b, 0, 1
    g, x, y = egcd(b % a, a)
    return g, y - (b // a) * x, x


def mod_inv(a, m):
    g, x, _ = egcd(a, m)
    return (x + m) % m


def isqrt(n):
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


def weiners_little_d(e, n):
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
                if sq * sq == D and (s + sq) % 2 == 0: return d


# ---------------------------------------


# JOHN: This is used to detect variables in a given file, or handle a given pubkey.
def find_variables(text):
    # First, check if this is a public key file.
    beginning_pubkey = re.search('^-----BEGIN.*?-----\s', text, re.MULTILINE | re.DOTALL)
    ending_pubkey = re.search('-----END.*?-----\s*$', text, re.MULTILINE | re.DOTALL)

    if beginning_pubkey and ending_pubkey:
        pubkey = text[beginning_pubkey.start():ending_pubkey.end()]

        pubkey = crypto.load_publickey(crypto.FILETYPE_PEM, pubkey)
        rsakey = pubkey.to_cryptography_key().public_numbers()
        values = (['n', rsakey.n], ['e', rsakey.e])
        for letter, value in values:
            yield letter, value

        return  # We can assume we won't find any other variables....
    matches = [
        'N',
        'exponent',
        'ciphertext',
        'message',
        'd',
        'p',
        'phi',
        'q',
        'totient',
    ]
    for m in matches:
        match = re.search(r'({0})({1})?\)?\s*[=:]\s*(.*)'.format(m[0], m[1:]), text, re.IGNORECASE)

        if match:
            letter = match.groups()[0].lower()
            middle = match.groups()[1]
            value = match.groups()[-1]

            if middle:
                middle = middle.lower()
                if letter.startswith('m') and middle.startswith('odulus'):
                    letter = 'n'
                if letter.startswith('p') and middle.startswith('hi'):
                    letter = 'phi'

            yield letter, value


def parse_int(given):
    if isinstance(given, int):
        return given
    found = -1

    if not utilities.isprintable(given):
        given = binascii.hexlify(given)
    if given == '':
        return found
    try:
        found = int(given)
    except ValueError:
        try:
            found = int(given, 16)
        except (ValueError, TypeError):
            pass
    return found


class Unit(units.NotEnglishUnit):
    PROTECTED_RECURSE = True
    PRIORITY = 60

    ARGUMENTS = [
        {'name': 'rsa_e',
         'type': str,
         'default': "",
         'required': False,
         'help': 'exponent value for RSA cryptography'
         },

        {'name': 'rsa_n',
         'type': str,
         'default': "",
         'required': False,
         'help': 'modulus value for RSA cryptography'
         },

        {'name': 'rsa_q',
         'type': str,
         'default': "",
         'required': False,
         'help': 'q factor for RSA cryptography'
         },

        {'name': 'rsa_p',
         'type': str,
         'default': "",
         'required': False,
         'help': 'p factor for RSA cryptography'
         },

        {'name': 'rsa_d',
         'type': str,
         'default': "",
         'required': False,
         'help': 'd value for RSA cryptography'
         },

        {'name': 'rsa_c',
         'type': str,
         'default': "",
         'required': False,
         'help': 'c value for RSA cryptography'
         },
    ]

    def __init__(self, katana, target):
        super(Unit, self).__init__(katana, target)

        if target.is_url:
            raise NotApplicable('target is a URL')

        # Extract all the variables out from the arguments, if they are supplied.
        # Since we need a ciphertext and that will be tested later, leave that empty.
        self.c = -1
        self.e = parse_int(katana.config['rsa_e'])
        self.n = parse_int(katana.config['rsa_n'])
        self.q = parse_int(katana.config['rsa_q'])
        self.p = parse_int(katana.config['rsa_p'])
        self.d = parse_int(katana.config['rsa_d'])
        self.phi = parse_int(katana.config['rsa_phi'])

        if katana.config['rsa_c']:
            try:
                handle = open(katana.config['rsa_c'], 'rb')
                is_file = True
            except OSError:
                is_file = False

            if is_file:
                ciphertext_data = handle.read()
                self.c = parse_int(ciphertext_data)
                if self.c == -1:
                    raise NotApplicable('could not determine ciphertext from file')
            else:
                self.c = parse_int(katana.config['rsa_c'])

        if self.target.is_file:
            try:
                self.raw_target = self.target.stream.read().decode('utf-8')
            except UnicodeDecodeError:
                raise NotApplicable('unicode error, must not be potential ciphertext')

            for finding in find_variables(self.raw_target):
                if finding:
                    vars(self)[finding[0]] = parse_int(finding[1])

        if self.c == -1:
            raise NotApplicable("no ciphertext determined")


    def evaluate(self, katana, case):

        # If e is not given, assume it is the standard 65537
        if self.e == -1:
            self.e = 0x10001

        # If e is large, we might have a Weiner's Little D attack!
        if self.e > 0x10001 and self.n != -1:
            self.d = weiners_little_d(self.e, self.n)

            # Attempt to decrypt!!!
            self.m = pow(self.c, self.d, self.n)
            try:
                result = binascii.unhexlify(hex(self.m)[2:].rstrip('L'))
            except binascii.Error:
                result = binascii.unhexlify(str('0' + hex(self.m)[2:].rstrip('L')))

            katana.add_results(self, result)
            katana.recurse(self, result)
            return

        # if n is NOT given but p and q are, multiply them to get n
        if self.n == -1 and self.p != -1 and self.q != -1:
            self.n = self.p * self.q

        # If e is only 3, we might have a cubed root attack!
        if self.e == 3 and self.n != -1:
            # Set laaaarrge precision
            decimal.getcontext().prec = 3000

            # The ciphertext must be in this new object form
            c_decimal = decimal.Decimal(str(self.c))

            # Take the cubed root of c to find the plaintext message
            self.m = c_decimal ** (decimal.Decimal('1') / 3)

            # This needs to be rounded... a fine cheap hack is just round up
            self.m = int(self.m) + 1

            try:
                result = binascii.unhexlify(hex(self.m)[2:].rstrip('L'))
            except binascii.Error:
                result = binascii.unhexlify(str('0' + hex(self.m)[2:].rstrip('L')))

            katana.add_results(self, result)
            katana.recurse(self, result)
            return

        # if n is given but p and q are not, try TO factor n.
        if self.p == -1 and self.q == -1 and self.n != -1:
            factors = list([int(x) for x in primefac.factorint(self.n)])
            if len(factors) == 2:
                self.p, self.q = factors
            else:
                if len(factors) == 1:
                    raise NotImplemented("factordb could not factor this!")
                else:
                    raise NotImplemented("We need support for multifactor RSA!")

            pass

        # Now that all the given values are found, try to calcuate phi
        self.phi = (self.q - 1) * (self.p - 1)

        # If d is not supplied (which is normal) calculate it
        if self.d == -1:
            self.d = inverse(self.e, self.phi)

        try:
            result = binascii.unhexlify(hex(self.m)[2:].rstrip('L'))
        except binascii.Error:
            result = binascii.unhexlify(str('0' + hex(self.m)[2:].rstrip('L')))

        katana.add_results(self, result)
        katana.recurse(self, result)