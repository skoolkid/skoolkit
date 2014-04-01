# -*- coding: utf-8 -*-

# Copyright 2009-2014 Richard Dymond (rjdymond@gmail.com)
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

from . import warn, get_int_param, open_file
from .skoolctl import AD_START, AD_WRITER, AD_ORG, AD_END, AD_SET

class CtlParserError(Exception):
    pass

def parse_params(ctl, params, lengths_index=2):
    int_params = []
    prefix = None
    for i, num in enumerate(params):
        if i < lengths_index:
            length, prefix = _parse_length(num)
            int_params.append(length)
        else:
            if '*' in num:
                n, m = num.split('*', 1)
            else:
                n, m = num, '1'
            if ctl in 'BSTW':
                int_params += [_parse_sublengths(n, ctl, prefix)] * get_int_param(m)
            else:
                int_params += [(get_int_param(n), None)] * get_int_param(m)
    if prefix and len(int_params) == lengths_index:
        int_params.append((None, [(None, prefix)]))
    return int_params

def _parse_sublengths(sublengths, subctl, default_prefix):
    length = 0
    lengths = []
    for num in sublengths.split(':'):
        sublength, prefix = _parse_length(num, subctl, default_prefix)
        lengths.append((sublength, prefix))
        length += sublength
    if len(lengths) == 1 and prefix is None:
        return (length, None)
    if subctl == 'S':
        length = lengths[0][0]
    return (length, lengths)

def _parse_length(length, subctl=None, default_prefix=None):
    if length.startswith(('b', 'd', 'h')) or (subctl in ('B', 'T') and length.startswith(('B', 'T'))):
        return (get_int_param(length[1:]), length[0])
    return (get_int_param(length), default_prefix)

