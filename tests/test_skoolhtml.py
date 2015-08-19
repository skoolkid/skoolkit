# -*- coding: utf-8 -*-
import re
from os.path import basename, isfile
from posixpath import join
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from skoolkittest import SkoolKitTestCase, StringIO
from skoolkit import VERSION, SkoolKitError, SkoolParsingError, defaults, skoolhtml
from skoolkit.skoolmacro import MacroParsingError, UnsupportedMacroError
from skoolkit.skoolhtml import HtmlWriter, FileInfo, Udg, Frame
from skoolkit.skoolparser import SkoolParser, BASE_10, BASE_16, CASE_LOWER, CASE_UPPER
from skoolkit.refparser import RefParser

GAMEDIR = 'test'
ASMDIR = 'asm'
MAPS_DIR = 'maps'
GRAPHICS_DIR = 'graphics'
BUFFERS_DIR = 'buffers'
REFERENCE_DIR = 'reference'
FONTDIR = 'images/font'
SCRDIR = 'images/scr'
UDGDIR = 'images/udgs'

REF_SECTIONS = {
    'PageHeaders': defaults.get_section('PageHeaders'),
    'Template_img': defaults.get_section('Template:img'),
    'Template_link': defaults.get_section('Template:link'),
    'Template_list': defaults.get_section('Template:list'),
    'Template_list_item': defaults.get_section('Template:list_item'),
    'Template_table': defaults.get_section('Template:table'),
    'Template_table_cell': defaults.get_section('Template:table_cell'),
    'Template_table_header_cell': defaults.get_section('Template:table_header_cell'),
    'Template_table_row': defaults.get_section('Template:table_row'),
    'Template_reg': defaults.get_section('Template:reg')
}

MINIMAL_REF_FILE = """
[Game]
AddressAnchor={{address}}
Created=
LinkInternalOperands=0
LinkOperands=CALL,DEFW,DJNZ,JP,JR
[Paths]
CodePath={}
CodeFiles={{address}}.html
""".format(ASMDIR)

METHOD_MINIMAL_REF_FILE = """
[Game]
AddressAnchor={{address}}
Created=
LinkInternalOperands=0
LinkOperands=CALL,DEFW,DJNZ,JP,JR
[Paths]
CodePath={ASMDIR}
ScreenshotImagePath={SCRDIR}
UDGImagePath={UDGDIR}
CodeFiles={{address}}.html
""".format(**locals())

SKOOL_MACRO_MINIMAL_REF_FILE = """
[Game]
AddressAnchor={{address}}
Created=
LinkInternalOperands=0
LinkOperands=CALL,DEFW,DJNZ,JP,JR
{REF_SECTIONS[PageHeaders]}
[Paths]
CodePath={ASMDIR}
FontImagePath=images/font
ScreenshotImagePath={SCRDIR}
UDGImagePath={UDGDIR}
Bugs={REFERENCE_DIR}/bugs.html
CodeFiles={{address}}.html
Facts={REFERENCE_DIR}/facts.html
Pokes={REFERENCE_DIR}/pokes.html
{REF_SECTIONS[Template_img]}
{REF_SECTIONS[Template_link]}
{REF_SECTIONS[Template_list]}
{REF_SECTIONS[Template_list_item]}
{REF_SECTIONS[Template_reg]}
{REF_SECTIONS[Template_table]}
{REF_SECTIONS[Template_table_cell]}
{REF_SECTIONS[Template_table_header_cell]}
{REF_SECTIONS[Template_table_row]}
[Titles]
Asm-b=Data at
Asm-c=Routine at
Asm-g=Game status buffer entry at
Asm-s=Unused RAM at
Asm-t=Data at
Asm-u=Unused RAM at
Asm-w=Data at
""".format(**locals())

HEADER = """<!DOCTYPE html>
<html>
<head>
<title>{name}: {title}</title>
<meta charset="utf-8" />
<link rel="stylesheet" type="text/css" href="{path}skoolkit.css" />
{script}
</head>
<body class="{body_class}">
<table class="header">
<tr>
<td class="logo"><a href="{path}index.html">{logo}</a></td>
<td class="page-header">{header}</td>
</tr>
</table>"""

INDEX_HEADER = """<!DOCTYPE html>
<html>
<head>
<title>{name}: {title}</title>
<meta charset="utf-8" />
<link rel="stylesheet" type="text/css" href="{path}skoolkit.css" />
{script}
</head>
<body class="{body_class}">
<table class="header">
<tr>
<td class="page-header">{header_prefix}</td>
<td class="logo">{logo}</td>
<td class="page-header">{header_suffix}</td>
</tr>
</table>"""

BARE_FOOTER = """<footer>
<div class="release"></div>
<div class="copyright"></div>
<div class="created">Created using <a href="http://skoolkit.ca/">SkoolKit</a> {}.</div>
</footer>
</body>
</html>""".format(VERSION)

PREV_UP_NEXT = """<table class="asm-navigation">
<tr>
<td class="prev">{prev_link}</td>
<td class="up">{up_link}</td>
<td class="next">{next_link}</td>
</tr>
</table>"""

ERROR_PREFIX = 'Error while parsing #{0} macro'

class MockSkoolParser:
    def __init__(self, snapshot=None, entries=None, memory_map=()):
        self.snapshot = snapshot
        self.entries = entries or {}
        self.memory_map = memory_map
        self.skoolfile = ''
        self.base = None

    def get_entry(self, address):
        return self.entries.get(address)

class MockFileInfo:
    def __init__(self):
        self.fname = None
        self.mode = None

    # PY: open_file(self, *names, mode='w') in Python 3
    def open_file(self, *names, **kwargs):
        self.fname = join(*names)
        self.mode = kwargs.get('mode', 'w') # PY: Not needed in Python 3
        return StringIO()

    def add_image(self, image_path):
        return

    def need_image(self, image_path):
        return True

class MockImageWriter:
    def __init__(self, palette, options):
        self.palette = palette
        self.options = options
        self.default_format = 'png'

    def write_image(self, frames, img_file, img_format):
        self.frames = frames
        self.img_format = img_format
        if isinstance(frames, list):
            frame1 = frames[0]
            self.udg_array = frame1.udgs
            self.scale = frame1.scale
            self.mask = frame1.mask
            self.x = frame1.x
            self.y = frame1.y
            self.width = frame1.width
            self.height = frame1.height

class HtmlWriterTestCase(SkoolKitTestCase):
    def _mock_write_file(self, fname, contents):
        self.files[fname] = contents

    def _get_writer(self, ref=None, snapshot=(), case=None, base=None,
                    skool=None, create_labels=False, asm_labels=False,
                    mock_file_info=False, mock_write_file=True):
        self.skoolfile = None
        ref_parser = RefParser()
        if ref is not None:
            ref_parser.parse(StringIO(ref))
        if skool is None:
            skool_parser = MockSkoolParser(snapshot)
        else:
            self.skoolfile = self.write_text_file(skool, suffix='.skool')
            skool_parser = SkoolParser(self.skoolfile, case=case, base=base, html=True, create_labels=create_labels, asm_labels=asm_labels)
        self.odir = self.make_directory()
        if mock_file_info:
            file_info = MockFileInfo()
        else:
            file_info = FileInfo(self.odir, GAMEDIR, False)
        patch.object(skoolhtml, 'ImageWriter', MockImageWriter).start()
        self.addCleanup(patch.stopall)
        writer = HtmlWriter(skool_parser, ref_parser, file_info)
        if mock_write_file:
            writer.write_file = self._mock_write_file
        return writer

class HtmlWriterTest(HtmlWriterTestCase):
    def test_OtherCode_Source_parameter(self):
        ref = '\n'.join((
            '[OtherCode:load]',
            '[OtherCode:save]',
            'Source=save.sks'
        ))
        writer = self._get_writer(ref=ref)
        self.assertEqual(len(writer.other_code), 2)
        i = 0
        for exp_code_id, exp_source in (('load', 'load.skool'), ('save', 'save.sks')):
            code_id, code = writer.other_code[i]
            self.assertEqual(code_id, exp_code_id)
            self.assertIn('Source', code)
            self.assertEqual(code['Source'], exp_source)
            i += 1

