# -*- coding: utf-8 -*-
import os
import unittest
try:
    from mock import patch, Mock
except ImportError:
    from unittest.mock import patch, Mock

from skoolkittest import SkoolKitTestCase
import skoolkit
from skoolkit import skool2asm, SkoolKitError, VERSION
from skoolkit.skoolparser import BASE_10, BASE_16, CASE_LOWER, CASE_UPPER

def mock_run(*args):
    global run_args
    run_args = args

class MockSkoolParser:
    def __init__(self, skoolfile, case, base, asm_mode, warnings, fix_mode, html,
                 create_labels, asm_labels, min_address, max_address):
        global mock_skool_parser
        mock_skool_parser = self
        self.skoolfile = skoolfile
        self.case = case
        self.base = base
        self.asm_mode = asm_mode
        self.warnings = warnings
        self.fix_mode = fix_mode
        self.html = html
        self.create_labels = create_labels
        self.asm_labels = asm_labels
        self.min_address = min_address
        self.max_address = max_address
        self.properties = {}
        self.asm_writer_class = ''

class MockAsmWriter:
    def __init__(self, parser, properties, lower):
        global mock_asm_writer
        mock_asm_writer = self
        self.parser = parser
        self.properties = properties
        self.lower = lower
        self.wrote = False

    def write(self):
        self.wrote = True

