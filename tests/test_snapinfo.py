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

    def test_z80v3_48k_uncompressed(self):
        header = list(range(30))
        header[6:8] = [0, 0] # Version 2+
        header[12] = 6 # BORDER 3, uncompressed RAM
        header.extend((54, 0)) # Remaining header length (version 3)
        header.extend((206, 250)) # PC=64206
        header += [0] * (header[-4] - 2)
        ram = [0] * 49152
        z80file = self.write_z80_file(header, ram)
        exp_output = [
            'Z80 file: {}'.format(z80file),
            'Version: 3',
            'Machine: 48K Spectrum',
            'Interrupts: enabled',
            'Interrupt mode: 1',
            'Border: 3',
            'Registers:',
            '  PC  64206 FACE    SP   2312 0908',
            '  IX   6681 1A19    IY   6167 1817',
            '  I      10   0A    R      11   0B',
            "  B       3   03    B'     16   10",
            "  C       2   02    C'     15   0F",
            "  BC    770 0302    BC'  4111 100F",
            "  D      14   0E    D'     18   12",
            "  E      13   0D    E'     17   11",
            "  DE   3597 0E0D    DE'  4625 1211",
            "  H       5   05    H'     20   14",
            "  L       4   04    L'     19   13",
            "  HL   1284 0504    HL'  5139 1413",
            "  A       0   00    A'     21   15",
            '    SZ5H3PNC           SZ5H3PNC',
            "  F 00000001        F' 00010110",
            'RAM block 4 (32768-49151 8000-BFFF): 16384 bytes (uncompressed)',
            'RAM block 5 (49152-65535 C000-FFFF): 16384 bytes (uncompressed)',
            'RAM block 8 (16384-32767 4000-7FFF): 16384 bytes (uncompressed)'
        ]

        output, error = self.run_snapinfo(z80file)
        self.assertEqual(error, '')
        self.assertEqual(exp_output, output)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_snapinfo(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

if __name__ == '__main__':
    unittest.main()
