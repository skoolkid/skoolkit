# -*- coding: utf-8 -*-
import re
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.skoolmacro import parse_ints, parse_params, MacroParsingError

class SkoolMacroTest(SkoolKitTestCase):
    def test_parse_ints(self):
        # Test with the exact number of parameters
        text = '1,$2,3'
        end, p1, p2, p3 = parse_ints(text, 0, 3)
        self.assertEqual((p1, p2, p3), (1, 2, 3))
        self.assertEqual(end, len(text))

        # Test with default parameter values
        text = '$1,2,3'
        end, p1, p2, p3, p4, p5 = parse_ints(text, 0, 5, (4, 5))
        self.assertEqual((p1, p2, p3, p4, p5), (1, 2, 3, 4, 5))
        self.assertEqual(end, len(text))

        # Test with more than enough parameters
        text = '1,2,3'
        end, p1, p2 = parse_ints(text, 0, 2)
        self.assertEqual((p1, p2), (1, 2))
        self.assertEqual(end, 3)

        # Test with not enough parameters
        with self.assertRaisesRegexp(MacroParsingError, "Not enough parameters \(expected 4\): '1,2,\$3'"):
            parse_ints('1,2,$3', 0, 4)

        # Test with blank parameters
        text = '1,,$a,'
        end, p1, p2, p3, p4 = parse_ints(text, 0, 4)
        self.assertEqual((p1, p2, p3, p4), (1, None, 10, None))
        self.assertEqual(end, len(text))

        # Test with an empty parameter string
        end, p1 = parse_ints('', 0, 1, (1,))
        self.assertEqual(p1, 1)
        self.assertEqual(end, 0)

        # Test with adjacent non-numeric characters
        junk = 'xyz'
        text = '1,2{0}'.format(junk)
        end, p1, p2 = parse_ints(text, 0, 2)
        self.assertEqual((p1, p2), (1, 2))
        self.assertEqual(end, len(text) - len(junk))

        # Test with an invalid parameter
        with self.assertRaisesRegexp(MacroParsingError, re.escape("Cannot parse integer '3$0' in parameter string: '1,3$0'")):
            parse_ints('1,3$0', 0, 2)

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

if __name__ == '__main__':
    unittest.main()
