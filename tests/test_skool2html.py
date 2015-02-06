# -*- coding: utf-8 -*-
import re
import os
from os.path import basename, isfile, join
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
import skoolkit
from skoolkit import normpath, skool2html, PACKAGE_DIR, VERSION, SkoolKitError
from skoolkit.skoolhtml import HtmlWriter
from skoolkit.skoolparser import CASE_UPPER, CASE_LOWER

TEST_WRITER_REF = """[Config]
HtmlWriterClass={0}.TestHtmlWriter
""".format(__name__)

html_writer = None

def mock_run(*args):
    global run_args
    run_args = args

def mock_write_disassembly(*args):
    global write_disassembly_args
    write_disassembly_args = args

class TestHtmlWriter(HtmlWriter):
    def init(self):
        global html_writer
        html_writer = self
        self.call_dict = {}

    def add_call(self, method_name, args):
        self.call_dict.setdefault(method_name, []).append(args)

    def write_logo_image(self, *args):
        self.add_call('write_logo_image', args)
        return True

    def write_asm_entries(self, *args):
        self.add_call('write_asm_entries', args)

    def write_map(self, *args):
        self.add_call('write_map', args)

    def write_page(self, *args):
        self.add_call('write_page', args)

    def write_graphics(self, *args):
        self.add_call('write_graphics', args)

    def write_graphic_glitches(self, *args):
        self.add_call('write_graphic_glitches', args)

    def write_changelog(self, *args):
        self.add_call('write_changelog', args)

    def write_bugs(self, *args):
        self.add_call('write_bugs', args)

    def write_facts(self, *args):
        self.add_call('write_facts', args)

    def write_glossary(self, *args):
        self.add_call('write_glossary', args)

    def write_pokes(self, *args):
        self.add_call('write_pokes', args)

    def write_entries(self, *args):
        self.add_call('write_entries', args)

    def write_index(self, *args):
        self.add_call('write_index', args)

class MockImageWriter:
    def __init__(self, palette, options):
        global mock_image_writer
        self.palette = palette
        self.options = options
        self.default_format = None
        mock_image_writer = self

class MockSkoolParser:
    def __init__(self, *args, **kwargs):
        global mock_skool_parser
        self.skoolfile = args[0]
        self.base = kwargs.get('base')
        self.create_labels = kwargs.get('create_labels')
        self.asm_labels = kwargs.get('asm_labels')
        self.snapshot = None
        self.entries = {}
        self.memory_map = []
        mock_skool_parser = self

