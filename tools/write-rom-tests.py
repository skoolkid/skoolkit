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

SNAPSHOT = '/usr/share/spectrum-roms/48.rom'

CTL = '{}/examples/48.rom.ctl'.format(SKOOLKIT_HOME)

REF = '{}/examples/48.rom.ref'.format(SKOOLKIT_HOME)

OUTPUT = """Using skool file: {skoolfile}
Using ref file: {reffile}
Parsing {skoolfile}
Creating directory {odir}/rom
Copying {SKOOLKIT_HOME}/skoolkit/resources/skoolkit.css to {odir}/rom/skoolkit.css
  Writing disassembly files in rom/asm
  Writing rom/maps/all.html
  Writing rom/maps/routines.html
  Writing rom/maps/data.html
  Writing rom/maps/messages.html
  Writing rom/maps/unused.html
  Writing rom/reference/changelog.html
  Writing rom/index.html"""

write_tests(snapshot=SNAPSHOT, output=OUTPUT, ctl=CTL, org=0, ref=REF, clean=False)
