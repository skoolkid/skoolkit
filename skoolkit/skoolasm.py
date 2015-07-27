# -*- coding: utf-8 -*-

# Copyright 2008-2015 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import skoolmacro, SkoolKitError, SkoolParsingError, warn, write_text, wrap, get_chr
from skoolkit.skoolmacro import MacroParsingError, UnsupportedMacroError
from skoolkit.skoolparser import TableParser, ListParser, TABLE_MARKER, TABLE_END_MARKER, LIST_MARKER, LIST_END_MARKER

UDGTABLE_MARKER = '#UDGTABLE'

DEF_INSTRUCTION_WIDTH = 23

class AsmWriter:
    def __init__(self, parser, properties, lower):
        self.parser = parser
        self.show_warnings = self._get_int_property(properties, 'warnings', 1)

        # Build a label dictionary
        self.labels = {}
        for entry in self.parser.memory_map:
            for instruction in entry.instructions:
                label = instruction.asm_label
                if label:
                    self.labels[instruction.address] = label

        # Determine the base and end addresses
        self.base_address = 16384
        self.end_address = 65535
        if self.labels:
            self.base_address = min([address for address in self.labels.keys()])
        elif self.parser.memory_map:
            self.base_address = self.parser.memory_map[0].instructions[0].address
        if self.parser.memory_map:
            self.end_address = self.parser.memory_map[-1].instructions[-1].address

        self.bullet = properties.get('bullet', '*')
        self.lower = lower

        # Field widths (line = indent + instruction + ' ; ' + comment)
        if self._get_int_property(properties, 'tab', 0):
            self.indent_width = 8
            self.indent = '\t'
        else:
            self.indent_width = self._get_int_property(properties, 'indent', 2)
            self.indent = ' ' * self.indent_width
        self.instr_width = self._get_int_property(properties, 'instruction-width', DEF_INSTRUCTION_WIDTH)
        self.min_comment_width = self._get_int_property(properties, 'comment-width-min', 10)
        self.line_width = self._get_int_property(properties, 'line-width', 79)
        self.desc_width = self.line_width - 2

        # Line terminator
        if self._get_int_property(properties, 'crlf', 0):
            self.end = '\r\n'
        else:
            self.end = '\n'

        # Label suffix
        if self._get_int_property(properties, 'label-colons', 1):
            self.label_suffix = ':'
        else:
            self.label_suffix = ''

        min_col_width = self._get_int_property(properties, 'wrap-column-width-min', 10)
        self.table_writer = TableWriter(self.desc_width, min_col_width)

        self.handle_unsupported_macros = self._get_int_property(properties, 'handle-unsupported-macros', 0)

        self.snapshot = self.parser.snapshot
        self._snapshots = [(self.snapshot, '')]

        self.list_parser = ListParser()

        self.macros = skoolmacro.get_macros(self)

    def _get_int_property(self, properties, name, default):
        try:
            return int(properties[name])
        except (KeyError, ValueError):
            return default

    def warn(self, s):
        if self.show_warnings:
            warn(s)

    def write(self):
        self.print_header(self.parser.header)
        for entry in self.parser.memory_map:
            first_instruction = entry.instructions[0]
            org = first_instruction.org
            if org:
                if self.lower:
                    org_dir = 'org'
                else:
                    org_dir = 'ORG'
                org_addr_str = self.parser.convert_address_operand(org)
                self.write_line('{0}{1} {2}'.format(self.indent, org_dir, org_addr_str))
                self.write_line('')
            self.entry = entry
            self.print_entry()
            self.write_line('')

    def print_header(self, header):
        if header:
            for line in header:
                self.write_line(('; ' + line).rstrip())
            self.write_line('')

    def print_entry(self):
        self.print_comment_lines([self.entry.description], ignoreua=self.entry.ignoreua['t'])
        if self.entry.details:
            self.print_comment_lines(self.entry.details, ignoreua=self.entry.ignoreua['d'], started=True)
        if self.entry.registers:
            self.print_registers()
        self.print_instructions()
        if self.entry.end_comment:
            self.print_comment_lines(self.entry.end_comment, ignoreua=self.entry.ignoreua['e'])

    def write_line(self, s):
        write_text('{0}{1}'.format(s, self.end))

    def pop_snapshot(self):
        """Discard the current memory snapshot and replace it with the one that
        was most recently saved (by
        :meth:`~skoolkit.skoolasm.AsmWriter.push_snapshot`)."""
        if len(self._snapshots) < 2:
            raise SkoolKitError("Cannot pop snapshot when snapshot stack is empty")
        self.snapshot = self._snapshots.pop()[0]

    def push_snapshot(self, name=''):
        """Save the current memory snapshot for later retrieval (by
        :meth:`~skoolkit.skoolasm.AsmWriter.pop_snapshot`), and put a copy in
        its place.

        :param name: An optional name for the snapshot.
        """
        self._snapshots.append((self.snapshot[:], name))

    def expand_bug(self, text, index):
        end, item, link_text = skoolmacro.parse_bug(text, index)
        return end, link_text or 'bug'

    def expand_call(self, text, index):
        return skoolmacro.parse_call(text, index, self)

    def expand_chr(self, text, index):
        end, num = skoolmacro.parse_chr(text, index)
        return end, get_chr(num)

    def expand_d(self, text, index):
        return skoolmacro.parse_d(text, index, self.parser)

    def expand_erefs(self, text, index):
        return skoolmacro.parse_erefs(text, index, self.parser)

    def expand_fact(self, text, index):
        end, item, link_text = skoolmacro.parse_fact(text, index)
        return end, link_text or 'fact'

    def expand_font(self, text, index):
        # #FONT[:(text)]addr[,chars,attr,scale][{x,y,width,height}][(fname)]
        if self.handle_unsupported_macros:
            if index < len(text) and text[index] == ':':
                index, message = skoolmacro.get_text_param(text, index + 1)
            end, params, p_text = skoolmacro.parse_params(text, index, chars='=,{}')
            return end, ''
        raise UnsupportedMacroError()

    def expand_html(self, text, index):
        end, message = skoolmacro.parse_html(text, index)
        return end, ''

    def expand_link(self, text, index):
        end, page_id, anchor, link_text = skoolmacro.parse_link(text, index)
        if not link_text:
            raise MacroParsingError("Blank link text: #LINK{}".format(text[index:end]))
        return end, link_text

    def expand_poke(self, text, index):
        end, item, link_text = skoolmacro.parse_poke(text, index)
        return end, link_text or 'poke'

    def expand_pokes(self, text, index):
        return skoolmacro.parse_pokes(text, index, self.snapshot)

    def expand_pops(self, text, index):
        return skoolmacro.parse_pops(text, index, self)

    def expand_pushs(self, text, index):
        return skoolmacro.parse_pushs(text, index, self)

    def expand_r(self, text, index):
        end, addr_str, address, code_id, anchor, link_text = skoolmacro.parse_r(text, index)
        if link_text:
            return end, link_text
        if code_id:
            return end, self.parser.get_instruction_addr_str(address, code_id)
        label = self.labels.get(address)
        if label is None:
            if self.base_address <= address <= self.end_address:
                self.warn('Could not convert address {} to label'.format(addr_str))
            label = self.parser.get_instruction_addr_str(address)
            if label is None:
                if addr_str.startswith('$'):
                    label = addr_str[1:]
                else:
                    label = addr_str
        return end, label

    def expand_refs(self, text, index):
        return skoolmacro.parse_refs(text, index, self.parser)

    def expand_reg(self, text, index):
        return skoolmacro.parse_reg(text, index, self.lower)

    def expand_scr(self, text, index):
        # #SCR[scale,x,y,w,h,df,af][{x,y,width,height}][(fname)]
        if self.handle_unsupported_macros:
            end, params, p_text = skoolmacro.parse_params(text, index, chars='=,{}')
            return end, ''
        raise UnsupportedMacroError()

    def expand_space(self, text, index):
        end, num_sp = skoolmacro.parse_space(text, index)
        return end, ' ' * num_sp

    def expand_udg(self, text, index):
        # #UDGaddr[,attr,scale,step,inc,flip,rotate,mask][:addr[,step]][{x,y,width,height}][(fname)]
        if self.handle_unsupported_macros:
            end, params, p_text = skoolmacro.parse_params(text, index, chars='=,:{}')
            return end, ''
        raise UnsupportedMacroError()

    def expand_udgarray(self, text, index):
        # #UDGARRAYwidth[,attr,scale,step,inc,flip,rotate,mask];addr[,attr,step,inc][:addr[,step]];...[{x,y,width,height}](fname)
        # #UDGARRAY*frame1[,delay];frame2[,delay];...(fname)
        if self.handle_unsupported_macros:
            if index < len(text) and text[index] == '*':
                end, params, p_text = skoolmacro.parse_params(text, index, except_chars=' (')
            else:
                end, params, p_text = skoolmacro.parse_params(text, index, chars='=,:;-{}')
            return end, ''
        raise UnsupportedMacroError()

    def expand(self, text):
        """Return `text` with skool macros expanded."""
        return skoolmacro.expand_macros(self.macros, text).strip()

    def find_markers(self, block_indexes, text, marker, end_marker):
        index = 0
        while text.find(marker, index) >= 0:
            block_index = text.index(marker, index)
            try:
                block_end_index = text.index(end_marker, block_index) + len(end_marker)
            except ValueError:
                raise SkoolParsingError("Missing end marker: {}...".format(text[block_index:block_index + len(marker) + 15]))
            block_indexes.append(block_index)
            block_indexes.append(block_end_index)
            index = block_end_index

    def extract_blocks(self, text):
        # Find table and list markers
        block_indexes = []
        self.find_markers(block_indexes, text, TABLE_MARKER, TABLE_END_MARKER)
        self.find_markers(block_indexes, text, UDGTABLE_MARKER, TABLE_END_MARKER)
        self.find_markers(block_indexes, text, LIST_MARKER, LIST_END_MARKER)

        # Extract blocks
        blocks = []
        all_indexes = [0]
        all_indexes += block_indexes
        all_indexes.sort()
        all_indexes.append(len(text))
        for i in range(len(all_indexes) - 1):
            start = all_indexes[i]
            end = all_indexes[i + 1]
            block = text[start:end].strip()
            if block and not block.startswith(UDGTABLE_MARKER):
                blocks.append(block)

        return blocks

    def format(self, text, width):
        lines = []
        for block in self.extract_blocks(text):
            if block.startswith(TABLE_MARKER):
                table_lines = self.table_writer.format_table(self.expand(block[len(TABLE_MARKER):]))
                if table_lines:
                    table_width = max([len(line) for line in table_lines])
                    if table_width > width:
                        self.warn('Table in entry at {0} is {1} characters wide'.format(self.entry.address, table_width))
                    lines.extend(table_lines)
            elif block.startswith(LIST_MARKER):
                list_obj = self.list_parser.parse_list(self.expand(block[len(LIST_MARKER):]))
                for item in list_obj.items:
                    item_lines = []
                    bullet = self.bullet
                    indent = ' ' * len(bullet)
                    for line in wrap(item, width - len(bullet) - 1):
                        item_lines.append('{0} {1}'.format(bullet, line))
                        bullet = indent
                    lines.extend(item_lines)
            else:
                lines.extend(wrap(self.expand(block), width))
        return lines

    def print_comment_lines(self, paragraphs, instruction=None, ignoreua=False, started=False):
        for paragraph in paragraphs:
            lines = self.format(paragraph, self.desc_width)
            if started and lines:
                self.write_line(';')
            if lines:
                started = True
            for line in lines:
                if not ignoreua:
                    uaddress = self.find_unconverted_address(line)
                    if uaddress:
                        if instruction:
                            if not instruction.ignoremrcua:
                                self.warn('Comment above {0} contains address ({1}) not converted to a label:\n; {2}'.format(instruction.address, uaddress, line))
                        else:
                            self.warn('Comment contains address ({0}) not converted to a label:\n; {1}'.format(uaddress, line))
                self.write_line('; {0}'.format(line).rstrip())

    def print_registers(self):
        self.write_line(';')
        prefix_len = max([len(reg.prefix) for reg in self.entry.registers])
        if prefix_len:
            prefix_len += 1
        indent = ''.ljust(prefix_len)
        for reg in self.entry.registers:
            if reg.prefix:
                prefix = '{}:'.format(reg.prefix).rjust(prefix_len)
            else:
                prefix = indent
            reg_label = prefix + reg.name
            reg_desc = self.expand(reg.contents)
            if not self.entry.ignoreua['r']:
                uaddress = self.find_unconverted_address(reg_desc)
                if uaddress:
                    line = '; {} {}'.format(reg_label, reg_desc)
                    self.warn('Register description contains address ({}) not converted to a label:\n{}'.format(uaddress, line))
            if reg_desc:
                desc_indent = len(reg_label) + 1
                desc_lines = wrap(reg_desc, self.desc_width - desc_indent)
                self.write_line('; {} {}'.format(reg_label, desc_lines[0]))
                desc_prefix = ''.ljust(desc_indent)
                for line in desc_lines[1:]:
                    self.write_line('; {}{}'.format(desc_prefix, line))
            else:
                self.write_line('; {}'.format(reg_label))

    def print_instruction_prefix(self, instruction, index):
        if instruction.mid_block_comment:
            if index == 0:
                self.write_line(';')
            self.print_comment_lines(instruction.mid_block_comment, instruction)
        if instruction.asm_label:
            self.write_line("{0}{1}".format(instruction.asm_label, self.label_suffix))

    def find_unconverted_address(self, text):
        search = re.search('[1-9][0-9][0-9][0-9][0-9]', text)
        if search:
            start, end = search.span()
            if (start == 0 or text[start - 1] == ' ') and (end == len(text) or not text[end].isalnum()):
                uaddress = int(search.group())
                if self.base_address <= uaddress <= self.end_address:
                    return uaddress

    def print_instructions(self):
        i = 0
        rowspan = 0
        lines = []
        instructions = self.entry.instructions

        while i < len(instructions) or lines:
            if i < len(instructions):
                instruction = instructions[i]
            else:
                instruction = None

            # Deal with remaining comment lines or rowspan on the previous
            # instruction
            if lines or rowspan > 0:
                if rowspan > 0:
                    self.print_instruction_prefix(instruction, i)
                    operation = instruction.operation
                    rowspan -= 1
                    i += 1
                else:
                    operation = ''

                if lines:
                    line_comment = lines.pop(0)
                    oline = '{0}{1} ; {2}'.format(self.indent, operation.ljust(instr_width), line_comment)
                else:
                    line_comment = ''
                    oline = '{0}{1}'.format(self.indent, operation)
                self.write_line(oline)
                if not ignoreua:
                    uaddress = self.find_unconverted_address(line_comment)
                    if uaddress:
                        self.warn('Comment at {0} contains address ({1}) not converted to a label:\n{2}'.format(iaddress, uaddress, oline))
                if len(oline) > self.line_width:
                    self.warn('Line is {0} characters long:\n{1}'.format(len(oline), oline))
                continue # pragma: no cover

            ignoreua = instruction.ignoreua
            iaddress = instruction.address

            rowspan = instruction.comment.rowspan
            instr_width = max(len(instruction.operation), self.instr_width)
            comment_width = self.line_width - 3 - instr_width - self.indent_width
            lines = wrap(self.expand(instruction.comment.text), max((comment_width, self.min_comment_width)))