class MethodTest(HtmlWriterTestCase):
    def setUp(self):
        HtmlWriterTestCase.setUp(self)
        patch.object(skoolhtml, 'REF_FILE', METHOD_MINIMAL_REF_FILE).start()
        self.addCleanup(patch.stopall)

    def _assert_scr_equal(self, game, x0=0, y0=0, w=32, h=24):
        snapshot = game.snapshot[:]
        scr = game.screenshot(x0, y0, w, h)
        self.assertEqual(len(scr), min((h, 24 - y0)))
        self.assertEqual(len(scr[0]), min((w, 32 - x0)))
        for j, row in enumerate(scr):
            for i, udg in enumerate(row):
                x, y = x0 + i, y0 + j
                df_addr = 16384 + 2048 * (y // 8) + 32 * (y % 8) + x
                af_addr = 22528 + 32 * y + x
                self.assertEqual(udg.data, snapshot[df_addr:df_addr + 2048:256], 'Graphic data for cell at ({0},{1}) is incorrect'.format(x, y))
                self.assertEqual(udg.attr, snapshot[af_addr], 'Attribute byte for cell at ({0},{1}) is incorrect'.format(x, y))

    def test_colour_parsing(self):
        # Valid colours
        exp_colours = (
            ('RED', '#C40000', (196, 0, 0)),
            ('WHITE', '#cde', (204, 221, 238)),
            ('YELLOW', '198,197,0', (198, 197, 0))
        )
        colours = ['[Colours]']
        colours.extend(['{}={}'.format(name, spec) for name, spec, rgb in exp_colours])
        writer = self._get_writer(ref='\n'.join(colours))
        for name, spec, rgb in exp_colours:
            self.assertEqual(writer.image_writer.palette[name], rgb)

        # Invalid colours
        bad_colours = (
            ('BLACK', ''),
            ('CYAN', '#)0C6C5'),
            ('MAGENTA', '!98,0,198')
        )
        for name, spec in bad_colours:
            with self.assertRaises(SkoolKitError) as cm:
                self._get_writer(ref='[Colours]\n{}={}'.format(name, spec))
            self.assertEqual(cm.exception.args[0], 'Invalid colour spec: {}={}'.format(name, spec))

    def test_get_screenshot(self):
        snapshot = [0] * 16384 + [i & 255 for i in range(6912)]
        writer = self._get_writer(snapshot=snapshot)
        self._assert_scr_equal(writer)
        self._assert_scr_equal(writer, 1, 2, 12, 10)
        self._assert_scr_equal(writer, 10, 10)

    def test_get_font_udg_array(self):
        snapshot = [0] * 65536
        char1 = [1, 2, 3, 4, 5, 6, 7, 8]
        char2 = [8, 7, 6, 5, 4, 3, 2, 1]
        chars = [char1, char2]
        char_data = []
        for char in chars:
            char_data.extend(char)
        address = 32768
        snapshot[address:address + sum(len(c) for c in chars)] = char_data
        writer = self._get_writer(snapshot=snapshot)
        attr = 56
        message = ''.join([chr(n) for n in range(32, 32 + len(chars))])
        font_udg_array = writer.get_font_udg_array(address, attr, message)
        self.assertEqual(len(font_udg_array[0]), len(chars))
        for i, udg in enumerate(font_udg_array[0]):
            self.assertEqual(udg.attr, attr)
            self.assertEqual(udg.data, chars[i])

    def test_ref_parsing(self):
        ref = '\n'.join((
            '[Links]',
            'Bugs=[Bugs] (program errors)',
            'Pokes=[Pokes [with square brackets in the link text]] (cheats)',
            '',
            '[MemoryMap:TestMap]',
            'EntryTypes=w',
        ))
        writer = self._get_writer(ref=ref, skool='w30000 DEFW 0')

        # [Links]
        self.assertEqual(writer.links['Bugs'], ('Bugs', ' (program errors)'))
        self.assertEqual(writer.links['Pokes'], ('Pokes [with square brackets in the link text]', ' (cheats)'))

        # [MemoryMap:*]
        self.assertIn('TestMap', writer.main_memory_maps)
        self.assertIn('TestMap', writer.memory_maps)
        self.assertEqual(writer.memory_maps['TestMap'], {'EntryTypes': 'w'})

    @patch.object(skoolhtml, 'REF_FILE', MINIMAL_REF_FILE + '[Foo]\nBar')
    def test_get_section_from_default_ref_file(self):
        writer = self._get_writer(ref='')
        section = writer.get_section('Foo')
        self.assertEqual(section, 'Bar')

    @patch.object(skoolhtml, 'REF_FILE', MINIMAL_REF_FILE + '[Foo]\nBar')
    def test_get_section_from_user_ref_file(self):
        writer = self._get_writer(ref='[Foo]\nBaz')
        section = writer.get_section('Foo')
        self.assertEqual(section, 'Baz')

    @patch.object(skoolhtml, 'REF_FILE', MINIMAL_REF_FILE + '[Foo:a]\nBar\n[Foo:b]\nBaz\n[Foo:c]\nQux')
    def test_get_sections(self):
        writer = self._get_writer(ref='[Foo:b]\nXyzzy')
        exp_sections = [('a', 'Bar'), ('b', 'Xyzzy'), ('c', 'Qux')]
        sections = writer.get_sections('Foo')
        self.assertEqual(exp_sections, sections)

    @patch.object(skoolhtml, 'REF_FILE', MINIMAL_REF_FILE + '[Foo]\nBar=Baz')
    def test_get_dictionary_from_default_ref_file(self):
        writer = self._get_writer(ref='')
        foo = writer.get_dictionary('Foo')
        self.assertEqual({'Bar': 'Baz'}, foo)

    @patch.object(skoolhtml, 'REF_FILE', MINIMAL_REF_FILE + '[Foo]\nBar=Baz\nQux=Xyzzy')
    def test_get_dictionary_from_user_ref_file(self):
        writer = self._get_writer(ref='[Foo]\nQux=Wibble')
        foo = writer.get_dictionary('Foo')
        self.assertEqual({'Bar': 'Baz', 'Qux': 'Wibble'}, foo)

    @patch.object(skoolhtml, 'REF_FILE', MINIMAL_REF_FILE + '[Foo:a]\nBar=Baz\n[Foo:b]\nBaz=Qux\nQux=Xyzzy\n[Foo:c]\nXyzzy=Wobble')
    def test_get_dictionaries(self):
        writer = self._get_writer(ref='[Foo:b]\nBaz=Wibble')
        exp_dicts = [
            ('a', {'Bar': 'Baz'}),
            ('b', {'Baz': 'Wibble', 'Qux': 'Xyzzy'}),
            ('c', {'Xyzzy': 'Wobble'})
        ]
        foo_dicts = writer.get_dictionaries('Foo')
        self.assertEqual(exp_dicts, foo_dicts)

    def test_write_file(self):
        fname = 'foo/bar/baz.html'
        contents = '<html></html>'
        writer = self._get_writer(mock_write_file=False)
        writer.write_file(fname, contents)
        fpath = join(self.odir, GAMEDIR, fname)
        self.assertTrue(isfile(fpath), '{} does not exist'.format(fpath))
        with open(fpath, 'r') as f:
            actual_contents = f.read()
        self.assertEqual(actual_contents, contents)

    def test_parse_image_params(self):
        writer = self._get_writer()
        def_crop_rect = (0, 0, None, None)

        text = '1,2,$3'
        end, img_path, crop_rect, p1, p2, p3 = writer.parse_image_params(text, 0, 3)
        self.assertEqual(img_path, None)
        self.assertEqual(crop_rect, def_crop_rect)
        self.assertEqual((p1, p2, p3), (1, 2, 3))
        self.assertEqual(end, len(text))

        text = '4,$a,6{0,1,24,32}'
        end, img_path, crop_rect, p1, p2, p3, p4, p5 = writer.parse_image_params(text, 0, 5, (7, 8))
        self.assertEqual(img_path, None)
        self.assertEqual(crop_rect, (0, 1, 24, 32))
        self.assertEqual((p1, p2, p3, p4, p5), (4, 10, 6, 7, 8))
        self.assertEqual(end, len(text))

        text = '$ff,8,9(img)'
        end, img_path, crop_rect, p1, p2, p3 = writer.parse_image_params(text, 0, 3)
        self.assertEqual(img_path, 'images/udgs/img.png')
        self.assertEqual(crop_rect, def_crop_rect)
        self.assertEqual((p1, p2, p3), (255, 8, 9))
        self.assertEqual(end, len(text))

        text = '0,1{1,2}(scr)'
        end, img_path, crop_rect, p1, p2 = writer.parse_image_params(text, 0, 2, path_id='ScreenshotImagePath')
        self.assertEqual(img_path, 'images/scr/scr.png')
        self.assertEqual(crop_rect, (1, 2, None, None))
        self.assertEqual((p1, p2), (0, 1))
        self.assertEqual(end, len(text))

    def test_parse_image_params_too_many_parameters(self):
        writer = self._get_writer()
        with self.assertRaisesRegexp(MacroParsingError, re.escape("Too many parameters (expected 3): '0,1,2,3'")):
            writer.parse_image_params('0,1,2,3{1,2}(x)', 0, 3)

    def test_parse_image_params_not_enough_parameters(self):
        writer = self._get_writer()
        with self.assertRaisesRegexp(MacroParsingError, re.escape("Not enough parameters (expected 2): '0'")):
            writer.parse_image_params('0(x)', 0, 2)

    def test_parse_image_params_with_kwargs(self):
        writer = self._get_writer()

        text = '1,baz=7,bar=23'
        end, img_path, crop_rect, foo, bar, baz = writer.parse_image_params(text, 0, defaults=(2, 3), names=('foo', 'bar', 'baz'))
        self.assertEqual(img_path, None)
        self.assertEqual((0, 0, None, None), crop_rect)
        self.assertEqual(foo, 1)
        self.assertEqual(bar, 23)
        self.assertEqual(baz, 7)
        self.assertEqual(end, len(text))

        text = '1{y=1,height=6}'
        end, img_path, crop_rect, p1 = writer.parse_image_params(text, 0, 1)
        self.assertEqual(img_path, None)
        self.assertEqual((0, 1, None, 6), crop_rect)
        self.assertEqual(p1, 1)
        self.assertEqual(end, len(text))

        text = '2{width=5,x=2}(foo)'
        end, img_path, crop_rect, p1 = writer.parse_image_params(text, 0, 1)
        self.assertEqual(img_path, 'images/udgs/foo.png')
        self.assertEqual((2, 0, 5, None), crop_rect)
        self.assertEqual(p1, 2)
        self.assertEqual(end, len(text))

        text = 'bar=3,foo=NaN(baz)'
        end, img_path, crop_rect, foo, bar = writer.parse_image_params(text, 0, chars='N', ints=(1,), names=('foo', 'bar'))
        self.assertEqual(foo, 'NaN')
        self.assertEqual(bar, 3)

    def test_parse_image_params_with_kwargs_not_enough_parameters(self):
        writer = self._get_writer()
        with self.assertRaisesRegexp(MacroParsingError, "Missing required argument 'foo'"):
            writer.parse_image_params('baz=0(x)', 0, defaults=(2, 3), names=('foo', 'bar', 'baz'))

    def test_parse_image_params_unknown_kwarg(self):
        writer = self._get_writer()
        with self.assertRaisesRegexp(MacroParsingError, "Unknown keyword argument: 'xyzzy=7'"):
            writer.parse_image_params('bar=1,xyzzy=7', 0, defaults=(1, 2), names=('foo', 'bar'))

    def test_parse_image_params_blank_path_id(self):
        writer = self._get_writer()

        text = '1(foo/bar)'
        end, img_path, crop_rect, val = writer.parse_image_params(text, 0, 1, path_id=None)
        self.assertEqual(img_path, 'foo/bar')

        text = '2(baz)'
        end, img_path, crop_rect, val = writer.parse_image_params(text, 0, 1, path_id='')
        self.assertEqual(img_path, 'baz')

    def test_image_path(self):
        writer = self._get_writer()
        def_img_format = writer.default_image_format

        img_path = writer.image_path('img')
        self.assertEqual(img_path, '{0}/img.{1}'.format(writer.paths['UDGImagePath'], def_img_format))

        img_path = writer.image_path('/pics/foo.png')
        self.assertEqual(img_path, 'pics/foo.png')

        path_id = 'ScreenshotImagePath'
        img_path = writer.image_path('img.gif', path_id)
        self.assertEqual(img_path, '{0}/img.gif'.format(writer.paths[path_id]))

        path_id = 'UnknownImagePath'
        fname = 'img.png'
        with self.assertRaisesRegexp(SkoolKitError, "Unknown path ID '{}' for image file '{}'".format(path_id, fname)):
            writer.image_path(fname, path_id)

    def test_flip_udgs(self):
        writer = self._get_writer()
        udg1 = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg2 = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [2, 4, 6, 8, 10, 12, 14, 16])
        udg3 = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1])
        udg4 = Udg(0, [8, 7, 6, 5, 4, 3, 2, 1], [255, 254, 253, 252, 251, 250, 249, 248])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.flip_udgs(udgs, 0)
        self.assertEqual(udgs, [[udg1, udg2], [udg3, udg4]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.flip_udgs(udgs, 1)
        udg1_f, udg2_f, udg3_f, udg4_f = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_f.flip(1)
        udg2_f.flip(1)
        udg3_f.flip(1)
        udg4_f.flip(1)
        self.assertEqual(udgs, [[udg2_f, udg1_f], [udg4_f, udg3_f]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.flip_udgs(udgs, 2)
        udg1_f, udg2_f, udg3_f, udg4_f = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_f.flip(2)
        udg2_f.flip(2)
        udg3_f.flip(2)
        udg4_f.flip(2)
        self.assertEqual(udgs, [[udg3_f, udg4_f], [udg1_f, udg2_f]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.flip_udgs(udgs, 3)
        udg1_f, udg2_f, udg3_f, udg4_f = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_f.flip(3)
        udg2_f.flip(3)
        udg3_f.flip(3)
        udg4_f.flip(3)
        self.assertEqual(udgs, [[udg4_f, udg3_f], [udg2_f, udg1_f]])

    def test_flip_udgs_with_duplicates(self):
        writer = self._get_writer()
        base_udg = Udg(1, [2, 3, 5, 7, 11, 13, 17, 19])
        udg = base_udg.copy()

        udgs = [[udg, udg]]
        writer.flip_udgs(udgs, 1)
        udg_f = base_udg.copy()
        udg_f.flip(1)
        self.assertEqual([[udg_f, udg_f]], udgs)

    def test_rotate_udgs(self):
        writer = self._get_writer()
        udg1 = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg2 = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [2, 4, 6, 8, 10, 12, 14, 16])
        udg3 = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1])
        udg4 = Udg(0, [8, 7, 6, 5, 4, 3, 2, 1], [255, 254, 253, 252, 251, 250, 249, 248])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.rotate_udgs(udgs, 0)
        self.assertEqual(udgs, [[udg1, udg2], [udg3, udg4]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.rotate_udgs(udgs, 1)
        udg1_r, udg2_r, udg3_r, udg4_r = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_r.rotate(1)
        udg2_r.rotate(1)
        udg3_r.rotate(1)
        udg4_r.rotate(1)
        self.assertEqual(udgs, [[udg3_r, udg1_r], [udg4_r, udg2_r]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.rotate_udgs(udgs, 2)
        udg1_r, udg2_r, udg3_r, udg4_r = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_r.rotate(2)
        udg2_r.rotate(2)
        udg3_r.rotate(2)
        udg4_r.rotate(2)
        self.assertEqual(udgs, [[udg4_r, udg3_r], [udg2_r, udg1_r]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.rotate_udgs(udgs, 3)
        udg1_r, udg2_r, udg3_r, udg4_r = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_r.rotate(3)
        udg2_r.rotate(3)
        udg3_r.rotate(3)
        udg4_r.rotate(3)
        self.assertEqual(udgs, [[udg2_r, udg4_r], [udg1_r, udg3_r]])

    def test_rotate_udgs_with_duplicates(self):
        writer = self._get_writer()
        base_udg = Udg(1, [2, 3, 5, 7, 11, 13, 17, 19])
        udg = base_udg.copy()

        udgs = [[udg, udg]]
        writer.rotate_udgs(udgs, 1)
        udg_r = base_udg.copy()
        udg_r.rotate(1)
        self.assertEqual([[udg_r], [udg_r]], udgs)

    def test_write_image(self):
        writer = self._get_writer(mock_file_info=True)
        image_writer = writer.image_writer
        file_info = writer.file_info

        # PNG
        image_path = 'images/test.png'
        udgs = [[Udg(0, (0,) * 8)]]
        writer.write_image(image_path, udgs)
        self.assertEqual(file_info.fname, image_path)
        self.assertEqual(file_info.mode, 'wb')
        self.assertEqual(image_writer.udg_array, udgs)
        self.assertEqual(image_writer.img_format, 'png')
        self.assertEqual(image_writer.scale, 2)
        self.assertFalse(image_writer.mask)
        self.assertEqual(image_writer.x, 0)
        self.assertEqual(image_writer.y, 0)
        self.assertEqual(image_writer.width, 16)
        self.assertEqual(image_writer.height, 16)

        # GIF
        image_path = 'images/test.gif'
        writer.write_image(image_path, udgs)
        self.assertEqual(file_info.fname, image_path)
        self.assertEqual(image_writer.img_format, 'gif')

        # Unsupported format
        image_path = 'images/test.jpg'
        with self.assertRaisesRegexp(SkoolKitError, 'Unsupported image file format: {}'.format(image_path)):
            writer.write_image(image_path, udgs)

    def test_write_animated_image_png(self):
        writer = self._get_writer(mock_file_info=True)
        image_writer = writer.image_writer
        file_info = writer.file_info

        image_path = 'images/test_animated.png'
        frames = object()
        writer.write_animated_image(image_path, frames)
        self.assertEqual(file_info.fname, image_path)
        self.assertEqual(file_info.mode, 'wb')
        self.assertEqual(image_writer.frames, frames)
        self.assertEqual(image_writer.img_format, 'png')

    def test_write_animated_image_gif(self):
        writer = self._get_writer(mock_file_info=True)
        image_writer = writer.image_writer
        file_info = writer.file_info

        image_path = 'images/test_animated.gif'
        frames = object()
        writer.write_animated_image(image_path, frames)
        self.assertEqual(file_info.fname, image_path)
        self.assertEqual(file_info.mode, 'wb')
        self.assertEqual(image_writer.frames, frames)
        self.assertEqual(image_writer.img_format, 'gif')

    def test_write_animated_image_unsupported_format(self):
        writer = self._get_writer(mock_file_info=True)

        image_path = 'images/test_animated.jpg'
        with self.assertRaisesRegexp(SkoolKitError, 'Unsupported image file format: {}'.format(image_path)):
            writer.write_animated_image(image_path, None)

class SkoolMacroTest(HtmlWriterTestCase):
    def setUp(self):
        HtmlWriterTestCase.setUp(self)
        patch.object(skoolhtml, 'REF_FILE', SKOOL_MACRO_MINIMAL_REF_FILE).start()
        self.addCleanup(patch.stopall)

    def _assert_html_equal(self, html, exp_html, eol=False, trim=False):
        lines = []
        for line in html.split('\n'):
            s_line = line.lstrip()
            if s_line or not trim:
                lines.append(s_line)
        exp_lines = []
        for line in exp_html.split('\n'):
            s_line = line.lstrip()
            if s_line:
                exp_lines.append(s_line)
        if eol:
            exp_lines.append('')
        self.assertEqual(exp_lines, lines)

    def _compare_udgs(self, udg_array, exp_udg_array):
        for i, row in enumerate(udg_array):
            exp_row = exp_udg_array[i]
            self.assertEqual(len(row), len(exp_row))
            for j, udg in enumerate(row):
                exp_udg = exp_row[j]
                self.assertEqual(udg.attr, exp_udg.attr)
                self.assertEqual(udg.data, exp_udg.data)
                self.assertEqual(udg.mask, exp_udg.mask)

    def _check_image(self, image_writer, udg_array, scale=2, mask=0, x=0, y=0, width=None, height=None):
        if width is None:
            width = 8 * len(udg_array[0]) * scale
        if height is None:
            height = 8 * len(udg_array) * scale
        self.assertEqual(image_writer.scale, scale)
        self.assertEqual(image_writer.mask, mask)
        self.assertEqual(image_writer.x, x)
        self.assertEqual(image_writer.y, y)
        self.assertEqual(image_writer.width, width)
        self.assertEqual(image_writer.height, height)
        self.assertEqual(len(image_writer.udg_array), len(udg_array))
        self._compare_udgs(image_writer.udg_array, udg_array)

    def _check_animated_image(self, image_writer, frames):
        self.assertEqual(len(image_writer.frames), len(frames))
        for i, frame in enumerate(image_writer.frames):
            exp_frame = frames[i]
            self.assertEqual(frame.scale, exp_frame.scale)
            self.assertEqual(frame.x, exp_frame.x)
            self.assertEqual(frame.y, exp_frame.y)
            self.assertEqual(frame.width, exp_frame.width)
            self.assertEqual(frame.height, exp_frame.height)
            self.assertEqual(frame.mask, exp_frame.mask)
            self.assertEqual(frame.delay, exp_frame.delay)
            self._compare_udgs(frame.udgs, exp_frame.udgs)

    def _assert_link_equals(self, html, href, text, suffix=''):
        self.assertEqual(html, '<a href="{}">{}</a>{}'.format(href, text, suffix))

    def _assert_img_equals(self, html, alt, src):
        self.assertEqual(html, '<img alt="{0}" src="{1}" />'.format(alt, src))

    def _test_reference_macro(self, macro, def_link_text, page):
        writer = self._get_writer()
        for link_text in ('', '(test)', '(test (nested) parentheses)'):
            for anchor in ('', '#test', '#foo$bar'):
                output = writer.expand('#{}{}{}'.format(macro, anchor, link_text), ASMDIR)
                self._assert_link_equals(output, '../{}/{}.html{}'.format(REFERENCE_DIR, page, anchor), link_text[1:-1] or def_link_text)

        for suffix in ',;:.!)?/"\'':
            output = writer.expand('#{}#name{}'.format(macro, suffix), ASMDIR)
            self._assert_link_equals(output, '../{}/{}.html#name'.format(REFERENCE_DIR, page), def_link_text, suffix)

    def _assert_error(self, writer, text, error_msg=None, prefix=None, error=SkoolParsingError):
        with self.assertRaises(error) as cm:
            writer.expand(text, ASMDIR)
        if error_msg:
            if prefix:
                error_msg = '{}: {}'.format(prefix, error_msg)
            self.assertEqual(cm.exception.args[0], error_msg)

    def _test_invalid_reference_macro(self, macro):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format(macro)

        # Non-existent item
        self._assert_error(writer, '#{}#nonexistentItem()'.format(macro), "Cannot determine title of item 'nonexistentItem'", prefix)

        # Malformed item name
        self._assert_error(writer, '#{}bad#name()'.format(macro), "Malformed macro: #{}bad#name()".format(macro), prefix)

        # No item name
        self._assert_error(writer, '#{}#(foo)'.format(macro), "No item name: #{}#(foo)".format(macro), prefix)

        # No closing bracket
        self._assert_error(writer, '#{}(foo'.format(macro), "No closing bracket: (foo", prefix)

    def _test_call(self, cwd, arg1, arg2, arg3=None):
        # Method used to test the #CALL macro
        return str((cwd, arg1, arg2, arg3))

    def _test_call_no_retval(self, *args):
        return

    def _unsupported_macro(self, *args):
        raise UnsupportedMacroError()

    def test_macro_bug(self):
        self._test_reference_macro('BUG', 'bug', 'bugs')

        # Anchor with empty link text
        writer = self._get_writer()
        anchor = 'bug1'
        title = 'Bad bug'
        writer.bugs = [(anchor, title, None)]
        output = writer.expand('#BUG#{0}()'.format(anchor), ASMDIR)
        self._assert_link_equals(output, '../reference/bugs.html#{0}'.format(anchor), title)

    def test_macro_bug_invalid(self):
        self._test_invalid_reference_macro('BUG')

    def test_macro_call(self):
        writer = self._get_writer()
        writer.test_call = self._test_call

        # All arguments given
        output = writer.expand('#CALL:test_call(10,test)', ASMDIR)
        self.assertEqual(output, self._test_call(ASMDIR, 10, 'test'))

        # One argument omitted
        output = writer.expand('#CALL:test_call(3,,test2)', ASMDIR)
        self.assertEqual(output, self._test_call(ASMDIR, 3, None, 'test2'))

        # No return value
        writer.test_call_no_retval = self._test_call_no_retval
        output = writer.expand('#CALL:test_call_no_retval(1,2)', ASMDIR)
        self.assertEqual(output, '')

        # Unknown method
        method_name = 'nonexistent_method'
        output = writer.expand('#CALL:{0}(0)'.format(method_name), ASMDIR)
        self.assertEqual(output, '')
        self.assertEqual(self.err.getvalue().split('\n')[0], 'WARNING: Unknown method name in #CALL macro: {0}'.format(method_name))

    def test_macro_call_invalid(self):
        writer = self._get_writer()
        writer.test_call = self._test_call
        prefix = ERROR_PREFIX.format('CALL')

        # No parameters
        self._assert_error(writer, '#CALL', 'No parameters', prefix)

        # Malformed #CALL macro
        self._assert_error(writer, '#CALLtest_call(5,s)', 'Malformed macro: #CALLt...', prefix)

        # No method name
        self._assert_error(writer, '#CALL:(0)', 'No method name', prefix)

        # #CALL a non-method
        writer.var = 'x'
        self._assert_error(writer, '#CALL:var(0)', 'Uncallable method name: var', prefix)

        # No argument list
        self._assert_error(writer, '#CALL:test_call', 'No argument list specified: #CALL:test_call', prefix)

        # No closing bracket
        self._assert_error(writer, '#CALL:test_call(1,2', 'No closing bracket: (1,2', prefix)

        # Not enough parameters
        self._assert_error(writer, '#CALL:test_call(1)')

        # Too many parameters
        self._assert_error(writer, '#CALL:test_call(1,2,3,4)')

    def test_macro_chr(self):
        writer = self._get_writer()

        output = writer.expand('#CHR169', ASMDIR)
        self.assertEqual(output, '&#169;')

        output = writer.expand('#CHR(163)1984', ASMDIR)
        self.assertEqual(output, '&#163;1984')

    def test_macro_chr_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('CHR')

        # No parameter
        self._assert_error(writer, '#CHR', 'No parameters (expected 1)', prefix)

        # Blank parameter
        self._assert_error(writer, '#CHR()', "Invalid integer: ''", prefix)

        # Invalid parameter (1)
        self._assert_error(writer, '#CHR2$', "Cannot parse integer '2$' in parameter string: '2$'", prefix)

        # Invalid parameter (2)
        self._assert_error(writer, '#CHR(x)', "Invalid integer: 'x'", prefix)

        # No closing bracket
        self._assert_error(writer, '#CHR(2 ...', 'No closing bracket: (2 ...', prefix)

    def test_macro_d(self):
        skool = '\n'.join((
            '; First routine',
            'c32768 RET',
            '',
            '; Second routine',
            'c32769 RET',
            '',
            'c32770 RET',
        ))
        writer = self._get_writer(skool=skool)

        output = writer.expand('#D32768', ASMDIR)
        self.assertEqual(output, 'First routine')

        output = writer.expand('#D$8001', ASMDIR)
        self.assertEqual(output, 'Second routine')

    def test_macro_d_invalid(self):
        writer = self._get_writer(skool='c32770 RET')
        prefix = ERROR_PREFIX.format('D')

        # No parameter (1)
        self._assert_error(writer, '#D', 'No parameters (expected 1)', prefix)

        # No parameter (2)
        self._assert_error(writer, '#Dx', 'No parameters (expected 1)', prefix)

        # Invalid parameter
        self._assert_error(writer, '#D234$', "Cannot parse integer '234$' in parameter string: '234$'", prefix)

        # Descriptionless entry
        self._assert_error(writer, '#D32770', 'Entry at 32770 has no description', prefix)

        # Non-existent entry
        self._assert_error(writer, '#D32771', 'Cannot determine description for non-existent entry at 32771', prefix)

    def test_macro_erefs(self):
        # Entry point with one referrer
        skool = '\n'.join((
            '; Referrer',
            'c40000 JP 40004',
            '',
            '; Routine',
            'c40003 LD A,B',
            ' 40004 INC A'
        ))
        writer = self._get_writer(skool=skool)
        output = writer.expand('#EREFS40004', ASMDIR)
        self.assertEqual(output, 'routine at <a href="40000.html">40000</a>')

        # Entry point with more than one referrer
        skool = '\n'.join((
            '; First routine',
            'c30000 CALL 30004',
            '',
            '; Second routine',
            'c30003 LD A,B',
            ' 30004 LD B,C',
            '',
            '; Third routine',
            'c30005 JP 30004',
        ))
        writer = self._get_writer(skool=skool)
        output = writer.expand('#EREFS30004', ASMDIR)
        self.assertEqual(output, 'routines at <a href="30000.html">30000</a> and <a href="30005.html">30005</a>')

    def test_macro_erefs_invalid(self):
        writer = self._get_writer(skool='c30005 JP 30004')
        prefix = ERROR_PREFIX.format('EREFS')

        # No parameter (1)
        self._assert_error(writer, '#EREFS', 'No parameters (expected 1)', prefix)

        # No parameter (2)
        self._assert_error(writer, '#EREFSx', 'No parameters (expected 1)', prefix)

        # Invalid parameter
        self._assert_error(writer, '#EREFS2$2', "Cannot parse integer '2$2' in parameter string: '2$2'", prefix)

        # Entry point with no referrers
        address = 30005
        self._assert_error(writer, '#EREFS30005', 'Entry point at 30005 has no referrers', prefix)

    def test_macro_fact(self):
        self._test_reference_macro('FACT', 'fact', 'facts')

        # Anchor with empty link text
        writer = self._get_writer()
        anchor = 'fact1'
        title = 'Amazing fact'
        writer.facts = [(anchor, title, None)]
        output = writer.expand('#FACT#{0}()'.format(anchor), ASMDIR)
        self._assert_link_equals(output, '../reference/facts.html#{0}'.format(anchor), title)

    def test_macro_fact_invalid(self):
        self._test_invalid_reference_macro('FACT')

    def test_macro_font(self):
        snapshot = [0] * 65536
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)

        output = writer.expand('#FONT32768,96', ASMDIR)
        self._assert_img_equals(output, 'font', '../{}/font.png'.format(FONTDIR))

        img_fname = 'font2'
        output = writer.expand('#FONT55584,96({0})'.format(img_fname), ASMDIR)
        self._assert_img_equals(output, img_fname, '../{}/{}.png'.format(FONTDIR, img_fname))

        img_fname = 'font3'
        font_addr = 32768
        char1 = [1, 2, 3, 4, 5, 6, 7, 8]
        char2 = [8, 7, 6, 5, 4, 3, 2, 1]
        char3 = [1, 3, 7, 15, 31, 63, 127, 255]
        chars = (char1, char2, char3)
        for i, char in enumerate(chars):
            snapshot[font_addr + i * 8:font_addr + (i + 1) * 8] = char
        attr = 4
        scale = 2
        x, y, w, h = 1, 2, 3, 4
        values = (font_addr, len(chars), attr, scale, x, y, w, h, img_fname)
        macro = '#FONT{0},{1},{2},{3}{{{4},{5},{6},{7}}}({8})'.format(*values)
        output = writer.expand(macro, ASMDIR)
        exp_img_fname = '../{}/{}.png'.format(FONTDIR, img_fname)
        self._assert_img_equals(output, img_fname, exp_img_fname)
        udg_array = [[Udg(4, char) for char in chars]]
        self._check_image(writer.image_writer, udg_array, scale, False, x, y, w, h)

        macro = '#FONTscale={3},chars={1},addr={0},attr={2}{{x={4},y={5},width={6},height={7}}}({8})'.format(*values)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, img_fname, exp_img_fname)
        self._check_image(writer.image_writer, udg_array, scale, False, x, y, w, h)

    def test_macro_font_text(self):
        snapshot = [1, 2, 3, 4, 5, 6, 7, 8] # ' '
        snapshot.extend((8, 7, 6, 5, 4, 3, 2, 1)) # '!'
        snapshot.extend((1, 3, 7, 15, 31, 63, 127, 255)) # '"'
        snapshot.extend([0] * 56)
        snapshot.extend((1, 3, 5, 7, 9, 11, 13, 15)) # ')'
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)

        img_fname = 'message'
        message = ' !"%'
        macro = '#FONT:({})0({})'.format(message, img_fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, img_fname, '../{}/{}.png'.format(FONTDIR, img_fname))
        udg_array = [[]]
        for c in message:
            c_addr = 8 * (ord(c) - 32)
            udg_array[0].append(Udg(56, snapshot[c_addr:c_addr + 8]))
        self._check_image(writer.image_writer, udg_array)

        message = ')!!!!'
        attr = 43
        scale = 5
        c_addr = 8 * (ord(message[0]) - 32)
        udg_array = [[Udg(attr, snapshot[c_addr:c_addr + 8])]]
        for delim1, delim2 in (('{', '}'), ('[', ']'), ('*', '*'), ('@', '@')):
            macro = '#FONT:{}{}{}0,1,{},{}({})'.format(delim1, message, delim2, attr, scale, img_fname)
            output = writer.expand(macro, ASMDIR)
            self._assert_img_equals(output, img_fname, '../{}/{}.png'.format(FONTDIR, img_fname))
            self._check_image(writer.image_writer, udg_array, scale)

    def test_macro_font_with_custom_font_image_path(self):
        font_path = 'graphics/font'
        ref = '[Paths]\nFontImagePath={}'.format(font_path)
        writer = self._get_writer(ref=ref, snapshot=[0] * 16, mock_file_info=True)
        img_fname = 'text'
        exp_img_path = '{}/{}.png'.format(font_path, img_fname)

        output = writer.expand('#FONT:(!!!)0({})'.format(img_fname), ASMDIR)
        self._assert_img_equals(output, img_fname, '../{}'.format(exp_img_path))
        self.assertEqual(writer.file_info.fname, exp_img_path)

    def test_macro_font_frames(self):
        char1 = [102] * 8
        char2 = [34] * 8
        char3 = [20] * 8
        char4 = [243] * 8
        snapshot = char1 + char2 + char3 + char4
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)
        file_info = writer.file_info

        output = writer.expand('#FONT0,1(*char1)', ASMDIR)
        self.assertEqual(output, '')
        self.assertIsNone(file_info.fname)

        output = writer.expand('#FONT8,1,7(char2*)', ASMDIR)
        exp_image_path = '{}/char2.png'.format(FONTDIR)
        self._assert_img_equals(output, 'char2', '../{}'.format(exp_image_path))
        self.assertEqual(file_info.fname, exp_image_path)

        output = writer.expand('#FONT16,1(char3*char3_frame)', ASMDIR)
        exp_image_path = '{}/char3.png'.format(FONTDIR)
        self._assert_img_equals(output, 'char3', '../{}'.format(exp_image_path))
        self.assertEqual(file_info.fname, exp_image_path)

        output = writer.expand('#FONT24,1,,3{1,2,16,16}(*)', ASMDIR)
        exp_image_path = '{}/font.png'.format(FONTDIR)
        self._assert_img_equals(output, 'font', '../{}'.format(exp_image_path))
        self.assertEqual(file_info.fname, exp_image_path)

        writer.expand('#UDGARRAY*char1;char2;char3_frame;font(chars)', ASMDIR)
        exp_frames = [
            Frame([[Udg(56, char1)]], scale=2),
            Frame([[Udg(7, char2)]], scale=2),
            Frame([[Udg(56, char3)]], scale=2),
            Frame([[Udg(56, char4)]], scale=3, x=1, y=2, width=16, height=16)
        ]
        self._check_animated_image(writer.image_writer, exp_frames)

    def test_macro_font_alt_text(self):
        writer = self._get_writer(snapshot=[0] * 8, mock_file_info=True)

        alt = 'Space'
        output = writer.expand('#FONT:( )0(|{})'.format(alt), ASMDIR)
        self._assert_img_equals(output, alt, '../{}/font.png'.format(FONTDIR))

        fname = 'space'
        alt = 'Another space'
        output = writer.expand('#FONT:( )0({}|{})'.format(fname, alt), ASMDIR)
        self._assert_img_equals(output, alt, '../{}/{}.png'.format(FONTDIR, fname))

    def test_macro_font_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('FONT')

        # No parameters
        self._assert_error(writer, '#FONT', 'No parameters (expected 1)', prefix)

        # No text parameter
        self._assert_error(writer, '#FONT:', 'No text parameter', prefix)

        # Too many parameters
        self._assert_error(writer, '#FONT0,1,2,3,4,5', "Too many parameters (expected 4): '0,1,2,3,4,5'", prefix)

        # Invalid parameter
        self._assert_error(writer, '#FONT0,1$,2', "Cannot parse integer '1$' in parameter string: '0,1$,2'", prefix)

        # No closing bracket
        self._assert_error(writer, '#FONT(foo', 'No closing bracket: (foo', prefix)

        # Empty message
        self._assert_error(writer, '#FONT:()0', 'Empty message: ()', prefix)

        # No terminating text delimiter
        self._assert_error(writer, '#FONT:[hi)0', 'No terminating delimiter: [hi)0', prefix)

    def test_macro_html(self):
        writer = self._get_writer()

        delimiters = {
            '(': ')',
            '[': ']',
            '{': '}'
        }
        for text in('', 'See <a href="url">this</a>', 'A &gt; B'):
            for delim1 in '([{!@$%^*_-+|':
                delim2 = delimiters.get(delim1, delim1)
                output = writer.expand('#HTML{0}{1}{2}'.format(delim1, text, delim2), ASMDIR)
                self.assertEqual(output, text)

        output = writer.expand('#HTML?#CHR169?', ASMDIR)
        self.assertEqual(output, '&#169;')

    def test_macro_html_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('HTML')

        # No text parameter
        self._assert_error(writer, '#HTML', 'No text parameter', prefix)

        # Unterminated
        self._assert_error(writer, '#HTML:unterminated', 'No terminating delimiter: :unterminated', prefix)

    def test_macro_link(self):
        ref = '\n'.join((
            '[Page:page]',
            '[Page:page2]',
            '[Links]',
            'page=Custom page',
            'page2=Custom page 2'
        ))
        writer = self._get_writer(ref=ref)

        link_text = 'bugs'
        output = writer.expand('#LINK:Bugs({0})'.format(link_text), ASMDIR)
        self._assert_link_equals(output, '../{0}/bugs.html'.format(REFERENCE_DIR), link_text)

        link_text = 'pokes'
        anchor = '#poke1'
        output = writer.expand('#LINK:Pokes{0}({1})'.format(anchor, link_text), ASMDIR)
        self._assert_link_equals(output, '../{0}/pokes.html{1}'.format(REFERENCE_DIR, anchor), link_text)

        output = writer.expand('#LINK:page()', ASMDIR)
        self._assert_link_equals(output, '../page.html', 'Custom page')

        output = writer.expand('#LINK:page2#anchor~1()', ASMDIR)
        self._assert_link_equals(output, '../page2.html#anchor~1', 'Custom page 2')

    def test_macro_link_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('LINK')

        # No parameters
        self._assert_error(writer, '#LINK', 'No parameters', prefix)

        # No page ID (1)
        self._assert_error(writer, '#LINK:', 'No page ID: #LINK:', prefix)

        # No page ID (2)
        self._assert_error(writer, '#LINK:(text)', 'No page ID: #LINK:(text)', prefix)

        # No closing bracket
        self._assert_error(writer, '#LINK:(text', 'No closing bracket: (text', prefix)

        # Malformed macro
        self._assert_error(writer, '#LINKpageID(text)', 'Malformed macro: #LINKp...', prefix)

        # Unknown page ID
        self._assert_error(writer, '#LINK:nonexistentPageID(text)', 'Unknown page ID: nonexistentPageID', prefix)

        # No link text
        self._assert_error(writer, '#LINK:Bugs', 'No link text: #LINK:Bugs', prefix)

    def test_macro_list(self):
        writer = self._get_writer()

        # List with a CSS class and an item containing a skool macro
        src = "(default){ Item 1 }{ Item 2 }{ #REGa }"
        html = '\n'.join((
            '<ul class="default">',
            '<li>Item 1</li>',
            '<li>Item 2</li>',
            '<li><span class="register">A</span></li>',
            '</ul>'
        ))
        output = writer.expand('#LIST{0}\nLIST#'.format(src), ASMDIR)
        self.assertEqual(output, html)

        # List with no CSS class
        src = "{ Item 1 }"
        html = '\n'.join((
            '<ul class="">',
            '<li>Item 1</li>',
            '</ul>'
        ))
        output = writer.expand('#LIST{0}\nLIST#'.format(src), ASMDIR)
        self.assertEqual(output, html)

        # Empty list
        output = writer.expand('#LIST LIST#', ASMDIR)
        self.assertEqual(output, '<ul class="">\n\n</ul>')

    def test_macro_list_invalid(self):
        writer = self._get_writer()

        # No end marker
        self._assert_error(writer, '#LIST { Item }', 'No end marker: #LIST { Item }...')

    def test_macro_poke(self):
        self._test_reference_macro('POKE', 'poke', 'pokes')

        # Anchor with empty link text
        writer = self._get_writer()
        anchor = 'poke1'
        title = 'Awesome POKE'
        writer.pokes = [(anchor, title, None)]
        output = writer.expand('#POKE#{0}()'.format(anchor), ASMDIR)
        self._assert_link_equals(output, '../reference/pokes.html#{0}'.format(anchor), title)

    def test_macro_poke_invalid(self):
        self._test_invalid_reference_macro('POKE')

    def test_macro_pokes(self):
        writer = self._get_writer(snapshot=[0] * 65536)
        snapshot = writer.snapshot

        output = writer.expand('#POKES32768,255', ASMDIR)
        self.assertEqual(output, '')
        self.assertEqual(snapshot[32768], 255)

        output = writer.expand('#POKES32768,254,10', ASMDIR)
        self.assertEqual(output, '')
        self.assertEqual(snapshot[32768:32778], [254] * 10)

        output = writer.expand('#POKES32768,253,20,2', ASMDIR)
        self.assertEqual(output, '')
        self.assertEqual(snapshot[32768:32808:2], [253] * 20)

        output = writer.expand('#POKES49152,1;49153,2', ASMDIR)
        self.assertEqual(output, '')
        self.assertEqual(snapshot[49152:49154], [1, 2])

    def test_macro_pokes_invalid(self):
        writer = self._get_writer(snapshot=[0])
        prefix = ERROR_PREFIX.format('POKES')

        # No parameters (1)
        self._assert_error(writer, '#POKES', 'No parameters (expected 2)', prefix)

        # Not enough parameters (1)
        self._assert_error(writer, '#POKES0', "Not enough parameters (expected 2): '0'", prefix)

        # Not enough parameters (2)
        self._assert_error(writer, '#POKES0,1;1', "Not enough parameters (expected 2): '1'", prefix)

        # Invalid parameter
        self._assert_error(writer, '#POKES40000,2$2', "Cannot parse integer '2$2' in parameter string: '40000,2$2'", prefix)

    def test_macro_pops(self):
        writer = self._get_writer(snapshot=[0] * 65536)
        addr, byte = 49152, 128
        writer.snapshot[addr] = byte
        writer.push_snapshot('test')
        writer.snapshot[addr] = (byte + 127) % 256
        output = writer.expand('#POPS', ASMDIR)
        self.assertEqual(output, '')
        self.assertEqual(writer.snapshot[addr], byte)

    def test_macro_pops_empty_stack(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('POPS')
        self._assert_error(writer, '#POPS', 'Cannot pop snapshot when snapshot stack is empty', prefix)

    def test_macro_pushs(self):
        writer = self._get_writer(snapshot=[0] * 65536)
        addr, byte = 32768, 64
        for name in ('test', '#foo', 'foo$abcd', ''):
            for suffix in ('', '(bar)', ':baz'):
                writer.snapshot[addr] = byte
                output = writer.expand('#PUSHS{}{}'.format(name, suffix), ASMDIR)
                self.assertEqual(output, suffix)
                self.assertEqual(writer.get_snapshot_name(), name)
                self.assertEqual(writer.snapshot[addr], byte)
                writer.snapshot[addr] = (byte + 127) % 256
                writer.pop_snapshot()
                self.assertEqual(writer.snapshot[addr], byte)

    def test_macro_r(self):
        skool = '\n'.join((
            'c00000 LD A,B',
            '',
            'c00007 LD A,C',
            '',
            'c00016 LD A,D',
            '',
            'c00115 LD A,E',
            '',
            'c01114 LD A,H',
            '',
            '; Routine',
            'c24576 LD HL,$6003',
            '',
            '; Data',
            'b$6003 DEFB 123',
            ' $6004 DEFB 246',
            '',
            '; Another routine',
            'c24581 NOP',
            ' 24582 NOP',
            '',
            '; Yet another routine',
            'c24583 CALL 24581',
            '',
            '; Another routine still',
            'c24586 CALL 24581',
            ' 24589 JP 24582',
            '',
            '; The final routine',
            'c24592 CALL 24582'
        ))
        writer = self._get_writer(skool=skool)

        # Reference address is 0
        output = writer.expand('#R0', ASMDIR)
        self._assert_link_equals(output, '0.html', '0')

        # Reference address is 1 digit
        output = writer.expand('#R7', ASMDIR)
        self._assert_link_equals(output, '7.html', '7')

        # Reference address is 2 digits
        output = writer.expand('#R16', ASMDIR)
        self._assert_link_equals(output, '16.html', '16')

        # Reference address is 3 digits
        output = writer.expand('#R115', ASMDIR)
        self._assert_link_equals(output, '115.html', '115')

        # Reference address is 4 digits
        output = writer.expand('#R1114', ASMDIR)
        self._assert_link_equals(output, '1114.html', '1114')

        # Routine reference
        output = writer.expand('#R24576', ASMDIR)
        self._assert_link_equals(output, '24576.html', '24576')

        # Explicit anchor
        output = writer.expand('#R24576#foo', ASMDIR)
        self._assert_link_equals(output, '24576.html#foo', '24576')

        # Link text
        link_text = 'Testing1'
        output = writer.expand('#R24576({0})'.format(link_text), ASMDIR)
        self._assert_link_equals(output, '24576.html', link_text)

        # Different current working directory
        output = writer.expand('#R24576', 'other')
        self._assert_link_equals(output, '../{0}/24576.html'.format(ASMDIR), '24576')

        # Routine with a hexadecimal address
        output = writer.expand('#R24579', ASMDIR)
        self._assert_link_equals(output, '24579.html', '6003')

        # Entry point reference
        output = writer.expand('#R24580', ASMDIR)
        self._assert_link_equals(output, '24579.html#24580', '6004')

        # Entry point reference with explicit anchor
        output = writer.expand('#R24580#bar', ASMDIR)
        self._assert_link_equals(output, '24579.html#bar', '6004')

        # Non-existent reference
        prefix = ERROR_PREFIX.format('R')
        self._assert_error(writer, '#R$ABCD', 'Could not find routine file containing $ABCD', prefix)

    def test_macro_r_other_code(self):
        ref = '\n'.join((
            '[OtherCode:other]',
            'Source=other.skool'
        ))
        skool = '\n'.join((
            'c49152 LD DE,0',
            ' 49155 RET',
            '',
            'r$C000 other',
            ' $c003'
        ))
        writer = self._get_writer(ref=ref, skool=skool)

        # Reference with the same address as a remote entry
        output = writer.expand('#R49152', ASMDIR)
        self._assert_link_equals(output, '49152.html', '49152')

        # Reference with the same address as a remote entry point
        output = writer.expand('#R49155', ASMDIR)
        self._assert_link_equals(output, '49152.html#49155', '49155')

        # Other code, no remote entry
        output = writer.expand('#R32768@other', ASMDIR)
        self._assert_link_equals(output, '../other/32768.html', '32768')

        # Other code with remote entry
        output = writer.expand('#R49152@other', ASMDIR)
        self._assert_link_equals(output, '../other/49152.html', 'C000')

        # Other code with remote entry point
        output = writer.expand('#R49155@other', ASMDIR)
        self._assert_link_equals(output, '../other/49152.html#49155', 'c003')

        # Other code with anchor and link text
        link_text = 'Testing2'
        anchor = 'testing3'
        output = writer.expand('#R32768@other#{0}({1})'.format(anchor, link_text), ASMDIR)
        self._assert_link_equals(output, '../other/32768.html#{0}'.format(anchor), link_text)

    def test_macro_r_decimal(self):
        ref = '\n'.join((
            '[OtherCode:other]',
            'Source=other.skool'
        ))
        skool = '\n'.join((
            'c32768 LD A,B',
            ' 32769 RET',
            '',
            'r$C000 other',
            ' $C003'
        ))
        writer = self._get_writer(ref=ref, skool=skool, base=BASE_10)

        # Routine
        output = writer.expand('#R32768', ASMDIR)
        self._assert_link_equals(output, '32768.html', '32768')

        # Routine entry point
        output = writer.expand('#R32769', ASMDIR)
        self._assert_link_equals(output, '32768.html#32769', '32769')

        # Other code, no remote entry
        output = writer.expand('#R32768@other', ASMDIR)
        self._assert_link_equals(output, '../other/32768.html', '32768')

        # Other code with remote entry
        output = writer.expand('#R49152@other', ASMDIR)
        self._assert_link_equals(output, '../other/49152.html', '49152')

        # Other code with remote entry point
        output = writer.expand('#R49155@other', ASMDIR)
        self._assert_link_equals(output, '../other/49152.html#49155', '49155')

    def test_macro_r_hex(self):
        ref = '\n'.join((
            '[OtherCode:other]',
            'Source=other.skool'
        ))
        skool = '\n'.join((
            'c32768 LD A,B',
            ' 32769 RET',
            '',
            'r$C000 other',
            ' $C003'
        ))
        writer = self._get_writer(ref=ref, skool=skool, base=BASE_16)

        # Routine
        output = writer.expand('#R32768', ASMDIR)
        self._assert_link_equals(output, '32768.html', '8000')

        # Routine entry point
        output = writer.expand('#R32769', ASMDIR)
        self._assert_link_equals(output, '32768.html#32769', '8001')

        # Other code, no remote entry
        output = writer.expand('#R32768@other', ASMDIR)
        self._assert_link_equals(output, '../other/32768.html', '8000')

        # Other code with remote entry
        output = writer.expand('#R49152@other', ASMDIR)
        self._assert_link_equals(output, '../other/49152.html', 'C000')

        # Other code with remote entry point
        output = writer.expand('#R49155@other', ASMDIR)
        self._assert_link_equals(output, '../other/49152.html#49155', 'C003')

    def test_macro_r_hex_lower(self):
        ref = '\n'.join((
            '[OtherCode:Other]',
            'Source=other.skool',
            '[Paths]',
            'Other-CodePath=other'
        ))
        skool = '\n'.join((
            'c40970 LD A,B',
            ' 40971 RET',
            '',
            'r$C000 other',
            ' $C003'
        ))
        writer = self._get_writer(ref=ref, skool=skool, case=CASE_LOWER, base=BASE_16)

        # Routine
        output = writer.expand('#R40970', ASMDIR)
        self._assert_link_equals(output, '40970.html', 'a00a')

        # Routine entry point
        output = writer.expand('#R40971', ASMDIR)
        self._assert_link_equals(output, '40970.html#40971', 'a00b')

        # Other code, no remote entry
        output = writer.expand('#R45066@Other', ASMDIR)
        self._assert_link_equals(output, '../other/45066.html', 'b00a')

        # Other code with remote entry
        output = writer.expand('#R49152@Other', ASMDIR)
        self._assert_link_equals(output, '../other/49152.html', 'c000')

        # Other code with remote entry point
        output = writer.expand('#R49155@Other', ASMDIR)
        self._assert_link_equals(output, '../other/49152.html#49155', 'c003')

    def test_macro_r_hex_upper(self):
        ref = '\n'.join((
            '[OtherCode:other]',
            'Source=other.skool'
        ))
        skool = '\n'.join((
            'c$a00a LD A,B',
            ' 40971 RET',
            '',
            'r$c000 other',
            ' $c003'
        ))
        writer = self._get_writer(ref=ref, skool=skool, case=CASE_UPPER, base=BASE_16)

        # Routine
        output = writer.expand('#R40970', ASMDIR)
        self._assert_link_equals(output, '40970.html', 'A00A')

        # Routine entry point
        output = writer.expand('#R40971', ASMDIR)
        self._assert_link_equals(output, '40970.html#40971', 'A00B')

        # Other code, no remote entry
        output = writer.expand('#R45066@other', ASMDIR)
        self._assert_link_equals(output, '../other/45066.html', 'B00A')

        # Other code with remote entry
        output = writer.expand('#R49152@other', ASMDIR)
        self._assert_link_equals(output, '../other/49152.html', 'C000')

        # Other code with remote entry point
        output = writer.expand('#R49155@other', ASMDIR)
        self._assert_link_equals(output, '../other/49152.html#49155', 'C003')

    def test_macro_r_with_custom_asm_filenames(self):
        ref = '[Paths]\nCodeFiles={address:04X}.html'
        skool = '\n'.join((
            '; Data at 32768',
            'b32768 DEFS 12345',
            '',
            '; Routine at 45113',
            'c45113 RET'
        ))
        writer = self._get_writer(ref=ref, skool=skool)

        for address in (32768, 45113):
            output = writer.expand('#R{}'.format(address), ASMDIR)
            exp_asm_fname = '{:04X}.html'.format(address)
            self._assert_link_equals(output, exp_asm_fname, str(address))

    def test_macro_r_with_invalid_filename_template(self):
        ref = '[Paths]\nCodeFiles={Address}.html'
        skool = 'b32768 DEFS 12345'
        writer = self._get_writer(ref=ref, skool=skool)
        error_msg = "Cannot format filename ({Address}.html) with address=32768"
        self._assert_error(writer, '#R32768', error_msg, error=SkoolKitError)

    def test_macro_r_with_custom_asm_anchor(self):
        ref = '[Game]\nAddressAnchor={address:04x}'
        skool = '\n'.join((
            '; Routine at 40000',
            'c40000 LD A,B',
            ' 40001 RET'
        ))
        writer = self._get_writer(ref=ref, skool=skool)

        output = writer.expand('#R40001', ASMDIR)
        self._assert_link_equals(output, '40000.html#9c41', '40001')

    def test_macro_r_with_invalid_asm_anchor(self):
        ref = '[Game]\nAddressAnchor={address:j}'
        skool = 'c40000 LD A,B\n 40001 RET'
        writer = self._get_writer(ref=ref, skool=skool)
        error_msg = "Cannot format anchor ({address:j}) with address=40001"
        self._assert_error(writer, '#R40001', error_msg, error=SkoolKitError)

    def test_macro_r_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('R')

        # No address (1)
        self._assert_error(writer, '#R', "No address", prefix)

        # No address (2)
        self._assert_error(writer, '#R@main', "No address", prefix)

        # No address (3)
        self._assert_error(writer, '#R#bar', "No address", prefix)

        # No address (4)
        self._assert_error(writer, '#R(baz)', "No address", prefix)

        # Invalid address
        self._assert_error(writer, '#R20$5', "Invalid address: 20$5", prefix)

        # No closing bracket
        self._assert_error(writer, '#R32768(qux', "No closing bracket: (qux", prefix)

        # Non-existent other code reference
        self._assert_error(writer, '#R24576@nonexistent', "Cannot find code path for 'nonexistent' disassembly", error=SkoolKitError)

    def test_macro_refs(self):
        # One referrer
        skool = '\n'.join((
            '; Referrer',
            'c40000 JP 40003',
            '',
            '; Routine',
            'c40003 LD A,B'
        ))
        writer = self._get_writer(skool=skool)
        output = writer.expand('#REFS40003', ASMDIR)
        self.assertEqual(output, 'routine at <a href="40000.html">40000</a>')

        skool = '\n'.join((
            '; Not used directly by any other routines',
            'c24576 LD HL,$6003',
            '',
            '; Used by the routines at 24581, 24584 and 24590',
            'c24579 LD A,H',
            ' 24580 RET',
            '',
            '; Calls 24579',
            'c24581 CALL 24579',
            '',
            '; Also calls 24579',
            'c24584 CALL 24579',
            ' 24587 JP 24580',
            '',
            '; Calls 24579 too',
            'c24590 CALL 24580',
        ))
        writer = self._get_writer(skool=skool)

        # Some referrers
        for address in ('24579', '$6003'):
            output = writer.expand('#REFS{}'.format(address), ASMDIR)
            self.assertEqual(output, 'routines at <a href="24581.html">24581</a>, <a href="24584.html">24584</a> and <a href="24590.html">24590</a>')

        # No referrers
        output = writer.expand('#REFS24576', ASMDIR)
        self.assertEqual(output, 'Not used directly by any other routines')

    def test_macro_refs_invalid(self):
        writer = self._get_writer(skool='')
        prefix = ERROR_PREFIX.format('REFS')

        # No address
        self._assert_error(writer, '#REFS', "No address", prefix)

        # Invalid address
        self._assert_error(writer, '#REFS3$56', "Invalid address: 3$56", prefix)

        # No closing bracket
        self._assert_error(writer, '#REFS34567(foo', "No closing bracket: (foo", prefix)

        # Non-existent entry
        self._assert_error(writer, '#REFS40000', "No entry at 40000", prefix)

    def test_macro_reg(self):
        # Lower case
        writer = self._get_writer()
        writer.case = CASE_LOWER
        output = writer.expand('#REGhl', ASMDIR)
        self.assertEqual(output, '<span class="register">hl</span>')
        writer.case = None

        # Upper case, all registers
        for reg in ("a", "b", "c", "d", "e", "h", "l", "i", "r", "ixl", "ixh", "iyl", "iyh", "b'", "c'", "d'", "e'", "h'", "l'", "bc", "de", "hl", "sp", "ix", "iy", "bc'", "de'", "hl'"):
            output = writer.expand('#REG{0}'.format(reg), ASMDIR)
            self.assertEqual(output, '<span class="register">{0}</span>'.format(reg.upper()))

    def test_macro_reg_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('REG')

        # Missing register argument (1)
        self._assert_error(writer, '#REG', 'Missing register argument', prefix)

        # Missing register argument (2)
        self._assert_error(writer, '#REGq', 'Missing register argument', prefix)

        # Bad register argument
        self._assert_error(writer, '#REGabcd', 'Bad register: "abcd"', prefix)

    def test_macro_scr(self):
        snapshot = [0] * 65536
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)

        output = writer.expand('#SCR', ASMDIR)
        self._assert_img_equals(output, 'scr', '../images/scr/scr.png')

        scr_fname = 'scr2'
        output = writer.expand('#SCR2,0,0,10,10({0})'.format(scr_fname), ASMDIR)
        self._assert_img_equals(output, scr_fname, '../images/scr/{0}.png'.format(scr_fname))

        scr_fname = 'scr3'
        data = [128, 64, 32, 16, 8, 4, 2, 1]
        attr = 48
        snapshot[16384:18432:256] = data
        snapshot[22528] = attr
        scale = 2
        x, y, w, h = 1, 2, 5, 6
        macro = '#SCR{0},0,0,1,1{{{1},{2},{3},{4}}}({5})'.format(scale, x, y, w, h, scr_fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, scr_fname, '../images/scr/{0}.png'.format(scr_fname))
        udg_array = [[Udg(attr, data)]]
        self._check_image(writer.image_writer, udg_array, scale, False, x, y, w, h)

        scr_fname = 'scr4'
        scale = 3
        x, y, w, h = 0, 0, 1, 1
        df = 0
        af = 32768
        data = snapshot[df:df + 2048:256] = [170] * 8
        attr = snapshot[af] = 56
        values = {'scale': scale, 'x': x, 'y': y, 'w': w, 'h': h, 'df': df, 'af': af, 'fname': scr_fname}
        macro = '#SCRx={x},h={h},af={af},scale={scale},y={y},df={df},w={w}({fname})'.format(**values)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, scr_fname, '../images/scr/{}.png'.format(scr_fname))
        udg_array = [[Udg(attr, data)]]
        self._check_image(writer.image_writer, udg_array, scale)

    def test_macro_scr_with_custom_screenshot_path(self):
        scr_path = 'graphics/screenshots'
        ref = '[Paths]\nScreenshotImagePath={}'.format(scr_path)
        writer = self._get_writer(ref=ref, snapshot=[0] * 23296, mock_file_info=True)
        exp_img_path = '{}/scr.png'.format(scr_path)

        output = writer.expand('#SCR', ASMDIR)
        self._assert_img_equals(output, 'scr', '../{}'.format(exp_img_path))
        self.assertEqual(writer.file_info.fname, exp_img_path)

    def test_macro_scr_frames(self):
        snapshot = [n & 255 for n in range(2048)] + [1, 2, 3, 4]
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)
        file_info = writer.file_info
        params = 'w=1,h=1,df=0,af=2048'

        output = writer.expand('#SCRx=0,y=0,{}(*scr1)'.format(params), ASMDIR)
        self.assertEqual(output, '')
        self.assertIsNone(file_info.fname)

        output = writer.expand('#SCRx=1,y=0,{}(scr2*)'.format(params), ASMDIR)
        exp_image_path = '{}/scr2.png'.format(SCRDIR)
        self._assert_img_equals(output, 'scr2', '../{}'.format(exp_image_path))
        self.assertEqual(file_info.fname, exp_image_path)

        output = writer.expand('#SCRx=2,y=0,{}(scr3*scr3_frame)'.format(params), ASMDIR)
        exp_image_path = '{}/scr3.png'.format(SCRDIR)
        self._assert_img_equals(output, 'scr3', '../{}'.format(exp_image_path))
        self.assertEqual(file_info.fname, exp_image_path)

        output = writer.expand('#SCRscale=2,x=3,y=0,{}{{2,3,8,8}}(*)'.format(params), ASMDIR)
        exp_image_path = '{}/scr.png'.format(SCRDIR)
        self._assert_img_equals(output, 'scr', '../{}'.format(exp_image_path))
        self.assertEqual(file_info.fname, exp_image_path)

        writer.expand('#UDGARRAY*scr1;scr2;scr3_frame;scr(scr.gif)', ASMDIR)
        exp_frames = [
            Frame([[Udg(1, snapshot[0:2048:256])]], scale=1),
            Frame([[Udg(2, snapshot[1:2048:256])]], scale=1),
            Frame([[Udg(3, snapshot[2:2048:256])]], scale=1),
            Frame([[Udg(4, snapshot[3:2048:256])]], scale=2, x=2, y=3, width=8, height=8)
        ]
        self._check_animated_image(writer.image_writer, exp_frames)

    def test_macro_scr_alt_text(self):
        snapshot = [0] * 23296
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)

        alt = 'An awesome screenshot'
        output = writer.expand('#SCR(|{})'.format(alt), ASMDIR)
        self._assert_img_equals(output, alt, '../images/scr/scr.png')

        fname = 'screenshot'
        alt = 'Another awesome screenshot'
        output = writer.expand('#SCR({}|{})'.format(fname, alt), ASMDIR)
        self._assert_img_equals(output, alt, '../images/scr/{}.png'.format(fname))

    def test_macro_scr_invalid(self):
        writer = self._get_writer(snapshot=[0] * 8)
        prefix = ERROR_PREFIX.format('SCR')

        # Too many parameters
        self._assert_error(writer, '#SCR0,1,2,3,4,5,6,7,8', "Too many parameters (expected 7): '0,1,2,3,4,5,6,7,8'", prefix)

        # No closing bracket
        self._assert_error(writer, '#SCR(foo', 'No closing bracket: (foo', prefix)

        # Invalid parameter
        self._assert_error(writer, '#SCR0,1,2$,3', "Cannot parse integer '2$' in parameter string: '0,1,2$,3'", prefix)

    def test_macro_space(self):
        writer = self._get_writer()

        output = writer.expand('#SPACE', ASMDIR)
        self.assertEqual(output, '&#160;')

        num = 10
        output = writer.expand('#SPACE{0}'.format(num), ASMDIR)
        self.assertEqual(output, '&#160;' * num)

        num = 7
        output = writer.expand('1#SPACE({0})1'.format(num), ASMDIR)
        self.assertEqual(output, '1{0}1'.format('&#160;' * num))

    def test_macro_space_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('SPACE')

        # Invalid integer
        self._assert_error(writer, '#SPACE5$3', "Cannot parse integer '5$3' in parameter string: '5$3'", prefix)

        # Invalid integer in brackets
        self._assert_error(writer, '#SPACE(5$3)', "Invalid integer: '5$3'", prefix)

        # No closing bracket
        self._assert_error(writer, '#SPACE(2', "No closing bracket: (2", prefix)

    def test_macro_table(self):
        src1 = '\n'.join((
            '(data)',
            '{ =h Col1 | =h Col2 | =h,c2 Cols3+4 }',
            '{ =r2 X   | Y       | Za  | Zb }',
            '{           Y2      | Za2 | =t }'
        ))
        html1 = """
            <table class="data">
            <tr>
            <th colspan="1" rowspan="1">Col1</th>
            <th colspan="1" rowspan="1">Col2</th>
            <th colspan="2" rowspan="1">Cols3+4</th>
            </tr>
            <tr>
            <td class="" colspan="1" rowspan="2">X</td>
            <td class="" colspan="1" rowspan="1">Y</td>
            <td class="" colspan="1" rowspan="1">Za</td>
            <td class="" colspan="1" rowspan="1">Zb</td>
            </tr>
            <tr>
            <td class="" colspan="1" rowspan="1">Y2</td>
            <td class="" colspan="1" rowspan="1">Za2</td>
            <td class="transparent" colspan="1" rowspan="1"></td>
            </tr>
            </table>
        """

        src2 = '\n'.join((
            '(,centre)',
            '{ =h Header }',
            '{ Cell }'
        ))
        html2 = """
            <table class="">
            <tr>
            <th colspan="1" rowspan="1">Header</th>
            </tr>
            <tr>
            <td class="centre" colspan="1" rowspan="1">Cell</td>
            </tr>
            </table>
        """

        writer = self._get_writer()
        for src, html in ((src1, html1), (src2, html2)):
            output = writer.expand('#TABLE{}\nTABLE#'.format(src), ASMDIR)
            self._assert_html_equal(output, html)

        # Empty table
        output = writer.expand('#TABLE TABLE#', ASMDIR)
        self.assertEqual(output, '<table class="">\n\n</table>')

    def test_macro_table_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('TABLE')

        # No end marker
        self._assert_error(writer, '#TABLE { A1 }', 'Missing table end marker: #TABLE { A1 }...')

    def test_macro_udg(self):
        snapshot = [0] * 65536
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)

        udg_fname = 'udg32768_56x4'
        output = writer.expand('#UDG32768', ASMDIR)
        self._assert_img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))

        udg_fname = 'udg40000_2x3'
        output = writer.expand('#UDG40000,2,3', ASMDIR)
        self._assert_img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))

        udg_fname = 'test_udg'
        output = writer.expand('#UDG32768,2,6,1,0:49152,2({0})'.format(udg_fname), ASMDIR)
        self._assert_img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))

        udg_fname = 'test_udg2'
        udg_addr = 32768
        attr = 2
        scale = 1
        step = 1
        inc = 0
        mask_addr = 32776
        x, y, w, h = 2, 1, 3, 4
        udg_data = [136] * 8
        udg_mask = [255] * 8
        snapshot[udg_addr:udg_addr + 8 * step:step] = udg_data
        snapshot[mask_addr:mask_addr + 8 * step:step] = udg_mask
        macro = '#UDG{0},{1},{2},{3},{4}:{5},{6}{{{7},{8},{9},{10}}}({11})'.format(udg_addr, attr, scale, step, inc, mask_addr, step, x, y, w, h, udg_fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))
        udg_array = [[Udg(attr, udg_data, udg_mask)]]
        self._check_image(writer.image_writer, udg_array, scale, 1, x, y, w, h)

        fname = 'test_udg3'
        addr = 49152
        attr = 2
        scale = 1
        step = 2
        inc = 0
        mask = 2
        mask_addr = 49153
        mask_step = 2
        x, y, width, height = 1, 2, 4, 3
        udg_data = [240] * 8
        udg_mask = [248] * 8
        snapshot[addr:addr + 8 * step:step] = udg_data
        snapshot[mask_addr:mask_addr + 8 * mask_step:mask_step] = udg_mask
        params = 'attr={attr},step={step},inc={inc},addr={addr},mask={mask},scale={scale}'
        mask_spec = ':step={step},addr={mask_addr}'
        crop = '{{x={x},y={y},width={width},height={height}}}'
        macro = ('#UDG' + params + mask_spec + crop + '({fname})').format(**locals())
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, '../{}/{}.png'.format(UDGDIR, fname))
        udg_array = [[Udg(attr, udg_data, udg_mask)]]
        self._check_image(writer.image_writer, udg_array, scale, mask, x, y, width, height)

    def test_macro_udg_with_custom_udg_image_path(self):
        font_path = 'graphics/udgs'
        ref = '[Paths]\nUDGImagePath={}'.format(font_path)
        writer = self._get_writer(ref=ref, snapshot=[0] * 8, mock_file_info=True)
        img_fname = 'udg0'
        exp_img_path = '{}/{}.png'.format(font_path, img_fname)

        output = writer.expand('#UDG0({})'.format(img_fname), ASMDIR)
        self._assert_img_equals(output, img_fname, '../{}'.format(exp_img_path))
        self.assertEqual(writer.file_info.fname, exp_img_path)

    def test_macro_udg_with_mask(self):
        udg_data = [240] * 8
        udg_mask = [248] * 8
        udg_array_no_mask = [[Udg(56, udg_data)]]
        udg_array = [[Udg(56, udg_data, udg_mask)]]
        scale = 4
        writer = self._get_writer(snapshot=udg_data + udg_mask, mock_file_info=True)

        # No mask parameter, no mask defined
        writer.expand('#UDG0', ASMDIR)
        self._check_image(writer.image_writer, udg_array_no_mask, scale, mask=0)

        # mask=1, no mask defined
        writer.expand('#UDG0,mask=1', ASMDIR)
        self._check_image(writer.image_writer, udg_array_no_mask, scale, mask=0)

        # mask=0, mask defined
        writer.expand('#UDG0,mask=0:8', ASMDIR)
        self._check_image(writer.image_writer, udg_array_no_mask, scale, mask=0)

        # No mask parameter, mask defined
        writer.expand('#UDG0:8', ASMDIR)
        self._check_image(writer.image_writer, udg_array, scale, mask=1)

        # mask=2, mask defined
        writer.expand('#UDG0,mask=2:8', ASMDIR)
        self._check_image(writer.image_writer, udg_array, scale, mask=2)

    def test_macro_udg_frames(self):
        udg1 = [170] * 8
        udg2 = [85] * 8
        udg3 = [1] * 8
        udg4 = [128] * 8
        snapshot = udg1 + udg2 + udg3 + udg4
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)
        file_info = writer.file_info

        output = writer.expand('#UDG0(*udg1)', ASMDIR)
        self.assertEqual(output, '')
        self.assertIsNone(file_info.fname)

        output = writer.expand('#UDG8(udg2*)', ASMDIR)
        exp_image_path = '{}/udg2.png'.format(UDGDIR)
        self._assert_img_equals(output, 'udg2', '../{}'.format(exp_image_path))
        self.assertEqual(file_info.fname, exp_image_path)

        output = writer.expand('#UDG16(udg3*udg3_frame)', ASMDIR)
        exp_image_path = '{}/udg3.png'.format(UDGDIR)
        self._assert_img_equals(output, 'udg3', '../{}'.format(exp_image_path))
        self.assertEqual(file_info.fname, exp_image_path)

        output = writer.expand('#UDG24,4,6:0{5,6,32,32}(*)', ASMDIR)
        exp_image_path = '{}/udg24_4x6.png'.format(UDGDIR)
        self._assert_img_equals(output, 'udg24_4x6', '../{}'.format(exp_image_path))
        self.assertEqual(file_info.fname, exp_image_path)

        writer.expand('#UDGARRAY*udg1;udg2;udg3_frame;udg24_4x6(udgs.gif)', ASMDIR)
        exp_frames = [
            Frame([[Udg(56, udg1)]], scale=4),
            Frame([[Udg(56, udg2)]], scale=4),
            Frame([[Udg(56, udg3)]], scale=4),
            Frame([[Udg(4, udg4, udg1)]], scale=6, mask=1, x=5, y=6, width=32, height=32)
        ]
        self._check_animated_image(writer.image_writer, exp_frames)

    def test_macro_udg_alt_text(self):
        writer = self._get_writer(snapshot=[0] * 8, mock_file_info=True)

        fname = 'foo'
        alt = 'bar'
        output = writer.expand('#UDG0({}|{})'.format(fname, alt), ASMDIR)
        self._assert_img_equals(output, alt, '../{}/{}.png'.format(UDGDIR, fname))

        alt = 'An awesome UDG'
        output = writer.expand('#UDG0(|{})'.format(alt), ASMDIR)
        self._assert_img_equals(output, alt, '../{}/udg0_56x4.png'.format(UDGDIR))

    def test_macro_udg_invalid(self):
        writer = self._get_writer(snapshot=[0] * 8)
        prefix = ERROR_PREFIX.format('UDG')

        # No parameters
        self._assert_error(writer, '#UDG', 'No parameters (expected 1)', prefix)

        # Too many parameters
        self._assert_error(writer, '#UDG0,1,2,3,4,5,6,7,8,9', "Too many parameters (expected 8): '0,1,2,3,4,5,6,7,8,9'", prefix)

        # Invalid parameter
        self._assert_error(writer, '#UDG0$,1,2', "Cannot parse integer '0$' in parameter string: '0$,1,2'", prefix)

        # No closing bracket
        self._assert_error(writer, '#UDG0(foo', 'No closing bracket: (foo', prefix)

    def test_macro_udgarray(self):
        snapshot = [0] * 65536
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)

        udg_fname = 'test_udg_array'
        output = writer.expand('#UDGARRAY8;32768-32784-1-8({0})'.format(udg_fname), ASMDIR)
        self._assert_img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))

        udg_fname = 'test_udg_array2'
        output = writer.expand('#UDGARRAY8,56,2,256,0;32768;32769;32770;32771;32772x12({0})'.format(udg_fname), ASMDIR)
        self._assert_img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))

        udg_fname = 'test_udg_array3'
        udg_addr = 32768
        mask_addr = 32769
        width = 2
        attr = 5
        scale = 1
        step = 256
        inc = 0
        x, y, w, h = 4, 6, 8, 5
        udg_data = [195] * 8
        udg_mask = [255] * 8
        snapshot[udg_addr:udg_addr + 8 * step:step] = udg_data
        snapshot[mask_addr:mask_addr + 8 * step:step] = udg_mask
        macro = '#UDGARRAY{0},{1},{2},{3},{4};{5}x4:{6}x4{{{7},{8},{9},{10}}}({11})'.format(width, attr, scale, step, inc, udg_addr, mask_addr, x, y, w, h, udg_fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))
        udg_array = [[Udg(attr, udg_data, udg_mask)] * width] * 2
        self._check_image(writer.image_writer, udg_array, scale, True, x, y, w, h)

        # Flip
        udg_fname = 'test_udg_array4'
        udg = Udg(56, [128, 64, 32, 16, 8, 4, 2, 1])
        udg_addr = 40000
        snapshot[udg_addr:udg_addr + 8] = udg.data
        output = writer.expand('#UDGARRAY1,,,,,1;{0}({1})'.format(udg_addr, udg_fname), ASMDIR)
        self._assert_img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))
        udg.flip(1)
        self._check_image(writer.image_writer, [[udg]], 2, False, 0, 0, 16, 16)

        # Rotate
        udg_fname = 'test_udg_array5'
        udg = Udg(56, [128, 64, 32, 16, 8, 4, 2, 1])
        udg_addr = 50000
        snapshot[udg_addr:udg_addr + 8] = udg.data
        output = writer.expand('#UDGARRAY1,,,,,,2;{0}({1})'.format(udg_addr, udg_fname), ASMDIR)
        self._assert_img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))
        udg.rotate(2)
        self._check_image(writer.image_writer, [[udg]], 2, False, 0, 0, 16, 16)

        # Keyword arguments
        fname = 'test_udg_array6'
        udg_addr = 32768
        mask_addr = 32769
        width = 2
        attr = 5
        scale = 1
        step = 256
        inc = 0
        mask = 1
        x, y, w, h = 4, 6, 8, 5
        udg_data = [195] * 8
        udg_mask = [255] * 8
        snapshot[udg_addr:udg_addr + 8 * step:step] = udg_data
        snapshot[mask_addr:mask_addr + 8 * step:step] = udg_mask
        params = 'attr={attr},step={step},inc={inc},mask={mask},scale={scale}'
        udg_spec = ';addr={udg_addr}x4,step={step}'
        mask_spec = ':step={step},addr={mask_addr}x4'
        crop = '{{x={x},y={y},width={w},height={h}}}'
        macro = ('#UDGARRAY{width},' + params + udg_spec + mask_spec + crop + '({fname})').format(**locals())
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, '../{}/{}.png'.format(UDGDIR, fname))
        udg_array = [[Udg(attr, udg_data, udg_mask)] * width] * 2
        self._check_image(writer.image_writer, udg_array, scale, mask, x, y, w, h)

    def test_macro_udgarray_with_custom_udg_image_path(self):
        font_path = 'udg_images'
        ref = '[Paths]\nUDGImagePath={}'.format(font_path)
        writer = self._get_writer(ref=ref, snapshot=[0] * 8, mock_file_info=True)
        img_fname = 'udgarray0'
        exp_img_path = '{}/{}.png'.format(font_path, img_fname)

        output = writer.expand('#UDGARRAY1;0({})'.format(img_fname), ASMDIR)
        self._assert_img_equals(output, img_fname, '../{}'.format(exp_img_path))
        self.assertEqual(writer.file_info.fname, exp_img_path)

    def test_macro_udgarray_with_mask(self):
        udg_data = [15] * 8
        udg_mask = [31] * 8
        udg_array_no_mask = [[Udg(56, udg_data)]]
        udg_array = [[Udg(56, udg_data, udg_mask)]]
        scale = 2
        writer = self._get_writer(snapshot=udg_data + udg_mask, mock_file_info=True)

        # No mask parameter, no mask defined
        writer.expand('#UDGARRAY1;0(udgarray)', ASMDIR)
        self._check_image(writer.image_writer, udg_array_no_mask, scale, mask=0)

        # mask=1, no mask defined
        writer.expand('#UDGARRAY1,mask=1;0(udgarray)', ASMDIR)
        self._check_image(writer.image_writer, udg_array_no_mask, scale, mask=0)

        # mask=0, mask defined
        writer.expand('#UDGARRAY1,mask=0;0:8(udgarray)', ASMDIR)
        self._check_image(writer.image_writer, udg_array_no_mask, scale, mask=0)

        # No mask parameter, mask defined
        writer.expand('#UDGARRAY1;0:8(udgarray)', ASMDIR)
        self._check_image(writer.image_writer, udg_array, scale, mask=1)

        # mask=2, mask defined
        writer.expand('#UDGARRAY1,mask=2;0:8(udgarray)', ASMDIR)
        self._check_image(writer.image_writer, udg_array, scale, mask=2)

    def test_macro_udgarray_invalid(self):
        writer = self._get_writer(snapshot=[0] * 8)
        prefix = ERROR_PREFIX.format('UDGARRAY')

        # No parameters
        self._assert_error(writer, '#UDGARRAY', 'No parameters (expected 1)', prefix)

        # Invalid parameter
        self._assert_error(writer, '#UDGARRAY1,5$,4;0(bar)', "Cannot parse integer '5$' in parameter string: '1,5$,4'", prefix)

        # Invalid UDG address range spec (1)
        self._assert_error(writer, '#UDGARRAY1;0-1$(bar)', 'Invalid address range specification: 0-1$', prefix)

        # Invalid UDG address range spec (2)
        self._assert_error(writer, '#UDGARRAY1;0-1x2x2(bar)', 'Invalid address range specification: 0-1x2x2', prefix)

        # Invalid UDG address range spec (3)
        self._assert_error(writer, '#UDGARRAY1;0-1-2-3-4x5(bar)', 'Invalid address range specification: 0-1-2-3-4x5', prefix)

        # Invalid UDG spec
        self._assert_error(writer, '#UDGARRAY1;0,5-(bar)', "Cannot parse integer '5-' in parameter string: '0,5-'", prefix)

        # Invalid mask address range spec (1)
        self._assert_error(writer, '#UDGARRAY1;0-2:0-2$(bar)', 'Invalid address range specification: 0-2$', prefix)

        # Invalid mask address range spec (2)
        self._assert_error(writer, '#UDGARRAY1;0-1x2:2-3x2x2(bar)', 'Invalid address range specification: 2-3x2x2', prefix)

        # Invalid mask address range spec (3)
        self._assert_error(writer, '#UDGARRAY1;0-1-2-3x9:4-5-6-7-8x9(bar)', 'Invalid address range specification: 4-5-6-7-8x9', prefix)

        # Invalid UDG mask spec
        self._assert_error(writer, '#UDGARRAY1;0,5:8,1x(bar)', "Cannot parse integer '1x' in parameter string: '8,1x'", prefix)

        # Missing filename (1)
        self._assert_error(writer, '#UDGARRAY1;0', 'Missing filename: #UDGARRAY1;0', prefix)

        # Missing filename (2)
        self._assert_error(writer, '#UDGARRAY1;0{0,0}1(foo)', 'Missing filename: #UDGARRAY1;0{0,0}', prefix)

        # No closing bracket
        self._assert_error(writer, '#UDGARRAY1;0(foo', 'No closing bracket: (foo', prefix)

    def test_macro_udgarray_frames(self):
        snapshot = [0] * 65536
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)

        # Frames
        udg1_addr = 40000
        udg1 = Udg(23, [101] * 8)
        udg2_addr = 40008
        udg2 = Udg(47, [35] * 8)
        udg3_addr = 40016
        udg3 = Udg(56, [19] * 8)
        snapshot[udg1_addr:udg1_addr + 8] = udg1.data
        snapshot[udg2_addr:udg2_addr + 8] = udg2.data
        snapshot[udg3_addr:udg3_addr + 8] = udg3.data
        macro1 = '#UDGARRAY1;{},{}(*foo)'.format(udg1_addr, udg1.attr)
        macro2 = '#UDGARRAY1;{},{}(bar*)'.format(udg2_addr, udg2.attr)
        macro3 = '#UDGARRAY1;{},{}(baz*qux)'.format(udg3_addr, udg3.attr)
        output = writer.expand(macro1, ASMDIR)
        self.assertEqual(output, '')
        output = writer.expand(macro2, ASMDIR)
        self._assert_img_equals(output, 'bar', '../{}/bar.png'.format(UDGDIR))
        output = writer.expand(macro3, ASMDIR)
        self._assert_img_equals(output, 'baz', '../{}/baz.png'.format(UDGDIR))
        delay1 = 93
        delay3 = 47
        fname = 'test_udg_array_frames'
        macro4 = '#UDGARRAY*foo,{};bar;qux,delay={}({})'.format(delay1, delay3, fname)
        output = writer.expand(macro4, ASMDIR)
        self._assert_img_equals(output, fname, '../{}/{}.png'.format(UDGDIR, fname))
        frame1 = Frame([[udg1]], 2, delay=delay1)
        frame2 = Frame([[udg2]], 2, delay=delay1)
        frame3 = Frame([[udg3]], 2, delay=delay3)
        frames = [frame1, frame2, frame3]
        self._check_animated_image(writer.image_writer, frames)

    def test_macro_udgarray_frames_invalid(self):
        writer = self._get_writer(snapshot=[0] * 8)
        prefix = ERROR_PREFIX.format('UDGARRAY')

        self._assert_error(writer, '#UDGARRAY1;0(*)', 'Missing filename or frame ID: #UDGARRAY1;0(*)', prefix)
        self._assert_error(writer, '#UDGARRAY*,3(foo)', 'Missing frame ID: #UDGARRAY*,3(foo)', prefix)
        self._assert_error(writer, '#UDGARRAY*foo', 'Missing filename: #UDGARRAY*foo', prefix)
        self._assert_error(writer, '#UDGARRAY*foo()', 'Missing filename: #UDGARRAY*foo()', prefix)
        self._assert_error(writer, '#UDGARRAY*foo(bar', 'No closing bracket: (bar', prefix)
        self._assert_error(writer, '#UDGARRAY*foo(bar)', 'No such frame: "foo"', prefix)
        self._assert_error(writer, '#UDGARRAY*foo,qux(bar)', "Cannot parse integer 'qux' in parameter string: 'qux'", prefix)

    def test_macro_udgarray_alt_text(self):
        writer = self._get_writer(snapshot=[0] * 8, mock_file_info=True)

        fname = 'foo'
        alt = 'bar'
        output = writer.expand('#UDGARRAY1;0({}|{})'.format(fname, alt), ASMDIR)
        self._assert_img_equals(output, alt, '../{}/{}.png'.format(UDGDIR, fname))

        fname = 'baz'
        frame = 'qux'
        alt = 'xyzzy'
        output = writer.expand('#UDGARRAY1;0({}*{}|{})'.format(fname, frame, alt), ASMDIR)
        self._assert_img_equals(output, alt, '../{}/{}.png'.format(UDGDIR, fname))

        fname = 'flip'
        alt = 'flop*flup'
        output = writer.expand('#UDGARRAY1;0({}|{})'.format(fname, alt), ASMDIR)
        self._assert_img_equals(output, alt, '../{}/{}.png'.format(UDGDIR, fname))

        fname = 'animated'
        alt = 'Animated'
        writer.expand('#UDGARRAY1;0(*frame1)', ASMDIR)
        writer.expand('#UDGARRAY1;0(*frame2)', ASMDIR)
        output = writer.expand('#UDGARRAY*frame1;frame2({}|{})'.format(fname, alt), ASMDIR)
        self._assert_img_equals(output, alt, '../{}/{}.png'.format(UDGDIR, fname))

    def test_macro_udgtable(self):
        src = '\n'.join((
            '(data)',
            '{ =h Col1 | =h Col2 | =h,c2 Cols3+4 }',
            '{ =r2 X   | Y       | Za  | Zb }',
            '{           Y2      | Za2 | =t }'
        ))
        html = """
            <table class="data">
            <tr>
            <th colspan="1" rowspan="1">Col1</th>
            <th colspan="1" rowspan="1">Col2</th>
            <th colspan="2" rowspan="1">Cols3+4</th>
            </tr>
            <tr>
            <td class="" colspan="1" rowspan="2">X</td>
            <td class="" colspan="1" rowspan="1">Y</td>
            <td class="" colspan="1" rowspan="1">Za</td>
            <td class="" colspan="1" rowspan="1">Zb</td>
            </tr>
            <tr>
            <td class="" colspan="1" rowspan="1">Y2</td>
            <td class="" colspan="1" rowspan="1">Za2</td>
            <td class="transparent" colspan="1" rowspan="1"></td>
            </tr>
            </table>
        """
        writer = self._get_writer()
        output = writer.expand('#UDGTABLE{}\nUDGTABLE#'.format(src), ASMDIR)
        self._assert_html_equal(output, html)

        # Empty table
        output = writer.expand('#UDGTABLE UDGTABLE#', ASMDIR)
        self.assertEqual(output, '<table class="">\n\n</table>')

    def test_macro_udgtable_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('UDGTABLE')

        # No end marker
        self._assert_error(writer, '#UDGTABLE { A1 }', 'Missing table end marker: #UDGTABLE { A1 }...')

    def test_unsupported_macro(self):
        writer = self._get_writer()
        writer.macros['#BUG'] = self._unsupported_macro
        self._assert_error(writer, '#BUG#bug1', 'Found unsupported macro: #BUG')

    def test_unknown_macro(self):
        writer = self._get_writer()
        for macro, params in (('#FOO', 'xyz'), ('#BAR', '1,2(baz)'), ('#UDGS', '#r1'), ('#LINKS', '')):
            self._assert_error(writer, macro + params, 'Found unknown macro: {}'.format(macro))

