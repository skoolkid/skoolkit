# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit import skool2sft, VERSION

def mock_run(*args):
    global run_args
    run_args = args

class Skool2SftTest(SkoolKitTestCase):
    def test_no_arguments(self):
        output, error = self.run_skool2sft(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: skool2sft.py'))

    def test_invalid_arguments(self):
        for args in ('-h', '-x test.skool'):
            output, error = self.run_skool2sft(args, catch_exit=2)
            self.assertEqual(len(output), 0)
            self.assertTrue(error.startswith('usage: skool2sft.py'))

    def test_default_option_values(self):
        self.mock(skool2sft, 'run', mock_run)
        skoolfile = 'test.skool'
        skool2sft.main((skoolfile,))
        infile, write_hex = run_args
        self.assertEqual(infile, skoolfile)
        self.assertFalse(write_hex)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_skool2sft(option, err_lines=True, catch_exit=0)
            self.assertEqual(len(output), 0)
            self.assertEqual(len(error), 1)
            self.assertEqual(error[0], 'SkoolKit {}'.format(VERSION))

    def test_option_h(self):
        self.mock(skool2sft, 'run', mock_run)
        skoolfile = 'test.skool'
        for option in ('-h', '--hex'):
            skool2sft.main((option, skoolfile))
            infile, write_hex = run_args
            self.assertEqual(infile, skoolfile)
            self.assertTrue(write_hex)

    def test_run(self):
        skool = '; Routine\nc32768 RET'
        skoolfile = self.write_text_file(skool, suffix='.skool')
        output, error = self.run_skool2sft(skoolfile)
        self.assertEqual(len(error), 0)
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0], '; Routine')
        self.assertEqual(output[1], 'cC32768,1')

if __name__ == '__main__':
    unittest.main()
