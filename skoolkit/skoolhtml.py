# -*- coding: utf-8 -*-

# Copyright 2008-2013 Richard Dymond (rjdymond@gmail.com)
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

"""
Defines the :class:`FileInfo` and :class:`HtmlWriter` classes.
"""

import re
import posixpath
import os.path
from os.path import isfile, isdir, basename
import inspect

from . import VERSION, warn, parse_int, SkoolKitError, SkoolParsingError
from .skoolmacro import parse_ints, parse_params, get_params, MacroParsingError, UnsupportedMacroError
from .skoolparser import TableParser, ListParser, CASE_LOWER, HTML_MACRO_DELIMITERS

#: The ID of the main disassembly.
MAIN_CODE_ID = 'main'

# Page IDs (as used in the [Paths], [Titles] and [Links] sections)
P_GAME_INDEX = 'GameIndex'
P_MEMORY_MAP = 'MemoryMap'
P_ROUTINES_MAP = 'RoutinesMap'
P_DATA_MAP = 'DataMap'
P_MESSAGES_MAP = 'MessagesMap'
P_UNUSED_MAP = 'UnusedMap'
P_GRAPHICS = 'Graphics'
P_GRAPHIC_GLITCHES = 'GraphicGlitches'
P_GSB = 'GameStatusBuffer'
P_GLOSSARY = 'Glossary'
P_FACTS = 'Facts'
P_BUGS = 'Bugs'
P_POKES = 'Pokes'
P_CHANGELOG = 'Changelog'

# Default image path ID
DEF_IMG_PATH = 'UDGImagePath'

# Byte flip table
FLIP = (
    0, 128, 64, 192, 32, 160, 96, 224, 16, 144, 80, 208, 48, 176, 112, 240, 
    8, 136, 72, 200, 40, 168, 104, 232, 24, 152, 88, 216, 56, 184, 120, 248, 
    4, 132, 68, 196, 36, 164, 100, 228, 20, 148, 84, 212, 52, 180, 116, 244, 
    12, 140, 76, 204, 44, 172, 108, 236, 28, 156, 92, 220, 60, 188, 124, 252, 
    2, 130, 66, 194, 34, 162, 98, 226, 18, 146, 82, 210, 50, 178, 114, 242, 
    10, 138, 74, 202, 42, 170, 106, 234, 26, 154, 90, 218, 58, 186, 122, 250, 
    6, 134, 70, 198, 38, 166, 102, 230, 22, 150, 86, 214, 54, 182, 118, 246, 
    14, 142, 78, 206, 46, 174, 110, 238, 30, 158, 94, 222, 62, 190, 126, 254, 
    1, 129, 65, 193, 33, 161, 97, 225, 17, 145, 81, 209, 49, 177, 113, 241, 
    9, 137, 73, 201, 41, 169, 105, 233, 25, 153, 89, 217, 57, 185, 121, 249, 
    5, 133, 69, 197, 37, 165, 101, 229, 21, 149, 85, 213, 53, 181, 117, 245, 
    13, 141, 77, 205, 45, 173, 109, 237, 29, 157, 93, 221, 61, 189, 125, 253, 
    3, 131, 67, 195, 35, 163, 99, 227, 19, 147, 83, 211, 51, 179, 115, 243, 
    11, 139, 75, 203, 43, 171, 107, 235, 27, 155, 91, 219, 59, 187, 123, 251, 
    7, 135, 71, 199, 39, 167, 103, 231, 23, 151, 87, 215, 55, 183, 119, 247, 
    15, 143, 79, 207, 47, 175, 111, 239, 31, 159, 95, 223, 63, 191, 127, 255
)

PROLOGUE = """<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
"""

def join(*path_components):
    return '/'.join([c for c in path_components if c.replace('/', '')])

