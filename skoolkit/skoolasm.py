# -*- coding: utf-8 -*-

# Copyright 2008-2013 Richard Dymond (rjdymond@gmail.com)
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
import inspect

from . import warn, write_text, wrap, parse_int, get_chr, SkoolParsingError
from .skoolmacro import parse_ints, parse_params, get_params, MacroParsingError, UnsupportedMacroError
from .skoolparser import TableParser, ListParser, TABLE_MARKER, TABLE_END_MARKER, LIST_MARKER, LIST_END_MARKER, HTML_MACRO_DELIMITERS

UDGTABLE_MARKER = '#UDGTABLE'

class AsmWriter:
    def __init__(self, parser, crlf, tab, properties, lower, instr_width, show_warnings):
        self.parser = parser
        self.show_warnings = show_warnings

        # Build a label dictionary
        self.labels = {}
        for address, instructions in parser.instructions.items():
            label = instructions[0].asm_label
            if label:
                self.labels[address] = label

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
        if tab:
            self.indent_width = 8
        else:
            self.indent_width = self._get_int_property(properties, 'indent', 2)
        self.instr_width = instr_width
        self.min_comment_width = self._get_int_property(properties, 'comment-width-min', 10)
        self.line_width = self._get_int_property(properties, 'line-width', 79)
        self.desc_width = self.line_width - 2

        # Line terminator and indent
        if crlf:
            self.end = '\r\n'
        else:
            self.end = '\n'
        if tab:
            self.indent = '\t'
        else:
            self.indent = ' ' * self.indent_width

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
        self.entries = self.parser.entries

        self.list_parser = ListParser()

        self._create_macros()

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
                self.write_line('{0}{1} {2}'.format(self.indent, org_dir, org))
                self.write_line('')
            self.entry = entry
            self.print_entry()
            self.write_line('')

    def print_header(self, header):
        if header:
            for line in header:
                self.write_line('; {0}'.format(self.expand(line)).rstrip())
            self.write_line('')

    def print_entry(self):
        self.print_comment_lines([self.entry.description], ignoreua=self.entry.ignoretua)
        if self.entry.details:
            self.print_comment_lines(self.entry.details, ignoreua=self.entry.ignoredua, started=True)
        if self.entry.is_routine() and self.entry.registers:
            self.write_line(';')
            prefix_len = max([len(reg.prefix) for reg in self.entry.registers])
            if prefix_len:
                prefix_len += 1
            indent = ''.ljust(prefix_len)
            for reg in self.entry.registers:
                if reg.prefix:
                    prefix = '{0}:'.format(reg.prefix).rjust(prefix_len)
                else:
                    prefix = indent
                self.write_line('; {0}{1} {2}'.format(prefix, reg.name, self.expand(reg.contents)))
        self.print_instructions()
        if self.entry.end_comment:
            self.print_comment_lines(self.entry.end_comment, ignoreua=self.entry.ignoreecua)

    def write_line(self, s):
        write_text('{0}{1}'.format(s, self.end))

    def _expand_item_macro(self, text, index, default):
        end, params, p_text = parse_params(text, index, default)
        return end, p_text

    def _expand_unsupported_macro(self, text, index):
        if self.handle_unsupported_macros:
            end, params, p_text = parse_params(text, index, chars=',:;-x{}')
            return end, ''
        raise UnsupportedMacroError()

    def pop_snapshot(self):
        """Discard the current memory snapshot and replace it with the one that
        was most recently saved (by
        :meth:`~skoolkit.skoolasm.AsmWriter.push_snapshot`)."""
        self.snapshot = self._snapshots.pop()[0]

    def push_snapshot(self, name=''):
        """Save the current memory snapshot for later retrieval (by
        :meth:`~skoolkit.skoolasm.AsmWriter.pop_snapshot`), and put a copy in
        its place.

        :param name: An optional name for the snapshot.
        """
        self._snapshots.append((self.snapshot[:], name))

    def _create_macros(self):
        self.macros = {}
        prefix = 'expand_'
        for name, method in inspect.getmembers(self, inspect.ismethod):
            search = re.search('{0}[a-z]+'.format(prefix), name)
            if search and name == search.group():
                macro = '#{0}'.format(name[len(prefix):].upper())
                self.macros[macro] = method

    def expand_bug(self, text, index):
        # #BUG[#name][(link text)]
        return self._expand_item_macro(text, index, 'bug')

    def expand_call(self, text, index):
        # #CALL:methodName(args)
        macro = '#CALL'
        if text[index] != ':':
            raise MacroParsingError("Malformed macro: {0}{1}...".format(macro, text[index]))
        end, method_name, arg_string = parse_params(text, index + 1, chars='_')
        if not hasattr(self, method_name):
            self.warn("Unknown method name in {0} macro: {1}".format(macro, method_name))
            return end, ''
        method = getattr(self, method_name)
        if not inspect.ismethod(method):
            raise MacroParsingError("Uncallable method name: {0}".format(method_name))
        if arg_string is None:
            raise MacroParsingError("No argument list specified: {0}{1}".format(macro, text[index:end]))
        args = get_params(arg_string)
        retval = method(*args)
        if retval is None:
            retval = ''
        return end, retval

    def expand_chr(self, text, index):
        # #CHRnum or #CHR(num)
        if text[index:].startswith('('):
            offset = 1
        else:
            offset = 0
        end, num = parse_ints(text, index + offset, 1)
        return end + offset, get_chr(num)

    def expand_d(self, text, index):
        # #Daddr
        end, addr = parse_ints(text, index, 1)
        entry = self.parser.get_entry(addr)
        if entry:
            if entry.description:
                return end, entry.description
            raise MacroParsingError('Entry at {0} has no description'.format(addr))
        raise MacroParsingError('Cannot determine description for nonexistent entry at {0}'.format(addr))

    def expand_erefs(self, text, index):
        # #EREFSaddr
        end, address = parse_ints(text, index, 1)
        ereferrers = self.parser.get_entry_point_refs(address)
        if text[index] == '$':
            addr_fmt = '${0:04X}'
        else:
            addr_fmt = '{0}'
        if not ereferrers:
            raise MacroParsingError('Entry point at {0} has no referrers'.format(addr_fmt.format(address)))
        ereferrers.sort()
        rep = 'routine at '
        if len(ereferrers) > 1:
            rep = 'routines at '
            rep += ', '.join('#R{0}'.format(addr_fmt.format(addr)) for addr in ereferrers[:-1])
            rep += ' and '
        addr = ereferrers[-1]
        rep += '#R{0}'.format(addr_fmt.format(addr))
        return end, rep

    def expand_fact(self, text, index):
        # #FACT[#name][(link text)]
        return self._expand_item_macro(text, index, 'fact')

    def expand_font(self, text, index):
        return self._expand_unsupported_macro(text, index)

    def expand_html(self, text, index):
        # #HTML(text)
        delim1 = text[index]
        delim2 = HTML_MACRO_DELIMITERS.get(delim1, delim1)
        start = index + 1
        end = text.find(delim2, start)
        if end < start:
            raise MacroParsingError("No terminating delimiter: #HTML{0}".format(text[index:]))
        return end + 1, ''

    def expand_link(self, text, index):
        # #LINK:PageId[#name](link text)
        macro = '#LINK'
        if text[index] != ':':
            raise MacroParsingError("Malformed macro: {0}{1}...".format(macro, text[index]))
        end, params, link_text = parse_params(text, index + 1)
        if not link_text:
            raise MacroParsingError("No link text specified: {0}{1}".format(macro, text[index:end]))
        return end, link_text

    def expand_poke(self, text, index):
        # #POKE[#name][(link text)]
        return self._expand_item_macro(text, index, 'poke')

    def expand_pokes(self, text, index):
        # #POKESaddr,byte[,length,step][;addr,byte[,length,step];...]
        end, addr, byte, length, step = parse_ints(text, index, 4, (1, 1))
        self.snapshot[addr:addr + length * step:step] = [byte] * length
        while end < len(text) and text[end] == ';':
            end, addr, byte, length, step = parse_ints(text, end + 1, 4, (1, 1))
            self.snapshot[addr:addr + length * step:step] = [byte] * length
        return end, ''

    def expand_pops(self, text, index):
        # #POPS
        self.pop_snapshot()
        return index, ''

    def expand_pushs(self, text, index):
        # #PUSHS[name]
        end, name, p_text = parse_params(text, index)
        self.push_snapshot(name)
        return end, ''

    def expand_r(self, text, index):
        # #Raddr[@code][#anchor][(link text)]
        end, params, p_text = parse_params(text, index, chars='@')
        if p_text:
            return end, p_text
        addr_str = params[:5]
        if params[5:].startswith('@'):
            return end, addr_str
        address = parse_int(addr_str)
        label = self.labels.get(address)
        if label is None:
            if self.base_address <= address <= self.end_address:
                self.warn('Could not convert address {0} to label'.format(addr_str))
            instructions = self.parser.instructions.get(address)
            if instructions:
                label = instructions[0].addr_str
            elif addr_str.startswith('$'):
                label = addr_str[1:]
            else:
                label = addr_str
        return end, label

    def expand_refs(self, text, index):
        # #REFSaddr[(prefix)]
        end, addr_str, prefix = parse_params(text, index, '')
        address = parse_int(addr_str)
        entry = self.entries.get(address)
        if not entry:
            raise MacroParsingError('No entry at {0}'.format(addr_str))
        if text[index] == '$':
            addr_fmt = '${0:04X}'
        else:
            addr_fmt = '{0}'
        referrers = [ref.address for ref in entry.referrers]
        if referrers:
            referrers.sort()
            rep = '{0} routine at '.format(prefix).lstrip()
            if len(referrers) > 1:
                rep = '{0} routines at '.format(prefix).lstrip()
                rep += ', '.join('#R{0}'.format(addr_fmt.format(addr)) for addr in referrers[:-1])
                rep += ' and '
            addr = referrers[-1]
            rep += '#R{0}'.format(addr_fmt.format(addr))
        else:
            rep = 'Not used directly by any other routines'
        return end, rep

    def expand_reg(self, text, index):
        # #REGreg
        end, reg, p_text = parse_params(text, index, chars="'")
        if not reg:
            raise MacroParsingError('Missing register argument')
        if len(reg) > 3 or any([char not in "abcdefhlirspxy'" for char in reg]):
            raise MacroParsingError('Bad register: "{0}"'.format(reg))
        if self.lower:
            reg_name = reg.lower()
        else:
            reg_name = reg.upper()
        return end, reg_name

    def expand_scr(self, text, index):
        return self._expand_unsupported_macro(text, index)

    def expand_space(self, text, index):
        # #SPACE[num] or #SPACE([num])
        if text[index:].startswith('('):
            offset = 1
        else:
            offset = 0
        end, num_sp = parse_ints(text, index + offset, 1, (1,))
        return end + offset, ''.ljust(num_sp)

    def expand_udg(self, text, index):
        return self._expand_unsupported_macro(text, index)

    def expand_udgarray(self, text, index):
        return self._expand_unsupported_macro(text, index)

    def expand(self, text):
        if text.find('#') < 0:
            return text

        while 1:
            search = re.search('#[A-Z]+', text)
            if not search:
                break
            marker = search.group()
            if not marker in self.macros:
                raise SkoolParsingError('Found unknown macro: {0}'.format(marker))
            repf = self.macros[marker]
            start, index = search.span()
            try:
                end, rep = repf(text, index)
            except UnsupportedMacroError:
                raise SkoolParsingError('Found unsupported macro: {0}'.format(marker))
            except MacroParsingError as e:
                raise SkoolParsingError('Error while parsing {0} macro: {1}'.format(marker, e.args[0]))
            text = "{0}{1}{2}".format(text[:start], rep, text[end:])

        return text.strip()

    def find_markers(self, block_indexes, text, marker, end_marker):
        index = 0
        while text.find(marker, index) >= 0:
            block_index = text.index(marker, index)
            block_end_index = text.index(end_marker, block_index) + len(end_marker)
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

    def print_instruction_prefix(self, instruction):
        mid_routine_comment = instruction.get_mid_routine_comment()
        if mid_routine_comment:
            self.print_comment_lines(mid_routine_comment, instruction)
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
                    self.print_instruction_prefix(instruction)
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
        self.cell_padding = len(' | ')
        self.table = None
        self.table_parser = TableParser()

    def format_table(self, text):
        self.table = self.table_parser.parse_table(text)
        self.table.cell_padding = self.cell_padding
        self.table.prepare_cells()
        self.table.reduce_width(self.max_width, self.min_col_width)
        return self._create_table_text()

    def _create_table_text(self):
        header_rows = [-1] + self.table.get_header_rows()
        lines = []
        prev_row = [(None, 1, 0)] * self.table.num_cols
        for row_index, row in enumerate(self.table.rows + [[]]):
            # Deal with remaining lines in previous row
            finished = row_index == 0
            while not finished:
                line = ''
                adj_transparent = True
                finished = True
                col_index = 0
                while col_index < self.table.num_cols:
                    prev_cell, prev_rowspan, prev_line_index = prev_row[col_index]
                    if adj_transparent and prev_cell.transparent:
                        line += ' '
                    else:
                        line += '|'
                    if prev_cell:
                        adj_transparent = prev_cell.transparent
                        colspan = prev_cell.colspan
                        if prev_line_index < len(prev_cell.contents):
                            contents = prev_cell.contents[prev_line_index]
                        else:
                            contents = ''
                    else:
                        colspan = 1
                        contents = ''
                    if contents and prev_rowspan == 1:
                        finished = False
                    line += " {0} ".format(contents.ljust(self.table.get_cell_width(col_index, colspan)))
                    prev_row[col_index] = (prev_cell, prev_rowspan, prev_line_index + 1)
                    col_index += colspan
                if finished:
                    for i, (prev_cell, prev_rowspan, prev_line_index) in enumerate(prev_row):
                        if prev_rowspan > 1:
                            prev_row[i] = (prev_cell, prev_rowspan, prev_line_index - 1)
                    break
                if not prev_cell.transparent:
                    line += '|'
                lines.append(line.rstrip())

            # Stop now if we've reached the end of the table (marked by an
            # empty row)
            if not row:
                break

            # Create a separator row if required
            if row_index - 1 in header_rows:
                lines.append(self._create_row_separator(row, prev_row, row_index > 0))

            line = ''
            adj_transparent = True
            col_index = 0
            for cell in row:
                # Deal with previous rowspan > 1
                prev_cell, prev_rowspan, prev_line_index = prev_row[col_index]
                while prev_rowspan > 1:
                    if adj_transparent and prev_cell.transparent:
                        line += ' '
                    else:
                        line += '|'
                    adj_transparent, colspan = prev_cell.transparent, prev_cell.colspan
                    if prev_line_index < len(prev_cell.contents):
                        contents = prev_cell.contents[prev_line_index]
                    else:
                        contents = ''
                    line += " {0} ".format(contents.ljust(self.table.get_cell_width(col_index, colspan)))
                    prev_row[col_index] = (prev_cell, prev_rowspan - 1, prev_line_index + 1)
                    col_index += colspan
                    prev_cell, prev_rowspan, prev_line_index = prev_row[col_index]

                # Deal with cells in this row
                if adj_transparent and cell.transparent:
                    line += ' '
                else:
                    line += '|'
                adj_transparent, colspan = cell.transparent, cell.colspan
                line += " {0} ".format(cell.contents[0].ljust(self.table.get_cell_width(col_index, colspan)))
                prev_row[col_index] = (cell, cell.rowspan, 1)
                col_index += colspan

            # Deal with cells at the end of the previous row that have rowspan
            # greater than 1
            while col_index < len(prev_row):
                prev_cell, prev_rowspan, prev_line_index = prev_row[col_index]
                if prev_rowspan > 1:
                    if adj_transparent and prev_cell.transparent:
                        line += ' '
                    else:
                        line += '|'
                    adj_transparent, colspan = prev_cell.transparent, prev_cell.colspan
                    if prev_line_index < len(prev_cell.contents):
                        contents = prev_cell.contents[prev_line_index]
                    else:
                        contents = ''
                    line += " {0} ".format(contents.ljust(self.table.get_cell_width(col_index, colspan)))
                    prev_row[col_index] = (prev_cell, prev_rowspan - 1, prev_line_index + 1)
                    col_index += prev_cell.colspan
                    cell = prev_cell
                else:
                    break

            if not cell.transparent:
                line += '|'
            lines.append(line.rstrip())

        lines.append(self._create_row_separator(self.table.rows[-1], prev_row))
        return lines

    def _create_row_separator(self, row, prev_row=None, fill=False):
        separator = ''
        col_index = 0
        adj_transparent = True
        for cell in row:
            # Deal with previous rowspan > 1
            if col_index < cell.col_index:
                prev_cell = prev_row[col_index][0]
                if prev_cell.transparent:
                    separator += ' '
                    spacer = ' '
                else:
                    separator += '+'
                    spacer = '-'
                colspan = cell.col_index - col_index
                separator += spacer * (2 + self.table.get_cell_width(col_index, colspan))

            # Deal with cells in this row
            col_index, colspan = cell.col_index, cell.colspan
            solid = fill or not cell.transparent
            if adj_transparent and not solid:
                separator += ' '
            else:
                separator += '+'
            if solid:
                spacer = '-'
            else:
                spacer = ' '
            separator += spacer * (2 + self.table.get_cell_width(col_index, colspan))
            adj_transparent = cell.transparent
            col_index += colspan

        # Deal with cells at the end of the previous row that have rowspan > 1
        if prev_row[0][0]:
            while col_index < self.table.num_cols:
                prev_cell = prev_row[col_index][0]
                if adj_transparent and prev_cell.transparent and not fill:
                    separator += ' '
                else:
                    separator += '+'
                if prev_cell.transparent:
                    spacer = ' '
                else:
                    spacer = '-'
                separator += spacer * (2 + self.table.get_cell_width(col_index, prev_cell.colspan))
                col_index += prev_cell.colspan

        if separator.endswith('-'):
            return separator + '+'
        return separator.rstrip()
