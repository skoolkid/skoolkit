# -*- coding: utf-8 -*-
import re
import unittest
import textwrap

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolParsingError
from skoolkit.skoolasm import AsmWriter
from skoolkit.skoolparser import SkoolParser, CASE_LOWER, CASE_UPPER, BASE_10, BASE_16

ERROR_PREFIX = 'Error while parsing #{0} macro'

def get_chr(code):
    try:
        return unichr(code).encode('utf-8')
    except NameError:
        return chr(code)

class AsmWriterTest(SkoolKitTestCase):
    def _get_writer(self, skool='', crlf=False, tab=False, case=None, base=None, instr_width=23, warn=False, asm_mode=1, fix_mode=0):
        skoolfile = self.write_text_file(skool, suffix='.skool')
        skool_parser = SkoolParser(skoolfile, case=case, base=base, asm_mode=asm_mode, fix_mode=fix_mode)
        properties = dict(skool_parser.properties)
        properties['crlf'] = '1' if crlf else '0'
        properties['tab'] = '1' if tab else '0'
        properties['instruction-width'] = instr_width
        properties['warnings'] = '1' if warn else '0'
        return AsmWriter(skool_parser, properties, case == CASE_LOWER)

    def _get_asm(self, skool, crlf=False, tab=False, case=None, base=None, instr_width=23, warn=False, asm_mode=1, fix_mode=0):
        self.clear_streams()
        writer = self._get_writer(skool, crlf, tab, case, base, instr_width, warn, asm_mode, fix_mode)
        writer.write()
        asm = self.out.getvalue().split('\n')[:-1]
        if warn:
            return asm, self.err.getvalue().split('\n')[:-1]
        return asm

    def assert_error(self, writer, text, error_msg=None, prefix=None):
        with self.assertRaises(SkoolParsingError) as cm:
            writer.expand(text)
        if error_msg:
            if prefix:
                error_msg = '{}: {}'.format(prefix, error_msg)
            self.assertEqual(cm.exception.args[0], error_msg)

    def _test_unsupported_macro(self, writer, text, error_msg=None):
        search = re.search('#[A-Z]+', text)
        macro = search.group()

        # handle_unsupported_macros = 0
        writer.handle_unsupported_macros = 0
        self.assert_error(writer, text, 'Found unsupported macro: {}'.format(macro))

        # handle_unsupported_macros = 1
        writer.handle_unsupported_macros = 1
        if error_msg is None:
            prefix = 'abc '
            suffix = ' xyz'
            output = writer.expand(prefix + text + suffix)
            self.assertEqual(output, prefix + suffix)
        else:
            prefix = ERROR_PREFIX.format(macro[1:])
            self.assert_error(writer, text, error_msg, prefix)

    def _test_reference_macro(self, macro, def_link_text):
        writer = self._get_writer()
        for link_text in ('', '()', '(testing)', '(testing (nested) parentheses)'):
            for anchor in ('', '#name', '#foo$bar'):
                output = writer.expand('#{}{}{}'.format(macro, anchor, link_text))
                self.assertEqual(output, link_text[1:-1] or def_link_text)

        for suffix in ',;:.!)?/"\'':
            output = writer.expand('#{}#name{}'.format(macro, suffix))
            self.assertEqual(output, def_link_text + suffix)

    def _test_invalid_reference_macro(self, macro):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format(macro)

        # Non-existent item
        self.assert_error(writer, '#{}#nonexistentItem()'.format(macro), "Cannot determine title of item 'nonexistentItem'", prefix)

        # Malformed item name
        self.assert_error(writer, '#{}bad#name()'.format(macro), "Malformed macro: #{}bad#name()".format(macro), prefix)

        # No item name
        self.assert_error(writer, '#{}#(foo)'.format(macro), "No item name: #{}#(foo)".format(macro), prefix)

        # No closing bracket
        self.assert_error(writer, '#{}(foo'.format(macro), "No closing bracket: (foo", prefix)

    def _test_call(self, arg1, arg2, arg3=None):
        # Method used to test the #CALL macro
        return str((arg1, arg2, arg3))

    def _test_call_no_retval(self, *args):
        return

    def test_macros_are_expanded(self):
        skool = '\n'.join((
            '@start',
            '; Data',
            'b$6003 DEFB 123 ; #REGa=0',
            " $6004 DEFB $23 ; '#'",
        ))
        asm = self._get_asm(skool)
        self.assertEqual(asm[1], '  DEFB 123                ; A=0')
        self.assertEqual(asm[2], "  DEFB $23                ; '#'")

    def test_macro_bug(self):
        self._test_reference_macro('BUG', 'bug')

    def test_macro_call(self):
        writer = self._get_writer(warn=True)
        writer.test_call = self._test_call

        # All arguments given
        output = writer.expand('#CALL:test_call(10,t,5)')
        self.assertEqual(output, self._test_call(10, 't', 5))

        # One argument omitted
        output = writer.expand('#CALL:test_call(7,,test2)')
        self.assertEqual(output, self._test_call(7, None, 'test2'))

        # No return value
        writer.test_call_no_retval = self._test_call_no_retval
        output = writer.expand('#CALL:test_call_no_retval(1,2)')
        self.assertEqual(output, '')

        # Unknown method
        method_name = 'nonexistent_method'
        output = writer.expand('#CALL:{0}(0)'.format(method_name))
        self.assertEqual(output, '')
        self.assertEqual(self.err.getvalue().split('\n')[0], 'WARNING: Unknown method name in #CALL macro: {0}'.format(method_name))

    def test_macro_call_invalid(self):
        writer = self._get_writer()
        writer.test_call = self._test_call
        prefix = ERROR_PREFIX.format('CALL')

        # No parameters
        self.assert_error(writer, '#CALL', 'No parameters', prefix)

        # Malformed #CALL macro
        self.assert_error(writer, '#CALLtest_call(5,s)', 'Malformed macro: #CALLt...', prefix)

        # No method name
        self.assert_error(writer, '#CALL:(0)', 'No method name', prefix)

        # #CALL a non-method
        writer.var = 'x'
        self.assert_error(writer, '#CALL:var(0)', 'Uncallable method name: var', prefix)

        # No argument list
        self.assert_error(writer, '#CALL:test_call', 'No argument list specified: #CALL:test_call', prefix)

        # No closing bracket
        self.assert_error(writer, '#CALL:test_call(1,2', 'No closing bracket: (1,2', prefix)

        # Not enough parameters
        self.assert_error(writer, '#CALL:test_call(1)')

        # Too many parameters
        self.assert_error(writer, '#CALL:test_call(1,2,3,4)')

    def test_macro_chr(self):
        writer = self._get_writer()

        output = writer.expand('#CHR169')
        self.assertEqual(output, get_chr(169))

        output = writer.expand('#CHR(163)1985')
        self.assertEqual(output, '{0}1985'.format(get_chr(163)))

    def test_macro_chr_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('CHR')

        # No parameter
        self.assert_error(writer, '#CHR', 'No parameters (expected 1)', prefix)

        # Blank parameter
        self.assert_error(writer, '#CHR()', "Invalid integer: ''", prefix)

        # Invalid parameter (1)
        self.assert_error(writer, '#CHR2$', "Cannot parse integer '2$' in parameter string: '2$'", prefix)

        # Invalid parameter (2)
        self.assert_error(writer, '#CHR(x,y)', "Invalid integer: 'x,y'", prefix)

        # No closing bracket
        self.assert_error(writer, '#CHR(2 ...', 'No closing bracket: (2 ...', prefix)

    def test_macro_d(self):
        skool = '\n'.join((
            '@start',
            '',
            '; First routine',
            'c32768 RET',
            '',
            '; Second routine',
            'c32769 RET',
            '',
            'c32770 RET',
        ))
        writer = self._get_writer(skool)

        output = writer.expand('#D32768')
        self.assertEqual(output, 'First routine')

        output = writer.expand('#D$8001')
        self.assertEqual(output, 'Second routine')

    def test_macro_d_invalid(self):
        skool = '@start\nc32770 RET'
        writer = self._get_writer(skool)
        prefix = ERROR_PREFIX.format('D')

        # No parameter (1)
        self.assert_error(writer, '#D', 'No parameters (expected 1)', prefix)

        # No parameter (2)
        self.assert_error(writer, '#Dx', 'No parameters (expected 1)', prefix)

        # Invalid parameter
        self.assert_error(writer, '#D234$', "Cannot parse integer '234$' in parameter string: '234$'", prefix)

        # Descriptionless entry
        self.assert_error(writer, '#D32770', 'Entry at 32770 has no description', prefix)

        # Non-existent entry
        self.assert_error(writer, '#D32771', 'Cannot determine description for non-existent entry at 32771', prefix)

    def test_macro_erefs(self):
        skool = '\n'.join((
            '@start',
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
        writer = self._get_writer(skool)

        for address in ('30004', '$7534'):
            output = writer.expand('#EREFS{}'.format(address))
            self.assertEqual(output, 'routines at 30000 and 30005')

    def test_macro_erefs_invalid(self):
        skool = '\n'.join((
            '@start',
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
        writer = self._get_writer(skool)
        prefix = ERROR_PREFIX.format('EREFS')

        # No parameter (1)
        self.assert_error(writer, '#EREFS', 'No parameters (expected 1)', prefix)

        # No parameter (2)
        self.assert_error(writer, '#EREFSx', 'No parameters (expected 1)', prefix)

        # Invalid parameter
        self.assert_error(writer, '#EREFS2$2', "Cannot parse integer '2$2' in parameter string: '2$2'", prefix)

        # Entry point with no referrers
        address = 30005
        self.assert_error(writer, '#EREFS30005', 'Entry point at 30005 has no referrers', prefix)

    def test_macro_fact(self):
        self._test_reference_macro('FACT', 'fact')

    def test_macro_font(self):
        writer = self._get_writer()
        self._test_unsupported_macro(writer, '#FONT55584,,,,1{1,2}')
        self._test_unsupported_macro(writer, '#FONT:[foo]0,,5')
        self._test_unsupported_macro(writer, '#FONTaddr=32768,3,scale=4{x=1,width=26}(chars)')

    def test_macro_font_invalid(self):
        writer = self._get_writer()

        self._test_unsupported_macro(writer, '#FONT:@bar', "No terminating delimiter: @bar")
        self._test_unsupported_macro(writer, '#FONT0(foo', "No closing bracket: (foo")

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
                output = writer.expand('#HTML{0}{1}{2}'.format(delim1, text, delim2))
                self.assertEqual(output, '')

        # Unterminated #HTML macro
        prefix = ERROR_PREFIX.format('HTML')
        self.assert_error(writer, '#HTML:unterminated', 'No terminating delimiter: :unterminated', prefix)

    def test_macro_link(self):
        writer = self._get_writer()

        link_text = 'Testing'
        output = writer.expand('#LINK:Page_ID#anchor%1({0})'.format(link_text))
        self.assertEqual(output, link_text)

    def test_macro_link_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('LINK')

        # No parameters
        self.assert_error(writer, '#LINK', 'No parameters', prefix)

        # No page ID (1)
        self.assert_error(writer, '#LINK:', 'No page ID: #LINK:', prefix)

        # No page ID (2)
        self.assert_error(writer, '#LINK:(text)', 'No page ID: #LINK:(text)', prefix)

        # No closing bracket
        self.assert_error(writer, '#LINK:(text', 'No closing bracket: (text', prefix)

        # Malformed #LINK macro
        self.assert_error(writer, '#LINKpageID', 'Malformed macro: #LINKp...', prefix)

        # No link text
        self.assert_error(writer, '#LINK:PageID', 'No link text: #LINK:PageID', prefix)

        # Blank link text
        self.assert_error(writer, '#LINK:PageID()', 'Blank link text: #LINK:PageID()', prefix)

    def test_macro_poke(self):
        self._test_reference_macro('POKE', 'poke')

    def test_macro_pokes(self):
        writer = self._get_writer()
        snapshot = writer.snapshot

        output = writer.expand('#POKES32768,255')
        self.assertEqual(output, '')
        self.assertEqual(snapshot[32768], 255)

        output = writer.expand('#POKES32768,254,10')
        self.assertEqual(output, '')
        self.assertEqual(snapshot[32768:32778], [254] * 10)

        output = writer.expand('#POKES32768,253,20,2')
        self.assertEqual(output, '')
        self.assertEqual(snapshot[32768:32808:2], [253] * 20)

        output = writer.expand('#POKES49152,1;49153,2')
        self.assertEqual(output, '')
        self.assertEqual(snapshot[49152:49154], [1, 2])

    def test_macro_pokes_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('POKES')

        # No parameters (1)
        self.assert_error(writer, '#POKES', 'No parameters (expected 2)', prefix)

        # Not enough parameters (1)
        self.assert_error(writer, '#POKES0', "Not enough parameters (expected 2): '0'", prefix)

        # Not enough parameters (2)
        self.assert_error(writer, '#POKES0,1;1', "Not enough parameters (expected 2): '1'", prefix)

        # Invalid parameter
        self.assert_error(writer, '#POKES40000,2$2', "Cannot parse integer '2$2' in parameter string: '40000,2$2'", prefix)

    def test_macro_pops(self):
        writer = self._get_writer()
        addr, byte = 49152, 128
        writer.snapshot[addr] = byte
        writer.push_snapshot('test')
        writer.snapshot[addr] = (byte + 127) % 256
        output = writer.expand('#POPS')
        self.assertEqual(output, '')
        self.assertEqual(writer.snapshot[addr], byte)

    def test_macro_pops_empty_stack(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('POPS')
        self.assert_error(writer, '#POPS', 'Cannot pop snapshot when snapshot stack is empty', prefix)

    def test_macro_pushs(self):
        writer = self._get_writer()
        addr, byte = 32768, 64
        for name in ('test', '#foo', 'foo$abcd', ''):
            for suffix in ('', '(bar)', ':baz'):
                writer.snapshot[addr] = byte
                output = writer.expand('#PUSHS{}{}'.format(name, suffix))
                self.assertEqual(output, suffix)
                self.assertEqual(writer.snapshot[addr], byte)
                writer.snapshot[addr] = (byte + 127) % 256
                writer.pop_snapshot()
                self.assertEqual(writer.snapshot[addr], byte)

    def test_macro_r(self):
        skool = '\n'.join((
            '@start',
            'c00000 LD A,B',
            '',
            'c00004 LD A,C',
            '',
            'c00015 LD A,D',
            '',
            'c00116 LD A,E',
            '',
            'c01117 LD A,H',
            '',
            'c11118 LD A,L',
            '',
            '@label=DOSTUFF',
            'c24576 LD HL,0',
            '',
            'b$6003 DEFB 123'
        ))
        writer = self._get_writer(skool, warn=True)

        # Reference address is 0
        output = writer.expand('#R0')
        self.assertEqual(output, '0')

        # Reference address is 1 digit
        output = writer.expand('#R4')
        self.assertEqual(output, '4')

        # Reference address is 2 digits
        output = writer.expand('#R15')
        self.assertEqual(output, '15')

        # Reference address is 3 digits
        output = writer.expand('#R116')
        self.assertEqual(output, '116')

        # Reference address is 4 digits
        output = writer.expand('#R1117')
        self.assertEqual(output, '1117')

        # Reference address is 5 digits
        output = writer.expand('#R11118')
        self.assertEqual(output, '11118')

        # Address resolves to a label
        output = writer.expand('#R24576')
        self.assertEqual(output, 'DOSTUFF')

        # Link text
        link_text = 'Testing1'
        output = writer.expand('#R24576({0})'.format(link_text))
        self.assertEqual(output, link_text)

        # Anchor
        output = writer.expand('#R24576#foo')
        self.assertEqual(output, 'DOSTUFF')

        # Anchor and link text
        link_text = 'Testing2'
        output = writer.expand('#R24576#foo({})'.format(link_text))
        self.assertEqual(output, link_text)

        # No label
        output = writer.expand('#R24579')
        self.assertEqual(output, '6003')
        self.assertEqual(self.err.getvalue(), 'WARNING: Could not convert address 24579 to label\n')
        self.clear_streams()

        # Address between instructions
        output = writer.expand('#R24577')
        self.assertEqual(output, '24577')
        self.assertEqual(self.err.getvalue(), 'WARNING: Could not convert address 24577 to label\n')
        self.clear_streams()

        # Hexadecimal address between instructions
        output = writer.expand('#R$6001')
        self.assertEqual(output, '6001')
        self.assertEqual(self.err.getvalue(), 'WARNING: Could not convert address $6001 to label\n')

    def test_macro_r_other_code(self):
        skool = '\n'.join((
            '@start',
            'c49152 LD HL,0',
            ' $c003 RET',
            '',
            'r$c000 other',
            ' $C003'
        ))
        writer = self._get_writer(skool)

        # Reference with the same address as a remote entry
        output = writer.expand('#R49152')
        self.assertEqual(output, '49152')

        # Reference with the same address as a remote entry point
        output = writer.expand('#R49155')
        self.assertEqual(output, 'c003')

        # Other code, no remote entry
        output = writer.expand('#R32768@other')
        self.assertEqual(output, '32768')

        # Other code with remote entry
        output = writer.expand('#R49152@other')
        self.assertEqual(output, 'c000')

        # Other code with remote entry point
        output = writer.expand('#R49155@other')
        self.assertEqual(output, 'C003')

        # Other code with link text
        link_text = 'Testing2'
        output = writer.expand('#R32768@other#testing({0})'.format(link_text))
        self.assertEqual(output, link_text)

    def test_macro_r_lower(self):
        skool = '\n'.join((
            '@start',
            '@label=START',
            'c32000 RET',
            '',
            'b$7D01 DEFB 0',
            '',
            'r$C000 other'
        ))
        writer = self._get_writer(skool, case=CASE_LOWER)

        # Label
        output = writer.expand('#R32000')
        self.assertEqual(output, 'START')

        # No label
        output = writer.expand('#R32001')
        self.assertEqual(output, '7d01')

        # Other code, no remote entry
        output = writer.expand('#R32768@main')
        self.assertEqual(output, '32768')

        # Other code with remote entry
        output = writer.expand('#R49152@other')
        self.assertEqual(output, 'c000')

    def test_macro_r_hex(self):
        skool = '\n'.join((
            '@start',
            'c24580 RET',
            '',
            'r49152 other',
        ))
        writer = self._get_writer(skool, base=BASE_16)

        # No label
        output = writer.expand('#R24580')
        self.assertEqual(output, '6004')

        # Other code, no remote entry
        output = writer.expand('#R32768@main')
        self.assertEqual(output, '8000')

        # Other code with remote entry
        output = writer.expand('#R49152@other')
        self.assertEqual(output, 'C000')

    def test_macro_r_hex_lower(self):
        skool = '\n'.join((
            '@start',
            'c24590 RET',
            '',
            'r49152 other'
        ))
        writer = self._get_writer(skool, base=BASE_16, case=CASE_LOWER)

        # No label
        output = writer.expand('#R24590')
        self.assertEqual(output, '600e')

        # Other code, no remote entry
        output = writer.expand('#R43981@main')
        self.assertEqual(output, 'abcd')

        # Other code with remote entry
        output = writer.expand('#R49152@other')
        self.assertEqual(output, 'c000')

    def test_macro_r_decimal(self):
        skool = '\n'.join((
            '@start',
            'c$8000 LD A,B',
            '',
            'r$C000 other'
        ))
        writer = self._get_writer(skool, base=BASE_10)

        # No label
        output = writer.expand('#R$8000')
        self.assertEqual(output, '32768')

        # Other code, no remote entry
        output = writer.expand('#R44444@main')
        self.assertEqual(output, '44444')

        # Other code with remote entry
        output = writer.expand('#R$c000@main')
        self.assertEqual(output, '49152')

    def test_macro_r_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('R')

        # No address (1)
        self.assert_error(writer, '#R', "No address", prefix)

        # No address (2)
        self.assert_error(writer, '#R@main', "No address", prefix)

        # No address (3)
        self.assert_error(writer, '#R#bar', "No address", prefix)

        # No address (4)
        self.assert_error(writer, '#R(baz)', "No address", prefix)

        # Invalid address
        self.assert_error(writer, '#R20$5', "Invalid address: 20$5", prefix)

        # No closing bracket
        self.assert_error(writer, '#R32768(qux', "No closing bracket: (qux", prefix)

    def test_macro_refs(self):
        skool = '\n'.join((
            '@start',
            '; Used by the routines at 24583, 24586 and 24589',
            'c24581 LD A,B',
            ' 24582 RET',
            '',
            '; Uses 24581',
            'c24583 CALL 24581',
            '',
            '; Also uses 24581',
            'c24586 CALL 24581',
            '',
            '; Uses 24581 too',
            'c24589 JP 24582',
        ))
        writer = self._get_writer(skool)

        # Some referrers
        for address in ('24581', '$6005'):
            output = writer.expand('#REFS{}'.format(address))
            self.assertEqual(output, 'routines at 24583, 24586 and 24589')

        # No referrers
        output = writer.expand('#REFS24586')
        self.assertEqual(output, 'Not used directly by any other routines')

    def test_macro_refs_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('REFS')

        # No address
        self.assert_error(writer, '#REFS', "No address", prefix)

        # Invalid address
        self.assert_error(writer, '#REFS3$56', "Invalid address: 3$56", prefix)

        # No closing bracket
        self.assert_error(writer, '#REFS34567(foo', "No closing bracket: (foo", prefix)

        # Non-existent entry
        self.assert_error(writer, '#REFS40000', "No entry at 40000", prefix)

    def test_macro_reg(self):
        writer = self._get_writer()
        for reg in ("a", "b", "c", "d", "e", "h", "l", "i", "r", "ixl", "ixh", "iyl", "iyh", "b'", "c'", "d'", "e'", "h'", "l'", "bc", "de", "hl", "sp", "ix", "iy", "bc'", "de'", "hl'"):
            output = writer.expand('#REG{0}'.format(reg))
            self.assertEqual(output, reg.upper())

    def test_macro_reg_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('REG')

        # Missing register argument (1)
        self.assert_error(writer, '#REG', 'Missing register argument', prefix)

        # Missing register argument (2)
        self.assert_error(writer, '#REGq', 'Missing register argument', prefix)

        # Bad register argument
        self.assert_error(writer, '#REGabcd', 'Bad register: "abcd"', prefix)

    def test_macro_scr(self):
        writer = self._get_writer()
        self._test_unsupported_macro(writer, '#SCR2(fname)')
        self._test_unsupported_macro(writer, '#SCR2,w=8,h=8{x=1,width=62}(fname)')

    def test_macro_scr_invalid(self):
        writer = self._get_writer()
        self._test_unsupported_macro(writer, '#SCR0(bar', "No closing bracket: (bar")

    def test_macro_space(self):
        writer = self._get_writer()

        output = writer.expand('"#SPACE"')
        self.assertEqual(output, '" "')

        output = writer.expand('"#SPACE5"')
        self.assertEqual(output, '"     "')

        output = writer.expand('1#SPACE(3)1')
        self.assertEqual(output, '1   1')

    def test_macro_space_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('SPACE')

        # Invalid integer
        self.assert_error(writer, '#SPACE5$3', "Cannot parse integer '5$3' in parameter string: '5$3'", prefix)

        # Invalid integer in brackets
        self.assert_error(writer, '#SPACE(5$3)', "Invalid integer: '5$3'", prefix)

        # No closing bracket
        self.assert_error(writer, '#SPACE(2', "No closing bracket: (2", prefix)

    def test_macro_udg(self):
        writer = self._get_writer()
        self._test_unsupported_macro(writer, '#UDG39144,6(safe_key)')
        self._test_unsupported_macro(writer, '#UDG65432,scale=2,mask=2:65440{y=2,height=14}(key)')

    def test_macro_udg_invalid(self):
        writer = self._get_writer()
        self._test_unsupported_macro(writer, '#UDG0(baz', "No closing bracket: (baz")

    def test_macro_udgarray(self):
        writer = self._get_writer()
        self._test_unsupported_macro(writer, '#UDGARRAY8,,,256;33008-33023(bubble)')
        self._test_unsupported_macro(writer, '#UDGARRAY4,mask=2,step=256;33008-33023:33024-33039{x=1,width=126}(sprite)')
        self._test_unsupported_macro(writer, '#UDGARRAY*foo,2;bar(baz)')
        self._test_unsupported_macro(writer, '#UDGARRAY*foo,delay=2;bar(baz)')

    def test_macro_udgarray_invalid(self):
        writer = self._get_writer()
        self._test_unsupported_macro(writer, '#UDGARRAY1;0(qux', "No closing bracket: (qux")
        self._test_unsupported_macro(writer, '#UDGARRAY*xyzzy;foo(wibble', "No closing bracket: (wibble")

    def test_macro_udgtable(self):
        writer = self._get_writer()
        udgtable = '#UDGTABLE { #UDG0 } UDGTABLE#'
        output = writer.format(udgtable, 79)
        self.assertEqual(output, [])

        # Empty table
        output = '\n'.join(writer.format('#UDGTABLE UDGTABLE#', 79))
        self.assertEqual(output, '')

    def test_macro_udgtable_invalid(self):
        writer = self._get_writer()

        # No end marker
        with self.assertRaisesRegexp(SkoolParsingError, re.escape("Missing end marker: #UDGTABLE { A1 }...")):
            writer.format('#UDGTABLE { A1 }', 79)

    def test_unknown_macro(self):
        writer = self._get_writer()
        for macro, params in (('#FOO', 'xyz'), ('#BAR', '1,2(baz)'), ('#UDGS', '#r1'), ('#LINKS', '')):
            self.assert_error(writer, macro + params, 'Found unknown macro: {}'.format(macro))

    def test_property_comment_width_min(self):
        skool = '\n'.join((
            '@start',
            '@set-comment-width-min={}',
            '; Data',
            'c35000 DEFB 255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255 ; {}',
        ))
        line_width = 79
        comment = 'This comment should have the designated minimum width'
        for width in (10, 15, 20, 'x'):
            asm = self._get_asm(skool.format(width, comment))
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
                exp_lines.append('{}; {}'.format(indent, comment_line))
            for line_no, exp_line in enumerate(exp_lines, 1):
                self.assertEqual(asm[line_no], exp_line)

    def test_property_indent(self):
        skool = '\n'.join((
            '@start',
            '@set-indent={}',
            '; Data',
            'b40000 DEFB 0 ; Comment',
        ))
        for indent in (1, 5, 'x'):
            asm = self._get_asm(skool.format(indent))
            try:
                indent_size = int(indent)
            except ValueError:
                indent_size = 2
            self.assertEqual(asm[1], '{}DEFB 0                  ; Comment'.format(' ' * indent_size))

    def test_property_label_colons(self):
        skool = '\n'.join((
            '@start',
            '@set-label-colons={}',
            '@label=START',
            'c30000 RET'
        ))

        # label-colons=0
        asm = self._get_asm(skool.format(0))
        self.assertEqual(asm[0], 'START')

        # label-colons=1
        asm = self._get_asm(skool.format(1))
        self.assertEqual(asm[0], 'START:')

    def test_property_line_width(self):
        skool = '\n'.join((
            '@start',
            '@set-line-width={}',
            '; Routine',
            'c49152 RET ; This is a fairly long instruction comment, which makes it suitable',
            '           ; for testing various line widths',
        ))
        indent = ' ' * 25
        instruction = '  RET'.ljust(len(indent))
        comment = 'This is a fairly long instruction comment, which makes it suitable for testing various line widths'
        for width in (65, 80, 95, 'x'):
            asm = self._get_asm(skool.format(width))
            try:
                line_width = int(width)
            except ValueError:
                line_width = 79
            comment_lines = textwrap.wrap(comment, line_width - len(instruction) - 3)
            exp_lines = [instruction + ' ; ' + comment_lines[0]]
            for comment_line in comment_lines[1:]:
                exp_lines.append('{} ; {}'.format(indent, comment_line))
            for line_no, exp_line in enumerate(exp_lines, 1):
                self.assertEqual(asm[line_no], exp_line)

    def test_property_wrap_column_width_min(self):
        skool = '\n'.join((
            '@start',
            '@set-wrap-column-width-min={}',
            '; Routine',
            ';',
            '; #TABLE(,:w)',
            '; {{ {} | An unwrappable column whose contents extend the table width beyond 80 characters }}',
            '; TABLE#',
            'c40000 RET',
        ))
        text = 'This wrappable text should have the designated minimum width'
        for width in (10, 18, 26, 'Z'):
            asm = self._get_asm(skool.format(width, text))
            try:
                wrap_column_width_min = int(width)
            except ValueError:
                wrap_column_width_min = 10
            text_lines = textwrap.wrap(text, wrap_column_width_min)
            actual_width = max([len(line) for line in text_lines])
            exp_lines = ['; | {} |'.format(line.ljust(actual_width)) for line in text_lines]
            for line_no, exp_line in enumerate(exp_lines, 3):
                self.assertEqual(asm[line_no][:len(exp_line)], exp_line)

    def test_continuation_line(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            'c40000 LD A,B ; This instruction has a long comment that will require a',
            '              ; continuation line',
        ))
        asm = self._get_asm(skool)
        self.assertEqual(asm[2], '                          ; require a continuation line')

    def test_warn_unconverted_addresses(self):
        skool = '\n'.join((
            '@start',
            '; Routine at 32768',
            ';',
            '; Used by the routine at 32768.',
            ';',
            '; HL 32768',
            'c32768 LD A,B  ; This instruction is at 32768',
            '; This mid-routine comment is above 32769.',
            ' 32769 RET',
        ))
        self._get_asm(skool, warn=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 10)
        self.assertEqual(warnings[0], 'WARNING: Comment contains address (32768) not converted to a label:')
        self.assertEqual(warnings[1], '; Routine at 32768')
        self.assertEqual(warnings[2], 'WARNING: Comment contains address (32768) not converted to a label:')
        self.assertEqual(warnings[3], '; Used by the routine at 32768.')
        self.assertEqual(warnings[4], 'WARNING: Register description contains address (32768) not converted to a label:')
        self.assertEqual(warnings[5], '; HL 32768')
        self.assertEqual(warnings[6], 'WARNING: Comment at 32768 contains address (32768) not converted to a label:')
        self.assertEqual(warnings[7], '  LD A,B                  ; This instruction is at 32768')
        self.assertEqual(warnings[8], 'WARNING: Comment above 32769 contains address (32769) not converted to a label:')
        self.assertEqual(warnings[9], '; This mid-routine comment is above 32769.')

    def test_warn_long_line(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            'c30000 BIT 3,(IX+101) ; Pneumonoultramicroscopicsilicovolcanoconiosis',
        ))
        self._get_asm(skool, instr_width=30, warn=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 2)
        self.assertEqual(warnings[0], 'WARNING: Line is 80 characters long:')
        self.assertEqual(warnings[1], '  BIT 3,(IX+101)                 ; Pneumonoultramicroscopicsilicovolcanoconiosis')

    def test_warn_wide_table(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            ';',
            '; #TABLE',
            '; { This is cell A1 | This is cell A2 | This is cell A3 | This is cell A4 | This is cell A5 }',
            '; TABLE#',
            'c50000 RET',
        ))
        self._get_asm(skool, warn=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0], 'WARNING: Table in entry at 50000 is 91 characters wide')

    def test_suppress_warnings(self):
        skool = '\n'.join((
            '@start',
            '; Routine at 24576',
            'c24576 JP 24576 ; VeryLongWordThatWouldNormallyTriggerALongLineWarning',
        ))
        self._get_asm(skool, warn=False)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 0)

    def test_option_crlf(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            'c32768 RET',
        ))
        asm = self._get_asm(skool, crlf=True)
        self.assertTrue(all(line.endswith('\r') for line in asm))

    def test_option_tab(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            'c32768 LD A,B',
            ' 32769 RET',
        ))
        asm = self._get_asm(skool, tab=True)
        for line in asm:
            if line and line[0].isspace():
                self.assertEqual(line[0], '\t')

    def test_option_lower(self):
        skool = '\n'.join((
            '@start',
            '@org=24576',
            '',
            '; Routine',
            ';',
            '; Description.',
            ';',
            '; A Value',
            '; B Another value',
            '@label=DOSTUFF',
            'c24576 LD HL,$6003',
            '',
            '; Data',
            'b$6003 DEFB 123 ; #REGa=0',
            ' $6004 DEFB 246 ; #R24576',
        ))
        asm = self._get_asm(skool, case=CASE_LOWER)

        # Test that the ORG directive is in lower case
        self.assertEqual(asm[0], '  org 24576')

        # Test that register names are in lower case
        self.assertEqual(asm[6], '; a Value')
        self.assertEqual(asm[7], '; b Another value')

        # Test that labels are unaffected
        self.assertEqual(asm[8], 'DOSTUFF:')

        # Test that #REG macro arguments are in lower case
        self.assertEqual(asm[12], '  defb 123                ; a=0')

        # Test that #R macro arguments that resolve to a label are unaffected
        self.assertEqual(asm[13], '  defb 246                ; DOSTUFF')

    def test_option_instr_width(self):
        skool = '\n'.join((
            '@start',
            '; Data',
            'b$6003 DEFB 123 ; #REGa=0',
        ))
        for width in (5, 10, 15, 20, 25, 30):
            asm = self._get_asm(skool, instr_width=width)
            self.assertEqual(asm[1], '  {0} ; A=0'.format('DEFB 123'.ljust(width)))

    def test_header(self):
        skool = [
            '@start',
            '; Header line 1.',
            ';   * Header line 2 (indented)',
            ';   * Header line #THREE (also indented)',
            ';',
            '; See <http://skoolkit.ca/>.',
            '',
            '; Start',
            'c32768 JP 49152'
        ]
        asm = self._get_asm('\n'.join(skool))
        self.assertEqual(skool[1:-1], asm[:len(skool) - 2])

    def test_registers(self):
        skool = '\n'.join((
            '@start',
            '; Test parsing of register blocks (1)',
            ';',
            '; Traditional.',
            ';',
            '; A Some value',
            '; B Some other value',
            'c24604 RET',
            '',
            '; Test parsing of register blocks (2)',
            ';',
            '; With prefixes.',
            ';',
            '; Input:a Some value',
            ';       b Some other value',
            '; Output:c The result',
            ';        d',
            'c24605 RET',
        ))
        asm = self._get_asm(skool)

        # Traditional
        self.assertEqual(asm[4], '; A Some value')
        self.assertEqual(asm[5], '; B Some other value')

        # With prefixes (right-justified to longest prefix)
        self.assertEqual(asm[12], ';  Input:a Some value')
        self.assertEqual(asm[13], ';        b Some other value')
        self.assertEqual(asm[14], '; Output:c The result')
        self.assertEqual(asm[15], ';        d')

    def test_register_description_continuation_lines(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            ';',
            '; .',
            ';',
            '; BC This register description is long enough that it needs to be',
            ';   .split over two lines',
            '; DE Short register description',
            '; HL Another register description that is long enough to need',
            '; .  splitting over two lines',
            'c40000 RET'
        ))
        asm = self._get_asm(skool)

        exp_asm = [
            '; BC This register description is long enough that it needs to be split over',
            ';    two lines',
            '; DE Short register description',
            '; HL Another register description that is long enough to need splitting over',
            ';    two lines',
            '  RET'
        ]
        self.assertEqual(exp_asm, asm[2:2 + len(exp_asm)])

    def test_registers_in_non_code_blocks(self):
        skool = '\n'.join((
            '@start',
            '; Byte',
            ';',
            '; .',
            ';',
            '; A Some value',
            'b54321 DEFB 0',
            '',
            '; GSB entry',
            ';',
            '; .',
            ';',
            '; B Some value',
            'g54322 DEFB 0',
            '',
            '; Space',
            ';',
            '; .',
            ';',
            '; C Some value',
            's54323 DEFS 10',
            '',
            '; Message',
            ';',
            '; .',
            ';',
            '; D Some value',
            't54333 DEFM "Hi"',
            '',
            '; Unused code',
            ';',
            '; .',
            ';',
            '; E Some value',
            'u54335 LD HL,12345',
            '',
            '; Words',
            ';',
            '; .',
            ';',
            '; H Some value',
            'w54338 DEFW 1,2'
        ))
        asm = self._get_asm(skool)

        line_no = 2
        for address, reg_name in ((54321, 'A'), (54322, 'B'), (54323, 'C'), (54333, 'D'), (54335, 'E'), (54338, 'H')):
            self.assertEqual(asm[line_no], '; {} Some value'.format(reg_name))
            line_no += 5

    def test_start_comment(self):
        start_comment = 'This is a start comment.'
        skool = '\n'.join((
            '@start',
            '; Test a start comment',
            ';',
            '; .',
            ';',
            '; .',
            ';',
            '; {}'.format(start_comment),
            'c50000 RET'
        ))
        exp_asm = [
            '; Test a start comment',
            ';',
            '; {}'.format(start_comment),
            '  RET'
        ]
        asm = self._get_asm(skool)
        self.assertEqual(exp_asm, asm[:len(exp_asm)])

    def test_multi_paragraph_start_comment(self):
        start_comment = ('First paragraph.', 'Second paragraph.')
        skool = '\n'.join((
            '@start',
            '; Test a multi-paragraph start comment',
            ';',
            '; .',
            ';',
            '; .',
            ';',
            '; {}'.format(start_comment[0]),
            '; .',
            '; {}'.format(start_comment[1]),
            'c50000 RET'
        ))
        exp_asm = [
            '; Test a multi-paragraph start comment',
            ';',
            '; {}'.format(start_comment[0]),
            ';',
            '; {}'.format(start_comment[1]),
            '  RET'
        ]
        asm = self._get_asm(skool)
        self.assertEqual(exp_asm, asm[:len(exp_asm)])

    def test_empty_description(self):
        skool = '\n'.join((
            '@start',
            '; Test an empty description',
            ';',
            '; #HTML(#UDG32768)',
            'c24604 RET',
        ))
        asm = self._get_asm(skool)
        self.assertEqual(asm[0], '; Test an empty description')
        self.assertEqual(asm[1], '  RET')

    def test_empty_description_with_registers(self):
        skool = '\n'.join((
            '@start',
            '; Test an empty description and a register section',
            ';',
            '; .',
            ';',
            '; A 0',
            '; B 1',
            'c25600 RET',
        ))
        asm = self._get_asm(skool)
        self.assertEqual(asm[0], '; Test an empty description and a register section')
        self.assertEqual(asm[1], ';')
        self.assertEqual(asm[2], '; A 0')
        self.assertEqual(asm[4], '  RET')

    def test_end_comment(self):
        skool = '\n'.join((
            '@start',
            '; Start',
            'c49152 RET',
            '; End comment.',
        ))
        asm = self._get_asm(skool)
        self.assertEqual(asm[1], '  RET')
        self.assertEqual(asm[2], '; End comment.')

    def test_entry_point_labels(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            '@label=START',
            'c40000 LD A,B',
            '*40001 LD C,D',
            '*40002 RET',
        ))
        asm = self._get_asm(skool)
        self.assertEqual(asm[1], 'START:')
        self.assertEqual(asm[3], 'START_0:')
        self.assertEqual(asm[5], 'START_1:')

    def test_org_address_converted_to_decimal(self):
        skool = '\n'.join((
            '@start',
            '@org=$8000',
            'c$8000 RET'
        ))
        asm = self._get_asm(skool, base=BASE_10)
        self.assertEqual(asm[0], '  ORG 32768')

    def test_org_address_converted_to_hex(self):
        skool = '\n'.join((
            '@start',
            '@org=32778',
            'c32778 RET'
        ))
        asm = self._get_asm(skool, base=BASE_16)
        self.assertEqual(asm[0], '  ORG $800A')

    def test_org_address_converted_to_lower_case_hex(self):
        skool = '\n'.join((
            '@start',
            '@org=61613',
            'c61613 RET'
        ))
        asm = self._get_asm(skool, base=BASE_16, case=CASE_LOWER)
        self.assertEqual(asm[0], '  org $f0ad')

    def test_org_address_converted_to_upper_case_hex(self):
        skool = '\n'.join((
            '@start',
            '@org=$f0ad',
            'c$f0ad RET'
        ))
        asm = self._get_asm(skool, base=BASE_16, case=CASE_UPPER)
        self.assertEqual(asm[0], '  ORG $F0AD')

    def test_ignoreua_directive_on_entry_title(self):
        skool = '\n'.join((
            '@start',
            '@ignoreua',
            '; Routine at 32768',
            'c32768 RET'
        ))
        self._get_asm(skool, warn=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 0)

    def test_ignoreua_directive_on_entry_description(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            ';',
            '@ignoreua',
            '; Description of routine at 32768.',
            'c32768 RET'
        ))
        self._get_asm(skool, warn=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 0)

    def test_ignoreua_directive_on_register_description(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            ';',
            '; .',
            ';',
            '@ignoreua',
            '; HL 32768',
            'c32768 RET'
        ))
        self._get_asm(skool, warn=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 0)

    def test_ignoreua_directive_on_start_comment(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            ';',
            '; Description.',
            ';',
            '; .',
            ';',
            '@ignoreua',
            '; Start comment for the routine at 32768.',
            'c32768 RET'
        ))
        self._get_asm(skool, warn=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 0)

    def test_ignoreua_directive_on_instruction_comment(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            '@ignoreua',
            'c32768 LD A,B ; This is the instruction at 32768'
        ))
        self._get_asm(skool, warn=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 0)

    def test_ignoreua_directive_on_mid_block_comment(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            'c32768 LD A,B ;',
            '@ignoreua',
            '; This is the mid-routine comment above 32769.',
            ' 32769 RET'
        ))
        self._get_asm(skool, warn=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 0)

    def test_ignoreua_directive_on_end_comment(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            'c32768 LD A,B ;',
            ' 32769 RET',
            '@ignoreua',
            '; This is the end comment after 32769.'
        ))
        self._get_asm(skool, warn=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 0)

    def test_nowarn_directive(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            '@nowarn',
            'c30000 LD HL,30003',
            '',
            '; Routine',
            '@label=NEXT',
            '@nowarn',
            'c30003 CALL 30000',
            '@nowarn',
            ' 30006 CALL 30001',
        ))
        for asm_mode in (1, 2, 3):
            self._get_asm(skool, warn=True, asm_mode=asm_mode)
            warnings = self.err.getvalue().split('\n')[:-1]
            self.assertEqual(len(warnings), 0)

    def test_keep_directive(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            '@keep',
            'c30000 LD HL,30003',
            '',
            '; Routine',
            '@label=NEXT',
            'c30003 RET',
        ))
        asm = self._get_asm(skool)
        self.assertEqual(asm[1], '  LD HL,30003')

    def test_nolabel_directive(self):
        skool = '\n'.join((
            '@start',
            '; Start',
            '@label=START',
            'c32768 LD A,B',
            '@nolabel',
            '*32769 RET',
        ))
        asm = self._get_asm(skool)
        self.assertEqual(asm[1], 'START:')
        self.assertEqual(asm[2], '  LD A,B')
        self.assertEqual(asm[3], '  RET')

    def test_comment_for_wide_instruction(self):
        skool = '\n'.join((
            '@start',
            'c30000 LD B,0     ; Comment',
            '@label=VERYLONGLABELINDEEDOHYES',
            ' 30002 DJNZ 30002 ; Comment for the DJNZ instruction with the very long',
            '                  ; label; the lines in the comment for this instruction',
            '                  ; should be aligned on the left (but not necessarily',
            '                  ; aligned with the comments for the other instructions)',
            ' 30004 RET        ; Comment',
        ))
        exp_asm = [
            '  LD B,0                  ; Comment',
            'VERYLONGLABELINDEEDOHYES:',
            '  DJNZ VERYLONGLABELINDEEDOHYES ; Comment for the DJNZ instruction with the',
            '                                ; very long label; the lines in the comment for',
            '                                ; this instruction should be aligned on the',
            '                                ; left (but not necessarily aligned with the',
            '                                ; comments for the other instructions)',
            '  RET                     ; Comment',
            '',
        ]
        self.assertEqual(exp_asm, self._get_asm(skool))

