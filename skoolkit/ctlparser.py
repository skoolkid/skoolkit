# Copyright 2009-2019 Richard Dymond (rjdymond@gmail.com)
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

import bisect
from collections import defaultdict

from skoolkit import warn, get_int_param, open_file
from skoolkit.skoolctl import (extract_entry_asm_directives, AD_IGNOREUA, AD_ORG, AD_START,
                               TITLE, DESCRIPTION, REGISTERS, MID_BLOCK, INSTRUCTION, END)
from skoolkit.skoolparser import parse_asm_data_directive
from skoolkit.textutils import partition_unquoted, split_unquoted

COMMENT_TYPES = (TITLE, DESCRIPTION, REGISTERS, MID_BLOCK, INSTRUCTION, END)

ENTRY_COMMENT_TYPES = (TITLE, DESCRIPTION, REGISTERS, END)

BASES = ('b', 'c', 'd', 'h', 'm', 'n')

class CtlParserError(Exception):
    pass

def parse_params(ctl, params, lengths_index=1):
    int_params = []
    prefix = None
    for i, param in enumerate(params):
        if i < lengths_index:
            length, prefix = _parse_length(param, required=False)
            int_params.append(length)
        else:
            n, sep, m = partition_unquoted(param, '*', '1')
            int_params += (_parse_sublengths(n, ctl, prefix),) * get_int_param(m)
    if prefix and len(int_params) == lengths_index:
        int_params.append((None, ((None, prefix),)))
    return tuple(int_params)

def _parse_sublengths(spec, subctl, default_prefix):
    length = 0
    lengths = []
    if subctl == 'C':
        sublengths = [spec]
    else:
        sublengths = split_unquoted(spec, ':')
    required = True
    for num in sublengths:
        sublength, prefix = _parse_length(num, subctl, default_prefix, required)
        lengths.append((sublength, prefix))
        if required or sublength is not None:
            length += sublength
        required = subctl != 'S'
    if len(lengths) == 1 and prefix is None:
        return (length, ((length, None),))
    if subctl == 'S':
        length = lengths[0][0]
    return (length, tuple(lengths))

def _parse_length(length, subctl=None, default_prefix=None, required=True):
    if length.startswith(BASES):
        prefix = length[0]
        if length[1:].startswith(BASES):
            prefix += length[1]
        if required or len(length) > len(prefix):
            return (get_int_param(length[len(prefix):]), prefix)
        return (None, prefix)
    if subctl in ('B', 'T') and length.startswith(('B', 'T')):
        return (get_int_param(length[1:]), length[0])
    if required or length:
        return (get_int_param(length), default_prefix)
    return (None, default_prefix)

