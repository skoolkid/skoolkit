from skoolkit import BASE_10, BASE_16, VERSION
from skoolkit.skoolhtml import HtmlWriter
from skoolkit.skoolparser import CASE_LOWER, CASE_UPPER

ERROR_PREFIX = 'Error while parsing #{} macro'

def nest_macros(template, *values):
    nested_macros = ['#IF(#EVAL1)({})'.format(v) for v in values]
    return template.format(*nested_macros)

class CommonSkoolMacroTest:
    def _check_call(self, writer, params, *args):
        macro = '#CALL:test_call({})'.format(params)
        cwd = ('<cwd>',) if isinstance(writer, HtmlWriter) else ()
        self.assertEqual(writer.expand(macro, *cwd), writer.test_call(*(cwd + args)))

    def test_macro_call(self):
        writer = self._get_writer(warn=True)
        writer.test_call = self._test_call

        # All arguments given
        self._check_call(writer, '10,t,5', 10, 't', 5)

        # One argument omitted
        self._check_call(writer, '7,,test2', 7, None, 'test2')

        # Arithmetic expressions
        self._check_call(writer, '7+2*5,12-4/2,3**3', 17, 10, 27)
        self._check_call(writer, '6&3|5,7^5,4%2', 7, 2, 0)
        self._check_call(writer, '1<<4,16>>4', 16, 1, None)
        self._check_call(writer, '1 + 1, (3 + 5) / 2, 4 * (9 - 7)', 2, 4, 8)

        # Nested macros
        value = 12345
        params = nest_macros('{0},{0}+1,{0}+2', value)
        self._check_call(writer, params, value, value + 1, value + 2)

        # Non-arithmetic Python expressions
        self._check_call(writer, '"a"+"b",None,sys.exit()', '"a"+"b"', 'None', 'sys.exit()')

        # No arguments
        writer.test_call_no_args = self._test_call_no_args
        output = writer.expand('#CALL:test_call_no_args()')
        self.assertEqual(output, 'OK')

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
        writer.var = 'x'
        prefix = ERROR_PREFIX.format('CALL')

        self._assert_error(writer, '#CALL', 'No parameters', prefix)
        self._assert_error(writer, '#CALLtest_call(5,s)', 'Malformed macro: #CALLt...', prefix)
        self._assert_error(writer, '#CALL:(0)', 'No method name', prefix)
        self._assert_error(writer, '#CALL:var(0)', 'Uncallable method name: var', prefix)
        self._assert_error(writer, '#CALL:test_call', 'No argument list specified: #CALL:test_call', prefix)
        self._assert_error(writer, '#CALL:test_call(1,2', 'No closing bracket: (1,2', prefix)
        self._assert_error(writer, '#CALL:test_call(1)')
        self._assert_error(writer, '#CALL:test_call(1,2,3,4)')

    def test_macro_chr_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('CHR')

        self._assert_error(writer, '#CHR', 'No parameters (expected 1)', prefix)
        self._assert_error(writer, '#CHRx', 'No parameters (expected 1)', prefix)
        self._assert_error(writer, '#CHR()', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#CHR(x,y)', "Cannot parse integer 'x' in parameter string: 'x,y'", prefix)
        self._assert_error(writer, '#CHR(1,2)', "Too many parameters (expected 1): '1,2'", prefix)
        self._assert_error(writer, '#CHR(2 ...', 'No closing bracket: (2 ...', prefix)

    def test_macro_d(self):
        skool = """
            @start

            ; First routine
            c32768 RET

            ; Second routine
            c32769 RET

            c32770 RET
        """
        writer = self._get_writer(skool=skool)

        # Decimal address
        output = writer.expand('#D32768')
        self.assertEqual(output, 'First routine')

        # Hexadecimal address
        output = writer.expand('#D$8001')
        self.assertEqual(output, 'Second routine')

        # Arithmetic expression
        output = writer.expand('#D($8000 + 2 * 3 - (10 + 5) / 3)')
        self.assertEqual(output, 'Second routine')

        # Nested macros
        output = writer.expand(nest_macros('#D({})', 32768))
        self.assertEqual(output, 'First routine')

        # Adjacent characters
        self.assertEqual(writer.expand('1+#D32768+1'), '1+First routine+1')
        self.assertEqual(writer.expand('+1#D(32768)1+'), '+1First routine1+')

    def test_macro_d_invalid(self):
        skool = '@start\nc32770 RET'
        writer = self._get_writer(skool=skool)
        prefix = ERROR_PREFIX.format('D')

        self._assert_error(writer, '#D', 'No parameters (expected 1)', prefix)
        self._assert_error(writer, '#Dx', 'No parameters (expected 1)', prefix)
        self._assert_error(writer, '#D32770', 'Entry at 32770 has no description', prefix)
        self._assert_error(writer, '#D32771', 'Cannot determine description for non-existent entry at 32771', prefix)

    def test_macro_eval(self):
        writer = self._get_writer()

        # Decimal
        self.assertEqual(writer.expand('#EVAL5'), '5')
        self.assertEqual(writer.expand('#EVAL(5 + 2 * (2 + 1) - ($13 - 1) / 3)'), '5')
        self.assertEqual(writer.expand('#EVAL5,10'), '5')
        self.assertEqual(writer.expand('#EVAL5,,5'), '00005')

        # Hexadecimal
        self.assertEqual(writer.expand('#EVAL10,16'), 'A')
        self.assertEqual(writer.expand('#EVAL(31 + 2 * (4 - 1) - ($11 + 1) / 3, 16)'), '1F')
        self.assertEqual(writer.expand('#EVAL10,16,2'), '0A')

        # Binary
        self.assertEqual(writer.expand('#EVAL10,2'), '1010')
        self.assertEqual(writer.expand('#EVAL(15 + 2 * (5 - 2) - ($10 + 2) / 3, 2)'), '1111')
        self.assertEqual(writer.expand('#EVAL16,2,8'), '00010000')

        # Nested macros
        self.assertEqual(writer.expand(nest_macros('#EVAL({})', '5+5')), '10')
        self.assertEqual(writer.expand(nest_macros('#EVAL(5+5,{})', '8+8')), 'A')
        self.assertEqual(writer.expand(nest_macros('#EVAL(5+5,16,{})', '1+1')), '0A')

        # Hexadecimal lower case
        writer = self._get_writer(case=CASE_LOWER)
        self.assertEqual(writer.expand('#EVAL57005,16'), 'dead')

    def test_macro_eval_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('EVAL')

        self._assert_error(writer, '#EVAL', 'No parameters (expected 1)', prefix)
        self._assert_error(writer, '#EVAL()', 'No parameters (expected 1)', prefix)
        self._assert_error(writer, '#EVALx', 'No parameters (expected 1)', prefix)

        self._assert_error(writer, '#EVAL,', "Missing required parameter in position 1/1: ','", prefix)
        self._assert_error(writer, '#EVAL(,)', "Missing required parameter in position 1/1: ','", prefix)
        self._assert_error(writer, '#EVAL,16', "Missing required parameter in position 1/1: ',16'", prefix)
        self._assert_error(writer, '#EVAL(,16)', "Missing required parameter in position 1/1: ',16'", prefix)

        self._assert_error(writer, '#EVAL(1,10,5,8)', "Too many parameters (expected 3): '1,10,5,8'", prefix)

        self._assert_error(writer, '#EVAL(1,x)', "Cannot parse integer 'x' in parameter string: '1,x'", prefix)
        self._assert_error(writer, '#EVAL(1,,x)', "Cannot parse integer 'x' in parameter string: '1,,x'", prefix)

        self._assert_error(writer, '#EVAL5,3', 'Invalid base (3): 5,3', prefix)

    def test_macro_font_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('FONT')

        self._test_invalid_image_macro(writer, '#FONT', 'No parameters (expected 1)', prefix)
        self._test_invalid_image_macro(writer, '#FONT()', 'No parameters (expected 1)', prefix)
        self._test_invalid_image_macro(writer, '#FONT:', 'No text parameter', prefix)
        self._test_invalid_image_macro(writer, '#FONT:()0', 'Empty message: ()', prefix)

        self._test_invalid_image_macro(writer, '#FONT,10', "Missing required argument 'addr': ',10'", prefix)
        self._test_invalid_image_macro(writer, '#FONT(,10)', "Missing required argument 'addr': ',10'", prefix)
        self._test_invalid_image_macro(writer, '#FONTscale=4', "Missing required argument 'addr': 'scale=4'", prefix)
        self._test_invalid_image_macro(writer, '#FONT(scale=4)', "Missing required argument 'addr': 'scale=4'", prefix)
        self._test_invalid_image_macro(writer, '#FONT,scale=4', "Missing required argument 'addr': ',scale=4'", prefix)
        self._test_invalid_image_macro(writer, '#FONT(,scale=4)', "Missing required argument 'addr': ',scale=4'", prefix)

        self._test_invalid_image_macro(writer, '#FONT0,1,2,3,4,5', "Too many parameters (expected 4): '0,1,2,3,4,5'", prefix)
        self._test_invalid_image_macro(writer, '#FONT0{0,0,23,14,5}(foo)', "Too many parameters in cropping specification (expected 4 at most): {0,0,23,14,5}", prefix)

        self._test_invalid_image_macro(writer, '#FONT(foo)', "Cannot parse integer 'foo' in parameter string: 'foo'", prefix)

        self._test_invalid_image_macro(writer, '#FONT0{0,0,23,14(foo)', 'No closing brace on cropping specification: {0,0,23,14(foo)', prefix)
        self._test_invalid_image_macro(writer, '#FONT0(foo', 'No closing bracket: (foo', prefix)
        self._test_invalid_image_macro(writer, '#FONT:[hi)0', 'No closing bracket: [hi)0', prefix)

    def test_macro_for(self):
        writer = self._get_writer()

        # Default step
        output = writer.expand('#FOR1,3(n,n)')
        self.assertEqual(output, '123')

        # Step
        output = writer.expand('#FOR1,5,2(n,n)')
        self.assertEqual(output, '135')

        # Brackets and commas in output
        output = writer.expand('(1)#FOR5,13,4//n/, (n)//')
        self.assertEqual(output, '(1), (5), (9), (13)')

        # Alternative delimiters
        for delim1, delim2 in (('[', ']'), ('{', '}')):
            output = writer.expand('1; #FOR4,10,3{}@n,@n; {}13'.format(delim1, delim2))
            self.assertEqual(output, '1; 4; 7; 10; 13')

        # Alternative separator
        output = writer.expand('1, #FOR4,10,3/|@n|@n, |/13')
        self.assertEqual(output, '1, 4, 7, 10, 13')

        # Arithmetic expression in 'start' parameter
        output = writer.expand('#FOR(10 - (20 + 7) / 3, 3)(n,n)')
        self.assertEqual(output, '123')

        # Arithmetic expression in 'stop' parameter
        output = writer.expand('#FOR(1, (5 + 1) / 2)(n,n)')
        self.assertEqual(output, '123')

        # Arithmetic expression in 'step' parameter
        output = writer.expand('#FOR(1, 13, 2 * (1 + 2))(n,[n])')
        self.assertEqual(output, '[1][7][13]')

        # Nested macros
        self.assertEqual(writer.expand(nest_macros('#FOR({},3)(n,n)', 1)), '123')
        self.assertEqual(writer.expand(nest_macros('#FOR(1,{})(n,n)', 3)), '123')
        self.assertEqual(writer.expand(nest_macros('#FOR(1,3,{})(n,n)', 2)), '13')
        self.assertEqual(writer.expand(nest_macros('#FOR(1,3)||n|{}||', 'n')), '123')

        # Commas inside brackets
        self.assertEqual(writer.expand('#FOR0,1(n,(0,n),:)'), '(0,0):(0,1)')
        self.assertEqual(writer.expand('#FOR0,1(n,#FOR(0,1)(m,(n,m),;),;)'), '(0,0);(0,1);(1,0);(1,1)')

    def test_macro_for_with_separator(self):
        writer = self._get_writer()

        # One value
        output = writer.expand('#FOR1,1($s,$s,+)')
        self.assertEqual(output, '1')

        # More than one value
        output = writer.expand('{ #FOR1,5(n,n, | ) }')
        self.assertEqual(output, '{ 1 | 2 | 3 | 4 | 5 }')

        # Separator contains a comma
        output = writer.expand('#FOR6,10//n/(n)/, //')
        self.assertEqual(output, '(6), (7), (8), (9), (10)')

    def test_macro_for_with_final_separator(self):
        writer = self._get_writer()

        # One value
        output = writer.expand('#FOR1,1($s,$s,+,-)')
        self.assertEqual(output, '1')

        # Two values
        output = writer.expand('#FOR1,2($s,$s,+,-)')
        self.assertEqual(output, '1-2')

        # Three values
        output = writer.expand('#FOR1,3//$s/$s/, / and //')
        self.assertEqual(output, '1, 2 and 3')

    def test_macro_for_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('FOR')

        self._assert_error(writer, '#FOR', 'No parameters (expected 2)', prefix)
        self._assert_error(writer, '#FOR()', 'No parameters (expected 2)', prefix)

        self._assert_error(writer, '#FOR0', "Not enough parameters (expected 2): '0'", prefix)
        self._assert_error(writer, '#FOR(0)', "Not enough parameters (expected 2): '0'", prefix)

        self._assert_error(writer, '#FOR,1(n,n)', "Missing required parameter in position 1/2: ',1'", prefix)
        self._assert_error(writer, '#FOR(,1)(n,n)', "Missing required parameter in position 1/2: ',1'", prefix)
        self._assert_error(writer, '#FOR0,(n,n)', "Missing required parameter in position 2/2: '0,'", prefix)
        self._assert_error(writer, '#FOR(0,)(n,n)', "Missing required parameter in position 2/2: '0,'", prefix)

        self._assert_error(writer, '#FOR0,1', 'No variable name: 0,1', prefix)
        self._assert_error(writer, '#FOR0,1()', "No variable name: 0,1()", prefix)

        self._assert_error(writer, '#FOR0,1(n,n', 'No closing bracket: (n,n', prefix)

    def test_macro_foreach(self):
        writer = self._get_writer()

        # No values
        output = writer.expand('#FOREACH()($s,$s)')
        self.assertEqual(output, '')

        # One value
        output = writer.expand('#FOREACH(a)($s,[$s])')
        self.assertEqual(output, '[a]')

        # Two values
        output = writer.expand('#FOREACH(a,b)($s,<$s>)')
        self.assertEqual(output, '<a><b>')

        # Three values
        output = writer.expand('#FOREACH(a,b,c)($s,*$s*)')
        self.assertEqual(output, '*a**b**c*')

        # Values containing commas
        output = writer.expand('#FOREACH//a,/b,/c//($s,$s)')
        self.assertEqual(output, 'a,b,c')

        # Nested macros
        output = writer.expand(nest_macros('#FOREACH(0,1,2)||n|({})||', 'n'))
        self.assertEqual(output, '(0)(1)(2)')

        # Commas inside brackets
        self.assertEqual(writer.expand('#FOREACH(0,1)(n,(0,n),:)'), '(0,0):(0,1)')
        self.assertEqual(writer.expand('#FOREACH(0,1)(n,#FOREACH(0,1)(m,(n,m),;),;)'), '(0,0);(0,1);(1,0);(1,1)')
        self.assertEqual(writer.expand('#FOREACH((0,0),(1,1))(n,(0,n),|)'), '(0,(0,0))|(0,(1,1))')

    def test_macro_foreach_with_separator(self):
        writer = self._get_writer()

        # No values
        output = writer.expand('#FOREACH()($s,$s,.)')
        self.assertEqual(output, '')

        # One value
        output = writer.expand('#FOREACH(a)($s,$s,.)')
        self.assertEqual(output, 'a')

        # Two values
        output = writer.expand('#FOREACH(a,b)($s,$s,+)')
        self.assertEqual(output, 'a+b')

        # Three values
        output = writer.expand('#FOREACH(a,b,c)($s,$s,-)')
        self.assertEqual(output, 'a-b-c')

        # Separator contains a comma
        output = writer.expand('#FOREACH(a,b,c)//$s/[$s]/, //')
        self.assertEqual(output, '[a], [b], [c]')

    def test_macro_foreach_with_final_separator(self):
        writer = self._get_writer()

        # No values
        output = writer.expand('#FOREACH()($s,$s,+,-)')
        self.assertEqual(output, '')

        # One value
        output = writer.expand('#FOREACH(a)($s,$s,+,-)')
        self.assertEqual(output, 'a')

        # Two values
        output = writer.expand('#FOREACH(a,b)($s,$s,+,-)')
        self.assertEqual(output, 'a-b')

        # Three values
        output = writer.expand('#FOREACH(a,b,c)//$s/$s/, / and //')
        self.assertEqual(output, 'a, b and c')

    def test_macro_foreach_with_entry(self):
        skool = """
            @start
            b30000 DEFB 1,2,3

            c30003 RET

            g30004 DEFB 0

            s30005 DEFS 5

            c30010 RET

            b30011 DEFB 4,5,6

            t30014 DEFM "Hey"

            u30017 DEFS 3

            w30020 DEFW 10000,20000

            c30024 RET
        """
        writer = self._get_writer(skool=skool)

        # All entries
        output = writer.expand('#FOREACH(ENTRY)||e|e|, ||')
        self.assertEqual(output, '30000, 30003, 30004, 30005, 30010, 30011, 30014, 30017, 30020, 30024')

        # Just code
        output = writer.expand('#FOREACH(ENTRYc)||e|e|, ||')
        self.assertEqual(output, '30003, 30010, 30024')

        # Code and text
        output = writer.expand('#FOREACH(ENTRYct)||e|e|, ||')
        self.assertEqual(output, '30003, 30010, 30014, 30024')

        # Everything but code and text
        output = writer.expand('#FOREACH(ENTRYbgsuw)||e|e|, ||')
        self.assertEqual(output, '30000, 30004, 30005, 30011, 30017, 30020')

        # Non-existent
        output = writer.expand('#FOREACH(ENTRYq)||e|e|, ||')
        self.assertEqual(output, '')

    def test_macro_foreach_with_eref(self):
        skool = """
            @start
            c30000 CALL 30004

            c30003 LD A,B
             30004 LD B,C

            c30005 JP 30004

            c30008 JR 30004
        """
        writer = self._get_writer(skool=skool)

        cwd = ('asm',) if isinstance(writer, HtmlWriter) else ()
        exp_output = writer.expand('#R30000, #R30005 and #R30008', *cwd)
        macro_t = '#FOREACH[EREF{}]||addr|#Raddr|, | and ||'

        # Decimal address
        output = writer.expand(macro_t.format(30004), *cwd)
        self.assertEqual(output, exp_output)

        # Hexadecimal address
        output = writer.expand(macro_t.format('$7534'), *cwd)
        self.assertEqual(output, exp_output)

        # Arithmetic expression
        output = writer.expand(macro_t.format('30000 + 8 * (7 + 1) - ($79 - 1) / 2'), *cwd)
        self.assertEqual(output, exp_output)

    def test_macro_foreach_with_eref_invalid(self):
        writer = self._get_writer(skool='')
        self.assertEqual(writer.expand('#FOREACH(EREFx)(n,n)'), 'EREFx')
        self.assertEqual(writer.expand('#FOREACH[EREF(x)](n,n)'), 'EREF(x)')

    def test_macro_foreach_with_ref(self):
        skool = """
            @start
            ; Used by the routines at 9, 89 and 789
            c00001 LD A,B
             00002 RET

            c00009 CALL 1

            c00089 CALL 1

            c00789 JP 2
        """
        writer = self._get_writer(skool=skool)

        cwd = ('asm',) if isinstance(writer, HtmlWriter) else ()
        exp_output = writer.expand('#R9, #R89 and #R789', *cwd)
        macro_t = '#FOREACH[REF{}]||addr|#Raddr|, | and ||'

        # Decimal address
        output = writer.expand(macro_t.format(1), *cwd)
        self.assertEqual(output, exp_output)

        # Hexadecimal address
        output = writer.expand(macro_t.format('$0001'), *cwd)
        self.assertEqual(output, exp_output)

        # Arithmetic expression
        output = writer.expand(macro_t.format('(1 + 5 * (2 + 3) - ($63 + 1) / 4)'), *cwd)
        self.assertEqual(output, exp_output)

    def test_macro_foreach_with_ref_invalid(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#FOREACH(REFx)(n,n)'), 'REFx')
        self.assertEqual(writer.expand('#FOREACH[REF(x)](n,n)'), 'REF(x)')

    def test_macro_foreach_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('FOREACH')

        self._assert_error(writer, '#FOREACH', 'No values', prefix)
        self._assert_error(writer, '#FOREACH()', 'No variable name: ()', prefix)
        self._assert_error(writer, '#FOREACH()()', 'No variable name: ()()', prefix)
        self._assert_error(writer, '#FOREACH(a,b[$s,$s]', 'No closing bracket: (a,b[$s,$s]', prefix)
        self._assert_error(writer, '#FOREACH(a,b)($s,$s', 'No closing bracket: ($s,$s', prefix)
        self._assert_error(writer, '#FOREACH(REF$81A4)(n,n)', 'No entry at 33188: REF$81A4', prefix)

    def test_macro_html_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('HTML')

        self._assert_error(writer, '#HTML', 'No text parameter', prefix)
        self._assert_error(writer, '#HTML:unterminated', 'No terminating delimiter: :unterminated', prefix)

    def test_macro_if(self):
        writer = self._get_writer()

        # Integers
        self.assertEqual(writer.expand('#IF1(Yes,No)'), 'Yes')
        self.assertEqual(writer.expand('#IF(0)(Yes,No)'), 'No')

        # Arithmetic expressions
        self.assertEqual(writer.expand('#IF(1+2*3+4/2)(On,Off)'), 'On')
        self.assertEqual(writer.expand('#IF(1+2*3-49/7)(On,Off)'), 'Off')
        self.assertEqual(writer.expand('#IF(2&5|1)(On,Off)'), 'On')
        self.assertEqual(writer.expand('#IF(7^7)(On,Off)'), 'Off')
        self.assertEqual(writer.expand('#IF(3%2)(On,Off)'), 'On')
        self.assertEqual(writer.expand('#IF(2>>2)(On,Off)'), 'Off')
        self.assertEqual(writer.expand('#IF(1<<2)(On,Off)'), 'On')

        # Equalities and inequalities
        self.assertEqual(writer.expand('#IF(0==0)||(True)|(False)||'), '(True)')
        self.assertEqual(writer.expand('#IF(0!=0)||(True)|(False)||'), '(False)')
        self.assertEqual(writer.expand('#IF(1<2)||(True)|(False)||'), '(True)')
        self.assertEqual(writer.expand('#IF(1>2)||(True)|(False)||'), '(False)')
        self.assertEqual(writer.expand('#IF(3<=4)||(True)|(False)||'), '(True)')
        self.assertEqual(writer.expand('#IF(3>=4)||(True)|(False)||'), '(False)')

        # Arithmetic expressions in equalities and inequalities
        self.assertEqual(writer.expand('#IF(1+2==6-3)||(Y)|(N)||'), '(Y)')
        self.assertEqual(writer.expand('#IF(1+2!=6-3)||(Y)|(N)||'), '(N)')
        self.assertEqual(writer.expand('#IF(3*3<4**5)||(Y)|(N)||'), '(Y)')
        self.assertEqual(writer.expand('#IF(3&3>4|5)||(Y)|(N)||'), '(N)')
        self.assertEqual(writer.expand('#IF(12/6<=12^4)||(Y)|(N)||'), '(Y)')
        self.assertEqual(writer.expand('#IF(12%6>=12/4)||(Y)|(N)||'), '(N)')
        self.assertEqual(writer.expand('#IF(1<<3>16>>2)||(Y)|(N)||'), '(Y)')

        # Arithmetic expressions with brackets and spaces
        self.assertEqual(writer.expand('#IF(3+(2*6)/4>(9-3)/3)||(Y)|(N)||'), '(Y)')
        self.assertEqual(writer.expand('#IF( 3 + (2 * 6) / 4 < (9 - 3) / 3 )||(Y)|(N)||'), '(N)')

        # Arithmetic expressions with && and ||
        self.assertEqual(writer.expand('#IF(5>4&&2!=3)(T,F)'), 'T')
        self.assertEqual(writer.expand('#IF(4 > 5 || 3 < 3)(T,F)'), 'F')
        self.assertEqual(writer.expand('#IF(2==2&&4>5||3<4)(T,F)'), 'T')

        # Nested macros
        self.assertEqual(writer.expand(nest_macros('#IF({})(y,n)', 1)), 'y')
        self.assertEqual(writer.expand(nest_macros('#IF1||{}|n||', 'y')), 'y')
        self.assertEqual(writer.expand(nest_macros('#IF0||y|{}||', 'n')), 'n')

        # Multi-line output strings
        self.assertEqual(writer.expand('#IF1(foo\nbar,baz\nqux)'), 'foo\nbar')
        self.assertEqual(writer.expand('#IF0(foo\nbar,baz\nqux)'), 'baz\nqux')

        # No 'false' parameter
        self.assertEqual(writer.expand('#IF1(aye)'), 'aye')
        self.assertEqual(writer.expand('#IF0(aye)'), '')
        self.assertEqual(writer.expand('#IF1()'), '')
        self.assertEqual(writer.expand('#IF0()'), '')

        # Commas inside brackets
        self.assertEqual(writer.expand('#IF1((0,1),(1,2))'), '(0,1)')
        self.assertEqual(writer.expand('#IF1(#IF0(0,1),2)'), '1')

    def test_macro_if_base_none(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#IF({base}==0)(PASS,FAIL)'), 'PASS')

    def test_macro_if_base_10(self):
        writer = self._get_writer(base=BASE_10)
        self.assertEqual(writer.expand('#IF({base}==10)(PASS,FAIL)'), 'PASS')

    def test_macro_if_base_16(self):
        writer = self._get_writer(base=BASE_16)
        self.assertEqual(writer.expand('#IF({base}==16)(PASS,FAIL)'), 'PASS')

    def test_macro_if_case_none(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#IF({case}==0)(PASS,FAIL)'), 'PASS')

    def test_macro_if_case_lower(self):
        writer = self._get_writer(case=CASE_LOWER)
        self.assertEqual(writer.expand('#IF({case}==1)(PASS,FAIL)'), 'PASS')

    def test_macro_if_case_upper(self):
        writer = self._get_writer(case=CASE_UPPER)
        self.assertEqual(writer.expand('#IF({case}==2)(PASS,FAIL)'), 'PASS')

    def test_macro_if_variables(self):
        writer = self._get_writer(skool='', variables=('foo=1', 'bar=2'))
        self.assertEqual(writer.expand('#IF({vars[foo]}==1)(PASS,FAIL)'), 'PASS')
        self.assertEqual(writer.expand('#IF({vars[bar]}==2)(PASS,FAIL)'), 'PASS')
        self.assertEqual(writer.expand('#IF({vars[baz]})(FAIL,PASS)'), 'PASS')

    def test_macro_if_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('IF')

        self._assert_error(writer, '#IF', "No valid expression found: '#IF'", prefix)
        self._assert_error(writer, '#IFx', "No valid expression found: '#IFx'", prefix)
        self._assert_error(writer, '#IF({asm)(1,0)', "Invalid expression: ({asm)", prefix)
        self._assert_error(writer, '#IF(0)', "No output strings: (0)", prefix)
        self._assert_error(writer, '#IF(0)(true,false,other)', "Too many output strings (expected 2): (0)(true,false,other)", prefix)
        self._assert_error(writer, '#IF1(true,false', "No closing bracket: (true,false", prefix)
        self._assert_error(writer, '#IF({vase})(true,false)', "Unrecognised field 'vase': ({vase})", prefix)

    def test_macro_include_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('INCLUDE')

        self._assert_error(writer, '#INCLUDE', "No text parameter", prefix)
        self._assert_error(writer, '#INCLUDE0', "No text parameter", prefix)
        self._assert_error(writer, '#INCLUDE(0)', "No text parameter", prefix)

    def test_macro_link_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('LINK')

        self._assert_error(writer, '#LINK', 'No parameters', prefix)
        self._assert_error(writer, '#LINK:', 'No page ID: #LINK:', prefix)
        self._assert_error(writer, '#LINK:(text)', 'No page ID: #LINK:(text)', prefix)
        self._assert_error(writer, '#LINK:(text', 'No closing bracket: (text', prefix)
        self._assert_error(writer, '#LINKpageID', 'Malformed macro: #LINKp...', prefix)
        self._assert_error(writer, '#LINK:Bugs', 'No link text: #LINK:Bugs', prefix)

        return writer, prefix

    def test_macro_map(self):
        writer = self._get_writer()

        # Key exists
        output = writer.expand('#MAP2(?,1:a,2:b,3:c)')
        self.assertEqual(output, 'b')

        # Key doesn't exist
        output = writer.expand('#MAP0(?,1:a,2:b,3:c)')
        self.assertEqual(output, '?')

        # Blank default and no keys
        output = writer.expand('#MAP1()')
        self.assertEqual(output, '')

        # No keys
        output = writer.expand('#MAP5(*)')
        self.assertEqual(output, '*')

        # Blank default value and no keys
        output = writer.expand('#MAP2()')
        self.assertEqual(output, '')

        # Key without value (defaults to key)
        output = writer.expand('#MAP7(0,1,7)')
        self.assertEqual(output, '7')

        # Arithmetic expression in 'value' parameter
        self.assertEqual(writer.expand('#MAP(2 * (2 + 1) + (11 - 3) / 2 - 4)(?,6:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP(4**3)(?,64:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP(5&3|4)(?,5:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP(5^7)(?,2:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP(4%3)(?,1:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP(2<<2)(?,8:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP(4>>2)(?,1:OK)'), 'OK')

        # Arithmetic expression in mapping key
        self.assertEqual(writer.expand('#MAP6||?|(1 + 1) * 3 + (12 - 4) / 2 - 4:OK||'), 'OK')
        self.assertEqual(writer.expand('#MAP64(?,4**3:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP5(?,5&3|4:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP2(?,5^7:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP1(?,4%3:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP8(?,2<<2:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP1(?,4>>2:OK)'), 'OK')

        # Nested macros
        self.assertEqual(writer.expand(nest_macros('#MAP({})(0,1:2)', 1)), '2')
        self.assertEqual(writer.expand(nest_macros('#MAP0//{}/1:2//', 3)), '3')
        self.assertEqual(writer.expand(nest_macros('#MAP#(1//0/{}:2//)', 1)), '2')
        self.assertEqual(writer.expand(nest_macros('#MAP1//0/1:{}//', 2)), '2')

        # Alternative delimiters
        for delim1, delim2 in (('[', ']'), ('{', '}')):
            output = writer.expand('#MAP1{}?,0:A,1:OK,2:C{}'.format(delim1, delim2))
            self.assertEqual(output, 'OK')

        # Alternative separator
        output = writer.expand('#MAP1|;?;0:A;1:Oh, OK;2:C;|')
        self.assertEqual(output, 'Oh, OK')

    def test_macro_map_base_none(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#MAP({base})(FAIL,0:PASS)'), 'PASS')

    def test_macro_map_base_10(self):
        writer = self._get_writer(base=BASE_10)
        self.assertEqual(writer.expand('#MAP({base})(FAIL,10:PASS)'), 'PASS')

    def test_macro_map_base_16(self):
        writer = self._get_writer(base=BASE_16)
        self.assertEqual(writer.expand('#MAP({base})(FAIL,16:PASS)'), 'PASS')

    def test_macro_map_case_none(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#MAP({case})(FAIL,0:PASS)'), 'PASS')

    def test_macro_map_case_lower(self):
        writer = self._get_writer(case=CASE_LOWER)
        self.assertEqual(writer.expand('#MAP({case})(FAIL,1:PASS)'), 'PASS')

    def test_macro_map_case_upper(self):
        writer = self._get_writer(case=CASE_UPPER)
        self.assertEqual(writer.expand('#MAP({case})(FAIL,2:PASS)'), 'PASS')

    def test_macro_map_variables(self):
        writer = self._get_writer(skool='', variables=('foo=1', 'bar=2'))
        self.assertEqual(writer.expand('#MAP({vars[foo]})(FAIL,1:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({vars[bar]})(FAIL,2:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({vars[baz]})(FAIL,0:PASS)'), 'PASS')

    def test_macro_map_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('MAP')

        self._assert_error(writer, '#MAP', "No valid expression found: '#MAP'", prefix)
        self._assert_error(writer, '#MAPq', "No valid expression found: '#MAPq'", prefix)
        self._assert_error(writer, '#MAP({html)(0)', "Invalid expression: ({html)", prefix)
        self._assert_error(writer, '#MAP0', "No mappings provided: 0", prefix)
        self._assert_error(writer, '#MAP0 ()', "No mappings provided: 0", prefix)
        self._assert_error(writer, '#MAP0(1,2:3', "No closing bracket: (1,2:3", prefix)
        self._assert_error(writer, '#MAP0(1,x1:3)', "Invalid key (x1): (1,x1:3)", prefix)
        self._assert_error(writer, '#MAP({ease})(0)', "Unrecognised field 'ease': ({ease})", prefix)

    def test_macro_n_decimal(self):
        for base in (None, BASE_10):
            for case in (None, CASE_LOWER, CASE_UPPER):
                writer = self._get_writer(base=base, case=case)
                for params, exp_output in (
                    ('12', '12'),
                    ('13579', '13579'),
                    ('23,4', '23'),
                    ('34,4,5', '00034'),
                    ('45,,,1(0x)', '45'),
                    ('56,,,1[,h]', '56'),
                    ('23456,,,1//$/H//', '23456')
                ):
                    self.assertEqual(writer.expand('#N{}'.format(params)), exp_output,
                                     "base={}, case={}".format(base, case))

    def test_macro_n_hex_lower(self):
        writer = self._get_writer(base=BASE_16, case=CASE_LOWER)
        for params, exp_output in (
            ('12', '0c'),
            ('12($)', '0c($)'),
            ('13579', '350b'),
            ('13,4', '000d'),
            ('14,4,5', '000e'),
            ('15,,,1(0x)', '0x0f'),
            ('26,,,1[,h]', '1ah'),
            ('27,,,1||$|H||', '$1bH'),
            ('13580,,,1($)', '$350c'),
            ('13581,,,1{,h}', '350dh'),
            ('13582,,,1::0x:H::', '0x350eH')
        ):
            self.assertEqual(writer.expand('#N{}'.format(params)), exp_output)

    def test_macro_n_hex_upper(self):
        for case in (None, CASE_UPPER):
            writer = self._get_writer(base=BASE_16, case=case)
            for params, exp_output in (
                ('12', '0C'),
                ('12($)', '0C($)'),
                ('13579', '350B'),
                ('13,4', '000D'),
                ('14,4,5', '000E'),
                ('15,,,1(0x)', '0x0F'),
                ('26,,,1(,h)', '1Ah'),
                ('27,,,1{$,H}', '$1BH'),
                ('13580,,,1;;$;;', '$350C'),
                ('13581,,,1(,h)', '350Dh'),
                ('13582,,,1! 0x H !', '0x350EH')
            ):
                self.assertEqual(writer.expand('#N{}'.format(params)), exp_output, 'case={}'.format(case))

    def test_macro_n_hex_param(self):
        for base, value, exp_output in (
            (None, 26, '1A'),
            (BASE_10, 42, '42'),
            (BASE_16, 58, '3A')
        ):
            writer = self._get_writer(base=base)
            self.assertEqual(writer.expand('#N{},,,,1'.format(value)), exp_output)

    def test_macro_n_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('N')

        self._assert_error(writer, '#N', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#N()', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#N(4,3,2,1)', "No text parameter", prefix)

        self._assert_error(writer, '#N,', "Missing required parameter in position 1/1: ','", prefix)
        self._assert_error(writer, '#N(,)', "Missing required parameter in position 1/1: ','", prefix)
        self._assert_error(writer, '#N,4', "Missing required parameter in position 1/1: ',4'", prefix)
        self._assert_error(writer, '#N(,4)', "Missing required parameter in position 1/1: ',4'", prefix)

        self._assert_error(writer, '#N(1,2,3,4,5,6)', "Too many parameters (expected 5): '1,2,3,4,5,6'", prefix)
        self._assert_error(writer, '#N(4,3,2,1)(a,b,c)', "Too many parameters (expected 2): 'a,b,c'", prefix)

        self._assert_error(writer, '#N(x,4)', "Cannot parse integer 'x' in parameter string: 'x,4'", prefix)

        self._assert_error(writer, '#N(2', "No closing bracket: (2", prefix)

    def test_macro_peek(self):
        writer = self._get_writer(snapshot=[1, 2, 3])

        output = writer.expand('#PEEK0')
        self.assertEqual(output, '1')

        output = writer.expand('#PEEK($0001)')
        self.assertEqual(output, '2')

        # Arithmetic expression
        self.assertEqual(writer.expand('#PEEK($0001 + (5 + 3) / 2 - (14 - 2) / 3)'), '2')

        # Address is taken modulo 65536
        output = writer.expand('#PEEK65538')
        self.assertEqual(output, '3')

        # Nested macros
        self.assertEqual(writer.expand(nest_macros('#PEEK({})', 2)), '3')

    def test_macro_peek_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('PEEK')

        self._assert_error(writer, '#PEEK', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#PEEK()', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#PEEK(3', "No closing bracket: (3", prefix)
        self._assert_error(writer, '#PEEK(4,5)', "Too many parameters (expected 1): '4,5'", prefix)

    def test_macro_pokes(self):
        writer = self._get_writer(snapshot=[0] * 20)
        snapshot = writer.snapshot

        # addr, byte
        output = writer.expand('#POKES0,255')
        self.assertEqual(output, '')
        self.assertEqual(snapshot[0], 255)

        # addr, byte, length
        output = writer.expand('#POKES0,254,10')
        self.assertEqual(output, '')
        self.assertEqual([254] * 10, snapshot[0:10])

        # addr, byte, length, step
        output = writer.expand('#POKES0,253,10,2')
        self.assertEqual(output, '')
        self.assertEqual([253] * 10, snapshot[0:20:2])

        # Two POKEs
        output = writer.expand('#POKES1,1;2,2')
        self.assertEqual(output, '')
        self.assertEqual([1, 2], snapshot[1:3])

        # Arithmetic expressions
        output = writer.expand('#POKES(1 + 1, 3 * 4, 10 - (1 + 1) * 2, (11 + 1) / 4)')
        self.assertEqual(output, '')
        self.assertEqual([12] * 6, snapshot[2:18:3])

        # Nested macros
        output = writer.expand(nest_macros('#POKES({},1)', 0))
        self.assertEqual(output, '')
        self.assertEqual(writer.snapshot[0], 1)

        # #() macro
        output = writer.expand('#POKES#(#FOR0,19||n|n,n|;||)')
        self.assertEqual(output, '')
        self.assertEqual(list(range(20)), writer.snapshot[0:20])

    def test_macro_pokes_invalid(self):
        writer = self._get_writer(snapshot=[0])
        prefix = ERROR_PREFIX.format('POKES')

        self._assert_error(writer, '#POKES', 'No parameters (expected 2)', prefix)
        self._assert_error(writer, '#POKES()', 'No parameters (expected 2)', prefix)

        self._assert_error(writer, '#POKES0', "Not enough parameters (expected 2): '0'", prefix)
        self._assert_error(writer, '#POKES(0)', "Not enough parameters (expected 2): '0'", prefix)
        self._assert_error(writer, '#POKES0,1;1', "Not enough parameters (expected 2): '1'", prefix)
        self._assert_error(writer, '#POKES(0,1);(1)', "Not enough parameters (expected 2): '1'", prefix)

        self._assert_error(writer, '#POKES,0', "Missing required parameter in position 1/2: ',0'", prefix)
        self._assert_error(writer, '#POKES(,0)', "Missing required parameter in position 1/2: ',0'", prefix)
        self._assert_error(writer, '#POKES0,', "Missing required parameter in position 2/2: '0,'", prefix)
        self._assert_error(writer, '#POKES0,x', "Missing required parameter in position 2/2: '0,'", prefix)
        self._assert_error(writer, '#POKES(0,)', "Missing required parameter in position 2/2: '0,'", prefix)
        self._assert_error(writer, '#POKES0,,1', "Missing required parameter in position 2/2: '0,,1'", prefix)
        self._assert_error(writer, '#POKES(0,,1)', "Missing required parameter in position 2/2: '0,,1'", prefix)

        self._assert_error(writer, '#POKES(0,x)', "Cannot parse integer 'x' in parameter string: '0,x'", prefix)

    def test_macro_pops(self):
        writer = self._get_writer(snapshot=[0, 0])
        addr, byte = 1, 128
        writer.snapshot[addr] = byte
        writer.push_snapshot('test')
        writer.snapshot[addr] = (byte + 127) % 256
        output = writer.expand('#POPS')
        self.assertEqual(output, '')
        self.assertEqual(writer.snapshot[addr], byte)

    def test_macro_pops_empty_stack(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('POPS')
        self._assert_error(writer, '#POPS', 'Cannot pop snapshot when snapshot stack is empty', prefix)

    def test_macro_pushs(self):
        writer = self._get_writer(snapshot=[0])
        addr, byte = 0, 64
        for name in ('test', '#foo', 'foo$abcd', ''):
            for suffix in ('', ';bar', ':baz'):
                writer.snapshot[addr] = byte
                output = writer.expand('#PUSHS{}{}'.format(name, suffix))
                self.assertEqual(output, suffix)
                self.assertEqual(writer.snapshot[addr], byte)
                if hasattr(writer, 'get_snapshot_name'):
                    self.assertEqual(writer.get_snapshot_name(), name)
                writer.snapshot[addr] = (byte + 127) % 256
                writer.pop_snapshot()
                self.assertEqual(writer.snapshot[addr], byte)

        name = 'testnestedSMPLmacros'
        output = writer.expand(nest_macros('#PUSHS#({})', name))
        self.assertEqual(output, '')
        if hasattr(writer, 'get_snapshot_name'):
            self.assertEqual(writer.get_snapshot_name(), name)

    def test_macro_r_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('R')

        self._assert_error(writer, '#R', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#R@main', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#R#bar', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#R(baz)', "Cannot parse integer 'baz' in parameter string: 'baz'", prefix)
        self._assert_error(writer, '#R32768(qux', "No closing bracket: (qux", prefix)

        return writer, prefix

    def test_macro_raw(self):
        writer = self._get_writer()

        self.assertEqual(writer.expand('#RAW(#SPACE)'), '#SPACE')
        self.assertEqual(writer.expand('#RAW[#IF(1)(1)]'), '#IF(1)(1)')
        self.assertEqual(writer.expand('#RAW{12#FOR3,4(n,n)56}'), '12#FOR3,4(n,n)56')
        self.assertEqual(writer.expand('#RAW/12#FOREACH(3,4)(m,m)56/'), '12#FOREACH(3,4)(m,m)56')

    def test_macro_raw_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('RAW')

        self._assert_error(writer, '#RAW', 'No text parameter', prefix)
        self._assert_error(writer, '#RAW:unterminated', 'No terminating delimiter: :unterminated', prefix)

    def test_macro_reg(self):
        writer = self._get_writer()
        template = '<span class="register">{}</span>' if isinstance(writer, HtmlWriter) else '{}'

        # Upper case, all registers
        for reg in ('a', 'b', 'c', 'd', 'e', 'f', 'h', 'l', "a'", "b'", "c'", "d'", "e'", "f'", "h'", "l'", 'af', 'bc', 'de', 'hl',
                    "af'", "bc'", "de'", "hl'", 'ix', 'iy', 'ixh', 'iyh', 'ixl', 'iyl', 'i', 'r', 'sp', 'pc'):
            output = writer.expand('#REG{}'.format(reg))
            self.assertEqual(output, template.format(reg.upper()))

        # Nested macros
        output = writer.expand(nest_macros('#REG#({})', 'hl'))
        self.assertEqual(output, template.format('HL'))

        # Arbitrary text argument
        output = writer.expand("#REG(hlh'l')")
        self.assertEqual(output, template.format("HLH'L'"))
        output = writer.expand("#REG/hl(de)/")
        self.assertEqual(output, template.format("HL(DE)"))

        # Lower case
        writer = self._get_writer(case=CASE_LOWER)
        output = writer.expand('#REGhl')
        self.assertEqual(output, template.format('hl'))

        # Arbitrary text argument, lower case
        writer = self._get_writer(case=CASE_LOWER)
        output = writer.expand("#REG[ded'e']")
        self.assertEqual(output, template.format("ded'e'"))

    def test_macro_reg_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('REG')

        self._assert_error(writer, '#REG', 'Missing register argument', prefix)
        self._assert_error(writer, '#REG()', 'Missing register argument', prefix)
        self._assert_error(writer, '#REG||', 'Missing register argument', prefix)
        self._assert_error(writer, '#REG(bc', 'No closing bracket: (bc', prefix)
        self._assert_error(writer, '#REG/hl', 'No terminating delimiter: /hl', prefix)
        self._assert_error(writer, '#REGq', 'Bad register: "q"', prefix)
        self._assert_error(writer, "#REGx'", 'Bad register: "x\'"', prefix)

    def test_macro_scr_invalid(self):
        writer = self._get_writer(snapshot=[0] * 8)
        prefix = ERROR_PREFIX.format('SCR')

        self._test_invalid_image_macro(writer, '#SCR0,1,2,3,4,5,6,7,8', "Too many parameters (expected 7): '0,1,2,3,4,5,6,7,8'", prefix)
        self._test_invalid_image_macro(writer, '#SCR{0,0,23,14,5}(foo)', "Too many parameters in cropping specification (expected 4 at most): {0,0,23,14,5}", prefix)
        self._test_invalid_image_macro(writer, '#SCR{0,0,23,14(foo)', 'No closing brace on cropping specification: {0,0,23,14(foo)', prefix)
        self._test_invalid_image_macro(writer, '#SCR(foo', 'No closing bracket: (foo', prefix)

    def test_macro_space(self):
        writer = self._get_writer()
        space = '&#160;' if isinstance(writer, HtmlWriter) else ' '

        self.assertEqual(writer.expand('#SPACE'), space.strip())
        self.assertEqual(writer.expand('"#SPACE10"'), '"{}"'.format(space * 10))
        self.assertEqual(writer.expand('1#SPACE(7)1'), '1{}1'.format(space * 7))
        self.assertEqual(writer.expand('|#SPACE2+2|'), '|{}+2|'.format(space * 2))
        self.assertEqual(writer.expand('|#SPACE3-1|'), '|{}-1|'.format(space * 3))
        self.assertEqual(writer.expand('|#SPACE2*2|'), '|{}*2|'.format(space * 2))
        self.assertEqual(writer.expand('|#SPACE3/3|'), '|{}/3|'.format(space * 3))
        self.assertEqual(writer.expand('|#SPACE(1+3*2-10/2)|'), '|{}|'.format(space * 2))
        self.assertEqual(writer.expand('|#SPACE($01 + 3 * 2 - (7 + 3) / 2)|'), '|{}|'.format(space * 2))
        self.assertEqual(writer.expand(nest_macros('"#SPACE({})"', 5)), '"{}"'.format(space * 5))
        self.assertEqual(writer.expand('<#SPACE#(#EVAL3)>'), '<{}>'.format(space * 3))
        self.assertEqual(writer.expand('<#SPACE#(#(2))>'), '<{}>'.format(space * 2))

    def test_macro_space_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('SPACE')

        self._assert_error(writer, '#SPACE(2', "No closing bracket: (2", prefix)
        self._assert_error(writer, '#SPACE(5$3)', "Cannot parse integer '5$3' in parameter string: '5$3'", prefix)

    def test_macro_udg_invalid(self):
        writer = self._get_writer(snapshot=[0] * 8)
        prefix = ERROR_PREFIX.format('UDG')

        self._test_invalid_image_macro(writer, '#UDG', 'No parameters (expected 1)', prefix)
        self._test_invalid_image_macro(writer, '#UDG()', 'No parameters (expected 1)', prefix)

        self._test_invalid_image_macro(writer, '#UDG,5', "Missing required argument 'addr': ',5'", prefix)
        self._test_invalid_image_macro(writer, '#UDG(,5)', "Missing required argument 'addr': ',5'", prefix)
        self._test_invalid_image_macro(writer, '#UDGscale=2', "Missing required argument 'addr': 'scale=2'", prefix)
        self._test_invalid_image_macro(writer, '#UDG(scale=2)', "Missing required argument 'addr': 'scale=2'", prefix)
        self._test_invalid_image_macro(writer, '#UDG,scale=2', "Missing required argument 'addr': ',scale=2'", prefix)
        self._test_invalid_image_macro(writer, '#UDG(,scale=2)', "Missing required argument 'addr': ',scale=2'", prefix)
        self._test_invalid_image_macro(writer, '#UDG0:,2', "Missing required argument 'addr': ',2'", prefix)
        self._test_invalid_image_macro(writer, '#UDG0:(,2)', "Missing required argument 'addr': ',2'", prefix)
        self._test_invalid_image_macro(writer, '#UDG0:step=2', "Missing required argument 'addr': 'step=2'", prefix)
        self._test_invalid_image_macro(writer, '#UDG0:(step=2)', "Missing required argument 'addr': 'step=2'", prefix)
        self._test_invalid_image_macro(writer, '#UDG0:,step=2', "Missing required argument 'addr': ',step=2'", prefix)
        self._test_invalid_image_macro(writer, '#UDG0:(,step=2)', "Missing required argument 'addr': ',step=2'", prefix)

        self._test_invalid_image_macro(writer, '#UDG0,1,2,3,4,5,6,7,8,9', "Too many parameters (expected 8): '0,1,2,3,4,5,6,7,8,9'", prefix)
        self._test_invalid_image_macro(writer, '#UDG0:1,2,3', "Too many parameters (expected 2): '1,2,3'", prefix)
        self._test_invalid_image_macro(writer, '#UDG0{0,0,23,14,5}(foo)', "Too many parameters in cropping specification (expected 4 at most): {0,0,23,14,5}", prefix)

        self._test_invalid_image_macro(writer, '#UDG(foo)', "Cannot parse integer 'foo' in parameter string: 'foo'", prefix)

        self._test_invalid_image_macro(writer, '#UDG0{0,0,23,14(foo)', 'No closing brace on cropping specification: {0,0,23,14(foo)', prefix)
        self._test_invalid_image_macro(writer, '#UDG0(foo', 'No closing bracket: (foo', prefix)

    def test_macro_udgarray_invalid(self):
        writer = self._get_writer(snapshot=[0] * 8)
        prefix = ERROR_PREFIX.format('UDGARRAY')

        self._test_invalid_image_macro(writer, '#UDGARRAY', 'No parameters (expected 1)', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY()', 'No parameters (expected 1)', prefix)

        self._test_invalid_image_macro(writer, '#UDGARRAY,5;0(foo)', "Missing required argument 'width': ',5'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY(,5);0(foo)', "Missing required argument 'width': ',5'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAYscale=4;0(foo)', "Missing required argument 'width': 'scale=4'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY(scale=4);0(foo)', "Missing required argument 'width': 'scale=4'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY,scale=4;0(foo)', "Missing required argument 'width': ',scale=4'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY(,scale=4);0(foo)', "Missing required argument 'width': ',scale=4'", prefix)

        self._test_invalid_image_macro(writer, '#UDGARRAY1;(foo)', 'Expected UDG address range specification: #UDGARRAY1;', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;,2(foo)', 'Expected UDG address range specification: #UDGARRAY1;', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0:(foo)', 'Expected mask address range specification: #UDGARRAY1;0:', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0:,2(foo)', 'Expected mask address range specification: #UDGARRAY1;0:', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0@(foo)', 'Expected attribute address range specification: #UDGARRAY1;0@', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0@1;(foo)', 'Expected attribute address range specification: #UDGARRAY1;0@1;', prefix)

        self._test_invalid_image_macro(writer, '#UDGARRAY1;0', 'Missing filename: #UDGARRAY1;0', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0()', 'Missing filename: #UDGARRAY1;0()', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0{0,0}1(foo)', 'Missing filename: #UDGARRAY1;0{0,0}', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0(*)', 'Missing filename or frame ID: #UDGARRAY1;0(*)', prefix)

        self._test_invalid_image_macro(writer, '#UDGARRAY1;32768,1,2,3,4', "Too many parameters (expected 3): '1,2,3,4'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;32768:32769,1,2', "Too many parameters (expected 1): '1,2'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0{0,0,23,14,5}(foo)', "Too many parameters in cropping specification (expected 4 at most): {0,0,23,14,5}", prefix)

        self._test_invalid_image_macro(writer, '#UDGARRAY(foo)', "Cannot parse integer 'foo' in parameter string: 'foo'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;32768xJ', "Invalid multiplier in address range specification: 32768xJ", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0x2:8xK', "Invalid multiplier in address range specification: 8xK", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0x2@2xn', "Invalid multiplier in address range specification: 2xn", prefix)

        self._test_invalid_image_macro(writer, '#UDGARRAY1;0{0,0,23,14(foo)', 'No closing brace on cropping specification: {0,0,23,14(foo)', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0(foo', 'No closing bracket: (foo', prefix)

    def test_macro_udgarray_frames_invalid(self):
        writer = self._get_writer(snapshot=[0] * 8)
        prefix = ERROR_PREFIX.format('UDGARRAY')

        self._test_invalid_image_macro(writer, '#UDGARRAY*(bar)', 'No frames specified: #UDGARRAY*(bar)', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*foo', 'Missing filename: #UDGARRAY*foo', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*foo()', 'Missing filename: #UDGARRAY*foo()', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*foo(bar', 'No closing bracket: (bar', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*foo,qux(bar)', "Missing 'delay' parameter for frame 'foo'", prefix)

        return writer, prefix

    def test_macro_version(self):
        writer = self._get_writer()
        output = writer.expand('#VERSION')
        self.assertEqual(output, VERSION)
