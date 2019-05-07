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

from skoolkit import (SkoolKitError, warn, write_line, wrap, parse_int,
                      get_address_format, format_template)
from skoolkit.disassembler import Disassembler
from skoolkit.skoolasm import UDGTABLE_MARKER
from skoolkit.skoolctl import (AD_IGNOREUA, AD_LABEL, TITLE, DESCRIPTION,
                               REGISTERS, MID_BLOCK, INSTRUCTION, END)
from skoolkit.skoolmacro import ClosingBracketError, parse_brackets
from skoolkit.skoolparser import (get_address, TABLE_MARKER, TABLE_END_MARKER,
                                  LIST_MARKER, LIST_END_MARKER)

MIN_COMMENT_WIDTH = 10

class Entry:
    def __init__(self, header, title, description, ctl, blocks, registers,
                 end_comment, footer, asm_directives, ignoreua_directives):
        self.header = header
        self.title = title
        self.has_title = any(title)
        self.ctl = ctl
        self.blocks = blocks
        self.instructions = []
        for block in blocks:
            for instruction in block.instructions:
                instruction.entry = self
                self.instructions.append(instruction)
        first_instruction = self.instructions[0]
        first_instruction.ctl = ctl
        self.registers = registers
        self.end_comment = end_comment
        self.footer = footer
        self.asm_directives = asm_directives
        self.ignoreua_directives = ignoreua_directives
        self.address = first_instruction.address
        self.description = description
        self.next = None
        self.bad_blocks = []
        for block in self.blocks:
            last_instruction = block.instructions[-1]
            if last_instruction.address + last_instruction.size() > block.end:
                self.bad_blocks.append(block)

    def width(self):
        return max([len(i.operation) for i in self.instructions])

    def has_ignoreua_directive(self, comment_type):
        return comment_type in self.ignoreua_directives

