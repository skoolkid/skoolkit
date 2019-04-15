import re
import os.path
from textwrap import dedent
from unittest.mock import patch, Mock

from skoolkittest import SkoolKitTestCase
import skoolkit
from skoolkit import normpath, skool2html, BASE_10, BASE_16, PACKAGE_DIR, VERSION, SkoolKitError
from skoolkit.config import COMMANDS
from skoolkit.skoolhtml import HtmlWriter
from skoolkit.skoolparser import CASE_UPPER, CASE_LOWER

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

    def write_asm_entries(self, *args):
        self.add_call('write_asm_entries', args)

    def write_map(self, *args):
        self.add_call('write_map', args)

    def write_page(self, *args):
        self.add_call('write_page', args)

    def write_entries(self, *args):
        self.add_call('write_entries', args)

    def write_index(self, *args):
        self.add_call('write_index', args)

class MockSkoolParser:
    def __init__(self, *args, **kwargs):
        global mock_skool_parser
        self.skoolfile = args[0]
        self.base = kwargs.get('base')
        self.case = kwargs.get('case')
        self.create_labels = kwargs.get('create_labels')
        self.asm_labels = kwargs.get('asm_labels')
        self.snapshot = None
        self.entries = {}
        self.memory_map = []
        self.fields = {}
        mock_skool_parser = self

    def get_entry(self, address):
        return self.entries.get(address)

    def make_replacements(self, item):
        pass

    def clone(self, skoolfile):
        return self

def mock_config(name):
    config = {}
    for k, v in COMMANDS.get(name, {}).items():
        if isinstance(v[0], tuple):
            config[k] = []
        else:
            config[k] = v[0]
    return config