class TableMacroTest(SkoolKitTestCase):
    def _get_writer(self, skool='', crlf=False, tab=False, instr_width=23, warn=False):
        skoolfile = self.write_text_file(skool, suffix='.skool')
        skool_parser = SkoolParser(skoolfile, asm_mode=1)
        properties = dict(skool_parser.properties)
        properties['crlf'] = '1' if crlf else '0'
        properties['tab'] = '1' if tab else '0'
        properties['instruction-width'] = instr_width
        properties['warnings'] = '1' if warn else '0'
        return AsmWriter(skool_parser, properties, False)

    def assert_error(self, skool, error):
        self.clear_streams()
        writer = self._get_writer(skool)
        with self.assertRaises(SkoolParsingError) as cm:
            writer.write()
        self.assertEqual(cm.exception.args[0], error)

    def _test_table(self, src_lines, exp_output):
        writer = self._get_writer()
        table = '#TABLE{}\nTABLE#'.format('\n'.join(src_lines))
        output = writer.format(table, 79)
        self.assertEqual(output, exp_output)

    def test_headers_and_colspans_and_rowspans(self):
        # Headers, colspans 1 and 2, rowspans 1 and 2
        src = (
            '(data)',
            '{ =h Col1 | =h Col2 | =h,c2 Cols3+4 }',
            '{ =r2 X   | Y       | Za  | Zb }',
            '{           Y2      | Za2 | Zb2 }',
        )
        exp_output = [
            '+------+------+-----------+',
            '| Col1 | Col2 | Cols3+4   |',
            '+------+------+-----+-----+',
            '| X    | Y    | Za  | Zb  |',
            '|      | Y2   | Za2 | Zb2 |',
            '+------+------+-----+-----+',
        ]
        self._test_table(src, exp_output)

    def test_cell_with_rowspan_2_in_middle_column(self):
        # Cell with rowspan > 1 in the middle column
        src = (
            '{ A1 cell | =r2 This is a cell with rowspan=2 | C1 cell }',
            '{ A2 cell | C2 cell }',
        )
        exp_output = [
            '+---------+-------------------------------+---------+',
            '| A1 cell | This is a cell with rowspan=2 | C1 cell |',
            '| A2 cell |                               | C2 cell |',
            '+---------+-------------------------------+---------+',
        ]
        self._test_table(src, exp_output)

    def test_cell_with_rowspan_2_in_last_column(self):
        # Cell with rowspan > 1 in the rightmost column
        src = (
            '{ A1 cell | B1 cell | =r2 This is a cell with rowspan=2 }',
            '{ A2 cell | B2 cell }',
        )
        exp_output = [
            '+---------+---------+-------------------------------+',
            '| A1 cell | B1 cell | This is a cell with rowspan=2 |',
            '| A2 cell | B2 cell |                               |',
            '+---------+---------+-------------------------------+',
        ]
        self._test_table(src, exp_output)

    def test_cell_with_colspan_2_and_wrapped_contents(self):
        # Cell with colspan > 1 and wrapped contents
        src = (
            '(,:w)',
            '{ =c2 Cell with colspan=2 and contents that will be wrapped onto the following line }',
            '{ A2 | B2 }',
        )

        exp_output = [
            '+--------------------------------------------------------------------------+',
            '| Cell with colspan=2 and contents that will be wrapped onto the following |',
            '| line                                                                     |',
            '| A2                                  | B2                                 |',
            '+-------------------------------------+------------------------------------+',
        ]
        self._test_table(src, exp_output)

    def test_cell_in_first_column_with_rowspan_2_and_wrapped_contents(self):
        # Cell in the first column with rowspan > 1 and wrapped contents
        src = (
            '(,:w)',
            '{ =r2 This cell has rowspan=2 and contains text that will wrap onto the next line | B1 }',
            '{ B2 }',
        )
        exp_output = [
            '+-------------------------------------------------------------------+----+',
            '| This cell has rowspan=2 and contains text that will wrap onto the | B1 |',
            '| next line                                                         | B2 |',
            '+-------------------------------------------------------------------+----+',
        ]
        self._test_table(src, exp_output)

    def test_cell_in_middle_column_with_rowspan_2_and_wrapped_contents(self):
        # Cell in the middle column with rowspan > 1 and wrapped contents
        src = (
            '(,,:w)',
            '{ A1 | =r2 This cell has rowspan=2 and contains text that will wrap onto the next line | C1 }',
            '{ A2 | C2 }',
        )
        exp_output = [
            '+----+---------------------------------------------------------------+----+',
            '| A1 | This cell has rowspan=2 and contains text that will wrap onto | C1 |',
            '| A2 | the next line                                                 | C2 |',
            '+----+---------------------------------------------------------------+----+',
        ]
        self._test_table(src, exp_output)

    def test_cell_in_last_column_with_rowspan_2_and_wrapped_contents(self):
        # Cell in the last column with rowspan > 1 and wrapped contents
        src = (
            '(,,:w)',
            '{ A1 | =r2 This cell has rowspan=2 and contains text that will wrap onto the next line }',
            '{ A2 }',
        )
        exp_output = [
            '+----+-------------------------------------------------------------------+',
            '| A1 | This cell has rowspan=2 and contains text that will wrap onto the |',
            '| A2 | next line                                                         |',
            '+----+-------------------------------------------------------------------+',
        ]
        self._test_table(src, exp_output)

    def test_short_header_row(self):
        # Header row shorter than the remaining rows
        src = (
            '{ =h H1 | =h H2 }',
            '{ A1    | B1    | C1 }',
            '{ A2    | B2    | C2 }',
        )
        exp_output = [
            '+----+----+',
            '| H1 | H2 |',
            '+----+----+----+',
            '| A1 | B1 | C1 |',
            '| A2 | B2 | C2 |',
            '+----+----+----+',
        ]
        self._test_table(src, exp_output)

    def test_transparent_cell_in_top_left_corner(self):
        # Transparent cell in the top left corner
        src = (
            '{ =t | =h H2 }',
            '{ A1 | B1 }',
        )
        exp_output = [
            '     +----+',
            '     | H2 |',
            '+----+----+',
            '| A1 | B1 |',
            '+----+----+',
        ]
        self._test_table(src, exp_output)

    def test_transparent_cell_in_top_right_corner(self):
        # Transparent cell in the top right corner
        src = (
            '{ =h H1 | =t }',
            '{ A1    | B1 }',
        )
        exp_output = [
            '+----+',
            '| H1 |',
            '+----+----+',
            '| A1 | B1 |',
            '+----+----+',
        ]
        self._test_table(src, exp_output)

    def test_transparent_cell_in_bottom_right_corner(self):
        # Transparent cell in the bottom right corner
        src = (
            '{ =h H1 | =h H2 }',
            '{ A1    | =t }',
        )
        exp_output = [
            '+----+----+',
            '| H1 | H2 |',
            '+----+----+',
            '| A1 |',
            '+----+',
        ]
        self._test_table(src, exp_output)

    def test_transparent_cell_in_bottom_left_corner(self):
        # Transparent cell in the bottom left corner
        src = (
            '{ =h H1 | =h H2 }',
            '{ =t    | B1 }',
        )
        exp_output = [
            '+----+----+',
            '| H1 | H2 |',
            '+----+----+',
            '     | B1 |',
            '     +----+',
        ]
        self._test_table(src, exp_output)

    def test_transparent_cells_with_rowspan_2_in_top_corners(self):
        # Transparent cells with rowspan > 1 in the top corners
        src = (
            '{ =t,r2 | H1    | =t,r2 }',
            '{         =h H2         }',
            '{ A1    | B1    | C1    }',
        )
        exp_output = [
            '     +----+',
            '     | H1 |',
            '     | H2 |',
            '+----+----+----+',
            '| A1 | B1 | C1 |',
            '+----+----+----+',
        ]
        self._test_table(src, exp_output)

    def test_transparent_cells__with_rowspan_2_in_bottom_corners(self):
        # Transparent cells with rowspan > 1 in the bottom corners
        src = (
            '{ =h H1 | =h H2 | =h H3 }',
            '{ =t,r2 | B1    | =t,r2 }',
            '{         B2 }',
        )
        exp_output = [
            '+----+----+----+',
            '| H1 | H2 | H3 |',
            '+----+----+----+',
            '     | B1 |',
            '     | B2 |',
            '     +----+',
        ]
        self._test_table(src, exp_output)

    def test_adjacent_transparent_cells_in_bottom_right_corner(self):
        # Adjacent transparent cells
        src = (
            '{ =h H1 | =h H2 | =h H3 }',
            '{ =h A1 | =h B1 | =t,r2 }',
            '{ A2    | =t }',
        )
        exp_output = [
            '+----+----+----+',
            '| H1 | H2 | H3 |',
            '+----+----+----+',
            '| A1 | B1 |',
            '+----+----+',
            '| A2 |',
            '+----+',
        ]
        self._test_table(src, exp_output)

    def test_adjacent_transparent_cells_in_bottom_left_corner(self):
        # More adjacent transparent cells
        src = (
            '{ =h H1 | =h H2 | =h H3 }',
            '{ =t,r2 | =h B1 | =h C1 }',
            '{         =t    | C2 }',
        )
        exp_output = [
            '+----+----+----+',
            '| H1 | H2 | H3 |',
            '+----+----+----+',
            '     | B1 | C1 |',
            '     +----+----+',
            '          | C2 |',
            '          +----+',
        ]
        self._test_table(src, exp_output)

    def test_short_header_row_ending_with_transparent_cell(self):
        # Short header row ending with a (redundant) transparent cell
        src = (
            '{ =h A1 | =t }',
            '{ A2 | B2 | C2 }',
        )
        exp_output = [
            '+----+',
            '| A1 |',
            '+----+----+----+',
            '| A2 | B2 | C2 |',
            '+----+----+----+',
        ]
        self._test_table(src, exp_output)

    def test_transparent_cell_in_last_column_of_middle_row(self):
        # Transparent cell in the last column between the top and bottom rows
        src = (
            '{ =h A1 | =h B1 | =h C1 }',
            '{ =h A2 | =h B2 | =t }',
            '{ A3 | B3 | C3 }',
        )
        exp_output = [
            '+----+----+----+',
            '| A1 | B1 | C1 |',
            '+----+----+----+',
            '| A2 | B2 |',
            '+----+----+----+',
            '| A3 | B3 | C3 |',
            '+----+----+----+',
        ]
        self._test_table(src, exp_output)

    def test_transparent_cell_in_middle_column_of_bottom_row(self):
        # Transparent cell in the bottom row between the first and last columns
        src = (
            '{ =h A1 | =h B1 | =h C1 }',
            '{ =h A2 | =h B2 | =h C2 }',
            '{ A3 | =t | C3 }',
        )
        exp_output = [
            '+----+----+----+',
            '| A1 | B1 | C1 |',
            '+----+----+----+',
            '| A2 | B2 | C2 |',
            '+----+----+----+',
            '| A3 |    | C3 |',
            '+----+    +----+',
        ]
        self._test_table(src, exp_output)

    def test_transparent_cell_in_first_column_of_middle_row(self):
        # Transparent cell in the first column between the top and bottom rows
        src = (
            '{ =h A1 | =h B1 | =h C1 }',
            '{ =t | =h B2 | =h C2 }',
            '{ A3 | B3 | C3 }',
        )
        exp_output = [
            '+----+----+----+',
            '| A1 | B1 | C1 |',
            '+----+----+----+',
            '     | B2 | C2 |',
            '+----+----+----+',
            '| A3 | B3 | C3 |',
            '+----+----+----+',
        ]
        self._test_table(src, exp_output)

    def test_transparent_cell_in_middle_column_of_top_row(self):
        # Transparent cell in the top row between the first and last columns
        src = (
            '{ =h A1 | =t | =h C1 }',
            '{ =h A2 | =h B2 | =h C2 }',
            '{ A3 | B3 | C3 }',
        )
        exp_output = [
            '+----+    +----+',
            '| A1 |    | C1 |',
            '+----+----+----+',
            '| A2 | B2 | C2 |',
            '+----+----+----+',
            '| A3 | B3 | C3 |',
            '+----+----+----+',
        ]
        self._test_table(src, exp_output)

    def test_header_cell_with_rowspan_2_and_wrapped_contents_in_first_column(self):
        # Header cell with rowspan > 1 and wrapped contents in the first column
        src = (
            '(,:w)',
            '{ =h,r2 The contents of this cell are wrapped onto two lines because of their excessive length | =h B1 }',
            '{ =h B2 }',
        )
        exp_output = [
            '+-----------------------------------------------------------------+----+',
            '| The contents of this cell are wrapped onto two lines because of | B1 |',
            '| their excessive length                                          +----+',
            '|                                                                 | B2 |',
            '+-----------------------------------------------------------------+----+',
        ]
        self._test_table(src, exp_output)

    def test_header_cell_with_rowspan_2_and_wrapped_contents_in_last_column(self):
        # Header cell with rowspan > 1 and wrapped contents in the last column
        src = (
            '(,,:w)',
            '; { =h A1 | =h,r2 The contents of this cell are wrapped onto two lines because of their excessive length }',
            '; { =h A2 }',
        )
        exp_output = [
            '+----+-----------------------------------------------------------------+',
            '| A1 | The contents of this cell are wrapped onto two lines because of |',
            '+----+ their excessive length                                          |',
            '| A2 |                                                                 |',
            '+----+-----------------------------------------------------------------+',
        ]
        self._test_table(src, exp_output)

    def test_header_cell_with_rowspan_2_and_wrapped_contents_in_middle_column(self):
        # Header cell with rowspan > 1 and wrapped contents in the middle column
        src = (
            '(,,:w)',
            '{ =h A1 | =h,r2 The contents of this cell are wrapped onto two lines because of their excessive length | =h C1 }',
            '{ =h A2 | =h C2 }',
        )
        exp_output = [
            '+----+-----------------------------------------------------------------+----+',
            '| A1 | The contents of this cell are wrapped onto two lines because of | C1 |',
            '+----+ their excessive length                                          +----+',
            '| A2 |                                                                 | C2 |',
            '+----+-----------------------------------------------------------------+----+',
        ]
        self._test_table(src, exp_output)

    def test_empty_table(self):
        self._test_table((), [])

    def test_missing_end_marker(self):
        writer = self._get_writer()
        with self.assertRaisesRegexp(SkoolParsingError, re.escape("Missing end marker: #TABLE { A1 }...")):
            writer.format('#TABLE { A1 }', 79)

    def test_no_closing_bracket_in_css_class_list(self):
        # No closing ')' in CSS class list
        skool = '\n'.join((
            '@start',
            '; Routine',
            ';',
            '; #TABLE(class1,class2,',
            '; { Hi }',
            '; TABLE#',
            'c32768 RET',
        ))
        error = '\n'.join((
            "Cannot find closing ')' in table CSS class list:",
            '(class1,class2, { Hi } TABLE#',
        ))
        self.assert_error(skool, error)

    def test_no_space_after_opening_brace(self):
        # No space after the opening '{'
        skool = '\n'.join((
            '@start',
            '; Routine',
            ';',
            '; #TABLE',
            '; {Lo }',
            '; TABLE#',
            'c49152 RET',
        ))
        error = '\n'.join((
            "Cannot find opening '{ ' in table row:",
            '{Lo } TABLE#',
        ))
        self.assert_error(skool, error)

    def test_no_space_before_closing_brace(self):
        # No space before the closing '}'
        skool = '\n'.join((
            '@start',
            '; Routine',
            ';',
            '; #TABLE',
            '; { Yo}',
            '; TABLE#',
            'c24576 RET',
        ))
        error = '\n'.join((
            "Cannot find closing ' }' in table row:",
            '{ Yo} TABLE#',
        ))
        self.assert_error(skool, error)

