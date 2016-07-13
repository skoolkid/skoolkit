# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.numberutils import get_number

TEST_NUMBERS = (
    # kwargs, result
    ({'snapshot': [0, 0, 210, 4, 0], 'i': 0},   1234), # Positive integer
    ({'snapshot': [0, 255, 207, 43, 0], 'i': 0}, -54321), # Negative integer
    ({'snapshot': [0, 127, 53, 179, 0], 'i': 0},  19659), # Positive integer, non-conforming sign byte
    ({'snapshot': [0, 128, 53, 179, 0], 'i': 0}, -45877), # Negative integer, non-conforming sign byte
    ({'snapshot': [0, 0, 0, 1, 1, 0], 'i': 1}, 257), # Positive integer, offset 1
)

class NumberUtilsTest(SkoolKitTestCase):
    def setUp(self):
        SkoolKitTestCase.setUp(self)
        self.longMessage = True

    def _test_function(self, exp_result, func, **kwargs):
        kwargs_str = ', '.join(['{}={!r}'.format(k, v) for k, v in kwargs.items()])
        if kwargs_str:
            kwargs_str = ', ' + kwargs_str
        msg = "{}({}) failed".format(func.__name__, kwargs_str)
        self.assertEqual(exp_result, func(**kwargs), msg)

    def test_get_number(self):
        for kwargs, exp_result in TEST_NUMBERS:
            self._test_function(exp_result, get_number, **kwargs)

if __name__ == '__main__':
    unittest.main()
