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
