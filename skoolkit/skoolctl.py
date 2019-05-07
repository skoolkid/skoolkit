# Copyright 2010-2019 Richard Dymond (rjdymond@gmail.com)
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

import re

from skoolkit import SkoolParsingError, write_line, get_int_param, get_address_format, open_file
from skoolkit.skoolparser import (Comment, Register, parse_comment_block, parse_instruction,
                                  parse_address_comments, join_comments, read_skool, DIRECTIVES)
from skoolkit.z80 import get_size, parse_string, parse_word, split_operation

ASM_DIRECTIVES = 'a'
BLOCKS = 'b'
BLOCK_TITLES = 't'
BLOCK_DESC = 'd'
REGISTERS = 'r'
BLOCK_COMMENTS = 'm'
SUBBLOCKS = 's'
COMMENTS = 'c'
NON_ENTRY_BLOCKS = 'n'

# ASM directives
AD_START = 'start'
AD_ORG = 'org'
AD_IGNOREUA = 'ignoreua'
AD_LABEL = 'label'

# An entry ASM directive is one that should be placed before the entry title
# when it is associated with the first instruction in the entry
RE_ENTRY_ASM_DIRECTIVE = re.compile("assemble=|def[bsw]=|end$|equ=|if\(|org$|org=|remote=|replace=|set-[-a-z]+=|start$|writer=")

# Comment types to which the @ignoreua directive may be applied
TITLE = 't'
DESCRIPTION = 'd'
REGISTERS = 'r'
MID_BLOCK = 'm'
INSTRUCTION = 'i'
END = 'e'

FORMAT_NO_BASE = {
    'b': 'b{}',
    'c': 'c{}',
    'd': '{}',
    'h': '{}',
    'm': 'm{}'
}

FORMAT_PRESERVE_BASE = {
    'b': 'b{}',
    'c': 'c{}',
    'd': 'd{}',
    'h': 'h{}',
    'm': 'm{}'
}

def _get_base(item, preserve_base=True):
    if item.startswith('%'):
        return 'b'
    if item.startswith('"'):
        return 'c'
    if item.startswith('$') and preserve_base:
        return 'h'
    if item.startswith('-'):
        return 'm'
    return 'd'

