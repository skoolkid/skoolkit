#!/usr/bin/env python3

import sys
import os.path
import argparse

def run(infile, options):
    ignore_lines = []
    if options.ignore_lines and os.path.isfile(options.ignore_lines):
        with open(options.ignore_lines) as f:
            ignore_lines = [line.rstrip('\n') for line in list(f)]
    c = c_ignore = 0
    with open(infile) as f:
        for line in f:
            s_line = line.rstrip('\n')
            if len(s_line) >= 80:
                if s_line in ignore_lines:
                    c_ignore += 1
                else:
                    if options.print_lines:
                        print(s_line)
                    c += 1
    sys.stderr.write("{} line(s) of length >= 80 found\n".format(c + c_ignore))
    if options.ignore_lines:
        sys.stderr.write("{} line(s) of length >= 80 ignored\n".format(c_ignore))
    return 1 if c else 0

###############################################################################
# Begin
###############################################################################
parser = argparse.ArgumentParser(
    usage='count80.py [options] FILE',
    description="Count the lines of length 80 or more in FILE.",
    add_help=False
)
parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-i', dest='ignore_lines', metavar='FILE',
                   help='Ignore lines that match those in this file')
group.add_argument('-p', dest='print_lines', action='store_true',
                   help='Print lines of length 80 or more')
namespace, unknown_args = parser.parse_known_args()
infile = namespace.infile
if unknown_args or infile is None:
    parser.exit(2, parser.format_help())
sys.exit(run(infile, namespace))
