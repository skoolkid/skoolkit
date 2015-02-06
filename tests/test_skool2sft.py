# -*- coding: utf-8 -*-
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import skool2sft, VERSION

class MockSftWriter:
    def __init__(self, *args):
        global mock_sft_writer
        self.args = args
        self.write_called = False
        mock_sft_writer = self

    def write(self):
        self.write_called = True

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

    @patch.object(skool2sft, 'SftWriter', MockSftWriter)
    def test_default_option_values(self):
        skoolfile = 'test.skool'
        skool2sft.main((skoolfile,))
        infile, write_hex, preserve_base = mock_sft_writer.args
        self.assertEqual(infile, skoolfile)
        self.assertFalse(write_hex)
        self.assertFalse(preserve_base)
        self.assertTrue(mock_sft_writer.write_called)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_skool2sft(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

    @patch.object(skool2sft, 'SftWriter', MockSftWriter)
    def test_option_h(self):
        skoolfile = 'test.skool'
        for option in ('-h', '--hex'):
            skool2sft.main((option, skoolfile))
            infile, write_hex, preserve_base = mock_sft_writer.args
            self.assertEqual(infile, skoolfile)
            self.assertTrue(write_hex)
            self.assertFalse(preserve_base)
            self.assertTrue(mock_sft_writer.write_called)

    @patch.object(skool2sft, 'SftWriter', MockSftWriter)
    def test_option_b(self):
        skoolfile = 'test.skool'
        for option in ('-b', '--preserve-base'):
            skool2sft.main((option, skoolfile))
            infile, write_hex, preserve_base = mock_sft_writer.args
            self.assertEqual(infile, skoolfile)
            self.assertFalse(write_hex)
            self.assertTrue(preserve_base)
            self.assertTrue(mock_sft_writer.write_called)

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
