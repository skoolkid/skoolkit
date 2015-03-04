#!/usr/bin/env python
import sys
import argparse

def run(infile, options):
    c = 0
    with open(infile) as f:
        for line in f:
            s = line.rstrip('\n')
            if len(s) >= 80:
                if options.print_lines:
                    print(s)
                c += 1
    sys.stderr.write("{} line(s) of length >= 80 found\n".format(c))
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
group.add_argument('-p', dest='print_lines', action='store_true',
                   help='Print lines of length 80 or more')
namespace, unknown_args = parser.parse_known_args()
infile = namespace.infile
if unknown_args or infile is None:
    parser.exit(2, parser.format_help())
sys.exit(run(infile, namespace))
