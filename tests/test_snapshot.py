# -*- coding: utf-8 -*-
import zlib
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.snapshot import get_snapshot, SnapshotError

class SnapshotTest(SkoolKitTestCase):
    def _check_ram(self, ram, exp_ram, model, out_7ffd, pages, page):
        self.assertEqual(len(ram), 49152)
        if model == 0:
            # 16K
            self.assertEqual(ram[:16384], exp_ram[:16384])
            self.assertEqual(ram[16384:], [0] * 32768)
        elif model == 1:
            # 48K
            self.assertEqual(ram, exp_ram)
        else:
            # 128K
            self.assertEqual(ram[:32768], exp_ram[:32768])
            if page is None:
                page = out_7ffd & 7
            self.assertEqual(ram[32768:], pages.get(page, exp_ram[32768:]))

class ErrorTest(SnapshotTest):
    def test_unknown_file_type(self):
        file_type = 'tzx'
        snapshot_file = self.write_bin_file(suffix='.{0}'.format(file_type))
        with self.assertRaisesRegexp(SnapshotError, "{}: Unknown file type '{}'".format(snapshot_file, file_type)):
            get_snapshot(snapshot_file)

    def test_bad_ram_size(self):
        ram_size = 3
        with self.assertRaisesRegexp(SnapshotError, 'RAM size is {}'.format(ram_size)):
            get_snapshot(self.write_bin_file([0] * (27 + ram_size), suffix='.sna'))

class SNATest(SnapshotTest):
    def test_sna_48k(self):
        header = [0] * 27
        exp_ram = [(n + 23) & 255 for n in range(49152)]
        sna = header + exp_ram
        tmp_sna = self.write_bin_file(sna, suffix='.sna')
        snapshot = get_snapshot(tmp_sna)
        ram = snapshot[16384:]
        self.assertEqual(len(ram), 49152)
        self.assertEqual(ram, exp_ram)

    def test_sna_128k(self):
        header = [0] * 27
        exp_ram = [(n + 37) & 255 for n in range(49152)]
        tail = [0] * (4 + 5 * 16384)
        sna = header + exp_ram + tail
        tmp_sna = self.write_bin_file(sna, suffix='.sna')
        snapshot = get_snapshot(tmp_sna)
        ram = snapshot[16384:]
        self.assertEqual(len(ram), 49152)
        self.assertEqual(ram, exp_ram)

    def test_sna_128k_page_1(self):
        header = [0] * 27
        page5 = [(n + 37) & 255 for n in range(16384)]
        page2 = [(n + 19) & 255 for n in range(16384)]
        page6 = [(n + 23) & 255 for n in range(16384)]
        page0 = [(n + 197) & 255 for n in range(16384)]
        page1 = [(n + 117) & 255 for n in range(16384)]
        page3 = [(n + 203) & 255 for n in range(16384)]
        page4 = [(n + 5) & 255 for n in range(16384)]
        page7 = [(n + 41) & 255 for n in range(16384)]
        config = [0, 0] # PC
        config.append(6) # Port 7ffd (page 6 mapped to 49152-65535)
        config.append(0) # TR-DOS ROM not paged
        sna = header + page5 + page2 + page6 + config + page0 + page1 + page3 + page4 + page7
        tmp_sna = self.write_bin_file(sna, suffix='.sna')
        snapshot = get_snapshot(tmp_sna, 1)
        ram = snapshot[16384:]
        self.assertEqual(len(ram), 49152)
        self.assertEqual(ram, page5 + page2 + page1)

    def test_sna_128k_page_5(self):
        header = [0] * 27
        page5 = [(n + 37) & 255 for n in range(16384)]
        page2 = [(n + 19) & 255 for n in range(16384)]
        page3 = [(n + 203) & 255 for n in range(16384)]
        page0 = [(n + 197) & 255 for n in range(16384)]
        page1 = [(n + 117) & 255 for n in range(16384)]
        page4 = [(n + 5) & 255 for n in range(16384)]
        page6 = [(n + 23) & 255 for n in range(16384)]
        page7 = [(n + 41) & 255 for n in range(16384)]
        config = [0, 0] # PC
        config.append(3) # Port 7ffd (page 3 mapped to 49152-65535)
        config.append(0) # TR-DOS ROM not paged
        sna = header + page5 + page2 + page3 + config + page0 + page1 + page4 + page6 + page7
        tmp_sna = self.write_bin_file(sna, suffix='.sna')
        snapshot = get_snapshot(tmp_sna, 5)
        ram = snapshot[16384:]
        self.assertEqual(len(ram), 49152)
        self.assertEqual(ram, page5 + page2 + page5)

