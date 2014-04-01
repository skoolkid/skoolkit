# -*- coding: utf-8 -*-

# Copyright 2010-2014 Richard Dymond (rjdymond@gmail.com)
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

from . import write_line, parse_int, open_file
from .skoolparser import (DIRECTIVES, parse_asm_block_directive, get_instruction_ctl,
                          get_defb_length, get_defm_length, get_defs_length, get_defw_length)

BLOCKS = 'b'
BLOCK_TITLES = 't'
BLOCK_DESC = 'd'
REGISTERS = 'r'
BLOCK_COMMENTS = 'm'
SUBBLOCKS = 's'
COMMENTS = 'c'

# Entry-level ASM directives
AD_START = 'start'
AD_WRITER = 'writer'
AD_ORG = 'org'
AD_END = 'end'
AD_SET = 'set-'

def get_lengths(stmt_lengths):
    # Find subsequences of identical statement lengths and abbreviate them,
    # e.g. '16,16,16,8,8,4' -> '16*3,8*2,4'
    lengths = []
    prev = None
    for length in stmt_lengths:
        if length == prev:
            lengths[-1][1] += 1
        else:
            lengths.append([length, 1])
            prev = length
    length_params = []
    for length, mult in lengths:
        if mult == 1:
            length_params.append(length)
        else:
            length_params.append('{0}*{1}'.format(length, mult))
    return ','.join(length_params)

