# -*- coding: utf-8 -*-

# Copyright 2008-2015 Richard Dymond (rjdymond@gmail.com)
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

import posixpath
import os.path
from os.path import isfile, isdir, basename
from collections import defaultdict
try:
    from StringIO import StringIO
except ImportError:         # pragma: no cover
    from io import StringIO # pragma: no cover

from skoolkit import skoolmacro, SkoolKitError, warn, get_int_param, parse_int, VERSION
from skoolkit.defaults import REF_FILE
from skoolkit.image import ImageWriter
from skoolkit.refparser import RefParser
from skoolkit.skoolmacro import MacroParsingError, get_macros, expand_macros
from skoolkit.skoolparser import TableParser, ListParser, CASE_LOWER

#: The ID of the main disassembly.
MAIN_CODE_ID = 'main'

# Page IDs (as used in the [Paths], [Titles] and [Links] sections)
P_GAME_INDEX = 'GameIndex'
P_MEMORY_MAP = 'MemoryMap'
P_ROUTINES_MAP = 'RoutinesMap'
P_DATA_MAP = 'DataMap'
P_MESSAGES_MAP = 'MessagesMap'
P_UNUSED_MAP = 'UnusedMap'
P_GRAPHIC_GLITCHES = 'GraphicGlitches'
P_GSB = 'GameStatusBuffer'
P_GLOSSARY = 'Glossary'
P_FACTS = 'Facts'
P_BUGS = 'Bugs'
P_POKES = 'Pokes'
P_CHANGELOG = 'Changelog'

# Default image path ID
DEF_IMG_PATH = 'UDGImagePath'

