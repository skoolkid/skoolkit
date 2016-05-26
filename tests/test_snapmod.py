# -*- coding: utf-8 -*-
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError, snapmod, read_bin_file, VERSION
from skoolkit.snapshot import get_snapshot

def mock_run(*args):
    global run_args
    run_args = args

class SnapmodTest(SkoolKitTestCase):
    def test_no_arguments(self):
        output, error = self.run_snapmod(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: snapmod.py'))

    def test_invalid_option(self):
        output, error = self.run_snapmod('-x test.z80', catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: snapmod.py'))

    def test_unrecognised_snapshot_type(self):
        with self.assertRaisesRegexp(SkoolKitError, 'Unrecognised input snapshot type$'):
            self.run_snapmod('unknown.snap')

    @patch.object(snapmod, 'run', mock_run)
    def test_options_s_state(self):
        for option in ('-s', '--state'):
            output, error = self.run_snapmod('{0} im=1 {0} iff=1 test.z80'.format(option))
            self.assertEqual([], output)
            self.assertEqual(error, '')
            infile, options, outfile = run_args
            self.assertEqual(['im=1', 'iff=1'], options.state)

    def test_option_s(self):
        header = [0] * 86
        header[30] = 54 # Version 3
        ram = [0] * 49152
        infile = self.write_z80_file(header, ram)
        exp_header = header[:]
        exp_header[12] |= 4 # BORDER 2
        exp_header[27] = 1 # IFF 1
        exp_header[28] = 1 # IFF 2
        exp_header[29] = (header[29] & 252) | 2 # IM 2
        outfile = self.write_bin_file(suffix='.z80')
        output, error = self.run_snapmod('-f -s border=2 -s iff=1 -s im=2 {} {}'.format(infile, outfile))
        self.assertEqual([], output)
        self.assertEqual(error, '')
        z80_header = list(read_bin_file(outfile, 86))
        self.assertEqual(exp_header, z80_header)
        z80_ram = get_snapshot(outfile)[16384:]
        self.assertEqual(ram, z80_ram, "RAM was not preserved")

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_snapmod(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

if __name__ == '__main__':
    unittest.main()
