# Copyright 2016-2017 Richard Dymond (rjdymond@gmail.com), Philip M. Anderson
# (weyoun47@gmail.com)
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

from skoolkit import get_word

TOKENS = {
    165: 'RND',
    166: 'INKEY$',
    167: 'PI',
    168: 'FN',
    169: 'POINT',
    170: 'SCREEN$',
    171: 'ATTR',
    172: 'AT',
    173: 'TAB',
    174: 'VAL$',
    175: 'CODE',
    176: 'VAL',
    177: 'LEN',
    178: 'SIN',
    179: 'COS',
    180: 'TAN',
    181: 'ASN',
    182: 'ACS',
    183: 'ATN',
    184: 'LN',
    185: 'EXP',
    186: 'INT',
    187: 'SQR',
    188: 'SGN',
    189: 'ABS',
    190: 'PEEK',
    191: 'IN',
    192: 'USR',
    193: 'STR$',
    194: 'CHR$',
    195: 'NOT',
    196: 'BIN',
    197: 'OR',
    198: 'AND',
    199: '<=',
    200: '>=',
    201: '<>',
    202: 'LINE',
    203: 'THEN',
    204: 'TO',
    205: 'STEP',
    206: 'DEF FN',
    207: 'CAT',
    208: 'FORMAT',
    209: 'MOVE',
    210: 'ERASE',
    211: 'OPEN #',
    212: 'CLOSE #',
    213: 'MERGE',
    214: 'VERIFY',
    215: 'BEEP',
    216: 'CIRCLE',
    217: 'INK',
    218: 'PAPER',
    219: 'FLASH',
    220: 'BRIGHT',
    221: 'INVERSE',
    222: 'OVER',
    223: 'OUT',
    224: 'LPRINT',
    225: 'LLIST',
    226: 'STOP',
    227: 'READ',
    228: 'DATA',
    229: 'RESTORE',
    230: 'NEW',
    231: 'BORDER',
    232: 'CONTINUE',
    233: 'DIM',
    234: 'REM',
    235: 'FOR',
    236: 'GO TO',
    237: 'GO SUB',
    238: 'INPUT',
    239: 'LOAD',
    240: 'LIST',
    241: 'LET',
    242: 'PAUSE',
    243: 'NEXT',
    244: 'POKE',
    245: 'PRINT',
    246: 'PLOT',
    247: 'RUN',
    248: 'SAVE',
    249: 'RANDOMIZE',
    250: 'IF',
    251: 'CLS',
    252: 'DRAW',
    253: 'CLEAR',
    254: 'RETURN',
    255: 'COPY'
}

def get_char(code, u_fmt='{{0x{:02X}}}', udg_fmt='{{UDG-{}}}', tokens=False):
    if code == 94:
        return '↑'
    if code == 96:
        return '£'
    if code == 127:
        return '©'
    if 32 <= code <= 126:
        return chr(code)
    if 144 <= code <= 164:
        return udg_fmt.format(chr(code - 79))
    if code >= 165 and tokens:
        return TOKENS[code]
    return u_fmt.format(code)

def _get_number(snapshot, i):
    if snapshot[i]:
        return _get_float(snapshot, i)
    return _get_integer(snapshot, i)

def _get_integer(snapshot, i):
    if snapshot[i + 1]:
        return get_word(snapshot, i + 2) - 65536
    return get_word(snapshot, i + 2)

def _get_float(snapshot, i):
    exponent = snapshot[i] - 160
    sign = -1 if snapshot[i + 1] & 128 else 1
    mantissa = float(16777216 * (snapshot[i + 1] | 128)
                     + 65536 * snapshot[i + 2]
                     + 256 * snapshot[i + 3]
                     + snapshot[i + 4])
    return sign * mantissa * (2 ** exponent)

def _unflatten(values, dimensions):
    for d in reversed(dimensions[1:]):
        values = [values[i:i + d] for i in range(0, len(values), d)]
    return values

class TextReader:
    def __init__(self):
        self.lspace = False

    def get_chars(self, code):
        if code <= 32:
            self.lspace = False
            return get_char(code)
        if code <= 164:
            self.lspace = True
            return get_char(code)
        return self._get_token(code)

    def _get_token(self, code):
        token = TOKENS[code]
        if self.lspace and code >= 197 and token[0] >= 'A':
            token = ' ' + token
        self.lspace = True
        if code < 168 or code == 203 or token[-1] in '#=>':
            # RND, INKEY$, PI, THEN, '<=', '>=', '<>', 'OPEN #', 'CLOSE #'
            return token
        self.lspace = False
        return token + ' '

