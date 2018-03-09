# Copyright 2015-2018 Richard Dymond (rjdymond@gmail.com)
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

import argparse

from skoolkit import SkoolParsingError, get_int_param, info, integer, open_file, warn, VERSION
from skoolkit.skoolparser import read_skool
from skoolkit.skoolsft import VALID_CTLS
from skoolkit.textutils import find_unquoted, partition_unquoted
from skoolkit.z80 import assemble

SKIP_BLOCKS = ('d', 'r')

class BinWriter:
    def __init__(self, skoolfile, asm_mode=0, fix_mode=0):
        self.asm_mode = asm_mode
        self.fix_mode = fix_mode
        self.snapshot = [0] * 65536
        self.base_address = len(self.snapshot)
        self.end_address = 0
        self.subs = [None] * 4
        self._parse_skool(skoolfile)

    def _parse_skool(self, skoolfile):
        f = open_file(skoolfile)
        for block in read_skool(f, 0, self.asm_mode, self.fix_mode):
            for line in block:
                if line.lstrip().startswith(';'):
                    continue
                if line.startswith('@'):
                    self._parse_asm_directive(line[1:])
                    continue
                if line.startswith(SKIP_BLOCKS):
                    break
                if line[0] in VALID_CTLS:
                    self._parse_instruction(line)
        f.close()

    def _parse_instruction(self, line):
        try:
            address = get_int_param(line[1:6])
        except ValueError:
            raise SkoolParsingError("Invalid address ({}):\n{}".format(line[1:6], line.rstrip()))
        for sub in self.subs:
            if sub is not None:
                operation = sub
                self.subs = [None] * 4
                break
        else:
            comment_index = find_unquoted(line, ';', 6)
            operation = line[7:comment_index].strip()
        data = assemble(operation, address)
        if data:
            end_address = address + len(data)
            self.snapshot[address:end_address] = data
            self.base_address = min(self.base_address, address)
            self.end_address = max(self.end_address, end_address)
        else:
            warn("Failed to assemble:\n {} {}".format(address, operation))

    def _parse_asm_directive(self, directive):
        if directive.startswith('isub=') and self.asm_mode > 0:
            self.subs[3] = partition_unquoted(directive[5:], ';')[0].rstrip()
        elif directive.startswith('ssub=') and self.asm_mode > 1:
            self.subs[2] = partition_unquoted(directive[5:], ';')[0].rstrip()
        elif directive.startswith('ofix=') and self.fix_mode > 0:
            self.subs[1] = partition_unquoted(directive[5:], ';')[0].rstrip()
        elif directive.startswith('bfix=') and self.fix_mode > 1:
            self.subs[0] = partition_unquoted(directive[5:], ';')[0].rstrip()

    def write(self, binfile, start, end):
        if start is None:
            base_address = self.base_address
        else:
            base_address = start
        if end is None:
            end_address = self.end_address
        else:
            end_address = end
        data = self.snapshot[base_address:end_address]
        with open_file(binfile, 'wb') as f:
            f.write(bytearray(data))
        if binfile == '-':
            binfile = 'stdout'
        info("Wrote {}: start={}, end={}, size={}".format(binfile, base_address, end_address, len(data)))

def run(skoolfile, binfile, options):
    binwriter = BinWriter(skoolfile, options.asm_mode, options.fix_mode)
    binwriter.write(binfile, options.start, options.end)

def main(args):
    parser = argparse.ArgumentParser(
        usage='skool2bin.py [options] file.skool [file.bin]',
        description="Convert a skool file into a binary (raw memory) file. "
                    "'file.skool' may be a regular file, or '-' for standard input. "
                    "If 'file.bin' is not given, it defaults to the name of the input file with '.skool' replaced by '.bin'. "
                    "'file.bin' may be a regular file, or '-' for standard output.",
        add_help=False
    )
    parser.add_argument('skoolfile', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('binfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-b', '--bfix', dest='fix_mode', action='store_const', const=2, default=0,
                       help="Apply @ofix and @bfix directives.")
    group.add_argument('-E', '--end', dest='end', metavar='ADDR', type=integer,
                       help='Stop converting at this address.')
    group.add_argument('-i', '--isub', dest='asm_mode', action='store_const', const=1, default=0,
                       help="Apply @isub directives.")
    group.add_argument('-o', '--ofix', dest='fix_mode', action='store_const', const=1, default=0,
                       help="Apply @ofix directives.")
    group.add_argument('-s', '--ssub', dest='asm_mode', action='store_const', const=2, default=0,
                       help="Apply @isub and @ssub directives.")
    group.add_argument('-S', '--start', dest='start', metavar='ADDR', type=integer,
                       help='Start converting at this address.')
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    namespace, unknown_args = parser.parse_known_args(args)
    skoolfile = namespace.skoolfile
    if unknown_args or skoolfile is None:
        parser.exit(2, parser.format_help())

    binfile = namespace.binfile
    if binfile is None:
        if skoolfile.lower().endswith('.skool'):
            binfile = skoolfile[:-6] + '.bin'
        elif skoolfile == '-':
            binfile = 'program.bin'
        else:
            binfile = skoolfile + '.bin'
    run(skoolfile, binfile, namespace)
