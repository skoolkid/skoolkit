#!/usr/bin/env python
import sys
import argparse

def analyse(tap):
    i = 0
    block_num = 1
    indent = '   '
    while i < len(tap):
        block_len = tap[i] + 256 * tap[i + 1]
        marker = tap[i + 2]
        header = marker == 0
        print("{:02} {} ({})".format(block_num, 'Header' if header else 'Data', i))
        print("{}Block length: {}".format(indent, block_len))
        print("{}Marker byte: {}".format(indent, marker))
        if header:
            block_type = tap[i + 3]
            title = ''.join(chr(b) for b in tap[i + 4:i + 14])
            if block_type == 3:
                # Bytes
                print("{}Bytes: {}".format(indent, title))
                start = tap[i + 16] + 256 * tap[i + 17]
                print("{}Start: {}".format(indent, start))
            elif block_type == 0:
                # Program
                print("{}Program: {}".format(indent, title))
                line = tap[i + 16] + 256 * tap[i + 17]
                print("{}LINE: {}".format(indent, line))
            else:
                print('ERROR: Unknown block type ({}) in header at {}'.format(block_type, i))
                sys.exit(1)
            length = tap[i + 14] + 256 * tap[i + 15]
            print("{}Length: {}".format(indent, length))
        print("{}Parity byte: {}".format(indent, tap[i + block_len + 1]))
        i += block_len + 2
        block_num += 1

###############################################################################
# Begin
###############################################################################
parser = argparse.ArgumentParser(
    usage="analyse-tap.py FILE.tap",
    description="Show the blocks in a TAP file.",
    add_help=False
)
parser.add_argument('tapfile', help=argparse.SUPPRESS, nargs='?')
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.tapfile is None:
    parser.exit(2, parser.format_help())

with open(namespace.tapfile, 'rb') as f:
    tap = bytearray(f.read())

analyse(tap)