class HtmlOutputTest(HtmlWriterTestCase):
    def setUp(self):
        HtmlWriterTestCase.setUp(self)
        self.files = {}

    def _read_file(self, fname, lines=False):
        if lines:
            return self.files[fname].split('\n')
        return self.files[fname]

    def _assert_files_equal(self, d_fname, subs, index=False, trim=True):
        d_html_lines = self._read_file(d_fname, True)
        body_lines = []
        for line in subs['content'].split('\n'):
            s_line = line.lstrip()
            if s_line:
                body_lines.append(s_line)
        js = subs.get('js')
        subs.setdefault('name', basename(self.skoolfile)[:-6])
        subs.setdefault('path', '../')
        subs.setdefault('script', '<script type="text/javascript" src="{}"></script>'.format(js) if js else '')
        subs.setdefault('title', subs['header'])
        subs.setdefault('logo', subs['name'])
        footer = subs.get('footer', BARE_FOOTER)
        prev_up_next_lines = []
        if 'up' in subs:
            subs['prev_link'] = '<span class="prev-0">Prev: <a href=""></a></span>'
            subs['up_link'] = 'Up: <a href="{path}maps/all.html#{up}">Map</a>'.format(**subs)
            subs['next_link'] = '<span class="next-0">Next: <a href=""></a></span>'
            if 'prev' in subs:
                subs['prev_link'] = '<span class="prev-1">Prev: <a href="{0}.html">{0:05d}</a></span>'.format(subs['prev'])
            if 'next' in subs:
                subs['next_link'] = '<span class="next-1">Next: <a href="{0}.html">{0:05d}</a></span>'.format(subs['next'])
            prev_up_next = PREV_UP_NEXT.format(**subs)
            prev_up_next_lines = prev_up_next.split('\n')
        header_template = INDEX_HEADER if index else HEADER
        t_html_lines = header_template.format(**subs).split('\n')
        t_html_lines.extend(prev_up_next_lines)
        t_html_lines.extend(body_lines)
        t_html_lines.extend(prev_up_next_lines)
        t_html_lines.extend(footer.split('\n'))
        if trim:
            d_html_lines = [line for line in d_html_lines if line]
            t_html_lines = [line for line in t_html_lines if line]
        self.assertEqual(t_html_lines, d_html_lines)

    def _assert_title_equals(self, fname, title, header):
        html = self._read_file(fname)
        name = self.skoolfile[:-6]
        self.assertIn('<title>{}: {}</title>'.format(name, title), html)
        self.assertIn('<td class="page-header">{}</td>'.format(header), html)

    def test_parameter_LinkInternalOperands_0(self):
        ref = '[Game]\nLinkInternalOperands=0'
        skool = '\n'.join((
            '; Routine at 30000',
            'c30000 CALL 30003',
            ' 30003 JP 30006',
            ' 30006 DJNZ 30006',
            ' 30009 JR 30000'
        ))
        writer = self._get_writer(ref=ref, skool=skool)
        self.assertFalse(writer.link_internal_operands)
        writer.write_asm_entries()
        html = self._read_file(join(ASMDIR, '30000.html'), True)
        line_no = 46
        for inst, address in (
            ('CALL', 30003),
            ('JP', 30006),
            ('DJNZ', 30006),
            ('JR', 30000)
        ):
            operation = '{} {}'.format(inst, address)
            self.assertEqual(html[line_no], '<td class="instruction">{}</td>'.format(operation))
            line_no += 6

    def test_parameter_LinkInternalOperands_1(self):
        ref = '[Game]\nLinkInternalOperands=1'
        skool = '\n'.join((
            '; Routine at 40000',
            'c40000 CALL 40003',
            ' 40003 JP 40006',
            ' 40006 DJNZ 40006',
            ' 40009 JR 40000'
        ))
        writer = self._get_writer(ref=ref, skool=skool)
        self.assertTrue(writer.link_internal_operands)
        writer.write_asm_entries()
        html = self._read_file(join(ASMDIR, '40000.html'), True)
        line_no = 46
        for inst, address in (
            ('CALL', 40003),
            ('JP', 40006),
            ('DJNZ', 40006),
            ('JR', 40000)
        ):
            operation = '{0} <a href="40000.html#{1}">{1}</a>'.format(inst, address)
            self.assertEqual(html[line_no], '<td class="instruction">{}</td>'.format(operation))
            line_no += 6

    def test_parameter_LinkOperands(self):
        ref = '[Game]\nLinkOperands={}'
        skool = '\n'.join((
            '; Routine at 32768',
            'c32768 RET',
            '',
            '; Routine at 32769',
            'c32769 CALL 32768',
            ' 32772 DEFW 32768',
            ' 32774 DJNZ 32768',
            ' 32776 JP 32768',
            ' 32779 JR 32768',
            ' 32781 LD HL,32768'
        ))
        for param_value in ('CALL,JP,JR', 'CALL,DEFW,djnz,JP,LD'):
            writer = self._get_writer(ref=ref.format(param_value), skool=skool)
            link_operands = tuple(param_value.upper().split(','))
            self.assertEqual(writer.link_operands, link_operands)
            writer.write_asm_entries()
            html = self._read_file(join(ASMDIR, '32769.html'), True)
            link = '<a href="32768.html">32768</a>'
            line_no = 46
            for prefix in ('CALL ', 'DEFW ', 'DJNZ ', 'JP ', 'JR ', 'LD HL,'):
                inst_type = prefix.split()[0]
                exp_html = prefix + (link if inst_type in link_operands else '32768')
                self.assertEqual(html[line_no], '<td class="instruction">{}</td>'.format(exp_html))
                line_no += 6

    def test_html_escape(self):
        # Check that HTML characters from the skool file are escaped
        skool = '\n'.join((
            '; Save & quit',
            ';',
            '; This routine saves & quits.',
            ';',
            '; A Some value >= 5',
            ';',
            '; First we save & quit.',
            'c24576 CALL 32768',
            '; Message: <&>',
            ' 24579 DEFM "<&>" ; a <= b & b >= c',
            '; </done>'
        ))
        writer = self._get_writer(skool=skool)
        writer.write_entry(ASMDIR, 0, writer.paths['MemoryMap'])
        html = self._read_file(join(ASMDIR, '24576.html'))
        self.assertIn('Save &amp; quit', html)
        self.assertIn('This routine saves &amp; quits.', html)
        self.assertIn('Some value &gt;= 5', html)
        self.assertIn('First we save &amp; quit.', html)
        self.assertIn('Message: &lt;&amp;&gt;', html)
        self.assertIn('DEFM "&lt;&amp;&gt;"', html)
        self.assertIn('a &lt;= b &amp; b &gt;= c', html)
        self.assertIn('&lt;/done&gt;', html)

    def test_html_no_escape(self):
        # Check that HTML characters from the ref file are not escaped
        ref = '[Bug:test:Test]\n<p>Hello</p>'
        writer = self._get_writer(ref=ref)
        writer.write_bugs()
        html = self._read_file(join(REFERENCE_DIR, 'bugs.html'))
        self.assertIn('<p>Hello</p>', html)

    def _test_write_index(self, files, content, ref='', custom_subs=None):
        writer = self._get_writer(ref=ref, skool='')
        for f in files:
            self.write_text_file(path=join(self.odir, GAMEDIR, f))
        writer.write_index()
        subs = {
            'header': 'Index',
            'header_prefix': 'The complete',
            'header_suffix': 'RAM disassembly',
            'path': '',
            'body_class': 'GameIndex',
            'content': content
        }
        if custom_subs:
            subs.update(custom_subs)
        self._assert_files_equal('index.html', subs, True)
        self.remove_files()

    def test_write_index_empty(self):
        # Empty index
        files = []
        content = ""
        self._test_write_index(files, content)

    def test_write_index_two_maps(self):
        # Memory map, routines map
        files = [
            join(MAPS_DIR, 'all.html'),
            join(MAPS_DIR, 'routines.html')
        ]
        content = """
            <div class="section-header">Memory maps</div>
            <ul class="index-list">
            <li><a href="maps/all.html">Everything</a></li>
            <li><a href="maps/routines.html">Routines</a></li>
            </ul>
        """
        self._test_write_index(files, content)

    def test_write_index_three_maps(self):
        # Memory map, routines map, data map
        files = [
            join(MAPS_DIR, 'all.html'),
            join(MAPS_DIR, 'routines.html'),
            join(MAPS_DIR, 'data.html')
        ]
        content = """
            <div class="section-header">Memory maps</div>
            <ul class="index-list">
            <li><a href="maps/all.html">Everything</a></li>
            <li><a href="maps/routines.html">Routines</a></li>
            <li><a href="maps/data.html">Data</a></li>
            </ul>
        """
        self._test_write_index(files, content)

    def test_write_index_four_maps(self):
        # Memory map, routines map, data map, messages map
        files = [
            join(MAPS_DIR, 'all.html'),
            join(MAPS_DIR, 'routines.html'),
            join(MAPS_DIR, 'data.html'),
            join(MAPS_DIR, 'messages.html')
        ]
        content = """
            <div class="section-header">Memory maps</div>
            <ul class="index-list">
            <li><a href="maps/all.html">Everything</a></li>
            <li><a href="maps/routines.html">Routines</a></li>
            <li><a href="maps/data.html">Data</a></li>
            <li><a href="maps/messages.html">Messages</a></li>
            </ul>
        """
        self._test_write_index(files, content)

    def test_write_index_other_code(self):
        # Other code
        files = ('other/other.html', 'load/index.html')
        ref = '\n'.join((
            '[OtherCode:otherCode]',
            'Source=other.skool',
            '[OtherCode:otherCode2]',
            'Source=load.skool',
            '[Links]',
            'otherCode-Index=Startup code',
            'otherCode2-Index=Loading code',
            '[Paths]',
            'otherCode-Index={}',
            'otherCode2-Index={}'
        )).format(*files)
        content = """
            <div class="section-header">Other code</div>
            <ul class="index-list">
            <li><a href="other/other.html">Startup code</a></li>
            <li><a href="load/index.html">Loading code</a></li>
            </ul>
        """
        self._test_write_index(files, content, ref)

    def test_write_index_custom(self):
        # Defined by [Game], [Index], [Index:*:*], [Links] and [Paths] sections
        title_prefix = 'The woefully incomplete'
        title_suffix = 'disassembly of the RAM'
        ref = '\n'.join((
            '[Game]',
            'TitlePrefix={}'.format(title_prefix),
            'TitleSuffix={}'.format(title_suffix),
            '',
            '[Index]',
            'Reference',
            'MemoryMaps',
            '',
            '[Index:Reference:Reference material]',
            'Bugs',
            'Facts',
            '',
            '[Index:MemoryMaps:RAM maps]',
            'RoutinesMap',
            'WordMap',
            '',
            '[Links]',
            'WordMap=Words',
            'Facts=Facts',
            '',
            '[MemoryMap:WordMap]',
            'EntryTypes=w',
            '',
            '[Paths]',
            'RoutinesMap=memorymaps/routines.html',
            'WordMap=memorymaps/words.html',
            'Bugs=ref/bugs.html',
            'Facts=ref/facts.html',
            'Changelog=ref/changelog.html',
        ))
        files = [
            'ref/bugs.html',
            'ref/facts.html',
            'ref/changelog.html',
            'memorymaps/routines.html',
            'memorymaps/words.html',
            'memorymaps/data.html'
        ]
        content = """
            <div class="section-header">Reference material</div>
            <ul class="index-list">
            <li><a href="ref/bugs.html">Bugs</a></li>
            <li><a href="ref/facts.html">Facts</a></li>
            </ul>
            <div class="section-header">RAM maps</div>
            <ul class="index-list">
            <li><a href="memorymaps/routines.html">Routines</a></li>
            <li><a href="memorymaps/words.html">Words</a></li>
            </ul>
        """
        custom_subs = {
            'header_prefix': title_prefix,
            'header_suffix': title_suffix
        }
        self._test_write_index(files, content, ref, custom_subs)

    def test_write_index_with_custom_link_text(self):
        ref = '\n'.join((
            '[Links]',
            'Bugs=[Bugs] (glitches)',
            'Changelog=Change log',
            'DataMap=Game data',
            'Facts=[Facts] (trivia)',
            'GameStatusBuffer=Workspace',
            'Glossary=List of terms',
            'GraphicGlitches=Graphic bugs',
            'MemoryMap=All code and data',
            'MessagesMap=Strings',
            'Pokes=POKEs',
            'RoutinesMap=Game code',
            'UnusedMap=Unused bytes'
        ))
        files = [
            'buffers/gbuffer.html',
            'graphics/glitches.html',
            'maps/all.html',
            'maps/data.html',
            'maps/messages.html',
            'maps/routines.html',
            'maps/unused.html',
            'reference/bugs.html',
            'reference/changelog.html',
            'reference/facts.html',
            'reference/glossary.html',
            'reference/pokes.html',
        ]
        content = """
            <div class="section-header">Memory maps</div>
            <ul class="index-list">
            <li><a href="maps/all.html">All code and data</a></li>
            <li><a href="maps/routines.html">Game code</a></li>
            <li><a href="maps/data.html">Game data</a></li>
            <li><a href="maps/messages.html">Strings</a></li>
            <li><a href="maps/unused.html">Unused bytes</a></li>
            </ul>
            <div class="section-header">Graphics</div>
            <ul class="index-list">
            <li><a href="graphics/glitches.html">Graphic bugs</a></li>
            </ul>
            <div class="section-header">Data tables and buffers</div>
            <ul class="index-list">
            <li><a href="buffers/gbuffer.html">Workspace</a></li>
            </ul>
            <div class="section-header">Reference</div>
            <ul class="index-list">
            <li><a href="reference/changelog.html">Change log</a></li>
            <li><a href="reference/glossary.html">List of terms</a></li>
            <li><a href="reference/facts.html">Facts</a> (trivia)</li>
            <li><a href="reference/bugs.html">Bugs</a> (glitches)</li>
            <li><a href="reference/pokes.html">POKEs</a></li>
            </ul>
        """
        self._test_write_index(files, content, ref)

    def test_write_index_with_custom_footer(self):
        files = []
        content = ""
        release = 'foo'
        c = 'bar'
        created = 'baz'
        ref = '\n'.join((
            '[Game]',
            'Copyright={}',
            'Created={}',
            'Release={}'
        )).format(c, created, release)
        footer = '\n'.join((
            '<footer>',
            '<div class="release">{}</div>',
            '<div class="copyright">{}</div>',
            '<div class="created">{}</div>',
            '</footer>',
            '</body>',
            '</html>'
        )).format(release, c, created)
        custom_subs = {'footer': footer}
        self._test_write_index(files, content, ref, custom_subs)

    def test_write_index_empty_with_logo_image(self):
        # Empty index with logo image
        writer = self._get_writer(skool='')
        logo_image_path = 'logo.png'
        writer.game_vars['LogoImage'] = logo_image_path
        self.write_bin_file(path=join(self.odir, GAMEDIR, logo_image_path))
        writer.write_index()
        game = basename(self.skoolfile)[:-6]
        subs = {
            'name': game,
            'header': 'Index',
            'header_prefix': 'The complete',
            'logo': '<img alt="{}" src="{}" />'.format(game, logo_image_path),
            'header_suffix': 'RAM disassembly',
            'path': '',
            'body_class': 'GameIndex',
            'content': ''
        }
        self._assert_files_equal('index.html', subs, True)

    def test_write_asm_entries(self):
        ref = '\n'.join((
            '[OtherCode:start]',
            'Source=start.skool'
        ))
        skool = '\n'.join((
            '; Routine at 24576',
            ';',
            '; Description of routine at 24576.',
            ';',
            '; A Some value',
            '; B Some other value',
            'c24576 LD A,B  ; Comment for instruction at 24576',
            '; Mid-routine comment above 24577.',
            '*24577 RET',
            '; End comment for routine at 24576.',
            '',
            '; Data block at 24578',
            'b24578 DEFB 0',
            '',
            '; Routine at 24579',
            'c24579 JR 24577',
            '',
            '; GSB entry at 24581',
            'g24581 DEFW 123',
            '',
            '; Unused',
            'u24583 DEFB 0',
            '',
            '; Routine at 24584 (register section but no description)',
            ';',
            '; .',
            ';',
            '; A 0',
            'c24584 CALL 30000  ; {Comment for the instructions at 24584 and 24587',
            ' 24587 JP 30003    ; }',
            '',
            'r30000 start',
            ' 30003',
        ))
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        # Routine at 24576
        content = """
            <div class="description">24576: Routine at 24576</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="4">
            <div class="details">
            <div class="paragraph">
            Description of routine at 24576.
            </div>
            </div>
            <table class="input-1">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            <tr>
            <td class="register">A</td>
            <td class="register-desc">Some value</td>
            </tr>
            <tr>
            <td class="register">B</td>
            <td class="register-desc">Some other value</td>
            </tr>
            </table>
            <table class="output-0">
            <tr class="asm-output-header">
            <th colspan="2">Output</th>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-2"><span id="24576"></span>24576</td>
            <td class="instruction">LD A,B</td>
            <td class="comment-11" rowspan="1">Comment for instruction at 24576</td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="4">
            <span id="24577"></span>
            <div class="comments">
            <div class="paragraph">
            Mid-routine comment above 24577.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-2"><span id="24577"></span>24577</td>
            <td class="instruction">RET</td>
            <td class="comment-11" rowspan="1"></td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="4">
            <div class="comments">
            <div class="paragraph">
            End comment for routine at 24576.
            </div>
            </div>
            </td>
            </tr>
            </table>
        """
        subs = {
            'title': 'Routine at 24576',
            'body_class': 'Asm-c',
            'header': 'Routines',
            'up': 24576,
            'next': 24578,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '24576.html'), subs)

        # Data at 24578
        content = """
            <div class="description">24578: Data block at 24578</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="4">
            <div class="details">
            </div>
            <table class="input-0">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            </table>
            <table class="output-0">
            <tr class="asm-output-header">
            <th colspan="2">Output</th>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="24578"></span>24578</td>
            <td class="instruction">DEFB 0</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'title': 'Data at 24578',
            'body_class': 'Asm-b',
            'header': 'Data',
            'prev': 24576,
            'up': 24578,
            'next': 24579,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '24578.html'), subs)

        # Routine at 24579
        content = """
            <div class="description">24579: Routine at 24579</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="4">
            <div class="details">
            </div>
            <table class="input-0">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            </table>
            <table class="output-0">
            <tr class="asm-output-header">
            <th colspan="2">Output</th>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-2"><span id="24579"></span>24579</td>
            <td class="instruction">JR <a href="24576.html#24577">24577</a></td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'title': 'Routine at 24579',
            'body_class': 'Asm-c',
            'header': 'Routines',
            'prev': 24578,
            'up': 24579,
            'next': 24581,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '24579.html'), subs)

        # Game status buffer entry at 24581
        content = """
            <div class="description">24581: GSB entry at 24581</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="4">
            <div class="details">
            </div>
            <table class="input-0">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            </table>
            <table class="output-0">
            <tr class="asm-output-header">
            <th colspan="2">Output</th>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="24581"></span>24581</td>
            <td class="instruction">DEFW 123</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'title': 'Game status buffer entry at 24581',
            'body_class': 'Asm-g',
            'header': 'Game status buffer',
            'prev': 24579,
            'up': 24581,
            'next': 24583,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '24581.html'), subs)

        # Unused RAM at 24583
        content = """
            <div class="description">24583: Unused</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="4">
            <div class="details">
            </div>
            <table class="input-0">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            </table>
            <table class="output-0">
            <tr class="asm-output-header">
            <th colspan="2">Output</th>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="24583"></span>24583</td>
            <td class="instruction">DEFB 0</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'title': 'Unused RAM at 24583',
            'body_class': 'Asm-u',
            'header': 'Unused',
            'prev': 24581,
            'up': 24583,
            'next': 24584,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '24583.html'), subs)

        # Routine at 24584
        content = """
            <div class="description">24584: Routine at 24584 (register section but no description)</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="4">
            <div class="details">
            </div>
            <table class="input-1">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            <tr>
            <td class="register">A</td>
            <td class="register-desc">0</td>
            </tr>
            </table>
            <table class="output-0">
            <tr class="asm-output-header">
            <th colspan="2">Output</th>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-2"><span id="24584"></span>24584</td>
            <td class="instruction">CALL <a href="../start/30000.html">30000</a></td>
            <td class="comment-11" rowspan="2">Comment for the instructions at 24584 and 24587</td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="24587"></span>24587</td>
            <td class="instruction">JP <a href="../start/30000.html#30003">30003</a></td>
            <td class="comment-01" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'title': 'Routine at 24584',
            'body_class': 'Asm-c',
            'header': 'Routines',
            'prev': 24583,
            'up': 24584,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '24584.html'), subs)

    def test_write_asm_entries_with_decimal_addresses_below_10000(self):
        skool = '\n'.join((
            'c00000 RET',
            '',
            'c00002 RET',
            '',
            'c00044 RET',
            '',
            'c00666 RET',
            '',
            'c08888 RET'
        ))
        entry_template = '\n'.join((
            '<div class="description">{address:05d}: </div>',
            '<table class="disassembly">',
            '<tr>',
            '<td class="routine-comment" colspan="4">',
            '<div class="details">',
            '</div>',
            '<table class="input-0">',
            '<tr class="asm-input-header">',
            '<th colspan="2">Input</th>',
            '</tr>',
            '</table>',
            '<table class="output-0">',
            '<tr class="asm-output-header">',
            '<th colspan="2">Output</th>',
            '</tr>',
            '</table>',
            '</td>',
            '</tr>',
            '<tr>',
            '<td class="asm-label-0"></td>',
            '<td class="address-2"><span id="{address}"></span>{address:05d}</td>',
            '<td class="instruction">RET</td>',
            '<td class="comment-10" rowspan="1"></td>',
            '</tr>',
            '</table>',
            ''
        ))
        common_subs = {
            'body_class': 'Asm-c',
            'header': 'Routines'
        }

        for base in (None, BASE_10):
            writer = self._get_writer(skool=skool, base=BASE_10)
            writer.write_asm_entries()

            # Address 0
            subs = {
                'title': 'Routine at 00000',
                'up': 0,
                'next': 2,
                'content': entry_template.format(address=0)
            }
            subs.update(common_subs)
            self._assert_files_equal(join(ASMDIR, '0.html'), subs)

            # Address 2
            subs = {
                'title': 'Routine at 00002',
                'prev': 0,
                'up': 2,
                'next': 44,
                'content': entry_template.format(address=2)
            }
            subs.update(common_subs)
            self._assert_files_equal(join(ASMDIR, '2.html'), subs)

            # Address 44
            subs = {
                'title': 'Routine at 00044',
                'prev': 2,
                'up': 44,
                'next': 666,
                'content': entry_template.format(address=44)
            }
            subs.update(common_subs)
            self._assert_files_equal(join(ASMDIR, '44.html'), subs)

            # Address 666
            subs = {
                'title': 'Routine at 00666',
                'prev': 44,
                'up': 666,
                'next': 8888,
                'content': entry_template.format(address=666)
            }
            subs.update(common_subs)
            self._assert_files_equal(join(ASMDIR, '666.html'), subs)

            # Address 8888
            subs = {
                'title': 'Routine at 08888',
                'prev': 666,
                'up': 8888,
                'content': entry_template.format(address=8888)
            }
            subs.update(common_subs)
            self._assert_files_equal(join(ASMDIR, '8888.html'), subs)

    def test_write_asm_entries_with_custom_titles_and_headers(self):
        titles = {
            'b': 'Bytes at',
            'c': 'Code at',
            'g': 'GSB entry at',
            's': 'Space at',
            't': 'Text at',
            'u': 'Unused bytes at',
            'w': 'Words at'
        }
        headers = {
            'b': 'Bytes',
            'c': 'Code',
            'g': 'GSB',
            's': 'Unused space',
            't': 'Text',
            'u': 'Unused bytes',
            'w': 'Words'
        }
        ref = '\n'.join((
            '[Titles]',
            'Asm-b={titles[b]}',
            'Asm-c={titles[c]}',
            'Asm-g={titles[g]}',
            'Asm-s={titles[s]}',
            'Asm-t={titles[t]}',
            'Asm-u={titles[u]}',
            'Asm-w={titles[w]}',
            '[PageHeaders]',
            'Asm-b={headers[b]}',
            'Asm-c={headers[c]}',
            'Asm-g={headers[g]}',
            'Asm-s={headers[s]}',
            'Asm-t={headers[t]}',
            'Asm-u={headers[u]}',
            'Asm-w={headers[w]}',
        )).format(titles=titles, headers=headers)
        skool = '\n'.join((
            '; b',
            'b30000 DEFB 0',
            '',
            '; c',
            'c30001 RET',
            '',
            '; g',
            'g30002 DEFB 0',
            '',
            '; s',
            's30003 DEFS 1',
            '',
            '; t',
            't30004 DEFM "a"',
            '',
            '; u',
            'u30005 DEFB 0',
            '',
            '; w',
            'w30006 DEFW 0'
        ))
        writer = self._get_writer(ref=ref, skool=skool)
        name = basename(self.skoolfile)[:-6]
        writer.write_asm_entries()

        address = 30000
        for entry_type in 'bcgstuw':
            path = '{}/{}.html'.format(ASMDIR, address)
            title = '{} {}'.format(titles[entry_type], address)
            self._assert_title_equals(path, title, headers[entry_type])
            address += 1

    def test_write_asm_entries_with_custom_filenames(self):
        ref = '[Paths]\nCodeFiles=asm-{address:04x}.html'
        skool = '\n'.join((
            '; Data',
            'b30000 DEFS 10000',
            '',
            '; More data',
            'b40000 DEFS 10000'
        ))
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        for address in (30000, 40000):
            path = '{}/asm-{:04x}.html'.format(ASMDIR, address)
            title = 'Data at {}'.format(address)
            self._assert_title_equals(path, title, 'Data')

    def test_write_asm_entries_with_invalid_filename_template(self):
        ref = '[Paths]\nCodeFiles={Address:04x}.html'
        skool = 'b30000 DEFS 10000'
        writer = self._get_writer(ref=ref, skool=skool)
        with self.assertRaises(SkoolKitError) as cm:
            writer.write_asm_entries()
        self.assertEqual(cm.exception.args[0], "Cannot format filename ({Address:04x}.html) with address=30000")

    def test_write_asm_entries_with_custom_anchors(self):
        ref = '\n'.join((
            '[Game]',
            'AddressAnchor={address:04X}',
            'LinkInternalOperands=1'
        ))
        skool = '\n'.join((
            '; Routine at 50000',
            'c50000 LD A,B',
            '; Jump back.',
            ' 50001 JR 50000'
        ))
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">50000: Routine at 50000</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="4">
            <div class="details">
            </div>
            <table class="input-0">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            </table>
            <table class="output-0">
            <tr class="asm-output-header">
            <th colspan="2">Output</th>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-2"><span id="C350"></span>50000</td>
            <td class="instruction">LD A,B</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="4">
            <span id="C351"></span>
            <div class="comments">
            <div class="paragraph">
            Jump back.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="C351"></span>50001</td>
            <td class="instruction">JR <a href="50000.html#C350">50000</a></td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at 50000',
            'body_class': 'Asm-c',
            'up': 'C350',
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '50000.html'), subs)

    def test_write_asm_entries_with_invalid_asm_anchor(self):
        ref = '[Game]\nAddressAnchor={Address:04x}'
        skool = 'c40000 RET'
        writer = self._get_writer(ref=ref, skool=skool)
        with self.assertRaises(SkoolKitError) as cm:
            writer.write_asm_entries()
        self.assertEqual(cm.exception.args[0], "Cannot format anchor ({Address:04x}) with address=40000")

    def test_write_asm_entries_with_missing_OtherCode_section(self):
        skool = '\n'.join((
            'c30000 JP 50000',
            '',
            'r50000 save'
        ))
        writer = self._get_writer(skool=skool)
        with self.assertRaises(SkoolKitError) as cm:
            writer.write_asm_entries()
        self.assertEqual(cm.exception.args[0], "Cannot find code path for 'save' disassembly")

    def test_block_start_comment(self):
        start_comment = ('Start comment paragraph 1.', 'Paragraph 2.')
        skool = '\n'.join((
            '; Routine with a start comment',
            ';',
            '; .',
            ';',
            '; .',
            ';',
            '; {}',
            '; .',
            '; {}',
            'c40000 RET'
        )).format(*start_comment)
        writer = self._get_writer(skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">40000: Routine with a start comment</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="4">
            <div class="details">
            </div>
            <table class="input-0">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            </table>
            <table class="output-0">
            <tr class="asm-output-header">
            <th colspan="2">Output</th>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="4">
            <span id="40000"></span>
            <div class="comments">
            <div class="paragraph">
            {}
            </div>
            <div class="paragraph">
            {}
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-2"><span id="40000"></span>40000</td>
            <td class="instruction">RET</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            </table>
        """.format(*start_comment)
        subs = {
            'header': 'Routines',
            'title': 'Routine at 40000',
            'body_class': 'Asm-c',
            'up': 40000,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '40000.html'), subs)

    def test_asm_labels(self):
        skool = '\n'.join((
            '; Routine with a label',
            '@label=START',
            'c50000 LD B,5     ; Loop 5 times',
            '*50002 DJNZ 50002',
            ' 50004 RET',
            '',
            '; Routine without a label',
            'c50005 JP 50000',
            '',
            '; DEFW statement with a @keep directive',
            '@keep',
            'w50008 DEFW 50000',
        ))
        writer = self._get_writer(skool=skool, asm_labels=True)
        writer.write_asm_entries()

        # Routine at 50000
        content = """
            <div class="description">50000: Routine with a label</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="4">
            <div class="details">
            </div>
            <table class="input-0">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            </table>
            <table class="output-0">
            <tr class="asm-output-header">
            <th colspan="2">Output</th>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="asm-label-1">START</td>
            <td class="address-2"><span id="50000"></span>50000</td>
            <td class="instruction">LD B,5</td>
            <td class="comment-11" rowspan="1">Loop 5 times</td>
            </tr>
            <tr>
            <td class="asm-label-1">START_0</td>
            <td class="address-2"><span id="50002"></span>50002</td>
            <td class="instruction">DJNZ <a href="50000.html#50002">START_0</a></td>
            <td class="comment-11" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-1"></td>
            <td class="address-1"><span id="50004"></span>50004</td>
            <td class="instruction">RET</td>
            <td class="comment-11" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at 50000',
            'body_class': 'Asm-c',
            'up': 50000,
            'next': 50005,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '50000.html'), subs)

        # Routine at 50005
        content = """
            <div class="description">50005: Routine without a label</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="4">
            <div class="details">
            </div>
            <table class="input-0">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            </table>
            <table class="output-0">
            <tr class="asm-output-header">
            <th colspan="2">Output</th>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-2"><span id="50005"></span>50005</td>
            <td class="instruction">JP <a href="50000.html">START</a></td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at 50005',
            'body_class': 'Asm-c',
            'prev': 50000,
            'up': 50005,
            'next': 50008,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '50005.html'), subs)

        # DEFW statement at 50008
        content = """
            <div class="description">50008: DEFW statement with a @keep directive</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="4">
            <div class="details">
            </div>
            <table class="input-0">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            </table>
            <table class="output-0">
            <tr class="asm-output-header">
            <th colspan="2">Output</th>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="50008"></span>50008</td>
            <td class="instruction">DEFW 50000</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Data',
            'title': 'Data at 50008',
            'body_class': 'Asm-w',
            'prev': 50005,
            'up': 50008,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '50008.html'), subs)

    def test_asm_labels_and_rst_instructions(self):
        ref = '\n'.join((
            '[Game]',
            'LinkOperands=CALL,DEFW,DJNZ,JP,JR,RST'
        ))
        skool = '\n'.join((
            '; Start',
            'c00000 RST 8  ; This operand should not be replaced by a label',
            ' 00001 DEFS 7',
            '',
            '; Restart routine at 8',
            '@label=DONOTHING',
            'c00008 RET'
        ))
        writer = self._get_writer(ref=ref, skool=skool, asm_labels=True)
        writer.write_asm_entries()

        # Routine at 00000
        content = """
            <div class="description">00000: Start</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="4">
            <div class="details">
            </div>
            <table class="input-0">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            </table>
            <table class="output-0">
            <tr class="asm-output-header">
            <th colspan="2">Output</th>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-2"><span id="0"></span>00000</td>
            <td class="instruction">RST <a href="8.html">8</a></td>
            <td class="comment-11" rowspan="1">This operand should not be replaced by a label</td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="1"></span>00001</td>
            <td class="instruction">DEFS 7</td>
            <td class="comment-11" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at 00000',
            'body_class': 'Asm-c',
            'up': 0,
            'next': 8,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '0.html'), subs)

    def test_write_map(self):
        skool = '\n'.join((
            '; Routine',
            'c30000 RET',
            '',
            '; Bytes',
            'b30001 DEFB 1,2',
            '',
            '; Words',
            'w30003 DEFW 257,65534',
            '',
            '; GSB entry',
            'g30007 DEFB 0',
            '',
            '; Unused',
            'u30008 DEFB 0',
            '',
            '; Zeroes',
            's30009 DEFS 9',
            '',
            '; Text',
            't30018 DEFM "Hi"'
        ))
        writer = self._get_writer(skool=skool)

        # Memory map
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page-1">Page</th>
            <th class="map-byte-1">Byte</th>
            <th>Address</th>
            <th class="map-length-0">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-1">117</td>
            <td class="map-byte-1">48</td>
            <td class="map-c"><span id="30000"></span><a href="../asm/30000.html">30000</a></td>
            <td class="map-length-0">1</td>
            <td class="map-c-desc">
            <div class="map-entry-title-10">Routine</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-1">117</td>
            <td class="map-byte-1">49</td>
            <td class="map-b"><span id="30001"></span><a href="../asm/30001.html">30001</a></td>
            <td class="map-length-0">2</td>
            <td class="map-b-desc">
            <div class="map-entry-title-10">Bytes</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-1">117</td>
            <td class="map-byte-1">51</td>
            <td class="map-w"><span id="30003"></span><a href="../asm/30003.html">30003</a></td>
            <td class="map-length-0">4</td>
            <td class="map-w-desc">
            <div class="map-entry-title-10">Words</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-1">117</td>
            <td class="map-byte-1">55</td>
            <td class="map-g"><span id="30007"></span><a href="../asm/30007.html">30007</a></td>
            <td class="map-length-0">1</td>
            <td class="map-g-desc">
            <div class="map-entry-title-10">GSB entry</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-1">117</td>
            <td class="map-byte-1">56</td>
            <td class="map-u"><span id="30008"></span><a href="../asm/30008.html">30008</a></td>
            <td class="map-length-0">1</td>
            <td class="map-u-desc">
            <div class="map-entry-title-10">Unused</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-1">117</td>
            <td class="map-byte-1">57</td>
            <td class="map-s"><span id="30009"></span><a href="../asm/30009.html">30009</a></td>
            <td class="map-length-0">9</td>
            <td class="map-s-desc">
            <div class="map-entry-title-10">Zeroes</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-1">117</td>
            <td class="map-byte-1">66</td>
            <td class="map-t"><span id="30018"></span><a href="../asm/30018.html">30018</a></td>
            <td class="map-length-0">35518</td>
            <td class="map-t-desc">
            <div class="map-entry-title-10">Text</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            </table>
        """
        writer.write_map('MemoryMap')
        subs = {
            'body_class': 'MemoryMap',
            'header': 'Memory map',
            'content': content
        }
        self._assert_files_equal(join(MAPS_DIR, 'all.html'), subs)

        # Routines map
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page-0">Page</th>
            <th class="map-byte-0">Byte</th>
            <th>Address</th>
            <th class="map-length-0">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-0">117</td>
            <td class="map-byte-0">48</td>
            <td class="map-c"><span id="30000"></span><a href="../asm/30000.html">30000</a></td>
            <td class="map-length-0">1</td>
            <td class="map-c-desc">
            <div class="map-entry-title-10">Routine</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            </table>
        """
        writer.write_map('RoutinesMap')
        subs = {
            'body_class': 'RoutinesMap',
            'header': 'Routines',
            'content': content
        }
        self._assert_files_equal(join(MAPS_DIR, 'routines.html'), subs)

        # Data map
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page-1">Page</th>
            <th class="map-byte-1">Byte</th>
            <th>Address</th>
            <th class="map-length-0">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-1">117</td>
            <td class="map-byte-1">49</td>
            <td class="map-b"><span id="30001"></span><a href="../asm/30001.html">30001</a></td>
            <td class="map-length-0">2</td>
            <td class="map-b-desc">
            <div class="map-entry-title-10">Bytes</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-1">117</td>
            <td class="map-byte-1">51</td>
            <td class="map-w"><span id="30003"></span><a href="../asm/30003.html">30003</a></td>
            <td class="map-length-0">4</td>
            <td class="map-w-desc">
            <div class="map-entry-title-10">Words</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            </table>
        """
        writer.write_map('DataMap')
        subs = {
            'body_class': 'DataMap',
            'header': 'Data',
            'content': content
        }
        self._assert_files_equal(join(MAPS_DIR, 'data.html'), subs)

        # Messages map
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page-0">Page</th>
            <th class="map-byte-0">Byte</th>
            <th>Address</th>
            <th class="map-length-0">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-0">117</td>
            <td class="map-byte-0">66</td>
            <td class="map-t"><span id="30018"></span><a href="../asm/30018.html">30018</a></td>
            <td class="map-length-0">35518</td>
            <td class="map-t-desc">
            <div class="map-entry-title-10">Text</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            </table>
        """
        writer.write_map('MessagesMap')
        subs = {
            'body_class': 'MessagesMap',
            'header': 'Messages',
            'content': content
        }
        self._assert_files_equal(join(MAPS_DIR, 'messages.html'), subs)

        # Unused map
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page-1">Page</th>
            <th class="map-byte-1">Byte</th>
            <th>Address</th>
            <th class="map-length-1">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-1">117</td>
            <td class="map-byte-1">56</td>
            <td class="map-u"><span id="30008"></span><a href="../asm/30008.html">30008</a></td>
            <td class="map-length-1">1</td>
            <td class="map-u-desc">
            <div class="map-entry-title-10">Unused</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-1">117</td>
            <td class="map-byte-1">57</td>
            <td class="map-s"><span id="30009"></span><a href="../asm/30009.html">30009</a></td>
            <td class="map-length-1">9</td>
            <td class="map-s-desc">
            <div class="map-entry-title-10">Zeroes</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            </table>
        """
        writer.write_map('UnusedMap')
        subs = {
            'body_class': 'UnusedMap',
            'header': 'Unused addresses',
            'content': content
        }
        self._assert_files_equal(join(MAPS_DIR, 'unused.html'), subs)

    def test_write_map_with_invalid_filename_template(self):
        ref = '[Paths]\nCodeFiles={address:q}.html'
        skool = 'c10000 RET'
        writer = self._get_writer(ref=ref, skool=skool)
        with self.assertRaises(SkoolKitError) as cm:
            writer.write_map('MemoryMap')
        self.assertEqual(cm.exception.args[0], "Cannot format filename ({address:q}.html) with address=10000")

    def test_write_map_with_custom_asm_anchors(self):
        ref = '[Game]\nAddressAnchor={address:04x}'
        skool = '; Routine at 23456\nc23456 RET'
        writer = self._get_writer(ref=ref, skool=skool)

        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page-1">Page</th>
            <th class="map-byte-1">Byte</th>
            <th>Address</th>
            <th class="map-length-0">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-1">91</td>
            <td class="map-byte-1">160</td>
            <td class="map-c"><span id="5ba0"></span><a href="../asm/23456.html">23456</a></td>
            <td class="map-length-0">42080</td>
            <td class="map-c-desc">
            <div class="map-entry-title-10">Routine at 23456</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            </table>
        """
        writer.write_map('MemoryMap')
        subs = {
            'body_class': 'MemoryMap',
            'header': 'Memory map',
            'content': content
        }
        self._assert_files_equal(join(MAPS_DIR, 'all.html'), subs)

    def test_write_map_with_invalid_asm_anchor(self):
        ref = '[Game]\nAddressAnchor={foo:04X}'
        skool = 'c32768 RET'
        writer = self._get_writer(ref=ref, skool=skool)
        with self.assertRaises(SkoolKitError) as cm:
            writer.write_map('MemoryMap')
        self.assertEqual(cm.exception.args[0], "Cannot format anchor ({foo:04X}) with address=32768")

    def test_write_custom_map(self):
        skool = '\n'.join((
            '; Routine',
            ';',
            '; Return early, return often.',
            'c30000 RET',
            '',
            '; Bytes',
            'b30001 DEFB 1,2',
            '',
            '; GSB entry',
            'g30003 DEFB 0',
            '',
            '; Unused',
            'u30004 DEFB 0',
            '',
            '; Zeroes',
            's30005 DEFS 6',
            '',
            '; Text',
            't30011 DEFM "Hi"'
        ))
        map_id = 'CustomMap'
        map_intro = 'Introduction.'
        map_path = 'maps/custom.html'
        map_title = 'Custom map'
        ref = '\n'.join((
            '[MemoryMap:{0}]',
            'EntryDescriptions=1',
            'EntryTypes=cg',
            'Intro={1}',
            'LengthColumn=1',
            ''
            '[Paths]',
            '{0}={2}',
            '',
            '[PageHeaders]',
            '{0}={3}',
            '',
            '[Titles]',
            '{0}={3}'
        )).format(map_id, map_intro, map_path, map_title)
        writer = self._get_writer(ref=ref, skool=skool)

        content = """
            <div class="map-intro">{}</div>
            <table class="map">
            <tr>
            <th class="map-page-0">Page</th>
            <th class="map-byte-0">Byte</th>
            <th>Address</th>
            <th class="map-length-1">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-0">117</td>
            <td class="map-byte-0">48</td>
            <td class="map-c"><span id="30000"></span><a href="../asm/30000.html">30000</a></td>
            <td class="map-length-1">1</td>
            <td class="map-c-desc">
            <div class="map-entry-title-11">Routine</div>
            <div class="map-entry-desc-1">
            <div class="paragraph">
            Return early, return often.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-0">117</td>
            <td class="map-byte-0">51</td>
            <td class="map-g"><span id="30003"></span><a href="../asm/30003.html">30003</a></td>
            <td class="map-length-1">1</td>
            <td class="map-g-desc">
            <div class="map-entry-title-11">GSB entry</div>
            <div class="map-entry-desc-1">
            </div>
            </td>
            </tr>
            </table>
        """.format(map_intro)
        writer.write_map(map_id)
        subs = {
            'body_class': map_id,
            'header': map_title,
            'content': content
        }
        self._assert_files_equal(map_path, subs)

    def test_write_custom_map_using_custom_template(self):
        map_id = 'CustomMap'
        ref = '\n'.join((
            '[MemoryMap:{0}]',
            'EntryTypes=c',
            'Intro=Bar',
            '[Template:{0}]',
            '<foo>{{MemoryMap[Intro]}}</foo>'
        )).format(map_id)
        writer = self._get_writer(ref=ref, skool='c50000 RET')
        writer.write_map(map_id)
        path = 'maps/{}.html'.format(map_id)
        self.assertEqual('<foo>Bar</foo>', self.files[path])

    def test_write_memory_map_with_intro(self):
        intro = 'This map is empty.'
        ref = '[MemoryMap:MemoryMap]\nIntro={}'.format(intro)
        writer = self._get_writer(ref=ref, skool='; Code\nc32768 RET')
        content = """
            <div class="map-intro">{}</div>
            <table class="map">
            <tr>
            <th class="map-page-1">Page</th>
            <th class="map-byte-1">Byte</th>
            <th>Address</th>
            <th class="map-length-0">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-1">128</td>
            <td class="map-byte-1">0</td>
            <td class="map-c"><span id="32768"></span><a href="../asm/32768.html">32768</a></td>
            <td class="map-length-0">32768</td>
            <td class="map-c-desc">
            <div class="map-entry-title-10">Code</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            </table>
        """.format(intro)
        subs = {
            'header': 'Memory map',
            'body_class': 'MemoryMap',
            'content': content
        }

        writer.write_map('MemoryMap')
        self._assert_files_equal(join(MAPS_DIR, 'all.html'), subs)

    def test_write_map_with_decimal_addresses_below_10000(self):
        skool = '\n'.join((
            'c00000 RET',
            '',
            'c00002 RET',
            '',
            'c00044 RET',
            '',
            'c00666 RET',
            '',
            'c08888 RET'
        ))
        exp_content = '\n'.join((
            '<div class="map-intro"></div>',
            '<table class="map">',
            '<tr>',
            '<th class="map-page-1">Page</th>',
            '<th class="map-byte-1">Byte</th>',
            '<th>Address</th>',
            '<th class="map-length-0">Length</th>',
            '<th>Description</th>',
            '</tr>\n'
        ))
        for address, length in ((0, 2), (2, 42), (44, 622), (666, 8222), (8888, 56648)):
            exp_content += '\n'.join((
                '<tr>',
                '<td class="map-page-1">{}</td>'.format(address // 256),
                '<td class="map-byte-1">{}</td>'.format(address % 256),
                '<td class="map-c"><span id="{0}"></span><a href="../asm/{0}.html">{0:05d}</a></td>'.format(address),
                '<td class="map-length-0">{}</td>'.format(length),
                '<td class="map-c-desc">',
                '<div class="map-entry-title-10"></div>',
                '<div class="map-entry-desc-0">',
                '</div>',
                '</td>',
                '</tr>\n'
            ))
        exp_content += '</table>\n'

        # Memory map
        for base in (None, BASE_10):
            writer = self._get_writer(skool=skool, base=base)
            writer.write_map('MemoryMap')
            subs = {
                'header': 'Memory map',
                'body_class': 'MemoryMap',
                'content': exp_content
            }
            self._assert_files_equal(join(MAPS_DIR, 'all.html'), subs)

    def test_write_data_map_with_custom_title_and_header_and_path(self):
        title = 'Data blocks'
        header = 'Blocks of data'
        path = 'foo/bar/data.html'
        ref = '\n'.join((
            '[Titles]',
            'DataMap={}',
            '[PageHeaders]',
            'DataMap={}',
            '[Paths]',
            'DataMap={}'
        )).format(title, header, path)
        writer = self._get_writer(ref=ref, skool='b30000 DEFB 0')
        writer.write_map('DataMap')
        self._assert_title_equals(path, title, header)

    def test_write_memory_map_with_custom_title_and_header_and_path(self):
        title = 'All the RAM'
        header = 'Every bit'
        path = 'memory_map.html'
        ref = '\n'.join((
            '[Titles]',
            'MemoryMap={}',
            '[PageHeaders]',
            'MemoryMap={}',
            '[Paths]',
            'MemoryMap={}'
        )).format(title, header, path)
        writer = self._get_writer(ref=ref, skool='c30000 RET')
        writer.write_map('MemoryMap')
        self._assert_title_equals(path, title, header)

    def test_write_messages_map_with_custom_title_and_header_and_path(self):
        title = 'Strings'
        header = 'Text'
        path = 'text/strings.html'
        ref = '\n'.join((
            '[Titles]',
            'MessagesMap={}',
            '[PageHeaders]',
            'MessagesMap={}',
            '[Paths]',
            'MessagesMap={}'
        )).format(title, header, path)
        writer = self._get_writer(ref=ref, skool='t30000 DEFM "a"')
        writer.write_map('MessagesMap')
        self._assert_title_equals(path, title, header)

    def test_write_routines_map_with_custom_title_and_header_and_path(self):
        title = 'All the code'
        header = 'Game code'
        path = 'mappage/code.html'
        ref = '\n'.join((
            '[Titles]',
            'RoutinesMap={}',
            '[PageHeaders]',
            'RoutinesMap={}',
            '[Paths]',
            'RoutinesMap={}'
        )).format(title, header, path)
        writer = self._get_writer(ref=ref, skool='c30000 RET')
        writer.write_map('RoutinesMap')
        self._assert_title_equals(path, title, header)

    def test_write_unused_map_with_custom_title_and_header_and_path(self):
        title = 'Bytes of no use'
        header = 'Unused memory'
        path = 'unused_bytes.html'
        ref = '\n'.join((
            '[Titles]',
            'UnusedMap={}',
            '[PageHeaders]',
            'UnusedMap={}',
            '[Paths]',
            'UnusedMap={}'
        )).format(title, header, path)
        writer = self._get_writer(ref=ref, skool='u30000 DEFB 0')
        writer.write_map('UnusedMap')
        self._assert_title_equals(path, title, header)

    def test_write_other_code_index(self):
        code_id = 'other'
        ref = '[OtherCode:{}]\nSource=other.skool'.format(code_id)
        routine_title = 'Other code'
        skool = '; {}\nc65535 RET'.format(routine_title)
        main_writer = self._get_writer(ref=ref, skool=skool)
        writer = main_writer.clone(main_writer.parser, code_id)
        writer.write_file = self._mock_write_file
        index_page_id = '{}-Index'.format(code_id)
        writer.write_map(index_page_id)
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page-0">Page</th>
            <th class="map-byte-0">Byte</th>
            <th>Address</th>
            <th class="map-length-0">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-0">255</td>
            <td class="map-byte-0">255</td>
            <td class="map-c"><span id="65535"></span><a href="65535.html">65535</a></td>
            <td class="map-length-0">1</td>
            <td class="map-c-desc">
            <div class="map-entry-title-10">{}</div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            </table>
        """.format(routine_title)
        subs = {
            'header': code_id,
            'body_class': index_page_id,
            'content': content
        }
        self._assert_files_equal('{0}/{0}.html'.format(code_id), subs)

    def test_write_changelog(self):
        ref = '\n'.join((
            '[Changelog:20120704]',
            'Documented many #BUG(bugs).',
            '',
            '1',
            '  2',
            '    3',
            '    4',
            '  5',
            '[Changelog:20120703]',
            '-',
            '',
            '1',
            '  2',
            '    3',
            '[Changelog:20120702]',
            'Initial release'
        ))
        content = """
            <ul class="contents">
            <li><a href="#20120704">20120704</a></li>
            <li><a href="#20120703">20120703</a></li>
            <li><a href="#20120702">20120702</a></li>
            </ul>
            <div><span id="20120704"></span></div>
            <div class="changelog changelog-1">
            <div class="changelog-title">20120704</div>
            <div class="changelog-desc">Documented many <a href="bugs.html">bugs</a>.</div>
            <ul class="changelog">
            <li>1
            <ul class="changelog1">
            <li>2
            <ul class="changelog2">
            <li>3</li>
            <li>4</li>
            </ul>
            </li>
            <li>5</li>
            </ul>
            </li>
            </ul>
            </div>
            <div><span id="20120703"></span></div>
            <div class="changelog changelog-2">
            <div class="changelog-title">20120703</div>
            <div class="changelog-desc"></div>
            <ul class="changelog">
            <li>1
            <ul class="changelog1">
            <li>2
            <ul class="changelog2">
            <li>3</li>
            </ul>
            </li>
            </ul>
            </li>
            </ul>
            </div>
            <div><span id="20120702"></span></div>
            <div class="changelog changelog-1">
            <div class="changelog-title">20120702</div>
            <div class="changelog-desc">Initial release</div>
            </div>
        """
        writer = self._get_writer(ref=ref, skool='')
        writer.write_changelog()
        subs = {
            'header': 'Changelog',
            'body_class': 'Changelog',
            'content': content
        }
        self._assert_files_equal(join(REFERENCE_DIR, 'changelog.html'), subs)

    def test_write_changelog_with_changelog_item_template(self):
        # Test that the 'changelog_item' template is used if defined (instead
        # of the default 'list_item' template)
        ref = '\n'.join((
            '[Changelog:20141123]',
            '-',
            '',
            'Item 1',
            'Item 2',
            '',
            '[Template:changelog_item]',
            '<li>* {item}</li>'
        ))
        content = """
            <ul class="contents">
            <li><a href="#20141123">20141123</a></li>
            </ul>
            <div><span id="20141123"></span></div>
            <div class="changelog changelog-1">
            <div class="changelog-title">20141123</div>
            <div class="changelog-desc"></div>
            <ul class="changelog">
            <li>* Item 1</li>
            <li>* Item 2</li>
            </ul>
            </div>
        """
        writer = self._get_writer(ref=ref, skool='')
        writer.write_changelog()
        subs = {
            'header': 'Changelog',
            'body_class': 'Changelog',
            'content': content
        }
        self._assert_files_equal(join(REFERENCE_DIR, 'changelog.html'), subs)

    def test_write_changelog_with_custom_title_and_header_and_path(self):
        title = 'Log of changes'
        header = 'What has changed?'
        path = 'changes/log.html'
        ref = '\n'.join((
            '[Titles]',
            'Changelog={}',
            '[PageHeaders]',
            'Changelog={}',
            '[Paths]',
            'Changelog={}'
        )).format(title, header, path)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_changelog()
        self._assert_title_equals(path, title, header)

    def test_write_glossary(self):
        ref = '\n'.join((
            '[Glossary:Term1]',
            'Definition 1.',
            '',
            '[Glossary:Term2]',
            'Definition 2. Paragraph 1.',
            '',
            'Definition 2. Paragraph 2.',
        ))
        content = """
            <ul class="contents">
            <li><a href="#term1">Term1</a></li>
            <li><a href="#term2">Term2</a></li>
            </ul>
            <div><span id="term1"></span></div>
            <div class="box box-1">
            <div class="box-title">Term1</div>
            <div class="paragraph">
            Definition 1.
            </div>
            </div>
            <div><span id="term2"></span></div>
            <div class="box box-2">
            <div class="box-title">Term2</div>
            <div class="paragraph">
            Definition 2. Paragraph 1.
            </div>
            <div class="paragraph">
            Definition 2. Paragraph 2.
            </div>
            </div>
        """
        writer = self._get_writer(ref=ref, skool='')
        writer.write_glossary()
        subs = {
            'header': 'Glossary',
            'body_class': 'Glossary',
            'content': content
        }
        self._assert_files_equal(join(REFERENCE_DIR, 'glossary.html'), subs)

    def test_write_glossary_with_custom_title_and_header_and_path(self):
        title = 'Terminology'
        header = 'Terms'
        path = 'terminology.html'
        ref = '\n'.join((
            '[Titles]',
            'Glossary={}',
            '[PageHeaders]',
            'Glossary={}',
            '[Paths]',
            'Glossary={}'
        )).format(title, header, path)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_glossary()
        self._assert_title_equals(path, title, header)

    def test_write_page(self):
        page_id = 'page'
        ref = '\n'.join((
            '[Page:{0}]',
            'JavaScript=test-html.js',
            '',
            '[PageContent:{0}]',
            '<b>This is the content of the custom page.</b>',
            '',
            '[PageHeaders]',
            '{0}=Custom page',
            '',
            '[Titles]',
            '{0}=Custom page'
        )).format(page_id)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        subs = {
            'title': 'Custom page',
            'header': 'Custom page',
            'path': '',
            'body_class': 'page',
            'js': 'test-html.js',
            'content': '<b>This is the content of the custom page.</b>\n'
        }
        self._assert_files_equal('{}.html'.format(page_id), subs)

    def test_write_page_using_custom_template(self):
        page_id = 'Custom'
        content = 'hello'
        ref = '\n'.join((
            '[Page:{0}]',
            'PageContent={1}',
            '[Template:{0}]',
            '<foo>{{content}}</foo>'
        )).format(page_id, content)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        path = '{}.html'.format(page_id)
        self.assertEqual('<foo>{}</foo>'.format(content), self.files[path])

    def test_write_page_using_footer_template(self):
        page_id = 'PageWithCustomFooter'
        content = 'hey'
        footer = '<footer>Notes</footer>'
        ref = '\n'.join((
            '[Page:{0}]',
            'PageContent={1}',
            '[Template:{0}]',
            '<bar>{{content}}</bar>',
            '{{t_footer}}',
            '[Template:footer]',
            footer
        )).format(page_id, content)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        path = '{}.html'.format(page_id)
        self.assertEqual('<bar>{}</bar>\n{}'.format(content, footer), self.files[path])

    def test_write_page_with_no_page_section(self):
        page_id = 'page'
        content = '<b>This is the content of the custom page.</b>'
        ref = '[PageContent:{}]\n{}'.format(page_id, content)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        subs = {
            'title': page_id,
            'header': page_id,
            'path': '',
            'body_class': page_id,
            'content': content + '\n'
        }
        self._assert_files_equal('{}.html'.format(page_id), subs)

    def test_write_bugs(self):
        ref = '\n'.join((
            '[Bug:b1:Showstopper]',
            'This bug is bad.',
            '',
            'Really bad.',
        ))
        content = """
            <ul class="contents">
            <li><a href="#b1">Showstopper</a></li>
            </ul>
            <div><span id="b1"></span></div>
            <div class="box box-1">
            <div class="box-title">Showstopper</div>
            <div class="paragraph">
            This bug is bad.
            </div>
            <div class="paragraph">
            Really bad.
            </div>
            </div>
        """
        writer = self._get_writer(ref=ref, skool='')
        writer.write_bugs()
        subs = {
            'header': 'Bugs',
            'body_class': 'Bugs',
            'content': content
        }
        self._assert_files_equal(join(REFERENCE_DIR, 'bugs.html'), subs)

    def test_write_bugs_with_custom_title_and_header_and_path(self):
        title = 'Things that go wrong'
        header = 'Misfeatures'
        path = 'ref/wrongness.html'
        ref = '\n'.join((
            '[Titles]',
            'Bugs={}',
            '[PageHeaders]',
            'Bugs={}',
            '[Paths]',
            'Bugs={}'
        )).format(title, header, path)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_bugs()
        self._assert_title_equals(path, title, header)

    def test_write_facts(self):
        ref = '\n'.join((
            '[Fact:f1:Interesting fact]',
            'Hello.',
            '',
            'Goodbye.',
            '',
            '[Fact:f2:Another interesting fact]',
            'Yes.',
        ))
        content = """
            <ul class="contents">
            <li><a href="#f1">Interesting fact</a></li>
            <li><a href="#f2">Another interesting fact</a></li>
            </ul>
            <div><span id="f1"></span></div>
            <div class="box box-1">
            <div class="box-title">Interesting fact</div>
            <div class="paragraph">
            Hello.
            </div>
            <div class="paragraph">
            Goodbye.
            </div>
            </div>
            <div><span id="f2"></span></div>
            <div class="box box-2">
            <div class="box-title">Another interesting fact</div>
            <div class="paragraph">
            Yes.
            </div>
            </div>
        """
        writer = self._get_writer(ref=ref, skool='')
        writer.write_facts()
        subs = {
            'header': 'Trivia',
            'body_class': 'Facts',
            'content': content
        }
        self._assert_files_equal(join(REFERENCE_DIR, 'facts.html'), subs)

    def test_write_facts_with_custom_title_and_header_and_path(self):
        title = 'Things that are true'
        header = 'Stuff you may not know'
        path = 'true_stuff.html'
        ref = '\n'.join((
            '[Titles]',
            'Facts={}',
            '[PageHeaders]',
            'Facts={}',
            '[Paths]',
            'Facts={}'
        )).format(title, header, path)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_facts()
        self._assert_title_equals(path, title, header)

    def test_write_pokes(self):
        html = """
            <ul class="contents">
            <li><a href="#p1">Infinite everything</a></li>
            </ul>
            <div><span id="p1"></span></div>
            <div class="box box-1">
            <div class="box-title">Infinite everything</div>
            <div class="paragraph">
            POKE 12345,0
            </div>
            </div>
        """
        ref = '[Poke:p1:Infinite everything]\nPOKE 12345,0'
        writer = self._get_writer(ref=ref, skool='')
        writer.write_pokes()
        subs = {
            'header': 'Pokes',
            'body_class': 'Pokes',
            'content': html
        }
        self._assert_files_equal(join(REFERENCE_DIR, 'pokes.html'), subs)

    def test_write_pokes_with_custom_title_and_header_and_path(self):
        title = 'Hacking the game'
        header = 'Cheats'
        path = 'qux/xyzzy/hacks.html'
        ref = '\n'.join((
            '[Titles]',
            'Pokes={}',
            '[PageHeaders]',
            'Pokes={}',
            '[Paths]',
            'Pokes={}'
        )).format(title, header, path)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_pokes()
        self._assert_title_equals(path, title, header)

    def test_write_graphic_glitches(self):
        ref = '[GraphicGlitch:g0:Wrong arms]\nHello.'
        content = """
            <ul class="contents">
            <li><a href="#g0">Wrong arms</a></li>
            </ul>
            <div><span id="g0"></span></div>
            <div class="box box-1">
            <div class="box-title">Wrong arms</div>
            <div class="paragraph">
            Hello.
            </div>
            </div>
        """
        writer = self._get_writer(ref=ref, skool='')
        writer.write_graphic_glitches()
        subs = {
            'header': 'Graphic glitches',
            'body_class': 'GraphicGlitches',
            'content': content
        }
        self._assert_files_equal(join(GRAPHICS_DIR, 'glitches.html'), subs)

    def test_write_graphic_glitches_with_custom_title_and_header_and_path(self):
        title = 'Bugs with the graphics'
        header = 'Graphical wrongness'
        path = 'cgi/graphic_bugs.html'
        ref = '\n'.join((
            '[Titles]',
            'GraphicGlitches={}',
            '[PageHeaders]',
            'GraphicGlitches={}',
            '[Paths]',
            'GraphicGlitches={}'
        )).format(title, header, path)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_graphic_glitches()
        self._assert_title_equals(path, title, header)

    def test_write_gsb_page(self):
        skool = '\n'.join((
            '; GSB entry 1',
            ';',
            '; Number of lives.',
            'g30000 DEFB 4',
            '',
            '; GSB entry 2',
            'g30001 DEFW 78',
            '',
            '; Not a game status buffer entry',
            't30003 DEFM "a"'
        ))
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page-0">Page</th>
            <th class="map-byte-0">Byte</th>
            <th>Address</th>
            <th class="map-length-1">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-0">117</td>
            <td class="map-byte-0">48</td>
            <td class="map-g"><span id="30000"></span><a href="../asm/30000.html">30000</a></td>
            <td class="map-length-1">1</td>
            <td class="map-g-desc">
            <div class="map-entry-title-11">GSB entry 1</div>
            <div class="map-entry-desc-1">
            <div class="paragraph">
            Number of lives.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-0">117</td>
            <td class="map-byte-0">49</td>
            <td class="map-g"><span id="30001"></span><a href="../asm/30001.html">30001</a></td>
            <td class="map-length-1">2</td>
            <td class="map-g-desc">
            <div class="map-entry-title-11">GSB entry 2</div>
            <div class="map-entry-desc-1">
            </div>
            </td>
            </tr>
            </table>
        """
        writer = self._get_writer(skool=skool)
        writer.write_map('GameStatusBuffer')
        subs = {
            'header': 'Game status buffer',
            'body_class': 'GameStatusBuffer',
            'content': content
        }
        self._assert_files_equal(join(BUFFERS_DIR, 'gbuffer.html'), subs)

    def test_write_gsb_page_with_includes(self):
        ref = '[Game]\nGameStatusBufferIncludes=30003,30004'
        skool = '\n'.join((
            '; GSB entry 1',
            ';',
            '; Number of lives.',
            'g30000 DEFB 4',
            '',
            '; GSB entry 2',
            'g30001 DEFW 78',
            '',
            '; Message ID',
            't30003 DEFB 0',
            '',
            '; Another message ID',
            't30004 DEFB 0',
            '',
            '; Not a game status buffer entry',
            'c30005 RET',
            '',
            'i30006',
        ))
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page-0">Page</th>
            <th class="map-byte-0">Byte</th>
            <th>Address</th>
            <th class="map-length-1">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-0">117</td>
            <td class="map-byte-0">48</td>
            <td class="map-g"><span id="30000"></span><a href="../asm/30000.html">30000</a></td>
            <td class="map-length-1">1</td>
            <td class="map-g-desc">
            <div class="map-entry-title-11">GSB entry 1</div>
            <div class="map-entry-desc-1">
            <div class="paragraph">
            Number of lives.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-0">117</td>
            <td class="map-byte-0">49</td>
            <td class="map-g"><span id="30001"></span><a href="../asm/30001.html">30001</a></td>
            <td class="map-length-1">2</td>
            <td class="map-g-desc">
            <div class="map-entry-title-11">GSB entry 2</div>
            <div class="map-entry-desc-1">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-0">117</td>
            <td class="map-byte-0">51</td>
            <td class="map-t"><span id="30003"></span><a href="../asm/30003.html">30003</a></td>
            <td class="map-length-1">1</td>
            <td class="map-t-desc">
            <div class="map-entry-title-11">Message ID</div>
            <div class="map-entry-desc-1">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-0">117</td>
            <td class="map-byte-0">52</td>
            <td class="map-t"><span id="30004"></span><a href="../asm/30004.html">30004</a></td>
            <td class="map-length-1">1</td>
            <td class="map-t-desc">
            <div class="map-entry-title-11">Another message ID</div>
            <div class="map-entry-desc-1">
            </div>
            </td>
            </tr>
            </table>
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_map('GameStatusBuffer')
        subs = {
            'header': 'Game status buffer',
            'body_class': 'GameStatusBuffer',
            'content': content
        }
        self._assert_files_equal(join(BUFFERS_DIR, 'gbuffer.html'), subs)

    def test_write_gsb_page_with_custom_title_and_header_and_path(self):
        title = 'Workspace'
        header = 'Status buffer'
        path = 'game/status_buffer.html'
        ref = '\n'.join((
            '[Titles]',
            'GameStatusBuffer={}',
            '[PageHeaders]',
            'GameStatusBuffer={}',
            '[Paths]',
            'GameStatusBuffer={}'
        )).format(title, header, path)
        writer = self._get_writer(ref=ref, skool='g32768 DEFB 0')
        writer.write_map('GameStatusBuffer')
        self._assert_title_equals(path, title, header)

    def test_page_content(self):
        ref = '[Page:ExistingPage]\nContent=asm/32768.html'
        writer = self._get_writer(ref=ref)
        self.assertNotIn('ExistingPage', writer.page_ids)
        self.assertIn('ExistingPage', writer.paths)
        self.assertTrue(writer.paths['ExistingPage'], 'asm/32768.html')

    def test_get_udg_addresses(self):
        writer = self._get_writer(snapshot=())
        addr_specs = [
            (0, 1, [0]),
            ('1', 1, [1]),
            ('2x3', 1, [2] * 3),
            ('0-3', 1, [0, 1, 2, 3]),
            ('0-2x3', 1, [0, 1, 2] * 3),
            ('0-6-2', 1, [0, 2, 4, 6]),
            ('0-6-3x2', 1, [0, 3, 6] * 2),
            ('0-49-1-16', 2, [0, 1, 16, 17, 32, 33, 48, 49]),
            ('0-528-8-256x4', 3, [0, 8, 16, 256, 264, 272, 512, 520, 528] * 4)
        ]
        for addr_spec, width, exp_addresses in addr_specs:
            self.assertEqual(writer._get_udg_addresses(addr_spec, width), exp_addresses)

    def test_get_snapshot_name(self):
        writer = self._get_writer()
        names = ['snapshot1', 'next', 'final']
        for name in names:
            writer.push_snapshot(name)
        while names:
            self.assertEqual(writer.get_snapshot_name(), names.pop())
            writer.pop_snapshot()

    def test_unwritten_maps(self):
        ref = '[MemoryMap:UnusedMap]\nWrite=0'
        skool = '\n'.join((
            '; Routine',
            'c40000 RET',
            '',
            '; Data',
            'b40001 DEFB 0',
            '',
            '; Unused',
            'u40002 DEFB 0',
        ))
        writer = self._get_writer(ref=ref, skool=skool)
        self.assertIn('MemoryMap', writer.main_memory_maps)
        self.assertIn('RoutinesMap', writer.main_memory_maps)
        self.assertIn('DataMap', writer.main_memory_maps)
        self.assertNotIn('MessagesMap', writer.main_memory_maps) # No entries
        self.assertNotIn('UnusedMap', writer.main_memory_maps)   # Write=0

    def test_format_registers_with_prefixes(self):
        skool = '\n'.join((
            '; Routine at 24576',
            ';',
            '; .',
            ';',
            ';  Input:A Some value',
            ';        B Some other value',
            '; Output:D The result',
            ';        E Result flags',
            'c24576 RET ; Done'
        ))
        writer = self._get_writer(skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">24576: Routine at 24576</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="4">
            <div class="details">
            </div>
            <table class="input-1">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            <tr>
            <td class="register">A</td>
            <td class="register-desc">Some value</td>
            </tr>
            <tr>
            <td class="register">B</td>
            <td class="register-desc">Some other value</td>
            </tr>
            </table>
            <table class="output-1">
            <tr class="asm-output-header">
            <th colspan="2">Output</th>
            </tr>
            <tr>
            <td class="register">D</td>
            <td class="register-desc">The result</td>
            </tr>
            <tr>
            <td class="register">E</td>
            <td class="register-desc">Result flags</td>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-2"><span id="24576"></span>24576</td>
            <td class="instruction">RET</td>
            <td class="comment-11" rowspan="1">Done</td>
            </tr>
            </table>
        """
        subs = {
            'title': 'Routine at 24576',
            'body_class': 'Asm-c',
            'header': 'Routines',
            'up': 24576,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '24576.html'), subs)

    def test_format_page_with_single_global_js(self):
        global_js = 'js/global.js'
        page_id = 'Custom'
        ref = '\n'.join((
            '[Game]',
            'JavaScript={0}',
            '[Page:{1}]',
            'Path=',
            '[Template:{1}]',
            '{{m_javascript}}'
        )).format(global_js, page_id)
        writer = self._get_writer(ref=ref)
        cwd = 'subdir/subdir2'
        page = writer.format_page(page_id, cwd, {}).split('\n')
        js_path = writer.relpath(cwd, '{}/{}'.format(writer.paths['JavaScriptPath'], basename(global_js)))
        self.assertEqual(page[0], '<script type="text/javascript" src="{}"></script>'.format(js_path))

    def test_format_page_with_multiple_global_js(self):
        js_files = ['js/global1.js', 'js.global2.js']
        global_js = ';'.join(js_files)
        page_id = 'Custom'
        ref = '\n'.join((
            '[Game]',
            'JavaScript={0}',
            '[Page:{1}]',
            'Path=',
            '[Template:{1}]',
            '{{m_javascript}}'
        )).format(global_js, page_id)
        writer = self._get_writer(ref=ref)
        cwd = 'subdir/subdir2'
        page = writer.format_page(page_id, cwd, {}).split('\n')
        js_paths = [writer.relpath(cwd, '{}/{}'.format(writer.paths['JavaScriptPath'], basename(js))) for js in js_files]
        self.assertEqual(page[0], '<script type="text/javascript" src="{}"></script>'.format(js_paths[0]))
        self.assertEqual(page[1], '<script type="text/javascript" src="{}"></script>'.format(js_paths[1]))

    def test_format_page_with_single_local_js(self):
        page_id = 'Custom'
        ref = '\n'.join((
            '[Page:{0}]',
            'Path=',
            '[Template:{0}]',
            '{{m_javascript}}'
        )).format(page_id)
        writer = self._get_writer(ref=ref)
        cwd = 'subdir/subdir2'
        js = 'js/script.js'
        page = writer.format_page(page_id, cwd, {}, js=js).split('\n')
        js_path = writer.relpath(cwd, '{}/{}'.format(writer.paths['JavaScriptPath'], basename(js)))
        self.assertEqual(page[0], '<script type="text/javascript" src="{}"></script>'.format(js_path))

    def test_format_page_with_multiple_local_js(self):
        page_id = 'Custom'
        ref = '\n'.join((
            '[Page:{0}]',
            'Path=',
            '[Template:{0}]',
            '{{m_javascript}}'
        )).format(page_id)
        writer = self._get_writer(ref=ref)
        cwd = 'subdir'
        js_files = ['js/script1.js', 'js/script2.js']
        js = ';'.join(js_files)
        page = writer.format_page(page_id, cwd, {}, js=js).split('\n')
        js_paths = [writer.relpath(cwd, '{}/{}'.format(writer.paths['JavaScriptPath'], basename(js))) for js in js_files]
        self.assertEqual(page[0], '<script type="text/javascript" src="{}"></script>'.format(js_paths[0]))
        self.assertEqual(page[1], '<script type="text/javascript" src="{}"></script>'.format(js_paths[1]))

    def test_format_page_with_local_and_global_js(self):
        global_js_files = ['js/global1.js', 'js.global2.js']
        global_js = ';'.join(global_js_files)
        local_js_files = ['js/local1.js', 'js/local2.js']
        local_js = ';'.join(local_js_files)
        page_id = 'Custom'
        ref = '\n'.join((
            '[Game]',
            'JavaScript={0}',
            '[Page:{1}]',
            'Path=',
            '[Template:{1}]',
            '{{m_javascript}}'
        )).format(global_js, page_id)
        writer = self._get_writer(ref=ref)
        cwd = 'subdir/subdir2'
        page = writer.format_page(page_id, cwd, {}, js=local_js).split('\n')
        for i, js in enumerate(global_js_files + local_js_files):
            js_path = writer.relpath(cwd, '{}/{}'.format(writer.paths['JavaScriptPath'], basename(js)))
            self.assertEqual(page[i], '<script type="text/javascript" src="{}"></script>'.format(js_path))

    def test_format_page_with_single_css(self):
        css = 'css/game.css'
        page_id = 'Custom'
        ref = '\n'.join((
            '[Game]',
            'StyleSheet={0}',
            '[Page:{1}]',
            'Path=',
            '[Template:{1}]',
            '{{m_stylesheet}}'
        )).format(css, page_id)
        writer = self._get_writer(ref=ref)
        cwd = ''
        page = writer.format_page(page_id, cwd, {}).split('\n')
        css_path = writer.relpath(cwd, '{}/{}'.format(writer.paths['StyleSheetPath'], basename(css)))
        self.assertEqual(page[0], '<link rel="stylesheet" type="text/css" href="{}" />'.format(css_path))

    def test_format_page_with_multiple_css(self):
        css_files = ['css/game.css', 'css/foo.css']
        page_id = 'Custom'
        ref = '\n'.join((
            '[Game]',
            'StyleSheet={0}',
            '[Page:{1}]',
            'Path=',
            '[Template:{1}]',
            '{{m_stylesheet}}'
        )).format(';'.join(css_files), page_id)
        writer = self._get_writer(ref=ref)
        cwd = ''
        page = writer.format_page(page_id, cwd, {}).split('\n')
        css_paths = [writer.relpath(cwd, '{}/{}'.format(writer.paths['StyleSheetPath'], basename(css))) for css in css_files]
        self.assertEqual(page[0], '<link rel="stylesheet" type="text/css" href="{}" />'.format(css_paths[0]))
        self.assertEqual(page[1], '<link rel="stylesheet" type="text/css" href="{}" />'.format(css_paths[1]))

    def test_write_page_no_game_name(self):
        page_id = 'Custom'
        path = '{}.html'.format(page_id)
        ref = '\n'.join((
            '[Page:{0}]',
            '[Template:{0}]',
            '{{Game[Logo]}}'
        )).format(page_id)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        game_name = self.skoolfile[:-6]
        page = self._read_file(path, True)
        self.assertEqual(page[0], game_name)

    def test_write_page_with_game_name(self):
        game_name = 'Some game'
        page_id = 'Custom'
        cwd = 'subdir'
        path = '{}/custom.html'.format(cwd)
        ref = '\n'.join((
            '[Game]',
            'Game={0}',
            '[Page:{1}]',
            '[Paths]',
            '{1}={2}',
            '[Template:{1}]',
            '{{Game[Logo]}}'
        )).format(game_name, page_id, path)
        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        page = self._read_file(path, True)
        self.assertEqual(page[0], game_name)

    def test_write_page_with_nonexistent_logo_image(self):
        page_id = 'Custom'
        cwd = 'subdir'
        path = '{}/custom.html'.format(cwd)
        ref = '\n'.join((
            '[Game]',
            'LogoImage=images/nonexistent.png',
            '[Page:{0}]',
            '[Paths]',
            '{0}={1}',
            '[Template:{0}]',
            '{{Game[Logo]}}'
        )).format(page_id, path)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        game_name = self.skoolfile[:-6]
        page = self._read_file(path, True)
        self.assertEqual(page[0], game_name)

    def test_write_page_with_logo_image(self):
        logo_image_fname = 'logo.png'
        page_id = 'Custom'
        cwd = 'subdir/subdir2'
        path = '{}/custom.html'.format(cwd)
        ref = '\n'.join((
            '[Game]',
            'LogoImage={0}',
            '[Page:{1}]',
            '[Paths]',
            '{1}={2}',
            '[Template:{1}]',
            '{{Game[Logo]}}'
        )).format(logo_image_fname, page_id, path)
        writer = self._get_writer(ref=ref, skool='')
        logo_image = self.write_bin_file(path=join(writer.file_info.odir, logo_image_fname))
        writer.write_page(page_id)
        logo = writer.relpath(cwd, logo_image_fname)
        game_name = self.skoolfile[:-6]
        page = self._read_file(path, True)
        self.assertEqual(page[0], '<img alt="{}" src="{}" />'.format(game_name, logo))

    def test_format_page_with_logo(self):
        logo = 'ABC #UDG30000 123'
        page_id = 'custom'
        ref = '\n'.join((
            '[Game]',
            'Logo={0}',
            '[Page:{1}]',
            '[Template:{1}]',
            '{{Game[Logo]}}'
        )).format(logo, page_id)
        writer = self._get_writer(ref=ref, skool='')
        cwd = ''
        writer.write_page(page_id)
        logo_value = writer.expand(logo, cwd)
        page = self._read_file('{}.html'.format(page_id), True)
        self.assertEqual(page[0], logo_value)

class UdgTest(SkoolKitTestCase):
    def test_flip(self):
        udg = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg.flip(0)
        self.assertEqual(udg.data, [1, 2, 4, 8, 16, 32, 64, 128])
        self.assertEqual(udg.mask, [1, 2, 4, 8, 16, 32, 64, 128])

        udg = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg.flip(1)
        self.assertEqual(udg.data, [128, 64, 32, 16, 8, 4, 2, 1])
        self.assertEqual(udg.mask, [128, 64, 32, 16, 8, 4, 2, 1])

        udg = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [2, 4, 6, 8, 10, 12, 14, 16])
        udg.flip(2)
        self.assertEqual(udg.data, [8, 7, 6, 5, 4, 3, 2, 1])
        self.assertEqual(udg.mask, [16, 14, 12, 10, 8, 6, 4, 2])

        udg = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1])
        udg.flip(3)
        self.assertEqual(udg.data, [16, 224, 96, 160, 32, 192, 64, 128])
        self.assertEqual(udg.mask, [128, 64, 192, 32, 160, 96, 224, 16])

    def test_rotate(self):
        udg = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg.rotate(0)
        self.assertEqual(udg.data, [1, 2, 4, 8, 16, 32, 64, 128])
        self.assertEqual(udg.mask, [1, 2, 4, 8, 16, 32, 64, 128])

        udg = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg.rotate(1)
        self.assertEqual(udg.data, [128, 64, 32, 16, 8, 4, 2, 1])
        self.assertEqual(udg.mask, [128, 64, 32, 16, 8, 4, 2, 1])

        udg = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1])
        udg.rotate(2)
        self.assertEqual(udg.data, [16, 224, 96, 160, 32, 192, 64, 128])
        self.assertEqual(udg.mask, [128, 64, 192, 32, 160, 96, 224, 16])

        udg = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [255, 254, 253, 252, 251, 250, 249, 248])
        udg.rotate(3)
        self.assertEqual(udg.data, [170, 102, 30, 1, 0, 0, 0, 0])
        self.assertEqual(udg.mask, [170, 204, 240, 255, 255, 255, 255, 255])

    def test_copy(self):
        udg = Udg(23, [1] * 8)
        replica = udg.copy()
        self.assertEqual(udg.attr, replica.attr)
        self.assertEqual(udg.data, replica.data)
        self.assertEqual(udg.mask, replica.mask)
        self.assertFalse(udg.data is replica.data)

        udg = Udg(47, [2] * 8, [3] * 8)
        replica = udg.copy()
        self.assertEqual(udg.attr, replica.attr)
        self.assertEqual(udg.data, replica.data)
        self.assertEqual(udg.mask, replica.mask)
        self.assertFalse(udg.data is replica.data)
        self.assertFalse(udg.mask is replica.mask)

    def test_eq(self):
        udg1 = Udg(1, [7] * 8)
        udg2 = Udg(1, [7] * 8)
        udg3 = Udg(2, [7] * 8)
        self.assertTrue(udg1 == udg2)
        self.assertFalse(udg1 == udg3)
        self.assertFalse(udg1 == 1)

    def test_repr(self):
        udg1 = Udg(1, [2, 3, 4, 5, 6, 7, 8, 9])
        self.assertEqual(repr(udg1), 'Udg(1, [2, 3, 4, 5, 6, 7, 8, 9])')

        udg2 = Udg(1, [2] * 8, [3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(repr(udg2), 'Udg(1, [2, 2, 2, 2, 2, 2, 2, 2], [3, 4, 5, 6, 7, 8, 9, 10])')

if __name__ == '__main__':
    unittest.main()
