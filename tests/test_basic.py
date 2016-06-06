# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.basic import BasicLister

class BasicListerTest(SkoolKitTestCase):
    def _test_basic(self, data, exp_output):
        snapshot = [0] * 23755 + data
        basic = BasicLister().list_basic(snapshot)
        self.assertEqual(exp_output, basic.split('\n'))

    def test_integers(self):
        basic = [
            0, 10, 12, 0,                    # Line 10, length
            245, 49, 50, 51, 52,             # PRINT 1234
            14, 0, 0, 210, 4, 0,             # 1234
            13,                              # ENTER
            0, 20, 13, 0,                    # Line 20, length
            245, 45, 49, 50, 51, 52,         # PRINT -1234
            14, 0, 0, 210, 4, 0,             # 1234
            13,                              # ENTER
            0, 30, 14, 0,                    # Line 30, length
            245, 49, 50, 51, 52, 53, 54,     # PRINT 123456
            14, 145, 113, 32, 0, 0,          # 123456
            13,                              # ENTER
            0, 40, 15, 0,                    # Line 40, length
            245, 45, 49, 50, 51, 52, 53, 54, # PRINT -123456
            14, 145, 113, 32, 0, 0,          # 123456
            13,                              # ENTER
            128                              # End of BASIC area
        ]
        exp_output = [
            '  10 PRINT 1234',
            '  20 PRINT -1234',
            '  30 PRINT 123456',
            '  40 PRINT -123456'
        ]
        self._test_basic(basic, exp_output)

    def test_floating_point_numbers(self):
        basic = [
            0, 10, 11, 0,               # Line 10, length
            245, 49, 46, 51,            # PRINT 1.3
            14, 129, 38, 102, 102, 102, # 1.3 in floating point form
            13,                         # ENTER
            0, 20, 13, 0,               # Line 20, length
            245, 49, 48, 101, 50, 48,   # PRINT 10e20
            14, 198, 88, 215, 38, 183,  # 10e20 in floating point form
            13,                         # ENTER
            0, 30, 12, 0,               # Line 30, length
            245, 55, 101, 45, 56,       # PRINT 7e-8
            14, 105, 22, 82, 232, 47,   # 7e-8 in floating point form
            13,                         # ENTER
            0, 40, 12, 0,               # Line 40, length
            245, 45, 53, 46, 55,        # PRINT -5.7
            14, 131, 54, 102, 102, 102, # 5.7 in floating point form (sign is
                                        # not stored here)
            13,                         # ENTER
            128                         # End of BASIC area
        ]
        exp_output = [
            '  10 PRINT 1.3',
            '  20 PRINT 10e20',
            '  30 PRINT 7e-8',
            '  40 PRINT -5.7'
        ]
        self._test_basic(basic, exp_output)

    def test_fake_floating_point_number(self):
        basic = [
            0, 10, 11, 0,         # Line 10, length
            245, 49, 50, 51,      # PRINT 123
            14, 129, 64, 0, 0, 0, # 1.5 in floating point form
            13,                   # ENTER
            128                   # End of BASIC area
        ]
        exp_output = ['  10 PRINT 123{1.5}']
        self._test_basic(basic, exp_output)

    def test_non_ascii_characters(self):
        basic = [
            0, 10, 7, 0,              # Line 10, length
            245, 34, 94, 96, 127, 34, # PRINT "↑£©"
            13,                       # ENTER
            128                       # End of BASIC area
        ]
        exp_output = ['  10 PRINT "↑£©"']
        self._test_basic(basic, exp_output)

    def test_undefined_character_codes(self):
        basic = [
            0, 10, 6, 0,       # Line 10, length
            234, 0, 1, 30, 31, # REM ????
            13,                # ENTER
            128                # End of BASIC area
        ]
        exp_output = ['  10 REM {0x00}{0x01}{0x1E}{0x1F}']
        self._test_basic(basic, exp_output)

if __name__ == '__main__':
    unittest.main()
