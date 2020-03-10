# Copyright 2015-2020 Richard Dymond (rjdymond@gmail.com)
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
from collections import defaultdict, namedtuple
from os.path import basename

from skoolkit import SkoolParsingError, get_int_param, info, integer, open_file, parse_int, warn, VERSION
from skoolkit.components import get_assembler, get_instruction_utility
from skoolkit.skoolmacro import MacroParsingError, parse_if
from skoolkit.skoolparser import (DIRECTIVES, parse_address_range, parse_asm_data_directive,
                                  parse_asm_keep_directive, parse_asm_nowarn_directive,
                                  parse_asm_sub_fix_directive, read_skool)
from skoolkit.textutils import partition_unquoted

VALID_CTLS = DIRECTIVES + ' *'

Entry = namedtuple('Entry', 'ctl instructions')

class Instruction:
    def __init__(self, skool_address, address=None, operation=None, sub=False, keep=None, nowarn=None, data=None, marker=' '):
        self.address = skool_address # API (InstructionUtility)
        self.operation = operation   # API (InstructionUtility)
        self.sub = sub               # API (InstructionUtility)
        self.keep = keep             # API (InstructionUtility)
        self.nowarn = nowarn         # API (InstructionUtility)
        self.original = operation
        self.real_address = address
        self.data = data
        self.marker = marker

    def __str__(self):
        if self.address in (None, self.real_address) and self.original == self.operation:
            suffix = ''
        elif self.address is None:
            suffix = ':            {}'.format(self.original)
        else:
            suffix = ': {0:05} {0:04X} {1}'.format(self.address, self.original)
        return '{0:05} {0:04X} {1} {2:13} {3}'.format(self.real_address, self.marker, self.operation, suffix).rstrip()

class BinWriter:
    def __init__(self, skoolfile, asm_mode=0, fix_mode=0, start=-1, end=65537, data=False, verbose=False, warn=True):
        if fix_mode > 2:
            asm_mode = 3
        elif asm_mode > 2:
            fix_mode = max(fix_mode, 1)
        self.asm_mode = asm_mode
        self.fix_mode = fix_mode
        self.start = start
        self.end = end
        self.verbose = verbose
        self.warn = warn
        self.weights = {
            'isub': int(asm_mode > 0),
            'ssub': 2 * int(asm_mode > 1),
            'rsub': 3 * int(asm_mode > 2),
            'ofix': 4 * int(fix_mode > 0),
            'bfix': 5 * int(fix_mode > 1),
            'rfix': 6 * int(fix_mode > 2)
        }
        self.fields = {
            'asm': asm_mode,
            'fix': fix_mode
        }
        self.snapshot = [0] * 65536
        self.base_address = len(self.snapshot)
        self.end_address = 0
        self._reset(data)
        self.entry_ctl = None
        self.entries = []
        self.remote_entries = []
        self.instructions = []
        self.address_map = {}
        self.assembler = get_assembler()
        self._parse_skool(skoolfile)
        self._relocate()

    def _reset(self, data):
        self.subs = defaultdict(list, {0: []})
        self.keep = None
        self.nowarn = None
        if data:
            self.data = []
        else:
            self.data = None

    def _parse_skool(self, skoolfile):
        f = open_file(skoolfile)
        address = None
        for non_entry, block in read_skool(f, 2, self.asm_mode, self.fix_mode):
            if non_entry:
                continue
            removed = set()
            for line in block:
                if line.startswith('@'):
                    address = self._parse_asm_directive(address, line[1:], removed)
                elif not line.lstrip().startswith(';') and line[0] in VALID_CTLS:
                    address = self._parse_instruction(address, line, removed)
            self.entries.append(Entry(self.entry_ctl, self.instructions))
            self.entry_ctl = None
            self.instructions = []
        f.close()

    def _parse_instruction(self, address, line, removed):
        if self.entry_ctl is None:
            self.entry_ctl = line[0]
        try:
            skool_address = get_int_param(line[1:6])
        except ValueError:
            if address is None or line[1:6].strip():
                raise SkoolParsingError("Invalid address ({}):\n{}".format(line[1:6], line.rstrip()))
            skool_address = None
        if address is None:
            address = skool_address
        subbed = max(self.subs)
        if subbed:
            operations = self.subs[subbed]
        else:
            operations = ['']
        if skool_address not in removed:
            original_op = partition_unquoted(line[6:], ';')[0].strip()
            address = self._add_instructions(address, skool_address, operations, original_op, removed)
        self._reset(self.data is not None)
        return address

    def _add_instructions(self, address, skool_address, operations, original_op, removed):
        parsed = [parse_asm_sub_fix_directive(v)[::2] for v in operations]
        before = [i[1] for i in parsed if i[0].prepend and i[1]]
        for operation in before:
            address += self._get_size(operation, address, '>')
        self.address_map.setdefault(skool_address, str(address))
        after = [(i[0].overwrite, i[1], i[0].append) for i in parsed if not i[0].prepend]
        if skool_address is None:
            offset = 0
        else:
            offset = skool_address - address
        if not after or after[0][2]:
            overwrite, operation, sub = False, original_op, False
        else:
            overwrite, operation = after.pop(0)[:2]
            if operation:
                sub = True
            else:
                operation, sub = original_op, False
        if operation:
            address += self._get_size(operation, address, ' ', overwrite, removed, offset, sub, skool_address)
        for overwrite, operation, append in after:
            if operation:
                address += self._get_size(operation, address, '+', overwrite, removed, offset)
        return address

    def _get_size(self, operation, address, marker, overwrite=False, removed=None, offset=0, sub=True, skool_address=None):
        if operation.upper().startswith(('DJNZ ', 'JR ')):
            size = 2
        else:
            size = self.assembler.get_size(operation, address)
        if size:
            if overwrite:
                removed.update(range(address + offset, address + offset + size))
                marker = '|'
            if self.start <= address < self.end:
                self.instructions.append(Instruction(skool_address, address, operation, sub, self.keep, self.nowarn, self.data, marker))
            return size
        raise SkoolParsingError("Failed to assemble:\n {} {}".format(address, operation))

    def _parse_asm_directive(self, address, directive, removed):
        if directive.startswith(('isub=', 'ssub=', 'rsub=', 'ofix=', 'bfix=', 'rfix=')):
            value = directive[5:].rstrip()
            if value.startswith('!'):
                if self.weights[directive[:4]]:
                    removed.update(parse_address_range(value[1:]))
            else:
                self.subs[self.weights[directive[:4]]].append(value)
        elif directive.startswith('if('):
            try:
                address = self._parse_asm_directive(address, parse_if(self.fields, directive, 2)[1], removed)
            except MacroParsingError:
                pass
        elif directive.startswith('org'):
            org = directive.rstrip().partition('=')[2]
            if org:
                try:
                    address = get_int_param(org)
                except ValueError:
                    raise SkoolParsingError("Invalid org address: {}".format(org))
            else:
                address = None
        elif directive.startswith('keep'):
            self.keep = parse_asm_keep_directive(directive)
        elif directive.startswith('nowarn'):
            self.nowarn = parse_asm_nowarn_directive(directive)
        elif self.data is not None and directive.startswith(('defb=', 'defs=', 'defw=')):
            self.data.append(directive)
        elif directive.startswith('remote='):
            addrs = [parse_int(a) for a in directive[7:].partition(':')[-1].split(',')]
            if addrs[0] is not None:
                self.remote_entries.append(Entry(None, [Instruction(a) for a in addrs if a is not None]))
        return address

    def _poke(self, instruction, data):
        address = instruction.real_address
        self.snapshot[address:address + len(data)] = data
        self.base_address = min(self.base_address, address)
        self.end_address = max(self.end_address, address + len(data))
        if self.verbose:
            info(str(instruction))

    def _warn(self, message, instruction):
        if self.warn:
            warn('{}:\n  {}'.format(message, instruction))

    def _relocate(self):
        get_instruction_utility().substitute_labels(self.entries, self.remote_entries, self.address_map, self.asm_mode, self._warn)
        for entry in self.entries:
            for i in entry.instructions:
                address = i.real_address
                while i.data:
                    data_dir = i.data.pop(0)
                    address, data = parse_asm_data_directive(self.snapshot, address, data_dir, False)
                    self._poke(Instruction(None, address, '@' + data_dir), data)
                    address += len(data)
                self._poke(i, self.assembler.assemble(i.operation, i.real_address))

    def write(self, binfile):
        if self.start < 0:
            base_address = self.base_address
        else:
            base_address = max(self.start, self.base_address)
        if self.end > 65536:
            end_address = self.end_address
        else:
            end_address = min(self.end, self.end_address)
        base_address = min(base_address, end_address)
        data = self.snapshot[base_address:end_address]
        with open_file(binfile, 'wb') as f:
            f.write(bytearray(data))
        if binfile == '-':
            binfile = 'stdout'
        info("Wrote {}: start={}, end={}, size={}".format(binfile, base_address, end_address, len(data)))

