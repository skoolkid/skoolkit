# -*- coding: utf-8 -*-

# Copyright 2016 Richard Dymond (rjdymond@gmail.com) and Philip M. Anderson
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

def get_number(snapshot, i):
    if snapshot[i] == 0:
        # Small integer (signed)
        num = _get_integer(snapshot, i)
    else:
        # Floating point number (signed)
        num = _get_float(snapshot, i)
    return num

def _get_integer(snapshot, i):
    # See ZX Spectrum ROM routine INT_FETCH at 0x2D7F
    sign = snapshot[i + 1]
    lsb = (snapshot[i + 2] ^ sign) - sign
    if lsb < 0:
        lsb += 256
        carry = 1
    else:
        carry = 0

    msb = ((snapshot[i + 3] + sign + carry) & 255) ^ sign

    num = 256 * msb + lsb
    if (sign & 128) != 0:
        num *= -1

    return num

def _get_float(snapshot, i):
    exponent = snapshot[i] - 160
    if (snapshot[i + 1] & 128) == 0:
        sign = 1
    else:
        sign = -1
    mantissa = float(16777216 * (snapshot[i + 1] | 128)
                     + 65536 * snapshot[i + 2]
                     + 256 * snapshot[i + 3]
                     + snapshot[i + 4])
    num = sign * mantissa * (2 ** exponent)
    return num

class TextReader:
    def __init__(self):
        self.lspace = False

    def get_chars(self, code):
        if code <= 32:
            self.lspace = False
            return self._get_char(code)
        if code <= 164:
            self.lspace = True
            return self._get_char(code)
        return self._get_token(code)

    def _get_char(self, code):
        if code == 94:
            return '↑'
        if code == 96:
            return '£'
        if code == 127:
            return '©'
        if 32 <= code <= 126:
            return chr(code)
        return '{{0x{:02X}}}'.format(code)

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
        lines = ['Basic listing:']
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
            num = get_number(self.snapshot, i + 1)
            if num and abs(1 - float(num_str) / num) > 1e-9:
                return '{{{}}}'.format(num)
        return ''

    def _get_num_str(self, j):
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
        lines = ['Variables:']
        self.snapshot = snapshot
        i = (snapshot[23627] + 256 * snapshot[23628]) or 23755
        while i < len(snapshot) and snapshot[i] != 128:
            self.text.lspace = False
            variable_type = (snapshot[i] & 224)
            if variable_type == 64:
                # String (010xxxxx)
                i, line = self._get_string_var(i)
            elif variable_type == 128:
                # Array of numbers (100xxxxx)
                i, line = self._get_num_array_var(i)
            elif variable_type == 160:
                # Number whose name is longer than one letter (101xxxxx)
                i, line = self._get_long_num_var(i)
            elif variable_type == 192:
                # Array of characters (110xxxxx)
                i, line = self._get_char_array_var(i)
            elif variable_type == 224:
                # Control variable of a FOR-NEXT loop (111xxxxx)
                i, line = self._get_control_var(i)
            elif variable_type == 96:
                # Number whose name is one letter (011xxxxx)
                i, line = self._get_short_num_var(i)
            else:
                # Basic line (000xxxxx / 001xxxxx)
                i, line = self._skip_basic_line(i)
            if line != '':
                lines.append('{}'.format(line))
        return '\n'.join(lines)

    def _get_string_var(self, i):
        line = '(String) '
        letter = (self.snapshot[i] & 31) + 96
        line += "{}$=\"".format(self.text.get_chars(letter))
        str_length = get_word(self.snapshot, i + 1)
        i += 3
        while str_length > 0:
            self.text.lspace = True
            code = self.snapshot[i]
            line += self.text.get_chars(code)
            str_length -= 1
            i += 1
        line += '"'
        return i, line

    def _get_num_array_var(self, i):
        line = '(Number array) '
        letter = (self.snapshot[i] & 31) + 96
        line += "{}(".format(self.text.get_chars(letter))
        data_length = get_word(self.snapshot, i + 1) - 1
        dimensions = self.snapshot[i + 3]
        i += 4
        dimension_lengths = []
        for x in range(0, dimensions):
            dimension_length = get_word(self.snapshot, i)
            i += 2
            data_length -= 2
            line += '{}'.format(dimension_length)
            if x < (dimensions - 1):
                line += ','
        line += ')=['
        while data_length > 0:
            line += '{}'.format(get_number(self.snapshot, i))
            i += 5
            data_length -= 5
            if data_length > 0:
                line += ','
        line += ']'
        return i,line

    def _get_long_num_var(self, i):
        line = '(Number) '
        letter = (self.snapshot[i] & 31) + 96
        letters = '{}'.format(self.text.get_chars(letter))
        i += 1
        letter = self.snapshot[i]
        while (letter & 128) == 0:
            letters += '{}'.format(self.text.get_chars(letter))
            i += 1
            letter = self.snapshot[i]
        letters += '{}'.format(self.text.get_chars(letter & 127))
        i += 1
        line += letters + "={}".format(get_number(self.snapshot, i))
        i += 5
        return i, line

    def _get_char_array_var(self, i):
        line = '(Character array) '
        letter = (self.snapshot[i] & 31) + 96
        line += "{}$(".format(self.text.get_chars(letter))
        data_length = get_word(self.snapshot, i + 1) - 1
        dimensions = self.snapshot[i + 3]
        i += 4
        dimension_lengths = []
        for x in range(0, dimensions):
            dimension_length = get_word(self.snapshot, i)
            i += 2
            data_length -= 2
            line += '{}'.format(dimension_length)
            if x < (dimensions - 1):
                line += ','
        line += ')=['
        while data_length > 0:
            line += '"{}"'.format(self.text.get_chars(self.snapshot[i]))
            i += 1
            data_length -= 1
            if data_length > 0:
                line += ','
        line += ']'
        return i,line

    def _get_control_var(self, i):
        line = '(FOR control variable) '
        letter = (self.snapshot[i] & 31) + 96
        line += "{}=".format(self.text.get_chars(letter))
        i += 1
        line += "{} (".format(get_number(self.snapshot, i))
        i += 5
        line += 'limit={}, '.format(get_number(self.snapshot, i))
        i += 5
        line += 'step={}, '.format(get_number(self.snapshot, i))
        i += 5
        line += 'line={}, '.format(get_word(self.snapshot, i))
        i += 2
        line += 'statement={})'.format(self.snapshot[i])
        i += 1
        return i,line

    def _get_short_num_var(self, i):
        line = '(Number) '
        letter = (self.snapshot[i] & 31) + 96
        line += '{}='.format(self.text.get_chars(letter))
        i += 1
        line += "{}".format(get_number(self.snapshot, i))
        i += 5
        return i, line

    def _skip_basic_line(self, i):
        line = ''
        i += 2
        line_length = get_word(self.snapshot, i)
        i += line_length + 2
        return i, line