class Z80Test(SnapshotTest):
    def _test_z80(self, exp_ram, version, compress, machine_id=0, modify=False, out_7ffd=0, pages={}, page=None):
        model, tmp_z80 = self.write_z80(exp_ram, version, compress, machine_id, modify, out_7ffd, pages)
        snapshot = get_snapshot(tmp_z80, page)
        self._check_ram(snapshot[16384:], exp_ram, model, out_7ffd, pages, page)

    def test_z80v1(self):
        exp_ram = [n & 255 for n in range(49152)]
        self._test_z80(exp_ram, 1, False)

    def test_z80v1_compressed(self):
        exp_ram = [0] * 261 + [1] * 10 + [2] * 4 + [237, 4] + [237] * 2
        exp_ram += [128] * (49152 - len(exp_ram))
        self._test_z80(exp_ram, 1, True)

    def test_z80v2_16k_compressed(self):
        exp_ram = [(n + 7) & 255 for n in range(49152)]
        self._test_z80(exp_ram, 2, True, modify=True)

    def test_z80v2_48k(self):
        exp_ram = [(n + 1) & 255 for n in range(49152)]
        self._test_z80(exp_ram, 2, False)

    def test_z80v2_48k_compressed(self):
        exp_ram = [33] * 263 + [7] * 11 + [144] * 3 + [13, 14] + [237] * 3
        exp_ram += [107] * (49152 - len(exp_ram))
        self._test_z80(exp_ram, 2, True)

    def test_z80v2_128k(self):
        exp_ram = [(n + 127) & 255 for n in range(49152)]
        self._test_z80(exp_ram, 2, False, machine_id=3)

    def test_z80v3_16k(self):
        exp_ram = [(n + 7) & 255 for n in range(49152)]
        self._test_z80(exp_ram, 3, False, machine_id=1, modify=True)

    def test_z80v3_48k(self):
        exp_ram = [(n + 128) & 255 for n in range(49152)]
        self._test_z80(exp_ram, 3, False)

    def test_z80v3_48k_compressed(self):
        exp_ram = [201] * 4336 + [19] * 255 + [142] * 2 + [1, 2] + [37] * 4
        exp_ram += [193] * (49152 - len(exp_ram))
        self._test_z80(exp_ram, 3, True)

    def test_z80v3_128k(self):
        exp_ram = [(n + 37) & 255 for n in range(49152)]
        self._test_z80(exp_ram, 3, False, machine_id=4)

    def test_z80v3_128k_page_4(self):
        exp_ram = [(n + 37) & 255 for n in range(49152)]
        pages = {4: [(n + 249) & 255 for n in range(16384)]}
        self._test_z80(exp_ram, 3, False, machine_id=4, pages=pages, page=4)

    def test_bad_z80(self):
        header = [0] * 30
        header[6] = 255 # Set PC > 0 to indicate a v1 Z80 snapshot
        header[12] |= 32 # Signal that the RAM data block is compressed
        z80 = header + [255] # Good byte to start with
        z80 += [237, 237, 0, 11] # Bad block of length 0
        z80 += [0, 237, 237, 0] # Terminator
        z80_file = self.write_bin_file(z80, suffix='.z80')
        with self.assertRaisesRegexp(SnapshotError, 'Found ED ED 00 0B'):
            get_snapshot(z80_file)

