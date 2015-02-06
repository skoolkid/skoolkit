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
    def __init__(self, *args):
        global mock_ctl_writer
        self.args = args
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
        infile, elements, write_hex, write_asm_dirs, preserve_base = mock_ctl_writer.args
        self.assertEqual(infile, skoolfile)
        self.assertEqual(elements, ELEMENTS)
        self.assertFalse(write_hex)
        self.assertTrue(write_asm_dirs)
        self.assertFalse(preserve_base)
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
                infile, elements, write_hex, write_asm_dirs, preserve_base = mock_ctl_writer.args
                self.assertEqual(infile, skoolfile)
                self.assertEqual(elements, w)
                self.assertFalse(write_hex)
                self.assertTrue(write_asm_dirs)
                self.assertFalse(preserve_base)
                self.assertTrue(mock_ctl_writer.write_called)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_h(self):
        skoolfile = 'test.skool'
        for option in ('-h', '--hex'):
            skool2ctl.main((option, skoolfile))
            infile, elements, write_hex, write_asm_dirs, preserve_base = mock_ctl_writer.args
            self.assertEqual(infile, skoolfile)
            self.assertEqual(elements, ELEMENTS)
            self.assertTrue(write_hex)
            self.assertTrue(write_asm_dirs)
            self.assertFalse(preserve_base)
            self.assertTrue(mock_ctl_writer.write_called)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_a(self):
        skoolfile = 'test.skool'
        for option in ('-a', '--no-asm-dirs'):
            skool2ctl.main((option, skoolfile))
            infile, elements, write_hex, write_asm_dirs, preserve_base = mock_ctl_writer.args
            self.assertEqual(infile, skoolfile)
            self.assertEqual(elements, ELEMENTS)
            self.assertFalse(write_hex)
            self.assertFalse(write_asm_dirs)
            self.assertFalse(preserve_base)
            self.assertTrue(mock_ctl_writer.write_called)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_b(self):
        skoolfile = 'test.skool'
        for option in ('-b', '--preserve-base'):
            skool2ctl.main((option, skoolfile))
            infile, elements, write_hex, write_asm_dirs, preserve_base = mock_ctl_writer.args
            self.assertEqual(infile, skoolfile)
            self.assertEqual(elements, ELEMENTS)
            self.assertFalse(write_hex)
            self.assertTrue(write_asm_dirs)
            self.assertTrue(preserve_base)
            self.assertTrue(mock_ctl_writer.write_called)

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
