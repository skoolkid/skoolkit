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
            5, 0,                    # Dimension 1, length 5
            0, 0, 1, 0, 0,           # s(1) = 1
            0, 0, 5, 0, 0,           # s(2) = 5
            0, 255, 252, 255, 0,     # s(3) = -4
            130, 102, 102, 102, 102, # s(4) = 3.6
            168, 162, 251, 64, 88,   # s(5) = -0.7e12
            145,                     # Number array variable name "q"
            35, 0,                   # ?????Length?????
            2,                       # 2 dimensions
            2, 0,                    # Dimension 1, length 2
            3, 0,                    # Dimension 2, length 3
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

    def test_numbers_long_name(self):
        variables = [
            174, 117, 237,       # Number variable of name "num"
            0, 0, 25, 2, 0,      # 537
            184, 121, 250,       # Number variable of name "xyz"
            0, 255, 179, 231, 0, # -6221
            128                  # End of variables area
        ]
        exp_output = [
            '(Number) num=537',
            '(Number) xyz=-6221',
        ]
        self._test_variables(variables, exp_output)

    def test_character_arrays(self):
        variables = [
            196,   # Character array variable of name "d$"
            7, 0,  # ?????Length?????
            1,     # 1 dimension
            4, 0,  # Dimension 1, length 4
            97,    # d$(1) = "a"
            98,    # d$(2) = "b"
            120,   # d$(3) = "x"
            122,   # d$(4) = "z"
            199,   # Character array variable of name "g$"
            11, 0, # ?????Length?????
            2,     # 2 dimensions
            2, 0,  # Dimension 1, length 2
            3, 0,  # Dimension 2, length 3
            49,    # g(1,1) = "1"
            50,    # g(1,2) = "2"
            51,    # g(1,3) = "3"
            79,    # g(2,1) = "O"
            84,    # g(2,2) = "T"
            90,    # g(2,3) = "Z"
            128    # End of variables area
        ]
        exp_output = [
            '(Character array) d$(4)=["a","b","x","z"]',
            '(Character array) g$(2,3)=["1","2","3","O","T","Z"]',
        ]
        self._test_variables(variables, exp_output)

    def test_control_vars(self):
        variables = [
            240,                 # FOR control variable of name "p"
            0, 0, 3, 0, 0,       # 3
            0, 0, 7, 0, 0,       # limit = 7
            0, 0, 2, 0, 0,       # step = 2
            12, 0,               # line = 12
            4,                   # statement = 4
            244,                 # FOR control variable of name "t"
            0, 255, 251, 255, 0, # -5
            0, 255, 246, 255, 0, # limit = -10
            0, 255, 251, 255, 0, # step = -5
            95, 8,               # line = 2143
            2,                   # statement = 2
            128                  # End of variables area
        ]
        exp_output = [
            '(FOR control variable) p=3 (limit=7, step=2, line=12, statement=4)',
            '(FOR control variable) t=-5 (limit=-10, step=-5, line=2143, statement=2)',
        ]
        self._test_variables(variables, exp_output)

if __name__ == '__main__':
    unittest.main()
