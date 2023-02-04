from skoolkit import BASE_10, BASE_16, VERSION
from skoolkit.skoolhtml import HtmlWriter
from skoolkit.skoolparser import CASE_LOWER, CASE_UPPER

ERROR_PREFIX = 'Error while parsing #{} macro'

def nest_macros(template, *values):
    nested_macros = ['#IF(#EVAL1)({})'.format(v) for v in values]
    return template.format(*nested_macros)

class CommonSkoolMacroTest:
    def _check_call(self, writer, params, *args, **kwargs):
        macro = '#CALL:test_call({})'.format(params)
        cwd = ('<cwd>',) if isinstance(writer, HtmlWriter) else ()
        self.assertEqual(writer.expand(macro, *cwd), writer.test_call(*(cwd + args), **kwargs))

    def _test_no_parameters(self, writer, macro, req, image_macro=False):
        prefix = ERROR_PREFIX.format(macro)
        test_m = self._test_invalid_image_macro if image_macro else self._assert_error
        test_m(writer, f'#{macro}', f'No parameters (expected {req})', prefix)
        test_m(writer, f'#{macro}x', f"No parameters (expected {req}): 'x'", prefix)
        test_m(writer, f'#{macro}y irrelevant text', f"No parameters (expected {req}): 'y irreleva...'", prefix)
        test_m(writer, f'#{macro}()', f"No parameters (expected {req}): '()'", prefix)
        test_m(writer, f'#{macro}() irrelevant text', f"No parameters (expected {req}): '()'", prefix)

    def test_macro_audio_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('AUDIO')

        self._test_invalid_audio_macro(writer, '#AUDIO', "Missing filename: #AUDIO", prefix)
        self._test_invalid_audio_macro(writer, '#AUDIO(', "No closing bracket: (", prefix)
        self._test_invalid_audio_macro(writer, '#AUDIO1(', "No closing bracket: (", prefix)
        self._test_invalid_audio_macro(writer, '#AUDIO(1,2,3)(f)', "Too many parameters (expected 2): '1,2,3'", prefix)
        self._test_invalid_audio_macro(writer, '#AUDIO({x})(f)', "Unrecognised field 'x': {x}", prefix)
        self._test_invalid_audio_macro(writer, '#AUDIO({x)(f)', "Invalid format string: {x", prefix)
        self._test_invalid_audio_macro(writer, '#AUDIO(f)(', "No closing bracket: (", prefix)

        return writer, prefix

    def test_macro_call(self):
        writer = self._get_writer(skool='', variables=[('one', 1)])
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

        # Replacement fields
        writer.expand('#LET(s$=me)')
        self._check_call(writer, '{s$},{vars[one]}', 'me', 1)

    def test_macro_call_with_no_arguments(self):
        writer = self._get_writer()
        writer.test_call_no_args = self._test_call_no_args
        self.assertEqual(writer.expand('#CALL:test_call_no_args()'), 'OK')

    def test_macro_call_with_no_return_value(self):
        writer = self._get_writer()
        writer.test_call_no_retval = self._test_call_no_retval
        self.assertEqual(writer.expand('#CALL:test_call_no_retval(1,2)'), '')

    def test_macro_call_with_keyword_arguments(self):
        writer = self._get_writer()
        writer.test_call = self._test_call_with_kwargs

        self._check_call(writer, '10,arg2=', 10, arg2=None)
        self._check_call(writer, '10,arg2=2', 10, arg2=2)
        self._check_call(writer, '10,arg3=3', 10, arg3=3)
        self._check_call(writer, '10,arg2=four,arg3=5', 10, arg2='four', arg3=5)
        self._check_call(writer, '10,arg3=6,arg2=seven', 10, arg2='seven', arg3=6)

    def test_macro_call_with_nonexistent_method(self):
        writer = self._get_writer(warn=True)
        method_name = 'nonexistent_method'
        output = writer.expand('#CALL:{}(0)'.format(method_name))
        self.assertEqual(output, '')
        self.assertEqual(self.err.getvalue().split('\n')[0], 'WARNING: Unknown method name in #CALL macro: {}'.format(method_name))

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
        self._assert_error(writer, '#CALL:test_call({no})', "Unrecognised field 'no': {no}", prefix)
        self._assert_error(writer, '#CALL:test_call({no)', "Invalid format string: {no", prefix)

    def test_macro_chr_utf8(self):
        writer = self._get_writer()

        self.assertEqual(writer.expand('#CHR65,1'), 'A')
        self.assertEqual(writer.expand('#CHR169,1'), chr(169))
        self.assertEqual(writer.expand('#CHR(66,#IF(1)(1))'), 'B')
        self.assertEqual(writer.expand('#LET(utf8=1)#CHR(174,{utf8})'), chr(174))

    def test_macro_chr_utf8_and_zx_charset(self):
        writer = self._get_writer()

        self.assertEqual(writer.expand('#CHR94,3'), '↑')
        self.assertEqual(writer.expand('#CHR96,3'), '£')
        self.assertEqual(writer.expand('#CHR127,3'), '©')

    def test_macro_chr_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('CHR')

        self._test_no_parameters(writer, 'CHR', 1)
        self._assert_error(writer, '#CHR(x,y)', "Cannot parse integer 'x' in parameter string: 'x,y'", prefix)
        self._assert_error(writer, '#CHR(1,2,3)', "Too many parameters (expected 2): '1,2,3'", prefix)
        self._assert_error(writer, '#CHR(2 ...', 'No closing bracket: (2 ...', prefix)
        self._assert_error(writer, '#CHR({no})', "Unrecognised field 'no': {no}", prefix)
        self._assert_error(writer, '#CHR({foo)', "Invalid format string: {foo", prefix)

    def test_macro_copy_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('COPY')
        writer.frames = {'f': None}

        self._test_invalid_image_macro(writer, '#COPY', "No text parameter", prefix)
        self._test_invalid_image_macro(writer, '#COPY1', "No text parameter", prefix)
        self._test_invalid_image_macro(writer, '#COPYx(f)', "No terminating delimiter: x(f)", prefix)
        self._test_invalid_image_macro(writer, '#COPY(f)', "Not enough parameters (expected 2): 'f'", prefix)
        self._test_invalid_image_macro(writer, '#COPY1(f)', "Not enough parameters (expected 2): 'f'", prefix)
        self._test_invalid_image_macro(writer, '#COPY1//f//', "Not enough parameters (expected 2): 'f'", prefix)
        self._test_invalid_image_macro(writer, '#COPY1,2,3,4,5,6,7,8,9(f)', "No terminating delimiter: ,9(f)", prefix)
        self._test_invalid_image_macro(writer, '#COPY(1,2,3,4,5,6,7,8,9)(f)', "Too many parameters (expected 8): '1,2,3,4,5,6,7,8,9'", prefix)
        self._test_invalid_image_macro(writer, '#COPY1//f/g/h//', "Too many parameters (expected 2): 'f/g/h'", prefix)
        self._test_invalid_image_macro(writer, '#COPY(f', "No closing bracket: (f", prefix)
        self._test_invalid_image_macro(writer, '#COPY//f', "No terminating delimiter: //f", prefix)
        self._test_invalid_image_macro(writer, '#COPY//f/', "No terminating delimiter: //f/", prefix)
        self._test_invalid_image_macro(writer, '#COPY({x},1)(f)', "Unrecognised field 'x': {x},1", prefix)
        self._test_invalid_image_macro(writer, '#COPY({x,1)(f)', "Invalid format string: {x,1", prefix)
        self._test_invalid_image_macro(writer, '#COPYa=1(f)', "Unknown keyword argument: 'a=1'", prefix)
        self._test_invalid_image_macro(writer, '#COPY{0,0,23,14,5}(f)', "Too many parameters in cropping specification (expected 4 at most): {0,0,23,14,5}", prefix)
        self._test_invalid_image_macro(writer, '#COPY{0,y}(f)', "Cannot parse integer 'y' in parameter string: '0,y'", prefix)
        self._test_invalid_image_macro(writer, '#COPY0,0{0,0,23,14(f)', 'No closing brace on cropping specification: {0,0,23,14(f)', prefix)

        return writer, prefix

    def test_macro_d(self):
        skool = """
            @start

            ; First routine
            c32768 RET

            ; Second routine
            c32769 RET

            c32770 RET
        """
        writer = self._get_writer(skool=skool, variables=[('foo', 32769)])

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

        # Replacement fields
        self.assertEqual(writer.expand('#LET(a=32768)#D({a})'), 'First routine')
        self.assertEqual(writer.expand('#D({vars[foo]})'), 'Second routine')

    def test_macro_d_invalid(self):
        skool = '@start\nc32770 RET'
        writer = self._get_writer(skool=skool)
        prefix = ERROR_PREFIX.format('D')

        self._test_no_parameters(writer, 'D', 1)
        self._assert_error(writer, '#D32770', 'Entry at 32770 has no description', prefix)
        self._assert_error(writer, '#D32771', 'Cannot determine description for non-existent entry at 32771', prefix)
        self._assert_error(writer, '#D({no})', "Unrecognised field 'no': {no}", prefix)
        self._assert_error(writer, '#D({foo)', "Invalid format string: {foo", prefix)

    def test_macro_def(self):
        writer = self._get_writer()

        self.assertEqual(writer.expand('#DEF(#AT @)'), '')
        self.assertEqual(writer.expand('#AT'), '@')

        self.assertEqual(writer.expand('#DEF(#DOUBLE(n) #EVAL($n*2))'), '')
        self.assertEqual(writer.expand('#DOUBLE2'), '4')

        self.assertEqual(writer.expand('#DEF(#IFZERO(n)(s) #IF($n==0)($s))'), '')
        self.assertEqual(writer.expand('#IFZERO0(PASS)'), 'PASS')

        self.assertEqual(writer.expand('#DEF(#IFNEG(n)(s,t) #IF($n<0)($s,$t))'), '')
        self.assertEqual(writer.expand('#IFZERO0(PASS,FAIL)'), 'PASS')

        self.assertEqual(writer.expand('#DEF(#SUM(n,m) #EVAL($n+$m))'), '')
        self.assertEqual(writer.expand('#LET(a=1)#LET(b=2)#SUM({a},{b})'), '3')

        self.assertEqual(writer.expand('#DEF(#CAT()(n,m) $n$m#FORMAT({s$}))'), '')
        self.assertEqual(writer.expand('#LET(s$=!)#CAT(hel,lo)'), 'hello!')

    def test_macro_def_with_incomplete_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#DEF(#IFZERO(n) #IF($n==0))'), '')
        self.assertEqual(writer.expand('#IFZERO0(PASS)'), 'PASS')

    def test_macro_def_with_default_integer_parameters(self):
        writer = self._get_writer()

        # 1 integer parameter, optional
        self.assertEqual(writer.expand('#DEF(#IT(a=1) $a)'), '')
        self.assertEqual(writer.expand('#IT'), '1')
        self.assertEqual(writer.expand('#IT2'), '2')

        # 2 integer parameters, 1 optional
        self.assertEqual(writer.expand('#DEF(#ARANGE(a,b=0) $a#IF($b)(-$b))'), '')
        self.assertEqual(writer.expand('#ARANGE1'), '1')
        self.assertEqual(writer.expand('#ARANGE1,2'), '1-2')

        # 2 integer parameters, both optional
        self.assertEqual(writer.expand('#DEF(#SUM(a=0,b=0) #EVAL($a+$b))'), '')
        self.assertEqual(writer.expand('#SUM'), '0')
        self.assertEqual(writer.expand('#SUM1'), '1')
        self.assertEqual(writer.expand('#SUM1,2'), '3')

        # 3 integer parameters, 2 optional
        self.assertEqual(writer.expand('#DEF(#SRANGE(a,b=0,c=0) $a#IF($b)(-$b#IF($c)(-$c)))'), '')
        self.assertEqual(writer.expand('#SRANGE1'), '1')
        self.assertEqual(writer.expand('#SRANGE1,2'), '1-2')
        self.assertEqual(writer.expand('#SRANGE1,3,2'), '1-3-2')

        # 3 integer parameters, 2 optional, middle parameter left blank
        self.assertEqual(writer.expand('#DEF(#PROD(a,b=1,c=1) #EVAL($a*$b*$c))'), '')
        self.assertEqual(writer.expand('#PROD2,,3'), '6')

        # 3 integer parameters, 2 optional, third parameter without explicit default
        self.assertEqual(writer.expand('#DEF(#OR(a,b=0,c) #EVAL($a|$b|$c))'), '')
        self.assertEqual(writer.expand('#OR1,2'), '3')

        # Whitespace in integer parameter spec
        self.assertEqual(writer.expand('#DEF(#AND(a, b=255, c = 255) #EVAL($a&$b&$c))'), '')
        self.assertEqual(writer.expand('#AND15,1'), '1')

    def test_macro_def_with_keyword_arguments(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#DEF(#PROD(a,b=1,c=1) #EVAL($a*$b*$c))'), '')
        self.assertEqual(writer.expand('#PROD(c=2,a=4,b=3)'), '24')

    def test_macro_def_with_replacement_fields(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#DEF(#PROD(a,b=1,c=1) #EVAL($a*$b*$c))'), '')
        writer.expand('#LET(p=7) #LET(q=4)')
        self.assertEqual(writer.expand('#PROD({p},c={q})'), '28')

    def test_macro_def_with_macro_arguments(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#DEF(#PROD(a,b=1,c=1) #EVAL($a*$b*$c))'), '')
        self.assertEqual(writer.expand('#PROD(#IF(0)(1,2),#IF(1)(3,4))'), '6')

    def test_macro_def_with_default_string_parameters(self):
        writer = self._get_writer()

        # 1 string parameter, optional
        self.assertEqual(writer.expand('#DEF(#STR()(s=nothing) $s)'), '')
        self.assertEqual(writer.expand('#STR'), 'nothing')
        self.assertEqual(writer.expand('#STR,'), 'nothing,')
        self.assertEqual(writer.expand('#STR[]'), 'nothing[]')
        self.assertEqual(writer.expand('#STR{}'), 'nothing{}')
        self.assertEqual(writer.expand('#STR//!//'), 'nothing//!//')
        self.assertEqual(writer.expand('#STR()'), '')
        self.assertEqual(writer.expand('#STR(something)'), 'something')

        # 2 string parameters, 1 optional
        self.assertEqual(writer.expand('#DEF(#CAT()(p,s=.) $p$s)'), '')
        self.assertEqual(writer.expand('#CAT(hi)'), 'hi.')
        self.assertEqual(writer.expand('#CAT(hi,!)'), 'hi!')

        # 2 string parameters, both optional
        self.assertEqual(writer.expand('#DEF(#BRKT()(p=[,s=]) ${p}hello$s)'), '')
        self.assertEqual(writer.expand('#BRKT'), '[hello]')
        self.assertEqual(writer.expand('#BRKT,'), '[hello],')
        self.assertEqual(writer.expand('#BRKT[]'), '[hello][]')
        self.assertEqual(writer.expand('#BRKT{}'), '[hello]{}')
        self.assertEqual(writer.expand('#BRKT//!//'), '[hello]//!//')
        self.assertEqual(writer.expand('#BRKT()'), 'hello]')
        self.assertEqual(writer.expand('#BRKT(,)'), 'hello')
        self.assertEqual(writer.expand('#BRKT(<)'), '<hello]')
        self.assertEqual(writer.expand('#BRKT(,>)'), 'hello>')
        self.assertEqual(writer.expand('#BRKT(<,>)'), '<hello>')

        # 1 string parameter, defaults to integer parameter value
        self.assertEqual(writer.expand('#DEF(#FOO(a)(s=$a) $s)'), '')
        self.assertEqual(writer.expand('#FOO1'), '1')
        self.assertEqual(writer.expand('#FOO1,'), '1,')
        self.assertEqual(writer.expand('#FOO1[]'), '1[]')
        self.assertEqual(writer.expand('#FOO1{}'), '1{}')
        self.assertEqual(writer.expand('#FOO1()'), '')
        self.assertEqual(writer.expand('#FOO1(one)'), 'one')

        # 3 string parameters, 2 optional, third parameter without explicit default
        self.assertEqual(writer.expand('#DEF(#BAR()(a,b=?,c) |$a|$b|$c|)'), '')
        self.assertEqual(writer.expand('#BAR(A,B)'), '|A|B||')

        # 1 optional string parameter, default value containing comma between parentheses
        self.assertEqual(writer.expand('#DEF(#BAZ()(s=f(x,y)) $s)'), '')
        self.assertEqual(writer.expand('#BAZ'), 'f(x,y)')
        self.assertEqual(writer.expand('#BAZ(something)'), 'something')

        # Whitespace in string parameter spec
        self.assertEqual(writer.expand('#DEF(#META()(a, b=bar, c = baz) $a/$b/$c)'), '')
        self.assertEqual(writer.expand('#META(foo)'), 'foo/bar/baz')

    def test_macro_def_with_default_integer_parameters_and_default_string_parameter(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#DEF(#BAR(a,b=0,c=0)(s=$a-$b-$c) $s)'), '')
        self.assertEqual(writer.expand('#BAR1'), '1-0-0')
        self.assertEqual(writer.expand('#BAR1,2'), '1-2-0')
        self.assertEqual(writer.expand('#BAR1,2,3'), '1-2-3')
        self.assertEqual(writer.expand('#BAR1(no)'), 'no')
        self.assertEqual(writer.expand('#BAR1,2(nope)'), 'nope')
        self.assertEqual(writer.expand('#BAR1,2,3(nah)'), 'nah')

    def test_macro_def_accepts_unescaped_replacement_fields(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand("#DEF(#INC(a) #LET(x=$a)#EVAL({x}+1))"), '')
        self.assertEqual(writer.expand('#INC1'), '2')

    def test_macro_def_allows_invalid_placeholders(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#DEF(#BAZ()(s=$b) $s:$c)'), '')
        self.assertEqual(writer.expand('#BAZ'), '$b:$c')
        self.assertEqual(writer.expand('#BAZ(hey)'), 'hey:$c')

    def test_macro_def_with_alternative_delimiters(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#DEF/#CAT()(p,q) $p$q/'), '')
        self.assertEqual(writer.expand('#CAT||A|B||'), 'AB')

    def test_macro_def_with_macro_arguments_as_replacement_fields(self):
        writer = self._get_writer()

        # Integer argument as replacement field
        self.assertEqual(writer.expand('#DEF1(#HEX(n) ${n:04X})'), '')
        self.assertEqual(writer.expand('#HEX64206'), '$FACE')

        # Integer argument as replacement field in string argument value
        self.assertEqual(writer.expand('#DEF1(#HEX(n)(s=${n:04X}) {s})'), '')
        self.assertEqual(writer.expand('#HEX64206'), '$FACE')
        self.assertEqual(writer.expand('#HEX64206(what)'), 'what')

        # String argument as replacement field
        self.assertEqual(writer.expand('#DEF1(#RJUST(n)(s) {s:>{n}})'), '')
        self.assertEqual(writer.expand('/#RJUST5(hi)/'), '/   hi/')

        # Escaped replacement field for non-argument value
        self.assertEqual(writer.expand('#DEF1(#ADD(n) #LET(c={{c}}+{n})#EVAL({{c}}))'), '')
        self.assertEqual(writer.expand('#LET(c=1)#ADD2'), '3')

    def test_macro_def_with_whitespace_stripped(self):
        writer = self._get_writer()
        macro = """
            #DEF2(#SQUARE(n)
                #LET(x=0)
                #FOR(1,$n)(_,#LET(x={x}+$n))
                #EVAL({x})
            )
        """.strip()
        self.assertEqual(writer.expand(macro), '')
        self.assertEqual(writer.expand('(#SQUARE3)'), '(9)')

    def test_macro_def_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('DEF')

        self._assert_error(writer, '#DEF', "No text parameter", prefix)
        self._assert_error(writer, '#DEFx', "No terminating delimiter: x", prefix)
        self._assert_error(writer, '#DEF(x)', "Invalid macro name: #DEF(x)", prefix)
        self._assert_error(writer, '#DEF(#x)', "Invalid macro name: #DEF(#x)", prefix)
        self._assert_error(writer, '#DEF(#M', "No closing bracket: (#M", prefix)
        self._assert_error(writer, '#DEF(#M(1))', "Invalid macro argument name: 1", prefix)
        self._assert_error(writer, '#DEF(#M(a1))', "Invalid macro argument name: a1", prefix)
        self._assert_error(writer, '#DEF(#M(a=b))', "Cannot parse integer argument value: 'a=b'", prefix)

    def test_macro_def_invalid_macros(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('FOO')

        writer.expand('#DEF(#FOO(a)(b,c) $a$b$c)')
        self._test_no_parameters(writer, 'FOO', 1)
        self._assert_error(writer, '#FOO(x)', "Cannot parse integer 'x' in parameter string: 'x'", prefix)
        self._assert_error(writer, '#FOO(1,2)', "Too many parameters (expected 1): '1,2'", prefix)
        self._assert_error(writer, '#FOO(1', 'No closing bracket: (1', prefix)
        self._assert_error(writer, '#FOO1(x', 'No closing bracket: (x', prefix)
        self._assert_error(writer, '#FOO1(a)', "Not enough parameters (expected 2): 'a'", prefix)
        self._assert_error(writer, '#FOO1(a,b,c)', "Too many parameters (expected 2): 'a,b,c'", prefix)
        self._assert_error(writer, '#FOO({foo})(a,b)', "Unrecognised field 'foo': {foo}", prefix)
        self._assert_error(writer, '#FOO({foo)(a,b)', "Invalid format string: {foo", prefix)
        self._assert_error(writer, '#FOO(d=1)(a,b)', "Unknown keyword argument: 'd=1'", prefix)

    def test_macro_def_invalid_macros_with_defaults(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('BAR')

        self.assertEqual(writer.expand('#DEF(#BAR(a,b,c=0) $a$b$c)'), '')
        self._test_no_parameters(writer, 'BAR', 2)
        self._assert_error(writer, '#BAR(0,1,2,3)', "Too many parameters (expected 3): '0,1,2,3'", prefix)

        self.assertEqual(writer.expand('#DEF(#BAR()(a,b,c=!) $a$b$c)'), '')
        self._assert_error(writer, '#BAR', "No text parameter", prefix)
        self._assert_error(writer, '#BAR(a)', "Not enough parameters (expected 2): 'a'", prefix)
        self._assert_error(writer, '#BAR(a,b,c,d)', "Too many parameters (expected 3): 'a,b,c,d'", prefix)

    def test_macro_define(self):
        writer = self._get_writer()

        self.assertEqual(writer.expand('#DEFINE0(AT,@)'), '')
        self.assertEqual(writer.expand('#AT'), '@')

        self.assertEqual(writer.expand('#DEFINE1(DOUBLE,#EVAL({}*2))'), '')
        self.assertEqual(writer.expand('#DOUBLE2'), '4')

        self.assertEqual(writer.expand('#DEFINE1,1(IFZERO,#IF({}==0)({}))'), '')
        self.assertEqual(writer.expand('#IFZERO0(PASS)'), 'PASS')

        self.assertEqual(writer.expand('#DEFINE1,2(IFNEG,#IF({}<0)({},{}))'), '')
        self.assertEqual(writer.expand('#IFZERO0(PASS,FAIL)'), 'PASS')

        self.assertEqual(writer.expand('#DEFINE2(SUM,#EVAL({}+{}))#LET(a=1)#LET(b=2)'), '')
        self.assertEqual(writer.expand('#SUM({a},{b})'), '3')

    def test_macro_define_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('DEFINE')

        self._test_no_parameters(writer, 'DEFINE', 1)
        self._assert_error(writer, '#DEFINE(x)', "Cannot parse integer 'x' in parameter string: 'x'", prefix)
        self._assert_error(writer, '#DEFINE0', 'No text parameter', prefix)
        self._assert_error(writer, '#DEFINE0(FOO)', "Not enough parameters (expected 2): 'FOO'", prefix)
        self._assert_error(writer, '#DEFINE0(BAR', "No closing bracket: (BAR", prefix)

    def test_macro_define_invalid_macro_definitions(self):
        writer = self._get_writer()

        writer.expand('#DEFINE1(FOO,{1})')
        self._assert_error(writer, '#FOO0', 'Field index out of range: {1}', ERROR_PREFIX.format('FOO'))

        writer.expand('#DEFINE1(BAR,{x})')
        self._assert_error(writer, '#BAR0', "Unrecognised field 'x': {x}", ERROR_PREFIX.format('BAR'))

        writer.expand('#DEFINE1(BAZ,{0)')
        self._assert_error(writer, '#BAZ0', "Invalid format string: {0", ERROR_PREFIX.format('BAZ'))

    def test_macro_define_invalid_macros(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('FOO')

        writer.expand('#DEFINE1,2(FOO,{0}{1}{2})')
        self._test_no_parameters(writer, 'FOO', 1)
        self._assert_error(writer, '#FOO(x)', "Cannot parse integer 'x' in parameter string: 'x'", prefix)
        self._assert_error(writer, '#FOO(1,2)', "Too many parameters (expected 1): '1,2'", prefix)
        self._assert_error(writer, '#FOO(1', 'No closing bracket: (1', prefix)
        self._assert_error(writer, '#FOO1(x', 'No closing bracket: (x', prefix)
        self._assert_error(writer, '#FOO1(a)', "Not enough parameters (expected 2): 'a'", prefix)
        self._assert_error(writer, '#FOO1(a,b,c)', "Too many parameters (expected 2): 'a,b,c'", prefix)
        self._assert_error(writer, '#FOO({foo})(a,b)', "Unrecognised field 'foo': {foo}", prefix)
        self._assert_error(writer, '#FOO({foo)(a,b)', "Invalid format string: {foo", prefix)

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

    def test_macro_eval_base_none(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#EVAL({base})'), '0')

    def test_macro_eval_base_10(self):
        writer = self._get_writer(base=BASE_10)
        self.assertEqual(writer.expand('#EVAL({base},16)'), 'A')

    def test_macro_eval_base_16(self):
        writer = self._get_writer(base=BASE_16)
        self.assertEqual(writer.expand('#EVAL(255,{base})'), 'FF')

    def test_macro_eval_case_none(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#EVAL({case})'), '0')

    def test_macro_eval_case_lower(self):
        writer = self._get_writer(case=CASE_LOWER)
        self.assertEqual(writer.expand('#EVAL({case})'), '1')

    def test_macro_eval_case_upper(self):
        writer = self._get_writer(case=CASE_UPPER)
        self.assertEqual(writer.expand('#EVAL({case},2)'), '10')

    def test_macro_eval_variables(self):
        writer = self._get_writer(skool='', variables=(('foo', 1), ('bar', 2), ('baz', 3)))
        self.assertEqual(writer.expand('#EVAL(2*{vars[foo]})'), '2')
        self.assertEqual(writer.expand('#EVAL({vars[bar]})'), '2')
        self.assertEqual(writer.expand('#EVAL({vars[baz]},{vars[bar]})'), '11')
        self.assertEqual(writer.expand('#EVAL({vars[qux]},{vars[bar]},8)'), '00000000')

    def test_macro_eval_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('EVAL')

        self._test_no_parameters(writer, 'EVAL', 1)
        self._assert_error(writer, '#EVAL,', "Missing required parameter in position 1/1: ','", prefix)
        self._assert_error(writer, '#EVAL(,)', "Missing required parameter in position 1/1: ','", prefix)
        self._assert_error(writer, '#EVAL,16', "Missing required parameter in position 1/1: ',16'", prefix)
        self._assert_error(writer, '#EVAL(,16)', "Missing required parameter in position 1/1: ',16'", prefix)
        self._assert_error(writer, '#EVAL(1,10,5,8)', "Too many parameters (expected 3): '1,10,5,8'", prefix)
        self._assert_error(writer, '#EVAL(1,x)', "Cannot parse integer 'x' in parameter string: '1,x'", prefix)
        self._assert_error(writer, '#EVAL(1,,x)', "Cannot parse integer 'x' in parameter string: '1,,x'", prefix)
        self._assert_error(writer, '#EVAL5,3', 'Invalid base (3): 5,3', prefix)
        self._assert_error(writer, '#EVAL({nope})', "Unrecognised field 'nope': {nope}", prefix)
        self._assert_error(writer, '#EVAL({foo)', "Invalid format string: {foo", prefix)

    def test_macro_font_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('FONT')

        self._test_no_parameters(writer, 'FONT', 1, True)
        self._test_invalid_image_macro(writer, '#FONT:', 'No text parameter', prefix)
        self._test_invalid_image_macro(writer, '#FONT:()0', 'Empty message: ()', prefix)
        self._test_invalid_image_macro(writer, '#FONT,10', "Missing required argument 'addr': ',10'", prefix)
        self._test_invalid_image_macro(writer, '#FONT(,10)', "Missing required argument 'addr': ',10'", prefix)
        self._test_invalid_image_macro(writer, '#FONTscale=4', "Missing required argument 'addr': 'scale=4'", prefix)
        self._test_invalid_image_macro(writer, '#FONT(scale=4)', "Missing required argument 'addr': 'scale=4'", prefix)
        self._test_invalid_image_macro(writer, '#FONT,scale=4', "Missing required argument 'addr': ',scale=4'", prefix)
        self._test_invalid_image_macro(writer, '#FONT(,scale=4)', "Missing required argument 'addr': ',scale=4'", prefix)
        self._test_invalid_image_macro(writer, '#FONT0{0,0,23,14,5}(foo)', "Too many parameters in cropping specification (expected 4 at most): {0,0,23,14,5}", prefix)
        self._test_invalid_image_macro(writer, '#FONT(foo)', "Cannot parse integer 'foo' in parameter string: 'foo'", prefix)
        self._test_invalid_image_macro(writer, '#FONT0{0,0,23,14(foo)', 'No closing brace on cropping specification: {0,0,23,14(foo)', prefix)
        self._test_invalid_image_macro(writer, '#FONT0(foo', 'No closing bracket: (foo', prefix)
        self._test_invalid_image_macro(writer, '#FONT:[hi)0', 'No closing bracket: [hi)0', prefix)
        self._test_invalid_image_macro(writer, '#FONT({no})', "Unrecognised field 'no': {no}", prefix)
        self._test_invalid_image_macro(writer, '#FONT0{{nope}}', "Unrecognised field 'nope': {nope}", prefix)
        self._test_invalid_image_macro(writer, '#FONT({foo)', "Invalid format string: {foo", prefix)

    def test_macro_for(self):
        writer = self._get_writer()

        # Default step
        output = writer.expand('#FOR1,3(n,n)')
        self.assertEqual(output, '123')

        # Step
        output = writer.expand('#FOR1,5,2(n,n)')
        self.assertEqual(output, '135')

        # Stop value missed because (stop - start) is not divisible by step
        output = writer.expand('#FOR1,6,2(n,n)')
        self.assertEqual(output, '135')

        # Empty loop
        output = writer.expand('#FOR1,0(n,n)')
        self.assertEqual(output, '')

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

    def test_macro_for_replacement_fields(self):
        writer = self._get_writer(skool='', variables=[('one', 1)])
        writer.fields.update({'two': 2, 'three': 3})
        self.assertEqual(writer.expand('#FOR({vars[one]},{three},{two})(n,[n])'), '[1][3]')

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

    def test_macro_for_with_commas_affixed_to_separator(self):
        writer = self._get_writer()

        # No commas
        output = writer.expand('#FOR0,1,,0($s,$s)')
        self.assertEqual(output, '01')

        # Default sep and fsep
        output = writer.expand('#FOR0,2,,1($s,$s)')
        self.assertEqual(output, '0,1,2')

        # Default sep, specified fsep
        output = writer.expand('#FOR0,2,,1($s,$s,,...)')
        self.assertEqual(output, '0,1...2')

        # Specified sep, default fsep
        output = writer.expand('#FOR0,2,,1($s,$s, )')
        self.assertEqual(output, '0, 1, 2')

        # Specified sep and fsep
        output = writer.expand('#FOR0,3,,1($s,$s, , and )')
        self.assertEqual(output, '0, 1, 2 and 3')

        # Comma suffix
        output = writer.expand('#FOR0,2,,2($s,$s,.0)')
        self.assertEqual(output, '0.0,1.0,2')

        # Comma prefix and suffix
        output = writer.expand('#FOR0,2,,3($s,$s,?)')
        self.assertEqual(output, '0,?,1,?,2')

    def test_macro_for_with_variable_name_replaced_in_separator(self):
        writer = self._get_writer()

        # Default fsep
        output = writer.expand('#FOR0,6,2,7(n,n,n+1)')
        self.assertEqual(output, '0,0+1,2,2+1,4,4+1,6')

        # Specified fsep
        output = writer.expand('#FOR0,6,2,4(n,n, n+1 , +)')
        self.assertEqual(output, '0 0+1 2 2+1 4 +6')

        # Specified fsep containing variable name (not replaced)
        output = writer.expand('#FOR0,6,2,4(n,n,;n+1;,n+)')
        self.assertEqual(output, '0;0+1;2;2+1;4n+6')

        # Stop value missed because (stop - start) is not divisible by step
        output = writer.expand('#FOR0,7,2,7(n,n,n+1)')
        self.assertEqual(output, '0,0+1,2,2+1,4,4+1,6')

    def test_macro_for_invalid(self):
        writer = self._get_writer()
        writer.fields['x'] = 'x'
        prefix = ERROR_PREFIX.format('FOR')

        self._test_no_parameters(writer, 'FOR', 2)
        self._assert_error(writer, '#FOR0', "Not enough parameters (expected 2): '0'", prefix)
        self._assert_error(writer, '#FOR(0)', "Not enough parameters (expected 2): '0'", prefix)
        self._assert_error(writer, '#FOR,1(n,n)', "Missing required parameter in position 1/2: ',1'", prefix)
        self._assert_error(writer, '#FOR(,1)(n,n)', "Missing required parameter in position 1/2: ',1'", prefix)
        self._assert_error(writer, '#FOR0,(n,n)', "Missing required parameter in position 2/2: '0,'", prefix)
        self._assert_error(writer, '#FOR(0,)(n,n)', "Missing required parameter in position 2/2: '0,'", prefix)
        self._assert_error(writer, '#FOR(1,2,3,4,5)', "Too many parameters (expected 4): '1,2,3,4,5'", prefix)
        self._assert_error(writer, '#FOR(1,2)(1,2,3,4,5)', "Too many parameters (expected 4): '1,2,3,4,5'", prefix)
        self._assert_error(writer, '#FOR0,1', 'No variable name: 0,1', prefix)
        self._assert_error(writer, '#FOR0,1()', "No variable name: 0,1()", prefix)
        self._assert_error(writer, '#FOR0,1(n,n', 'No closing bracket: (n,n', prefix)
        self._assert_error(writer, '#FOR(1,x)(n,n)', "Cannot parse integer 'x' in parameter string: '1,x'", prefix)
        self._assert_error(writer, '#FOR(1,{x})(n,n)', "Cannot parse integer 'x' in parameter string: '1,x'", prefix)
        self._assert_error(writer, '#FOR(1,{y})(n,n)', "Unrecognised field 'y': 1,{y}", prefix)
        self._assert_error(writer, '#FOR(1,{y)(n,n)', "Invalid format string: 1,{y", prefix)

    def test_macro_foreach(self):
        writer = self._get_writer()

        # No values
        output = writer.expand('#FOREACH()($s,$s)')
        self.assertEqual(output, '')

        # One value
        output = writer.expand('#FOREACH(a)($s,[$s])')
        self.assertEqual(output, '[a]')

        # Two values
        output = writer.expand('#FOREACH(a,b)($s,[$s])')
        self.assertEqual(output, '[a][b]')

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

    def test_macro_foreach_with_eref_and_refs_directive(self):
        skool = """
            @start
            ; Routine at 40000
            c40000 JP 40007 ; Jumps to 40007 (obviously)

            ; Routine at 40003
            c40003 JP (HL)  ; Also jumps to 40007 (say)

            ; Routine at 40004
            c40004 JP (HL)  ; Jumps to 40008 (say)

            ; Routine at 40005
            c40005 JP (HL)  ; Also jumps to 40008 (say)

            ; Routine at 40006
            c40006 XOR A
            @refs=40003:40009
             40007 INC A
            @refs=40004,40005
             40008 RET

            ; Routine at 40009
            c40009 JP 40007 ; Also jumps to 40007 (obviously)
        """
        writer = self._get_writer(skool=skool)
        self.assertEqual(writer.expand('#FOREACH(EREF40007)(a,a,;)'), '40000;40003')
        self.assertEqual(writer.expand('#FOREACH(EREF40008)(a,a,;)'), '40004;40005')

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

    def test_macro_foreach_with_ref_and_refs_directive(self):
        skool = """
            @start
            ; Routine at 40000
            c40000 JP 40006 ; Jumps to 40006 (obviously)

            ; Routine at 40003
            c40003 JP (HL)  ; Also jumps to 40006 (say)

            ; Routine at 40004
            c40004 JP (HL)  ; Jumps to 40007 (say)

            ; Routine at 40005
            c40005 JP (HL)  ; Also jumps to 40007 (say)

            ; Routine at 40006
            @refs=40003:40008
            c40006 XOR A
            @refs=40004,40005
             40007 RET

            ; Routine at 40008
            c40008 JP 40006 ; Also jumps to 40006 (obviously)
        """
        writer = self._get_writer(skool=skool)
        self.assertEqual(writer.expand('#FOREACH(REF40006)(a,a,;)'), '40000;40003;40004;40005')

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
        self._assert_error(writer, '#FOREACH(EREF$81A4)(n,n)', 'No instruction at 33188: EREF$81A4', prefix)
        self._assert_error(writer, '#FOREACH(REF$81A4)(n,n)', 'No entry at 33188: REF$81A4', prefix)

    def test_macro_format(self):
        writer = self._get_writer(base=BASE_16, case=CASE_LOWER)
        writer.fields['vars'].update({'foo': 255, 'bar$': 'Hello'})

        self.assertEqual(writer.expand('#FORMAT(base={base})'), 'base=16')
        self.assertEqual(writer.expand('#FORMAT(case={case})'), 'case=1')
        self.assertEqual(writer.expand('#FORMAT(html={html})'), 'html=1' if isinstance(writer, HtmlWriter) else 'html=0')
        self.assertEqual(writer.expand('#FORMAT({vars[foo]:02x})'), 'ff')
        self.assertEqual(writer.expand('#FORMAT({vars[bar$]:_^9})'), '__Hello__')
        self.assertEqual(writer.expand('#FORMAT0({vars[bar$]})'), 'Hello')
        self.assertEqual(writer.expand('#FORMAT1({vars[bar$]})'), 'hello')
        self.assertEqual(writer.expand('#FORMAT({case})({vars[bar$]})'), 'hello')
        self.assertEqual(writer.expand('#FORMAT2({vars[bar$]})'), 'HELLO')
        self.assertEqual(writer.expand('#FORMAT(1+1)({vars[bar$]})'), 'HELLO')
        self.assertEqual(writer.expand('#FORMAT(#EVAL(1+1))({vars[bar$]})'), 'HELLO')

    def test_macro_format_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('FORMAT')

        self._assert_error(writer, '#FORMAT', 'No text parameter', prefix)
        self._assert_error(writer, '#FORMAT({asm}', 'No closing bracket: ({asm}', prefix)
        self._assert_error(writer, '#FORMAT/{fix}', 'No terminating delimiter: /{fix}', prefix)
        self._assert_error(writer, '#FORMAT({unknown})(x)', "Unrecognised field 'unknown': {unknown}", prefix)
        self._assert_error(writer, '#FORMAT0({unknown})', "Unrecognised field 'unknown': ({unknown})", prefix)
        self._assert_error(writer, '#FORMAT({bad)(x)', 'Invalid format string: {bad', prefix)
        self._assert_error(writer, '#FORMAT0({bad)', 'Invalid format string: ({bad)', prefix)

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
        writer = self._get_writer(skool='')
        self.assertEqual(writer.expand('#IF({base}==0)(PASS,FAIL)'), 'PASS')
        self.assertEqual(writer.expand('#IF({mode[base]}==0)(PASS,FAIL)'), 'PASS')

    def test_macro_if_base_10(self):
        writer = self._get_writer(base=BASE_10)
        self.assertEqual(writer.expand('#IF({base}==10)(PASS,FAIL)'), 'PASS')

    def test_macro_if_base_16(self):
        writer = self._get_writer(base=BASE_16)
        self.assertEqual(writer.expand('#IF({base}==16)(PASS,FAIL)'), 'PASS')

    def test_macro_if_case_none(self):
        writer = self._get_writer(skool='')
        self.assertEqual(writer.expand('#IF({case}==0)(PASS,FAIL)'), 'PASS')
        self.assertEqual(writer.expand('#IF({mode[case]}==0)(PASS,FAIL)'), 'PASS')

    def test_macro_if_case_lower(self):
        writer = self._get_writer(case=CASE_LOWER)
        self.assertEqual(writer.expand('#IF({case}==1)(PASS,FAIL)'), 'PASS')

    def test_macro_if_case_upper(self):
        writer = self._get_writer(case=CASE_UPPER)
        self.assertEqual(writer.expand('#IF({case}==2)(PASS,FAIL)'), 'PASS')

    def test_macro_if_variables(self):
        writer = self._get_writer(skool='', variables=(('foo', 1), ('bar', 2)))
        self.assertEqual(writer.expand('#IF({vars[foo]}==1)(PASS,FAIL)'), 'PASS')
        self.assertEqual(writer.expand('#IF({vars[bar]}==2)(PASS,FAIL)'), 'PASS')
        self.assertEqual(writer.expand('#IF({vars[baz]}==0)(PASS,FAIL)'), 'PASS')

    def test_macro_if_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('IF')

        self._assert_error(writer, '#IF', "No valid expression found: '#IF'", prefix)
        self._assert_error(writer, '#IFx', "No valid expression found: '#IFx'", prefix)
        self._assert_error(writer, '#IF({asm)(1,0)', "Invalid format string: {asm", prefix)
        self._assert_error(writer, '#IF(0)', "No output strings: (0)", prefix)
        self._assert_error(writer, '#IF(0)(true,false,other)', "Too many output strings (expected 2): (0)(true,false,other)", prefix)
        self._assert_error(writer, '#IF1(true,false', "No closing bracket: (true,false", prefix)
        self._assert_error(writer, '#IF({vase})(true,false)', "Unrecognised field 'vase': {vase}", prefix)

    def test_macro_include_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('INCLUDE')

        self._assert_error(writer, '#INCLUDE', "No text parameter", prefix)
        self._assert_error(writer, '#INCLUDE0', "No text parameter", prefix)
        self._assert_error(writer, '#INCLUDE(0)', "No text parameter", prefix)
        self._assert_error(writer, '#INCLUDE({no})(foo)', "Unrecognised field 'no': {no}", prefix)
        self._assert_error(writer, '#INCLUDE({foo)(bar)', "Invalid format string: {foo", prefix)

    def test_macro_let_integers(self):
        writer = self._get_writer()

        # Plain value
        self.assertEqual(writer.expand('#LET(foo=1)'), '')
        self.assertEqual(writer.fields['foo'], 1)

        # Macro
        self.assertEqual(writer.expand('#LET[foo=#IF(1)(2,1)]'), '')
        self.assertEqual(writer.fields['foo'], 2)

        # Replacement field
        self.assertEqual(writer.expand('#LET{foo=3}'), '')
        self.assertEqual(writer.expand('#LET(bar={foo})'), '')
        self.assertEqual(writer.fields['bar'], 3)

        # Macro and replacement field
        self.assertEqual(writer.expand('#LET(foo=4)'), '')
        self.assertEqual(writer.expand('#LET(bar=5)'), '')
        self.assertEqual(writer.expand('#LET/baz=#IF(1)({foo},{bar})/'), '')
        self.assertEqual(writer.fields['baz'], 4)

        # Arithmetic expression
        self.assertEqual(writer.expand('#LET(foo=5)'), '')
        self.assertEqual(writer.expand('#LET(bar=6)'), '')
        self.assertEqual(writer.expand('#LET|baz={foo}+{bar}*2|'), '')
        self.assertEqual(writer.fields['baz'], 17)

    def test_macro_let_strings(self):
        writer = self._get_writer()

        # Plain value
        self.assertEqual(writer.expand('#LET(foo$=hello)'), '')
        self.assertEqual(writer.fields['foo$'], 'hello')

        # Empty value
        self.assertEqual(writer.expand('#LET(foo$=)'), '')
        self.assertEqual(writer.fields['foo$'], '')

        # Macro
        self.assertEqual(writer.expand('#LET[foo$=#IF(1)(a,b)]'), '')
        self.assertEqual(writer.fields['foo$'], 'a')

        # Replacement field
        self.assertEqual(writer.expand('#LET{foo$=h}'), '')
        self.assertEqual(writer.expand('#LET(bar$={foo$}i)'), '')
        self.assertEqual(writer.fields['bar$'], 'hi')

        # Macro and replacement field
        self.assertEqual(writer.expand('#LET(foo$=black)'), '')
        self.assertEqual(writer.expand('#LET(bar$=white)'), '')
        self.assertEqual(writer.expand('#LET/baz$=#IF(1)({foo$},{bar$})/'), '')
        self.assertEqual(writer.fields['baz$'], 'black')

    def test_macro_let_dictionary_of_strings(self):
        writer = self._get_writer()

        # Blank default value only
        self.assertEqual(writer.expand('#LET(a$[]=())'), '')
        self.assertEqual(writer.fields['a$'], {})
        self.assertEqual(writer.fields['a$'][0], '')

        # Default value only
        self.assertEqual(writer.expand('#LET(a$[]=(null))'), '')
        self.assertEqual(writer.fields['a$'], {})
        self.assertEqual(writer.fields['a$'][0], 'null')

        # Default value and one key-value pair
        self.assertEqual(writer.expand('#LET(b$[]=(0,1:2))'), '')
        self.assertEqual(writer.fields['b$'], {1: '2'})
        self.assertEqual(writer.fields['b$'][0], '0')

        # Default value and two key-value pairs
        self.assertEqual(writer.expand('#LET(c$[]=(!,1:3,2:6))'), '')
        self.assertEqual(writer.fields['c$'], {1: '3', 2: '6'})
        self.assertEqual(writer.fields['c$'][0], '!')

        # Implied values
        self.assertEqual(writer.expand('#LET(d$[]=(0,1,2,3))'), '')
        self.assertEqual(writer.fields['d$'], {1: '1', 2: '2', 3: '3'})
        self.assertEqual(writer.fields['d$'][0], '0')

        # Macros
        self.assertEqual(writer.expand('#LET(e$[]=(,#IF(0)(0,1):#IF(1)(2,0)))'), '')
        self.assertEqual(writer.fields['e$'], {1: '2'})
        self.assertEqual(writer.fields['e$'][0], '')

        # Replacement field
        self.assertEqual(writer.expand('#LET(x=10)'), '')
        self.assertEqual(writer.expand('#LET(f$[]=(-,1:{x}))'), '')
        self.assertEqual(writer.fields['f$'], {1: '10'})
        self.assertEqual(writer.fields['f$'][0], '-')

        # Macro and replacement field
        self.assertEqual(writer.expand('#LET(y=5)'), '')
        self.assertEqual(writer.expand('#LET(g$[]=(:,1:#IF({y}>1)({y},0)))'), '')
        self.assertEqual(writer.fields['g$'], {1: '5'})
        self.assertEqual(writer.fields['g$'][0], ':')

    def test_macro_let_dictionary_of_integers(self):
        writer = self._get_writer()

        # Default value only
        self.assertEqual(writer.expand('#LET(a[]=(0))'), '')
        self.assertEqual(writer.fields['a'], {})
        self.assertEqual(writer.fields['a'][0], 0)

        # Default value and one key-value pair
        self.assertEqual(writer.expand('#LET(b[]=(0,1:2))'), '')
        self.assertEqual(writer.fields['b'], {1: 2})
        self.assertEqual(writer.fields['b'][0], 0)

        # Default value and two key-value pairs
        self.assertEqual(writer.expand('#LET(c[]=(0,1:3,2:6))'), '')
        self.assertEqual(writer.fields['c'], {1: 3, 2: 6})
        self.assertEqual(writer.fields['c'][0], 0)

        # Implied values
        self.assertEqual(writer.expand('#LET(d[]=(0,1,2,3))'), '')
        self.assertEqual(writer.fields['d'], {1: 1, 2: 2, 3: 3})
        self.assertEqual(writer.fields['d'][0], 0)

        # Macros
        self.assertEqual(writer.expand('#LET(e[]=(-1,#IF(0)(0,1):#IF(1)(2,0)))'), '')
        self.assertEqual(writer.fields['e'], {1: 2})
        self.assertEqual(writer.fields['e'][0], -1)

        # Replacement field
        self.assertEqual(writer.expand('#LET(x=10)'), '')
        self.assertEqual(writer.expand('#LET(f[]=(-1,1:{x}))'), '')
        self.assertEqual(writer.fields['f'], {1: 10})
        self.assertEqual(writer.fields['f'][0], -1)

        # Macro and replacement field
        self.assertEqual(writer.expand('#LET(y=5)'), '')
        self.assertEqual(writer.expand('#LET(g[]=(0,1:#IF({y}>1)({y},0)))'), '')
        self.assertEqual(writer.fields['g'], {1: 5})
        self.assertEqual(writer.fields['g'][0], 0)

        # Arithmetic expressions
        self.assertEqual(writer.expand('#LET(e[]=(1<<8,1:1+0,2:3-1,3:9/3,4:2*2))'), '')
        self.assertEqual(writer.fields['e'], {1: 1, 2: 2, 3: 3, 4: 4})
        self.assertEqual(writer.fields['e'][0], 256)

    def test_macro_let_dictionary_with_alternative_delimiters(self):
        writer = self._get_writer()

        self.assertEqual(writer.expand('#LET(a[]=[100,0:0,1:2])'), '')
        self.assertEqual(writer.fields['a'], {0: 0, 1: 2})
        self.assertEqual(writer.fields['a'][2], 100)

        self.assertEqual(writer.expand('#LET(b$[]=//?/0:A/1:B//)'), '')
        self.assertEqual(writer.fields['b$'], {0: 'A', 1: 'B'})
        self.assertEqual(writer.fields['b$'][2], '?')

    def test_macro_let_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('LET')

        self._assert_error(writer, '#LET', 'No text parameter', prefix)
        self._assert_error(writer, '#LET()', "Missing variable name: ''", prefix)
        self._assert_error(writer, '#LET(=)', "Missing variable name: '='", prefix)
        self._assert_error(writer, '#LET(=1)', "Missing variable name: '=1'", prefix)
        self._assert_error(writer, '#LET(foo)', "Missing variable value: 'foo'", prefix)
        self._assert_error(writer, '#LET(foo=)', "Cannot parse integer value '': foo=", prefix)
        self._assert_error(writer, '#LET(foo', 'No closing bracket: (foo', prefix)
        self._assert_error(writer, '#LET(foo={wrong})', "Unrecognised field 'wrong': (foo={wrong})", prefix)
        self._assert_error(writer, '#LET(foo={bad)', 'Invalid format string: (foo={bad)', prefix)
        self._assert_error(writer, '#LET(foo=#IF({fix}<1)(a+b))', "Cannot parse integer value 'a+b': foo=#IF({fix}<1)(a+b)", prefix)
        self._assert_error(writer, '#LET(foo=#IF())', "No valid expression found: '#IF()'", ERROR_PREFIX.format('IF'))
        self._assert_error(writer, '#LET(f[]=)', "No values provided: 'f[]='", prefix)
        self._assert_error(writer, '#LET(f[]=(z,0:0))', "Invalid default integer value (z): (z,0:0)", prefix)
        self._assert_error(writer, '#LET(f[]=(1,x1:3))', "Invalid key (x1): (1,x1:3)", prefix)
        self._assert_error(writer, '#LET(f[]=(0,1:y))', "Invalid integer value (y): (0,1:y)", prefix)
        self._assert_error(writer, '#LET(f[]=1,2:2)', "No terminating delimiter: 1,2:2", prefix)

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
        writer = self._get_writer(skool='', variables=(('foo', 1), ('bar', 2)))
        self.assertEqual(writer.expand('#MAP({vars[foo]})(FAIL,1:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({vars[bar]})(FAIL,2:PASS)'), 'PASS')
        self.assertEqual(writer.expand('#MAP({vars[baz]})(FAIL,0:PASS)'), 'PASS')

    def test_macro_map_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('MAP')

        self._assert_error(writer, '#MAP', "No valid expression found: '#MAP'", prefix)
        self._assert_error(writer, '#MAPq', "No valid expression found: '#MAPq'", prefix)
        self._assert_error(writer, '#MAP({html)(0)', "Invalid format string: {html", prefix)
        self._assert_error(writer, '#MAP0', "No mappings provided: 0", prefix)
        self._assert_error(writer, '#MAP0 ()', "No mappings provided: 0", prefix)
        self._assert_error(writer, '#MAP0(1,2:3', "No closing bracket: (1,2:3", prefix)
        self._assert_error(writer, '#MAP0(1,x1:3)', "Invalid key (x1): (1,x1:3)", prefix)
        self._assert_error(writer, '#MAP({ease})(0)', "Unrecognised field 'ease': {ease}", prefix)

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

    def test_macro_n_with_replacement_fields(self):
        writer = self._get_writer(skool='', variables=[('w', 2)])
        self.assertEqual(writer.expand('#LET(v=3)#N({v},{vars[w]},,1,1)($)'), '$03')

    def test_macro_n_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('N')

        self._test_no_parameters(writer, 'N', 1)
        self._assert_error(writer, '#N(4,3,2,1)', "No text parameter", prefix)
        self._assert_error(writer, '#N,', "Missing required parameter in position 1/1: ','", prefix)
        self._assert_error(writer, '#N(,)', "Missing required parameter in position 1/1: ','", prefix)
        self._assert_error(writer, '#N,4', "Missing required parameter in position 1/1: ',4'", prefix)
        self._assert_error(writer, '#N(,4)', "Missing required parameter in position 1/1: ',4'", prefix)
        self._assert_error(writer, '#N(1,2,3,4,5,6)', "Too many parameters (expected 5): '1,2,3,4,5,6'", prefix)
        self._assert_error(writer, '#N(4,3,2,1)(a,b,c)', "Too many parameters (expected 2): 'a,b,c'", prefix)
        self._assert_error(writer, '#N(x,4)', "Cannot parse integer 'x' in parameter string: 'x,4'", prefix)
        self._assert_error(writer, '#N(2', "No closing bracket: (2", prefix)
        self._assert_error(writer, '#N({no},1)', "Unrecognised field 'no': {no},1", prefix)
        self._assert_error(writer, '#N({foo,1)', "Invalid format string: {foo,1", prefix)

    def test_macro_over_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('OVER')

        self._test_no_parameters(writer, 'OVER', 2, True)
        self._test_invalid_image_macro(writer, '#OVER1', "Missing required argument 'y': '1'", prefix)
        self._test_invalid_image_macro(writer, '#OVER1,y(f)', "Missing required argument 'y': '1,'", prefix)
        self._test_invalid_image_macro(writer, '#OVER1(f)', "Missing required argument 'y': '1'", prefix)
        self._test_invalid_image_macro(writer, '#OVER1,1', "No text parameter", prefix)
        self._test_invalid_image_macro(writer, '#OVER0,0,,,1(f)', "No text parameter", prefix)
        self._test_invalid_image_macro(writer, '#OVER0,0,,,2(f)', "No text parameter", prefix)
        self._test_invalid_image_macro(writer, '#OVER0,0,,,3(a)(b)', "No text parameter", prefix)
        self._test_invalid_image_macro(writer, '#OVER1,2,3,4,5,6(f)', "No terminating delimiter: ,6(f)", prefix)
        self._test_invalid_image_macro(writer, '#OVER(f)', "Cannot parse integer 'f' in parameter string: 'f'", prefix)
        self._test_invalid_image_macro(writer, '#OVER0,0(f)', "Not enough parameters (expected 2): 'f'", prefix)
        self._test_invalid_image_macro(writer, '#OVER0,0//f//', "Not enough parameters (expected 2): 'f'", prefix)
        self._test_invalid_image_macro(writer, '#OVER0,0(f,g,h)', "Too many parameters (expected 2): 'f,g,h'", prefix)
        self._test_invalid_image_macro(writer, '#OVER0,0//f/g/h//', "Too many parameters (expected 2): 'f/g/h'", prefix)
        self._test_invalid_image_macro(writer, '#OVER1,1(f', "No closing bracket: (f", prefix)
        self._test_invalid_image_macro(writer, '#OVER1,1//f', "No terminating delimiter: //f", prefix)
        self._test_invalid_image_macro(writer, '#OVER1,1//f/', "No terminating delimiter: //f/", prefix)
        self._test_invalid_image_macro(writer, '#OVER({x},1)(f)', "Unrecognised field 'x': {x},1", prefix)
        self._test_invalid_image_macro(writer, '#OVER({x,1)(f)', "Invalid format string: {x,1", prefix)
        self._test_invalid_image_macro(writer, '#OVERa=1(f)', "Unknown keyword argument: 'a=1'", prefix)

        return writer, prefix

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

    def test_macro_peek_replacement_field(self):
        writer = self._get_writer(snapshot=[1, 2, 3])
        writer.fields['address'] = 1
        self.assertEqual(writer.expand('#PEEK({address})'), '2')

    def test_macro_peek_invalid(self):
        writer = self._get_writer()
        writer.fields['x'] = 'x'
        prefix = ERROR_PREFIX.format('PEEK')

        self._test_no_parameters(writer, 'PEEK', 1)
        self._assert_error(writer, '#PEEK(3', "No closing bracket: (3", prefix)
        self._assert_error(writer, '#PEEK(4,5)', "Too many parameters (expected 1): '4,5'", prefix)
        self._assert_error(writer, '#PEEK(x)', "Cannot parse integer 'x' in parameter string: 'x'", prefix)
        self._assert_error(writer, '#PEEK({x})', "Cannot parse integer 'x' in parameter string: 'x'", prefix)
        self._assert_error(writer, '#PEEK({y})', "Unrecognised field 'y': {y}", prefix)
        self._assert_error(writer, '#PEEK({y)', "Invalid format string: {y", prefix)

    def test_macro_plot_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('PLOT')

        self._test_no_parameters(writer, 'PLOT', 2, True)
        self._test_invalid_image_macro(writer, '#PLOT1', "Missing required argument 'y': '1'", prefix)
        self._test_invalid_image_macro(writer, '#PLOT1,y(f)', "Missing required argument 'y': '1,'", prefix)
        self._test_invalid_image_macro(writer, '#PLOT1(f)', "Missing required argument 'y': '1'", prefix)
        self._test_invalid_image_macro(writer, '#PLOT1,1', "Missing frame name: #PLOT1,1", prefix)
        self._test_invalid_image_macro(writer, '#PLOT1,1,v(f)', "Missing frame name: #PLOT1,1,", prefix)
        self._test_invalid_image_macro(writer, '#PLOT(f)', "Cannot parse integer 'f' in parameter string: 'f'", prefix)
        self._test_invalid_image_macro(writer, '#PLOT1,1(f', "No closing bracket: (f", prefix)
        self._test_invalid_image_macro(writer, '#PLOT({x},1)(f)', "Unrecognised field 'x': {x},1", prefix)
        self._test_invalid_image_macro(writer, '#PLOT({x,1)(f)', "Invalid format string: {x,1", prefix)

        return writer, prefix

    def test_macro_pokes(self):
        writer = self._get_writer(skool='', snapshot=[0] * 20, variables=[('v', 247)])
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

        # Replacement fields
        output = writer.expand('#LET(addr=12)#POKES({addr},{vars[v]})')
        self.assertEqual(output, '')
        self.assertEqual(writer.snapshot[12], 247)

    def test_macro_pokes_invalid(self):
        writer = self._get_writer(snapshot=[0])
        prefix = ERROR_PREFIX.format('POKES')

        self._test_no_parameters(writer, 'POKES', 2)
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
        self._assert_error(writer, '#POKES(0,{no})', "Unrecognised field 'no': 0,{no}", prefix)
        self._assert_error(writer, '#POKES(0,{foo)', "Invalid format string: 0,{foo", prefix)

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

        self._test_no_parameters(writer, 'R', 1)
        self._assert_error(writer, '#R@main', "No parameters (expected 1): '@main'", prefix)
        self._assert_error(writer, '#R#bar', "No parameters (expected 1): '#bar'", prefix)
        self._assert_error(writer, '#R(baz)', "Cannot parse integer 'baz' in parameter string: 'baz'", prefix)
        self._assert_error(writer, '#R32768(qux', "No closing bracket: (qux", prefix)
        self._assert_error(writer, '#R({no})', "Unrecognised field 'no': {no}", prefix)
        self._assert_error(writer, '#R({foo)', "Invalid format string: {foo", prefix)

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

        self._test_invalid_image_macro(writer, '#SCR{0,0,23,14,5}(foo)', "Too many parameters in cropping specification (expected 4 at most): {0,0,23,14,5}", prefix)
        self._test_invalid_image_macro(writer, '#SCR{0,0,23,14(foo)', 'No closing brace on cropping specification: {0,0,23,14(foo)', prefix)
        self._test_invalid_image_macro(writer, '#SCR(foo', 'No closing bracket: (foo', prefix)
        self._test_invalid_image_macro(writer, '#SCR({no})(scr)', "Unrecognised field 'no': {no}", prefix)
        self._test_invalid_image_macro(writer, '#SCR{{nope}}', "Unrecognised field 'nope': {nope}", prefix)
        self._test_invalid_image_macro(writer, '#SCR({foo)', "Invalid format string: {foo", prefix)

    def test_macro_space(self):
        writer = self._get_writer(skool='', variables=[('n', 2)])
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
        self.assertEqual(writer.expand('#LET(m=1)[#SPACE({m}+{vars[n]})]'), '[{}]'.format(space * 3))

    def test_macro_space_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('SPACE')

        self._assert_error(writer, '#SPACE(2', "No closing bracket: (2", prefix)
        self._assert_error(writer, '#SPACE(5$3)', "Cannot parse integer '5$3' in parameter string: '5$3'", prefix)
        self._assert_error(writer, '#SPACE({no})', "Unrecognised field 'no': {no}", prefix)
        self._assert_error(writer, '#SPACE({foo)', "Invalid format string: {foo", prefix)

    def test_macro_str(self):
        snapshot = [0] * 65536
        snapshot[:5] = [ord(c) for c in 'Hello']
        snapshot[32768:32771] = [79, 75, 191] # OK?
        snapshot[49152:49155] = [94, 96, 127] # ↑£©
        snapshot[-7:] = [ord(c) for c in 'Goodbye']
        writer = self._get_writer(snapshot=snapshot)

        self.assertEqual(writer.expand('#STR0'), 'Hello')
        self.assertEqual(writer.expand('#STR0,0,2'), 'He')
        self.assertEqual(writer.expand('#STR(0,0,5)'), 'Hello')
        self.assertEqual(writer.expand('#STR(0+1,,4)'), 'ello')
        self.assertEqual(writer.expand('#LET(a=3)#STR({a})'), 'lo')
        self.assertEqual(writer.expand('#STR(0,,#IF(1)(4))'), 'Hell')
        self.assertEqual(writer.expand('#STR32768'), 'OK?')
        self.assertEqual(writer.expand('#STR49152'), '↑£©')
        self.assertEqual(writer.expand('#STR65529'), 'Goodbye')

    def test_macro_str_strips_whitespace(self):
        writer = self._get_writer(snapshot=[ord(c) for c in '  Hello   '])

        self.assertEqual(writer.expand('/#STR0,1,10/'), '/  Hello/')
        self.assertEqual(writer.expand('/#STR0,2,10/'), '/Hello   /')
        self.assertEqual(writer.expand('/#STR0,3,10/'), '/Hello/')

    def test_macro_str_with_spaces(self):
        writer = self._get_writer(snapshot=[ord(c) for c in '  A B  C   '])
        space = '&#160;' if isinstance(writer, HtmlWriter) else ' '

        self.assertEqual(writer.expand('/#STR0,4,11/'), '/..A B..C.../'.replace('.', space))
        self.assertEqual(writer.expand('/#STR0,5,11/'), '/..A B..C/'.replace('.', space))
        self.assertEqual(writer.expand('/#STR0,6,11/'), '/A B..C.../'.replace('.', space))
        self.assertEqual(writer.expand('/#STR0,7,11/'), '/A B..C/'.replace('.', space))

    def test_macro_str_with_end(self):
        writer = self._get_writer(snapshot=[ord(c) for c in 'Hello\x01Bye\x00\x80\xff'])

        self.assertEqual(writer.expand('#STR0,8($b==1)'), 'Hello')
        self.assertEqual(writer.expand('#LET(min=32)#STR0,8($b<{min})'), 'Hello')
        self.assertEqual(writer.expand('#STR0,8($b>101)'), 'He')
        self.assertEqual(writer.expand('#STR6,8($b==0)'), 'Bye')
        self.assertEqual(writer.expand('#STR6,8($b==$80)'), 'Bye\x00')
        self.assertEqual(writer.expand('#LET(end=255)#STR6,8($b=={end})'), 'Bye\x00\x80')

    def test_macro_str_invalid(self):
        writer = self._get_writer(snapshot=[0])
        prefix = ERROR_PREFIX.format('STR')

        self._test_no_parameters(writer, 'STR', 1)
        self._assert_error(writer, '#STR(1,2,3,4)', "Too many parameters (expected 3): '1,2,3,4'", prefix)
        self._assert_error(writer, '#STR(2', "No closing bracket: (2", prefix)
        self._assert_error(writer, '#STR(0,5$3)', "Cannot parse integer '5$3' in parameter string: '0,5$3'", prefix)
        self._assert_error(writer, '#STR({no})', "Unrecognised field 'no': {no}", prefix)
        self._assert_error(writer, '#STR({foo)', "Invalid format string: {foo", prefix)
        self._assert_error(writer, '#STR0,8(1', "No closing bracket: (1", prefix)
        self._assert_error(writer, '#STR0,8(x)', "Cannot parse integer 'x' in parameter string: 'x'", prefix)
        self._assert_error(writer, '#STR0,8({nope})', "Unrecognised field 'nope': {nope}", prefix)
        self._assert_error(writer, '#STR0,8({bar)', "Invalid format string: {bar", prefix)

    def test_macro_tstates(self):
        skool = """
            @start
            @assemble=2,2
            ; Routine
            c32768 XOR A       ; 4 T-states
             32769 ADD A,(HL)  ; 7 T-states
             32770 JR NC,32772 ; 12/7 T-states
             32772 RET         ; 10 T-states
        """
        writer = self._get_writer(skool=skool)

        self.assertEqual(writer.expand('#TSTATES32768'), '4')
        self.assertEqual(writer.expand('#TSTATES32768,32770'), '11')
        self.assertEqual(writer.expand('#TSTATES32770'), '7')
        self.assertEqual(writer.expand('#TSTATES32770,,1'), '12')
        self.assertEqual(writer.expand('#TSTATES32770,32773'), '17')
        self.assertEqual(writer.expand('#TSTATES32770,32773,1'), '22')
        self.assertEqual(writer.expand('#TSTATES32769,,2($min or $max)'), '7 or 7')
        self.assertEqual(writer.expand('#TSTATES32770,,2/${min} or ${max}/'), '7 or 12')
        self.assertEqual(writer.expand('#TSTATES32770,32773,2[$min or $max]'), '17 or 22')
        self.assertEqual(writer.expand('#TSTATES32770,32773,2|#EVAL(($min+$max)/2)|'), '19')
        self.assertEqual(writer.expand('#LET(a=32768)#TSTATES({a},{a}+2)'), '11')

    def test_macro_tstates_with_simulator(self):
        skool = """
            @start
            @assemble=2,2
            ; Routine
            c32768 LD B,2     ; 7 T-states
            *32770 DJNZ 32770 ; 13 + 8 = 21 T-states
             32772 RET
        """
        writer = self._get_writer(skool=skool)

        self.assertEqual(writer.expand('#TSTATES32768,32772,4'), '28')
        self.assertEqual(writer.expand('#TSTATES32768,32772,6($tstates T-states)'), '28 T-states')

    def test_macro_tstates_with_simulator_does_not_modify_writer_snapshot(self):
        skool = """
            @start
            @assemble=2,2
            ; Routine
            c32768 LD A,6
             32770 LD (32768),A
             32773 RET
        """
        writer = self._get_writer(skool=skool)
        writer.expand('#TSTATES32768,32773,4')
        self.assertEqual(writer.snapshot[32768], 62)

    def test_macro_tstates_invalid(self):
        skool = """
            @start
            @assemble=2,2
            ; Stuff
            c32768 XOR A
             32769 DEFB 0
        """
        writer = self._get_writer(skool=skool)
        prefix = ERROR_PREFIX.format('TSTATES')

        self._test_no_parameters(writer, 'TSTATES', 1)
        self._assert_error(writer, '#TSTATES32768,32770', "Failed to get timing for instruction at 32769", prefix)
        self._assert_error(writer, '#TSTATES32769', "Failed to get timing for instruction at 32769", prefix)
        self._assert_error(writer, '#TSTATES32770', "Failed to get timing for instruction at 32770", prefix)
        self._assert_error(writer, '#TSTATES32768,,4', "Missing stop address: '32768,,4'", prefix)
        self._assert_error(writer, '#TSTATES(1,2,3,4)', "Too many parameters (expected 3): '1,2,3,4'", prefix)
        self._assert_error(writer, '#TSTATES(2', "No closing bracket: (2", prefix)
        self._assert_error(writer, '#TSTATES(0,5$3)', "Cannot parse integer '5$3' in parameter string: '0,5$3'", prefix)
        self._assert_error(writer, '#TSTATES({no})', "Unrecognised field 'no': {no}", prefix)
        self._assert_error(writer, '#TSTATES({foo)', "Invalid format string: {foo", prefix)
        self._assert_error(writer, '#TSTATES32768,,2(hi', "No closing bracket: (hi", prefix)
        self._assert_error(writer, '#TSTATES32768,,2/hi', "No terminating delimiter: /hi", prefix)

    def test_macro_sim(self):
        skool = """
            @start
            @assemble=2,2
            ; Routine
            c32768 INC A
             32769 INC B
             32770 INC C
             32771 INC D
             32772 INC E
             32773 ADD HL,BC
             32774 ADD IX,DE
             32776 ADD IY,BC
             32778 EXX
             32779 INC B
             32780 INC C
             32781 INC D
             32782 INC E
             32783 ADD HL,BC
             32784 EXX
             32785 EX AF,AF'
             32786 INC A
             32787 EX AF,AF'
             32788 LD I,A
             32790 LD R,A
             32792 RET
             32793 PUSH HL
             32794 CALL 32768
             32797 JP 32768
        """
        writer = self._get_writer(skool=skool)
        macro = (
            "#FORMAT(A={sim[A]},F={sim[F]},BC={sim[BC]},DE={sim[DE]},HL={sim[HL]},A'={sim[^A]},"
            "F'={sim[^F]},BC'={sim[^BC]},DE'={sim[^DE]},HL'={sim[^HL]},IX={sim[IX]},IY={sim[IY]},"
            "I={sim[I]},R={sim[R]},SP={sim[SP]},PC={sim[PC]},tstates={sim[tstates]})"
        )

        # First run
        self.assertEqual(writer.expand('#SIM32797,32793,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,23296'), '')
        self.assertEqual(writer.expand(macro), "A=2,F=0,BC=260,DE=261,HL=265,A'=7,F'=1,BC'=265,DE'=266,HL'=275,IX=272,IY=272,I=2,R=3,SP=23294,PC=32797,tstates=164")

        # Resume
        self.assertEqual(writer.expand('#SIM32792'), '')
        self.assertEqual(writer.expand(macro), "A=3,F=0,BC=517,DE=518,HL=782,A'=8,F'=9,BC'=522,DE'=523,HL'=797,IX=790,IY=789,I=3,R=3,SP=23294,PC=32792,tstates=300")

        # Clear
        self.assertEqual(writer.expand('#SIM32792,32768,1'), '')
        self.assertEqual(writer.expand(macro), "A=1,F=0,BC=257,DE=257,HL=257,A'=1,F'=0,BC'=257,DE'=257,HL'=257,IX=257,IY=23867,I=1,R=1,SP=23552,PC=32792,tstates=126")

    def test_macro_sim_modifies_internal_memory_snapshot(self):
        skool = """
            @start
            @assemble=2,2
            ; Routine
            c49152 LD (HL),A
             49153 RET
        """
        writer = self._get_writer(skool=skool)
        writer.expand('#SIM(start=49152,stop=49153,a=255,hl=32768)')
        self.assertEqual(writer.snapshot[32768], 255)
        writer.expand('#PUSHS #SIM(start=49152,stop=49153,a=77,hl=32768) #POPS')
        self.assertEqual(writer.snapshot[32768], 255)

    def test_macro_sim_with_keyword_arguments_and_replacement_fields(self):
        skool = """
            @start
            @assemble=2,2
            ; Routine
            c49152 INC HL
             49153 RET
        """
        writer = self._get_writer(skool=skool)
        writer.fields.update({'start': 49152, 'stop': 49153, 'hl': 1})
        self.assertEqual(writer.expand('#SIM(start={start},stop={stop},hl={hl})'), '')
        self.assertEqual(writer.expand('#FORMAT(HL={sim[HL]})'), 'HL=2')

    def test_macro_sim_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('SIM')

        self._test_no_parameters(writer, 'SIM', 1)
        params = '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19'
        self._assert_error(writer, f'#SIM({params})', f"Too many parameters (expected 18): '{params}'", prefix)
        self._assert_error(writer, '#SIM(30000', "No closing bracket: (30000", prefix)
        self._assert_error(writer, '#SIM(0,5$3)', "Cannot parse integer '5$3' in parameter string: '0,5$3'", prefix)
        self._assert_error(writer, '#SIM({no})', "Unrecognised field 'no': {no}", prefix)
        self._assert_error(writer, '#SIM({foo)', "Invalid format string: {foo", prefix)

    def test_macro_udg_invalid(self):
        writer = self._get_writer(snapshot=[0] * 8)
        prefix = ERROR_PREFIX.format('UDG')

        self._test_no_parameters(writer, 'UDG', 1, True)
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
        self._test_invalid_image_macro(writer, '#UDG0{0,0,23,14,5}(foo)', "Too many parameters in cropping specification (expected 4 at most): {0,0,23,14,5}", prefix)
        self._test_invalid_image_macro(writer, '#UDG(foo)', "Cannot parse integer 'foo' in parameter string: 'foo'", prefix)
        self._test_invalid_image_macro(writer, '#UDG0{0,0,23,14(foo)', 'No closing brace on cropping specification: {0,0,23,14(foo)', prefix)
        self._test_invalid_image_macro(writer, '#UDG0(foo', 'No closing bracket: (foo', prefix)
        self._test_invalid_image_macro(writer, '#UDG({no})', "Unrecognised field 'no': {no}", prefix)
        self._test_invalid_image_macro(writer, '#UDG0:({nay})', "Unrecognised field 'nay': {nay}", prefix)
        self._test_invalid_image_macro(writer, '#UDG0{{nope}}', "Unrecognised field 'nope': {nope}", prefix)
        self._test_invalid_image_macro(writer, '#UDG({foo)', "Invalid format string: {foo", prefix)

    def test_macro_udgarray_invalid(self):
        writer = self._get_writer(snapshot=[0] * 16)
        prefix = ERROR_PREFIX.format('UDGARRAY')

        self._test_no_parameters(writer, 'UDGARRAY', 1, True)

        self._test_invalid_image_macro(writer, '#UDGARRAY,5;0(foo)', "Missing required argument 'width': ',5'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY(,5);0(foo)', "Missing required argument 'width': ',5'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAYscale=4;0(foo)', "Missing required argument 'width': 'scale=4'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY(scale=4);0(foo)', "Missing required argument 'width': 'scale=4'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY,scale=4;0(foo)', "Missing required argument 'width': ',scale=4'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY(,scale=4);0(foo)', "Missing required argument 'width': ',scale=4'", prefix)

        self._test_invalid_image_macro(writer, '#UDGARRAY1;(foo)', 'Expected UDG address range specification: #UDGARRAY1;', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1()(foo)', 'Expected UDG address range specification: #UDGARRAY1(', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;,2(foo)', 'Expected UDG address range specification: #UDGARRAY1;', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1(,2)(foo)', 'Expected UDG address range specification: #UDGARRAY1(', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0:(foo)', 'Expected mask address range specification: #UDGARRAY1;0:', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1(0:)(foo)', 'Expected mask address range specification: #UDGARRAY1(0:', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0:,2(foo)', 'Expected mask address range specification: #UDGARRAY1;0:', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1(0:,2)(foo)', 'Expected mask address range specification: #UDGARRAY1(0:', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0@(foo)', 'Expected attribute address range specification: #UDGARRAY1;0@', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0@1;(foo)', 'Expected attribute address range specification: #UDGARRAY1;0@1;', prefix)

        self._test_invalid_image_macro(writer, '#UDGARRAY1;0', 'Missing filename: #UDGARRAY1;0', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0()', 'Missing filename: #UDGARRAY1;0()', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0{0,0}1(foo)', 'Missing filename: #UDGARRAY1;0{0,0}', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0(*)', 'Missing filename or frame ID: #UDGARRAY1;0(*)', prefix)

        self._test_invalid_image_macro(writer, '#UDGARRAY1,2,3,4,5,6,7,8,9,10,11;0', "Missing filename: #UDGARRAY1,2,3,4,5,6,7,8,9,10", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0,1,2,3,4', "Missing filename: #UDGARRAY1;0,1,2,3", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0:0,1,2', "Missing filename: #UDGARRAY1;0:0,1", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0{0,0,23,14,5}(foo)', "Too many parameters in cropping specification (expected 4 at most): {0,0,23,14,5}", prefix)

        self._test_invalid_image_macro(writer, '#UDGARRAY(foo)', "Cannot parse integer 'foo' in parameter string: 'foo'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;32768xJ', "Invalid multiplier in address range specification: 32768xJ", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0x2:8xK', "Invalid multiplier in address range specification: 8xK", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0x2@2xn', "Invalid multiplier in address range specification: 2xn", prefix)

        self._test_invalid_image_macro(writer, '#UDGARRAY1;0{0,0,23,14(foo)', 'No closing brace on cropping specification: {0,0,23,14(foo)', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0(foo', 'No closing bracket: (foo', prefix)

        self._test_invalid_image_macro(writer, '#UDGARRAY({no});0(udg)', "Unrecognised field 'no': {no}", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;({nope})(udg)', "Unrecognised field 'nope': {nope}", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0x({nah})(udg)', "Unrecognised field 'nah': {nah}", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0,({nein})(udg)', "Unrecognised field 'nein': {nein}", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0:({nay})(udg)', "Unrecognised field 'nay': {nay}", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0:0x({nae})(udg)', "Unrecognised field 'nae': {nae}", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0:0,({nada})(udg)', "Unrecognised field 'nada': {nada}", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0@({nix})(udg)', "Unrecognised field 'nix': {nix}", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0{{nyet}}(udg)', "Unrecognised field 'nyet': {nyet}", prefix)

        self._test_invalid_image_macro(writer, '#UDGARRAY({foo);0(udg)', "Invalid format string: {foo", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;({bar)(udg)', "Invalid format string: {bar", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0,({baz)(udg)', "Invalid format string: {baz", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0:({qux)(udg)', "Invalid format string: {qux", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0:0,({xyzzy)(udg)', "Invalid format string: {xyzzy", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0@({bish)(udg)', "Invalid format string: {bish", prefix)

    def test_macro_udgarray_frames_invalid(self):
        writer = self._get_writer(snapshot=[0] * 8)
        prefix = ERROR_PREFIX.format('UDGARRAY')

        self._test_invalid_image_macro(writer, '#UDGARRAY*()(img)', 'No frames specified: #UDGARRAY*()(img)', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*foo', 'Missing filename: #UDGARRAY*foo', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*(foo)', 'Missing filename: #UDGARRAY*(foo)', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*foo()', 'Missing filename: #UDGARRAY*foo()', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*foo(bar', 'No closing bracket: (bar', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*(foo(bar)', 'No closing bracket: (foo(bar)', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*foo,(d,x)(bar', "Cannot parse integer 'd' in parameter string: 'd,x'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*foo,({no})(bar', "Unrecognised field 'no': {no}", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*foo,({bar)(bar', "Invalid format string: {bar", prefix)

        return writer, prefix

    def test_macro_udgs_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('UDGS')

        self._test_no_parameters(writer, 'UDGS', 2, True)
        self._test_invalid_image_macro(writer, '#UDGS2', "Missing required argument 'height': '2'", prefix)
        self._test_invalid_image_macro(writer, '#UDGS(2)', "Missing required argument 'height': '2'", prefix)
        self._test_invalid_image_macro(writer, '#UDGS,2', "Missing required argument 'width': ',2'", prefix)
        self._test_invalid_image_macro(writer, '#UDGS(,2)', "Missing required argument 'width': ',2'", prefix)
        self._test_invalid_image_macro(writer, '#UDGSheight=2', "Missing required argument 'width': 'height=2'", prefix)
        self._test_invalid_image_macro(writer, '#UDGS(height=2)', "Missing required argument 'width': 'height=2'", prefix)
        self._test_invalid_image_macro(writer, '#UDGS1,1', "Missing filename: #UDGS1,1", prefix)
        self._test_invalid_image_macro(writer, '#UDGS1,1(*)', "Missing filename or frame ID: #UDGS1,1(*)", prefix)
        self._test_invalid_image_macro(writer, '#UDGS0,1', "Invalid dimensions: #UDGS0,1", prefix)
        self._test_invalid_image_macro(writer, '#UDGS1,0', "Invalid dimensions: #UDGS1,0", prefix)
        self._test_invalid_image_macro(writer, '#UDGS(x=2)', "Unknown keyword argument: 'x=2'", prefix)
        self._test_invalid_image_macro(writer, '#UDGS(1,2,3,4,5,6,7,8,9)', "Too many parameters (expected 8): '1,2,3,4,5,6,7,8,9'", prefix)
        self._test_invalid_image_macro(writer, '#UDGS1,1{0,0,23,14,5}(foo)(f)', "Too many parameters in cropping specification (expected 4 at most): {0,0,23,14,5}", prefix)
        self._test_invalid_image_macro(writer, '#UDGS(foo)', "Cannot parse integer 'foo' in parameter string: 'foo'", prefix)
        self._test_invalid_image_macro(writer, '#UDGS1,1{foo}', "Cannot parse integer 'foo' in parameter string: 'foo'", prefix)
        self._test_invalid_image_macro(writer, '#UDGS(1,1', 'No closing bracket: (1,1', prefix)
        self._test_invalid_image_macro(writer, '#UDGS1,1{0,0,23,14(foo)(f)', 'No closing brace on cropping specification: {0,0,23,14(foo)(f)', prefix)
        self._test_invalid_image_macro(writer, '#UDGS1,1(foo', 'No closing bracket: (foo', prefix)
        self._test_invalid_image_macro(writer, '#UDGS1,1(foo)(f', 'No closing bracket: (f', prefix)
        self._test_invalid_image_macro(writer, '#UDGS({no},1)', "Unrecognised field 'no': {no},1", prefix)
        self._test_invalid_image_macro(writer, '#UDGS1,1{{nope}}', "Unrecognised field 'nope': {nope}", prefix)
        self._test_invalid_image_macro(writer, '#UDGS({foo,1)', "Invalid format string: {foo,1", prefix)

        return writer, prefix

    def test_macro_version(self):
        writer = self._get_writer()
        output = writer.expand('#VERSION')
        self.assertEqual(output, VERSION)

    def test_macro_while(self):
        writer = self._get_writer(snapshot=[1, 1, 1, 1, 1, 1, 1, 0])

        # Condition always false
        self.assertEqual(writer.expand('#WHILE(0)(hello)'), '')

        # Condition true once
        writer.expand('#LET(c=1)')
        self.assertEqual(writer.expand('#WHILE({c})(#LET(c={c}-1)hello)'), 'hello')

        # Condition true twice
        writer.expand('#LET(c=0)')
        self.assertEqual(writer.expand('#WHILE({c}<2)(#LET(c={c}+1)hello)'), 'hellohello')

        # Condition true several times
        writer.expand('#LET(a=0)')
        self.assertEqual(writer.expand('#WHILE(#PEEK({a}))(#EVAL({a})#LET(a={a}+1))'), '0123456')

    def test_macro_while_with_alternative_delimiters(self):
        writer = self._get_writer()
        writer.expand('#LET(c=2)')
        self.assertEqual(writer.expand('#WHILE({c})/#LET(c={c}-1)hello/'), 'hellohello')

    def test_macro_while_strips_whitespace(self):
        writer = self._get_writer()
        writer.expand('#LET(c=3)')
        macro = """
           #WHILE({c})(
              #EVAL({c})
              #LET(c={c}-1)
           )
        """.strip()
        self.assertEqual(writer.expand(f'/{macro}/'), '/321/')

    def test_macro_while_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('WHILE')

        self._assert_error(writer, '#WHILE', "Missing conditional expression", prefix)
        self._assert_error(writer, '#WHILE()', "Missing conditional expression", prefix)
        self._assert_error(writer, '#WHILE/body/', "Missing conditional expression", prefix)
        self._assert_error(writer, '#WHILE(0)(body', "No closing bracket: (body", prefix)
        self._assert_error(writer, '#WHILE(0)/body', "No terminating delimiter: /body", prefix)
        self._assert_error(writer, '#WHILE(1,2)(body)', "Too many parameters (expected 1): '1,2'", prefix)
        self._assert_error(writer, '#WHILE(x)(body)', "Cannot parse integer 'x' in parameter string: 'x'", prefix)
        self._assert_error(writer, '#WHILE({no})(body)', "Unrecognised field 'no': {no}", prefix)
        self._assert_error(writer, '#WHILE({foo)(body)', "Invalid format string: {foo", prefix)
