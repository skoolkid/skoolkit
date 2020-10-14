# Copyright 2008-2020 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import (CASE_LOWER, skoolmacro, SkoolKitError, SkoolParsingError,
                      format_template, warn, write_text, wrap)
from skoolkit.skoolparser import (TableParser, ListParser, TABLE_MARKER, TABLE_END_MARKER,
                                  LIST_MARKER, LIST_END_MARKER)

BLOCK_SEP = '\x00'

UDGTABLE_MARKER = '#UDGTABLE'

TEMPLATES = {
    'comment': '; {text}',
    'equ': '{label} {equ} {value}',
    'instruction': '{indent}{operation:{width}} {sep} {text}',
    'label': '{label}{suffix}',
    'org': '{indent}{org} {address}',
    'register': '; {prefix:>{prefix_len}}{reg:{reg_len}} {text}'
}

class AsmWriter:
    def __init__(self, parser, properties, templates):
        self.parser = parser
        self.templates = TEMPLATES.copy()
        self.templates.update(templates)
        self.show_warnings = self._get_int_property(properties, 'warnings', 1)

        self.fields = parser.fields

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
            self.base_address = min(self.labels)
        elif self.parser.memory_map:
            self.base_address = self.parser.memory_map[0].instructions[0].address
        if self.parser.memory_map:
            self.end_address = self.parser.memory_map[-1].instructions[-1].address

        self.lower = self.case == CASE_LOWER

        # Field widths (line = indent + instruction + ' ; ' + comment)
        if self._get_int_property(properties, 'tab', 0):
            self.indent_width = 8
            self.indent = '\t'
        else:
            self.indent_width = self._get_int_property(properties, 'indent', 2)
            self.indent = ' ' * self.indent_width
        self.instr_width = self._get_int_property(properties, 'instruction-width', 23)
        self.min_comment_width = self._get_int_property(properties, 'comment-width-min', 10)
        self.line_width = self._get_int_property(properties, 'line-width', 79)
        self.desc_width = self._get_text_width('comment')

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
        self.table_writer = TableWriter(self, self.desc_width, min_col_width, properties)

        self.handle_unsupported_macros = self._get_int_property(properties, 'handle-unsupported-macros', 0)

        self.snapshot = self.parser.snapshot
        self._snapshots = [(self.snapshot, '')]

        self.list_parser = ListParser(properties.get('bullet', '*'))

        self.to_chr = chr
        self.get_reg = lambda r: r
        self.space = ' '
        self.pc = 0
        self.macros = skoolmacro.get_macros(self)
        for e in self.parser.expands:
            self.expand(e)

        self.init()

    # API
    def init(self):
        """Perform post-initialisation operations. This method is called after
        `__init__()` has completed. By default the method does nothing, but
        subclasses may override it.
        """
        return

    # API
    @property
    def base(self):
        return self.parser.base

    # API
    @property
    def case(self):
        return self.parser.case

    def _get_int_property(self, properties, name, default):
        try:
            return int(properties[name])
        except (KeyError, ValueError):
            return default

    def _get_text_width(self, template_name, **subs):
        template = self.templates[template_name]
        text_f = '{text'
        if text_f in template:
            text_f = skoolmacro.parse_strings(template, template.index(text_f), 1)[1]
        return self.line_width - len(template.replace(text_f, 'text').format(text='', **subs))

    def warn(self, s):
        if self.show_warnings:
            warn(s)

    def format_warn(self, one, many, items, *args):
        if len(items) > 1:
            self.warn(many.format(', '.join(sorted(items)), *args))
        elif len(items) == 1:
            self.warn(one.format(items.pop(), *args))

    def format_template(self, name, fields):
        return format_template(self.templates.get(name, ''), name, **fields)

    def write(self):
        for index, entry in enumerate(self.parser.memory_map):
            self.pc = entry.address
            self.print_blocks(entry.headers)
            if index == 0:
                self.print_equs(self.parser.equs)
            if entry.instructions[0].org:
                subs = {
                    'indent': self.indent,
                    'org': 'ORG',
                    'address': self.parser.convert_address_operand(entry.instructions[0].org)
                }
                if self.lower:
                    subs['org'] = 'org'
                self.write_line(self.format_template('org', subs))
                self.write_line('')
            self.entry = entry
            self.print_entry()
            self.write_line('')
            self.print_blocks(entry.footers)

    def print_blocks(self, blocks):
        for block in blocks:
            if block:
                for line in block:
                    self.write_line(line)
                self.write_line('')

    def print_equs(self, equs):
        if equs:
            if self.lower:
                equ_dir = 'equ'
            else:
                equ_dir = 'EQU'
            for label, value in equs:
                subs = {
                    'label': label,
                    'equ': equ_dir,
                    'value': self.parser.convert_equ_value(value)
                }
                self.write_line(self.format_template('equ', subs))
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
        """Replace the current memory snapshot with the one most recently saved
        by :meth:`~skoolkit.skoolasm.AsmWriter.push_snapshot`."""
        if len(self._snapshots) < 2:
            raise SkoolKitError("Cannot pop snapshot when snapshot stack is empty")
        self.snapshot[:] = self._snapshots.pop()[0]

    def push_snapshot(self, name=''):
        """Save a copy of the current memory snapshot for later retrieval (by
        :meth:`~skoolkit.skoolasm.AsmWriter.pop_snapshot`).

        :param name: An optional name for the snapshot.
        """
        self._snapshots.append((self.snapshot[:], name))

    def expand_font(self, text, index):
        if self.handle_unsupported_macros:
            return skoolmacro.parse_font(text, index, self.fields)[0], ''
        raise skoolmacro.UnsupportedMacroError()

    def expand_html(self, text, index):
        end, message = skoolmacro.parse_html(text, index)
        return end, ''

    def expand_include(self, text, index):
        end, paragraphs, section = skoolmacro.parse_include(text, index, self.fields)
        return end, ''

    def expand_link(self, text, index):
        end, page_id, anchor, link_text = skoolmacro.parse_link(text, index)
        if not link_text:
            raise skoolmacro.MacroParsingError("Blank link text: #LINK{}".format(text[index:end]))
        return end, link_text

    def expand_list(self, text, index):
        return self._ignore_block(text, index, LIST_MARKER, LIST_END_MARKER)

    def expand_plot(self, text, index):
        if self.handle_unsupported_macros:
            return skoolmacro.parse_plot(text, index, self.fields)
        raise skoolmacro.UnsupportedMacroError()

    def expand_r(self, text, index):
        end, addr_str, address, code_id, anchor, link_text = skoolmacro.parse_r(self.fields, text, index)
        if link_text:
            return end, link_text
        if code_id:
            return end, self.parser.get_instruction_addr_str(address, addr_str, code_id)
        label = self.labels.get(address)
        if label is None:
            if self.base_address <= address <= self.end_address:
                self.warn('Could not convert address {} to label'.format(addr_str))
            label = self.parser.get_instruction_addr_str(address, addr_str)
        return end, label

    def expand_scr(self, text, index):
        if self.handle_unsupported_macros:
            return skoolmacro.parse_scr(text, index, self.fields)[0], ''
        raise skoolmacro.UnsupportedMacroError()

    def expand_table(self, text, index):
        return self._ignore_block(text, index, TABLE_MARKER, TABLE_END_MARKER)

    def expand_udg(self, text, index):
        if self.handle_unsupported_macros:
            return skoolmacro.parse_udg(text, index, self.fields)[0], ''
        raise skoolmacro.UnsupportedMacroError()

    def expand_udgarray(self, text, index):
        if self.handle_unsupported_macros:
            if index < len(text) and text[index] == '*':
                end = skoolmacro.parse_udgarray_with_frames(text, index, self.fields)[0]
            else:
                end = skoolmacro.parse_udgarray(text, index, fields=self.fields)[0]
            return end, ''
        raise skoolmacro.UnsupportedMacroError()

    def expand_udgtable(self, text, index):
        return self._ignore_block(text, index, UDGTABLE_MARKER, TABLE_END_MARKER, '')

    # API
    def expand(self, text):
        """Return `text` with skool macros expanded."""
        return skoolmacro.expand_macros(self, text).strip()

    def _ignore_block(self, text, index, marker, end_marker, rep=None):
        try:
            end = text.index(end_marker, index) + len(end_marker)
        except ValueError:
            raise SkoolParsingError("Missing end marker: {}...".format(text[index - len(marker):index + 15]))
        if rep is None:
            rep = BLOCK_SEP + text[index - len(marker):end] + BLOCK_SEP
        return -end, rep

    def format(self, text, width):
        lines = []
        for index, block in enumerate(self.expand(text).split(BLOCK_SEP)):
            if index % 2 == 0:
                if block:
                    lines.extend(wrap(block, width))
            elif block.startswith(TABLE_MARKER):
                table_lines = self.table_writer.format_table(block[len(TABLE_MARKER):].lstrip())
                if table_lines:
                    table_width = max([len(line) for line in table_lines])
                    if table_width > width:
                        self.warn('Table in entry at {0} is {1} characters wide'.format(self.entry.address, table_width))
                    lines.extend(table_lines)
            elif block.startswith(LIST_MARKER):
                list_obj = self.list_parser.parse_list(self, block[len(LIST_MARKER):].lstrip())
                for item in list_obj.items:
                    item_lines = []
                    if list_obj.bullet:
                        prefix = list_obj.bullet + ' '
                        indent = ' ' * len(prefix)
                    else:
                        prefix = indent = ''
                    for line in wrap(item, width - len(prefix)):
                        item_lines.append(prefix + line)
                        prefix = indent
                    lines.extend(item_lines)
        return lines

    def print_paragraph_separator(self):
        self.write_line(self.format_template('comment', {'text': ''}).rstrip())

    def print_comment_lines(self, paragraphs, instruction=None, ignoreua=None, started=False):
        for paragraph in paragraphs:
            lines = self.format(paragraph, self.desc_width)
            if started and lines:
                self.print_paragraph_separator()
            if lines:
                started = True
            for line in lines:
                if instruction:
                    self.format_warn('Comment above {1} contains address ({0}) not converted to a label:\n; {2}',
                                     'Comment above {1} contains addresses ({0}) not converted to labels:\n; {2}',
                                     self.find_unconverted_addresses(line, ignoreua), instruction.address, line)
                else:
                    self.format_warn('Comment contains address ({}) not converted to a label:\n; {}',
                                     'Comment contains addresses ({}) not converted to labels:\n; {}',
                                     self.find_unconverted_addresses(line, ignoreua), line)
                self.write_line(self.format_template('comment', {'text': line}).rstrip())

    def print_registers(self):
        self.print_paragraph_separator()
        max_reg_len = prefix_len = 0
        for reg in self.entry.registers:
            if reg.delimiters[0]:
                reg.name = self.expand(reg.name)
            max_reg_len = max(max_reg_len, len(reg.name))
            if reg.prefix:
                reg.prefix += ':'
            prefix_len = max(prefix_len, len(reg.prefix))
        for reg in self.entry.registers:
            subs = {
                'max_reg_len': max_reg_len,
                'prefix': reg.prefix,
                'prefix_len': prefix_len,
                'reg': reg.name,
                'reg_len': len(reg.name)
            }
            reg_lines = []
            for line in self.format(reg.contents, self._get_text_width('register', **subs)) or ['']:
                subs['text'] = line
                reg_lines.append(self.format_template('register', subs).rstrip())
                subs['prefix'] = subs['reg'] = ''
            reg_desc = '\n'.join(reg_lines)
            self.format_warn('Register description contains address ({}) not converted to a label:\n{}',
                             'Register description contains addresses ({}) not converted to labels:\n{}',
                             self.find_unconverted_addresses(reg_desc, self.entry.ignoreua['r']), reg_desc)
            self.write_line(reg_desc)

    def print_instruction_prefix(self, instruction, index):
        if instruction.mid_block_comment:
            if index == 0:
                self.print_paragraph_separator()
            self.print_comment_lines(instruction.mid_block_comment, instruction, instruction.ignoreua['m'])
        if instruction.asm_label:
            subs = {
                'label': instruction.asm_label,
                'suffix': self.label_suffix
            }
            self.write_line(self.format_template('label', subs))

    def find_unconverted_addresses(self, text, ignores):
        if ignores == []:
            return ()
        addresses = set()
        for match in re.finditer('(\A|\s|\()((?:0x|\$)[0-9A-Fa-f]{4}|[1-9][0-9]{2,4})(?!([0-9A-Za-z]|[./*+][0-9]))', text):
            addr = match.group(2)
            if addr.startswith(('0x', '$')):
                address = int(addr[-4:], 16)
                min_address = self.base_address
            else:
                address = int(addr)
                min_address = max(self.base_address, 257)
            if min_address <= address <= self.end_address and (ignores is None or address not in ignores):
                addresses.add(addr)
        return addresses

    def print_instructions(self):
        i = 0
        rows = 0
        lines = []
        instructions = self.entry.instructions

        while i < len(instructions) or lines:
            if i < len(instructions):
                instruction = instructions[i]
            else:
                instruction = None

            # Deal with remaining comment lines or rowspan on the previous
            # instruction
            if lines or rows:
                if rows:
                    self.print_instruction_prefix(instruction, i)
                    operation = instruction.operation
                    rows -= 1
                    i += 1
                else:
                    operation = ''

                subs = {
                    'indent': self.indent,
                    'operation': operation,
                    'width': instr_width,
                    'sep': ';',
                    'text': ''
                }
                if lines:
                    subs['text'] = lines.pop(0)
                elif rowspan == 1:
                    subs['sep'] = ''
                oline = self.format_template('instruction', subs).rstrip()
                self.format_warn('Comment at {1} contains address ({0}) not converted to a label:\n{2}',
                                 'Comment at {1} contains addresses ({0}) not converted to labels:\n{2}',
                                 self.find_unconverted_addresses(subs['text'], ignoreua), self.pc, oline)
                self.write_line(oline)
                if len(oline) > self.line_width:
                    self.warn('Line is {0} characters long:\n{1}'.format(len(oline), oline))
                continue

            ignoreua = instruction.ignoreua['i']
            self.pc = instruction.address

            rowspan = rows = instruction.comment.rowspan
            instr_width = max([len(i.operation) for i in instructions[i:i + rowspan]] + [self.instr_width])
            comment_width = self.line_width - 3 - instr_width - self.indent_width
            lines = self.format(instruction.comment.text, max(comment_width, self.min_comment_width))

