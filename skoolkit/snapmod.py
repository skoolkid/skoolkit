# Copyright 2015-2017 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import SkoolKitError, get_word, read_bin_file, write_line, VERSION
from skoolkit.snapshot import (get_snapshot, make_z80_ram_block, make_z80v3_ram_blocks,
                               move, poke, print_reg_help, print_state_help,
                               set_z80_registers, set_z80_state)

def _read_z80(z80file):
    data = read_bin_file(z80file)
    if get_word(data, 6) > 0:
        header = data[:30]
    else:
        header_len = 32 + get_word(data, 30)
        header = data[:header_len]
    return list(header), get_snapshot(z80file)

def _write_z80(header, snapshot, fname):
    if len(header) == 30:
        header[12] |= 32
        ram = make_z80_ram_block(snapshot[16384:], 0)[3:] + [0, 237, 237, 0]
    else:
        ram = make_z80v3_ram_blocks(snapshot[16384:])
    with open(fname, 'wb') as f:
        f.write(bytearray(header + ram))

def run(infile, options, outfile):
    header, snapshot = _read_z80(infile)
    for spec in options.moves:
        move(snapshot, spec)
    for spec in options.pokes:
        poke(snapshot, spec)
    set_z80_registers(header, *options.reg)
    set_z80_state(header, *options.state)
    _write_z80(header, snapshot, outfile)

def main(args):
    parser = argparse.ArgumentParser(
        usage='snapmod.py [options] in.z80 [out.z80]',
        description="Modify a 48K Z80 snapshot.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('outfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-f', '--force', dest='force', action='store_true',
                       help="Overwrite an existing snapshot.")
    group.add_argument('-m', '--move', dest='moves', metavar='src,size,dest', action='append', default=[],
                       help='Move a block of bytes of the given size from src to dest. This option may be used multiple times.')
    group.add_argument('-p', '--poke', dest='pokes', metavar='a[-b[-c]],[^+]v', action='append', default=[],
                       help="POKE N,v for N in {a, a+c, a+2c..., b}. "
                            "Prefix 'v' with '^' to perform an XOR operation, or '+' to perform an ADD operation. "
                            "This option may be used multiple times.")
    group.add_argument('-r', '--reg', dest='reg', metavar='name=value', action='append', default=[],
                       help="Set the value of a register. Do '--reg help' for more information. This option may be used multiple times.")
    group.add_argument('-s', '--state', dest='state', metavar='name=value', action='append', default=[],
                       help="Set a hardware state attribute. Do '--state help' for more information. This option may be used multiple times.")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    namespace, unknown_args = parser.parse_known_args(args)
    if 'help' in namespace.reg:
        print_reg_help('r')
        return
    if 'help' in namespace.state:
        print_state_help('s')
        return
    infile = namespace.infile
    outfile = namespace.outfile
    if unknown_args or infile is None:
        parser.exit(2, parser.format_help())
    if not infile.lower().endswith('.z80'):
        raise SkoolKitError('Unrecognised input snapshot type')

    if outfile is None:
        outfile = infile
    if namespace.force or not os.path.isfile(outfile):
        run(infile, namespace, outfile)
    else:
        write_line('{}: file already exists; use -f to overwrite'.format(outfile))
