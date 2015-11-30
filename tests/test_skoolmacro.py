# -*- coding: utf-8 -*-
import re
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.skoolmacro import (parse_ints, parse_strings, parse_params, parse_address_range,
                                 MacroParsingError, NoParametersError, MissingParameterError, TooManyParametersError)

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
        end, p1, p2, p3, p4 = parse_ints(text, 0, 4)
        self.assertEqual((1, None, 10, None), (p1, p2, p3, p4))
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
        with self.assertRaisesRegexp(MacroParsingError, re.escape("Not enough parameters (expected 4): '1,2,$3'")):
            parse_ints('1,2,$3', num=4)

    def test_parse_ints_with_kwargs_not_enough_parameters(self):
        with self.assertRaisesRegexp(MacroParsingError, "Missing required argument 'a'"):
            parse_ints('b=4,c=5', defaults=(2, 3), names=('a', 'b', 'c'))

    def test_parse_ints_non_kwarg_after_kwarg(self):
        with self.assertRaisesRegexp(MacroParsingError, "Non-keyword argument after keyword argument: '3'"):
            parse_ints('1,bar=2,3', names=('foo', 'bar', 'baz'))

    def test_parse_ints_unknown_kwarg(self):
        with self.assertRaisesRegexp(MacroParsingError, "Unknown keyword argument: 'qux=2'"):
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

        with self.assertRaisesRegexp(NoParametersError, msg):
            parse_strings('')

        with self.assertRaisesRegexp(NoParametersError, msg):
            parse_strings(' (')

        with self.assertRaisesRegexp(NoParametersError, msg):
            parse_strings('\t{')

    def test_parse_strings_no_terminating_delimiter(self):
        text = '(foo'
        with self.assertRaisesRegexp(MacroParsingError, re.escape("No closing bracket: {}".format(text))):
            parse_strings(text)

        text = '{foo)'
        with self.assertRaisesRegexp(MacroParsingError, re.escape("No closing bracket: {}".format(text))):
            parse_strings(text)

        text = '[foo}'
        with self.assertRaisesRegexp(MacroParsingError, re.escape("No closing bracket: {}".format(text))):
            parse_strings(text)

        text = '/foo,bar/'
        with self.assertRaisesRegexp(MacroParsingError, "No terminating delimiter: {}".format(text)):
            parse_strings(text)

        text = '//foo/bar/'
        with self.assertRaisesRegexp(MacroParsingError, "No terminating delimiter: {}".format(text)):
            parse_strings(text)

    def test_parse_strings_too_many_parameters(self):
        text = '(foo,bar,baz)'
        with self.assertRaises(TooManyParametersError) as e:
            parse_strings(text, num=2)
            self.assertEqual(e[0], "Too many parameters (expected 2): '{}'".format(text[1:-1]))
            self.assertEqual(e[1], len(text))

    def test_parse_strings_missing_parameters(self):
        text = '(foo,bar)'
        with self.assertRaises(MissingParameterError) as e:
            parse_strings(text, num=3)
            self.assertEqual(e[0], "Not enough parameters (expected 3): '{}'".format(text[1:-1]))
            self.assertEqual(e[1], len(text))

        text = '{foo,bar}'
        with self.assertRaises(MissingParameterError) as e:
            parse_strings(text, num=5, defaults=('qux',))
            self.assertEqual(e[0], "Not enough parameters (expected 4): '{}'".format(text[1:-1]))
            self.assertEqual(e[1], len(text))

    def test_parse_params_default_valid_characters(self):
        text = '$5B'
        result = parse_params(text, 0)
        self.assertEqual(result, (len(text), '$5B', None))

        text = '$5B[foo]'
        result = parse_params(text, 0, 'qux')
        self.assertEqual(result, (text.index('['), '$5B', 'qux'))

        text = '1234(foo)'
        result = parse_params(text, 0, 'qux')
        self.assertEqual(result, (len(text), '1234', 'foo'))

        text = '#foo(bar)'
        result = parse_params(text, 0)
        self.assertEqual(result, (len(text), '#foo', 'bar'))

        text = '1,2,3,4(foo)'
        result = parse_params(text, 0)
        self.assertEqual(result, (1, '1', None))

    def test_parse_params_extra_valid_characters(self):
        text = '$5A,2'
        result = parse_params(text, 0, chars=',')
        self.assertEqual(result, (len(text), '$5A,2', None))

        text = '$5A,2.'
        result = parse_params(text, 0, 'xyzzy', chars=',',)
        self.assertEqual(result, (text.index('.'), '$5A,2', 'xyzzy'))

        text = '1;2#blah(hey)'
        result = parse_params(text, 0, 'xyzzy', chars=';',)
        self.assertEqual(result, (len(text), '1;2#blah', 'hey'))

    def test_parse_params_except_chars(self):
        text = '*foo,3;bar,$4:baz*'
        result = parse_params(text, 0, except_chars=' (')
        self.assertEqual(result, (len(text), '*foo,3;bar,$4:baz*', None))

        text = '*foo,3;bar,$4:baz* etc.'
        result = parse_params(text, 0, 'qux', except_chars=' (')
        self.assertEqual(result, (text.index(' '), '*foo,3;bar,$4:baz*', 'qux'))

        text = '*foo,3;bar,$4:baz*(qux)'
        result = parse_params(text, 0, except_chars=' (')
        self.assertEqual(result, (len(text), '*foo,3;bar,$4:baz*', 'qux'))

        text = '*foo,3(bar,$4){baz}* etc.'
        result = parse_params(text, 0, except_chars=' ')
        self.assertEqual(result, (text.index(' '), '*foo,3(bar,$4){baz}*', None))

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

if __name__ == '__main__':
    unittest.main()