class TableWriter:
    def __init__(self, max_width, min_col_width):
        self.max_width = max_width
        self.min_col_width = min_col_width
        self.table = None
        self.table_parser = TableParser()
        self.cell_matrix = None

    def format_table(self, text):
        self.table = self.table_parser.parse_table(text)
        self.table.cell_padding = 3
        self.table.prepare_cells()
        self.table.reduce_width(self.max_width, self.min_col_width)
        self.cell_matrix = self._build_cell_matrix()
        return self._create_table_text()

    def _build_cell_matrix(self):
        cell_matrix = []
        for row in self.table.rows:
            cell_matrix.append([None] * self.table.num_cols)
        for cell in self.table.cells:
            for x in range(cell.col_index, cell.col_index + cell.colspan):
                for y in range(cell.row_index, cell.row_index + cell.rowspan):
                    cell_matrix[y][x] = cell
        return cell_matrix

    def _get_cell(self, col_index, row_index):
        if 0 <= row_index < len(self.cell_matrix) and 0 <= col_index < self.table.num_cols:
            return self.cell_matrix[row_index][col_index]

    def _render_row(self, lines, row_index, first_line=True):
        rendered = False
        line = ''
        col_index = 0
        cell_left_transparent = True
        cell = self._get_cell(col_index, row_index)
        while cell:
            if cell.transparent and cell_left_transparent:
                border = ' '
            else:
                border = '|'
            text = ''
            if cell.contents and (first_line or row_index == cell.row_index + cell.rowspan - 1):
                text = cell.contents.pop(0)
                rendered = True
            line += "{} {} ".format(border, text.ljust(self.table.get_cell_width(col_index, cell.colspan)))
            col_index += cell.colspan
            cell_left_transparent = cell.transparent
            cell = self._get_cell(col_index, row_index)
        if rendered:
            if (cell and not cell.transparent) or (cell is None and not cell_left_transparent):
                line += '|'
            lines.append(line.rstrip())
        return rendered

    def _create_table_text(self):
        lines = []
        max_row_index = len(self.table.rows)
        if max_row_index == 0:
            return lines
        separator_row_indexes = set((0, max_row_index))
        separator_row_indexes.update([i + 1 for i in self.table.get_header_rows()])
        for row_index in range(max_row_index):
            if row_index in separator_row_indexes:
                lines.append(self._create_row_separator(row_index))
            self._render_row(lines, row_index)
            while self._render_row(lines, row_index, False):
                pass
        lines.append(self._create_row_separator(max_row_index))
        return lines

    def _create_row_separator(self, row_index):
        # Return a separator between rows `row_index - 1` and `row_index`
        line = ''
        col_index = 0
        cell_left_contents = True

        while col_index < self.table.num_cols:
            cell_above = self._get_cell(col_index, row_index - 1)
            if row_index < len(self.table.rows):
                cell = self._get_cell(col_index, row_index)
            else:
                cell = cell_above
            if cell is None:
                break
            cell_above_transparent = cell_above is None or cell_above.transparent
            cell_above_left = self._get_cell(col_index - 1, row_index - 1)
            cell_above_left_transparent = cell_above_left is None or cell_above_left.transparent
            cell_left = self._get_cell(col_index - 1, row_index)
            cell_left_transparent = cell_left is None or cell_left.transparent
            cell_contents = bool(cell_above and cell_above.contents)
            if cell.transparent and cell_above_transparent and cell_above_left_transparent and cell_left_transparent:
                line += ' '
            elif cell_contents and cell_left_contents:
                line += '|'
            else:
                line += '+'
            if cell_contents:
                text = cell.contents.pop(0)
                line += ' {} '.format(text.ljust(self.table.get_cell_width(col_index, cell_above.colspan)))
            else:
                if cell.transparent and cell_above_transparent:
                    spacer = ' '
                else:
                    spacer = '-'
                line += spacer * (2 + self.table.get_cell_width(col_index, cell.colspan))
            cell_left_contents = cell_contents
            col_index += cell.colspan

        if cell_contents:
            return line + '|'
        if line.endswith(' '):
            return line.rstrip()
        return line + '+'
