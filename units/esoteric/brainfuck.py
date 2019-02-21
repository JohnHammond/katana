from unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *

def BrainfuckMap(m):
    if len(m) != 8:
        raise argparse.ArgumentTypeError('{0}: not a valid brainfuck mapping (expected 8 commands)')
    if len(Counter(m)) != len(m):
        raise argparse.ArgumentTypeError('{0}: repeating characters are not allowed in brainfuck mapping')
    return m

def evaluate_brainfuck(prog, mapping='><+-.,[]', infile=sys.stdin):
        data, ptr = [0], 0
        ip = 0
        output = ''
    
        while True:
            # If we're done, get outa here!
            if ip >= len(prog):
                return output
    
            try:
                cmd = mapping.index(prog[ip])
            except ValueError as e:
                raise ValueError('{0}: invalid command'.format(prog[ip])) from e
    
            if cmd == 0:
                # Increase the pointer by 1
                ptr += 1
                if ptr >= len(data):
                    data.append(0)
            elif cmd == 1:
                # Decrease the pointer by 1
                ptr -= 1
            elif cmd == 2:
                # Increase value at pointer by 1
                data[ptr] = (data[ptr] + 1) % 256
            elif cmd == 3:
                # Decrease value at pointer by 1
                data[ptr] = (data[ptr] - 1) % 256
            elif cmd == 4:
                # Output the character the pointer
                output += chr(data[ptr])
            elif cmd == 5:
                # Read a byte from the user
                data[ptr] = infile.read(1)
            elif cmd == 6 and data[ptr] == 0:
                # Jump to next brace if data at pointer is zero
                ip = prog.find(mapping[7], ip)
            elif cmd == 7 and data[ptr] != 0:
                # Jump to previous brace if data at pointer is not zero
                ip = prog.rfind(mapping[6], 0, ip)
    
            ip += 1
    
        return output

class Unit(BaseUnit):

    @classmethod
    def prepare_parser(cls, config, parser):
        parser.add_argument('--bf-file', action='store_true', default=False, help='target specifies a file name')
        parser.add_argument('--bf-map', default='><+-.,[]', type=BrainfuckMap, help='the mapping for brainfuck commands')
        parser.add_argument('--bf-input', default=StringIO(''), type=argparse.FileType('r'), help='the file to use for input')

    def evaluate(self, target):
        if self.config['bf_file']:
            with open(target, 'r') as f:
                target = f.read()
        else:
            target = target.lstrip()

        try:
            output = evaluate_brainfuck(target, self.config['bf_map'], self.config['bf_input'])
        except ValueError:
            log.warning('{0}: invalid brainfuck command detected')
            return None

        return output

