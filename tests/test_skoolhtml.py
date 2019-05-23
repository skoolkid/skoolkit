import html
from os.path import basename, isfile
from posixpath import join
from textwrap import dedent
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase, StringIO
from macrotest import CommonSkoolMacroTest, nest_macros
from skoolkit import BASE_10, BASE_16, VERSION, SkoolKitError, SkoolParsingError, defaults, skoolhtml
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
    'Template_asm_instruction': defaults.get_section('Template:asm_instruction'),
    'Template_img': defaults.get_section('Template:img'),
    'Template_link': defaults.get_section('Template:link'),
    'Template_list': defaults.get_section('Template:list'),
    'Template_list_item': defaults.get_section('Template:list_item'),
    'Template_paragraph': defaults.get_section('Template:paragraph'),
    'Template_reg': defaults.get_section('Template:reg'),
    'Template_table': defaults.get_section('Template:table'),
    'Template_table_cell': defaults.get_section('Template:table_cell'),
    'Template_table_header_cell': defaults.get_section('Template:table_header_cell'),
    'Template_table_row': defaults.get_section('Template:table_row'),
}

MINIMAL_REF_FILE = """
[Game]
AddressAnchor={{address}}
Created=
LinkInternalOperands=0
LinkOperands=CALL,DEFW,DJNZ,JP,JR
[Paths]
CodePath={ASMDIR}
CodeFiles={{address}}.html
UDGFilename=udg{{addr}}_{{attr}}x{{scale}}
{REF_SECTIONS[Template_asm_instruction]}
""".format(**locals())

METHOD_MINIMAL_REF_FILE = """
[Game]
AddressAnchor={{address}}
Created=
LinkInternalOperands=0
LinkOperands=CALL,DEFW,DJNZ,JP,JR
[Paths]
CodePath={ASMDIR}
ImagePath={IMAGEDIR}
ScreenshotImagePath={SCRDIR}
UDGImagePath={UDGDIR}
UDGFilename=udg{{addr}}_{{attr}}x{{scale}}
CodeFiles={{address}}.html
{REF_SECTIONS[Template_asm_instruction]}
{REF_SECTIONS[Template_img]}
""".format(**locals())

