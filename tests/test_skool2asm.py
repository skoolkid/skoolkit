# -*- coding: utf-8 -*-
import os
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch
try:
    from importlib import invalidate_caches
except ImportError:
    invalidate_caches = lambda: None

from skoolkittest import SkoolKitTestCase
import skoolkit
from skoolkit import skool2asm, write_text, SkoolKitError, VERSION
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

    def write(self):
        pass

class TestAsmWriter:
    def __init__(self, *args):
        pass

    def write(self):
        write_text('OK')

class Skool2AsmTest(SkoolKitTestCase):
    def _get_asm(self, skool, args='', out_lines=True, err_lines=True, strip_cr=True):
        skoolfile = self.write_text_file(skool, suffix='.skool')
        output, error = self.run_skool2asm('{} {}'.format(args, skoolfile), out_lines, err_lines, strip_cr)
        self.assertEqual('Wrote ASM to stdout', error[-1][:19], 'Error(s) while running skool2asm.main() with args "{}"'.format(args))
        return output

    @patch.object(skool2asm, 'run', mock_run)
    def test_default_option_values(self):
        skoolfile = 'test.skool'
        skool2asm.main((skoolfile,))
        fname, options = run_args
        self.assertEqual(fname, skoolfile)
        self.assertFalse(options.crlf)
        self.assertIsNone(options.inst_width)
        self.assertFalse(options.quiet)
        self.assertFalse(options.tabs)
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

    def test_no_options(self):
        skool = '\n'.join((
            '; @start',
            '; @org=24593',
            '',
            "; Let's test some @ofix directives",
            'c24593 NOP',
            '; @ofix=LD A,C',
            ' 24594 LD A,B',
            '; @ofix-begin',
            ' 24595 LD B,A',
            '; @ofix+else',
            ' 24595 LD B,C',
            '; @ofix+end',
            '',
            "; Let's test some @bfix directives",
            'c24596 NOP',
            '; @bfix=LD C,B',
            ' 24597 LD C,A',
            '; @bfix-begin',
            ' 24598 LD D,A',
            '; @bfix+else',
            ' 24598 LD D,B',
            '; @bfix+end',
            '',
            "; Let's test the @rfix block directive",
            'c24599 NOP',
            '; @rfix-begin',
            ' 24600 LD E,A',
            '; @rfix+else',
            ' 24600 LD E,B',
            '; @rfix+end',
            '',
            "; Let's test the @ssub directive",
            '; @ssub=JP (HL)',
            'c24601 RET',
            '',
            "; Let's test the @rsub block directive",
            'c24602 NOP',
            '; @rsub-begin',
            ' 24603 LD A,0',
            '; @rsub+else',
            ' 24603 XOR A',
            '; @rsub+end',
        ))
        asm = self._get_asm(skool)
        self.assertEqual(asm[0], '  ORG 24593') # no crlf, tabs or lower case
        self.assertEqual(asm[4], '  LD A,B')    # No @ofix
        self.assertEqual(asm[5], '  LD B,A')    # @ofix-
        self.assertEqual(asm[9], '  LD C,A')    # No @bfix
        self.assertEqual(asm[10], '  LD D,A')   # @bfix-
        self.assertEqual(asm[14], '  LD E,A')   # @rfix-
        self.assertEqual(asm[17], '  RET')      # No @ssub
        self.assertEqual(asm[21], '  LD A,0')   # @rsub-

    def test_parse_stdin(self):
        skool = '\n'.join((
            '; @start',
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

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_E(self):
        for option, end in (('-E', 50000), ('--end', 60000)):
            output, error = self.run_skool2asm('-q {} {} test-E.skool'.format(option, end))
            self.assertEqual(error, '')
            self.assertEqual(mock_skool_parser.max_address, end)

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_options_S_and_E(self):
        start = 24576
        end = 32768
        output, error = self.run_skool2asm('-q -S {} -E {} test-S-and-E.skool'.format(start, end))
        self.assertEqual(error, '')
        self.assertEqual(mock_skool_parser.min_address, start)
        self.assertEqual(mock_skool_parser.max_address, end)

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

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_w(self):
        for option in ('-w', '--no-warnings'):
            output, error = self.run_skool2asm('-q {} test-w.skool'.format(option))
            self.assertEqual(mock_skool_parser.warnings, False)
            self.assertEqual({'warnings': '0'}, mock_asm_writer.properties)
            mock_asm_writer.properties = None

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_d(self):
        for option in ('-d', '--crlf'):
            output, error = self.run_skool2asm('-q {} test-d.skool'.format(option))
            self.assertEqual({'crlf': '1'}, mock_asm_writer.properties)
            mock_asm_writer.properties = None

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_t(self):
        for option in ('-t', '--tabs'):
            output, error = self.run_skool2asm('-q {} test-t.skool'.format(option))
            self.assertEqual({'tab': '1'}, mock_asm_writer.properties)
            mock_asm_writer.properties = None

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_l(self):
        for option in ('-l', '--lower'):
            output, error = self.run_skool2asm('-q {} test-l.skool'.format(option))
            self.assertEqual(mock_skool_parser.case, CASE_LOWER)
            mock_skool_parser.case = None
            self.assertTrue(mock_asm_writer.lower)
            mock_asm_writer.lower = None

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_u(self):
        for option in ('-u', '--upper'):
            output, error = self.run_skool2asm('-q {} test-u.skool'.format(option))
            self.assertEqual(mock_skool_parser.case, CASE_UPPER)
            mock_skool_parser.case = None
            self.assertFalse(mock_asm_writer.lower)
            mock_asm_writer.lower = True

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_D(self):
        for option in ('-D', '--decimal'):
            output, error = self.run_skool2asm('-q {} test-D.skool'.format(option))
            self.assertEqual(mock_skool_parser.base, BASE_10)
            mock_skool_parser.base = None

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_H(self):
        for option in ('-H', '--hex'):
            output, error = self.run_skool2asm('-q {} test-H.skool'.format(option))
            self.assertEqual(mock_skool_parser.base, BASE_16)
            mock_skool_parser.base = None

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_i(self):
        width = 30
        for option in ('-i', '--inst-width'):
            output, error = self.run_skool2asm('-q {} {} test-u.skool'.format(option, width))
            self.assertEqual({'instruction-width': width}, mock_asm_writer.properties)
            mock_asm_writer.properties = None

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_f(self):
        for option, value in (('-f', 1), ('--fixes', 2)):
            output, error = self.run_skool2asm('-q {} {} test-u.skool'.format(option, value))
            self.assertEqual(mock_skool_parser.fix_mode, value)
            mock_skool_parser.fix_mode = None

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_s(self):
        for option in ('-s', '--ssub'):
            output, error = self.run_skool2asm('-q {} test-s.skool'.format(option))
            self.assertEqual(mock_skool_parser.asm_mode, 2)
            mock_skool_parser.asm_mode = None

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_r(self):
        for option in ('-r', '--rsub'):
            output, error = self.run_skool2asm('-q {} test-r.skool'.format(option))
            self.assertEqual(mock_skool_parser.asm_mode, 3)
            mock_skool_parser.asm_mode = None

    @patch.object(skool2asm, 'SkoolParser', MockSkoolParser)
    @patch.object(skool2asm, 'AsmWriter', MockAsmWriter)
    def test_option_c(self):
        for option in ('-c', '--create-labels'):
            output, error = self.run_skool2asm('-q {} test-c.skool'.format(option))
            self.assertTrue(mock_skool_parser.create_labels)
            mock_skool_parser.create_labels = None

    def test_writer(self):
        skool = '\n'.join((
            '; @start',
            '; @writer={}',
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
        asm = self._get_asm(skool.format('test_skool2asm.TestAsmWriter'))
        self.assertEqual(asm[0], 'OK')

        # Test a writer in a module that is not in the search path
        mod = '\n'.join((
            'from skoolkit.skoolasm import AsmWriter',
            '',
            'class TestAsmWriter(AsmWriter):',
            '    def write(self):',
            "        self.write_line('{}')",
        ))
        message = 'Testing TestAsmWriter'
        module = self.write_text_file(mod.format(message), suffix='.py')
        invalidate_caches()
        module_path = os.path.dirname(module)
        module_name = os.path.basename(module)[:-3]
        writer = '{0}:{1}.TestAsmWriter'.format(module_path, module_name)
        asm = self._get_asm(skool.format(writer))
        self.assertEqual(asm[0], message)

    def test_option_W(self):
        skool = '\n'.join((
            '; @start',
            '; @writer=SomeWriterThatWillBeOverridden',
            '; Begin',
            'c32768 RET',
        ))
        mod = '\n'.join((
            'from skoolkit.skoolasm import AsmWriter',
            '',
            'class TestAsmWriter(AsmWriter):',
            '    def write(self):',
            "        self.write_line('{}')",
        ))
        message = 'Testing the -W option'
        module = self.write_text_file(mod.format(message), suffix='.py')
        invalidate_caches()
        module_path = os.path.dirname(module)
        module_name = os.path.basename(module)[:-3]
        writer = '{}:{}.TestAsmWriter'.format(module_path, module_name)
        asm = self._get_asm(skool, '-W {}'.format(writer))
        self.assertEqual(asm[0], message)

    def test_tab_property(self):
        skool = '\n'.join((
            '; @start',
            '; @set-{}={}',
            '; Data',
            'b40000 DEFB 0 ; Comment',
        ))
        property_name = 'tab'

        # tab=0
        asm = self._get_asm(skool.format(property_name, '0'))
        self.assertEqual(asm[1], '  DEFB 0                  ; Comment')

        # tab=1
        asm = self._get_asm(skool.format(property_name, '1'))
        self.assertEqual(asm[1], '\tDEFB 0                  ; Comment')

        # tab=0, overridden by '-t' option
        asm = self._get_asm(skool.format(property_name, '0'), '-t')
        self.assertEqual(asm[1], '\tDEFB 0                  ; Comment')

    def test_crlf_property(self):
        skool = '\n'.join((
            '; @start',
            '; @set-{}={}',
            '; Data',
            'b40000 DEFB 0 ; Comment',
        ))
        property_name = 'crlf'

        # crlf=0
        asm = self._get_asm(skool.format(property_name, '0'), strip_cr=False)
        self.assertEqual(asm[1], '  DEFB 0                  ; Comment')

        # crlf=1
        asm = self._get_asm(skool.format(property_name, '1'), strip_cr=False)
        self.assertEqual(asm[1], '  DEFB 0                  ; Comment\r')

        # crlf=0, overridden by '-d' option
        asm = self._get_asm(skool.format(property_name, '0'), '-d', strip_cr=False)
        self.assertEqual(asm[1], '  DEFB 0                  ; Comment\r')

    def test_warnings_property(self):
        skool = '\n'.join((
            '; @start',
            '; @set-warnings={}',
            '; Routine at 25000',
            ';',
            '; Used by the routine at 25000.',
            'c25000 JP 25000',
        ))

        # warnings=0 (SkoolParser warnings only)
        skoolfile = self.write_text_file(skool.format(0), suffix='.skool')
        output, error = self.run_skool2asm('-q {0}'.format(skoolfile))
        self.assertEqual(error, 'WARNING: Found no label for operand: 25000 JP 25000\n')

        # warnings=1 (SkoolParser and AsmWriter warnings)
        skoolfile = self.write_text_file(skool.format(1), suffix='.skool')
        output, error = self.run_skool2asm('-q {0}'.format(skoolfile), err_lines=True)
        self.assertEqual(len(error), 5)
        self.assertEqual(error[0], 'WARNING: Found no label for operand: 25000 JP 25000')
        self.assertEqual(error[1], 'WARNING: Comment contains address (25000) not converted to a label:')
        self.assertEqual(error[2], '; Routine at 25000')
        self.assertEqual(error[3], 'WARNING: Comment contains address (25000) not converted to a label:')
        self.assertEqual(error[4], '; Used by the routine at 25000.')

        # warnings=1, overridden by '-w' option (no warnings)
        skoolfile = self.write_text_file(skool.format(1), suffix='.skool')
        output, error = self.run_skool2asm('-q -w {0}'.format(skoolfile))
        self.assertEqual(error, '')

    def test_instruction_width_property(self):
        skool = '\n'.join((
            '; @start',
            '; @set-{}={}',
            '; Data',
            'b40000 DEFB 0 ; Comment',
        ))
        property_name = 'instruction-width'

        for value in (20, 25, 30, 'z'):
            try:
                width = int(value)
            except ValueError:
                width = 23
            asm = self._get_asm(skool.format(property_name, value))
            self.assertEqual(asm[1], '  {0} ; Comment'.format('DEFB 0'.ljust(width)))

        # instruction-width=27, overridden by '-i'
        for width in (20, 25, 30):
            asm = self._get_asm(skool.format(property_name, 27), '-i {}'.format(width))
            self.assertEqual(asm[1], '  {0} ; Comment'.format('DEFB 0'.ljust(width)))

if __name__ == '__main__':
    unittest.main()