def run(skoolfile, binfile, options):
    binwriter = BinWriter(skoolfile, options.asm_mode, options.fix_mode, options.start, options.end,
                          options.data, options.verbose, not options.no_warnings)
    binwriter.write(binfile)

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
    group.add_argument('-d', '--data', dest='data', action='store_true',
                       help="Process @defb, @defs and @defw directives.")
    group.add_argument('-E', '--end', dest='end', metavar='ADDR', type=integer, default=65537,
                       help='Stop converting at this address.')
    group.add_argument('-i', '--isub', dest='asm_mode', action='store_const', const=1, default=0,
                       help="Apply @isub directives.")
    group.add_argument('-o', '--ofix', dest='fix_mode', action='store_const', const=1, default=0,
                       help="Apply @ofix directives.")
    group.add_argument('-r', '--rsub', dest='asm_mode', action='store_const', const=3, default=0,
                       help="Apply @isub, @ssub and @rsub directives (implies --ofix).")
    group.add_argument('-R', '--rfix', dest='fix_mode', action='store_const', const=3, default=0,
                       help="Apply @ofix, @bfix and @rfix directives (implies --rsub).")
    group.add_argument('-s', '--ssub', dest='asm_mode', action='store_const', const=2, default=0,
                       help="Apply @isub and @ssub directives.")
    group.add_argument('-S', '--start', dest='start', metavar='ADDR', type=integer, default=-1,
                       help='Start converting at this address.')
    group.add_argument('-v', '--verbose', action='store_true',
                       help='Show info on each converted instruction.')
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    group.add_argument('-w', '--no-warnings', action='store_true',
                       help="Suppress warnings.")
    namespace, unknown_args = parser.parse_known_args(args)
    skoolfile = namespace.skoolfile
    if unknown_args or skoolfile is None:
        parser.exit(2, parser.format_help())

    binfile = namespace.binfile
    if binfile is None:
        if skoolfile.lower().endswith('.skool'):
            binfile = basename(skoolfile)[:-6] + '.bin'
        elif skoolfile == '-':
            binfile = 'program.bin'
        else:
            binfile = basename(skoolfile) + '.bin'
    run(skoolfile, binfile, namespace)
