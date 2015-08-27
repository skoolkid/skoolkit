# -*- coding: utf-8 -*-
import sys
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError, VERSION, skool2bin

PY3 = sys.version_info >= (3,)

class MockBinWriter:
    def __init__(self, skoolfile, asm_mode):
        global mock_bin_writer
        mock_bin_writer = self
        self.skoolfile = skoolfile
        self.asm_mode = asm_mode
        self.binfile = None
        self.start = None
        self.end = None

    def write(self, binfile, start, end):
        self.binfile = binfile
        self.start = start
        self.end = end

class Skool2BinTest(SkoolKitTestCase):
    def test_no_arguments(self):
        output, error = self.run_skool2bin(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: skool2bin.py'))

    def test_invalid_option(self):
        output, error = self.run_skool2bin('-x test.skool', catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: skool2bin.py'))

    def test_invalid_option_value(self):
        skoolfile = self.write_text_file(suffix='.skool')
        for option in ('-E ABC', '-S ='):
            output, error = self.run_skool2bin('{} {}'.format(option, skoolfile), catch_exit=2)
            self.assertEqual(len(output), 0)
            self.assertTrue(error.startswith('usage: skool2bin.py'))

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_default_option_values(self):
        skoolfile = 'test-defaults.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        output, error = self.run_skool2bin(skoolfile)
        self.assertEqual(len(error), 0)
        self.assertEqual(mock_bin_writer.skoolfile, skoolfile)
        self.assertEqual(mock_bin_writer.asm_mode, 0)
        self.assertEqual(mock_bin_writer.binfile, exp_binfile)
        self.assertIsNone(mock_bin_writer.start)
        self.assertIsNone(mock_bin_writer.end)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_nonstandard_skool_name(self):
        skoolfile = 'nonstandard.sks'
        exp_binfile = skoolfile + '.bin'
        output, error = self.run_skool2bin(skoolfile)
        self.assertEqual(len(error), 0)
        self.assertEqual(mock_bin_writer.binfile, exp_binfile)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_skool_file_from_stdin(self):
        output, error = self.run_skool2bin('-')
        self.assertEqual(len(error), 0)
        self.assertEqual(mock_bin_writer.binfile, 'program.bin')

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_E(self):
        skoolfile = 'test-E.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option, value in (('-E', 32768), ('--end', 49152)):
            output, error = self.run_skool2bin('{} {} {}'.format(option, value, skoolfile))
            self.assertEqual(len(error), 0)
            self.assertEqual(mock_bin_writer.skoolfile, skoolfile)
            self.assertEqual(mock_bin_writer.asm_mode, 0)
            self.assertEqual(mock_bin_writer.binfile, exp_binfile)
            self.assertIsNone(mock_bin_writer.start)
            self.assertEqual(mock_bin_writer.end, value)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_i(self):
        skoolfile = 'test-i.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option in ('-i', '--isub'):
            output, error = self.run_skool2bin('{} {}'.format(option, skoolfile))
            self.assertEqual(len(error), 0)
            self.assertEqual(mock_bin_writer.skoolfile, skoolfile)
            self.assertEqual(mock_bin_writer.asm_mode, 1)
            self.assertEqual(mock_bin_writer.binfile, exp_binfile)
            self.assertIsNone(mock_bin_writer.start)
            self.assertIsNone(mock_bin_writer.end)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_S(self):
        skoolfile = 'test-S.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option, value in (('-S', 24576), ('--start', 32768)):
            output, error = self.run_skool2bin('{} {} {}'.format(option, value, skoolfile))
            self.assertEqual(len(error), 0)
            self.assertEqual(mock_bin_writer.skoolfile, skoolfile)
            self.assertEqual(mock_bin_writer.asm_mode, 0)
            self.assertEqual(mock_bin_writer.binfile, exp_binfile)
            self.assertEqual(mock_bin_writer.start, value)
            self.assertIsNone(mock_bin_writer.end)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_skool2bin(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

class BinWriterTest(SkoolKitTestCase):
    def _test_write(self, skool, base_address, exp_data, exp_err=None, asm_mode=0, start=None, end=None):
        if skool is None:
            skoolfile = '-'
            binfile = self.write_bin_file(suffix='.bin')
        else:
            skoolfile = self.write_text_file(skool, suffix='.skool')
            binfile = skoolfile[:-6] + '.bin'
            self.tempfiles.append(binfile)
        bin_writer = skool2bin.BinWriter(skoolfile, asm_mode)
        bin_writer.write(binfile, start, end)
        with open(binfile, 'rb') as f:
            data = f.read()
        if PY3:
            data = list(data)
        else:
            data = [ord(c) for c in data]
        self.assertEqual(exp_data, data)
        size = len(data)
        stderr = self.to_lines(self.err.getvalue(), True)
        if exp_err:
            self.assertEqual(exp_err, stderr[:-1])
        self.assertEqual(stderr[-1], "Wrote {}: start={}, end={}, size={}".format(binfile, base_address, base_address + size, size))

    def test_write(self):
        skool = '\n'.join((
            '; Routine at 30000',
            '@label=START',
            'c30000 RET',
            '',
            '; Routine at 30001',
            '@ssub-begin',
            'c30001 LD A,10  ; Load the',
            '                ; accumulator with 10',
            '@ssub+else',
            'c30001 LD A,11  ; Load the',
            '                ; accumulator with 11',
            '@ssub+end',
            ' 30003 RET',
            '',
            'd30004 DEFB 0'
        ))
        self._test_write(skool, 30000, [201, 62, 10, 201])

    def test_write_i_block(self):
        skool = '\n'.join((
            'i29999 DEFB 128',
            '',
            'c30000 RET'
        ))
        self._test_write(skool, 29999, [128, 201])

    def test_nonexistent_skool_file(self):
        with self.assertRaises(SkoolKitError) as cm:
            self.run_skool2bin('nonexistent.skool')
        self.assertEqual(cm.exception.args[0], 'nonexistent.skool: file not found')

    def test_invalid_instruction_address(self):
        skoolfile = self.write_text_file('c4000d RET', suffix='.skool')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_skool2bin(skoolfile)
        self.assertEqual(cm.exception.args[0], 'Invalid address (4000d):\nc4000d RET')

    def test_invalid_instruction(self):
        skool = '\n'.join((
            'c40000 LD A,B',
            ' 40001 XOR HL',
            ' 40002 RET'
        ))
        self._test_write(skool, 40000, [120, 0, 201], ['WARNING: Failed to assemble:', ' 40001 XOR HL'])

    def test_skool_file_from_stdin(self):
        self.write_stdin('c49152 RET')
        self._test_write(None, 49152, [201])

    def test_start_address(self):
        skool = '\n'.join((
            'c50000 LD A,C',
            ' 50001 XOR B',
            ' 50002 RET'
        ))
        self._test_write(skool, 50001, [168, 201], start=50001)

    def test_end_address(self):
        skool = '\n'.join((
            'c60000 LD A,C',
            ' 60001 XOR B',
            ' 60002 RET'
        ))
        self._test_write(skool, 60000, [121, 168], end=60002)

    def test_start_address_and_end_address(self):
        skool = '\n'.join((
            'c32768 LD A,C',
            ' 32769 XOR B',
            ' 32770 RET'
        ))
        self._test_write(skool, 32769, [168], start=32769, end=32770)

    def test_isub_mode(self):
        skool = '\n'.join((
            '@isub+begin',
            'c39997 JP 40000',
            '@isub+end',
            '',
            'c40000 XOR A',
            '@isub=LD B,1',
            ' 40001 LD B,n',
            ' 40003 RET',
        ))
        exp_data = [195, 64, 156, 175, 6, 1, 201]
        self._test_write(skool, 39997, exp_data, asm_mode=1)

if __name__ == '__main__':
    unittest.main()