# Default memory map entry types
DEF_MEMORY_MAP_ENTRY_TYPES = 'bcgstuw'

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
    :param case: The case in which to render register names produced by the
                 :ref:`REG` macro (:data:`~skoolkit.skoolparser.CASE_LOWER` for
                 lower case, anything else for upper case)
    :param code_id: The ID of the disassembly.
    """
    def __init__(self, skool_parser, ref_parser, file_info=None, case=None, code_id=MAIN_CODE_ID):
        self.parser = skool_parser
        self.ref_parser = ref_parser
        self.defaults = RefParser()
        self.defaults.parse(StringIO(REF_FILE))
        self.file_info = file_info
        self.case = case
        self.base = skool_parser.base

        colours = self._parse_colours(self.get_dictionary('Colours'))
        iw_options = self.get_dictionary('ImageWriter')
        self.image_writer = ImageWriter(colours, iw_options)
        self.default_image_format = self.image_writer.default_format
        self.frames = {}

        self.snapshot = self.parser.snapshot
        self._snapshots = [(self.snapshot, '')]
        self.asm_entry_dicts = {}
        self.map_entry_dicts = {}
        self.nonexistent_entry_dict = defaultdict(lambda: '', exists=0)
        self.memory_map = [e for e in self.parser.memory_map if e.ctl != 'i']

        self.table_parser = TableParser()
        self.list_parser = ListParser()
        self.macros = get_macros(self)

        self.game_vars = self.get_dictionary('Game')
        self.asm_anchor_template = self.game_vars['AddressAnchor']
        self.paths = self.get_dictionary('Paths')
        self.asm_fname_template = self.paths['CodeFiles']
        self.titles = self.get_dictionary('Titles')
        self.page_headers = self.get_dictionary('PageHeaders')
        links = self.get_dictionary('Links')

        self.page_ids = []
        self.pages = {}
        for page_id, contents in self.get_sections('PageContent'):
            self.pages[page_id] = {'PageContent': contents}
            self.page_ids.append(page_id)
        for page_id, details in self.get_dictionaries('Page'):
            if page_id not in self.page_ids:
                self.page_ids.append(page_id)
            page = self.pages.setdefault(page_id, {})
            page.update(details)
        for page_id, page in self.pages.items():
            path = page.get('Content')
            if path:
                self.page_ids.remove(page_id)
            else:
                path = '{}.html'.format(page_id)
            self.paths.setdefault(page_id, path)
            self.titles.setdefault(page_id, page_id)

        self.other_code = []
        other_code_indexes = set()
        for c_id, code in self.get_dictionaries('OtherCode'):
            code.setdefault('Source', '{}.skool'.format(c_id))
            self.other_code.append((c_id, code))
            index_page_id = code['IndexPageId'] = '{}-Index'.format(c_id)
            other_code_indexes.add(index_page_id)
            self.paths.setdefault(index_page_id, '{0}/{0}.html'.format(c_id))
            self.titles.setdefault(index_page_id, c_id)
            code_path_id = code['CodePathId'] = '{}-CodePath'.format(c_id)
            self.paths.setdefault(code_path_id, c_id)
            for entry_type in 'bcgstuw':
                asm_page_id = self._get_asm_page_id(c_id, entry_type)
                default_asm_page_id = self._get_asm_page_id(MAIN_CODE_ID, entry_type)
                self.titles.setdefault(asm_page_id, self.titles[default_asm_page_id])
                self.page_headers.setdefault(asm_page_id, self.page_headers[default_asm_page_id])

        self.gsb_includes = []
        for addr_str in self.game_vars.get('GameStatusBufferIncludes', '').split(','):
            address = parse_int(addr_str)
            if self.get_entry(address):
                self.gsb_includes.append(address)

        self.main_memory_maps = []
        self.memory_maps = {}
        for map_name, map_details in self.get_dictionaries('MemoryMap'):
            self.memory_maps[map_name] = map_details
            if map_name not in other_code_indexes and self._should_write_map(map_details):
                self.main_memory_maps.append(map_name)
                self.paths.setdefault(map_name, 'maps/{}.html'.format(map_name))
                self.titles.setdefault(map_name, map_name)

        for page_id, title in self.titles.items():
            self.page_headers.setdefault(page_id, title)
            links.setdefault(page_id, self.page_headers[page_id])
        self.links = self._parse_links(links)

        self.code_id = code_id
        self.code_path = self.get_code_path(code_id)
        if not self.game_vars.get('Game'):
            def_game_name, sep, suffix = basename(self.parser.skoolfile).rpartition('.')
            if not sep:
                def_game_name = suffix
            self.game_vars['Game'] = def_game_name
        self.game_name = self.game_vars['Game']
        self.game = self.game_vars.copy()
        link_operands = self.game_vars['LinkOperands']
        self.link_operands = tuple(op.upper() for op in link_operands.split(','))
        self.link_internal_operands = self.game_vars['LinkInternalOperands'] != '0'
        self.js_files = ()
        global_js = self.game_vars.get('JavaScript')
        if global_js:
            self.js_files = tuple(global_js.split(';'))

        self.bugs = self.get_sections('Bug', True)
        self.facts = self.get_sections('Fact', True)
        self.pokes = self.get_sections('Poke', True)
        self.graphic_glitches = self.get_sections('GraphicGlitch', True)
        self.glossary = []
        for term, paragraphs in self.get_sections('Glossary', True):
            anchor = term.lower().replace(' ', '_')
            self.glossary.append((anchor, term, paragraphs))
        self.changelog = self._get_changelog()

        self.templates = {}
        for name, template in self.get_sections('Template'):
            self.templates[name] = template
        self.game['Created'] = self.game['Created'].replace('$VERSION', VERSION)
        self.skoolkit = {}
        self.stylesheets = {}
        self.javascript = {}
        self.logo = {}
        self.template_subs = {
            'Game': self.game,
            'SkoolKit': self.skoolkit
        }

        self.init()

    def init(self):
        """Perform post-initialisation operations. This method is called after
        `__init__()` has completed. By default the method does nothing, but
        subclasses may override it.
        """
        return

    def warn(self, s):
        warn(s)

    def clone(self, skool_parser, code_id):
        the_clone = self.__class__(skool_parser, self.ref_parser, self.file_info, self.case, code_id)
        the_clone.set_style_sheet(self.game_vars['StyleSheet'])
        return the_clone

    def set_style_sheet(self, value):
        self.game_vars['StyleSheet'] = value

    def format_template(self, template_name, subs, default=None):
        template = self.templates.get(template_name, self.templates.get(default))
        subs.update(self.template_subs)
        return template.format(**subs)

    def _parse_colours(self, colour_specs):
        colours = {}
        for k, v in colour_specs.items():
            if v.startswith('#'):
                hex_rgb = v[1:7]
                if len(hex_rgb) == 3:
                    hex_rgb = '{0}{0}{1}{1}{2}{2}'.format(*hex_rgb)
                else:
                    hex_rgb = '0' * (6 - len(hex_rgb)) + hex_rgb
                values = [hex_rgb[i:i + 2] for i in range(0, 5, 2)]
                base = 16
            else:
                values = v.split(',')[:3]
                values.extend(['0'] * (3 - len(values)))
                base = 10
            try:
                colours[k] = tuple([int(n, base) for n in values])
            except ValueError:
                raise SkoolKitError("Invalid colour spec: {}={}".format(k, v))
        return colours

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
            return self.paths['CodePath']
        for c_id, code in self.other_code:
            if c_id.lower() == code_id.lower():
                return self.paths[code['CodePathId']]
        raise SkoolKitError("Cannot find code path for '{}' disassembly".format(code_id))

    def _get_asm_page_id(self, code_id, entry_type):
        if code_id == MAIN_CODE_ID:
            return 'Asm-{}'.format(entry_type)
        return '{}-Asm-{}'.format(code_id, entry_type)

    def get_dictionary(self, section_name):
        """Return a dictionary built from the contents of a `ref` file section.
        Each line in the section should be of the form ``X=Y``.
        """
        dictionary = self.defaults.get_dictionary(section_name)
        dictionary.update(self.ref_parser.get_dictionary(section_name))
        return dictionary

    def get_dictionaries(self, section_type):
        """Return a list of 2-tuples of the form ``(suffix, dict)`` derived
        from `ref` file sections whose names start with `section_type` followed
        by a colon. ``suffix`` is the part of the section name that follows the
        first colon, and ``dict`` is a dictionary built from the contents of
        that section; each line in the section should be of the form ``X=Y``.
        """
        dictionaries = []
        index = {}
        default_dicts = self.defaults.get_dictionaries(section_type)
        user_dicts = self.ref_parser.get_dictionaries(section_type)
        for suffix, dictionary in default_dicts + user_dicts:
            if suffix in index:
                dictionaries[index[suffix]][1].update(dictionary)
            else:
                index[suffix] = len(dictionaries)
                dictionaries.append((suffix, dictionary))
        return dictionaries

    def get_section(self, section_name, paragraphs=False, lines=False):
        """Return the contents of a `ref` file section.

        :param section_name: The section name.
        :param paragraphs: If `True`, return the contents as a list of
                           paragraphs.
        :param lines: If `True`, return the contents (or each paragraph) as a
                      list of lines; otherwise return the contents (or each
                      paragraph) as a single string.
        """
        if self.ref_parser.has_section(section_name):
            return self.ref_parser.get_section(section_name, paragraphs, lines)
        return self.defaults.get_section(section_name, paragraphs, lines)

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
        sections = []
        index = {}
        default_sections = self.defaults.get_sections(section_type, paragraphs, lines)
        user_sections = self.ref_parser.get_sections(section_type, paragraphs, lines)
        for section in default_sections + user_sections:
            suffix = ':'.join(section[:-1])
            if suffix in index:
                sections[index[suffix]] = section
            else:
                index[suffix] = len(sections)
                sections.append(section)
        return sections

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
        if len(self._snapshots) < 2:
            raise SkoolKitError("Cannot pop snapshot when snapshot stack is empty")
        self.snapshot = self._snapshots.pop()[0]

    def push_snapshot(self, name=''):
        """Save the current memory snapshot for later retrieval (by
        :meth:`~skoolkit.skoolhtml.HtmlWriter.pop_snapshot`), and put a copy in
        its place.

        :param name: An optional name for the snapshot.
        """
        self._snapshots.append((self.snapshot[:], name))

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

    def relpath(self, cwd, target):
        return posixpath.relpath(target, cwd)

    def asm_fname(self, address, path=''):
        try:
            return posixpath.normpath(join(path, self.asm_fname_template.format(address=address)))
        except:
            raise SkoolKitError("Cannot format filename ({}) with address={}".format(self.asm_fname_template, address))

    def asm_relpath(self, cwd, address, path):
        return self.relpath(cwd, join(path, self.asm_fname(address)))

    def asm_anchor(self, address):
        try:
            return self.asm_anchor_template.format(address=address)
        except:
            raise SkoolKitError("Cannot format anchor ({}) with address={}".format(self.asm_anchor_template, address))

    def join_paragraphs(self, paragraphs, cwd):
        lines = []
        for p in paragraphs:
            lines.append(self.format_template('paragraph', {'paragraph': self.expand(p, cwd).strip()}))
        return '\n'.join(lines)

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
        flipped_udgs = set()
        for row in udgs:
            for udg in row:
                if id(udg) not in flipped_udgs:
                    udg.flip(flip)
                    flipped_udgs.add(id(udg))
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
        rotated_udgs = set()
        for row in udgs:
            for udg in row:
                if id(udg) not in rotated_udgs:
                    udg.rotate(rotate)
                    rotated_udgs.add(id(udg))
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

    def get_font_udg_array(self, address, attr, message):
        udgs = []
        for c in message:
            a = address + 8 * (ord(c) - 32)
            udgs.append(Udg(attr, self.snapshot[a:a + 8]))
        return [udgs]

    def write_graphic_glitches(self):
        self._write_box_page(P_GRAPHIC_GLITCHES, self.graphic_glitches)

    def write_index(self):
        index_fname = self.paths[P_GAME_INDEX]
        cwd = self._set_cwd(P_GAME_INDEX, index_fname)

        link_groups = {}
        for section_id, header_text, page_list in self.get_sections('Index', False, True):
            link_groups[section_id] = (header_text, page_list)
        sections = {}
        for section_id, (header_text, page_list) in link_groups.items():
            links = []
            for page_id in page_list:
                fname = self.paths.get(page_id)
                if fname and self.file_exists(fname):
                    link_file = self.relpath(cwd, fname)
                    link_text = self.links[page_id]
                    links.append((link_file, link_text[0], link_text[1]))
            sections[section_id] = (header_text, links)
        other_code_links = []
        for code_id, code in self.other_code:
            fname = self.paths[code['IndexPageId']]
            if self.file_exists(fname):
                link_file = self.relpath(cwd, fname)
                link_text = self.links[code['IndexPageId']]
                other_code_links.append((link_file, link_text[0], link_text[1]))
        sections['OtherCode'] = ('Other code', other_code_links)

        sections_html = []
        index = self.get_section('Index', False, True)
        for section_id in index:
            header, links = sections.get(section_id, ('', ()))
            if links:
                items = []
                for href, link_text, other_text in links:
                    t_index_section_item_subs = {
                        'href': href,
                        'link_text': link_text,
                        'other_text': other_text
                    }
                    items.append(self.format_template('index_section_item', t_index_section_item_subs))
                t_index_section_subs = {
                    'header': header,
                    'm_index_section_item': '\n'.join(items)
                }
                sections_html.append(self.format_template('index_section', t_index_section_subs))

        subs = {'m_index_section': '\n'.join(sections_html)}
        html = self.format_page(P_GAME_INDEX, cwd, subs)
        self.write_file(index_fname, html)

    def _get_entry_dict(self, cwd, entry, desc=True):
        if desc:
            description = self.join_paragraphs(entry.details, cwd)
        else:
            description = ''
        return {
            'exists': 1,
            'labels': int(any([instruction.asm_label for instruction in entry.instructions])),
            'type': entry.ctl,
            'location': entry.address,
            'address': entry.addr_str,
            'page': entry.address // 256,
            'byte': entry.address % 256,
            'label': self.parser.get_asm_label(entry.address),
            'description': description,
            'href': self.asm_relpath(cwd, entry.address, self.code_path),
            'size': entry.size,
            'title': self.expand(entry.description, cwd)
        }

    def _get_map_entry_dict(self, cwd, entry, desc):
        address = entry.address
        key = (cwd, address, desc)
        if key not in self.map_entry_dicts:
            self.map_entry_dicts[key] = self._get_entry_dict(cwd, entry, desc)
        return self.map_entry_dicts[key]

    def _get_asm_entry_dict(self, cwd, index, map_file):
        entry = self.memory_map[index]
        address = entry.address
        if address not in self.asm_entry_dicts:
            entry_dict = self._get_entry_dict(cwd, entry)
            entry_dict['map_href'] = '{}#{}'.format(self.relpath(cwd, map_file), self.asm_anchor(entry.address))
            self.asm_entry_dicts[address] = entry_dict
        return self.asm_entry_dicts[address]

    def _format_contents_list_items(self, link_list):
        items = []
        for anchor, title in link_list:
            subs = {'href': '#' + anchor, 'title': title}
            items.append(self.format_template('contents_list_item', subs))
        return '\n'.join(items)

    def _write_box_page(self, page_id, entries):
        fname = self.paths[page_id]
        cwd = self._set_cwd(page_id, fname)
        entries_html = []
        for i, (anchor, title, paragraphs) in enumerate(entries):
            t_reference_entry_subs = {
                't_anchor': self.format_anchor(anchor),
                'num': 1 + i % 2,
                'title': title,
                'contents': self.join_paragraphs(paragraphs, cwd)
            }
            entries_html.append(self.format_template('reference_entry', t_reference_entry_subs))
        subs = {
            'm_contents_list_item': self._format_contents_list_items([(anchor, title) for anchor, title, p in entries]),
            'entries': '\n'.join(entries_html),
        }
        html = self.format_page(page_id, cwd, subs, 'Reference')
        self.write_file(fname, html)

    def write_pokes(self):
        self._write_box_page(P_POKES, self.pokes)

    def write_bugs(self):
        self._write_box_page(P_BUGS, self.bugs)

    def write_facts(self):
        self._write_box_page(P_FACTS, self.facts)

    def write_glossary(self):
        self._write_box_page(P_GLOSSARY, self.glossary)

    def _build_changelog_items(self, items, level=0):
        if not items:
            return ''
        changelog_items = []
        for item, subitems in items:
            if subitems:
                item = '{}\n{}\n'.format(item, self._build_changelog_items(subitems, level + 1))
            changelog_items.append(self.format_template('changelog_item', {'item': item}, 'list_item'))
        if level > 0:
            indent = level
        else:
            indent = ''
        t_changelog_item_list_subs = {
            'indent': indent,
            'm_changelog_item': '\n'.join(changelog_items)
        }
        return self.format_template('changelog_item_list', t_changelog_item_list_subs)

    def write_changelog(self):
        fname = self.paths[P_CHANGELOG]
        cwd = self._set_cwd(P_CHANGELOG, fname)

        contents = []
        entries = []
        for j, (title, description, items) in enumerate(self.changelog):
            contents.append((title, title))
            changelog_items = []
            for item in items:
                indents = [(0, changelog_items)]
                for line in item:
                    subitems = indents[-1][1]
                    item_text = self.expand(line.strip(), cwd)
                    new_indent = len(line) - len(line.lstrip())
                    if new_indent == indents[-1][0]:
                        subitems.append([item_text, None])
                    elif new_indent > indents[-1][0]:
                        new_subitems = [[item_text, None]]
                        subitems[-1][1] = new_subitems
                        indents.append((new_indent, new_subitems))
                    else:
                        while new_indent < indents[-1][0]:
                            indents.pop()
                        subitems = indents[-1][1]
                        subitems.append([item_text, None])
            t_changelog_entry_subs = {
                't_anchor': self.format_anchor(title),
                'num': 1 + j % 2,
                'title': title,
                'description': self.expand(description, cwd),
                't_changelog_item_list': self._build_changelog_items(changelog_items)
            }
            entries.append(self.format_template('changelog_entry', t_changelog_entry_subs))

        subs = {
            'm_contents_list_item': self._format_contents_list_items(contents),
            'entries': '\n'.join(entries),
        }
        html = self.format_page(P_CHANGELOG, cwd, subs, 'Reference')
        self.write_file(fname, html)

    def format_registers(self, cwd, registers, entry_dict):
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

        reg_lists = []
        subs = {'entry': entry_dict}
        for reg_type, registers in (('input', input_values), ('output', output_values)):
            registers_html = []
            entry_dict[reg_type] = min(len(registers), 1)
            for reg in registers:
                subs['name'] = reg.name
                subs['description'] = self.expand(reg.contents, cwd)
                registers_html.append(self.format_template('asm_register', subs))
            reg_lists.append('\n'.join(registers_html))
        return reg_lists

    def format_entry_comment(self, cwd, entry_dict, paragraphs, anchor=''):
        t_asm_comment_subs = {
            'entry': entry_dict,
            't_anchor': anchor,
            'm_paragraph': self.join_paragraphs(paragraphs, cwd)
        }
        return self.format_template('asm_comment', t_asm_comment_subs)

    def write_entry(self, cwd, index, map_file):
        entry = self.memory_map[index]
        fname = join(cwd, self.asm_fname(entry.address))
        page_id = self._get_asm_page_id(self.code_id, entry.ctl)
        self._set_cwd(page_id, fname)

        entry_dict = self._get_asm_entry_dict(cwd, index, map_file)
        entry_dict['annotated'] = int(any([i.comment and i.comment.text for i in entry.instructions]))

        if index:
            prev_entry_dict = self._get_asm_entry_dict(cwd, index - 1, map_file)
        else:
            prev_entry_dict = self.nonexistent_entry_dict
        if index + 1 < len(self.memory_map):
            next_entry_dict = self._get_asm_entry_dict(cwd, index + 1, map_file)
        else:
            next_entry_dict = self.nonexistent_entry_dict

        input_reg, output_reg = self.format_registers(cwd, entry.registers, entry_dict)

        lines = []
        instruction_subs = {'entry': entry_dict}
        for instruction in entry.instructions:
            address = instruction.address
            anchor = self.format_anchor(self.asm_anchor(address))
            if instruction.mid_block_comment:
                lines.append(self.format_entry_comment(cwd, entry_dict, instruction.mid_block_comment, anchor))

            operation, reference = instruction.operation, instruction.reference
            operation_u = operation.upper()
            if reference and operation_u.startswith(self.link_operands):
                asm_label = self.parser.get_asm_label(reference.address)
                external_ref = entry != reference.entry
                if external_ref or asm_label or self.link_internal_operands:
                    entry_address = reference.entry.address
                    if external_ref and reference.address == entry_address:
                        name = ''
                    else:
                        name = '#{}'.format(self.asm_anchor(reference.address))
                    if reference.entry.asm_id:
                        # This is a reference to an entry in another disassembly
                        entry_file = self.asm_relpath(cwd, entry_address, self.get_code_path(reference.entry.asm_id))
                    else:
                        # This is a reference to an entry in the same disassembly
                        entry_file = self.asm_fname(entry_address)
                    if asm_label and not operation_u.startswith('RST'):
                        link_text = asm_label
                    else:
                        link_text = reference.addr_str
                    link = self.format_link(entry_file + name, link_text)
                    operation = operation.replace(reference.addr_str, link)

            comment = instruction.comment
            if comment:
                comment_rowspan = comment.rowspan
                comment_text = self.expand(comment.text, cwd)
                annotated = 1
            else:
                comment_rowspan = 1
                comment_text = ''
                annotated = 0
            instruction_subs['address'] = instruction.addr_str
            instruction_subs['called'] = 1 + int(instruction.ctl in 'c*')
            instruction_subs['label'] = instruction.asm_label or ''
            instruction_subs['operation'] = operation
            instruction_subs['comment'] = comment_text
            instruction_subs['comment_rowspan'] = comment_rowspan
            instruction_subs['annotated'] = annotated
            instruction_subs['t_anchor'] = anchor
            lines.append(self.format_template('asm_instruction', instruction_subs))

        if entry.end_comment:
            lines.append(self.format_entry_comment(cwd, entry_dict, entry.end_comment))

        subs = {
            'prev_entry': prev_entry_dict,
            'entry': entry_dict,
            'next_entry': next_entry_dict,
            'registers_input': input_reg,
            'registers_output': output_reg,
            'disassembly': '\n'.join(lines)
        }
        self.write_file(fname, self.format_page(page_id, cwd, subs, 'Asm'))

    def write_entries(self, cwd, map_file):
        for i in range(len(self.memory_map)):
            self.write_entry(cwd, i, map_file)

    def write_asm_entries(self):
        self.write_entries(self.code_path, self.paths[P_MEMORY_MAP])

    def _should_write_map(self, map_details):
        if map_details.get('Write') == '0':
            return False
        entry_types = map_details.get('EntryTypes', DEF_MEMORY_MAP_ENTRY_TYPES)
        if 'G' in entry_types and self.gsb_includes:
            return True
        return any([entry.ctl in entry_types for entry in self.memory_map])

    def write_map(self, map_name):
        fname = self.paths[map_name]
        cwd = self._set_cwd(map_name, fname)

        map_details = self.memory_maps.get(map_name, {})
        entry_types = map_details.get('EntryTypes', DEF_MEMORY_MAP_ENTRY_TYPES)
        map_dict = {
            'EntryDescriptions': map_details.get('EntryDescriptions', '0'),
            'EntryTypes': entry_types,
            'Intro': self.expand(map_details.get('Intro', ''), cwd),
            'LengthColumn': map_details.get('LengthColumn', '0'),
            'PageByteColumns': map_details.get('PageByteColumns', '0')
        }
        desc = map_dict['EntryDescriptions'] != '0'

        map_entries = []
        t_map_entry_subs = {'MemoryMap': map_dict}
        for entry in self.memory_map:
            if entry.ctl in entry_types or ('G' in entry_types and entry.address in self.gsb_includes):
                t_map_entry_subs['entry'] = self._get_map_entry_dict(cwd, entry, desc)
                t_map_entry_subs['t_anchor'] = self.format_anchor(self.asm_anchor(entry.address))
                map_entries.append(self.format_template('map_entry', t_map_entry_subs))

        subs = {
            'MemoryMap': map_dict,
            'm_map_entry': '\n'.join(map_entries)
        }
        html = self.format_page(map_name, cwd, subs, P_MEMORY_MAP)
        self.write_file(fname, html)

    def write_page(self, page_id):
        fname = self.paths[page_id]
        cwd = self._set_cwd(page_id, fname)
        page = self.pages[page_id]
        subs = {'content': self.expand(page.get('PageContent', ''), cwd)}
        js = page.get('JavaScript')
        html = self.format_page(page_id, cwd, subs, 'Page', js)
        self.write_file(fname, html)

    def write_file(self, fname, contents):
        with self.file_info.open_file(fname) as f:
            f.write(contents)

    def _set_cwd(self, page_id, fname):
        cwd = os.path.dirname(fname)
        self.skoolkit['page_id'] = page_id
        self.skoolkit['index_href'] = self.relpath(cwd, self.paths[P_GAME_INDEX])
        self.skoolkit['title'] = self.titles[page_id]
        self.skoolkit['page_header'] = self.page_headers[page_id]
        self.game['Logo'] = self.game['LogoImage'] = self._get_logo(cwd)
        return cwd

    def format_page(self, page_id, cwd, subs, default=None, js=None):
        if cwd not in self.stylesheets:
            stylesheets = []
            for css_file in self.game_vars['StyleSheet'].split(';'):
                t_stylesheet_subs = {'href': self.relpath(cwd, join(self.paths['StyleSheetPath'], basename(css_file)))}
                stylesheets.append(self.format_template('stylesheet', t_stylesheet_subs))
            self.stylesheets[cwd] = '\n'.join(stylesheets)

        js_key = (cwd, js)
        if js_key not in self.javascript:
            javascript = []
            if js:
                js_files = list(self.js_files)
                js_files.extend(js.split(';'))
            else:
                js_files = self.js_files
            for js_file in js_files:
                t_javascript_subs = {'src': self.relpath(cwd, join(self.paths['JavaScriptPath'], basename(js_file)))}
                javascript.append(self.format_template('javascript', t_javascript_subs))
            self.javascript[js_key] = '\n'.join(javascript)

        subs['m_stylesheet'] = self.stylesheets[cwd]
        subs['m_javascript'] = self.javascript[js_key]
        subs['t_footer'] = self.format_template('footer', {})
        return self.format_template(page_id, subs, default)

    def _get_logo(self, cwd):
        if cwd not in self.logo:
            logo_macro = self.game_vars.get('Logo')
            if logo_macro:
                self.logo[cwd] = self.expand(logo_macro, cwd)
            else:
                logo_image = self.game_vars.get('LogoImage')
                if logo_image and self.file_exists(logo_image):
                    self.logo[cwd] = self.format_img(self.game_name, self.relpath(cwd, logo_image))
                else:
                    self.logo[cwd] = self.game_name
        return self.logo[cwd]

    def format_anchor(self, anchor):
        return self.format_template('anchor', {'anchor': anchor})

    def format_link(self, href, link_text):
        return self.format_template('link', {'href': href, 'link_text': link_text})

    def format_img(self, alt, src):
        return self.format_template('img', {'alt': alt, 'src': src})

    def _get_image_format(self, image_path):
        img_file_ext = image_path.lower()[-4:]
        if img_file_ext == '.png':
            return 'png'
        if img_file_ext == '.gif':
            return 'gif'
        raise SkoolKitError('Unsupported image file format: {}'.format(image_path))

    def write_image(self, image_path, udgs, crop_rect=(), scale=2, mask=0):
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
        :param mask: The type of mask to apply to the tiles: 0 (no mask), 1
                     (OR-AND mask), or 2 (AND-OR mask).
        """
        frame = Frame(udgs, scale, mask, *crop_rect)
        self.write_animated_image(image_path, [frame])

    def write_animated_image(self, image_path, frames):
        """Create an animated image and write it to a file.

        :param image_path: The full path of the file to which to write the
                           image (relative to the root directory of the
                           disassembly).
        :param frames: A list of the frames (instances of
                       :class:`~skoolkit.skoolhtml.Frame`) from which to build
                       the image.
        """
        img_format = self._get_image_format(image_path)
        f = self.file_info.open_file(image_path, mode='wb')
        self.image_writer.write_image(frames, f, img_format)
        f.close()
        self.file_info.add_image(image_path)

    def build_table(self, table):
        rows = []
        for row in table.rows:
            cells = []
            for cell in row:
                cell_subs = {
                    'colspan': cell.colspan,
                    'rowspan': cell.rowspan,
                    'contents': cell.contents
                }
                if cell.header:
                    cells.append(self.format_template('table_header_cell', cell_subs))
                else:
                    cell_class = cell.cell_class
                    if cell.transparent:
                        cell_class += " transparent"
                    cell_subs['class'] = cell_class.lstrip()
                    cells.append(self.format_template('table_cell', cell_subs))
            rows.append(self.format_template('table_row', {'cells': '\n'.join(cells)}))
        table_subs = {'class': table.table_class, 'm_table_row': '\n'.join(rows)}
        return self.format_template('table', table_subs)

    def build_list(self, list_obj):
        items = [self.format_template('list_item', {'item': i}) for i in list_obj.items]
        list_subs = {'class': list_obj.css_class, 'm_list_item': '\n'.join(items)}
        return self.format_template('list', list_subs)

    def _get_udg_addresses(self, addr_spec, width):
        if type(addr_spec) is int:
            return [addr_spec]
        num = 1
        addr = addr_spec
        if 'x' in addr:
            addr, num = addr_spec.split('x', 1)
            try:
                num = get_int_param(num)
            except ValueError:
                raise MacroParsingError("Invalid address range specification: {}".format(addr_spec))
        try:
            elements = [get_int_param(n) for n in addr.split('-', 3)]
        except ValueError:
            raise MacroParsingError("Invalid address range specification: {}".format(addr_spec))
        if len(elements) < 2:
            elements.append(elements[0])
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
        return self.format_img(alt, self.relpath(cwd, image_path))

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

    def parse_image_params(self, text, index, num=0, defaults=(),
                           path_id=DEF_IMG_PATH, fname='', chars='', ints=None,
                           names=(), frame=False, alt=False):
        """Parse a string of the form:

        ``params[{x,y,width,height}][(fname[*frame][|alt])]``

        The parameter string ``params`` may contain comma-separated values and
        is parsed until either the end is reached, or an invalid character is
        encountered. The default set of valid characters consists of the comma,
        '$', the digits 0-9, and the letters A-F and a-f; if `names` is not
        empty, the set of valid characters also includes '=' and the letters
        g-z.

        :param text: The text to parse.
        :param index: The index at which to start parsing.
        :param num: The maximum number of parameters to parse; this is set to
                    the number of elements in `names` if that list is not
                    empty.
        :param defaults: The default values of the optional parameters.
        :param path_id: The ID of the target directory for the image file (as
                        defined in the :ref:`paths` section of the `ref` file).
        :param fname: The default base name of the image file.
        :param chars: Characters to consider valid in addition to those in the
                      default set.
        :param ints: A list of the indexes (0-based) of the parameters that
                     must evaluate to an integer; if `None`, every parameter
                     must evaluate to an integer.
        :param names: The names of the parameters; if not empty, keyword
                      arguments in the parameter string ``params`` are parsed.
        :param frame: Whether to parse and return the frame name.
        :param alt: Whether to parse and return the alt text.
        :return: A list of the form
                 ``[end, image_path, frame, alt, crop_rect, value1, value2...]``,
                 where:

                 * ``end`` is the index at which parsing terminated
                 * ``image_path`` is either the full path of the image file
                   (relative to the root directory of the disassembly) or
                   ``fname`` (if `path_id` is blank or `None`)
                 * ``frame`` is the frame name (present only if `frame` is
                   `True`)
                 * ``alt`` is the alt text (present only if `alt` is `True`)
                 * ``crop_rect`` is ``(x, y, width, height)``
                 * ``value1``, ``value2`` etc. are the parameter values
        """
        valid_chars = '$0123456789abcdefABCDEF,' + chars
        if names:
            valid_chars += 'ghijklmnopqrstuvwxyz='
            num = len(names)
        end, param_string, p_text = skoolmacro.parse_params(text, index, only_chars=valid_chars)
        params = skoolmacro.get_params(param_string, num, defaults, ints, names)

        defaults = (0, 0, None, None)
        if end < len(text) and text[end] == '{':
            param_names = ('x', 'y', 'width', 'height')
            end, x, y, width, height = skoolmacro.parse_ints(text, end + 1, defaults=defaults, names=param_names)
            end, param_string, p_text = skoolmacro.parse_params(text, end, only_chars='}')
        else:
            x, y, width, height = defaults

        alt_text = None
        frame_name = None
        if p_text:
            if alt and '|' in p_text:
                p_text, alt_text = p_text.split('|', 1)
            if frame and '*' in p_text:
                p_text, frame_name = p_text.split('*', 1)
            if p_text:
                fname = p_text
            elif frame_name:
                fname = ''
            if frame_name == '':
                frame_name = fname
        if path_id:
            img_path = self.image_path(fname, path_id)
        else:
            img_path = fname

        retval = [end, img_path, (x, y, width, height)] + params
        if alt:
            retval.insert(2, alt_text)
        if frame:
            retval.insert(2, frame_name)
        return retval

    def _expand_item_macro(self, item, link_text, cwd, items, path_id):
        if item and link_text == '':
            for name, title, contents in items:
                if item == name:
                    link_text = title
                    break
            else:
                raise MacroParsingError("Cannot determine title of item '{}'".format(item))
        href = self.relpath(cwd, self.paths[path_id])
        if item:
            href += '#' + item
        return self.format_link(href, link_text)

    def expand_bug(self, text, index, cwd):
        end, item, link_text = skoolmacro.parse_bug(text, index)
        return end, self._expand_item_macro(item, link_text, cwd, self.bugs, P_BUGS)

    def expand_call(self, text, index, cwd):
        return skoolmacro.parse_call(text, index, self, cwd)

    def expand_chr(self, text, index, cwd):
        end, num = skoolmacro.parse_chr(text, index)
        return end, '&#{};'.format(num)

    def expand_d(self, text, index, cwd):
        return skoolmacro.parse_d(text, index, self)

    def expand_erefs(self, text, index, cwd):
        return skoolmacro.parse_erefs(text, index, self)

    def expand_fact(self, text, index, cwd):
        end, item, link_text = skoolmacro.parse_fact(text, index)
        return end, self._expand_item_macro(item, link_text, cwd, self.facts, P_FACTS)

    def expand_font(self, text, index, cwd):
        # #FONT[:(text)]addr[,chars,attr,scale][{x,y,width,height}][(fname)]
        if index < len(text) and text[index] == ':':
            index, message = skoolmacro.get_text_param(text, index + 1)
            if not message:
                raise MacroParsingError("Empty message: {}".format(text[index - 2:index]))
        else:
            message = ''.join([chr(n) for n in range(32, 128)])

        param_names = ('addr', 'chars', 'attr', 'scale')
        defaults = (len(message), 56, 2)
        params = self.parse_image_params(text, index, defaults=defaults, path_id='FontImagePath', fname='font', names=param_names, frame=True, alt=True)
        end, img_path, frame, alt, crop_rect, addr, chars, attr, scale = params
        need_image = img_path and self.need_image(img_path)
        if frame or need_image:
            udg_array = self.get_font_udg_array(addr, attr, message[:chars])
            if need_image:
                self.write_image(img_path, udg_array, crop_rect, scale)
            if frame:
                self.frames[frame] = Frame(udg_array, scale, 0, *crop_rect)
        if img_path:
            return end, self.img_element(cwd, img_path, alt)
        return end, ''

    def expand_html(self, text, index, cwd):
        return skoolmacro.parse_html(text, index)

    def expand_link(self, text, index, cwd):
        end, page_id, anchor, link_text = skoolmacro.parse_link(text, index)
        if page_id not in self.paths:
            raise MacroParsingError("Unknown page ID: {}".format(page_id))
        if link_text == '':
            link_text = self.links[page_id][0]
        href = self.relpath(cwd, self.paths[page_id]) + anchor
        return end, self.format_link(href, link_text)

    def expand_list(self, text, index, cwd):
        # #LIST[(class)]<items>LIST#
        end, list_obj = self.list_parser.parse_text(text, index)
        return end, self.build_list(list_obj)

    def expand_poke(self, text, index, cwd):
        end, item, link_text = skoolmacro.parse_poke(text, index)
        return end, self._expand_item_macro(item, link_text, cwd, self.pokes, P_POKES)

    def expand_pokes(self, text, index, cwd):
        return skoolmacro.parse_pokes(text, index, self.snapshot)

    def expand_pops(self, text, index, cwd):
        return skoolmacro.parse_pops(text, index, self)

    def expand_pushs(self, text, index, cwd):
        return skoolmacro.parse_pushs(text, index, self)

    def expand_r(self, text, index, cwd):
        end, addr_str, address, code_id, anchor, link_text = skoolmacro.parse_r(text, index)
        if code_id:
            code_path = self.get_code_path(code_id)
        else:
            code_path = self.code_path
        container = self.parser.get_container(address, code_id)
        if not code_id and not container:
            raise MacroParsingError('Could not find routine file containing {}'.format(addr_str))
        inst_addr_str = self.parser.get_instruction_addr_str(address, code_id)
        if container:
            container_address = container.address
        else:
            container_address = address
        if not anchor and address != container_address:
            anchor = '#{}'.format(self.asm_anchor(address))
        asm_label = self.parser.get_asm_label(address)
        ref_file = self.asm_relpath(cwd, container_address, code_path)
        return end, self.format_link(ref_file + anchor, link_text or asm_label or inst_addr_str)

    def expand_refs(self, text, index, cwd):
        return skoolmacro.parse_refs(text, index, self.parser)

    def expand_reg(self, text, index, cwd):
        end, reg = skoolmacro.parse_reg(text, index, self.case == CASE_LOWER)
        return end, self.format_template('reg', {'reg': reg})

    def expand_scr(self, text, index, cwd):
        # #SCR[scale,x,y,w,h,df,af][{x,y,width,height}][(fname)]
        param_names = ('scale', 'x', 'y', 'w', 'h', 'df', 'af')
        defaults = (1, 0, 0, 32, 24, 16384, 22528)
        params = self.parse_image_params(text, index, defaults=defaults, path_id='ScreenshotImagePath', fname='scr', names=param_names, frame=True, alt=True)
        end, scr_path, frame, alt, crop_rect, scale, x, y, w, h, df, af = params
        need_image = scr_path and self.need_image(scr_path)
        if frame or need_image:
            udgs = self.screenshot(x, y, w, h, df, af)
            if need_image:
                self.write_image(scr_path, udgs, crop_rect, scale)
            if frame:
                self.frames[frame] = Frame(udgs, scale, 0, *crop_rect)
        if scr_path:
            return end, self.img_element(cwd, scr_path, alt)
        return end, ''

    def expand_space(self, text, index, cwd):
        end, num_sp = skoolmacro.parse_space(text, index)
        return end, '&#160;' * num_sp

    def expand_table(self, text, index, cwd):
        # #TABLE[(class[,col1class[,col2class...]])]<rows>TABLE#
        end, table = self.table_parser.parse_text(text, index)
        return end, self.build_table(table)

    def expand_udg(self, text, index, cwd):
        # #UDGaddr[,attr,scale,step,inc,flip,rotate,mask][:addr[,step]][{x,y,width,height}][(fname)]
        path_id = 'UDGImagePath'
        param_names = ('addr', 'attr', 'scale', 'step', 'inc', 'flip', 'rotate', 'mask')
        defaults = (56, 4, 1, 0, 0, 0, 1)
        udg_params = self.parse_image_params(text, index, defaults=defaults, path_id=path_id, names=param_names, frame=True, alt=True)
        end, udg_path, frame, alt, crop_rect, addr, attr, scale, step, inc, flip, rotate, mask = udg_params
        if end < len(text) and text[end] == ':':
            mask_params = self.parse_image_params(text, end + 1, defaults=(step,), path_id=path_id, names=('addr', 'step'), frame=True, alt=True)
            end, udg_path, frame, alt, crop_rect, mask_addr, mask_step = mask_params
        else:
            mask_params = None
            mask = 0
        if not udg_path and not frame:
            udg_fname = 'udg{}_{}x{}'.format(addr, attr, scale)
            udg_path = self.image_path(udg_fname)
            if frame == '':
                frame = udg_fname
        need_image = udg_path and self.need_image(udg_path)
        if frame or need_image:
            udg_bytes = [(self.snapshot[addr + n * step] + inc) % 256 for n in range(8)]
            mask_bytes = None
            if mask and mask_params:
                mask_bytes = self.snapshot[mask_addr:mask_addr + 8 * mask_step:mask_step]
            udg = Udg(attr, udg_bytes, mask_bytes)
            udg.flip(flip)
            udg.rotate(rotate)
            udg_array = [[udg]]
            if need_image:
                self.write_image(udg_path, udg_array, crop_rect, scale, mask)
            if frame:
                self.frames[frame] = Frame(udg_array, scale, mask, *crop_rect)
        if udg_path:
            return end, self.img_element(cwd, udg_path, alt)
        return end, ''

    def _expand_udgarray_with_frames(self, text, index, cwd):
        end, frame_params, fname = skoolmacro.parse_params(text, index, except_chars=' (')
        if not fname:
            raise MacroParsingError('Missing filename: #UDGARRAY{}'.format(text[index:end]))
        alt = None
        if '|' in fname:
            fname, alt = fname.split('|', 1)
        img_path = self.image_path(fname, 'UDGImagePath')
        if self.need_image(img_path):
            frames = []
            default_delay = 32 # 0.32s
            for frame_param in frame_params[1:].split(';'):
                elements = frame_param.rsplit(',', 1)
                if len(elements) == 2:
                    frame_id = elements[0]
                    delay = default_delay = skoolmacro.parse_ints(elements[1], names=('delay',))[1]
                else:
                    frame_id = frame_param
                    delay = default_delay
                if not frame_id:
                    raise MacroParsingError('Missing frame ID: #UDGARRAY{}'.format(text[index:end]))
                try:
                    frame = self.frames[frame_id]
                except KeyError:
                    raise MacroParsingError('No such frame: "{}"'.format(frame_id))
                frame.delay = delay
                frames.append(frame)
            self.write_animated_image(img_path, frames)
        return end, self.img_element(cwd, img_path, alt)

    def expand_udgarray(self, text, index, cwd):
        # #UDGARRAYwidth[,attr,scale,step,inc,flip,rotate,mask];addr[,attr,step,inc][:addr[,step]];...[{x,y,width,height}](fname)
        # #UDGARRAY*frame1[,delay];frame2[,delay];...(fname)
        if index < len(text) and text[index] == '*':
            return self._expand_udgarray_with_frames(text, index, cwd)

        param_names = ('width', 'attr', 'scale', 'step', 'inc', 'flip', 'rotate', 'mask')
        defaults = (56, 2, 1, 0, 0, 0, 1)
        kwargs = {'path_id': 'UDGImagePath', 'frame': True, 'alt': True}
        udg_array_params = self.parse_image_params(text, index, defaults=defaults, names=param_names, **kwargs)
        end, img_path, frame, alt, crop_rect, width, attr, scale, step, inc, flip, rotate, mask = udg_array_params
        udg_array = [[]]
        has_masks = False
        while end < len(text) and text[end] == ';':
            param_names = ('addr', 'attr', 'step', 'inc')
            defaults = (attr, step, inc)
            udg_params = self.parse_image_params(text, end + 1, defaults=defaults, chars='-x', ints=(1, 2, 3), names=param_names, **kwargs)
            end, img_path, frame, alt, crop_rect, udg_addr, udg_attr, udg_step, udg_inc = udg_params
            udg_addresses = self._get_udg_addresses(udg_addr, width)
            mask_addresses = []
            if end < len(text) and text[end] == ':':
                param_names = ('addr', 'step')
                defaults = (udg_step,)
                mask_params = self.parse_image_params(text, end + 1, defaults=defaults, chars='-x', ints=(1,), names=param_names, **kwargs)
                end, img_path, frame, alt, crop_rect, mask_addr, mask_step = mask_params
                if mask:
                    mask_addresses = self._get_udg_addresses(mask_addr, width)
            has_masks = has_masks or len(mask_addresses) > 0
            mask_addresses += [None] * (len(udg_addresses) - len(mask_addresses))
            for u, m in zip(udg_addresses, mask_addresses):
                udg_bytes = [(self.snapshot[u + n * udg_step] + udg_inc) % 256 for n in range(8)]
                udg = Udg(udg_attr, udg_bytes)
                if m is not None:
                    udg.mask = [self.snapshot[m + n * mask_step] for n in range(8)]
                if len(udg_array[-1]) == width:
                    udg_array.append([udg])
                else:
                    udg_array[-1].append(udg)
        if not has_masks:
            mask = 0

        if not img_path and frame is None:
            raise MacroParsingError('Missing filename: #UDGARRAY{}'.format(text[index:end]))

        if not img_path and not frame:
            raise MacroParsingError('Missing filename or frame ID: #UDGARRAY{}'.format(text[index:end]))

        need_image = img_path and self.need_image(img_path)
        if frame or need_image:
            if flip:
                self.flip_udgs(udg_array, flip)
            if rotate:
                self.rotate_udgs(udg_array, rotate)
            if frame:
                self.frames[frame] = Frame(udg_array, scale, mask, *crop_rect)
            if need_image:
                self.write_image(img_path, udg_array, crop_rect, scale, mask)
        if img_path:
            return end, self.img_element(cwd, img_path, alt)
        return end, ''

    def expand_udgtable(self, text, index, cwd):
        return self.expand_table(text, index, cwd)

    def expand(self, text, cwd):
        """Return `text` with skool macros expanded. `cwd` is the current
        working directory, which is required by macros that create images or
        hyperlinks.
        """
        return expand_macros(self.macros, text, cwd)

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
        self.images = set()

    # PY: open_file(self, *names, mode='w') in Python 3
    def open_file(self, *names, **kwargs):
        path = self.odir
        for name in names:
            path = join(path, name)
        if not isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        mode = kwargs.get('mode', 'w') # PY: Not needed in Python 3
        return open(path, mode)

    def add_image(self, image_path):
        self.images.add(image_path)

    def need_image(self, image_path):
        return (self.replace_images and image_path not in self.images) or not self.file_exists(image_path)

    def file_exists(self, fname):
        return isfile(join(self.odir, fname))

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

