# Copyright 2010-2017 Richard Dymond (rjdymond@gmail.com)
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
from skoolkit.skoolparser import (Comment, Register, parse_comment_block, parse_instruction, parse_address_comments,
                                  join_comments, parse_asm_block_directive, DIRECTIVES)
from skoolkit.z80 import get_size, parse_string, parse_word, split_operation

ASM_DIRECTIVES = 'a'
BLOCKS = 'b'
BLOCK_TITLES = 't'
BLOCK_DESC = 'd'
REGISTERS = 'r'
BLOCK_COMMENTS = 'm'
SUBBLOCKS = 's'
COMMENTS = 'c'

# ASM directives
AD_START = 'start'
AD_ORG = 'org'
AD_IGNOREUA = 'ignoreua'

# An entry ASM directive is one that should be placed before the entry title
# when it is associated with the first instruction in the entry
RE_ENTRY_ASM_DIRECTIVE = re.compile("end$|equ=|org=|replace=|set-[-a-z]+=|start$|writer=")

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
    'h': '{}'
}

FORMAT_PRESERVE_BASE = {
    'b': 'b{}',
    'c': 'c{}',
    'd': 'd{}',
    'h': 'h{}'
}

def _get_base(item, preserve_base=True):
    if item.startswith('%'):
        return 'b'
    if item.startswith('"'):
        return 'c'
    if item.startswith('$') and preserve_base:
        return 'h'
    return 'd'

