# -*- coding: utf-8 -*-
import sys
import unittest

from skoolkittest import (SkoolKitTestCase, get_parity, create_header_block,
                          create_data_block, create_tap_header_block, create_tap_data_block)
from skoolkit import tapinfo, SkoolKitError, VERSION

class TapinfoTest(SkoolKitTestCase):
    def _write_tzx(self, blocks):
        tzx_data = [ord(c) for c in "ZXTape!"]
        tzx_data.extend((26, 1, 20))
        for block in blocks:
            tzx_data.extend(block)
        return self.write_bin_file(tzx_data, suffix='.tzx')

    def test_no_arguments(self):
        output, error = self.run_tapinfo(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: tapinfo.py'))

    def test_invalid_option(self):
        output, error = self.run_tapinfo('-x test.tap', catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: tapinfo.py'))

    def test_unrecognised_tape_type(self):
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tapinfo('unknown.tape')
        self.assertEqual(cm.exception.args[0], 'Unrecognised tape type')

    def test_tap_file(self):
        data = [1, 2, 4]
        tap_data = create_tap_header_block('test_tap', 32768, len(data))
        tap_data.extend(create_tap_data_block(data))
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        output, error = self.run_tapinfo(tapfile)
        self.assertEqual(len(error), 0)
        exp_output = [
            '1:',
            '  Type: Header block',
            '  Name: test_tap',
            '  Length: 19',
            '  Data: 0, 3, 116, 101, 115, 116, 95 ... 3, 0, 0, 128, 0, 0, 172',
            '2:',
            '  Type: Data block',
            '  Length: 5',
            '  Data: 255, 1, 2, 4, 7'
        ]
        self.assertEqual(exp_output, output)

    def test_tzx_file(self):
        data = [1, 4, 16]
        blocks = []

        block = [16] # Block ID
        block.extend((0, 0)) # Pause duration
        data_block = create_header_block('TEST_tzx', 49152, len(data))
        length = len(data_block)
        block.extend((length % 256, length // 256))
        block.extend(data_block)
        blocks.append(block)

        block = [16] # Block ID
        block.extend((0, 0)) # Pause duration
        data_block = create_data_block(data)
        length = len(data_block)
        block.extend((length % 256, length // 256))
        block.extend(data_block)
        blocks.append(block)

        tzxfile = self._write_tzx(blocks)
        output, error = self.run_tapinfo(tzxfile)
        self.assertEqual(len(error), 0)
        exp_output = [
            'Version: 1.20',
            '1: Standard speed data (0x10)',
            '  Type: Header block',
            '  Name: TEST_tzx',
            '  Length: 19',
            '  Data: 0, 3, 84, 69, 83, 84, 95 ... 3, 0, 0, 192, 0, 0, 255',
            '2: Standard speed data (0x10)',
            '  Type: Data block',
            '  Length: 5',
            '  Data: 255, 1, 4, 16, 21'
        ]
        self.assertEqual(exp_output, output)

    def test_invalid_tzx_file(self):
        invalid_tzx = self.write_text_file('This is not a TZX file', suffix='.tzx')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tapinfo(invalid_tzx)
        self.assertEqual(cm.exception.args[0], 'Not a TZX file')

    def test_tzx_with_unknown_block(self):
        block_id = 26
        block = [block_id, 0]
        tzxfile = self._write_tzx([block])
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tapinfo(tzxfile)
        self.assertEqual(cm.exception.args[0], 'Unknown block ID: 0x{:02X}'.format(block_id))

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_tapinfo(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

if __name__ == '__main__':
    unittest.main()
