# -*- coding: utf-8 -*-
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import skool2ctl, VERSION

ELEMENTS = 'btdrmsc'

class MockCtlWriter:
    def __init__(self, skoolfile, elements, write_hex, write_asm_dirs, preserve_base, min_address, max_address):
        global mock_ctl_writer
        self.skoolfile = skoolfile
        self.elements = elements
        self.write_hex = write_hex
        self.write_asm_dirs = write_asm_dirs
        self.preserve_base = preserve_base
        self.min_address = min_address
        self.max_address = max_address
        self.write_called = False
        mock_ctl_writer = self

    def write(self):
        self.write_called = True

class Skool2CtlTest(SkoolKitTestCase):
    def test_no_arguments(self):
        output, error = self.run_skool2ctl(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: skool2ctl.py'))

    def test_invalid_arguments(self):
        for args in ('-h', '-x test.skool'):
            output, error = self.run_skool2ctl(args, catch_exit=2)
            self.assertEqual(len(output), 0)
            self.assertTrue(error.startswith('usage: skool2ctl.py'))

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_default_option_values(self):
        skoolfile = 'test.skool'
        skool2ctl.main((skoolfile,))
        self.assertEqual(mock_ctl_writer.skoolfile, skoolfile)
        self.assertEqual(mock_ctl_writer.elements, ELEMENTS)
        self.assertEqual(mock_ctl_writer.write_hex, 0)
        self.assertTrue(mock_ctl_writer.write_asm_dirs)
        self.assertFalse(mock_ctl_writer.preserve_base)
        self.assertEqual(mock_ctl_writer.min_address, 0)
        self.assertEqual(mock_ctl_writer.max_address, 65536)
        self.assertTrue(mock_ctl_writer.write_called)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_skool2ctl(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_w(self):
        skoolfile = 'test.skool'
        for w in ('b', 't', 'd', 'r', 'm', 's', 'c', 'btd', ELEMENTS):
            for option in ('-w', '--write'):
                skool2ctl.main((option, w, skoolfile))
                self.assertEqual(mock_ctl_writer.skoolfile, skoolfile)
                self.assertEqual(mock_ctl_writer.elements, w)
                self.assertEqual(mock_ctl_writer.write_hex, 0)
                self.assertTrue(mock_ctl_writer.write_asm_dirs)
                self.assertFalse(mock_ctl_writer.preserve_base)
                self.assertEqual(mock_ctl_writer.min_address, 0)
                self.assertEqual(mock_ctl_writer.max_address, 65536)
                self.assertTrue(mock_ctl_writer.write_called)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_h(self):
        skoolfile = 'test.skool'
        for option in ('-h', '--hex'):
            skool2ctl.main((option, skoolfile))
            self.assertEqual(mock_ctl_writer.skoolfile, skoolfile)
            self.assertEqual(mock_ctl_writer.elements, ELEMENTS)
            self.assertEqual(mock_ctl_writer.write_hex, 1)
            self.assertTrue(mock_ctl_writer.write_asm_dirs)
            self.assertFalse(mock_ctl_writer.preserve_base)
            self.assertEqual(mock_ctl_writer.min_address, 0)
            self.assertEqual(mock_ctl_writer.max_address, 65536)
            self.assertTrue(mock_ctl_writer.write_called)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_l(self):
        skoolfile = 'test.skool'
        for option in ('-l', '--hex-lower'):
            skool2ctl.main((option, skoolfile))
            self.assertEqual(mock_ctl_writer.skoolfile, skoolfile)
            self.assertEqual(mock_ctl_writer.elements, ELEMENTS)
            self.assertEqual(mock_ctl_writer.write_hex, -1)
            self.assertTrue(mock_ctl_writer.write_asm_dirs)
            self.assertFalse(mock_ctl_writer.preserve_base)
            self.assertEqual(mock_ctl_writer.min_address, 0)
            self.assertEqual(mock_ctl_writer.max_address, 65536)
            self.assertTrue(mock_ctl_writer.write_called)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_a(self):
        skoolfile = 'test.skool'
        for option in ('-a', '--no-asm-dirs'):
            skool2ctl.main((option, skoolfile))
            self.assertEqual(mock_ctl_writer.skoolfile, skoolfile)
            self.assertEqual(mock_ctl_writer.elements, ELEMENTS)
            self.assertEqual(mock_ctl_writer.write_hex, 0)
            self.assertFalse(mock_ctl_writer.write_asm_dirs)
            self.assertFalse(mock_ctl_writer.preserve_base)
            self.assertEqual(mock_ctl_writer.min_address, 0)
            self.assertEqual(mock_ctl_writer.max_address, 65536)
            self.assertTrue(mock_ctl_writer.write_called)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_b(self):
        skoolfile = 'test.skool'
        for option in ('-b', '--preserve-base'):
            skool2ctl.main((option, skoolfile))
            self.assertEqual(mock_ctl_writer.skoolfile, skoolfile)
            self.assertEqual(mock_ctl_writer.elements, ELEMENTS)
            self.assertEqual(mock_ctl_writer.write_hex, 0)
            self.assertTrue(mock_ctl_writer.write_asm_dirs)
            self.assertTrue(mock_ctl_writer.preserve_base)
            self.assertEqual(mock_ctl_writer.min_address, 0)
            self.assertEqual(mock_ctl_writer.max_address, 65536)
            self.assertTrue(mock_ctl_writer.write_called)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_S(self):
        skoolfile = 'test.skool'
        for option, start in (('-S', 30000), ('--start', 40000)):
            skool2ctl.main((option, str(start), skoolfile))
            self.assertEqual(mock_ctl_writer.skoolfile, skoolfile)
            self.assertEqual(mock_ctl_writer.elements, ELEMENTS)
            self.assertEqual(mock_ctl_writer.write_hex, 0)
            self.assertTrue(mock_ctl_writer.write_asm_dirs)
            self.assertFalse(mock_ctl_writer.preserve_base)
            self.assertTrue(mock_ctl_writer.write_called)
            self.assertEqual(mock_ctl_writer.min_address, start)
            self.assertEqual(mock_ctl_writer.max_address, 65536)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_E(self):
        skoolfile = 'test.skool'
        for option, end in (('-E', 40000), ('--end', 50000)):
            skool2ctl.main((option, str(end), skoolfile))
            self.assertEqual(mock_ctl_writer.skoolfile, skoolfile)
            self.assertEqual(mock_ctl_writer.elements, ELEMENTS)
            self.assertEqual(mock_ctl_writer.write_hex, 0)
            self.assertTrue(mock_ctl_writer.write_asm_dirs)
            self.assertFalse(mock_ctl_writer.preserve_base)
            self.assertTrue(mock_ctl_writer.write_called)
            self.assertEqual(mock_ctl_writer.min_address, 0)
            self.assertEqual(mock_ctl_writer.max_address, end)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_options_S_and_E(self):
        skoolfile = 'test.skool'
        start = 24576
        end = 32768
        skool2ctl.main(('-S', str(start), '-E', str(end), skoolfile))
        self.assertEqual(mock_ctl_writer.skoolfile, skoolfile)
        self.assertEqual(mock_ctl_writer.elements, ELEMENTS)
        self.assertEqual(mock_ctl_writer.write_hex, 0)
        self.assertTrue(mock_ctl_writer.write_asm_dirs)
        self.assertFalse(mock_ctl_writer.preserve_base)
        self.assertTrue(mock_ctl_writer.write_called)
        self.assertEqual(mock_ctl_writer.min_address, start)
        self.assertEqual(mock_ctl_writer.max_address, end)

    def test_run(self):
        skool = '\n'.join((
            '; Test skool file for skool2ctl testing',
            'c32768 RET'
        ))
        skoolfile = self.write_text_file(skool, suffix='.skool')
        output, error = self.run_skool2ctl(skoolfile)
        self.assertEqual(len(error), 0)
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], 'c 32768 Test skool file for skool2ctl testing')

if __name__ == '__main__':
    unittest.main()
