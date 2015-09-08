# -*- coding: utf-8 -*-

# Copyright 2015 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import SkoolParsingError, open_file, info, warn, get_int_param, VERSION
from skoolkit.skoolparser import parse_asm_block_directive
from skoolkit.skoolsft import VALID_CTLS
from skoolkit.textutils import find_unquoted
from skoolkit.z80 import assemble

SKIP_BLOCKS = ('d', 'r')

class BinWriter:
    def __init__(self, skoolfile, asm_mode=0):
        self.asm_mode = asm_mode
        self.snapshot = [0] * 65536
        self.base_address = len(self.snapshot)
        self.end_address = 0
        self.stack = []
        self.include = True
        self.sub = None
        self._parse_skool(skoolfile)

    def _parse_skool(self, skoolfile):
        entry_ctl = None
        f = open_file(skoolfile)
        for line in f:
            if line.startswith(';'):
                continue
            if line.startswith('@'):
                self._parse_asm_directive(line[1:].rstrip())
                continue
            if not self.include:
                continue
            s_line = line.strip()
            if not s_line:
                # This line is blank
                entry_ctl = None
                continue
            # Check whether we're in a block that can be skipped
            if entry_ctl is None and line.startswith(SKIP_BLOCKS):
                entry_ctl = line[0]
            if entry_ctl in SKIP_BLOCKS:
                continue
            if s_line.startswith(';'):
                # This line is a continuation of an instruction comment
                continue
            if line[0] in VALID_CTLS:
                # This line contains an instruction
                self._parse_instruction(line)
        f.close()

    def _parse_instruction(self, line):
        try:
            address = get_int_param(line[1:6])
        except ValueError:
            raise SkoolParsingError("Invalid address ({}):\n{}".format(line[1:6], line.rstrip()))
        if self.sub:
            operation = self.sub
            self.sub = None
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
        if parse_asm_block_directive(directive, self.stack):
            self.include = True
            for p, i in self.stack:
                if p == 'isub':
                    do_op = self.asm_mode > 0
                else:
                    do_op = False
                if do_op:
                    self.include = i == '+'
                else:
                    self.include = i == '-'
                if not self.include:
                    break
        if not self.include:
            return
        if directive.startswith('isub=') and self.asm_mode > 0:
            self.sub = directive[5:].rstrip()

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
        with open(binfile, 'wb') as f:
            f.write(bytearray(data))
        info("Wrote {}: start={}, end={}, size={}".format(binfile, base_address, end_address, len(data)))

def run(skoolfile, binfile, options):
    binwriter = BinWriter(skoolfile, options.asm_mode)
    binwriter.write(binfile, options.start, options.end)

def main(args):
    parser = argparse.ArgumentParser(
        usage='skool2bin.py [options] file.skool [file.bin]',
        description="Convert a skool file into a binary (raw memory) file. "
                    "'file.skool' may be a regular file, or '-' for standard input. "
                    "If 'file.bin' is not given, it defaults to the name of the input file with '.skool' replaced by '.bin'.",
        add_help=False
    )
    parser.add_argument('skoolfile', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('binfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-E', '--end', dest='end', metavar='ADDR', type=int,
                       help='Stop converting at this address')
    group.add_argument('-i', '--isub', dest='asm_mode', action='store_const', const=1, default=0,
                       help="Apply instruction substitutions (@isub)")
    group.add_argument('-S', '--start', dest='start', metavar='ADDR', type=int,
                       help='Start converting at this address')
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit')
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
