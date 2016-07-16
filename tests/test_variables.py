# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.variables import VariableLister

class VariableListerTest(SkoolKitTestCase):
    def _test_variables(self, data, exp_output):
        snapshot = [0] * 23755 + data
        variables = VariableLister().list_variables(snapshot)
        self.assertEqual(exp_output, variables.split('\n'))

    def test_strings(self):
        variables = [
            67,                         # String variable of name "c$"
            7, 0,                       # 7 characters long
            97, 98, 99, 32, 49, 50, 51, # "abc 123"
            68,                         # String variable of name "d$"
            1, 0,                       # 1 character long
            166,                        # "INKEY$" (token with no space)
            70,                         # String variable of name "f$"
            1, 0,                       # 1 character long
            168,                        # "FN " (token with trailing space)
            90,                         # String variable of name "k$"
            1, 0,                       # 1 character long
            197,                        # "OR" (token with leading and trailing spaces)
            128                         # End of variables area
        ]
        exp_output = [
            '(String) c$="abc 123"',
            '(String) d$="INKEY$"',
            '(String) f$="FN "',
            '(String) z$=" OR "',
        ]
        self._test_variables(variables, exp_output)

    def test_number_arrays(self):
        variables = [
            147,                     # Number array variable of name "s"
            28, 0,                   # ?????Length?????, 
            1,                       # 1 dimension
            5, 0,                    # Dimension 1, length 5?????
            0, 0, 1, 0, 0,           # s(1) = 1
            0, 0, 5, 0, 0,           # s(2) = 5
            0, 255, 252, 255, 0,     # s(3) = -4
            130, 102, 102, 102, 102, # s(4) = 3.6
            168, 162, 251, 64, 88,   # s(5) = -0.7e12
            145,                     # Number array variable name "q"
            35, 0,                   # ?????Length?????
            2,                       # 2 dimensions
            2, 0,                    # Dimension 1 length
            3, 0,                    # Dimension 2 length
            0, 0, 11, 0, 0,          # q(1,1) = 11
            0, 0, 21, 0, 0,          # q(1,2) = 21
            0, 0, 31, 0, 0,          # q(1,3) = 31
            0, 0, 12, 0, 0,          # q(2,1) = 12
            0, 0, 22, 0, 0,          # q(2,2) = 22
            0, 0, 32, 0, 0,          # q(2,3) = 32
            128                      # End of variables area
        ]
        exp_output = [
            '(Number array) s(5)=[1,5,-4,3.59999999963,-7e+11]',
            '(Number array) q(2,3)=[11,21,31,12,22,32]',
        ]
        self._test_variables(variables, exp_output)

if __name__ == '__main__':
    unittest.main()
