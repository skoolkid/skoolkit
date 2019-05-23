# Copyright 2008-2019 Richard Dymond (rjdymond@gmail.com)
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

from collections import defaultdict, namedtuple
import html
import re

from skoolkit import (BASE_10, BASE_16, CASE_LOWER, CASE_UPPER, SkoolParsingError,
                      warn, wrap, get_int_param, parse_int, open_file)
from skoolkit.skoolmacro import INTEGER, ClosingBracketError, MacroParsingError, parse_brackets, parse_if, parse_strings
from skoolkit.textutils import partition_unquoted, split_quoted, split_unquoted
from skoolkit.z80 import assemble, convert_case, get_size, split_operation

DIRECTIVES = 'bcgistuw'

TABLE_MARKER = '#TABLE'
TABLE_END_MARKER = 'TABLE#'
COLUMN_WRAP_MARKER = ':w'

LIST_MARKER = '#LIST'
LIST_END_MARKER = 'LIST#'

Flags = namedtuple('Flags', 'prepend final overwrite append')

def _replace_nums(operation, hex_fmt=None, skip_bit=False, prefix=None):
    elements = re.split('(?<=[\s,(%*/+-])(\$[0-9A-Fa-f]+|\d+)', (prefix or '(') + operation)
    for i in range(2 * int(skip_bit) + 1, len(elements), 2):
        p1, p2 = elements[i - 1][:-1].strip(), elements[i - 1][-1]
        if (p2 != '%' or not p1 or p1[-1] in ')"') and p2 != '"':
            p = elements[i]
            if hex_fmt is None and p.startswith('$'):
                elements[i] = str(int(p[1:], 16))
            elif hex_fmt and not p.startswith('$'):
                elements[i] = hex_fmt.format(int(p))
    return ''.join(elements)[1:]

def get_address(operation):
    search = re.search('(\A|[\s,(+-])(\$[0-9A-Fa-f]+|%[01]+|\d+)', operation)
    if search:
        return search.group(2)

def set_bytes(snapshot, address, operation):
    data = assemble(operation, address)
    snapshot[address:address + len(data)] = data
    return data

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

def parse_asm_data_directive(snapshot, directive):
    address, sep, values = directive[5:].partition(':')
    if sep:
        addr = parse_int(address)
        if addr is not None:
            operation = '{} {}'.format(directive[:4], partition_unquoted(values, ';')[0])
            set_bytes(snapshot, addr, operation)

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

def parse_address_range(value):
    addresses = [parse_int(n) for n in value.split('-', 1)]
    if len(addresses) == 1 and addresses[0] is not None:
        return addresses
    if len(addresses) == 2 and all(a is not None for a in addresses):
        return range(addresses[0], addresses[1] + 1)
    return ()

def _html_escape(text):
    return html.escape(text, False)

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

def _apply_ignores(ignores, section_ignores, index, line_no):
    for i in ignores:
        if i < line_no:
            ignores.remove(i)
            section_ignores[index] = True
            return

def _parse_registers(lines, mode, keep_lines):
    if keep_lines:
        if any(c for c in lines if c.strip() != '.'):
            return [('', '', lines)]
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
            registers.append((prefix, reg, ' '.join(desc_lines).lstrip()))
            desc_lines.clear()
        prefix = ''
        elements = s_line.split(None, 1)
        reg = elements[0]
        if len(elements) > 1:
            desc_lines.append(elements[1])
        else:
            desc_lines.append('')
        if ':' in reg:
            prefix, reg = reg.split(':', 1)
        if mode.lower:
            reg = reg.lower()
        elif mode.upper:
            reg = reg.upper()
    if desc_lines:
        registers.append((prefix, reg, ' '.join(desc_lines).lstrip()))
    return registers

def parse_comment_block(comments, ignores, mode, keep_lines=False):
    sections = [[], [], [], []]
    section_ignores = [False] * len(sections)
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
    mode.entry_ignoreua['t'] = section_ignores[0]
    mode.entry_ignoreua['d'] = section_ignores[1]
    mode.entry_ignoreua['r'] = section_ignores[2]
    mode.ignoremrcua = section_ignores[3]
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