class CtlWriter:
    def __init__(self, skoolfile, elements='btdrmsc', write_hex=False, write_asm_dirs=True, preserve_base=False):
        parser = SkoolParser(skoolfile, preserve_base)
        self.entries = parser.memory_map
        self.elements = elements
        self.write_hex = write_hex
        self.write_asm_dirs = write_asm_dirs

    def write(self):
        for entry in self.entries:
            self.write_entry(entry)

    def _write_asm_directive(self, directive, address, value):
        if value is None:
            suffix = ''
        else:
            suffix = '={0}'.format(value)
        write_line('; @{0}:{1}{2}'.format(directive, address, suffix))

    def _write_entry_asm_directive(self, entry, directive, value=None):
        if self.write_asm_dirs:
            self._write_asm_directive(directive, self.addr_str(entry.address, False), value)

    def _write_instruction_asm_directives(self, instruction):
        if not self.write_asm_dirs:
            return
        address = self.addr_str(instruction.address, False)
        for directive, value in instruction.asm_directives:
            self._write_asm_directive(directive, address, value)

    def write_entry(self, entry):
        if entry.start:
            self._write_entry_asm_directive(entry, AD_START)
        if entry.writer:
            self._write_entry_asm_directive(entry, AD_WRITER, entry.writer)
        for name, value in entry.properties:
            self._write_entry_asm_directive(entry, '{0}{1}'.format(AD_SET, name), value)
        if entry.org:
            self._write_entry_asm_directive(entry, AD_ORG, entry.org)
        address = self.addr_str(entry.address)
        if BLOCKS in self.elements:
            if BLOCK_TITLES in self.elements:
                write_line('{0} {1} {2}'.format(entry.ctl, address, entry.description).rstrip())
            else:
                write_line('{0} {1}'.format(entry.ctl, address))
        if BLOCK_DESC in self.elements:
            for p in entry.details:
                write_line('D {0} {1}'.format(address, p))
        if REGISTERS in self.elements:
            for reg in entry.registers:
                write_line('R {0} {1} {2}'.format(address, reg.name, reg.contents))
        self.write_body(entry)
        if BLOCK_COMMENTS in self.elements:
            for p in entry.end_comment:
                write_line('E {0} {1}'.format(address, p))
        if entry.end:
            self._write_entry_asm_directive(entry, AD_END)

    def write_body(self, entry):
        if entry.ctl in 'gu':
            entry_ctl = 'b'
        else:
            entry_ctl = entry.ctl
        first_instruction = entry.instructions[0]
        if entry_ctl == 'i' and not first_instruction.operation:
            # Don't write any sub-blocks for an empty 'i' entry
            return

        # Split the entry into sections separated by mid-routine comments
        sections = [('', [first_instruction])]
        for instruction in entry.instructions[1:]:
            mrc = instruction.get_mid_routine_comment()
            if mrc:
                sections.append((mrc, [instruction]))
            else:
                sections[-1][1].append(instruction)

        for k, (mrc, instructions) in enumerate(sections):
            if BLOCK_COMMENTS in self.elements and mrc:
                address = instructions[0].address
                for paragraph in mrc:
                    write_line('D {0} {1}'.format(self.addr_str(address), paragraph))

            if SUBBLOCKS in self.elements:
                sub_blocks = self.get_sub_blocks(instructions)
                for j, (ctl, instructions) in enumerate(sub_blocks):
                    for instruction in instructions:
                        self._write_instruction_asm_directives(instruction)
                    if ctl != 'M' or COMMENTS in self.elements:
                        length = None
                        if ctl == 'M':
                            offset = instructions[0].comment.rowspan + 1
                        else:
                            offset = 1
                        if j + offset < len(sub_blocks):
                            length = int(sub_blocks[j + offset][1][0].address) - int(instructions[0].address)
                        elif k + 1 < len(sections):
                            length = int(sections[k + 1][1][0].address) - int(instructions[0].address)
                        comment_text = ''
                        comment = instructions[0].comment
                        if comment and COMMENTS in self.elements:
                            comment_text = comment.text
                            if comment.rowspan > 1 and not comment_text.replace('.', ''):
                                comment_text = '.' + comment_text
                        if comment_text or ctl != entry_ctl or ctl != 'c':
                            self.write_sub_block(ctl, entry_ctl, comment_text, instructions, length)

    def addr_str(self, address, pad=True):
        if self.write_hex:
            return '${:04X}'.format(address)
        if pad:
            return '{:05d}'.format(address)
        return str(address)

    def get_sub_blocks(self, instructions):
        # Split a block of instructions into sub-blocks by comment rowspan
        # and/or instruction type
        sub_blocks = []
        i = 0
        prev_ctl = ''
        while i < len(instructions):
            instruction = instructions[i]
            comment = instruction.comment
            ctl = instruction.inst_ctl
            if comment and (comment.rowspan > 1 or comment.text):
                inst_ctls = set()
                for inst in instructions[i:i + comment.rowspan]:
                    inst_ctls.add(inst.inst_ctl)
                if len(inst_ctls) > 1:
                    # We've found a set of two or more instructions of various
                    # types with a single comment, so add a commented 'M'
                    # sub-block and commentless sub-blocks for the instructions
                    sub_blocks.append(('M', [FakeInstruction(instruction.address, instruction.comment)]))
                    instruction.comment = None
                    sub_blocks += self.get_sub_blocks(instructions[i:i + comment.rowspan])
                else:
                    # We've found a set of one or more instructions of the same
                    # type with a comment, so add a new sub-block
                    sub_blocks.append((ctl, instructions[i:i + comment.rowspan]))
                prev_ctl = ''
            elif ctl == prev_ctl:
                # This instruction is commentless and is of the same type as
                # the previous instruction (which was also commentless), so add
                # it to the current sub-block
                sub_blocks[-1][1].append(instruction)
            else:
                # This instruction is commentless but of a different type from
                # the previous instruction, so start a new sub-block
                sub_blocks.append((ctl, [instruction]))
                prev_ctl = ctl
            if comment:
                i += comment.rowspan
            else:
                i += 1
        return sub_blocks

    def write_sub_block(self, ctl, entry_ctl, comment, instructions, length):
        if ctl == entry_ctl:
            sub_block_ctl = ' '
        else:
            sub_block_ctl = ctl.upper()
        address = self.addr_str(instructions[0].address)
        lengths = ''

        if ctl in 'bstw':
            # Find the byte lengths of each line in a 'B', 'S', 'T' or 'W'
            # sub-block
            length = 0
            stmt_lengths = []
            for stmt in instructions:
                length += stmt.size
                stmt_lengths.append(stmt.length)
            while len(stmt_lengths) > 1 and stmt_lengths[-1] == stmt_lengths[-2]:
                stmt_lengths.pop()
            lengths = ',' + get_lengths(stmt_lengths)

        if length:
            write_line('{0} {1},{2}{3} {4}'.format(sub_block_ctl, address, length, lengths, comment).rstrip())
        else:
            write_line('{0} {1} {2}'.format(sub_block_ctl, address, comment).rstrip())

