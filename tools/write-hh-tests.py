#!/usr/bin/env python3

import sys
import os

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}: directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, '{}/tools'.format(SKOOLKIT_HOME))
from testwriter import write_tests

SNAPSHOT = 'build/hungry_horace.z80'

CTL = 'examples/hungry_horace.ctl'

REF = 'examples/hungry_horace.ref'

OUTPUT = """Using ref file: {reffile}
Parsing {skoolfile}
Output directory: {odir}/hungry_horace
Copying {SKOOLKIT_HOME}/skoolkit/resources/skoolkit.css to skoolkit.css
Writing disassembly files in asm
Writing maps/all.html
Writing maps/routines.html
Writing maps/data.html
Writing maps/messages.html
Writing maps/unused.html
Writing reference/changelog.html
Writing index.html"""

write_tests(snapshot=SNAPSHOT, output=OUTPUT, sources=False, ctl=CTL, ref=REF, clean=False)
