import html
from io import StringIO
from os.path import basename, isdir, isfile
from posixpath import join
from textwrap import dedent
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase, Stream
from macrotest import CommonSkoolMacroTest, nest_macros
from skoolkit import BASE_10, BASE_16, VERSION, SkoolKitError, SkoolParsingError, components, defaults, skoolhtml
from skoolkit.graphics import Udg, Frame
from skoolkit.image import ImageWriter
from skoolkit.skoolmacro import UnsupportedMacroError
from skoolkit.skoolhtml import HtmlWriter, FileInfo
from skoolkit.skoolparser import SkoolParser, CASE_LOWER, CASE_UPPER
from skoolkit.refparser import RefParser

GAMEDIR = 'test'
ASMDIR = 'asm'
MAPS_DIR = 'maps'
GRAPHICS_DIR = 'graphics'
BUFFERS_DIR = 'buffers'
REFERENCE_DIR = 'reference'
IMAGEDIR = 'images'
FONTDIR = 'images/font'
SCRDIR = 'images/scr'
UDGDIR = 'images/udgs'

REF_SECTIONS = {
    'Page_Bugs': defaults.get_section('Page:Bugs'),
    'Page_Facts': defaults.get_section('Page:Facts'),
    'Page_Pokes': defaults.get_section('Page:Pokes'),
    'PageHeaders': defaults.get_section('PageHeaders'),
    'Template_img': defaults.get_section('Template:img'),
    'Template_link': defaults.get_section('Template:link'),
    'Template_list': defaults.get_section('Template:list'),
    'Template_reg': defaults.get_section('Template:reg'),
    'Template_section': defaults.get_section('Template:section'),
    'Template_table': defaults.get_section('Template:table'),
}

MINIMAL_REF_FILE = """
[Game]
Address=
AddressAnchor={{address}}
AsmSinglePage=0
Created=
Length={{size}}
LinkInternalOperands=0
LinkOperands=CALL,DEFW,DJNZ,JP,JR
[Paths]
CodePath={ASMDIR}
CodeFiles={{address}}.html
UDGFilename=udg{{addr}}_{{attr}}x{{scale}}
""".format(**locals())

METHOD_MINIMAL_REF_FILE = """
[Game]
Address=
AddressAnchor={{address}}
AsmSinglePage=0
Created=
Length={{size}}
LinkInternalOperands=0
LinkOperands=CALL,DEFW,DJNZ,JP,JR
[Paths]
CodePath={ASMDIR}
ImagePath={IMAGEDIR}
ScreenshotImagePath={SCRDIR}
UDGImagePath={UDGDIR}
UDGFilename=udg{{addr}}_{{attr}}x{{scale}}
CodeFiles={{address}}.html
{REF_SECTIONS[Template_img]}
""".format(**locals())

SKOOL_MACRO_MINIMAL_REF_FILE = """
[Game]
Address=
AddressAnchor={{address}}
AsmSinglePage=0
Created=
Length={{size}}
LinkInternalOperands=0
LinkOperands=CALL,DEFW,DJNZ,JP,JR
StyleSheet=skoolkit.css
{REF_SECTIONS[Page_Bugs]}
{REF_SECTIONS[Page_Facts]}
{REF_SECTIONS[Page_Pokes]}
{REF_SECTIONS[PageHeaders]}
[Paths]
CodePath={ASMDIR}
FontImagePath={{ImagePath}}/font
ImagePath=images
ScreenshotImagePath={{ImagePath}}/scr
UDGImagePath={{ImagePath}}/udgs
UDGFilename=udg{{addr}}_{{attr}}x{{scale}}
AsmSinglePage=asm.html
Bugs={REFERENCE_DIR}/bugs.html
CodeFiles={{address}}.html
Facts={REFERENCE_DIR}/facts.html
Pokes={REFERENCE_DIR}/pokes.html
{REF_SECTIONS[Template_img]}
{REF_SECTIONS[Template_link]}
{REF_SECTIONS[Template_list]}
{REF_SECTIONS[Template_reg]}
{REF_SECTIONS[Template_section]}
{REF_SECTIONS[Template_table]}
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
<td class="page-header">{header[1]}</td>
</tr>
</table>"""

PREFIX_HEADER = """<!DOCTYPE html>
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
<td class="page-header">{header[0]}</td>
<td class="logo"><a href="{path}index.html">{logo}</a></td>
<td class="page-header">{header[1]}</td>
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
<td class="page-header">{header[0]}</td>
<td class="logo">{logo}</td>
<td class="page-header">{header[1]}</td>
</tr>
</table>"""

BARE_FOOTER = """<footer>
<div class="release"></div>
<div class="copyright"></div>
<div class="created">Created using <a href="https://skoolkit.ca">SkoolKit</a> {}.</div>
</footer>
</body>
</html>""".format(VERSION)

PREV_UP_NEXT = """<table class="asm-navigation">
<tr>
<td class="prev">
{prev_link}
</td>
<td class="up">{up_link}</td>
<td class="next">
{next_link}
</td>
</tr>
</table>"""

ERROR_PREFIX = 'Error while parsing #{0} macro'

class MockSkoolParser:
    def __init__(self, snapshot, base, case):
        self.snapshot = snapshot
        self.entries = {}
        self.memory_map = ()
        self.base = base
        self.case = case
        self.skoolfile = ''
        self.fields = {'asm': 0, 'base': base, 'case': case, 'fix': 0, 'html': 1, 'vars': {}}
        self.expands = ()

    def get_entry(self, address):
        return self.entries.get(address)

    def get_instruction(self, address):
        return None

    def get_container(self, address, code_id):
        return None

    def make_replacements(self, item):
        pass

class MockFileInfo:
    def __init__(self):
        self.fname = None
        self.mode = None
        self.files = {}

    def open_file(self, *names, mode='w'):
        self.fname = join(*names)
        self.mode = mode
        self.files[self.fname] = Stream('b' in mode)
        return self.files[self.fname]

    def add_image(self, image_path):
        self.files[image_path] = self.files[image_path].getvalue()

    def need_image(self, image_path):
        return True

class TestImageWriter(ImageWriter):
    def write_image(self, frames, img_file):
        self.frames = frames
        if isinstance(frames, list):
            frame1 = frames[0]
            self.udg_array = frame1.udgs
            self.scale = frame1.scale
            self.mask = frame1.mask
            self.x = frame1.x
            self.y = frame1.y
            self.width = frame1.width
            self.height = frame1.height
            self.tindex = frame1.tindex
            self.alpha = frame1.alpha
        img_file.write(b'a')

class HtmlWriterTestCase(SkoolKitTestCase):
    def setUp(self):
        super().setUp()
        self.force_odir = None

    def _mock_write_file(self, fname, contents):
        self.files[fname] = contents

    def _get_writer(self, ref=None, snapshot=(), case=0, base=0, skool=None,
                    create_labels=False, asm_labels=False, variables=(),
                    mock_file_info=False, mock_write_file=True,
                    mock_image_writer=True, warn=False):
        self.skoolfile = None
        ref_parser = RefParser()
        if ref is not None:
            ref_parser.parse(StringIO(dedent(ref).strip()))
        if skool is None:
            skool_parser = MockSkoolParser(snapshot, base, case)
        else:
            self.skoolfile = self.write_text_file(dedent(skool).strip(), suffix='.skool')
            skool_parser = SkoolParser(self.skoolfile, case=case, base=base, html=True,
                                       create_labels=create_labels, asm_labels=asm_labels,
                                       variables=variables)
        self.odir = self.force_odir or self.make_directory()
        if mock_file_info:
            file_info = MockFileInfo()
        else:
            file_info = FileInfo(self.odir, GAMEDIR, False)
        if mock_image_writer:
            patch.object(skoolhtml, 'get_image_writer', TestImageWriter).start()
        self.addCleanup(patch.stopall)
        writer = HtmlWriter(skool_parser, ref_parser, file_info)
        if mock_write_file:
            writer.write_file = self._mock_write_file
        writer.skoolkit['page_id'] = 'None'
        return writer

    def _check_image(self, writer, udg_array, scale=2, mask=0, tindex=0, alpha=-1, x=0, y=0, width=None, height=None, path=None):
        self.assertEqual(writer.file_info.fname, path)
        if width is None:
            width = 8 * len(udg_array[0]) * scale
        if height is None:
            height = 8 * len(udg_array) * scale
        image_writer = writer.image_writer
        self.assertEqual(image_writer.scale, scale)
        self.assertEqual(image_writer.mask, mask)
        self.assertEqual(image_writer.tindex, tindex)
        self.assertEqual(image_writer.alpha, alpha)
        self.assertEqual(image_writer.x, x)
        self.assertEqual(image_writer.y, y)
        self.assertEqual(image_writer.width, width)
        self.assertEqual(image_writer.height, height)
        self.assertEqual(len(image_writer.udg_array), len(udg_array))
        self._compare_udgs(image_writer.udg_array, udg_array)

    def _compare_udgs(self, udg_array, exp_udg_array):
        for i, row in enumerate(udg_array):
            exp_row = exp_udg_array[i]
            self.assertEqual(len(row), len(exp_row))
            for j, udg in enumerate(row):
                exp_udg = exp_row[j]
                self.assertEqual(udg.attr, exp_udg.attr)
                self.assertEqual(udg.data, exp_udg.data)
                self.assertEqual(udg.mask, exp_udg.mask)

class HtmlWriterTest(HtmlWriterTestCase):
    def _test_unexpandable_macros_in_ref_file_section(self, section, *exceptions, params=None):
        if not params:
            params = []
            for line in defaults.get_section(section).split('\n')[1:]:
                if line.startswith(';'):
                    line = line[1:].lstrip()
                params.append(line.split('=', 1)[0])
            for param in exceptions:
                params.remove(param)
        for param in params:
            ref = '[{}]\n{}=#R32768'.format(section, param)
            exp_error = '^Failed to expand macros in {} parameter: #R32768$'.format(param)
            with self.assertRaisesRegex(SkoolKitError, exp_error, msg='{}:{}'.format(section, param)):
                self._get_writer(ref=ref)

    def test_OtherCode_Source_parameter(self):
        ref = """
            [OtherCode:load]
            [OtherCode:save]
            Source=save.sks
        """
        writer = self._get_writer(ref=ref)
        self.assertEqual(len(writer.other_code), 2)
        i = 0
        for exp_code_id, exp_source in (('load', 'load.skool'), ('save', 'save.sks')):
            code_id, code = writer.other_code[i]
            self.assertEqual(code_id, exp_code_id)
            self.assertIn('Source', code)
            self.assertEqual(code['Source'], exp_source)
            i += 1

    def test_replace_directive(self):
        ref = """
            [Test]
            Hello @all.
            Goodbye @all.
        """
        skool = """
            @replace=/@all/everyone
            c32768 RET
        """
        writer = self._get_writer(ref=ref, skool=skool)
        section = writer.get_section('Test', lines=True)
        self.assertEqual(['Hello everyone.', 'Goodbye everyone.'], section)

    def test_replace_directive_on_entry_section_name(self):
        ref = """
            [Test#foo]
            Work#foo.
        """
        skool = """
            @replace=/#foo/ing
            c32768 RET
        """
        writer = self._get_writer(ref=ref, skool=skool)
        section = writer.get_section('Testing', lines=True)
        self.assertEqual(['Working.'], section)

    def test_non_empty_box_page_is_registered(self):
        ref = """
            [Page:Foo]
            SectionPrefix=Foo
            [Foo:foo:Foo]
            Hello.
        """
        writer = self._get_writer(ref=ref)
        self.assertIn('Foo', writer.get_page_ids())

    def test_empty_box_page_is_not_registered(self):
        ref = """
            [Page:Bar]
            SectionPrefix=Bar
        """
        writer = self._get_writer(ref=ref)
        self.assertNotIn('Bar', writer.get_page_ids())

    def test_unexpandable_macros_in_Game_section(self):
        self._test_unexpandable_macros_in_ref_file_section('Game', 'Logo')

    def test_unexpandable_macros_in_MemoryMap_section(self):
        self._test_unexpandable_macros_in_ref_file_section('MemoryMap:MemoryMap', 'Intro')

    def test_unexpandable_macros_in_Page_section(self):
        params = ('Content', 'JavaScript', 'SectionPrefix', 'SectionType')
        self._test_unexpandable_macros_in_ref_file_section('Page:MyPage', params=params)

    def test_unexpandable_macros_in_Paths_section(self):
        self._test_unexpandable_macros_in_ref_file_section('Paths')

class MethodTest(HtmlWriterTestCase):
    def setUp(self):
        HtmlWriterTestCase.setUp(self)
        patch.object(skoolhtml, 'REF_FILE', METHOD_MINIMAL_REF_FILE).start()
        self.addCleanup(patch.stopall)
        self.files = {}

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

    def _test_format_template(self, ref, tname, fields, exp_output):
        writer = self._get_writer(ref=ref)
        output = writer.format_template(tname, fields)
        self.assertEqual(dedent(exp_output).strip(), output)

    def test_colour_parsing(self):
        # Valid colours
        exp_colours = (
            (3, 'RED', '#C40000', (196, 0, 0)),
            (8, 'WHITE', '#cde', (204, 221, 238)),
            (7, 'YELLOW', '198,197,0', (198, 197, 0))
        )
        colours = ['[Colours]']
        colours.extend(['{}={}'.format(name, spec) for index, name, spec, rgb in exp_colours])
        writer = self._get_writer(ref='\n'.join(colours))
        for index, name, spec, rgb in exp_colours:
            self.assertEqual(writer.image_writer.colours[index], rgb)

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

    def test_ref_parsing(self):
        ref = """
            [Links]
            Bugs=[Bugs] (program errors)
            Pokes=[Pokes [with square brackets in the link text]] (cheats)

            [MemoryMap:TestMap]
            EntryTypes=w
        """
        writer = self._get_writer(ref=ref, skool='w30000 DEFW 0')

        # [Links]
        self.assertEqual(writer.links['Bugs'], ('Bugs', ' (program errors)'))
        self.assertEqual(writer.links['Pokes'], ('Pokes [with square brackets in the link text]', ' (cheats)'))

        # [MemoryMap:*]
        self.assertIn('TestMap', writer.main_memory_maps)
        self.assertIn('TestMap', writer.memory_maps)
        self.assertEqual(writer.memory_maps['TestMap'], {'EntryTypes': 'w', 'Includes': []})

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

    def test_get_section_trim_lines(self):
        ref = """
            [Foo]
              Line 1.
                Line 2.
        """
        writer = self._get_writer(ref=ref)
        section = writer.get_section('Foo')
        self.assertEqual(section, 'Line 1.\nLine 2.')

    def test_get_section_no_trim_lines(self):
        ref = """
            [Foo]
              Line 1.
                Line 2.
        """
        writer = self._get_writer(ref=ref)
        section = writer.get_section('Foo', trim=False)
        self.assertEqual(section, '  Line 1.\n    Line 2.')

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

    def test_handle_image(self):
        writer = self._get_writer(mock_file_info=True)
        image_writer = writer.image_writer
        file_info = writer.file_info
        udgs = [[Udg(0, (0,) * 8)]]
        frame = Frame(udgs)
        fname = 'test.png'
        writer.handle_image(frame, fname)
        self.assertEqual(file_info.fname, '{}/{}'.format(IMAGEDIR, fname))
        self.assertEqual(file_info.mode, 'wb')
        self.assertEqual(image_writer.udg_array, udgs)
        self.assertEqual(image_writer.scale, 1)
        self.assertEqual(image_writer.mask, 0)
        self.assertEqual(image_writer.x, 0)
        self.assertEqual(image_writer.y, 0)
        self.assertEqual(image_writer.width, 8)
        self.assertEqual(image_writer.height, 8)

    def test_handle_image_animated(self):
        writer = self._get_writer(mock_file_info=True)
        image_writer = writer.image_writer
        file_info = writer.file_info
        udg1 = Udg(1, (1,) * 8)
        udg2 = Udg(2, (2,) * 8)
        frames = [Frame([[udg1]]), Frame([[udg2]])]
        fname = 'test_animated.png'
        writer.handle_image(frames, fname)
        self.assertEqual(file_info.fname, '{}/{}'.format(IMAGEDIR, fname))
        self.assertEqual(file_info.mode, 'wb')
        self.assertEqual(image_writer.frames, frames)

    def test_handle_image_with_paths(self):
        writer = self._get_writer(mock_file_info=True)
        file_info = writer.file_info
        udgs = [[Udg(0, (0,) * 8)]]
        frame = Frame(udgs)

        writer.handle_image(frame, 'img')
        self.assertEqual(file_info.fname, '{}/img.png'.format(writer.paths['ImagePath']))

        writer.handle_image(frame, '/pics/foo.png')
        self.assertEqual(file_info.fname, 'pics/foo.png')

        path_id = 'ScreenshotImagePath'
        writer.handle_image(frame, 'img.png', path_id=path_id)
        self.assertEqual(file_info.fname, '{}/img.png'.format(writer.paths[path_id]))

        path_id = 'UnknownImagePath'
        fname = 'img.png'
        with self.assertRaisesRegex(SkoolKitError, "Unknown path ID '{}' for image file '{}'".format(path_id, fname)):
            writer.handle_image(frame, fname, path_id=path_id)

    def test_handle_image_detects_animation(self):
        writer = self._get_writer(mock_file_info=True)
        file_info = writer.file_info
        udg_path = writer.paths['ImagePath']

        # One frame, no flash
        udgs = [[Udg(1, (0,) * 8)]]
        writer.handle_image(Frame(udgs), 'img')
        self.assertEqual(file_info.fname, '{}/img.png'.format(udg_path))

        # One frame, flashing, same INK and PAPER
        udgs = [[Udg(128, (0,) * 8)]]
        writer.handle_image(Frame(udgs), 'img')
        self.assertEqual(file_info.fname, '{}/img.png'.format(udg_path))

        # One frame, flashing, different INK and PAPER
        udgs = [[Udg(129, (0,) * 8)]]
        writer.handle_image(Frame(udgs), 'img')
        self.assertEqual(file_info.fname, '{}/img.png'.format(udg_path))

        # One frame, flashing, fully cropped
        udgs = [[Udg(129, (0,) * 8), Udg(0, (0,) * 8)]]
        writer.handle_image(Frame(udgs, 1, 0, 8), 'img')
        self.assertEqual(file_info.fname, '{}/img.png'.format(udg_path))

        # One frame, flashing, partly cropped
        udgs = [[Udg(129, (0,) * 8), Udg(0, (0,) * 8)]]
        writer.handle_image(Frame(udgs, 1, 0, 4), 'img')
        self.assertEqual(file_info.fname, '{}/img.png'.format(udg_path))

        # One frame, FLASH bit set, completely transparent (no flash rect)
        udgs = [[Udg(129, (0,) * 8, (255,) * 8)]]
        writer.handle_image(Frame(udgs, 1, 1), 'img')
        self.assertEqual(file_info.fname, '{}/img.png'.format(udg_path))

        # Two frames
        udgs = [[Udg(0, (0,) * 8)]]
        writer.handle_image([Frame(udgs)] * 2, 'img')
        self.assertEqual(file_info.fname, '{}/img.png'.format(udg_path))

    def test_init_page_for_disassembly_page(self):
        exp_skoolkit = {
            'include': 'asm',
            'index_href': '../index.html',
            'javascripts': [],
            'page_header': ['', 'Routine at 32768'],
            'page_id': 'Asm-c',
            'path': 'asm/32768.html',
            'stylesheets': [{'href': '../style.css'}],
            'title': 'Routine at 32768'
        }
        def mock_init_page(skoolkit, game):
            self.assertEqual(exp_skoolkit, skoolkit)
        ref = """
            [Game]
            Bytes=
            StyleSheet=
            [Paths]
            GameIndex=index.html
            MemoryMap=all.html
            StyleSheetPath=style.css
            [Template:Layout]
            Nothing to see here!
            [Titles]
            Asm-c=Routine at {entry[address]}
        """
        writer = self._get_writer(skool='c32768 RET', ref=ref, mock_file_info=True)
        writer.init_page = mock_init_page
        writer.write_asm_entries()

    def test_format_template(self):
        writer = self._get_writer(ref='[Template:foo]\n{bar}')
        output = writer.format_template('foo', {'bar': 'baz'})
        self.assertEqual(output, 'baz')

    def test_format_template_page_specific_template_exists(self):
        page_id = 'CustomPage'
        ref = """
            [Template:{}-foo]
            !!{{bar}}!!
            [Template:foo]
            {{bar}}
        """.format(page_id)
        writer = self._get_writer(ref=ref)
        writer.skoolkit['page_id'] = page_id
        output = writer.format_template('foo', {'bar': 'baz'})
        self.assertEqual(output, '!!baz!!')

    def test_format_template_unknown_field(self):
        writer = self._get_writer(ref='[Template:foo]\n{bar}')
        with self.assertRaisesRegex(SkoolKitError, "^Unknown field 'bar' in foo template$"):
            writer.format_template('foo', {'notbar': 'baz'})

    def test_format_template_unknown_format_code(self):
        writer = self._get_writer(ref='[Template:foo]\n{bar:04x}')
        with self.assertRaisesRegex(SkoolKitError, "^Failed to format foo template: Unknown format code 'x' for object of type 'str'$"):
            writer.format_template('foo', {'bar': 'baz'})

    def test_format_template_nonexistent_template(self):
        writer = self._get_writer()
        with self.assertRaisesRegex(SkoolKitError, "^'non-existent' template does not exist$"):
            writer.format_template('non-existent', {})

    def test_format_template_foreach(self):
        ref = """
            [Template:loop]
            <# foreach(item,list) #>
            {item}
            <# endfor #>
        """
        fields = {'list': ('item 1', 'item 2', 'item 3')}
        exp_output = """
            item 1
            item 2
            item 3
        """
        self._test_format_template(ref, 'loop', fields, exp_output)

    def test_format_template_foreach_complex(self):
        ref = """
            [Template:loop]
            <# foreach(item,list) #>
            {item[id]}: {item[name]}
            <# endfor #>
        """
        fields = {
            'list': (
                {'id': 1, 'name': 'item 1'},
                {'id': 2, 'name': 'item 2'},
                {'id': 3, 'name': 'item 3'}
            )
        }
        exp_output = """
            1: item 1
            2: item 2
            3: item 3
        """
        self._test_format_template(ref, 'loop', fields, exp_output)

    def test_format_template_foreach_nested_simple(self):
        ref = """
            [Template:rows]
            <# foreach(row,table) #>
            <tr>
            <# foreach(cell,row) #>
            <td>{cell}</td>
            <# endfor #>
            </tr>
            <# endfor #>
        """
        fields = {
            'table': (
                ('row 1, cell 1', 'row 1, cell 2'),
                ('row 2, cell 1', 'row 2, cell 2')
            )
        }
        exp_output = """
            <tr>
            <td>row 1, cell 1</td>
            <td>row 1, cell 2</td>
            </tr>
            <tr>
            <td>row 2, cell 1</td>
            <td>row 2, cell 2</td>
            </tr>
        """
        self._test_format_template(ref, 'rows', fields, exp_output)

    def test_format_template_foreach_nested_complex(self):
        ref = """
            [Template:table]
            {table[name]}:
            <# foreach(row,table[rows]) #>
            - Row {row[id]}:
            <# foreach(cell,row[cells]) #>
            -- Row {row[id]}: {cell}
            <# endfor #>
            <# endfor #>
        """
        fields = {
            'table': {
                'name': 'A table',
                'rows': (
                    {'id': 1, 'cells': ('cell 1', 'cell 2')},
                    {'id': 2, 'cells': ('cell A', 'cell B', 'cell C')}
                )
            }
        }
        exp_output = """
            A table:
            - Row 1:
            -- Row 1: cell 1
            -- Row 1: cell 2
            - Row 2:
            -- Row 2: cell A
            -- Row 2: cell B
            -- Row 2: cell C
        """
        self._test_format_template(ref, 'table', fields, exp_output)

    def test_format_template_foreach_doubly_nested(self):
        ref = """
            [Template:parents]
            <# foreach($parent,parents) #>
            {$parent[name]}:
            <# foreach($child,$parent[children]) #>
            - {$parent[name]}: {$child[name]}:
            <# foreach($grandchild,$child[children]) #>
            -- {$parent[name]}: {$child[name]}: {$grandchild[name]}
            <# endfor #>
            <# endfor #>
            <# endfor #>
        """
        fields = {
            'parents': ({
                'name': 'Parent A',
                'children': ({
                    'name': 'Child A1',
                    'children': ({'name': 'Grandchild A1-1'}, {'name': 'Grandchild A1-2'})
                }, {
                    'name': 'Child A2',
                    'children': ({'name': 'Grandchild A2-1'}, {'name': 'Grandchild A2-2'})
                })
            }, {
                'name': 'Parent B',
                'children': ({
                    'name': 'Child B1',
                    'children': ({'name': 'Grandchild B1-1'}, {'name': 'Grandchild B1-2'})
                }, {
                    'name': 'Child B2',
                    'children': ({'name': 'Grandchild B2-1'}, {'name': 'Grandchild B2-2'})
                })
            })
        }
        exp_output = """
            Parent A:
            - Parent A: Child A1:
            -- Parent A: Child A1: Grandchild A1-1
            -- Parent A: Child A1: Grandchild A1-2
            - Parent A: Child A2:
            -- Parent A: Child A2: Grandchild A2-1
            -- Parent A: Child A2: Grandchild A2-2
            Parent B:
            - Parent B: Child B1:
            -- Parent B: Child B1: Grandchild B1-1
            -- Parent B: Child B1: Grandchild B1-2
            - Parent B: Child B2:
            -- Parent B: Child B2: Grandchild B2-1
            -- Parent B: Child B2: Grandchild B2-2
        """
        self._test_format_template(ref, 'parents', fields, exp_output)

    def test_format_template_foreach_with_if(self):
        ref = """
            [Template:loop]
            <# foreach(item,list) #>
            <# if({item[large]}) #>
            Large {item[name]}
            <# else #>
            Small {item[name]}
            <# endif #>
            <# endfor #>
        """
        fields = {
            'list': (
                {'large': 1, 'name': 'apple'},
                {'large': 0, 'name': 'orange'}
            )
        }
        exp_output = """
            Large apple
            Small orange
        """
        self._test_format_template(ref, 'loop', fields, exp_output)

    def test_format_template_foreach_with_include(self):
        ref = """
            [Template:loopinclude]
            <# foreach($item,list) #>
            <# include(item) #>
            <# endfor #>
            [Template:item]
            <# if({$item[large]}) #>
            Large {$item[name]}
            <# else #>
            Small {$item[name]}
            <# endif #>
        """
        fields = {
            'list': (
                {'large': 1, 'name': 'apple'},
                {'large': 0, 'name': 'orange'}
            )
        }
        exp_output = """
            Large apple
            Small orange
        """
        self._test_format_template(ref, 'loopinclude', fields, exp_output)

    def test_format_template_extra_endfor_directives(self):
        ref = """
            [Template:loop]
            <# foreach(item,list) #>
            {item}
            <# endfor #>
            <# endfor #>
            <# endfor #>
        """
        fields = {'list': ('item 1', 'item 2')}
        exp_output = """
            item 1
            item 2
            <# endfor #>
            <# endfor #>
        """
        self._test_format_template(ref, 'loop', fields, exp_output)

    def test_format_template_foreach_no_parameters(self):
        ref = """
            [Template:loop]
            <# foreach() #>
            {item}
            <# endfor #>
        """
        with self.assertRaisesRegex(SkoolKitError, "^Invalid foreach directive: Not enough parameters \(expected 2\): ''$"):
            self._get_writer(ref=ref).format_template('loop', {})

    def test_format_template_foreach_missing_parameter(self):
        ref = """
            [Template:loop]
            <# foreach(item) #>
            {item}
            <# endfor #>
        """
        with self.assertRaisesRegex(SkoolKitError, "^Invalid foreach directive: Not enough parameters \(expected 2\): 'item'$"):
            self._get_writer(ref=ref).format_template('loop', {})

    def test_format_template_foreach_extra_parameter(self):
        ref = """
            [Template:loop]
            <# foreach(item,list,surplus) #>
            {item}
            <# endfor #>
        """
        with self.assertRaisesRegex(SkoolKitError, "^Invalid foreach directive: Too many parameters \(expected 2\): 'item,list,surplus'$"):
            self._get_writer(ref=ref).format_template('loop', {})

    def test_format_template_foreach_no_closing_bracket(self):
        ref = """
            [Template:loop]
            <# foreach(item,list #>
            {item}
            <# endfor #>
        """
        with self.assertRaisesRegex(SkoolKitError, "^Invalid foreach directive: No closing bracket: \(item,list$"):
            self._get_writer(ref=ref).format_template('loop', {})

    def test_format_template_foreach_unknown_variable(self):
        ref = """
            [Template:loop]
            <# foreach(item,nonexistent) #>
            {item}
            <# endfor #>
        """
        with self.assertRaisesRegex(SkoolKitError, "^Invalid foreach directive: name 'nonexistent' is not defined$"):
            self._get_writer(ref=ref).format_template('loop', {})

    def test_format_template_foreach_noniterable_parameter(self):
        ref = """
            [Template:loop]
            <# foreach(item,0) #>
            {item}
            <# endfor #>
        """
        with self.assertRaisesRegex(SkoolKitError, "^Invalid foreach directive: '0' is not a list$"):
            self._get_writer(ref=ref).format_template('loop', {})

    def test_format_template_if_int_values(self):
        ref = """
            [Template:if]
            <# if(yes) #>
            Visible
            <# endif #>
            <# if(no) #>
            Hidden
            <# endif #>
        """
        fields = {'no': 0, 'yes': 1}
        exp_output = "Visible"
        self._test_format_template(ref, 'if', fields, exp_output)

    def test_format_template_if_str_values(self):
        ref = """
            [Template:if]
            <# if(yes) #>
            Visible
            <# endif #>
            <# if(no) #>
            Hidden
            <# endif #>
        """
        fields = {'no': '', 'yes': '0'}
        exp_output = "Visible"
        self._test_format_template(ref, 'if', fields, exp_output)

    def test_format_template_if_str_values_replaced_by_int(self):
        ref = """
            [Template:if]
            <# if({yes}) #>
            Visible
            <# endif #>
            <# if({no}) #>
            Hidden
            <# endif #>
        """
        fields = {'no': '0', 'yes': '1'}
        exp_output = "Visible"
        self._test_format_template(ref, 'if', fields, exp_output)

    def test_format_template_if_list_values(self):
        ref = """
            [Template:if]
            <# if(list1) #>
            list1 is not empty
            <# endif #>
            <# if(list2) #>
            list2 is not empty
            <# endif #>
        """
        fields = {'list1': [], 'list2': [0]}
        exp_output = "list2 is not empty"
        self._test_format_template(ref, 'if', fields, exp_output)

    def test_format_template_if_arithmetic_expressions(self):
        ref = """
            [Template:if]
            <# if(val1>1) #>
            val1 ({val1}) is greater than 1
            <# endif #>
            <# if(val2>1) #>
            This should not happen
            <# endif #>
        """
        fields = {'val1': 2, 'val2': 0}
        exp_output = "val1 (2) is greater than 1"
        self._test_format_template(ref, 'if', fields, exp_output)

    def test_format_template_if_else(self):
        ref = """
            [Template:ifelse]
            <# if({true}) #>
            Included
            <# else #>
            Omitted
            <# endif #>
            <# if({false}) #>
            Also omitted
            <# else #>
            Also included
            <# endif #>
        """
        fields = {'false': 0, 'true': 1}
        exp_output = """
            Included
            Also included
        """
        self._test_format_template(ref, 'ifelse', fields, exp_output)

    def test_format_template_if_nested(self):
        ref = """
            [Template:ifnest]
            <# if({yes}) #>
            Visible
            <# if({false}) #>
            Hidden
            <# endif #>
            <# endif #>
            <# if({no}) #>
            Hidden
            <# if({true}) #>
            Also hidden
            <# endif #>
            <# endif #>
        """
        fields = {'no': 0, 'yes': 1, 'false': 0, 'true': 1}
        exp_output = "Visible"
        self._test_format_template(ref, 'ifnest', fields, exp_output)

    def test_format_template_if_else_nested(self):
        ref = """
            [Template:ifelsenest]
            <# if({true}) #>
            Visible
            <# if({false}) #>
            Hidden
            <# else #>
            Also visible
            <# endif #>
            <# else #>
            Hidden
            <# if({true}) #>
            Also hidden
            <# else #>
            Still hidden
            <# endif #>
            <# endif #>
        """
        fields = {'false': 0, 'true': 1}
        exp_output = """
            Visible
            Also visible
        """
        self._test_format_template(ref, 'ifelsenest', fields, exp_output)

    def test_format_template_if_with_include(self):
        ref = """
            [Template:ifinclude]
            <# if({true}) #>
            <# include(t1) #>
            <# else #>
            <# include(t2) #>
            <# endif #>
            [Template:t1]
            Included
            [Template:t2]
            Not included
        """
        fields = {'true': 1}
        exp_output = "Included"
        self._test_format_template(ref, 'ifinclude', fields, exp_output)

    def test_format_template_extra_endif_directives(self):
        ref = """
            [Template:endifs]
            <# if({true}) #>
            Hi
            <# endif #>
            <# endif #>
            <# endif #>
        """
        fields = {'true': 1}
        exp_output = """
            Hi
            <# endif #>
            <# endif #>
        """
        self._test_format_template(ref, 'endifs', fields, exp_output)

    def test_format_template_extra_else_directives(self):
        ref = """
            [Template:elses]
            <# if({true}) #>
            Hi
            <# endif #>
            <# else #>
            <# else #>
        """
        fields = {'true': 1}
        exp_output = """
            Hi
            <# else #>
            <# else #>
        """
        self._test_format_template(ref, 'elses', fields, exp_output)

    def test_format_template_if_missing_parameter(self):
        ref = """
            [Template:if]
            <# if() #>
            Content
            <# endif #>
        """
        with self.assertRaisesRegex(SkoolKitError, "^Invalid if directive: Expression is missing$"):
            self._get_writer(ref=ref).format_template('if', {})

    def test_format_template_if_no_closing_bracket(self):
        ref = """
            [Template:if]
            <# if(true #>
            Content
            <# endif #>
        """
        with self.assertRaisesRegex(SkoolKitError, "^Invalid if directive: No closing bracket: \(true$"):
            self._get_writer(ref=ref).format_template('if', {})

    def test_format_template_if_unknown_variable(self):
        ref = """
            [Template:if]
            <# if(nonexistent) #>
            Content
            <# endif #>
        """
        with self.assertRaisesRegex(SkoolKitError, "^Invalid if directive: name 'nonexistent' is not defined$"):
            self._get_writer(ref=ref).format_template('if', {})

    def test_format_template_if_invalid_replacement_field(self):
        ref = """
            [Template:if]
            <# if({nonexistent}) #>
            Content
            <# endif #>
        """
        with self.assertRaisesRegex(SkoolKitError, "^Invalid if directive: Unrecognised field 'nonexistent'$"):
            self._get_writer(ref=ref).format_template('if', {})

    def test_format_template_if_syntax_error(self):
        ref = """
            [Template:if]
            <# if((1;)) #>
            Content
            <# endif #>
        """
        with self.assertRaisesRegex(SkoolKitError, "^Invalid if directive: Syntax error in expression: '\(1;\)'$"):
            self._get_writer(ref=ref).format_template('if', {})

    def test_format_template_include(self):
        ref = """
            [Template:t1]
            Begin
            <# include(t2) #>
            End
            [Template:t2]
            Do stuff
        """
        exp_output = """
            Begin
            Do stuff
            End
        """
        self._test_format_template(ref, 't1', {}, exp_output)

    def test_format_template_include_with_replacement_field(self):
        ref = """
            [Template:t1]
            Begin
            <# include({template}) #>
            End
            [Template:t2]
            Do stuff
        """
        exp_output = """
            Begin
            Do stuff
            End
        """
        self._test_format_template(ref, 't1', {'template': 't2'}, exp_output)

    def test_format_template_include_nested(self):
        ref = """
            [Template:t1]
            Begin
            <# include(t2) #>
            End
            [Template:t2]
            Do stuff
            <# include(t3) #>
            [Template:t3]
            Do more stuff
        """
        exp_output = """
            Begin
            Do stuff
            Do more stuff
            End
        """
        self._test_format_template(ref, 't1', {}, exp_output)

    def test_format_template_include_extra_parameter(self):
        ref = """
            [Template:include]
            <# include(t1,t2) #>
        """
        with self.assertRaisesRegex(SkoolKitError, "^Invalid include directive: 't1,t2' template does not exist$"):
            self._get_writer(ref=ref).format_template('include', {})

    def test_format_template_include_no_closing_bracket(self):
        ref = """
            [Template:include]
            <# include(t1 #>
        """
        with self.assertRaisesRegex(SkoolKitError, "^Invalid include directive: No closing bracket: \(t1$"):
            self._get_writer(ref=ref).format_template('include', {})

    def test_format_template_include_unknown_template(self):
        ref = """
            [Template:include]
            <# include(nonexistent) #>
        """
        with self.assertRaisesRegex(SkoolKitError, "^Invalid include directive: 'nonexistent' template does not exist$"):
            self._get_writer(ref=ref).format_template('include', {})

    def test_format_template_include_invalid_replacement_field(self):
        ref = """
            [Template:include]
            <# include({no}) #>
        """
        with self.assertRaisesRegex(SkoolKitError, "^Invalid include directive: Unrecognised field 'no'$"):
            self._get_writer(ref=ref).format_template('include', {})

    def test_format_template_with_indented_directives(self):
        ref = """
            [Template:test]
            <div>
                <# foreach($i,list) #>
                    <# if($i[on]) #>
                        On: {$i[name]}
                    <# else #>
                        Off: {$i[name]}
                    <# endif #>
                <# endfor #>
                <# include(extra) #>
            </div>

            [Template:extra]
            Done
        """
        fields = {'list': [{'on': 1, 'name': 'Yes'}, {'on': 0, 'name': 'No'}]}
        exp_output = """
            <div>
            On: Yes
            Off: No
            Done
            </div>
        """
        self._test_format_template(ref, 'test', fields, exp_output)

    def test_push_snapshot_keeps_original_in_place(self):
        writer = self._get_writer(snapshot=[0])
        snapshot = writer.snapshot
        writer.push_snapshot()
        writer.snapshot[0] = 1
        self.assertEqual(snapshot[0], 1)

    def test_pop_snapshot_modifies_snapshot_in_place(self):
        writer = self._get_writer(snapshot=[0])
        snapshot = writer.snapshot
        writer.snapshot[0] = 1
        writer.push_snapshot()
        writer.snapshot[0] = 2
        writer.pop_snapshot()
        self.assertEqual(snapshot[0], 1)

    def test_get_snapshot_name(self):
        writer = self._get_writer(snapshot=[])
        names = ['snapshot1', 'next', 'final']
        for name in names:
            writer.push_snapshot(name)
        while names:
            self.assertEqual(writer.get_snapshot_name(), names.pop())
            writer.pop_snapshot()