def get_operand_bases(operation, preserve_base):
    elements = split_operation(operation, True)
    if not elements:
        return ''
    if preserve_base:
        base_fmt = {'b': 'b', 'c': 'c', 'd': 'd', 'h': 'h'}
    else:
        base_fmt = {'b': 'b', 'c': 'c', 'd': 'n', 'h': 'n'}
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
        if num.startswith(('"', '%', '$', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
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
        byte_fmt = {'b': 'b{}', 'd': 'B{}', 'h': 'B{}'}
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
    values = []
    for item in split_operation(operation)[1:3]:
        base = _get_base(item, preserve_base)
        try:
            value = get_int_param(item)
        except ValueError:
            try:
                item = value = parse_word(item)
            except ValueError:
                raise SkoolParsingError("Invalid integer '{}': {}".format(item, operation))
            if base == 'c':
                base = 'd'
        values.append((value, fmt[base].format(item)))
    return values[0][0], ':'.join([v[1] for v in values])

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
    def __init__(self, skoolfile, elements='abtdrmsc', write_hex=0,
                 preserve_base=False, min_address=0, max_address=65536):
        self.parser = SkoolParser(skoolfile, preserve_base, min_address, max_address)
        self.elements = elements
        self.write_asm_dirs = ASM_DIRECTIVES in elements
        self.address_fmt = get_address_format(write_hex, write_hex < 0)

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

    def write_entry(self, entry):
        for directive in entry.asm_directives:
            self._write_entry_asm_directive(entry, directive)
        address = self.addr_str(entry.address)

        self._write_entry_ignoreua_directive(entry, TITLE)
        if BLOCKS in self.elements:
            if BLOCK_TITLES in self.elements:
                write_line('{0} {1} {2}'.format(entry.ctl, address, entry.description).rstrip())
            else:
                write_line('{0} {1}'.format(entry.ctl, address))

        self._write_entry_ignoreua_directive(entry, DESCRIPTION)
        if BLOCK_DESC in self.elements:
            for p in entry.details:
                write_line('D {0} {1}'.format(address, p))

        self._write_entry_ignoreua_directive(entry, REGISTERS)
        if REGISTERS in self.elements:
            for reg in entry.registers:
                if reg.prefix:
                    name = '{}:{}'.format(reg.prefix, reg.name)
                else:
                    name = reg.name
                write_line('R {} {} {}'.format(address, name, reg.contents).rstrip())

        self.write_body(entry)

        self._write_entry_ignoreua_directive(entry, END)
        if BLOCK_COMMENTS in self.elements:
            for p in entry.end_comment:
                write_line('E {0} {1}'.format(address, p))

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
                address_str = self.addr_str(first_instruction.address)
                for paragraph in mbc:
                    write_line('N {} {}'.format(address_str, paragraph))

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
                            offset = first_instruction.comment.rowspan + 1
                            if j + offset < len(sub_blocks):
                                length = sub_blocks[j + offset][1][0].address - first_instruction.address
                            elif k + 1 < len(sections):
                                length = sections[k + 1][1][0].address - first_instruction.address
                            else:
                                length = ''
                        else:
                            length = None
                        comment_text = ''
                        comment = first_instruction.comment
                        if comment and COMMENTS in self.elements:
                            comment_text = comment.text
                            if comment.rowspan > 1 and not comment_text.replace('.', ''):
                                comment_text = '.' + comment_text
                        if comment_text or ctl != entry_ctl or ctl != 'c' or has_bases:
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
        if ctl == 'c':
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
            if not comment and len(sublengths) > 1 and entry_ctl == 'c':
                if not sublengths[-1][0]:
                    length -= sublengths.pop()[1]
                if not sublengths[0][0]:
                    sublength = sublengths.pop(0)[1]
                    length -= sublength
                    address += sublength
            lengths = ','.join(['{}{}'.format(*s) for s in sublengths])
            if len(sublengths) > 1:
                lengths = '{},{}'.format(length, lengths)
        elif ctl in 'bstw':
            # Compute the sublengths for a 'B', 'S', 'T' or 'W' sub-block
            for statement in instructions:
                length += statement.size
                sublengths.append(statement.length)
            while len(sublengths) > 1 and sublengths[-1] == sublengths[-2]:
                sublengths.pop()
            lengths = '{},{}'.format(length, get_lengths(sublengths))

        if ctl == entry_ctl:
            sub_block_ctl = ' '
        else:
            sub_block_ctl = ctl.upper()
        addr_str = self.addr_str(address)
        if lengths:
            lengths = ',{}'.format(lengths)
        write_line('{} {}{} {}'.format(sub_block_ctl, addr_str, lengths, comment).rstrip())

class SkoolParser:
    def __init__(self, skoolfile, preserve_base, min_address, max_address):
        self.skoolfile = skoolfile
        self.preserve_base = preserve_base
        self.mode = Mode()
        self.memory_map = []
        self.stack = []
        self.end_address = 65536

        with open_file(skoolfile) as f:
            self._parse_skool(f, min_address, max_address)

    def _parse_skool(self, skoolfile, min_address, max_address):
        map_entry = None
        instruction = None
        comments = []
        ignores = []
        address_comments = []
        for line in skoolfile:
            if line.startswith(';'):
                if self.mode.include:
                    comments.append(line[2:].rstrip())
                instruction = None
                address_comments.append((None, None))
                continue

            if line.startswith('@'):
                self._parse_asm_directive(line[1:].rstrip(), ignores, len(comments))
                continue

            if not self.mode.include:
                continue

            s_line = line.strip()
            if not s_line:
                instruction = None
                address_comments.append((None, None))
                if comments and map_entry:
                    map_entry.end_comment = join_comments(comments, True)
                comments[:] = []
                map_entry = None
                continue

            if s_line.startswith(';'):
                if map_entry and instruction:
                    # This is an instruction comment continuation line
                    address_comments[-1][1] = '{} {}'.format(address_comments[-1][1], s_line[1:].lstrip())
                continue # pragma: no cover

            # This line contains an instruction
            instruction, address_comment = self._parse_instruction(line)
            address = instruction.address
            if address < min_address:
                continue
            if address >= max_address:
                map_entry = None
                break
            ctl = instruction.ctl
            if ctl in DIRECTIVES:
                start_comment, desc, details, registers = parse_comment_block(comments, ignores, self.mode)
                map_entry = Entry(ctl, desc, details, registers, self.mode.entry_ignoreua)
                instruction.mid_block_comment = start_comment
                map_entry.asm_directives = extract_entry_asm_directives(instruction.asm_directives)
                self.memory_map.append(map_entry)
                comments[:] = []
                instruction.ignoremrcua = self.mode.ignoremrcua
            elif ctl in 'dr':
                # This is a data definition entry or a remote entry
                map_entry = None

            if map_entry:
                address_comments.append([instruction, address_comment])
                map_entry.add_instruction(instruction)
                if comments:
                    instruction.mid_block_comment = join_comments(comments, True)
                    comments[:] = []
                    instruction.ignoremrcua = 0 in ignores
                    instruction.ignoreua = any(ignores)
                elif ignores:
                    instruction.ignoreua = True

            ignores[:] = []

        if comments and map_entry:
            map_entry.end_comment = join_comments(comments, True)
            map_entry.ignoreua[END] = len(ignores) > 0

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

        parse_address_comments(address_comments)

    def _parse_asm_directive(self, directive, ignores, line_no):
        if parse_asm_block_directive(directive, self.stack):
            self.mode.include = True
            for _p, i in self.stack:
                if i != '-':
                    self.mode.include = False
                    break
            return

        if self.mode.include:
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
        self.include = True
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
        self.inst_ctl = get_instruction_ctl(operation).lower()
        self.bases = ''
        self.size = None
        self.length = None
        if self.inst_ctl == 'b':
            self.size, self.length = get_defb_length(operation, preserve_base)
        elif self.inst_ctl == 't':
            self.size, self.length = get_defb_length(operation, preserve_base)
        elif self.inst_ctl == 'w':
            self.size, self.length = get_defw_length(operation, preserve_base)
        elif self.inst_ctl == 's':
            self.size, self.length = get_defs_length(operation, preserve_base)
        else:
            self.bases = get_operand_bases(operation, preserve_base)

    def set_comment(self, rowspan, text):
        self.comment = Comment(rowspan, text)

class Entry:
    def __init__(self, ctl, description, details, registers, ignoreua):
        self.ctl = ctl
        self.description = description
        self.details = details
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