class CtlParser:
    def __init__(self):
        self.ctls = {}
        self.subctls = {}
        self.titles = {}
        self.instruction_comments = {}
        self.comments = {}
        self.registers = {}
        self.end_comments = {}
        self.lengths = {}
        self.multiline_comments = {}
        self.entry_asm_directives = {}
        self.instruction_asm_directives = {}

    def parse_ctl(self, ctlfile):
        entry_ctl = None
        f = open_file(ctlfile)
        for line_no, line in enumerate(f, 1):
            s_line = line.rstrip()
            if not s_line:
                continue
            try:
                ctl, start, end, text, lengths, asm_directive = self._parse_ctl_line(s_line, entry_ctl)
            except CtlParserError as e:
                warn('Ignoring line {} in {} ({}):\n{}'.format(line_no, ctlfile, e.args[0], s_line))
                continue
            if ctl:
                ctl = ctl.strip()
                if ctl.islower():
                    self.ctls[start] = ctl
                    entry_ctl = ctl
                    self.titles[start] = text
                elif ctl == 'D':
                    self.comments.setdefault(start, []).append(text)
                    self.subctls.setdefault(start, None)
                elif ctl == 'E':
                    self.end_comments.setdefault(start, []).append(text)
                elif ctl == 'R':
                    fields = text.split(' ', 1)
                    valid = len(fields) == 2
                    if valid:
                        self.registers.setdefault(start, [])
                        self.registers[start].append(fields)
                elif ctl == 'M':
                    self.multiline_comments[start] = (end, text)
                else:
                    self.subctls[start] = ctl.lower()
                    self.instruction_comments[start] = text
                    if end:
                        self.subctls[end + 1] = None
                if lengths:
                    self.lengths[start] = lengths
            elif asm_directive:
                directive, address, value = asm_directive
                if directive in (AD_ORG, AD_WRITER, AD_START, AD_END) or directive.startswith(AD_SET):
                    self.entry_asm_directives.setdefault(address, []).append((directive, value))
                else:
                    self.instruction_asm_directives.setdefault(address, []).append((directive, value))
        f.close()

    def _parse_ctl_line(self, line, entry_ctl):
        ctl = start = end = text = asm_directive = None
        lengths = []
        first_char = line[0]
        content = line[1:].lstrip()
        if content:
            if first_char in ' bBcCDEgiMRsStTuwW':
                fields = content.split(' ', 1)
                ctl = first_char
                if ctl == ' ':
                    if entry_ctl is None:
                        raise CtlParserError("blank directive with no containing block")
                    if entry_ctl in 'bcstw':
                        ctl = entry_ctl.upper()
                    else:
                        ctl = 'B'
                use_length = False
                if '-' in fields[0]:
                    params = fields[0].split('-', 1)
                    params[1:] = params[1].split(',')
                else:
                    params = fields[0].split(',')
                    use_length = len(params) > 1
                try:
                    int_params = parse_params(ctl, params)
                except ValueError:
                    raise CtlParserError("invalid integer")
                start = int_params[0]
                if len(int_params) > 1:
                    if ctl.islower():
                        raise CtlParserError("extra parameters after address")
                    end = int_params[1]
                    if use_length:
                        end += start - 1
                else:
                    end = None
                lengths = int_params[2:]
                if len(fields) > 1:
                    text = fields[1]
            elif first_char == ';' and content.startswith('@'):
                asm_fields = content.split(':', 1)
                if len(asm_fields) < 2:
                    raise CtlParserError("invalid ASM directive declaration")
                asm_fields[1] = asm_fields[1].split('=', 1)
                try:
                    address = get_int_param(asm_fields[1][0])
                except ValueError:
                    raise CtlParserError("invalid ASM directive address")
                directive = asm_fields[0][1:]
                if len(asm_fields[1]) == 2:
                    value = asm_fields[1][1]
                else:
                    value = None
                asm_directive = (directive, address, value)
            elif first_char not in '#%;':
                raise CtlParserError("invalid directive")
        return ctl, start, end, text, lengths, asm_directive

    def get_block_title(self, address):
        return self.titles.get(address)

    def get_block_comment(self, address):
        return self.comments.get(address, ())

    def get_registers(self, address):
        return self.registers.get(address, ())

    def get_instruction_comment(self, address):
        return self.instruction_comments.get(address) or ''

    def get_end_comment(self, address):
        return self.end_comments.get(address, ())

    def get_lengths(self, address):
        return self.lengths.get(address)

    def get_multiline_comment(self, address):
        return self.multiline_comments.get(address, (None, None))

    def get_instruction_asm_directives(self, address):
        return self.instruction_asm_directives.get(address, ())

    def get_entry_asm_directives(self, address):
        return self.entry_asm_directives.get(address, ())

    def contains_entry_asm_directive(self, asm_dir):
        for entry_asm_dir in self.entry_asm_directives.values():
            for (directive, value) in entry_asm_dir:
                if directive == asm_dir:
                    return True

    def get_blocks(self):
        # Create top-level blocks
        blocks = []
        for address in sorted(self.ctls.keys()):
            blocks.append(Block(self.ctls[address], address, True))

        # Set top-level block end addresses
        for i, block in enumerate(blocks[1:]):
            blocks[i].end = block.start
        blocks[-1].end = 65536

        # Create sub-blocks
        for sub_address in sorted(self.subctls.keys()):
            for block in blocks:
                if block.start <= sub_address < block.end:
                    block.add_block(self.subctls[sub_address], sub_address)
                    break

        # Set sub-block end addresses
        for block in blocks:
            for i, sub_block in enumerate(block.blocks[1:]):
                block.blocks[i].end = sub_block.start
            block.blocks[-1].end = block.end

        return blocks

class Block:
    def __init__(self, ctl, start, top=False):
        self.ctl = ctl
        self.start = start
        self.end = None
        self.header = None
        self.comment = None
        self.instructions = None
        if top:
            self.blocks = [Block(ctl, start)]

    def add_block(self, ctl, start):
        real_ctl = ctl or self.ctl
        if start == self.start:
            self.blocks[0].ctl = real_ctl
        else:
            self.blocks.append(Block(real_ctl, start))