class SkoolMacroTest(HtmlWriterTestCase, CommonSkoolMacroTest):
    def setUp(self):
        HtmlWriterTestCase.setUp(self)
        patch.object(skoolhtml, 'REF_FILE', SKOOL_MACRO_MINIMAL_REF_FILE).start()
        self.addCleanup(patch.stopall)

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
            self.assertEqual(frame.x_offset, exp_frame.x_offset)
            self.assertEqual(frame.y_offset, exp_frame.y_offset)
            self._compare_udgs(frame.udgs, exp_frame.udgs)

    def _assert_link_equals(self, html, href, text, suffix=''):
        self.assertEqual(html, '<a href="{}">{}</a>{}'.format(href, text, suffix))

    def _assert_img_equals(self, html, alt, src):
        self.assertEqual(html, '<img alt="{0}" src="{1}" />'.format(alt, src))

    def _assert_error(self, writer, text, error_msg=None, prefix=None, error=SkoolParsingError):
        with self.assertRaises(error) as cm:
            writer.expand(text, ASMDIR)
        if error_msg is not None:
            if prefix:
                error_msg = '{}: {}'.format(prefix, error_msg)
            self.assertEqual(cm.exception.args[0], error_msg)

    def _test_image_macro_with_replacement_field_in_filename(self, macro, defdir=UDGDIR, snapshot=(0,) * 8):
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)
        for prefix, path, alt in (
                ('Font', 'images/font', ''),
                ('', 'images', ''),
                ('Screenshot', 'images/scr', '|screenshot'),
                ('UDG', 'images/udgs', '|{donotreplacethis}'),
                ('Nonexistent', defdir + '/{NonexistentImagePath}', '')
        ):
            fname = '{{{}ImagePath}}/foo.png{}'.format(prefix, alt)
            exp_image_path = '{}/foo.png'.format(path)
            exp_src = '../{}'.format(exp_image_path)
            output = writer.expand('{}({})'.format(macro, fname), ASMDIR)
            self._assert_img_equals(output, alt[1:] or 'foo', exp_src)
            self.assertEqual(writer.file_info.fname, exp_image_path)

    def _test_invalid_image_macro(self, writer, macro, error_msg, prefix):
        self._assert_error(writer, macro, error_msg, prefix)

    def _test_call(self, cwd, arg1, arg2, arg3=None):
        # Method used to test the #CALL macro
        return str((cwd, arg1, arg2, arg3))

    def _test_call_with_kwargs(self, cwd, arg1, arg2=None, arg3=None):
        # Method used to test the #CALL macro with keyword arguments
        return str((arg1, arg2, arg3))

    def _test_call_no_retval(self, *args):
        return

    def _test_call_no_args(self, cwd):
        return 'OK'

    def _unsupported_macro(self, *args):
        raise UnsupportedMacroError()

    def test_macro_chr(self):
        writer = self._get_writer(skool='', variables=[('foo', 66)])

        self.assertEqual(writer.expand('#CHR169'), '&#169;')
        self.assertEqual(writer.expand('#CHR(163)1984'), '&#163;1984')
        self.assertEqual(writer.expand('#CHR65+3'), '&#65;+3')
        self.assertEqual(writer.expand('#CHR65*2'), '&#65;*2')
        self.assertEqual(writer.expand('#CHR65-9'), '&#65;-9')
        self.assertEqual(writer.expand('#CHR65/5'), '&#65;/5')
        self.assertEqual(writer.expand('#CHR(65+3*2-9/3)'), '&#68;')
        self.assertEqual(writer.expand('#CHR($42 + 3 * 2 - (2 + 7) / 3)'), '&#69;')
        self.assertEqual(writer.expand(nest_macros('#CHR({})', 70)), '&#70;')
        self.assertEqual(writer.expand('#CHR({vars[foo]})'), '&#66;')
        self.assertEqual(writer.expand('#LET(c=67)#CHR({c})'), '&#67;')

    def test_macro_eval_asm(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#EVAL({asm})'), '0')

    def test_macro_eval_fix(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#EVAL({fix})'), '0')

    def test_macro_eval_html(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#EVAL({html},2,8)'), '00000001')

    def test_macro_font(self):
        snapshot = [0] * 65536
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)

        # Default filename
        fname = 'font'
        exp_image_path = '{}/{}.png'.format(FONTDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#FONT32768,96', ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        # Filename specified
        fname = 'font2'
        exp_image_path = '{}/{}.png'.format(FONTDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#FONT55584,96({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        # Every parameter
        fname = 'font3'
        exp_image_path = '{}/{}.png'.format(FONTDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        font_addr = 32768
        char1 = [1, 2, 3, 4, 5, 6, 7, 8]
        char2 = [8, 7, 6, 5, 4, 3, 2, 1]
        char3 = [1, 3, 7, 15, 31, 63, 127, 255]
        chars = (char1, char2, char3)
        for i, char in enumerate(chars):
            snapshot[font_addr + i * 8:font_addr + (i + 1) * 8] = char
        attr = 4
        scale = 2
        tindex = 5
        alpha = 50
        x, y, w, h = 1, 2, 3, 4
        values = (font_addr, len(chars), attr, scale, tindex, alpha, x, y, w, h, fname)
        macro = '#FONT{0},{1},{2},{3},{4},{5}{{{6},{7},{8},{9}}}({10})'.format(*values)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(4, char) for char in chars]]
        self._check_image(writer, udg_array, scale, False, tindex, alpha, x, y, w, h, exp_image_path)

        # Keyword arguments
        macro = '#FONTscale={3},chars={1},tindex={4},addr={0},alpha={5},,attr={2}{{x={6},y={7},width={8},height={9}}}({10})'.format(*values)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, udg_array, scale, False, tindex, alpha, x, y, w, h, exp_image_path)

        # Keyword arguments, arithmetic expressions
        values = ('128*256', '1+(3+1)/2', '(1 + 1) * 2', '7&2', '2+3', '5*5*2', '2*2-3', '(8 + 8) / 8', '6>>1', '2<<1', fname)
        macro = '#FONT({0}, scale={3}, alpha={5}, chars = {1}, tindex={4}, attr={2}){{x={6}, y = {7}, width={8},height ={9}}}({10})'.format(*values)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, udg_array, scale, False, tindex, alpha, x, y, w, h, exp_image_path)

        # Nested macros
        fname = 'nested'
        exp_image_path = '{}/{}.png'.format(FONTDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        x = 5
        output = writer.expand(nest_macros('#FONT({},1){{x={}}}({})', font_addr, x, fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, [[Udg(56, char1)]], 2, x=x, width=11, path=exp_image_path)

    def test_macro_font_with_replacement_fields(self):
        char1 = [1, 2, 3, 4, 5, 6, 7, 8]
        exp_image_path = '{}/font.png'.format(FONTDIR)
        writer = self._get_writer(snapshot=char1, mock_file_info=True)
        output = writer.expand('#LET(a=0)#LET(y=1)#FONT({a},1){y={y}}', ASMDIR)
        self._assert_img_equals(output, 'font', '../{}'.format(exp_image_path))
        self._check_image(writer, [[Udg(56, char1)]], 2, y=1, height=15, path=exp_image_path)

    def test_macro_font_text(self):
        snapshot = [1, 2, 3, 4, 5, 6, 7, 8] # ' '
        snapshot.extend((8, 7, 6, 5, 4, 3, 2, 1)) # '!'
        snapshot.extend((1, 3, 7, 15, 31, 63, 127, 255)) # '"'
        snapshot.extend([0] * 56)
        snapshot.extend((1, 3, 5, 7, 9, 11, 13, 15)) # ')'
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)

        fname = 'message'
        exp_image_path = '{}/{}.png'.format(FONTDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        message = ' !"%'
        macro = '#FONT:({})0({})'.format(message, fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[]]
        for c in message:
            c_addr = 8 * (ord(c) - 32)
            udg_array[0].append(Udg(56, snapshot[c_addr:c_addr + 8]))
        self._check_image(writer, udg_array, path=exp_image_path)

        message = ')!!!!'
        attr = 43
        scale = 5
        c_addr = 8 * (ord(message[0]) - 32)
        udg_array = [[Udg(attr, snapshot[c_addr:c_addr + 8])]]
        for delim1, delim2 in (('{', '}'), ('[', ']'), ('*', '*'), ('@', '@')):
            macro = '#FONT:{}{}{}0,1,{},{}({})'.format(delim1, message, delim2, attr, scale, fname)
            output = writer.expand(macro, ASMDIR)
            self._assert_img_equals(output, fname, exp_src)
            self._check_image(writer, udg_array, scale, path=exp_image_path)

    def test_macro_font_with_custom_font_image_path(self):
        font_path = 'graphics/font'
        ref = '[Paths]\nFontImagePath={}'.format(font_path)
        writer = self._get_writer(ref=ref, snapshot=[0] * 16, mock_file_info=True)

        fname = 'text'
        exp_image_path = '{}/{}.png'.format(font_path, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#FONT:(!!!)0({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

    def test_macro_font_with_custom_image_path_containing_skool_macro(self):
        ref = '[Paths]\nImagePath=#MAP({case})(graphics,2:GRAPHICS)'
        writer = self._get_writer(ref=ref, snapshot=[0] * 16, mock_file_info=True)

        fname = 'text'
        exp_image_path = 'graphics/font/{}.png'.format(fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#FONT:(!!!)0({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

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

        fname = 'char2'
        exp_image_path = '{}/{}.png'.format(FONTDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#FONT8,1,7({}*)'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(file_info.fname, exp_image_path)

        fname = 'char3'
        exp_image_path = '{}/{}.png'.format(FONTDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#FONT16,1({}*char3_frame)'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(file_info.fname, exp_image_path)

        fname = 'font'
        exp_image_path = '{}/{}.png'.format(FONTDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#FONT24,1,,3{1,2,16,16}(*)', ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
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

        fname = 'font'
        exp_image_path = '{}/{}.png'.format(FONTDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        alt = 'Space'
        output = writer.expand('#FONT:( )0(|{})'.format(alt), ASMDIR)
        self._assert_img_equals(output, alt, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        fname = 'space'
        exp_image_path = '{}/{}.png'.format(FONTDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        alt = 'Another space'
        output = writer.expand('#FONT:( )0({}|{})'.format(fname, alt), ASMDIR)
        self._assert_img_equals(output, alt, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

    def test_macro_font_with_replacement_field_in_filename(self):
        self._test_image_macro_with_replacement_field_in_filename('#FONT0,1', FONTDIR)

    def test_macro_foreach_entry_omits_i_blocks(self):
        skool = """
            i23296 DEFS 1280

            c24576 RET
        """
        writer = self._get_writer(skool=skool)

        output = writer.expand('#FOREACH(ENTRY)(n,n, )')
        self.assertEqual(output, '24576')

    def test_macro_html(self):
        writer = self._get_writer()

        delimiters = {
            '(': ')',
            '[': ']',
            '{': '}'
        }
        for text in('', 'Hello', '&lt;&amp;&gt;'):
            for delim1 in '([{!@$%^*_-+|':
                delim2 = delimiters.get(delim1, delim1)
                output = writer.expand('#HTML{0}{1}{2}'.format(delim1, text, delim2))
                self.assertEqual(output, html.unescape(text))

        output = writer.expand('#HTML?#CHR169?')
        self.assertEqual(output, '&#169;')

        text = 'tested nested SMPL macros'
        output = writer.expand(nest_macros('#HTML/{}/', text))
        self.assertEqual(output, text)

    def test_macro_if_asm(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#IF({asm})(FAIL,PASS)'), 'PASS')

    def test_macro_if_fix(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#IF({fix})(FAIL,PASS)'), 'PASS')

    def test_macro_if_html(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#IF({html})(PASS,FAIL)'), 'PASS')

    def test_macro_if_clone(self):
        ref = '[OtherCode:other]'
        main_writer = self._get_writer(ref=ref, skool='', variables=(('foo', 1), ('bar', 2)))
        writer = main_writer.clone(main_writer.parser, 'other')

        self.assertEqual(writer.expand('#IF({asm})(FAIL,PASS)'), 'PASS')
        self.assertEqual(writer.expand('#IF({base})(FAIL,PASS)'), 'PASS')
        self.assertEqual(writer.expand('#IF({case})(FAIL,PASS)'), 'PASS')
        self.assertEqual(writer.expand('#IF({fix})(FAIL,PASS)'), 'PASS')
        self.assertEqual(writer.expand('#IF({html})(PASS,FAIL)'), 'PASS')
        self.assertEqual(writer.expand('#IF({vars[foo]}==1)(PASS,FAIL)'), 'PASS')
        self.assertEqual(writer.expand('#IF({vars[bar]}==2)(PASS,FAIL)'), 'PASS')

    def test_macro_include_no_paragraphs(self):
        ref = """
            [Foo]
            Bar

            #IF0(Baz,Qux)
        """
        exp_html = dedent("""
            Bar

            Qux
        """).strip()
        writer = self._get_writer(ref=ref)

        for params in ('(Foo)', '0[Foo]', '(){Foo}', '(0+0)/Foo/'):
            output = writer.expand('#INCLUDE' + params, ASMDIR)
            self.assertEqual(exp_html, output)

    def test_macro_include_with_paragraphs(self):
        ref = """
            [Foo]
            Bar

            #IF1(Baz,Qux)
        """
        exp_html = dedent("""
            <div class="paragraph">
            Bar
            </div>
            <div class="paragraph">
            Baz
            </div>
        """).strip()
        writer = self._get_writer(ref=ref)

        for params in ('1(Foo)', '(1)[Foo]', '(1*1){Foo}', '(0+1)/Foo/'):
            output = writer.expand('#INCLUDE' + params, ASMDIR)
            self.assertEqual(exp_html, output)

    def test_macro_include_with_replacement_field(self):
        ref = """
            [Foo]
            Bar
        """
        exp_html = "Bar"
        writer = self._get_writer(ref=ref)
        output = writer.expand('#LET(p=0)#INCLUDE({p})(Foo)', ASMDIR)
        self.assertEqual(exp_html, output)

    def test_macro_link(self):
        ref = """
            [Page:page]
            [Page:page2]
            [Links]
            page=Custom page
            page2=Custom page 2
        """
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

        link_text = 'test nested SMPL macros'
        output = writer.expand(nest_macros('#LINK:page2({})', link_text), ASMDIR)
        self._assert_link_equals(output, '../page2.html', link_text)

        anchor = 'testNestedSmplMacros'
        link_text = 'Testing2'
        output = writer.expand(nest_macros('#LINK#(:page2#{{}})({})'.format(link_text), anchor), ASMDIR)
        self._assert_link_equals(output, '../page2.html#{}'.format(anchor), link_text)

        page_id = 'page2'
        link_text = 'Testing3'
        output = writer.expand(nest_macros('#LINK#(:{{}})({})'.format(link_text), page_id), ASMDIR)
        self._assert_link_equals(output, '../page2.html', link_text)

    def test_macro_link_to_memory_map_page(self):
        skool = """
            c40000 RET

            b40001 DEFB 0

            t40002 DEFM "!"
        """
        address_fmt = '{address:04x}'
        ref = """
            [Game]
            AddressAnchor={}
            [MemoryMap:MemoryMap]
            EntryTypes=bct
            [MemoryMap:RoutinesMap]
            EntryTypes=c
            [MemoryMap:CustomMap]
            EntryTypes=bt
        """.format(address_fmt)
        writer = self._get_writer(skool=skool, ref=ref)

        # Anchor matches an entry address - anchor should be converted
        for page_id, address in (
            ('RoutinesMap', 40000),
            ('MemoryMap', 40001),
            ('CustomMap', 40002),
        ):
            output = writer.expand('#LINK:{0}#{1}({1})'.format(page_id, address), ASMDIR)
            exp_anchor = address_fmt.format(address=address)
            self._assert_link_equals(output, '../maps/{}.html#{}'.format(page_id, exp_anchor), str(address))

        # Anchor doesn't match an entry address - anchor should be unchanged
        for page_id, anchor in (
            ('RoutinesMap', '40003'),
            ('MemoryMap', '40004'),
            ('CustomMap', '40005'),
            ('RoutinesMap', 'foo'),
            ('MemoryMap', 'bar'),
            ('CustomMap', 'baz')
        ):
            output = writer.expand('#LINK:{0}#{1}({1})'.format(page_id, anchor), ASMDIR)
            self._assert_link_equals(output, '../maps/{}.html#{}'.format(page_id, anchor), anchor)

    def test_macro_link_to_memory_map_page_with_upper_case_hexadecimal_asm_anchor(self):
        skool = "c43981 RET"
        ref = """
            [Game]
            AddressAnchor={address:04X}
            [MemoryMap:MemoryMap]
            EntryTypes=c
        """
        writer = self._get_writer(skool=skool, ref=ref)
        output = writer.expand('#LINK:MemoryMap#43981(ABCD)', ASMDIR)
        self._assert_link_equals(output, '../maps/MemoryMap.html#ABCD', 'ABCD')

    def test_macro_link_to_non_memory_map_page_with_entry_address_anchor(self):
        skool = 'c40000 RET'
        ref = """
            [Game]
            AddressAnchor={address:04x}
            [Page:CustomPage]
            PageContent=Hello
        """
        writer = self._get_writer(skool=skool, ref=ref)
        output = writer.expand('#LINK:CustomPage#40000(foo)', ASMDIR)
        self._assert_link_equals(output, '../CustomPage.html#40000', 'foo')

    def test_macro_link_to_box_page_item_with_blank_link_text(self):
        ref = """
            [Page:Boxes]
            SectionPrefix=Box
            [Box:item1:Item 1]
            This is item 1.
        """
        writer = self._get_writer(ref=ref)
        output = writer.expand('#LINK:Boxes#item1()', ASMDIR)
        self._assert_link_equals(output, '../Boxes.html#item1', 'Item 1')

    def test_macro_link_invalid(self):
        writer, prefix = CommonSkoolMacroTest.test_macro_link_invalid(self)
        self._assert_error(writer, '#LINK:nonexistentPageID(text)', 'Unknown page ID: nonexistentPageID', prefix)

    def test_macro_list(self):
        writer = self._get_writer(skool='c32768 RET')

        # List with a CSS class and an item containing a skool macro
        src = "(default){ Item 1 }{ Item 2 }{ #R32768 }"
        exp_html = """
            <ul class="default">
            <li>Item 1</li>
            <li>Item 2</li>
            <li><a href="32768.html">32768</a></li>
            </ul>
        """
        output = writer.expand('#LIST{}\nLIST#'.format(src), ASMDIR)
        self.assertEqual(dedent(exp_html).strip(), output)

        # List with no CSS class
        src = "{ Item 1 }"
        exp_html = """
            <ul class="">
            <li>Item 1</li>
            </ul>
        """
        output = writer.expand('#LIST{}\nLIST#'.format(src))
        self.assertEqual(dedent(exp_html).strip(), output)

        # Empty list
        output = writer.expand('#LIST LIST#')
        self.assertEqual(output, '<ul class="">\n</ul>')

        # Nested macros
        css_class = 'someclass'
        output = writer.expand(nest_macros('#LIST({}){{ A }}LIST#', css_class))
        self.assertEqual(output, '<ul class="{}">\n<li>A</li>\n</ul>'.format(css_class))

    def test_macro_list_with_wrap_flag(self):
        writer = self._get_writer()
        html = '<ul class="{}">\n<li>A</li>\n</ul>'
        for params, exp_class_name in (('', ''), ('(default)', 'default')):
            for flag in ('nowrap', 'wrapalign'):
                with self.subTest(params=params, flag=flag):
                    output = writer.expand('#LIST{}<{}> {{ A }} LIST#'.format(params, flag))
                    self.assertEqual(html.format(exp_class_name), output)

    def test_macro_list_invalid(self):
        writer = self._get_writer()

        # No end marker
        self._assert_error(writer, '#LIST { Item }', 'No end marker: #LIST { Item }...')

    def test_macro_map_asm(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#MAP({asm})(FAIL,0:PASS)'), 'PASS')

    def test_macro_map_fix(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#MAP({fix})(FAIL,0:PASS)'), 'PASS')

    def test_macro_map_html(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#MAP({html})(FAIL,1:PASS)'), 'PASS')

    def test_macro_map_clone(self):
        ref = '[OtherCode:other]'
        main_writer = self._get_writer(ref=ref, skool='', variables=(('foo', 1), ('bar', 2)))
        writer = main_writer.clone(main_writer.parser, 'other')

        self.assertEqual(writer.expand('#MAP({asm})(FAIL,0:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({base})(FAIL,0:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({case})(FAIL,0:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({fix})(FAIL,0:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({html})(FAIL,1:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({vars[foo]})(FAIL,1:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({vars[bar]})(FAIL,2:PASS)'), 'PASS')

    def test_macro_plot(self):
        exp_image_path = '{}/img.png'.format(UDGDIR)
        writer = self._get_writer(snapshot=[1] * 8, mock_file_info=True)
        macros = (
            '#UDGARRAY2;0x4(*f)',
            '#PLOT0,0(f)',                # Set bit at (0,0)
            '#PLOT(value=0,x=15,y=0)(f)', # Reset bit at (15,0)
            '#PLOT0,15,1(f)',             # Set bit at (0,15)
            '#PLOT15,15,2(f)',            # Reset bit at (15,15)
            '#UDGARRAY*f(img)'
        )
        output = writer.expand(''.join(macros), ASMDIR)
        self._assert_img_equals(output, 'img', '../{}'.format(exp_image_path))
        exp_udgs = [
            [Udg(56, [129] + [1] * 7), Udg(56, [0] + [1] * 7)],
            [Udg(56, [1] * 7 + [129]), Udg(56, [1] * 7 + [0])]
        ]
        self._check_image(writer, exp_udgs, scale=2, path=exp_image_path)

    def test_macro_plot_with_replacement_fields(self):
        exp_image_path = '{}/udg.png'.format(UDGDIR)
        writer = self._get_writer(snapshot=[0] * 8, mock_file_info=True)
        macros = (
            '#UDG0(*f)',
            '#LET(x=7)',
            '#LET(y=0)',
            '#LET(v=1)',
            '#PLOT({x},{y},{v})(f)',
            '#UDGARRAY*f(udg)'
        )
        output = writer.expand(''.join(macros), ASMDIR)
        self._assert_img_equals(output, 'udg', '../{}'.format(exp_image_path))
        exp_udgs = [[Udg(56, [1] + [0] * 7)]]
        self._check_image(writer, exp_udgs, scale=4, path=exp_image_path)

    def test_macro_plot_out_of_range(self):
        exp_image_path = '{}/udg.png'.format(UDGDIR)
        writer = self._get_writer(snapshot=[0] * 8, mock_file_info=True)
        macros = (
            '#UDG0(*f)',
            '#PLOT8,0(f)', # No effect
            '#PLOT0,8(f)', # No effect
            '#UDGARRAY*f(udg)'
        )
        output = writer.expand(''.join(macros), ASMDIR)
        self._assert_img_equals(output, 'udg', '../{}'.format(exp_image_path))
        exp_udgs = [[Udg(56, [0] * 8)]]
        self._check_image(writer, exp_udgs, scale=4, path=exp_image_path)

    def test_macro_plot_invalid(self):
        writer, prefix = CommonSkoolMacroTest.test_macro_plot_invalid(self)
        self._assert_error(writer, '#PLOT1,1(foo)', 'No such frame: "foo"', prefix)

    def test_macro_r(self):
        skool = """
            c00000 LD A,B

            c00007 LD A,C

            c00016 LD A,D

            c00115 LD A,E

            c01114 LD A,H

            ; Routine
            c24576 LD HL,$6003

            ; Data
            b$6003 DEFB 123
             $6004 DEFB 246

            ; Another routine
            c24581 NOP
             24582 NOP

            ; Yet another routine
            c24583 CALL 24581

            ; Another routine still
            c24586 CALL 24581
             24589 JP 24582

            ; The final routine
            c24592 CALL 24582
        """
        writer = self._get_writer(skool=skool, variables=[('one', 1)])

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

        # Arithmetic expression for address
        output = writer.expand('#R(96 * $100 - 5 + (8 + 2) / 2)', ASMDIR)
        self._assert_link_equals(output, '24576.html', '24576')

        # Nested macros: address
        output = writer.expand(nest_macros('#R({})', 24576), ASMDIR)
        self._assert_link_equals(output, '24576.html', '24576')

        # Explicit anchor
        output = writer.expand('#R24576#foo', ASMDIR)
        self._assert_link_equals(output, '24576.html#foo', '24576')

        # Nested macros: anchor
        output = writer.expand(nest_macros('#R#(24576#{})', 'bar'), ASMDIR)
        self._assert_link_equals(output, '24576.html#bar', '24576')

        # Link text
        link_text = 'Testing1'
        output = writer.expand('#R24576({0})'.format(link_text), ASMDIR)
        self._assert_link_equals(output, '24576.html', link_text)

        # Nested macros: link text
        link_text = 'Testing2'
        output = writer.expand(nest_macros('#R24576({})', link_text), ASMDIR)
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

        # Replacement fields
        output = writer.expand('#LET(a=24591)#R({a}+{vars[one]})', ASMDIR)
        self._assert_link_equals(output, '24592.html', '24592')

        # Non-existent reference
        prefix = ERROR_PREFIX.format('R')
        self._assert_error(writer, '#R$ABCD', 'Could not find instruction at $ABCD', prefix)

        # Explicit code ID and non-existent reference
        self._assert_error(writer, '#R$ABCD@main', 'Could not find instruction at $ABCD', prefix)

    def test_macro_r_asm_single_page(self):
        ref = '[Game]\nAsmSinglePage=1'
        skool = 'c40000 LD A,B\n 40001 RET'
        writer = self._get_writer(ref=ref, skool=skool)

        output = writer.expand('#R40000', '')
        self._assert_link_equals(output, 'asm.html#40000', '40000')

        output = writer.expand('#R40001', '')
        self._assert_link_equals(output, 'asm.html#40001', '40001')

    def test_macro_r_other_code(self):
        ref = "[OtherCode:other]"
        skool = """
            @remote=other:$C000,$c003
            c49152 LD DE,0
             49155 RET
        """
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

        # Nested macros: other code with remote entry
        output = writer.expand(nest_macros('#R#(49152@{})', 'other'), ASMDIR)
        self._assert_link_equals(output, '../other/49152.html', 'C000')

    def test_macro_r_with_remote_directive(self):
        ref = '[OtherCode:other]'
        skool = """
            @remote=other:40000,$9c45
            c32768 RET
        """
        for base, case, addr1, addr2 in (
            (0, 0, '40000', '9c45'),
            (BASE_10, 0, '40000', '40005'),
            (BASE_16, 0, '9C40', '9C45'),
            (BASE_16, CASE_UPPER, '9C40', '9C45'),
            (BASE_16, CASE_LOWER, '9c40', '9c45')
        ):
            writer = self._get_writer(ref=ref, skool=skool, base=base, case=case)
            with self.subTest(base=base, case=case):
                self._assert_link_equals(writer.expand('#R40000@other', ASMDIR), '../other/40000.html', addr1)
                self._assert_link_equals(writer.expand('#R40005@other', ASMDIR), '../other/40000.html#40005', addr2)

    def test_macro_r_other_code_asm_single_page(self):
        ref = """
            [Game]
            AsmSinglePage=1
            [OtherCode:other]
        """
        writer = self._get_writer(ref=ref, skool='')

        output = writer.expand('#R40000@other', '')
        self._assert_link_equals(output, 'other/asm.html#40000', '40000')

    def test_macro_r_decimal(self):
        ref = "[OtherCode:other]"
        skool = """
            @remote=other:$C000,$C003
            c32768 LD A,B
             32769 RET
        """
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
        ref = "[OtherCode:other]"
        skool = """
            @remote=other:$C000,$C003
            c32768 LD A,B
             32769 RET
        """
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
        ref = """
            [OtherCode:Other]
            [Paths]
            Other-CodePath=other
        """
        skool = """
            @remote=other:$C000,$C003
            c40970 LD A,B
             40971 RET
        """
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
        ref = "[OtherCode:other]"
        skool = """
            @remote=other:$c000,$c003
            c$a00a LD A,B
             40971 RET
        """
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
        skool = """
            ; Data at 32768
            b32768 DEFS 12345

            ; Routine at 45113
            c45113 RET
        """
        writer = self._get_writer(ref=ref, skool=skool)

        for address in (32768, 45113):
            output = writer.expand('#R{}'.format(address), ASMDIR)
            exp_asm_fname = '{:04X}.html'.format(address)
            self._assert_link_equals(output, exp_asm_fname, str(address))

    def test_macro_r_with_invalid_filename_template(self):
        ref = '[Paths]\nCodeFiles={Address}.html'
        skool = 'b32768 DEFS 12345'
        writer = self._get_writer(ref=ref, skool=skool)
        error_msg = "Unknown field 'Address' in CodeFiles template"
        self._assert_error(writer, '#R32768', error_msg, error=SkoolKitError)

    def test_macro_r_with_custom_address_format(self):
        ref = '[Game]\nAddress=${address:04x}'
        skool = "c40000 LD A,B"
        writer = self._get_writer(ref=ref, skool=skool)

        output = writer.expand('#R40000', ASMDIR)
        self._assert_link_equals(output, '40000.html', '$9c40')

    def test_macro_r_with_custom_address_format_containing_skool_macro(self):
        ref = '[Game]\nAddress=#IF(1)(${address:04X})'
        skool = "c40000 LD A,B"
        writer = self._get_writer(ref=ref, skool=skool)

        output = writer.expand('#R40000', ASMDIR)
        self._assert_link_equals(output, '40000.html', '$9C40')

    def test_macro_r_with_custom_asm_anchor(self):
        ref = '[Game]\nAddressAnchor={address:04x}'
        skool = """
            ; Routine at 40000
            c40000 LD A,B
             40001 RET
        """
        writer = self._get_writer(ref=ref, skool=skool)

        output = writer.expand('#R40001', ASMDIR)
        self._assert_link_equals(output, '40000.html#9c41', '40001')

    def test_macro_r_with_custom_asm_anchor_containing_skool_macro(self):
        ref = '[Game]\nAddressAnchor=#IF({base}==10)({address},{address:04x})'
        skool = """
            ; Routine at 50000
            c50000 LD A,B
             50001 RET
        """
        writer = self._get_writer(ref=ref, skool=skool)

        output = writer.expand('#R50001', ASMDIR)
        self._assert_link_equals(output, '50000.html#c351', '50001')

    def test_macro_r_converts_entry_address_to_custom_asm_anchor(self):
        ref = '[Game]\nAddressAnchor={address:04x}'
        writer = self._get_writer(ref=ref, skool='c40000 RET')

        output = writer.expand('#R40000#40000', ASMDIR)
        self._assert_link_equals(output, '40000.html#9c40', '40000')

    def test_macro_r_with_upper_case_hexadecimal_asm_anchors(self):
        ref = '[Game]\nAddressAnchor={address:04X}'
        skool = """
            ; Routine at 43981
            c43981 LD A,B
             43982 RET
        """
        writer = self._get_writer(ref=ref, skool=skool)

        output = writer.expand('#R43981#43981', ASMDIR)
        self._assert_link_equals(output, '43981.html#ABCD', '43981')

        output = writer.expand('#R43982', ASMDIR)
        self._assert_link_equals(output, '43981.html#ABCE', '43982')

    def test_macro_r_with_invalid_asm_anchor(self):
        ref = '[Game]\nAddressAnchor={address:j}'
        skool = 'c40000 LD A,B\n 40001 RET'
        writer = self._get_writer(ref=ref, skool=skool)
        error_msg = "Failed to format AddressAnchor template: Unknown format code 'j' for object of type 'int'"
        self._assert_error(writer, '#R40001', error_msg, error=SkoolKitError)

    def test_macro_r_invalid(self):
        writer, prefix = CommonSkoolMacroTest.test_macro_r_invalid(self)

        # Non-existent other code reference
        self._assert_error(writer, '#R24576@nonexistent', "Cannot find code path for 'nonexistent' disassembly", error=SkoolKitError)

    def test_macro_scr(self):
        snapshot = [0] * 65536
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)

        fname = 'scr'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#SCR', ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        fname = 'scr2'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#SCR2,0,0,10,10({0})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        fname = 'scr3'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        data = [128, 64, 32, 16, 8, 4, 2, 1]
        attr = 48
        snapshot[16384:18432:256] = data
        snapshot[22528] = attr
        scale = 1
        tindex = 7
        alpha = 64
        x, y, w, h = 1, 2, 5, 6
        macro = '#SCR,0,0,1,1,,,{},{}{{{},{},{},{}}}({})'.format(tindex, alpha, x, y, w, h, fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(attr, data)]]
        self._check_image(writer, udg_array, scale, False, tindex, alpha, x, y, w, h, exp_image_path)

        fname = 'scr4'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        scale = 3
        tindex = 8
        alpha = 128
        x, y, w, h = 0, 0, 1, 1
        df = 0
        af = 32768
        data = snapshot[df:df + 2048:256] = [170] * 8
        attr = snapshot[af] = 56
        values = {'scale': scale, 'x': x, 'y': y, 'w': w, 'h': h, 'df': df, 'af': af, 'tindex': tindex, 'alpha': alpha, 'fname': fname}
        macro = '#SCRx={x},h={h},af={af},tindex={tindex},scale={scale},y={y},alpha={alpha},df={df},w={w}({fname})'.format(**values)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(attr, data)]]
        self._check_image(writer, udg_array, scale, 0, tindex, alpha, path=exp_image_path)

        # Arithmetic expressions
        fname = 'scr5'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        scale = 3
        tindex = 2
        alpha = 192
        df = 0
        af = 6144
        data = snapshot[df:df + 2048:256] = [85] * 8
        attr = snapshot[af] = 57
        crop = (1, 2, 17, 14)
        crop_spec = '{5-4, 2 * 1, width=(2+2)*4+1, height = 7*2}'
        macro = '#SCR(2+1, 0*1, 5-5, (1 + 1) / 2, 1**1, 1^1, 24*256, 4/2, 255&192){}({})'.format(crop_spec, fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(attr, data)]]
        self._check_image(writer, udg_array, scale, 0, tindex, alpha, *crop, exp_image_path)

        # Nested macros
        fname = 'nested'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        scale = 4
        x = 2
        output = writer.expand(nest_macros('#SCR({},,,1,1){{x={}}}({})', scale, x, fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(snapshot[22528], snapshot[16384:18432:256])]]
        self._check_image(writer, udg_array, scale, x=x, width=30, path=exp_image_path)

    def test_macro_scr_with_replacement_fields(self):
        char1 = [1, 2, 3, 4, 5, 6, 7, 8]
        snapshot = [56] * 2048
        snapshot[::256] = char1
        exp_image_path = '{}/scr.png'.format(SCRDIR)
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)
        output = writer.expand('#LET(x=0)#LET(w=15)#SCR(2,{x},0,1,1,0,1){width={w}}', ASMDIR)
        self._assert_img_equals(output, 'scr', '../{}'.format(exp_image_path))
        self._check_image(writer, [[Udg(56, char1)]], 2, width=15, path=exp_image_path)

    def test_macro_scr_with_custom_screenshot_path(self):
        scr_path = 'graphics/screenshots'
        ref = '[Paths]\nScreenshotImagePath={}'.format(scr_path)
        writer = self._get_writer(ref=ref, snapshot=[0] * 23296, mock_file_info=True)

        fname = 'scr'
        exp_image_path = '{}/{}.png'.format(scr_path, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#SCR', ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

    def test_macro_scr_with_custom_image_path_containing_skool_macro(self):
        ref = '[Paths]\nImagePath=#MAP({case})(graphics,2:GRAPHICS)'
        writer = self._get_writer(ref=ref, snapshot=[0] * 23296, mock_file_info=True)

        fname = 'scr'
        exp_image_path = 'graphics/scr/{}.png'.format(fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#SCR', ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

    def test_macro_scr_frames(self):
        snapshot = [n & 255 for n in range(2048)] + [1, 2, 3, 4]
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)
        file_info = writer.file_info
        params = 'w=1,h=1,df=0,af=2048'

        output = writer.expand('#SCRx=0,y=0,{}(*scr1)'.format(params), ASMDIR)
        self.assertEqual(output, '')
        self.assertIsNone(file_info.fname)

        fname = 'scr2'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#SCRx=1,y=0,{}({}*)'.format(params, fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(file_info.fname, exp_image_path)

        fname = 'scr3'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#SCRx=2,y=0,{}({}*scr3_frame)'.format(params, fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(file_info.fname, exp_image_path)

        fname = 'scr'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#SCRscale=2,x=3,y=0,{}{{2,3,8,8}}(*)'.format(params), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(file_info.fname, exp_image_path)

        writer.expand('#UDGARRAY*scr1;scr2;scr3_frame;scr(scr.png)', ASMDIR)
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

        fname = 'scr'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        alt = 'An awesome screenshot'
        output = writer.expand('#SCR(|{})'.format(alt), ASMDIR)
        self._assert_img_equals(output, alt, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        fname = 'screenshot'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        alt = 'Another awesome screenshot'
        output = writer.expand('#SCR({}|{})'.format(fname, alt), ASMDIR)
        self._assert_img_equals(output, alt, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

    def test_macro_scr_with_replacement_field_in_filename(self):
        self._test_image_macro_with_replacement_field_in_filename('#SCR1,0,0,1,1,0,0', SCRDIR, (0,) * 2048)

    def test_macro_table(self):
        src1 = """(data)
            { =h Col1 | =h Col2 | =h,c2 Cols3+4 }
            { =r2 X   | Y       | Za  | Zb }
            {           Y2      | Za2 | =t }
        """
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

        src2 = """(,centre)
            { =h Header }
            { Cell }
        """
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

        writer = self._get_writer(skool='c32768 RET')
        for src, html in ((src1, html1), (src2, html2)):
            output = writer.expand('#TABLE{}\nTABLE#'.format(src))
            self.assertEqual(dedent(html).strip(), output)

        # Cell containing a skool macro
        output = writer.expand('#TABLE { #R32768 } TABLE#', ASMDIR)
        self.assertEqual(output, '<table class="">\n<tr>\n<td class="" colspan="1" rowspan="1"><a href="32768.html">32768</a></td>\n</tr>\n</table>')

        # Empty table
        output = writer.expand('#TABLE TABLE#')
        self.assertEqual(output, '<table class="">\n</table>')

        # Nested macros
        css_class = 'someclass'
        output = writer.expand(nest_macros('#TABLE({}){{ A }}TABLE#', css_class))
        self.assertEqual(output, '<table class="{}">\n<tr>\n<td class="" colspan="1" rowspan="1">A</td>\n</tr>\n</table>'.format(css_class))

    def test_macro_table_with_wrap_flag(self):
        writer = self._get_writer()
        html = '<table class="{}">\n<tr>\n<td class="" colspan="1" rowspan="1">A</td>\n</tr>\n</table>'
        for params, exp_class_name in (('', ''), ('(default)', 'default')):
            for flag in ('nowrap', 'wrapalign'):
                with self.subTest(params=params, flag=flag):
                    output = writer.expand('#TABLE{}<{}> {{ A }} TABLE#'.format(params, flag))
                    self.assertEqual(html.format(exp_class_name), output)

    def test_macro_table_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('TABLE')

        # No end marker
        self._assert_error(writer, '#TABLE { A1 }', 'Missing table end marker: #TABLE { A1 }...')

    def test_macro_udg(self):
        snapshot = [0] * 65536
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)

        fname = 'udg32768_56x4'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDG32768', ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        fname = 'udg40000_2x3'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDG40000,2,3', ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        fname = 'test_udg'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDG32768,2,6,1,0:49152,2({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        fname = 'test_udg2'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        udg_addr = 32768
        attr = 2
        scale = 1
        step = 1
        inc = 0
        mask = 1
        tindex = 1
        alpha = 32
        mask_addr = 32776
        x, y, w, h = 2, 1, 3, 4
        udg_data = [136] * 8
        udg_mask = [255] * 8
        snapshot[udg_addr:udg_addr + 8 * step:step] = udg_data
        snapshot[mask_addr:mask_addr + 8 * step:step] = udg_mask
        macro = '#UDG{0},{1},{2},{3},{4},,,{5},{6},{7}:{8},{9}{{{10},{11},{12},{13}}}({14})'.format(udg_addr, attr, scale, step, inc, mask, tindex, alpha, mask_addr, step, x, y, w, h, fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(attr, udg_data, udg_mask)]]
        self._check_image(writer, udg_array, scale, mask, tindex, alpha, x, y, w, h, exp_image_path)

        fname = 'test_udg3'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        addr = 49152
        attr = 2
        scale = 1
        step = 2
        inc = 0
        mask = 2
        tindex = 3
        alpha = 64
        mask_addr = 49153
        mask_step = 2
        x, y, width, height = 1, 2, 4, 3
        udg_data = [240] * 8
        udg_mask = [248] * 8
        snapshot[addr:addr + 8 * step:step] = udg_data
        snapshot[mask_addr:mask_addr + 8 * mask_step:mask_step] = udg_mask
        params = 'attr={attr},alpha={alpha},step={step},inc={inc},tindex={tindex},addr={addr},mask={mask},scale={scale}'
        mask_spec = ':step={step},addr={mask_addr}'
        crop = '{{x={x},y={y},width={width},height={height}}}'
        macro = ('#UDG' + params + mask_spec + crop + '({fname})').format(**locals())
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(attr, udg_data, udg_mask)]]
        self._check_image(writer, udg_array, scale, mask, tindex, alpha, x, y, width, height, exp_image_path)

        # Arithmetic expressions
        fname = 'test_udg4'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        addr = 49152
        scale = 4
        mask = 1
        x, y, w, h = 1, 2, 4, 3
        udg_data = [240] * 8
        mask_data = [248] * 8
        snapshot[addr:addr + 8] = udg_data + mask_data
        params = '(192*256, attr = (2 + 2) / 2)'
        mask_spec = '(192*256+8,(8-6)/2)'
        crop = '{1*1, 4/2, 2**2, 1+(7+5)/6}'
        macro = '#UDG{}:{}{}({})'.format(params, mask_spec, crop, fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(2, udg_data, mask_data)]]
        self._check_image(writer, udg_array, scale, mask, 0, -1, x, y, w, h, exp_image_path)

        # Nested macros
        fname = 'nested'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        addr = 23296
        scale = 4
        mask = 1
        y = 4
        udg = Udg(56, [137] * 8, [241] * 8)
        snapshot[addr:addr + 16] = udg.data + udg.mask
        macro = nest_macros('#UDG({}):({}){{y={}}}({})', addr, addr + 8, y, fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, [[udg]], scale, mask, y=y, height=28, path=exp_image_path)

    def test_macro_udg_with_replacement_fields(self):
        udg = Udg(56, [137] * 8, [241] * 8)
        snapshot = udg.data + udg.mask
        exp_image_path = '{}/udg.png'.format(UDGDIR)
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)
        output = writer.expand('#LET(d=0)#LET(m=8)#LET(h=31)#UDG({d}):({m}){height={h}}(udg)', ASMDIR)
        self._assert_img_equals(output, 'udg', '../{}'.format(exp_image_path))
        self._check_image(writer, [[udg]], scale=4, mask=1, height=31, path=exp_image_path)

    def test_macro_udg_with_custom_default_udg_filename(self):
        udg_filename = 'udg{addr:04X}_{attr:02X}x{scale}'
        ref = '[Paths]\nUDGFilename={}'.format(udg_filename)
        writer = self._get_writer(ref=ref, snapshot=[0] * 24, mock_file_info=True)

        addr = 16
        attr = 40
        scale = 3
        exp_fname = 'udg0010_28x3'
        exp_image_path = '{}/{}.png'.format(UDGDIR, exp_fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDG{},{},{}'.format(addr, attr, scale), ASMDIR)
        self._assert_img_equals(output, exp_fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

    def test_macro_udg_with_custom_default_udg_filename_specified_by_skool_macro(self):
        udg_filename = '#IF({base}==16)(udg{addr:04X}_{attr:02X}x{scale},udg{addr})'
        ref = '[Paths]\nUDGFilename={}'.format(udg_filename)
        writer = self._get_writer(ref=ref, snapshot=[0] * 18, base=BASE_16, mock_file_info=True)

        addr = 10
        attr = 26
        scale = 2
        exp_fname = 'udg000A_1Ax2'
        exp_image_path = '{}/{}.png'.format(UDGDIR, exp_fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDG{},{},{}'.format(addr, attr, scale), ASMDIR)
        self._assert_img_equals(output, exp_fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

    def test_macro_udg_with_invalid_filename_template(self):
        ref = '[Paths]\nUDGFilename={Address}x{Scale}'
        skool = 'b32768 DEFS 8'
        writer = self._get_writer(ref=ref, skool=skool)
        error_msg = "Unknown field 'Address' in UDGFilename template"
        self._assert_error(writer, '#UDG32768,5,2', error_msg, error=SkoolKitError)

    def test_macro_udg_with_custom_udg_image_path(self):
        udg_path = 'graphics/udgs'
        ref = '[Paths]\nUDGImagePath={}'.format(udg_path)
        writer = self._get_writer(ref=ref, snapshot=[0] * 8, mock_file_info=True)

        fname = 'udg0'
        exp_image_path = '{}/{}.png'.format(udg_path, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDG0({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

    def test_macro_udg_with_custom_image_path_containing_skool_macro(self):
        udg_array = [[Udg(56, [0] * 8)]]
        ref = '[Paths]\nImagePath=#MAP({case})(graphics,2:GRAPHICS)'
        writer = self._get_writer(ref=ref, snapshot=[0] * 8, mock_file_info=True)

        fname = 'udg0'
        exp_image_path = 'graphics/udgs/{}.png'.format(fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDG0({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

    def test_macro_udg_with_mask(self):
        udg_data = [240] * 8
        udg_mask = [248] * 8
        udg_array_no_mask = [[Udg(56, udg_data)]]
        udg_array = [[Udg(56, udg_data, udg_mask)]]
        scale = 4
        writer = self._get_writer(snapshot=udg_data + udg_mask, mock_file_info=True)

        # No mask parameter, no mask defined
        fname = 'udg0_56x4'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDG0', ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, udg_array_no_mask, scale, mask=0, path=exp_image_path)

        # mask=1, no mask defined
        output = writer.expand('#UDG0,mask=1', ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, udg_array_no_mask, scale, mask=0, path=exp_image_path)

        # mask=0, mask defined
        output = writer.expand('#UDG0,mask=0:8', ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, udg_array_no_mask, scale, mask=0, path=exp_image_path)

        # No mask parameter, mask defined
        output = writer.expand('#UDG0:8', ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, udg_array, scale, mask=1, path=exp_image_path)

        # mask=2, mask defined
        output = writer.expand('#UDG0,mask=2:8', ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, udg_array, scale, mask=2, path=exp_image_path)

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

        fname = 'udg2'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDG8(udg2*)', ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(file_info.fname, exp_image_path)

        fname = 'udg3'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDG16({}*udg3_frame)'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(file_info.fname, exp_image_path)

        fname = 'udg24_4x6'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDG24,4,6:0{5,6,32,32}(*)', ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(file_info.fname, exp_image_path)

        writer.expand('#UDGARRAY*udg1;udg2;udg3_frame;udg24_4x6(udgs.png)', ASMDIR)
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
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        alt = 'bar'
        output = writer.expand('#UDG0({}|{})'.format(fname, alt), ASMDIR)
        self._assert_img_equals(output, alt, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        fname = 'udg0_56x4'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        alt = 'An awesome UDG'
        output = writer.expand('#UDG0(|{})'.format(alt), ASMDIR)
        self._assert_img_equals(output, alt, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

    def test_macro_udg_with_replacement_field_in_filename(self):
        self._test_image_macro_with_replacement_field_in_filename('#UDG0')

    def test_macro_udgarray(self):
        snapshot = [0] * 65536
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)

        fname = 'test_udg_array'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY2;32768-32785-1-16({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        fname = 'test_udg_array2'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY8,56,2,256,0;32768;32769;32770;32771;32772x12({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        fname = 'test_udg_array3'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        udg_addr = 32768
        mask_addr = 32769
        width = 2
        attr = 5
        scale = 1
        step = 256
        inc = 0
        tindex = 1
        alpha = 100
        x, y, w, h = 4, 6, 8, 5
        udg_data = [195] * 8
        udg_mask = [255] * 8
        snapshot[udg_addr:udg_addr + 8 * step:step] = udg_data
        snapshot[mask_addr:mask_addr + 8 * step:step] = udg_mask
        macro = '#UDGARRAY{},{},{},{},{},,,,{},{};{}x4:{}x4{{{},{},{},{}}}({})'.format(width, attr, scale, step, inc, tindex, alpha, udg_addr, mask_addr, x, y, w, h, fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(attr, udg_data, udg_mask)] * width] * 2
        self._check_image(writer, udg_array, scale, True, tindex, alpha, x, y, w, h, exp_image_path)

        # Separately specified attributes
        fname = 'attrs'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY2;0,1;0,2;0,3;0,4({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        exp_udgs = [[Udg(1, [0] * 8), Udg(2, [0] * 8)], [Udg(3, [0] * 8), Udg(4, [0] * 8)]]
        self._check_image(writer, exp_udgs, path=exp_image_path)

        # Flip
        fname = 'test_udg_array4'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        udg = Udg(56, [128, 64, 32, 16, 8, 4, 2, 1])
        udg_addr = 40000
        snapshot[udg_addr:udg_addr + 8] = udg.data
        output = writer.expand('#UDGARRAY1,,,,,1;{}({})'.format(udg_addr, fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg.flip(1)
        self._check_image(writer, [[udg]], 2, False, 0, -1, 0, 0, 16, 16, exp_image_path)

        # Rotate
        fname = 'test_udg_array5'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        udg = Udg(56, [128, 64, 32, 16, 8, 4, 2, 1])
        udg_addr = 50000
        snapshot[udg_addr:udg_addr + 8] = udg.data
        output = writer.expand('#UDGARRAY1,,,,,,2;{}({})'.format(udg_addr, fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg.rotate(2)
        self._check_image(writer, [[udg]], 2, False, 0, -1, 0, 0, 16, 16, exp_image_path)

        # Keyword arguments
        fname = 'test_udg_array6'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        udg_addr = 32768
        mask_addr = 32769
        width = 2
        attr = 5
        scale = 1
        step = 256
        inc = 0
        mask = 1
        tindex = 6
        alpha = 16
        x, y, w, h = 4, 6, 8, 5
        udg_data = [195] * 8
        udg_mask = [255] * 8
        snapshot[udg_addr:udg_addr + 8 * step:step] = udg_data
        snapshot[mask_addr:mask_addr + 8 * step:step] = udg_mask
        params = 'attr={attr},alpha={alpha},step={step},inc={inc},tindex={tindex},mask={mask},scale={scale}'
        udg_spec = ';{udg_addr}x4,step={step}'
        mask_spec = ':{mask_addr}x4,step={step}'
        crop = '{{x={x},y={y},width={w},height={h}}}'
        macro = ('#UDGARRAY{width},' + params + udg_spec + mask_spec + crop + '({fname})').format(**locals())
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(attr, udg_data, udg_mask)] * width] * 2
        self._check_image(writer, udg_array, scale, mask, tindex, alpha, x, y, w, h, exp_image_path)

        # Arithmetic expressions: main params, UDG address range, cropping spec
        fname = 'test_udg_array7'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        udg1 = Udg(40, [128, 64, 32, 16, 8, 4, 2, 1])
        udg2 = Udg(40, [64, 32, 16, 8, 4, 2, 1, 128])
        udg3 = Udg(40, [32, 16, 8, 4, 2, 1, 128, 64])
        udg_addr = '40000-(40000+(4+4)*2)-(10-2)x(2-1)'
        snapshot[40000:40008] = udg1.data
        snapshot[40008:40016] = udg2.data
        snapshot[40016:40024] = udg3.data
        scale = 2
        mask = 0
        x, y, w, h = 3, 4, 42, 8
        crop = '{x=1+2,y = (1 + 1) * 2, width = 6 * 7, height=2**3}'
        output = writer.expand('#UDGARRAY(2+1,(4 + 1) * 8);{}{}({})'.format(udg_addr, crop, fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, [[udg1, udg2, udg3]], scale, mask, 0, -1, x, y, w, h, exp_image_path)

        # Arithmetic expressions: UDG spec, mask spec
        fname = 'test_udg_array8'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        udg = Udg(40, [240] * 8, [248] * 8)
        snapshot[30000:30016] = udg.data + udg.mask
        udg_spec = '(10000*3),((2+3)*8, inc=5-5)'
        mask_spec = '(10000*3+8),((12-8)/4)'
        scale = 2
        mask = 1
        output = writer.expand('#UDGARRAY1;{}:{}({})'.format(udg_spec, mask_spec, fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, [[udg]], scale, mask, path=exp_image_path)

        # Nested macros
        fname = 'nested'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        udg_addr = 23296
        scale = 2
        mask = 1
        x = 1
        udg = Udg(56, [45] * 8, [173] * 8)
        snapshot[udg_addr:udg_addr + 16] = udg.data + udg.mask
        macro = nest_macros('#UDGARRAY1;({0})-({0})-({1})-({1})x({1}):({2})-({2})-({1})-({1})x({1}){{x={3}}}({4})', udg_addr, 1, udg_addr + 8, x, fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, [[udg]], scale, mask, x=x, width=15, path=exp_image_path)

        # #() macro
        fname = 'thing'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        udg1 = Udg(43, [17] * 8)
        udg2 = Udg(5, [178] * 8)
        snapshot[20000:20018] = [udg1.attr] + udg1.data + [udg2.attr] + udg2.data
        scale = 2
        output = writer.expand('#UDGARRAY#(2#FOR20000,20009,9||n|;(n+1),#PEEKn||)({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, [[udg1, udg2]], scale, path=exp_image_path)

    def test_macro_udgarray_with_attribute_addresses(self):
        snapshot = [0] * 38
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)

        # Individual addresses and address range
        fname = 'attr_addrs'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        attrs = [1, 2, 3, 4]
        snapshot[32:32 + len(attrs)] = attrs
        exp_udgs = [[Udg(a, [0] * 8) for a in attrs]]
        output = writer.expand('#UDGARRAY4;0-24-8@32;33;34-35({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, exp_udgs, path=exp_image_path)

        # Address with multiplier
        fname = 'attr_addrs_mult'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        snapshot[32] = 4
        exp_udgs = [[Udg(4, [0] * 8)]] * 3
        output = writer.expand('#UDGARRAY1;0;8;16@32x3({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, exp_udgs, path=exp_image_path)

        # Address range with step
        fname = 'attr_addrs_step'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        attrs = [12, 13, 14]
        step = 2
        snapshot[32:32 + step * len(attrs):step] = attrs
        exp_udgs = [[Udg(a, [0] * 8) for a in attrs]]
        output = writer.expand('#UDGARRAY3;0;8;16@32-36-{}({})'.format(step, fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, exp_udgs, path=exp_image_path)

        # Address range with horizontal step and vertical step
        fname = 'attr_addrs_hstep_vstep'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        attrs = [15, 16, 17, 18]
        snapshot[32:34] = attrs[:2]
        snapshot[36:38] = attrs[2:]
        exp_udgs = [[Udg(a, [0] * 8) for a in attrs[:2]], [Udg(a, [0] * 8) for a in attrs[2:]]]
        output = writer.expand('#UDGARRAY2;0-24-8@32-37-1-4({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, exp_udgs, path=exp_image_path)

        # Address range too long
        fname = 'attr_addrs_long'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        attrs = [19, 20, 21]
        snapshot[32:32 + len(attrs)] = attrs
        exp_udgs = [[Udg(a, [0] * 8) for a in attrs]]
        output = writer.expand('#UDGARRAY3;0;8;16@32-36({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, exp_udgs, path=exp_image_path)

        # Address range too short
        fname = 'attr_addrs_short'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        attrs = [22, 23]
        snapshot[32:32 + len(attrs)] = attrs
        exp_udgs = [[Udg(a, [0] * 8) for a in attrs] + [Udg(56, [0] * 8)]]
        output = writer.expand('#UDGARRAY3;0;8;16@32-33({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, exp_udgs, path=exp_image_path)

    def test_macro_udgarray_with_replacement_fields(self):
        udg = Udg(48, [137] * 8, [241] * 8)
        snapshot = udg.data + udg.mask + udg.data + udg.mask + [48]
        exp_image_path = '{}/img.png'.format(UDGDIR)
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)
        lets = '#LET(w=3)#LET(a=0)#LET(m=8)#LET(s=1)#LET(aa=32)#LET(h=15)'
        macro = '#UDGARRAY({w});({a}),(,{s}):({m}),({s});({a})-({a}+16)-16x({s}):({m})x2@({aa})x3{height={h}}(img)'
        output = writer.expand(lets + macro, ASMDIR)
        self._assert_img_equals(output, 'img', '../{}'.format(exp_image_path))
        self._check_image(writer, [[udg] * 3], scale=2, mask=1, height=15, path=exp_image_path)

    def test_macro_udgarray_with_short_array(self):
        writer = self._get_writer(snapshot=[0] * 24, mock_file_info=True)

        # Width 2, 2 rows, 1 UDG in bottom row - padded
        fname = 'short'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        udg = Udg(56, [0] * 8)
        fill_udg = Udg(66, [129, 66, 36, 24, 24, 36, 66, 128])
        exp_udgs = [[udg, udg], [udg, fill_udg]]
        output = writer.expand('#UDGARRAY2;0;8;16({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, exp_udgs, path=exp_image_path)

        # Width 3, 1 row, 2 UDGs - no padding
        fname = 'short2'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        udg = Udg(56, [0] * 8)
        exp_udgs = [[udg, udg]]
        output = writer.expand('#UDGARRAY3;0;8({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, exp_udgs, path=exp_image_path)

    def test_macro_udgarray_with_custom_udg_image_path(self):
        udg_path = 'udg_images'
        ref = '[Paths]\nUDGImagePath={}'.format(udg_path)
        writer = self._get_writer(ref=ref, snapshot=[0] * 8, mock_file_info=True)

        fname = 'udgarray0'
        exp_image_path = '{}/{}.png'.format(udg_path, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY1;0({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

    def test_macro_udgarray_with_flash(self):
        writer = self._get_writer(snapshot=[0] * 8, mock_file_info=True)

        # No flash
        fname = 'udgarray_no_flash'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY1,56;0({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        # Flash: different INK and PAPER
        fname = 'udgarray_flash1'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY1,184;0({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        # Flash: same INK and PAPER
        fname = 'udgarray_flash2'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY1,128;0({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        # Flash: cropped
        fname = 'udgarray_flash3'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY2;0,184;0,56{{16}}({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

    def test_macro_udgarray_with_mask(self):
        udg_data = [15] * 8
        udg_mask = [31] * 8
        udg_array_no_mask = [[Udg(56, udg_data)]]
        udg_array = [[Udg(56, udg_data, udg_mask)]]
        scale = 2
        writer = self._get_writer(snapshot=udg_data + udg_mask, mock_file_info=True)

        # No mask parameter, no mask defined
        fname = 'udgarray'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY1;0({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, udg_array_no_mask, scale, mask=0, path=exp_image_path)

        # mask=1, no mask defined
        fname = 'udgarray2'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY1,mask=1;0({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, udg_array_no_mask, scale, mask=0, path=exp_image_path)

        # mask=0, mask defined
        fname = 'udgarray3'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY1,mask=0;0:8({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, udg_array_no_mask, scale, mask=0, path=exp_image_path)

        # No mask parameter, mask defined
        fname = 'udgarray4'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY1;0:8({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, udg_array, scale, mask=1, path=exp_image_path)

        # mask=2, mask defined
        fname = 'udgarray5'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY1,mask=2;0:8({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, udg_array, scale, mask=2, path=exp_image_path)

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
        macro2 = '#UDGARRAY1,,1;{},{}(bar*)'.format(udg2_addr, udg2.attr)
        macro3 = '#UDGARRAY1;{},{}(baz*qux)'.format(udg3_addr, udg3.attr)

        output = writer.expand(macro1, ASMDIR)
        self.assertEqual(output, '')

        fname = 'bar'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand(macro2, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        fname = 'baz'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand(macro3, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        fname = 'test_udg_array_frames'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        delay1 = 93
        macro4 = '#UDGARRAY*foo,{};bar,,2,3;qux,(delay=5+8*2-12/3)({})'.format(delay1, fname)
        output = writer.expand(macro4, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        frame1 = Frame([[udg1]], 2, delay=delay1)
        frame2 = Frame([[udg2]], 1, delay=delay1, x_offset=2, y_offset=3) # Same delay as frame1
        frame3 = Frame([[udg3]], 2, delay=17)                             # Offsets revert to (0, 0)
        exp_frames = [frame1, frame2, frame3]
        self._check_animated_image(writer.image_writer, exp_frames)

    def test_macro_udgarray_frames_with_replacement_fields(self):
        udg1, udg2 = Udg(23, [101] * 8), Udg(47, [35] * 8)
        snapshot = udg1.data + udg2.data
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)
        writer.expand('#UDGARRAY1;0,23(*foo)', ASMDIR)
        writer.expand('#UDGARRAY1,,1;8,47(*bar)', ASMDIR)
        writer.expand('#LET(d=50) #LET(x=1) #LET(y=2)')

        exp_image_path = '{}/img.png'.format(UDGDIR)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY*foo,({d});bar,(x={x},y={y})(img)', ASMDIR)
        self._assert_img_equals(output, 'img', exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        frame1 = Frame([[udg1]], 2, delay=50)
        frame2 = Frame([[udg2]], 1, delay=50, x_offset=1, y_offset=2)
        exp_frames = [frame1, frame2]
        self._check_animated_image(writer.image_writer, exp_frames)

    def test_macro_udgarray_frames_invalid(self):
        writer, prefix = CommonSkoolMacroTest.test_macro_udgarray_frames_invalid(self)
        self._assert_error(writer, '#UDGARRAY*foo(bar)', 'No such frame: "foo"', prefix)
        self._assert_error(writer, '#UDG0,,1(f*) #UDG0,,2(g*) #UDGARRAY*f;g(a)', "Frame 'g' (16x16) is larger than the first frame (8x8)", prefix)

    def test_macro_udgarray_alt_text(self):
        writer = self._get_writer(snapshot=[0] * 8, mock_file_info=True)

        fname = 'foo'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        alt = 'bar'
        output = writer.expand('#UDGARRAY1;0({}|{})'.format(fname, alt), ASMDIR)
        self._assert_img_equals(output, alt, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        fname = 'baz'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        frame = 'qux'
        alt = 'xyzzy'
        output = writer.expand('#UDGARRAY1;0({}*{}|{})'.format(fname, frame, alt), ASMDIR)
        self._assert_img_equals(output, alt, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        fname = 'flip'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        alt = 'flop*flup'
        output = writer.expand('#UDGARRAY1;0({}|{})'.format(fname, alt), ASMDIR)
        self._assert_img_equals(output, alt, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        fname = 'animated'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        alt = 'Animated'
        writer.expand('#UDGARRAY1;0(*frame1)', ASMDIR)
        writer.expand('#UDGARRAY1;0(*frame2)', ASMDIR)
        output = writer.expand('#UDGARRAY*frame1;frame2({}|{})'.format(fname, alt), ASMDIR)
        self._assert_img_equals(output, alt, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

    def test_macro_udgarray_with_replacement_field_in_filename(self):
        self._test_image_macro_with_replacement_field_in_filename('#UDGARRAY1;0')

    def test_macro_udgtable(self):
        src = """(data)
            { =h Col1 | =h Col2 | =h,c2 Cols3+4 }
            { =r2 X   | Y       | Za  | Zb }
            {           Y2      | Za2 | =t }
        """
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
        output = writer.expand('#UDGTABLE{}\nUDGTABLE#'.format(src))
        self.assertEqual(dedent(html).strip(), output)

        # Empty table
        output = writer.expand('#UDGTABLE UDGTABLE#')
        self.assertEqual(output, '<table class="">\n</table>')

        # Nested macros
        css_class = 'someclass'
        output = writer.expand(nest_macros('#UDGTABLE({}){{ A }}UDGTABLE#', css_class))
        self.assertEqual(output, '<table class="{}">\n<tr>\n<td class="" colspan="1" rowspan="1">A</td>\n</tr>\n</table>'.format(css_class))

    def test_macro_udgtable_with_wrap_flag(self):
        writer = self._get_writer()
        html = '<table class="{}">\n<tr>\n<td class="" colspan="1" rowspan="1">A</td>\n</tr>\n</table>'
        for params, exp_class_name in (('', ''), ('(default)', 'default')):
            for flag in ('nowrap', 'wrapalign'):
                with self.subTest(params=params, flag=flag):
                    output = writer.expand('#UDGTABLE{}<{}> {{ A }} TABLE#'.format(params, flag))
                    self.assertEqual(html.format(exp_class_name), output)

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

class HtmlWriterOutputTestCase(HtmlWriterTestCase):
    def _assert_content_equal(self, exp_content, fpath):
        self.assertEqual(dedent(exp_content).strip(), self.files[fpath])

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
        if isinstance(subs['header'], str):
            subs['header'] = ('', subs['header'])
        subs.setdefault('name', basename(self.skoolfile)[:-6])
        subs.setdefault('path', '../')
        subs.setdefault('map', '{}maps/all.html'.format(subs['path']))
        subs.setdefault('script', '<script type="text/javascript" src="{}"></script>'.format(js) if js else '')
        subs.setdefault('title', subs['header'][1])
        subs.setdefault('logo', subs['name'])
        footer = subs.get('footer', BARE_FOOTER)
        prev_up_next_lines = []
        if 'up' in subs:
            subs['prev_link'] = ''
            subs['up_link'] = 'Up: <a href="{map}#{up}">Map</a>'.format(**subs)
            subs['next_link'] = ''
            if 'prev' in subs:
                if 'prev_text' in subs:
                    subs['prev_link'] = 'Prev: <a href="{}.html">{}</a>'.format(subs['prev'], subs['prev_text'])
                else:
                    subs['prev_link'] = 'Prev: <a href="{0}.html">{0:05d}</a>'.format(subs['prev'])
            if 'next' in subs:
                if 'next_text' in subs:
                    subs['next_link'] = 'Next: <a href="{}.html">{}</a>'.format(subs['next'], subs['next_text'])
                else:
                    subs['next_link'] = 'Next: <a href="{0}.html">{0:05d}</a>'.format(subs['next'])
            prev_up_next = PREV_UP_NEXT.format(**subs)
            prev_up_next_lines = prev_up_next.split('\n')
        if index:
            header_template = INDEX_HEADER
        elif subs['header'][0]:
            header_template = PREFIX_HEADER
        else:
            header_template = HEADER
        t_html_lines = header_template.format(**subs).split('\n')
        t_html_lines.extend(prev_up_next_lines)
        t_html_lines.extend(body_lines)
        t_html_lines.extend(prev_up_next_lines)
        t_html_lines.extend(footer.split('\n'))
        if trim:
            d_html_lines = [line for line in d_html_lines if line]
            t_html_lines = [line for line in t_html_lines if line]
        self.assertEqual(t_html_lines, d_html_lines)

class HtmlOutputTest(HtmlWriterOutputTestCase):
    def _assert_title_equals(self, fname, title, header):
        html = self._read_file(fname)
        name = self.skoolfile[:-6]
        self.assertIn('<title>{}: {}</title>'.format(name, title), html)
        self.assertIn('<td class="page-header">{}</td>'.format(header), html)

    def _test_Game_parameter_containing_skool_macro(self, param, value='#IF({html})(PASS,FAIL)', exp_value='PASS', extra=''):
        ref = """
            [Game]
            {0}={1}
            {2}

            [Template:Asm-c]
            {{Game[{0}]}}
        """.format(param, value, extra)
        writer = self._get_writer(ref=ref, skool='c40000 RET')
        writer.write_asm_entries()
        self._assert_content_equal(exp_value, join(ASMDIR, '40000.html'))

    def _test_Page_parameter_containing_skool_macro(self, param, value='#IF({html})(PASS,FAIL)', exp_value='PASS', extra=''):
        ref = """
            [Page:Custom]
            {0}={1}
            {2}

            [Template:Custom]
            {{Page[{0}]}}
        """.format(param, value, extra)
        writer = self._get_writer(ref=ref)
        writer.write_page('Custom')
        self._assert_content_equal(exp_value, 'Custom.html')

    def _test_MemoryMap_parameter_containing_skool_macro(self, param, value='#IF({html})(PASS,FAIL)', exp_value='PASS'):
        skool = """
            @label=START
            c50000 RET
        """
        ref = """
            [MemoryMap:Custom]
            EntryTypes=c
            {0}={1}

            [Template:Custom]
            {{MemoryMap[{0}]}}
        """.format(param, value)
        writer = self._get_writer(ref=ref, skool=skool, asm_labels=True)
        writer.write_map('Custom')
        self._assert_content_equal(exp_value, 'maps/Custom.html')

    def test_expand_directives(self):
        skool = """
            @expand=#DEFINE2(MIN,#IF({0}<{1})({0},{1}))
            @expand=#LET(foo=1)
            ; Routine
            ;
            ; foo=#EVAL({foo}); min(1,2)=#MIN(1,2)
            c32768 RET
        """
        writer = self._get_writer(skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">32768: Routine</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            <div class="paragraph">
            foo=1; min(1,2)=1
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="32768"></span>32768</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at 32768',
            'body_class': 'Asm-c',
            'up': '32768',
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '32768.html'), subs)

    def test_expand_directives_over_multiple_lines(self):
        skool = """
            @expand=#LET(start=1)
            @expand=#DEFINE2(COUNT,
            @expand=+#FOR({},{})(n,n,-)
            @expand=+)
            @expand=#LET(end=5)
            ; Routine
            ;
            ; start=#EVAL({start}); end=#EVAL({end});
            ; count(start,end)=#COUNT({start},{end})
            c32768 RET
        """
        writer = self._get_writer(skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">32768: Routine</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            <div class="paragraph">
            start=1; end=5; count(start,end)=1-2-3-4-5
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="32768"></span>32768</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at 32768',
            'body_class': 'Asm-c',
            'up': '32768',
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '32768.html'), subs)

    def test_expand_directive_with_invalid_macro(self):
        skool = """
            @expand=#N(x)
            c32768 RET
        """
        with self.assertRaisesRegex(SkoolParsingError, "^@expand failed to expand '#N\(x\)': Error while parsing #N macro: Cannot parse integer 'x' in parameter string: 'x'$"):
            self._get_writer(skool=skool)

    def test_expand_directive_with_unexpandable_macro(self):
        skool = """
            @expand=#R32768
            c32768 RET
        """
        with self.assertRaisesRegex(SkoolKitError, "^@expand failed to expand '#R32768'$"):
            self._get_writer(skool=skool)

    def test_macro_pc(self):
        skool = """
            ; Code at #PC
            ;
            ; Description of the routine at #PC.
            ;
            ; A Input to the routine at #PC
            ;
            ; And so the routine at #PC begins.
            c30000 XOR A ; First instruction at #PC.
            ; The next instruction is at #PC.
             30001 SUB B ; Second instruction at #PC.
             30002 RET   ; Final instruction at #PC.
            ; End comment after the instruction at #PC.

            ; Data at #PC
            b30003 DEFB 0 ; A byte (#PEEK(#PC)) at #PC.
             30004 DEFB 1 ; Another byte (#PEEK(#PC)) at #PC.
        """
        writer = self._get_writer(skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">30000: Code at 30000</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            <div class="paragraph">
            Description of the routine at 30000.
            </div>
            </div>
            <table class="input">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            <tr>
            <td class="register">A</td>
            <td class="register-desc">Input to the routine at 30000</td>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="5">
            <span id="30000"></span>
            <div class="comments">
            <div class="paragraph">
            And so the routine at 30000 begins.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="30000"></span>30000</td>
            <td class="instruction">XOR A</td>
            <td class="comment-1" rowspan="1">First instruction at 30000.</td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="5">
            <span id="30001"></span>
            <div class="comments">
            <div class="paragraph">
            The next instruction is at 30001.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-1"><span id="30001"></span>30001</td>
            <td class="instruction">SUB B</td>
            <td class="comment-1" rowspan="1">Second instruction at 30001.</td>
            </tr>
            <tr>
            <td class="address-1"><span id="30002"></span>30002</td>
            <td class="instruction">RET</td>
            <td class="comment-1" rowspan="1">Final instruction at 30002.</td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="comments">
            <div class="paragraph">
            End comment after the instruction at 30002.
            </div>
            </div>
            </td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at 30000',
            'body_class': 'Asm-c',
            'up': '30000',
            'next': 30003,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '30000.html'), subs)

        content = """
            <div class="description">30003: Data at 30003</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-1"><span id="30003"></span>30003</td>
            <td class="instruction">DEFB 0</td>
            <td class="comment-1" rowspan="1">A byte (0) at 30003.</td>
            </tr>
            <tr>
            <td class="address-1"><span id="30004"></span>30004</td>
            <td class="instruction">DEFB 1</td>
            <td class="comment-1" rowspan="1">Another byte (1) at 30004.</td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Data',
            'title': 'Data at 30003',
            'body_class': 'Asm-b',
            'prev': 30000,
            'up': '30003',
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '30003.html'), subs)

        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page">Page</th>
            <th class="map-byte">Byte</th>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page">117</td>
            <td class="map-byte">48</td>
            <td class="map-c"><span id="30000"></span><a href="../asm/30000.html">30000</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30000.html">Code at 30000</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-page">117</td>
            <td class="map-byte">51</td>
            <td class="map-b"><span id="30003"></span><a href="../asm/30003.html">30003</a></td>
            <td class="map-b-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30003.html">Data at 30003</a></div>
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

    def test_parameter_AsmSinglePage_containing_skool_macro(self):
        self._test_Game_parameter_containing_skool_macro('AsmSinglePage', '#IF({html})(0,1)', '0')

    def test_parameter_Bytes_blank_with_assembled_code(self):
        skool = """
            @assemble=2
            ; Routine at 32768
            c32768 RET
        """
        writer = self._get_writer(skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">32768: Routine at 32768</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="32768"></span>32768</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at 32768',
            'body_class': 'Asm-c',
            'up': '32768',
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '32768.html'), subs)

    def test_parameter_Bytes_blank_with_assembled_code_produces_blank_output(self):
        skool = """
            @assemble=2
            c32768 RET
        """
        ref = """
            [Template:Asm]
            <# foreach($i,entry[instructions]) #>
            {$i[address]} [{$i[bytes]:{Game[Bytes]}}] {$i[operation]}
            <# endfor #>
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal('32768 [] RET', 'asm/32768.html')

    def test_parameter_Bytes_with_assembled_code_and_data(self):
        ref = """
            [Game]
            Bytes=02X
        """
        skool = """
            @assemble=2
            ; Routine at 32768
            c32768 LD BC,(0)
             32772 LD BC,0
             32775 LD B,0
             32777 DEFB 0
             32778 DEFM "0"
             32779 DEFS 1
             32780 DEFW 0
             32782 RET
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">32768: Routine at 32768</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="32768"></span>32768</td>
            <td class="bytes">ED4B0000</td>
            <td class="instruction">LD BC,(0)</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="address-1"><span id="32772"></span>32772</td>
            <td class="bytes">010000</td>
            <td class="instruction">LD BC,0</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="address-1"><span id="32775"></span>32775</td>
            <td class="bytes">0600</td>
            <td class="instruction">LD B,0</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="address-1"><span id="32777"></span>32777</td>
            <td class="bytes"></td>
            <td class="instruction">DEFB 0</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="address-1"><span id="32778"></span>32778</td>
            <td class="bytes"></td>
            <td class="instruction">DEFM "0"</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="address-1"><span id="32779"></span>32779</td>
            <td class="bytes"></td>
            <td class="instruction">DEFS 1</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="address-1"><span id="32780"></span>32780</td>
            <td class="bytes"></td>
            <td class="instruction">DEFW 0</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="address-1"><span id="32782"></span>32782</td>
            <td class="bytes">C9</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at 32768',
            'body_class': 'Asm-c',
            'up': '32768',
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '32768.html'), subs)

    def test_parameter_Bytes_with_data(self):
        ref = """
            [Game]
            Bytes=02X
        """
        skool = """
            @assemble=1
            ; Data at 32768
            b32768 DEFB 0
             32769 DEFM "0"
             32770 DEFS 1
             32771 DEFW 0
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">32768: Data at 32768</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-1"><span id="32768"></span>32768</td>
            <td class="instruction">DEFB 0</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="address-1"><span id="32769"></span>32769</td>
            <td class="instruction">DEFM "0"</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="address-1"><span id="32770"></span>32770</td>
            <td class="instruction">DEFS 1</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="address-1"><span id="32771"></span>32771</td>
            <td class="instruction">DEFW 0</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Data',
            'title': 'Data at 32768',
            'body_class': 'Asm-b',
            'up': '32768',
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '32768.html'), subs)

    def test_parameter_Bytes_with_unassembled_code(self):
        ref = """
            [Game]
            Bytes=02X
        """
        skool = """
            @assemble=1
            ; Routine at 32768
            c32768 RET
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">32768: Routine at 32768</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="32768"></span>32768</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at 32768',
            'body_class': 'Asm-c',
            'up': '32768',
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '32768.html'), subs)

    def test_parameter_Bytes_containing_skool_macro(self):
        ref = """
            [Game]
            Bytes=02#MAP({case})(X,1:x)
            [Template:Asm]
            <# foreach($i,entry[instructions]) #>
            {$i[address]} {$i[bytes]:{Game[Bytes]}} {$i[operation]}
            <# endfor #>
        """
        skool = """
            @assemble=2
            c32768 RET
        """
        writer = self._get_writer(ref=ref, skool=skool, case=CASE_LOWER)
        writer.write_asm_entries()
        self._assert_content_equal('32768 c9 ret', 'asm/32768.html')

    def test_parameter_Copyright_containing_skool_macro(self):
        self._test_Game_parameter_containing_skool_macro('Copyright')

    def test_parameter_DisassemblyTableNumCols(self):
        ref = """
            [Game]
            DisassemblyTableNumCols=100
        """
        skool = """
            ; Routine at 50000
            ;
            ; .
            ;
            ; .
            ;
            ; It begins here.
            c50000 RET
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">50000: Routine at 50000</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="100">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="100">
            <span id="50000"></span>
            <div class="comments">
            <div class="paragraph">
            It begins here.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="50000"></span>50000</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at 50000',
            'body_class': 'Asm-c',
            'up': '50000',
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '50000.html'), subs)

    def test_parameter_DisassemblyTableNumCols_containing_skool_macro(self):
        self._test_Game_parameter_containing_skool_macro('DisassemblyTableNumCols')

    def test_parameter_Font_containing_skool_macro(self):
        self._test_Game_parameter_containing_skool_macro('Font')

    def test_parameter_Game_containing_skool_macro(self):
        self._test_Game_parameter_containing_skool_macro('Game')

    def test_parameter_InputRegisterTableHeader_containing_skool_macro(self):
        self._test_Game_parameter_containing_skool_macro('InputRegisterTableHeader')

    def test_parameter_Game_JavaScript_containing_skool_macro(self):
        self._test_Game_parameter_containing_skool_macro('JavaScript')

    def test_parameter_LinkInternalOperands_0(self):
        ref = '[Game]\nLinkInternalOperands=0'
        skool = """
            ; Routine at 30000
            c30000 CALL 30003
             30003 JP 30006
             30006 DJNZ 30006
             30009 JR 30000
        """
        writer = self._get_writer(ref=ref, skool=skool)
        self.assertFalse(writer.link_internal_operands)
        writer.write_asm_entries()
        html = self._read_file(join(ASMDIR, '30000.html'), True)
        line_no = 33
        for inst, address in (
            ('CALL', 30003),
            ('JP', 30006),
            ('DJNZ', 30006),
            ('JR', 30000)
        ):
            operation = '{} {}'.format(inst, address)
            self.assertEqual(html[line_no], '<td class="instruction">{}</td>'.format(operation))
            line_no += 5

    def test_parameter_LinkInternalOperands_1(self):
        ref = '[Game]\nLinkInternalOperands=1'
        skool = """
            ; Routine at 40000
            c40000 CALL 40003
             40003 JP 40006
             40006 DJNZ 40006
             40009 JR 40000
        """
        writer = self._get_writer(ref=ref, skool=skool)
        self.assertTrue(writer.link_internal_operands)
        writer.write_asm_entries()
        html = self._read_file(join(ASMDIR, '40000.html'), True)
        line_no = 33
        for inst, address in (
            ('CALL', 40003),
            ('JP', 40006),
            ('DJNZ', 40006),
            ('JR', 40000)
        ):
            operation = '{0} <a href="40000.html#{1}">{1}</a>'.format(inst, address)
            self.assertEqual(html[line_no], '<td class="instruction">{}</td>'.format(operation))
            line_no += 5

    def test_parameter_LinkInternalOperands_containing_skool_macro(self):
        self._test_Game_parameter_containing_skool_macro('LinkInternalOperands')

    def test_parameter_LinkOperands(self):
        ref = '[Game]\nLinkOperands={}'
        skool = """
            ; Routine at 32768
            c32768 RET

            ; Routine at 32769
            c32769 CALL 32768
             32772 DEFW 32768
             32774 DJNZ 32768
             32776 JP 32768
             32779 JR 32768
             32781 LD HL,32768
        """
        for param_value in ('CALL,JP,JR', 'CALL,DEFW,djnz,JP,LD'):
            writer = self._get_writer(ref=ref.format(param_value), skool=skool)
            link_operands = tuple(param_value.upper().split(','))
            self.assertEqual(writer.link_operands, link_operands)
            writer.write_asm_entries()
            html = self._read_file(join(ASMDIR, '32769.html'), True)
            link = '<a href="32768.html">32768</a>'
            line_no = 34
            for prefix in ('CALL ', 'DEFW ', 'DJNZ ', 'JP ', 'JR ', 'LD HL,'):
                inst_type = prefix.split()[0]
                exp_html = prefix + (link if inst_type in link_operands else '32768')
                self.assertEqual(html[line_no], '<td class="instruction">{}</td>'.format(exp_html))
                line_no += 5

    def test_parameter_LinkOperands_containing_skool_macro(self):
        self._test_Game_parameter_containing_skool_macro('LinkOperands')

    def test_parameter_Logo_is_stripped(self):
        page_id = 'custom'
        ref = """
            [Game]
            Logo=#INCLUDE(Logo)

            [Logo]
            #PUSHS
            #POKES30000,1
            #UDG30000
            #POPS

            [Page:{0}]

            [Template:{0}]
            {{Game[Logo]}}
        """.format(page_id)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        exp_contents = writer.expand('#UDG30000', '')
        page = self._read_file('{}.html'.format(page_id))
        self.assertEqual(page, exp_contents)

    def test_parameter_LogoImage_containing_skool_macro(self):
        self.force_odir = self.make_directory()
        self.write_bin_file(path='{}/{}/logo.png'.format(self.force_odir, GAMEDIR))
        self._test_Game_parameter_containing_skool_macro(
            'LogoImage', '#IF({html})(logo.png,not.png)',
            '<img alt="LogoImageTest" src="../logo.png" />',
            'Game=LogoImageTest'
        )

    def test_parameter_OutputRegisterTableHeader_containing_skool_macro(self):
        self._test_Game_parameter_containing_skool_macro('OutputRegisterTableHeader')

    def test_parameter_Release_containing_skool_macro(self):
        self._test_Game_parameter_containing_skool_macro('Release')

    def test_parameter_StyleSheet_containing_skool_macro(self):
        self._test_Game_parameter_containing_skool_macro('StyleSheet')

    def test_parameter_Content_containing_skool_macro(self):
        self.force_odir = self.make_directory()
        self.write_text_file(path='{}/{}/Stuff.html'.format(self.force_odir, GAMEDIR))
        ref = """
            [Page:Stuff]
            Content=#IF({html})(Stuff.html,Wrong.html)

            [Index]
            Stuff

            [Index:Stuff:Things]
            Stuff

            [Template:GameIndex]
            {sections[0][header]}: {sections[0][items][0][href]}
        """
        writer = self._get_writer(ref=ref)
        writer.write_index()
        self._assert_content_equal('Things: Stuff.html', 'index.html')

    def test_Page_parameter_JavaScript_containing_skool_macro(self):
        self._test_Page_parameter_containing_skool_macro('JavaScript')

    def test_parameter_SectionPrefix_containing_skool_macro(self):
        self._test_Page_parameter_containing_skool_macro('SectionPrefix', '#IF({html})(Right,Wrong)', 'Right', '[Right:Item]')

    def test_parameter_SectionType_containing_skool_macro(self):
        self._test_Page_parameter_containing_skool_macro('SectionType')

    def test_parameter_EntryDescriptions_containing_skool_macro(self):
        self._test_MemoryMap_parameter_containing_skool_macro('EntryDescriptions')

    def test_parameter_EntryTypes_containing_skool_macro(self):
        self._test_MemoryMap_parameter_containing_skool_macro('EntryTypes', '#IF({html})(c,u)', 'c')

    def test_parameter_Includes_containing_skool_macro(self):
        self._test_MemoryMap_parameter_containing_skool_macro('Includes', '#IF({html})(50000,0)', '[50000]')

    def test_parameter_LabelColumn_containing_skool_macro(self):
        self._test_MemoryMap_parameter_containing_skool_macro('LabelColumn')

    def test_parameter_LengthColumn_containing_skool_macro(self):
        self._test_MemoryMap_parameter_containing_skool_macro('LengthColumn')

    def test_parameter_Write_containing_skool_macro(self):
        self._test_MemoryMap_parameter_containing_skool_macro('Write')

    def test_html_escape(self):
        # Check that HTML characters from the skool file are escaped
        skool = """
            ; Save & quit
            ;
            ; This routine saves & quits.
            ;
            ; A Some value >= 5
            ;
            ; First we save & quit.
            c24576 CALL 32768
            ; Message: <&>
             24579 DEFM "<&>" ; a <= b & b >= c
            ; </done>
        """
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
        writer.write_page('Bugs')
        html = self._read_file(join(REFERENCE_DIR, 'bugs.html'))
        self.assertIn('<p>Hello</p>', html)

    def test_macro_font_text_parameter_is_not_html_escaped(self):
        font_addr = 30000
        fname = 'message'
        exp_image_path = '{}/{}.png'.format(FONTDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        message = '<&>'
        skool = """
            ; Font
            ;
            ; #FONT:({}){}({})
            b30048 DEFS 8,1 ; &
             30224 DEFS 8,2 ; <
             30240 DEFS 8,3 ; >
        """.format(message, font_addr, fname)
        writer = self._get_writer(skool=skool, mock_file_info=True)
        writer.write_asm_entries()
        udg_array = [[]]
        for c in message:
            c_addr = font_addr + 8 * (ord(c) - 32)
            udg_array[0].append(Udg(56, writer.snapshot[c_addr:c_addr + 8]))
        self._check_image(writer, udg_array, path=exp_image_path)

    def test_macro_html_parameter_is_not_html_escaped(self):
        text = '<&>'
        skool = """
            ; Routine at 50000
            ;
            ; #HTML({})
            c50000 RET
        """.format(text)
        writer = self._get_writer(skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">50000: Routine at 50000</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            <div class="paragraph">
            {}
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="50000"></span>50000</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """.format(text)
        subs = {
            'header': 'Routines',
            'title': 'Routine at 50000',
            'body_class': 'Asm-c',
            'up': '50000',
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '50000.html'), subs)

    def _test_write_index(self, files, content, ref='', custom_subs=None):
        writer = self._get_writer(ref=ref, skool='')
        for f in files:
            self.write_text_file(path=join(self.odir, GAMEDIR, f))
        writer.write_index()
        subs = {
            'title': 'Index',
            'header': ('The complete', 'RAM disassembly'),
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
        ref = """
            [OtherCode:otherCode]
            Source=other.skool
            [OtherCode:otherCode2]
            Source=load.skool
            [Links]
            otherCode-Index=Startup code
            otherCode2-Index=Loading code
            [Paths]
            otherCode-Index={}
            otherCode2-Index={}
        """.format(*files)
        content = """
            <div class="section-header">Other code</div>
            <ul class="index-list">
            <li><a href="other/other.html">Startup code</a></li>
            <li><a href="load/index.html">Loading code</a></li>
            </ul>
        """
        self._test_write_index(files, content, ref)

    def test_write_index_custom(self):
        title_prefix = 'The woefully incomplete'
        title_suffix = 'disassembly of the RAM'
        ref = """
            [Index]
            Reference
            MemoryMaps

            [Index:Reference:Reference material]
            Bugs
            Facts

            [Index:MemoryMaps:RAM maps]
            RoutinesMap
            WordMap

            [Links]
            WordMap=Words
            Facts=Facts

            [MemoryMap:WordMap]
            EntryTypes=w

            [PageHeaders]
            GameIndex={}<>{}

            [Paths]
            RoutinesMap=memorymaps/routines.html
            WordMap=memorymaps/words.html
            Bugs=ref/bugs.html
            Facts=ref/facts.html
            Changelog=ref/changelog.html
        """.format(title_prefix, title_suffix)
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
            'header': (title_prefix, title_suffix)
        }
        self._test_write_index(files, content, ref, custom_subs)

    def test_write_index_with_custom_link_text(self):
        ref = """
            [Links]
            Bugs=[Bugs] (glitches)
            Changelog=Change log
            DataMap=Game data
            Facts=[Facts] (trivia)
            GameStatusBuffer=Workspace
            Glossary=List of terms
            GraphicGlitches=Graphic bugs
            MemoryMap=All code and data
            MessagesMap=Strings
            Pokes=POKEs
            RoutinesMap=Game code
            UnusedMap=Unused bytes
        """
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

    def test_write_index_with_custom_link_text_containing_skool_macros(self):
        ref = """
            [Links]
            Bugs=[Bugs#IF1(!)] (#N23)
            Changelog=[Changelog#IF1(?)] (#EVAL35,16)
            start-Index=Startup code (#IF1(23))
            [OtherCode:start]
        """
        files = [
            'reference/bugs.html',
            'reference/changelog.html',
            'start/start.html'
        ]
        content = """
            <div class="section-header">Other code</div>
            <ul class="index-list">
            <li><a href="start/start.html">Startup code (23)</a></li>
            </ul>
            <div class="section-header">Reference</div>
            <ul class="index-list">
            <li><a href="reference/changelog.html">Changelog?</a> (23)</li>
            <li><a href="reference/bugs.html">Bugs!</a> (23)</li>
            </ul>
        """
        self._test_write_index(files, content, ref)

    def test_write_index_with_custom_link_to_existing_page_specified_using_skool_macro(self):
        ref = """
            [Page:AlreadyThere]
            Content=asm/#MAP({base})(32768,16:8000).html
            [Index:DataTables:Data tables and buffers]
            AlreadyThere
        """
        files = ['asm/32768.html']
        content = """
            <div class="section-header">Data tables and buffers</div>
            <ul class="index-list">
            <li><a href="asm/32768.html">AlreadyThere</a></li>
            </ul>
        """
        self._test_write_index(files, content, ref)

    def test_write_index_with_custom_footer(self):
        files = []
        content = ""
        release = 'foo'
        c = 'bar'
        created = 'baz'
        ref = """
            [Game]
            Copyright={}
            Created={}
            Release={}
        """.format(c, created, release)
        footer = """
            <footer>
            <div class="release">{}</div>
            <div class="copyright">{}</div>
            <div class="created">{}</div>
            </footer>
            </body>
            </html>
        """.format(release, c, created)
        custom_subs = {'footer': dedent(footer).strip()}
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
            'title': 'Index',
            'header': ('The complete', 'RAM disassembly'),
            'logo': '<img alt="{}" src="{}" />'.format(game, logo_image_path),
            'path': '',
            'body_class': 'GameIndex',
            'content': ''
        }
        self._assert_files_equal('index.html', subs, True)

    def test_write_asm_entries(self):
        ref = "[OtherCode:start]"
        skool = """
            @remote=start:30000,30003
            ; Routine at 24576
            ;
            ; Description of routine at 24576.
            ;
            ; A Some value
            ; B Some other value
            c24576 LD A,B  ; Comment for instruction at 24576
            ; Mid-routine comment above 24577.
            *24577 RET
            ; End comment for routine at 24576.

            ; Data block at 24578
            b24578 DEFB 0

            ; Routine at 24579
            c24579 JR 24577

            ; GSB entry at 24581
            g24581 DEFW 123

            ; Unused
            u24583 DEFB 0

            ; Routine at 24584 (register section but no description)
            ;
            ; .
            ;
            ; A 0
            c24584 CALL 30000  ; {Comment for the instructions at 24584 and 24587
             24587 JP 30003    ; }
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        # Routine at 24576
        content = """
            <div class="description">24576: Routine at 24576</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            <div class="paragraph">
            Description of routine at 24576.
            </div>
            </div>
            <table class="input">
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
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="24576"></span>24576</td>
            <td class="instruction">LD A,B</td>
            <td class="comment-1" rowspan="1">Comment for instruction at 24576</td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="5">
            <span id="24577"></span>
            <div class="comments">
            <div class="paragraph">
            Mid-routine comment above 24577.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="24577"></span>24577</td>
            <td class="instruction">RET</td>
            <td class="comment-1" rowspan="1"></td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="5">
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
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-1"><span id="24578"></span>24578</td>
            <td class="instruction">DEFB 0</td>
            <td class="comment-0" rowspan="1"></td>
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
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="24579"></span>24579</td>
            <td class="instruction">JR <a href="24576.html#24577">24577</a></td>
            <td class="comment-0" rowspan="1"></td>
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
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-1"><span id="24581"></span>24581</td>
            <td class="instruction">DEFW 123</td>
            <td class="comment-0" rowspan="1"></td>
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
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-1"><span id="24583"></span>24583</td>
            <td class="instruction">DEFB 0</td>
            <td class="comment-0" rowspan="1"></td>
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
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            <table class="input">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            <tr>
            <td class="register">A</td>
            <td class="register-desc">0</td>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="24584"></span>24584</td>
            <td class="instruction">CALL <a href="../start/30000.html">30000</a></td>
            <td class="comment-1" rowspan="2">Comment for the instructions at 24584 and 24587</td>
            </tr>
            <tr>
            <td class="address-1"><span id="24587"></span>24587</td>
            <td class="instruction">JP <a href="../start/30000.html#30003">30003</a></td>
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

    def test_write_asm_entries_hex_lower(self):
        skool = """
            ; Routine at 8007
            c$8007 jp $800a

            ; Routine at 800a
            c$800a jp $8007
        """
        writer = self._get_writer(skool=skool)
        writer.write_asm_entries()

        # Routine at 8007
        content = """
            <div class="description">8007: Routine at 8007</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="32775"></span>8007</td>
            <td class="instruction">jp <a href="32778.html">$800a</a></td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'title': 'Routine at 8007',
            'body_class': 'Asm-c',
            'header': 'Routines',
            'up': 32775,
            'next': 32778,
            'next_text': '800a',
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '32775.html'), subs)

        # Routine at 800a
        content = """
            <div class="description">800a: Routine at 800a</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="32778"></span>800a</td>
            <td class="instruction">jp <a href="32775.html">$8007</a></td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'title': 'Routine at 800a',
            'body_class': 'Asm-c',
            'header': 'Routines',
            'prev': 32775,
            'prev_text': '8007',
            'up': 32778,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '32778.html'), subs)

    def test_write_asm_entries_with_decimal_addresses_below_10000(self):
        skool = """
            c00000 RET

            c00002 RET

            c00044 RET

            c00666 RET

            c08888 RET
        """
        entry_template = """
            <div class="description">{address:05d}: </div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="{address}"></span>{address:05d}</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
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
        ref = """
            [Titles]
            Asm-b=Bytes at {entry[address]}
            Asm-c=Code at {entry[address]}
            Asm-g=GSB entry at {entry[label]}
            Asm-s=Space at {entry[address]}
            Asm-t=Text at {entry[location]:04X}
            Asm-u=Unused bytes at {entry[address]}
            Asm-w=Words at {entry[address]}
            [PageHeaders]
            Asm-b=Bytes
            Asm-c=Code at {entry[location]:04X}
            Asm-g=GSB
            Asm-s=Unused space
            Asm-t=Text
            Asm-u=Unused bytes
            Asm-w=Words at {entry[label]}
        """
        skool = """
            ; b
            b30000 DEFB 0

            ; c
            c30001 RET

            ; g
            @label=LIVES
            g30002 DEFB 0

            ; s
            s30003 DEFS 1

            ; t
            t30004 DEFM "a"

            ; u
            u30005 DEFB 0

            ; w
            @label=WORDS
            w30006 DEFW 0
        """
        writer = self._get_writer(ref=ref, skool=skool, asm_labels=True)
        writer.write_asm_entries()

        for address, exp_title, exp_header in (
                (30000, 'Bytes at 30000', 'Bytes'),
                (30001, 'Code at 30001', 'Code at 7531'),
                (30002, 'GSB entry at LIVES', 'GSB'),
                (30003, 'Space at 30003', 'Unused space'),
                (30004, 'Text at 7534', 'Text'),
                (30005, 'Unused bytes at 30005', 'Unused bytes'),
                (30006, 'Words at 30006', 'Words at WORDS')
        ):
            path = '{}/{}.html'.format(ASMDIR, address)
            self._assert_title_equals(path, exp_title, exp_header)

    def test_write_asm_entries_with_entry_group_but_no_custom_title_or_page_header(self):
        ref = """
            [EntryGroups]
            GameState=40000,$9c41
        """
        skool = """
            ; Number of lives
            b40000 DEFB 0

            ; Score
            w40001 DEFW 0
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        exp_header = 'Data'
        for address in (40000, 40001):
            exp_title = 'Data at {}'.format(address)
            path = '{}/{}.html'.format(ASMDIR, address)
            self._assert_title_equals(path, exp_title, exp_header)

    def test_write_asm_entries_with_entry_group_and_custom_title(self):
        ref = """
            [EntryGroups]
            GameState=40000,$9c41

            [Titles]
            Asm-GameState=Game state variable at {entry[address]}
        """
        skool = """
            ; Number of lives
            b40000 DEFB 0

            ; Score
            w40001 DEFW 0
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        for address in (40000, 40001):
            exp_title = exp_header = 'Game state variable at {}'.format(address)
            path = '{}/{}.html'.format(ASMDIR, address)
            self._assert_title_equals(path, exp_title, exp_header)

    def test_write_asm_entries_with_entry_group_and_custom_title_and_page_header(self):
        ref = """
            [EntryGroups]
            GameState=40000,$9c41

            [Titles]
            Asm-GameState=Game state variable at {entry[address]}

            [PageHeaders]
            Asm-GameState=Game state variables
        """
        skool = """
            ; Number of lives
            b40000 DEFB 0

            ; Score
            w40001 DEFW 0
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        exp_header = 'Game state variables'
        for address in (40000, 40001):
            exp_title = 'Game state variable at {}'.format(address)
            path = '{}/{}.html'.format(ASMDIR, address)
            self._assert_title_equals(path, exp_title, exp_header)

    def test_write_asm_entries_with_custom_filenames(self):
        ref = '[Paths]\nCodeFiles=asm-{address:04x}.html'
        skool = """
            ; Data
            b30000 DEFS 10000

            ; More data
            b40000 DEFS 10000
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        for address in (30000, 40000):
            path = '{}/asm-{:04x}.html'.format(ASMDIR, address)
            title = 'Data at {}'.format(address)
            self._assert_title_equals(path, title, 'Data')

    def test_write_asm_entries_with_custom_filenames_specified_by_skool_macro(self):
        ref = '[Paths]\nCodeFiles=0#IF({base}==16)(x{address:04x},d{address}).html'
        skool = """
            ; Data
            b40000 DEFS 10000

            ; More data
            b50000 DEFS 10000
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        for address in (40000, 50000):
            path = '{}/0d{}.html'.format(ASMDIR, address)
            title = 'Data at {}'.format(address)
            self._assert_title_equals(path, title, 'Data')

    def test_write_asm_entries_with_invalid_filename_template(self):
        ref = '[Paths]\nCodeFiles={Address:04x}.html'
        skool = 'b30000 DEFS 10000'
        writer = self._get_writer(ref=ref, skool=skool)
        with self.assertRaisesRegex(SkoolKitError, "^Unknown field 'Address' in CodeFiles template$"):
            writer.write_asm_entries()

    def test_write_asm_entries_with_custom_address_format(self):
        skool = """
            ; Routine at 32768
            c32768 RET

            ; Routine at 32769
            c32769 RET

            ; Routine at 32770
            c32770 RET
        """
        ref = """
            [Game]
            Address=${address:04X}
        """
        writer = self._get_writer(skool=skool, ref=ref)
        writer.write_asm_entries()

        content = """
            <div class="description">$8001: Routine at 32769</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="32769"></span>$8001</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at $8001',
            'body_class': 'Asm-c',
            'prev': '32768',
            'prev_text': '$8000',
            'up': '32769',
            'next': '32770',
            'next_text': '$8002',
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '32769.html'), subs)

    def test_write_asm_entries_with_custom_address_format_containing_skool_macro(self):
        skool = """
            ; Routine at 52992
            c52992 RET

            ; Routine at 52993
            c52993 RET

            ; Routine at 52994
            c52994 RET
        """
        ref = """
            [Game]
            Address=#IF(1)(${address:04x})
        """
        writer = self._get_writer(skool=skool, ref=ref)
        writer.write_asm_entries()

        content = """
            <div class="description">$cf01: Routine at 52993</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="52993"></span>$cf01</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at $cf01',
            'body_class': 'Asm-c',
            'prev': '52992',
            'prev_text': '$cf00',
            'up': '52993',
            'next': '52994',
            'next_text': '$cf02',
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '52993.html'), subs)

    def test_write_asm_entries_with_custom_anchors(self):
        ref = """
            [Game]
            AddressAnchor={address:04X}
            LinkInternalOperands=1
        """
        skool = """
            ; Routine at 50000
            c50000 LD A,B
            ; Jump back.
             50001 JR 50000
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">50000: Routine at 50000</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="C350"></span>50000</td>
            <td class="instruction">LD A,B</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="5">
            <span id="C351"></span>
            <div class="comments">
            <div class="paragraph">
            Jump back.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-1"><span id="C351"></span>50001</td>
            <td class="instruction">JR <a href="50000.html#C350">50000</a></td>
            <td class="comment-0" rowspan="1"></td>
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

    def test_write_asm_entries_with_custom_address_anchor_containing_skool_macro(self):
        ref = """
            [Game]
            AddressAnchor=#IF(0)({address},{address:04X})
            LinkInternalOperands=1
        """
        skool = """
            ; Routine at 30000
            c30000 LD A,B
            ; Jump back.
             30001 JR 30000
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">30000: Routine at 30000</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="7530"></span>30000</td>
            <td class="instruction">LD A,B</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="5">
            <span id="7531"></span>
            <div class="comments">
            <div class="paragraph">
            Jump back.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-1"><span id="7531"></span>30001</td>
            <td class="instruction">JR <a href="30000.html#7530">30000</a></td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at 30000',
            'body_class': 'Asm-c',
            'up': '7530',
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '30000.html'), subs)

    def test_write_asm_entries_on_single_page(self):
        ref = '[Game]\nAsmSinglePage=1'
        skool = """
            ; Routine at 32768
            c32768 CALL 32775
             32771 JR Z,32776
             32773 JR 32768

            ; Routine at 32775
            ;
            ; Used by the routine at #R32768.
            c32775 LD A,B
            *32776 RET
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        content = """
            <div id="32768" class="description">32768: Routine at 32768</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="32768"></span>32768</td>
            <td class="instruction">CALL <a href="#32775">32775</a></td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="address-1"><span id="32771"></span>32771</td>
            <td class="instruction">JR Z,<a href="#32776">32776</a></td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="address-1"><span id="32773"></span>32773</td>
            <td class="instruction">JR 32768</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
            <div id="32775" class="description">32775: Routine at 32775</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            <div class="paragraph">
            Used by the routine at <a href="asm.html#32768">32768</a>.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="32775"></span>32775</td>
            <td class="instruction">LD A,B</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="address-2"><span id="32776"></span>32776</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'path': '',
            'header': 'Disassembly',
            'title': 'Disassembly',
            'body_class': 'AsmSinglePage',
            'content': content
        }
        self._assert_files_equal('asm.html', subs)

    def test_write_asm_entries_on_single_page_with_custom_path_and_title_and_header(self):
        path = 'allinone.html'
        header = 'All the entries'
        title = 'The disassembly'
        ref = """
            [Game]
            AsmSinglePage=1
            [Paths]
            AsmSinglePage={}
            [Titles]
            AsmSinglePage={}
            [PageHeaders]
            AsmSinglePage={}
        """.format(path, title, header)
        skool = '; Routine at 40000\nc40000 RET'
        content = """
            <div id="40000" class="description">40000: Routine at 40000</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="40000"></span>40000</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'path': '',
            'header': header,
            'title': title,
            'body_class': 'AsmSinglePage',
            'content': content
        }

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_files_equal(path, subs)

    def test_write_asm_entries_with_invalid_asm_anchor(self):
        ref = '[Game]\nAddressAnchor={Address:04x}'
        skool = 'c40000 RET'
        writer = self._get_writer(ref=ref, skool=skool)
        with self.assertRaisesRegex(SkoolKitError, "^Unknown field 'Address' in AddressAnchor template$"):
            writer.write_asm_entries()

    def test_write_asm_entries_with_missing_OtherCode_section(self):
        skool = """
            @remote=save:50000
            c30000 JP 50000
        """
        writer = self._get_writer(skool=skool)
        with self.assertRaises(SkoolKitError) as cm:
            writer.write_asm_entries()
        self.assertEqual(cm.exception.args[0], "Cannot find code path for 'save' disassembly")

    def test_indented_comment_lines_are_ignored(self):
        skool = """
            ; Routine
            ;
             ; Ignore me.
            ; Paragraph 1.
             ; Ignore me too,
            ; .
             ; Ignore me three.
            ; Paragraph 2.
            ;
            ; HL Address
             ; Ignore me four.
            ;
             ; Ignore me five.
            ; Start comment paragraph 1.
            ; .
             ; Ignore me six.
            ; Start comment paragraph 2.
            c50000 XOR A
            ; Mid-block comment.
             ; Ignore me seven.
            ; Mid-block comment continued.
             50001 RET
            ; End comment.
             ; Ignore me eight.
            ; End comment continued.
        """
        writer = self._get_writer(skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">50000: Routine</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            <div class="paragraph">
            Paragraph 1.
            </div>
            <div class="paragraph">
            Paragraph 2.
            </div>
            </div>
            <table class="input">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            <tr>
            <td class="register">HL</td>
            <td class="register-desc">Address</td>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="5">
            <span id="50000"></span>
            <div class="comments">
            <div class="paragraph">
            Start comment paragraph 1.
            </div>
            <div class="paragraph">
            Start comment paragraph 2.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="50000"></span>50000</td>
            <td class="instruction">XOR A</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="5">
            <span id="50001"></span>
            <div class="comments">
            <div class="paragraph">
            Mid-block comment. Mid-block comment continued.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-1"><span id="50001"></span>50001</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="comments">
            <div class="paragraph">
            End comment. End comment continued.
            </div>
            </div>
            </td>
            </tr>
            </table>
        """
        subs = {
            'title': 'Routine at 50000',
            'body_class': 'Asm-c',
            'header': 'Routines',
            'up': 50000,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '50000.html'), subs)

    def test_block_start_comment(self):
        start_comment = ('Start comment paragraph 1.', 'Paragraph 2.')
        skool = """
            ; Routine with a start comment
            ;
            ; .
            ;
            ; .
            ;
            ; {}
            ; .
            ; {}
            c40000 RET
        """.format(*start_comment)
        writer = self._get_writer(skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">40000: Routine with a start comment</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="routine-comment" colspan="5">
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
            <td class="address-2"><span id="40000"></span>40000</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
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
        skool = """
            ; Routine with a label
            @label=START
            c50000 LD B,5     ; Loop 5 times
            *50002 DJNZ 50002
             50004 RET

            ; Routine without a label
            c50005 JP 50000

            ; DEFW statement with a @keep directive
            @keep
            w50008 DEFW 50000
        """
        writer = self._get_writer(skool=skool, asm_labels=True)
        writer.write_asm_entries()

        # Routine at 50000
        content = """
            <div class="description">50000: Routine with a label</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="asm-label">START</td>
            <td class="address-2"><span id="50000"></span>50000</td>
            <td class="instruction">LD B,5</td>
            <td class="comment-1" rowspan="1">Loop 5 times</td>
            </tr>
            <tr>
            <td class="asm-label">START_0</td>
            <td class="address-2"><span id="50002"></span>50002</td>
            <td class="instruction">DJNZ <a href="50000.html#50002">START_0</a></td>
            <td class="comment-1" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label"></td>
            <td class="address-1"><span id="50004"></span>50004</td>
            <td class="instruction">RET</td>
            <td class="comment-1" rowspan="1"></td>
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
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="50005"></span>50005</td>
            <td class="instruction">JP <a href="50000.html">START</a></td>
            <td class="comment-0" rowspan="1"></td>
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
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-1"><span id="50008"></span>50008</td>
            <td class="instruction">DEFW 50000</td>
            <td class="comment-0" rowspan="1"></td>
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
        ref = """
            [Game]
            LinkOperands=CALL,DEFW,DJNZ,JP,JR,RST
        """
        skool = """
            ; Start
            c00000 RST 8  ; This operand should not be replaced by a label
             00001 DEFS 7

            ; Restart routine at 8
            @label=DONOTHING
            c00008 RET
        """
        writer = self._get_writer(ref=ref, skool=skool, asm_labels=True)
        writer.write_asm_entries()

        # Routine at 00000
        content = """
            <div class="description">00000: Start</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="0"></span>00000</td>
            <td class="instruction">RST <a href="8.html">8</a></td>
            <td class="comment-1" rowspan="1">This operand should not be replaced by a label</td>
            </tr>
            <tr>
            <td class="address-1"><span id="1"></span>00001</td>
            <td class="instruction">DEFS 7</td>
            <td class="comment-1" rowspan="1"></td>
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

    def test_label_marks_instruction_as_entry_point(self):
        skool = """
            ; Start
            c50000 XOR A
            @label=*SELF
             50001 JR 50001
        """
        writer = self._get_writer(skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">50000: Start</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="50000"></span>50000</td>
            <td class="instruction">XOR A</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="address-2"><span id="50001"></span>50001</td>
            <td class="instruction">JR 50001</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at 50000',
            'body_class': 'Asm-c',
            'up': 50000,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '50000.html'), subs)

    def test_blank_label_directive(self):
        skool = """
            ; Routine with a blank @label directive
            @label=START
            c50000 XOR A
            @label=
            *50001 JR 50001
        """
        writer = self._get_writer(skool=skool, asm_labels=True)
        writer.write_asm_entries()

        content = """
            <div class="description">50000: Routine with a blank @label directive</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="asm-label">START</td>
            <td class="address-2"><span id="50000"></span>50000</td>
            <td class="instruction">XOR A</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label"></td>
            <td class="address-1"><span id="50001"></span>50001</td>
            <td class="instruction">JR 50001</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': 'Routines',
            'title': 'Routine at 50000',
            'body_class': 'Asm-c',
            'up': 50000,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '50000.html'), subs)

    def test_write_map(self):
        skool = """
            ; Routine
            c30000 RET

            ; Bytes
            b30001 DEFB 1,2

            ; Words
            w30003 DEFW 257,65534

            ; GSB entry
            g30007 DEFB 0

            ; Unused
            u30008 DEFB 0

            ; Zeroes
            s30009 DEFS 9

            ; Text
            t30018 DEFM "Hi"
        """
        writer = self._get_writer(skool=skool)

        # Memory map
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page">Page</th>
            <th class="map-byte">Byte</th>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page">117</td>
            <td class="map-byte">48</td>
            <td class="map-c"><span id="30000"></span><a href="../asm/30000.html">30000</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30000.html">Routine</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-page">117</td>
            <td class="map-byte">49</td>
            <td class="map-b"><span id="30001"></span><a href="../asm/30001.html">30001</a></td>
            <td class="map-b-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30001.html">Bytes</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-page">117</td>
            <td class="map-byte">51</td>
            <td class="map-w"><span id="30003"></span><a href="../asm/30003.html">30003</a></td>
            <td class="map-w-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30003.html">Words</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-page">117</td>
            <td class="map-byte">55</td>
            <td class="map-g"><span id="30007"></span><a href="../asm/30007.html">30007</a></td>
            <td class="map-g-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30007.html">GSB entry</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-page">117</td>
            <td class="map-byte">56</td>
            <td class="map-u"><span id="30008"></span><a href="../asm/30008.html">30008</a></td>
            <td class="map-u-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30008.html">Unused</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-page">117</td>
            <td class="map-byte">57</td>
            <td class="map-s"><span id="30009"></span><a href="../asm/30009.html">30009</a></td>
            <td class="map-s-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30009.html">Zeroes</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-page">117</td>
            <td class="map-byte">66</td>
            <td class="map-t"><span id="30018"></span><a href="../asm/30018.html">30018</a></td>
            <td class="map-t-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30018.html">Text</a></div>
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
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-c"><span id="30000"></span><a href="../asm/30000.html">30000</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30000.html">Routine</a></div>
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
            <th class="map-page">Page</th>
            <th class="map-byte">Byte</th>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page">117</td>
            <td class="map-byte">49</td>
            <td class="map-b"><span id="30001"></span><a href="../asm/30001.html">30001</a></td>
            <td class="map-b-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30001.html">Bytes</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-page">117</td>
            <td class="map-byte">51</td>
            <td class="map-w"><span id="30003"></span><a href="../asm/30003.html">30003</a></td>
            <td class="map-w-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30003.html">Words</a></div>
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
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-t"><span id="30018"></span><a href="../asm/30018.html">30018</a></td>
            <td class="map-t-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30018.html">Text</a></div>
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
            <th class="map-page">Page</th>
            <th class="map-byte">Byte</th>
            <th>Address</th>
            <th class="map-length">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page">117</td>
            <td class="map-byte">56</td>
            <td class="map-u"><span id="30008"></span><a href="../asm/30008.html">30008</a></td>
            <td class="map-length">1</td>
            <td class="map-u-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30008.html">Unused</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-page">117</td>
            <td class="map-byte">57</td>
            <td class="map-s"><span id="30009"></span><a href="../asm/30009.html">30009</a></td>
            <td class="map-length">9</td>
            <td class="map-s-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30009.html">Zeroes</a></div>
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
        with self.assertRaisesRegex(SkoolKitError, "^Failed to format CodeFiles template: Unknown format code 'q' for object of type 'int'$"):
            writer.write_map('MemoryMap')

    def test_write_map_with_custom_address_format(self):
        ref = '[Game]\nAddress=${address:04X}'
        skool = '; Routine at 23456\nc23456 RET'
        writer = self._get_writer(ref=ref, skool=skool)

        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page">Page</th>
            <th class="map-byte">Byte</th>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page">91</td>
            <td class="map-byte">160</td>
            <td class="map-c"><span id="23456"></span><a href="../asm/23456.html">$5BA0</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/23456.html">Routine at 23456</a></div>
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

    def test_write_map_with_custom_address_format_containing_skool_macro(self):
        ref = '[Game]\nAddress=#IF(1)(${address:04x})'
        skool = '; Routine at 23456\nc23456 RET'
        writer = self._get_writer(ref=ref, skool=skool)

        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page">Page</th>
            <th class="map-byte">Byte</th>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page">91</td>
            <td class="map-byte">160</td>
            <td class="map-c"><span id="23456"></span><a href="../asm/23456.html">$5ba0</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/23456.html">Routine at 23456</a></div>
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

    def test_write_map_with_custom_asm_anchors(self):
        ref = '[Game]\nAddressAnchor={address:04x}'
        skool = '; Routine at 23456\nc23456 RET'
        writer = self._get_writer(ref=ref, skool=skool)

        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page">Page</th>
            <th class="map-byte">Byte</th>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page">91</td>
            <td class="map-byte">160</td>
            <td class="map-c"><span id="5ba0"></span><a href="../asm/23456.html">23456</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/23456.html">Routine at 23456</a></div>
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

    def test_write_map_with_custom_asm_anchor_containing_skool_macro(self):
        ref = '[Game]\nAddressAnchor=#MAP({base})({address:04x},10:{address})'
        skool = '; Routine at 34567\nc34567 RET'
        writer = self._get_writer(ref=ref, skool=skool)

        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page">Page</th>
            <th class="map-byte">Byte</th>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page">135</td>
            <td class="map-byte">7</td>
            <td class="map-c"><span id="8707"></span><a href="../asm/34567.html">34567</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/34567.html">Routine at 34567</a></div>
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

    def test_write_map_with_upper_case_asm_anchors_and_address_links(self):
        ref = """
            [Game]
            AddressAnchor={address:04X}
            [MemoryMap:MemoryMap]
            Intro=First instruction at #LINK:MemoryMap#43981(ABCD), second at #R43982.
        """
        skool = """
            ; Routine at 43981
            c43981 XOR A
             43982 RET
        """
        writer = self._get_writer(ref=ref, skool=skool)

        content = """
            <div class="map-intro">First instruction at <a href="all.html#ABCD">ABCD</a>, second at <a href="../asm/43981.html#ABCE">43982</a>.</div>
            <table class="map">
            <tr>
            <th class="map-page">Page</th>
            <th class="map-byte">Byte</th>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page">171</td>
            <td class="map-byte">205</td>
            <td class="map-c"><span id="ABCD"></span><a href="../asm/43981.html">43981</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/43981.html">Routine at 43981</a></div>
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
        with self.assertRaisesRegex(SkoolKitError, "^Unknown field 'foo' in AddressAnchor template$"):
            writer.write_map('MemoryMap')

    def test_write_map_with_entry_group(self):
        ref = """
            [EntryGroups]
            GameState=40000,40001

            [MemoryMap:GameState]
            Includes=GameState
        """
        skool = """
            ; Number of lives
            b40000 DEFB 0

            ; Score
            w40001 DEFW 0

            ; Not game state
            c40003 RET
        """
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-b"><span id="40000"></span><a href="../asm/40000.html">40000</a></td>
            <td class="map-b-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/40000.html">Number of lives</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-w"><span id="40001"></span><a href="../asm/40001.html">40001</a></td>
            <td class="map-w-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/40001.html">Score</a></div>
            </td>
            </tr>
            </table>
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_map('GameState')
        subs = {
            'body_class': 'GameState',
            'header': 'GameState',
            'content': content
        }
        self._assert_files_equal(join(MAPS_DIR, 'GameState.html'), subs)

    def test_write_map_with_single_page_template(self):
        ref = '[Game]\nAsmSinglePage=1'
        skool = """
            ; A routine here
            c32768 RET

            ; A data block there
            b32769 DEFB 0
        """
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page">Page</th>
            <th class="map-byte">Byte</th>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page">128</td>
            <td class="map-byte">0</td>
            <td class="map-c"><span id="32768"></span><a href="../asm.html#32768">32768</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm.html#32768">A routine here</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-page">128</td>
            <td class="map-byte">1</td>
            <td class="map-b"><span id="32769"></span><a href="../asm.html#32769">32769</a></td>
            <td class="map-b-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm.html#32769">A data block there</a></div>
            </td>
            </tr>
            </table>
        """
        subs = {
            'body_class': 'MemoryMap',
            'header': 'Memory map',
            'content': content
        }

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_map('MemoryMap')
        self._assert_files_equal(join(MAPS_DIR, 'all.html'), subs)

    def test_write_map_with_single_page_template_and_upper_case_asm_anchors_and_address_link(self):
        ref = """
            [Game]
            AddressAnchor={address:04X}
            AsmSinglePage=1
            [MemoryMap:MemoryMap]
            Intro=First instruction at #R43981.
        """
        skool = """
            ; Routine at 43981
            c43981 RET
        """
        writer = self._get_writer(ref=ref, skool=skool)

        content = """
            <div class="map-intro">First instruction at <a href="../asm.html#ABCD">43981</a>.</div>
            <table class="map">
            <tr>
            <th class="map-page">Page</th>
            <th class="map-byte">Byte</th>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page">171</td>
            <td class="map-byte">205</td>
            <td class="map-c"><span id="ABCD"></span><a href="../asm.html#ABCD">43981</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm.html#ABCD">Routine at 43981</a></div>
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

    def test_write_map_with_single_page_template_using_custom_path(self):
        path = 'disassembly.html'
        ref = """
            [Game]
            AsmSinglePage=1
            [Paths]
            AsmSinglePage={}
        """.format(path)
        skool = '; A routine\nc30000 RET'
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page">Page</th>
            <th class="map-byte">Byte</th>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page">117</td>
            <td class="map-byte">48</td>
            <td class="map-c"><span id="30000"></span><a href="../{0}#30000">30000</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../{0}#30000">A routine</a></div>
            </td>
            </tr>
            </table>
        """.format(path)
        subs = {
            'body_class': 'MemoryMap',
            'header': 'Memory map',
            'content': content
        }

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_map('MemoryMap')
        self._assert_files_equal(join(MAPS_DIR, 'all.html'), subs)

    def test_write_custom_map(self):
        skool = """
            ; Routine
            ;
            ; Return early, return often.
            c30000 RET

            ; Bytes
            b30001 DEFB 1,2

            ; GSB entry
            g30003 DEFB 0

            ; Unused
            u30004 DEFB 0

            ; Zeroes
            s30005 DEFS 6

            ; Text
            t30011 DEFM "Hi"
        """
        map_id = 'CustomMap'
        map_intro = 'Introduction.'
        map_path = 'maps/custom.html'
        map_title = 'Custom map'
        ref = """
            [MemoryMap:{0}]
            EntryDescriptions=1
            EntryTypes=cg
            Intro={1}
            LengthColumn=1

            [Paths]
            {0}={2}

            [PageHeaders]
            {0}={3}

            [Titles]
            {0}={3}
        """.format(map_id, map_intro, map_path, map_title)
        writer = self._get_writer(ref=ref, skool=skool)

        content = """
            <div class="map-intro">{}</div>
            <table class="map">
            <tr>
            <th>Address</th>
            <th class="map-length">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-c"><span id="30000"></span><a href="../asm/30000.html">30000</a></td>
            <td class="map-length">1</td>
            <td class="map-c-desc">
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30000.html">Routine</a></div>
            <div class="map-entry-desc">
            <div class="paragraph">
            Return early, return often.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-g"><span id="30003"></span><a href="../asm/30003.html">30003</a></td>
            <td class="map-length">1</td>
            <td class="map-g-desc">
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30003.html">GSB entry</a></div>
            <div class="map-entry-desc">
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

    def test_write_map_with_LabelColumn(self):
        skool = """
            ; Routine
            @label=START
            c30000 JP 30003

            ; Another routine
            @label=CONTINUE
            c30003 JP 30006

            ; Yet another routine
            @label=STOP
            c30006 RET
        """
        ref = """
            [MemoryMap:RoutinesMap]
            LabelColumn=1
        """
        writer = self._get_writer(ref=ref, skool=skool, asm_labels=True)

        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th>Label</th>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-label"><a href="../asm/30000.html">START</a></td>
            <td class="map-c"><span id="30000"></span><a href="../asm/30000.html">30000</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30000.html">Routine</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-label"><a href="../asm/30003.html">CONTINUE</a></td>
            <td class="map-c"><span id="30003"></span><a href="../asm/30003.html">30003</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30003.html">Another routine</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-label"><a href="../asm/30006.html">STOP</a></td>
            <td class="map-c"><span id="30006"></span><a href="../asm/30006.html">30006</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30006.html">Yet another routine</a></div>
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
        self._assert_files_equal('maps/routines.html', subs)

    def test_write_map_with_LabelColumn_but_some_labels_undefined(self):
        skool = """
            ; Routine
            @label=START
            c30000 JP 30003

            ; Another routine
            c30003 JP 30006

            ; Yet another routine
            c30006 RET
        """
        ref = """
            [MemoryMap:RoutinesMap]
            LabelColumn=1
        """
        writer = self._get_writer(ref=ref, skool=skool, asm_labels=True)

        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th>Label</th>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-label"><a href="../asm/30000.html">START</a></td>
            <td class="map-c"><span id="30000"></span><a href="../asm/30000.html">30000</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30000.html">Routine</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-label"><a href="../asm/30003.html"></a></td>
            <td class="map-c"><span id="30003"></span><a href="../asm/30003.html">30003</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30003.html">Another routine</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-label"><a href="../asm/30006.html"></a></td>
            <td class="map-c"><span id="30006"></span><a href="../asm/30006.html">30006</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30006.html">Yet another routine</a></div>
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
        self._assert_files_equal('maps/routines.html', subs)

    def test_write_map_with_LabelColumn_but_no_labels_defined(self):
        skool = """
            ; Routine
            c30000 JP 30003

            ; Another routine
            c30003 JP 30006

            ; Yet another routine
            c30006 RET
        """
        ref = """
            [MemoryMap:RoutinesMap]
            LabelColumn=1
        """
        writer = self._get_writer(ref=ref, skool=skool, asm_labels=True)

        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-c"><span id="30000"></span><a href="../asm/30000.html">30000</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30000.html">Routine</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-c"><span id="30003"></span><a href="../asm/30003.html">30003</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30003.html">Another routine</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-c"><span id="30006"></span><a href="../asm/30006.html">30006</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30006.html">Yet another routine</a></div>
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
        self._assert_files_equal('maps/routines.html', subs)

    def test_write_map_with_custom_Length(self):
        skool = """
            ; Data block
            b40000 DEFB 0,0,0

            ; Another data block
            b40003 DEFS 12

            ; Yet another data block
            b40015 DEFS 512
        """
        ref = """
            [Game]
            Length=${size:02X}

            [MemoryMap:DataMap]
            PageByteColumns=0
            LengthColumn=1
        """
        writer = self._get_writer(ref=ref, skool=skool)

        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th>Address</th>
            <th class="map-length">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-b"><span id="40000"></span><a href="../asm/40000.html">40000</a></td>
            <td class="map-length">$03</td>
            <td class="map-b-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/40000.html">Data block</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-b"><span id="40003"></span><a href="../asm/40003.html">40003</a></td>
            <td class="map-length">$0C</td>
            <td class="map-b-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/40003.html">Another data block</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-b"><span id="40015"></span><a href="../asm/40015.html">40015</a></td>
            <td class="map-length">$200</td>
            <td class="map-b-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/40015.html">Yet another data block</a></div>
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
        self._assert_files_equal('maps/data.html', subs)

    def test_write_map_with_custom_Length_containing_skool_macro(self):
        skool = """
            ; Data block
            b40000 DEFB 0,0,0

            ; Another data block
            b40003 DEFS 12

            ; Yet another data block
            b40015 DEFS 512
        """
        ref = """
            [Game]
            Length=#IF(1)(${size:04x})

            [MemoryMap:DataMap]
            PageByteColumns=0
            LengthColumn=1
        """
        writer = self._get_writer(ref=ref, skool=skool)

        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th>Address</th>
            <th class="map-length">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-b"><span id="40000"></span><a href="../asm/40000.html">40000</a></td>
            <td class="map-length">$0003</td>
            <td class="map-b-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/40000.html">Data block</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-b"><span id="40003"></span><a href="../asm/40003.html">40003</a></td>
            <td class="map-length">$000c</td>
            <td class="map-b-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/40003.html">Another data block</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-b"><span id="40015"></span><a href="../asm/40015.html">40015</a></td>
            <td class="map-length">$0200</td>
            <td class="map-b-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/40015.html">Yet another data block</a></div>
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
        self._assert_files_equal('maps/data.html', subs)

    def test_write_map_with_PageByteColumns_containing_skool_macro(self):
        ref = """
            [MemoryMap:MemoryMap]
            PageByteColumns=#IF({base}==16)(0,1)
        """
        skool = '; Routine at 45678\nc45678 RET'
        writer = self._get_writer(ref=ref, skool=skool, base=BASE_16)

        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-c"><span id="45678"></span><a href="../asm/45678.html">B26E</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/45678.html">Routine at 45678</a></div>
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

    def test_write_memory_map_with_intro(self):
        intro = 'This map is empty.'
        ref = '[MemoryMap:MemoryMap]\nIntro={}'.format(intro)
        writer = self._get_writer(ref=ref, skool='; Code\nc32768 RET')
        content = """
            <div class="map-intro">{}</div>
            <table class="map">
            <tr>
            <th class="map-page">Page</th>
            <th class="map-byte">Byte</th>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page">128</td>
            <td class="map-byte">0</td>
            <td class="map-c"><span id="32768"></span><a href="../asm/32768.html">32768</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/32768.html">Code</a></div>
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
        skool = """
            c00000 RET

            c00002 RET

            c00044 RET

            c00666 RET

            c08888 RET
        """
        exp_content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th class="map-page">Page</th>
            <th class="map-byte">Byte</th>
            <th>Address</th>
            <th>Description</th>
            </tr>\n
        """
        for address in (0, 2, 44, 666, 8888):
            exp_content += """
                <tr>
                <td class="map-page">{0}</td>
                <td class="map-byte">{1}</td>
                <td class="map-c"><span id="{2}"></span><a href="../asm/{2}.html">{2:05d}</a></td>
                <td class="map-c-desc">
                <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/{2}.html"></a></div>
                </td>
                </tr>\n
            """.format(address // 256, address % 256, address)
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

    def test_write_map_with_includes_but_no_entry_types(self):
        ref = """
            [MemoryMap:Custom]
            Includes=30001,30003,30004
        """
        skool = """
            ; GSB entry
            ;
            ; Number of lives.
            g30000 DEFB 4

            ; Data
            w30001 DEFW 78

            ; Message ID
            t30003 DEFB 0

            ; Another message ID
            t30004 DEFB 0

            ; Code
            c30005 RET

            i30006
        """
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-w"><span id="30001"></span><a href="../asm/30001.html">30001</a></td>
            <td class="map-w-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30001.html">Data</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-t"><span id="30003"></span><a href="../asm/30003.html">30003</a></td>
            <td class="map-t-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30003.html">Message ID</a></div>
            </td>
            </tr>
            <tr>
            <td class="map-t"><span id="30004"></span><a href="../asm/30004.html">30004</a></td>
            <td class="map-t-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30004.html">Another message ID</a></div>
            </td>
            </tr>
            </table>
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_map('Custom')
        subs = {
            'header': 'Custom',
            'body_class': 'Custom',
            'content': content
        }
        self._assert_files_equal(join(MAPS_DIR, 'Custom.html'), subs)

    def test_write_data_map_with_custom_title_and_header_and_path(self):
        title = 'Data blocks'
        header = 'Blocks of data'
        path = 'foo/bar/data.html'
        ref = """
            [Titles]
            DataMap={}
            [PageHeaders]
            DataMap={}
            [Paths]
            DataMap={}
        """.format(title, header, path)
        writer = self._get_writer(ref=ref, skool='b30000 DEFB 0')
        writer.write_map('DataMap')
        self._assert_title_equals(path, title, header)

    def test_write_memory_map_with_custom_title_and_header_and_path(self):
        title = 'All the RAM'
        header = 'Every bit'
        path = 'memory_map.html'
        ref = """
            [Titles]
            MemoryMap={}
            [PageHeaders]
            MemoryMap={}
            [Paths]
            MemoryMap={}
        """.format(title, header, path)
        writer = self._get_writer(ref=ref, skool='c30000 RET')
        writer.write_map('MemoryMap')
        self._assert_title_equals(path, title, header)

    def test_write_messages_map_with_custom_title_and_header_and_path(self):
        title = 'Strings'
        header = 'Text'
        path = 'text/strings.html'
        ref = """
            [Titles]
            MessagesMap={}
            [PageHeaders]
            MessagesMap={}
            [Paths]
            MessagesMap={}
        """.format(title, header, path)
        writer = self._get_writer(ref=ref, skool='t30000 DEFM "a"')
        writer.write_map('MessagesMap')
        self._assert_title_equals(path, title, header)

    def test_write_routines_map_with_custom_title_and_header_and_path(self):
        title = 'All the code'
        header = 'Game code'
        path = 'mappage/code.html'
        ref = """
            [Titles]
            RoutinesMap={}
            [PageHeaders]
            RoutinesMap={}
            [Paths]
            RoutinesMap={}
        """.format(title, header, path)
        writer = self._get_writer(ref=ref, skool='c30000 RET')
        writer.write_map('RoutinesMap')
        self._assert_title_equals(path, title, header)

    def test_write_unused_map_with_custom_title_and_header_and_path(self):
        title = 'Bytes of no use'
        header = 'Unused memory'
        path = 'unused_bytes.html'
        ref = """
            [Titles]
            UnusedMap={}
            [PageHeaders]
            UnusedMap={}
            [Paths]
            UnusedMap={}
        """.format(title, header, path)
        writer = self._get_writer(ref=ref, skool='u30000 DEFB 0')
        writer.write_map('UnusedMap')
        self._assert_title_equals(path, title, header)

    def test_write_other_code_asm_entries(self):
        code_id = 'startup'
        ref = '[OtherCode:{}]'.format(code_id)
        other_skool = """
            ; Some data
            b30000 DEFB 0

            ; A routine
            c30001 RET

            ; A message
            t30002 DEFM "a"
        """
        main_writer = self._get_writer(ref=ref, skool=other_skool)

        code = main_writer.other_code[0][1]
        index_page_id = code['IndexPageId']
        self.assertEqual(index_page_id, '{}-Index'.format(code_id))
        map_path = main_writer.paths[index_page_id]
        self.assertEqual(map_path, '{}/{}.html'.format(code_id, code_id))
        code_path_id = code['CodePathId']
        self.assertEqual(code_path_id, '{}-CodePath'.format(code_id))
        asm_path = main_writer.paths[code_path_id]
        self.assertEqual(asm_path, code_id)

        writer = main_writer.clone(main_writer.parser, code_id)
        writer.write_file = self._mock_write_file
        writer.write_entries(asm_path, map_path)

        content = """
            <div class="description">30000: Some data</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-1"><span id="30000"></span>30000</td>
            <td class="instruction">DEFB 0</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'map': basename(map_path),
            'title': 'Data at 30000',
            'header': 'Data',
            'body_class': '{}-Asm-b'.format(code_id),
            'up': 30000,
            'next': 30001,
            'content': content
        }
        self._assert_files_equal('{}/30000.html'.format(asm_path), subs)

        content = """
            <div class="description">30001: A routine</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="30001"></span>30001</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'map': basename(map_path),
            'title': 'Routine at 30001',
            'header': 'Routines',
            'body_class': '{}-Asm-c'.format(code_id),
            'prev': 30000,
            'up': 30001,
            'next': 30002,
            'content': content
        }
        self._assert_files_equal('{}/30001.html'.format(asm_path), subs)

        content = """
            <div class="description">30002: A message</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-1"><span id="30002"></span>30002</td>
            <td class="instruction">DEFM "a"</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'map': basename(map_path),
            'title': 'Text at 30002',
            'header': 'Messages',
            'body_class': '{}-Asm-t'.format(code_id),
            'prev': 30001,
            'up': 30002,
            'content': content
        }
        self._assert_files_equal('{}/30002.html'.format(asm_path), subs)

    def test_write_other_code_asm_entries_with_custom_path_and_titles_and_headers(self):
        ref = """
            [OtherCode:secondary]

            [Paths]
            secondary-CodePath=other-code

            [Titles]
            secondary-Asm-b=Bytes at {entry[address]}
            secondary-Asm-c=Code at {entry[address]}
            secondary-Asm-g=GSB entry at {entry[label]}
            secondary-Asm-s=Space at {entry[address]}
            secondary-Asm-t=Text at {entry[location]:04X}
            secondary-Asm-u=Unused bytes at {entry[address]}
            secondary-Asm-w=Words at {entry[address]}

            [PageHeaders]
            secondary-Asm-b=Bytes
            secondary-Asm-c=Code at {entry[location]:04X}
            secondary-Asm-g=GSB
            secondary-Asm-s=Unused space
            secondary-Asm-t=Text
            secondary-Asm-u=Unused bytes
            secondary-Asm-w=Words at {entry[label]}
        """
        other_skool = """
            ; b
            b30000 DEFB 0

            ; c
            c30001 RET

            ; g
            @label=LIVES
            g30002 DEFB 0

            ; s
            s30003 DEFS 1

            ; t
            t30004 DEFM "a"

            ; u
            u30005 DEFB 0

            ; w
            @label=WORDS
            w30006 DEFW 0
        """
        main_writer = self._get_writer(ref=ref, skool=other_skool, asm_labels=True)

        code = main_writer.other_code[0][1]
        index_page_id = code['IndexPageId']
        self.assertEqual(index_page_id, 'secondary-Index')
        map_path = main_writer.paths[index_page_id]
        self.assertEqual(map_path, 'secondary/secondary.html')
        code_path_id = code['CodePathId']
        self.assertEqual(code_path_id, 'secondary-CodePath')
        asm_path = main_writer.paths[code_path_id]
        self.assertEqual(asm_path, 'other-code')

        writer = main_writer.clone(main_writer.parser, 'secondary')
        writer.write_file = self._mock_write_file
        writer.write_entries(asm_path, map_path)

        for address, exp_title, exp_header in (
                (30000, 'Bytes at 30000', 'Bytes'),
                (30001, 'Code at 30001', 'Code at 7531'),
                (30002, 'GSB entry at LIVES', 'GSB'),
                (30003, 'Space at 30003', 'Unused space'),
                (30004, 'Text at 7534', 'Text'),
                (30005, 'Unused bytes at 30005', 'Unused bytes'),
                (30006, 'Words at 30006', 'Words at WORDS')
        ):
            path = '{}/{}.html'.format(asm_path, address)
            self._assert_title_equals(path, exp_title, exp_header)

    def test_write_other_code_using_single_page_template(self):
        code_id = 'other'
        ref = """
            [Game]
            AsmSinglePage=1
            [OtherCode:{}]
        """.format(code_id)
        other_skool = """
            ; Routine at 40000
            c40000 JR 40002

            ; Routine at 40002
            c40002 JR 40000
        """
        main_writer = self._get_writer(ref=ref, skool=other_skool)
        code = main_writer.other_code[0][1]
        index_page_id = code['IndexPageId']
        self.assertEqual(index_page_id, '{}-Index'.format(code_id))
        map_path = main_writer.paths[index_page_id]
        self.assertEqual(map_path, '{0}/{0}.html'.format(code_id))
        code_path_id = code['CodePathId']
        self.assertEqual(code_path_id, '{}-CodePath'.format(code_id))
        asm_path = main_writer.paths[code_path_id]
        self.assertEqual(asm_path, code_id)
        writer = main_writer.clone(main_writer.parser, code_id)
        writer.write_file = self._mock_write_file
        content = """
            <div id="40000" class="description">40000: Routine at 40000</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="40000"></span>40000</td>
            <td class="instruction">JR <a href="#40002">40002</a></td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
            <div id="40002" class="description">40002: Routine at 40002</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="40002"></span>40002</td>
            <td class="instruction">JR <a href="#40000">40000</a></td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'header': code_id,
            'body_class': '{}-AsmSinglePage'.format(code_id),
            'content': content
        }

        writer.write_entries(asm_path, map_path)
        self._assert_files_equal('{}/asm.html'.format(asm_path), subs)

    def test_write_other_code_using_single_page_template_with_custom_path_and_title_and_header(self):
        code_id = 'other'
        path = 'code.html'
        title = 'All the other code'
        header = 'The disassembly'
        ref = """
            [Game]
            AsmSinglePage=1
            [Paths]
            {0}-AsmSinglePage={1}
            [Titles]
            {0}-AsmSinglePage={2}
            [PageHeaders]
            {0}-AsmSinglePage={3}
            [OtherCode:{0}]
        """.format(code_id, path, title, header)
        other_skool = '; Routine at 40000\nc40000 RET'
        main_writer = self._get_writer(ref=ref, skool=other_skool)
        code = main_writer.other_code[0][1]
        index_page_id = code['IndexPageId']
        self.assertEqual(index_page_id, '{}-Index'.format(code_id))
        map_path = main_writer.paths[index_page_id]
        self.assertEqual(map_path, '{0}/{0}.html'.format(code_id))
        code_path_id = code['CodePathId']
        self.assertEqual(code_path_id, '{}-CodePath'.format(code_id))
        asm_path = main_writer.paths[code_path_id]
        self.assertEqual(asm_path, code_id)
        writer = main_writer.clone(main_writer.parser, code_id)
        writer.write_file = self._mock_write_file
        content = """
            <div id="40000" class="description">40000: Routine at 40000</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="40000"></span>40000</td>
            <td class="instruction">RET</td>
            <td class="comment-0" rowspan="1"></td>
            </tr>
            </table>
        """
        subs = {
            'title': title,
            'header': header,
            'path': '',
            'body_class': '{}-AsmSinglePage'.format(code_id),
            'content': content
        }

        writer.write_entries(asm_path, map_path)
        self._assert_files_equal(path, subs)

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
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-c"><span id="65535"></span><a href="65535.html">65535</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="65535.html">{}</a></div>
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

    def test_write_other_code_index_using_single_page_template(self):
        code_id = 'other'
        ref = """
            [Game]
            AsmSinglePage=1
            [OtherCode:{}]
        """.format(code_id)
        routine_title = 'Other code'
        skool = '; {}\nc65535 RET'.format(routine_title)
        main_writer = self._get_writer(ref=ref, skool=skool)
        writer = main_writer.clone(main_writer.parser, code_id)
        writer.write_file = self._mock_write_file
        code = main_writer.other_code[0][1]
        index_page_id = code['IndexPageId']
        self.assertEqual(index_page_id, '{}-Index'.format(code_id))
        index_path = writer.paths[index_page_id]
        self.assertEqual(index_path, '{0}/{0}.html'.format(code_id))
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-c"><span id="65535"></span><a href="asm.html#65535">65535</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="asm.html#65535">{}</a></div>
            </td>
            </tr>
            </table>
        """.format(routine_title)
        subs = {
            'header': code_id,
            'body_class': index_page_id,
            'content': content
        }

        writer.write_map(index_page_id)
        self._assert_files_equal(index_path, subs)

    def test_write_other_code_index_using_single_page_template_with_custom_path(self):
        code_id = 'secondary'
        asm_single_page = 'disassembly.html'
        ref = """
            [Game]
            AsmSinglePage=1
            [Paths]
            {0}-AsmSinglePage={0}/{1}
            [OtherCode:{0}]
        """.format(code_id, asm_single_page)
        routine_title = 'Other code'
        skool = '; {}\nc65535 RET'.format(routine_title)
        main_writer = self._get_writer(ref=ref, skool=skool)
        writer = main_writer.clone(main_writer.parser, code_id)
        writer.write_file = self._mock_write_file
        code = main_writer.other_code[0][1]
        index_page_id = code['IndexPageId']
        self.assertEqual(index_page_id, '{}-Index'.format(code_id))
        index_path = writer.paths[index_page_id]
        self.assertEqual(index_path, '{0}/{0}.html'.format(code_id))
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th>Address</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-c"><span id="65535"></span><a href="{0}#65535">65535</a></td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="{0}#65535">{1}</a></div>
            </td>
            </tr>
            </table>
        """.format(asm_single_page, routine_title)
        subs = {
            'header': code_id,
            'body_class': index_page_id,
            'content': content
        }

        writer.write_map(index_page_id)
        self._assert_files_equal(index_path, subs)

    def test_write_changelog(self):
        ref = """
            [Changelog:20120706]
            -

            There are blank lines...

            ...between these...

            ...top-level items
            [Changelog:20120705]
            -

            There are no blank lines...
            ...between these...
            ...top-level items
            [Changelog:20120704]
            Documented many #LINK:Bugs(bugs).

            1
              2
                3
                4
              5

            6
            [Changelog:20120703]
            -

            1
              2
                3
            4
            [Changelog:20120702]
            Initial release
        """
        content = """
            <ul class="contents">
            <li><a href="#20120706">20120706</a></li>
            <li><a href="#20120705">20120705</a></li>
            <li><a href="#20120704">20120704</a></li>
            <li><a href="#20120703">20120703</a></li>
            <li><a href="#20120702">20120702</a></li>
            </ul>
            <div><span id="20120706"></span></div>
            <div class="list-entry list-entry-1">
            <div class="list-entry-title">20120706</div>
            <div class="list-entry-desc"></div>
            <ul class="list-entry">
            <li>There are blank lines...</li>
            <li>...between these...</li>
            <li>...top-level items</li>
            </ul>
            </div>
            <div><span id="20120705"></span></div>
            <div class="list-entry list-entry-2">
            <div class="list-entry-title">20120705</div>
            <div class="list-entry-desc"></div>
            <ul class="list-entry">
            <li>There are no blank lines...</li>
            <li>...between these...</li>
            <li>...top-level items</li>
            </ul>
            </div>
            <div><span id="20120704"></span></div>
            <div class="list-entry list-entry-1">
            <div class="list-entry-title">20120704</div>
            <div class="list-entry-desc">Documented many <a href="bugs.html">bugs</a>.</div>
            <ul class="list-entry">
            <li>1
            <ul class="list-entry1">
            <li>2
            <ul class="list-entry2">
            <li>3</li>
            <li>4</li>
            </ul>
            </li>
            <li>5</li>
            </ul>
            </li>
            <li>6</li>
            </ul>
            </div>
            <div><span id="20120703"></span></div>
            <div class="list-entry list-entry-2">
            <div class="list-entry-title">20120703</div>
            <div class="list-entry-desc"></div>
            <ul class="list-entry">
            <li>1
            <ul class="list-entry1">
            <li>2
            <ul class="list-entry2">
            <li>3</li>
            </ul>
            </li>
            </ul>
            </li>
            <li>4</li>
            </ul>
            </div>
            <div><span id="20120702"></span></div>
            <div class="list-entry list-entry-1">
            <div class="list-entry-title">20120702</div>
            <div class="list-entry-desc">Initial release</div>
            </div>
        """
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page('Changelog')
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
        ref = """
            [Titles]
            Changelog={}
            [PageHeaders]
            Changelog={}
            [Paths]
            Changelog={}
        """.format(title, header, path)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page('Changelog')
        self._assert_title_equals(path, title, header)

    def test_write_changelog_entry_with_specified_anchor(self):
        anchor = 'latest'
        title = '20161101'
        ref = """
            [Changelog:{}:{}]
            -

            Item 1
        """.format(anchor, title)
        content = """
            <ul class="contents">
            <li><a href="#{0}">{1}</a></li>
            </ul>
            <div><span id="{0}"></span></div>
            <div class="list-entry list-entry-1">
            <div class="list-entry-title">{1}</div>
            <div class="list-entry-desc"></div>
            <ul class="list-entry">
            <li>Item 1</li>
            </ul>
            </div>
        """.format(anchor, title)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page('Changelog')
        subs = {
            'header': 'Changelog',
            'body_class': 'Changelog',
            'content': content
        }
        self._assert_files_equal(join(REFERENCE_DIR, 'changelog.html'), subs)

    def test_write_glossary(self):
        ref = """
            [Glossary:Term1]
            Definition 1.

            [Glossary:Term2]
            Definition 2. Paragraph 1.

            Definition 2. Paragraph 2.
        """
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
        writer.write_page('Glossary')
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
        ref = """
            [Titles]
            Glossary={}
            [PageHeaders]
            Glossary={}
            [Paths]
            Glossary={}
        """.format(title, header, path)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page('Glossary')
        self._assert_title_equals(path, title, header)

    def test_write_page(self):
        page_id = 'CustomPage'
        ref = """
            [Page:{0}]
            JavaScript=test-html.js
            PageContent=<b>This is the content of the custom page.</b>

            [PageHeaders]
            {0}=Custom page

            [Titles]
            {0}=Custom page
        """.format(page_id)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        subs = {
            'title': 'Custom page',
            'header': 'Custom page',
            'path': '',
            'body_class': page_id,
            'js': 'test-html.js',
            'content': '<b>This is the content of the custom page.</b>\n'
        }
        self._assert_files_equal('{}.html'.format(page_id), subs)

    def test_write_page_with_section_prefix(self):
        page_id = 'mypage'
        header = 'Welcome to my page'
        title = 'This is my page'
        ref = """
            [Page:{0}]
            JavaScript={0}.js
            SectionPrefix={0}
            [{0}:item1:Item 1]
            Item 1, paragraph 1.

            Item 1, paragraph 2.
            [{0}:item2:Item 2]
            Item 2, paragraph 1.

            Item 2, paragraph 2.
            [Titles]
            {0}={1}
            [PageHeaders]
            {0}={2}
        """.format(page_id, title, header)
        exp_content = """
            <ul class="contents">
            <li><a href="#item1">Item 1</a></li>
            <li><a href="#item2">Item 2</a></li>
            </ul>
            <div><span id="item1"></span></div>
            <div class="box box-1">
            <div class="box-title">Item 1</div>
            <div class="paragraph">
            Item 1, paragraph 1.
            </div>
            <div class="paragraph">
            Item 1, paragraph 2.
            </div>
            </div>
            <div><span id="item2"></span></div>
            <div class="box box-2">
            <div class="box-title">Item 2</div>
            <div class="paragraph">
            Item 2, paragraph 1.
            </div>
            <div class="paragraph">
            Item 2, paragraph 2.
            </div>
            </div>
        """

        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        subs = {
            'title': title,
            'header': header,
            'path': '',
            'body_class': page_id,
            'js': '{}.js'.format(page_id),
            'content': exp_content
        }
        self._assert_files_equal('{}.html'.format(page_id), subs)

    def test_write_page_with_section_prefix_and_missing_anchor(self):
        page_id = 'Custom'
        title = 'Item 1\t(First)'
        exp_anchor = 'item_1__first_'
        ref = """
            [Page:{0}]
            SectionPrefix={0}
            [{0}:{1}]
            This is an item.
        """.format(page_id, title)
        content = """
            <ul class="contents">
            <li><a href="#{0}">{1}</a></li>
            </ul>
            <div><span id="{0}"></span></div>
            <div class="box box-1">
            <div class="box-title">{1}</div>
            <div class="paragraph">
            This is an item.
            </div>
            </div>
        """.format(exp_anchor, title)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        subs = {
            'title': page_id,
            'header': page_id,
            'path': '',
            'body_class': page_id,
            'content': content
        }
        self._assert_files_equal('{}.html'.format(page_id), subs)

    def test_write_page_with_section_prefix_and_custom_parameter(self):
        ref = """
            [Page:MyPage]
            SectionPrefix=Item
            intro=Welcome to my page!

            [Item:item1:Item 1]
            An item.

            [Template:MyPage]
            {Page[intro]}
            - {entries[0][contents][0]}
        """
        exp_content = """
            Welcome to my page!
            - An item.
        """

        writer = self._get_writer(ref=ref, skool='')
        writer.write_page('MyPage')
        self._assert_content_equal(exp_content, 'MyPage.html')

    def test_write_page_with_section_prefix_as_list_items(self):
        page_id = 'MyListItemsPage'
        ref = """
            [Page:{0}]
            SectionPrefix=Entry
            SectionType=ListItems
            [Entry:entry1:Entry 1]
            Intro.

            Item 1
              Subitem 1A
              Subitem 1B
            Item 2
        """.format(page_id)
        exp_content = """
            <ul class="contents">
            <li><a href="#entry1">Entry 1</a></li>
            </ul>
            <div><span id="entry1"></span></div>
            <div class="list-entry list-entry-1">
            <div class="list-entry-title">Entry 1</div>
            <div class="list-entry-desc">Intro.</div>
            <ul class="list-entry">
            <li>Item 1
            <ul class="list-entry1">
            <li>Subitem 1A</li>
            <li>Subitem 1B</li>
            </ul>
            </li>
            <li>Item 2</li>
            </ul>
            </div>
        """

        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        subs = {
            'title': page_id,
            'header': page_id,
            'path': '',
            'body_class': page_id,
            'content': exp_content
        }
        self._assert_files_equal('{}.html'.format(page_id), subs)

    def test_write_page_with_section_prefix_as_list_items_and_custom_parameter(self):
        ref = """
            [Page:MyPage]
            SectionPrefix=Item
            SectionType=ListItems
            intro=Welcome to my page!

            [Item:item1:Item 1]
            A list item.

            [Template:MyPage]
            {Page[intro]}
            - {entries[0][intro]}
        """
        exp_content = """
            Welcome to my page!
            - A list item.
        """

        writer = self._get_writer(ref=ref, skool='')
        writer.write_page('MyPage')
        self._assert_content_equal(exp_content, 'MyPage.html')

    def test_write_page_with_header_prefix_and_suffix(self):
        page_id = 'CustomPage'
        ref = """
            [Page:{0}]
            PageContent=Hello
            [PageHeaders]
            {0}=Prefix<>Suffix
        """.format(page_id)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        subs = {
            'title': page_id,
            'header': ('Prefix', 'Suffix'),
            'path': '',
            'body_class': page_id,
            'content': 'Hello\n'
        }
        self._assert_files_equal('{}.html'.format(page_id), subs)

    def test_write_bugs(self):
        ref = """
            [Bug:b1:Showstopper]
            This bug is bad.

            Really bad.
        """
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
        writer.write_page('Bugs')
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
        ref = """
            [Titles]
            Bugs={}
            [PageHeaders]
            Bugs={}
            [Paths]
            Bugs={}
        """.format(title, header, path)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page('Bugs')
        self._assert_title_equals(path, title, header)

    def test_write_bugs_with_missing_anchor(self):
        ref = """
            [Bug:Bug 1]
            This is a bug.
        """
        content = """
            <ul class="contents">
            <li><a href="#bug_1">Bug 1</a></li>
            </ul>
            <div><span id="bug_1"></span></div>
            <div class="box box-1">
            <div class="box-title">Bug 1</div>
            <div class="paragraph">
            This is a bug.
            </div>
            </div>
        """
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page('Bugs')
        subs = {
            'header': 'Bugs',
            'body_class': 'Bugs',
            'content': content
        }
        self._assert_files_equal(join(REFERENCE_DIR, 'bugs.html'), subs)

    def test_write_facts(self):
        ref = """
            [Fact:f1:Interesting fact]
            Hello.

            Goodbye.

            [Fact:f2:Another interesting fact]
            Yes.
        """
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
        writer.write_page('Facts')
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
        ref = """
            [Titles]
            Facts={}
            [PageHeaders]
            Facts={}
            [Paths]
            Facts={}
        """.format(title, header, path)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page('Facts')
        self._assert_title_equals(path, title, header)

    def test_write_facts_with_missing_anchor(self):
        ref = """
            [Fact:Fact A]
            This is a fact.
        """
        content = """
            <ul class="contents">
            <li><a href="#fact_a">Fact A</a></li>
            </ul>
            <div><span id="fact_a"></span></div>
            <div class="box box-1">
            <div class="box-title">Fact A</div>
            <div class="paragraph">
            This is a fact.
            </div>
            </div>
        """
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page('Facts')
        subs = {
            'header': 'Trivia',
            'body_class': 'Facts',
            'content': content
        }
        self._assert_files_equal(join(REFERENCE_DIR, 'facts.html'), subs)

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
        writer.write_page('Pokes')
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
        ref = """
            [Titles]
            Pokes={}
            [PageHeaders]
            Pokes={}
            [Paths]
            Pokes={}
        """.format(title, header, path)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page('Pokes')
        self._assert_title_equals(path, title, header)

    def test_write_pokes_with_missing_anchor(self):
        ref = """
            [Poke:POKE A]
            This is a POKE.
        """
        content = """
            <ul class="contents">
            <li><a href="#poke_a">POKE A</a></li>
            </ul>
            <div><span id="poke_a"></span></div>
            <div class="box box-1">
            <div class="box-title">POKE A</div>
            <div class="paragraph">
            This is a POKE.
            </div>
            </div>
        """
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page('Pokes')
        subs = {
            'header': 'Pokes',
            'body_class': 'Pokes',
            'content': content
        }
        self._assert_files_equal(join(REFERENCE_DIR, 'pokes.html'), subs)

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
        writer.write_page('GraphicGlitches')
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
        ref = """
            [Titles]
            GraphicGlitches={}
            [PageHeaders]
            GraphicGlitches={}
            [Paths]
            GraphicGlitches={}
        """.format(title, header, path)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page('GraphicGlitches')
        self._assert_title_equals(path, title, header)

    def test_write_graphic_glitches_with_missing_anchor(self):
        ref = """
            [GraphicGlitch:Glitch 1]
            This is a graphic glitch.
        """
        content = """
            <ul class="contents">
            <li><a href="#glitch_1">Glitch 1</a></li>
            </ul>
            <div><span id="glitch_1"></span></div>
            <div class="box box-1">
            <div class="box-title">Glitch 1</div>
            <div class="paragraph">
            This is a graphic glitch.
            </div>
            </div>
        """
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page('GraphicGlitches')
        subs = {
            'header': 'Graphic glitches',
            'body_class': 'GraphicGlitches',
            'content': content
        }
        self._assert_files_equal(join(GRAPHICS_DIR, 'glitches.html'), subs)

    def test_write_gsb_page(self):
        skool = """
            ; GSB entry 1
            ;
            ; Number of lives.
            g30000 DEFB 4

            ; GSB entry 2
            g30001 DEFW 78

            ; Not a game status buffer entry
            t30003 DEFM "a"
        """
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th>Address</th>
            <th class="map-length">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-g"><span id="30000"></span><a href="../asm/30000.html">30000</a></td>
            <td class="map-length">1</td>
            <td class="map-g-desc">
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30000.html">GSB entry 1</a></div>
            <div class="map-entry-desc">
            <div class="paragraph">
            Number of lives.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-g"><span id="30001"></span><a href="../asm/30001.html">30001</a></td>
            <td class="map-length">2</td>
            <td class="map-g-desc">
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30001.html">GSB entry 2</a></div>
            <div class="map-entry-desc">
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
        ref = """
            [MemoryMap:GameStatusBuffer]
            EntryTypes=g
            Includes=30003,30004
        """
        skool = """
            ; GSB entry 1
            ;
            ; Number of lives.
            g30000 DEFB 4

            ; GSB entry 2
            g30001 DEFW 78

            ; Message ID
            t30003 DEFB 0

            ; Another message ID
            t30004 DEFB 0

            ; Not a game status buffer entry
            c30005 RET

            i30006
        """
        content = """
            <div class="map-intro"></div>
            <table class="map">
            <tr>
            <th>Address</th>
            <th class="map-length">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-g"><span id="30000"></span><a href="../asm/30000.html">30000</a></td>
            <td class="map-length">1</td>
            <td class="map-g-desc">
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30000.html">GSB entry 1</a></div>
            <div class="map-entry-desc">
            <div class="paragraph">
            Number of lives.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-g"><span id="30001"></span><a href="../asm/30001.html">30001</a></td>
            <td class="map-length">2</td>
            <td class="map-g-desc">
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30001.html">GSB entry 2</a></div>
            <div class="map-entry-desc">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-t"><span id="30003"></span><a href="../asm/30003.html">30003</a></td>
            <td class="map-length">1</td>
            <td class="map-t-desc">
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30003.html">Message ID</a></div>
            <div class="map-entry-desc">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-t"><span id="30004"></span><a href="../asm/30004.html">30004</a></td>
            <td class="map-length">1</td>
            <td class="map-t-desc">
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30004.html">Another message ID</a></div>
            <div class="map-entry-desc">
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
        ref = """
            [Titles]
            GameStatusBuffer={}
            [PageHeaders]
            GameStatusBuffer={}
            [Paths]
            GameStatusBuffer={}
        """.format(title, header, path)
        writer = self._get_writer(ref=ref, skool='g32768 DEFB 0')
        writer.write_map('GameStatusBuffer')
        self._assert_title_equals(path, title, header)

    def test_page_content(self):
        ref = '[Page:ExistingPage]\nContent=asm/32768.html'
        writer = self._get_writer(ref=ref)
        self.assertNotIn('ExistingPage', writer.page_ids)
        self.assertIn('ExistingPage', writer.paths)
        self.assertTrue(writer.paths['ExistingPage'], 'asm/32768.html')

    def test_unwritten_maps(self):
        ref = '[MemoryMap:UnusedMap]\nWrite=0'
        skool = """
            ; Routine
            c40000 RET

            ; Data
            b40001 DEFB 0

            ; Unused
            u40002 DEFB 0
        """
        writer = self._get_writer(ref=ref, skool=skool)
        self.assertIn('MemoryMap', writer.main_memory_maps)
        self.assertIn('RoutinesMap', writer.main_memory_maps)
        self.assertIn('DataMap', writer.main_memory_maps)
        self.assertNotIn('MessagesMap', writer.main_memory_maps) # No entries
        self.assertNotIn('UnusedMap', writer.main_memory_maps)   # Write=0

    def test_registers(self):
        skool = """
            ; Test registers
            ;
            ; .
            ;
            ; A Some value
            ; B Some other value
            ; #CHR(67) No macro expansion
            c24576 RET ; Done
        """
        writer = self._get_writer(skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">24576: Test registers</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            <table class="input">
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
            <tr>
            <td class="register">#CHR(67)</td>
            <td class="register-desc">No macro expansion</td>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="24576"></span>24576</td>
            <td class="instruction">RET</td>
            <td class="comment-1" rowspan="1">Done</td>
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

    def test_registers_with_prefixes(self):
        skool = """
            ; Routine at 24576
            ;
            ; .
            ;
            ;  Input:A Some value
            ;        B Some other value
            ; Output:D The result
            ;        E Result flags
            c24576 RET ; Done
        """
        writer = self._get_writer(skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">24576: Routine at 24576</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            <table class="input">
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
            <table class="output">
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
            <td class="address-2"><span id="24576"></span>24576</td>
            <td class="instruction">RET</td>
            <td class="comment-1" rowspan="1">Done</td>
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

    def test_registers_with_arbitrary_names(self):
        skool = """
            ; Test registers with arbitrary names
            ;
            ; .
            ;
            ; |Input:The accumulator| Some value
            ;        {B and C} Some other values
            ; *Output:HL* The result
            ;         /DE Another result
            ;         [(#R24796)] Yet another result
            c24795 RET ; Done

            ; Result storage
            b24796 DEFB 0
        """
        writer = self._get_writer(skool=skool)
        writer.write_asm_entries()

        content = """
            <div class="description">24795: Test registers with arbitrary names</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
            <div class="details">
            </div>
            <table class="input">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            <tr>
            <td class="register">The accumulator</td>
            <td class="register-desc">Some value</td>
            </tr>
            <tr>
            <td class="register">B and C</td>
            <td class="register-desc">Some other values</td>
            </tr>
            </table>
            <table class="output">
            <tr class="asm-output-header">
            <th colspan="2">Output</th>
            </tr>
            <tr>
            <td class="register">HL</td>
            <td class="register-desc">The result</td>
            </tr>
            <tr>
            <td class="register">/DE</td>
            <td class="register-desc">Another result</td>
            </tr>
            <tr>
            <td class="register">(<a href="24796.html">24796</a>)</td>
            <td class="register-desc">Yet another result</td>
            </tr>
            </table>
            </td>
            </tr>
            <tr>
            <td class="address-2"><span id="24795"></span>24795</td>
            <td class="instruction">RET</td>
            <td class="comment-1" rowspan="1">Done</td>
            </tr>
            </table>
        """
        subs = {
            'title': 'Routine at 24795',
            'body_class': 'Asm-c',
            'header': 'Routines',
            'up': 24795,
            'next': 24796,
            'content': content
        }
        self._assert_files_equal(join(ASMDIR, '24795.html'), subs)

    def test_write_page_with_single_global_js(self):
        global_js = 'js/global.js'
        page_id = 'Custom'
        ref = """
            [Game]
            JavaScript={0}
            [Page:{1}]
            [Template:{1}]
            <# foreach($js,SkoolKit[javascripts]) #>
            <script type="text/javascript" src="{{$js[src]}}"></script>
            <# endfor #>
        """.format(global_js, page_id)
        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        js_path = basename(global_js)
        self.assertEqual(self._read_file(page_id + '.html'), '<script type="text/javascript" src="{}"></script>'.format(js_path))

    def test_write_page_with_multiple_global_js(self):
        js_files = ['js/global1.js', 'js.global2.js']
        global_js = ';'.join(js_files)
        page_id = 'Custom'
        ref = """
            [Game]
            JavaScript={0}
            [Page:{1}]
            Path=
            [Template:{1}]
            <# foreach($js,SkoolKit[javascripts]) #>
            <script type="text/javascript" src="{{$js[src]}}"></script>
            <# endfor #>
        """.format(global_js, page_id)
        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        js_paths = [basename(js) for js in js_files]
        page = self._read_file(page_id + '.html', True)
        self.assertEqual(page[0], '<script type="text/javascript" src="{}"></script>'.format(js_paths[0]))
        self.assertEqual(page[1], '<script type="text/javascript" src="{}"></script>'.format(js_paths[1]))

    def test_write_page_with_single_local_js(self):
        page_id = 'Custom'
        js = 'js/script.js'
        ref = """
            [Page:{0}]
            JavaScript={1}
            [Template:{0}]
            <# foreach($js,SkoolKit[javascripts]) #>
            <script type="text/javascript" src="{{$js[src]}}"></script>
            <# endfor #>
        """.format(page_id, js)
        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        js_path = basename(js)
        self.assertEqual(self._read_file(page_id + '.html'), '<script type="text/javascript" src="{}"></script>'.format(js_path))

    def test_write_page_with_multiple_local_js(self):
        page_id = 'Custom'
        js_files = ['js/script1.js', 'js/script2.js']
        js = ';'.join(js_files)
        ref = """
            [Page:{0}]
            JavaScript={1}
            [Template:{0}]
            <# foreach($js,SkoolKit[javascripts]) #>
            <script type="text/javascript" src="{{$js[src]}}"></script>
            <# endfor #>
        """.format(page_id, js)
        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        js_paths = [basename(js) for js in js_files]
        page = self._read_file(page_id + '.html', True)
        self.assertEqual(page[0], '<script type="text/javascript" src="{}"></script>'.format(js_paths[0]))
        self.assertEqual(page[1], '<script type="text/javascript" src="{}"></script>'.format(js_paths[1]))

    def test_write_page_with_local_and_global_js(self):
        global_js_files = ['js/global1.js', 'js.global2.js']
        global_js = ';'.join(global_js_files)
        local_js_files = ['js/local1.js', 'js/local2.js']
        local_js = ';'.join(local_js_files)
        page_id = 'Custom'
        ref = """
            [Game]
            JavaScript={0}
            [Page:{1}]
            JavaScript={2}
            [Template:{1}]
            <# foreach($js,SkoolKit[javascripts]) #>
            <script type="text/javascript" src="{{$js[src]}}"></script>
            <# endfor #>
        """.format(global_js, page_id, local_js)
        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        page = self._read_file(page_id + '.html', True)
        for i, js in enumerate(global_js_files + local_js_files):
            self.assertEqual(page[i], '<script type="text/javascript" src="{}"></script>'.format(basename(js)))

    def test_write_default_box_page_with_local_js(self):
        page_id = 'Custom'
        js = 'js/script.js'
        ref = """
            [Page:{0}]
            JavaScript={1}
            SectionPrefix=Box
            [Box:box1]
            Hi.
            [Template:{0}]
            <# foreach($js,SkoolKit[javascripts]) #>
            <script type="text/javascript" src="{{$js[src]}}"></script>
            <# endfor #>
        """.format(page_id, js)
        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        js_path = basename(js)
        self.assertEqual(self._read_file(page_id + '.html'), '<script type="text/javascript" src="{}"></script>'.format(js_path))

    def test_write_list_items_box_page_with_local_js(self):
        page_id = 'Custom'
        js = 'js/script.js'
        ref = """
            [Page:{0}]
            JavaScript={1}
            SectionPrefix=Box
            SectionType=ListItems
            [Box:box1]
            Hi.
            [Template:{0}]
            <# foreach($js,SkoolKit[javascripts]) #>
            <script type="text/javascript" src="{{$js[src]}}"></script>
            <# endfor #>
        """.format(page_id, js)
        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        js_path = basename(js)
        self.assertEqual(self._read_file(page_id + '.html'), '<script type="text/javascript" src="{}"></script>'.format(js_path))

    def test_write_bullet_points_box_page_with_local_js(self):
        page_id = 'Custom'
        js = 'js/script.js'
        ref = """
            [Page:{0}]
            JavaScript={1}
            SectionPrefix=Box
            SectionType=BulletPoints
            [Box:box1]
            Hi.
            [Template:{0}]
            <# foreach($js,SkoolKit[javascripts]) #>
            <script type="text/javascript" src="{{$js[src]}}"></script>
            <# endfor #>
        """.format(page_id, js)
        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        js_path = basename(js)
        self.assertEqual(self._read_file(page_id + '.html'), '<script type="text/javascript" src="{}"></script>'.format(js_path))

    def test_write_page_with_single_css(self):
        css = 'css/game.css'
        page_id = 'Custom'
        ref = """
            [Game]
            StyleSheet={0}
            [Page:{1}]
            Path=
            [Template:{1}]
            <# foreach($css,SkoolKit[stylesheets]) #>
            <link rel="stylesheet" type="text/css" href="{{$css[href]}}" />
            <# endfor #>
        """.format(css, page_id)
        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        page = self._read_file(page_id + '.html')
        self.assertEqual(page, '<link rel="stylesheet" type="text/css" href="{}" />'.format(basename(css)))

    def test_write_page_with_multiple_css(self):
        css_files = ['css/game.css', 'css/foo.css']
        page_id = 'Custom'
        ref = """
            [Game]
            StyleSheet={0}
            [Page:{1}]
            Path=
            [Template:{1}]
            <# foreach($css,SkoolKit[stylesheets]) #>
            <link rel="stylesheet" type="text/css" href="{{$css[href]}}" />
            <# endfor #>
        """.format(';'.join(css_files), page_id)
        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        page = self._read_file(page_id + '.html', True)
        css_paths = [basename(css) for css in css_files]
        self.assertEqual(page[0], '<link rel="stylesheet" type="text/css" href="{}" />'.format(css_paths[0]))
        self.assertEqual(page[1], '<link rel="stylesheet" type="text/css" href="{}" />'.format(css_paths[1]))

    def test_write_page_no_game_name(self):
        page_id = 'Custom'
        path = '{}.html'.format(page_id)
        ref = """
            [Page:{0}]
            [Template:{0}]
            {{Game[Logo]}}
        """.format(page_id)
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
        ref = """
            [Game]
            Game={0}
            [Page:{1}]
            [Paths]
            {1}={2}
            [Template:{1}]
            {{Game[Logo]}}
        """.format(game_name, page_id, path)
        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        page = self._read_file(path, True)
        self.assertEqual(page[0], game_name)

    def test_write_page_with_nonexistent_logo_image(self):
        page_id = 'Custom'
        cwd = 'subdir'
        path = '{}/custom.html'.format(cwd)
        ref = """
            [Game]
            LogoImage=images/nonexistent.png
            [Page:{0}]
            [Paths]
            {0}={1}
            [Template:{0}]
            {{Game[Logo]}}
        """.format(page_id, path)
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
        ref = """
            [Game]
            LogoImage={0}
            [Page:{1}]
            [Paths]
            {1}={2}
            [Template:{1}]
            {{Game[Logo]}}
        """.format(logo_image_fname, page_id, path)
        writer = self._get_writer(ref=ref, skool='')
        logo_image = self.write_bin_file(path=join(writer.file_info.odir, logo_image_fname))
        writer.write_page(page_id)
        logo = writer.relpath(cwd, logo_image_fname)
        game_name = self.skoolfile[:-6]
        page = self._read_file(path, True)
        self.assertEqual(page[0], '<img alt="{}" src="{}" />'.format(game_name, logo))

    def test_write_page_with_logo(self):
        logo = 'ABC #UDG30000 123'
        page_id = 'custom'
        ref = """
            [Game]
            Logo={0}
            [Page:{1}]
            [Template:{1}]
            {{Game[Logo]}}
        """.format(logo, page_id)
        writer = self._get_writer(ref=ref, skool='')
        cwd = ''
        writer.write_page(page_id)
        logo_value = writer.expand(logo, cwd)
        page = self._read_file('{}.html'.format(page_id), True)
        self.assertEqual(page[0], logo_value)

    def test_write_page_with_path_and_title_and_page_header_containing_skool_macros(self):
        page_id = 'SMTest'
        content = 'Hi.'
        ref = """
            [Page:{0}]
            PageContent={1}

            [Paths]
            {0}=item#EVAL85,16.html

            [PageHeaders]
            {0}=Item #EVAL85,2,8

            [Titles]
            {0}=Items (#EVAL85,2,8)
        """.format(page_id, content)
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        subs = {
            'title': 'Items (01010101)',
            'header': 'Item 01010101',
            'path': '',
            'body_class': page_id,
            'content': content
        }
        self._assert_files_equal('item55.html', subs)

    def test_write_page_with_broken_template(self):
        page_id = 'Custom'
        ref = """
            [Page:{0}]
            [Template:{0}]
            {{this_will_not_work}}
        """.format(page_id)
        writer = self._get_writer(ref=ref)
        with self.assertRaisesRegex(SkoolKitError, "^Unknown field 'this_will_not_work' in Custom template$"):
            writer.write_page(page_id)

    @patch.object(components, 'SK_CONFIG', None)
    def test_custom_image_writer(self):
        custom_image_writer = """
            class CustomImageWriter:
                def __init__(self, options, palette):
                    pass
                def image_fname(self, fname):
                    return fname
                def write_image(self, frames, img_file):
                    img_file.write(b'hello')
        """
        self.write_component_config('ImageWriter', '*.CustomImageWriter', custom_image_writer)
        page_id = 'Stuff'
        img_fname = 'thing.gif'
        ref = """
            [Page:{}]
            PageContent=#UDG0({})
        """.format(page_id, img_fname)
        writer = self._get_writer(ref=ref, mock_image_writer=False, mock_file_info=True)
        writer.write_page(page_id)
        self.assertEqual(writer.file_info.files['images/udgs/{}'.format(img_fname)], b'hello')

    @patch.object(components, 'SK_CONFIG', None)
    def test_custom_image_writer_returning_content(self):
        custom_image_writer = """
            class CustomImageWriter:
                def __init__(self, options, palette):
                    pass
                def image_fname(self, fname):
                    return fname
                def write_image(self, frames, img_file):
                    return 'goodbye'
        """
        self.write_component_config('ImageWriter', '*.CustomImageWriter', custom_image_writer)
        page_id = 'Stuff'
        img_fname = 'thing.gif'
        ref = """
            [Page:{0}]
            PageContent=#UDG0({1})

            [Template:{0}]
            {{Page[PageContent]}}
        """.format(page_id, img_fname)
        writer = self._get_writer(ref=ref, mock_image_writer=False)
        writer.write_page(page_id)
        self._assert_content_equal('goodbye', '{}.html'.format(page_id))
        img_dir = '{}/{}/{}'.format(self.odir, GAMEDIR, UDGDIR)
        self.assertTrue(isdir(img_dir))
        img_path = '{}/{}'.format(img_dir, img_fname)
        self.assertFalse(isfile(img_path), '{} exists'.format(img_path))

class HtmlTemplateTest(HtmlWriterOutputTestCase):
    def test_custom_map_with_custom_page_template(self):
        map_id = 'CustomMap'
        ref = """
            [MemoryMap:{0}]
            EntryTypes=c
            Intro=Bar
            [Template:{0}]
            <foo>{{MemoryMap[Intro]}}</foo>
        """.format(map_id)

        writer = self._get_writer(ref=ref, skool='c50000 RET')
        writer.write_map(map_id)
        path = 'maps/{}.html'.format(map_id)
        self.assertEqual('<foo>Bar</foo>', self.files[path])

    def test_changelog_with_custom_item_list_template(self):
        # Test that the 'Changelog-item_list' template is used if defined
        # instead of the default 'item_list' template)
        ref = """
            [Changelog:20141123]
            -

            Item 1
            Item 2

            [Template:Changelog-item_list]
            <ul class="list-entry{indent}">
            <# foreach($item,items) #>
            <li>* {$item[text]}</li>
            <# endfor #>
            </ul>
        """
        content = """
            <ul class="contents">
            <li><a href="#20141123">20141123</a></li>
            </ul>
            <div><span id="20141123"></span></div>
            <div class="list-entry list-entry-1">
            <div class="list-entry-title">20141123</div>
            <div class="list-entry-desc"></div>
            <ul class="list-entry">
            <li>* Item 1</li>
            <li>* Item 2</li>
            </ul>
            </div>
        """

        writer = self._get_writer(ref=ref, skool='')
        writer.write_page('Changelog')
        subs = {
            'header': 'Changelog',
            'body_class': 'Changelog',
            'content': content
        }
        self._assert_files_equal(join(REFERENCE_DIR, 'changelog.html'), subs)

    def test_page_with_custom_page_template(self):
        page_id = 'Custom'
        content = 'hello'
        ref = """
            [Page:{0}]
            PageContent={1}
            [Template:{0}]
            <foo>{{Page[PageContent]}}</foo>
        """.format(page_id, content)

        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        path = '{}.html'.format(page_id)
        self._assert_content_equal('<foo>{}</foo>'.format(content), path)

    def test_page_with_custom_footer_template(self):
        page_id = 'PageWithCustomFooter'
        content = 'hey'
        footer = '<footer>Notes</footer>'
        ref = """
            [Page:{0}]
            PageContent={1}
            [Template:{0}]
            <bar>{{Page[PageContent]}}</bar>
            <# include(footer) #>
            [Template:footer]
            {2}
        """.format(page_id, content, footer)

        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        path = '{}.html'.format(page_id)
        self.assertEqual('<bar>{}</bar>\n{}'.format(content, footer), self.files[path])

    def test_page_with_content_defined_by_include_macro(self):
        page_id = 'MyPage'
        content = 'This is the content of my page.'
        ref = """
            [Page:{0}]
            PageContent=#INCLUDE({0})
            [{0}]
            {1}
        """.format(page_id, content)
        subs = {
            'header': page_id,
            'body_class': page_id,
            'path': '',
            'content': content
        }

        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        self._assert_files_equal('{}.html'.format(page_id), subs)

    def test_page_using_skoolkit_path(self):
        page_id = 'Custom'
        path = 'pages/mypage.html'
        ref = """
            [Page:{0}]
            PageContent=
            [Template:{0}]
            This page is at {{SkoolKit[path]}}.
            [Paths]
            {0}={1}
        """.format(page_id, path)

        self._get_writer(ref=ref, skool='').write_page(page_id)
        exp_content = 'This page is at {}.'.format(path)
        self._assert_content_equal(exp_content, path)

    def test_box_page_with_custom_page_template(self):
        page_id = 'MyCustomBoxPage'
        ref = """
            [Page:{}]
            SectionPrefix=Entry

            [Entry:Entry 1]
            First entry.

            [Template:{}]
            Just the entries!

            <# foreach($entry,entries) #>
            {$entry[title]}:
            - {$entry[contents][0]}
            <# endfor #>
        """.replace('{}', page_id)
        exp_content = """
            Just the entries!

            Entry 1:
            - First entry.
        """

        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        self._assert_content_equal(exp_content, '{}.html'.format(page_id))

    def test_box_page_as_list_items_with_custom_subtemplate(self):
        page_id = 'MyListItemsPage'
        ref = """
            [Page:{}]
            SectionPrefix=Entry
            SectionType=ListItems

            [Entry:entry1:Entry 1]
            Intro.

            Item 1
              Subitem 1A
              Subitem 1B
            Item 2

            [Template:{}-item_list]
            <ul class="level{indent}">
            <# foreach($item,items) #>
            <# if($item[subitems]) #>
            <li>* {$item[text]}
            {$item[subitems]}
            </li>
            <# else #>
            <li>* {$item[text]}</li>
            <# endif #>
            <# endfor #>
            </ul>
        """.replace('{}', page_id)
        exp_content = """
            <ul class="contents">
            <li><a href="#entry1">Entry 1</a></li>
            </ul>
            <div><span id="entry1"></span></div>
            <div class="list-entry list-entry-1">
            <div class="list-entry-title">Entry 1</div>
            <div class="list-entry-desc">Intro.</div>
            <ul class="level">
            <li>* Item 1
            <ul class="level1">
            <li>* Subitem 1A</li>
            <li>* Subitem 1B</li>
            </ul>
            </li>
            <li>* Item 2</li>
            </ul>
            </div>
        """

        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        subs = {
            'title': page_id,
            'header': page_id,
            'path': '',
            'body_class': page_id,
            'content': exp_content
        }
        self._assert_files_equal('{}.html'.format(page_id), subs)

    def test_box_page_as_bullet_points(self):
        page_id = 'Changes'
        ref = """
            [Page:{}]
            SectionPrefix=Change
            SectionType=BulletPoints

            [Change:20170106]
            -

            - There are blank lines...

            - ...between these...

            - ...top-level items

            [Change:20170105]
            -

            - There are no blank lines...
            - ...between these...
            - ...top-level items

            [Change:20170104]
            Many #LINK:Facts(changes).

            - This is
              bullet point 1
              - This is bullet
                point 2
                - This is bullet point
                  3
                - This
                  is bullet
                  point 4
              - This is bullet point 5


            - This is #LINK:Bugs(bullet
              point 6)

            [Change:20170103]
            -

            - This is bullet point 1

              - This is bullet
                point 2
                - This is
                  bullet point 3
            - This is
              bullet point 4

            [Change:20170102]
            Intro on #HTML(two
            lines).

            This item is ignored (no bullet)

            - This is the first item
            [Change:20170101]
            Initial release
        """.format(page_id)
        content = """
            <ul class="contents">
            <li><a href="#20170106">20170106</a></li>
            <li><a href="#20170105">20170105</a></li>
            <li><a href="#20170104">20170104</a></li>
            <li><a href="#20170103">20170103</a></li>
            <li><a href="#20170102">20170102</a></li>
            <li><a href="#20170101">20170101</a></li>
            </ul>
            <div><span id="20170106"></span></div>
            <div class="list-entry list-entry-1">
            <div class="list-entry-title">20170106</div>
            <div class="list-entry-desc"></div>
            <ul class="list-entry">
            <li>There are blank lines...</li>
            <li>...between these...</li>
            <li>...top-level items</li>
            </ul>
            </div>
            <div><span id="20170105"></span></div>
            <div class="list-entry list-entry-2">
            <div class="list-entry-title">20170105</div>
            <div class="list-entry-desc"></div>
            <ul class="list-entry">
            <li>There are no blank lines...</li>
            <li>...between these...</li>
            <li>...top-level items</li>
            </ul>
            </div>
            <div><span id="20170104"></span></div>
            <div class="list-entry list-entry-1">
            <div class="list-entry-title">20170104</div>
            <div class="list-entry-desc">Many <a href="reference/facts.html">changes</a>.</div>
            <ul class="list-entry">
            <li>This is bullet point 1
            <ul class="list-entry1">
            <li>This is bullet point 2
            <ul class="list-entry2">
            <li>This is bullet point 3</li>
            <li>This is bullet point 4</li>
            </ul>
            </li>
            <li>This is bullet point 5</li>
            </ul>
            </li>
            <li>This is <a href="reference/bugs.html">bullet point 6</a></li>
            </ul>
            </div>
            <div><span id="20170103"></span></div>
            <div class="list-entry list-entry-2">
            <div class="list-entry-title">20170103</div>
            <div class="list-entry-desc"></div>
            <ul class="list-entry">
            <li>This is bullet point 1
            <ul class="list-entry1">
            <li>This is bullet point 2
            <ul class="list-entry2">
            <li>This is bullet point 3</li>
            </ul>
            </li>
            </ul>
            </li>
            <li>This is bullet point 4</li>
            </ul>
            </div>
            <div><span id="20170102"></span></div>
            <div class="list-entry list-entry-1">
            <div class="list-entry-title">20170102</div>
            <div class="list-entry-desc">Intro on two lines.</div>
            <ul class="list-entry">
            <li>This is the first item</li>
            </ul>
            </div>
            <div><span id="20170101"></span></div>
            <div class="list-entry list-entry-2">
            <div class="list-entry-title">20170101</div>
            <div class="list-entry-desc">Initial release</div>
            </div>
        """
        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        subs = {
            'title': page_id,
            'header': page_id,
            'path': '',
            'body_class': page_id,
            'content': content
        }
        self._assert_files_equal('{}.html'.format(page_id), subs)

    def test_box_page_with_skool_macros_in_section_name(self):
        page_id = 'MyPageWithSkoolMacrosInTheSectionName'
        ref = """
            [Page:{}]
            SectionPrefix=Entry

            [Entry:entry#EVAL1,2,8:Entry #EVAL1,16,2]
            Hello.
        """.format(page_id)
        exp_content = """
            <ul class="contents">
            <li><a href="#entry00000001">Entry 01</a></li>
            </ul>
            <div><span id="entry00000001"></span></div>
            <div class="box box-1">
            <div class="box-title">Entry 01</div>
            <div class="paragraph">
            Hello.
            </div>
            </div>
        """

        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        subs = {
            'title': page_id,
            'header': page_id,
            'path': '',
            'body_class': page_id,
            'content': exp_content
        }
        self._assert_files_equal('{}.html'.format(page_id), subs)

    def test_box_page_as_list_items_with_skool_macros_in_section_name(self):
        page_id = 'MyListItemsPageWithSkoolMacrosInTheSectionName'
        ref = """
            [Page:{}]
            SectionPrefix=Entry
            SectionType=ListItems

            [Entry:entry#EVAL1,2,8:Entry #EVAL1,16,2]
            -

            An item
        """.format(page_id)
        exp_content = """
            <ul class="contents">
            <li><a href="#entry00000001">Entry 01</a></li>
            </ul>
            <div><span id="entry00000001"></span></div>
            <div class="list-entry list-entry-1">
            <div class="list-entry-title">Entry 01</div>
            <div class="list-entry-desc"></div>
            <ul class="list-entry">
            <li>An item</li>
            </ul>
            </div>
        """

        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        subs = {
            'title': page_id,
            'header': page_id,
            'path': '',
            'body_class': page_id,
            'content': exp_content
        }
        self._assert_files_equal('{}.html'.format(page_id), subs)

    def test_box_page_as_bullet_points_with_skool_macros_in_section_name(self):
        page_id = 'MyBulletPointsPageWithSkoolMacrosInTheSectionName'
        ref = """
            [Page:{}]
            SectionPrefix=Entry
            SectionType=BulletPoints

            [Entry:entry#EVAL1,2,8:Entry #EVAL1,16,2]
            -

            - A bullet point
        """.format(page_id)
        exp_content = """
            <ul class="contents">
            <li><a href="#entry00000001">Entry 01</a></li>
            </ul>
            <div><span id="entry00000001"></span></div>
            <div class="list-entry list-entry-1">
            <div class="list-entry-title">Entry 01</div>
            <div class="list-entry-desc"></div>
            <ul class="list-entry">
            <li>A bullet point</li>
            </ul>
            </div>
        """

        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        subs = {
            'title': page_id,
            'header': page_id,
            'path': '',
            'body_class': page_id,
            'content': exp_content
        }
        self._assert_files_equal('{}.html'.format(page_id), subs)

    def test_page_with_custom_table_template(self):
        page_id = 'JustSomePage'
        ref = """
            [Page:{}]
            PageContent=#INCLUDE({})

            [{}]
            #TABLE
            { =h This | =h That }
            { 1A | 1B }
            { 2A | 2B }
            TABLE#

            [Template:{}-table]
            BEGIN TABLE (
            <# foreach($row,rows) #>
            <row>
            <# foreach($cell,$row[cells]) #>
            <# if({$cell[header]}) #>
            <header>{$cell[contents]}</header>
            <# else #>
            <cell>{$cell[contents]}</cell>
            <# endif #>
            <# endfor #>
            </row>
            <# endfor #>
            ) END TABLE
        """.replace('{}', page_id)
        exp_content = """
            BEGIN TABLE (
            <row>
            <header>This</header>
            <header>That</header>
            </row>
            <row>
            <cell>1A</cell>
            <cell>1B</cell>
            </row>
            <row>
            <cell>2A</cell>
            <cell>2B</cell>
            </row>
            ) END TABLE
        """

        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        subs = {
            'title': page_id,
            'header': page_id,
            'path': '',
            'body_class': page_id,
            'content': exp_content
        }
        self._assert_files_equal('{}.html'.format(page_id), subs)

    def test_bytes_field_in_Asm_template(self):
        skool = """
            @assemble=2
            ; Routine at 32768
            c32768 XOR A    ; One byte
             32769 LD A,0   ; Two bytes
             32771 LD HL,0  ; Three bytes
             32774 LD IX,0  ; Four bytes
             32778 DEFB 0   ; No bytes
             32779 DEFM "a" ; No bytes
             32780 DEFS 1   ; No bytes
             32781 DEFW 0   ; No bytes
        """
        ref = """
            [Template:Asm]
            {entry[title]}
            <# foreach($i,entry[instructions]) #>
            {$i[address]} {$i[bytes]:02X}: {$i[operation]} ; {$i[comment]}
            <# endfor #>
        """
        exp_content = """
            Routine at 32768
            32768 AF: XOR A ; One byte
            32769 3E00: LD A,0 ; Two bytes
            32771 210000: LD HL,0 ; Three bytes
            32774 DD210000: LD IX,0 ; Four bytes
            32778 : DEFB 0 ; No bytes
            32779 : DEFM "a" ; No bytes
            32780 : DEFS 1 ; No bytes
            32781 : DEFW 0 ; No bytes
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_bytes_field_with_separator_in_Asm_template(self):
        skool = """
            @assemble=2
            ; Routine at 32768
            c32768 XOR A   ; One byte
             32769 LD A,0  ; Two bytes
             32771 LD HL,0 ; Three bytes
             32774 LD IX,0 ; Four bytes
        """
        ref = """
            [Template:Asm]
            {entry[title]}
            <# foreach($i,entry[instructions]) #>
            {$i[address]} {$i[bytes]:/03/,}: {$i[operation]} ; {$i[comment]}
            <# endfor #>
        """
        exp_content = """
            Routine at 32768
            32768 175: XOR A ; One byte
            32769 062,000: LD A,0 ; Two bytes
            32771 033,000,000: LD HL,0 ; Three bytes
            32774 221,033,000,000: LD IX,0 ; Four bytes
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_bytes_field_with_specifier_for_entire_string_in_Asm_template(self):
        skool = """
            @assemble=2
            ; Routine at 32768
            c32768 XOR A   ; One byte
             32769 LD A,1  ; Two bytes
             32771 LD HL,2 ; Three bytes
             32774 LD IX,3 ; Four bytes
        """
        ref = """
            [Template:Asm]
            {entry[title]}
            <# foreach($i,entry[instructions]) #>
            {$i[address]} {$i[bytes]:/02X/ />11}: {$i[operation]:7} ; {$i[comment]}
            <# endfor #>
        """
        exp_content = """
            Routine at 32768
            32768          AF: XOR A   ; One byte
            32769       3E 01: LD A,1  ; Two bytes
            32771    21 02 00: LD HL,2 ; Three bytes
            32774 DD 21 03 00: LD IX,3 ; Four bytes
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_custom_index_page_with_custom_subtemplate(self):
        ref = """
            [Template:GameIndex]
            Not much to see here.
            <# include({SkoolKit[include]}) #>

            [Template:GameIndex-home]
            Told you so.
        """
        exp_content = """
            Not much to see here.
            Told you so.
        """
        writer = self._get_writer(ref=ref)
        writer.write_index()
        self._assert_content_equal(exp_content, 'index.html')

    def test_custom_other_code_index_page_with_custom_subtemplate(self):
        code_id = 'Stuff'
        ref = """
            [OtherCode:{}]

            [Template:{}-Index]
            Not much to see here either.
            <# include({SkoolKit[include]}) #>

            [Template:{}-Index-memory_map]
            See?
        """.replace('{}', code_id)
        exp_content = """
            Not much to see here either.
            See?
        """

        main_writer = self._get_writer(ref=ref)
        oc_writer = main_writer.clone(main_writer.parser, code_id)
        oc_writer.write_file = self._mock_write_file
        oc_writer.write_map(code_id + '-Index')
        self._assert_content_equal(exp_content, '{0}/{0}.html'.format(code_id))

    def test_custom_asm_footer_template(self):
        skool = """
            ; Routine at 32768
            c32768 RET ; That's it.
        """
        ref = """
            [Template:Asm]
            {entry[title]}
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]} ; {$i[comment]}
            <# endfor #>
            <# include(footer) #>

            [Template:Asm-footer]
            That was the entry at {entry[location]}.
        """
        exp_content = """
            Routine at 32768
            32768: RET ; That's it.
            That was the entry at 32768.
        """

        writer = self._get_writer(ref=ref, skool=skool, asm_labels=True)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_custom_asm_c_page_with_custom_subtemplates(self):
        skool = """
            ; Routine at 32768
            ;
            ; Do stuff.
            ;
            ; HL 0
            c32768 XOR A  ; #REGa=0
        """
        ref = """
            [Template:Asm-c]
            {entry[title]}
            <# foreach($paragraph,entry[description]) #>
            {$paragraph}
            <# endfor #>
            <# foreach($reg,entry[input_registers]) #>
            {$reg[name]} register: {$reg[description]}
            <# endfor #>
            <# include({SkoolKit[include]}) #>

            [Template:Asm-c-asm]
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]} ; {$i[comment]}
            <# endfor #>

            [Template:Asm-c-reg]
            {reg}
        """
        exp_content = """
            Routine at 32768
            Do stuff.
            HL register: 0
            32768: XOR A ; A=0
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_custom_asm_page_with_custom_subtemplates(self):
        skool = """
            ; Routine at 32768
            ;
            ; Do stuff.
            ;
            ; HL 0
            c32768 XOR A  ; #REGa=0
        """
        ref = """
            [Template:Asm]
            {entry[title]}
            <# foreach($paragraph,entry[description]) #>
            {$paragraph}
            <# endfor #>
            <# foreach($reg,entry[input_registers]) #>
            {$reg[name]} register: {$reg[description]}
            <# endfor #>
            <# include({SkoolKit[include]}) #>

            [Template:Asm-asm]
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]} ; {$i[comment]}
            <# endfor #>

            [Template:Asm-reg]
            {reg}
        """
        exp_content = """
            Routine at 32768
            Do stuff.
            HL register: 0
            32768: XOR A ; A=0
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_custom_other_code_asm_c_page_with_custom_subtemplates(self):
        code_id = 'Stuff'
        other_skool = """
            ; Routine at 32768
            ;
            ; Do stuff.
            ;
            ; HL 0
            c32768 LD B,A  ; #REGb=#REGa
        """
        ref = """
            [OtherCode:{}]

            [Template:{}-Asm-c]
            {entry[title]}
            <# foreach($paragraph,entry[description]) #>
            {$paragraph}
            <# endfor #>
            <# foreach($reg,entry[input_registers]) #>
            {$reg[name]} register: {$reg[description]}
            <# endfor #>
            <# include({SkoolKit[include]}) #>

            [Template:{}-Asm-c-asm]
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]} ; {$i[comment]}
            <# endfor #>

            [Template:{}-Asm-c-reg]
            {reg}
        """.replace('{}', code_id)
        exp_content = """
            Routine at 32768
            Do stuff.
            HL register: 0
            32768: LD B,A ; B=A
        """

        main_writer = self._get_writer(ref=ref, skool=other_skool)
        oc_writer = main_writer.clone(main_writer.parser, code_id)
        oc_writer.write_file = self._mock_write_file
        asm_path = map_path = 'other'
        oc_writer.write_entries(asm_path, map_path)
        self._assert_content_equal(exp_content, '{}/32768.html'.format(asm_path))

    def test_custom_other_code_asm_page_with_custom_subtemplates(self):
        code_id = 'Stuff'
        other_skool = """
            ; Routine at 32768
            ;
            ; Do stuff.
            ;
            ; HL 0
            c32768 LD B,A  ; #REGb=#REGa
        """
        ref = """
            [OtherCode:{}]

            [Template:{}-Asm]
            {entry[title]}
            <# foreach($paragraph,entry[description]) #>
            {$paragraph}
            <# endfor #>
            <# include({SkoolKit[include]}) #>

            [Template:{}-Asm-asm]
            <# foreach($reg,entry[input_registers]) #>
            {$reg[name]} register: {$reg[description]}
            <# endfor #>
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]} ; {$i[comment]}
            <# endfor #>

            [Template:{}-Asm-reg]
            {reg}
        """.replace('{}', code_id)
        exp_content = """
            Routine at 32768
            Do stuff.
            HL register: 0
            32768: LD B,A ; B=A
        """

        main_writer = self._get_writer(ref=ref, skool=other_skool)
        oc_writer = main_writer.clone(main_writer.parser, code_id)
        oc_writer.write_file = self._mock_write_file
        asm_path = map_path = 'other'
        oc_writer.write_entries(asm_path, map_path)
        self._assert_content_equal(exp_content, '{}/32768.html'.format(asm_path))

    def test_custom_asm_single_page_template_with_custom_subtemplate(self):
        skool = """
            ; Routine at 32768
            c32768 XOR A

            ; Data block at 32769
            b32769 DEFB 0
        """
        ref = """
            [Game]
            AsmSinglePage=1

            [Template:AsmSinglePage]
            The entire disassembly.
            <# include({SkoolKit[include]}) #>

            [Template:AsmSinglePage-asm_single_page]
            <# foreach($entry,entries) #>
            {$entry[title]}
            <# foreach($i,$entry[instructions]) #>
            {$i[address]}: {$i[operation]}
            <# endfor #>
            <# endfor #>
        """
        exp_content = """
            The entire disassembly.
            Routine at 32768
            32768: XOR A
            Data block at 32769
            32769: DEFB 0
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm.html')

    def test_custom_other_code_asm_single_page_template_with_custom_subtemplate(self):
        code_id = 'Other'
        other_skool = """
            ; Routine at 49152
            c49152 XOR B

            ; Data block at 49153
            b49153 DEFB 1
        """
        ref = """
            [OtherCode:{}]

            [Game]
            AsmSinglePage=1

            [Template:{}-AsmSinglePage]
            All the entries on one page.
            <# include({SkoolKit[include]}) #>

            [Template:{}-AsmSinglePage-asm_single_page]
            <# foreach($entry,entries) #>
            {$entry[title]}
            <# foreach($i,$entry[instructions]) #>
            {$i[address]}: {$i[operation]}
            <# endfor #>
            <# endfor #>
        """.replace('{}', code_id)
        exp_content = """
            All the entries on one page.
            Routine at 49152
            49152: XOR B
            Data block at 49153
            49153: DEFB 1
        """

        main_writer = self._get_writer(ref=ref, skool=other_skool)
        oc_writer = main_writer.clone(main_writer.parser, code_id)
        oc_writer.write_file = self._mock_write_file
        asm_path = map_path = 'other'
        oc_writer.write_entries(asm_path, map_path)
        self._assert_content_equal(exp_content, '{}/asm.html'.format(code_id))

    def test_custom_asm_b_page_with_custom_subtemplates(self):
        skool = """
            ; Data block at 32768
            b32768 DEFB 0
        """
        ref = """
            [Template:Asm-b]
            {entry[title]}
            <# include({SkoolKit[include]}) #>
            <# include(footer) #>

            [Template:Asm-b-asm]
            <# foreach($i,entry[instructions]) #>
            {$i[anchor]}: {$i[operation]}
            <# endfor #>

            [Template:Asm-b-footer]
            The end.
        """
        exp_content = """
            Data block at 32768
            32768: DEFB 0
            The end.
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_custom_other_code_asm_b_page_with_custom_subtemplates(self):
        code_id = 'Stuff'
        other_skool = """
            ; Data block at 32768
            ;
            ; #LINK:Bugs(bug)
            b32768 DEFB 0
        """
        ref = """
            [OtherCode:{}]

            [Template:{}-Asm-b]
            {entry[title]}
            <# foreach($paragraph,entry[description]) #>
            {$paragraph}
            <# endfor #>
            <# include({SkoolKit[include]}) #>

            [Template:{}-Asm-b-asm]
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]}
            <# endfor #>

            [Template:{}-Asm-b-link]
            Link: {href} ({link_text})
        """.replace('{}', code_id)
        exp_content = """
            Data block at 32768
            Link: ../reference/bugs.html (bug)
            32768: DEFB 0
        """

        main_writer = self._get_writer(ref=ref, skool=other_skool)
        oc_writer = main_writer.clone(main_writer.parser, code_id)
        oc_writer.write_file = self._mock_write_file
        asm_path = map_path = 'other'
        oc_writer.write_entries(asm_path, map_path)
        self._assert_content_equal(exp_content, '{}/32768.html'.format(asm_path))

    def test_custom_asm_g_page_with_custom_subtemplates(self):
        skool = """
            ; Game status buffer entry at 32768
            g32768 DEFB 0
        """
        ref = """
            [Template:Asm-g]
            {entry[title]}
            <# include({SkoolKit[include]}) #>
            <# include(footer) #>

            [Template:Asm-g-asm]
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]}
            <# endfor #>

            [Template:Asm-g-footer]
            (done)
        """
        exp_content = """
            Game status buffer entry at 32768
            32768: DEFB 0
            (done)
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_custom_other_code_asm_g_page_with_custom_subtemplates(self):
        code_id = 'Stuff'
        other_skool = """
            ; Game status buffer entry at 32768
            ;
            ; #LIST { Thing 1 } { Thing 2 } LIST#
            g32768 DEFB 0
        """
        ref = """
            [OtherCode:{}]

            [Template:{}-Asm-g]
            {entry[title]}
            <# include({SkoolKit[include]}) #>
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]}
            <# endfor #>

            [Template:{}-Asm-g-asm]
            <# foreach($paragraph,entry[description]) #>
            {$paragraph}
            <# endfor #>

            [Template:{}-Asm-g-list]
            Items:
            <# foreach($item,items) #>
            + {$item}
            <# endfor #>
        """.replace('{}', code_id)
        exp_content = """
            Game status buffer entry at 32768
            Items:
            + Thing 1
            + Thing 2
            32768: DEFB 0
        """

        main_writer = self._get_writer(ref=ref, skool=other_skool)
        oc_writer = main_writer.clone(main_writer.parser, code_id)
        oc_writer.write_file = self._mock_write_file
        asm_path = map_path = 'other'
        oc_writer.write_entries(asm_path, map_path)
        self._assert_content_equal(exp_content, '{}/32768.html'.format(asm_path))

    def test_custom_asm_s_page_with_custom_subtemplates(self):
        skool = """
            ; Space
            s32768 DEFS 10
        """
        ref = """
            [Template:Asm-s]
            {entry[title]}
            <# include({SkoolKit[include]}) #>
            <# include(footer) #>

            [Template:Asm-s-asm]
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]}
            <# endfor #>

            [Template:Asm-s-footer]
            -- That was the entry at {entry[address]} --
        """
        exp_content = """
            Space
            32768: DEFS 10
            -- That was the entry at 32768 --
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_custom_other_code_asm_s_page_with_custom_subtemplates(self):
        code_id = 'Stuff'
        other_skool = """
            ; Space
            s32768 DEFS 10
        """
        ref = """
            [OtherCode:{}]

            [Template:{}-Asm-s]
            {entry[title]}
            <# include({SkoolKit[include]}) #>
            <# include(footer) #>

            [Template:{}-Asm-s-asm]
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]}
            <# endfor #>

            [Template:{}-Asm-s-footer]
            Over and out.
        """.replace('{}', code_id)
        exp_content = """
            Space
            32768: DEFS 10
            Over and out.
        """

        main_writer = self._get_writer(ref=ref, skool=other_skool)
        oc_writer = main_writer.clone(main_writer.parser, code_id)
        oc_writer.write_file = self._mock_write_file
        asm_path = map_path = 'other'
        oc_writer.write_entries(asm_path, map_path)
        self._assert_content_equal(exp_content, '{}/32768.html'.format(asm_path))

    def test_custom_asm_t_page_with_custom_subtemplates(self):
        skool = """
            ; Message at 32768
            t32768 DEFM "Hello"
        """
        ref = """
            [Game]
            JavaScript=foo.js

            [Template:Asm-t]
            {entry[title]}
            <# include({SkoolKit[include]}) #>
            <# include(footer) #>

            [Template:Asm-t-asm]
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]}
            <# endfor #>

            [Template:Asm-t-footer]
            -- That was the entry at {entry[address]} --
        """
        exp_content = """
            Message at 32768
            32768: DEFM "Hello"
            -- That was the entry at 32768 --
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_custom_other_code_asm_t_page_with_custom_subtemplates(self):
        code_id = 'Stuff'
        other_skool = """
            ; Message at 32768
            t32768 DEFM "Hello"
        """
        ref = """
            [OtherCode:{}]

            [Template:{}-Asm-t]
            {entry[title]}
            <# include({SkoolKit[include]}) #>
            <# include(footer) #>

            [Template:{}-Asm-t-asm]
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]}
            <# endfor #>

            [Template:{}-Asm-t-footer]
            Done.
        """.replace('{}', code_id)
        exp_content = """
            Message at 32768
            32768: DEFM "Hello"
            Done.
        """

        main_writer = self._get_writer(ref=ref, skool=other_skool)
        oc_writer = main_writer.clone(main_writer.parser, code_id)
        oc_writer.write_file = self._mock_write_file
        asm_path = map_path = 'other'
        oc_writer.write_entries(asm_path, map_path)
        self._assert_content_equal(exp_content, '{}/32768.html'.format(asm_path))

    def test_custom_asm_u_page_with_custom_subtemplates(self):
        skool = """
            ; Unused
            ;
            ; #UDG32768
            u32768 DEFS 100
        """
        ref = """
            [Template:Asm-u]
            {entry[title]}
            <# foreach($paragraph,entry[description]) #>
            {$paragraph}
            <# endfor #>
            <# include({SkoolKit[include]}) #>

            [Template:Asm-u-asm]
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]}
            <# endfor #>

            [Template:Asm-u-img]
            Image: {src}
        """
        exp_content = """
            Unused
            Image: ../images/udgs/udg32768_56x4.png
            32768: DEFS 100
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_custom_other_code_asm_u_page_with_custom_subtemplates(self):
        code_id = 'Stuff'
        other_skool = """
            ; Unused
            u32768 DEFS 100
        """
        ref = """
            [OtherCode:{}]

            [Template:{}-Asm-u]
            {entry[title]}
            <# include({SkoolKit[include]}) #>
            <# include(footer) #>

            [Template:{}-Asm-u-asm]
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]}
            <# endfor #>

            [Template:{}-Asm-u-footer]
            Bye.
        """.replace('{}', code_id)
        exp_content = """
            Unused
            32768: DEFS 100
            Bye.
        """

        main_writer = self._get_writer(ref=ref, skool=other_skool)
        oc_writer = main_writer.clone(main_writer.parser, code_id)
        oc_writer.write_file = self._mock_write_file
        asm_path = map_path = 'other'
        oc_writer.write_entries(asm_path, map_path)
        self._assert_content_equal(exp_content, '{}/32768.html'.format(asm_path))

    def test_custom_asm_w_page_with_custom_subtemplates(self):
        skool = """
            ; A word
            w32768 DEFW 1759
        """
        ref = """
            [Template:Asm-w]
            {entry[title]}
            <# include({SkoolKit[include]}) #>
            <# include(footer) #>

            [Template:Asm-w-asm]
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]}
            <# endfor #>

            [Template:Asm-w-footer]
            The end.
        """
        exp_content = """
            A word
            32768: DEFW 1759
            The end.
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_custom_other_code_asm_w_page_with_custom_subtemplates(self):
        code_id = 'Stuff'
        other_skool = """
            ; A word
            w32768 DEFW 1759
        """
        ref = """
            [OtherCode:{}]

            [Template:{}-Asm-w]
            {entry[title]}
            <# include({SkoolKit[include]}) #>
            <# include(footer) #>

            [Template:{}-Asm-w-asm]
            <# foreach($i,entry[instructions]) #>
            {$i[address]}: {$i[operation]}
            <# endfor #>

            [Template:{}-Asm-w-footer]
            End.
        """.replace('{}', code_id)
        exp_content = """
            A word
            32768: DEFW 1759
            End.
        """

        main_writer = self._get_writer(ref=ref, skool=other_skool)
        oc_writer = main_writer.clone(main_writer.parser, code_id)
        oc_writer.write_file = self._mock_write_file
        asm_path = map_path = 'other'
        oc_writer.write_entries(asm_path, map_path)
        self._assert_content_equal(exp_content, '{}/32768.html'.format(asm_path))

    def test_custom_map_page_with_custom_subtemplate(self):
        skool = """
            ; Routine at 49152
            ;
            ; Reset HL.
            c49152 LD HL,0
        """
        ref = """
            [MemoryMap:MemoryMap]
            EntryDescriptions=1

            [Template:MemoryMap]
            <# foreach($entry,entries) #>
            {$entry[address]}: {$entry[title]}
            <# include({SkoolKit[include]}) #>
            <# endfor #>

            [Template:MemoryMap-memory_map]
            <# foreach($paragraph,$entry[description]) #>
            {$paragraph}
            <# endfor #>
        """
        exp_content = """
            49152: Routine at 49152
            Reset HL.
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_map('MemoryMap')
        self._assert_content_equal(exp_content, 'maps/all.html')

    def test_custom_page_template_with_custom_subtemplate(self):
        page_id = 'Stuff'
        ref = """
            [Page:{}]
            PageContent=Here's some stuff.

            [Template:{}]
            Welcome to the Stuff page.
            <# include({SkoolKit[include]}) #>

            [Template:{}-page]
            The content follows.
            - {Page[PageContent]}
        """.replace('{}', page_id)
        exp_content = """
            Welcome to the Stuff page.
            The content follows.
            - Here's some stuff.
        """

        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        self._assert_content_equal(exp_content, '{}.html'.format(page_id))

    def test_custom_box_page_template_with_custom_box_entries_subtemplate(self):
        page_id = 'Things'
        ref = """
            [Page:{}]
            SectionPrefix=Thing

            [Thing:Thing1]
            First thing.

            [Thing:Thing2]
            Second thing.

            [Template:{}]
            <# foreach($entry,entries) #>
            <# include({SkoolKit[include]}) #>
            <# endfor #>

            [Template:{}-box_entries]
            * {$entry[contents][0]}
        """.replace('{}', page_id)
        exp_content = """
            * First thing.
            * Second thing.
        """

        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        self._assert_content_equal(exp_content, '{}.html'.format(page_id))

    def test_custom_box_page_template_with_custom_box_list_entries_subtemplate(self):
        page_id = 'Things'
        ref = """
            [Page:{}]
            SectionPrefix=Thing
            SectionType=ListItems

            [Thing:Thing1]
            First intro.

            [Thing:Thing2]
            Second intro.

            [Template:{}]
            <# foreach($entry,entries) #>
            <# include({SkoolKit[include]}) #>
            <# endfor #>

            [Template:{}-box_list_entries]
            * {$entry[intro]}
        """.replace('{}', page_id)
        exp_content = """
            * First intro.
            * Second intro.
        """

        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        self._assert_content_equal(exp_content, '{}.html'.format(page_id))

    @patch.object(components, 'SK_CONFIG', None)
    def test_custom_html_template_formatter(self):
        custom_formatter = """
            from skoolkit.skoolhtml import TemplateFormatter

            class CustomFormatter(TemplateFormatter):
                def format_template(self, page_id, name, fields):
                    return 'Hello {Page[PageContent]}'.format(**fields)
        """
        self.write_component_config('HtmlTemplateFormatter', '*.CustomFormatter', custom_formatter)
        page_id = 'Things'
        ref = """
            [Page:{}]
            PageContent=there
        """.format(page_id)
        exp_content = "Hello there"

        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        self._assert_content_equal(exp_content, '{}.html'.format(page_id))

    @patch.object(components, 'SK_CONFIG', None)
    def test_html_template_formatter_api(self):
        custom_formatter = """
            class CustomFormatter:
                def __init__(self, templates):
                    assert templates['Stuff'] == 'bar'

                def format_template(self, page_id, name, fields):
                    assert page_id == 'Stuff'
                    assert name == 'Layout'
                    assert fields['Page'] == {'PageContent': 'foo'}
                    return "baz"
        """
        self.write_component_config('HtmlTemplateFormatter', '*.CustomFormatter', custom_formatter)
        page_id = 'Stuff'
        ref = """
            [Page:{0}]
            PageContent=foo

            [Template:{0}]
            bar
        """.format(page_id)
        exp_content = "baz"

        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        self._assert_content_equal(exp_content, '{}.html'.format(page_id))
