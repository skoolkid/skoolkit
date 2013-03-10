# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.skoolmacro import parse_ints, MacroParsingError

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
        text = '1,2,$3'
        try:
            parse_ints(text, 0, 4)
        except MacroParsingError as e:
            self.assertEqual(e.args[0], "Not enough parameters (expected 4): '{0}'".format(text))
        else:
            self.fail()

        # Test with blank parameters
        text = '1,,$a,'
        end, p1, p2, p3, p4 = parse_ints(text, 0, 4)
        self.assertEqual((p1, p2, p3, p4), (1, None, 10, None))
        self.assertEqual(end, len(text))

        # Test with an empty parameter string
        end, p1 = parse_ints('', 0, 1)
        self.assertEqual(p1, None)
        self.assertEqual(end, 0)

        # Test with adjacent non-numeric characters
        junk = 'xyz'
        text = '1,2{0}'.format(junk)
        end, p1, p2 = parse_ints(text, 0, 2)
        self.assertEqual((p1, p2), (1, 2))
        self.assertEqual(end, len(text) - len(junk))

        # Test with an invalid parameter
        invalid_param = '3$0'
        text = '1,{0}'.format(invalid_param)
        try:
            parse_ints(text, 0, 2)
        except MacroParsingError as e:
            self.assertEqual(e.args[0], "Cannot parse integer '{0}' in macro parameter list: '{1}'".format(invalid_param, text))
        else:
            self.fail()

if __name__ == '__main__':
    unittest.main()
