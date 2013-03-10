# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit import skool2ctl, UsageError

ELEMENTS = 'btdrmsc'

USAGE = """skool2ctl.py [options] FILE

  Convert a skool file into a control file, written to standard output. FILE
  may be a regular file, or '-' for standard input.

Options:
  -w X  Write only these elements, where X is one or more of:
          b = block types and addresses
          t = block titles
          d = block descriptions
          r = registers
          m = mid-block comments and block end comments
          s = sub-block types and addresses
          c = instruction-level comments
  -h    Write addresses in hexadecimal format
  -a    Do not write ASM directives"""

TEST_SKOOL = """; Test skool file for skool2ctl testing
c32768 RET
"""

class Skool2CtlTest(SkoolKitTestCase):
    def test_no_arguments(self):
        try:
            self.run_skool2ctl()
            self.fail()
        except UsageError as e:
            self.assertEqual(e.args[0], USAGE)

    def test_invalid_arguments(self):
        for args in ('-h', '-x test.skool'):
            try:
                self.run_skool2ctl(args)
                self.fail()
            except UsageError as e:
                self.assertEqual(e.args[0], USAGE)

    def test_default_option_values(self):
        skoolfile = 'test.skool'
        infile, elements, write_hex, write_asm_dirs = skool2ctl.parse_args((skoolfile,))
        self.assertEqual(infile, skoolfile)
        self.assertEqual(elements, ELEMENTS)
        self.assertFalse(write_hex)
        self.assertTrue(write_asm_dirs)

    def test_option_w(self):
        skoolfile = 'test.skool'
        for w in ('b', 't', 'd', 'r', 'm', 's', 'c', 'btd', ELEMENTS):
            infile, elements, write_hex, write_asm_dirs = skool2ctl.parse_args(('-w', w, skoolfile))
            self.assertEqual(infile, skoolfile)
            self.assertEqual(elements, w)
            self.assertFalse(write_hex)
            self.assertTrue(write_asm_dirs)

    def test_option_h(self):
        skoolfile = 'test.skool'
        infile, elements, write_hex, write_asm_dirs = skool2ctl.parse_args(('-h', skoolfile))
        self.assertEqual(infile, skoolfile)
        self.assertEqual(elements, ELEMENTS)
        self.assertTrue(write_hex)
        self.assertTrue(write_asm_dirs)

    def test_option_a(self):
        skoolfile = 'test.skool'
        infile, elements, write_hex, write_asm_dirs = skool2ctl.parse_args(('-a', skoolfile))
        self.assertEqual(infile, skoolfile)
        self.assertEqual(elements, ELEMENTS)
        self.assertFalse(write_hex)
        self.assertFalse(write_asm_dirs)

    def test_run(self):
        skoolfile = self.write_text_file(TEST_SKOOL, suffix='.skool')
        output, error = self.run_skool2ctl(skoolfile)
        self.assertEqual(len(error), 0)
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], 'c 32768 Test skool file for skool2ctl testing')

if __name__ == '__main__':
    unittest.main()