def get_operand_bases(operation, preserve_base):
    elements = split_operation(operation, True)
    if not elements:
        return ''
    if preserve_base:
        base_fmt = {'b': 'b', 'c': 'c', 'd': 'd', 'h': 'h', 'm': 'm'}
    else:
        base_fmt = {'b': 'b', 'c': 'c', 'd': 'n', 'h': 'n', 'm': 'm'}
    if elements[0] in ('BIT', 'RES', 'SET'):
        operands = elements[2:]
    else:
        operands = elements[1:]
    bases = ''
    for operand in operands:
        if operand.startswith(('(IX+', '(IX-', '(IY+', '(IY-')):
            num = operand[4:]
        elif operand.startswith('('):
            num = operand[1:]
        else:
            num = operand
        if num.startswith(('"', '%', '$', '-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
            bases += base_fmt[_get_base(num)]
    if bases in ('n', 'nn'):
        return ''
    return bases

def get_instruction_ctl(op):
    op = op.upper()
    if op.startswith('DEFB'):
        return 'B'
    if op.startswith('DEFW'):
        return 'W'
    if op.startswith('DEFM'):
        return 'T'
    if op.startswith('DEFS'):
        return 'S'
    return 'C'

def get_defb_length(operation, preserve_base):
    parts = split_operation(operation)
    if parts.pop(0).upper() == 'DEFB':
        byte_fmt = FORMAT_NO_BASE
        text_fmt = 'T{}'
    else:
        byte_fmt = {'b': 'b{}', 'd': 'B{}', 'h': 'B{}', 'm': 'm{}'}
        text_fmt = '{}'
    if preserve_base:
        byte_fmt = FORMAT_PRESERVE_BASE
    full_length = 0
    lengths = []
    length = 0
    prev_base = None
    for item in parts + ['""']:
        c_data = parse_string(item)
        if c_data is not None:
            if length:
                lengths.append(byte_fmt[prev_base].format(length))
                full_length += length
                prev_base = None
            length = len(c_data)
            if length:
                lengths.append(text_fmt.format(length))
                full_length += length
                length = 0
        else:
            cur_base = _get_base(item, preserve_base)
            if cur_base == 'c':
                cur_base = 'd'
            if prev_base != cur_base and length:
                lengths.append(byte_fmt[prev_base].format(length))
                full_length += length
                length = 0
            length += 1
            prev_base = cur_base
    return full_length, ':'.join(lengths)

def get_defw_length(operation, preserve_base):
    if preserve_base:
        word_fmt = FORMAT_PRESERVE_BASE
    else:
        word_fmt = FORMAT_NO_BASE
    full_length = 0
    lengths = []
    length = 0
    prev_base = None
    for item in split_operation(operation)[1:]:
        cur_base = _get_base(item, preserve_base)
        if prev_base != cur_base and length:
            lengths.append(word_fmt[prev_base].format(length))
            full_length += length
            length = 0
        length += 2
        prev_base = cur_base
    lengths.append(word_fmt[prev_base].format(length))
    full_length += length
    return full_length, ':'.join(lengths)

def get_defs_length(operation, preserve_base):
    if preserve_base:
        fmt = FORMAT_PRESERVE_BASE
    else:
        fmt = FORMAT_NO_BASE
    items = split_operation(operation)[1:3]

    try:
        size = parse_word(items[0])
    except ValueError:
        raise SkoolParsingError("Invalid integer '{}': {}".format(items[0], operation))
    size_base = _get_base(items[0], preserve_base)
    try:
        get_int_param(items[0])
        size_fmt = fmt[size_base].format(items[0])
    except ValueError:
        size_fmt = fmt[size_base].format(size)

    if len(items) == 1:
        return size, size_fmt

    value_base = _get_base(items[1], preserve_base)
    if value_base in 'dh' and not preserve_base:
        value_base = 'n'
    return size, '{}:{}'.format(size_fmt, value_base)

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

def extract_entry_asm_directives(asm_directives):
    entry_asm_dirs = []
    for directive in asm_directives[:]:
        if RE_ENTRY_ASM_DIRECTIVE.match(directive):
            entry_asm_dirs.append(directive)
            asm_directives.remove(directive)
    return entry_asm_dirs

class CtlWriter:
    def __init__(self, skoolfile, elements='abtdrmscn', write_hex=0,
                 preserve_base=False, min_address=0, max_address=65536, keep_lines=0):
        self.keep_lines = keep_lines > 0
        self.parser = SkoolParser(skoolfile, preserve_base, min_address, max_address, self.keep_lines)
        self.elements = elements
        self.write_asm_dirs = ASM_DIRECTIVES in elements
        self.address_fmt = get_address_format(write_hex, write_hex == 1)

    def write(self):
        for entry in self.parser.memory_map:
            self.write_entry(entry)
        if self.parser.end_address < 65536:
            write_line('i {}'.format(self.addr_str(self.parser.end_address)))

    def _write_asm_directive(self, directive, address):
        write_line('@ {} {}'.format(self.addr_str(address), directive))

    def _write_entry_asm_directive(self, entry, directive):
        if self.write_asm_dirs:
            self._write_asm_directive(directive, entry.address)

    def _write_entry_ignoreua_directive(self, entry, comment_type):
        if entry.ignoreua[comment_type] and self.write_asm_dirs:
            self._write_asm_directive('{}:{}'.format(AD_IGNOREUA, comment_type), entry.address)

    def _write_instruction_asm_directives(self, instruction):
        if self.write_asm_dirs:
            address = instruction.address
            for directive in instruction.asm_directives:
                self._write_asm_directive(directive, address)
            if instruction.ignoreua:
                self._write_asm_directive('{}:{}'.format(AD_IGNOREUA, INSTRUCTION), address)

    def _write_blocks(self, blocks, address, footer=False):
        if NON_ENTRY_BLOCKS in self.elements:
            prefix = '> ' + address
            if footer:
                prefix += ',1'
            for index, block in enumerate(blocks):
                if index:
                    write_line(prefix)
                for line in block:
                    write_line('{} {}'.format(prefix, line))

    def _write_lines(self, lines, ctl=None, address=None, grouped=False):
        if ctl:
            write_line('{} {}'.format(ctl, address))
        if grouped:
            for index, group in enumerate(lines):
                for line_no, line in enumerate(group):
                    if line_no and index < len(lines) - 1:
                        write_line((': ' + line).rstrip())
                    else:
                        write_line(('. ' + line).rstrip())
        else:
            for line in lines:
                write_line(('. ' + line).rstrip())

    def _write_block_comments(self, comments, ctl, address):
        if self.keep_lines:
            self._write_lines(comments, ctl, address)
        else:
            for p in comments:
                write_line('{} {} {}'.format(ctl, address, p))

    def write_entry(self, entry):
        address = self.addr_str(entry.address)

        self._write_blocks(entry.header, address)

        for directive in entry.asm_directives:
            self._write_entry_asm_directive(entry, directive)

        self._write_entry_ignoreua_directive(entry, TITLE)
        if BLOCKS in self.elements:
            if BLOCK_TITLES in self.elements and not self.keep_lines:
                write_line('{} {} {}'.format(entry.ctl, address, entry.title).rstrip())
            else:
                write_line('{0} {1}'.format(entry.ctl, address))
                if self.keep_lines:
                    self._write_lines(entry.title)

        self._write_entry_ignoreua_directive(entry, DESCRIPTION)
        if entry.description and BLOCK_DESC in self.elements:
            self._write_block_comments(entry.description, 'D', address)

        self._write_entry_ignoreua_directive(entry, REGISTERS)
        if entry.registers and REGISTERS in self.elements:
            if self.keep_lines:
                self._write_lines(entry.registers[0].contents, 'R', address)
            else:
                for reg in entry.registers:
                    if reg.prefix:
                        name = '{}:{}'.format(reg.prefix, reg.name)
                    else:
                        name = reg.name
                    write_line('R {} {} {}'.format(address, name, reg.contents).rstrip())

        self.write_body(entry)

        self._write_entry_ignoreua_directive(entry, END)
        if entry.end_comment and BLOCK_COMMENTS in self.elements:
            self._write_block_comments(entry.end_comment, 'E', address)

        self._write_blocks(entry.footer, address, True)

    def write_body(self, entry):
        if entry.ctl in 'gu':
            entry_ctl = 'b'
        else:
            entry_ctl = entry.ctl
        first_instruction = entry.instructions[0]
        if entry_ctl == 'i' and not first_instruction.operation:
            # Don't write any sub-blocks for an empty 'i' entry
            return

        # Split the entry into sections separated by mid-block comments
        sections = []
        for instruction in entry.instructions:
            mbc = instruction.mid_block_comment
            if mbc or not sections:
                sections.append((mbc, [instruction]))
            else:
                sections[-1][1].append(instruction)

        for k, (mbc, instructions) in enumerate(sections):
            if BLOCK_COMMENTS in self.elements and mbc:
                first_instruction = instructions[0]
                if first_instruction.ignoremrcua and self.write_asm_dirs:
                    self._write_asm_directive('{}:{}'.format(AD_IGNOREUA, MID_BLOCK), first_instruction.address)
                self._write_block_comments(mbc, 'N', self.addr_str(first_instruction.address))

            if SUBBLOCKS in self.elements:
                sub_blocks = self.get_sub_blocks(instructions)
                for j, (ctl, instructions) in enumerate(sub_blocks):
                    has_bases = False
                    for instruction in instructions:
                        self._write_instruction_asm_directives(instruction)
                        if instruction.bases:
                            has_bases = True
                    first_instruction = instructions[0]
                    if ctl != 'M' or COMMENTS in self.elements:
                        if ctl == 'M':
                            offset = first_instruction.comment.rowspan
                            index = j + 1
                            while offset > 0 and index < len(sub_blocks):
                                offset -= len(sub_blocks[index][1])
                                index += 1
                            if index < len(sub_blocks):
                                length = sub_blocks[index][1][0].address - first_instruction.address
                            elif k + 1 < len(sections):
                                length = sections[k + 1][1][0].address - first_instruction.address
                            else:
                                length = ''
                        else:
                            length = None
                        comment_text = ''
                        comment = first_instruction.comment
                        write_comment = False
                        if comment and COMMENTS in self.elements:
                            comment_text = comment.text
                            if self.keep_lines:
                                write_comment = comment.rowspan > 1 or comment.text[0] != ['']
                            else:
                                if comment.rowspan > 1 and not comment.text.replace('.', ''):
                                    comment_text = '.' + comment_text
                                write_comment = comment_text != ''
                        if write_comment or ctl.lower() != entry_ctl or ctl != 'C' or has_bases:
                            self.write_sub_block(ctl, entry_ctl, comment_text, instructions, length)

    def addr_str(self, address):
        return self.address_fmt.format(address)

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
            if comment and (comment.rowspan > 1 or any(comment.text)):
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
                # the previous instruction (which is also commentless), so add
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

    def write_sub_block(self, ctl, entry_ctl, comment, instructions, lengths):
        length = 0
        sublengths = []
        address = instructions[0].address
        if ctl == 'C':
            # Compute the sublengths for a 'C' sub-block
            for i, instruction in enumerate(instructions):
                addr = instruction.address
                if i < len(instructions) - 1:
                    sublength = instructions[i + 1].address - addr
                else:
                    sublength = get_size(instruction.operation, addr)
                if sublength > 0:
                    length += sublength
                    bases = instruction.bases
                    if sublengths and bases == sublengths[-1][0]:
                        sublengths[-1][1] += sublength
                    else:
                        sublengths.append([bases, sublength])
            if not any(comment) and len(sublengths) > 1 and entry_ctl == 'c':
                if not sublengths[-1][0]:
                    length -= sublengths.pop()[1]
                if not sublengths[0][0]:
                    sublength = sublengths.pop(0)[1]
                    length -= sublength
                    address += sublength
            lengths = ','.join(['{}{}'.format(*s) for s in sublengths])
            if len(sublengths) > 1:
                lengths = '{},{}'.format(length, lengths)
        elif ctl in 'BSTW':
            # Compute the sublengths for a 'B', 'S', 'T' or 'W' sub-block
            for statement in instructions:
                length += statement.size
                sublengths.append(statement.length)
            while len(sublengths) > 1 and sublengths[-1] == sublengths[-2]:
                sublengths.pop()
            lengths = '{},{}'.format(length, get_lengths(sublengths))

        addr_str = self.addr_str(address)
        if lengths:
            lengths = ',{}'.format(lengths)
        if isinstance(comment, str):
            write_line('{} {}{} {}'.format(ctl, addr_str, lengths, comment).rstrip())
        else:
            # Remove redundant trailing blank lines
            min_comments = min(len(instructions) - 1, 1)
            while len(comment) > min_comments and comment[-1] == ['']:
                comment.pop()
            self._write_lines(comment, ctl, addr_str + lengths, True)

class SkoolParser:
    def __init__(self, skoolfile, preserve_base, min_address, max_address, keep_lines):
        self.skoolfile = skoolfile
        self.preserve_base = preserve_base
        self.mode = Mode()
        self.memory_map = []
        self.end_address = 65536
        self.keep_lines = keep_lines

        with open_file(skoolfile) as f:
            self._parse_skool(f, min_address, max_address)

    def _parse_skool(self, skoolfile, min_address, max_address):
        address_comments = []
        non_entries = []
        done = False
        for non_entry, block in read_skool(skoolfile, 1):
            if non_entry:
                non_entries.append(block)
                continue
            map_entry = None
            instruction = None
            comments = []
            ignores = []
            address_comments.append((None, None, None))
            for line in block:
                if line.startswith(';'):
                    self._parse_comment_line(comments, line)
                    instruction = None
                    address_comments.append((None, None, None))
                    continue

                if line.startswith('@'):
                    self._parse_asm_directive(line[1:], ignores, len(comments))
                    continue

                s_line = line.lstrip()
                if s_line.startswith(';'):
                    if map_entry and instruction:
                        # This is an instruction comment continuation line
                        self._parse_comment_line(address_comments[-1][1], s_line)
                    continue

                # This line contains an instruction
                instruction, address_comment = self._parse_instruction(line)
                address = instruction.address
                if address < min_address:
                    non_entries.clear()
                    break
                if address >= max_address:
                    non_entries.clear()
                    map_entry = None
                    done = True
                    break
                ctl = instruction.ctl
                if ctl in DIRECTIVES:
                    start_comment, title, description, registers = parse_comment_block(comments, ignores, self.mode, self.keep_lines)
                    map_entry = Entry(ctl, title, description, registers, self.mode.entry_ignoreua)
                    instruction.mid_block_comment = start_comment
                    map_entry.asm_directives = extract_entry_asm_directives(instruction.asm_directives)
                    self.memory_map.append(map_entry)
                    comments[:] = []
                    instruction.ignoremrcua = self.mode.ignoremrcua

                if map_entry:
                    address_comments.append((instruction, [address_comment], []))
                    map_entry.add_instruction(instruction)
                    if comments:
                        instruction.mid_block_comment = join_comments(comments, True, self.keep_lines)
                        comments = []
                        instruction.ignoremrcua = 0 in ignores
                        instruction.ignoreua = any(ignores)
                    elif ignores:
                        instruction.ignoreua = True

                ignores[:] = []

            if map_entry:
                if comments:
                    map_entry.end_comment = join_comments(comments, True, self.keep_lines)
                    map_entry.ignoreua[END] = len(ignores) > 0
                map_entry.header = non_entries
                non_entries = []

            if done:
                break

        if self.memory_map:
            self.memory_map[-1].footer = non_entries

        last_entry = None
        last_instruction = None
        for entry in self.memory_map:
            entry.sort_instructions()
            if last_entry is None or last_entry.address < entry.address:
                last_entry = entry
            end_instruction = entry.instructions[-1]
            if last_instruction is None or last_instruction.address < end_instruction.address:
                last_instruction = end_instruction
        if last_entry is not None and last_entry.ctl != 'i':
            address = last_instruction.address
            self.end_address = address + (get_size(last_instruction.operation, address) or 1)

        parse_address_comments(address_comments, self.keep_lines)

    def _parse_comment_line(self, comments, line):
        if line.startswith('; '):
            comments.append(line[2:].rstrip())
        else:
            comments.append(line[1:].rstrip())

    def _parse_asm_directive(self, directive, ignores, line_no):
        if directive == AD_IGNOREUA:
            ignores.append(line_no)
        else:
            self.mode.add_asm_directive(directive)

    def _parse_instruction(self, line):
        ctl, addr_str, operation, comment = parse_instruction(line)
        try:
            address = get_int_param(addr_str)
        except ValueError:
            raise SkoolParsingError("Invalid address ({}):\n{}".format(addr_str, line.rstrip()))
        instruction = Instruction(ctl, address, operation, self.preserve_base)
        self.mode.apply_asm_directives(instruction)
        return instruction, comment

class Mode:
    def __init__(self):
        self.asm_directives = []
        self.entry_ignoreua = {}
        self.lower = False
        self.upper = False

    def add_asm_directive(self, directive):
        self.asm_directives.append(directive)

    def apply_asm_directives(self, instruction):
        instruction.asm_directives = self.asm_directives
        self.asm_directives = []

class FakeInstruction:
    def __init__(self, address, comment):
        self.address = address
        self.comment = comment
        self.asm_directives = ()
        self.ignoreua = False
        self.bases = ''

class Instruction:
    def __init__(self, ctl, address, operation, preserve_base):
        self.ctl = ctl
        self.address = address
        self.operation = operation
        self.mid_block_comment = None
        self.comment = None
        self.asm_directives = None
        self.ignoreua = False
        self.ignoremrcua = False
        self.inst_ctl = get_instruction_ctl(operation)
        self.bases = ''
        self.size = None
        self.length = None
        if self.inst_ctl == 'B':
            self.size, self.length = get_defb_length(operation, preserve_base)
        elif self.inst_ctl == 'T':
            self.size, self.length = get_defb_length(operation, preserve_base)
        elif self.inst_ctl == 'W':
            self.size, self.length = get_defw_length(operation, preserve_base)
        elif self.inst_ctl == 'S':
            self.size, self.length = get_defs_length(operation, preserve_base)
        else:
            self.bases = get_operand_bases(operation, preserve_base)

    def set_comment(self, rowspan, text):
        self.comment = Comment(rowspan, text)

class Entry:
    def __init__(self, ctl, title, description, registers, ignoreua):
        self.header = ()
        self.footer = ()
        self.ctl = ctl
        self.title = title
        self.description = description
        self.registers = [Register(prefix, name, desc) for prefix, name, desc in registers]
        self.ignoreua = {
            TITLE: ignoreua['t'],
            DESCRIPTION: ignoreua['d'],
            REGISTERS: ignoreua['r'],
            END: False
        }
        self.instructions = []
        self.end_comment = ()
        self.asm_directives = None

    def sort_instructions(self):
        self.instructions.sort(key=lambda i: i.address)
        self.address = self.instructions[0].address

    def add_instruction(self, instruction):
        self.instructions.append(instruction)