class SZXTest(SnapshotTest):
    def _get_szx_header(self, machine_id=1, ch7ffd=0, specregs=True):
        header = [90, 88, 83, 84] # ZXST
        header.extend((1, 4)) # Version 1.4
        header.append(machine_id) # 0=16K, 1=48K, 2+=128K
        header.append(0) # Flags
        if specregs:
            header.extend((83, 80, 67, 82)) # SPCR
            header.extend((8, 0, 0, 0)) # Size
            header.append(0) # Border
            header.append(ch7ffd) # Last OUT to port $7FFD
            header.extend((0, 0, 0, 0, 0, 0))
        return header

    def _get_zxstrampage(self, page, compress, data):
        if compress:
            # PY: No need to convert to bytes and bytearray in Python 3
            ram = bytearray(zlib.compress(bytes(bytearray(data)), 9))
        else:
            ram = data
        ramp = [82, 65, 77, 80] # RAMP
        size = len(ram) + 3
        ramp.extend((size % 256, size // 256, 0, 0))
        ramp.extend((1 if compress else 0, 0))
        ramp.append(page)
        ramp.extend(ram)
        return ramp

    def _test_szx(self, exp_ram, compress, machine_id=1, ch7ffd=0, pages={}, page=None):
        szx = self._get_szx_header(machine_id, ch7ffd)
        rampages = {5: self._get_zxstrampage(5, compress, exp_ram[:16384])}
        if machine_id >= 1:
            # 48K and 128K
            rampages[2] = self._get_zxstrampage(2, compress, exp_ram[16384:32768])
            if machine_id == 1:
                # 48K
                rampages[0] = self._get_zxstrampage(0, compress, exp_ram[32768:])
            else:
                # 128K
                rampages[ch7ffd & 7] = self._get_zxstrampage(ch7ffd & 7, compress, exp_ram[32768:])
                for bank, data in pages.items():
                    rampages[bank] = self._get_zxstrampage(bank, compress, data)
                for bank in set(range(8)) - set(rampages.keys()):
                    rampages[bank] = self._get_zxstrampage(bank, compress, [0] * 16384)
        for rampage in rampages.values():
            szx.extend(rampage)
        tmp_szx = self.write_bin_file(szx, suffix='.szx')
        snapshot = get_snapshot(tmp_szx, page)
        self._check_ram(snapshot[16384:], exp_ram, machine_id, ch7ffd, pages, page)

    def test_szx_16k(self):
        exp_ram = [(n + 13) & 255 for n in range(16384)]
        self._test_szx(exp_ram, True, machine_id=0)

    def test_szx_48k_compressed(self):
        exp_ram = [(n + 59) & 255 for n in range(49152)]
        self._test_szx(exp_ram, True)

    def test_szx_48k_uncompressed(self):
        exp_ram = [(n + 73) & 255 for n in range(49152)]
        self._test_szx(exp_ram, False)

    def test_szx_48k_bad_zlib_block(self):
        szx = self._get_szx_header()
        szx.extend((82, 65, 77, 80)) # RAMP
        ram = (1, 2, 3, 4, 5, 6, 7, 8) # Invalid zlib block
        size = len(ram) + 3
        szx.extend((size % 256, size // 256, 0, 0))
        szx.extend((1, 0)) # Compressed
        page = 5
        szx.append(page)
        tmp_szx = self.write_bin_file(szx, suffix='.szx')
        try:
            get_snapshot(tmp_szx)
        except SnapshotError as e:
            self.assertTrue(e.args[0].startswith("Error while decompressing page {0}:".format(page)))

    def test_szx_48k_bad_page_size(self):
        szx = self._get_szx_header()
        ram = [0, 0, 0] # Bad page size (3 != 16384)
        page = 5
        szx.extend(self._get_zxstrampage(page, False, ram))
        tmp_szx = self.write_bin_file(szx, suffix='.szx')
        try:
            get_snapshot(tmp_szx)
        except SnapshotError as e:
            self.assertEqual(e.args[0], "Page {0} is {1} bytes (should be 16384)".format(5, len(ram)))

    def test_szx_48k_missing_page(self):
        szx = self._get_szx_header()
        szx.extend(self._get_zxstrampage(5, True, [0] * 16384))
        tmp_szx = self.write_bin_file(szx, suffix='.szx')
        try:
            get_snapshot(tmp_szx)
        except SnapshotError as e:
            self.assertEqual(e.args[0], "Page 2 not found")

    def test_szx_128k(self):
        exp_ram = [(n + 73) & 255 for n in range(49152)]
        self._test_szx(exp_ram, True, 3)

    def test_szx_128k_no_specregs(self):
        szx = self._get_szx_header(2, specregs=False)
        tmp_szx = self.write_bin_file(szx, suffix='.szx')
        try:
            get_snapshot(tmp_szx)
        except SnapshotError as e:
            self.assertEqual(e.args[0], "SPECREGS (SPCR) block not found")

    def test_szx_128k_page_1(self):
        exp_ram = [(n + 173) & 255 for n in range(49152)]
        pages = {1: [(n + 19) & 255 for n in range(16384)]}
        self._test_szx(exp_ram, False, machine_id=2, pages=pages, page=1)

if __name__ == '__main__':
    unittest.main()
