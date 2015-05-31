# -*- coding: utf-8 -*-

# Copyright 2015 Richard Dymond (rjdymond@gmail.com)
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

def find_unquoted(text, char, start=0, end=None, neg=False):
    i = start
    if end is None:
        end = len(text)
    quoted = False
    while i < end:
        c = text[i]
        if c == char and not quoted:
            return i
        if c == '\\' and quoted:
            i += 1
        elif c == '"':
            quoted = not quoted
        i += 1
    if neg:
        return -1
    return end

def split_unquoted(text, sep, maxsplit=0):
    i = 0
    quoted = False
    elements = ['']
    while i < len(text):
        c = text[i]
        if c == '"':
            quoted = not quoted
        elif c == '\\' and quoted:
            elements[-1] += text[i:i + 2]
            i += 2
            continue
        elif c == sep and not quoted:
            i += 1
            if len(elements) == maxsplit > 0:
                elements.append(text[i:])
                break
            elements.append('')
            continue
        elements[-1] += c
        i += 1
    return elements

def partition_unquoted(text, sep, default=''):
    parts = split_unquoted(text, sep, 1)
    if len(parts) == 2:
        return (parts[0], sep, parts[1])
    return (text, '', default)
