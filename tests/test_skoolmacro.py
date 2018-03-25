import re

from skoolkittest import SkoolKitTestCase
from skoolkit.skoolmacro import (parse_ints, parse_strings, parse_brackets, parse_image_macro,
                                 parse_address_range, MacroParsingError, NoParametersError, MissingParameterError,
                                 TooManyParametersError)

class SkoolMacroTest(SkoolKitTestCase):
    def test_parse_ints_without_kwargs(self):
        # No parameters expected
        self.assertEqual([0], parse_ints('', 0))
        self.assertEqual([0], parse_ints('{not a param}', 0))
        self.assertEqual([0], parse_ints('xxx', 0))

        # Exact number of parameters
        text = '1,$2,3'
        end, p1, p2, p3 = parse_ints(text, 0, 3)
        self.assertEqual((1, 2, 3), (p1, p2, p3))
        self.assertEqual(end, len(text))

        # Default parameter values
        text = '$1,2,3'
        end, p1, p2, p3, p4, p5 = parse_ints(text, 0, 5, (4, 5))
        self.assertEqual((1, 2, 3, 4, 5), (p1, p2, p3, p4, p5))
        self.assertEqual(end, len(text))

        # More than enough parameters
        text = '1,2,3'
        end, p1, p2 = parse_ints(text, 0, 2)
        self.assertEqual((1, 2), (p1, p2))
        self.assertEqual(end, 3)

        # Blank parameters
        text = '1,,$a,'
        end, p1, p2, p3, p4 = parse_ints(text, 0, 4, (0, 0, 0))
        self.assertEqual((1, 0, 10, 0), (p1, p2, p3, p4))
        self.assertEqual(end, len(text))

        # First parameter optional and omitted
        end, p1, p2, p3 = parse_ints(',1,2', 0, 3, (0, 5, 10))
        self.assertEqual((0, 1, 2), (p1, p2, p3))
        self.assertEqual(end, 4)

        # Empty parameter string
        end, p1 = parse_ints('', 0, 1, (1,))
        self.assertEqual(p1, 1)
        self.assertEqual(end, 0)

        # Empty parameter string in brackets
        end, p1 = parse_ints('()', 0, 1, (1,))
        self.assertEqual(p1, 1)
        self.assertEqual(end, 2)

        # Adjacent non-numeric characters
        junk = 'xyz'
        text = '1,2{0}'.format(junk)
        end, p1, p2 = parse_ints(text, 0, 2)
        self.assertEqual((1, 2), (p1, p2))
        self.assertEqual(end, len(text) - len(junk))

        # Arithmetic expressions: +, -, *, /, **
        text = '(-1,1+1,5-2,10-3*2,2+7/2,3**2)'
        self.assertEqual([len(text), -1, 2, 3, 4, 5, 9], parse_ints(text, 0, 6))

        # Arithmetic expressions: &, |, ^, %
        text = '(6&3,8|4,7^2,10%3)'
        self.assertEqual([len(text), 2, 12, 5, 1], parse_ints(text, 0, 4))

        # Arithmetic expressions: <<, >>
        text = '(1<<5,96>>3)'
        self.assertEqual([len(text), 32, 12], parse_ints(text, 0, 2))

        # Arithmetic expressions: ==, !=, >, <, >=, <=
        text = '(1==1,1!=1,5>4,5<4,6>=3,6<=3)'
        self.assertEqual([len(text), 1, 0, 1, 0, 1, 0], parse_ints(text, 0, 6))

        # Arithmetic expressions: (, )
        text = '(1+(1+1)/2,(2+2)*3-1)'
        self.assertEqual([len(text), 2, 11], parse_ints(text, 0, 2))

        # Arithmetic expressions: spaces
        text = '(1 - (1 + 1) / 2, (2 + 2) * 3 + 1)'
        self.assertEqual([len(text), 0, 13], parse_ints(text, 0, 2))

    def test_parse_ints_with_kwargs(self):
        for param_string, defaults, names, exp_params in (
            ('1,baz=3', (2, 4, 6), ('foo', 'bar', 'baz', 'qux'), [1, 2, 3, 6]),
            ('g=0,h=', (1, 2, 3), ('f', 'g', 'h'), [1, 0, 3]),
        ):
            params = parse_ints(param_string, defaults=defaults, names=names)[1:]
            self.assertEqual(exp_params, params)

        # First parameter optional and omitted
        end, p, q, r = parse_ints(',r=2', defaults=(0, 5, 10), names=('p', 'q', 'r'))
        self.assertEqual((0, 5, 2), (p, q, r))
        self.assertEqual(end, 4)

        # Arithmetic expressions with brackets
        text = '(foo=1+(3-2)*4,baz=(1^255)+1)'
        names = ('foo', 'bar', 'baz')
        defaults = (2, 3)
        self.assertEqual([len(text), 5, 2, 255], parse_ints(text, defaults=defaults, names=names))

        # Arithmetic expressions with spaces
        text = '(foo = 12 / 3, bar = 34 & 15, baz = 7 | 8)'
        names = ('foo', 'bar', 'baz')
        self.assertEqual([len(text), 4, 2, 15], parse_ints(text, names=names))

    def test_parse_ints_not_enough_parameters(self):
        with self.assertRaisesRegex(MacroParsingError, re.escape("Not enough parameters (expected 4): '1,2,$3'")):
            parse_ints('1,2,$3', num=4)

    def test_parse_ints_with_required_parameter_left_blank(self):
        for text, num, defaults, pos in (
            (',1,2', 3, (), 1),
            (',1,', 3, (2,), 1),
            ('0,,2', 3, (), 2),
            ('0,,', 3, (2,), 2),
            ('0,1,', 3, (), 3),
            ('0,1,', 3, (), 3)
        ):
            error_msg = "Missing required parameter in position {}/{}: '{}'".format(pos, num - len(defaults), text)
            for param_string in (text, '({})'.format(text)):
                with self.assertRaisesRegex(MacroParsingError, error_msg):
                    parse_ints(param_string, num=num, defaults=defaults)

    def test_parse_ints_with_kwargs_not_enough_parameters(self):
        with self.assertRaisesRegex(MacroParsingError, "Missing required argument 'a': 'b=4,c=5'$"):
            parse_ints('b=4,c=5', defaults=(2, 3), names=('a', 'b', 'c'))

    def test_parse_ints_non_kwarg_after_kwarg(self):
        with self.assertRaisesRegex(MacroParsingError, "Non-keyword argument after keyword argument: '3'"):
            parse_ints('1,bar=2,3', names=('foo', 'bar', 'baz'))

    def test_parse_ints_unknown_kwarg(self):
        with self.assertRaisesRegex(MacroParsingError, "Unknown keyword argument: 'qux=2'"):
            parse_ints('foo=1,qux=2', names=('foo', 'bar'))

    def test_parse_strings(self):
        # One string, blank
        self.assertEqual((2, ''), parse_strings('()', num=1))
        self.assertEqual((2, ''), parse_strings('{}', num=1))
        self.assertEqual((2, ''), parse_strings('[]', num=1))
        self.assertEqual((2, ''), parse_strings('//', num=1))
        self.assertEqual((2, ''), parse_strings('||', num=1))

        # One string, not blank
        self.assertEqual((5, 'foo'), parse_strings('(foo)', num=1))
        self.assertEqual((5, 'bar'), parse_strings('{bar}', num=1))
        self.assertEqual((5, 'baz'), parse_strings('[baz]', num=1))
        self.assertEqual((5, 'qux'), parse_strings('/qux/', num=1))
        self.assertEqual((7, 'xyzzy'), parse_strings('|xyzzy|', num=1))

        # Two strings
        self.assertEqual((9, ['foo', 'bar']), parse_strings('(foo,bar)', num=2))
        self.assertEqual((9, ['foo', 'bar']), parse_strings('{foo,bar}', num=2))
        self.assertEqual((9, ['foo', 'bar']), parse_strings('[foo,bar]', num=2))
        self.assertEqual((11, ['foo', 'bar']), parse_strings('/,foo,bar,/', num=2))
        self.assertEqual((11, ['foo', 'bar']), parse_strings('||foo|bar||', num=2))

        # Three strings, default values
        self.assertEqual((2, ['', 'bar', 'baz']), parse_strings('()', num=3, defaults=('bar', 'baz')))
        self.assertEqual((5, ['foo', 'bar', 'baz']), parse_strings('{foo}', num=3, defaults=('bar', 'baz')))
        self.assertEqual((9, ['foo', 'bar', 'baz']), parse_strings('[foo,bar]', num=3, defaults=('baz',)))
        self.assertEqual((8, ['foo', '', 'baz']), parse_strings(':;foo;;:', num=3, defaults=('bim', 'baz')))

        # Unlimited strings
        self.assertEqual((2, ['']), parse_strings('()', num=0))
        self.assertEqual((5, ['foo']), parse_strings('(foo)', num=0))
        self.assertEqual((9, ['foo', 'bar']), parse_strings('{foo,bar}', num=0))
        self.assertEqual((13, ['foo', 'bar', 'baz']), parse_strings('[foo,bar,baz]', num=0))
        self.assertEqual((19, ['foo', 'bar', 'baz', 'qux']), parse_strings('/ foo bar baz qux /', num=0))
        self.assertEqual((19, ['foo', '', 'baz', '', 'xyzzy']), parse_strings('|;foo;;baz;;xyzzy;|', num=0))

    def test_parse_strings_no_parameters(self):
        msg = "No text parameter"

        with self.assertRaisesRegex(NoParametersError, msg):
            parse_strings('')

        with self.assertRaisesRegex(NoParametersError, msg):
            parse_strings(' (')

        with self.assertRaisesRegex(NoParametersError, msg):
            parse_strings('\t{')

    def test_parse_strings_no_terminating_delimiter(self):
        text = '(foo'
        with self.assertRaisesRegex(MacroParsingError, re.escape("No closing bracket: {}".format(text))):
            parse_strings(text)

        text = '{foo)'
        with self.assertRaisesRegex(MacroParsingError, re.escape("No closing bracket: {}".format(text))):
            parse_strings(text)

        text = '[foo}'
        with self.assertRaisesRegex(MacroParsingError, re.escape("No closing bracket: {}".format(text))):
            parse_strings(text)

        text = '/foo,bar/'
        with self.assertRaisesRegex(MacroParsingError, "No terminating delimiter: {}".format(text)):
            parse_strings(text)

        text = '//foo/bar/'
        with self.assertRaisesRegex(MacroParsingError, "No terminating delimiter: {}".format(text)):
            parse_strings(text)

    def test_parse_strings_too_many_parameters(self):
        text = '(foo,bar,baz)'
        with self.assertRaises(TooManyParametersError) as cm:
            parse_strings(text, num=2)
        self.assertEqual(cm.exception.args[0], "Too many parameters (expected 2): '{}'".format(text[1:-1]))
        self.assertEqual(cm.exception.args[1], len(text))

    def test_parse_strings_missing_parameters(self):
        text = '(foo,bar)'
        with self.assertRaises(MissingParameterError) as cm:
            parse_strings(text, num=3)
        self.assertEqual(cm.exception.args[0], "Not enough parameters (expected 3): '{}'".format(text[1:-1]))
        self.assertEqual(cm.exception.args[1], len(text))

        text = '{foo,bar}'
        with self.assertRaises(MissingParameterError) as cm:
            parse_strings(text, num=5, defaults=('qux',))
        self.assertEqual(cm.exception.args[0], "Not enough parameters (expected 4): '{}'".format(text[1:-1]))
        self.assertEqual(cm.exception.args[1], len(text))

    def test_parse_brackets(self):
        self.assertEqual((0, None), parse_brackets(''))
        self.assertEqual((0, None), parse_brackets('xxx'))
        self.assertEqual((5, ''), parse_brackets('...()...', 3))
        self.assertEqual((5, 'foo'), parse_brackets('(foo)'))

    def test_parse_brackets_with_default_value(self):
        self.assertEqual((0, 'bar'), parse_brackets('', default='bar'))
        self.assertEqual((0, 'bar'), parse_brackets('xxx', default='bar'))
        self.assertEqual((2, ''), parse_brackets('()', default='bar'))
        self.assertEqual((5, 'foo'), parse_brackets('(foo)', default='bar'))

    def test_parse_brackets_with_custom_delimiters(self):
        self.assertEqual((0, None), parse_brackets('', opening='<', closing='>'))
        self.assertEqual((0, None), parse_brackets('xxx', opening='<', closing='>'))
        self.assertEqual((0, None), parse_brackets('()', opening='<', closing='>'))
        self.assertEqual((0, None), parse_brackets('(foo)', opening='<', closing='>'))
        self.assertEqual((2, ''), parse_brackets('<>', opening='<', closing='>'))
        self.assertEqual((5, 'foo'), parse_brackets('<foo>', opening='<', closing='>'))
        self.assertEqual((5, 'bar'), parse_brackets('[bar]', opening='[', closing=']'))

    def test_parse_brackets_with_default_value_and_custom_delimiters(self):
        self.assertEqual((0, 'bar'), parse_brackets('', 0, 'bar', '<', '>'))
        self.assertEqual((1, 'bar'), parse_brackets('xxx', 1, 'bar', '<', '>'))
        self.assertEqual((0, 'bar'), parse_brackets('()', 0, 'bar', '<', '>'))
        self.assertEqual((0, 'bar'), parse_brackets('(foo)', 0, 'bar', '<', '>'))
        self.assertEqual((2, ''), parse_brackets('<>', 0, 'bar', '<', '>'))
        self.assertEqual((5, 'foo'), parse_brackets('<foo>', 0, 'bar', '<', '>'))

    def test_parse_image_macro_with_no_parameters_expected(self):
        # No parameters, no cropping spec, no filename
        end, crop_rect, fname, frame, alt, values = parse_image_macro('xxx')
        self.assertEqual(end, 0)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, '')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([], values)

        # No parameters, no cropping spec, filename
        end, crop_rect, fname, frame, alt, values = parse_image_macro('#FOO(image)', 4)
        self.assertEqual(end, 11)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, 'image')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([], values)

        # No parameters, cropping spec, no filename
        end, crop_rect, fname, frame, alt, values = parse_image_macro('{1,2,3,4}')
        self.assertEqual(end, 9)
        self.assertEqual(crop_rect, (1, 2, 3, 4))
        self.assertEqual(fname, '')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([], values)

    def test_parse_image_macro_with_parameters(self):
        # One required parameter
        end, crop_rect, fname, frame, alt, values = parse_image_macro('#BAR1', 4, names=('arg',))
        self.assertEqual(end, 5)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, '')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([1], values)

        # Two required parameters
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1,2', names=('arga', 'argb'))
        self.assertEqual(end, 3)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, '')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([1, 2], values)

        # One required parameter, one optional and omitted
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1', defaults=(2,), names=('arga', 'argb'))
        self.assertEqual(end, 1)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, '')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([1, 2], values)

        # One required parameter, two optional, second omitted
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1,,3', defaults=(2, 3), names=('arga', 'argb', 'argc'))
        self.assertEqual(end, 4)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, '')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([1, 2, 3], values)

        # One required parameter, two optional, second omitted, third named
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1,argc=3', defaults=(2, 3), names=('arga', 'argb', 'argc'))
        self.assertEqual(end, 8)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, '')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([1, 2, 3], values)

        # Two optional parameters omitted, filename
        end, crop_rect, fname, frame, alt, values = parse_image_macro('(logo)', defaults=(1, 2), names=('arga', 'argb'))
        self.assertEqual(end, 6)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, 'logo')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([1, 2], values)

    def test_parse_image_macro_with_cropping_spec(self):
        # Cropping spec with all parameters omitted
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1{}', names=('a',))
        self.assertEqual(end, 3)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, '')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([1], values)

        # Cropping spec with some parameters omitted
        end, crop_rect, fname, frame, alt, values = parse_image_macro('#BAZ1{1,2}', 4, names=('a',))
        self.assertEqual(end, 10)
        self.assertEqual(crop_rect, (1, 2, None, None))
        self.assertEqual(fname, '')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([1], values)

        # Cropping spec with some parameters omitted, one named
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1{1,width=5}', names=('a',))
        self.assertEqual(end, 12)
        self.assertEqual(crop_rect, (1, 0, 5, None))
        self.assertEqual(fname, '')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([1], values)

        # Cropping spec with all parameters named
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1{width=5,height=6,x=1,y=2}', names=('a',))
        self.assertEqual(end, 27)
        self.assertEqual(crop_rect, (1, 2, 5, 6))
        self.assertEqual(fname, '')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([1], values)

    def test_parse_image_macro_with_filename(self):
        # No default filename, no filename specified
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1', names=('a',))
        self.assertEqual(end, 1)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, '')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([1], values)

        # No default filename, filename specified
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1(image)', names=('a',))
        self.assertEqual(end, 8)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, 'image')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([1], values)

        # Default filename, no filename specified
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1', names=('a',), fname='image')
        self.assertEqual(end, 1)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, 'image')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([1], values)

        # Default filename, filename specified
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1(logo)', names=('a',), fname='image')
        self.assertEqual(end, 7)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, 'logo')
        self.assertIsNone(frame)
        self.assertIsNone(alt)
        self.assertEqual([1], values)

    def test_parse_image_macro_with_frame(self):
        # Implicit frame name
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1(logo*)', names=('a',))
        self.assertEqual(end, 8)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, 'logo')
        self.assertEqual(frame, fname)
        self.assertIsNone(alt)
        self.assertEqual([1], values)

        # Explicit frame name
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1(logo*frame1)', names=('a',))
        self.assertEqual(end, 14)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, 'logo')
        self.assertEqual(frame, 'frame1')
        self.assertIsNone(alt)
        self.assertEqual([1], values)

        # Explicit frame name, no filename
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1(*frame1)', names=('a',))
        self.assertEqual(end, 10)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, '')
        self.assertEqual(frame, 'frame1')
        self.assertIsNone(alt)
        self.assertEqual([1], values)

    def test_parse_image_macro_with_alt_text(self):
        # Alt text
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1(logo|Logo)', names=('a',))
        self.assertEqual(end, 12)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, 'logo')
        self.assertIsNone(frame)
        self.assertEqual(alt, 'Logo')
        self.assertEqual([1], values)

        # Filename, implicit frame name, alt text
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1(logo*|Logo)', names=('a',))
        self.assertEqual(end, 13)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, 'logo')
        self.assertEqual(frame, fname)
        self.assertEqual(alt, 'Logo')
        self.assertEqual([1], values)

        # Filename, explicit frame name, alt text
        end, crop_rect, fname, frame, alt, values = parse_image_macro('1(logo*frame1|Logo)', names=('a',))
        self.assertEqual(end, 19)
        self.assertEqual(crop_rect, (0, 0, None, None))
        self.assertEqual(fname, 'logo')
        self.assertEqual(frame, 'frame1')
        self.assertEqual(alt, 'Logo')
        self.assertEqual([1], values)

    def test_parse_address_range(self):
        addr_specs = [
            ('1', 1, [1]),
            ('2x3', 1, [2] * 3),
            ('0-3', 1, [0, 1, 2, 3]),
            ('0-2x3', 1, [0, 1, 2] * 3),
            ('0-6-2', 1, [0, 2, 4, 6]),
            ('0-6-3x2', 1, [0, 3, 6] * 2),
            ('0-49-1-16', 2, [0, 1, 16, 17, 32, 33, 48, 49]),
            ('0-$0210-8-256x4', 3, [0, 8, 16, 256, 264, 272, 512, 520, 528] * 4),

            ('(1+3)', 1, [4]),
            ('1-(1+1)', 2, [1, 2]),
            ('1-(3-1)', 2, [1, 2]),
            ('0-16-(4*2)', 3, [0, 8, 16]),
            ('0-17-1-($08+8)', 2, [0, 1, 16, 17]),
            ('1x(7/3)', 2, [1, 1]),
            ('1x(1+$01)', 2, [1, 1])
        ]
        for spec, width, exp_addresses in addr_specs:
            end, addresses = parse_address_range(spec, 0, width)
            self.assertEqual(end, len(spec), spec)
            self.assertEqual(exp_addresses, addresses)
