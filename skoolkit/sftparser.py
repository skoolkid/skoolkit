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

from skoolkit import SkoolKitError, write_line, get_int_param, parse_int, get_address_format, open_file
from skoolkit.ctlparser import parse_params
from skoolkit.disassembler import Disassembler
from skoolkit.skoolparser import set_bytes, parse_asm_block_directive, DIRECTIVES
from skoolkit.skoolsft import VerbatimLine, VALID_CTLS, VERBATIM_BLOCKS
from skoolkit.textutils import find_unquoted, split_unquoted

class SftParsingError(SkoolKitError):
    pass

class InstructionLine:
    def __init__(self, ctl=None, address=None, operation=None, comment_index=-1, comment=None):
        self.ctl = ctl
        self.address = address
        self.operation = operation
        self.comment_index = comment_index
        self.comment = comment

    def __str__(self):
        if self.address:
            op_width = self.comment_index - 8
            if self.comment:
                return "{0}{1} {2} ; {3}".format(self.ctl, self.address, self.operation.ljust(op_width), self.comment)
            if self.comment_index > 0:
                return "{0}{1} {2} ;".format(self.ctl, self.address, self.operation.ljust(op_width))
            return "{0}{1} {2}".format(self.ctl, self.address, self.operation)
        indent = ''.ljust(self.comment_index)
        if self.comment:
            return "{0}; {1}".format(indent, self.comment)
        return "{0};".format(indent)

    def is_trimmable(self):
        return False

    def is_blank(self):
        return False

class SftParser:
    def __init__(self, snapshot, sftfile, zfill=False, asm_hex=False, asm_lower=False):
        self.snapshot = snapshot
        self.disassembler = Disassembler(snapshot, zfill=zfill, asm_hex=asm_hex, asm_lower=asm_lower)
        self.sftfile = sftfile
        self.address_fmt = get_address_format(asm_hex, asm_lower)
        self.stack = []
        self.disassemble = True

    def _parse_instruction(self, line):
        ctl = line[0]
        lengths = []
        if line[1] == ';':
            inst_ctl = None
            start = None
            i = line.find(' ', 2)
            if i < 0:
                i = len(line.rstrip())
            comment_index = get_int_param(line[2:i])
        else:
            inst_ctl = line[1]
            comma_index = line.index(',', 2)
            start = get_int_param(line[2:comma_index])
            i = find_unquoted(line.rstrip(), ' ', comma_index + 1)
            j = find_unquoted(line, ';', comma_index + 1, i)
            if j == i:
                comment_index = -1
            else:
                comment_index = get_int_param(line[j + 1:i])
            if j > comma_index + 1:
                params = split_unquoted(line[comma_index + 1:j], ',')
                lengths = parse_params(inst_ctl, params, 0)
            else:
                raise ValueError
        comment = line[i:].strip()
        return ctl, inst_ctl, start, lengths, comment_index, comment

    def _parse_asm_directive(self, directive):
        if parse_asm_block_directive(directive, self.stack):
            self.disassemble = True
            for _p, i in self.stack:
                if i != '-':
                    self.disassemble = False
                    break

    def _set_bytes(self, line):
        address = parse_int(line[1:6])
        if address is not None:
            comment_index = find_unquoted(line, ';')
            operation = line[7:comment_index].strip()
            set_bytes(self.snapshot, address, operation)

    def _parse_sft(self, min_address, max_address):
        start_index = -1
        lines = []
        entry_ctl = None
        f = open_file(self.sftfile)
        for line in f:
            if line.startswith('#'):
                # This line is a skool file template comment
                continue

            if not line.strip():
                # This line is blank
                lines.append(VerbatimLine(line))
                entry_ctl = None
                continue

            if line.startswith(';'):
                # This line is an entry-level comment
                lines.append(VerbatimLine(line))
                continue

            if line.startswith('@'):
                lines.append(VerbatimLine(line))
                self._parse_asm_directive(line[1:].rstrip())
                continue

            if not self.disassemble:
                # This line is inside a '+' block, so include it as is
                lines.append(VerbatimLine(line))
                continue

            # Check whether we're in a block that should be restored verbatim
            if entry_ctl is None and line.startswith(VERBATIM_BLOCKS):
                entry_ctl = line[0]
            if entry_ctl in VERBATIM_BLOCKS:
                if entry_ctl == 'd':
                    self._set_bytes(line)
                lines.append(VerbatimLine(line))
                continue

            # Check whether the line starts with a valid character
            if line[0] not in VALID_CTLS:
                lines.append(VerbatimLine(line))
                continue

            try:
                ctl, inst_ctl, start, lengths, comment_index, comment = self._parse_instruction(line)
            except (IndexError, ValueError):
                raise SftParsingError("Invalid line: {0}".format(line.split()[0]))
            if start is not None:
                # This line contains a control directive
                if start >= min_address > 0 and start_index < 0:
                    start_index = len(lines)
                instructions = []
                for length, sublengths in lengths:
                    end = start + length
                    if inst_ctl == 'C':
                        base = sublengths[0][1]
                        instructions += self.disassembler.disassemble(start, end, base)
                    elif inst_ctl == 'W':
                        instructions += self.disassembler.defw_range(start, end, sublengths)
                    elif inst_ctl == 'T':
                        instructions += self.disassembler.defm_range(start, end, sublengths)
                    elif inst_ctl == 'S':
                        instructions.append(self.disassembler.defs(start, end, sublengths))
                    else:
                        instructions += self.disassembler.defb_range(start, end, sublengths)
                    start += length
                done = False
                for instruction in instructions:
                    if instruction.address >= max_address:
                        while lines and lines[-1].is_trimmable():
                            lines.pop()
                        done = True
                        break
                    address = self.address_fmt.format(instruction.address)
                    lines.append(InstructionLine(ctl, address, instruction.operation, comment_index, comment))
                    ctl = ' '
                if done:
                    break
            else:
                # This line is an instruction-level comment continuation line
                lines.append(InstructionLine(comment_index=comment_index, comment=comment))
        f.close()

        if start_index < 0:
            return lines
        if start_index < len(lines):
            if str(lines[start_index])[0] in DIRECTIVES:
                while start_index > 0 and not lines[start_index].is_blank():
                    start_index -= 1
            else:
                while start_index < len(lines) and not lines[start_index].is_blank():
                    start_index += 1
            return lines[start_index + 1:]
        return []

    def write_skool(self, min_address=0, max_address=65536):
        for line in self._parse_sft(min_address, max_address):
            write_line(str(line))
