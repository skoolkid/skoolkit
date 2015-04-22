#!/usr/bin/env python
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

SNAPSHOT = '{}/build/hungry_horace.z80'.format(SKOOLKIT_HOME)

CTL = '{}/examples/hungry_horace.ctl'.format(SKOOLKIT_HOME)

REF = '{}/examples/hungry_horace.ref'.format(SKOOLKIT_HOME)

OUTPUT = """Creating directory {odir}
Using skool file: {skoolfile}
Using ref file: {reffile}
Parsing {skoolfile}
Creating directory {odir}/hungry_horace
Copying {SKOOLKIT_HOME}/skoolkit/resources/skoolkit.css to {odir}/hungry_horace/skoolkit.css
  Writing disassembly files in hungry_horace/asm
  Writing hungry_horace/maps/all.html
  Writing hungry_horace/maps/routines.html
  Writing hungry_horace/maps/data.html
  Writing hungry_horace/maps/messages.html
  Writing hungry_horace/maps/unused.html
  Writing hungry_horace/reference/changelog.html
  Writing hungry_horace/index.html"""

write_tests(snapshot=SNAPSHOT, output=OUTPUT, ctl=CTL, ref=REF, clean=False)