def read_skool(skoolfile, asm=0, sub_mode=0, fix_mode=0):
    """Read a skool file and return each block as it's found.

    :param skoolfile: The file-like object to read.
    :param asm: 0 to read every line, and process no ASM block directives
                (sft); 1 to read every line, and process ASM block directives
                except in non-entry blocks (ctl); 2 to read every line, and
                process all ASM block directives (bin, html); or 3 to read
                lines only between @start and @end, and process all ASM block
                directives (asm).
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

        if asm > 0 and line.startswith('@'):
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

        if asm == 0:
            all_lines.append(s_line)
            lines.append(s_line)

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

class SkoolParser:
    """Parses a skool file.

    :param skoolfile: The name of the skool file to parse.
    :param case: 2 to force upper case, 1 to force lower case, or 0 to leave
                 case unchanged.
    :param base: 10 to force decimal, 16 to force hexadecimal, or 0 to leave
                 number bases unchanged.
    :param asm_mode: 0 to ignore ASM directives, 1 to parse them in `@isub`
                     mode, 2 to parse them in `@ssub` mode, or 3 to parse them
                     in `@rsub` mode. Add 4 to ignore @start and @end
                     directives.
    :param warnings: Whether to show warnings.
    :param fix_mode: 0 to apply no fixes, 1 to parse `@ofix` directives, 2 to
                     parse `@ofix` and `@bfix` directives, and 3 to parse
                     `@ofix`, `@bfix` and `@rfix` directives.
    :param html: Whether to escape HTML characters.
    :param create_labels: Whether to create default labels for unlabelled
                          instructions.
    :param asm_labels: Whether to parse `@label` directives.
    :param min_address: Ignore addresses below this one.
    :param max_address: Ignore addresses above this one.
    :param variables: List of 'name=value' strings defining variables that can
                      be used by `@if`, `#IF` and `#MAP`.
    :param snapshot: Base snapshot to use instead of an empty one.
    """
    def __init__(self, skoolfile, case=0, base=0, asm_mode=0, warnings=False, fix_mode=0, html=False,
                 create_labels=False, asm_labels=True, min_address=0, max_address=65536, variables=(),
                 snapshot=None):
        self.skoolfile = skoolfile
        self.mode = Mode(case, base, asm_mode & 3, warnings, fix_mode, html, create_labels, asm_labels)
        self.case = case
        self.base = base
        self.variables = variables
        self.fields = {
            'asm': asm_mode & 3,
            'base': base,
            'case': case,
            'fix': fix_mode,
            'html': int(html),
            'vars': self._get_vars()
        }
        self.snapshot = snapshot or [0] * 65536  # 64K of Spectrum memory
        self._instructions = {}                  # address -> [Instructions]
        self._entries = {}                       # address -> SkoolEntry
        self.memory_map = []                     # SkoolEntry instances
        self.base_address = 65536
        self.end_address = 0
        self.comments = []
        self.ignores = []
        self.asm_writer_class = None
        self.properties = {}
        self._replacements = []
        self.equs = []
        self._equ_values = {}

        with open_file(skoolfile) as f:
            self._parse_skool(f, asm_mode, min_address, max_address)

    def clone(self, skoolfile):
        return SkoolParser(
            skoolfile,
            self.case,
            self.base,
            self.mode.asm_mode,
            self.mode.warn,
            self.mode.fix_mode,
            self.mode.html,
            self.mode.create_labels,
            self.mode.asm_labels,
            snapshot=self.snapshot[:],
            variables=self.variables
        )

    def _get_vars(self):
        vars_dict = defaultdict(int)
        for name, sep, value in [v.partition('=') for v in self.variables]:
            if sep:
                vars_dict[name] = value
        return vars_dict

    def get_entry(self, address):
        """Return the routine or data block that starts at `address`."""
        return self._entries.get(address)

    def get_instruction(self, address, asm_id=''):
        """Return the instruction at `address`."""
        for instruction in self._instructions.get(address, ()):
            if instruction.container.asm_id.lower() == asm_id.lower():
                return instruction

    def get_container(self, address, asm_id):
        """Return the routine or data block that contains `address`."""
        instruction = self.get_instruction(address, asm_id)
        if instruction:
            return instruction.container

    def get_entry_point_refs(self, address):
        """Return the addresses of the routines and data blocks that contain
        instructions that refer to `address`.
        """
        return [referrer.address for referrer in self.get_instruction(address).referrers]

    def get_asm_label(self, address):
        instruction = self.get_instruction(address)
        if instruction:
            return instruction.asm_label

    def get_instruction_addr_str(self, address, default, asm_id=''):
        instruction = self.get_instruction(address, asm_id)
        if instruction:
            return instruction.get_addr_str()
        return self.mode.get_addr_str(address, default)

    def convert_operand(self, operand):
        operation = self.mode.apply_case('', 'DEFB ' + operand)[1]
        return self.mode.apply_base('', operation)[1][5:]

    def convert_address_operand(self, operand):
        return self.mode.convert_address_operand(operand)

    def _parse_skool(self, skoolfile, asm_mode, min_address, max_address):
        address_comments = []
        asm = 2 + int(1 <= asm_mode <= 3)
        non_entries = []
        for non_entry, block in read_skool(skoolfile, asm, self.mode.asm_mode, self.mode.fix_mode):
            removed = set()
            if non_entry:
                non_entries.append(self._parse_non_entry(block, removed))
                continue
            mid_block_comment = None
            instruction = None
            map_entry = None
            address_comments.append((None, None, None))
            self.ignores[:] = []
            for line in block:
                if line.startswith('@'):
                    self._parse_asm_directive(line[1:], removed)
                    continue

                if line.startswith(';'):
                    self.comments.append(line[1:])
                    self.mode.ignoreua = False
                    instruction = None
                    address_comments.append((None, None, None))
                    continue

                s_line = line.lstrip()
                if s_line.startswith(';'):
                    if map_entry and instruction:
                        # This is an instruction comment continuation line
                        address_comment[1].append(s_line[1:].lstrip())
                    continue

                # This line contains an instruction
                instruction, address_comment = self._parse_instruction(line)
                address = instruction.address
                addr_str = instruction.addr_str
                ctl = instruction.ctl
                if ctl in DIRECTIVES:
                    if address is None:
                        raise SkoolParsingError("Invalid address: '{}'".format(addr_str))
                    start_comment, desc, details, registers = parse_comment_block(self.comments, self.ignores, self.mode)
                    map_entry = SkoolEntry(address, addr_str, ctl, desc, details, registers)
                    mid_block_comment = start_comment
                    map_entry.ignoreua.update(self.mode.entry_ignoreua)
                    self.mode.reset_entry_ignoreua()
                    self.comments[:] = []
                    self.base_address = min((address, self.base_address))

                if map_entry:
                    address_comment = (instruction, [address_comment], [])
                    address_comments.append(address_comment)
                    if self.comments:
                        mid_block_comment = join_comments(self.comments, split=True)
                        self.comments[:] = []
                        self.mode.ignoremrcua = 0 in self.ignores
                    if address not in removed:
                        instruction.mid_block_comment = mid_block_comment
                        mid_block_comment = None
                        if address is not None:
                            self._instructions.setdefault(address, []).append(instruction)
                        map_entry.add_instruction(instruction)

                self.mode.apply_asm_attributes(instruction, map_entry, self._instructions, address_comments, removed)
                self.ignores[:] = []

                # Set bytes in the snapshot if the instruction is DEF{B,M,S,W}
                if address is not None:
                    operation = instruction.operation
                    if self.mode.assemble > 1 or (self.mode.assemble and operation.upper().startswith(('DEFB ', 'DEFM ', 'DEFS ', 'DEFW '))):
                        instruction.data = set_bytes(self.snapshot, address, operation)

            if map_entry and map_entry.instructions:
                self._entries[map_entry.address] = map_entry
                self.memory_map.append(map_entry)
                if self.comments:
                    map_entry.end_comment = join_comments(self.comments, split=True)
                    map_entry.ignoreua['e'] = len(self.ignores) > 0
                map_entry.headers = non_entries
                non_entries = []

            self.comments[:] = []

        if min_address > 0 or max_address < 65536:
            self.memory_map = [e for e in self.memory_map if min_address <= e.address < max_address]
            self._entries = {k: v for k, v in self._entries.items() if min_address <= k < max_address}
            if self._entries:
                self.base_address = min(self._entries)
                last_entry = self._entries[max(self._entries)]
                last_entry.instructions = [i for i in last_entry.instructions if i.address is None or i.address < max_address]
            else:
                self.base_address = max_address
            self._instructions = {k: v for k, v in self._instructions.items() if self.base_address <= k < max_address}
            address_comments = [c for c in address_comments if c[0] is None or c[0].address is None or self.base_address <= c[0].address < max_address]

        if self.memory_map:
            self.memory_map[-1].footers = non_entries
            end_address = max([i.address for e in self.memory_map for i in e.instructions if i.address is not None])
            last_instruction = self.get_instruction(end_address)
            self.end_address = end_address + (get_size(last_instruction.operation, end_address) or 1)

        # Do some post-processing
        parse_address_comments([c for c in address_comments if c[0] is None or c[0].container])
        self.make_replacements(self)
        if self.mode.html:
            for entry in self.memory_map:
                entry.apply_replacements(_html_escape)
        self._calculate_references()
        if self.mode.asm_labels:
            self._generate_labels()
        if self.mode.html:
            self._calculate_entry_sizes()
            self._escape_instructions()
        else:
            self._substitute_labels()

    def _parse_non_entry(self, block, removed):
        lines = []
        for line in block:
            if line.startswith('@'):
                self._parse_asm_directive(line[1:], removed)
            else:
                lines.append(line)
        self.mode.reset()
        return lines

    def _add_replacement(self, s):
        try:
            pattern, rep = s[1:].split(s[0])[:2]
            self._replacements.append((re.compile(pattern.replace('\\i', INTEGER)), rep))
        except (IndexError, ValueError):
            pass
        except re.error as e:
            raise SkoolParsingError("Failed to compile regular expression '{}': {}".format(pattern, e.args[0]))

    def apply_replacements(self, repf):
        for entry in self.memory_map:
            entry.apply_replacements(repf)

    def make_replacements(self, item):
        if self._replacements:
            item.apply_replacements(self._replace)

    def _replace(self, text):
        for regex, rep in self._replacements:
            try:
                text = regex.sub(rep, text)
            except re.error as e:
                raise SkoolParsingError("Failed to replace '{}' with '{}': {}".format(regex.pattern, rep, e.args[0]))
        return text

    def _parse_asm_directive(self, directive, removed):
        if directive.startswith('label='):
            self.mode.label = directive[6:].rstrip()
        elif directive.startswith(('defb=', 'defs=', 'defw=')):
            if self.mode.assemble:
                parse_asm_data_directive(self.snapshot, directive)
        elif directive.startswith('keep'):
            self.mode.keep = []
            if directive.startswith('keep='):
                for n in directive[5:].split(','):
                    addr = parse_int(n)
                    if addr is not None:
                        self.mode.keep.append(addr)
        elif directive.startswith('remote='):
            self._parse_remote_directive(directive[7:])
        elif directive.startswith('replace='):
            self._add_replacement(directive[8:])
        elif directive.startswith('assemble='):
            html_value, asm_value = [parse_int(i) for i in (directive[9:] + ',').split(',')][:2]
            if self.mode.html and html_value is not None:
                self.mode.assemble = html_value
            elif not (self.mode.html or asm_value is None):
                self.mode.assemble = asm_value
        elif directive.startswith('if('):
            try:
                self._parse_asm_directive(parse_if(self.fields, directive, 2)[1], removed)
            except MacroParsingError:
                pass
        elif self.mode.asm_mode:
            if directive.startswith(('isub=', 'ssub=', 'rsub=', 'ofix=', 'bfix=', 'rfix=')):
                value = directive[5:].rstrip()
                if value.startswith('!'):
                    if self.mode.weights[directive[:4]]:
                        removed.update(parse_address_range(value[1:]))
                else:
                    self.mode.add_sub(directive[:4], value)
            elif directive.startswith('nowarn'):
                self.mode.nowarn = True
            elif directive.startswith('ignoreua'):
                self.mode.ignoreua = True
                self.ignores.append(len(self.comments))
            elif directive.startswith('org'):
                self.mode.org = directive.rstrip().partition('=')[2]
            elif directive.startswith('writer='):
                self.asm_writer_class = directive[7:].rstrip()
            elif directive.startswith('set-'):
                name, sep, value = directive[4:].partition('=')
                if sep:
                    self.properties[name.lower()] = value
            elif directive.startswith('equ='):
                name, sep, value = directive[4:].rstrip().partition('=')
                if sep:
                    self.equs.append((name, value))
                    try:
                        self._equ_values[get_int_param(value)] = name
                    except ValueError:
                        pass

    def _parse_remote_directive(self, params):
        asm_id, sep, addresses = params.partition(':')
        addrs = addresses.split(',')
        address = parse_int(addrs[0])
        if address is not None:
            remote_entry = RemoteEntry(asm_id, address)
            addr_str = self.mode.apply_base(self.mode.apply_case(addrs[0])[0])[0]
            remote_entry.add_instruction(Instruction('r', addr_str, asm_id))
            for addr_str in addrs[1:]:
                addr_str = self.mode.apply_base(self.mode.apply_case(addr_str)[0])[0]
                remote_entry.add_instruction(Instruction(' ', addr_str, ''))
            for instruction in remote_entry.instructions:
                self._instructions.setdefault(instruction.address, []).append(instruction)

    def _parse_instruction(self, line):
        ctl, addr_str, operation, comment = parse_instruction(line)
        addr_str, operation = self.mode.apply_case(addr_str, operation)
        addr_str, operation = self.mode.apply_base(addr_str, operation)
        instruction = Instruction(ctl, addr_str, operation)
        return instruction, comment

    def _calculate_entry_sizes(self):
        for entry in self.memory_map:
            address = max([i.address for i in entry.instructions if i.address is not None])
            last_instruction = self.get_instruction(address)
            entry.size = address + (get_size(last_instruction.operation, address) or 1) - entry.address

    def _is_8_bit_ld_instruction(self, operation):
        if operation.startswith('LD '):
            ld_args = [arg.strip() for arg in operation[3:].split(',', 1)]
            if not set(ld_args) & {'A', 'BC', 'DE', 'HL', 'SP', 'IX', 'IY'}:
                return True
            if 'A' in ld_args:
                other_arg = ld_args[ld_args.index('A') - 1]
                if not other_arg.startswith('('):
                    return True
                other_arg = other_arg[1:].lstrip()
                if other_arg and other_arg[0] not in '$%0123456789':
                    return True
        return False

    def _calculate_references(self):
        # Parse operations for routine/data addresses
        for entry in self.memory_map:
            for instruction in entry.instructions:
                operation = instruction.operation.upper()
                if not operation.startswith(('CALL', 'DEFW', 'DJNZ', 'JP', 'JR', 'LD ', 'RST')) or self._is_8_bit_ld_instruction(operation):
                    continue
                addr_str = get_address(instruction.operation)
                if not addr_str:
                    continue
                address = parse_int(addr_str)
                if instruction.keep_value(address):
                    continue
                other_instruction = self._instructions.get(address, (None,))[0]
                if other_instruction:
                    other_entry = other_instruction.container
                    if other_entry.is_ignored():
                        continue
                    if other_entry.is_remote() or operation.startswith(('DEFW', 'LD ')) or other_entry.is_routine():
                        instruction.set_reference(other_entry, address, addr_str)
                        if operation.startswith(('CALL', 'DJNZ', 'JP', 'JR', 'RST')):
                            other_instruction.add_referrer(entry)

    def _escape_instructions(self):
        for entry in self.memory_map:
            for instruction in entry.instructions:
                instruction.html_escape()

    def warn(self, s):
        if self.mode.warn:
            warn(s)

    def _substitute_labels(self):
        for entry in self.memory_map:
            for instruction in entry.instructions:
                if not instruction.keep_values():
                    operation = instruction.operation
                    if operation.upper().startswith(('DEFB', 'DEFM', 'DEFW')):
                        operands = [self._replace_addresses(instruction, op) for op in split_unquoted(operation[5:], ',')]
                        instruction.operation = operation[:5] + ','.join(operands)
                    elif not operation.upper().startswith(('RST', 'DEFS')):
                        instruction.operation = self._replace_addresses(instruction, operation)

    def _generate_labels(self):
        """Generate labels for mid-routine entry points (based on the label of
           the main entry point)."""
        for entry in self._entries.values():
            instructions = entry.instructions
            if instructions:
                main_label = instructions[0].asm_label
                if self.mode.create_labels and (not main_label or main_label == '*'):
                    main_label = instructions[0].asm_label = 'L{0}'.format(entry.addr_str)
                if main_label:
                    index = 0
                    for instruction in instructions[1:]:
                        if instruction.ctl == '*' and instruction.asm_label is None or instruction.asm_label == '*':
                            instruction.asm_label = '{0}_{1}'.format(main_label, index)
                            index += 1

    def _replace_addresses(self, instruction, operand):
        rep = ''
        for p in split_quoted(operand):
            if not p.startswith('"'):
                pieces = re.split('(\A|(?<=[\s,(+-]))(\$[0-9A-Fa-f]+|%[01]+|\d+)', p)
                for i in range(2, len(pieces), 3):
                    label = self._get_label(instruction, pieces[i])
                    if label:
                        pieces[i] = label
                p = ''.join(pieces)
            rep += p
        return rep

    def _get_label(self, instruction, addr_str):
        operation_u = instruction.operation.upper()
        address = get_int_param(addr_str)
        if instruction.keep_value(address):
            return
        if address < 256 and (not operation_u.startswith(('CALL', 'DEFW', 'DJNZ', 'JP', 'JR', 'LD '))
                              or self._is_8_bit_ld_instruction(operation_u)):
            return
        label_warn = instruction.sub is None and instruction.warn
        reference = self.get_instruction(address)
        if reference:
            if reference.asm_label:
                if reference.is_in_routine() and label_warn and operation_u.startswith('LD '):
                    # Warn if a LD operand is replaced with a routine label in
                    # an unsubbed operation (will need @keep to retain operand,
                    # or @nowarn if the replacement is OK)
                    rep = instruction.operation.replace(addr_str, reference.asm_label)
                    self.warn('LD operand replaced with routine label in unsubbed operation:\n  {} {} -> {}'.format(instruction.addr_str, instruction.operation, rep))
                return reference.asm_label
            if instruction.warn and instruction.is_in_routine():
                # Warn if we cannot find a label to replace the operand of this
                # routine instruction (will need @nowarn if this is OK)
                self.warn('Found no label for operand: {} {}'.format(instruction.addr_str, instruction.operation))
        elif address in self._equ_values:
            return self._equ_values[address]
        else:
            references = self._instructions.get(address)
            is_local = not (references and references[0].container.is_remote())
            if is_local and label_warn and self.mode.asm_mode > 1 and self.base_address <= address < self.end_address:
                # Warn if the operand is inside the address range of the
                # disassembly (where code might be) but doesn't refer to the
                # address of an instruction (will need @nowarn if this is OK)
                self.warn('Unreplaced operand: {} {}'.format(instruction.addr_str, instruction.operation))

class Mode:
    def __init__(self, case, base, asm_mode, warnings, fix_mode, html, create_labels, asm_labels):
        self.lower = case == CASE_LOWER
        self.upper = case == CASE_UPPER
        self.decimal = base == BASE_10
        self.hexadecimal = base == BASE_16
        self.html = html
        self.asm_mode = asm_mode
        self.warn = warnings
        self.assemble = int(html)
        self.fix_mode = fix_mode
        self.labels = []
        self.create_labels = create_labels
        self.asm_labels = asm_labels
        self.entry_ignoreua = {}
        if self.lower:
            self.hex2fmt = '${0:02x}'
            self.hex4fmt = '${0:04x}'
            self.addr_fmt = '{0:04x}'
        else:
            self.hex2fmt = '${0:02X}'
            self.hex4fmt = '${0:04X}'
            self.addr_fmt = '{0:04X}'
        self.weights = {
            'isub': int(asm_mode > 0),
            'ssub': 2 * int(asm_mode > 1),
            'rsub': 3 * int(asm_mode > 2),
            'ofix': 4 * int(fix_mode > 0),
            'bfix': 5 * int(fix_mode > 1),
            'rfix': 6 * int(fix_mode > 2)
        }
        self.reset()
        self.reset_entry_ignoreua()

    def reset(self):
        self.label = None
        self.subs = defaultdict(list, {0: ()})
        self.keep = None
        self.nowarn = False
        self.ignoreua = False
        self.ignoremrcua = False
        self.org = None

    def reset_entry_ignoreua(self):
        for section in 'tdr':
            self.entry_ignoreua[section] = False

    def add_sub(self, directive, value):
        weight = self.weights[directive]
        if weight:
            self.subs[weight].append(value)

    def compose_instructions(self, subs, current=False):
        instructions = []
        for flags, label, op, comment in subs:
            if flags.append and not instructions:
                instructions.append((False, None, '', [None]))
            op = self.apply_base('', self.apply_case('', op)[1])[1]
            if op or (current and not instructions):
                instructions.append((flags.overwrite, label, op, [comment]))
            elif instructions:
                instructions[-1][-1].append(comment)
            if flags.final and instructions:
                instructions[-1][-1].append(None)
        return instructions

    def process_label(self, instruction, label, removed=None):
        if label and label.startswith('*'):
            if len(label) > 1:
                label = label[1:]
            elif not self.create_labels:
                label = None
            instruction.ctl = '*'
        elif label == '':
            instruction.ctl = ' '
        if self.asm_labels:
            if label and label != '*':
                if label in self.labels:
                    raise SkoolParsingError('Duplicate label {} at {}'.format(label, instruction.address))
                if removed is None or instruction.address not in removed:
                    self.labels.append(label)
            instruction.asm_label = label

    def process_instruction(self, instruction, label, overwrite=False, removed=None):
        if label is not None:
            self.process_label(instruction, label)
        if overwrite:
            size = get_size(instruction.operation, instruction.address)
            if size:
                removed.update(range(instruction.address, instruction.address + size))
                return instruction.address + size

    def apply_asm_attributes(self, instruction, map_entry, instructions, address_comments, removed):
        instruction.keep = self.keep

        self.process_label(instruction, self.label, removed)

        if self.asm_mode:
            if self.org != '':
                instruction.org = self.org
            instruction.warn = not self.nowarn
            instruction.ignoreua = self.ignoreua
            instruction.ignoremrcua = self.ignoremrcua

            parsed = [parse_asm_sub_fix_directive(d) for d in self.subs[max(self.subs)]]
            before = self.compose_instructions(s for s in parsed if s[0].prepend)
            after = self.compose_instructions((s for s in parsed if not s[0].prepend), True)

            for overwrite, label, op, comments in before:
                inst = Instruction(' ', '     ', op)
                map_entry.add_instruction(inst, True)
                address_comments.insert(len(address_comments) - 1, (inst, [], comments))
                self.process_instruction(inst, label)

            address = instruction.address
            if after:
                overwrite, label, op, comments = after.pop(0)
                if op:
                    instruction.sub = instruction.operation = op
                if comments[0] is None:
                    comments[0] = address_comments[-1][1][0]
                address_comments[-1][2].extend(comments)
                address = self.process_instruction(instruction, label, overwrite, removed)

            for overwrite, label, op, comments in after:
                if overwrite:
                    if address is None:
                        raise SkoolParsingError("Cannot determine address of instruction after '{} {}'".format(instruction.addr_str, instruction.operation))
                    addr_str = self.apply_base(self.apply_case(str(address))[0])[0]
                    instruction = Instruction(' ', addr_str, op)
                    if address not in removed:
                        instructions.setdefault(address, []).append(instruction)
                        map_entry.add_instruction(instruction)
                else:
                    instruction = Instruction(' ', '     ', op)
                    map_entry.add_instruction(instruction)
                address_comments.append((instruction, [], comments))
                address = self.process_instruction(instruction, label, overwrite, removed)

        self.reset()

    def get_addr_str(self, address, default):
        if self.hexadecimal:
            return self.addr_fmt.format(address)
        if self.decimal:
            return str(address)
        if default.startswith('$'):
            return default[1:]
        return default

    def convert_address_operand(self, operand):
        if self.decimal:
            return str(parse_int(operand))
        if self.hexadecimal:
            return self.hex4fmt.format(parse_int(operand))
        return operand

    def apply_case(self, addr_str, operation=''):
        if self.lower:
            addr_str = addr_str.lower()
        elif self.upper:
            addr_str = addr_str.upper()
        if self.lower or self.upper:
            operation = convert_case(operation, self.lower)
            if self.upper and not operation.startswith(('DEFB', 'DEFM', 'DEFS', 'DEFW')):
                operation = re.sub('(I[XY])H', r'\1h', operation)
                operation = re.sub('(I[XY])L', r'\1l', operation)
        return addr_str, operation

    def apply_base(self, addr_str, operation=''):
        address = parse_int(addr_str)
        if self.decimal:
            if address is not None:
                addr_str = '{:05d}'.format(address)
            if operation:
                operation = self.convert(operation)
        elif self.hexadecimal:
            if address is not None:
                addr_str = self.hex4fmt.format(address)
            if operation:
                operation = self.convert(operation, self.hex2fmt, self.hex4fmt)
        return addr_str, operation

    def convert(self, operation, hex2fmt=None, hex4fmt=None):
        if operation.upper().startswith(('DEFB ', 'DEFM ', 'DEFS ', 'DEFW ')):
            if operation.upper().startswith('DEFW'):
                hex_fmt = hex4fmt
            else:
                hex_fmt = hex2fmt
            converted = operation[:4]
            prefix = None
            for p in split_quoted(operation[4:]):
                if p.startswith('"'):
                    converted += p
                    prefix = '"'
                else:
                    converted += _replace_nums(p, hex_fmt, prefix=prefix)
                    prefix = None
            return converted

        elements = split_operation(operation, tidy=True)
        op = elements[0]

        # Instructions containing '(I[XY]+d)'
        if re.search('\(I[XY] *[+-].*\)', operation.upper()):
            return _replace_nums(operation, hex2fmt, op in ('BIT', 'RES', 'SET'))

        if op in ('CALL', 'DJNZ', 'JP', 'JR'):
            return _replace_nums(operation, hex4fmt)

        if op in ('AND', 'OR', 'XOR', 'SUB', 'CP', 'IN', 'OUT', 'ADD', 'ADC', 'SBC', 'RST'):
            return _replace_nums(operation, hex2fmt)

        if op == 'LD' and len(elements) == 3:
            operands = elements[1:]
            if operands[0] in ('A', 'B', 'C', 'D', 'E', 'H', 'L', 'IXL', 'IXH', 'IYL', 'IYH', '(HL)') and not operands[1].startswith('('):
                # LD r,n; LD (HL),n
                return _replace_nums(operation, hex2fmt)
            if not set(('A', 'BC', 'DE', 'HL', 'IX', 'IY', 'SP')).isdisjoint(operands):
                # LD A,(nn); LD (nn),A; LD rr,nn; LD rr,(nn); LD (nn),rr
                return _replace_nums(operation, hex4fmt)

        return operation

class Instruction:
    def __init__(self, ctl, addr_str, operation):
        self.ctl = ctl
        if addr_str.startswith('$'):
            self.addr_str = addr_str[1:]
            self.addr_base = BASE_16
        else:
            self.addr_str = addr_str
            self.addr_base = BASE_10
        self.address = parse_int(addr_str)
        self.operation = operation
        self.data = ()
        self.container = None
        self.reference = None
        self.mid_block_comment = None
        self.comment = None
        self.referrers = []
        self.asm_label = None
        self.org = addr_str
        # If this instruction has no address, it was inserted between
        # @rsub+begin and @rsub+end; in that case, mark it as a subbed
        # instruction already
        if self.address is None:
            self.sub = operation
        else:
            self.sub = None
        self.keep = None
        self.warn = True
        self.ignoreua = False
        self.ignoremrcua = False

    def set_comment(self, rowspan, text):
        self.comment = Comment(rowspan, text)

    def set_reference(self, entry, address, addr_str):
        self.reference = Reference(entry, address, addr_str)

    def add_referrer(self, routine):
        if routine not in self.referrers:
            self.referrers.append(routine)
        self.container.add_referrer(routine)

    def is_in_routine(self):
        return self.container.is_routine()

    def html_escape(self):
        self.operation = html.escape(self.operation, False)

    def get_addr_str(self):
        if self.addr_base == BASE_10:
            return re.sub('^0{1,4}', '', self.addr_str)
        return self.addr_str

    def apply_replacements(self, repf):
        if self.mid_block_comment:
            self.mid_block_comment = [repf(p) for p in self.mid_block_comment]
        if self.comment:
            self.comment.apply_replacements(repf)

    def keep_values(self):
        return self.keep == []

    def keep_value(self, value):
        return self.keep_values() or (self.keep and value in self.keep)

class Reference:
    def __init__(self, entry, address, addr_str):
        self.entry = entry
        self.address = address
        self.addr_str = addr_str

class Comment:
    def __init__(self, rowspan, text):
        self.rowspan = rowspan
        self.text = text

    def apply_replacements(self, repf):
        self.text = repf(self.text)

class SkoolEntry:
    def __init__(self, address, addr_str=None, ctl=None, description=None, details=(), registers=()):
        self.headers = ()
        self.footers = ()
        self.asm_id = ''
        self.address = address
        self.addr_str = addr_str
        self.ctl = ctl
        self.description = description
        self.details = details
        self.registers = [Register(prefix, name, contents) for prefix, name, contents in registers]
        self.instructions = []
        self.end_comment = ()
        self.referrers = []
        self.size = None
        self.ignoreua = {'t': False, 'd': False, 'r': False, 'e': False}

    def is_routine(self):
        """Return whether the entry is a routine (code block)."""
        return self.ctl == 'c'

    def is_remote(self):
        """Return whether the entry is a remote entry."""
        return False

    def is_ignored(self):
        return self.ctl == 'i'

    def add_instruction(self, instruction, insert=False):
        instruction.container = self
        if insert:
            index = len(self.instructions) - 1
            if index:
                instruction.org = None
            else:
                instruction.org = self.instructions[0].org
            instruction.mid_block_comment = self.instructions[index].mid_block_comment
            self.instructions[index].mid_block_comment = None
            self.instructions.insert(index, instruction)
        else:
            self.instructions.append(instruction)

    def add_referrer(self, routine):
        if routine not in self.referrers:
            self.referrers.append(routine)

    def apply_replacements(self, repf):
        self.description = repf(self.description)
        self.details = [repf(p) for p in self.details]
        for reg in self.registers:
            reg.apply_replacements(repf)
        for i in self.instructions:
            i.apply_replacements(repf)
        self.end_comment = [repf(p) for p in self.end_comment]

class RemoteEntry(SkoolEntry):
    def __init__(self, asm_id, address):
        SkoolEntry.__init__(self, address)
        self.asm_id = asm_id

    def is_remote(self):
        return True

class Register:
    def __init__(self, prefix, name, contents):
        self.prefix = prefix
        self.name = name
        self.contents = contents

    def apply_replacements(self, repf):
        self.contents = repf(self.contents)

class TableParser:
    def parse_text(self, writer, text, index, *cwd):
        try:
            end = text.index(TABLE_END_MARKER, index) + len(TABLE_END_MARKER)
        except ValueError:
            marker = text[text.rindex('#', 0, index):index]
            raise SkoolParsingError("Missing table end marker: {}{}...".format(marker, text[index:index + 15]))
        return end, self.parse_table(writer, text[index:end], *cwd)

    def parse_table(self, writer, table_def, *cwd):
        text = table_def
        for ws_char in '\n\r\t':
            text = text.replace(ws_char, ' ')

        try:
            index, params = parse_brackets(text, default='')
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

        text = writer.expand(text[index:], *cwd)
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
        self.cell_padding = None
        self.num_cols = None

    def add_row(self, cells):
        self.rows.append(cells)
        self.cells.extend(cells)

    def prepare_cells(self):
        # For each cell, set row_index and col_index, and convert the contents
        # to a 1-item list. Also calculate num_cols and col_widths.
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

        if self.rows:
            self.num_cols = 1 + max([cell.col_index for cell in [row[-1] for row in self.rows]])
        else:
            self.num_cols = 0
        self._calculate_col_widths()

    def get_header_rows(self):
        headers = []
        for i, row in enumerate(self.rows):
            if len([c for c in row if not (c.transparent or c.header)]) == 0:
                headers.append(i)
        return headers

    def get_cell_width(self, col_index, colspan):
        return sum(self.col_widths[col_index:col_index + colspan]) + self.cell_padding * (colspan - 1)

    def _calculate_col_widths(self):
        # Loop over the cells to collect their widths (considering only those
        # cells with colspan=1 on this pass)
        cell_widths = [[0] * self.num_cols for row in self.rows]
        for cell in [c for c in self.cells if c.colspan == 1]:
            cell_widths[cell.row_index][cell.col_index] = cell.get_width()

        # Scan each column to find the widest cell; the width of that cell will
        # be the width of the column
        self.col_widths = [max([row[i] for row in cell_widths]) for i in range(self.num_cols)]

        # Scan the cells again to make sure that those with colspan > 1 have
        # enough space
        for cell in [c for c in self.cells if c.colspan > 1]:
            col_index, colspan = cell.col_index, cell.colspan
            space_needed = cell.get_width() - self.get_cell_width(col_index, colspan)
            while space_needed > 0:
                for j in range(colspan):
                    if space_needed > 0:
                        self.col_widths[col_index + j] += 1
                        space_needed -= 1

    def reduce_width(self, max_table_width, min_col_width):
        # Reduce the width of the wrappable columns until either the table is
        # narrow enough or all the wrappable columns are the minimum width
        done = False
        while self.get_width() > max_table_width and not done:
            done = True
            for wrap_col in self.wrap_columns:
                if self.col_widths[wrap_col] > min_col_width:
                    self.col_widths[wrap_col] -= 1
                    done = False

        # Wrap the contents of the cells in the wrappable columns
        for cell in [c for c in self.cells if c.col_index in self.wrap_columns]:
            width = self.get_cell_width(cell.col_index, cell.colspan)
            cell.contents = wrap(cell.contents[0], width) or ['']

        # The column widths need to be recalculated now
        self._calculate_col_widths()

    def get_width(self):
        padding = self.cell_padding * (self.num_cols + 1) - 2
        return padding + sum(self.col_widths)

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