class SkoolParser:
    def __init__(self, skoolfile, preserve_base):
        self.skoolfile = skoolfile
        self.preserve_base = preserve_base
        self.mode = Mode()
        self.memory_map = []
        self.header = []
        self.stack = []

        with open_file(skoolfile) as f:
            self._parse_skool(f)

    def _parse_skool(self, skoolfile):
        map_entry = None
        instruction = None
        comments = []
        address_comments = []
        for line in skoolfile:
            if line[0] == ';':
                if self._parse_comment(line, comments):
                    instruction = None
                continue # pragma: no cover

            if not self.mode.include:
                continue

            s_line = line.strip()
            if not s_line:
                instruction = None
                if comments:
                    if map_entry:
                        map_entry.end_comment = self._join_comments(comments, True)
                    else:
                        self.header += comments
                # Process an '@end' directive if one was found
                if self.mode.entry_asm_directives and map_entry:
                    self.mode.apply_entry_asm_directives(map_entry)
                comments[:] = []
                map_entry = None
                continue

            if s_line[0] == ';' and map_entry and instruction:
                # This is an instruction comment continuation line
                address_comments[-1][1] = '{0} {1}'.format(address_comments[-1][1], s_line[1:].lstrip())
                continue

            # This line contains an instruction
            instruction, address_comment = self._parse_instruction(line)
            address = instruction.address
            addr_str = instruction.addr_str
            ctl = instruction.ctl
            if ctl in DIRECTIVES:
                desc, details, registers = self._parse_comment_block(comments)
                map_entry = Entry(address, addr_str, ctl, desc, details, registers)
                self.mode.apply_entry_asm_directives(map_entry)
                self.memory_map.append(map_entry)
                comments[:] = []
            elif ctl in 'dr':
                # This is a data definition entry or a remote entry
                map_entry = None

            if map_entry:
                address_comments.append([instruction, address_comment])
                map_entry.add_instruction(instruction)
                if comments:
                    mid_routine_comment = self._join_comments(comments, True)
                    map_entry.add_mid_routine_comment(instruction.label, mid_routine_comment)
                    comments[:] = []

        if comments and map_entry:
            map_entry.end_comment = self._join_comments(comments, True)

        self._parse_address_comments(address_comments)

    def _join_comments(self, comments, split=False):
        sections = [[]]
        for line in comments:
            s_line = line.strip()
            if split and s_line == '.':
                sections.append([])
            elif s_line:
                sections[-1].append(s_line)
        paragraphs = [" ".join(section) for section in sections if section]
        if split:
            return paragraphs
        if paragraphs:
            return paragraphs[0]
        return ''

    def _parse_comment(self, line, comments):
        """Parses a comment line. Returns False if the line contains an ASM (@)
        directive, and True otherwise."""
        comment = line[2:].rstrip()
        if comment.startswith('@'):
            self._parse_asm_directive(comment[1:])
            return False
        if self.mode.include:
            comments.append(comment)
        return True

    def _parse_asm_directive(self, directive):
        if parse_asm_block_directive(directive, self.stack):
            self.mode.include = True
            for _p, i in self.stack:
                if i != '-':
                    self.mode.include = False
                    break
            return

        if self.mode.include:
            tag, sep, value = directive.rstrip().partition('=')
            if sep and tag in ('rsub', 'ssub', 'isub', 'bfix', 'ofix', 'label', 'rem'):
                self.mode.add_instruction_asm_directive(tag, value)
            elif not sep and tag in ('nolabel', 'nowarn', 'ignoreua', 'keep'):
                self.mode.add_instruction_asm_directive(tag)
            elif sep and tag in (AD_ORG, AD_WRITER):
                self.mode.add_entry_asm_directive(tag, value)
            elif sep and tag.startswith(AD_SET):
                self.mode.add_entry_asm_directive(tag, value)
            elif not sep and tag in (AD_START, AD_END):
                self.mode.add_entry_asm_directive(tag)

    def _parse_instruction(self, line):
        ctl = line[0]
        addr_str = line[1:6]
        address = parse_int(addr_str)
        comment_index = line.find(';')
        if comment_index < 0:
            comment_index = len(line)
        operation = line[7:comment_index].strip()
        address_comment = line[comment_index + 1:].strip()
        instruction = Instruction(ctl + addr_str, address, operation, self.preserve_base)
        self.mode.apply_instruction_asm_directives(instruction)
        return instruction, address_comment

    def _parse_comment_block(self, comments):
        sections = [[], [], []]
        index = 0
        last_line = ""
        for line in comments:
            if len(line) == 0:
                if len(last_line) > 0:
                    index += 1
                continue # pragma: no cover
            sections[index].append(line)
            last_line = line
        registers = [reg_line.split(None, 1) for reg_line in sections[2]]
        return [self._join_comments(sections[0]), self._join_comments(sections[1], True), registers]

    def _parse_address_comments(self, comments):
        i = 0
        while i < len(comments):
            instruction, comment = comments[i]
            comment_lines = []
            if comment and comment.strip()[0] == '{':
                nesting = comment.count('{') - comment.count('}')
                while nesting > 0:
                    comment_lines.append(comments[i][1])
                    i += 1
                    nesting += comments[i][1].count('{') - comments[i][1].count('}')
                comment_lines.append(comments[i][1].strip('}'))
                comment_lines[0] = comment_lines[0].strip('{')
            else:
                comment_lines.append(comment)
            rowspan = len(comment_lines)
            address_comment = self._join_comments(comment_lines).strip()
            instruction.set_comment(rowspan, address_comment)
            i += 1

