# Copyright 2015, 2017, 2018 Richard Dymond (rjdymond@gmail.com)
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

def find_unquoted(text, char, start=0, end=None, neg=False):
    if end is None:
        end = len(text)
    index = text.find(char, start, end)
    if index >= 0:
        if '"' not in text[start:end] or index < text.index('"', start, end):
            return index
        for p in split_quoted(text[start:end]):
            index = p.find(char)
            if index >= 0 and ('"' not in p or index < p.index('"')):
                return start + index
            start += len(p)
    if neg:
        return -1
    return end

def split_unquoted(text, sep, maxsplit=-1):
    if '"' not in text:
        return text.split(sep, maxsplit)
    elements = []
    quoted = 0
    for p in text.split(sep):
        if quoted:
            elements[-1] += sep + p
        else:
            elements.append(p)
        i = 0
        while i < len(p):
            c = p[i]
            if c == '"':
                quoted = 1 - quoted
            elif c == '\\' and quoted:
                i += 1
            i += 1
    if len(elements) > maxsplit + 1 > 0:
        elements[maxsplit:] = [sep.join(elements[maxsplit:])]
    return elements

def partition_unquoted(text, sep, default=''):
    parts = split_unquoted(text, sep, 1)
    if len(parts) == 2:
        return (parts[0], sep, parts[1])
    return (text, '', default)

def split_quoted(text):
    return [e for e in re.split(r'("(?:[^"\\]|\\.)*")', text) if e]