class Skool2HtmlTest(SkoolKitTestCase):
    def setUp(self):
        global html_writer
        SkoolKitTestCase.setUp(self)
        self.odir = 'html-{0}'.format(os.getpid())
        self.tempdirs.append(self.odir)
        html_writer = None

    def _write_ref_file(self, text, path=None, suffix='.ref'):
        return self.write_text_file(dedent(text).strip(), path, suffix)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'get_config', mock_config)
    def _test_option_w(self, write_option, file_ids, method_name, exp_arg_list=None):
        ref = """
            [OtherCode:other]
            Source={0}
            [Bug:test:Test]
            <p>Hello</p>
            [Changelog:20120704]
            Intro.
            Item 1
            [Glossary:Term1]
            Definition 1.
            [Page:CustomPage1]
            PageContent=<b>This is the content of custom page 1.</b>
            [Page:CustomPage2]
            PageContent=Lo
            [GraphicGlitch:SpriteBug]
            There is a bug in this sprite.
            [Fact:fact:Fact]
            This is a trivia item.
            [Poke:poke:POKE]
            This is a POKE.
        """
        skool = """
            ; Routine
            c24576 LD HL,$6003

            ; Data
            b$6003 DEFB 123

            ; Game status buffer entry
            g24580 DEFB 0

            ; A message
            t24581 DEFM "!"

            ; Unused
            u24582 DEFB 0
        """
        other_skool = "; Other code routine\nc32768 RET"
        other_skoolfile = self.write_text_file(other_skool, suffix='.skool')
        reffile = self._write_ref_file(ref.format(other_skoolfile))
        skoolfile = self.write_text_file(dedent(skool).strip(), '{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('-d {} {} {} {}'.format(self.odir, write_option, file_ids, skoolfile))
        self.assertEqual(error, '')
        self.assertIn(method_name, html_writer.call_dict, '{} was not called'.format(method_name))
        arg_list = html_writer.call_dict[method_name]
        exp_arg_list = exp_arg_list or [()]
        self.assertEqual(arg_list, exp_arg_list, '{}: {} != {}'.format(method_name, arg_list, exp_arg_list))

    @patch.object(skool2html, 'run', mock_run)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_default_option_values(self):
        infiles = ['game1.ref', 'game2.skool']
        skool2html.main(infiles)
        files, options = run_args
        self.assertEqual(files, infiles)
        self.assertFalse(options.asm_labels)
        self.assertFalse(options.asm_one_page)
        self.assertFalse(options.create_labels)
        self.assertEqual(options.single_css, '')
        self.assertEqual(options.search, [])
        self.assertEqual(options.themes, [])
        self.assertFalse(options.quiet)
        self.assertFalse(options.show_timings)
        self.assertEqual(options.config_specs, [])
        self.assertFalse(options.new_images)
        self.assertEqual(options.case, 0)
        self.assertEqual(options.base, 0)
        self.assertEqual(options.files, 'dimoP')
        self.assertEqual(options.pages, [])
        self.assertEqual(options.output_dir, '.')
        self.assertEqual(options.params, [])
        self.assertEqual(options.variables, [])

    @patch.object(skool2html, 'run', mock_run)
    def test_config_read_from_file(self):
        output_dir = self.make_directory()
        ini = """
            [skool2html]
            AsmLabels=1
            AsmOnePage=1
            Base=16
            Case=-1
            CreateLabels=1
            JoinCss=css.css
            OutputDir={}
            Quiet=1
            RebuildImages=1
            Search=this,that
            Theme=dark,wide
            Time=1
        """.format(output_dir)
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        infiles = ['game1.ref', 'game2.skool']
        skool2html.main(infiles)
        files, options = run_args
        self.assertEqual(files, infiles)
        self.assertTrue(options.asm_labels)
        self.assertTrue(options.asm_one_page)
        self.assertTrue(options.create_labels)
        self.assertEqual(options.single_css, 'css.css')
        self.assertEqual(options.search, ['this', 'that'])
        self.assertEqual(options.themes, ['dark', 'wide'])
        self.assertEqual(options.quiet, 1)
        self.assertTrue(options.show_timings)
        self.assertEqual(options.config_specs, ['Game/AsmSinglePageTemplate=AsmAllInOne'])
        self.assertTrue(options.new_images)
        self.assertEqual(options.case, -1)
        self.assertEqual(options.base, 16)
        self.assertEqual(options.files, 'dimoP')
        self.assertEqual(options.pages, [])
        self.assertEqual(options.output_dir, output_dir)

    @patch.object(skool2html, 'run', mock_run)
    def test_invalid_option_values_read_from_file(self):
        ini = """
            [skool2html]
            AsmLabels=x
            Base=10
            CreateLabels=y
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        infiles = ['game.skool']
        skool2html.main(infiles)
        files, options = run_args
        self.assertEqual(files, infiles)
        self.assertFalse(options.asm_labels)
        self.assertFalse(options.asm_one_page)
        self.assertFalse(options.create_labels)
        self.assertEqual(options.single_css, '')
        self.assertEqual(options.search, [])
        self.assertEqual(options.themes, [])
        self.assertFalse(options.quiet)
        self.assertFalse(options.show_timings)
        self.assertEqual(options.config_specs, [])
        self.assertFalse(options.new_images)
        self.assertEqual(options.case, 0)
        self.assertEqual(options.base, 10)
        self.assertEqual(options.files, 'dimoP')
        self.assertEqual(options.pages, [])
        self.assertEqual(options.output_dir, '.')

    def test_no_arguments(self):
        output, error = self.run_skool2html(catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: skool2html.py'))

    def test_invalid_option(self):
        output, error = self.run_skool2html('-X', catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: skool2html.py'))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'get_config', mock_config)
    def test_no_ref(self):
        skool = """
            ; Routine
            c24576 RET

            ; Data
            b24577 DEFB 0

            ; Message
            t24578 DEFM "Hello"
        """
        skoolfile = self.write_text_file(dedent(skool).strip(), suffix='.skool')
        game_name = skoolfile[:-6]
        cssfile = self.write_text_file(suffix='.css')
        exp_output = """
            Found no ref file for {1}.skool
            Parsing {1}.skool
            Output directory: {0}/{1}
            Copying {2} to {2}
            Writing disassembly files in asm
            Writing maps/all.html
            Writing maps/routines.html
            Writing maps/data.html
            Writing maps/messages.html
            Writing index.html
        """.format(self.odir, game_name, cssfile)
        output, error = self.run_skool2html('-c Game/StyleSheet={} -d {} {}'.format(cssfile, self.odir, skoolfile))
        self.assertEqual(error, '')
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_nonexistent_skool_file(self):
        skoolfile = 'xyz.skool'
        with self.assertRaisesRegex(SkoolKitError, '{}: file not found'.format(skoolfile)):
            self.run_skool2html('-d {0} {1}'.format(self.odir, skoolfile))

    def test_nonexistent_secondary_skool_file(self):
        other_skoolfile = 'save.skool'
        ref = '[OtherCode:save]\nSource={}'.format(other_skoolfile)
        reffile = self._write_ref_file(ref)
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        with self.assertRaisesRegex(SkoolKitError, '{}: file not found'.format(other_skoolfile)):
            self.run_skool2html('-w o -d {} {}'.format(self.odir, skoolfile))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_ref_file_on_command_line(self):
        ref2 = """
            [Game]
            Game=Bar
        """
        ref2file = self._write_ref_file(ref2)
        ref1 = """
            [Config]
            RefFiles={}
            [Game]
            Game=Foo
        """.format(ref2file)
        ref1file = self._write_ref_file(ref1)
        ref3 = """
            [Game]
            Game=Baz
        """
        ref3file = self._write_ref_file(ref3)
        exp_reffiles = (ref1file, ref2file, ref3file)
        skoolfile = self.write_text_file(path=ref1file[:-4] + '.skool')
        output, error = self.run_skool2html('{} {}'.format(skoolfile, ref3file))
        self.assertEqual(error, '')
        self.assertIn('Using ref files: {}\n'.format(', '.join(exp_reffiles)), output)
        html_writer = write_disassembly_args[0]
        self.assertEqual(html_writer.game_vars['Game'], 'Baz')

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_ref_files_on_command_line(self):
        ref1 = """
            [Game]
            Game=Foo
        """
        ref1file = self._write_ref_file(ref1)
        ref2 = """
            [Game]
            Game=Bar
        """
        ref2file = self._write_ref_file(ref2)
        exp_reffiles = (ref1file, ref2file)
        skoolfile = self.write_text_file(suffix='.skool')
        output, error = self.run_skool2html('{} {} {}'.format(skoolfile, ref1file, ref2file))
        self.assertEqual(error, '')
        self.assertIn('Using ref files: {}\n'.format(', '.join(exp_reffiles)), output)
        html_writer = write_disassembly_args[0]
        self.assertEqual(html_writer.game_vars['Game'], 'Bar')

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_ref_file_on_command_line_appends_content(self):
        ref1 = """
            [Game]
            AddressAnchor={address:04x}
            Game=Foo
        """
        ref1file = self._write_ref_file(ref1)
        ref2 = """
            [Game+]
            Game=Baz
            Release=1.0
        """
        ref2file = self._write_ref_file(ref2)
        skoolfile = self.write_text_file(path=ref1file[:-4] + '.skool')
        output, error = self.run_skool2html('{} {}'.format(skoolfile, ref2file))
        self.assertEqual(error, '')
        self.assertIn('Using ref files: {}, {}\n'.format(ref1file, ref2file), output)
        html_writer = write_disassembly_args[0]
        self.assertEqual(html_writer.game_vars['AddressAnchor'], '{address:04x}')
        self.assertEqual(html_writer.game_vars['Game'], 'Baz')
        self.assertEqual(html_writer.game_vars['Release'], '1.0')

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_ref_file_on_command_line_is_one_already_automatically_parsed(self):
        ref2 = """
            [Game]
            Game=Bar
        """
        ref2file = self._write_ref_file(ref2)
        ref1 = """
            [Config]
            RefFiles={}
            [Game]
            Game=Foo
        """.format(ref2file)
        ref1file = self._write_ref_file(ref1)
        exp_reffiles = (ref1file, ref2file)
        skoolfile = self.write_text_file(path=ref1file[:-4] + '.skool')
        output, error = self.run_skool2html('{} {}'.format(skoolfile, ref1file))
        self.assertEqual(error, '')
        self.assertIn('Using ref files: {}\n'.format(', '.join(exp_reffiles)), output)
        html_writer = write_disassembly_args[0]
        self.assertEqual(html_writer.game_vars['Game'], 'Bar')

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_ref_file_on_command_line_is_already_in_RefFiles_parameter(self):
        ref2 = """
            [Game]
            Game=Bar
        """
        ref2file = self._write_ref_file(ref2)
        ref1 = """
            [Config]
            RefFiles={}
            [Game]
            Game=Foo
        """.format(ref2file)
        ref1file = self._write_ref_file(ref1)
        exp_reffiles = (ref1file, ref2file)
        skoolfile = self.write_text_file(path=ref1file[:-4] + '.skool')
        output, error = self.run_skool2html('{} {}'.format(skoolfile, ref2file))
        self.assertEqual(error, '')
        self.assertIn('Using ref files: {}\n'.format(', '.join(exp_reffiles)), output)
        html_writer = write_disassembly_args[0]
        self.assertEqual(html_writer.game_vars['Game'], 'Bar')

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_skool_file_and_ref_file_in_separate_subdirectories(self):
        skool_path = os.path.join(self.make_directory(), 'test.skool')
        skoolfile = self.write_text_file(path=skool_path)
        ref = """
            [Game]
            Game=Bar
        """
        ref_path = os.path.join(self.make_directory(), 'extra.ref')
        reffile = self._write_ref_file(ref, path=ref_path)
        output, error = self.run_skool2html('{} {}'.format(skoolfile, reffile))
        self.assertEqual(error, '')
        self.assertIn('Using ref file: {}\n'.format(normpath(reffile)), output)
        self.assertIn('Parsing {}\n'.format(normpath(skoolfile)), output)
        html_writer = write_disassembly_args[0]
        self.assertEqual(html_writer.game_vars['Game'], 'Bar')

    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_nonexistent_ref_file_on_command_line(self):
        skoolfile = self.write_text_file(suffix='.skool')
        reffile = 'nonexistent.ref'
        with self.assertRaisesRegex(SkoolKitError, '{}: file not found'.format(reffile)):
            self.run_skool2html('-d {} {} {}'.format(self.odir, skoolfile, reffile))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_nonexistent_css_file(self):
        cssfile = 'abc.css'
        skoolfile = self.write_text_file(suffix='.skool')
        with self.assertRaisesRegex(SkoolKitError, '{}: file not found'.format(cssfile)):
            self.run_skool2html('-c Game/StyleSheet={0} -w "" -d {1} {2}'.format(cssfile, self.odir, skoolfile))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_nonexistent_js_file(self):
        jsfile = 'cba.js'
        skoolfile = self.write_text_file(suffix='.skool')
        ref = """
            [Page:P1]
            JavaScript={}
        """.format(jsfile)
        self._write_ref_file(ref, '{}.ref'.format(skoolfile[:-6]))
        with self.assertRaisesRegex(SkoolKitError, '{}: file not found'.format(jsfile)):
            self.run_skool2html('-w P -d {} {}'.format(self.odir, skoolfile))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_invalid_page_id(self):
        page_id = 'NonexistentPage'
        skoolfile = self.write_text_file(suffix='.skool')
        with self.assertRaisesRegex(SkoolKitError, 'Invalid page ID: {}'.format(page_id)):
            self.run_skool2html('-d {0} -w P -P {1} {2}'.format(self.odir, page_id, skoolfile))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_default_ref_file(self):
        skoolfile = self.write_text_file(suffix='.skool')
        game_dir = 'default-ref-file-test-{0}'.format(os.getpid())
        reffile = self.write_text_file("[Config]\nGameDir={0}".format(game_dir), '{0}.ref'.format(skoolfile[:-6]))
        output, error = self.run_skool2html('-d {} {}'.format(self.odir, skoolfile))
        self.assertEqual(error, '')
        self.assertIn('Using ref file: {}\n'.format(reffile), output)
        self.assertIn('\nOutput directory: {}/{}\n'.format(self.odir, game_dir), output)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_multiple_ref_files(self):
        skoolfile = self.write_text_file(suffix='.skool')
        prefix = skoolfile[:-6]
        game_dir = 'game'
        reffile = self.write_text_file("[Config]\nGameDir={}".format(game_dir), '{}-1.ref'.format(prefix))
        code_path = "disasm"
        reffile2 = self.write_text_file("[Paths]\nCodePath={0}".format(code_path), '{0}-2.ref'.format(prefix))
        output, error = self.run_skool2html('-d {} {}'.format(self.odir, skoolfile))
        self.assertEqual(error, '')
        self.assertIn('Using ref files: {}, {}\n'.format(reffile, reffile2), output)
        self.assertIn('\nWriting disassembly files in {}\n'.format(code_path), output)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_config_in_secondary_ref_file(self):
        skoolfile = self.write_text_file(suffix='.skool')
        prefix = skoolfile[:-6]
        reffile1 = self.write_text_file(path='{}.ref'.format(prefix))
        game_dir = 'foo'
        ref = "[Config]\nGameDir={}".format(game_dir)
        reffile2 = self._write_ref_file(ref, '{}-2.ref'.format(prefix))
        output, error = self.run_skool2html(skoolfile)
        self.assertEqual(error, '')
        html_writer = write_disassembly_args[0]
        self.assertEqual(html_writer.file_info.odir, game_dir)
        skool_parser = html_writer.parser
        self.assertEqual(skool_parser.skoolfile, skoolfile)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'get_config', mock_config)
    def test_skool_from_stdin(self):
        self.write_stdin('; Routine\nc30000 RET')
        game_dir = 'program'
        output, error = self.run_skool2html('-d {} -'.format(self.odir))
        self.assertEqual(error, '')
        self.assertIn('Parsing skool file from standard input\nOutput directory: {}/{}\n'.format(self.odir, game_dir), output)
        self.assertIsNotNone(html_writer.get_entry(30000))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_output_dir_with_trailing_separator(self):
        skoolfile = self.write_text_file(suffix='.skool')
        output, error = self.run_skool2html('-d {}/ {}'.format(self.odir, skoolfile))
        self.assertEqual(error, '')
        self.assertIn('\nOutput directory: {}/{}\n'.format(self.odir, skoolfile[:-6]), output)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_no_output_dir(self):
        skoolfile = self.write_text_file(suffix='.skool')
        name = os.path.basename(skoolfile[:-6])
        self.tempdirs.append(name)
        output, error = self.run_skool2html(skoolfile)
        self.assertEqual(error, '')
        self.assertIn('\nOutput directory: {}\n'.format(name), output)

    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_html_writer_class(self):
        message = 'Initialising TestHtmlWriter'
        writer_module = """
            import sys
            from skoolkit.skoolhtml import HtmlWriter
            class TestHtmlWriter(HtmlWriter):
                def init(self):
                    sys.stdout.write("{}\\n")
        """.format(message)
        ref = "[Config]\nHtmlWriterClass={0}:{1}.TestHtmlWriter"
        module_dir = self.make_directory()
        module_path = os.path.join(module_dir, 'testmod.py')
        module = self.write_text_file(dedent(writer_module).strip(), path=module_path)
        module_name = os.path.basename(module)[:-3]
        reffile = self.write_text_file(ref.format(module_dir, module_name), suffix='.ref')
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html(skoolfile)
        self.assertEqual(error, '')
        self.assertIn('\n{}\n'.format(message), output)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_first_input_file_is_treated_as_skool_file_regardless_of_name(self):
        for suffix in ('.skool', '.sks', '.ref', ''):
            skoolfile = self.write_text_file(suffix=suffix)
            output, error = self.run_skool2html(skoolfile)
            self.assertEqual(error, '')
            self.assertIn('Parsing {}\n'.format(skoolfile), output)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_ref_file_in_same_directory_as_skool_file(self):
        subdir = self.make_directory()
        skoolfile = self.write_text_file(path='{}/test-{}.skool'.format(subdir, os.getpid()))
        reffile = self.write_text_file(path='{}.ref'.format(skoolfile[:-6]))
        output, error = self.run_skool2html(skoolfile)
        self.assertEqual(error, '')
        self.assertIn('Using ref file: {}\n'.format(reffile), output)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_skool_file_in_same_directory_as_ref_file(self):
        subdir = self.make_directory()
        reffile = self.write_text_file(path='{}/test-{}.ref'.format(subdir, os.getpid()))
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html(skoolfile)
        self.assertEqual(error, '')
        self.assertIn('Parsing {}\n'.format(skoolfile), output)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
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
        ref = '\n'.join(['[ImageWriter]'] + ['{}={}'.format(k, v) for k, v in exp_iw_options])
        reffile = self.write_text_file(ref, suffix='.ref')
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))

        output, error = self.run_skool2html(skoolfile)
        self.assertEqual(error, '')
        iw_options = write_disassembly_args[0].image_writer.options
        for k, v in exp_iw_options:
            self.assertEqual(iw_options[k], v)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_font_is_copied(self):
        font_file = self.write_bin_file(suffix='.ttf')
        reffile = self.write_text_file("[Game]\nFont={}".format(font_file), suffix='.ref')
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('-d {} {}'.format(self.odir, skoolfile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, font_file)))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_multiple_fonts_are_copied(self):
        font_files = [self.write_bin_file(suffix='.ttf'), self.write_bin_file(suffix='.ttf')]
        reffile = self.write_text_file("[Game]\nFont={}".format(';'.join(font_files)), suffix='.ref')
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('-d {} {}'.format(self.odir, skoolfile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, font_files[0])))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, font_files[1])))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_custom_font_path(self):
        font_file = self.write_bin_file(suffix='.ttf')
        font_path = 'fonts'
        ref = """
            [Game]
            Font={}
            [Paths]
            FontPath={}
        """.format(font_file, font_path)
        reffile = self._write_ref_file(ref)
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('-d {} {}'.format(self.odir, skoolfile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, font_path, font_file)))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_js_file_is_copied(self):
        global_js_file = self.write_text_file(suffix='.js')
        local_js_file = self.write_text_file(suffix='.js')
        ref = """
            [Game]
            JavaScript={}
            [Page:CustomPage]
            JavaScript={}
            PageContent=<b>Hello</b>
        """.format(global_js_file, local_js_file)
        reffile = self._write_ref_file(ref)
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('-d {} -w P {}'.format(self.odir, skoolfile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, global_js_file)))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, local_js_file)))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_multiple_js_files_are_copied(self):
        global_js_files = [self.write_text_file(suffix='.js'), self.write_text_file(suffix='.js')]
        local_js_files = [self.write_text_file(suffix='.js'), self.write_text_file(suffix='.js')]
        ref = """
            [Game]
            JavaScript={}
            [Page:CustomPage]
            JavaScript={}
            PageContent=<b>Hello</b>
        """.format(';'.join(global_js_files), ';'.join(local_js_files))
        reffile = self._write_ref_file(ref)
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('-d {} -w P {}'.format(self.odir, skoolfile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        for js_file in global_js_files + local_js_files:
            self.assertTrue(os.path.isfile(os.path.join(game_dir, js_file)))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_custom_javascript_path(self):
        global_js_file = self.write_text_file(suffix='.js')
        local_js_file = self.write_text_file(suffix='.js')
        js_path = 'javascript'
        ref = """
            [Game]
            JavaScript={}
            [Paths]
            JavaScriptPath={}
            [Page:CustomPage]
            JavaScript={}
            PageContent=<b>Hello</b>
        """.format(global_js_file, js_path, local_js_file)
        reffile = self._write_ref_file(ref)
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('-d {} -w P {}'.format(self.odir, skoolfile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, js_path, global_js_file)))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, js_path, local_js_file)))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_custom_style_sheet_path(self):
        css_file = self.write_text_file(suffix='.css')
        style_sheet_path = 'css'
        ref = """
            [Game]
            StyleSheet={}
            [Paths]
            StyleSheetPath={}
        """.format(css_file, style_sheet_path)
        reffile = self._write_ref_file(ref)
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('-d {} {}'.format(self.odir, skoolfile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, style_sheet_path, css_file)))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_resources_are_copied(self):
        resource1 = self.write_bin_file(suffix='.jpg')
        resource2 = self.write_bin_file(suffix='.swf')
        resource3 = self.write_bin_file(suffix='.pdf')
        dest_dir = 'stuff'
        ref = """
            [Resources]
            {0}=.
            {1}={3}
            {2}={3}
        """.format(resource1, resource2, resource3, dest_dir)
        reffile = self._write_ref_file(ref)
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('-d {} {}'.format(self.odir, skoolfile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, resource1)))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, dest_dir, resource2)))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, dest_dir, resource3)))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_resources_using_pathname_expansion(self):
        resource_dir = self.make_directory()
        self.write_bin_file(path=os.path.join(resource_dir, 'bar.png'))
        self.write_bin_file(path=os.path.join(resource_dir, 'baz.png'))
        self.write_bin_file(path=os.path.join(resource_dir, 'foo.txt'))
        self.write_bin_file(path=os.path.join(resource_dir, 'qux.pdf'))
        self.write_bin_file(path=os.path.join(resource_dir, 'xyzzy.png'))
        ref = """
            [Resources]
            b*.png=images
            fo?.txt=text
            [p-r]*.pdf=pdf
            [!b]*.png=png
        """
        reffile = self._write_ref_file(ref)
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('-d {} -S {} {}'.format(self.odir, resource_dir, skoolfile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, reffile[:-4])
        self.assertTrue(os.path.isfile(os.path.join(game_dir, 'images', 'bar.png')))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, 'images', 'baz.png')))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, 'text', 'foo.txt')))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, 'pdf', 'qux.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, 'png', 'xyzzy.png')))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_resource_not_found(self):
        resource = 'nosuchfile.png'
        reffile = self.write_text_file("[Resources]\n{}=foo".format(resource), suffix='.ref')
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        with self.assertRaisesRegex(SkoolKitError, 'Cannot copy resource "{}": file not found'.format(resource)):
            self.run_skool2html('-d {} {}'.format(self.odir, skoolfile))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_resource_is_not_copied_over_existing_file(self):
        resource = self.write_bin_file(suffix='.jpg')
        dest_dir = 'already-exists'
        reffile = self.write_text_file("[Resources]\n{}={}".format(resource, dest_dir), suffix='.ref')
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        path = os.path.join(self.odir, reffile[:-4], dest_dir)
        self.write_text_file(path=path)
        with self.assertRaisesRegex(SkoolKitError, 'Cannot copy {0} to {1}: {1} is not a directory'.format(resource, dest_dir)):
            self.run_skool2html('-d {} {}'.format(self.odir, skoolfile))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_single_page_disassembly(self):
        reffile = self.write_text_file("[Game]\nAsmSinglePageTemplate=AsmAllInOne", suffix='.ref')
        prefix = reffile[:-4]
        skoolfile = self.write_text_file(path='{}.skool'.format(prefix))
        output, error = self.run_skool2html('-d {} {}'.format(self.odir, skoolfile))
        self.assertEqual(error, '')
        self.assertIn('\nWriting asm.html\n', output)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_single_page_disassembly_other_code(self):
        ref = """
            [Game]
            AsmSinglePageTemplate=AsmAllInOne
            [OtherCode:start]
            Source={}
        """.format(self.write_text_file(suffix='.skool'))
        reffile = self._write_ref_file(ref)
        prefix = reffile[:-4]
        skoolfile = self.write_text_file(path='{}.skool'.format(prefix))
        output, error = self.run_skool2html('-d {} {}'.format(self.odir, skoolfile))
        self.assertEqual(error, '')
        self.assertIn('\nWriting start/asm.html\n', output)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_other_code_source_in_subdirectory(self):
        subdir = self.make_directory()
        ref = """
            [OtherCode:start]
            Source={}
        """.format(os.path.join(subdir, 'start.skool'))
        self.write_text_file(path='{}/start.skool'.format(subdir))
        reffile = self._write_ref_file(ref)
        prefix = reffile[:-4]
        skoolfile = self.write_text_file(path='{}.skool'.format(prefix))
        output, error = self.run_skool2html('-d {} {}'.format(self.odir, skoolfile))
        self.assertEqual(error, '')
        self.assertIn('\nParsing {}/start.skool\n'.format(subdir), output)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_1(self):
        skoolfile = self.write_text_file(suffix='.skool')
        for option in ('-1', '--asm-one-page'):
            output, error = self.run_skool2html('{} {}'.format(option, skoolfile))
            self.assertEqual(error, '')
            self.assertEqual(html_writer.asm_single_page_template, 'AsmAllInOne')

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_S(self):
        resource_dir = self.make_directory()
        css_fname = 'foo.css'
        cssfile = self.write_text_file(path='{}/{}'.format(resource_dir, css_fname))
        reffile = self.write_text_file('[Game]\nStyleSheet={}'.format(css_fname), suffix='.ref')
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        for option in ('-S', '--search'):
            output, error = self.run_skool2html('{} {} -d {} {}'.format(option, resource_dir, self.odir, skoolfile))
            self.assertEqual(error, '')
            game_dir = os.path.join(self.odir, reffile[:-4])
            self.assertTrue(os.path.isfile(os.path.join(game_dir, css_fname)))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_S_multiple(self):
        css_fname = 'foo.css'
        js_fname = 'bar.js'
        ref = """
            [Game]
            StyleSheet={}
            JavaScript={}
        """.format(css_fname, js_fname)
        resource_dir1 = self.make_directory()
        resource_dir2 = self.make_directory()
        resource_dir3 = self.make_directory()
        cssfile = self.write_text_file(path='{}/{}'.format(resource_dir1, css_fname))
        jsfile = self.write_text_file(path='{}/{}'.format(resource_dir2, js_fname))
        skoolfile = self.write_text_file(path='{}/option_S.skool'.format(resource_dir3))
        reffile = self._write_ref_file(ref, path='{}/option_S.ref'.format(resource_dir3))
        output, error = self.run_skool2html('-S {} --search {} -S {} -d {} {}'.format(resource_dir1, resource_dir2, resource_dir3, self.odir, skoolfile))
        self.assertEqual(error, '')
        game_dir = os.path.join(self.odir, 'option_S')
        self.assertTrue(os.path.isfile(os.path.join(game_dir, css_fname)))
        self.assertTrue(os.path.isfile(os.path.join(game_dir, js_fname)))

    def test_option_s(self):
        exp_preamble = """
            skool2html.py searches the following directories for CSS files, JavaScript
            files, font files, and files listed in the [Resources] section of the ref file:

            - The directory that contains the skool file named on the command line
            - The current working directory
            - {}
            - {}
            - {}
            - Any other directories specified by the -S/--search option
        """.format(os.path.join('.', 'resources'),
                   os.path.join(os.path.expanduser('~'), '.skoolkit'),
                   os.path.join(PACKAGE_DIR, 'resources'))
        for option in ('-s', '--search-dirs'):
            output, error = self.run_skool2html(option, catch_exit=0)
            self.assertEqual(error, '')
            self.assertEqual(dedent(exp_preamble).strip(), output.rstrip())

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_j(self):
        css1_content = 'a { color: blue }'
        css1 = self.write_text_file(css1_content, suffix='.css')
        css2_content = 'td { color: red }'
        css2 = self.write_text_file(css2_content, suffix='.css')
        ref = '[Game]\nStyleSheet={};{}'.format(css1, css2)
        reffile = self.write_text_file(ref, suffix='.ref')
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        game_dir = normpath(self.odir, reffile[:-4])
        single_css = 'style.css'
        single_css_f = normpath(game_dir, single_css)
        appending_msg = 'Appending {{}} to {}'.format(single_css_f)
        for option in ('-j', '--join-css'):
            output, error = self.run_skool2html('{} {} -d {} {}'.format(option, single_css, self.odir, skoolfile))
            self.assertEqual(error, '')
            self.assertIn(appending_msg.format(css1), output)
            self.assertIn(appending_msg.format(css2), output)
            self.assertTrue(os.path.isfile(single_css_f))
            self.assertFalse(os.path.isfile(os.path.join(game_dir, css1)))
            self.assertFalse(os.path.isfile(os.path.join(game_dir, css2)))
            with open(single_css_f) as f:
                css = f.read()
            self.assertEqual(css, '\n'.join((css1_content, css2_content, '')))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_option_j_directory_exists(self):
        single_css = 'game.css'
        skoolfile = self.write_text_file(suffix='.skool')
        game_dir = normpath(self.odir, skoolfile[:-6])
        dest = normpath(game_dir, single_css)
        self.make_directory(dest)
        error_msg = "Cannot write CSS file '{}': {} already exists and is a directory".format(single_css, dest)
        for option in ('-j', '--join-css'):
            with self.assertRaisesRegex(SkoolKitError, error_msg):
                self.run_skool2html('{} {} -d {} {}'.format(option, single_css, self.odir, skoolfile))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_a(self):
        skoolfile = self.write_text_file(suffix='.skool')
        for option in ('-a', '--asm-labels'):
            output, error = self.run_skool2html('{} {}'.format(option, skoolfile))
            self.assertEqual(error, '')
            self.assertFalse(mock_skool_parser.create_labels)
            self.assertTrue(mock_skool_parser.asm_labels)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_C(self):
        skoolfile = self.write_text_file(suffix='.skool')
        for option in ('-C', '--create-labels'):
            output, error = self.run_skool2html('{} {}'.format(option, skoolfile))
            self.assertEqual(error, '')
            self.assertTrue(mock_skool_parser.create_labels)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_P(self):
        ref = """
            [Page:Page1]
            [Page:Page2]
        """
        reffile = self._write_ref_file(ref)
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        for option in ('-P', '--pages'):
            for pages in ('Page1', 'Page1,Page2'):
                output, error = self.run_skool2html('{} {} {}'.format(option, pages, skoolfile))
                self.assertEqual(error, '')
                self.assertEqual(write_disassembly_args[4], pages.split(','))
        output, error = self.run_skool2html(skoolfile)
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
        exp_pages = ('Bugs', 'Changelog', 'Facts', 'Glossary', 'GraphicGlitches', 'Pokes', 'CustomPage1', 'CustomPage2')
        self._test_option_w('--write', 'P', 'write_page', [(p,) for p in exp_pages])

    def test_option_w_o_map(self):
        self._test_option_w('-w', 'o', 'write_map', [('other-Index',)])

    def test_option_w_o_entries(self):
        self._test_option_w('--write', 'o', 'write_entries', [('other', 'other/other.html')])

    def test_option_w_i(self):
        self._test_option_w('-w', 'i', 'write_index')

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_skool2html(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))

    def test_option_p(self):
        for option in ('-p', '--package-dir'):
            output, error = self.run_skool2html(option, catch_exit=0)
            self.assertEqual(error, '')
            self.assertEqual(output, os.path.dirname(skoolkit.__file__) + '\n')

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    def test_option_q(self):
        skoolfile = self.write_text_file(suffix='.skool')
        index_method = 'write_index'
        for option in ('-q', '--quiet'):
            output, error = self.run_skool2html('{} -d {} -w i {}'.format(option, self.odir, skoolfile))
            self.assertEqual(error, '')
            self.assertIn(index_method, html_writer.call_dict, '{0} was not called'.format(index_method))
            self.assertEqual(output, '')

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_t(self):
        skoolfile = self.write_text_file(suffix='.skool')
        pattern = 'Done \([0-9]+\.[0-9][0-9]s\)'
        for option in ('-t', '--time'):
            output, error = self.run_skool2html('{} -w i -d {} {}'.format(option, self.odir, skoolfile))
            self.assertEqual(error, '')
            done = output.split('\n')[-2]
            match = re.match(pattern, done)
            self.assertTrue(match, '"{}" is not of the form "{}"'.format(done, pattern))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_c(self):
        ref = '[Colours]\nRED=197,0,0'
        reffile = self.write_text_file(ref, suffix='.ref')
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        sl_spec = 'GARBAGE'
        for option in ('-c', '--config'):
            for section_name, param_name, value in (
                ('Colours', 'RED', '255,0,0'),
                ('Config', 'GameDir', 'test-c'),
                ('ImageWriter', 'DefaultFormat', 'gif')
            ):
                output, error = self.run_skool2html('{} {}/{}={} {}'.format(option, section_name, param_name, value, skoolfile))
                self.assertEqual(error, '')
                section = html_writer.ref_parser.get_dictionary(section_name)
                self.assertEqual(section[param_name], value, '{0}/{1}!={2}'.format(section_name, param_name, value))
            with self.assertRaisesRegex(SkoolKitError, 'Malformed SectionName/Line spec: {0}'.format(sl_spec)):
                self.run_skool2html('{} {} {}'.format(option, sl_spec, skoolfile))

    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_W(self):
        writer_class = '{}.TestHtmlWriter'.format(__name__)
        skoolfile = self.write_text_file(suffix='.skool')
        for option in ('-W', '--writer'):
            output, error = self.run_skool2html('{} {} {}'.format(option, writer_class, skoolfile))
            self.assertEqual(error, '')
            self.assertEqual(html_writer.__class__, TestHtmlWriter)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_T(self):
        skoolfile = self.write_text_file(suffix='.skool')
        cssfile1 = self.write_text_file(suffix='.css')
        cssfile2 = self.write_text_file(suffix='.css')
        cssfile4 = self.write_text_file(suffix='.css')
        theme = cssfile4[:-4]
        cssfile3 = self.write_text_file(path='{0}-{1}.css'.format(cssfile2[:-4], theme))
        stylesheet = 'Game/StyleSheet={0};{1}'.format(cssfile1, cssfile2)
        exp_css_files = (cssfile1, cssfile2, cssfile3, cssfile4)
        for option in ('-T', '--theme'):
            output, error = self.run_skool2html('-d {} -c {} {} {} {}'.format(self.odir, stylesheet, option, theme, skoolfile))
            self.assertEqual(error, '')
            self.assertEqual(html_writer.game_vars['StyleSheet'], ';'.join(exp_css_files))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_T_multiple(self):
        skoolfile = self.write_text_file(suffix='.skool')
        default_css = [self.write_text_file(suffix='.css') for i in range(2)]
        themes = ('dark', 'wide', 'long')
        exp_css = []
        for css in default_css:
            exp_css.append(css)
            for theme in themes:
                exp_css.append(self.write_text_file(path='{0}-{1}.css'.format(css[:-4], theme)))
        stylesheet = 'Game/StyleSheet={}'.format(';'.join(default_css))
        theme_options = ['-T {}'.format(theme) for theme in themes]
        output, error = self.run_skool2html('-d {} -c {} {} {}'.format(self.odir, stylesheet, ' '.join(theme_options), skoolfile))
        self.assertEqual(error, '')
        actual_css = html_writer.game_vars['StyleSheet'].split(';')
        self.assertEqual(exp_css, actual_css)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_o(self):
        skoolfile = self.write_text_file(suffix='.skool')
        for option in ('-o', '--rebuild-images'):
            output, error = self.run_skool2html('{} {}'.format(option, skoolfile))
            self.assertEqual(error, '')
            self.assertTrue(html_writer.file_info.replace_images)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_l(self):
        skoolfile = self.write_text_file(suffix='.skool')
        for option in ('-l', '--lower'):
            output, error = self.run_skool2html('{} {}'.format(option, skoolfile))
            self.assertEqual(error, '')
            self.assertEqual(mock_skool_parser.case, CASE_LOWER)
            self.assertEqual(html_writer.case, CASE_LOWER)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_u(self):
        skoolfile = self.write_text_file(suffix='.skool')
        for option in ('-u', '--upper'):
            output, error = self.run_skool2html('{} {}'.format(option, skoolfile))
            self.assertEqual(error, '')
            self.assertEqual(mock_skool_parser.case, CASE_UPPER)
            self.assertEqual(html_writer.case, CASE_UPPER)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_D(self):
        skoolfile = self.write_text_file(suffix='.skool')
        for option in ('-D', '--decimal'):
            output, error = self.run_skool2html('{} {}'.format(option, skoolfile))
            self.assertEqual(error, '')
            self.assertTrue(mock_skool_parser.base, BASE_10)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    def test_option_H(self):
        skoolfile = self.write_text_file(suffix='.skool')
        for option in ('-H', '--hex'):
            output, error = self.run_skool2html('{} {}'.format(option, skoolfile))
            self.assertEqual(error, '')
            self.assertTrue(mock_skool_parser.base, BASE_16)

    def test_option_R(self):
        for option in ('-R', '--ref-file'):
            output, error = self.run_skool2html(option, catch_exit=0)
            self.assertEqual(error, '')
            self.assertTrue(output.startswith('[Colours]\n'))
            self.assertIn('\n[Titles]\n', output)

    def test_option_r(self):
        for option in ('-r', '--ref-sections'):
            for prefix, exp_headers in (
                ('Colours', ['Colours']),
                ('Template:index_section', ['Template:index_section', 'Template:index_section_item']),
                ('Template:index_section$', ['Template:index_section'])
            ):
                output, error = self.run_skool2html('{} {}'.format(option, prefix), catch_exit=0)
                self.assertEqual(error, '')
                headers = [line[1:-1] for line in output.split('\n') if line.startswith('[') and line.endswith(']')]
                self.assertEqual(exp_headers, headers)

    @patch.object(skool2html, 'run', mock_run)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_I(self):
        for option, spec, attr, exp_value in (('-I', 'Base=16', 'base', 16), ('--ini', 'Case=1', 'case', 1)):
            self.run_skool2html('{} {} test-I.skool'.format(option, spec))
            options = run_args[1]
            self.assertEqual(options.params, [spec])
            self.assertEqual(getattr(options, attr), exp_value)

    @patch.object(skool2html, 'run', mock_run)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_I_multiple(self):
        self.run_skool2html('-I Quiet=1 --ini Time=1 test-I-multiple.skool')
        options = run_args[1]
        self.assertEqual(options.params, ['Quiet=1', 'Time=1'])
        self.assertEqual(options.quiet, 1)
        self.assertEqual(options.show_timings, 1)

    @patch.object(skool2html, 'run', mock_run)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_I_multivalued_parameters(self):
        self.run_skool2html('-I Search=dir1,dir2 --ini Theme=theme1,theme2 test-I-multivalued.skool')
        options = run_args[1]
        self.assertEqual(options.params, ['Search=dir1,dir2', 'Theme=theme1,theme2'])
        self.assertEqual(options.search, ['dir1', 'dir2'])
        self.assertEqual(options.themes, ['theme1', 'theme2'])

    @patch.object(skool2html, 'run', mock_run)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_I_overrides_other_options(self):
        self.run_skool2html('-H -I Base=10 -l --ini Case=2 test.skool')
        options = run_args[1]
        self.assertEqual(options.params, ['Base=10', 'Case=2'])
        self.assertEqual(options.base, 10)
        self.assertEqual(options.case, 2)

    @patch.object(skool2html, 'run', mock_run)
    def test_option_I_overrides_config_read_from_file(self):
        ini = """
            [skool2html]
            Base=10
            Case=1
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        self.run_skool2html('-I Base=16 --ini Case=2 test.skool')
        options = run_args[1]
        self.assertEqual(options.params, ['Base=16', 'Case=2'])
        self.assertEqual(options.base, 16)
        self.assertEqual(options.case, 2)

    @patch.object(skool2html, 'run', mock_run)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_I_invalid_value(self):
        self.run_skool2html('-I Quiet=x test-I-invalid.skool')
        options = run_args[1]
        self.assertEqual(options.quiet, 0)

    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_show_config(self):
        output, error = self.run_skool2html('--show-config', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            [skool2html]
            AsmLabels=0
            AsmOnePage=0
            Base=0
            Case=0
            CreateLabels=0
            JoinCss=
            OutputDir=.
            Quiet=0
            RebuildImages=0
            Search=
            Theme=
            Time=0
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_show_config_read_from_file(self):
        ini = """
            [skool2html]
            AsmLabels=1
            OutputDir=html
            Quiet=1
            Theme=dark,wide
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        output, error = self.run_skool2html('--show-config', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            [skool2html]
            AsmLabels=1
            AsmOnePage=0
            Base=0
            Case=0
            CreateLabels=0
            JoinCss=
            OutputDir=html
            Quiet=1
            RebuildImages=0
            Search=
            Theme=dark,wide
            Time=0
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    @patch.object(skool2html, 'run', mock_run)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_var(self):
        self.run_skool2html('--var foo=1 test-var.skool')
        options = run_args[1]
        self.assertEqual(['foo=1'], options.variables)

    @patch.object(skool2html, 'run', mock_run)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_var_multiple(self):
        self.run_skool2html('--var bar=2 --var baz=3 test-var-multiple.skool')
        options = run_args[1]
        self.assertEqual(['bar=2', 'baz=3'], options.variables)

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_Config_RefFiles_parameter(self):
        ref1 = """
            [Game]
            Game=Foo
        """
        ref1file = self._write_ref_file(ref1)
        ref2 = """
            [ImageWriter]
            DefaultFormat=gif
        """
        ref2file = self._write_ref_file(ref2)
        ref = """
            [Config]
            RefFiles={};{}
        """.format(ref1file, ref2file)
        reffile = self._write_ref_file(ref)
        exp_reffiles = (reffile, ref1file, ref2file)
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html(skoolfile)
        self.assertEqual(error, '')
        self.assertIn('Using ref files: {}\n'.format(', '.join(exp_reffiles)), output)
        html_writer = write_disassembly_args[0]
        self.assertEqual(html_writer.game_vars['Game'], 'Foo')
        self.assertEqual(html_writer.image_writer.default_format, 'gif')

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_Config_RefFiles_parameter_contains_ref_file_already_parsed(self):
        skoolfile = self.write_text_file(suffix='.skool')
        prefix = skoolfile[:-6]
        ref1 = """
            [Paths]
            CodePath=code
        """
        ref1file = self._write_ref_file(ref1)
        ref2 = """
            [Game]
            Game=Bar
        """
        ref2file = self._write_ref_file(ref2, path='{}-auto.ref'.format(prefix))
        ref = """
            [Config]
            RefFiles={};{}
        """.format(ref1file, ref2file)
        reffile = self._write_ref_file(ref, path='{}.ref'.format(prefix))
        exp_reffiles = (reffile, ref2file, ref1file)
        output, error = self.run_skool2html(skoolfile)
        self.assertEqual(error, '')
        self.assertIn('Using ref files: {}\n'.format(', '.join(exp_reffiles)), output)
        html_writer = write_disassembly_args[0]
        self.assertEqual(html_writer.game_vars['Game'], 'Bar')
        self.assertEqual(html_writer.paths['CodePath'], 'code')

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_Config_RefFiles_parameter_contains_nonexistent_file(self):
        ref1file = self._write_ref_file('')
        ref2file = 'nonexistent.ref'
        ref = """
            [Config]
            RefFiles={};{}
        """.format(ref1file, ref2file)
        reffile = self._write_ref_file(ref)
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        with self.assertRaisesRegex(SkoolKitError, '{}: file not found'.format(ref2file)):
            self.run_skool2html('-d {} {}'.format(self.odir, skoolfile))

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_Config_RefFiles_parameter_via_option_c(self):
        ref = """
            [Game]
            Copyright=(C) 2015 me
        """
        reffile = self._write_ref_file(ref)
        skoolfile = self.write_text_file(suffix='.skool')
        output, error = self.run_skool2html('-c Config/RefFiles={} {}'.format(reffile, skoolfile))
        self.assertEqual(error, '')
        self.assertIn('Using ref file: {}\n'.format(reffile), output)
        html_writer = write_disassembly_args[0]
        self.assertEqual(html_writer.game_vars['Copyright'], '(C) 2015 me')

    @patch.object(skool2html, 'get_class', Mock(return_value=TestHtmlWriter))
    @patch.object(skool2html, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2html, 'write_disassembly', mock_write_disassembly)
    @patch.object(skool2html, 'get_config', mock_config)
    def test_option_c_modifies_extra_ref_files(self):
        extra_ref = """
            [Game]
            Game=Qux
        """
        extra_reffile = self._write_ref_file(extra_ref)
        ref = """
            [Config]
            RefFiles={}
        """.format(extra_reffile)
        reffile = self._write_ref_file(ref)
        skoolfile = self.write_text_file(path='{}.skool'.format(reffile[:-4]))
        output, error = self.run_skool2html('-c Game/Game=Baz {}'.format(skoolfile))
        self.assertEqual(error, '')
        self.assertIn('Using ref files: {}, {}\n'.format(reffile, extra_reffile), output)
        html_writer = write_disassembly_args[0]
        self.assertEqual(html_writer.game_vars['Game'], 'Baz')
