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

from skoolkit.numberutils import get_number
from skoolkit.text import TextReader

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
