#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

def parse_args(args):
    show_lines = False
    p_args = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-v':
            show_lines = True
        elif arg.startswith('-'):
            show_usage()
        else:
            p_args.append(arg)
        i += 1
    if len(p_args) != 1:
        show_usage()
    return show_lines, p_args[0]

def show_usage():
    sys.stderr.write("""Usage: {} [options] FILE

  Count the lines of length 80 or more in FILE.

Available options:
  -v  Print lines of length 80 or more
""".format(os.path.basename(sys.argv[0])))
    sys.exit(1)

show_lines, fname = parse_args(sys.argv[1:])

c = 0
with open(fname) as f:
    for line in f:
        s = line.rstrip('\n')
        if len(s) >= 80:
            if show_lines:
                print(s)
            c += 1
sys.stderr.write("{} lines of length >= 80 found\n".format(c))