class Skool2HtmlTest(SkoolKitTestCase):
    def setUp(self):
        global html_writer
        SkoolKitTestCase.setUp(self)
        self.odir = 'html-{0}'.format(os.getpid())
        self.tempdirs.append(self.odir)
        html_writer = None

    def _css_c(self):
        return '-c Game/StyleSheet={0}'.format(self.write_text_file(suffix='.css'))

    def _test_option_w(self, write_option, file_ids, method_name, exp_arg_list=None):
        ref = TEST_WRITER_REF + '\n'.join((
            '[OtherCode:other]',
            'Source={0}',
            '[Bug:test:Test]',
            '<p>Hello</p>',
            '[Changelog:20120704]',
            'Intro.',
            'Item 1',
            '[Glossary:Term1]',
            'Definition 1.',
            '[Page:CustomPage1]',
            '[PageContent:CustomPage1]',
            '<b>This is the content of custom page 1.</b>',
            '[Page:CustomPage2]',
            '[PageContent:CustomPage2]',
            'Lo',
            '[GraphicGlitch:SpriteBug]',
            'There is a bug in this sprite.',
            '[Fact:fact:Fact]',
            'This is a trivia item.',
            '[Poke:poke:POKE]',
            'This is a POKE.'
        ))
        skool = '\n'.join((
            '; Routine',
            'c24576 LD HL,$6003',
            '',
            '; Data',
            'b$6003 DEFB 123',
            '',
            '; Game status buffer entry',
            'g24580 DEFB 0',
            '',
            '; A message',
            't24581 DEFM "!"',
            '',
            '; Unused',
            'u24582 DEFB 0'
        ))
        other_skool = "; Other code routine\nc32768 RET"
        other_skoolfile = self.write_text_file(other_skool, suffix='.skool')
        reffile = self.write_text_file(ref.format(other_skoolfile), suffix='.ref')
        self.write_text_file(skool, '{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('{} -d {} {} {} {}'.format(self._css_c(), self.odir, write_option, file_ids, reffile))
        self.assertEqual(error, '')
        self.assertIn(method_name, html_writer.call_dict, '{} was not called'.format(method_name))
        arg_list = html_writer.call_dict[method_name]
        exp_arg_list = exp_arg_list or [()]
        self.assertEqual(arg_list, exp_arg_list, '{}: {} != {}'.format(method_name, arg_list, exp_arg_list))

    @patch.object(skool2html, 'run', mock_run)
    def test_default_option_values(self):
        infiles = ['game1.ref', 'game2.skool']
        skool2html.main(infiles)
        files, options = run_args
        self.assertEqual(files, infiles)
        self.assertTrue(options.verbose)
        self.assertFalse(options.show_timings)
        self.assertEqual(options.config_specs, [])
        self.assertFalse(options.new_images)
        self.assertEqual(options.case, None)
        self.assertEqual(options.base, None)
        self.assertEqual(options.files, 'BbcdGgimoPpty')
        self.assertEqual(options.pages, [])
        self.assertEqual(options.output_dir, None)

    def test_no_arguments(self):
        output, error = self.run_skool2html(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: skool2html.py'))

    def test_invalid_option(self):
        output, error = self.run_skool2html('-X', catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: skool2html.py'))

    def test_no_ref(self):
        skool = '\n'.join((
            '; Routine',
            'c24576 RET',
            '',
            '; Data',
            'b24577 DEFB 0',
            '',
            '; Message',
            't24578 DEFM "Hello"'
        ))
        exp_output = '\n'.join((
            'Creating directory {0}',
            'Using skool file: {1}.skool',
            'Found no ref file for {1}.skool',
            'Parsing {1}.skool',
            'Creating directory {0}/{1}',
            'Copying {2} to {0}/{1}/{2}',
            '  Writing disassembly files in {1}/asm',
            '  Writing {1}/maps/all.html',
            '  Writing {1}/maps/routines.html',
            '  Writing {1}/maps/data.html',
            '  Writing {1}/maps/messages.html',
            '  Writing {1}/index.html'
        ))
        skoolfile = self.write_text_file(skool, suffix='.skool')
        game_name = skoolfile[:-6]
        cssfile = self.write_text_file(suffix='.css')
        output, error = self.run_skool2html('-c Game/StyleSheet={0} -d {1} {2}'.format(cssfile, self.odir, skoolfile))
        self.assertEqual(len(error), 0)
        self.assert_output_equal(output, exp_output.format(self.odir, game_name, cssfile).split('\n'), True)

    def test_nonexistent_skool_file(self):
        skoolfile = 'xyz.skool'
        with self.assertRaisesRegexp(SkoolKitError, '{}: file not found'.format(skoolfile)):
            self.run_skool2html('-d {0} {1}'.format(self.odir, skoolfile))

    def test_nonexistent_skool_file_named_in_ref_file(self):
        skoolfile = 'pqr.skool'
        ref = '[Config]\nSkoolFile={}'.format(skoolfile)
        reffile = self.write_text_file(ref, suffix='.ref')
        with self.assertRaisesRegexp(SkoolKitError, '{}: file not found'.format(skoolfile)):
            self.run_skool2html('-d {} {}'.format(self.odir, reffile))

    def test_nonexistent_ref_file(self):
        reffile = 'zyx.ref'
        with self.assertRaisesRegexp(SkoolKitError, '{}: file not found'.format(reffile)):
            self.run_skool2html('-d {0} {1}'.format(self.odir, reffile))

    def test_nonexistent_css_file(self):
        cssfile = 'abc.css'
        skoolfile = self.write_text_file(suffix='.skool')
        with self.assertRaisesRegexp(SkoolKitError, '{}: file not found'.format(cssfile)):
            self.run_skool2html('-c Game/StyleSheet={0} -w "" -d {1} {2}'.format(cssfile, self.odir, skoolfile))

    def test_nonexistent_js_file(self):
        jsfile = 'cba.js'
        skoolfile = self.write_text_file(suffix='.skool')
        ref = '\n'.join((
            '[Page:P1]',
            'JavaScript={}'.format(jsfile)
        ))
        self.write_text_file(ref, '{}.ref'.format(skoolfile[:-6]))
        with self.assertRaisesRegexp(SkoolKitError, '{}: file not found'.format(jsfile)):
            self.run_skool2html('{0} -w P -d {1} {2}'.format(self._css_c(), self.odir, skoolfile))

    def test_invalid_page_id(self):
        page_id = 'NonexistentPage'
        skoolfile = self.write_text_file(suffix='.skool')
        with self.assertRaisesRegexp(SkoolKitError, 'Invalid page ID: {}'.format(page_id)):
            self.run_skool2html('-d {0} -w P -P {1} {2}'.format(self.odir, page_id, skoolfile))

    def test_default_ref_file(self):
        skoolfile = self.write_text_file("; Routine\nc24576 RET", suffix='.skool')
        game_dir = 'default-ref-file-test-{0}'.format(os.getpid())
        reffile = self.write_text_file("[Config]\nGameDir={0}".format(game_dir), '{0}.ref'.format(skoolfile[:-6]))
        output, error = self.run_skool2html('{0} -d {1} {2}'.format(self._css_c(), self.odir, skoolfile))
        self.assertEqual(len(error), 0)
        self.assertEqual(output[2], 'Using ref file: {0}'.format(reffile))
        self.assertEqual(output[4], 'Creating directory {0}/{1}'.format(self.odir, game_dir))

    def test_multiple_ref_files(self):
        skoolfile = self.write_text_file("; Routine\nc30000 RET", suffix='.skool')
        reffile = self.write_text_file("[Config]\nSkoolFile={0}".format(skoolfile), suffix='.ref')
        prefix = reffile[:-4]
        code_path = "disasm"
        reffile2 = self.write_text_file("[Paths]\nCodePath={0}".format(code_path), '{0}-2.ref'.format(prefix))
        output, error = self.run_skool2html('{0} -d {1} {2}'.format(self._css_c(), self.odir, reffile))
        self.assertEqual(len(error), 0)
        self.assertEqual(output[2], 'Using ref files: {0}, {1}'.format(reffile, reffile2))
        self.assertEqual(output[6], '  Writing disassembly files in {0}/{1}'.format(basename(prefix), code_path))

    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_config_in_secondary_ref_file(self):
        skoolfile = self.write_text_file(suffix='.skool')
        reffile1 = self.write_text_file(suffix='.ref')
        game_dir = 'foo'
        ref = '\n'.join((
            '[Config]',
            'SkoolFile={}'.format(skoolfile),
            'GameDir={}'.format(game_dir)
        ))
        reffile2 = self.write_text_file(ref, '{}-2.ref'.format(reffile1[:-4]))
        output, error = self.run_skool2html(reffile1)
        self.assertEqual(error, '')
        html_writer = write_disassembly_args[0]
        self.assertEqual(html_writer.file_info.game_dir, game_dir)
        skool_parser = html_writer.parser
        self.assertEqual(skool_parser.skoolfile, skoolfile)

    def test_skool_from_stdin(self):
        self.write_stdin('; Routine\nc30000 RET')
        game_dir = 'program'
        output, error = self.run_skool2html('{0} -d {1} -'.format(self._css_c(), self.odir))
        self.assertEqual(len(error), 0)
        self.assertEqual(output[1], 'Parsing skool file from standard input')
        self.assertEqual(output[2], 'Creating directory {}/{}'.format(self.odir, game_dir))
        self.assertTrue(isfile(join(self.odir, game_dir, 'asm', '30000.html')))

    def test_output_dir_with_trailing_separator(self):
        skoolfile = self.write_text_file("; Routine\nc49152 RET", suffix='.skool')
        output, error = self.run_skool2html('{0} -d {1}/ {2}'.format(self._css_c(), self.odir, skoolfile))
        self.assertEqual(len(error), 0)
        self.assertEqual(output[0], 'Creating directory {0}'.format(self.odir))

    def test_no_output_dir(self):
        skoolfile = self.write_text_file("; Routine\nc49152 RET", suffix='.skool')
        name = basename(skoolfile[:-6])
        self.tempdirs.append(name)
        output, error = self.run_skool2html('{0} {1}'.format(self._css_c(), skoolfile))
        self.assertEqual(len(error), 0)
        self.assertEqual(output[3], 'Creating directory {0}'.format(name))

    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_html_writer_class(self):
        writer_module = '\n'.join((
            'import sys',
            'from skoolkit.skoolhtml import HtmlWriter',
            'class TestHtmlWriter(HtmlWriter):',
            '    def init(self):',
            '        sys.stdout.write("{0}\\n")'
        ))
        ref = "[Config]\nHtmlWriterClass={0}:{1}.TestHtmlWriter"
        module_dir = self.make_directory()
        module_path = os.path.join(module_dir, 'testmod.py')
        message = 'Initialising TestHtmlWriter'
        module = self.write_text_file(writer_module.format(message), path=module_path)
        module_name = basename(module)[:-3]
        reffile = self.write_text_file(ref.format(module_dir, module_name), suffix='.ref')
        name = reffile[:-4]
        self.write_text_file('', '{0}.skool'.format(name))
        output, error = self.run_skool2html(reffile)
        self.assertEqual(error, '')
        self.assertEqual(output[3], message)

    def test_file_identification(self):
        # Test that a file named *.ref is treated as a ref file
        reffile = self.write_text_file(TEST_WRITER_REF, suffix='.ref')
        self.write_text_file(path='{0}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('{0} -d {1} {2}'.format(self._css_c(), self.odir, reffile))
        self.assertEqual(error, '')
        self.assertIn('write_index', html_writer.call_dict)

        # Test that a file not named *.ref is treated as a skool file
        for suffix in ('.skool', '.sks', '.kit', ''):
            skoolfile = self.write_text_file("; Data\nb40000 DEFB 0", suffix=suffix)
            game_dir = skoolfile[:-len(suffix)] if suffix else skoolfile
            output, error = self.run_skool2html('{0} -d {1} {2}'.format(self._css_c(), self.odir, skoolfile))
            self.assertEqual(error, '')
            self.assertEqual(output[0], 'Using skool file: {0}'.format(skoolfile))
            self.assertTrue(isfile(join(self.odir, game_dir, 'asm', '40000.html')))

    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_search_dirs(self):
        subdir = self.make_directory()
        skool = '; Routine\nc30000 RET'
        skoolfile = self.write_text_file(skool, os.path.join(subdir, 'test-{}.skool'.format(os.getpid())))
        game = 'Test{}'.format(os.getpid())
        ref = '[Game]\nGame={}'.format(game)
        reffile = self.write_text_file(ref, '{}.ref'.format(skoolfile[:-6]))

        # Test that a ref file in the same directory as the skool file is found
        output, error = self.run_skool2html(skoolfile)
        self.assertEqual(error, '')
        html_writer = write_disassembly_args[0]
        self.assertEqual(html_writer.game['Game'], game)

        # Test that a skool file in the same directory as the ref file is found
        output, error = self.run_skool2html(reffile)
        self.assertEqual(error, '')
        html_writer = write_disassembly_args[0]
        self.assertEqual(len(html_writer.entries), 1)
        self.assertIn(30000, html_writer.entries)

    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_image_writer_options(self):
        exp_iw_options = (
            ('DefaultFormat', 'gif'),
            ('GIFEnableAnimation', 0),
            ('GIFTransparency', 1),
            ('PNGAlpha', 1),
            ('PNGCompressionLevel', 4),
            ('PNGEnableAnimation', 0)
        )
        ref = '[ImageWriter]\n' + '\n'.join(['{}={}'.format(k, v) for k, v in exp_iw_options])
        reffile = self.write_text_file(ref, suffix='.ref')
        self.write_text_file(path='{}.skool'.format(reffile[:-4]))

        output, error = self.run_skool2html(reffile)
        self.assertEqual(error, '')
        iw_options = write_disassembly_args[0].image_writer.options
        for k, v in exp_iw_options:
            self.assertEqual(iw_options[k], v)

    def test_font_is_copied(self):
        font_file = self.write_bin_file(suffix='.ttf')
        reffile = self.write_text_file("[Game]\nFont={}".format(font_file), suffix='.ref')
        self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('{} -d {} {}'.format(self._css_c(), self.odir, reffile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, font_file)))

    def test_multiple_fonts_are_copied(self):
        font_files = [self.write_bin_file(suffix='.ttf'), self.write_bin_file(suffix='.ttf')]
        reffile = self.write_text_file("[Game]\nFont={}".format(';'.join(font_files)), suffix='.ref')
        self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('{} -d {} {}'.format(self._css_c(), self.odir, reffile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, font_files[0])))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, font_files[1])))

    def test_custom_font_path(self):
        font_file = self.write_bin_file(suffix='.ttf')
        font_path = 'fonts'
        ref = '\n'.join((
            '[Game]',
            'Font={}',
            '[Paths]',
            'FontPath={}'
        )).format(font_file, font_path)
        reffile = self.write_text_file(ref, suffix='.ref')
        self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('{} -d {} {}'.format(self._css_c(), self.odir, reffile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, font_path, font_file)))

    def test_js_file_is_copied(self):
        global_js_file = self.write_text_file(suffix='.js')
        local_js_file = self.write_text_file(suffix='.js')
        ref = '\n'.join((
            '[Game]',
            'JavaScript={}',
            '[Page:CustomPage]',
            'JavaScript={}',
            'PageContent=<b>Hello</b>'
        )).format(global_js_file, local_js_file)
        reffile = self.write_text_file(ref, suffix='.ref')
        self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('{} -d {} -w P {}'.format(self._css_c(), self.odir, reffile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, global_js_file)))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, local_js_file)))

    def test_multiple_js_files_are_copied(self):
        global_js_files = [self.write_text_file(suffix='.js'), self.write_text_file(suffix='.js')]
        local_js_files = [self.write_text_file(suffix='.js'), self.write_text_file(suffix='.js')]
        ref = '\n'.join((
            '[Game]',
            'JavaScript={}',
            '[Page:CustomPage]',
            'JavaScript={}',
            'PageContent=<b>Hello</b>'
        )).format(';'.join(global_js_files), ';'.join(local_js_files))
        reffile = self.write_text_file(ref, suffix='.ref')
        self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('{} -d {} -w P {}'.format(self._css_c(), self.odir, reffile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        for js_file in global_js_files + local_js_files:
            self.assertTrue(os.path.isfile(os.path.join(game_dir, js_file)))

    def test_custom_javascript_path(self):
        global_js_file = self.write_text_file(suffix='.js')
        local_js_file = self.write_text_file(suffix='.js')
        js_path = 'javascript'
        ref = '\n'.join((
            '[Game]',
            'JavaScript={}',
            '[Paths]',
            'JavaScriptPath={}',
            '[Page:CustomPage]',
            'JavaScript={}',
            'PageContent=<b>Hello</b>'
        )).format(global_js_file, js_path, local_js_file)
        reffile = self.write_text_file(ref, suffix='.ref')
        self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('{} -d {} -w P {}'.format(self._css_c(), self.odir, reffile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, js_path, global_js_file)))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, js_path, local_js_file)))

    def test_custom_style_sheet_path(self):
        css_file = self.write_text_file(suffix='.css')
        style_sheet_path = 'css'
        ref = '\n'.join((
            '[Game]',
            'StyleSheet={}',
            '[Paths]',
            'StyleSheetPath={}'
        )).format(css_file, style_sheet_path)
        reffile = self.write_text_file(ref, suffix='.ref')
        self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('-d {} {}'.format(self.odir, reffile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, style_sheet_path, css_file)))

    def test_resources_are_copied(self):
        resource1 = self.write_bin_file(suffix='.jpg')
        resource2 = self.write_bin_file(suffix='.swf')
        resource3 = self.write_bin_file(suffix='.pdf')
        dest_dir = 'stuff'
        ref = '\n'.join((
            '[Resources]',
            '{}=.'.format(resource1),
            '{}={}'.format(resource2, dest_dir),
            '{}={}'.format(resource3, dest_dir)
        ))
        reffile = self.write_text_file(ref, suffix='.ref')
        self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('{} -d {} {}'.format(self._css_c(), self.odir, reffile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, resource1)))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, dest_dir, resource2)))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, dest_dir, resource3)))

    def test_resource_not_found(self):
        resource = 'nosuchfile.png'
        reffile = self.write_text_file("[Resources]\n{}=foo".format(resource), suffix='.ref')
        self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        with self.assertRaisesRegexp(SkoolKitError, 'Cannot copy resource "{}": file not found'.format(resource)):
            self.run_skool2html('{} -d {} {}'.format(self._css_c(), self.odir, reffile))

    def test_resource_is_not_copied_over_existing_file(self):
        resource = self.write_bin_file(suffix='.jpg')
        dest_dir = 'already-exists'
        reffile = self.write_text_file("[Resources]\n{}={}".format(resource, dest_dir), suffix='.ref')
        self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        path = os.path.join(self.odir, reffile[:-4], dest_dir)
        self.write_text_file(path=path)
        with self.assertRaisesRegexp(SkoolKitError, 'Cannot copy {0} to {1}: {1} is not a directory'.format(resource, dest_dir)):
            self.run_skool2html('{} -d {} {}'.format(self._css_c(), self.odir, reffile))

    def test_option_S(self):
        resource_dir = self.make_directory()
        css_fname = 'foo.css'
        cssfile = self.write_text_file(path='{}/{}'.format(resource_dir, css_fname))
        reffile = self.write_text_file('[Game]\nStyleSheet={}'.format(css_fname), suffix='.ref')
        self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        for option in ('-S', '--search'):
            output, error = self.run_skool2html('{} {} -d {} {}'.format(option, resource_dir, self.odir, reffile))
            self.assertEqual(error, '')
            game_dir = os.path.join(self.odir, reffile[:-4])
            self.assertTrue(os.path.isfile(os.path.join(game_dir, css_fname)))

    def test_option_S_multiple(self):
        css_fname = 'foo.css'
        js_fname = 'bar.js'
        ref = '\n'.join((
            '[Game]',
            'StyleSheet={}'.format(css_fname),
            'JavaScript={}'.format(js_fname)
        ))
        reffile = self.write_text_file(ref, suffix='.ref')
        resource_dir1 = self.make_directory()
        resource_dir2 = self.make_directory()
        resource_dir3 = self.make_directory()
        cssfile = self.write_text_file(path='{}/{}'.format(resource_dir1, css_fname))
        jsfile = self.write_text_file(path='{}/{}'.format(resource_dir2, js_fname))
        self.write_text_file(path='{}/{}.skool'.format(resource_dir3, reffile[:-4]))
        output, error = self.run_skool2html('-S {} --search {} -S {} -d {} {}'.format(resource_dir1, resource_dir2, resource_dir3, self.odir, reffile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, css_fname)))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, js_fname)))

    def test_option_s(self):
        exp_preamble = [
            'skool2html.py searches the following directories for skool files, ref files,',
            'CSS files, JavaScript files, font files, and files listed in the [Resources]',
            'section of the ref file:',
            ''
        ]
        preamble_len = len(exp_preamble)
        exp_search_dirs = [
            'The directory that contains the skool or ref file named on the command line',
            'The current working directory',
            os.path.join('.', 'resources'),
            os.path.join(os.path.expanduser('~'), '.skoolkit'),
            os.path.join(PACKAGE_DIR, 'resources'),
            'Any other directories specified by the -S/--search option'
        ]
        for option in ('-s', '--search-dirs'):
            output, error = self.run_skool2html(option, catch_exit=0)
            self.assertEqual(error, '')
            self.assertEqual(output[:preamble_len], exp_preamble)
            self.assertEqual(output[preamble_len:], ['- ' + d for d in exp_search_dirs])

    def test_option_j(self):
        css1_content = 'a { color: blue }'
        css1 = self.write_text_file(css1_content, suffix='.css')
        css2_content = 'td { color: red }'
        css2 = self.write_text_file(css2_content, suffix='.css')
        ref = '[Game]\nStyleSheet={};{}'.format(css1, css2)
        reffile = self.write_text_file(ref, suffix='.ref')
        self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        game_dir = normpath(self.odir, reffile[:-4])
        single_css = 'style.css'
        single_css_f = normpath(game_dir, single_css)
        appending_msg = 'Appending {{}} to {}'.format(single_css_f)
        for option in ('-j', '--join-css'):
            output, error = self.run_skool2html('{} {} -d {} {}'.format(option, single_css, self.odir, reffile))
            self.assertEqual(error, '')
            self.assertIn(appending_msg.format(css1), output)
            self.assertIn(appending_msg.format(css2), output)
            self.assertTrue(os.path.isfile(single_css_f))
            self.assertFalse(os.path.isfile(os.path.join(game_dir, css1)))
            self.assertFalse(os.path.isfile(os.path.join(game_dir, css2)))
            with open(single_css_f) as f:
                css = f.read()
            self.assertEqual(css, '\n'.join((css1_content, css2_content, '')))

    def test_option_j_directory_exists(self):
        single_css = 'game.css'
        skoolfile = self.write_text_file(suffix='.skool')
        game_dir = normpath(self.odir, skoolfile[:-6])
        dest = normpath(game_dir, single_css)
        self.make_directory(dest)
        error_msg = "Cannot write CSS file '{}': {} already exists and is a directory".format(single_css, dest)
        for option in ('-j', '--join-css'):
            with self.assertRaisesRegexp(SkoolKitError, error_msg):
                self.run_skool2html('{} {} {} -d {} {}'.format(option, single_css, self._css_c(), self.odir, skoolfile))

    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_option_a(self):
        skoolfile = self.write_text_file(suffix='.skool')
        for option in ('-a', '--asm-labels'):
            output, error = self.run_skool2html('{} {}'.format(option, skoolfile))
            self.assertEqual(error, '')
            self.assertIs(mock_skool_parser.create_labels, False)
            self.assertIs(mock_skool_parser.asm_labels, True)

    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_option_C(self):
        skoolfile = self.write_text_file(suffix='.skool')
        for option in ('-C', '--create-labels'):
            output, error = self.run_skool2html('{} {}'.format(option, skoolfile))
            self.assertEqual(error, '')
            self.assertIs(mock_skool_parser.create_labels, True)

    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_P(self):
        ref = '\n'.join((
            '[Page:Page1]',
            '[Page:Page2]'
        ))
        reffile = self.write_text_file(ref, suffix='.ref')
        self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        for option in ('-P', '--pages'):
            for pages in ('Page1', 'Page1,Page2'):
                output, error = self.run_skool2html('{} {} {}'.format(option, pages, reffile))
                self.assertEqual(error, '')
                self.assertEqual(write_disassembly_args[4], pages.split(','))
        output, error = self.run_skool2html(reffile)
        self.assertEqual(write_disassembly_args[4], ['Page1', 'Page2'])

    def test_option_w_m(self):
        exp_arg_list = [
            ('MemoryMap',),
            ('RoutinesMap',),
            ('DataMap',),
            ('MessagesMap',),
            ('UnusedMap',),
            ('GameStatusBuffer',)
        ]
        self._test_option_w('--write', 'm', 'write_map', exp_arg_list)

    def test_option_w_d(self):
        self._test_option_w('-w', 'd', 'write_asm_entries')

    def test_option_w_P(self):
        self._test_option_w('--write', 'P', 'write_page', [('CustomPage1',), ('CustomPage2',)])

    def test_option_w_B(self):
        self._test_option_w('-w', 'B', 'write_graphic_glitches')

    def test_option_w_c(self):
        self._test_option_w('--write', 'c', 'write_changelog')

    def test_option_w_b(self):
        self._test_option_w('-w', 'b', 'write_bugs')

    def test_option_w_t(self):
        self._test_option_w('--write', 't', 'write_facts')

    def test_option_w_y(self):
        self._test_option_w('-w', 'y', 'write_glossary')

    def test_option_w_p(self):
        self._test_option_w('--write', 'p', 'write_pokes')

    def test_option_w_o_map(self):
        self._test_option_w('-w', 'o', 'write_map', [('other-Index',)])

    def test_option_w_o_entries(self):
        self._test_option_w('--write', 'o', 'write_entries', [('other', 'other/other.html')])

    def test_option_w_i(self):
        self._test_option_w('-w', 'i', 'write_index')

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_skool2html(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

    def test_option_p(self):
        for option in ('-p', '--package-dir'):
            output, error = self.run_skool2html(option, catch_exit=0)
            self.assertEqual(error, '')
            self.assertEqual(len(output), 1)
            self.assertEqual(output[0], os.path.dirname(skoolkit.__file__))

    def test_option_q(self):
        reffile = self.write_text_file(TEST_WRITER_REF, suffix='.ref')
        name = reffile[:-4]
        self.write_text_file('', '{0}.skool'.format(name))
        index_method = 'write_index'
        for option in ('-q', '--quiet'):
            output, error = self.run_skool2html('{0} {1} -d {2} -w i {3}'.format(self._css_c(), option, self.odir, reffile))
            self.assertEqual(error, '')
            self.assertIn(index_method, html_writer.call_dict, '{0} was not called'.format(index_method))
            self.assertEqual(len(output), 0)

    def test_option_t(self):
        skoolfile = self.write_text_file(suffix='.skool')
        pattern = 'Done \([0-9]+\.[0-9][0-9]s\)'
        for option in ('-t', '--time'):
            output, error = self.run_skool2html('{0} {1} -w i -d {2} {3}'.format(self._css_c(), option, self.odir, skoolfile))
            self.assertEqual(error, '')
            done = output[-1]
            search = re.search(pattern, done)
            self.assertIsNot(search, None, '"{0}" is not of the form "{1}"'.format(done, pattern))

    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_c(self):
        ref = TEST_WRITER_REF + '[Colours]\nRED=197,0,0'
        reffile = self.write_text_file(ref, suffix='.ref')
        self.write_text_file('', '{0}.skool'.format(reffile[:-4]))
        sl_spec = 'GARBAGE'
        for option in ('-c', '--config'):
            for section_name, param_name, value in (
                ('Colours', 'RED', '255,0,0'),
                ('Config', 'GameDir', 'test-c'),
                ('ImageWriter', 'DefaultFormat', 'gif')
            ):
                output, error = self.run_skool2html('{} {}/{}={} {}'.format(option, section_name, param_name, value, reffile))
                self.assertEqual(error, '')
                section = html_writer.ref_parser.get_dictionary(section_name)
                self.assertEqual(section[param_name], value, '{0}/{1}!={2}'.format(section_name, param_name, value))
            with self.assertRaisesRegexp(SkoolKitError, 'Malformed SectionName/Line spec: {0}'.format(sl_spec)):
                self.run_skool2html('{} {} {}'.format(option, sl_spec, reffile))

    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_W(self):
        writer_class = '{}.TestHtmlWriter'.format(__name__)
        skoolfile = self.write_text_file(suffix='.skool')
        for option in ('-W', '--writer'):
            output, error = self.run_skool2html('{} {} {}'.format(option, writer_class, skoolfile))
            self.assertEqual(error, '')
            self.assertEqual(html_writer.__class__, TestHtmlWriter)

    def test_option_T(self):
        reffile = self.write_text_file(TEST_WRITER_REF, suffix='.ref')
        skoolfile = self.write_text_file(path='{0}.skool'.format(reffile[:-4]))
        cssfile1 = self.write_text_file(suffix='.css')
        cssfile2 = self.write_text_file(suffix='.css')
        theme = 'blue'
        cssfile3 = self.write_text_file(path='{0}-{1}.css'.format(cssfile2[:-4], theme))
        stylesheet = 'Game/StyleSheet={0};{1}'.format(cssfile1, cssfile2)
        for option in ('-T', '--theme'):
            output, error = self.run_skool2html('-d {0} -c {1} {2} {3} {4}'.format(self.odir, stylesheet, option, theme, reffile))
            self.assertEqual(error, '')
            self.assertEqual(html_writer.game_vars['StyleSheet'], '{};{};{}'.format(cssfile1, cssfile2, cssfile3))

    def test_option_T_multiple(self):
        reffile = self.write_text_file(TEST_WRITER_REF, suffix='.ref')
        skoolfile = self.write_text_file(path='{0}.skool'.format(reffile[:-4]))
        default_css = [self.write_text_file(suffix='.css') for i in range(2)]
        themes = ('dark', 'wide', 'long')
        exp_css = []
        for css in default_css:
            exp_css.append(css)
            for theme in themes:
                exp_css.append(self.write_text_file(path='{0}-{1}.css'.format(css[:-4], theme)))
        stylesheet = 'Game/StyleSheet={}'.format(';'.join(default_css))
        theme_options = ['-T {}'.format(theme) for theme in themes]
        output, error = self.run_skool2html('-d {} -c {} {} {}'.format(self.odir, stylesheet, ' '.join(theme_options), reffile))
        self.assertEqual(error, '')
        actual_css = html_writer.game_vars['StyleSheet'].split(';')
        self.assertEqual(actual_css, exp_css)

    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_o(self):
        reffile = self.write_text_file(TEST_WRITER_REF, suffix='.ref')
        self.write_text_file('', '{0}.skool'.format(reffile[:-4]))
        for option in ('-o', '--rebuild-images'):
            output, error = self.run_skool2html('{} {}'.format(option, reffile))
            self.assertEqual(error, '')
            self.assertTrue(html_writer.file_info.replace_images)

    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_l(self):
        reffile = self.write_text_file(TEST_WRITER_REF, suffix='.ref')
        self.write_text_file('', '{0}.skool'.format(reffile[:-4]))
        for option in ('-l', '--lower'):
            output, error = self.run_skool2html('{} {}'.format(option, reffile))
            self.assertEqual(error, '')
            self.assertEqual(html_writer.case, CASE_LOWER)

    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_u(self):
        reffile = self.write_text_file(TEST_WRITER_REF, suffix='.ref')
        self.write_text_file('', '{0}.skool'.format(reffile[:-4]))
        for option in ('-u', '--upper'):
            output, error = self.run_skool2html('{} {}'.format(option, reffile))
            self.assertEqual(error, '')
            self.assertEqual(html_writer.case, CASE_UPPER)

    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_D(self):
        reffile = self.write_text_file(TEST_WRITER_REF, suffix='.ref')
        self.write_text_file('', '{0}.skool'.format(reffile[:-4]))
        for option in ('-D', '--decimal'):
            output, error = self.run_skool2html('{} {}'.format(option, reffile))
            self.assertEqual(error, '')
            self.assertTrue(html_writer.parser.mode.decimal)

    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_H(self):
        reffile = self.write_text_file(TEST_WRITER_REF, suffix='.ref')
        self.write_text_file('', '{0}.skool'.format(reffile[:-4]))
        for option in ('-H', '--hex'):
            output, error = self.run_skool2html('{} {}'.format(option, reffile))
            self.assertEqual(error, '')
            self.assertTrue(html_writer.parser.mode.hexadecimal)

    def test_option_R(self):
        for option in ('-R', '--ref-file'):
            output, error = self.run_skool2html(option, catch_exit=0)
            self.assertEqual(error, '')
            self.assertEqual(output[0], '[Colours]')
            self.assertIn('[Titles]', output)

    def test_option_r(self):
        for option in ('-r', '--ref-sections'):
            for prefix, exp_headers in (
                ('Colours', ['Colours']),
                ('Template:index_section', ['Template:index_section', 'Template:index_section_item']),
                ('Template:index_section$', ['Template:index_section'])
            ):
                output, error = self.run_skool2html('{} {}'.format(option, prefix), catch_exit=0)
                self.assertEqual(error, '')
                headers = [line[1:-1] for line in output if line.startswith('[') and line.endswith(']')]
                self.assertEqual(exp_headers, headers)

if __name__ == '__main__':
    unittest.main()
