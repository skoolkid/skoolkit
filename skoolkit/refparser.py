# -*- coding: utf-8 -*-

# Copyright 2009-2015 Richard Dymond (rjdymond@gmail.com)
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

from collections import OrderedDict

from skoolkit import open_file

class RefParser:
    """Parses `ref` files."""
    def __init__(self):
        self._sections = OrderedDict()

    def _add_section(self, section_name, section_lines):
        if section_name:
            while section_lines and not section_lines[-1]:
                section_lines.pop()
            self._sections[section_name] = section_lines

    def parse(self, reffile):
        """Parse a `ref` file. This method may be called as many times as
        required to collect sections from multiple `ref` files.

        :param reffile: The name of the `ref` file to parse.
        """
        section_name = None
        section_lines = []
        infile = open_file(reffile)
        for line in infile:
            s_line = line.rstrip()
            if s_line.startswith(('[[', ';;')):
                section_lines.append(s_line[1:])
            elif s_line.startswith('[') and s_line.endswith(']'):
                self._add_section(section_name, section_lines)
                section_name = s_line[1:-1]
                section_lines = []
            elif not s_line.startswith(';'):
                section_lines.append(s_line)
        infile.close()
        self._add_section(section_name, section_lines)

    def add_line(self, section_name, line):
        """Add a line to a section."""
        if section_name in self._sections:
            self._sections[section_name].append(line)
        else:
            self._sections[section_name] = [line]

    def has_section(self, section_name):
        """Return whether there is any section named `section_name`."""
        return section_name in self._sections

    def has_sections(self, section_type):
        """Return whether there are any sections whose names start with
        `section_type` followed by a colon.
        """
        prefix = section_type + ':'
        for section_name in self._sections:
            if section_name.startswith(prefix):
                return True
        return False

    def get_dictionary(self, section_name):
        """Return a dictionary built from the contents of a section. Each line
        in the section should be of the form ``X=Y``.
        """
        return self._get_dictionary(self._sections.get(section_name, ()))

    def get_dictionaries(self, section_type):
        """Return a list of 2-tuples of the form ``(suffix, dict)`` derived
        from sections whose names start with `section_type` followed by a
        colon. ``suffix`` is the part of the section name that follows the
        first colon, and ``dict`` is a dictionary built from the contents of
        that section; each line in the section should be of the form
        ``X=Y``.
        """
        sep = ':'
        prefix = section_type + sep
        dictionaries = []
        for section_name, lines in self._sections.items():
            if section_name.startswith(prefix):
                section_id = section_name.split(sep, 1)[1]
                dictionaries.append((section_id, self._get_dictionary(lines)))
        return dictionaries

    def get_section(self, section_name, paragraphs=False, lines=False):
        """Return the contents of a section.

        :param section_name: The section name.
        :param paragraphs: If `True`, return the contents as a list of
                           paragraphs.
        :param lines: If `True`, return the contents (or each paragraph) as a
                      list of lines; otherwise return the contents (or each
                      paragraph) as a single string.
        """
        contents = self._sections.get(section_name, ())
        if paragraphs:
            return self._get_paragraphs(contents, lines)
        if lines:
            return contents[:]
        return '\n'.join(contents)

    def get_sections(self, section_type, paragraphs=False, lines=False):
        """Return a list of 2-tuples of the form ``(suffix, contents)`` or
        3-tuples of the form ``(infix, suffix, contents)`` derived from
        sections whose names start with `section_type` followed by a colon.
        ``suffix`` is the part of the section name that follows either the
        first colon (when there is only one) or the second colon (when there is
        more than one); ``infix`` is the part of the section name between the
        first and second colons (when there is more than one).

        :param section_type: The section name prefix.
        :param paragraphs: If `True`, return the contents of each section as a
                           list of paragraphs.
        :param lines: If `True`, return the contents (or each paragraph) of
                      each section as a list of lines; otherwise return the
                      contents (or each paragraph) as a single string.
        """
        sep = ':'
        prefix = section_type + sep
        items = []
        for section_name in self._sections:
            if section_name.startswith(prefix):
                contents = self.get_section(section_name, paragraphs, lines)
                elements = section_name.split(sep, 2)
                if len(elements) < 3:
                    items.append((elements[1], contents))
                else:
                    items.append((elements[1], elements[2], contents))
        return items

    def _get_dictionary(self, contents):
        dictionary = {}
        for line in contents:
            if line:
                try:
                    key, value = line.split('=', 1)
                except ValueError:
                    continue
                if key.isdigit():
                    key = int(key)
                dictionary[key] = value
        return dictionary

    def _get_paragraphs(self, contents, lines):
        paragraphs = []
        p = []
        for line in contents:
            if line:
                p.append(line)
            elif p:
                if lines:
                    paragraphs.append(p)
                else:
                    paragraphs.append('\n'.join(p))
                p = []
        if p:
            if lines:
                paragraphs.append(p)
            else:
                paragraphs.append('\n'.join(p))
        return paragraphs
