# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit import tap2sna, VERSION

class Tap2SnaTest(SkoolKitTestCase):
    def test_no_arguments(self):
        output, error = self.run_tap2sna(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage:'))

    def test_invalid_arguments(self):
        for args in ('--foo', '-k test.zip'):
            output, error = self.run_tap2sna(args, catch_exit=2)
            self.assertEqual(len(output), 0)
            self.assertTrue(error.startswith('usage:'))

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_tap2sna(option, err_lines=True, catch_exit=0)
            self.assertEqual(len(output), 0)
            self.assertEqual(len(error), 1)
            self.assertEqual(error[0], 'SkoolKit {}'.format(VERSION))

if __name__ == '__main__':
    unittest.main()
