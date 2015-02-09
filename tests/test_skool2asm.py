# -*- coding: utf-8 -*-
import os
import unittest
import textwrap
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

def mock_run(*args):
    global run_args
    run_args = args

class TestAsmWriter:
    def __init__(self, *args):
        pass

    def write(self):
        write_text('OK')

class Skool2AsmTest(SkoolKitTestCase):
    @patch.object(skool2asm, 'run', mock_run)
    def test_default_option_values(self):
        skool2asm.main(('test.skool',))
        fname, options, parser_mode, writer_mode = run_args
        self.assertEqual(fname, 'test.skool')
        case = base = None
        asm_mode = 1
        warn = True
        fix_mode = 0
        create_labels = False
        self.assertFalse(options.crlf)
        self.assertIsNone(options.inst_width)
        self.assertFalse(options.quiet)
        self.assertFalse(options.tabs)
        self.assertIsNone(options.writer)
        self.assertEqual(parser_mode, (case, base, asm_mode, warn, fix_mode, create_labels))
        self.assertEqual(writer_mode, (False, warn))

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
        asm = self.get_asm(skool=skool)
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

    def test_option_q(self):
        skool = '\n'.join((
            '; @start',
            '; Do nothing',
            'c30000 RET',
        ))
        skoolfile = self.write_text_file(skool, suffix='.skool')
        for option in ('-q', '--quiet'):
            output, error = self.run_skool2asm('{0} {1}'.format(option, skoolfile))
            self.assertEqual(error, '')

    def test_option_w(self):
        skool = '\n'.join((
            '; @start',
            '; Routine at 24576',
            ';',
            '; Used by the routine at 24576.',
            'c24576 JP 24576',
        ))
        skoolfile = self.write_text_file(skool, suffix='.skool')
        for option in ('-w', '--no-warnings'):
            output, error = self.run_skool2asm('-q {0} {1}'.format(option, skoolfile))
            self.assertEqual(error, '')

    def test_option_d(self):
        skool = '\n'.join((
            '; @start',
            '; Begin',
            'c$8000 RET',
        ))
        for option in ('-d', '--crlf'):
            asm = self.get_asm(option, skool, strip_cr=False)
            self.assertEqual(asm[0][-1], '\r')

    def test_option_t(self):
        skool = '\n'.join((
            '; @start',
            '; @org=24576',
            '',
            '; Routine',
            'c24576 RET',
        ))
        for option in ('-t', '--tabs'):
            asm = self.get_asm(option, skool)
            self.assertEqual(asm[0], '\tORG 24576')
            self.assertEqual(asm[3], '\tRET')

    def test_option_l(self):
        skool = '\n'.join((
            '; @start',
            '; @org=24576',
            '',
            '; Routine',
            '; @label=DOSTUFF',
            'c24576 NOP',
        ))
        for option in ('-l', '--lower'):
            asm = self.get_asm(option, skool)
            self.assertEqual(asm[0], '  org 24576')
            self.assertEqual(asm[3], 'DOSTUFF:') # Labels unaffected
            self.assertEqual(asm[4], '  nop')

    def test_option_u(self):
        skool = '\n'.join((
            '; @start',
            '; Start the game',
            '; @label=start',
            'c49152 nop',
        ))
        for option in ('-u', '--upper'):
            asm = self.get_asm(option, skool)
            self.assertEqual(asm[1], 'start:') # Labels unaffected
            self.assertEqual(asm[2], '  NOP')

    def test_option_D(self):
        skool = '\n'.join((
            '; @start',
            '; Begin',
            'c$8000 JP $ABCD',
        ))
        for option in ('-D', '--decimal'):
            asm = self.get_asm(option, skool)
            self.assertEqual(asm[1], '  JP 43981')

    def test_option_H(self):
        skool = '\n'.join((
            '; @start',
            '; Begin',
            'c$8000 JP 56506',
        ))
        for option in ('-H', '--hex'):
            asm = self.get_asm(option, skool)
            self.assertEqual(asm[1], '  JP $DCBA')

    def test_option_i(self):
        skool = '\n'.join((
            '; @start',
            '; Do nothing',
            'c50000 RET ; Return',
        ))
        width = 30
        for option in ('-i', '--inst-width'):
            asm = self.get_asm('{0} {1}'.format(option, width), skool)
            self.assertEqual(asm[1].find(';'), width + 3)

    def test_option_f0(self):
        skool = '\n'.join((
            '; @start',
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
        ))
        for option in ('-f', '--fixes'):
            asm = self.get_asm('{0} 0'.format(option), skool)
            self.assertEqual(asm[2], '  LD A,B')
            self.assertEqual(asm[3], '  LD B,A')
            self.assertEqual(asm[7], '  LD C,A')
            self.assertEqual(asm[8], '  LD D,A')
            self.assertEqual(asm[12], '  LD E,A')

    def test_option_f1(self):
        skool = '\n'.join((
            '; @start',
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
        ))
        for option in ('-f', '--fixes'):
            asm = self.get_asm('{0} 1'.format(option), skool)
            self.assertEqual(asm[2], '  LD A,C')
            self.assertEqual(asm[3], '  LD B,C')
            self.assertEqual(asm[7], '  LD C,A')
            self.assertEqual(asm[8], '  LD D,A')
            self.assertEqual(asm[12], '  LD E,A')

    def test_option_f2(self):
        skool = '\n'.join((
            '; @start',
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
        ))
        for option in ('-f', '--fixes'):
            asm = self.get_asm('{0} 2'.format(option), skool)
            self.assertEqual(asm[2], '  LD A,C')
            self.assertEqual(asm[3], '  LD B,C')
            self.assertEqual(asm[7], '  LD C,B')
            self.assertEqual(asm[8], '  LD D,B')
            self.assertEqual(asm[12], '  LD E,A')

    def test_option_f3(self):
        skool = '\n'.join((
            '; @start',
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
        ))
        for option in ('-f', '--fixes'):
            asm = self.get_asm('{0} 3'.format(option), skool)
            self.assertEqual(asm[2], '  LD A,C')
            self.assertEqual(asm[3], '  LD B,C')
            self.assertEqual(asm[7], '  LD C,B')
            self.assertEqual(asm[8], '  LD D,B')
            self.assertEqual(asm[12], '  LD E,B')

    def test_option_s(self):
        skool = '\n'.join((
            '; @start',
            "; Let's test the @ssub directive",
            '; @ssub=JP (HL)',
            'c24601 RET',
        ))
        for option in ('-s', '--ssub'):
            asm = self.get_asm(option, skool)
            self.assertEqual(asm[1], '  JP (HL)')

    def test_option_r(self):
        skool = '\n'.join((
            '; @start',
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
        for option in ('-r', '--rsub'):
            asm = self.get_asm(option, skool)
            self.assertEqual(asm[2], '  LD A,C')   # @ofix
            self.assertEqual(asm[3], '  LD B,C')   # @ofix+
            self.assertEqual(asm[7], '  LD C,A')   # No @bfix
            self.assertEqual(asm[8], '  LD D,A')   # @bfix-
            self.assertEqual(asm[12], '  LD E,A')  # @rfix-
            self.assertEqual(asm[15], '  JP (HL)') # @ssub
            self.assertEqual(asm[19], '  XOR A')   # @rsub+

    def test_option_c(self):
        skool = '\n'.join((
            '; @start',
            '; Begin',
            'c32768 JR 32770',
            '',
            '; End',
            'c32770 JR 32768',
        ))
        for option in ('-c', '--create-labels'):
            asm = self.get_asm(option, skool)
            self.assertEqual(asm[1], 'L32768:')
            self.assertEqual(asm[2], '  JR L32770')
            self.assertEqual(asm[5], 'L32770:')
            self.assertEqual(asm[6], '  JR L32768')

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
        asm = self.get_asm(skool=skool.format('test_skool2asm.TestAsmWriter'))
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
        asm = self.get_asm(skool=skool.format(writer))
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
        asm = self.get_asm('-W {}'.format(writer), skool)
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
        asm = self.get_asm(skool=skool.format(property_name, '0'))
        self.assertEqual(asm[1], '  DEFB 0                  ; Comment')

        # tab=1
        asm = self.get_asm(skool=skool.format(property_name, '1'))
        self.assertEqual(asm[1], '\tDEFB 0                  ; Comment')

        # tab=0, overridden by '-t' option
        asm = self.get_asm('-t', skool=skool.format(property_name, '0'))
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
        asm = self.get_asm(skool=skool.format(property_name, '0'), strip_cr=False)
        self.assertEqual(asm[1], '  DEFB 0                  ; Comment')

        # crlf=1
        asm = self.get_asm(skool=skool.format(property_name, '1'), strip_cr=False)
        self.assertEqual(asm[1], '  DEFB 0                  ; Comment\r')

        # crlf=0, overridden by '-d' option
        asm = self.get_asm('-d', skool=skool.format(property_name, '0'), strip_cr=False)
        self.assertEqual(asm[1], '  DEFB 0                  ; Comment\r')

    def test_indent_property(self):
        skool = '\n'.join((
            '; @start',
            '; @set-{}={}',
            '; Data',
            'b40000 DEFB 0 ; Comment',
        ))
        for indent in (1, 5, 'x'):
            asm = self.get_asm(skool=skool.format('indent', indent))
            try:
                indent_size = int(indent)
            except ValueError:
                indent_size = 2
            self.assertEqual(asm[1], '{0}DEFB 0                  ; Comment'.format(' ' * indent_size))

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
            asm = self.get_asm(skool=skool.format(property_name, value))
            self.assertEqual(asm[1], '  {0} ; Comment'.format('DEFB 0'.ljust(width)))

        # instruction-width=27, overridden by '-i'
        for width in (20, 25, 30):
            asm = self.get_asm('-i {0}'.format(width), skool=skool.format(property_name, 27))
            self.assertEqual(asm[1], '  {0} ; Comment'.format('DEFB 0'.ljust(width)))

    def test_line_width_property(self):
        skool = '\n'.join((
            '; @start',
            '; @set-line-width={}',
            '; Routine',
            'c49152 RET ; This is a fairly long instruction comment, which makes it suitable',
            '           ; for testing various line widths',
        ))
        indent = ' ' * 25
        instruction = '  RET'.ljust(len(indent))
        comment = 'This is a fairly long instruction comment, which makes it suitable for testing various line widths'
        for width in (65, 80, 95, 'x'):
            asm = self.get_asm(skool=skool.format(width))
            try:
                line_width = int(width)
            except ValueError:
                line_width = 79
            comment_lines = textwrap.wrap(comment, line_width - len(instruction) - 3)
            exp_lines = [instruction + ' ; ' + comment_lines[0]]
            for comment_line in comment_lines[1:]:
                exp_lines.append('{0} ; {1}'.format(indent, comment_line))
            for line_no, exp_line in enumerate(exp_lines, 1):
                self.assertEqual(asm[line_no], exp_line)

    def test_comment_width_min_property(self):
        skool = '\n'.join((
            '; @start',
            '; @set-comment-width-min={}',
            '; Data',
            'c35000 DEFB 255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255 ; {}',
        ))
        line_width = 79
        comment = 'This comment should have the designated minimum width'
        for width in (10, 15, 20, 'x'):
            asm = self.get_asm(skool=skool.format(width, comment))
            try:
                comment_width_min = int(width)
            except ValueError:
                comment_width_min = 10
            instruction, sep, comment_line = asm[1].partition(';')
            instr_width = len(instruction)
            indent = ' ' * instr_width
            comment_width = line_width - 2 - instr_width
            comment_lines = textwrap.wrap(comment, max((comment_width, comment_width_min)))
            exp_lines = [instruction + '; ' + comment_lines[0]]
            for comment_line in comment_lines[1:]:
                exp_lines.append('{0}; {1}'.format(indent, comment_line))
            for line_no, exp_line in enumerate(exp_lines, 1):
                self.assertEqual(asm[line_no], exp_line)

    def test_wrap_column_width_min_property(self):
        skool = '\n'.join((
            '; @start',
            '; @set-wrap-column-width-min={}',
            '; Routine',
            ';',
            '; #TABLE(,:w)',
            '; {{ {} | An unwrappable column whose contents extend the table width beyond 80 characters }}',
            '; TABLE#',
            'c40000 RET',
        ))
        text = 'This wrappable text should have the designated minimum width'
        for width in (10, 18, 26, 'Z'):
            asm = self.get_asm(skool=skool.format(width, text))
            try:
                wrap_column_width_min = int(width)
            except ValueError:
                wrap_column_width_min = 10
            text_lines = textwrap.wrap(text, wrap_column_width_min)
            actual_width = max([len(line) for line in text_lines])
            exp_lines = ['; | {} |'.format(line.ljust(actual_width)) for line in text_lines]
            for line_no, exp_line in enumerate(exp_lines, 3):
                self.assertEqual(asm[line_no][:len(exp_line)], exp_line)

    def test_no_html_escape(self):
        skool = '\n'.join((
            '; @start',
            '; Text',
            't24576 DEFM "&<>" ; a <= b & b >= c',
        ))
        asm = self.get_asm(skool=skool)
        self.assertEqual(asm[1], '  DEFM "&<>"              ; a <= b & b >= c')

    def test_macro_expansion(self):
        skool = '\n'.join((
            '; @start',
            '; Data',
            'b$6003 DEFB 123 ; #REGa=0',
            " $6004 DEFB $23 ; '#'",
        ))
        asm = self.get_asm(skool=skool)
        self.assertEqual(asm[1], '  DEFB 123                ; A=0')
        self.assertEqual(asm[2], "  DEFB $23                ; '#'")

    def get_asm(self, args='', skool='', out_lines=True, err_lines=True, strip_cr=True):
        skoolfile = self.write_text_file(skool, suffix='.skool')
        output, error = self.run_skool2asm('{0} {1}'.format(args, skoolfile), out_lines, err_lines, strip_cr)
        self.assertEqual('Wrote ASM to stdout', error[-1][:19], 'Error(s) while running skool2asm.main() with args "{0}"'.format(args))
        return output

if __name__ == '__main__':
    unittest.main()
