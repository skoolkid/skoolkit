# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit import tap2sna, VERSION
from skoolkit.snapshot import get_snapshot

class Tap2SnaTest(SkoolKitTestCase):
    def _write_tap(self, blocks):
        tap_data = []
        for block in blocks:
            tap_data.extend(block)
        return self.write_bin_file(tap_data, suffix='.tap')

    def _create_tap_data_block(self, data):
        parity = 0
        for b in data:
            parity ^= b
        length = len(data) + 2 # Marker + data + parity
        return [length % 256, length // 256, 255] + data + [parity]

    def test_no_arguments(self):
        output, error = self.run_tap2sna(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage:'))

    def test_invalid_arguments(self):
        for args in ('--foo', '-k test.zip'):
            output, error = self.run_tap2sna(args, catch_exit=2)
            self.assertEqual(len(output), 0)
            self.assertTrue(error.startswith('usage:'))

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_tap2sna(option, err_lines=True, catch_exit=0)
            self.assertEqual(len(output), 0)
            self.assertEqual(len(error), 1)
            self.assertEqual(error[0], 'SkoolKit {}'.format(VERSION))

    def test_ram_load(self):
        data = [1, 2, 3]
        block = self._create_tap_data_block(data)
        tapfile = self._write_tap([block])
        z80file = self.write_bin_file(suffix='.z80')
        start = 16384
        output, error = self.run_tap2sna('--force --ram load=1,{} {} {}'.format(start, tapfile, z80file))
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], 'Writing {}'.format(z80file))
        self.assertEqual(error, '')
        snapshot = get_snapshot(z80file)
        self.assertEqual(snapshot[start:start + len(data)], data)

if __name__ == '__main__':
    unittest.main()
