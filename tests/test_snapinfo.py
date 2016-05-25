# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError, VERSION

class SnapinfoTest(SkoolKitTestCase):
    def test_no_arguments(self):
        output, error = self.run_snapinfo(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: snapinfo.py'))

    def test_invalid_option(self):
        output, error = self.run_snapinfo('-x test.z80', catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: snapinfo.py'))

    def test_unrecognised_snapshot_type(self):
        with self.assertRaisesRegexp(SkoolKitError, 'Unrecognised snapshot type$'):
            self.run_snapinfo('unknown.snap')

    def test_sna_48k(self):
        sna = list(range(23))
        sna[19] = 4 # Interrupts enabled
        sna.extend((0, 64)) # SP=16384
        sna.append(1) # IM 1
        sna.append(2) # BORDER 2
        sna.extend((0, 128)) # PC=32768
        sna.extend([0] * 49150)
        snafile = self.write_bin_file(sna, suffix='.sna')
        exp_output = [
            'RAM: 48K',
            'Interrupts: enabled',
            'Interrupt mode: 1',
            'Border: 2',
            'Registers:',
            '  PC  32768 8000    SP  16384 4000',
            '  IX   4625 1211    IY   4111 100F',
            '  I       0   00    R      20   14',
            "  B      14   0E    B'      6   06",
            "  C      13   0D    C'      5   05",
            "  BC   3597 0E0D    BC'  1541 0605",
            "  D      12   0C    D'      4   04",
            "  E      11   0B    E'      3   03",
            "  DE   3083 0C0B    DE'  1027 0403",
            "  H      10   0A    H'      2   02",
            "  L       9   09    L'      1   01",
            "  HL   2569 0A09    HL'   513 0201",
            "  A      22   16    A'      8   08",
            '    SZ5H3PNC           SZ5H3PNC',
            "  F 00010101        F' 00000111"
        ]

        output, error = self.run_snapinfo(snafile)
        self.assertEqual(error, '')
        self.assertEqual(exp_output, output)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_snapinfo(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

if __name__ == '__main__':
    unittest.main()
