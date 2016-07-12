# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.numberutils import get_number

TEST_NUMBERS = (
    # kwargs, result
    ({'snapshot': [0, 0, 210, 4, 0], 'i': 0}, 1234), # Positive integer
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
