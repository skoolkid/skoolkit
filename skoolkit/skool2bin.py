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
from collections import defaultdict

from skoolkit import SkoolParsingError, get_int_param, info, integer, open_file, VERSION
from skoolkit.skoolmacro import MacroParsingError, parse_if
from skoolkit.skoolparser import parse_address_range, parse_asm_sub_fix_directive, read_skool
from skoolkit.skoolsft import VALID_CTLS
from skoolkit.textutils import partition_unquoted
from skoolkit.z80 import assemble

class BinWriter:
    def __init__(self, skoolfile, asm_mode=0, fix_mode=0):
        self.asm_mode = asm_mode
        self.fix_mode = fix_mode
        self.weights = {
            'isub': int(asm_mode > 0),
            'ssub': 2 * int(asm_mode > 1),
            'ofix': 3 * int(fix_mode > 0),
            'bfix': 4 * int(fix_mode > 1)
        }
        self.fields = {
            'asm': asm_mode,
            'fix': fix_mode
        }
        self.snapshot = [0] * 65536
        self.base_address = len(self.snapshot)
        self.end_address = 0
        self.subs = defaultdict(list, {0: []})
        self._parse_skool(skoolfile)

    def _parse_skool(self, skoolfile):
        f = open_file(skoolfile)
        for non_entry, block in read_skool(f, 2, self.asm_mode, self.fix_mode):
            if non_entry:
                continue
            address = None
            removed = set()
            for line in block:
                if line.startswith('@'):
                    self._parse_asm_directive(line[1:], removed)
                elif not line.lstrip().startswith(';') and line[0] in VALID_CTLS:
                    address = self._parse_instruction(address, line, removed)
        f.close()

    def _parse_instruction(self, address, line, removed):
        try:
            skool_address = get_int_param(line[1:6])
        except ValueError:
            raise SkoolParsingError("Invalid address ({}):\n{}".format(line[1:6], line.rstrip()))
        if address is None:
            address = skool_address
        original_op = partition_unquoted(line[6:], ';')[0].strip()
        subbed = max(self.subs)
        if subbed:
            operations = self.subs[subbed]
        else:
            operations = [original_op]
        self.subs = defaultdict(list, {0: []})
        parsed = [parse_asm_sub_fix_directive(v)[::2] for v in operations]
        before = [i[1] for i in parsed if i[0].prepend and i[1]]
        for operation in before:
            address = self._assemble(operation, address)
        after = [(i[0].overwrite, i[1], i[0].append) for i in parsed if not i[0].prepend]
        if not after or after[0][2]:
            after.insert(0, (False, original_op, False))
        overwrite, operation = after.pop(0)[:2]
        operation = operation or original_op
        if skool_address not in removed:
            address = self._assemble(operation, address, overwrite, removed)
        for overwrite, operation, append in after:
            if operation:
                address = self._assemble(operation, address, overwrite, removed)
        return address

    def _assemble(self, operation, address, overwrite=False, removed=None):
        data = assemble(operation, address)
        if data:
            end_address = address + len(data)
            if removed is None or address not in removed:
                self.snapshot[address:end_address] = data
                self.base_address = min(self.base_address, address)
                self.end_address = max(self.end_address, end_address)
            if overwrite:
                removed.update(range(address, end_address))
            return end_address
        raise SkoolParsingError("Failed to assemble:\n {} {}".format(address, operation))

    def _parse_asm_directive(self, directive, removed):
        if directive.startswith(('isub=', 'ssub=', 'ofix=', 'bfix=')):
            value = directive[5:].rstrip()
            if value.startswith('!'):
                if self.weights[directive[:4]]:
                    removed.update(parse_address_range(value[1:]))
            else:
                self.subs[self.weights[directive[:4]]].append(value)
        elif directive.startswith('if('):
            try:
                self._parse_asm_directive(parse_if(self.fields, directive, 2)[1], removed)
            except MacroParsingError:
                pass

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