class Disassembly:
    def __init__(self, snapshot, ctl_parser, config=None, final=False, defb_size=8, defb_mod=1,
                 zfill=False, defm_width=66, asm_hex=False, asm_lower=False):
        ctl_parser.apply_asm_data_directives(snapshot)
        self.disassembler = Disassembler(snapshot, defb_size, defb_mod, zfill, defm_width, asm_hex, asm_lower)
        self.ctl_parser = ctl_parser
        if asm_hex:
            if asm_lower:
                self.address_fmt = '{0:04x}'
            else:
                self.address_fmt = '{0:04X}'
        else:
            self.address_fmt = '{0}'
        self.entry_map = {}
        self.config = config or {}
        self.build(final)

    def build(self, final=False):
        self.instructions = {}
        self.entries = []
        self._create_entries()
        if self.entries:
            self.org = self.entries[0].address
        else:
            self.org = None
        if final:
            self._calculate_references()

    def _create_entries(self):
        for block in self.ctl_parser.get_blocks():
            if block.start in self.entry_map:
                entry = self.entry_map[block.start]
                self.entries.append(entry)
                for instruction in entry.instructions:
                    self.instructions[instruction.address] = instruction
                continue
            title = block.title
            if not any(title):
                ctl = block.ctl
                if ctl != 'i' or block.description or block.registers or block.blocks[0].header:
                    name = 'Title-' + ctl
                    title = [format_template(self.config.get(name, ''), name, address=self._address_str(block.start))]
            for sub_block in block.blocks:
                address = sub_block.start
                if sub_block.ctl in 'cBT':
                    base = sub_block.sublengths[0][1]
                    instructions = self.disassembler.disassemble(sub_block.start, sub_block.end, base)
                elif sub_block.ctl in 'bgstuw':
                    sublengths = sub_block.sublengths
                    if sublengths[0][0]:
                        if sub_block.ctl == 's':
                            length = sublengths[0][0]
                        else:
                            length = sum([s[0] for s in sublengths])
                    else:
                        length = sub_block.end - sub_block.start
                    instructions = []
                    while address < sub_block.end:
                        end = min(address + length, sub_block.end)
                        if sub_block.ctl == 't':
                            instructions += self.disassembler.defm_range(address, end, sublengths)
                        elif sub_block.ctl == 'w':
                            instructions += self.disassembler.defw_range(address, end, sublengths)
                        elif sub_block.ctl == 's':
                            instructions += self.disassembler.defs(address, end, sublengths)
                        else:
                            instructions += self.disassembler.defb_range(address, end, sublengths)
                        address += length
                else:
                    instructions = self.disassembler.ignore(sub_block.start, sub_block.end)
                self._add_instructions(sub_block, instructions)

            sub_blocks = []
            i = 0
            while i < len(block.blocks):
                sub_block = block.blocks[i]
                i += 1
                sub_blocks.append(sub_block)
                if sub_block.multiline_comment is not None:
                    end, sub_block.comment = sub_block.multiline_comment
                    while i < len(block.blocks) and block.blocks[i].start < end:
                        next_sub_block = block.blocks[i]
                        sub_block.instructions += next_sub_block.instructions
                        sub_block.end = next_sub_block.end
                        i += 1

            entry = Entry(block.header, title, block.description, block.ctl, sub_blocks,
                          block.registers, block.end_comment, block.footer, block.asm_directives,
                          block.ignoreua_directives)
            self.entry_map[entry.address] = entry
            self.entries.append(entry)
        for i, entry in enumerate(self.entries[1:]):
            self.entries[i].next = entry

    def remove_entry(self, address):
        if address in self.entry_map:
            del self.entry_map[address]

    def _add_instructions(self, sub_block, instructions):
        sub_block.instructions = instructions
        for instruction in instructions:
            self.instructions[instruction.address] = instruction
            instruction.asm_directives = sub_block.asm_directives.get(instruction.address, ())
            instruction.label = None
            for asm_dir in instruction.asm_directives:
                if asm_dir.startswith(AD_LABEL + '='):
                    instruction.label = asm_dir[6:]
                    if instruction.label.startswith('*'):
                        instruction.ctl = '*'
                    break

    def _calculate_references(self):
        for entry in self.entries:
            for instruction in entry.instructions:
                instruction.referrers = []
        for entry in self.entries:
            for instruction in entry.instructions:
                operation = instruction.operation
                if operation.upper().startswith(('DJ', 'JR', 'JP', 'CA', 'RS')):
                    addr_str = get_address(operation)
                    if addr_str:
                        callee = self.instructions.get(parse_int(addr_str))
                        if callee and (entry.ctl != 'u' or callee.entry == entry) and callee.label != '':
                            callee.add_referrer(entry)

    def _address_str(self, address):
        return self.address_fmt.format(address)

