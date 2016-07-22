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
            28, 0,                   # Length, 
            1,                       # 1 dimension
            5, 0,                    # Dimension 1, length 5
            0, 0, 1, 0, 0,           # s(1) = 1
            0, 0, 5, 0, 0,           # s(2) = 5
            0, 255, 252, 255, 0,     # s(3) = -4
            0, 0, 0, 5, 0,           # s(4) = 1280
            0, 255, 0, 5, 0,         # s(5) = -64256
            145,                     # Number array variable name "q"
            35, 0,                   # Length
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
            '(Number array) s(5)=[1,5,-4,1280,-64256]',
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
            7, 0,  # Length
            1,     # 1 dimension
            4, 0,  # Dimension 1, length 4
            97,    # d$(1) = "a"
            98,    # d$(2) = "b"
            120,   # d$(3) = "x"
            122,   # d$(4) = "z"
            199,   # Character array variable of name "g$"
            11, 0, # Length
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

    def test_numbers_short_name(self):
        variables = [
            112,              # Number variable of name "p"
            0, 0, 12, 0, 0,   # 12
            116,              # Number variable of name "t"
            0, 0, 64, 0, 0,   # 64
            128               # End of variables area
        ]
        exp_output = [
            '(Number) p=12',
            '(Number) t=64',
        ]
        self._test_variables(variables, exp_output)

    def test_basic_lines_skipped(self):
        variables = [
            0, 10, 12, 0,                    # Line 10, length
            245, 49, 50, 51, 52,             # PRINT 1234
            14, 0, 0, 210, 4, 0,             # 1234
            13,                              # ENTER
            39, 15, 13, 0,                   # Line 9999, length
            245, 45, 49, 50, 51, 52,         # PRINT -1234
            14, 0, 0, 210, 4, 0,             # 1234
            13,                              # ENTER
            128                              # End of variables area
        ]
        exp_output = ['']
        self._test_variables(variables, exp_output)

    def test_mixed_variables(self):
        variables = [
            65, 4, 0, 97, 115, 100, 102,                 # a$="asdf"
            130, 35, 0, 2, 2, 0, 3, 0,                   # dim b(2,3)
            0, 0, 1, 0, 0,                               # b(1,1)=1
            0, 255, 255, 255, 0,                         # b(1,2)=-1
            0, 0, 64, 0, 0,                              # b(1,3)=64
            0, 0, 128, 0, 0,                             # b(2,1)=128
            0, 0, 16, 0, 0,                              # b(2,2)=16
            0, 0, 32, 0, 0,                              # b(2,3)=32
            172,111,110,103,111,110,229,                 # longone=255
            0, 0, 255, 0, 0,                             #
            195, 8, 0, 1, 5, 0,                          # dim c$(5)
            119,                                         # c$(1)="w"
            119,                                         # c$(2)="w"
            119,                                         # c$(3)="w"
            119,                                         # c$(4)="w"
            119,                                         # c$(5)="w"
            228,                                         # FOR control variable of name "d"
            0, 0, 1, 0, 0,                               # 1
            0, 0, 8, 0, 0,                               # limit = 8
            0, 0, 1, 0, 0,                               # step = 1
            4, 0,                                        # line = 4
            7,                                           # statement = 7
            101, 0, 0, 250, 255, 0,                      # e=65530
            0, 12, 3, 0, 243, 105, 13,                   # 12 NEXT i
            39, 7, 6, 0, 234, 116, 101, 115, 116, 13,    # 9991 REM test
            70, 5, 0, 122, 120, 99, 118, 98,             # f$="zxcvb"
            135, 33, 0, 1, 6, 0,                         # dim g(6)
            0, 0, 12, 0, 0,                              # g(1)=12
            0, 0, 13, 0, 0,                              # g(2)=13
            0, 0, 14, 0, 0,                              # g(3)=14
            0, 0, 15, 0, 0,                              # g(4)=15
            0, 0, 16, 0, 0,                              # g(5)=16
            0, 0, 17, 0, 0,                              # g(6)=17
            172, 111, 110, 103, 101, 114, 111, 110, 229, # longerone=-63741
            0, 255, 3, 7, 0,                             #
            200, 11, 0, 2, 3, 0, 2, 0,                   # dim h$(3,2)
            97,                                          # h$(1,1)="a"
            122,                                         # h$(1,2)="z"
            98,                                          # h$(2,1)="b"
            121,                                         # h$(2,2)="y"
            99,                                          # h$(3,1)="c"
            120,                                         # h$(3,2)="x"
            233,                                         # FOR control variable of name "i"
            0, 0, 0, 1, 0,                               # 256
            0, 0, 0, 2, 0,                               # limit = 512
            0, 0, 0, 1, 0,                               # step = 256
            17, 0,                                       # line = 17
            1,                                           # statement = 1
            106, 0, 0, 36, 0, 0,                         # j=36
            0, 10, 3, 0, 245, 112, 13,                   # 10 PRINT p
            39, 15, 2, 0, 230, 13,                       # 9999 NEW
            128                                          # End of variables area
        ]
        exp_output = [
            '(String) a$="asdf"',
            '(Number array) b(2,3)=[1,-1,64,128,16,32]',
            '(Number) longone=255',
            '(Character array) c$(5)=["w","w","w","w","w"]',
            '(FOR control variable) d=1 (limit=8, step=1, line=4, statement=7)',
            '(Number) e=65530',
            '(String) f$="zxcvb"',
            '(Number array) g(6)=[12,13,14,15,16,17]',
            '(Number) longerone=-63741',
            '(Character array) h$(3,2)=["a","z","b","y","c","x"]',
            '(FOR control variable) i=256 (limit=512, step=256, line=17, statement=1)',
            '(Number) j=36',
        ]
        self._test_variables(variables, exp_output)

if __name__ == '__main__':
    unittest.main()
