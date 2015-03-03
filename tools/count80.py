#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

def parse_args(args):
    show_80s = False
    show_80_plus = False
    p_args = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-v':
            show_80s = True
        elif arg == '-V':
            show_80_plus = True
        elif arg.startswith('-'):
            show_usage()
        else:
            p_args.append(arg)
        i += 1
    if len(p_args) != 1:
        show_usage()
    return show_80s, show_80_plus, p_args[0]

def show_usage():
    sys.stderr.write("""Usage: {} [options] FILE

  Count the lines of length 80 or more in FILE.

Available options:
  -v  Print lines of length 80
  -V  Print lines of length > 80
""".format(os.path.basename(sys.argv[0])))
    sys.exit(1)

show_80s, show_80_plus, fname = parse_args(sys.argv[1:])

c = 0
d = 0
f = open(fname)
for line in f:
    s = line.rstrip()
    if len(s) == 80:
        if show_80s:
            print(s)
        c += 1
    elif len(s) > 80:
        if show_80_plus:
            print(s)
        d += 1
f.close()
print("{} lines of length = 80 found".format(c))
print("{} lines of length > 80 found".format(d))