class CtlParser:
    def __init__(self, ctls=None):
        self._subctls = {}
        self._titles = {}
        self._instruction_comments = {}
        self._descriptions = defaultdict(list)
        self._registers = defaultdict(list)
        self._mid_block_comments = defaultdict(list)
        self._end_comments = defaultdict(list)
        self._lengths = {}
        self._multiline_comments = {}
        self._asm_directives = defaultdict(list)
        self._ignoreua_directives = defaultdict(set)
        self._headers = defaultdict(list)
        self._footers = defaultdict(list)
        self._loops = []
        if ctls:
            self._ctls = ctls
            self._asm_directives[min(ctls)] = [AD_START, AD_ORG]
        else:
            self._ctls = {}

    def parse_ctls(self, ctlfiles, min_address=0, max_address=65536):
        ctl_lines = []
        for ctlfile in ctlfiles:
            self._parse_ctl_file(ctlfile, ctl_lines, min_address, max_address)

        entry_addresses = sorted(self._ctls)

        comment = []
        for line_no, s_line in enumerate(ctl_lines, 1):
            try:
                ctl, start, end, text, lengths, asm_directive = self._parse_ctl_line(s_line, entry_addresses)
            except CtlParserError as e:
                warn('Ignoring line {} in {} ({}):\n{}'.format(line_no, ctlfile, e.args[0], s_line))
                continue
            if ctl:
                if ctl in '.:':
                    comment.append(('.:'.index(ctl), text))
                    continue
                if not min_address <= start < max_address:
                    continue
                comment = [(0, text or '')]
                if ctl == '>':
                    if end:
                        self._footers[start].append(text or '')
                    else:
                        self._headers[start].append(text or '')
                elif ctl.islower():
                    self._titles[start] = comment
                elif ctl == 'D':
                    self._descriptions[start].append(comment)
                    self._subctls.setdefault(start, None)
                elif ctl == 'N':
                    self._mid_block_comments[start].append(comment)
                    self._subctls.setdefault(start, None)
                elif ctl == 'E':
                    self._end_comments[start].append(comment)
                elif ctl == 'R':
                    self._registers[start].append(comment)
                elif ctl == 'M':
                    self._multiline_comments[start] = (end, comment)
                    self._subctls.setdefault(start, None)
                elif ctl == 'L':
                    count = lengths[0][0]
                    if count > 1:
                        if len(lengths) > 1:
                            repeat_entries = lengths[1][0]
                        else:
                            repeat_entries = 0
                        loop_end = start + count * (end - start)
                        if loop_end > 65536:
                            warn('Loop crosses 64K boundary:\n{}'.format(s_line))
                        self._loops.append((start, end, count, repeat_entries))
                        self._subctls[loop_end] = None
                else:
                    self._subctls[start] = ctl.lower()
                    self._instruction_comments[start] = comment
                    if end:
                        self._subctls[end] = None
                if ctl != 'L' and lengths:
                    self._lengths[start] = lengths[0][1]
                    if len(lengths) > 1:
                        address = start + lengths[0][0]
                        subctl = self._subctls[start]
                        for length, sublengths in lengths[1:]:
                            self._lengths[address] = sublengths
                            self._subctls[address] = subctl
                            address += length
                        self._multiline_comments[start] = (address, comment)
            elif asm_directive:
                directive, address = asm_directive
                self._asm_directives[address].append(directive)

        self._terminate_multiline_comments()
        self._unroll_loops(max_address)
        self._ctls[max_address] = 'i'

    def _parse_ctl_file(self, ctlfile, ctl_lines, min_address, max_address):
        with open_file(ctlfile) as f:
            for line in f:
                s_line = line.rstrip()
                if s_line:
                    ctl_lines.append(s_line)
                    if s_line.startswith(('b', 'c', 'g', 'i', 's', 't', 'u', 'w')):
                        try:
                            address = get_int_param(s_line[1:].lstrip().split(' ', 1)[0])
                            if min_address <= address < max_address:
                                self._ctls[address] = s_line[0]
                        except ValueError:
                            pass

    def _parse_ctl_line(self, line, entry_addresses):
        ctl = start = end = text = asm_directive = None
        lengths = ()
        first_char = line[0]
        content = line[1:].lstrip()
        if first_char in '.:':
            ctl = first_char
            text = line[2:].rstrip()
        elif content:
            if first_char in ' >bBcCDEgiLMNRsStTuwW':
                fields = split_unquoted(content, ' ', 1)
                params = split_unquoted(fields[0], ',')
                try:
                    start = get_int_param(params[0])
                except ValueError:
                    raise CtlParserError("invalid address")
                ctl = first_char
                if ctl == ' ':
                    index = bisect.bisect_right(entry_addresses, start) - 1
                    if index < 0:
                        raise CtlParserError("blank directive with no containing block")
                    entry_ctl = self._ctls[entry_addresses[index]]
                    if entry_ctl in 'cstw':
                        ctl = entry_ctl.upper()
                    else:
                        ctl = 'B'
                try:
                    int_params = parse_params(ctl, params[1:])
                except ValueError:
                    raise CtlParserError("invalid integer")
                if int_params:
                    if ctl not in '>BCLMSTW':
                        raise CtlParserError("extra parameters after address")
                    length = int_params[0]
                    if length is not None:
                        end = start + length
                lengths = int_params[1:]
                if ctl == 'L':
                    if end is None:
                        raise CtlParserError("loop length not specified")
                    if not lengths:
                        raise CtlParserError("loop count not specified")
                if len(fields) > 1:
                    text = fields[1]
            elif first_char == '@':
                asm_directive = self._parse_asm_directive(content)
            elif first_char not in '#%;':
                raise CtlParserError("invalid directive")
        return ctl, start, end, text, lengths, asm_directive

    def _parse_asm_directive(self, content):
        fields = [f.lstrip() for f in content.split(' ', 1)]
        if len(fields) < 2:
            raise CtlParserError("invalid ASM directive declaration")
        try:
            address = get_int_param(fields[0])
        except ValueError:
            raise CtlParserError("invalid ASM directive address")
        directive = fields[1]
        comment_type = 'i'
        if directive.startswith(AD_IGNOREUA + ':'):
            directive, comment_type = directive.split(':', 1)
        if directive != AD_IGNOREUA:
            return directive, address
        if comment_type not in COMMENT_TYPES:
            raise CtlParserError("invalid @ignoreua directive suffix: '{}'".format(comment_type))
        self._ignoreua_directives[address].add(comment_type)

    def _terminate_multiline_comments(self):
        addresses = sorted(set(self._ctls) | set(self._mid_block_comments) | {65536})
        for address, (end, text) in self._multiline_comments.items():
            max_end = addresses[bisect.bisect_right(addresses, address)]
            if end is None or end > max_end:
                self._multiline_comments[address] = (max_end, text)

    def _unroll_loops(self, max_address):
        for start, end, count, repeat_entries in self._loops:
            for directives in (self._subctls, self._mid_block_comments, self._instruction_comments, self._lengths):
                self._repeat_directives(directives, start, end, count, max_address)
            self._repeat_multiline_comments(start, end, count, max_address)
            if repeat_entries:
                for directives in (self._ctls, self._titles, self._descriptions, self._registers, self._end_comments):
                    self._repeat_directives(directives, start, end, count, max_address)

    def _repeat_directives(self, directives, start, end, count, max_address):
        interval = end - start
        repeated = {k: v for k, v in directives.items() if start <= k < end}
        for addr, value in repeated.items():
            for i in range(1, count):
                address = addr + i * interval
                if address < max_address:
                    directives[address] = value
                else:
                    break

    def _repeat_multiline_comments(self, start, end, count, max_address):
        interval = end - start
        repeated = {k: v for k, v in self._multiline_comments.items() if start <= k < end}
        for addr, (mlc_end, comment) in repeated.items():
            for i in range(1, count):
                offset = i * interval
                address = addr + offset
                if address < max_address:
                    self._multiline_comments[address] = (mlc_end + offset, comment)
                else:
                    break

    def _reduce(self, collection, address, paragraphs=True):
        if address in collection:
            if paragraphs:
                return [[t[1] for t in p] for p in collection[address]]
            return [t[1] for t in collection[address]]
        return ()

    def get_blocks(self):
        # Create top-level blocks
        blocks = []
        block_addresses = sorted(self._ctls)
        for i, address in enumerate(block_addresses[:-1]):
            block = Block(self._ctls[address], address)
            block.end = block_addresses[i + 1]
            block.asm_directives = extract_entry_asm_directives(self._asm_directives.get(address, ()))
            if self._asm_directives.get(address) == []:
                del self._asm_directives[address]
            block.ignoreua_directives = tuple(self._ignoreua_directives.get(address, set()).intersection(ENTRY_COMMENT_TYPES))
            block.header = self._headers.get(address, ())
            block.title = self._reduce(self._titles, address, False)
            block.description = self._reduce(self._descriptions, address)
            block.registers = self._reduce(self._registers, address)
            block.end_comment = self._reduce(self._end_comments, address)
            block.footer = self._footers.get(address, ())
            blocks.append(block)

        # Create sub-blocks
        for sub_address in sorted(self._subctls):
            for block in blocks:
                if block.start <= sub_address < block.end:
                    block.add_block(self._subctls[sub_address], sub_address)
                    break

        # Set sub-block end addresses
        for block in blocks:
            for i, sub_block in enumerate(block.blocks[1:]):
                block.blocks[i].end = sub_block.start
            block.blocks[-1].end = block.end

        # Set sub-block attributes
        asm_directives = tuple(self._asm_directives.items())
        for block in blocks:
            for sub_block in block.blocks:
                sub_address = sub_block.start
                sub_block.sublengths = self._lengths.get(sub_address, ((None, None),))
                sub_block.header = self._reduce(self._mid_block_comments, sub_address)
                sub_block.comment = self._instruction_comments.get(sub_address) or ()
                sub_block.multiline_comment = self._multiline_comments.get(sub_address)
                sub_block.asm_directives = dict([d for d in asm_directives if sub_address <= d[0] < sub_block.end])
                sub_block.ignoreua_directives = {}
                for addr, dirs in self._ignoreua_directives.items():
                    if sub_address <= addr < sub_block.end:
                        sub_block.ignoreua_directives[addr] = tuple(dirs.difference(ENTRY_COMMENT_TYPES))

        return blocks

    def apply_asm_data_directives(self, snapshot):
        for directives in self._asm_directives.values():
            for directive in directives:
                if directive.startswith(('defb=', 'defs=', 'defw=')):
                    parse_asm_data_directive(snapshot, directive)

class Block:
    def __init__(self, ctl, start, top=True):
        self.ctl = ctl
        self.start = start
        if top:
            self.blocks = [Block(ctl, start, False)]

    def add_block(self, ctl, start):
        real_ctl = ctl or self.ctl
        if start == self.start:
            self.blocks[0].ctl = real_ctl
        else:
            self.blocks.append(Block(real_ctl, start, False))

    def has_ignoreua_directive(self, address, comment_type):
        return comment_type in self.ignoreua_directives.get(address, ())