class HtmlWriter:
    """Converts a `skool` file and its associated `ref` files to HTML.

    :type skool_parser: :class:`~skoolkit.skoolparser.SkoolParser`
    :param skool_parser: The `skool` file parser to use.
    :type ref_parser: :class:`~skoolkit.refparser.RefParser`
    :param ref_parser: The `ref` file parser to use.
    :type file_info: :class:`FileInfo`
    :param file_info: The `FileInfo` object to use.
    :type image_writer: :class:`~skoolkit.image.ImageWriter`
    :param image_writer: The image writer to use.
    :param case: The case in which to render register names produced by the
                 :ref:`REG` macro (:data:`~skoolkit.skoolparser.CASE_LOWER` for
                 lower case, anything else for upper case)
    :param code_id: The ID of the disassembly.
    """
    def __init__(self, skool_parser, ref_parser, file_info=None, image_writer=None, case=None, code_id=MAIN_CODE_ID):
        self.parser = skool_parser
        self.ref_parser = ref_parser
        self.file_info = file_info
        self.image_writer = image_writer
        self.default_image_format = image_writer.default_format
        self.case = case
        self.base = skool_parser.base

        self.snapshot = self.parser.snapshot
        self._snapshots = [(self.snapshot, '')]
        self.entries = self.parser.entries
        self.memory_map = [e for e in self.parser.memory_map if e.ctl != 'i']

        self.info = self.get_dictionary('Info')

        self.table_parser = TableParser()
        self.list_parser = ListParser()
        self._create_macros()

        paths = self.get_dictionary('Paths')
        titles = self.get_dictionary('Titles')
        link_text = self.get_dictionary('Links')

        self.page_ids = []
        self.pages = {}
        for page_id, details in self.get_dictionaries('Page'):
            self.page_ids.append(page_id)
            self.pages[page_id] = details
        self.page_contents = {}
        for page_id, page in self.pages.items():
            self.page_contents[page_id] = page.get('PageContent', self.get_section('PageContent:{0}'.format(page_id)))
            path = page.get('Content')
            if path:
                self.page_ids.remove(page_id)
            else:
                path = page['Path']
            paths[page_id] = path
            titles[page_id] = page.get('Title', page_id)
            link_text[page_id] = page.get('Link', titles[page_id])
        links = self._parse_links(link_text)

        self.paths = self._get_paths()
        self.paths.update(paths)
        self.titles = self._get_titles()
        self.titles.update(titles)
        self.links = self._get_links()
        self.links.update(links)

        self.other_code = self.get_dictionaries('OtherCode')
        for c_id, code in self.other_code:
            page_id = code.get('IndexPageId')
            if page_id and page_id not in self.paths:
                self.paths[page_id] = code['Index']

        self.memory_map_names = [P_MEMORY_MAP, P_ROUTINES_MAP, P_DATA_MAP, P_MESSAGES_MAP, P_UNUSED_MAP]
        self.memory_maps = self._get_memory_maps()
        for map_name, map_details in self.get_dictionaries('MemoryMap'):
            if map_name not in self.memory_maps:
                self.memory_maps[map_name] = {}
                self.memory_map_names.append(map_name)
            self.memory_maps[map_name].update(map_details)
        for map_name, map_details in self.memory_maps.items():
            map_details['Name'] = map_name

        self.code_path = self.get_code_path(code_id)
        self.game_vars = self.get_dictionary('Game')
        def_game_name = basename(self.parser.skoolfile)
        suffix = '.skool'
        if def_game_name.endswith(suffix):
            def_game_name = def_game_name[:-len(suffix)]
        self.game = self.game_vars.get('Game', def_game_name)
        link_operands = self.game_vars.get('LinkOperands', 'CALL,DEFW,DJNZ,JP,JR')
        self.link_operands = tuple(op.upper() for op in link_operands.split(','))
        self.game_vars.setdefault('StyleSheet', 'skoolkit.css')

        self.bugs = self.get_sections('Bug', True)
        self.facts = self.get_sections('Fact', True)
        self.pokes = self.get_sections('Poke', True)
        self.graphic_glitches = self.get_sections('GraphicGlitch', True)

        self.glossary = []
        for term, paragraphs in self.get_sections('Glossary', True):
            anchor = term.lower().replace(' ', '_')
            self.glossary.append((anchor, term, paragraphs))

        self.graphics = self.get_section('Graphics')
        self.changelog = self._get_changelog()

        self.footer = self._build_footer()

        self.init()

    def init(self):
        """Perform post-initialisation operations. This method is called after
        `__init__()` has completed. By default the method does nothing, but
        subclasses may override it.
        """
        return

    def clone(self, skool_parser, code_id):
        the_clone = self.__class__(skool_parser, self.ref_parser, self.file_info, self.image_writer, self.case, code_id)
        the_clone.set_style_sheet(self.game_vars['StyleSheet'])
        return the_clone

    def set_style_sheet(self, value):
        self.game_vars['StyleSheet'] = value

    def _build_footer(self):
        lines = ['<div class="footer">']
        release_name = self.info.get('Release')
        copyright_message = self.info.get('Copyright')
        created_message = self.info.get('Created', 'Created using <a class="link" href="http://pyskool.ca/?page_id=177">SkoolKit</a> $VERSION.')
        if release_name:
            lines.append('<div class="release">{0}</div>'.format(release_name))
        if copyright_message:
            lines.append('<div class="copyright">{0}</div>'.format(copyright_message))
        if created_message:
            lines.append('<div class="created">{0}</div>'.format(created_message.replace('$VERSION', VERSION)))
        lines.append('</div>')
        lines.append('</body>')
        lines.append('</html>')
        return '\n'.join(lines)

    def _parse_links(self, links):
        new_links = {}
        for page_id, link_text in links.items():
            if link_text.startswith('['):
                sb_count = 1
                index = 1
                length = len(link_text)
                while index < length and sb_count > 0:
                    if link_text[index] == '[':
                        sb_count += 1
                    elif link_text[index] == ']':
                        sb_count -= 1
                    index += 1
                if sb_count == 0:
                    new_links[page_id] = (link_text[1:index - 1], link_text[index:])
            if page_id not in new_links:
                new_links[page_id] = (link_text.strip(), '')
        return new_links

    def get_code_path(self, code_id):
        if code_id.lower() == MAIN_CODE_ID:
            return self.paths.get('CodePath', 'asm')
        for c_id, code in self.other_code:
            if c_id.lower() == code_id.lower():
                return code['Path']

    def has_gbuffer(self):
        return any(entry.ctl == 'g' for entry in self.memory_map)

    def get_dictionary(self, section_name):
        """Return a dictionary built from the contents of a `ref` file section.
        Each line in the section should be of the form ``X=Y``.
        """
        return self.ref_parser.get_dictionary(section_name)

    def get_dictionaries(self, section_type):
        """Return a list of 2-tuples of the form ``(suffix, dict)`` derived
        from `ref` file sections whose names start with `section_type` followed
        by a colon. ``suffix`` is the part of the section name that follows the
        first colon, and ``dict`` is a dictionary built from the contents of
        that section; each line in the section should be of the form ``X=Y``.
        """
        return self.ref_parser.get_dictionaries(section_type)

    def get_section(self, section_name, paragraphs=False, lines=False):
        """Return the contents of a `ref` file section.

        :param section_name: The section name.
        :param paragraphs: If `True`, return the contents as a list of
                           paragraphs.
        :param lines: If `True`, return the contents (or each paragraph) as a
                      list of lines; otherwise return the contents (or each
                      paragraph) as a single string.
        """
        return self.ref_parser.get_section(section_name, paragraphs, lines)

    def get_sections(self, section_type, paragraphs=False, lines=False):
        """Return a list of 2-tuples of the form ``(suffix, contents)`` or
        3-tuples of the form ``(infix, suffix, contents)`` derived from
        `ref` file sections whose names start with `section_type` followed by a
        colon. ``suffix`` is the part of the section name that follows either
        the first colon (when there is only one) or the second colon (when
        there is more than one); ``infix`` is the part of the section name
        between the first and second colons (when there is more than one).

        :param section_type: The section name prefix.
        :param paragraphs: If `True`, return the contents of each section as a
                           list of paragraphs.
        :param lines: If `True`, return the contents (or each paragraph) of
                      each section as a list of lines; otherwise return the
                      contents (or each paragraph) as a single string.
        """
        return self.ref_parser.get_sections(section_type, paragraphs, lines)

    def get_entry(self, address):
        """Return the routine or data block that starts at `address`."""
        return self.parser.get_entry(address)

    def get_entry_point_refs(self, address):
        """Return the addresses of the routines and data blocks that contain
        instructions that refer to `address`.
        """
        return self.parser.get_entry_point_refs(address)

    def get_snapshot_name(self):
        """Return the name of the current memory snapshot."""
        return self._snapshots[-1][1]

    def pop_snapshot(self):
        """Discard the current memory snapshot and replace it with the one that
        was most recently saved (by
        :meth:`~skoolkit.skoolhtml.HtmlWriter.push_snapshot`)."""
        self.snapshot = self._snapshots.pop()[0]

    def push_snapshot(self, name=''):
        """Save the current memory snapshot for later retrieval (by
        :meth:`~skoolkit.skoolhtml.HtmlWriter.pop_snapshot`), and put a copy in
        its place.

        :param name: An optional name for the snapshot.
        """
        self._snapshots.append((self.snapshot[:], name))

    def _get_paths(self):
        buffers_path = 'buffers'
        graphics_path = 'graphics'
        images_path = 'images'
        maps_path = 'maps'
        reference_path = 'reference'
        paths = {
            'FontImagePath': join(images_path, 'font'),
            'JavaScriptPath': '.',
            'ScreenshotImagePath': join(images_path, 'scr'),
            'StyleSheetPath': '.',
            'UDGImagePath': join(images_path, 'udgs'),
            P_GAME_INDEX: 'index.html',
            P_MEMORY_MAP: join(maps_path, 'all.html'),
            P_ROUTINES_MAP: join(maps_path, 'routines.html'),
            P_DATA_MAP: join(maps_path, 'data.html'),
            P_MESSAGES_MAP: join(maps_path, 'messages.html'),
            P_UNUSED_MAP: join(maps_path, 'unused.html'),
            P_BUGS: join(reference_path, 'bugs.html'),
            P_CHANGELOG: join(reference_path, 'changelog.html'),
            P_FACTS: join(reference_path, 'facts.html'),
            P_GLOSSARY: join(reference_path, 'glossary.html'),
            P_POKES: join(reference_path, 'pokes.html'),
            P_GSB: join(buffers_path, 'gbuffer.html'),
            P_GRAPHICS: join(graphics_path, 'graphics.html'),
            P_GRAPHIC_GLITCHES: join(graphics_path, 'glitches.html'),
        }
        return paths

    def _get_titles(self):
        titles = {
            P_BUGS: 'Bugs',
            P_CHANGELOG: 'Changelog',
            P_DATA_MAP: 'Data',
            P_FACTS: 'Trivia',
            P_GAME_INDEX: 'Index',
            P_GSB: 'Game status buffer',
            P_GLOSSARY: 'Glossary',
            P_GRAPHIC_GLITCHES: 'Graphic glitches',
            P_GRAPHICS: 'Graphics',
            P_MEMORY_MAP: 'Memory map',
            P_MESSAGES_MAP: 'Messages',
            P_POKES: 'Pokes',
            P_ROUTINES_MAP: 'Routines',
            P_UNUSED_MAP: 'Unused addresses'
        }
        return titles

    def _get_links(self):
        links = {}
        for page_id, text in self._get_titles().items():
            links[page_id] = (text, '')
        links[P_MEMORY_MAP] = ('Everything', '')
        return links

    def _get_memory_maps(self):
        memory_maps = {}
        memory_maps[P_MEMORY_MAP] = {
            'PageByteColumns': '1'
        }
        memory_maps[P_ROUTINES_MAP] = {
            'EntryTypes': 'c'
        }
        memory_maps[P_DATA_MAP] = {
            'EntryTypes': 'bw',
            'PageByteColumns': '1'
        }
        memory_maps[P_MESSAGES_MAP] = {
            'EntryTypes': 't'
        }
        memory_maps[P_UNUSED_MAP] = {
            'EntryTypes': 'uz',
            'PageByteColumns': '1'
        }
        return memory_maps

    def _get_changelog(self):
        changelog = []
        for title, paragraphs in self.get_sections('Changelog', True, True):
            intro = paragraphs[0][0]
            if intro == '-':
                intro = ''
            items = []
            for p in paragraphs[1:]:
                items.append(p)
            changelog.append((title, intro, items))
        return changelog

    def get_page_ids(self):
        return self.page_ids

    def need_image(self, image_path):
        """Return whether an image file needs to be created. This will be true
        only if the file doesn't already exist, or all images are being
        rebuilt. Well-behaved image-creating methods will call this to check
        whether an image file needs to be written, and thus avoid building an
        image when it is not necessary.

        :param image_path: The full path of the image file relative to the root
                           directory of the disassembly.
        """
        return self.file_info.need_image(image_path)

    def file_exists(self, fname):
        return self.file_info.file_exists(fname)

    def join_paragraphs(self, paragraphs, cwd):
        return '\n'.join(['<div class="paragraph">\n{0}\n</div>'.format(self.expand(p, cwd).strip()) for p in paragraphs])

    def _get_screen_udg(self, row, col, df_addr=16384, af_addr=22528):
        attr = self.snapshot[af_addr + 32 * row + col]
        address = df_addr + 2048 * (row // 8) + 32 * (row % 8) + col
        return Udg(attr, self.snapshot[address:address + 2048:256])

    def screenshot(self, x=0, y=0, w=32, h=24, df_addr=16384, af_addr=22528):
        """Return a two-dimensional array of tiles (instances of
        :class:`~skoolkit.skoolhtml.Udg`) built from the display file and
        attribute file of the current memory snapshot.

        :param x: The x-coordinate of the top-left tile to include (0-31).
        :param y: The y-coordinate of the top-left tile to include (0-23).
        :param w: The width of the array (in tiles).
        :param h: The height of the array (in tiles).
        :param df_addr: The display file address to use.
        :param af_addr: The attribute file address to use.
        """
        width = min((w, 32 - x))
        height = min((h, 24 - y))
        scr_udgs = []
        for r in range(y, y + height):
            scr_udgs.append([self._get_screen_udg(r, c, df_addr, af_addr) for c in range(x, x + width)])
        return scr_udgs

    def flip_udgs(self, udgs, flip=1):
        """Flip a 2D array of UDGs (instances of
        :class:`~skoolkit.skoolhtml.Udg`).

        :param udgs: The array of UDGs.
        :param flip: 1 to flip horizontally, 2 to flip vertically, or 3 to flip
                     horizontally and vertically.
        """
        for row in udgs:
            for udg in row:
                udg.flip(flip)
        if flip & 1:
            for row in udgs:
                row.reverse()
        if flip & 2:
            udgs.reverse()

    def rotate_udgs(self, udgs, rotate=1):
        """Rotate a 2D array of UDGs (instances of
        :class:`~skoolkit.skoolhtml.Udg`) 90 degrees clockwise.

        :param udgs: The array of UDGs.
        :param rotate: The number of rotations to perform.
        """
        for row in udgs:
            for udg in row:
                udg.rotate(rotate)
        if rotate & 3 == 1:
            rotated = []
            for i in range(len(udgs[0])):
                rotated.append([])
                for j in range(len(udgs)):
                    rotated[-1].insert(0, udgs[j][i])
            udgs[:] = rotated
        elif rotate & 3 == 2:
            udgs.reverse()
            for row in udgs:
                row.reverse()
        elif rotate & 3 == 3:
            rotated = []
            for i in range(len(udgs[0])):
                rotated.insert(0, [])
                for j in range(len(udgs)):
                    rotated[0].append(udgs[j][i])
            udgs[:] = rotated

    def get_font_udg_array(self, address, chars, attr):
        return 8 * chars, [[Udg(attr, self.snapshot[a:a + 8]) for a in range(address, address + 8 * chars, 8)]]

    def write_asm_entries(self):
        self.write_entries(self.code_path, self.paths[P_MEMORY_MAP])

    def write_graphics(self):
        ofile, cwd = self.open_file(self.paths[P_GRAPHICS])
        self.write_header(ofile, self.titles[P_GRAPHICS], cwd, 'graphics')
        ofile.write(self.expand(self.graphics, cwd))
        ofile.write('\n')
        ofile.write(self.footer)

    def write_graphic_glitches(self):
        self.write_box_page(self.paths[P_GRAPHIC_GLITCHES], self.titles[P_GRAPHIC_GLITCHES], 'graphics', self.graphic_glitches)

    def write_index(self):
        ofile, cwd = self.open_file(self.paths[P_GAME_INDEX])
        self.write_head(ofile, 'Index', cwd)
        ofile.write('<body class="main">\n')
        prefix = self.game_vars.get('TitlePrefix', 'The complete')
        suffix = self.game_vars.get('TitleSuffix', 'RAM disassembly')
        ofile.write('<table class="header">\n')
        ofile.write('<tr>\n')
        ofile.write('<td class="headerText">{0}</td>\n'.format(prefix))
        ofile.write('<td class="headerLogo">{0}</td>\n'.format(self._get_logo(cwd)))
        ofile.write('<td class="headerText">{0}</td>\n'.format(suffix))
        ofile.write('</tr>\n')
        ofile.write('</table>\n')

        memory_maps = []
        for map_name in (P_MEMORY_MAP, P_ROUTINES_MAP, P_DATA_MAP, P_MESSAGES_MAP, P_UNUSED_MAP):
            map_details = self.memory_maps[map_name]
            if map_details.get('Write') != '0':
                memory_maps.append(map_name)
        link_groups = {
            'MemoryMaps': ('Memory maps', memory_maps),
            'Graphics': ('Graphics', (
                P_GRAPHICS,
                P_GRAPHIC_GLITCHES
            )),
            'DataTables': ('Data tables and buffers', (
                P_GSB,
            )),
            'Reference': ('Reference', (
                P_CHANGELOG,
                P_GLOSSARY,
                P_FACTS,
                P_BUGS,
                P_POKES
            ))
        }
        for section_id, header_text, page_list in self.get_sections('Index', False, True):
            link_groups[section_id] = (header_text, page_list)
        sections = {}
        for section_id, (header_text, page_list) in link_groups.items():
            links = []
            for page_id in page_list:
                fname = self.paths.get(page_id)
                if fname and self.file_exists(fname):
                    link_file = FileInfo.relpath(cwd, fname)
                    link_text = self.links[page_id]
                    links.append((link_file, link_text[0], link_text[1]))
            sections[section_id] = ('<div class="headerText">{0}</div>\n'.format(header_text), links)
        other_code_links = []
        for code_id, code in self.other_code:
            fname = code['Index']
            if self.file_exists(fname):
                link_file = FileInfo.relpath(cwd, fname)
                other_code_links.append((link_file, code.get('Link', code['Title']), ''))
        sections['OtherCode'] = ('<div class="headerText">Other code</div>\n', other_code_links)

        index = self.get_section('Index', False, True)
        if not index:
            index = ('MemoryMaps', 'Graphics', 'DataTables', 'OtherCode', 'Reference')
        for section_id in index:
            header, links = sections.get(section_id, ('', ()))
            if links:
                ofile.write(header)
                ofile.write('<ul class="indexList">\n')
                for href, link_text, other_text in links:
                    ofile.write('<li><a class="link" href="{0}">{1}</a>{2}</li>\n'.format(href, link_text, other_text))
                ofile.write('</ul>\n')

        ofile.write(self.footer)

    def write_gbuffer(self):
        ofile, cwd = self.open_file(self.paths[P_GSB])
        self.write_header(ofile, self.titles[P_GSB], cwd, "gbuffer")
        ofile.write('<table class="gbuffer">\n')
        ofile.write('<tr>\n')
        ofile.write('<th>Address</th>\n')
        ofile.write('<th>Length</th>\n')
        ofile.write('<th>Purpose</th>\n')
        ofile.write('</tr>\n')
        gsb_includes = self.game_vars.get('GameStatusBufferIncludes', [])
        if gsb_includes:
            gsb_includes = [parse_int(a) for a in gsb_includes.split(',')]
        for entry in self.memory_map:
            if not (entry.ctl == 'g' or entry.address in gsb_includes):
                continue
            address = entry.address
            desc = '<div class="gbufDesc">{0}</div>'.format(self.expand(entry.description, cwd))
            if entry.details:
                desc += '\n<div class="gbufDetails">\n{0}\n</div>'.format(self.join_paragraphs(entry.details, cwd))
            ofile.write('<tr>\n')
            asm_file = FileInfo.asm_relpath(cwd, address, self.code_path)
            entry_link = '<a name="{0}" class="link" href="{1}">{2}</a>'.format(address, asm_file, entry.addr_str)
            ofile.write('<td class="gbufAddress">{0}</td>\n'.format(entry_link))
            ofile.write('<td class="gbufLength">{0}</td>\n'.format(entry.size))
            ofile.write('<td class="gbufDesc">\n{0}\n</td>\n'.format(desc))
            ofile.write('</tr>\n')
        ofile.write('</table>\n')
        ofile.write(self.footer)

    def write_link_list(self, ofile, link_list):
        ofile.write('<ul class="linkList">\n')
        for anchor, title in link_list:
            ofile.write('<li><a class="link" href="#{0}">{1}</a></li>\n'.format(anchor, title))
        ofile.write('</ul>\n')

    def write_boxes(self, ofile, boxes, cwd):
        box_num = 1
        for anchor, title, paragraphs in boxes:
            ofile.write('<div><a name="{0}"></a></div>\n'.format(anchor))
            ofile.write('<div class="box box{0}">\n'.format(box_num))
            ofile.write('<div class="boxTitle">{0}</div>\n'.format(title))
            for paragraph in paragraphs:
                ofile.write('<div class="paragraph">\n{0}\n</div>\n'.format(self.expand(paragraph, cwd).strip()))
            ofile.write('</div>\n')
            box_num = 3 - box_num

    def write_box_page(self, fname, title, body_class, boxes):
        ofile, cwd = self.open_file(fname)
        self.write_header(ofile, title, cwd, body_class)
        self.write_link_list(ofile, [(anchor, title) for anchor, title, p in boxes])
        self.write_boxes(ofile, boxes, cwd)
        ofile.write(self.footer)

    def write_pokes(self):
        self.write_box_page(self.paths[P_POKES], self.titles[P_POKES], 'pokes', self.pokes)

    def write_bugs(self):
        self.write_box_page(self.paths[P_BUGS], self.titles[P_BUGS], 'bugs', self.bugs)

    def write_facts(self):
        self.write_box_page(self.paths[P_FACTS], self.titles[P_FACTS], 'facts', self.facts)

    def write_glossary(self):
        self.write_box_page(self.paths[P_GLOSSARY], self.titles[P_GLOSSARY], 'glossary', self.glossary)

    def write_changelog(self):
        ofile, cwd = self.open_file(self.paths[P_CHANGELOG])
        self.write_header(ofile, self.titles[P_CHANGELOG], cwd, 'changelog')
        ofile.write('<ul class="linkList">\n')
        for title, description, items in self.changelog:
            ofile.write('<li><a class="link" href="#{0}">{0}</a></li>\n'.format(title))
        ofile.write('</ul>\n')
        for j, (title, description, items) in enumerate(self.changelog):
            ofile.write('<div><a name="{0}"></a></div>\n'.format(title))
            ofile.write('<div class="changelog changelog{0}">\n'.format(1 + j % 2))
            ofile.write('<div class="changelogTitle">{0}</div>\n'.format(title))
            if description:
                ofile.write('<div class="changelogDesc">{0}</div>\n'.format(description))
            if items:
                ofile.write('<ul class="changelog">\n')
                for item in items:
                    indents = [0]
                    for i, line in enumerate(item):
                        new_indent = len(line) - len(line.lstrip())
                        if new_indent == indents[-1]:
                            if i > 0:
                                ofile.write('</li>\n')
                        else:
                            if new_indent > indents[-1]:
                                ofile.write('\n<ul class="changelog{0}">\n'.format(len(indents)))
                                indents.append(new_indent)
                            else:
                                while new_indent < indents[-1]:
                                    ofile.write('</li>\n</ul>\n')
                                    indents.pop()
                                ofile.write('</li>\n')
                        ofile.write('<li>{0}'.format(self.expand(line.strip(), cwd)))
                    ofile.write('</li>\n')
                    while len(indents) > 1:
                        ofile.write('</ul>\n</li>\n')
                        indents.pop()
                ofile.write('</ul>\n')
            ofile.write('</div>\n')
        ofile.write(self.footer)

    def write_prev_next(self, ofile, prev_link, next_link, up_link):
        if prev_link or next_link or up_link:
            prev_text = next_text = up_text = ''
            if prev_link:
                prev_text = 'Prev: {0}'.format(prev_link)
            if next_link:
                next_text = 'Next: {0}'.format(next_link)
            if up_link:
                up_text = 'Up: {0}'.format(up_link)
            ofile.write('<table class="prevNext">\n')
            ofile.write('<tr>\n')
            ofile.write('<td class="prev">{0}</td>\n'.format(prev_text))
            ofile.write('<td class="up">{0}</td>\n'.format(up_text))
            ofile.write('<td class="next">{0}</td>\n'.format(next_text))
            ofile.write('</tr>\n')
            ofile.write('</table>\n')

    def write_registers(self, ofile, registers, cwd):
        input_values = []
        output_values = []
        mode = 'I'
        for reg in registers:
            if reg.prefix:
                mode = reg.prefix.upper()[0]
            if mode == 'O':
                output_values.append(reg)
            else:
                input_values.append(reg)

        input_header = self.game_vars.get('InputRegisterTableHeader')
        output_header = self.game_vars.get('OutputRegisterTableHeader')
        for table_class, header, registers in (('input', input_header, input_values), ('output', output_header, output_values)):
            if registers:
                ofile.write('<table class="{0}">\n'.format(table_class))
                if header:
                    ofile.write('<tr>\n')
                    ofile.write('<th colspan="2">{0}</th>\n'.format(header))
                    ofile.write('</tr>\n')
                for reg in registers:
                    ofile.write('<tr>\n')
                    ofile.write('<td class="register">{0}</td>\n'.format(reg.name))
                    ofile.write('<td class="registerContents">{0}</td>\n'.format(self.expand(reg.contents, cwd)))
                    ofile.write('</tr>\n')
                ofile.write('</table>\n')

    def write_entry(self, cwd, entry, fname=None, page_header=None, prev_entry=None, next_entry=None, up=None):
        fname = fname or FileInfo.asm_fname(entry.address)
        ofile = self.file_info.open_file(cwd, fname)
        title_suffix = ''
        asm_label = self.parser.get_asm_label(entry.address)
        if asm_label:
            title_suffix = ' ({0})'.format(asm_label)
        body_class = "disassembly"
        if entry.is_routine():
            title_format = "Routine at {0}"
            page_header = page_header or "Routines"
        elif entry.ctl in 'uz':
            title_format = "Unused RAM at {0}"
            page_header = page_header or "Unused"
        elif entry.ctl == 'g':
            title_format = "Game status buffer entry at {0}"
            page_header = page_header or "Game status buffer"
        else:
            title_format = "Data at {0}"
            page_header = page_header or "Data"
        self.write_header(ofile, title_format.format(entry.addr_str) + title_suffix, cwd, body_class, page_header)

        prev_link = None
        if prev_entry:
            prev_file = FileInfo.asm_fname(prev_entry.address)
            prev_link = '<a class="link" href="{0}">{1}</a>'.format(prev_file, prev_entry.addr_str)
        next_link = None
        if next_entry:
            next_file = FileInfo.asm_fname(next_entry.address)
            next_link = '<a class="link" href="{0}">{1}</a>'.format(next_file, next_entry.addr_str)
        up_link = None
        if up:
            map_path = FileInfo.relpath(cwd, up)
            up_link = '<a class="link" href="{0}#{1}">Map</a>'.format(map_path, entry.address)
        self.write_prev_next(ofile, prev_link, next_link, up_link)

        desc = self.expand(entry.description, cwd)
        label_text = ''
        if asm_label:
            label_text = '{0}: '.format(asm_label)
        ofile.write('<div class="description">{0}{1}: {2}</div>\n'.format(label_text, entry.addr_str, desc))

        table_class = 'disassembly'
        comment_class = 'comment'
        transparent_class = 'transparentComment'
        if entry.ctl not in 'cuz':
            table_class = 'dataDisassembly'
            comment_class = 'dataComment'
            transparent_class = 'transparentDataComment'
        ofile.write('<table class="{0}">\n'.format(table_class))

        show_comment_col = False
        show_label_col = False
        routine_comment_colspan = 3
        for instruction in entry.instructions:
            if instruction.comment and instruction.comment.text:
                show_comment_col = True
            if instruction.asm_label:
                show_label_col = True
                routine_comment_colspan = 4
            if show_comment_col and show_label_col:
                break
        routine_comment_td = '<td class="routineComment" colspan="{}">\n'.format(routine_comment_colspan)

        ofile.write('<tr>\n')
        ofile.write(routine_comment_td)
        ofile.write('<div class="details">\n')
        if entry.details:
            ofile.write('{0}\n'.format(self.join_paragraphs(entry.details, cwd)))
        ofile.write('</div>\n')
        if entry.registers:
            self.write_registers(ofile, entry.registers, cwd)
        ofile.write('</td>\n')
        ofile.write('</tr>\n')

        for instruction in entry.instructions:
            mid_routine_comments = entry.get_mid_routine_comment(instruction.label)
            address = instruction.address
            anchor = '<a name="{0}"></a>'.format(address)
            if mid_routine_comments:
                ofile.write('<tr>\n')
                ofile.write(routine_comment_td)
                ofile.write('{0}\n'.format(anchor))
                ofile.write('<div class="comments">\n{0}\n</div>\n'.format(self.join_paragraphs(mid_routine_comments, cwd)))
                ofile.write('</td>\n')
                ofile.write('</tr>\n')
                anchor = ''
            ofile.write('<tr>\n')
            if show_label_col:
                ofile.write('<td class="asmLabel">{}</td>\n'.format(instruction.asm_label or ''))
            if instruction.ctl in 'c*!':
                tdclass = 'label'
            else:
                tdclass = 'address'
            ofile.write('<td class="{0}">{1}{2}</td>\n'.format(tdclass, anchor, instruction.addr_str))
            operation, reference = instruction.operation, instruction.reference
            if reference and operation.upper().startswith(self.link_operands):
                entry_address = reference.entry.address
                if reference.address == entry_address:
                    name = ''
                else:
                    name = '#{0}'.format(reference.address)
                if reference.entry.asm_id:
                    # This is a reference to an entry in another disassembly
                    entry_file = FileInfo.asm_relpath(cwd, entry_address, self.get_code_path(reference.entry.asm_id))
                else:
                    # This is a reference to an entry in the same disassembly
                    entry_file = FileInfo.asm_fname(entry_address)
                link_text = self.parser.get_asm_label(reference.address) or reference.addr_str
                link = '<a class="link" href="{0}{1}">{2}</a>'.format(entry_file, name, link_text)
                operation = operation.replace(reference.addr_str, link)
            ofile.write('<td class="instruction">{0}</td>\n'.format(operation))
            if show_comment_col:
                comment = instruction.comment
                if comment:
                    if comment.rowspan < 2:
                        rowspan = ''
                    else:
                        rowspan = ' rowspan="{0}"'.format(comment.rowspan)
                    comment_html = self.expand(comment.text, cwd)
                    ofile.write('<td class="{0}"{1}>{2}</td>\n'.format(comment_class, rowspan, comment_html))
            else:
                ofile.write('<td class="{0}" />\n'.format(transparent_class))
            ofile.write('</tr>\n')

        if entry.end_comment:
            ofile.write('<tr>\n')
            ofile.write(routine_comment_td)
            ofile.write('<div class="comments">\n{0}\n</div>\n'.format(self.join_paragraphs(entry.end_comment, cwd)))
            ofile.write('</td>\n')
            ofile.write('</tr>\n')

        ofile.write('</table>\n')

        self.write_prev_next(ofile, prev_link, next_link, up_link)
        ofile.write(self.footer)

    def write_entries(self, cwd, map_file, page_header=None):
        prev_entry = None
        memory_map = self.memory_map
        for i, entry in enumerate(memory_map):
            if i + 1 < len(memory_map):
                next_entry = memory_map[i + 1]
            else:
                next_entry = None
            self.write_entry(cwd, entry, page_header=page_header, prev_entry=prev_entry, next_entry=next_entry, up=map_file)
            prev_entry = entry

    def should_write_map(self, map_details):
        if map_details.get('Write') == '0':
            return False
        entry_types = map_details.get('EntryTypes')
        if not entry_types:
            return True
        return any(entry.ctl in entry_types for entry in self.memory_map)

    def get_map_path(self, map_details):
        if 'Path' in map_details:
            return map_details['Path']
        map_name = map_details['Name']
        return self.paths.get(map_name, '{0}.html'.format(map_name))

    def write_map(self, map_details):
        map_file = self.get_map_path(map_details)
        if 'Title' in map_details:
            title = map_details['Title']
        else:
            map_name = map_details['Name']
            title = self.titles.get(map_name, map_name)
        entry_types = map_details.get('EntryTypes', 'bcgtuwz')
        show_page_byte = map_details.get('PageByteColumns', '0') != '0'
        intro = map_details.get('Intro')
        asm_path = map_details.get('AsmPath', self.code_path)

        cwd = os.path.dirname(map_file)
        ofile = self.file_info.open_file(map_file)
        self.write_header(ofile, title, cwd, "map")
        if intro:
            ofile.write('<div class="mapIntro">{0}</div>\n'.format(self.expand(intro, cwd)))
        headers = ['Address', 'Description']
        if show_page_byte:
            headers.insert(0, 'Page')
            headers.insert(1, 'Byte')
        ofile.write('<table class="map">\n')
        ofile.write('<tr>\n')
        for header in headers:
            ofile.write('<th>{0}</th>\n'.format(header))
        ofile.write('</tr>\n')

        for entry in self.memory_map:
            if entry.ctl not in entry_types:
                continue

            purpose = entry.description
            if entry.ctl == 'c':
                entry_class = 'routine'
                desc_class = 'routineDesc'
            elif entry.ctl in 'bw':
                entry_class = 'data'
                desc_class = 'dataDesc'
            elif entry.ctl in 'g':
                entry_class = 'gbuffer'
                desc_class = 'gbufferDesc'
            elif entry.ctl in 'uz':
                size = entry.size
                if size > 1:
                    suffix = 's'
                else:
                    suffix = ''
                purpose = 'Unused ({0} byte{1})'.format(size, suffix)
                entry_class = 'unused'
                desc_class = 'unusedDesc'
            elif entry.ctl == 't':
                entry_class = 'message'
                desc_class = 'messageDesc'

            address = entry.address
            ofile.write('<tr>\n')
            if show_page_byte:
                ofile.write('<td class="mapPage">{0}</td>\n'.format(address // 256))
                ofile.write('<td class="mapByte">{0}</td>\n'.format(address % 256))
            asm_relpath = FileInfo.relpath(cwd, asm_path)
            asm_file = FileInfo.asm_fname(address, asm_relpath)
            content = '<a class="link" name="{0}" href="{1}">{2}</a>'.format(address, asm_file, entry.addr_str)
            ofile.write('<td class="{0}">{1}</td>\n'.format(entry_class, content))
            ofile.write('<td class="{0}">{1}</td>\n'.format(desc_class, self.expand(purpose, cwd)))
            ofile.write('</tr>\n')

        ofile.write('</table>\n')
        ofile.write(self.footer)

    def write_page(self, page_id):
        ofile, cwd = self.open_file(self.paths[page_id])
        page = self.pages[page_id]
        body_class = page.get('BodyClass')
        js = page.get('JavaScript')
        self.write_header(ofile, self.titles[page_id], cwd, body_class, js=js)
        page_content = self.expand(self.page_contents[page_id], cwd).strip()
        ofile.write('{0}\n'.format(page_content))
        ofile.write(self.footer)

    def open_file(self, fname):
        ofile = self.file_info.open_file(fname)
        cwd = os.path.dirname(fname)
        return ofile, cwd

    def write_head(self, ofile, title, cwd, js=None):
        ofile.write(PROLOGUE)
        ofile.write('<head>\n')
        ofile.write('<meta http-equiv="content-type" content="text/html; charset=utf-8" />\n')
        ofile.write('<title>{0}: {1}</title>\n'.format(self.game, title))
        for css_file in self.game_vars['StyleSheet'].split(';'):
            ofile.write('<link rel="stylesheet" type="text/css" href="{0}" />\n'.format(FileInfo.relpath(cwd, join(self.paths['StyleSheetPath'], basename(css_file)))))
        if js:
            for js_file in js.split(';'):
                ofile.write('<script type="text/javascript" src="{0}"></script>\n'.format(FileInfo.relpath(cwd, join(self.paths['JavaScriptPath'], basename(js_file)))))
        ofile.write('</head>\n')

    def _get_logo(self, cwd):
        logo_macro = self.game_vars.get('Logo')
        if logo_macro:
            return self.expand(logo_macro, cwd)
        logo_image = self.game_vars.get('LogoImage')
        if logo_image and self.file_exists(logo_image):
            return '<img src="{0}" alt="{1}" />'.format(FileInfo.relpath(cwd, logo_image), self.game)
        return self.game

    def write_header(self, ofile, title, cwd, body_class, body_title=None, js=None):
        self.write_head(ofile, title, cwd, js)
        index = FileInfo.relpath(cwd, self.paths[P_GAME_INDEX])
        if body_class:
            ofile.write('<body class="{0}">\n'.format(body_class))
        else:
            ofile.write('<body>\n')
        ofile.write('<table class="header">\n')
        ofile.write('<tr>\n')
        ofile.write('<td class="headerLogo"><a class="link" href="{0}">{1}</a></td>\n'.format(index, self._get_logo(cwd)))
        ofile.write('<td class="headerText">{0}</td>\n'.format(body_title or title))
        ofile.write('</tr>\n')
        ofile.write('</table>\n')

    def write_image(self, image_path, udgs, crop_rect=(), scale=2, mask=False):
        """Create an image and write it to a file.

        :param image_path: The full path of the file to which to write the
                           image (relative to the root directory of the
                           disassembly).
        :param udgs: The two-dimensional array of tiles (instances of
                     :class:`~skoolkit.skoolhtml.Udg`) from which to build the
                     image.
        :param crop_rect: The cropping rectangle, ``(x, y, width, height)``,
                          where ``x`` and ``y`` are the x- and y-coordinates of
                          the top-left pixel to include in the final image, and
                          ``width`` and ``height`` are the width and height of
                          the final image.
        :param scale: The scale of the image.
        :param mask: Whether to apply masks to the tiles in the image.
        """
        if self.image_writer:
            img_file_ext = image_path.lower()[-4:]
            if img_file_ext == '.png':
                img_format = 'png'
            elif img_file_ext == '.gif':
                img_format = 'gif'
            else:
                raise SkoolKitError('Unsupported image file format: {0}'.format(image_path))
            f = self.file_info.open_file(image_path, mode='wb')
            self.image_writer.write_image(udgs, f, img_format, scale, mask, *crop_rect)
            f.close()

    def _create_macros(self):
        self.macros = {}
        prefix = 'expand_'
        for name, method in inspect.getmembers(self, inspect.ismethod):
            search = re.search('{0}[a-z]+'.format(prefix), name)
            if search and name == search.group():
                macro = '#{0}'.format(name[len(prefix):].upper())
                self.macros[macro] = method

    def build_table(self, table):
        table_class = table.table_class
        html = []
        if table_class:
            class_attr = ' class="{0}"'.format(table_class)
        else:
            class_attr = ''
        html.append('<table{0}>'.format(class_attr))
        for row in table.rows:
            html.append('<tr>')
            for cell in row:
                if cell.colspan > 1:
                    colspan = ' colspan="{0}"'.format(cell.colspan)
                else:
                    colspan = ''
                if cell.rowspan > 1:
                    rowspan = ' rowspan="{0}"'.format(cell.rowspan)
                else:
                    rowspan = ''
                if cell.header:
                    tag = 'th'
                    td_class = ''
                else:
                    tag = 'td'
                    cell_class = cell.cell_class
                    if cell.transparent:
                        cell_class += " transparent"
                    cell_class = cell_class.lstrip()
                    if cell_class:
                        td_class = ' class="{0}"'.format(cell_class)
                    else:
                        td_class = ''
                html.append('<{0}{1}{2}{3}>{4}</{0}>'.format(tag, td_class, colspan, rowspan, cell.contents))
            html.append('</tr>')
        html.append('</table>')
        return '\n'.join(html)

    def build_list(self, list_obj):
        html = []
        if list_obj.css_class:
            class_attr = ' class="{0}"'.format(list_obj.css_class)
        else:
            class_attr = ''
        html.append('<ul{0}>'.format(class_attr))
        for item in list_obj.items:
            html.append('<li>{0}</li>'.format(item))
        html.append('</ul>')
        return '\n'.join(html)

    def _get_udg_addresses(self, addr, width):
        if type(addr) is int:
            return [addr]
        num = 1
        if 'x' in addr:
            addr, num = addr.split('x')
            num = parse_int(num)
        if '-' in addr:
            elements = [parse_int(n) for n in addr.split('-')]
            if len(elements) < 3:
                elements.append(1)
            if len(elements) < 4:
                elements.append(elements[2] * width)
            address, end_address, h_step, v_step = elements
            addresses = []
            while address <= end_address:
                addresses.append(address)
                if len(addresses) % width:
                    address += h_step
                else:
                    address += v_step - (width - 1) * h_step
        else:
            addresses = [parse_int(addr)]
        return addresses * num

    def img_element(self, cwd, image_path, alt=None):
        """Return an ``<img .../>`` element for an image file.

        :param cwd: The current working directory (from which the relative path
                    of the image file will be computed).
        :param image_path: The full path of the image file relative to the root
                           directory of the disassembly.
        :param alt: The alt text to use for the image; if `None`, the base name
                    of the image file (with the '.png' or '.gif' suffix
                    removed) will be used.
        """
        if alt is None:
            alt = basename(image_path)[:-4]
        return '<img alt="{0}" src="{1}" />'.format(alt, FileInfo.relpath(cwd, image_path))

    def image_path(self, fname, path_id=DEF_IMG_PATH):
        """Return the full path of an image file relative to the root directory
        of the disassembly. If `fname` does not end with '.png' or '.gif', an
        appropriate suffix will be appended (depending on the default image
        format). If `fname` starts with a '/', it will be removed and the
        remainder returned (in which case `path_id` is ignored). If `fname` is
        blank, `None` is returned.

        :param fname: The name of the image file.
        :param path_id: The ID of the target directory (as defined in the
                        :ref:`paths` section of the `ref` file).
        """
        if fname:
            if fname[-4:].lower() in ('.png', '.gif'):
                suffix = ''
            else:
                suffix = '.{0}'.format(self.default_image_format)
            if fname[0] == '/':
                return '{0}{1}'.format(fname[1:], suffix)
            if path_id in self.paths:
                return join(self.paths[path_id], '{0}{1}'.format(fname, suffix))
            raise SkoolKitError("Unknown path ID '{0}' for image file '{1}'".format(path_id, fname))

    def parse_image_params(self, text, index, num, defaults=(), path_id=DEF_IMG_PATH, fname='', chars=''):
        """Parse a string of the form ``params[{X,Y,W,H}][(fname)]``. The
        parameter string ``params`` may contain comma-separated values and will
        be parsed until either the end of the text is reached, or an invalid
        character is encountered.

        :param text: The text to parse.
        :param index: The index at which to start parsing.
        :param num: The maximum number of parameters to parse.
        :param defaults: The default values of the optional parameters.
        :param path_id: The ID of the target directory for the image file (as
                        defined in the :ref:`paths` section of the `ref` file).
        :param fname: The default base name of the image file.
        :param chars: Characters to consider valid in the parameter string in
                      addition to the comma, '$', the digits 0-9, and the
                      letters A-F and a-f.
        :return: A list of the form
                 ``[end, image_path, crop_rect, value1, value2...]``, where
                 ``end`` is the index at which parsing terminated,
                 ``image_path`` is the full path of the image file (relative to
                 the root directory of the disassembly), ``crop_rect`` is
                 ``(X, Y, W, H)``, and ``value1``, ``value2`` etc. are the
                 parameter values.
        """
        valid_chars = '$0123456789abcdefABCDEF,' + chars
        param_string = ''
        commas = 0

        while index < len(text) and text[index] in valid_chars:
            char = text[index]
            if char == ',':
                commas += 1
                if commas == num:
                    break
            param_string += char
            index += 1
        params = get_params(param_string, num, defaults)

        x = y = 0
        width = height = None
        if index < len(text) and text[index] == '{':
            index, x, y, width, height = parse_ints(text, index + 1, 4, (0, 0, None, None))
            index += 1

        if index < len(text) and text[index] == '(':
            end = text.index(')', index) + 1
            fname = text[index + 1:end - 1]
        else:
            end = index
        img_path = self.image_path(fname, path_id)

        return [end, img_path, (x, y, width, height)] + params

    def _expand_item_macro(self, macro, text, index, cwd, items, path_id, def_link_text):
        end, anchor, link_text = parse_params(text, index)
        if anchor and link_text == '':
            for name, title, contents in items:
                if anchor[1:] == name:
                    link_text = title
                    break
            else:
                raise MacroParsingError("Cannot determine title of item: {0}{1}()".format(macro, anchor))
        if link_text is None:
            link_text = def_link_text
        items_file = FileInfo.relpath(cwd, self.paths[path_id])
        link = '<a class="link" href="{0}{1}">{2}</a>'.format(items_file, anchor, link_text)
        return end, link

    def expand_bug(self, text, index, cwd):
        # #BUG[#name][(link text)]
        return self._expand_item_macro('#BUG', text, index, cwd, self.bugs, P_BUGS, 'bug')

    def expand_call(self, text, index, cwd):
        # #CALL:methodName(args)
        macro = '#CALL'
        if text[index] != ':':
            raise MacroParsingError("Malformed macro: {0}{1}...".format(macro, text[index]))
        end, method_name, arg_string = parse_params(text, index + 1, chars='_')
        if not hasattr(self, method_name):
            warn("Unknown method name in {0} macro: {1}".format(macro, method_name))
            return end, ''
        method = getattr(self, method_name)
        if not inspect.ismethod(method):
            raise MacroParsingError("Uncallable method name: {0}".format(method_name))
        if arg_string is None:
            raise MacroParsingError("No argument list specified: {0}{1}".format(macro, text[index:end]))
        args = [cwd] + get_params(arg_string)
        retval = method(*args)
        if retval is None:
            retval = ''
        return end, retval

    def expand_chr(self, text, index, cwd):
        # #CHRnum or #CHR(num)
        if text[index:].startswith('('):
            offset = 1
        else:
            offset = 0
        end, num = parse_ints(text, index + offset, 1)
        return end + offset, '&#{0};'.format(num)

    def expand_d(self, text, index, cwd):
        # #Daddr
        end, addr = parse_ints(text, index, 1)
        entry = self.get_entry(addr)
        if entry:
            if entry.description:
                return end, entry.description
            raise MacroParsingError('Entry at {0} has no description'.format(addr))
        raise MacroParsingError('Cannot determine description for nonexistent entry at {0}'.format(addr))

    def expand_erefs(self, text, index, cwd):
        # #EREFSaddr
        end, address = parse_ints(text, index, 1)
        ereferrers = self.get_entry_point_refs(address)
        if not ereferrers:
            raise MacroParsingError('Entry point at {0} has no referrers'.format(address))
        if len(ereferrers) == 1:
            html = 'routine at '
        else:
            ereferrers.sort()
            html = 'routines at '
            html += ', '.join('#R{}'.format(addr) for addr in ereferrers[:-1])
            html += ' and '
        html += '#R{}'.format(ereferrers[-1])
        return end, html

    def expand_fact(self, text, index, cwd):
        # #FACT[#name][(link text)]
        return self._expand_item_macro('#FACT', text, index, cwd, self.facts, P_FACTS, 'fact')

    def expand_font(self, text, index, cwd):
        # #FONTaddr,chars[,attr,scale][{X,Y,W,H}][(fname)]
        end, img_path, crop_rect, addr, chars, attr, scale = self.parse_image_params(text, index, 4, (56, 2), 'FontImagePath', 'font')
        if self.need_image(img_path):
            full_width, font_udg_array = self.get_font_udg_array(addr, chars, attr)
            if crop_rect[2] is None:
                crop_rect = (crop_rect[0], crop_rect[1], full_width * scale, crop_rect[3])
            self.write_image(img_path, font_udg_array, crop_rect, scale)
        return end, self.img_element(cwd, img_path)

    def expand_html(self, text, index, cwd):
        # #HTML(text)
        delim1 = text[index]
        delim2 = HTML_MACRO_DELIMITERS.get(delim1, delim1)
        start = index + 1
        end = text.find(delim2, start)
        if end < start:
            raise MacroParsingError("No terminating delimiter: {0}{1}".format('#HTML', text[index:]))
        return end + 1, text[start:end]

    def expand_link(self, text, index, cwd):
        # #LINK:PageId[#name](link text)
        macro = '#LINK'
        if text[index] != ':':
            raise MacroParsingError("Malformed macro: {0}{1}...".format(macro, text[index]))
        end, page_id, link_text = parse_params(text, index + 1)
        anchor = ''
        if '#' in page_id:
            page_id, anchor = page_id.split('#')
            anchor = '#' + anchor
        if page_id not in self.paths:
            raise MacroParsingError("Unknown page ID: {0}".format(page_id))
        if link_text == '':
            link_text = self.links[page_id][0]
        href = FileInfo.relpath(cwd, self.paths[page_id])
        if not link_text:
            raise MacroParsingError("No link text: {0}{1}".format(macro, text[index:end]))
        link = '<a class="link" href="{0}{1}">{2}</a>'.format(href, anchor, link_text)
        return end, link

    def expand_list(self, text, index, cwd):
        # #LIST[(class)]<items>LIST#
        end, list_obj = self.list_parser.parse_text(text, index)
        return end, self.build_list(list_obj)

    def expand_poke(self, text, index, cwd):
        # #POKE[#name][(link text)]
        return self._expand_item_macro('#POKE', text, index, cwd, self.pokes, P_POKES, 'poke')

    def expand_pokes(self, text, index, cwd):
        # #POKESaddr,byte[,length,step][;addr,byte[,length,step];...]
        end, addr, byte, length, step = parse_ints(text, index, 4, (1, 1))
        self.snapshot[addr:addr + length * step:step] = [byte] * length
        while end < len(text) and text[end] == ';':
            end, addr, byte, length, step = parse_ints(text, end + 1, 4, (1, 1))
            self.snapshot[addr:addr + length * step:step] = [byte] * length
        return end, ''

    def expand_pops(self, text, index, cwd):
        # #POPS
        self.pop_snapshot()
        return index, ''

    def expand_pushs(self, text, index, cwd):
        # #PUSHS[name]
        end, name, p_text = parse_params(text, index)
        self.push_snapshot(name)
        return end, ''

    def expand_r(self, text, index, cwd):
        # #Raddr[@code][#anchor][(link text)]
        end, params, link_text = parse_params(text, index, chars='@')
        anchor = ''
        anchor_index = params.find('#')
        if anchor_index > 0:
            anchor = params[anchor_index:]
            params = params[:anchor_index]
        code_id = ''
        code_id_index = params.find('@')
        if code_id_index > 0:
            code_id = params[code_id_index + 1:]
            params = params[:code_id_index]
        if code_id:
            code_path = self.get_code_path(code_id)
            if code_path is None:
                raise MacroParsingError("Could not find code path for '{}' disassembly".format(code_id))
        else:
            code_path = self.code_path
        addr_str = params
        address = parse_int(addr_str)
        container = self.parser.get_container(address, code_id)
        if not code_id and not container:
            raise MacroParsingError('Could not find routine file containing {0}'.format(addr_str))
        inst_addr_str = self.parser.get_instruction_addr_str(address, code_id)
        if container:
            container_address = container.address
        else:
            container_address = address
        if address != container_address:
            anchor = '#{0}'.format(address)
        asm_label = self.parser.get_asm_label(address)
        ref_file = FileInfo.asm_relpath(cwd, container_address, code_path)
        link = '<a class="link" href="{0}{1}">{2}</a>'.format(ref_file, anchor, link_text or asm_label or inst_addr_str)
        return end, link

    def expand_refs(self, text, index, cwd):
        # #REFSaddr[(prefix)]
        end, addr_str, prefix = parse_params(text, index, '')
        address = parse_int(addr_str)
        entry = self.entries.get(address)
        if not entry:
            raise MacroParsingError('No entry at {0}'.format(addr_str))
        referrers = [ref.address for ref in entry.referrers]
        if referrers:
            if len(referrers) == 1:
                html = ('{0} routine at '.format(prefix)).lstrip()
            else:
                referrers.sort()
                html = ('{0} routines at '.format(prefix)).lstrip()
                html += ', '.join('#R{}'.format(addr) for addr in referrers[:-1])
                html += ' and '
            html += '#R{}'.format(referrers[-1])
        else:
            html = 'Not used directly by any other routines'
        return end, html

    def expand_reg(self, text, index, cwd):
        # #REGreg
        end = index
        while end < len(text) and text[end] in "abcdefhlirspxy'":
            end += 1
        reg = text[index:end]
        if not reg:
            raise MacroParsingError('Missing register argument')
        if len(reg) > 3:
            raise MacroParsingError('Bad register: "{0}"'.format(reg))
        if self.case == CASE_LOWER:
            reg_name = reg.lower()
        else:
            reg_name = reg.upper()
        return end, '<span class="register">{0}</span>'.format(reg_name)

    def expand_scr(self, text, index, cwd):
        # #SCR[scale,x,y,w,h,dfAddr,afAddr][{X,Y,W,H}][(fname)]
        end, scr_path, crop_rect, scale, x, y, w, h, df_addr, af_addr = self.parse_image_params(text, index, 7, (1, 0, 0, 32, 24, 16384, 22528), 'ScreenshotImagePath', 'scr')
        if self.need_image(scr_path):
            self.write_image(scr_path, self.screenshot(x, y, w, h, df_addr, af_addr), crop_rect, scale)
        return end, self.img_element(cwd, scr_path)

    def expand_space(self, text, index, cwd):
        # #SPACE[num] or #SPACE([num])
        if text[index:].startswith('('):
            offset = 1
        else:
            offset = 0
        end, num_sp = parse_ints(text, index + offset, 1, (1,))
        return end + offset, '&#160;' * num_sp

    def expand_table(self, text, index, cwd):
        # #TABLE[(class[,col1class[,col2class...]])]<rows>TABLE#
        end, table = self.table_parser.parse_text(text, index)
        return end, self.build_table(table)

    def expand_udg(self, text, index, cwd):
        # #UDGaddr[,attr,scale,step,inc,flip,rotate][:maskAddr[,maskStep]][{X,Y,W,H}][(fname)]
        path_id = 'UDGImagePath'
        udg_params = self.parse_image_params(text, index, 7, (56, 4, 1, 0, 0, 0), path_id)
        end = udg_params[0]
        if end < len(text) and text[end] == ':':
            mask_defaults = (udg_params[6],) # Default mask step value
            end, img_path, crop_rect, mask_addr, mask_step = self.parse_image_params(text, end + 1, 2, mask_defaults, path_id)
            udg_params[0:3] = [end, img_path, crop_rect]
            udg_params += [mask_addr, mask_step]
        else:
            udg_params += [None, None]
        end, udg_path, crop_rect, addr, attr, scale, step, inc, flip, rotate, mask_addr, mask_step = udg_params
        if udg_path is None:
            udg_path = self.image_path('udg{0}_{1}x{2}'.format(addr, attr, scale))
        if self.need_image(udg_path):
            udg_bytes = [(self.snapshot[addr + n * step] + inc) % 256 for n in range(8)]
            mask_bytes = None
            mask = mask_addr is not None
            if mask:
                mask_bytes = self.snapshot[mask_addr:mask_addr + 8 * mask_step:mask_step]
            udg = Udg(attr, udg_bytes, mask_bytes)
            udg.flip(flip)
            udg.rotate(rotate)
            self.write_image(udg_path, [[udg]], crop_rect, scale, mask)
        return end, self.img_element(cwd, udg_path)

    def expand_udgarray(self, text, index, cwd):
        # #UDGARRAYwidth[,attr,scale,step,inc,flip,rotate];addr1[,attr1,step1,inc1][:maskAddr1[,maskStep1]];...[{X,Y,W,H}](fname)
        udg_path_id = 'UDGImagePath'
        end, img_path, crop_rect, width, def_attr, scale, def_step, def_inc, flip, rotate = self.parse_image_params(text, index, 7, (56, 2, 1, 0, 0, 0), udg_path_id)
        udg_array = [[]]
        has_masks = False
        while end < len(text) and text[end] == ';':
            end, img_path, crop_rect, address, attr, step, inc = self.parse_image_params(text, end + 1, 4, (def_attr, def_step, def_inc), udg_path_id, chars='-x')
            udg_addresses = self._get_udg_addresses(address, width)
            mask_addresses = []
            if end < len(text) and text[end] == ':':
                end, img_path, crop_rect, mask_addr, mask_step = self.parse_image_params(text, end + 1, 2, (step,), udg_path_id, chars='-x')
                mask_addresses = self._get_udg_addresses(mask_addr, width)
            has_masks = len(mask_addresses) > 0
            mask_addresses += [None] * (len(udg_addresses) - len(mask_addresses))
            for u, m in zip(udg_addresses, mask_addresses):
                udg_bytes = [(self.snapshot[u + n * step] + inc) % 256 for n in range(8)]
                udg = Udg(attr, udg_bytes)
                if m is not None:
                    udg.mask = [self.snapshot[m + n * mask_step] for n in range(8)]
                if len(udg_array[-1]) == width:
                    udg_array.append([udg])
                else:
                    udg_array[-1].append(udg)
        if img_path is None:
            raise MacroParsingError('Missing filename: #UDGARRAY{0}'.format(text[index:end]))
        if self.need_image(img_path):
            if flip:
                self.flip_udgs(udg_array, flip)
            if rotate:
                self.rotate_udgs(udg_array, rotate)
            self.write_image(img_path, udg_array, crop_rect, scale, has_masks)
        return end, self.img_element(cwd, img_path)

    def expand_udgtable(self, text, index, cwd):
        return self.expand_table(text, index, cwd)

    def expand(self, text, cwd):
        if not text or text.find('#') < 0:
            return text

        while 1:
            search = re.search('#[A-Z]+', text)
            if not search:
                break
            marker = search.group()
            if not marker in self.macros:
                raise SkoolParsingError('Found unknown macro: {0}'.format(marker))
            repf = self.macros[marker]
            start, index = search.span()
            try:
                end, rep = repf(text, index, cwd)
            except UnsupportedMacroError:
                raise SkoolParsingError('Found unsupported macro: {0}'.format(marker))
            except MacroParsingError as e:
                raise SkoolParsingError('Error while parsing {0} macro: {1}'.format(marker, e.args[0]))
            text = text[:start] + rep + text[end:]

        return text

class FileInfo:
    """Utility class for file-related operations.

    :param topdir: The top-level directory.
    :param game_dir: The subdirectory of `topdir` in which to write all HTML
                     files and image files.
    :param replace_images: Whether existing images should be overwritten.
    """
    def __init__(self, topdir, game_dir, replace_images):
        self.game_dir = game_dir
        self.odir = join(topdir, game_dir)
        self.replace_images = replace_images

    # PY: open_file(self, *names, mode='w') in Python 3
    def open_file(self, *names, **kwargs):
        path = self.odir
        for name in names:
            path = join(path, name)
        if not isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        mode = kwargs.get('mode', 'w') # PY: Not needed in Python 3
        return open(path, mode)

    def need_image(self, image_path):
        return self.replace_images or not self.file_exists(image_path)

    def file_exists(self, fname):
        return isfile(join(self.odir, fname))

    @classmethod
    def relpath(cls, cwd, target):
        return posixpath.relpath(target, cwd)

    @classmethod
    def asm_fname(cls, address, path=''):
        return posixpath.normpath(join(path, '{0}.html'.format(address)))

    @classmethod
    def asm_relpath(cls, cwd, address, path):
        return cls.relpath(cwd, join(path, cls.asm_fname(address)))

class Udg(object):
    """Initialise the UDG.

    :param attr: The attribute byte.
    :param data: The graphic data (sequence of 8 bytes).
    :param mask: The mask data (sequence of 8 bytes).
    """
    def __init__(self, attr, data, mask=None):
        self.attr = attr
        self.data = data
        self.mask = mask

    def __repr__(self):
        if self.mask is None:
            return 'Udg({0}, {1})'.format(self.attr, self.data)
        return 'Udg({0}, {1}, {2})'.format(self.attr, self.data, self.mask)

    def __eq__(self, other):
        if type(other) is Udg:
            return self.attr == other.attr and self.data == other.data and self.mask == other.mask
        return False

    def _rotate_tile(self, tile_data):
        rotated = []
        b = 1
        while b < 129:
            rbyte = 0
            for byte in tile_data:
                rbyte //= 2
                if byte & b:
                    rbyte += 128
            rotated.append(rbyte)
            b *= 2
        rotated.reverse()
        return rotated

    def flip(self, flip=1):
        """Flip the UDG.

        :param flip: 1 to flip horizontally, 2 to flip vertically, or 3 to flip
                     horizontally and vertically.
        """
        if flip & 1:
            for i in range(8):
                self.data[i] = FLIP[self.data[i]]
                if self.mask:
                    self.mask[i] = FLIP[self.mask[i]]
        if flip & 2:
            self.data.reverse()
            if self.mask:
                self.mask.reverse()

    def rotate(self, rotate=1):
        """Rotate the UDG 90 degrees clockwise.

        :param rotate: The number of rotations to perform.
        """
        for i in range(rotate & 3):
            self.data = self._rotate_tile(self.data)
            if self.mask:
                self.mask = self._rotate_tile(self.mask)

    def copy(self):
        if self.mask:
            return Udg(self.attr, self.data[:], self.mask[:])
        return Udg(self.attr, self.data[:])
