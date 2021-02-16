# Copyright 2008-2021 Richard Dymond (rjdymond@gmail.com)
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

from html import unescape
import posixpath
import os.path
from os.path import isfile, isdir, basename
from collections import defaultdict
import re
from io import StringIO

from skoolkit import skoolmacro, SkoolKitError, SkoolParsingError, evaluate, format_template, parse_int, warn
from skoolkit.components import get_component, get_image_writer
from skoolkit.defaults import REF_FILE
from skoolkit.graphics import Frame, adjust_udgs, build_udg, font_udgs, scr_udgs
from skoolkit.refparser import RefParser
from skoolkit.skoolparser import TableParser, ListParser

#: The ID of the main disassembly.
MAIN_CODE_ID = 'main'

# Page IDs
P_GAME_INDEX = 'GameIndex'
P_ASM_SINGLE_PAGE = 'AsmSinglePage'

# Full-page template name
T_LAYOUT = 'Layout'

# UDG image path ID
UDG_IMAGE_PATH = 'UDGImagePath'

def join(*path_components):
    return '/'.join([c for c in path_components if c.replace('/', '')])

class HtmlWriter:
    """Converts a skool file and its associated ref files to HTML.

    :type skool_parser: :class:`~skoolkit.skoolparser.SkoolParser`
    :param skool_parser: The skool file parser to use.
    :type ref_parser: :class:`~skoolkit.refparser.RefParser`
    :param ref_parser: The ref file parser to use.
    :type file_info: :class:`FileInfo`
    :param file_info: The `FileInfo` object to use.
    :param code_id: The ID of the disassembly.
    """
    def __init__(self, skool_parser, ref_parser, file_info=None, code_id=MAIN_CODE_ID):
        self.parser = skool_parser
        self.ref_parser = ref_parser
        skool_parser.make_replacements(ref_parser)
        self.defaults = RefParser()
        self.defaults.parse(StringIO(REF_FILE))
        self.file_info = file_info

        self.fields = skool_parser.fields

        colours = self._parse_colours(self.get_dictionary('Colours'))
        iw_config = self.get_dictionary('ImageWriter')
        self.image_writer = get_image_writer(iw_config, colours)
        self.frames = {}

        self.snapshot = self.parser.snapshot
        self._snapshots = [(self.snapshot, '')]
        self.asm_entry_dicts = {}
        self.map_entry_dicts = {}
        self.nonexistent_entry_dict = defaultdict(lambda: '', exists=0)
        self.memory_map = [e for e in self.parser.memory_map if e.ctl != 'i']

        self.table_parser = TableParser()
        self.list_parser = ListParser()
        self.to_chr = '&#{};'.format
        self.get_reg = lambda r: self.format_template('reg', {'reg': r})
        self.space = '&#160;'
        self.pc = 0
        self.macros = skoolmacro.get_macros(self)
        for m in self.parser.expands:
            try:
                self.expand(m)
            except SkoolParsingError as e:
                raise SkoolParsingError("@expand failed to expand '{}': {}".format(m, e.args[0]))
            except:
                raise SkoolKitError("@expand failed to expand '{}'".format(m))

        self.game_vars = self._expand_values('Game', 'Logo')
        self.asm_anchor_template = self.game_vars['AddressAnchor']
        self.asm_address_template = self.game_vars['Address']
        self.asm_single_page = self.game_vars['AsmSinglePage'] != '0'
        self.paths = self.get_dictionary('Paths')
        self.titles = self.get_dictionary('Titles')
        self.page_headers = self.get_dictionary('PageHeaders')
        links = self.get_dictionary('Links')

        self.page_ids = []
        self.pages = defaultdict(dict)
        self.box_pages = {}
        for page_id, details in self.get_dictionaries('Page'):
            self._expand_values(details, 'PageContent')
            page = self.pages[page_id]
            section_prefix = details.get('SectionPrefix')
            if section_prefix:
                self.box_pages[page_id] = entries = []
                use_paragraphs = details.get('SectionType') not in ('ListItems', 'BulletPoints')
                if use_paragraphs:
                    sections = self.get_sections(section_prefix, True)
                else:
                    sections = self.get_sections(section_prefix, True, True, False)
                for entry in sections:
                    try:
                        anchor, title, paragraphs = entry
                    except ValueError:
                        title, paragraphs = entry
                        anchor = re.sub('[\s()]', '_', title.lower())
                    if use_paragraphs:
                        entries.append((anchor, title, paragraphs))
                    else:
                        intro = ' '.join(paragraphs[0])
                        if intro == '-':
                            intro = ''
                        entries.append((anchor, title, intro, paragraphs[1:]))
                if not entries:
                    continue
            if page_id not in self.page_ids:
                self.page_ids.append(page_id)
            page.update(details)
        for page_id, page in self.pages.items():
            path = page.get('Content')
            if path:
                self.page_ids.remove(page_id)
            else:
                path = '{}.html'.format(page_id)
            self.paths.setdefault(page_id, path)
            self.titles.setdefault(page_id, page_id)

        self.memory_maps = {}
        self.other_code = []
        other_code_indexes = set()
        for c_id, code in self.get_dictionaries('OtherCode'):
            code.setdefault('Source', '{}.skool'.format(c_id))
            self.other_code.append((c_id, code))
            index_page_id = code['IndexPageId'] = '{}-Index'.format(c_id)
            other_code_indexes.add(index_page_id)
            self.memory_maps[index_page_id] = {'EntryTypes': 'bcgstuw'}
            self.paths.setdefault(index_page_id, '{0}/{0}.html'.format(c_id))
            self.titles.setdefault(index_page_id, c_id)
            code_path_id = code['CodePathId'] = '{}-CodePath'.format(c_id)
            self.paths.setdefault(code_path_id, c_id)
            asm_single_page_id = code['AsmSinglePageId'] = '{}-{}'.format(c_id, P_ASM_SINGLE_PAGE)
            self.paths.setdefault(asm_single_page_id, '{}/asm.html'.format(c_id))
            self.titles.setdefault(asm_single_page_id, c_id)
            if not self.asm_single_page:
                for entry_type in 'bcgstuw':
                    asm_page_id = self._get_asm_page_id(c_id, entry_type)
                    default_asm_page_id = self._get_asm_page_id(MAIN_CODE_ID, entry_type)
                    self.titles.setdefault(asm_page_id, self.titles[default_asm_page_id])
                    self.page_headers.setdefault(asm_page_id, self.page_headers[default_asm_page_id])

        self.entry_groups = {}
        group_entries = defaultdict(set)
        for group, addresses in self.get_dictionary('EntryGroups').items():
            for addr_str in addresses.split(','):
                address = parse_int(addr_str)
                if self.get_entry(address):
                    self.entry_groups[address] = 'Asm-' + group
                    group_entries[group].add(address)

        self.main_memory_maps = []
        for map_name, map_details in self.get_dictionaries('MemoryMap'):
            self._expand_values(map_details, 'Intro')
            self.memory_maps[map_name] = map_details
            includes = []
            for addr_str in map_details.get('Includes', '').split(','):
                address = parse_int(addr_str)
                if self.get_entry(address):
                    includes.append(address)
                else:
                    includes.extend(group_entries.get(addr_str, ()))
            map_details['Includes'] = includes
            if map_name not in other_code_indexes and self._should_write_map(map_details):
                self.main_memory_maps.append(map_name)
                self.paths.setdefault(map_name, 'maps/{}.html'.format(map_name))
                self.titles.setdefault(map_name, map_name)

        self._expand_values(self.paths)
        self.image_paths = {k: v for k, v in self.paths.items() if k.endswith('ImagePath')}

        self.asm_fname_template = self.paths['CodeFiles']
        self.udg_fname_template = self.paths['UDGFilename']

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
        link_operands = self.game_vars['LinkOperands']
        self.link_operands = tuple(op.upper() for op in link_operands.split(','))
        self.link_internal_operands = self.game_vars['LinkInternalOperands'] != '0'
        self.js_files = ()
        global_js = self.game_vars.get('JavaScript')
        if global_js:
            self.js_files = tuple(global_js.split(';'))

        self.formatter = get_component('HtmlTemplateFormatter', dict(self.get_sections('Template')))
        self.game = self.game_vars.copy()
        self.skoolkit = {}
        self.stylesheets = defaultdict(list)
        self.javascript = {}
        self.logo = {}
        self.template_subs = {
            'Game': self.game,
            'SkoolKit': self.skoolkit
        }

        self.init()

    # API
    def init(self):
        """Perform post-initialisation operations. This method is called after
        `__init__()` has completed. By default the method does nothing, but
        subclasses may override it.
        """
        return

    # API
    @property
    def base(self):
        return self.parser.base

    # API
    @property
    def case(self):
        return self.parser.case

    def warn(self, s):
        warn(s)

    def clone(self, skool_parser, code_id):
        the_clone = self.__class__(skool_parser, self.ref_parser, self.file_info, code_id)
        the_clone.set_style_sheet(self.game_vars['StyleSheet'])
        return the_clone

    def set_style_sheet(self, value):
        self.game_vars['StyleSheet'] = value

    # API
    def format_template(self, name, fields):
        """Format a template with a set of replacement fields.

        :param name: The name of the template.
        :param fields: A dictionary of replacement field names and values.
        :return: The formatted string.
        """
        fields.update(self.template_subs)
        return self.formatter.format_template(self._get_page_id(), name, fields)

    def _expand_values(self, obj, *exceptions):
        if isinstance(obj, str):
            d = self.get_dictionary(obj)
        else:
            d = obj
        for k in d:
            if k not in exceptions:
                try:
                    d[k] = self.expand(d[k])
                except:
                    raise SkoolKitError('Failed to expand macros in {} parameter: {}'.format(k, d[k]))
        return d

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

    def _get_asm_page_id(self, code_id, entry_type=None):
        if self.asm_single_page:
            if code_id == MAIN_CODE_ID:
                return P_ASM_SINGLE_PAGE
            return '{}-{}'.format(code_id, P_ASM_SINGLE_PAGE)
        if code_id == MAIN_CODE_ID:
            return 'Asm-{}'.format(entry_type)
        return '{}-Asm-{}'.format(code_id, entry_type)

    # API
    def get_dictionary(self, section_name):
        """Return a dictionary built from the contents of a ref file section.
        Each line in the section should be of the form ``X=Y``.
        """
        dictionary = self.defaults.get_dictionary(section_name)
        dictionary.update(self.ref_parser.get_dictionary(section_name))
        return dictionary

    # API
    def get_dictionaries(self, section_type):
        """Return a list of 2-tuples of the form ``(suffix, dict)`` derived
        from ref file sections whose names start with `section_type` followed
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

    # API
    def get_section(self, section_name, paragraphs=False, lines=False, trim=True):
        """Return the contents of a ref file section.

        :param section_name: The section name.
        :param paragraphs: If `True`, return the contents as a list of
                           paragraphs.
        :param lines: If `True`, return the contents (or each paragraph) as a
                      list of lines; otherwise return the contents (or each
                      paragraph) as a single string.
        :param trim: If `True`, remove leading whitespace from each line.
        """
        if self.ref_parser.has_section(section_name):
            return self.ref_parser.get_section(section_name, paragraphs, lines, trim)
        return self.defaults.get_section(section_name, paragraphs, lines, trim)

    # API
    def get_sections(self, section_type, paragraphs=False, lines=False, trim=True):
        """Return a list of 2-tuples of the form ``(suffix, contents)`` or
        3-tuples of the form ``(infix, suffix, contents)`` derived from ref
        file sections whose names start with `section_type` followed by a
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
        :param trim: If `True`, remove leading whitespace from each line.
        """
        sections = []
        index = {}
        default_sections = self.defaults.get_sections(section_type, paragraphs, lines, trim)
        user_sections = self.ref_parser.get_sections(section_type, paragraphs, lines, trim)
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

    # API
    def get_snapshot_name(self):
        """Return the name of the current memory snapshot."""
        return self._snapshots[-1][1]

    # API
    def pop_snapshot(self):
        """Replace the current memory snapshot with the one most recently saved
        by :meth:`~skoolkit.skoolhtml.HtmlWriter.push_snapshot`."""
        if len(self._snapshots) < 2:
            raise SkoolKitError("Cannot pop snapshot when snapshot stack is empty")
        self.snapshot[:] = self._snapshots.pop()[0]

    # API
    def push_snapshot(self, name=''):
        """Save a copy of the current memory snapshot for later retrieval (by
        :meth:`~skoolkit.skoolhtml.HtmlWriter.pop_snapshot`).

        :param name: An optional name for the snapshot.
        """
        self._snapshots.append((self.snapshot[:], name))

    def get_page_ids(self):
        return self.page_ids

    def file_exists(self, fname):
        return self.file_info.file_exists(fname)

    def relpath(self, cwd, target):
        return posixpath.relpath(target, cwd)

    def asm_fname(self, address, path=''):
        return posixpath.normpath(join(path, format_template(self.asm_fname_template, 'CodeFiles', address=address)))

    def _asm_relpath(self, cwd, address, code_id=None, raw=False):
        if not code_id:
            code_id = self.code_id
        if self.asm_single_page:
            page_id = self._get_asm_page_id(code_id)
            fname = self.relpath(cwd, self.paths[page_id])
            return '{}#{}'.format(fname, self.asm_anchor(address, raw))
        code_path = self.get_code_path(code_id)
        return self.relpath(cwd, join(code_path, self.asm_fname(address)))

    def asm_anchor(self, address, raw=False):
        anchor = format_template(self.asm_anchor_template, 'AddressAnchor', address=address)
        if raw:
            return 'RAW(#{})'.format(anchor)
        return anchor

    def asm_address(self, address, default):
        if self.asm_address_template:
            return self.asm_address_template.format(address=address)
        return default

    # API
    def screenshot(self, x=0, y=0, w=32, h=24, df_addr=16384, af_addr=22528):
        """Return a two-dimensional array of tiles (instances of
        :class:`~skoolkit.graphics.Udg`) built from the display file and
        attribute file of the current memory snapshot.

        :param x: The x-coordinate of the top-left tile to include (0-31).
        :param y: The y-coordinate of the top-left tile to include (0-23).
        :param w: The width of the array (in tiles).
        :param h: The height of the array (in tiles).
        :param df_addr: The display file address to use.
        :param af_addr: The attribute file address to use.
        """
        return scr_udgs(self.snapshot, x, y, w, h, df_addr, af_addr)

    def _get_page_id(self):
        return self.skoolkit['page_id']

    def write_index(self):
        index_fname, cwd = self._set_cwd(P_GAME_INDEX, 'home')

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
                    link_text = [self.expand(t, cwd) for t in self.links[page_id]]
                    links.append((link_file, link_text[0], link_text[1]))
            sections[section_id] = (header_text, links)
        other_code_links = []
        for code_id, code in self.other_code:
            fname = self.paths[code['IndexPageId']]
            if self.file_exists(fname):
                link_file = self.relpath(cwd, fname)
                link_text = [self.expand(t, cwd) for t in self.links[code['IndexPageId']]]
                other_code_links.append((link_file, link_text[0], link_text[1]))
        sections['OtherCode'] = ('Other code', other_code_links)

        section_objs = []
        for section_id in self.get_section('Index', False, True):
            header, links = sections.get(section_id, ('', ()))
            if links:
                items = []
                for href, link_text, other_text in links:
                    items.append({
                        'href': href,
                        'link_text': link_text,
                        'other_text': other_text
                    })
                section_objs.append({'header': header, 'items': items})

        html = self.format_template(T_LAYOUT, {'sections': section_objs})
        self.write_file(index_fname, html)

    def _get_entry_dict(self, cwd, entry, desc=True):
        self.pc = entry.address
        if desc:
            description = [self.expand(p, cwd).strip() for p in entry.details]
        else:
            description = ()
        return {
            'exists': 1,
            'type': entry.ctl,
            'location': entry.address,
            'address': self.asm_address(entry.address, entry.addr_str),
            'anchor': self.asm_anchor(entry.address),
            'page': entry.address // 256,
            'byte': entry.address % 256,
            'label': self.parser.get_asm_label(entry.address) or '',
            'description': description,
            'href': self._asm_relpath(cwd, entry.address),
            'size': entry.size,
            'length': self.game_vars['Length'].format(size=entry.size),
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

    def _build_box_page_entries(self, cwd):
        page_id = self._get_page_id()
        entries = []
        for i, (anchor, title, paragraphs) in enumerate(self.box_pages[page_id]):
            anchor = self.expand(anchor, cwd)
            title = self.expand(title, cwd)
            entries.append({
                'anchor': anchor,
                'order': 1 + i % 2,
                'title': title,
                'contents': [self.expand(p, cwd).strip() for p in paragraphs]
            })
        return entries

    def _build_box_page_list_entries(self, cwd, bullets):
        page_id = self._get_page_id()
        if bullets:
            prefix = '-'
        else:
            prefix = ''
        entries = []
        for j, (anchor, title, intro, items) in enumerate(self.box_pages[page_id]):
            anchor = self.expand(anchor, cwd)
            title = self.expand(title, cwd)
            list_items = []
            for item in items:
                indents = [(0, list_items)]
                for line in item:
                    subitems = indents[-1][1]
                    s_line = line.lstrip()
                    new_indent = len(line) - len(s_line)
                    if prefix and not s_line.startswith(prefix):
                        if not subitems:
                            continue
                        subitems[-1][0] += ' {}'.format(s_line)
                    else:
                        subitem = [s_line[len(prefix):].lstrip(), ()]
                        if new_indent == indents[-1][0]:
                            subitems.append(subitem)
                        elif new_indent > indents[-1][0]:
                            new_subitems = [subitem]
                            subitems[-1][1] = new_subitems
                            indents.append((new_indent, new_subitems))
                        else:
                            while new_indent < indents[-1][0]:
                                indents.pop()
                            subitems = indents[-1][1]
                            subitems.append(subitem)
            entries.append({
                'anchor': anchor,
                'order': 1 + j % 2,
                'title': title,
                'intro': self.expand(intro, cwd),
                'item_list': self._build_list_items(cwd, list_items)
            })
        return entries

    def _build_list_items(self, cwd, items, level=0):
        if not items:
            return ''
        list_items = []
        for item, subitems in items:
            list_items.append({
                'text': self.expand(item, cwd),
                'subitems': self._build_list_items(cwd, subitems, level + 1)
            })
        if level > 0:
            indent = level
        else:
            indent = ''
        t_list_items_subs = {
            'indent': indent,
            'items': list_items
        }
        return self.format_template('item_list', t_list_items_subs)

    def format_registers(self, cwd, registers, entry_dict):
        entry_dict['input_registers'] = input_values = []
        entry_dict['output_registers'] = output_values = []
        mode = 'I'
        for reg in registers:
            if reg.prefix:
                mode = reg.prefix.upper()[0]
            if reg.delimiters[0]:
                reg.name = self.expand(reg.name, cwd)
            reg_obj = {
                'name': reg.name,
                'description': self.expand(reg.contents, cwd)
            }
            if mode == 'O':
                output_values.append(reg_obj)
            else:
                input_values.append(reg_obj)

    def _get_asm_entry(self, cwd, index, map_file):
        entry = self.memory_map[index]
        entry_dict = self._get_asm_entry_dict(cwd, index, map_file)

        self.format_registers(cwd, entry.registers, entry_dict)

        entry_dict['instructions'] = instructions = []
        for instruction in entry.instructions:
            self.pc = instruction.address
            instruction.byte_values = Bytes(instruction.bytes)

            operation, reference = instruction.operation, instruction.reference
            operation_u = operation.upper()
            if reference and operation_u.startswith(self.link_operands):
                asm_label = self.parser.get_asm_label(reference.address)
                external_ref = entry != reference.entry
                if external_ref or asm_label or self.link_internal_operands:
                    if self.asm_single_page:
                        href = '#{}'.format(self.asm_anchor(reference.address))
                    else:
                        entry_address = reference.entry.address
                        href = self._asm_relpath(cwd, entry_address, reference.entry.asm_id)
                        if not (external_ref and reference.address == entry_address):
                            href += '#{}'.format(self.asm_anchor(reference.address))
                    if asm_label and reference.use_label:
                        link_text = asm_label
                    else:
                        link_text = reference.addr_str
                    link = self.format_link(href, link_text)
                    operation = operation.replace(reference.addr_str, link)

            if instruction.mid_block_comment:
                block_comment = [self.expand(p, cwd).strip() for p in instruction.mid_block_comment]
            else:
                block_comment = ()
            comment = instruction.comment
            if comment:
                comment_rowspan = comment.rowspan
                comment_text = self.expand(comment.text, cwd)
            else:
                comment_rowspan = 0
                comment_text = ''

            instructions.append({
                'block_comment': block_comment,
                'address': self.asm_address(instruction.address, instruction.addr_str),
                'location': instruction.address,
                'called': 1 + int(instruction.ctl in 'c*'),
                'label': instruction.asm_label or '',
                'operation': operation,
                'comment': comment_text,
                'comment_rowspan': comment_rowspan,
                'anchor': self.asm_anchor(instruction.address),
                'bytes': instruction.byte_values
            })

        entry_dict['annotated'] = int(any([i.comment and i.comment.text for i in entry.instructions]))
        entry_dict['end_comment'] = [self.expand(p, cwd).strip() for p in entry.end_comment]
        entry_dict['labels'] = int(any([instruction.asm_label for instruction in entry.instructions]))
        entry_dict['show_bytes'] = int(self.game_vars['Bytes'] != '' and any(i.byte_values.values for i in entry.instructions))

        return entry_dict

    def write_entry(self, cwd, index, map_file):
        entry = self.memory_map[index]
        page_id = self._get_asm_page_id(self.code_id, entry.ctl)
        fname = join(cwd, self.asm_fname(entry.address))
        group = self.entry_groups.get(entry.address)
        self._set_cwd(page_id, 'asm', fname, group)

        subs = {'entry': self._get_asm_entry(cwd, index, map_file)}
        self.skoolkit['title'] = self.skoolkit['title'].format(**subs)
        self.skoolkit['page_header'] = [h.format(**subs) for h in self.skoolkit['page_header']]
        self.init_page(self.skoolkit, self.game)

        if index:
            prev_entry_dict = self._get_asm_entry_dict(cwd, index - 1, map_file)
        else:
            prev_entry_dict = self.nonexistent_entry_dict
        if index + 1 < len(self.memory_map):
            next_entry_dict = self._get_asm_entry_dict(cwd, index + 1, map_file)
        else:
            next_entry_dict = self.nonexistent_entry_dict
        subs['prev_entry'] = prev_entry_dict
        subs['next_entry'] = next_entry_dict

        html = self.format_template(T_LAYOUT, subs)
        self.write_file(fname, html)

    def _write_asm_single_page(self, map_file):
        page_id = self._get_asm_page_id(self.code_id)
        fname, cwd = self._set_cwd(page_id, 'asm_single_page')
        asm_entries = [self._get_asm_entry(cwd, i, map_file) for i in range(len(self.memory_map))]
        html = self.format_template(T_LAYOUT, {'entries': asm_entries})
        self.write_file(fname, html)

    def write_entries(self, cwd, map_file):
        if self.asm_single_page:
            self._write_asm_single_page(map_file)
        else:
            for i in range(len(self.memory_map)):
                self.write_entry(cwd, i, map_file)

    def write_asm_entries(self):
        self.write_entries(self.code_path, self.paths['MemoryMap'])

    def _should_write_map(self, map_details):
        if map_details.get('Write') == '0':
            return False
        if map_details['Includes']:
            return True
        entry_types = map_details.get('EntryTypes', '')
        return any([entry.ctl in entry_types for entry in self.memory_map])

    def write_map(self, map_name):
        fname, cwd = self._set_cwd(map_name, 'memory_map')

        map_details = self.memory_maps.get(map_name, {})
        entry_types = map_details.get('EntryTypes', '')
        map_dict = {
            'EntryDescriptions': map_details.get('EntryDescriptions', '0'),
            'EntryTypes': entry_types,
            'Includes': map_details.get('Includes', ()),
            'Intro': self.expand(map_details.get('Intro', ''), cwd),
            'LabelColumn': map_details.get('LabelColumn', '0'),
            'LengthColumn': map_details.get('LengthColumn', '0'),
            'PageByteColumns': map_details.get('PageByteColumns', '0'),
            'Write': map_details.get('Write', '1')
        }
        desc = map_dict['EntryDescriptions'] != '0'

        map_entries = []
        asm_labels = False
        for entry in self.memory_map:
            if entry.ctl in entry_types or entry.address in map_dict['Includes']:
                if entry.instructions[0].asm_label:
                    asm_labels = True
                map_entries.append(self._get_map_entry_dict(cwd, entry, desc))
        if not asm_labels:
            map_dict['LabelColumn'] = '0'

        subs = {
            'MemoryMap': map_dict,
            'entries': map_entries
        }
        html = self.format_template(T_LAYOUT, subs)
        self.write_file(fname, html)

    def write_page(self, page_id):
        page = self.pages[page_id]
        subs = {'Page': page}
        if page_id in self.box_pages:
            section_type = page.get('SectionType')
            if section_type in ('ListItems', 'BulletPoints'):
                fname, cwd = self._set_cwd(page_id, 'box_list_entries', js=page.get('JavaScript'))
                subs['entries'] = self._build_box_page_list_entries(cwd, section_type == 'BulletPoints')
            else:
                fname, cwd = self._set_cwd(page_id, 'box_entries', js=page.get('JavaScript'))
                subs['entries'] = self._build_box_page_entries(cwd)
        else:
            fname, cwd = self._set_cwd(page_id, 'page', js=page.get('JavaScript'))
            page['PageContent'] = self.expand(page.get('PageContent', ''), cwd)
        html = self.format_template(T_LAYOUT, subs)
        self.write_file(fname, html)

    def write_file(self, fname, contents):
        with self.file_info.open_file(fname) as f:
            f.write(contents)

    def _set_cwd(self, page_id, include, asm_fname=None, group=None, js=None):
        if asm_fname is None:
            fname = self.paths[page_id]
        else:
            fname = asm_fname
        cwd = os.path.dirname(fname)

        if cwd not in self.stylesheets:
            for css_file in self.game_vars['StyleSheet'].split(';'):
                self.stylesheets[cwd].append({'href': self.relpath(cwd, join(self.paths['StyleSheetPath'], basename(css_file)))})

        js_key = (cwd, js)
        if js_key not in self.javascript:
            js_files = self.js_files
            if js:
                js_files += tuple(js.split(';'))
            self.javascript[js_key] = [{'src': self.relpath(cwd, join(self.paths['JavaScriptPath'], basename(j)))} for j in js_files]

        title = self.titles.get(group, self.titles[page_id])
        page_header = self.page_headers.get(group, self.page_headers[page_id])

        self.skoolkit['page_id'] = page_id
        self.skoolkit['path'] = fname
        self.skoolkit['index_href'] = self.relpath(cwd, self.paths[P_GAME_INDEX])
        self.skoolkit['title'] = self.expand(title, cwd)
        self.skoolkit['page_header'] = self.expand(page_header, cwd).rpartition('<>')[::2]
        self.skoolkit['include'] = include
        self.skoolkit['javascripts'] = self.javascript[js_key]
        self.skoolkit['stylesheets'] = self.stylesheets[cwd]
        self.game['Logo'] = self.game['LogoImage'] = self._get_logo(cwd)
        if asm_fname is None:
            self.init_page(self.skoolkit, self.game)
        return fname, cwd

    # API
    def init_page(self, skoolkit, game):
        """Perform page initialisation operations. This method is called after
        the ``SkoolKit`` and ``Game`` parameter dictionaries have been
        initialised, and provides those dictionaries as arguments for
        inspection and customisation before a page is formatted. By default the
        method does nothing, but subclasses may override it.

        :param skoolkit: The ``SkoolKit`` parameter dictionary.
        :param game: The ``Game`` parameter dictionary.
        """

    def _get_logo(self, cwd):
        if cwd not in self.logo:
            logo_macro = self.game_vars.get('Logo')
            if logo_macro:
                self.logo[cwd] = self.expand(logo_macro, cwd).strip()
            else:
                logo_image = self.game_vars.get('LogoImage')
                if logo_image and self.file_exists(logo_image):
                    self.logo[cwd] = self.format_img(self.game_name, self.relpath(cwd, logo_image))
                else:
                    self.logo[cwd] = self.game_name
        return self.logo[cwd]

    def format_link(self, href, link_text):
        return self.format_template('link', {'href': href, 'link_text': link_text})

    def format_img(self, alt, src):
        return self.format_template('img', {'alt': alt, 'src': src})

    # API
    def handle_image(self, frames, fname='', cwd=None, alt=None, path_id='ImagePath'):
        """Register a named frame for an image, and write an image file if
        required. If `fname` is blank, no image file will be created. If
        `fname` does not end with '.png', that suffix will be appended. If
        `fname` contains an image path ID replacement field, the corresponding
        parameter value from the :ref:`Paths` section will be substituted.

        :param frames: A frame (instance of :class:`~skoolkit.graphics.Frame`)
                       or list of frames from which to build the image.
        :param fname: The name of the image file.
        :param cwd: The current working directory (from which the relative path
                    of the image file will be computed).
        :param alt: The alt text to use for the image.
        :param path_id: The ID of the target directory (as defined in the
                        :ref:`paths` section of the ref file). This is not used
                        if `fname` starts with a '/' or contains an image path
                        ID replacement field.
        :return: The ``<img .../>`` element, or an empty string if no image is
                 created.
        """
        if isinstance(frames, Frame):
            frames = [frames]
        if len(frames) == 1:
            self.frames[frames[0].name] = frames[0]
        image_path = self._image_path(fname, path_id)
        if image_path:
            if self.file_info.need_image(image_path):
                content = self._write_image(image_path, frames)
            else:
                content = None
            if content is None:
                if alt is None:
                    alt = basename(image_path)[:-4]
                return self.format_img(alt, self.relpath(cwd, image_path))
            return content
        return ''

    def _write_image(self, image_path, frames):
        f = self.file_info.open_file(image_path, mode='wb')
        content = self.image_writer.write_image(frames, f)
        fsize = f.tell()
        f.close()
        if fsize:
            self.file_info.add_image(image_path)
        elif isfile(f.name):
            os.remove(f.name)
        return content

    def build_table(self, table):
        rows = []
        for row in table.rows:
            cells = []
            for cell in row:
                cell_class = cell.cell_class
                if cell.transparent:
                    cell_class += " transparent"
                cell_subs = {
                    'header': int(cell.header),
                    'class': cell_class.lstrip(),
                    'colspan': cell.colspan,
                    'rowspan': cell.rowspan,
                    'contents': cell.contents
                }
                cells.append(cell_subs)
            rows.append({'cells': cells})
        fields = {'class': table.table_class, 'rows': rows}
        return self.format_template('table', fields)

    def build_list(self, list_obj):
        fields = {'class': list_obj.css_class, 'items': list_obj.items}
        return self.format_template('list', fields)

    def _image_path(self, fname, path_id):
        """Return the full path of an image file relative to the root directory
        of the disassembly. If `fname` does not end with '.png', that suffix
        will be appended. If `fname` starts with a '/', it is removed and the
        remainder returned. If `fname` is blank, `None` is returned. If `fname`
        contains an image path ID replacement field, the corresponding
        parameter value from the [Paths] section is substituted.

        :param fname: The name of the image file.
        :param path_id: The ID of the target directory (as defined in the
                        [Paths] section). This is not used if `fname` starts
                        with a '/' or contains an image path ID replacement
                        field.
        """
        if fname:
            fname = self.image_writer.image_fname(fname)
            expanded = self._expand_image_path(fname)
            if expanded != fname or fname.startswith('/'):
                return expanded.lstrip('/')
            if path_id in self.paths:
                return join(self._expand_image_path(self.paths[path_id]), fname)
            raise SkoolKitError("Unknown path ID '{0}' for image file '{1}'".format(path_id, fname))

    def _expand_image_path(self, path):
        orig_path = prev_path = path
        while True:
            try:
                path = path.format(**self.image_paths)
            except KeyError:
                break
            if path in (prev_path, orig_path):
                break
            prev_path = path
        return path

    def expand_font(self, text, index, cwd):
        end, crop_rect, fname, frame, alt, params = skoolmacro.parse_font(text, index, self.fields)
        message, addr, chars, attr, scale, tindex, alpha = params
        udgs = lambda: font_udgs(self.snapshot, addr, attr, unescape(message)[:chars])
        frame = Frame(udgs, scale, 0, *crop_rect, name=frame, tindex=tindex, alpha=alpha)
        return end, self.handle_image(frame, fname, cwd, alt, 'FontImagePath')

    def expand_html(self, text, index, cwd):
        end, content = skoolmacro.parse_html(text, index)
        return end, unescape(content)

    def expand_include(self, text, index, cwd):
        end, paragraphs, section = skoolmacro.parse_include(text, index, self.fields)
        content = self.get_section(section, paragraphs)
        if paragraphs:
            return end, self.format_template('section', {'section': [self.expand(p, cwd).strip() for p in content]})
        return end, content

    def expand_link(self, text, index, cwd):
        end, page_id, anchor, link_text = skoolmacro.parse_link(text, index)
        if page_id not in self.paths:
            raise skoolmacro.MacroParsingError("Unknown page ID: {}".format(page_id))
        if link_text == '':
            if anchor and page_id in self.page_ids and page_id in self.box_pages:
                for item_anchor, title, paragraphs in self.box_pages[page_id]:
                    if anchor[1:] == item_anchor:
                        link_text = title
                        break
            if not link_text:
                link_text = self.links[page_id][0]
        if page_id in self.main_memory_maps:
            try:
                anchor = '#' + self.asm_anchor(self.get_entry(int(anchor[1:])).address, True)
            except (ValueError, AttributeError):
                pass
        href = self.relpath(cwd, self.paths[page_id]) + anchor
        return end, self.format_link(href, link_text)

    def expand_list(self, text, index, cwd):
        # #LIST[(class)]<items>LIST#
        end, list_obj = self.list_parser.parse_text(self, text, index, cwd)
        return end, self.build_list(list_obj)

    def expand_plot(self, text, index, cwd):
        return skoolmacro.parse_plot(text, index, self.fields, self.frames)

    def expand_r(self, text, index, cwd):
        end, addr_str, address, code_id, anchor, link_text = skoolmacro.parse_r(self.fields, text, index)
        container = self.parser.get_container(address, code_id)
        if (not code_id or code_id == self.code_id) and not container:
            raise skoolmacro.MacroParsingError('Could not find instruction at {}'.format(addr_str))
        if self.asm_single_page:
            href = self._asm_relpath(cwd, address, code_id, True)
        else:
            if container:
                container_address = container.address
            else:
                container_address = address
            if anchor:
                try:
                    if evaluate(anchor[1:]) == container_address:
                        anchor = '#{}'.format(self.asm_anchor(container_address, True))
                except ValueError:
                    pass
            elif address != container_address:
                anchor = '#{}'.format(self.asm_anchor(address, True))
            href = self._asm_relpath(cwd, container_address, code_id) + anchor
        asm_label = self.parser.get_asm_label(address)
        inst_addr_str = self.parser.get_instruction_addr_str(address, addr_str, code_id)
        return end, self.format_link(href, link_text or asm_label or self.asm_address(address, inst_addr_str))

    def expand_scr(self, text, index, cwd):
        end, crop_rect, fname, frame, alt, params = skoolmacro.parse_scr(text, index, self.fields)
        scale, x, y, w, h, df, af, tindex, alpha = params
        udgs = lambda: self.screenshot(x, y, w, h, df, af)
        frame = Frame(udgs, scale, 0, *crop_rect, name=frame, tindex=tindex, alpha=alpha)
        return end, self.handle_image(frame, fname, cwd, alt, 'ScreenshotImagePath')

    def expand_table(self, text, index, cwd):
        # #TABLE[(class[,col1class[,col2class...]])]<rows>TABLE#
        end, table = self.table_parser.parse_text(self, text, index, cwd)
        return end, self.build_table(table)

    def expand_udg(self, text, index, cwd):
        end, crop_rect, fname, frame, alt, params = skoolmacro.parse_udg(text, index, self.fields)
        addr, attr, scale, step, inc, flip, rotate, mask, tindex, alpha, mask_addr, mask_step = params
        udgs = lambda: [[build_udg(self.snapshot, addr, attr, step, inc, flip, rotate, mask, mask_addr, mask_step)]]
        if not fname and not frame:
            fname = format_template(self.udg_fname_template, 'UDGFilename', addr=addr, attr=attr, scale=scale)
            if frame == '':
                frame = fname
        frame = Frame(udgs, scale, mask, *crop_rect, name=frame, tindex=tindex, alpha=alpha)
        return end, self.handle_image(frame, fname, cwd, alt, UDG_IMAGE_PATH)

    def _expand_udgarray_with_frames(self, text, index, cwd):
        end, fname, alt, frames = skoolmacro.parse_udgarray_with_frames(text, index, self.fields, self.frames)
        return end, self.handle_image(frames, fname, cwd, alt, UDG_IMAGE_PATH)

    def expand_udgarray(self, text, index, cwd):
        if index < len(text) and text[index] == '*':
            return self._expand_udgarray_with_frames(text, index, cwd)

        end, crop_rect, fname, frame, alt, params = skoolmacro.parse_udgarray(text, index, self.snapshot, fields=self.fields)
        udg_array, scale, flip, rotate, mask, tindex, alpha = params
        udgs = lambda: adjust_udgs(udg_array, flip, rotate)
        frame = Frame(udgs, scale, mask, *crop_rect, name=frame, tindex=tindex, alpha=alpha)
        return end, self.handle_image(frame, fname, cwd, alt, UDG_IMAGE_PATH)

    def expand_udgtable(self, text, index, cwd):
        return self.expand_table(text, index, cwd)

    # API
    def expand(self, text, cwd=None):
        """Return `text` with skool macros expanded. `cwd` is the current
        working directory, which is required by macros that create images or
        hyperlinks.
        """
        return skoolmacro.expand_macros(self, text, cwd)

class FileInfo:
    """Utility class for file-related operations.

    :param topdir: The top-level directory.
    :param game_dir: The subdirectory of `topdir` in which to write all HTML
                     files and image files.
    :param replace_images: Whether existing images should be overwritten.
    """
    def __init__(self, topdir, game_dir, replace_images):
        self.odir = join(topdir, game_dir)
        self.replace_images = replace_images
        self.images = set()

    def open_file(self, *names, mode='w'):
        path = self.odir
        for name in names:
            path = join(path, name)
        if not isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        return open(path, mode, encoding=None if 'b' in mode else 'utf8')

    def add_image(self, image_path):
        self.images.add(image_path)

    def need_image(self, image_path):
        return image_path not in self.images if self.replace_images else not self.file_exists(image_path)

    def file_exists(self, fname):
        return isfile(join(self.odir, fname))

class Bytes:
    def __init__(self, values=()):
        self.values = values

    def __format__(self, spec):
        if not spec:
            return ''
        if spec and spec.count(spec[0]) > 1:
            bspec, sep, fmt = (spec[1:] + spec[0]).split(spec[0])[:3]
        else:
            bspec, sep, fmt = spec, '', ''
        return '{:{}}'.format(sep.join(v.__format__(bspec) for v in self.values), fmt)

class TemplateFormatter:
    """Initialise the template formatter.

    :param templates: A dictionary of templates keyed by template name.
    """
    # Component API
    def __init__(self, templates):
        self.templates = templates

    # Component API
    def format_template(self, page_id, name, fields):
        """Format a template.

        :param page_id: The ID of the current page.
        :param name: The template name.
        :param fields: A dictionary of replacement field values.
        :return: The text of the formatted template.
        """
        tname, lines = self._get_template(page_id, name)
        try:
            lines = self._process_include(page_id, lines, fields)
        except SkoolKitError as e:
            raise SkoolKitError("Invalid include directive: {}".format(e.args[0]))
        try:
            lines = self._process_foreach(lines, fields)
        except (skoolmacro.MacroParsingError, NameError, ValueError) as e:
            raise SkoolKitError("Invalid foreach directive: {}".format(e.args[0]))
        try:
            lines = self._process_if(lines, fields)
        except (SkoolKitError, skoolmacro.MacroParsingError, NameError, ValueError) as e:
            raise SkoolKitError("Invalid if directive: {}".format(e.args[0]))
        return format_template('\n'.join(lines), tname, **fields)

    def _get_template(self, page_id, name):
        tname = page_id
        if name != T_LAYOUT:
            tname += '-' + name
        if tname not in self.templates:
            tname = re.sub('Asm-[bcgstuw]', 'Asm', tname)
        if tname not in self.templates:
            tname = name
        try:
            return tname, self.templates[tname].split('\n')
        except KeyError as e:
            raise SkoolKitError("'{}' template does not exist".format(e.args[0]))

    def _process_include(self, page_id, lines, fields):
        while 1:
            done = True
            processed = []
            for line in lines:
                directive = self._html_template_directive(line)
                if directive.startswith('include('):
                    try:
                        tname = skoolmacro.parse_strings(directive, 7, 1)[1].format(**fields)
                    except KeyError as e:
                        raise SkoolKitError("Unrecognised field '{}'".format(e.args[0]))
                    if tname:
                        processed.extend(self._get_template(page_id, tname)[1])
                    done = False
                else:
                    processed.append(line)
            if done:
                return processed
            lines = processed

    def _process_foreach(self, lines, fields):
        processed = []
        stack = [processed]
        for line in lines:
            directive = self._html_template_directive(line)
            if directive.startswith('foreach('):
                varname, seqname = skoolmacro.parse_strings(directive, 7, 2)[1]
                stack.append([])
                stack[-2].append((varname, seqname, stack[-1]))
            elif directive == 'endfor' and len(stack) > 1:
                stack.pop()
            else:
                stack[-1].append(line)
        while any(isinstance(line, tuple) for line in processed):
            processed = self._unroll_loops(processed, fields)
        return processed

    def _process_if(self, lines, fields):
        processed = []
        stack = [1]
        for line in lines:
            directive = self._html_template_directive(line)
            if directive.startswith('if('):
                end, expr = skoolmacro.parse_brackets(directive, 2)
                value = self._eval_template_expr(expr, fields)
                stack.append(value)
            elif directive == 'else' and len(stack) > 1:
                stack[-1] = not stack[-1]
            elif directive == 'endif' and len(stack) > 1:
                stack.pop()
            elif all(stack):
                processed.append(line)
        return processed

    def _html_template_directive(self, line):
        if line.startswith('<#') and line.endswith('#>'):
            return line[2:-2].strip()
        return ''

    def _unroll_loops(self, lines, fields):
        unrolled = []
        for line in lines:
            if isinstance(line, tuple):
                varname, seqname, loop = line
                seq = self._eval_template_expr(seqname, fields)
                try:
                    for i in range(len(seq)):
                        unrolled.extend(self._sub_loop_var(loop, varname, '{}[{}]'.format(seqname, i)))
                except TypeError:
                    raise ValueError("'{}' is not a list".format(seqname))
            else:
                unrolled.append(line)
        return unrolled

    def _eval_template_expr(self, expr, fields):
        if expr:
            try:
                return eval(re.sub('\[([^0-9][^]]*)\]', r"['\1']", expr.format(**fields)), None, fields)
            except SyntaxError:
                raise ValueError("Syntax error in expression: '{}'".format(expr))
            except KeyError as e:
                raise SkoolKitError("Unrecognised field '{}'".format(e.args[0]))
        raise ValueError('Expression is missing')

    def _sub_loop_var(self, lines, substr, rep):
        subbed = []
        for line in lines:
            if isinstance(line, tuple):
                varname, seqname, loop = line
                subbed_loop = self._sub_loop_var(loop, substr, rep)
                subbed.append((varname, seqname.replace(substr, rep), subbed_loop))
            else:
                subbed.append(line.replace(substr, rep))
        return subbed
