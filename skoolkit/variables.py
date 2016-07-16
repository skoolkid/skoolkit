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
from skoolkit import get_word

class VariableLister:
    def __init__(self):
        self.text = TextReader()

    def list_variables(self, snapshot):
        lines = []
        self.snapshot = snapshot
        i = (snapshot[23627] + 256 * snapshot[23628]) or 23755
        while i < len(snapshot) and snapshot[i] != 128:
            self.text.lspace = False
            variable_type = (snapshot[i] & 224)
            if (variable_type == 64):
                # String
                i, line = self._get_string_var(i)
            elif (variable_type == 128):
                # Array of numbers
                i, line = self._get_num_array_var(i)
            elif (variable_type == 160):
                # Number whose name is longer than one letter
                i, line = self._get_long_num_var(i)
            elif (variable_type == 192):
                # Array of characters
                i, line = self._get_char_array_var(i)
            elif (variable_type == 224):
                # Control variable of a FOR-NEXT loop
                i, line = self._get_control_var(i)
            else:
                # Number whose name is one letter
                i, line = self._get_short_num_var(i)
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
