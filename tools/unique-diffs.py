#!/usr/bin/env python3
import os
import sys

diffs = []
for fname in sys.argv[1:]:
    if not os.path.isfile(fname):
        continue
    with open(fname) as f:
        diff = []
        for line in f:
            s_line = line.strip()
            if s_line:
                diff.append(s_line)
            elif diff:
                if diff not in diffs:
                    diffs.append(diff)
                    print('\n'.join(diff + ['']))
                diff = []