class Frame(object):
    """Create a frame of an animated image.

    :param udgs: The two-dimensional array of tiles (instances of
                 :class:`~skoolkit.skoolhtml.Udg`) from which to build the
                 frame.
    :param scale: The scale of the frame.
    :param mask: The type of mask to apply to the tiles in the frame: 0 (no
                 mask), 1 (OR-AND mask), or 2 (AND-OR mask).
    :param x: The x-coordinate of the top-left pixel to include in the frame.
    :param y: The y-coordinate of the top-left pixel to include in the frame.
    :param width: The width of the frame; if `None`, the maximum width
                  (derived from `x` and the width of the array of tiles) is
                  used.
    :param height: The height of the frame; if `None`, the maximum height
                   (derived from `y` and the height of the array of tiles) is
                   used.
    :param delay: The delay between this frame and the next in 1/100ths of a
                  second.
    """
    def __init__(self, udgs, scale=1, mask=0, x=0, y=0, width=None, height=None, delay=32):
        self._udgs = udgs
        self._scale = scale
        self.mask = int(mask)
        self._x = x
        self._y = y
        self._full_width = 8 * len(udgs[0]) * scale
        self._full_height = 8 * len(udgs) * scale
        self._width = min(width or self._full_width, self._full_width - x)
        self._height = min(height or self._full_height, self._full_height - y)
        self.delay = delay
        self._tiles = len(udgs[0]) * len(udgs)

    def swap_colours(self, tx=0, ty=0, tw=None, th=None, x=0, y=0, width=None, height=None):
        # Swap paper and ink in UDGs that are flashing
        t_width = tw or len(self.udgs[0])
        t_height = th or len(self.udgs)
        udgs = [self.udgs[i][tx:tx + t_width] for i in range(ty, ty + t_height)]
        for row in udgs:
            for i in range(len(row)):
                udg = row[i]
                attr = udg.attr
                if attr & 128:
                    new_attr = (attr & 192) + (attr & 7) * 8 + (attr & 56) // 8
                    row[i] = Udg(new_attr, udg.data, udg.mask)
        return Frame(udgs, self.scale, self.mask, x, y, width, height)

    @property
    def udgs(self):
        return self._udgs

    @property
    def scale(self):
        return self._scale

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def cropped(self):
        return self._width != self._full_width or self._height != self._full_height

    @property
    def tiles(self):
        return self._tiles
