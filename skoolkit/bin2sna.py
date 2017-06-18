# Copyright 2016-2017 Richard Dymond (rjdymond@gmail.com)
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
from skoolkit.snapshot import write_z80v3

def run(infile, outfile, options):
    ram = list(read_bin_file(infile, 49152))
    org = options.org or 65536 - len(ram)
    ram = [0] * (org - 16384) + ram + [0] * (65536 - org - len(ram))
    if options.start is None:
        start = org
    else:
        start = options.start
    if options.stack is None:
        stack = org
    else:
        stack = options.stack
    parent_dir = os.path.dirname(outfile)
    if parent_dir and not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)
    registers = ('sp={}'.format(stack), 'pc={}'.format(start))
    state = ('border={}'.format(options.border),)
    write_z80v3(outfile, ram, registers, state)

def main(args):
    parser = argparse.ArgumentParser(
        usage='bin2sna.py [options] file.bin [file.z80]',
        description="Convert a binary (raw memory) file into a Z80 snapshot. "
                    "'file.bin' may be a regular file, or '-' for standard input. "
                    "If 'file.z80' is not given, it defaults to the name of the input file with '.bin' replaced by '.z80', "
                    "or 'program.z80' if reading from standard input.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('outfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-b', '--border', dest='border', metavar='BORDER', type=int, default=7,
                       help="Set the border colour (default: 7)")
    group.add_argument('-o', '--org', dest='org', metavar='ORG', type=int,
                       help="Set the origin address (default: 65536 minus the length of file.bin)")
    group.add_argument('-p', '--stack', dest='stack', metavar='STACK', type=int,
                       help="Set the stack pointer (default: ORG)")
    group.add_argument('-s', '--start', dest='start', metavar='START', type=int,
                       help="Set the address at which to start execution (default: ORG)")
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
        elif infile == '-':
            outfile = 'program.z80'
        else:
            outfile = infile + '.z80'
    run(infile, outfile, namespace)