SKOOL_MACRO_MINIMAL_REF_FILE = """
[Game]
AddressAnchor={{address}}
Created=
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
{REF_SECTIONS[Template_asm_instruction]}
{REF_SECTIONS[Template_img]}
{REF_SECTIONS[Template_link]}
{REF_SECTIONS[Template_list]}
{REF_SECTIONS[Template_list_item]}
{REF_SECTIONS[Template_paragraph]}
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
<div class="created">Created using <a href="https://skoolkit.ca">SkoolKit</a> {}.</div>
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
    def __init__(self, snapshot, base, case):
        self.snapshot = snapshot
        self.entries = {}
        self.memory_map = ()
        self.base = base
        self.case = case
        self.skoolfile = ''
        self.fields = {'asm': 0, 'base': base, 'case': case, 'fix': 0, 'html': 1}

    def get_entry(self, address):
        return self.entries.get(address)

    def make_replacements(self, item):
        pass

class MockFileInfo:
    def __init__(self):
        self.fname = None
        self.mode = None

    def open_file(self, *names, mode='w'):
        self.fname = join(*names)
        self.mode = mode
        return StringIO()

    def add_image(self, image_path):
        return

    def need_image(self, image_path):
        return True

class TestImageWriter(ImageWriter):
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

    def _get_writer(self, ref=None, snapshot=(), case=0, base=0, skool=None,
                    create_labels=False, asm_labels=False, variables=(),
                    mock_file_info=False, mock_write_file=True, warn=False):
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
        self.odir = self.make_directory()
        if mock_file_info:
            file_info = MockFileInfo()
        else:
            file_info = FileInfo(self.odir, GAMEDIR, False)
        patch.object(skoolhtml, 'ImageWriter', TestImageWriter).start()
        self.addCleanup(patch.stopall)
        writer = HtmlWriter(skool_parser, ref_parser, file_info)
        if mock_write_file:
            writer.write_file = self._mock_write_file
        writer.skoolkit['page_id'] = 'None'
        return writer

    def _check_image(self, writer, udg_array, scale=2, mask=0, x=0, y=0, width=None, height=None, path=None):
        self.assertEqual(writer.file_info.fname, path)
        if width is None:
            width = 8 * len(udg_array[0]) * scale
        if height is None:
            height = 8 * len(udg_array) * scale
        image_writer = writer.image_writer
        self.assertEqual(image_writer.scale, scale)
        self.assertEqual(image_writer.mask, mask)
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
        for img_format in ('png', 'gif'):
            fname = 'test.' + img_format
            with self.subTest(img_format=img_format):
                writer.handle_image(frame, fname)
                self.assertEqual(file_info.fname, '{}/{}'.format(IMAGEDIR, fname))
                self.assertEqual(file_info.mode, 'wb')
                self.assertEqual(image_writer.udg_array, udgs)
                self.assertEqual(image_writer.img_format, img_format)
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
        for img_format in ('png', 'gif'):
            fname = 'test_animated.' + img_format
            with self.subTest(img_format=img_format):
                writer.handle_image(frames, fname)
                self.assertEqual(file_info.fname, '{}/{}'.format(IMAGEDIR, fname))
                self.assertEqual(file_info.mode, 'wb')
                self.assertEqual(image_writer.frames, frames)
                self.assertEqual(image_writer.img_format, img_format)

    def test_handle_image_with_paths(self):
        writer = self._get_writer(mock_file_info=True)
        file_info = writer.file_info
        udgs = [[Udg(0, (0,) * 8)]]
        frame = Frame(udgs)
        def_img_format = writer.default_image_format

        writer.handle_image(frame, 'img')
        self.assertEqual(file_info.fname, '{}/img.{}'.format(writer.paths['ImagePath'], def_img_format))

        writer.handle_image(frame, '/pics/foo.png')
        self.assertEqual(file_info.fname, 'pics/foo.png')

        path_id = 'ScreenshotImagePath'
        writer.handle_image(frame, 'img.gif', path_id=path_id)
        self.assertEqual(file_info.fname, '{}/img.gif'.format(writer.paths[path_id]))

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
        self.assertEqual(file_info.fname, '{}/img.gif'.format(udg_path))

        # One frame, flashing, fully cropped
        udgs = [[Udg(129, (0,) * 8), Udg(0, (0,) * 8)]]
        writer.handle_image(Frame(udgs, 1, 0, 8), 'img')
        self.assertEqual(file_info.fname, '{}/img.png'.format(udg_path))

        # One frame, flashing, partly cropped
        udgs = [[Udg(129, (0,) * 8), Udg(0, (0,) * 8)]]
        writer.handle_image(Frame(udgs, 1, 0, 4), 'img')
        self.assertEqual(file_info.fname, '{}/img.gif'.format(udg_path))

        # One frame, FLASH bit set, completely transparent (no flash rect)
        udgs = [[Udg(129, (0,) * 8, (255,) * 8)]]
        writer.handle_image(Frame(udgs, 1, 1), 'img')
        self.assertEqual(file_info.fname, '{}/img.png'.format(udg_path))

        # Two frames
        udgs = [[Udg(0, (0,) * 8)]]
        writer.handle_image([Frame(udgs)] * 2, 'img')
        self.assertEqual(file_info.fname, '{}/img.gif'.format(udg_path))

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

    def test_format_template_unused_default(self):
        ref = """
            [Template:foo]
            {bar}
            [Template:default-foo]
            <<{bar}>>
        """
        writer = self._get_writer(ref=ref)
        output = writer.format_template('foo', {'bar': 'baz'}, 'default-foo')
        self.assertEqual(output, 'baz')

    def test_format_template_uses_default(self):
        writer = self._get_writer(ref='[Template:default-foo]\n{bar}')
        output = writer.format_template('foo', {'bar': 'baz'}, 'default-foo')
        self.assertEqual(output, 'baz')

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

    def test_format_template_nonexistent_default(self):
        writer = self._get_writer()
        with self.assertRaisesRegex(SkoolKitError, "^'default' template does not exist$"):
            writer.format_template('non-existent', {}, 'default')

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

    def _test_call_no_retval(self, *args):
        return

    def _test_call_no_args(self, cwd):
        return 'OK'

    def _unsupported_macro(self, *args):
        raise UnsupportedMacroError()

    def test_macro_chr(self):
        writer = self._get_writer()

        self.assertEqual(writer.expand('#CHR169'), '&#169;')
        self.assertEqual(writer.expand('#CHR(163)1984'), '&#163;1984')
        self.assertEqual(writer.expand('#CHR65+3'), '&#65;+3')
        self.assertEqual(writer.expand('#CHR65*2'), '&#65;*2')
        self.assertEqual(writer.expand('#CHR65-9'), '&#65;-9')
        self.assertEqual(writer.expand('#CHR65/5'), '&#65;/5')
        self.assertEqual(writer.expand('#CHR(65+3*2-9/3)'), '&#68;')
        self.assertEqual(writer.expand('#CHR($42 + 3 * 2 - (2 + 7) / 3)'), '&#69;')
        self.assertEqual(writer.expand(nest_macros('#CHR({})', 70)), '&#70;')

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
        x, y, w, h = 1, 2, 3, 4
        values = (font_addr, len(chars), attr, scale, x, y, w, h, fname)
        macro = '#FONT{0},{1},{2},{3}{{{4},{5},{6},{7}}}({8})'.format(*values)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(4, char) for char in chars]]
        self._check_image(writer, udg_array, scale, False, x, y, w, h, exp_image_path)

        # Keyword arguments
        macro = '#FONTscale={3},chars={1},addr={0},attr={2}{{x={4},y={5},width={6},height={7}}}({8})'.format(*values)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, udg_array, scale, False, x, y, w, h, exp_image_path)

        # Keyword arguments, arithmetic expressions
        values = ('128*256', '1+(3+1)/2', '(1 + 1) * 2', '7&2', '2*2-3', '(8 + 8) / 8', '6>>1', '2<<1', fname)
        macro = '#FONT({0}, scale={3}, chars = {1}, attr={2}){{x={4}, y = {5}, width={6},height ={7}}}({8})'.format(*values)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, udg_array, scale, False, x, y, w, h, exp_image_path)

        # Nested macros
        fname = 'nested'
        exp_image_path = '{}/{}.png'.format(FONTDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        x = 5
        output = writer.expand(nest_macros('#FONT({},1){{x={}}}({})', font_addr, x, fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self._check_image(writer, [[Udg(56, char1)]], 2, x=x, width=11, path=exp_image_path)

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

    def test_macro_font_uses_default_animation_format(self):
        writer = self._get_writer(snapshot=[0] * 8, mock_file_info=True)

        # No flash
        fname = 'font_no_flash'
        exp_image_path = '{}/{}.png'.format(FONTDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#FONT0,1,56({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        # Flash: different INK and PAPER
        fname = 'font_flash1'
        exp_image_path = '{}/{}.gif'.format(FONTDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#FONT0,1,184({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        # Flash: same INK and PAPER
        fname = 'font_flash2'
        exp_image_path = '{}/{}.png'.format(FONTDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#FONT0,1,128({})'.format(fname), ASMDIR)
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
        main_writer = self._get_writer(ref=ref, skool='', variables=('foo=1', 'bar=2'))
        writer = main_writer.clone(main_writer.parser, 'other')

        self.assertEqual(writer.expand('#IF({asm})(FAIL,PASS)'), 'PASS')
        self.assertEqual(writer.expand('#IF({base})(FAIL,PASS)'), 'PASS')
        self.assertEqual(writer.expand('#IF({case})(FAIL,PASS)'), 'PASS')
        self.assertEqual(writer.expand('#IF({fix})(FAIL,PASS)'), 'PASS')
        self.assertEqual(writer.expand('#IF({html})(PASS,FAIL)'), 'PASS')
        self.assertEqual(writer.expand('#IF({vars[foo]}==1)(PASS,FAIL)'), 'PASS')
        self.assertEqual(writer.expand('#IF({vars[bar]}==2)(PASS,FAIL)'), 'PASS')
        self.assertEqual(writer.expand('#IF({vars[baz]}==0)(PASS,FAIL)'), 'PASS')

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
        self.assertEqual(output, '<ul class="">\n\n</ul>')

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
        main_writer = self._get_writer(ref=ref, skool='', variables=('foo=1', 'bar=2'))
        writer = main_writer.clone(main_writer.parser, 'other')

        self.assertEqual(writer.expand('#MAP({asm})(FAIL,0:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({base})(FAIL,0:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({case})(FAIL,0:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({fix})(FAIL,0:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({html})(FAIL,1:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({vars[foo]})(FAIL,1:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({vars[bar]})(FAIL,2:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({vars[baz]})(FAIL,0:PASS)'), 'PASS')

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

        # Non-existent reference
        prefix = ERROR_PREFIX.format('R')
        self._assert_error(writer, '#R$ABCD', 'Could not find instruction at $ABCD', prefix)

        # Explicit code ID and non-existent reference
        self._assert_error(writer, '#R$ABCD@main', 'Could not find instruction at $ABCD', prefix)

    def test_macro_r_asm_single_page(self):
        ref = '[Game]\nAsmSinglePageTemplate=AsmAllInOne'
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
            AsmSinglePageTemplate=AsmAllInOne
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
        x, y, w, h = 1, 2, 5, 6
        macro = '#SCR,0,0,1,1{{{},{},{},{}}}({})'.format(x, y, w, h, fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(attr, data)]]
        self._check_image(writer, udg_array, scale, False, x, y, w, h, exp_image_path)

        fname = 'scr4'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        scale = 3
        x, y, w, h = 0, 0, 1, 1
        df = 0
        af = 32768
        data = snapshot[df:df + 2048:256] = [170] * 8
        attr = snapshot[af] = 56
        values = {'scale': scale, 'x': x, 'y': y, 'w': w, 'h': h, 'df': df, 'af': af, 'fname': fname}
        macro = '#SCRx={x},h={h},af={af},scale={scale},y={y},df={df},w={w}({fname})'.format(**values)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(attr, data)]]
        self._check_image(writer, udg_array, scale, path=exp_image_path)

        # Arithmetic expressions
        fname = 'scr5'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        scale = 3
        df = 0
        af = 6144
        data = snapshot[df:df + 2048:256] = [85] * 8
        attr = snapshot[af] = 57
        crop = (1, 2, 17, 14)
        crop_spec = '{5-4, 2 * 1, width=(2+2)*4+1, height = 7*2}'
        macro = '#SCR(2+1, 0*1, 5-5, (1 + 1) / 2, 1**1, 1^1, 24*256){}({})'.format(crop_spec, fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(attr, data)]]
        self._check_image(writer, udg_array, scale, 0, *crop, path=exp_image_path)

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

    def test_macro_scr_uses_default_animation_format(self):
        snapshot = [0] * 2050
        af = 2048
        writer = self._get_writer(snapshot=snapshot, mock_file_info=True)

        # No flash
        fname = 'scr_no_flash'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        snapshot[af] = 56
        output = writer.expand('#SCRw=1,h=1,df=0,af={}({})'.format(af, fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        # Flash: different INK and PAPER
        fname = 'scr_flash1'
        exp_image_path = '{}/{}.gif'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        snapshot[af] = 184
        output = writer.expand('#SCRw=1,h=1,df=0,af={}({})'.format(af, fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        # Flash: same INK and PAPER
        fname = 'scr_flash2'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        snapshot[af] = 128
        output = writer.expand('#SCRw=1,h=1,df=0,af={}({})'.format(af, fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        # Flash: cropped
        fname = 'scr_flash3'
        exp_image_path = '{}/{}.png'.format(SCRDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        snapshot[af:af + 2] = [184, 56]
        output = writer.expand('#SCRw=2,h=1,df=0,af={}{{8}}({})'.format(af, fname), ASMDIR)
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
        self.assertEqual(output, '<table class="">\n\n</table>')

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
        mask_addr = 32776
        x, y, w, h = 2, 1, 3, 4
        udg_data = [136] * 8
        udg_mask = [255] * 8
        snapshot[udg_addr:udg_addr + 8 * step:step] = udg_data
        snapshot[mask_addr:mask_addr + 8 * step:step] = udg_mask
        macro = '#UDG{0},{1},{2},{3},{4}:{5},{6}{{{7},{8},{9},{10}}}({11})'.format(udg_addr, attr, scale, step, inc, mask_addr, step, x, y, w, h, fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(attr, udg_data, udg_mask)]]
        self._check_image(writer, udg_array, scale, 1, x, y, w, h, exp_image_path)

        fname = 'test_udg3'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
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
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(attr, udg_data, udg_mask)]]
        self._check_image(writer, udg_array, scale, mask, x, y, width, height, exp_image_path)

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
        self._check_image(writer, udg_array, scale, mask, x, y, w, h, exp_image_path)

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

    def test_macro_udg_uses_default_animation_format(self):
        writer = self._get_writer(snapshot=[0] * 8, mock_file_info=True)

        # No flash
        fname = 'udg_no_flash'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDG0,56({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        # Flash: different INK and PAPER
        fname = 'udg_flash1'
        exp_image_path = '{}/{}.gif'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDG0,184({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        # Flash: same INK and PAPER
        fname = 'udg_flash2'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDG0,128({})'.format(fname), ASMDIR)
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
        x, y, w, h = 4, 6, 8, 5
        udg_data = [195] * 8
        udg_mask = [255] * 8
        snapshot[udg_addr:udg_addr + 8 * step:step] = udg_data
        snapshot[mask_addr:mask_addr + 8 * step:step] = udg_mask
        macro = '#UDGARRAY{},{},{},{},{};{}x4:{}x4{{{},{},{},{}}}({})'.format(width, attr, scale, step, inc, udg_addr, mask_addr, x, y, w, h, fname)
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(attr, udg_data, udg_mask)] * width] * 2
        self._check_image(writer, udg_array, scale, True, x, y, w, h, exp_image_path)

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
        self._check_image(writer, [[udg]], 2, False, 0, 0, 16, 16, exp_image_path)

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
        self._check_image(writer, [[udg]], 2, False, 0, 0, 16, 16, exp_image_path)

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
        x, y, w, h = 4, 6, 8, 5
        udg_data = [195] * 8
        udg_mask = [255] * 8
        snapshot[udg_addr:udg_addr + 8 * step:step] = udg_data
        snapshot[mask_addr:mask_addr + 8 * step:step] = udg_mask
        params = 'attr={attr},step={step},inc={inc},mask={mask},scale={scale}'
        udg_spec = ';{udg_addr}x4,step={step}'
        mask_spec = ':{mask_addr}x4,step={step}'
        crop = '{{x={x},y={y},width={w},height={h}}}'
        macro = ('#UDGARRAY{width},' + params + udg_spec + mask_spec + crop + '({fname})').format(**locals())
        output = writer.expand(macro, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        udg_array = [[Udg(attr, udg_data, udg_mask)] * width] * 2
        self._check_image(writer, udg_array, scale, mask, x, y, w, h, exp_image_path)

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
        self._check_image(writer, [[udg1, udg2, udg3]], scale, mask, x, y, w, h, exp_image_path)

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
        self._check_image(writer, [[udg]], scale, mask, x, width=15, path=exp_image_path)

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
        exp_image_path = '{}/{}.gif'.format(UDGDIR, fname)
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
        macro2 = '#UDGARRAY1;{},{}(bar*)'.format(udg2_addr, udg2.attr)
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
        exp_image_path = '{}/{}.gif'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        delay1 = 93
        macro4 = '#UDGARRAY*foo,{};bar;qux,(delay=5+8*2-12/3)({})'.format(delay1, fname)
        output = writer.expand(macro4, ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        frame1 = Frame([[udg1]], 2, delay=delay1)
        frame2 = Frame([[udg2]], 2, delay=delay1)
        frame3 = Frame([[udg3]], 2, delay=17)
        frames = [frame1, frame2, frame3]
        self._check_animated_image(writer.image_writer, frames)

    def test_macro_udgarray_frames_uses_default_animation_format(self):
        writer = self._get_writer(snapshot=[0] * 8, mock_file_info=True)

        writer.expand('#UDG0,1(*frame1)')
        writer.expand('#UDG0,2(*frame2)')

        # One frame
        fname = 'one_frame'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY*frame1({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

        # Two frames
        fname = 'two_frames'
        exp_image_path = '{}/{}.gif'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        output = writer.expand('#UDGARRAY*frame1;frame2({})'.format(fname), ASMDIR)
        self._assert_img_equals(output, fname, exp_src)
        self.assertEqual(writer.file_info.fname, exp_image_path)

    def test_macro_udgarray_frames_invalid(self):
        writer, prefix = CommonSkoolMacroTest.test_macro_udgarray_frames_invalid(self)
        self._assert_error(writer, '#UDGARRAY*foo(bar)', 'No such frame: "foo"', prefix)

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
        exp_image_path = '{}/{}.gif'.format(UDGDIR, fname)
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
        self.assertEqual(output, '<table class="">\n\n</table>')

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
        subs.setdefault('name', basename(self.skoolfile)[:-6])
        subs.setdefault('path', '../')
        subs.setdefault('map', '{}maps/all.html'.format(subs['path']))
        subs.setdefault('script', '<script type="text/javascript" src="{}"></script>'.format(js) if js else '')
        subs.setdefault('title', subs['header'])
        subs.setdefault('logo', subs['name'])
        footer = subs.get('footer', BARE_FOOTER)
        prev_up_next_lines = []
        if 'up' in subs:
            subs['prev_link'] = '<span class="prev-0">Prev: <a href=""></a></span>'
            subs['up_link'] = 'Up: <a href="{map}#{up}">Map</a>'.format(**subs)
            subs['next_link'] = '<span class="next-0">Next: <a href=""></a></span>'
            if 'prev' in subs:
                if 'prev_text' in subs:
                    subs['prev_link'] = '<span class="prev-1">Prev: <a href="{}.html">{}</a></span>'.format(subs['prev'], subs['prev_text'])
                else:
                    subs['prev_link'] = '<span class="prev-1">Prev: <a href="{0}.html">{0:05d}</a></span>'.format(subs['prev'])
            if 'next' in subs:
                if 'next_text' in subs:
                    subs['next_link'] = '<span class="next-1">Next: <a href="{}.html">{}</a></span>'.format(subs['next'], subs['next_text'])
                else:
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

class HtmlOutputTest(HtmlWriterOutputTestCase):
    def _assert_title_equals(self, fname, title, header):
        html = self._read_file(fname)
        name = self.skoolfile[:-6]
        self.assertIn('<title>{}: {}</title>'.format(name, title), html)
        self.assertIn('<td class="page-header">{}</td>'.format(header), html)

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
            <td class="address-2"><span id="32768"></span>32768</td>
            <td class="bytes-0"></td>
            <td class="instruction">RET</td>
            <td class="comment-10" rowspan="1"></td>
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
            <td class="address-2"><span id="32768"></span>32768</td>
            <td class="bytes-1">ED4B0000</td>
            <td class="instruction">LD BC,(0)</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="32772"></span>32772</td>
            <td class="bytes-1">010000</td>
            <td class="instruction">LD BC,0</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="32775"></span>32775</td>
            <td class="bytes-1">0600</td>
            <td class="instruction">LD B,0</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="32777"></span>32777</td>
            <td class="bytes-1"></td>
            <td class="instruction">DEFB 0</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="32778"></span>32778</td>
            <td class="bytes-1"></td>
            <td class="instruction">DEFM "0"</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="32779"></span>32779</td>
            <td class="bytes-1"></td>
            <td class="instruction">DEFS 1</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="32780"></span>32780</td>
            <td class="bytes-1"></td>
            <td class="instruction">DEFW 0</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="32782"></span>32782</td>
            <td class="bytes-1">C9</td>
            <td class="instruction">RET</td>
            <td class="comment-10" rowspan="1"></td>
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
            <td class="address-1"><span id="32768"></span>32768</td>
            <td class="bytes-0"></td>
            <td class="instruction">DEFB 0</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="32769"></span>32769</td>
            <td class="bytes-0"></td>
            <td class="instruction">DEFM "0"</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="32770"></span>32770</td>
            <td class="bytes-0"></td>
            <td class="instruction">DEFS 1</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="32771"></span>32771</td>
            <td class="bytes-0"></td>
            <td class="instruction">DEFW 0</td>
            <td class="comment-10" rowspan="1"></td>
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
            <td class="address-2"><span id="32768"></span>32768</td>
            <td class="bytes-0"></td>
            <td class="instruction">RET</td>
            <td class="comment-10" rowspan="1"></td>
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
            {disassembly}
            [Template:asm_instruction]
            {address} {bytes:{Game[Bytes]}} {operation}
        """
        skool = """
            @assemble=2
            c32768 RET
        """
        writer = self._get_writer(ref=ref, skool=skool, case=CASE_LOWER)
        writer.write_asm_entries()
        self._assert_content_equal('32768 c9 ret', 'asm/32768.html')

    def test_parameter_DisassemblyTableNumCols_default_value(self):
        ref = """
            [Template:asm_instruction]
            <tr>
            <td class="instruction">{label} {t_anchor}{address} {operation}</td>
            <td class="comment-{annotated}{entry[annotated]}" rowspan="{comment_rowspan}">{comment}</td>
            </tr>
        """
        skool = """
            ; Routine at 50000
            ;
            ; .
            ;
            ; .
            ;
            ; It begins here.
            @label=START
            c50000 RET
        """
        writer = self._get_writer(ref=ref, skool=skool, asm_labels=True)
        writer.write_asm_entries()

        content = """
            <div class="description">50000: Routine at 50000</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="2">
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
            <td class="routine-comment" colspan="2">
            <span id="50000"></span>
            <div class="comments">
            <div class="paragraph">
            It begins here.
            </div>
            </div>
            </td>
            </tr>
            <tr>
            <td class="instruction">START <span id="50000"></span>50000 RET</td>
            <td class="comment-10" rowspan="1"></td>
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

    def test_parameter_DisassemblyTableNumCols_default_value_with_single_page(self):
        ref = """
            [Game]
            AsmSinglePageTemplate=AsmAllInOne

            [Template:asm_instruction]
            <tr>
            <td class="asm-label-{entry[labels]}">{label}</td>
            <td class="instruction">{t_anchor}{address} {operation}</td>
            <td class="comment-{annotated}{entry[annotated]}" rowspan="{comment_rowspan}">{comment}</td>
            </tr>
        """
        skool = """
            ; Routine at 32768
            c32768 RET
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        content = """
            <div id="32768" class="description">32768: Routine at 32768</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="3">
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
            <td class="instruction"><span id="32768"></span>32768 RET</td>
            <td class="comment-10" rowspan="1"></td>
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

    def test_parameter_DisassemblyTableNumCols_specified_value(self):
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
            <td class="asm-label-0"></td>
            <td class="address-2"><span id="50000"></span>50000</td>
            <td class="bytes-0"></td>
            <td class="instruction">RET</td>
            <td class="comment-10" rowspan="1"></td>
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
        line_no = 47
        for inst, address in (
            ('CALL', 30003),
            ('JP', 30006),
            ('DJNZ', 30006),
            ('JR', 30000)
        ):
            operation = '{} {}'.format(inst, address)
            self.assertEqual(html[line_no], '<td class="instruction">{}</td>'.format(operation))
            line_no += 7

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
        line_no = 47
        for inst, address in (
            ('CALL', 40003),
            ('JP', 40006),
            ('DJNZ', 40006),
            ('JR', 40000)
        ):
            operation = '{0} <a href="40000.html#{1}">{1}</a>'.format(inst, address)
            self.assertEqual(html[line_no], '<td class="instruction">{}</td>'.format(operation))
            line_no += 7

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
            line_no = 47
            for prefix in ('CALL ', 'DEFW ', 'DJNZ ', 'JP ', 'JR ', 'LD HL,'):
                inst_type = prefix.split()[0]
                exp_html = prefix + (link if inst_type in link_operands else '32768')
                self.assertEqual(html[line_no], '<td class="instruction">{}</td>'.format(exp_html))
                line_no += 7

    def test_parameter_DefaultAnimationFormat(self):
        ref = '[ImageWriter]\nDefaultAnimationFormat=png'
        fname = 'test_animation'
        exp_image_path = '{}/{}.png'.format(UDGDIR, fname)
        exp_src = '../{}'.format(exp_image_path)
        udg = Udg(130, [136] * 8) # Flashing
        macro = '#UDG0,{}({})'.format(udg.attr, fname)
        writer = self._get_writer(snapshot=udg.data, ref=ref, mock_file_info=True)
        output = writer.expand(macro, ASMDIR)
        self.assertEqual(output, '<img alt="{}" src="{}" />'.format(fname, exp_src))
        self.assertEqual(writer.file_info.fname, exp_image_path)
        self.assertEqual([[udg]], writer.image_writer.udg_array)

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
            <td class="address-2"><span id="50000"></span>50000</td>
            <td class="bytes-0"></td>
            <td class="instruction">RET</td>
            <td class="comment-10" rowspan="1"></td>
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
        # Defined by [Game], [Index], [Index:*:*], [Links] and [Paths] sections
        title_prefix = 'The woefully incomplete'
        title_suffix = 'disassembly of the RAM'
        ref = """
            [Game]
            TitlePrefix={}
            TitleSuffix={}

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
            'header_prefix': title_prefix,
            'header_suffix': title_suffix
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
            <td class="bytes-0"></td>
            <td class="instruction">LD A,B</td>
            <td class="comment-11" rowspan="1">Comment for instruction at 24576</td>
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
            <td class="asm-label-0"></td>
            <td class="address-2"><span id="24577"></span>24577</td>
            <td class="bytes-0"></td>
            <td class="instruction">RET</td>
            <td class="comment-11" rowspan="1"></td>
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
            <td class="bytes-0"></td>
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
            <td class="routine-comment" colspan="5">
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
            <td class="bytes-0"></td>
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
            <td class="routine-comment" colspan="5">
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
            <td class="bytes-0"></td>
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
            <td class="routine-comment" colspan="5">
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
            <td class="bytes-0"></td>
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
            <td class="routine-comment" colspan="5">
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
            <td class="bytes-0"></td>
            <td class="instruction">CALL <a href="../start/30000.html">30000</a></td>
            <td class="comment-11" rowspan="2">Comment for the instructions at 24584 and 24587</td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="24587"></span>24587</td>
            <td class="bytes-0"></td>
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
            <td class="address-2"><span id="32775"></span>8007</td>
            <td class="bytes-0"></td>
            <td class="instruction">jp <a href="32778.html">$800a</a></td>
            <td class="comment-10" rowspan="1"></td>
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
            <td class="address-2"><span id="32778"></span>800a</td>
            <td class="bytes-0"></td>
            <td class="instruction">jp <a href="32775.html">$8007</a></td>
            <td class="comment-10" rowspan="1"></td>
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
            <td class="address-2"><span id="{address}"></span>{address:05d}</td>
            <td class="bytes-0"></td>
            <td class="instruction">RET</td>
            <td class="comment-10" rowspan="1"></td>
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
        ref = """
            [Titles]
            Asm-b={titles[b]}
            Asm-c={titles[c]}
            Asm-g={titles[g]}
            Asm-s={titles[s]}
            Asm-t={titles[t]}
            Asm-u={titles[u]}
            Asm-w={titles[w]}
            [PageHeaders]
            Asm-b={headers[b]}
            Asm-c={headers[c]}
            Asm-g={headers[g]}
            Asm-s={headers[s]}
            Asm-t={headers[t]}
            Asm-u={headers[u]}
            Asm-w={headers[w]}
        """.format(titles=titles, headers=headers)
        skool = """
            ; b
            b30000 DEFB 0

            ; c
            c30001 RET

            ; g
            g30002 DEFB 0

            ; s
            s30003 DEFS 1

            ; t
            t30004 DEFM "a"

            ; u
            u30005 DEFB 0

            ; w
            w30006 DEFW 0
        """
        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()

        address = 30000
        for entry_type in 'bcgstuw':
            path = '{}/{}.html'.format(ASMDIR, address)
            title = '{} {}'.format(titles[entry_type], address)
            self._assert_title_equals(path, title, headers[entry_type])
            address += 1

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
            <td class="bytes-0"></td>
            <td class="instruction">LD A,B</td>
            <td class="comment-10" rowspan="1"></td>
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
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="C351"></span>50001</td>
            <td class="bytes-0"></td>
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
            <td class="address-2"><span id="7530"></span>30000</td>
            <td class="bytes-0"></td>
            <td class="instruction">LD A,B</td>
            <td class="comment-10" rowspan="1"></td>
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
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="7531"></span>30001</td>
            <td class="bytes-0"></td>
            <td class="instruction">JR <a href="30000.html#7530">30000</a></td>
            <td class="comment-10" rowspan="1"></td>
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
        ref = '[Game]\nAsmSinglePageTemplate=AsmAllInOne'
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
            <td class="address-2"><span id="32768"></span>32768</td>
            <td class="bytes-0"></td>
            <td class="instruction">CALL <a href="#32775">32775</a></td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="32771"></span>32771</td>
            <td class="bytes-0"></td>
            <td class="instruction">JR Z,<a href="#32776">32776</a></td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="32773"></span>32773</td>
            <td class="bytes-0"></td>
            <td class="instruction">JR 32768</td>
            <td class="comment-10" rowspan="1"></td>
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
            <td class="address-2"><span id="32775"></span>32775</td>
            <td class="bytes-0"></td>
            <td class="instruction">LD A,B</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-2"><span id="32776"></span>32776</td>
            <td class="bytes-0"></td>
            <td class="instruction">RET</td>
            <td class="comment-10" rowspan="1"></td>
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
            AsmSinglePageTemplate=AsmAllInOne
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
            <td class="address-2"><span id="40000"></span>40000</td>
            <td class="bytes-0"></td>
            <td class="instruction">RET</td>
            <td class="comment-10" rowspan="1"></td>
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
            <table class="input-1">
            <tr class="asm-input-header">
            <th colspan="2">Input</th>
            </tr>
            <tr>
            <td class="register">HL</td>
            <td class="register-desc">Address</td>
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
            <td class="asm-label-0"></td>
            <td class="address-2"><span id="50000"></span>50000</td>
            <td class="bytes-0"></td>
            <td class="instruction">XOR A</td>
            <td class="comment-10" rowspan="1"></td>
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
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="50001"></span>50001</td>
            <td class="bytes-0"></td>
            <td class="instruction">RET</td>
            <td class="comment-10" rowspan="1"></td>
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
            <td class="asm-label-0"></td>
            <td class="address-2"><span id="40000"></span>40000</td>
            <td class="bytes-0"></td>
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
            <td class="bytes-0"></td>
            <td class="instruction">LD B,5</td>
            <td class="comment-11" rowspan="1">Loop 5 times</td>
            </tr>
            <tr>
            <td class="asm-label-1">START_0</td>
            <td class="address-2"><span id="50002"></span>50002</td>
            <td class="bytes-0"></td>
            <td class="instruction">DJNZ <a href="50000.html#50002">START_0</a></td>
            <td class="comment-11" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-1"></td>
            <td class="address-1"><span id="50004"></span>50004</td>
            <td class="bytes-0"></td>
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
            <td class="routine-comment" colspan="5">
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
            <td class="bytes-0"></td>
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
            <td class="routine-comment" colspan="5">
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
            <td class="bytes-0"></td>
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
            <td class="bytes-0"></td>
            <td class="instruction">RST <a href="8.html">8</a></td>
            <td class="comment-11" rowspan="1">This operand should not be replaced by a label</td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-1"><span id="1"></span>00001</td>
            <td class="bytes-0"></td>
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
            <td class="address-2"><span id="50000"></span>50000</td>
            <td class="bytes-0"></td>
            <td class="instruction">XOR A</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-0"></td>
            <td class="address-2"><span id="50001"></span>50001</td>
            <td class="bytes-0"></td>
            <td class="instruction">JR 50001</td>
            <td class="comment-10" rowspan="1"></td>
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
            <td class="bytes-0"></td>
            <td class="instruction">XOR A</td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            <tr>
            <td class="asm-label-1"></td>
            <td class="address-1"><span id="50001"></span>50001</td>
            <td class="bytes-0"></td>
            <td class="instruction">JR 50001</td>
            <td class="comment-10" rowspan="1"></td>
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
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30000.html">Routine</a></div>
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
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30001.html">Bytes</a></div>
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
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30003.html">Words</a></div>
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
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30007.html">GSB entry</a></div>
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
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30008.html">Unused</a></div>
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
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30009.html">Zeroes</a></div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-1">117</td>
            <td class="map-byte-1">66</td>
            <td class="map-t"><span id="30018"></span><a href="../asm/30018.html">30018</a></td>
            <td class="map-length-0">2</td>
            <td class="map-t-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30018.html">Text</a></div>
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
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30000.html">Routine</a></div>
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
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30001.html">Bytes</a></div>
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
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30003.html">Words</a></div>
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
            <td class="map-length-0">2</td>
            <td class="map-t-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30018.html">Text</a></div>
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
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30008.html">Unused</a></div>
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
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30009.html">Zeroes</a></div>
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
        with self.assertRaisesRegex(SkoolKitError, "^Failed to format CodeFiles template: Unknown format code 'q' for object of type 'int'$"):
            writer.write_map('MemoryMap')

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
            <td class="map-length-0">1</td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/23456.html">Routine at 23456</a></div>
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

    def test_write_map_with_custom_asm_anchor_containing_skool_macro(self):
        ref = '[Game]\nAddressAnchor=#MAP({base})({address:04x},10:{address})'
        skool = '; Routine at 34567\nc34567 RET'
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
            <td class="map-page-1">135</td>
            <td class="map-byte-1">7</td>
            <td class="map-c"><span id="8707"></span><a href="../asm/34567.html">34567</a></td>
            <td class="map-length-0">1</td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/34567.html">Routine at 34567</a></div>
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
            <th class="map-page-1">Page</th>
            <th class="map-byte-1">Byte</th>
            <th>Address</th>
            <th class="map-length-0">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-1">171</td>
            <td class="map-byte-1">205</td>
            <td class="map-c"><span id="ABCD"></span><a href="../asm/43981.html">43981</a></td>
            <td class="map-length-0">2</td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/43981.html">Routine at 43981</a></div>
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
        with self.assertRaisesRegex(SkoolKitError, "^Unknown field 'foo' in AddressAnchor template$"):
            writer.write_map('MemoryMap')

    def test_write_map_with_single_page_template(self):
        ref = '[Game]\nAsmSinglePageTemplate=AsmAllInOne'
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
            <th class="map-page-1">Page</th>
            <th class="map-byte-1">Byte</th>
            <th>Address</th>
            <th class="map-length-0">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-1">128</td>
            <td class="map-byte-1">0</td>
            <td class="map-c"><span id="32768"></span><a href="../asm.html#32768">32768</a></td>
            <td class="map-length-0">1</td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm.html#32768">A routine here</a></div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-1">128</td>
            <td class="map-byte-1">1</td>
            <td class="map-b"><span id="32769"></span><a href="../asm.html#32769">32769</a></td>
            <td class="map-length-0">1</td>
            <td class="map-b-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm.html#32769">A data block there</a></div>
            <div class="map-entry-desc-0">
            </div>
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
            AsmSinglePageTemplate=AsmAllInOne
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
            <th class="map-page-1">Page</th>
            <th class="map-byte-1">Byte</th>
            <th>Address</th>
            <th class="map-length-0">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-1">171</td>
            <td class="map-byte-1">205</td>
            <td class="map-c"><span id="ABCD"></span><a href="../asm.html#ABCD">43981</a></td>
            <td class="map-length-0">1</td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm.html#ABCD">Routine at 43981</a></div>
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

    def test_write_map_with_single_page_template_using_custom_path(self):
        path = 'disassembly.html'
        ref = """
            [Game]
            AsmSinglePageTemplate=AsmAllInOne
            [Paths]
            AsmSinglePage={}
        """.format(path)
        skool = '; A routine\nc30000 RET'
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
            <td class="map-c"><span id="30000"></span><a href="../{0}#30000">30000</a></td>
            <td class="map-length-0">1</td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../{0}#30000">A routine</a></div>
            <div class="map-entry-desc-0">
            </div>
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
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30000.html">Routine</a></div>
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
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30003.html">GSB entry</a></div>
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
            <th class="map-page-0">Page</th>
            <th class="map-byte-0">Byte</th>
            <th>Address</th>
            <th class="map-length-0">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-0">178</td>
            <td class="map-byte-0">110</td>
            <td class="map-c"><span id="45678"></span><a href="../asm/45678.html">B26E</a></td>
            <td class="map-length-0">1</td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/45678.html">Routine at 45678</a></div>
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
            <td class="map-length-0">1</td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/32768.html">Code</a></div>
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
            <th class="map-page-1">Page</th>
            <th class="map-byte-1">Byte</th>
            <th>Address</th>
            <th class="map-length-0">Length</th>
            <th>Description</th>
            </tr>\n
        """
        for address in (0, 2, 44, 666, 8888):
            exp_content += """
                <tr>
                <td class="map-page-1">{0}</td>
                <td class="map-byte-1">{1}</td>
                <td class="map-c"><span id="{2}"></span><a href="../asm/{2}.html">{2:05d}</a></td>
                <td class="map-length-0">1</td>
                <td class="map-c-desc">
                <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/{2}.html"></a></div>
                <div class="map-entry-desc-0">
                </div>
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
            EntryTypes=
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
            <th class="map-page-0">Page</th>
            <th class="map-byte-0">Byte</th>
            <th>Address</th>
            <th class="map-length-0">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-0">117</td>
            <td class="map-byte-0">49</td>
            <td class="map-w"><span id="30001"></span><a href="../asm/30001.html">30001</a></td>
            <td class="map-length-0">2</td>
            <td class="map-w-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30001.html">Data</a></div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-0">117</td>
            <td class="map-byte-0">51</td>
            <td class="map-t"><span id="30003"></span><a href="../asm/30003.html">30003</a></td>
            <td class="map-length-0">1</td>
            <td class="map-t-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30003.html">Message ID</a></div>
            <div class="map-entry-desc-0">
            </div>
            </td>
            </tr>
            <tr>
            <td class="map-page-0">117</td>
            <td class="map-byte-0">52</td>
            <td class="map-t"><span id="30004"></span><a href="../asm/30004.html">30004</a></td>
            <td class="map-length-0">1</td>
            <td class="map-t-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="../asm/30004.html">Another message ID</a></div>
            <div class="map-entry-desc-0">
            </div>
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
            <td class="address-1"><span id="30000"></span>30000</td>
            <td class="bytes-0"></td>
            <td class="instruction">DEFB 0</td>
            <td class="comment-10" rowspan="1"></td>
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
            <td class="address-2"><span id="30001"></span>30001</td>
            <td class="bytes-0"></td>
            <td class="instruction">RET</td>
            <td class="comment-10" rowspan="1"></td>
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
            <td class="address-1"><span id="30002"></span>30002</td>
            <td class="bytes-0"></td>
            <td class="instruction">DEFM "a"</td>
            <td class="comment-10" rowspan="1"></td>
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
        code_id = 'secondary'
        code_path = 'other-code'
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
        ref = """
            [OtherCode:{code_id}]

            [Paths]
            {code_id}-CodePath={code_path}

            [Titles]
            {code_id}-Asm-b={titles[b]}
            {code_id}-Asm-c={titles[c]}
            {code_id}-Asm-g={titles[g]}
            {code_id}-Asm-s={titles[s]}
            {code_id}-Asm-t={titles[t]}
            {code_id}-Asm-u={titles[u]}
            {code_id}-Asm-w={titles[w]}

            [PageHeaders]
            {code_id}-Asm-b={headers[b]}
            {code_id}-Asm-c={headers[c]}
            {code_id}-Asm-g={headers[g]}
            {code_id}-Asm-s={headers[s]}
            {code_id}-Asm-t={headers[t]}
            {code_id}-Asm-u={headers[u]}
            {code_id}-Asm-w={headers[w]}
        """.format(code_id=code_id, code_path=code_path, titles=titles, headers=headers)
        other_skool = """
            ; b
            b30000 DEFB 0

            ; c
            c30001 RET

            ; g
            g30002 DEFB 0

            ; s
            s30003 DEFS 1

            ; t
            t30004 DEFM "a"

            ; u
            u30005 DEFB 0

            ; w
            w30006 DEFW 0
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
        self.assertEqual(asm_path, code_path)

        writer = main_writer.clone(main_writer.parser, code_id)
        writer.write_file = self._mock_write_file
        writer.write_entries(asm_path, map_path)

        address = 30000
        for entry_type in 'bcgstuw':
            path = '{}/{}.html'.format(asm_path, address)
            title = '{} {}'.format(titles[entry_type], address)
            self._assert_title_equals(path, title, headers[entry_type])
            address += 1

    def test_write_other_code_using_single_page_template(self):
        code_id = 'other'
        ref = """
            [Game]
            AsmSinglePageTemplate=AsmAllInOne
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
            <td class="address-2"><span id="40000"></span>40000</td>
            <td class="bytes-0"></td>
            <td class="instruction">JR <a href="#40002">40002</a></td>
            <td class="comment-10" rowspan="1"></td>
            </tr>
            </table>
            <div id="40002" class="description">40002: Routine at 40002</div>
            <table class="disassembly">
            <tr>
            <td class="routine-comment" colspan="5">
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
            <td class="address-2"><span id="40002"></span>40002</td>
            <td class="bytes-0"></td>
            <td class="instruction">JR <a href="#40000">40000</a></td>
            <td class="comment-10" rowspan="1"></td>
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
            AsmSinglePageTemplate=AsmAllInOne
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
            <td class="address-2"><span id="40000"></span>40000</td>
            <td class="bytes-0"></td>
            <td class="instruction">RET</td>
            <td class="comment-10" rowspan="1"></td>
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
            <div class="map-entry-title-10"><a class="map-entry-title" href="65535.html">{}</a></div>
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

    def test_write_other_code_index_using_single_page_template(self):
        code_id = 'other'
        ref = """
            [Game]
            AsmSinglePageTemplate=AsmAllInOne
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
            <th class="map-page-0">Page</th>
            <th class="map-byte-0">Byte</th>
            <th>Address</th>
            <th class="map-length-0">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-0">255</td>
            <td class="map-byte-0">255</td>
            <td class="map-c"><span id="65535"></span><a href="asm.html#65535">65535</a></td>
            <td class="map-length-0">1</td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="asm.html#65535">{}</a></div>
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

        writer.write_map(index_page_id)
        self._assert_files_equal(index_path, subs)

    def test_write_other_code_index_using_single_page_template_with_custom_path(self):
        code_id = 'secondary'
        asm_single_page = 'disassembly.html'
        ref = """
            [Game]
            AsmSinglePageTemplate=AsmAllInOne
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
            <th class="map-page-0">Page</th>
            <th class="map-byte-0">Byte</th>
            <th>Address</th>
            <th class="map-length-0">Length</th>
            <th>Description</th>
            </tr>
            <tr>
            <td class="map-page-0">255</td>
            <td class="map-byte-0">255</td>
            <td class="map-c"><span id="65535"></span><a href="{0}#65535">65535</a></td>
            <td class="map-length-0">1</td>
            <td class="map-c-desc">
            <div class="map-entry-title-10"><a class="map-entry-title" href="{0}#65535">{1}</a></div>
            <div class="map-entry-desc-0">
            </div>
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
        page_id = 'page'
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
            'body_class': 'page',
            'js': 'test-html.js',
            'content': '<b>This is the content of the custom page.</b>\n'
        }
        self._assert_files_equal('{}.html'.format(page_id), subs)

    def test_write_page_with_no_page_section(self):
        page_id = 'page'
        content = '<b>This is the content of the custom page.</b>'
        ref = '[Page:{}]\nPageContent={}'.format(page_id, content)
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
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30000.html">GSB entry 1</a></div>
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
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30001.html">GSB entry 2</a></div>
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
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30000.html">GSB entry 1</a></div>
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
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30001.html">GSB entry 2</a></div>
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
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30003.html">Message ID</a></div>
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
            <div class="map-entry-title-11"><a class="map-entry-title" href="../asm/30004.html">Another message ID</a></div>
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

    def test_format_registers_with_prefixes(self):
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
            <td class="bytes-0"></td>
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

    def test_write_page_with_single_global_js(self):
        global_js = 'js/global.js'
        page_id = 'Custom'
        ref = """
            [Game]
            JavaScript={0}
            [Page:{1}]
            [Template:{1}]
            {{m_javascript}}
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
            {{m_javascript}}
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
            {{m_javascript}}
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
            {{m_javascript}}
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
            {{m_javascript}}
        """.format(global_js, page_id, local_js)
        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        page = self._read_file(page_id + '.html', True)
        for i, js in enumerate(global_js_files + local_js_files):
            self.assertEqual(page[i], '<script type="text/javascript" src="{}"></script>'.format(basename(js)))

    def test_write_page_with_single_css(self):
        css = 'css/game.css'
        page_id = 'Custom'
        ref = """
            [Game]
            StyleSheet={0}
            [Page:{1}]
            Path=
            [Template:{1}]
            {{m_stylesheet}}
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
            {{m_stylesheet}}
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

    def test_changelog_with_custom_item_template(self):
        # Test that the 'Changelog-list_item' template is used if defined
        # instead of the default 'list_item' template)
        ref = """
            [Changelog:20141123]
            -

            Item 1
            Item 2

            [Template:Changelog-list_item]
            <li>* {item}</li>
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
            <foo>{{content}}</foo>
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
            <bar>{{content}}</bar>
            {{t_footer}}
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
            {entries}
        """.replace('{}', page_id)
        exp_content = """
            Just the entries!
            <div><span id="entry_1"></span></div>
            <div class="box box-1">
            <div class="box-title">Entry 1</div>
            <div class="paragraph">
            First entry.
            </div>
            </div>
        """

        writer = self._get_writer(ref=ref, skool='')
        writer.write_page(page_id)
        self._assert_content_equal(exp_content, '{}.html'.format(page_id))

    def test_box_page_as_list_items_with_custom_subtemplates(self):
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

            [Template:{}-entry]
            <div>{t_anchor}</div>
            <div class="entry entry-{num}">
            <div class="entry-title">{title}</div>
            <div class="entry-intro">{description}</div>
            {t_list_items}
            </div>

            [Template:{}-item_list]
            <ul class="level{indent}">
            {m_list_item}
            </ul>

            [Template:{}-list_item]
            <li>* {item}</li>
        """.replace('{}', page_id)
        exp_content = """
            <ul class="contents">
            <li><a href="#entry1">Entry 1</a></li>
            </ul>
            <div><span id="entry1"></span></div>
            <div class="entry entry-1">
            <div class="entry-title">Entry 1</div>
            <div class="entry-intro">Intro.</div>
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

    def test_page_with_custom_table_templates(self):
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
            {m_table_row}
            ) END TABLE

            [Template:{}-table_row]
            <row>
            {cells}
            </row>

            [Template:{}-table_header_cell]
            <header>{contents}</header>

            [Template:{}-table_cell]
            <cell>{contents}</cell>
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

    def test_custom_asm_instruction_template(self):
        skool = """
            ; Routine at 32768
            @label=START
            c32768 XOR A  ; Clear A.
        """
        ref = """
            [Template:Asm]
            {entry[title]}
            {disassembly}

            [Template:asm_instruction]
            {label} {address} {location:04X}: {operation} ; {comment}
        """
        exp_content = """
            Routine at 32768
            START 32768 8000: XOR A ; Clear A.
        """

        writer = self._get_writer(ref=ref, skool=skool, asm_labels=True)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_bytes_field_in_asm_instruction_template(self):
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
            {disassembly}

            [Template:asm_instruction]
            {address} {bytes:02X}: {operation} ; {comment}
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

    def test_bytes_field_with_separator_in_asm_instruction_template(self):
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
            {disassembly}

            [Template:asm_instruction]
            {address} {bytes:/03/,}: {operation} ; {comment}
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

    def test_custom_asm_footer_template(self):
        skool = """
            ; Routine at 32768
            c32768 RET ; That's it.
        """
        ref = """
            [Template:Asm]
            {entry[title]}
            {disassembly}
            {t_footer}

            [Template:asm_instruction]
            {address}: {operation} ; {comment}

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
            {entry[description]}
            {registers_input}
            {disassembly}

            [Template:Asm-c-asm_register]
            {name} register: {description}

            [Template:Asm-c-asm_comment]
            {m_paragraph}

            [Template:Asm-c-paragraph]
            {paragraph}

            [Template:Asm-c-asm_instruction]
            {address}: {operation} ; {comment}

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
            {entry[description]}
            {registers_input}
            {disassembly}

            [Template:Asm-asm_register]
            {name} register: {description}

            [Template:Asm-asm_comment]
            {m_paragraph}

            [Template:Asm-paragraph]
            {paragraph}

            [Template:Asm-asm_instruction]
            {address}: {operation} ; {comment}

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
            {entry[description]}
            {registers_input}
            {disassembly}

            [Template:{}-Asm-c-asm_register]
            {name} register: {description}

            [Template:{}-Asm-c-asm_comment]
            {m_paragraph}

            [Template:{}-Asm-c-paragraph]
            {paragraph}

            [Template:{}-Asm-c-asm_instruction]
            {address}: {operation} ; {comment}

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
            {entry[description]}
            {registers_input}
            {disassembly}

            [Template:{}-Asm-asm_register]
            {name} register: {description}

            [Template:{}-Asm-asm_comment]
            {m_paragraph}

            [Template:{}-Asm-paragraph]
            {paragraph}

            [Template:{}-Asm-asm_instruction]
            {address}: {operation} ; {comment}

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

    def test_custom_asm_single_page_with_custom_subtemplates(self):
        skool = """
            ; Routine at 32768
            c32768 XOR A

            ; Data block at 32769
            b32769 DEFB 0
        """
        ref = """
            [Game]
            AsmSinglePageTemplate=AsmAllInOne

            [Template:AsmSinglePage]
            {m_asm_entry}

            [Template:AsmSinglePage-asm_entry]
            {entry[title]}
            {disassembly}

            [Template:AsmSinglePage-asm_instruction]
            {address}: {operation}
        """
        exp_content = """
            Routine at 32768
            32768: XOR A
            Data block at 32769
            32769: DEFB 0
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm.html')

    def test_custom_other_code_asm_single_page_with_custom_subtemplates(self):
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
            AsmSinglePageTemplate=AsmAllInOne

            [Template:{}-AsmSinglePage]
            {m_asm_entry}

            [Template:{}-AsmSinglePage-asm_entry]
            {entry[title]}
            {disassembly}

            [Template:{}-AsmSinglePage-asm_instruction]
            {address}: {operation}
        """.replace('{}', code_id)
        exp_content = """
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
            {disassembly}

            [Template:Asm-b-asm_instruction]
            {t_anchor}: {operation}

            [Template:Asm-b-anchor]
            {anchor}
        """
        exp_content = """
            Data block at 32768
            32768: DEFB 0
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
            {entry[description]}
            {disassembly}

            [Template:{}-Asm-b-asm_instruction]
            {address}: {operation}

            [Template:{}-Asm-b-paragraph]
            {paragraph}

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
            {disassembly}
            {t_footer}

            [Template:Asm-g-asm_instruction]
            {address}: {operation}

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
            {entry[description]}
            {disassembly}

            [Template:{}-Asm-g-asm_instruction]
            {address}: {operation}

            [Template:{}-Asm-g-paragraph]
            {paragraph}

            [Template:{}-Asm-g-list]
            Items:
            {m_list_item}

            [Template:{}-Asm-g-list_item]
            + {item}
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
            {m_stylesheet}
            {entry[title]}
            {disassembly}

            [Template:Asm-s-asm_instruction]
            {address}: {operation}

            [Template:Asm-s-stylesheet]
            -- {href} --
        """
        exp_content = """
            -- ../skoolkit.css --
            Space
            32768: DEFS 10
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_custom_other_code_asm_s_page_with_custom_subtemplate(self):
        code_id = 'Stuff'
        other_skool = """
            ; Space
            s32768 DEFS 10
        """
        ref = """
            [OtherCode:{}]

            [Template:{}-Asm-s]
            {entry[title]}
            {disassembly}

            [Template:{}-Asm-s-asm_instruction]
            {address}: {operation}
        """.replace('{}', code_id)
        exp_content = """
            Space
            32768: DEFS 10
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
            {m_javascript}
            {entry[title]}
            {disassembly}

            [Template:Asm-t-asm_instruction]
            {address}: {operation}

            [Template:Asm-t-javascript]
            -- {src} --
        """
        exp_content = """
            -- ../foo.js --
            Message at 32768
            32768: DEFM "Hello"
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_custom_other_code_asm_t_page_with_custom_subtemplate(self):
        code_id = 'Stuff'
        other_skool = """
            ; Message at 32768
            t32768 DEFM "Hello"
        """
        ref = """
            [OtherCode:{}]

            [Template:{}-Asm-t]
            {entry[title]}
            {disassembly}

            [Template:{}-Asm-t-asm_instruction]
            {address}: {operation}
        """.replace('{}', code_id)
        exp_content = """
            Message at 32768
            32768: DEFM "Hello"
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
            {entry[description]}
            {disassembly}

            [Template:Asm-u-asm_instruction]
            {address}: {operation}

            [Template:Asm-u-paragraph]
            {paragraph}

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

    def test_custom_other_code_asm_u_page_with_custom_subtemplate(self):
        code_id = 'Stuff'
        other_skool = """
            ; Unused
            u32768 DEFS 100
        """
        ref = """
            [OtherCode:{}]

            [Template:{}-Asm-u]
            {entry[title]}
            {disassembly}

            [Template:{}-Asm-u-asm_instruction]
            {address}: {operation}
        """.replace('{}', code_id)
        exp_content = """
            Unused
            32768: DEFS 100
        """

        main_writer = self._get_writer(ref=ref, skool=other_skool)
        oc_writer = main_writer.clone(main_writer.parser, code_id)
        oc_writer.write_file = self._mock_write_file
        asm_path = map_path = 'other'
        oc_writer.write_entries(asm_path, map_path)
        self._assert_content_equal(exp_content, '{}/32768.html'.format(asm_path))

    def test_custom_asm_w_page_with_custom_subtemplate(self):
        skool = """
            ; A word
            w32768 DEFW 1759
        """
        ref = """
            [Template:Asm-w]
            {entry[title]}
            {disassembly}

            [Template:Asm-w-asm_instruction]
            {address}: {operation}
        """
        exp_content = """
            A word
            32768: DEFW 1759
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_asm_entries()
        self._assert_content_equal(exp_content, 'asm/32768.html')

    def test_custom_other_code_asm_w_page_with_custom_subtemplate(self):
        code_id = 'Stuff'
        other_skool = """
            ; A word
            w32768 DEFW 1759
        """
        ref = """
            [OtherCode:{}]

            [Template:{}-Asm-w]
            {entry[title]}
            {disassembly}

            [Template:{}-Asm-w-asm_instruction]
            {address}: {operation}
        """.replace('{}', code_id)
        exp_content = """
            A word
            32768: DEFW 1759
        """

        main_writer = self._get_writer(ref=ref, skool=other_skool)
        oc_writer = main_writer.clone(main_writer.parser, code_id)
        oc_writer.write_file = self._mock_write_file
        asm_path = map_path = 'other'
        oc_writer.write_entries(asm_path, map_path)
        self._assert_content_equal(exp_content, '{}/32768.html'.format(asm_path))

    def test_custom_box_page_with_custom_subtemplates(self):
        page_id = 'MyBoxes'
        ref = """
            [Page:{}]
            SectionPrefix=Box

            [Box:Box 1]
            Stuff.

            [Box:Box 2]
            More stuff.

            [Template:{}]
            {m_contents_list_item}

            {entries}

            [Template:{}-contents_list_item]
            * {title}

            [Template:{}-paragraph]
            {paragraph}

            [Template:{}-entry]
            {title}: {contents}
        """.replace('{}', page_id)
        exp_content = """
            * Box 1
            * Box 2

            Box 1: Stuff.
            Box 2: More stuff.
        """

        writer = self._get_writer(ref=ref)
        writer.write_page(page_id)
        self._assert_content_equal(exp_content, '{}.html'.format(page_id))

    def test_custom_map_page_with_custom_subtemplates(self):
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
            {m_map_entry}

            [Template:MemoryMap-map_entry]
            {entry[address]}: {entry[title]}
            {entry[description]}

            [Template:MemoryMap-paragraph]
            {paragraph}
        """
        exp_content = """
            49152: Routine at 49152
            Reset HL.
        """

        writer = self._get_writer(ref=ref, skool=skool)
        writer.write_map('MemoryMap')
        self._assert_content_equal(exp_content, 'maps/all.html')
