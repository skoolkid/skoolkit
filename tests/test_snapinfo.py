# -*- coding: utf-8 -*-
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError, snapinfo, VERSION

class MockBasicLister:
    def list_basic(self, snapshot):
        global mock_basic_lister
        mock_basic_lister = self
        self.snapshot = snapshot
        return 'DONE!'

class SnapinfoTest(SkoolKitTestCase):
    def _test_sna(self, ram, exp_output, options='', header=None):
        if header is None:
            header = [0] * 27
        snafile = self.write_bin_file(header + ram, suffix='.sna')
        output, error = self.run_snapinfo(' '.join((options, snafile)))
        self.assertEqual(error, '')
        self.assertEqual(exp_output, output)

    def _test_z80(self, exp_output, header=None, ram=None, version=3, compress=False, machine_id=0, pages=None):
        if ram is None:
            ram = [0] * 49152
        z80file = self.write_z80_file(header, ram, version, compress, machine_id, pages or {})
        output, error = self.run_snapinfo(z80file)
        self.assertEqual(error, '')
        self.assertEqual(['Z80 file: {}'.format(z80file)] + exp_output, output)

    def _test_szx(self, exp_output, registers=None, border=0, ram=None, compress=False, machine_id=1, ch7ffd=0, pages=None):
        if ram is None:
            ram = [0] * 49152
        if machine_id > 1 and pages is None:
            bank = (0,) * 16384
            pages = {p: bank for p in (1, 3, 4, 6, 7)}
        szxfile = self.write_szx(ram, compress, machine_id, ch7ffd, pages, registers, border)
        output, error = self.run_snapinfo(szxfile)
        self.assertEqual(error, '')
        self.assertEqual(exp_output, output)

    def _test_basic(self, data, exp_output, option):
        ram = [0] * 49152
        ram[7371:7371 + len(data)] = data
        self._test_sna(ram, exp_output, ('-b', '--basic')[option])

    def _test_bad_spec(self, option, bad_spec, exp_error):
        with self.assertRaises(SkoolKitError) as cm:
            self.run_snapinfo('{} {} test.sna'.format(option, bad_spec))
        self.assertEqual(cm.exception.args[0], '{}: {}'.format(exp_error, bad_spec))

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

    def test_nonexistent_input_file(self):
        infile = 'non-existent.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_snapinfo(infile)
        self.assertEqual(cm.exception.args[0], '{}: file not found'.format(infile))

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

    def test_sna_128k(self):
        header = list(range(25))
        header[19] = 0 # Interrupts disabled
        header.append(2) # IM 2
        header.append(4) # BORDER 4
        ram = [0] * 49152
        header2 = [0, 96] # PC=24576
        header2.append(1) # Port 0x7ffd
        header2.append(0) # TR-DOS ROM not paged
        banks = [0] * (5 * 16384)
        exp_output = [
            'RAM: 128K',
            'Interrupts: disabled',
            'Interrupt mode: 2',
            'Border: 4',
            'Registers:',
            '  PC  24576 6000    SP   6167 1817',
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
            "  F 00010101        F' 00000111",
            'RAM bank 5 (16384 bytes: 16384-32767 4000-7FFF)',
            'RAM bank 2 (16384 bytes: 32768-49151 8000-BFFF)',
            'RAM bank 1 (16384 bytes: 49152-65535 C000-FFFF)',
            'RAM bank 0 (16384 bytes)',
            'RAM bank 3 (16384 bytes)',
            'RAM bank 4 (16384 bytes)',
            'RAM bank 6 (16384 bytes)',
            'RAM bank 7 (16384 bytes)'
        ]

        self._test_sna(ram + header2 + banks, exp_output, header=header)

    def test_sna_128k_9_banks(self):
        header = list(range(25))
        header[19] = 0 # Interrupts disabled
        header.append(1) # IM 1
        header.append(5) # BORDER 5
        ram = [0] * 49152
        header2 = [0, 96] # PC=24576
        header2.append(2) # Port 0x7ffd
        header2.append(0) # TR-DOS ROM not paged
        banks = [0] * (6 * 16384)
        exp_output = [
            'RAM: 128K',
            'Interrupts: disabled',
            'Interrupt mode: 1',
            'Border: 5',
            'Registers:',
            '  PC  24576 6000    SP   6167 1817',
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
            "  F 00010101        F' 00000111",
            'RAM bank 5 (16384 bytes: 16384-32767 4000-7FFF)',
            'RAM bank 2 (16384 bytes: 32768-49151 8000-BFFF)',
            'RAM bank 2 (16384 bytes: 49152-65535 C000-FFFF)',
            'RAM bank 0 (16384 bytes)',
            'RAM bank 1 (16384 bytes)',
            'RAM bank 3 (16384 bytes)',
            'RAM bank 4 (16384 bytes)',
            'RAM bank 6 (16384 bytes)',
            'RAM bank 7 (16384 bytes)'
        ]
        self._test_sna(ram + header2 + banks, exp_output, header=header)

    def test_sna_bad_size(self):
        for size in (49178, 49180, 131104, 147488):
            infile = self.write_bin_file([0] * size, suffix='.sna')
            with self.assertRaises(SkoolKitError) as cm:
                self.run_snapinfo(infile)
            self.assertEqual(cm.exception.args[0], '{}: not a SNA file'.format(infile))

    def test_z80v1_uncompressed(self):
        header = list(range(16, 46))
        header[12] = 12 # BORDER 6, uncompressed RAM
        exp_output = [
            'Version: 1',
            'Machine: 48K Spectrum',
            'Interrupts: enabled',
            'Interrupt mode: 1',
            'Border: 6',
            'Registers:',
            '  PC   5910 1716    SP   6424 1918',
            '  IX  10793 2A29    IY  10279 2827',
            '  I      26   1A    R      27   1B',
            "  B      19   13    B'     32   20",
            "  C      18   12    C'     31   1F",
            "  BC   4882 1312    BC'  8223 201F",
            "  D      30   1E    D'     34   22",
            "  E      29   1D    E'     33   21",
            "  DE   7709 1E1D    DE'  8737 2221",
            "  H      21   15    H'     36   24",
            "  L      20   14    L'     35   23",
            "  HL   5396 1514    HL'  9251 2423",
            "  A      16   10    A'     37   25",
            '    SZ5H3PNC           SZ5H3PNC',
            "  F 00010001        F' 00100110",
            '48K RAM block (16384-65535 4000-FFFF): 49152 bytes (uncompressed)'
        ]
        self._test_z80(exp_output, header, version=1)

    def test_z80v1_compressed(self):
        header = list(range(16, 46))
        header[12] = 42 # BORDER 5, compressed RAM
        exp_output = [
            'Version: 1',
            'Machine: 48K Spectrum',
            'Interrupts: enabled',
            'Interrupt mode: 1',
            'Border: 5',
            'Registers:',
            '  PC   5910 1716    SP   6424 1918',
            '  IX  10793 2A29    IY  10279 2827',
            '  I      26   1A    R      27   1B',
            "  B      19   13    B'     32   20",
            "  C      18   12    C'     31   1F",
            "  BC   4882 1312    BC'  8223 201F",
            "  D      30   1E    D'     34   22",
            "  E      29   1D    E'     33   21",
            "  DE   7709 1E1D    DE'  8737 2221",
            "  H      21   15    H'     36   24",
            "  L      20   14    L'     35   23",
            "  HL   5396 1514    HL'  9251 2423",
            "  A      16   10    A'     37   25",
            '    SZ5H3PNC           SZ5H3PNC',
            "  F 00010001        F' 00100110",
            '48K RAM block (16384-65535 4000-FFFF): 776 bytes (compressed)'
        ]
        self._test_z80(exp_output, header, version=1, compress=True)

    def test_z80v2_48k_uncompressed(self):
        header = list(range(30))
        header[6:8] = [0, 0] # Version 2+
        header[12] = 8 # BORDER 4
        header.extend((23, 0)) # Remaining header length (version 2)
        header.extend((173, 222)) # PC=57005
        header.extend([0] * (header[-4] - 2))
        exp_output = [
            'Version: 2',
            'Machine: 48K Spectrum',
            'Interrupts: enabled',
            'Interrupt mode: 1',
            'Border: 4',
            'Registers:',
            '  PC  57005 DEAD    SP   2312 0908',
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
        self._test_z80(exp_output, header, version=2)

    def test_z80v2_48k_compressed(self):
        header = list(range(30))
        header[6:8] = [0, 0] # Version 2+
        header[12] = 10 # BORDER 5
        header.extend((23, 0)) # Remaining header length (version 2)
        header.extend((239, 190)) # PC=48879
        header.extend([0] * (header[-4] - 2))
        exp_output = [
            'Version: 2',
            'Machine: 48K Spectrum',
            'Interrupts: enabled',
            'Interrupt mode: 1',
            'Border: 5',
            'Registers:',
            '  PC  48879 BEEF    SP   2312 0908',
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
            'RAM block 4 (32768-49151 8000-BFFF): 260 bytes (compressed)',
            'RAM block 5 (49152-65535 C000-FFFF): 260 bytes (compressed)',
            'RAM block 8 (16384-32767 4000-7FFF): 260 bytes (compressed)'
        ]
        self._test_z80(exp_output, header, version=2, compress=True)

    def test_z80v3_48k_uncompressed(self):
        header = list(range(30))
        header[6:8] = [0, 0] # Version 2+
        header[12] = 6 # BORDER 3
        header.extend((54, 0)) # Remaining header length (version 3)
        header.extend((206, 250)) # PC=64206
        header += [0] * (header[-4] - 2)
        exp_output = [
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
        self._test_z80(exp_output, header, version=3)

    def test_z80v3_48k_compressed(self):
        header = list(range(48, 78))
        header[6:8] = [0, 0] # Version 2+
        header[12] = 14 # BORDER 7
        header[28] = 0 # Interrupts disabled
        header.extend((54, 0)) # Remaining header length (version 3)
        header.extend((183, 201)) # PC=51639
        header += [0] * (header[-4] - 2)
        exp_output = [
            'Version: 3',
            'Machine: 48K Spectrum',
            'Interrupts: disabled',
            'Interrupt mode: 1',
            'Border: 7',
            'Registers:',
            '  PC  51639 C9B7    SP  14648 3938',
            '  IX  19017 4A49    IY  18503 4847',
            '  I      58   3A    R      59   3B',
            "  B      51   33    B'     64   40",
            "  C      50   32    C'     63   3F",
            "  BC  13106 3332    BC' 16447 403F",
            "  D      62   3E    D'     66   42",
            "  E      61   3D    E'     65   41",
            "  DE  15933 3E3D    DE' 16961 4241",
            "  H      53   35    H'     68   44",
            "  L      52   34    L'     67   43",
            "  HL  13620 3534    HL' 17475 4443",
            "  A      48   30    A'     69   45",
            '    SZ5H3PNC           SZ5H3PNC',
            "  F 00110001        F' 01000110",
            'RAM block 4 (32768-49151 8000-BFFF): 260 bytes (compressed)',
            'RAM block 5 (49152-65535 C000-FFFF): 260 bytes (compressed)',
            'RAM block 8 (16384-32767 4000-7FFF): 260 bytes (compressed)'
        ]
        self._test_z80(exp_output, header, version=3, compress=True)

    def test_z80v3_128k_uncompressed(self):
        header = list(range(32, 62))
        header[6:8] = [0, 0] # Version 2+
        header[12] = 8 # BORDER 4
        header.extend((54, 0)) # Remaining header length (version 3)
        header.extend((27, 101)) # PC=25883
        header.append(4) # 128K
        header.append(3) # Port 0x7ffd
        header += [0] * (header[-6] - 4)
        pages = {bank: [0] * 16384 for bank in (1, 3, 4, 6, 7)}
        exp_output = [
            'Version: 3',
            'Machine: 128K Spectrum',
            'Interrupts: enabled',
            'Interrupt mode: 1',
            'Border: 4',
            'Port $7FFD: 3 - bank 3 (block 6) paged into 49152-65535 C000-FFFF',
            'Registers:',
            '  PC  25883 651B    SP  10536 2928',
            '  IX  14905 3A39    IY  14391 3837',
            '  I      42   2A    R      43   2B',
            "  B      35   23    B'     48   30",
            "  C      34   22    C'     47   2F",
            "  BC   8994 2322    BC' 12335 302F",
            "  D      46   2E    D'     50   32",
            "  E      45   2D    E'     49   31",
            "  DE  11821 2E2D    DE' 12849 3231",
            "  H      37   25    H'     52   34",
            "  L      36   24    L'     51   33",
            "  HL   9508 2524    HL' 13363 3433",
            "  A      32   20    A'     53   35",
            '    SZ5H3PNC           SZ5H3PNC',
            "  F 00100001        F' 00110110",
            'RAM block 3: 16384 bytes (uncompressed)',
            'RAM block 4: 16384 bytes (uncompressed)',
            'RAM block 5 (32768-49151 8000-BFFF): 16384 bytes (uncompressed)',
            'RAM block 6 (49152-65535 C000-FFFF): 16384 bytes (uncompressed)',
            'RAM block 7: 16384 bytes (uncompressed)',
            'RAM block 8 (16384-32767 4000-7FFF): 16384 bytes (uncompressed)',
            'RAM block 9: 16384 bytes (uncompressed)',
            'RAM block 10: 16384 bytes (uncompressed)'
        ]
        self._test_z80(exp_output, header, compress=False, machine_id=4, pages=pages)

    def test_z80v3_128k_compressed(self):
        header = list(range(32, 62))
        header[6:8] = [0, 0] # Version 2+
        header[12] = 14 # BORDER 7
        header.extend((54, 0)) # Remaining header length (version 3)
        header.extend((237, 254)) # PC=65261
        header.append(4) # 128K
        header.append(3) # Port 0x7ffd
        header += [0] * (header[-6] - 4)
        pages = {bank: [0] * 16384 for bank in (1, 3, 4, 6, 7)}
        exp_output = [
            'Version: 3',
            'Machine: 128K Spectrum',
            'Interrupts: enabled',
            'Interrupt mode: 1',
            'Border: 7',
            'Port $7FFD: 3 - bank 3 (block 6) paged into 49152-65535 C000-FFFF',
            'Registers:',
            '  PC  65261 FEED    SP  10536 2928',
            '  IX  14905 3A39    IY  14391 3837',
            '  I      42   2A    R      43   2B',
            "  B      35   23    B'     48   30",
            "  C      34   22    C'     47   2F",
            "  BC   8994 2322    BC' 12335 302F",
            "  D      46   2E    D'     50   32",
            "  E      45   2D    E'     49   31",
            "  DE  11821 2E2D    DE' 12849 3231",
            "  H      37   25    H'     52   34",
            "  L      36   24    L'     51   33",
            "  HL   9508 2524    HL' 13363 3433",
            "  A      32   20    A'     53   35",
            '    SZ5H3PNC           SZ5H3PNC',
            "  F 00100001        F' 00110110",
            'RAM block 3: 260 bytes (compressed)',
            'RAM block 4: 260 bytes (compressed)',
            'RAM block 5 (32768-49151 8000-BFFF): 260 bytes (compressed)',
            'RAM block 6 (49152-65535 C000-FFFF): 260 bytes (compressed)',
            'RAM block 7: 260 bytes (compressed)',
            'RAM block 8 (16384-32767 4000-7FFF): 260 bytes (compressed)',
            'RAM block 9: 260 bytes (compressed)',
            'RAM block 10: 260 bytes (compressed)'
        ]
        self._test_z80(exp_output, header, compress=True, machine_id=4, pages=pages)

    def test_szx_16k_uncompressed(self):
        registers = list(range(32, 58)) # Registers
        registers.extend((0, 0)) # IFF1, IFF2
        registers.append(1) # Interrupt mode
        registers.extend((0, 0, 0, 0, 0, 0, 0, 0))
        exp_output = [
            'Version: 1.4',
            'Machine: 16K ZX Spectrum',
            'SPCR: 8 bytes',
            '  Border: 1',
            '  Port $7FFD: 0 (bank 0 paged into 49152-65535 C000-FFFF)',
            'Z80R: 37 bytes',
            '  Interrupts: disabled',
            '  Interrupt mode: 1',
            '  PC  14134 3736    SP  13620 3534',
            '  IX  12592 3130    IY  13106 3332',
            '  I      56   38    R      57   39',
            "  B      35   23    B'     43   2B",
            "  C      34   22    C'     42   2A",
            "  BC   8994 2322    BC' 11050 2B2A",
            "  D      37   25    D'     45   2D",
            "  E      36   24    E'     44   2C",
            "  DE   9508 2524    DE' 11564 2D2C",
            "  H      39   27    H'     47   2F",
            "  L      38   26    L'     46   2E",
            "  HL  10022 2726    HL' 12078 2F2E",
            "  A      33   21    A'     41   29",
            '    SZ5H3PNC           SZ5H3PNC',
            "  F 00100000        F' 00101000",
            'RAMP: 16387 bytes',
            '  Page: 5',
            '  RAM: 16384-32767 4000-7FFF: 16384 bytes, uncompressed'
        ]
        self._test_szx(exp_output, registers, border=1, compress=False, machine_id=0)

    def test_szx_16k_compressed(self):
        registers = list(range(32, 58)) # Registers
        registers.extend((0, 0)) # IFF1, IFF2
        registers.append(1) # Interrupt mode
        registers.extend((0, 0, 0, 0, 0, 0, 0, 0))
        exp_output = [
            'Version: 1.4',
            'Machine: 16K ZX Spectrum',
            'SPCR: 8 bytes',
            '  Border: 2',
            '  Port $7FFD: 0 (bank 0 paged into 49152-65535 C000-FFFF)',
            'Z80R: 37 bytes',
            '  Interrupts: disabled',
            '  Interrupt mode: 1',
            '  PC  14134 3736    SP  13620 3534',
            '  IX  12592 3130    IY  13106 3332',
            '  I      56   38    R      57   39',
            "  B      35   23    B'     43   2B",
            "  C      34   22    C'     42   2A",
            "  BC   8994 2322    BC' 11050 2B2A",
            "  D      37   25    D'     45   2D",
            "  E      36   24    E'     44   2C",
            "  DE   9508 2524    DE' 11564 2D2C",
            "  H      39   27    H'     47   2F",
            "  L      38   26    L'     46   2E",
            "  HL  10022 2726    HL' 12078 2F2E",
            "  A      33   21    A'     41   29",
            '    SZ5H3PNC           SZ5H3PNC',
            "  F 00100000        F' 00101000",
            'RAMP: 42 bytes',
            '  Page: 5',
            '  RAM: 16384-32767 4000-7FFF: 39 bytes, compressed'
        ]
        self._test_szx(exp_output, registers, border=2, compress=True, machine_id=0)

    def test_szx_48k_uncompressed(self):
        registers = list(range(26)) # Registers
        registers.extend((1, 1)) # IFF1, IFF2
        registers.append(2) # Interrupt mode
        registers.extend((0, 0, 0, 0, 0, 0, 0, 0))
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
        self._test_szx(exp_output, registers, border=3, compress=False)

    def test_szx_48k_compressed(self):
        registers = list(range(26)) # Registers
        registers.extend((1, 1)) # IFF1, IFF2
        registers.append(2) # Interrupt mode
        registers.extend((0, 0, 0, 0, 0, 0, 0, 0))
        exp_output = [
            'Version: 1.4',
            'Machine: 48K ZX Spectrum',
            'SPCR: 8 bytes',
            '  Border: 4',
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
            'RAMP: 42 bytes',
            '  Page: 0',
            '  RAM: 39 bytes, compressed',
            'RAMP: 42 bytes',
            '  Page: 2',
            '  RAM: 32768-49151 8000-BFFF: 39 bytes, compressed',
            'RAMP: 42 bytes',
            '  Page: 5',
            '  RAM: 16384-32767 4000-7FFF: 39 bytes, compressed'
        ]
        self._test_szx(exp_output, registers, border=4, compress=True)

    def test_szx_128k_uncompressed(self):
        registers = list(range(16, 42)) # Registers
        registers.extend((0, 0)) # IFF1, IFF2
        registers.append(1) # Interrupt mode
        registers.extend((0, 0, 0, 0, 0, 0, 0, 0))
        exp_output = [
            'Version: 1.4',
            'Machine: ZX Spectrum 128',
            'SPCR: 8 bytes',
            '  Border: 6',
            '  Port $7FFD: 1 (bank 1 paged into 49152-65535 C000-FFFF)',
            'Z80R: 37 bytes',
            '  Interrupts: disabled',
            '  Interrupt mode: 1',
            '  PC  10022 2726    SP   9508 2524',
            '  IX   8480 2120    IY   8994 2322',
            '  I      40   28    R      41   29',
            "  B      19   13    B'     27   1B",
            "  C      18   12    C'     26   1A",
            "  BC   4882 1312    BC'  6938 1B1A",
            "  D      21   15    D'     29   1D",
            "  E      20   14    E'     28   1C",
            "  DE   5396 1514    DE'  7452 1D1C",
            "  H      23   17    H'     31   1F",
            "  L      22   16    L'     30   1E",
            "  HL   5910 1716    HL'  7966 1F1E",
            "  A      17   11    A'     25   19",
            '    SZ5H3PNC           SZ5H3PNC',
            "  F 00010000        F' 00011000",
            'RAMP: 16387 bytes',
            '  Page: 0',
            '  RAM: 16384 bytes, uncompressed',
            'RAMP: 16387 bytes',
            '  Page: 1',
            '  RAM: 49152-65535 C000-FFFF: 16384 bytes, uncompressed',
            'RAMP: 16387 bytes',
            '  Page: 2',
            '  RAM: 32768-49151 8000-BFFF: 16384 bytes, uncompressed',
            'RAMP: 16387 bytes',
            '  Page: 3',
            '  RAM: 16384 bytes, uncompressed',
            'RAMP: 16387 bytes',
            '  Page: 4',
            '  RAM: 16384 bytes, uncompressed',
            'RAMP: 16387 bytes',
            '  Page: 5',
            '  RAM: 16384-32767 4000-7FFF: 16384 bytes, uncompressed',
            'RAMP: 16387 bytes',
            '  Page: 6',
            '  RAM: 16384 bytes, uncompressed',
            'RAMP: 16387 bytes',
            '  Page: 7',
            '  RAM: 16384 bytes, uncompressed'
        ]
        self._test_szx(exp_output, registers, border=6, compress=False, machine_id=2, ch7ffd=1, pages=None)

    def test_szx_128k_compressed(self):
        registers = list(range(16, 42)) # Registers
        registers.extend((0, 0)) # IFF1, IFF2
        registers.append(1) # Interrupt mode
        registers.extend((0, 0, 0, 0, 0, 0, 0, 0))
        exp_output = [
            'Version: 1.4',
            'Machine: ZX Spectrum 128',
            'SPCR: 8 bytes',
            '  Border: 7',
            '  Port $7FFD: 1 (bank 1 paged into 49152-65535 C000-FFFF)',
            'Z80R: 37 bytes',
            '  Interrupts: disabled',
            '  Interrupt mode: 1',
            '  PC  10022 2726    SP   9508 2524',
            '  IX   8480 2120    IY   8994 2322',
            '  I      40   28    R      41   29',
            "  B      19   13    B'     27   1B",
            "  C      18   12    C'     26   1A",
            "  BC   4882 1312    BC'  6938 1B1A",
            "  D      21   15    D'     29   1D",
            "  E      20   14    E'     28   1C",
            "  DE   5396 1514    DE'  7452 1D1C",
            "  H      23   17    H'     31   1F",
            "  L      22   16    L'     30   1E",
            "  HL   5910 1716    HL'  7966 1F1E",
            "  A      17   11    A'     25   19",
            '    SZ5H3PNC           SZ5H3PNC',
            "  F 00010000        F' 00011000",
            'RAMP: 42 bytes',
            '  Page: 0',
            '  RAM: 39 bytes, compressed',
            'RAMP: 42 bytes',
            '  Page: 1',
            '  RAM: 49152-65535 C000-FFFF: 39 bytes, compressed',
            'RAMP: 42 bytes',
            '  Page: 2',
            '  RAM: 32768-49151 8000-BFFF: 39 bytes, compressed',
            'RAMP: 42 bytes',
            '  Page: 3',
            '  RAM: 39 bytes, compressed',
            'RAMP: 42 bytes',
            '  Page: 4',
            '  RAM: 39 bytes, compressed',
            'RAMP: 42 bytes',
            '  Page: 5',
            '  RAM: 16384-32767 4000-7FFF: 39 bytes, compressed',
            'RAMP: 42 bytes',
            '  Page: 6',
            '  RAM: 39 bytes, compressed',
            'RAMP: 42 bytes',
            '  Page: 7',
            '  RAM: 39 bytes, compressed'
        ]
        self._test_szx(exp_output, registers, border=7, compress=True, machine_id=2, ch7ffd=1, pages=None)

    def test_szx_without_magic_number(self):
        non_szx = self.write_bin_file((1, 2, 3), suffix='.szx')
        with self.assertRaisesRegexp(SkoolKitError, '{} is not an SZX file$'.format(non_szx)):
            self.run_snapinfo(non_szx)

    @patch.object(snapinfo, 'BasicLister', MockBasicLister)
    def test_option_b(self):
        ram = [127] * 49152
        snafile = self.write_bin_file([0] * 27 + ram, suffix='.sna')
        exp_snapshot = [0] * 16384 + ram
        for option in ('-b', '--basic'):
            output, error = self.run_snapinfo('{} {}'.format(option, snafile))
            self.assertEqual(error, '')
            self.assertEqual(['DONE!'], output)
            self.assertEqual(exp_snapshot, mock_basic_lister.snapshot)
            mock_basic_lister.snapshot = None

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

    def test_option_f_with_hexadecimal_values(self):
        ram = [0] * 49152
        address = 47983
        seq = (0x02, 0x3f, 0x5a)
        step = 0x1a
        ram[address - 16384:address - 16384 + step * len(seq):step] = seq
        seq_str = ','.join(['${:02X}'.format(b) for b in seq])
        exp_output = ['47983-48035-26 BB6F-BBA3-1A: {}'.format(seq_str)]
        self._test_sna(ram, exp_output, '-f {}-${:02x}'.format(seq_str, step))

    def test_option_find_with_nonexistent_byte_sequence(self):
        ram = [0] * 49152
        exp_output = []
        self._test_sna(ram, exp_output, '--find 1,2,3')

    def test_option_find_with_invalid_byte_sequence(self):
        exp_error = 'Invalid byte sequence'
        self._test_bad_spec('--find', 'z', exp_error)
        self._test_bad_spec('-f', '1,!', exp_error)
        self._test_bad_spec('--find', '1,2,?', exp_error)
        self._test_bad_spec('-f', '1,,3', exp_error)

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

    def test_option_p_with_hexadecimal_values(self):
        ram = [0] * 49152
        address1 = 0x81ad
        address2 = 0x81c1
        step = 0x0a
        ram[address1 - 16384:address2 -16383:step] = [33, 65, 255]
        exp_output = [
            '33197 81AD:  33  21  00100001  !',
            '33207 81B7:  65  41  01000001  A',
            '33217 81C1: 255  FF  11111111'
        ]
        self._test_sna(ram, exp_output, '-p ${:04X}-${:04x}-${:X}'.format(address1, address2, step))

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

    def test_option_peek_with_invalid_address_range(self):
        exp_error = 'Invalid address range'
        self._test_bad_spec('--peek', 'X', exp_error)
        self._test_bad_spec('-p', '32768-?', exp_error)
        self._test_bad_spec('--peek', '32768-32868-q', exp_error)
        self._test_bad_spec('-p', '32768-32868-2-3', exp_error)

    def test_option_t_with_single_occurrence(self):
        ram = [0] * 49152
        text = 'foo'
        address = 43567
        ram[address - 16384:address - 16384 + len(text)] = [ord(c) for c in text]
        exp_output = ['{0}-{1} {0:04X}-{1:04X}: {2}'.format(address, address + len(text) - 1, text)]
        self._test_sna(ram, exp_output, '-t {}'.format(text))

    def test_option_find_text_with_multiple_occurrences(self):
        ram = [0] * 49152
        text = 'bar'
        text_bin = [ord(c) for c in text]
        addresses = (32536, 43567, 61437)
        exp_output = []
        for a in addresses:
            ram[a - 16384:a - 16384 + len(text)] = text_bin
            exp_output.append('{0}-{1} {0:04X}-{1:04X}: {2}'.format(a, a + len(text) - 1, text))
        self._test_sna(ram, exp_output, '--find-text {}'.format(text))

    def test_option_t_with_no_occurrences(self):
        ram = [0] * 49152
        exp_output = []
        self._test_sna(ram, exp_output, '-t nowhere')

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_snapinfo(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

if __name__ == '__main__':
    unittest.main()
