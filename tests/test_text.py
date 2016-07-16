# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.text import TextReader

TEST_CODES_32_AND_BELOW = (
    # args, result
    (([0]), '{0x00}'),  # 0x00
    (([12]), '{0x0C}'), # 0x0C
    (([32]), ' '),      # ' '
)

TEST_CODES_33_TO_164 = (
    # args, result
    (([33]), '!'),       # '!'
    (([94]), '↑'),       # '↑'
    (([96]), '£'),       # '£'
    (([126]), '~'),      # '~'
    (([127]), '©'),      # '©'
    (([128]), '{0x80}'), # 0x80
    (([164]), '{0xA4}'), # 0xA4
)

TEST_TOKENS = (
    # args, lspace, result
    (([165]), False, 'RND'),  # 'RND' with leading space FALSE
    (([165]), True, 'RND'),   # 'RND' with leading space TRUE
    (([197]), False, 'OR '),  # 'OR' with leading space FALSE
    (([197]), True, ' OR '),  # 'OR' with leading space TRUE
    (([199]), False, '<='),   # '<=' with leading space FALSE
    (([199]), True, '<='),    # '<=' with leading space TRUE
    (([203]), False, 'THEN'), # 'THEN' with leading space FALSE
    (([203]), True, ' THEN'), # 'THEN' with leading space TRUE
)

TEST_MULTIPLE_CALLS = (
    # args, lspace, result
    ([31, 202], '{0x1F}LINE '),    # Character that turns lspace off and token with leading space
    ([33, 202], '! LINE '),        # Character that turns lspace on and token with leading space
    ([31, 196], '{0x1F}BIN '),     # Character that turns lspace off and token without leading space
    ([33, 196], '!BIN '),          # Character that turns lspace on and token without leading space
    ([170, 202], 'SCREEN$ LINE '), # Token that turns lspace off and token with leading space
    ([166, 202], 'INKEY$ LINE '),  # Token that turns lspace on and token with leading space
    ([170, 196], 'SCREEN$ BIN '),  # Token that turns lspace off and token without leading space
    ([166, 196], 'INKEY$BIN '),    # Token that turns lspace on and token without leading space
)

class TextReaderTest(SkoolKitTestCase):
    def setUp(self):
        self.text = TextReader()
        SkoolKitTestCase.setUp(self)
        self.longMessage = True

    def _test_get_chars_single(self, exp_result, *args):
        args_str = ', '.join([repr(a) for a in args])
        msg = "get_chars ({}) failed".format(args_str)
        self.assertEqual(exp_result, self.text.get_chars(*args), msg)

    def _test_get_chars_single_tokens(self, lspace, exp_result, *args):
        args_str = ', '.join([repr(a) for a in args])
        msg = "get_chars ({}) with lspace {} failed".format(args_str, lspace)
        self.text.lspace = lspace
        self.assertEqual(exp_result, self.text.get_chars(*args), msg)

    def _test_get_chars_multiple(self, exp_result, charlist):
        actual = ''
        for code in charlist:
            actual = actual + self.text.get_chars(code)
        codes_str = ', '.join([repr(code) for code in charlist])
        msg = "get_chars with [{}] failed".format(codes_str)
        self.assertEqual(exp_result, actual, msg)

    def test_codes_32_and_below(self):
        for args, exp_result in TEST_CODES_32_AND_BELOW:
            self._test_get_chars_single(exp_result, *args)

    def test_codes_33_to_164(self):
        for args, exp_result in TEST_CODES_33_TO_164:
            self._test_get_chars_single(exp_result, *args)

    def test_tokens(self):
        for args, lspace, exp_result in TEST_TOKENS:
            self._test_get_chars_single_tokens(lspace, exp_result, *args)

    def test_multiple_calls(self):
        for charlist, exp_result in TEST_MULTIPLE_CALLS:
            self._test_get_chars_multiple(exp_result, charlist)

if __name__ == '__main__':
    unittest.main()
