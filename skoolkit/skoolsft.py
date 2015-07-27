# -*- coding: utf-8 -*-

# Copyright 2011-2015 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import SkoolParsingError, write_line, get_int_param, get_address_format, open_file
from skoolkit.skoolctl import (get_instruction_ctl, get_lengths, get_operand_bases,
                               get_defb_length, get_defs_length, get_defw_length)
from skoolkit.skoolparser import parse_asm_block_directive, DIRECTIVES
from skoolkit.textutils import find_unquoted
from skoolkit.z80 import get_size

VALID_CTLS = DIRECTIVES + ' *'
VERBATIM_BLOCKS = ('d', 'i', 'r')

class VerbatimLine:
    def __init__(self, text):
        self.text = text.rstrip('\r\n')

    def __str__(self):
        return self.text

    def is_ctl_line(self):
        return False

    def is_trimmable(self):
        if (self.text.startswith('@') and self.text.endswith(('+end', '-end'))):
            return False
        return len(self.text) > 0

    def is_blank(self):
        return self.text == ''

class ControlLine:
    def __init__(self, ctl, address, addr_str, operation, comment_index, comment, preserve_base):
        self.ctl = ctl
        self.address = address
        self.addr_str = addr_str
        self.comment_index = comment_index
        self.comment = comment
        self.operation = operation
        self.inst_ctl = get_instruction_ctl(operation)
        if self.inst_ctl == 'C':
            size = get_size(operation, address)
            length = [get_operand_bases(operation, preserve_base), size]
        elif self.inst_ctl == 'B':
            size, length = get_defb_length(self.operation, preserve_base)
        elif self.inst_ctl == 'T':
            size, length = get_defb_length(self.operation, preserve_base)
        elif self.inst_ctl == 'W':
            size, length = get_defw_length(self.operation, preserve_base)
        else:
            size, length = get_defs_length(self.operation, preserve_base)
        self.end = address + size
        self.lengths = [length]

    def __str__(self):
        comment = ' {0}'.format(self.comment).rstrip()
        if self.comment_index > 0:
            comment_index = ';{0}'.format(self.comment_index)
        else:
            comment_index = ''
        return "{}{}{},{}{}{}".format(self.ctl, self.inst_ctl, self.addr_str,
                                      self._get_lengths(), comment_index, comment)

    def _get_lengths(self):
        if self.inst_ctl == 'C':
            return ','.join(['{}{}'.format(bases, length or 1) for bases, length in self.lengths])
        # Find subsequences of identical statement lengths and abbreviate them,
        # e.g. '16,16,16,8,8,4' -> '16*3,8*2,4'
        return get_lengths(self.lengths)

    def add_length(self, ctl_line):
        self.end = ctl_line.end
        if self.inst_ctl == 'C' and self.lengths[-1][0] == ctl_line.lengths[0][0]:
            self.lengths[-1][1] += ctl_line.lengths[0][1]
        else:
            self.lengths.append(ctl_line.lengths[0])

    def is_ctl_line(self):
        return True

    def is_trimmable(self):
        return False

    def is_blank(self):
        return False

class SftWriter:
    def __init__(self, skoolfile, write_hex=0, preserve_base=False):
        self.skoolfile = skoolfile
        self.preserve_base = preserve_base
        self.stack = []
        self.verbatim = False
        self.address_fmt = get_address_format(write_hex, write_hex < 0)

    def _parse_skool(self, min_address, max_address):
        start_index = -1
        lines = []
        ctl_lines = []
        entry_ctl = None
        f = open_file(self.skoolfile)
        for line in f:
            if line.startswith(';'):
                lines.append(VerbatimLine(line))
                continue
            if line.startswith('@'):
                lines.append(VerbatimLine(line))
                self._parse_asm_directive(line[1:].rstrip())
                continue
            if self.verbatim:
                # This line is inside a '+' block, so include it as is
                lines.append(VerbatimLine(line))
                continue
            s_line = line.strip()
            if not s_line:
                # This line is blank
                lines.append(VerbatimLine(line))
                entry_ctl = None
                continue
            # Check whether we're in a block that should be preserved verbatim
            if entry_ctl is None and line.startswith(VERBATIM_BLOCKS):
                entry_ctl = line[0]
            if entry_ctl in VERBATIM_BLOCKS:
                lines.append(VerbatimLine(line))
            elif s_line.startswith(';'):
                # This line is a continuation of an instruction comment
                comment_index = line.index(';')
                lines.append(VerbatimLine(" ;{} {}".format(comment_index, line[comment_index + 1:].lstrip())))
            elif line[0] in VALID_CTLS:
                # This line contains an instruction
                ctl_line = self._parse_instruction(line)
                if ctl_line.address >= max_address:
                    while lines and lines[-1].is_trimmable():
                        lines.pop()
                    while lines and lines[-1].is_blank():
                        lines.pop()
                    break
                if ctl_line.address >= min_address > 0 and start_index < 0:
                    start_index = len(lines)
                lines.append(ctl_line)
                ctl_lines.append(ctl_line)
            else:
                lines.append(VerbatimLine(line))
        f.close()

        if min_address > 0:
            if start_index < 0:
                return []
            if start_index < len(lines):
                if str(lines[start_index])[0] in DIRECTIVES:
                    while start_index > 0 and not lines[start_index].is_blank():
                        start_index -= 1
                else:
                    while start_index < len(lines) and not lines[start_index].is_blank():
                        start_index += 1
                return self._compress_blocks(lines[start_index + 1:])
        return self._compress_blocks(lines)

    def _parse_instruction(self, line):
        ctl = line[0]
        try:
            address = get_int_param(line[1:6])
        except ValueError:
            raise SkoolParsingError("Invalid address ({}):\n{}".format(line[1:6], line.rstrip()))
        addr_str = self.address_fmt.format(address)
        comment_index = find_unquoted(line, ';', 6, neg=True)
        if comment_index > 0:
            end = comment_index
        else:
            end = len(line)
        operation = line[7:end].strip()
        comment = line[end + 1:].strip()
        return ControlLine(ctl, address, addr_str, operation, comment_index, comment, self.preserve_base)

    def _parse_asm_directive(self, directive):
        if parse_asm_block_directive(directive, self.stack):
            self.verbatim = False
            for _p, i in self.stack:
                if i != '-':
                    self.verbatim = True
                    break

    def _compress_blocks(self, lines):
        """Compress sequences of commentless lines into a single line."""
        compressed = []
        prev_line = None
        for line in lines:
            if line.is_ctl_line() and not line.comment and (line.ctl == ' ' or line.ctl in DIRECTIVES):
                if prev_line is None:
                    prev_line = line
                elif (prev_line.inst_ctl == line.inst_ctl
                      and prev_line.comment_index == line.comment_index and prev_line.end == line.address):
                    prev_line.add_length(line)
                else:
                    compressed.append(prev_line)
                    prev_line = line
            else:
                if prev_line:
                    compressed.append(prev_line)
                compressed.append(line)
                prev_line = None
        if prev_line:
            compressed.append(prev_line)
        return compressed

    def write(self, min_address=0, max_address=65536):
        for line in self._parse_skool(min_address, max_address):
            write_line(str(line))
