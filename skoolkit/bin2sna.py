# Copyright 2016-2018, 2020, 2023 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import integer, read_bin_file, VERSION
from skoolkit.snapshot import Memory, poke, print_reg_help, print_state_help, write_snapshot

def bank(arg):
    bank, sep, bankfile = arg.partition(',')
    if not sep:
        raise argparse.ArgumentTypeError(f"invalid argument: '{arg}'")
    try:
        return (int(bank) % 8, bankfile)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid integer '{bank}' in '{arg}'")

def run(infile, outfile, options):
    ram = list(read_bin_file(infile, 0x20000))
    if len(ram) == 0x20000:
        org = 0
        memory = Memory(ram, page=options.page or 0)
    else:
        ram = ram[:49152]
        org = options.org or 65536 - len(ram)
        mem = [0] * org + ram + [0] * (65536 - org - len(ram))
        if options.page is None:
            memory = Memory(mem)
        else:
            banks = {
                5: mem[0x4000:0x8000],
                2: mem[0x8000:0xC000],
                options.page: mem[0xC000:]
            }
            for bank, f in options.bank:
                data = list(read_bin_file(f, 0x4000))
                banks[bank] = data + [0] * (0x4000 - len(data))
            mem = []
            for bank in range(8):
                mem.extend(banks.get(bank, [0] * 0x4000))
            memory = Memory(mem, page=options.page)
    state = [f'border={options.border}']
    if options.page is not None:
        state.append(f'7ffd={options.page}')
    if options.start is None:
        start = org
    else:
        start = options.start
    if options.stack is None:
        stack = org
    else:
        stack = options.stack
    for spec in options.pokes:
        poke(memory, spec)
    parent_dir = os.path.dirname(outfile)
    if parent_dir and not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)
    registers = [f'sp={stack}', f'pc={start}'] + options.reg
    write_snapshot(outfile, memory.contents(), registers, state + options.state)

def main(args):
    parser = argparse.ArgumentParser(
        usage='bin2sna.py [options] file.bin [OUTFILE]',
        description="Convert a binary (raw memory) file into an SZX or Z80 snapshot. "
                    "'file.bin' may be a regular file, or '-' for standard input. "
                    "If 'OUTFILE' is not given, it defaults to the name of the input file with '.bin' replaced by '.z80', "
                    "or 'program.z80' if reading from standard input.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('outfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('--bank', metavar='N,file', type=bank, action='append', default=[],
                       help="Load RAM bank N (0-7) from the named file. This option may be used multiple times.")
    group.add_argument('-b', '--border', dest='border', metavar='BORDER', type=int, default=7,
                       help="Set the border colour (default: 7).")
    group.add_argument('-o', '--org', dest='org', metavar='ORG', type=integer,
                       help="Set the origin address (default: 65536 minus the length of file.bin).")
    group.add_argument('--page', metavar='N', type=int, choices=range(8),
                       help="Specify the RAM bank (N=0-7) mapped to 49152 (0xC000) in the main input file. This option creates a 128K snapshot.")
    group.add_argument('-p', '--stack', dest='stack', metavar='STACK', type=integer,
                       help="Set the stack pointer (default: ORG).")
    group.add_argument('-P', '--poke', dest='pokes', metavar='[p:]a[-b[-c]],[^+]v', action='append', default=[],
                       help="POKE N,v in RAM bank p for N in {a, a+c, a+2c..., b}. "
                            "Prefix 'v' with '^' to perform an XOR operation, or '+' to perform an ADD operation. "
                            "This option may be used multiple times.")
    group.add_argument('-r', '--reg', dest='reg', metavar='name=value', action='append', default=[],
                       help="Set the value of a register. Do '--reg help' for more information. This option may be used multiple times.")
    group.add_argument('-s', '--start', dest='start', metavar='START', type=integer,
                       help="Set the address at which to start execution (default: ORG).")
    group.add_argument('-S', '--state', dest='state', metavar='name=value', action='append', default=[],
                       help="Set a hardware state attribute. Do '--state help' for more information. This option may be used multiple times.")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    namespace, unknown_args = parser.parse_known_args(args)
    if 'help' in namespace.reg:
        print_reg_help('r')
        return
    if 'help' in namespace.state:
        print_state_help('S')
        return
    infile = namespace.infile
    if unknown_args or infile is None:
        parser.exit(2, parser.format_help())
    outfile = namespace.outfile
    if outfile is None:
        if infile.lower().endswith('.bin'):
            outfile = os.path.basename(infile)[:-3] + 'z80'
        elif infile == '-':
            outfile = 'program.z80'
        else:
            outfile = os.path.basename(infile) + '.z80'
    run(infile, outfile, namespace)
