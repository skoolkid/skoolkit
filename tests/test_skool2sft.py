# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit import skool2sft, UsageError

USAGE = """skool2sft.py [options] FILE

  Convert a skool file into a skool file template, written to standard output.
  FILE may be a regular file, or '-' for standard input.

Options:
  -h  Write addresses in hexadecimal format"""

TEST_SKOOL = """; Routine
c32768 RET
"""

class Skool2SftTest(SkoolKitTestCase):
    def test_no_arguments(self):
        try:
            self.run_skool2sft()
            self.fail()
        except UsageError as e:
            self.assertEqual(e.args[0], USAGE)

    def test_invalid_arguments(self):
        for args in ('-h', '-x test.skool'):
            try:
                self.run_skool2sft(args)
                self.fail()
            except UsageError as e:
                self.assertEqual(e.args[0], USAGE)

    def test_default_option_values(self):
        skoolfile = 'test.skool'
        infile, write_hex = skool2sft.parse_args((skoolfile,))
        self.assertEqual(infile, skoolfile)
        self.assertFalse(write_hex)

    def test_option_h(self):
        skoolfile = 'test.skool'
        infile, write_hex = skool2sft.parse_args(('-h', skoolfile))
        self.assertEqual(infile, skoolfile)
        self.assertTrue(write_hex)

    def test_run(self):
        skoolfile = self.write_text_file(TEST_SKOOL, suffix='.skool')
        output, error = self.run_skool2sft(skoolfile)
        self.assertEqual(len(error), 0)
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0], '; Routine')
        self.assertEqual(output[1], 'cC32768,1')

if __name__ == '__main__':
    unittest.main()
