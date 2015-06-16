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

    def write(self, min_address, max_address):
        self.write_called = True
        self.min_address = min_address
        self.max_address = max_address

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
        self.assertEqual(write_hex, 0)
        self.assertFalse(preserve_base)
        self.assertTrue(mock_sft_writer.write_called)
        self.assertEqual(mock_sft_writer.min_address, 0)
        self.assertEqual(mock_sft_writer.max_address, 65536)

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
            self.assertEqual(write_hex, 1)
            self.assertFalse(preserve_base)
            self.assertTrue(mock_sft_writer.write_called)

    @patch.object(skool2sft, 'SftWriter', MockSftWriter)
    def test_option_l(self):
        skoolfile = 'test.skool'
        for option in ('-l', '--hex-lower'):
            skool2sft.main((option, skoolfile))
            infile, write_hex, preserve_base = mock_sft_writer.args
            self.assertEqual(infile, skoolfile)
            self.assertEqual(write_hex, -1)
            self.assertFalse(preserve_base)
            self.assertTrue(mock_sft_writer.write_called)

    @patch.object(skool2sft, 'SftWriter', MockSftWriter)
    def test_option_b(self):
        skoolfile = 'test.skool'
        for option in ('-b', '--preserve-base'):
            skool2sft.main((option, skoolfile))
            infile, write_hex, preserve_base = mock_sft_writer.args
            self.assertEqual(infile, skoolfile)
            self.assertEqual(write_hex, 0)
            self.assertTrue(preserve_base)
            self.assertTrue(mock_sft_writer.write_called)

    @patch.object(skool2sft, 'SftWriter', MockSftWriter)
    def test_option_E(self):
        for option, end in (('-E', 30000), ('--end', 40000)):
            skool2sft.main((option, str(end), 'test.skool'))
            self.assertTrue(mock_sft_writer.write_called)
            self.assertEqual(mock_sft_writer.min_address, 0)
            self.assertEqual(mock_sft_writer.max_address, end)

    @patch.object(skool2sft, 'SftWriter', MockSftWriter)
    def test_option_S(self):
        for option, start in (('-S', 40000), ('--start', 50000)):
            skool2sft.main((option, str(start), 'test.skool'))
            self.assertTrue(mock_sft_writer.write_called)
            self.assertEqual(mock_sft_writer.min_address, start)
            self.assertEqual(mock_sft_writer.max_address, 65536)

    @patch.object(skool2sft, 'SftWriter', MockSftWriter)
    def test_options_S_and_E(self):
        start = 32768
        end = 49152
        skool2sft.main(('-S', str(start), '-E', str(end), 'test.skool'))
        self.assertTrue(mock_sft_writer.write_called)
        self.assertEqual(mock_sft_writer.min_address, start)
        self.assertEqual(mock_sft_writer.max_address, end)

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