class Skool2AsmTest(SkoolKitTestCase):
    def setUp(self):
        global mock_skool_parser, mock_asm_writer
        SkoolKitTestCase.setUp(self)
        mock_skool_parser = None
        mock_asm_writer = None

    @patch.object(skool2asm, 'run', mock_run)
    def test_default_option_values(self):
        skoolfile = 'test.skool'
        skool2asm.main((skoolfile,))
        fname, options = run_args
        self.assertEqual(fname, skoolfile)
        self.assertFalse(options.quiet)
        self.assertIsNone(options.writer)
        self.assertIsNone(options.case)
        self.assertIsNone(options.base)
        self.assertEqual(options.asm_mode, 1)
        self.assertTrue(options.warn)
        self.assertEqual(options.fix_mode, 0)
        self.assertFalse(options.create_labels)
        self.assertEqual(options.start, 0)
        self.assertEqual(options.end, 65536)

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_default_option_values_are_passed(self):
        skoolfile = 'test.skool'
        skool2asm.main((skoolfile,))

        self.assertEqual(mock_skool_parser.skoolfile, skoolfile)
        self.assertIsNone(mock_skool_parser.case)
        self.assertIsNone(mock_skool_parser.base)
        self.assertEqual(mock_skool_parser.asm_mode, 1)
        self.assertTrue(mock_skool_parser.warnings)
        self.assertEqual(mock_skool_parser.fix_mode, 0)
        self.assertFalse(mock_skool_parser.html)
        self.assertFalse(mock_skool_parser.create_labels)
        self.assertTrue(mock_skool_parser.asm_labels)
        self.assertEqual(mock_skool_parser.min_address, 0)
        self.assertEqual(mock_skool_parser.max_address, 65536)

        self.assertIs(mock_asm_writer.parser, mock_skool_parser)
        self.assertFalse(mock_asm_writer.lower)
        self.assertEqual({}, mock_asm_writer.properties)
        self.assertTrue(mock_asm_writer.wrote)

    def test_no_arguments(self):
        output, error = self.run_skool2asm('-x', catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: skool2asm.py'))

    def test_invalid_option(self):
        output, error = self.run_skool2asm('-x', catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: skool2asm.py'))

    def test_invalid_option_value(self):
        for args in ('-i ABC', '-f +'):
            output, error = self.run_skool2asm(args, catch_exit=2)
            self.assertEqual(len(output), 0)
            self.assertTrue(error.startswith('usage: skool2asm.py'))

    def test_parse_stdin(self):
        skool = '\n'.join((
            '@start',
            '; Do nothing',
            'c60000 RET'
        ))
        self.write_stdin(skool)
        output, error = self.run_skool2asm('-', err_lines=True)
        self.assertEqual(error[0][:12], 'Parsed stdin')

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_S(self):
        for option, start in (('-S', 30000), ('--start', 40000)):
            output, error = self.run_skool2asm('-q {} {} test-S.skool'.format(option, start))
            self.assertEqual(error, '')
            self.assertEqual(mock_skool_parser.min_address, start)
            self.assertTrue(mock_asm_writer.wrote)
            mock_asm_writer.wrote = False

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_E(self):
        for option, end in (('-E', 50000), ('--end', 60000)):
            output, error = self.run_skool2asm('-q {} {} test-E.skool'.format(option, end))
            self.assertEqual(error, '')
            self.assertEqual(mock_skool_parser.max_address, end)
            self.assertTrue(mock_asm_writer.wrote)
            mock_asm_writer.wrote = False

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_options_S_and_E(self):
        start = 24576
        end = 32768
        output, error = self.run_skool2asm('-q -S {} -E {} test-S-and-E.skool'.format(start, end))
        self.assertEqual(error, '')
        self.assertEqual(mock_skool_parser.min_address, start)
        self.assertEqual(mock_skool_parser.max_address, end)
        self.assertTrue(mock_asm_writer.wrote)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_skool2asm(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

    def test_option_p(self):
        for option in ('-p', '--package-dir'):
            output, error = self.run_skool2asm(option, catch_exit=0)
            self.assertEqual(error, '')
            self.assertEqual(len(output), 1)
            self.assertEqual(output[0], os.path.dirname(skoolkit.__file__))

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_q(self):
        for option in ('-q', '--quiet'):
            output, error = self.run_skool2asm('{} test-q.skool'.format(option))
            self.assertEqual(error, '')
            self.assertTrue(mock_asm_writer.wrote)
            mock_asm_writer.wrote = False

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_w(self):
        for option in ('-w', '--no-warnings'):
            output, error = self.run_skool2asm('-q {} test-w.skool'.format(option))
            self.assertEqual(mock_skool_parser.warnings, False)
            self.assertEqual({'warnings': '0'}, mock_asm_writer.properties)
            self.assertTrue(mock_asm_writer.wrote)
            mock_asm_writer.properties = None
            mock_asm_writer.wrote = False

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_l(self):
        for option in ('-l', '--lower'):
            output, error = self.run_skool2asm('-q {} test-l.skool'.format(option))
            self.assertEqual(mock_skool_parser.case, CASE_LOWER)
            mock_skool_parser.case = None
            self.assertTrue(mock_asm_writer.lower)
            self.assertTrue(mock_asm_writer.wrote)
            mock_asm_writer.lower = None
            mock_asm_writer.wrote = False

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_u(self):
        for option in ('-u', '--upper'):
            output, error = self.run_skool2asm('-q {} test-u.skool'.format(option))
            self.assertEqual(mock_skool_parser.case, CASE_UPPER)
            mock_skool_parser.case = None
            self.assertFalse(mock_asm_writer.lower)
            self.assertTrue(mock_asm_writer.wrote)
            mock_asm_writer.lower = True
            mock_asm_writer.wrote = False

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_D(self):
        for option in ('-D', '--decimal'):
            output, error = self.run_skool2asm('-q {} test-D.skool'.format(option))
            self.assertEqual(mock_skool_parser.base, BASE_10)
            self.assertTrue(mock_asm_writer.wrote)
            mock_skool_parser.base = None
            mock_asm_writer.wrote = False

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_H(self):
        for option in ('-H', '--hex'):
            output, error = self.run_skool2asm('-q {} test-H.skool'.format(option))
            self.assertEqual(mock_skool_parser.base, BASE_16)
            self.assertTrue(mock_asm_writer.wrote)
            mock_skool_parser.base = None
            mock_asm_writer.wrote = False

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_f(self):
        for option, value in (('-f', 1), ('--fixes', 2)):
            output, error = self.run_skool2asm('-q {} {} test-u.skool'.format(option, value))
            self.assertEqual(mock_skool_parser.fix_mode, value)
            self.assertTrue(mock_asm_writer.wrote)
            mock_skool_parser.fix_mode = None
            mock_asm_writer.wrote = False

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_s(self):
        for option in ('-s', '--ssub'):
            output, error = self.run_skool2asm('-q {} test-s.skool'.format(option))
            self.assertEqual(mock_skool_parser.asm_mode, 2)
            self.assertTrue(mock_asm_writer.wrote)
            mock_skool_parser.asm_mode = None
            mock_asm_writer.wrote = False

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_r(self):
        for option in ('-r', '--rsub'):
            output, error = self.run_skool2asm('-q {} test-r.skool'.format(option))
            self.assertEqual(mock_skool_parser.asm_mode, 3)
            self.assertTrue(mock_asm_writer.wrote)
            mock_skool_parser.asm_mode = None
            mock_asm_writer.wrote = False

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_c(self):
        for option in ('-c', '--create-labels'):
            output, error = self.run_skool2asm('-q {} test-c.skool'.format(option))
            self.assertTrue(mock_skool_parser.create_labels)
            self.assertTrue(mock_asm_writer.wrote)
            mock_skool_parser.create_labels = None
            mock_asm_writer.wrote = False

    def test_writer(self):
        skool = '\n'.join((
            '@start',
            '@writer={}',
            '; Begin',
            'c24576 RET',
        ))

        # Test a writer with no module or package name
        writer = 'AbsoluteAsmWriter'
        skoolfile = self.write_text_file(skool.format(writer), suffix='.skool')
        with self.assertRaisesRegexp(SkoolKitError, "Invalid class name: '{}'".format(writer)):
            self.run_skool2asm(skoolfile)

        # Test a writer in a nonexistent module
        writer = 'nonexistentmodule.AsmWriter'
        skoolfile = self.write_text_file(skool.format(writer), suffix='.skool')
        with self.assertRaisesRegexp(SkoolKitError, "Failed to import class nonexistentmodule.AsmWriter: No module named '?nonexistentmodule'?"):
            self.run_skool2asm(skoolfile)

        # Test a writer that doesn't exist
        writer = 'test_skool2asm.NonexistentAsmWriter'
        skoolfile = self.write_text_file(skool.format(writer), suffix='.skool')
        with self.assertRaisesRegexp(SkoolKitError, "No class named 'NonexistentAsmWriter' in module 'test_skool2asm'"):
            self.run_skool2asm(skoolfile)

        # Test a writer that exists
        skoolfile = self.write_text_file(skool.format('test_skool2asm.MockAsmWriter'), suffix='.skool')
        self.run_skool2asm(skoolfile)
        self.assertTrue(mock_asm_writer.wrote)

    @patch.object(skool2asm, 'get_class', Mock(return_value=MockAsmWriter))
    def test_option_W(self):
        skool = '\n'.join((
            '@start',
            '@writer=SomeWriterThatWillBeOverridden',
            'c32768 RET',
        ))
        skoolfile = self.write_text_file(skool, suffix='.skool')
        for option in ('-W', '--writer'):
            self.run_skool2asm('{} dummy_value {}'.format(option, skoolfile))
            self.assertTrue(mock_asm_writer.wrote)
            mock_asm_writer.wrote = False

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_P(self):
        for option, prop, value in (('-P', 'crlf', '1'), ('--set', 'bullet', '+')):
            output, error = self.run_skool2asm('-q {} {}={} test-P.skool'.format(option, prop, value))
            self.assertEqual({prop: value}, mock_asm_writer.properties)
            self.assertTrue(mock_asm_writer.wrote)
            mock_asm_writer.properties = None
            mock_asm_writer.wrote = False

    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_tab_property(self):
        skool = '\n'.join((
            '@start',
            '@set-tab={}',
            '; Data',
            'b40000 DEFB 0 ; Comment',
        ))

        for tab in ('0', '1'):
            skoolfile = self.write_text_file(skool.format(tab), suffix='.skool')
            self.run_skool2asm(skoolfile)
            self.assertEqual(mock_asm_writer.properties['tab'], tab)
            self.assertTrue(mock_asm_writer.wrote)
            mock_asm_writer.properties = None
            mock_asm_writer.wrote = False

        # tab=0, overridden by --set option
        tab = '0'
        skoolfile = self.write_text_file(skool.format(tab), suffix='.skool')
        self.run_skool2asm('--set tab=1 {}'.format(skoolfile))
        self.assertEqual(mock_asm_writer.properties['tab'], '1')
        self.assertTrue(mock_asm_writer.wrote)

    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_crlf_property(self):
        skool = '\n'.join((
            '@start',
            '@set-crlf={}',
            '; Data',
            'b40000 DEFB 0 ; Comment',
        ))

        for crlf in ('0', '1'):
            skoolfile = self.write_text_file(skool.format(crlf), suffix='.skool')
            self.run_skool2asm(skoolfile)
            self.assertEqual(mock_asm_writer.properties['crlf'], crlf)
            self.assertTrue(mock_asm_writer.wrote)
            mock_asm_writer.properties = None
            mock_asm_writer.wrote = False

        # crlf=0, overridden by --set option
        crlf = '0'
        skoolfile = self.write_text_file(skool.format(crlf), suffix='.skool')
        self.run_skool2asm('--set crlf=1 {}'.format(skoolfile))
        self.assertEqual(mock_asm_writer.properties['crlf'], '1')
        self.assertTrue(mock_asm_writer.wrote)

    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_warnings_property(self):
        skool = '\n'.join((
            '@start',
            '@set-warnings={}',
            '; Routine at 25000',
            ';',
            '; Used by the routine at 25000.',
            'c25000 JP 25000',
        ))

        for value in ('0', '1'):
            skoolfile = self.write_text_file(skool.format(value), suffix='.skool')
            self.run_skool2asm(skoolfile)
            self.assertEqual(mock_asm_writer.properties['warnings'], value)
            self.assertTrue(mock_asm_writer.wrote)
            mock_asm_writer.properties = None
            mock_asm_writer.wrote = False

        # warnings=1, overridden by '-w' option
        skoolfile = self.write_text_file(skool.format(1), suffix='.skool')
        output, error = self.run_skool2asm('-w {}'.format(skoolfile))
        self.assertEqual(mock_asm_writer.properties['warnings'], '0')
        self.assertTrue(mock_asm_writer.wrote)

    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_instruction_width_property(self):
        skool = '\n'.join((
            '@start',
            '@set-instruction-width={}',
            '; Data',
            'b40000 DEFB 0 ; Comment',
        ))

        for value in ('20', '25'):
            skoolfile = self.write_text_file(skool.format(value), suffix='.skool')
            self.run_skool2asm(skoolfile)
            self.assertEqual(mock_asm_writer.properties['instruction-width'], value)
            self.assertTrue(mock_asm_writer.wrote)
            mock_asm_writer.properties = None
            mock_asm_writer.wrote = False

        # instruction-width=27, overridden by --set option
        skoolfile = self.write_text_file(skool.format(27), suffix='.skool')
        width = '20'
        self.run_skool2asm('--set instruction-width={} {}'.format(width, skoolfile))
        self.assertEqual(mock_asm_writer.properties['instruction-width'], width)
        self.assertTrue(mock_asm_writer.wrote)

if __name__ == '__main__':
    unittest.main()
