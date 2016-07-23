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

from skoolkit.basic import get_number
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
                # String (010xxxxx)
                i, line = self._get_string_var(i)
            elif (variable_type == 128):
                # Array of numbers (100xxxxx)
                i, line = self._get_num_array_var(i)
            elif (variable_type == 160):
                # Number whose name is longer than one letter (101xxxxx)
                i, line = self._get_long_num_var(i)
            elif (variable_type == 192):
                # Array of characters (110xxxxx)
                i, line = self._get_char_array_var(i)
            elif (variable_type == 224):
                # Control variable of a FOR-NEXT loop (111xxxxx)
                i, line = self._get_control_var(i)
            elif (variable_type == 96):
                # Number whose name is one letter (011xxxxx)
                i, line = self._get_short_num_var(i)
            else:
                # Basic line (000xxxxx / 001xxxxx)
                i, line = self._skip_basic_line(i)
            if (line != ''):
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
            if (x < (dimensions - 1)):
                line += ','
        line += ')=['
        while (data_length > 0):
            line += '{}'.format(get_number(self.snapshot, i))
            i += 5
            data_length -= 5
            if (data_length > 0):
                line += ','
        line += ']'
        return i,line

    def _get_long_num_var(self, i):
        line = '(Number) '
        letter = (self.snapshot[i] & 31) + 96
        letters = '{}'.format(self.text.get_chars(letter))
        i += 1
        letter = self.snapshot[i]
        while ((letter & 128) == 0):
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
            if (x < (dimensions - 1)):
                line += ','
        line += ')=['
        while (data_length > 0):
            line += '"{}"'.format(self.text.get_chars(self.snapshot[i]))
            i += 1
            data_length -= 1
            if (data_length > 0):
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
