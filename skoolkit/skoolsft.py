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

from . import write_line, get_int_param, get_address_format, open_file
from .skoolparser import (DIRECTIVES, parse_asm_block_directive, get_instruction_ctl,
                          get_defb_length, get_defm_length, get_defs_length, get_defw_length)
from .skoolctl import get_lengths

VALID_CTLS = DIRECTIVES + ' *'
VERBATIM_BLOCKS = ('d', 'i', 'r')

class Line:
    def is_ctl_line(self):
        return False

class VerbatimLine(Line):
    def __init__(self, text):
        self.text = text.rstrip('\r\n')

    def __str__(self):
        return self.text

class ControlLine(Line):
    def __init__(self, ctl, address, addr_str, operation, comment_index, comment, preserve_base):
        self.ctl = ctl
        self.address = address
        self.addr_str = addr_str
        self.comment_index = comment_index
        self.comment = comment
        self.operation = operation
        self.preserve_base = preserve_base
        self.inst_ctl = get_instruction_ctl(operation)
        self.lengths = None

    def __str__(self):
        comment = ' {0}'.format(self.comment).rstrip()
        if self.comment_index > 0:
            comment_index = ';{0}'.format(self.comment_index)
        else:
            comment_index = ''
        return "{0}{1}{2},{3}{4}{5}".format(self.ctl, self.inst_ctl, self.addr_str, self._get_lengths(), comment_index, comment)

    def _get_lengths(self):
        # Find subsequences of identical statement lengths and abbreviate them,
        # e.g. '16,16,16,8,8,4' -> '16*3,8*2,4'
        if self.inst_ctl == 'C':
            return self.size
        return get_lengths(self.lengths)

    def calculate_length(self, next_ctl_line):
        if self.inst_ctl == 'C':
            if next_ctl_line:
                length = next_ctl_line.address - self.address
            else:
                length = -1
            if length < 0 or length > 4:
                length = 1
            self.size = length
            self.lengths = [str(length)]
        elif self.inst_ctl == 'B':
            self.size, length = get_defb_length(self.operation[5:], self.preserve_base)
            self.lengths = [length]
        elif self.inst_ctl == 'T':
            self.size, length = get_defm_length(self.operation[5:], self.preserve_base)
            self.lengths = [length]
        elif self.inst_ctl == 'W':
            self.size, length = get_defw_length(self.operation[5:], self.preserve_base)
            self.lengths = [length]
        else:
            self.size, length = get_defs_length(self.operation[5:], self.preserve_base)
            self.lengths = [length]

    def add_length(self, ctl_line):
        self.size += ctl_line.size
        self.lengths.append(ctl_line.lengths[0])

    def end(self):
        return self.address + self.size

    def is_ctl_line(self):
        return True

class SftWriter:
    def __init__(self, skoolfile, write_hex=False, preserve_base=False):
        self.skoolfile = skoolfile
        self.write_hex = write_hex
        self.preserve_base = preserve_base
        self.stack = []
        self.verbatim = False
        self.address_fmt = get_address_format(write_hex)

    def _parse_skool(self):
        lines = []
        ctl_lines = []
        entry_ctl = None
        f = open_file(self.skoolfile)
        for line in f:
            if line.startswith(';'):
                lines.append(VerbatimLine(line))
                comment = line[1:].strip()
                if comment.startswith('@'):
                    self._parse_asm_directive(comment[1:])
                continue # pragma: no cover
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
                lines.append(ctl_line)
                ctl_lines.append(ctl_line)
            else:
                lines.append(VerbatimLine(line))
        f.close()
        self._calculate_lengths(ctl_lines)
        return self._compress_blocks(lines)

    def _parse_instruction(self, line):
        ctl = line[0]
        address = get_int_param(line[1:6])
        addr_str = self.address_fmt.format(address)
        comment_index = line.find(';', 7)
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

    def _calculate_lengths(self, ctl_lines):
        for i, ctl_line in enumerate(ctl_lines):
            if i < len(ctl_lines) - 1:
                next_ctl_line = ctl_lines[i + 1]
            else:
                next_ctl_line = None
            ctl_line.calculate_length(next_ctl_line)

    def _compress_blocks(self, lines):
        """Compress sequences of commentless lines into a single line."""
        compressed = []
        prev_line = None
        for line in lines:
            if line.is_ctl_line() and not line.comment and (line.ctl == ' ' or line.ctl in DIRECTIVES):
                if prev_line is None:
                    prev_line = line
                elif prev_line.inst_ctl == line.inst_ctl and prev_line.comment_index == line.comment_index and line.address == prev_line.end():
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

    def write(self):
        for line in self._parse_skool():
            write_line(str(line))
