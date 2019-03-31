from unit import BaseUnit
from esoteric import EsotericUnit
from collections import Counter
import sys
from io import StringIO
import argparse
import os
from pwn import *
import math

# JOHN: This code is shamelessly stolen from https://github.com/kmyk/malbolge-interpreter

def isword(x):
    return 0 <= x < 3**10
def unword(x):
    assert isword(x)
    y = []
    for _ in range(10):
        y += [ x % 3 ]
        x //= 3
    return list(reversed(y))
def word(ys):
    x = 0
    for i, y in enumerate(ys):
        assert 0 <= y < 3
        x = x * 3 + y
    assert i+1 == 10
    return x
def tri(x):
    return '0t' + ''.join(map(str, unword(x)))
def rotr(x):
    assert isword(x)
    return (x // 3) + (x % 3 * 3**9)
def crz(xs, ys):
    table = [
        [ 1, 0, 0 ],
        [ 1, 0, 2 ],
        [ 2, 2, 1 ] ]
    return word(map(lambda x, y: table[y][x], unword(xs), unword(ys)))

xlat1 = "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha"
xlat2 = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
assert len(xlat1) == len(xlat2) == 94
def crypt1(i, m):
    assert 32 < ord(m) < 127
    return xlat1[(ord(m) - 33 + i) % 94]
def crypt2(m):
    assert 32 < ord(m) < 127
    return xlat2[ord(m) - 33]
def decrypt1(i, c):
    return chr((xlat1.index(c) - i) % 94 + 33)

def initial_memory(code, allow_not_isprint=False):
    mem = [ 0 ] * (3**10)
    i = 0
    for c in code:
        c = ord(c)
        if chr(c).isspace():
            continue
        if 32 < c < 127:
            assert crypt1(i, chr(c)) in 'ji*p</vo' # 'invalid character in source file'
        else:
            assert allow_not_isprint
        assert i <= 3**10
        mem[i] = c
        i += 1
    return mem
def execute_step(a, c, d, mem, inf=sys.stdin.buffer, outf=sys.stdout.buffer):
    output = []
    if not (32 < mem[c] < 127):
        raise # loop
    m = crypt1(c, chr(mem[c]))
    if   m == 'j':
        d = mem[d]
    elif m == 'i':
        c = mem[d]
    elif m == '*':
        a = mem[d] = rotr(mem[d])
    elif m == 'p':
        a = mem[d] = crz(a, mem[d])
    elif m == '<':
        # outf.write(bytes([ a % 256 ]))
        output.append(chr( a % 256 ))
    elif m == '/':
        x = inf.read(1)
        if x:
            a, = x
        else:
            a = (-1) % (3**10)
    elif m == 'v':
        raise StopIteration
    mem[c] = ord(crypt2(chr(mem[c])))
    c = (c + 1) % (3**10)
    d = (d + 1) % (3**10)

    return a, c, d, mem, output
def execute(code, inf=sys.stdin.buffer, allow_not_isprint=False, debug=False):
    output = []
    mem = initial_memory(code, allow_not_isprint=allow_not_isprint)
    a, c, d = 0, 0, 0
    while True:
        if debug:
            # I don't intend to use this but left it in here for preservations sake
            print('\tA: {} ({}),  C: {},  D: {},  [C]: {} ({}),  [D]: {} ({})'.format(tri(a)[2:], str(a).rjust(5), str(c).rjust(5), str(d).rjust(5), tri(mem[c])[2:], crypt1(c, chr(mem[c])), tri(mem[d])[2:], str(mem[d]).rjust(5)))
        try:
            a, c, d, mem, one_output = execute_step(a, c, d, mem, inf=inf)
            output += one_output
        except StopIteration:
            return ''.join(output)
            break
    
    
class Unit(EsotericUnit):

    @classmethod
    def prepare_parser(cls, config, parser):
        pass

        # JOHN: Below is Caleb's code.
        #       I did not get these to work with the new interpreter
        parser.add_argument('--mal-file', action='store_true', default=False, help='target specifies a file name')
        # parser.add_argument('--bf-map', default='><+-.,[]', type=BrainfuckMap, help='the mapping for brainfuck commands')
        parser.add_argument('--mal-input', default=sys.stdin, type=argparse.FileType('r'), help='the file to use for input')

    def evaluate(self, target):

        if self.config['mal_file'] or os.path.isfile(target):
            with open(target, 'r') as f:
                target = f.read()
        else:
            target = target.lstrip()

        try:
            output = execute(target,self.config['mal_input'])

        except ValueError:
            log.warning('{0}: invalid malbolge command detected')
            return None

        self.find_flags(output)
        return output