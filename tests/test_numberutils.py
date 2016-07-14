# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.numberutils import get_number

TEST_NUMBERS_INTEGER = (
    # kwargs, result
    ({'snapshot': [0, 0, 210, 4, 0], 'i': 0},   1234),    # Positive integer
    ({'snapshot': [0, 0, 100, 0, 0], 'i': 0},   100),     # Positive integer, LSB only
    ({'snapshot': [0, 0, 0, 27, 0], 'i': 0},   6912),     # Positive integer, MSB only
    ({'snapshot': [0, 255, 207, 43, 0], 'i': 0}, -54321), # Negative integer
    ({'snapshot': [0, 255, 12, 0, 0], 'i': 0}, -65524),   # Negative integer, LSB only
    ({'snapshot': [0, 255, 0, 62, 0], 'i': 0}, -49664),   # Negative integer, MSB only
    ({'snapshot': [0, 127, 53, 179, 0], 'i': 0},  19659), # Positive integer, non-conforming sign byte
    ({'snapshot': [0, 128, 53, 179, 0], 'i': 0}, -45877), # Negative integer, non-conforming sign byte
    ({'snapshot': [0, 0, 0, 1, 1, 0], 'i': 1}, 257),      # Positive integer, offset 1
)

TEST_NUMBERS_FLOAT = (
    # kwargs, result
    ({'snapshot': [134, 111, 255, 255, 255], 'i': 0}, 0.6e2),        # Positive mantissa, small positive exponent
    ({'snapshot': [251, 45, 85, 109, 9], 'i': 0}, 0.72e37),          # Positive mantissa, large positive exponent
    ({'snapshot': [121, 45, 171, 159, 85], 'i': 0}, 0.53e-2),        # Positive mantissa, small negative exponent
    ({'snapshot': [2, 65, 211, 40, 119], 'i': 0}, 0.89e-38),         # Positive mantissa, large negative exponent
    ({'snapshot': [135, 182, 0, 0, 0], 'i': 0}, -0.91e2),            # Negative mantissa, small positive exponent
    ({'snapshot': [251, 182, 246, 157, 194], 'i': 0}, -0.76e37),     # Negative mantissa, large positive exponent
    ({'snapshot': [121, 209, 183, 23, 88], 'i': 0}, -0.64e-2),       # Negative mantissa, small negative exponent
    ({'snapshot': [2, 182, 239, 144, 158], 'i': 0}, -0.84e-38),      # Negative mantissa, large negative exponent
    ({'snapshot': [168, 5, 142, 188, 109], 'i': 0}, 0.573625364e12), # Long mantissa
)

class NumberUtilsTest(SkoolKitTestCase):
    def setUp(self):
        SkoolKitTestCase.setUp(self)
        self.longMessage = True

    def _test_function_integer(self, exp_result, func, **kwargs):
        kwargs_str = ', '.join(['{}={!r}'.format(k, v) for k, v in kwargs.items()])
        msg = "{}({}) failed".format(func.__name__, kwargs_str)
        self.assertEqual(exp_result, func(**kwargs), msg)

    def _test_function_float(self, exp_result, func, **kwargs):
        kwargs_str = ', '.join(['{}={!r}'.format(k, v) for k, v in kwargs.items()])
        msg = "{}({}) = {} failed".format(func.__name__, kwargs_str, exp_result)
        self.assertTrue(abs(1 - exp_result / func(**kwargs)) <= 1e-9, msg)

    def test_get_number_integer(self):
        for kwargs, exp_result in TEST_NUMBERS_INTEGER:
            self._test_function_integer(exp_result, get_number, **kwargs)

    def test_get_number_float(self):
        for kwargs, exp_result in TEST_NUMBERS_FLOAT:
            self._test_function_float(exp_result, get_number, **kwargs)

if __name__ == '__main__':
    unittest.main()