class TableWriter:
    def __init__(self, asm_writer, max_width, min_col_width, properties):
        self.asm_writer = asm_writer
        self.max_width = max_width
        self.min_col_width = min_col_width
        border_h = properties.get('table-border-horizontal', '-')
        self.border_h_ext = border_h[:1].strip()
        self.border_h_int = (border_h[1:2] or self.border_h_ext).strip()
        self.border_v = properties.get('table-border-vertical', '')[:1] or '|'
        self.border_join = properties.get('table-border-join', '')[:1] or '+'
        self.row_sep = properties.get('table-row-separator', '')[:1].strip()
        self.table = None
        self.table_parser = TableParser()
        self.cell_matrix = None

    def format_table(self, text):
        self.table = self.table_parser.parse_table(self.asm_writer, text)
        self.table.prepare_cells(self.min_col_width, self.max_width)
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
                border = self.border_v
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
                line += self.border_v
            lines.append(line.rstrip())
        return rendered

    def _create_table_text(self):
        lines = []
        max_row_index = len(self.table.rows)
        if max_row_index == 0:
            return lines
        sep = True
        for row_index in range(max_row_index + 1):
            if sep or row_index == max_row_index or self.row_sep:
                row_sep = self._create_row_separator(row_index, sep or row_index == max_row_index)
                if row_sep:
                    lines.append(row_sep)
            if row_index < max_row_index:
                self._render_row(lines, row_index)
                while self._render_row(lines, row_index, False):
                    pass
                sep = any(c.header for c in self.table.rows[row_index])
        return lines

    def _create_row_separator(self, row_index, header):
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
            cell_contents = bool(cell_above and (cell_above.contents or cell_above.row_index + cell_above.rowspan > row_index))
            if cell.transparent and cell_above_transparent and cell_above_left_transparent and cell_left_transparent:
                line += ' '
            elif cell_contents and cell_left_contents:
                line += self.border_v
            else:
                line += self.border_join
            if cell_contents:
                if cell.contents:
                    text = cell.contents.pop(0)
                else:
                    text = ''
                line += ' {} '.format(text.ljust(self.table.get_cell_width(col_index, cell_above.colspan)))
            else:
                if cell.transparent and cell_above_transparent:
                    spacer = ' '
                elif 0 < row_index < len(self.table.rows):
                    if (cell_above is None and not header) or (cell_above and not cell_above.header and self.row_sep):
                        spacer = self.row_sep
                    else:
                        spacer = self.border_h_int
                else:
                    spacer = self.border_h_ext
                if not spacer:
                    return None
                line += spacer * (2 + self.table.get_cell_width(col_index, cell.colspan))
            cell_left_contents = cell_contents
            col_index += cell.colspan

        if cell_contents and not cell_above_transparent:
            return line + self.border_v
        if line.endswith(' '):
            return line.rstrip()
        return line + self.border_join
