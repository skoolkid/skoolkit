# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError, scr2img, VERSION

class Scr2ImgTest(SkoolKitTestCase):
    def test_no_arguments(self):
        output, error = self.run_scr2img(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: scr2img.py'))

    def test_invalid_option(self):
        output, error = self.run_scr2img('-x test.z80', catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: scr2img.py'))

    def test_unrecognised_snapshot_type(self):
        with self.assertRaisesRegexp(SkoolKitError, 'Unrecognised input file type$'):
            self.run_scr2img('unknown.snap')

    def test_nonexistent_input_file(self):
        infile = 'non-existent.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_scr2img(infile)
        self.assertEqual(cm.exception.args[0], '{}: file not found'.format(infile))

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_scr2img(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

if __name__ == '__main__':
    unittest.main()
