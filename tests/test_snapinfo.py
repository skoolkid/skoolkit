# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError, VERSION

class SnapinfoTest(SkoolKitTestCase):
    def _test_sna(self, ram, exp_output, options='', header=None):
        if header is None:
            header = [0] * 27
        snafile = self.write_bin_file(header + ram, suffix='.sna')
        output, error = self.run_snapinfo(' '.join((options, snafile)))
        self.assertEqual(error, '')
        self.assertEqual(exp_output, output)

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
        header = list(range(23))
        header[19] = 4 # Interrupts enabled
        header.extend((0, 64)) # SP=16384
        header.append(1) # IM 1
        header.append(2) # BORDER 2
        ram = [0, 128] # PC=32768
        ram.extend([0] * 49150)
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
        self._test_sna(ram, exp_output, header=header)

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

    def test_szx_48k_uncompressed(self):
        registers = list(range(26)) # Registers
        registers.extend((1, 1)) # IFF1, IFF2
        registers.append(2) # Interrupt mode
        registers.extend((0, 0, 0, 0, 0, 0, 0, 0))
        szxfile = self.write_szx([0] * 49152, False, registers=registers, border=3)
        exp_output = [
            'Version: 1.4',
            'Machine: 48K ZX Spectrum',
            'SPCR: 8 bytes',
            '  Border: 3',
            '  Port $7FFD: 0 (bank 0 paged into 49152-65535 C000-FFFF)',
            'Z80R: 37 bytes',
            '  Interrupts: enabled',
            '  Interrupt mode: 2',
            '  PC   5910 1716    SP   5396 1514',
            '  IX   4368 1110    IY   4882 1312',
            '  I      24   18    R      25   19',
            "  B       3   03    B'     11   0B",
            "  C       2   02    C'     10   0A",
            "  BC    770 0302    BC'  2826 0B0A",
            "  D       5   05    D'     13   0D",
            "  E       4   04    E'     12   0C",
            "  DE   1284 0504    DE'  3340 0D0C",
            "  H       7   07    H'     15   0F",
            "  L       6   06    L'     14   0E",
            "  HL   1798 0706    HL'  3854 0F0E",
            "  A       1   01    A'      9   09",
            '    SZ5H3PNC           SZ5H3PNC',
            "  F 00000000        F' 00001000",
            'RAMP: 16387 bytes',
            '  Page: 0',
            '  RAM: 16384 bytes, uncompressed',
            'RAMP: 16387 bytes',
            '  Page: 2',
            '  RAM: 32768-49151 8000-BFFF: 16384 bytes, uncompressed',
            'RAMP: 16387 bytes',
            '  Page: 5',
            '  RAM: 16384-32767 4000-7FFF: 16384 bytes, uncompressed'
        ]

        output, error = self.run_snapinfo(szxfile)
        self.assertEqual(error, '')
        self.assertEqual(exp_output, output)

    def test_option_b_with_integers(self):
        basic = (
            0, 10,                # Line 10
            13, 0,                # Length of line 10
            253,                  # CLEAR
            50, 52, 53, 55, 53,   # 24575
            14, 0, 0, 255, 95, 0, # 24575 in floating point form
            13,                   # ENTER
            0, 20,                # Line 20
            5, 0,                 # Length of line 20
            239, 34, 34, 175,     # LOAD ""CODE
            13,                   # ENTER
            0, 30,                # Line 30
            14, 0,                # Length of line 30
            249, 192,             # RANDOMIZE USR
            50, 52, 53, 55, 54,   # 24576
            14, 0, 0, 0, 96, 0,   # 24576 in floating point form
            13,                   # ENTER
            128                   # End of BASIC area
        )
        ram = [0] * 49152
        ram[7371:7371 + len(basic)] = basic
        exp_output = [
            '  10 CLEAR 24575',
            '  20 LOAD ""CODE',
            '  30 RANDOMIZE USR 24576'
        ]
        self._test_sna(ram, exp_output, '-b')

    def test_option_f_with_single_byte(self):
        ram = [0] * 49152
        address = 53267
        ram[address - 16384] = 77
        exp_output = ['53267-53267-1 D013-D013-1: 77']
        self._test_sna(ram, exp_output, '-f 77')

    def test_option_find_with_byte_sequence(self):
        ram = [0] * 49152
        address = 35674
        seq = (2, 4, 6)
        ram[address - 16384:address - 16384 + len(seq)] = seq
        seq_str = ','.join([str(b) for b in seq])
        exp_output = ['35674-35676-1 8B5A-8B5C-1: {}'.format(seq_str)]
        self._test_sna(ram, exp_output, '--find {}'.format(seq_str))

    def test_option_f_with_byte_sequence_and_step(self):
        ram = [0] * 49152
        address = 47983
        seq = (2, 3, 5)
        step = 2
        ram[address - 16384:address - 16384 + step * len(seq):step] = seq
        seq_str = ','.join([str(b) for b in seq])
        exp_output = ['47983-47987-2 BB6F-BB73-2: {}'.format(seq_str)]
        self._test_sna(ram, exp_output, '-f {}-{}'.format(seq_str, step))

    def test_option_find_with_nonexistent_byte_sequence(self):
        ram = [0] * 49152
        exp_output = []
        self._test_sna(ram, exp_output, '--find 1,2,3')

    def test_option_p_with_single_address(self):
        ram = [0] * 49152
        address = 31759
        ram[address - 16384] = 47
        exp_output = ['31759 7C0F:  47  2F  00101111  /']
        self._test_sna(ram, exp_output, '-p {}'.format(address))

    def test_option_peek_with_address_range(self):
        ram = [0] * 49152
        address1 = 41885
        address2 = 41888
        ram[address1 - 16384:address2 -16383] = list(range(153, 154 + address2 - address1))
        exp_output = [
            '41885 A39D: 153  99  10011001',
            '41886 A39E: 154  9A  10011010',
            '41887 A39F: 155  9B  10011011',
            '41888 A3A0: 156  9C  10011100'
        ]
        self._test_sna(ram, exp_output, '--peek {}-{}'.format(address1, address2))

    def test_option_p_with_address_range_and_step(self):
        ram = [0] * 49152
        address1 = 25663
        address2 = 25669
        step = 3
        ram[address1 - 16384:address2 -16383:step] = [33, 65, 255]
        exp_output = [
            '25663 643F:  33  21  00100001  !',
            '25666 6442:  65  41  01000001  A',
            '25669 6445: 255  FF  11111111'
        ]
        self._test_sna(ram, exp_output, '-p {}-{}-{}'.format(address1, address2, step))

    def test_option_peek_multiple(self):
        ram = [0] * 49152
        options = []
        addresses = (33333, 44173, 50998)
        for a in addresses:
            ram[a - 16384] = a % 256
            options.append('--peek {}'.format(a))
        exp_output = [
            '33333 8235:  53  35  00110101  5',
            '44173 AC8D: 141  8D  10001101',
            '50998 C736:  54  36  00110110  6'
        ]
        self._test_sna(ram, exp_output, ' '.join(options))

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_snapinfo(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

if __name__ == '__main__':
    unittest.main()