class BasicLister:
    def __init__(self):
        self.text = TextReader()

    def list_basic(self, snapshot):
        lines = []
        self.snapshot = snapshot
        i = (snapshot[23635] + 256 * snapshot[23636]) or 23755
        while i < len(snapshot) and snapshot[i] < 64:
            line_no = snapshot[i] * 256 + snapshot[i + 1]
            self.text.lspace = False
            i, line = self._get_basic_line(i + 4)
            lines.append('{:>4} {}'.format(line_no, line))
        return '\n'.join(lines)

    def _get_basic_line(self, i):
        line = ''
        while i < len(self.snapshot) and self.snapshot[i] != 13:
            code = self.snapshot[i]
            if code == 14:
                if i + 5 < len(self.snapshot):
                    line += self._get_fp_num(i)
                    i += 6
                else:
                    while i < len(self.snapshot):
                        line += '{{0x{:02X}}}'.format(self.snapshot[i])
                        i += 1
            elif 16 <= code <= 21 and i + 1 < len(self.snapshot):
                line += '{{0x{:02X}{:02X}}}'.format(code, self.snapshot[i + 1])
                i += 2
            elif 22 <= code <= 23 and i + 2 < len(self.snapshot):
                line += '{{0x{:02X}{:02X}{:02X}}}'.format(code, self.snapshot[i + 1], self.snapshot[i + 2])
                i += 3
            else:
                line += self.text.get_chars(code)
                i += 1
        return i + 1, line

    def _get_fp_num(self, i):
        num_str = self._get_num_str(i - 1)
        if num_str:
            num = _get_number(self.snapshot, i + 1)
            str_val = float(num_str)
            if num:
                delta = abs(1 - str_val / num)
            else:
                delta = abs(str_val)
            if delta > 1e-9:
                return '{{{}}}'.format(num)
        return ''

    def _get_num_str(self, j):
        while self.snapshot[j] < 33:
            j -= 1
        num_str = chr(self.snapshot[j])
        while re.match('[0-9.]+([eE][-+]?[0-9]+)?', num_str):
            j -= 1
            this_chr = chr(self.snapshot[j])
            signed = this_chr in '+-'
            if signed:
                num_str = this_chr + num_str
                j -= 1
                this_chr = chr(self.snapshot[j])
            if this_chr in 'eE':
                num_str = this_chr + num_str
                j -= 1
            elif signed:
                break
            num_str = chr(self.snapshot[j]) + num_str
        return num_str[1:]

class VariableLister:
    def __init__(self):
        self.text = TextReader()

    def list_variables(self, snapshot):
        lines = []
        self.snapshot = snapshot
        i = snapshot[23627] + 256 * snapshot[23628]
        while i < len(snapshot) and snapshot[i] != 128:
            self.text.lspace = True
            varname = chr((snapshot[i] & 31) + 96)
            variable_type = snapshot[i] & 224
            if variable_type == 64:
                # String (010xxxxx)
                i, line = self._get_string_var(varname, i)
            elif variable_type == 128:
                # Array of numbers (100xxxxx)
                i, line = self._get_num_array_var(varname, i)
            elif variable_type == 160:
                # Number whose name is longer than one letter (101xxxxx)
                i, line = self._get_long_num_var(varname, i)
            elif variable_type == 192:
                # Array of characters (110xxxxx)
                i, line = self._get_char_array_var(varname, i)
            elif variable_type == 224:
                # Control variable of a FOR-NEXT loop (111xxxxx)
                i, line = self._get_control_var(varname, i)
            elif variable_type == 96:
                # Number whose name is one letter (011xxxxx)
                i, line = self._get_short_num_var(varname, i)
            else:
                # Basic line (00xxxxxx)
                i += get_word(snapshot, i + 2) + 4
                continue
            lines.append(line)
        return '\n'.join(lines)

    def _get_string_var(self, name, i):
        end = i + 3 + get_word(self.snapshot, i + 1)
        value = ''.join([self.text.get_chars(c) for c in self.snapshot[i + 3:end]])
        line = '{}$="{}"'.format(name, value)
        return end, line

    def _get_num_array_var(self, name, i):
        v_start = i + 4 + 2 * self.snapshot[i + 3]
        v_end = i + 3 + get_word(self.snapshot, i + 1)
        dims = [get_word(self.snapshot, c) for c in range(i + 4, v_start, 2)]
        dims_str = ','.join([str(d) for d in dims])
        values = _unflatten([_get_number(self.snapshot, c) for c in range(v_start, v_end, 5)], dims)
        line = '{}({})={}'.format(name, dims_str, values)
        return v_end, line

    def _get_long_num_var(self, name, i):
        j = i + 1
        while self.snapshot[j] < 128:
            j += 1
        name += ''.join([chr(self.snapshot[k] & 127) for k in range(i + 1, j + 1)])
        line = '{}={}'.format(name, _get_number(self.snapshot, j + 1))
        return j + 6, line

    def _get_char_array_var(self, name, i):
        v_start = i + 4 + 2 * self.snapshot[i + 3]
        v_end = i + 3 + get_word(self.snapshot, i + 1)
        dims = [get_word(self.snapshot, c) for c in range(i + 4, v_start, 2)]
        dims_str = ','.join([str(d) for d in dims])
        str_len = dims[-1]
        strings = [''.join([self.text.get_chars(self.snapshot[k]) for k in range(j, j + str_len)]) for j in range(v_start, v_end, str_len)]
        if len(dims) > 1:
            values = _unflatten(strings, dims[:-1])
        else:
            values = strings[0]
        line = '{}$({})={!r}'.format(name, dims_str, values)
        return v_end, line

    def _get_control_var(self, name, i):
        value = _get_number(self.snapshot, i + 1)
        limit = _get_number(self.snapshot, i + 6)
        step = _get_number(self.snapshot, i + 11)
        line_number = get_word(self.snapshot, i + 16)
        statement = self.snapshot[i + 18]
        line = '{}={} (limit={}, step={}, line={}, statement={})'.format(name, value, limit, step, line_number, statement)
        return i + 19, line

    def _get_short_num_var(self, name, i):
        line = '{}={}'.format(name, _get_number(self.snapshot, i + 1))
        return i + 6, line
