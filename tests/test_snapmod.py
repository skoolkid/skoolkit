# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError, VERSION

class SnapmodTest(SkoolKitTestCase):
    def test_no_arguments(self):
        output, error = self.run_snapmod(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: snapmod.py'))

    def test_invalid_option(self):
        output, error = self.run_snapmod('-x test.z80', catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: snapmod.py'))

    def test_unrecognised_snapshot_type(self):
        with self.assertRaisesRegexp(SkoolKitError, 'Unrecognised input snapshot type$'):
            self.run_snapmod('unknown.snap')

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_snapmod(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

if __name__ == '__main__':
    unittest.main()
