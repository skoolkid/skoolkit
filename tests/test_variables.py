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

if __name__ == '__main__':
    unittest.main()