class SkoolWriter:
    def __init__(self, snapshot, ctl_parser, options, config):
        self.comment_width = max(options.line_width - 2, MIN_COMMENT_WIDTH)
        self.asm_hex = options.base == 16
        self.disassembly = Disassembly(snapshot, ctl_parser, config, True, config['DefbSize'], config['DefbMod'],
                                       config['DefbZfill'], config['DefmSize'], self.asm_hex, options.case == 1)
        self.address_fmt = get_address_format(self.asm_hex, options.case == 1)
        self.config = config

    def address_str(self, address, pad=True):
        if self.asm_hex or pad:
            return self.address_fmt.format(address)
        return str(address)

    def _trim_lines(self, lines):
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
        return lines

    def write_skool(self, write_refs, text):
        for entry_index, entry in enumerate(self.disassembly.entries):
            if entry_index:
                write_line('')
            self._write_entry(entry, write_refs, text)

    def _write_entry(self, entry, write_refs, show_text):
        if entry.header:
            for line in entry.header:
                write_line(line)
            write_line('')

        self.write_asm_directives(*entry.asm_directives)
        if entry.has_ignoreua_directive(TITLE):
            self.write_asm_directives(AD_IGNOREUA)

        if entry.ctl == 'i' and entry.blocks[-1].end >= 65536 and not entry.has_title and all([b.ctl == 'i' for b in entry.blocks]):
            return

        for block in entry.bad_blocks:
            addr1 = self.address_str(block.instructions[-1].address, False)
            addr2 = self.address_str(block.end, False)
            warn('Instruction at {} overlaps the following instruction at {}'.format(addr1, addr2))

        if entry.has_title:
            self.write_comment(entry.title)
            wrote_desc = self._write_entry_description(entry, write_refs)
            wrote_desc = self._write_registers(entry, wrote_desc)
        else:
            wrote_desc = False

        self._write_body(entry, wrote_desc, write_refs, show_text and entry.ctl != 't')

        if entry.has_ignoreua_directive(END):
            self.write_asm_directives(AD_IGNOREUA)
        self.write_paragraphs(entry.end_comment)

        if entry.footer:
            write_line('')
            for line in entry.footer:
                write_line(line)

    def _write_entry_description(self, entry, write_refs):
        wrote_desc = False
        ignoreua_d = entry.has_ignoreua_directive(DESCRIPTION)
        if write_refs:
            referrers = entry.instructions[0].referrers
            if referrers and (write_refs == 2 or not entry.description):
                self.write_comment('')
                if ignoreua_d:
                    self.write_asm_directives(AD_IGNOREUA)
                self.write_referrers(referrers, False)
                wrote_desc = True
        if entry.description:
            if wrote_desc:
                self._write_paragraph_separator()
            else:
                self.write_comment('')
                if ignoreua_d:
                    self.write_asm_directives(AD_IGNOREUA)
            self.write_paragraphs(entry.description)
            wrote_desc = True
        return wrote_desc

    def _write_registers(self, entry, wrote_desc):
        registers = []
        for spec in entry.registers:
            if len(spec) == 1:
                reg, desc = spec[0].partition(' ')[::2]
                if reg:
                    registers.append((reg, desc))
            elif self._trim_lines(spec):
                registers.append(('', spec))

        entry.registers = registers
        if registers:
            max_indent = max(r[0].find(':') for r in registers)
            if not wrote_desc:
                self._write_empty_paragraph()
                wrote_desc = True
            self.write_comment('')
            if entry.has_ignoreua_directive(REGISTERS):
                self.write_asm_directives(AD_IGNOREUA)
            for reg, desc in registers:
                if reg:
                    reg = reg.rjust(max_indent + len(reg) - reg.find(':'))
                    desc_indent = len(reg) + 1
                    desc_lines = wrap(desc, max(self.comment_width - desc_indent, MIN_COMMENT_WIDTH)) or ['']
                    desc_prefix = '.'.ljust(desc_indent)
                    write_line('; {} {}'.format(reg, desc_lines[0]).rstrip())
                    for line in desc_lines[1:]:
                        write_line('; {}{}'.format(desc_prefix, line).rstrip())
                else:
                    for line in desc:
                        write_line('; {}'.format(line).rstrip())

        return wrote_desc

    def _set_instruction_comments(self, block, width, closing, show_text):
        for instruction in block.instructions:
            instruction.comment = [None]
            if block.comment:
                instruction.comment[0] = block.comment.pop(0)[1]
                while block.comment and block.comment[0][0]:
                    instruction.comment.append(block.comment.pop(0)[1])
            elif show_text:
                instruction.comment[0] = self.to_ascii(instruction.bytes)
            elif closing:
                instruction.comment[0] = ''
        final_comment = block.instructions[-1].comment
        final_comment.extend(t[1] for t in block.comment)
        if closing:
            if len(final_comment[-1]) + len(closing) <= width:
                final_comment[-1] = (final_comment[-1] + closing).lstrip()
            else:
                final_comment.append(closing.lstrip())

    def _format_instruction_comments(self, block, width, show_text):
        comment = ''.join(t[1] for t in block.comment)
        multi_line = len(block.instructions) > 1 and (comment or len(block.comment) > 1)
        opening = closing = ''
        if multi_line and len(block.comment) == 1 and not comment.replace('.', ''):
            comment = comment[1:]
            block.comment[0] = (0, comment)
        if multi_line or comment.startswith('{'):
            balance = comment.count('{') - comment.count('}')
            if multi_line and balance < 0:
                opening = '{' * (1 - balance)
            else:
                opening = '{'
            if comment.startswith('{'):
                opening = opening + ' '
            closing = '}' * max(1 + balance, 1)
            if comment.endswith('}'):
                closing = ' ' + closing
        if len(block.comment) == 1:
            block.comment[:] = [(0, t) for t in wrap(opening + block.comment[0][1], width)]
        elif block.comment:
            if not block.comment[0][1]:
                block.comment.pop(0)
            block.comment[0] = (0, opening + block.comment[0][1])
        self._set_instruction_comments(block, width, closing, show_text)

    def _write_body(self, entry, wrote_desc, write_refs, show_text):
        op_width = max((self.config['InstructionWidth'], entry.width()))
        comment_width = max(self.comment_width - op_width - 8, self.config['CommentWidthMin'])
        for index, block in enumerate(entry.blocks):
            ignoreua_m = block.has_ignoreua_directive(block.start, MID_BLOCK)
            begun_header = False
            if index > 0 and entry.ctl == 'c' and write_refs:
                referrers = block.instructions[0].referrers
                if referrers and (write_refs == 2 or not block.header):
                    if ignoreua_m:
                        self.write_asm_directives(AD_IGNOREUA)
                    self.write_referrers(referrers)
                    begun_header = True
            if block.header:
                if index == 0:
                    if not wrote_desc:
                        self._write_empty_paragraph()
                    if not entry.registers:
                        self._write_empty_paragraph()
                    self.write_comment('')
                if begun_header:
                    self._write_paragraph_separator()
                elif ignoreua_m:
                    self.write_asm_directives(AD_IGNOREUA)
                self.write_paragraphs(block.header)
            self._format_instruction_comments(block, comment_width, show_text)
            self._write_instructions(entry, block, op_width, write_refs)

    def _write_instructions(self, entry, block, op_width, write_refs):
        for index, instruction in enumerate(block.instructions):
            ctl = instruction.ctl or ' '
            address = instruction.address
            operation = instruction.operation
            comment = instruction.comment.pop(0)
            if index > 0 and entry.ctl == 'c' and ctl == '*' and write_refs:
                self.write_referrers(instruction.referrers)
            self.write_asm_directives(*instruction.asm_directives)
            if block.has_ignoreua_directive(instruction.address, INSTRUCTION):
                self.write_asm_directives(AD_IGNOREUA)
            if entry.ctl in self.config['Semicolons'] or comment is not None:
                write_line(('{}{} {:{}} ; {}'.format(ctl, self.address_str(address), operation, op_width, comment or '')).rstrip())
            else:
                write_line(('{}{} {}'.format(ctl, self.address_str(address), operation)).rstrip())
            for comment in instruction.comment:
                write_line('       {:{}} ; {}'.format('', op_width, comment).rstrip())

    def write_comment(self, text, paragraphs=False):
        if isinstance(text, str):
            lines = [text]
        elif len(text) == 1:
            lines = self.wrap(text[0])
        else:
            lines = self._trim_lines(text[:])
        for line in lines:
            if line:
                write_line('; ' + line)
            elif paragraphs:
                self._write_paragraph_separator()
            else:
                write_line(';')

    def _write_empty_paragraph(self):
        self.write_comment('')
        self.write_comment('.')

    def _write_paragraph_separator(self):
        self.write_comment('.')

    def write_paragraphs(self, paragraphs):
        for i, paragraph in enumerate(p for p in paragraphs if any(p)):
            if i:
                self._write_paragraph_separator()
            self.write_comment(paragraph, True)

    def write_referrers(self, referrers, erefs=True):
        if referrers:
            if erefs:
                key = 'EntryPointRef'
            else:
                key = 'Ref'
            fields = {'ref': '#R' + self.address_str(referrers[-1].address, False)}
            if len(referrers) > 1:
                key += 's'
                fields['refs'] = ', '.join(['#R' + self.address_str(r.address, False) for r in referrers[:-1]])
            self.write_comment(format_template(self.config[key], key, **fields))

    def write_asm_directives(self, *directives):
        for directive in directives:
            write_line('@' + directive)

    def to_ascii(self, data):
        chars = ['[']
        for b in data:
            if 32 <= b < 127:
                chars.append(chr(b))
            else:
                chars.append('.')
        chars.append(']')
        return ''.join(chars)

    def wrap(self, text):
        lines = []
        for line, wrap_flag in self.parse_blocks(text):
            if wrap_flag == 0:
                lines.append(line)
            elif wrap_flag == 1:
                lines.extend(wrap(line, self.comment_width))
            else:
                block = wrap(line, self.comment_width)
                lines.append(block[0])
                if len(block) > 1:
                    if block[0].endswith(' |'):
                        indent = 2
                    else:
                        indent = block[0].rfind(' | ') + 3
                    while indent < len(block[0]) and block[0][indent] == ' ':
                        indent += 1
                    pad = ' ' * indent
                    lines.extend(pad + line for line in wrap(' '.join(block[1:]), self.comment_width - indent))
        return lines

    def parse_block(self, text, begin):
        try:
            index = parse_brackets(text, begin)[0]
        except ClosingBracketError:
            raise SkoolKitError("No closing ')' on parameter list: {}...".format(text[begin:begin + 15]))
        try:
            index, flag = parse_brackets(text, index, '', '<', '>')
        except ClosingBracketError:
            raise SkoolKitError("No closing '>' on flags: {}...".format(text[index:index + 15]))
        wrap_flag = 1
        if flag == 'nowrap':
            wrap_flag = 0
        elif flag == 'wrapalign':
            wrap_flag = 2

        indexes = [(index, 1)]

        # Parse the table rows or list items
        while True:
            start = text.find('{ ', index)
            if start < 0:
                break
            try:
                end = text.index(' }', start)
            except ValueError:
                raise SkoolKitError("No closing ' }}' on row/item: {}...".format(text[start:start + 15]))
            index = end + 2
            indexes.append((index, wrap_flag))


        indexes.append((len(text), 1))
        return indexes

    def parse_blocks(self, text):
        markers = ((TABLE_MARKER, TABLE_END_MARKER), (UDGTABLE_MARKER, TABLE_END_MARKER), (LIST_MARKER, LIST_END_MARKER))
        indexes = []

        # Find table/list markers and row/item definitions
        index = 0
        while True:
            starts = [(marker[0], marker[1], text.find(marker[0], index)) for marker in markers]
            for marker, end_marker, start in starts:
                if start >= 0:
                    if start > 0:
                        indexes.append((start - 1, 1))
                    try:
                        end = text.index(end_marker, start) + len(end_marker)
                    except ValueError:
                        raise SkoolKitError("No end marker found: {}...".format(text[start:start + len(marker) + 15]))
                    indexes.extend(self.parse_block(text[:end], start + len(marker)))
                    break
            else:
                break
            index = indexes[-1][0] + 1

        if not indexes or indexes[-1][0] != len(text):
            indexes.append((len(text), 1))
        indexes.sort(key=lambda e: e[0])
        lines = []
        start = 0
        for end, wrap_flag in indexes:
            lines.append((text[start:end].strip(), wrap_flag))
            start = end
        return lines
