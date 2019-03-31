from unit import BaseUnit
from esoteric import EsotericUnit
from collections import Counter
import sys
from io import StringIO
import argparse
import os
from pwn import *

# JOHN: Below is part of Caleb's old code. I am keeping it here for
#       preservation's sake.
#
# def BrainfuckMap(m):
#     if len(m) != 8:
#         raise argparse.ArgumentTypeError('{0}: not a valid brainfuck mapping (expected 8 commands)')
#     if len(Counter(m)) != len(m):
#         raise argparse.ArgumentTypeError('{0}: repeating characters are not allowed in brainfuck mapping')
#     return m

def cleanup(code):
    return ''.join(filter(lambda x: x in ['.', ',', '[', ']', '<', '>', '+', '-'], code))


def buildbracemap(code):
    temp_bracestack, bracemap = [], {}

    for position, command in enumerate(code):
        if command == "[": 
            temp_bracestack.append(position)
        if command == "]":
            start = temp_bracestack.pop()
            bracemap[start] = position
            bracemap[position] = start
    return bracemap

def evaluate_brainfuck(code):
# def evaluate_brainfuck(code, mapping='><+-.,[]', infile=sys.stdin):
    output = []
    code    = cleanup(list(code))
    bracemap = buildbracemap(code)

    cells, codeptr, cellptr = [0], 0, 0

    while codeptr < len(code):
        command = code[codeptr]

        if command == ">":
            cellptr += 1
            if cellptr == len(cells): cells.append(0)

        if command == "<":
            cellptr = 0 if cellptr <= 0 else cellptr - 1

        if command == "+":
            cells[cellptr] = cells[cellptr] + 1 if cells[cellptr] < 255 else 0

        if command == "-":
            cells[cellptr] = cells[cellptr] - 1 if cells[cellptr] > 0 else 255

        if command == "[" and cells[cellptr] == 0: codeptr = bracemap[codeptr]
        if command == "]" and cells[cellptr] != 0: codeptr = bracemap[codeptr]
        if command == ".": output.append(chr(cells[cellptr]))
        if command == ",": cells[cellptr] = sys.stdin.read(1)

        codeptr += 1
    
    return ''.join(output)


class Unit(EsotericUnit):

    @classmethod
    def prepare_parser(cls, config, parser):
        pass

        # JOHN: Below is Caleb's code.
        #       I did not get these to work with the new interpreter
        parser.add_argument('--bf-file', action='store_true', default=False, help='target specifies a file name')
        # parser.add_argument('--bf-map', default='><+-.,[]', type=BrainfuckMap, help='the mapping for brainfuck commands')
        # parser.add_argument('--bf-input', default=StringIO(''), type=argparse.FileType('r'), help='the file to use for input')

    def evaluate(self, target):

        print(target)
        if self.config['bf_file'] or os.path.isfile(target):
            with open(target, 'r') as f:
                target = f.read()
        else:
            target = target.lstrip()

        try:
            output = evaluate_brainfuck(target)
            self.find_flags(output)

            # JOHN: Again, this is from Caleb's old code.
            # output = evaluate_brainfuck(target, self.config['bf_map'], self.config['bf_input'])
        except ValueError:
            log.warning('{0}: invalid brainfuck command detected')
            return None

        return output

