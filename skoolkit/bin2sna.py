# -*- coding: utf-8 -*-

# Copyright 2016 Richard Dymond (rjdymond@gmail.com)
#
# This file is part of SkoolKit.
#
# SkoolKit is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# SkoolKit is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# SkoolKit. If not, see <http://www.gnu.org/licenses/>.

import os
import argparse

from skoolkit import read_bin_file, VERSION
from skoolkit.snapshot import make_z80_ram_block, set_z80_registers, set_z80_state

def _get_z80(ram, org):
    z80 = [0] * 86
    z80[30] = 54 # Indicate a v3 Z80 snapshot
    set_z80_registers(z80, 'i=63', 'iy=23610', 'sp={}'.format(org), 'pc={}'.format(org))
    set_z80_state(z80, 'iff=1', 'im=1')
    for bank, data in ((5, ram[:16384]), (1, ram[16384:32768]), (2, ram[32768:49152])):
        z80 += make_z80_ram_block(data, bank + 3)
    return z80

def _write_z80(infile, outfile):
    ram = list(read_bin_file(infile, 49152))
    org = 65536 - len(ram)
    ram = [0] * (49152 - len(ram)) + ram
    parent_dir = os.path.dirname(outfile)
    if parent_dir and not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)
    with open(outfile, 'wb') as f:
        f.write(bytearray(_get_z80(ram, org)))

def main(args):
    parser = argparse.ArgumentParser(
        usage='bin2sna.py [options] file.bin [file.z80]',
        description="Convert a binary (raw memory) file into a Z80 snapshot. "
                    "If 'file.z80' is not given, it defaults to the name of the input file with '.bin' replaced by '.z80'.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('outfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit')
    namespace, unknown_args = parser.parse_known_args(args)
    infile = namespace.infile
    if unknown_args or infile is None:
        parser.exit(2, parser.format_help())
    outfile = namespace.outfile
    if outfile is None:
        if infile.lower().endswith('.bin'):
            outfile = infile[:-3] + 'z80'
        else:
            outfile = infile + '.z80'
    _write_z80(infile, outfile)
