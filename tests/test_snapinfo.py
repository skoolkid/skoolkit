import textwrap
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError, snapinfo, VERSION

class MockBasicLister:
    def list_basic(self, snapshot):
        global mock_basic_lister
        mock_basic_lister = self
        self.snapshot = snapshot
        return 'BASIC DONE!'

class MockVariableLister:
    def list_variables(self, snapshot):
        global mock_variable_lister
        mock_variable_lister = self
        self.snapshot = snapshot
        return 'VARIABLES DONE!'

class SnapinfoTest(SkoolKitTestCase):
    def _test_sna(self, ram, exp_output, options='', header=None):
        if header is None:
            header = [0] * 27
        snafile = self.write_bin_file(header + ram, suffix='.sna')
        output, error = self.run_snapinfo(' '.join((options, snafile)))
        self.assertEqual(error, '')
        self.assertEqual(textwrap.dedent(exp_output).strip(), output.rstrip())

    def _test_z80(self, exp_output, header=None, ram=None, version=3, compress=False, machine_id=0, pages=None):
        if ram is None:
            ram = [0] * 49152
        z80file = self.write_z80_file(header, ram, version, compress, machine_id, pages or {})
        output, error = self.run_snapinfo(z80file)
        self.assertEqual(error, '')
        self.assertEqual('Z80 file: {}{}'.format(z80file, textwrap.dedent(exp_output)), output)

    def _test_szx(self, exp_output, registers=None, border=0, ram=None, compress=False, machine_id=1, ch7ffd=0, pages=None):
        if ram is None:
            ram = [0] * 49152
        if machine_id > 1 and pages is None:
            bank = (0,) * 16384
            pages = {p: bank for p in (1, 3, 4, 6, 7)}
        szxfile = self.write_szx(ram, compress, machine_id, ch7ffd, pages, registers, border)
        output, error = self.run_snapinfo(szxfile)
        self.assertEqual(error, '')
        self.assertEqual(textwrap.dedent(exp_output).lstrip(), output)

    def _test_bad_spec(self, option, bad_spec, exp_error, add_spec=True):
        snafile = self.write_bin_file((0,) * 49179, suffix='.sna')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_snapinfo('{} {} {}'.format(option, bad_spec, snafile))
        if add_spec:
            self.assertEqual(cm.exception.args[0], '{}: {}'.format(exp_error, bad_spec))
        else:
            self.assertEqual(cm.exception.args[0], exp_error)

    def test_no_arguments(self):
        output, error = self.run_snapinfo(catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: snapinfo.py'))

    def test_invalid_option(self):
        output, error = self.run_snapinfo('-x test.z80', catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: snapinfo.py'))

    def test_unrecognised_snapshot_type(self):
        with self.assertRaisesRegex(SkoolKitError, 'Unrecognised snapshot type$'):
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
        exp_output = """
            RAM: 48K
            Interrupts: enabled
            Interrupt mode: 1
            Border: 2
            Registers:
              PC  32768 8000    SP  16384 4000
              IX   4625 1211    IY   4111 100F
              I       0   00    R      20   14
              B      14   0E    B'      6   06
              C      13   0D    C'      5   05
              BC   3597 0E0D    BC'  1541 0605
              D      12   0C    D'      4   04
              E      11   0B    E'      3   03
              DE   3083 0C0B    DE'  1027 0403
              H      10   0A    H'      2   02
              L       9   09    L'      1   01
              HL   2569 0A09    HL'   513 0201
              A      22   16    A'      8   08
                SZ5H3PNC           SZ5H3PNC
              F 00010101        F' 00000111
        """
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
        exp_output = """
            RAM: 128K
            Interrupts: disabled
            Interrupt mode: 2
            Border: 4
            Registers:
              PC  24576 6000    SP   6167 1817
              IX   4625 1211    IY   4111 100F
              I       0   00    R      20   14
              B      14   0E    B'      6   06
              C      13   0D    C'      5   05
              BC   3597 0E0D    BC'  1541 0605
              D      12   0C    D'      4   04
              E      11   0B    E'      3   03
              DE   3083 0C0B    DE'  1027 0403
              H      10   0A    H'      2   02
              L       9   09    L'      1   01
              HL   2569 0A09    HL'   513 0201
              A      22   16    A'      8   08
                SZ5H3PNC           SZ5H3PNC
              F 00010101        F' 00000111
            RAM bank 5 (16384 bytes: 16384-32767 4000-7FFF)
            RAM bank 2 (16384 bytes: 32768-49151 8000-BFFF)
            RAM bank 1 (16384 bytes: 49152-65535 C000-FFFF)
            RAM bank 0 (16384 bytes)
            RAM bank 3 (16384 bytes)
            RAM bank 4 (16384 bytes)
            RAM bank 6 (16384 bytes)
            RAM bank 7 (16384 bytes)
        """

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
        exp_output = """
            RAM: 128K
            Interrupts: disabled
            Interrupt mode: 1
            Border: 5
            Registers:
              PC  24576 6000    SP   6167 1817
              IX   4625 1211    IY   4111 100F
              I       0   00    R      20   14
              B      14   0E    B'      6   06
              C      13   0D    C'      5   05
              BC   3597 0E0D    BC'  1541 0605
              D      12   0C    D'      4   04
              E      11   0B    E'      3   03
              DE   3083 0C0B    DE'  1027 0403
              H      10   0A    H'      2   02
              L       9   09    L'      1   01
              HL   2569 0A09    HL'   513 0201
              A      22   16    A'      8   08
                SZ5H3PNC           SZ5H3PNC
              F 00010101        F' 00000111
            RAM bank 5 (16384 bytes: 16384-32767 4000-7FFF)
            RAM bank 2 (16384 bytes: 32768-49151 8000-BFFF)
            RAM bank 2 (16384 bytes: 49152-65535 C000-FFFF)
            RAM bank 0 (16384 bytes)
            RAM bank 1 (16384 bytes)
            RAM bank 3 (16384 bytes)
            RAM bank 4 (16384 bytes)
            RAM bank 6 (16384 bytes)
            RAM bank 7 (16384 bytes)
        """
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
        exp_output = """
            Version: 1
            Machine: 48K Spectrum
            Interrupts: enabled
            Interrupt mode: 1
            Border: 6
            Registers:
              PC   5910 1716    SP   6424 1918
              IX  10793 2A29    IY  10279 2827
              I      26   1A    R      27   1B
              B      19   13    B'     32   20
              C      18   12    C'     31   1F
              BC   4882 1312    BC'  8223 201F
              D      30   1E    D'     34   22
              E      29   1D    E'     33   21
              DE   7709 1E1D    DE'  8737 2221
              H      21   15    H'     36   24
              L      20   14    L'     35   23
              HL   5396 1514    HL'  9251 2423
              A      16   10    A'     37   25
                SZ5H3PNC           SZ5H3PNC
              F 00010001        F' 00100110
            48K RAM block (16384-65535 4000-FFFF): 49152 bytes (uncompressed)
        """
        self._test_z80(exp_output, header, version=1)

    def test_z80v1_compressed(self):
        header = list(range(16, 46))
        header[12] = 42 # BORDER 5, compressed RAM
        exp_output = """
            Version: 1
            Machine: 48K Spectrum
            Interrupts: enabled
            Interrupt mode: 1
            Border: 5
            Registers:
              PC   5910 1716    SP   6424 1918
              IX  10793 2A29    IY  10279 2827
              I      26   1A    R      27   1B
              B      19   13    B'     32   20
              C      18   12    C'     31   1F
              BC   4882 1312    BC'  8223 201F
              D      30   1E    D'     34   22
              E      29   1D    E'     33   21
              DE   7709 1E1D    DE'  8737 2221
              H      21   15    H'     36   24
              L      20   14    L'     35   23
              HL   5396 1514    HL'  9251 2423
              A      16   10    A'     37   25
                SZ5H3PNC           SZ5H3PNC
              F 00010001        F' 00100110
            48K RAM block (16384-65535 4000-FFFF): 776 bytes (compressed)
        """
        self._test_z80(exp_output, header, version=1, compress=True)

    def test_z80v2_48k_uncompressed(self):
        header = list(range(30))
        header[6:8] = [0, 0] # Version 2+
        header[12] = 8 # BORDER 4
        header.extend((23, 0)) # Remaining header length (version 2)
        header.extend((173, 222)) # PC=57005
        header.extend([0] * (header[-4] - 2))
        exp_output = """
            Version: 2
            Machine: 48K Spectrum
            Interrupts: enabled
            Interrupt mode: 1
            Border: 4
            Registers:
              PC  57005 DEAD    SP   2312 0908
              IX   6681 1A19    IY   6167 1817
              I      10   0A    R      11   0B
              B       3   03    B'     16   10
              C       2   02    C'     15   0F
              BC    770 0302    BC'  4111 100F
              D      14   0E    D'     18   12
              E      13   0D    E'     17   11
              DE   3597 0E0D    DE'  4625 1211
              H       5   05    H'     20   14
              L       4   04    L'     19   13
              HL   1284 0504    HL'  5139 1413
              A       0   00    A'     21   15
                SZ5H3PNC           SZ5H3PNC
              F 00000001        F' 00010110
            RAM block 4 (32768-49151 8000-BFFF): 16384 bytes (uncompressed)
            RAM block 5 (49152-65535 C000-FFFF): 16384 bytes (uncompressed)
            RAM block 8 (16384-32767 4000-7FFF): 16384 bytes (uncompressed)
        """
        self._test_z80(exp_output, header, version=2)

    def test_z80v2_48k_compressed(self):
        header = list(range(30))
        header[6:8] = [0, 0] # Version 2+
        header[12] = 10 # BORDER 5
        header.extend((23, 0)) # Remaining header length (version 2)
        header.extend((239, 190)) # PC=48879
        header.extend([0] * (header[-4] - 2))
        exp_output = """
            Version: 2
            Machine: 48K Spectrum
            Interrupts: enabled
            Interrupt mode: 1
            Border: 5
            Registers:
              PC  48879 BEEF    SP   2312 0908
              IX   6681 1A19    IY   6167 1817
              I      10   0A    R      11   0B
              B       3   03    B'     16   10
              C       2   02    C'     15   0F
              BC    770 0302    BC'  4111 100F
              D      14   0E    D'     18   12
              E      13   0D    E'     17   11
              DE   3597 0E0D    DE'  4625 1211
              H       5   05    H'     20   14
              L       4   04    L'     19   13
              HL   1284 0504    HL'  5139 1413
              A       0   00    A'     21   15
                SZ5H3PNC           SZ5H3PNC
              F 00000001        F' 00010110
            RAM block 4 (32768-49151 8000-BFFF): 260 bytes (compressed)
            RAM block 5 (49152-65535 C000-FFFF): 260 bytes (compressed)
            RAM block 8 (16384-32767 4000-7FFF): 260 bytes (compressed)
        """
        self._test_z80(exp_output, header, version=2, compress=True)

    def test_z80v3_48k_uncompressed(self):
        header = list(range(30))
        header[6:8] = [0, 0] # Version 2+
        header[12] = 6 # BORDER 3
        header.extend((54, 0)) # Remaining header length (version 3)
        header.extend((206, 250)) # PC=64206
        header += [0] * (header[-4] - 2)
        exp_output = """
            Version: 3
            Machine: 48K Spectrum
            Interrupts: enabled
            Interrupt mode: 1
            Border: 3
            Registers:
              PC  64206 FACE    SP   2312 0908
              IX   6681 1A19    IY   6167 1817
              I      10   0A    R      11   0B
              B       3   03    B'     16   10
              C       2   02    C'     15   0F
              BC    770 0302    BC'  4111 100F
              D      14   0E    D'     18   12
              E      13   0D    E'     17   11
              DE   3597 0E0D    DE'  4625 1211
              H       5   05    H'     20   14
              L       4   04    L'     19   13
              HL   1284 0504    HL'  5139 1413
              A       0   00    A'     21   15
                SZ5H3PNC           SZ5H3PNC
              F 00000001        F' 00010110
            RAM block 4 (32768-49151 8000-BFFF): 16384 bytes (uncompressed)
            RAM block 5 (49152-65535 C000-FFFF): 16384 bytes (uncompressed)
            RAM block 8 (16384-32767 4000-7FFF): 16384 bytes (uncompressed)
        """
        self._test_z80(exp_output, header, version=3)

    def test_z80v3_48k_compressed(self):
        header = list(range(48, 78))
        header[6:8] = [0, 0] # Version 2+
        header[12] = 14 # BORDER 7
        header[28] = 0 # Interrupts disabled
        header.extend((54, 0)) # Remaining header length (version 3)
        header.extend((183, 201)) # PC=51639
        header += [0] * (header[-4] - 2)
        exp_output = """
            Version: 3
            Machine: 48K Spectrum
            Interrupts: disabled
            Interrupt mode: 1
            Border: 7
            Registers:
              PC  51639 C9B7    SP  14648 3938
              IX  19017 4A49    IY  18503 4847
              I      58   3A    R      59   3B
              B      51   33    B'     64   40
              C      50   32    C'     63   3F
              BC  13106 3332    BC' 16447 403F
              D      62   3E    D'     66   42
              E      61   3D    E'     65   41
              DE  15933 3E3D    DE' 16961 4241
              H      53   35    H'     68   44
              L      52   34    L'     67   43
              HL  13620 3534    HL' 17475 4443
              A      48   30    A'     69   45
                SZ5H3PNC           SZ5H3PNC
              F 00110001        F' 01000110
            RAM block 4 (32768-49151 8000-BFFF): 260 bytes (compressed)
            RAM block 5 (49152-65535 C000-FFFF): 260 bytes (compressed)
            RAM block 8 (16384-32767 4000-7FFF): 260 bytes (compressed)
        """
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
        exp_output = """
            Version: 3
            Machine: 128K Spectrum
            Interrupts: enabled
            Interrupt mode: 1
            Border: 4
            Port $7FFD: 3 - bank 3 (block 6) paged into 49152-65535 C000-FFFF
            Registers:
              PC  25883 651B    SP  10536 2928
              IX  14905 3A39    IY  14391 3837
              I      42   2A    R      43   2B
              B      35   23    B'     48   30
              C      34   22    C'     47   2F
              BC   8994 2322    BC' 12335 302F
              D      46   2E    D'     50   32
              E      45   2D    E'     49   31
              DE  11821 2E2D    DE' 12849 3231
              H      37   25    H'     52   34
              L      36   24    L'     51   33
              HL   9508 2524    HL' 13363 3433
              A      32   20    A'     53   35
                SZ5H3PNC           SZ5H3PNC
              F 00100001        F' 00110110
            RAM block 3: 16384 bytes (uncompressed)
            RAM block 4: 16384 bytes (uncompressed)
            RAM block 5 (32768-49151 8000-BFFF): 16384 bytes (uncompressed)
            RAM block 6 (49152-65535 C000-FFFF): 16384 bytes (uncompressed)
            RAM block 7: 16384 bytes (uncompressed)
            RAM block 8 (16384-32767 4000-7FFF): 16384 bytes (uncompressed)
            RAM block 9: 16384 bytes (uncompressed)
            RAM block 10: 16384 bytes (uncompressed)
        """
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
        exp_output = """
            Version: 3
            Machine: 128K Spectrum
            Interrupts: enabled
            Interrupt mode: 1
            Border: 7
            Port $7FFD: 3 - bank 3 (block 6) paged into 49152-65535 C000-FFFF
            Registers:
              PC  65261 FEED    SP  10536 2928
              IX  14905 3A39    IY  14391 3837
              I      42   2A    R      43   2B
              B      35   23    B'     48   30
              C      34   22    C'     47   2F
              BC   8994 2322    BC' 12335 302F
              D      46   2E    D'     50   32
              E      45   2D    E'     49   31
              DE  11821 2E2D    DE' 12849 3231
              H      37   25    H'     52   34
              L      36   24    L'     51   33
              HL   9508 2524    HL' 13363 3433
              A      32   20    A'     53   35
                SZ5H3PNC           SZ5H3PNC
              F 00100001        F' 00110110
            RAM block 3: 260 bytes (compressed)
            RAM block 4: 260 bytes (compressed)
            RAM block 5 (32768-49151 8000-BFFF): 260 bytes (compressed)
            RAM block 6 (49152-65535 C000-FFFF): 260 bytes (compressed)
            RAM block 7: 260 bytes (compressed)
            RAM block 8 (16384-32767 4000-7FFF): 260 bytes (compressed)
            RAM block 9: 260 bytes (compressed)
            RAM block 10: 260 bytes (compressed)
        """
        self._test_z80(exp_output, header, compress=True, machine_id=4, pages=pages)

    def test_szx_16k_uncompressed(self):
        registers = list(range(32, 58)) # Registers
        registers.extend((0, 0)) # IFF1, IFF2
        registers.append(1) # Interrupt mode
        registers.extend((0, 0, 0, 0, 0, 0, 0, 0))
        exp_output = """
            Version: 1.4
            Machine: 16K ZX Spectrum
            SPCR: 8 bytes
              Border: 1
              Port $7FFD: 0 (bank 0 paged into 49152-65535 C000-FFFF)
            Z80R: 37 bytes
              Interrupts: disabled
              Interrupt mode: 1
              PC  14134 3736    SP  13620 3534
              IX  12592 3130    IY  13106 3332
              I      56   38    R      57   39
              B      35   23    B'     43   2B
              C      34   22    C'     42   2A
              BC   8994 2322    BC' 11050 2B2A
              D      37   25    D'     45   2D
              E      36   24    E'     44   2C
              DE   9508 2524    DE' 11564 2D2C
              H      39   27    H'     47   2F
              L      38   26    L'     46   2E
              HL  10022 2726    HL' 12078 2F2E
              A      33   21    A'     41   29
                SZ5H3PNC           SZ5H3PNC
              F 00100000        F' 00101000
            RAMP: 16387 bytes
              Page: 5
              RAM: 16384-32767 4000-7FFF: 16384 bytes, uncompressed
        """
        self._test_szx(exp_output, registers, border=1, compress=False, machine_id=0)

    def test_szx_16k_compressed(self):
        registers = list(range(32, 58)) # Registers
        registers.extend((0, 0)) # IFF1, IFF2
        registers.append(1) # Interrupt mode
        registers.extend((0, 0, 0, 0, 0, 0, 0, 0))
        exp_output = """
            Version: 1.4
            Machine: 16K ZX Spectrum
            SPCR: 8 bytes
              Border: 2
              Port $7FFD: 0 (bank 0 paged into 49152-65535 C000-FFFF)
            Z80R: 37 bytes
              Interrupts: disabled
              Interrupt mode: 1
              PC  14134 3736    SP  13620 3534
              IX  12592 3130    IY  13106 3332
              I      56   38    R      57   39
              B      35   23    B'     43   2B
              C      34   22    C'     42   2A
              BC   8994 2322    BC' 11050 2B2A
              D      37   25    D'     45   2D
              E      36   24    E'     44   2C
              DE   9508 2524    DE' 11564 2D2C
              H      39   27    H'     47   2F
              L      38   26    L'     46   2E
              HL  10022 2726    HL' 12078 2F2E
              A      33   21    A'     41   29
                SZ5H3PNC           SZ5H3PNC
              F 00100000        F' 00101000
            RAMP: 42 bytes
              Page: 5
              RAM: 16384-32767 4000-7FFF: 39 bytes, compressed
        """
        self._test_szx(exp_output, registers, border=2, compress=True, machine_id=0)

    def test_szx_48k_uncompressed(self):
        registers = list(range(26)) # Registers
        registers.extend((1, 1)) # IFF1, IFF2
        registers.append(2) # Interrupt mode
        registers.extend((0, 0, 0, 0, 0, 0, 0, 0))
        exp_output = """
            Version: 1.4
            Machine: 48K ZX Spectrum
            SPCR: 8 bytes
              Border: 3
              Port $7FFD: 0 (bank 0 paged into 49152-65535 C000-FFFF)
            Z80R: 37 bytes
              Interrupts: enabled
              Interrupt mode: 2
              PC   5910 1716    SP   5396 1514
              IX   4368 1110    IY   4882 1312
              I      24   18    R      25   19
              B       3   03    B'     11   0B
              C       2   02    C'     10   0A
              BC    770 0302    BC'  2826 0B0A
              D       5   05    D'     13   0D
              E       4   04    E'     12   0C
              DE   1284 0504    DE'  3340 0D0C
              H       7   07    H'     15   0F
              L       6   06    L'     14   0E
              HL   1798 0706    HL'  3854 0F0E
              A       1   01    A'      9   09
                SZ5H3PNC           SZ5H3PNC
              F 00000000        F' 00001000
            RAMP: 16387 bytes
              Page: 0
              RAM: 16384 bytes, uncompressed
            RAMP: 16387 bytes
              Page: 2
              RAM: 32768-49151 8000-BFFF: 16384 bytes, uncompressed
            RAMP: 16387 bytes
              Page: 5
              RAM: 16384-32767 4000-7FFF: 16384 bytes, uncompressed
        """
        self._test_szx(exp_output, registers, border=3, compress=False)

    def test_szx_48k_compressed(self):
        registers = list(range(26)) # Registers
        registers.extend((1, 1)) # IFF1, IFF2
        registers.append(2) # Interrupt mode
        registers.extend((0, 0, 0, 0, 0, 0, 0, 0))
        exp_output = """
            Version: 1.4
            Machine: 48K ZX Spectrum
            SPCR: 8 bytes
              Border: 4
              Port $7FFD: 0 (bank 0 paged into 49152-65535 C000-FFFF)
            Z80R: 37 bytes
              Interrupts: enabled
              Interrupt mode: 2
              PC   5910 1716    SP   5396 1514
              IX   4368 1110    IY   4882 1312
              I      24   18    R      25   19
              B       3   03    B'     11   0B
              C       2   02    C'     10   0A
              BC    770 0302    BC'  2826 0B0A
              D       5   05    D'     13   0D
              E       4   04    E'     12   0C
              DE   1284 0504    DE'  3340 0D0C
              H       7   07    H'     15   0F
              L       6   06    L'     14   0E
              HL   1798 0706    HL'  3854 0F0E
              A       1   01    A'      9   09
                SZ5H3PNC           SZ5H3PNC
              F 00000000        F' 00001000
            RAMP: 42 bytes
              Page: 0
              RAM: 39 bytes, compressed
            RAMP: 42 bytes
              Page: 2
              RAM: 32768-49151 8000-BFFF: 39 bytes, compressed
            RAMP: 42 bytes
              Page: 5
              RAM: 16384-32767 4000-7FFF: 39 bytes, compressed
        """
        self._test_szx(exp_output, registers, border=4, compress=True)

    def test_szx_128k_uncompressed(self):
        registers = list(range(16, 42)) # Registers
        registers.extend((0, 0)) # IFF1, IFF2
        registers.append(1) # Interrupt mode
        registers.extend((0, 0, 0, 0, 0, 0, 0, 0))
        exp_output = """
            Version: 1.4
            Machine: ZX Spectrum 128
            SPCR: 8 bytes
              Border: 6
              Port $7FFD: 1 (bank 1 paged into 49152-65535 C000-FFFF)
            Z80R: 37 bytes
              Interrupts: disabled
              Interrupt mode: 1
              PC  10022 2726    SP   9508 2524
              IX   8480 2120    IY   8994 2322
              I      40   28    R      41   29
              B      19   13    B'     27   1B
              C      18   12    C'     26   1A
              BC   4882 1312    BC'  6938 1B1A
              D      21   15    D'     29   1D
              E      20   14    E'     28   1C
              DE   5396 1514    DE'  7452 1D1C
              H      23   17    H'     31   1F
              L      22   16    L'     30   1E
              HL   5910 1716    HL'  7966 1F1E
              A      17   11    A'     25   19
                SZ5H3PNC           SZ5H3PNC
              F 00010000        F' 00011000
            RAMP: 16387 bytes
              Page: 0
              RAM: 16384 bytes, uncompressed
            RAMP: 16387 bytes
              Page: 1
              RAM: 49152-65535 C000-FFFF: 16384 bytes, uncompressed
            RAMP: 16387 bytes
              Page: 2
              RAM: 32768-49151 8000-BFFF: 16384 bytes, uncompressed
            RAMP: 16387 bytes
              Page: 3
              RAM: 16384 bytes, uncompressed
            RAMP: 16387 bytes
              Page: 4
              RAM: 16384 bytes, uncompressed
            RAMP: 16387 bytes
              Page: 5
              RAM: 16384-32767 4000-7FFF: 16384 bytes, uncompressed
            RAMP: 16387 bytes
              Page: 6
              RAM: 16384 bytes, uncompressed
            RAMP: 16387 bytes
              Page: 7
              RAM: 16384 bytes, uncompressed
        """
        self._test_szx(exp_output, registers, border=6, compress=False, machine_id=2, ch7ffd=1, pages=None)

    def test_szx_128k_compressed(self):
        registers = list(range(16, 42)) # Registers
        registers.extend((0, 0)) # IFF1, IFF2
        registers.append(1) # Interrupt mode
        registers.extend((0, 0, 0, 0, 0, 0, 0, 0))
        exp_output = """
            Version: 1.4
            Machine: ZX Spectrum 128
            SPCR: 8 bytes
              Border: 7
              Port $7FFD: 1 (bank 1 paged into 49152-65535 C000-FFFF)
            Z80R: 37 bytes
              Interrupts: disabled
              Interrupt mode: 1
              PC  10022 2726    SP   9508 2524
              IX   8480 2120    IY   8994 2322
              I      40   28    R      41   29
              B      19   13    B'     27   1B
              C      18   12    C'     26   1A
              BC   4882 1312    BC'  6938 1B1A
              D      21   15    D'     29   1D
              E      20   14    E'     28   1C
              DE   5396 1514    DE'  7452 1D1C
              H      23   17    H'     31   1F
              L      22   16    L'     30   1E
              HL   5910 1716    HL'  7966 1F1E
              A      17   11    A'     25   19
                SZ5H3PNC           SZ5H3PNC
              F 00010000        F' 00011000
            RAMP: 42 bytes
              Page: 0
              RAM: 39 bytes, compressed
            RAMP: 42 bytes
              Page: 1
              RAM: 49152-65535 C000-FFFF: 39 bytes, compressed
            RAMP: 42 bytes
              Page: 2
              RAM: 32768-49151 8000-BFFF: 39 bytes, compressed
            RAMP: 42 bytes
              Page: 3
              RAM: 39 bytes, compressed
            RAMP: 42 bytes
              Page: 4
              RAM: 39 bytes, compressed
            RAMP: 42 bytes
              Page: 5
              RAM: 16384-32767 4000-7FFF: 39 bytes, compressed
            RAMP: 42 bytes
              Page: 6
              RAM: 39 bytes, compressed
            RAMP: 42 bytes
              Page: 7
              RAM: 39 bytes, compressed
        """
        self._test_szx(exp_output, registers, border=7, compress=True, machine_id=2, ch7ffd=1, pages=None)

    def test_szx_without_magic_number(self):
        non_szx = self.write_bin_file((1, 2, 3), suffix='.szx')
        with self.assertRaisesRegex(SkoolKitError, '{} is not an SZX file$'.format(non_szx)):
            self.run_snapinfo(non_szx)

    @patch.object(snapinfo, 'BasicLister', MockBasicLister)
    def test_option_b(self):
        ram = [127] * 49152
        snafile = self.write_bin_file([0] * 27 + ram, suffix='.sna')
        exp_snapshot = [0] * 16384 + ram
        for option in ('-b', '--basic'):
            output, error = self.run_snapinfo('{} {}'.format(option, snafile))
            self.assertEqual(error, '')
            self.assertEqual('BASIC DONE!\n', output)
            self.assertEqual(exp_snapshot, mock_basic_lister.snapshot)
            mock_basic_lister.snapshot = None

    @patch.object(snapinfo, 'VariableLister', MockVariableLister)
    def test_option_v(self):
        ram = [127] * 49152
        snafile = self.write_bin_file([0] * 27 + ram, suffix='.sna')
        exp_snapshot = [0] * 16384 + ram
        for option in ('-v', '--variables'):
            output, error = self.run_snapinfo('{} {}'.format(option, snafile))
            self.assertEqual(error, '')
            self.assertEqual('VARIABLES DONE!\n', output)
            self.assertEqual(exp_snapshot, mock_variable_lister.snapshot)
            mock_variable_lister.snapshot = None

    @patch.object(snapinfo, 'BasicLister', MockBasicLister)
    @patch.object(snapinfo, 'VariableLister', MockVariableLister)
    def test_options_b_and_v(self):
        ram = [127] * 49152
        snafile = self.write_bin_file([0] * 27 + ram, suffix='.sna')
        exp_snapshot = [0] * 16384 + ram
        for option in ('-bv', '-b --variables', '--basic -v', '--basic --variables'):
            output, error = self.run_snapinfo('{} {}'.format(option, snafile))
            self.assertEqual(error, '')
            self.assertEqual('BASIC DONE!\nVARIABLES DONE!\n', output)
            self.assertEqual(exp_snapshot, mock_basic_lister.snapshot)
            self.assertEqual(exp_snapshot, mock_variable_lister.snapshot)
            mock_basic_lister.snapshot = None
            mock_variable_lister.snapshot = None

    def test_option_f_with_single_byte(self):
        ram = [0] * 49152
        address = 53267
        ram[address - 16384] = 77
        exp_output = '53267-53267-1 D013-D013-1: 77'
        self._test_sna(ram, exp_output, '-f 77')

    def test_option_find_with_byte_sequence(self):
        ram = [0] * 49152
        address = 35674
        seq = (2, 4, 6)
        ram[address - 16384:address - 16384 + len(seq)] = seq
        seq_str = ','.join([str(b) for b in seq])
        exp_output = '35674-35676-1 8B5A-8B5C-1: {}'.format(seq_str)
        self._test_sna(ram, exp_output, '--find {}'.format(seq_str))

    def test_option_f_with_byte_sequence_and_step(self):
        ram = [0] * 49152
        address = 47983
        seq = (2, 3, 5)
        step = 2
        ram[address - 16384:address - 16384 + step * len(seq):step] = seq
        seq_str = ','.join([str(b) for b in seq])
        exp_output = '47983-47987-2 BB6F-BB73-2: {}'.format(seq_str)
        self._test_sna(ram, exp_output, '-f {}-{}'.format(seq_str, step))

    def test_option_f_with_byte_sequence_and_step_range(self):
        ram = [0] * 49152
        addresses = (31783, 42567, 52172)
        seq = (8, 10, 13)
        steps = (2, 3, 4)
        seq_str = ','.join([str(b) for b in seq])
        for addr, step in zip(addresses, steps):
            ram[addr - 16384:addr - 16384 + step * len(seq):step] = seq
        exp_output = """
            31783-31787-2 7C27-7C2B-2: 8,10,13
            42567-42573-3 A647-A64D-3: 8,10,13
            52172-52180-4 CBCC-CBD4-4: 8,10,13
        """
        self._test_sna(ram, exp_output, '-f {}-1-5'.format(seq_str))

    def test_option_f_with_hexadecimal_values(self):
        ram = [0] * 49152
        address = 47983
        seq = (0x02, 0x3f, 0x5a)
        step = 0x1a
        ram[address - 16384:address - 16384 + step * len(seq):step] = seq
        seq_str = ','.join(['${:02X}'.format(b) for b in seq])
        exp_output = '47983-48035-26 BB6F-BBA3-1A: {}'.format(seq_str)
        self._test_sna(ram, exp_output, '-f {}-${:02x}'.format(seq_str, step))

    def test_option_f_with_0x_hexadecimal_values(self):
        ram = [0] * 49152
        address = 47983
        seq = (0x02, 0x3f, 0x5a)
        step = 0x1a
        ram[address - 16384:address - 16384 + step * len(seq):step] = seq
        seq_str = ','.join(['0x{:02X}'.format(b) for b in seq])
        exp_output = '47983-48035-26 BB6F-BBA3-1A: {}'.format(seq_str)
        self._test_sna(ram, exp_output, '-f {}-0x{:02x}-0x{:02x}'.format(seq_str, step, step + 1))

    def test_option_find_with_nonexistent_byte_sequence(self):
        ram = [0] * 49152
        exp_output = ''
        self._test_sna(ram, exp_output, '--find 1,2,3')

    def test_option_find_with_invalid_byte_sequence(self):
        exp_error = 'Invalid byte sequence'
        self._test_bad_spec('--find', 'z', exp_error)
        self._test_bad_spec('-f', '1,!', exp_error)
        self._test_bad_spec('--find', '1,2,?', exp_error)
        self._test_bad_spec('-f', '1,,3', exp_error)

    def test_option_find_with_invalid_step(self):
        exp_error = 'Invalid distance: {}'
        self._test_bad_spec('--find', '1,2,3-x', exp_error.format('x'), False)
        self._test_bad_spec('-f', '4,5,6-1-y', exp_error.format('1-y'), False)
        self._test_bad_spec('--find', '7,8,9-z-5', exp_error.format('z-5'), False)
        self._test_bad_spec('-f', '10,11,12-q-?', exp_error.format('q-?'), False)

    def test_option_p_with_single_address(self):
        ram = [0] * 49152
        address = 31759
        ram[address - 16384] = 47
        exp_output = '31759 7C0F:  47  2F  00101111  /'
        self._test_sna(ram, exp_output, '-p {}'.format(address))

    def test_option_peek_with_address_range(self):
        ram = [0] * 49152
        address1 = 41885
        address2 = 41888
        ram[address1 - 16384:address2 -16383] = list(range(99, 100 + address2 - address1))
        exp_output = """
            41885 A39D:  99  63  01100011  c
            41886 A39E: 100  64  01100100  d
            41887 A39F: 101  65  01100101  e
            41888 A3A0: 102  66  01100110  f
        """
        self._test_sna(ram, exp_output, '--peek {}-{}'.format(address1, address2))

    def test_option_p_with_address_range_and_step(self):
        ram = [0] * 49152
        address1 = 25663
        address2 = 25669
        step = 3
        ram[address1 - 16384:address2 -16383:step] = [33, 65, 126]
        exp_output = """
            25663 643F:  33  21  00100001  !
            25666 6442:  65  41  01000001  A
            25669 6445: 126  7E  01111110  ~
        """
        self._test_sna(ram, exp_output, '-p {}-{}-{}'.format(address1, address2, step))

    def test_option_p_with_hexadecimal_values(self):
        ram = [0] * 49152
        address1 = 0x81ad
        address2 = 0x81c1
        step = 0x0a
        ram[address1 - 16384:address2 -16383:step] = [33, 65, 126]
        exp_output = """
            33197 81AD:  33  21  00100001  !
            33207 81B7:  65  41  01000001  A
            33217 81C1: 126  7E  01111110  ~
        """
        self._test_sna(ram, exp_output, '-p ${:04X}-${:04x}-${:X}'.format(address1, address2, step))

    def test_option_p_with_0x_hexadecimal_values(self):
        ram = [0] * 49152
        address1 = 0x81ad
        address2 = 0x81c1
        step = 0x0a
        ram[address1 - 16384:address2 -16383:step] = [33, 65, 126]
        exp_output = """
            33197 81AD:  33  21  00100001  !
            33207 81B7:  65  41  01000001  A
            33217 81C1: 126  7E  01111110  ~
        """
        self._test_sna(ram, exp_output, '-p 0x{:04X}-0x{:04x}-0x{:X}'.format(address1, address2, step))

    def test_option_peek_multiple(self):
        ram = [0] * 49152
        options = []
        addresses = (33333, 44173, 50998)
        for a in addresses:
            ram[a - 16384] = a % 256
            options.append('--peek {}'.format(a))
        exp_output = '\n'.join((
            '33333 8235:  53  35  00110101  5',
            '44173 AC8D: 141  8D  10001101  ',
            '50998 C736:  54  36  00110110  6'
        ))
        self._test_sna(ram, exp_output, ' '.join(options))

    def test_option_p_with_udgs(self):
        ram = [0] * 49152
        address = 61892
        udgs = list(range(144, 165))
        ram[address - 16384:address - 16384 + len(udgs)] = udgs
        exp_output = """
            61892 F1C4: 144  90  10010000  UDG-A
            61893 F1C5: 145  91  10010001  UDG-B
            61894 F1C6: 146  92  10010010  UDG-C
            61895 F1C7: 147  93  10010011  UDG-D
            61896 F1C8: 148  94  10010100  UDG-E
            61897 F1C9: 149  95  10010101  UDG-F
            61898 F1CA: 150  96  10010110  UDG-G
            61899 F1CB: 151  97  10010111  UDG-H
            61900 F1CC: 152  98  10011000  UDG-I
            61901 F1CD: 153  99  10011001  UDG-J
            61902 F1CE: 154  9A  10011010  UDG-K
            61903 F1CF: 155  9B  10011011  UDG-L
            61904 F1D0: 156  9C  10011100  UDG-M
            61905 F1D1: 157  9D  10011101  UDG-N
            61906 F1D2: 158  9E  10011110  UDG-O
            61907 F1D3: 159  9F  10011111  UDG-P
            61908 F1D4: 160  A0  10100000  UDG-Q
            61909 F1D5: 161  A1  10100001  UDG-R
            61910 F1D6: 162  A2  10100010  UDG-S
            61911 F1D7: 163  A3  10100011  UDG-T
            61912 F1D8: 164  A4  10100100  UDG-U
        """
        self._test_sna(ram, exp_output, '-p {}-{}'.format(address, address + len(udgs) - 1))

    def test_option_peek_with_basic_tokens(self):
        ram = [0] * 49152
        address = 42152
        tokens = list(range(165, 256))
        ram[address - 16384:address - 16384 + len(tokens)] = tokens
        exp_output = """
            42152 A4A8: 165  A5  10100101  RND
            42153 A4A9: 166  A6  10100110  INKEY$
            42154 A4AA: 167  A7  10100111  PI
            42155 A4AB: 168  A8  10101000  FN
            42156 A4AC: 169  A9  10101001  POINT
            42157 A4AD: 170  AA  10101010  SCREEN$
            42158 A4AE: 171  AB  10101011  ATTR
            42159 A4AF: 172  AC  10101100  AT
            42160 A4B0: 173  AD  10101101  TAB
            42161 A4B1: 174  AE  10101110  VAL$
            42162 A4B2: 175  AF  10101111  CODE
            42163 A4B3: 176  B0  10110000  VAL
            42164 A4B4: 177  B1  10110001  LEN
            42165 A4B5: 178  B2  10110010  SIN
            42166 A4B6: 179  B3  10110011  COS
            42167 A4B7: 180  B4  10110100  TAN
            42168 A4B8: 181  B5  10110101  ASN
            42169 A4B9: 182  B6  10110110  ACS
            42170 A4BA: 183  B7  10110111  ATN
            42171 A4BB: 184  B8  10111000  LN
            42172 A4BC: 185  B9  10111001  EXP
            42173 A4BD: 186  BA  10111010  INT
            42174 A4BE: 187  BB  10111011  SQR
            42175 A4BF: 188  BC  10111100  SGN
            42176 A4C0: 189  BD  10111101  ABS
            42177 A4C1: 190  BE  10111110  PEEK
            42178 A4C2: 191  BF  10111111  IN
            42179 A4C3: 192  C0  11000000  USR
            42180 A4C4: 193  C1  11000001  STR$
            42181 A4C5: 194  C2  11000010  CHR$
            42182 A4C6: 195  C3  11000011  NOT
            42183 A4C7: 196  C4  11000100  BIN
            42184 A4C8: 197  C5  11000101  OR
            42185 A4C9: 198  C6  11000110  AND
            42186 A4CA: 199  C7  11000111  <=
            42187 A4CB: 200  C8  11001000  >=
            42188 A4CC: 201  C9  11001001  <>
            42189 A4CD: 202  CA  11001010  LINE
            42190 A4CE: 203  CB  11001011  THEN
            42191 A4CF: 204  CC  11001100  TO
            42192 A4D0: 205  CD  11001101  STEP
            42193 A4D1: 206  CE  11001110  DEF FN
            42194 A4D2: 207  CF  11001111  CAT
            42195 A4D3: 208  D0  11010000  FORMAT
            42196 A4D4: 209  D1  11010001  MOVE
            42197 A4D5: 210  D2  11010010  ERASE
            42198 A4D6: 211  D3  11010011  OPEN #
            42199 A4D7: 212  D4  11010100  CLOSE #
            42200 A4D8: 213  D5  11010101  MERGE
            42201 A4D9: 214  D6  11010110  VERIFY
            42202 A4DA: 215  D7  11010111  BEEP
            42203 A4DB: 216  D8  11011000  CIRCLE
            42204 A4DC: 217  D9  11011001  INK
            42205 A4DD: 218  DA  11011010  PAPER
            42206 A4DE: 219  DB  11011011  FLASH
            42207 A4DF: 220  DC  11011100  BRIGHT
            42208 A4E0: 221  DD  11011101  INVERSE
            42209 A4E1: 222  DE  11011110  OVER
            42210 A4E2: 223  DF  11011111  OUT
            42211 A4E3: 224  E0  11100000  LPRINT
            42212 A4E4: 225  E1  11100001  LLIST
            42213 A4E5: 226  E2  11100010  STOP
            42214 A4E6: 227  E3  11100011  READ
            42215 A4E7: 228  E4  11100100  DATA
            42216 A4E8: 229  E5  11100101  RESTORE
            42217 A4E9: 230  E6  11100110  NEW
            42218 A4EA: 231  E7  11100111  BORDER
            42219 A4EB: 232  E8  11101000  CONTINUE
            42220 A4EC: 233  E9  11101001  DIM
            42221 A4ED: 234  EA  11101010  REM
            42222 A4EE: 235  EB  11101011  FOR
            42223 A4EF: 236  EC  11101100  GO TO
            42224 A4F0: 237  ED  11101101  GO SUB
            42225 A4F1: 238  EE  11101110  INPUT
            42226 A4F2: 239  EF  11101111  LOAD
            42227 A4F3: 240  F0  11110000  LIST
            42228 A4F4: 241  F1  11110001  LET
            42229 A4F5: 242  F2  11110010  PAUSE
            42230 A4F6: 243  F3  11110011  NEXT
            42231 A4F7: 244  F4  11110100  POKE
            42232 A4F8: 245  F5  11110101  PRINT
            42233 A4F9: 246  F6  11110110  PLOT
            42234 A4FA: 247  F7  11110111  RUN
            42235 A4FB: 248  F8  11111000  SAVE
            42236 A4FC: 249  F9  11111001  RANDOMIZE
            42237 A4FD: 250  FA  11111010  IF
            42238 A4FE: 251  FB  11111011  CLS
            42239 A4FF: 252  FC  11111100  DRAW
            42240 A500: 253  FD  11111101  CLEAR
            42241 A501: 254  FE  11111110  RETURN
            42242 A502: 255  FF  11111111  COPY
        """
        self._test_sna(ram, exp_output, '--peek {}-{}'.format(address, address + len(tokens) - 1))

    def test_option_p_with_nonstandard_characters(self):
        ram = [0] * 49152
        address = 44637
        chars = [94, 96, 127]
        ram[address - 16384:address - 16384 + len(chars)] = chars
        exp_output = """
            44637 AE5D:  94  5E  01011110  ↑
            44638 AE5E:  96  60  01100000  £
            44639 AE5F: 127  7F  01111111  ©
        """
        self._test_sna(ram, exp_output, '-p {}-{}'.format(address, address + len(chars) - 1))

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
        exp_output = '{0}-{1} {0:04X}-{1:04X}: {2}'.format(address, address + len(text) - 1, text)
        self._test_sna(ram, exp_output, '-t {}'.format(text))

    def test_option_find_text_with_multiple_occurrences(self):
        ram = [0] * 49152
        text = 'bar'
        text_bin = [ord(c) for c in text]
        addresses = (32536, 43567, 61437)
        exp_output = ''
        for a in addresses:
            ram[a - 16384:a - 16384 + len(text)] = text_bin
            exp_output += '{0}-{1} {0:04X}-{1:04X}: {2}\n'.format(a, a + len(text) - 1, text)
        self._test_sna(ram, exp_output, '--find-text {}'.format(text))

    def test_option_t_with_no_occurrences(self):
        ram = [0] * 49152
        exp_output = ''
        self._test_sna(ram, exp_output, '-t nowhere')

    def test_option_T(self):
        ram = [0] * 49152
        tile_addr = 54212
        tile_data = [0, 24, 12, 6, 127, 6, 12, 24]
        x, y = 3, 7
        df_addr = 16384 + 2048 * (y // 8) + 32 * (y & 7) + x
        ram[df_addr - 16384:df_addr - 14336:256] = tile_data
        ram[tile_addr - 16384:tile_addr - 16376] = tile_data
        exp_output = """
            |        |
            |   **   |
            |    **  |
            |     ** |
            | *******|
            |     ** |
            |    **  |
            |   **   |
            54212-54219-1 D3C4-D3CB-1: 0,24,12,6,127,6,12,24
        """
        self._test_sna(ram, exp_output, '-T {},{}'.format(x, y))

    def test_option_find_tile_with_step(self):
        ram = [0] * 49152
        tile_addr = 27483
        tile_data = [0, 127, 127, 96, 96, 103, 103, 102]
        x, y = 9, 15
        step = 2
        df_addr = 16384 + 2048 * (y // 8) + 32 * (y & 7) + x
        ram[df_addr - 16384:df_addr - 14336:256] = tile_data
        ram[tile_addr - 16384:tile_addr - 16384 + 8 * step:step] = tile_data
        exp_output = """
            |        |
            | *******|
            | *******|
            | **     |
            | **     |
            | **  ***|
            | **  ***|
            | **  ** |
            27483-27497-2 6B5B-6B69-2: 0,127,127,96,96,103,103,102
        """
        self._test_sna(ram, exp_output, '--find-tile {},{}-{}'.format(x, y, step))

    def test_option_T_with_step_range(self):
        ram = [0] * 49152
        tile_addr = 46987
        tile_data = [0, 254, 254, 6, 6, 230, 230, 102]
        x, y = 27, 2
        step = 3
        df_addr = 16384 + 2048 * (y // 8) + 32 * (y & 7) + x
        ram[df_addr - 16384:df_addr - 14336:256] = tile_data
        ram[tile_addr - 16384:tile_addr - 16384 + 8 * step:step] = tile_data
        exp_output = """
            |        |
            |******* |
            |******* |
            |     ** |
            |     ** |
            |***  ** |
            |***  ** |
            | **  ** |
            46987-47008-3 B78B-B7A0-3: 0,254,254,6,6,230,230,102
        """
        self._test_sna(ram, exp_output, '-T {},{}-2-3'.format(x, y))

    def test_option_T_with_hex_step_range_limits(self):
        ram = [0] * 49152
        tile_addr = 51132
        tile_data = [102, 103, 103, 96, 96, 127, 127, 0]
        x, y = 27, 2
        step = 3
        df_addr = 16384 + 2048 * (y // 8) + 32 * (y & 7) + x
        ram[df_addr - 16384:df_addr - 14336:256] = tile_data
        ram[tile_addr - 16384:tile_addr - 16384 + 8 * step:step] = tile_data
        exp_output = """
            | **  ** |
            | **  ***|
            | **  ***|
            | **     |
            | **     |
            | *******|
            | *******|
            |        |
            51132-51153-3 C7BC-C7D1-3: 102,103,103,96,96,127,127,0
        """
        self._test_sna(ram, exp_output, '-T {},{}-0x02-0x03'.format(x, y))

    def test_option_find_tile_with_invalid_coordinates(self):
        exp_error = 'Invalid tile coordinates'
        self._test_bad_spec('--find-tile', 'x,0', exp_error)
        self._test_bad_spec('-T', '0,y', exp_error)
        self._test_bad_spec('--find-tile', '?,!', exp_error)
        self._test_bad_spec('-T', '33,1', exp_error)
        self._test_bad_spec('--find-tile', '2,27', exp_error)

    def test_option_find_tile_with_invalid_step(self):
        exp_error = 'Invalid distance: {}'
        self._test_bad_spec('--find-tile', '2,3-x', exp_error.format('x'), False)
        self._test_bad_spec('-T', '5,6-1-y', exp_error.format('1-y'), False)
        self._test_bad_spec('--find-tile', '8,9-z-5', exp_error.format('z-5'), False)
        self._test_bad_spec('-T', '11,12-q-?', exp_error.format('q-?'), False)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_snapinfo(option, catch_exit=0)
            self.assertEqual('SkoolKit {}\n'.format(VERSION), output)

    def test_option_w_with_single_address(self):
        ram = [0] * 49152
        address = 46731
        ram[address - 16384:address - 16382] = [47, 10]
        exp_output = '46731 B68B:  2607  0A2F'
        self._test_sna(ram, exp_output, '-w {}'.format(address))

    def test_option_word_with_address_range(self):
        ram = [0] * 49152
        address1 = 57116
        address2 = 57122
        ram[address1 - 16384:address2 -16382] = [27, 45, 132, 19, 18, 3, 23, 0]
        exp_output = """
            57116 DF1C: 11547  2D1B
            57118 DF1E:  4996  1384
            57120 DF20:   786  0312
            57122 DF22:    23  0017
        """
        self._test_sna(ram, exp_output, '--word {}-{}'.format(address1, address2))

    def test_option_w_with_address_range_and_step(self):
        ram = [0] * 49152
        address1 = 36874
        address2 = 36880
        step = 3
        ram[address1 - 16384:address2 -16382] = [1, 0, 0, 215, 2, 0, 7, 113]
        exp_output = """
            36874 900A:     1  0001
            36877 900D:   727  02D7
            36880 9010: 28935  7107
        """
        self._test_sna(ram, exp_output, '-w {}-{}-{}'.format(address1, address2, step))

    def test_option_w_with_hexadecimal_values(self):
        ram = [0] * 49152
        address1 = 0x900a
        address2 = 0x9010
        step = 0x03
        ram[address1 - 16384:address2 -16382] = [1, 0, 0, 215, 2, 0, 7, 113]
        exp_output = """
            36874 900A:     1  0001
            36877 900D:   727  02D7
            36880 9010: 28935  7107
        """
        self._test_sna(ram, exp_output, '-w ${:04X}-${:04x}-${:X}'.format(address1, address2, step))

    def test_option_w_with_0x_hexadecimal_values(self):
        ram = [0] * 49152
        address1 = 0x900a
        address2 = 0x9010
        step = 0x03
        ram[address1 - 16384:address2 -16382] = [1, 0, 0, 215, 2, 0, 7, 113]
        exp_output = """
            36874 900A:     1  0001
            36877 900D:   727  02D7
            36880 9010: 28935  7107
        """
        self._test_sna(ram, exp_output, '-w 0x{:04X}-0x{:04x}-0x{:X}'.format(address1, address2, step))

    def test_option_word_multiple(self):
        ram = [0] * 49152
        options = []
        addresses = (37162, 42174, 56118)
        for a in addresses:
            ram[a - 16384:a - 16382] = [a // 256, a % 256]
            options.append('--word {}'.format(a))
        exp_output = """
            37162 912A: 10897  2A91
            42174 A4BE: 48804  BEA4
            56118 DB36: 14043  36DB
        """
        self._test_sna(ram, exp_output, ' '.join(options))

    def test_option_word_with_invalid_address_range(self):
        exp_error = 'Invalid address range'
        self._test_bad_spec('--word', 'X', exp_error)
        self._test_bad_spec('-w', '32768-?', exp_error)
        self._test_bad_spec('--word', '32768-32868-q', exp_error)
        self._test_bad_spec('-w', '32768-32868-2-3', exp_error)