class Mode:
    def __init__(self):
        self.include = True
        self.instruction_asm_directives = []
        self.entry_asm_directives = []

    def add_instruction_asm_directive(self, directive, value=None):
        self.instruction_asm_directives.append((directive, value))

    def add_entry_asm_directive(self, directive, value=None):
        self.entry_asm_directives.append((directive, value))

    def apply_instruction_asm_directives(self, instruction):
        instruction.asm_directives = self.instruction_asm_directives
        self.instruction_asm_directives = []

    def apply_entry_asm_directives(self, entry):
        for directive, value in self.entry_asm_directives:
            if directive == AD_ORG:
                entry.org = value
            elif directive == AD_WRITER:
                entry.writer = value
            elif directive == AD_START:
                entry.start = True
            elif directive == AD_END:
                entry.end = True
            elif directive.startswith(AD_SET):
                entry.add_property(directive[len(AD_SET):], value)
        self.entry_asm_directives = []

class FakeInstruction:
    def __init__(self, address, comment):
        self.address = address
        self.comment = comment
        self.asm_directives = ()

class Instruction:
    def __init__(self, label, address, operation, preserve_base):
        self.label = label
        self.ctl = label[0]
        if label[1].isdigit():
            self.addr_str = label[1:]
        else:
            self.addr_str = label[2:]
        self.address = address
        self.operation = operation
        self.container = None
        self.comment = None
        self.asm_directives = None
        self.inst_ctl = get_instruction_ctl(operation).lower()
        self.size = None
        self.length = None
        if self.inst_ctl == 'b':
            self.size, self.length = get_defb_length(operation[5:], preserve_base)
        elif self.inst_ctl == 't':
            self.size, self.length = get_defm_length(operation[5:], preserve_base)
        elif self.inst_ctl == 'w':
            self.size, self.length = get_defw_length(operation[5:], preserve_base)
        elif self.inst_ctl == 's':
            self.size, self.length = get_defs_length(operation[5:], preserve_base)

    def set_comment(self, rowspan, text):
        self.comment = Comment(rowspan, text)

    def get_mid_routine_comment(self):
        return self.container.get_mid_routine_comment(self.label)

class Entry:
    def __init__(self, address, addr_str=None, ctl=None, description=None, details=(), registers=()):
        self.address = address
        self.addr_str = addr_str
        self.ctl = ctl
        self.description = description
        self.details = details
        self.registers = [Register(name, contents) for name, contents in registers]
        self.instructions = []
        self.mid_routine_comments = {}
        self.end_comment = ()
        self.org = None
        self.writer = None
        self.start = False
        self.end = False
        self.properties = []

    def add_instruction(self, instruction):
        instruction.container = self
        self.instructions.append(instruction)

    def get_mid_routine_comment(self, address):
        return self.mid_routine_comments.get(address, ())

    def add_mid_routine_comment(self, address, text):
        self.mid_routine_comments[address] = text

    def add_property(self, name, value):
        self.properties.append((name, value))

class Register:
    def __init__(self, name, contents):
        self.name = name
        self.contents = contents

class Comment:
    def __init__(self, rowspan, text):
        self.rowspan = rowspan
        self.text = text
