# Copyright 2008-2024 Richard Dymond (rjdymond@gmail.com)
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

from collections import namedtuple
import re

from skoolkit import (CASE_LOWER, CASE_UPPER, ROM128, SkoolParsingError,
                      get_int_param, parse_int, read_bin_file, wrap, z80)
from skoolkit.skoolmacro import ClosingBracketError, MacroParsingError, parse_brackets, parse_strings
from skoolkit.textutils import partition_unquoted

COLUMN_WRAP_MARKER = ':w'
DIRECTIVES = 'bcgistuw'
LIST_MARKER = '#LIST'
LIST_END_MARKER = 'LIST#'
TABLE_MARKER = '#TABLE'
TABLE_END_MARKER = 'TABLE#'
Z80_ASSEMBLER = z80.Assembler()

INDEX_STOP = {None: 65536}

Flags = namedtuple('Flags', 'prepend final overwrite append')

class Memory:
    def __init__(self, banks=None, bank=None, roms=None, rom=None, o7ffd=0):
        if banks is None:
            self.banks = [None] * 8
            self.banks[5] = [0] * 0x4000
            self.banks[2] = [0] * 0x4000
            self.banks[0] = [0] * 0x4000
        else:
            self.banks = banks
        if roms is None:
            self.roms = tuple(list(read_bin_file(r)) for r in ROM128)
        else:
            self.roms = roms
        self.memory = [rom or [0] * 0x4000, self.banks[5], self.banks[2], bank or self.banks[0]]
        self.o7ffd = o7ffd

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.memory[index // 0x4000][index % 0x4000]
        return [self.memory[a // 0x4000][a % 0x4000] for a in range(index.start or 0, INDEX_STOP.get(index.stop, index.stop), index.step or 1)]

    def __setitem__(self, index, value):
        if isinstance(index, int):
            self.memory[index // 0x4000][index % 0x4000] = value
        else:
            for a, b in zip(range(index.start or 0, INDEX_STOP.get(index.stop, index.stop), index.step or 1), value):
                self.memory[a // 0x4000][a % 0x4000] = b

    def __len__(self):
        if None in self.banks:
            return 0x10000
        return 0x20000

    def bank(self, page, data=None):
        if None in self.banks:
            for i in (1, 3, 4, 6, 7):
                self.banks[i] = [0] * 0x4000
            self.memory[0] = self.roms[0]
        if data is None:
            self.memory[3] = self.banks[page]
            self.o7ffd = (self.o7ffd & 0xF8) + page
        else:
            self.banks[page][:] = data

    def copy(self):
        banks = [bank[:] if bank else None for bank in self.banks]
        roms = (self.roms[0][:], self.roms[1][:])
        if all(banks):
            bank = banks[self.banks.index(self.memory[3])]
            rom = roms[self.roms.index(self.memory[0])]
        else:
            bank = banks[0]
            rom = self.memory[0][:]
        return Memory(banks, bank, roms, rom, self.o7ffd)

    def out7ffd(self, value):
        if all(self.banks):
            self.memory[0] = self.roms[(value % 32) // 16]
            self.memory[3] = self.banks[value % 8]
            self.o7ffd = value

    def convert(self): # pragma: no cover
        # Prepare for use by a CSimulator
        if all(self.banks):
            rom_id = (self.o7ffd % 32) // 16
            page = self.o7ffd % 8
            self.roms = tuple(bytearray(rom) for rom in self.roms)
            self.banks = [bytearray(bank) for bank in self.banks]
            self.memory = [self.roms[rom_id], self.banks[5], self.banks[2], self.banks[page]]

class Comment:
    def __init__(self, rowspan, text):
        self.rowspan = rowspan
        self.text = text

    def apply_replacements(self, repf):
        self.text = repf(self.text)

class TableParser:
    def parse_text(self, writer, text, index, *cwd):
        try:
            end = text.index(TABLE_END_MARKER, index) + len(TABLE_END_MARKER)
        except ValueError:
            marker = text[text.rindex('#', 0, index):index]
            raise SkoolParsingError("Missing table end marker: {}{}...".format(marker, text[index:index + 15]))
        return end, self.parse_table(writer, text[index:end], *cwd)

    def parse_table(self, writer, table_def, *cwd):
        try:
            index, params = parse_brackets(table_def, default='')
        except ClosingBracketError:
            raise SkoolParsingError("Cannot find closing ')' in table CSS class list:\n{}".format(table_def))
        classes = [c.strip() for c in writer.expand(params, *cwd).split(',')]
        table_class = classes[0]
        column_classes = classes[1:]
        wrap_columns = []
        for i, column_class in enumerate(column_classes):
            if column_class.endswith(COLUMN_WRAP_MARKER):
                column_classes[i] = column_class[:-len(COLUMN_WRAP_MARKER)]
                wrap_columns.append(i)
        table = Table(table_class, wrap_columns)

        text = writer.expand(table_def[index:], *cwd)
        for ws_char in '\n\r\t':
            text = text.replace(ws_char, ' ')
        index = 0
        prev_spans = {}
        while text.find('{', index) >= 0:
            row = []
            row_start = text.find('{ ', index)
            if row_start < 0:
                raise SkoolParsingError("Cannot find opening '{{ ' in table row:\n{0}".format(table_def))
            row_end = text.find(' }', row_start)
            if row_end < 0:
                raise SkoolParsingError("Cannot find closing ' }}' in table row:\n{0}".format(table_def))
            col_index = 0
            for cell in text[row_start + 1:row_end + 1].split(' | '):
                prev_rowspan, prev_colspan = prev_spans.get(col_index, (1, 1))
                while prev_rowspan > 1:
                    prev_spans[col_index] = (prev_rowspan - 1, prev_colspan)
                    col_index += prev_colspan
                    prev_rowspan, prev_colspan = prev_spans.get(col_index, (1, 1))
                header, transparent = False, False
                rowspan, colspan = 1, 1
                if len(column_classes) > col_index:
                    cell_class = column_classes[col_index]
                else:
                    cell_class = ''
                cell = cell.strip()
                if cell.startswith('='):
                    end = cell.find(' ')
                    if end < 0:
                        end = len(cell)
                    for span in cell[1:end].split(','):
                        if span[0] == 'c':
                            try:
                                colspan = int(span[1:])
                            except ValueError:
                                raise SkoolParsingError("Invalid colspan indicator: '{}'".format(span))
                        elif span[0] == 'r':
                            try:
                                rowspan = int(span[1:])
                            except ValueError:
                                raise SkoolParsingError("Invalid rowspan indicator: '{}'".format(span))
                        elif span[0] == 'h':
                            header = True
                        elif span[0] == 't':
                            transparent = True
                    cell = cell[end:].lstrip()
                row.append(Cell(cell, transparent, colspan, rowspan, header, cell_class))
                prev_spans[col_index] = (rowspan, colspan)
                col_index += colspan

            # Deal with the case where the previous row contains one or more
            # cells at the end with rowspan > 1
            while col_index in prev_spans:
                prev_rowspan, prev_colspan = prev_spans[col_index]
                if prev_rowspan > 1:
                    prev_spans[col_index] = (prev_rowspan - 1, prev_colspan)
                col_index += prev_colspan

            table.add_row(row)
            index = row_end + 1

        return table

class Table:
    def __init__(self, table_class, wrap_columns):
        self.table_class = table_class
        self.wrap_columns = wrap_columns
        self.rows = []
        self.cells = []
        self.col_widths = None
        self.num_cols = 0

    def add_row(self, cells):
        self.rows.append(cells)
        self.cells.extend(cells)

    def prepare_cells(self, min_col_width, max_table_width):
        # For each cell, set its row_index, col_index and wrappable flag, and
        # convert the contents to a 1-item list
        prev_spans = {}
        for row_index, row in enumerate(self.rows):
            col_index = 0
            for cell in row:
                while True:
                    prev_rowspan, prev_colspan = prev_spans.get(col_index, (1, 1))
                    if prev_rowspan == 1:
                        break
                    prev_spans[col_index] = (prev_rowspan - 1, prev_colspan)
                    col_index += prev_colspan
                cell.row_index, cell.col_index = row_index, col_index
                self.num_cols = max(self.num_cols, col_index + 1)
                cell.wrappable = col_index in self.wrap_columns
                cell.contents = [cell.contents]
                prev_spans[col_index] = (cell.rowspan, cell.colspan)
                col_index += cell.colspan

            # Deal with cells at the end of the previous row that have rowspan
            # greater than 1
            while col_index in prev_spans:
                prev_rowspan, prev_colspan = prev_spans[col_index]
                if prev_rowspan > 1:
                    prev_spans[col_index] = (prev_rowspan - 1, prev_colspan)
                col_index += prev_colspan

        # Calculate initial (minimum) column widths
        self._calculate_col_widths(min_col_width)

        # Increase the width of the wrappable cells until either none of them
        # need wrapping or the table is the maximum width
        self._increase_widths(max_table_width)

        # Wrap the contents of the cells in the wrappable columns
        for cell in self.cells:
            if cell.wrappable:
                width = self.get_cell_width(cell.col_index, cell.colspan)
                cell.contents = wrap(cell.contents[0], width) or ['']

        # Recalculate column widths to fit the wrapped contents
        self._calculate_col_widths()

    def get_cell_width(self, col_index, colspan):
        return sum(self.col_widths[col_index:col_index + colspan]) + 3 * (colspan - 1)

    def _calculate_col_widths(self, min_col_width=0):
        # Examine cells with colspan=1; on the first call, any wrappable column
        # will have its width set to at least min_col_width > 0
        self.col_widths = [0] * self.num_cols
        for cell in self.cells:
            if cell.colspan == 1:
                if min_col_width and cell.wrappable:
                    self.col_widths[cell.col_index] = max(self.col_widths[cell.col_index], min_col_width)
                else:
                    self.col_widths[cell.col_index] = max(self.col_widths[cell.col_index], cell.get_width())

        # Make sure that cells with colspan > 1 have enough space
        for cell in self.cells:
            if cell.colspan > 1 and (min_col_width == 0 or not cell.wrappable):
                space_needed = cell.get_width() - self.get_cell_width(cell.col_index, cell.colspan)
                if space_needed > 0:
                    # On the first call, give extra space only to wrappable
                    # columns if there are any, or all columns otherwise; on
                    # the second call, give extra space to all columns (because
                    # the wrappable ones have already been wrapped and had
                    # their width decided)
                    subcols = list(range(cell.col_index, cell.col_index + cell.colspan))
                    if min_col_width:
                        subcols = [i for i in subcols if i in self.wrap_columns] or subcols
                    while space_needed > 0:
                        for col_index in subcols:
                            if space_needed > 0:
                                self.col_widths[col_index] += 1
                                space_needed -= 1

    def _increase_widths(self, max_table_width):
        width = 3 * (self.num_cols + 1) - 2 + sum(self.col_widths)
        done = width >= max_table_width
        while not done:
            done = True
            for cell in self.cells:
                if cell.wrappable and len(cell.contents[0]) > self.col_widths[cell.col_index]:
                    done = False
                    for col_index in range(cell.col_index, cell.col_index + cell.colspan):
                        self.col_widths[col_index] += 1
                        width += 1
                        if width == max_table_width:
                            return

class Cell:
    def __init__(self, contents, transparent, colspan, rowspan, header, cell_class):
        self.contents = contents
        self.colspan = colspan
        self.rowspan = rowspan
        self.header = header
        self.transparent = transparent
        self.cell_class = cell_class
        self.row_index = None
        self.col_index = None
        self.wrappable = None

    def get_width(self):
        return max([len(line) for line in self.contents])

class ListParser:
    def __init__(self, bullet=''):
        self.bullet = bullet

    def parse_text(self, writer, text, index, *cwd):
        try:
            end = text.index(LIST_END_MARKER, index) + len(LIST_END_MARKER)
        except ValueError:
            raise SkoolParsingError("No end marker: #LIST{}...".format(text[index:index + 15]))
        return end, self.parse_list(writer, text[index:end], *cwd)

    def parse_list(self, writer, list_def, *cwd):
        text = list_def
        for ws_char in '\n\r\t':
            text = text.replace(ws_char, ' ')

        if text.startswith('('):
            try:
                index, params = parse_strings(text, 0, 2, ('', self.bullet))
            except ClosingBracketError:
                raise SkoolParsingError("Cannot find closing ')' in parameter list:\n{}".format(list_def))
        else:
            index, params = 0, ('', self.bullet)
        list_obj = List(writer.expand(params[0], *cwd).strip(), writer.expand(params[1], *cwd))

        text = writer.expand(text[index:], *cwd)
        index = 0
        while text.find('{', index) >= 0:
            item_start = text.find('{ ', index)
            if item_start < 0:
                raise SkoolParsingError("Cannot find opening '{{ ' in list item:\n{0}".format(list_def))
            item_end = text.find(' }', item_start)
            if item_end < 0:
                raise SkoolParsingError("Cannot find closing ' }}' in list item:\n{0}".format(list_def))
            list_obj.add_item(text[item_start + 1:item_end].strip())
            index = item_end + 2

        return list_obj

class List:
    def __init__(self, css_class, bullet):
        self.css_class = css_class
        self.bullet = bullet
        self.items = []

    def add_item(self, text):
        self.items.append(text)

class Register:
    def __init__(self, delimiters, prefix, name, contents):
        self.delimiters = delimiters
        self.prefix = prefix
        self.name = name
        self.contents = contents

    def apply_replacements(self, repf):
        self.contents = repf(self.contents)

def get_address(operation):
    search = re.search(r'(\A|[\s,(+-])(\$[0-9A-Fa-f]+|%[01]+|\d+)', operation)
    if search:
        return search.group(2)

def join_comments(comments, split=False, keep_lines=False):
    if keep_lines:
        if any(c for c in comments if c.strip() != '.'):
            return comments
        return ()
    sections = [[]]
    for line in comments:
        s_line = line.strip()
        if split and s_line == '.':
            sections.append([])
        elif s_line:
            sections[-1].append(s_line)
    paragraphs = [' '.join(s) for s in sections if s]
    if split:
        return paragraphs
    if paragraphs:
        return paragraphs[0]
    return ''

def _apply_comment_subs(lines, sub_lines):
    if len(lines) <= len(sub_lines) or (sub_lines and sub_lines[-1] is None):
        comment_lines = [line for line in sub_lines if line is not None]
    else:
        comment_lines = sub_lines + lines[len(sub_lines):]
    return ' '.join(comment_lines), comment_lines

def parse_address_comments(comments, keep_lines=False):
    i = 0
    while i < len(comments):
        instruction = comments[i][0]
        if instruction:
            comment, comment_lines = _apply_comment_subs(*comments[i][1:3])
            grouped = [comment_lines]
            rowspan = 1
            if comment.startswith('{'):
                comment_lines[0] = comment_lines[0].lstrip('{')
                if comment_lines[0].startswith(' {'):
                    comment_lines[0] = comment_lines[0][1:]
                nesting = comment.count('{') - comment.count('}')
                while nesting > 0:
                    i += 1
                    if i >= len(comments) or comments[i][0] is None:
                        break
                    if comments[i][0]:
                        comment_lines = []
                        grouped.append(comment_lines)
                    comment, lines = _apply_comment_subs(*comments[i][1:3])
                    comment_lines.extend(lines)
                    rowspan += 1
                    nesting += comment.count('{') - comment.count('}')
                comment_lines[-1] = comment_lines[-1].rstrip('}')
                if comment_lines[-1].endswith('} '):
                    comment_lines[-1] = comment_lines[-1][:-1]
            if keep_lines:
                instruction.set_comment(rowspan, grouped)
            else:
                text = ' '.join(c for cl in grouped for c in cl if c).strip()
                instruction.set_comment(rowspan, text)
        i += 1

def parse_address_range(value):
    addresses = [parse_int(n) for n in value.split('-', 1)]
    if len(addresses) == 1 and addresses[0] is not None:
        return addresses
    if len(addresses) == 2 and all(a is not None for a in addresses):
        return range(addresses[0], addresses[1] + 1)
    return ()

def parse_addresses(line):
    addresses = []
    if line.startswith('='):
        for n in line[1:].split(','):
            addr = parse_int(n)
            if addr is not None:
                addresses.append(addr)
    return addresses

def parse_asm_bank_directive(directive, snapshot, skool_reader, **kwargs):
    bank, sep, skoolfile = directive[5:].partition(',')
    page = parse_int(bank, 0) % 8
    if skoolfile:
        snapshot.bank(page, skool_reader(skoolfile, **kwargs).snapshot[49152:])
    else:
        snapshot.bank(page)

def parse_asm_block_directive(directive, stack):
    prefix = directive[:4]
    infix = directive[len(prefix):len(prefix) + 1]
    suffix = directive[len(prefix) + len(infix):].rstrip()
    if prefix in ('ofix', 'bfix', 'rfix', 'isub', 'ssub', 'rsub') and infix in '+-' and suffix in ('begin', 'else', 'end'):
        if stack:
            cur_op = stack[-1]
        else:
            cur_op = (None, None)
        if suffix == 'begin':
            if prefix == cur_op[0]:
                raise SkoolParsingError('{0} inside {1}{2} block'.format(directive, cur_op[0], cur_op[1]))
            stack.append((prefix, infix))
        elif suffix == 'else':
            if cur_op[0] is None:
                raise SkoolParsingError('{0} not inside block'.format(directive))
            if prefix != cur_op[0] or infix == cur_op[1]:
                raise SkoolParsingError('{0} inside {1}{2} block'.format(directive, cur_op[0], cur_op[1]))
            stack[-1] = (prefix, infix)
        elif suffix == 'end':
            if cur_op[0] is None:
                raise SkoolParsingError('{0} has no matching start directive'.format(directive))
            if (prefix, infix) != cur_op:
                raise SkoolParsingError('{0} cannot end {1}{2} block'.format(directive, cur_op[0], cur_op[1]))
            stack.pop()
        return True
    return False

def parse_asm_bytes_directive(directive):
    try:
        return tuple(get_int_param(b) for b in directive[6:].split(','))
    except ValueError:
        return ()

def parse_asm_data_directive(snapshot, address, directive, advance=True):
    a, sep, values = directive[5:].rpartition(':')
    if sep:
        addr = parse_int(a)
        if addr is None:
            return address
    else:
        addr = address
    operation = '{} {}'.format(directive[:4], partition_unquoted(values, ';')[0])
    data = set_bytes(snapshot, Z80_ASSEMBLER, addr, operation)
    if advance:
        return addr + len(data)
    return addr, data

def parse_asm_keep_directive(directive):
    return parse_addresses(directive[4:])

def parse_asm_nowarn_directive(directive):
    return parse_addresses(directive[6:])

def parse_asm_refs_directive(directive):
    refs, sep, rrefs = directive[4:].partition(':')
    return parse_addresses(refs), parse_addresses('=' + rrefs)

def parse_asm_sub_fix_directive(directive):
    match = re.match('[>/|+]+', directive)
    if match:
        prefix = match.group()
        directive = directive[len(prefix):]
    else:
        prefix = ''
    prepend = '>' in prefix
    final = '/' in prefix
    overwrite = '|' in prefix
    append = '+' in prefix
    op, sep, comment = partition_unquoted(directive, ';')
    if sep:
        comment = comment.strip()
    else:
        comment = None
    label, lsep, op = partition_unquoted(op, ':')
    flags = Flags(prepend, final, overwrite, append)
    if lsep:
        return flags, label.strip(), op.strip(), comment
    return flags, None, label.strip(), comment

def _apply_ignores(ignores, section_ignores, index, line_no):
    for i in sorted(ignores):
        if i < line_no:
            section_ignores[index] = ignores.pop(i)
            return

def _parse_registers(lines, mode, keep_lines):
    if keep_lines:
        if any(c for c in lines if c.strip() != '.'):
            return [Register(('', ''), '', '', lines)]
        return ()
    registers = []
    desc_lines = []
    for line in lines:
        s_line = line.strip()
        if s_line == '.':
            continue
        if desc_lines and s_line.startswith('.'):
            desc_lines.append(s_line[1:].lstrip())
            continue
        if desc_lines:
            registers.append(Register(delimiters, prefix, reg, ' '.join(desc_lines).lstrip()))
            desc_lines.clear()
        delimiters, reg, desc = parse_register(s_line)
        desc_lines.append(desc)
        prefix = ''
        if ':' in reg:
            prefix, reg = reg.split(':', 1)
        if mode.case == CASE_LOWER:
            reg = reg.lower()
        elif mode.case == CASE_UPPER:
            reg = reg.upper()
    if desc_lines:
        registers.append(Register(delimiters, prefix, reg, ' '.join(desc_lines).lstrip()))
    return registers

def parse_entry_header(comments, ignores, mode, keep_lines=False):
    sections = [[], [], [], []]
    section_ignores = [None] * len(sections)
    line_no = 0
    index = 0
    last_line = ""
    for line in comments:
        if keep_lines:
            s_line = line.rstrip()
        else:
            s_line = line.strip()
        if s_line:
            sections[index].append(s_line)
            last_line = s_line
        elif last_line:
            _apply_ignores(ignores, section_ignores, index, line_no)
            index = min(index + 1, len(sections) - 1)
        line_no += 1
    _apply_ignores(ignores, section_ignores, index, line_no)
    mode.ignoreua.update({
        't': section_ignores[0],
        'd': section_ignores[1],
        'r': section_ignores[2],
        'm': section_ignores[3],
        'e': None
    })
    title = join_comments(sections[0], False, keep_lines)
    description = join_comments(sections[1], True, keep_lines)
    registers = _parse_registers(sections[2], mode, keep_lines)
    start_comment = join_comments(sections[3], True, keep_lines)
    return start_comment, title, description, registers

def parse_instruction(line):
    ctl = line[0]
    addr_str = line[1:6]
    operation, sep, comment = partition_unquoted(line[6:], ';')
    return ctl, addr_str, operation.strip(), comment.strip()

def parse_register(line):
    delimiters = ('', '')
    if not line[0].isalnum():
        try:
            end, reg = parse_strings(line, num=1)
            delimiters = (line[0], line[end - 1])
            desc = line[end:].lstrip()
        except MacroParsingError:
            pass
    if not delimiters[0]:
        elements = line.split(None, 1)
        reg = elements[0]
        if len(elements) > 1:
            desc = elements[1]
        else:
            desc = ''
    return delimiters, reg, desc

def read_skool(skoolfile, asm=1, sub_mode=0, fix_mode=0):
    """Read a skool file and return each block as it's found.

    :param skoolfile: The file-like object to read.
    :param asm: 1 to read every line, and process ASM block directives except
                in non-entry blocks (ctl); 2 to read every line, and process
                all ASM block directives (bin, html); or 3 to read lines only
                between @start and @end, and process all ASM block directives
                (asm).
    :param sub_mode: 1 to parse @*sub block directives in @isub mode, 2 to
                     parse them in @ssub mode, 3 to parse them in @rsub mode,
                     or 0 to parse them in none of these modes.
    :param fix_mode: 1 to parse @*fix block directives in @ofix mode, 2 to
                     parse them in @bfix mode, 3 to parse them in @rfix mode,
                     or 0 to parse them in none of these modes.
    """
    modes = {
        'isub': ('-', '+')[sub_mode > 0],
        'ssub': ('-', '+')[sub_mode > 1],
        'rsub': ('-', '+')[sub_mode > 2],
        'ofix': ('-', '+')[fix_mode > 0],
        'bfix': ('-', '+')[fix_mode > 1],
        'rfix': ('-', '+')[fix_mode > 2]
    }
    stack = []
    lines = []
    all_lines = []
    entry = False
    include = True
    started = asm < 3

    for line in skoolfile:
        s_line = line.rstrip()

        if line.startswith('@'):
            directive = s_line[1:]
            if parse_asm_block_directive(directive, stack):
                include = all(i == modes[p] for p, i in stack)
                all_lines.append(s_line)
                continue
            if asm == 3 and include and directive.startswith(('start', 'end')):
                started = directive.startswith('start')
                all_lines.append(s_line)
                continue

        if s_line:
            all_lines.append(s_line)
            if started and include:
                if s_line[0] in DIRECTIVES:
                    entry = True
                lines.append(s_line)
            continue

        if asm > 1 and not include:
            continue

        if asm > 1 or entry:
            yield not entry, lines
        else:
            yield True, all_lines
        lines = []
        all_lines = []
        entry = False

    if asm > 1 or entry:
        yield not entry, lines
    else:
        yield True, all_lines

def set_bytes(snapshot, assembler, address, operation):
    data = assembler.assemble(operation, address)
    snapshot[address:address + len(data)] = data
    return data