class ListMacroTest(SkoolKitTestCase):
    def _get_writer(self, skool='', crlf=False, tab=False, instr_width=23, warn=False):
        skoolfile = self.write_text_file(skool, suffix='.skool')
        skool_parser = SkoolParser(skoolfile, asm_mode=1)
        properties = dict(skool_parser.properties)
        properties['crlf'] = '1' if crlf else '0'
        properties['tab'] = '1' if tab else '0'
        properties['instruction-width'] = instr_width
        properties['warnings'] = '1' if warn else '0'
        return AsmWriter(skool_parser, properties, False)

    def assert_error(self, skool, error):
        self.clear_streams()
        writer = self._get_writer(skool)
        with self.assertRaises(SkoolParsingError) as cm:
            writer.write()
        self.assertEqual(cm.exception.args[0], error)

    def _test_list(self, src_lines, exp_output, bullet='*'):
        writer = self._get_writer()
        writer.bullet = bullet
        list_src = '#LIST{}\nLIST#'.format('\n'.join(src_lines))
        output = writer.format(list_src, 79)
        self.assertEqual(output, exp_output)

    def test_wrapped_item(self):
        src = (
            '(data)',
            '{ Really long item that should end up being wrapped onto two lines when rendered in ASM mode }',
            '{ Short item with a skool macro: #REGa }',
        )
        exp_output = [
            '* Really long item that should end up being wrapped onto two lines when',
            '  rendered in ASM mode',
            '* Short item with a skool macro: A',
        ]
        self._test_list(src, exp_output)

    def test_bullet(self):
        src = (
            '{ First item }',
            '{ Second item }',
        )
        exp_output = [
            '-- First item',
            '-- Second item',
        ]
        self._test_list(src, exp_output, '--')

    def test_empty_list(self):
        self._test_list((), [])

    def test_missing_end_marker(self):
        writer = self._get_writer()
        with self.assertRaisesRegexp(SkoolParsingError, re.escape("Missing end marker: #LIST { Item }...")):
            writer.format('#LIST { Item }', 79)

    def test_no_closing_bracket_in_parameter_list(self):
        # No closing ')' in parameter list
        skool = '\n'.join((
            '@start',
            '; Routine',
            ';',
            '; #LIST(default',
            '; { Item 1 }',
            '; LIST#',
            'c32768 RET',
        ))
        error = '\n'.join((
            "Cannot find closing ')' in parameter list:",
            '(default { Item 1 } LIST#',
        ))
        self.assert_error(skool, error)

    def test_no_space_after_opening_brace(self):
        # No space after the opening '{'
        skool = '\n'.join((
            '@start',
            '; Routine',
            ';',
            '; #LIST',
            '; {Item }',
            '; LIST#',
            'c40000 RET',
        ))
        error = '\n'.join((
            "Cannot find opening '{ ' in list item:",
            '{Item } LIST#',
        ))
        self.assert_error(skool, error)

    def test_no_space_before_closing_brace(self):
        # No space before the closing '}'
        skool = '\n'.join((
            '@start',
            '; Routine',
            ';',
            '; #LIST',
            '; { Item}',
            '; LIST#',
            'c50000 RET',
        ))
        error = '\n'.join((
            "Cannot find closing ' }' in list item:",
            '{ Item} LIST#',
        ))
        self.assert_error(skool, error)

if __name__ == '__main__':
    unittest.main()
