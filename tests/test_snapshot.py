from collections import defaultdict
import zlib

from skoolkittest import SkoolKitTestCase, Z80 as Z80Reader
from skoolkit import SkoolKitError, get_dword
from skoolkit.snapshot import Snapshot, Z80, get_snapshot, write_snapshot, SnapshotError

class SnapshotTest(SkoolKitTestCase):
    def _check_ram(self, ram, exp_ram, model, out_7ffd, pages, page):
        if model == 0:
            # 16K
            self.assertEqual(len(ram), 49152)
            self.assertEqual(ram[:16384], exp_ram[:16384])
            self.assertEqual(sum(ram[16384:]), 0)
        elif model == 1:
            # 48K
            self.assertEqual(len(ram), 49152)
            self.assertEqual(ram, exp_ram)
        else:
            # 128K
            if page is None:
                page = out_7ffd & 7
            if page >= 0:
                self.assertEqual(len(ram), 49152)
                self.assertEqual(ram[:32768], exp_ram[:32768])
                self.assertEqual(ram[32768:], pages.get(page, exp_ram[32768:]))
            else:
                self.assertEqual(len(ram), 0x20000)
                self.assertEqual(exp_ram[0x8000:0xC000], ram[0x00000:0x04000]) # Bank 0
                self.assertEqual(pages[1], ram[0x04000:0x08000])               # Bank 1
                self.assertEqual(exp_ram[0x4000:0x8000], ram[0x08000:0x0C000]) # Bank 2
                self.assertEqual(pages[3], ram[0x0C000:0x10000])               # Bank 3
                self.assertEqual(pages[4], ram[0x10000:0x14000])               # Bank 4
                self.assertEqual(exp_ram[:0x4000], ram[0x14000:0x18000])       # Bank 5
                self.assertEqual(pages[6], ram[0x18000:0x1C000])               # Bank 6
                self.assertEqual(pages[7], ram[0x1C000:0x20000])               # Bank 7

class ErrorTest(SnapshotTest):
    def test_unknown_file_type(self):
        file_type = 'tzx'
        snapshot_file = self.write_bin_file(suffix='.{0}'.format(file_type))
        with self.assertRaisesRegex(SnapshotError, "{}: Unknown file type".format(snapshot_file)):
            get_snapshot(snapshot_file)

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

    def test_sna_128k_all_pages(self):
        header = [0] * 27
        pages = {p: [p] * 16384 for p in range(8)}
        config = [0, 0] # PC
        config.append(3) # Port 7ffd (page 3 mapped to 49152-65535)
        config.append(0) # TR-DOS ROM not paged
        sna = header + pages[5] + pages[2] + pages[3] + config + pages[0] + pages[1] + pages[4] + pages[6] + pages[7]
        tmp_sna = self.write_bin_file(sna, suffix='.sna')
        ram = get_snapshot(tmp_sna, -1)
        self.assertEqual(len(ram), 131072)
        self.assertTrue(set(ram[0x00000:0x04000]), {5})
        self.assertTrue(set(ram[0x04000:0x08000]), {2})
        self.assertTrue(set(ram[0x08000:0x0C000]), {0})
        self.assertTrue(set(ram[0x0C000:0x10000]), {1})
        self.assertTrue(set(ram[0x10000:0x14000]), {3})
        self.assertTrue(set(ram[0x14000:0x18000]), {4})
        self.assertTrue(set(ram[0x18000:0x1C000]), {6})
        self.assertTrue(set(ram[0x1C000:0x20000]), {7})

class Z80Test(SnapshotTest):
    def _test_z80(self, exp_ram, version, compress, machine_id=0, modify=False, out_7ffd=0, pages={}, page=None):
        model, tmp_z80 = self.write_z80(exp_ram, version, compress, machine_id, modify, out_7ffd, pages)
        snapshot = get_snapshot(tmp_z80, page)
        ram = snapshot[16384:] if len(snapshot) == 65536 else snapshot
        self._check_ram(ram, exp_ram, model, out_7ffd, pages, page)

    def test_z80v1(self):
        exp_ram = [n & 255 for n in range(49152)]
        self._test_z80(exp_ram, 1, False)

    def test_z80v1_compressed(self):
        exp_ram = [0] * 261 + [1] * 10 + [2] * 4 + [237, 4] + [237] * 2
        exp_ram += [128] * (49152 - len(exp_ram))
        self._test_z80(exp_ram, 1, True)

    def test_z80v1_bad_ram_size(self):
        header = [0] * 30
        header[6] = 1 # PC
        ram = [0] * 2
        z80file = self.write_bin_file(header + ram, suffix='.z80')
        with self.assertRaisesRegex(SnapshotError, r"RAM is 2 bytes \(should be 49152\)"):
            get_snapshot(z80file)

    def test_z80v2_16k_compressed(self):
        exp_ram = [(n + 7) & 255 for n in range(16384)] + [0] * 32768
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

    def test_z80v2_bad_ram_page_size(self):
        header = [0] * 55
        header[30] = 23
        ram_block = [3, 0, 4, 1, 2, 3]
        z80file = self.write_bin_file(header + ram_block, suffix='.z80')
        with self.assertRaisesRegex(SnapshotError, r"Page 1 is 3 bytes \(should be 16384\)"):
            get_snapshot(z80file)

    def test_z80v3_16k(self):
        exp_ram = [(n + 7) & 255 for n in range(16384)] + [0] * 32768
        self._test_z80(exp_ram, 3, False, machine_id=1, modify=True)

    def test_z80v3_48k(self):
        exp_ram = [(n + 128) & 255 for n in range(49152)]
        self._test_z80(exp_ram, 3, False)

    def test_z80v3_48k_mgt(self):
        exp_ram = [(n + 128) & 255 for n in range(49152)]
        self._test_z80(exp_ram, 3, False, machine_id=3)

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

    def test_z80v3_128k_all_pages(self):
        exp_ram = [(n + 37) & 255 for n in range(49152)]
        pages = {p: [p] * 16384 for p in (1, 3, 4, 6, 7)}
        self._test_z80(exp_ram, 3, False, machine_id=4, pages=pages, page=-1)

    def test_z80v3_48k_compressed_block_ending_with_ED(self):
        exp_ram = [0] * 49152
        exp_ram[16383] = 237
        self._test_z80(exp_ram, 3, True)

    def test_bad_z80(self):
        header = [0] * 30
        header[6] = 255 # Set PC > 0 to indicate a v1 Z80 snapshot
        header[12] |= 32 # Signal that the RAM data block is compressed
        z80 = header + [255] # Good byte to start with
        z80 += [237, 237, 0, 11] # Bad block of length 0
        z80 += [0, 237, 237, 0] # Terminator
        z80_file = self.write_bin_file(z80, suffix='.z80')
        with self.assertRaisesRegex(SnapshotError, 'Found ED ED 00 0B'):
            get_snapshot(z80_file)

class Z80CompressionTest(SkoolKitTestCase):
    def test_single_ED_followed_by_five_identical_values(self):
        data = [237, 1, 1, 1, 1, 1]
        z80file = 'test.z80'
        Z80(ram=data + [0] * 49146).write(z80file)
        ram = Z80Reader(z80file).ram
        self.assertEqual(data, ram[:6])
        self.assertEqual(sum(ram[6:]), 0)

    def test_single_ED_followed_by_six_identical_values(self):
        data = [237, 2, 2, 2, 2, 2, 2]
        z80file = 'test.z80'
        Z80(ram=data + [0] * 49145).write(z80file)
        ram = Z80Reader(z80file).ram
        self.assertEqual(data, ram[:7])
        self.assertEqual(sum(ram[7:]), 0)

    def test_block_ending_with_single_ED(self):
        data = [0] * 16383 + [237]
        z80file = 'test.z80'
        Z80(ram=data + [0] * 32768).write(z80file)
        ram = Z80Reader(z80file).ram
        self.assertEqual(ram[16383], 237)
        self.assertEqual(sum(ram), 237)

class Z80StateTest(SkoolKitTestCase):
    def test_iff(self):
        z80 = Z80()
        for iff in (0, 1):
            z80.header[27:29] = (255, 255)
            z80.set_registers_and_state((), [f'iff={iff}'])
            self.assertEqual([iff, iff], z80.header[27:29])

    def test_im(self):
        z80 = Z80()
        for im in (0, 1, 2):
            z80.header[29] = 255
            z80.set_registers_and_state((), [f'im={im}'])
            self.assertEqual(z80.header[29], 252 + im)

    def test_border(self):
        z80 = Z80()
        for border in range(8):
            z80.header[12] = 255
            z80.set_registers_and_state((), [f'border={border}'])
            self.assertEqual(z80.header[12], 241 + border * 2)

    def test_tstates_is_ignored_v1(self):
        ram = [0] * 0xC000
        z80file = self.write_z80_file(None, ram, version=1)
        z80 = Snapshot.get(z80file)
        exp_header = list(z80.header)
        z80.set_registers_and_state((), ['tstates=50000'])
        self.assertEqual(exp_header, z80.header)

    def test_tstates_is_ignored_v2(self):
        ram = [0] * 0xC000
        z80file = self.write_z80_file(None, ram, version=2)
        z80 = Snapshot.get(z80file)
        exp_header = list(z80.header)
        z80.set_registers_and_state((), ['tstates=50000'])
        self.assertEqual(exp_header, z80.header)

    def test_tstates_48k(self):
        z80 = Z80()
        z80.header[34] = 0 # 48K
        for tstates in (0, 1000, 17471, 17472, 20000, 38000, 56000, 69887, 69888):
            z80.set_registers_and_state((), [f'tstates={tstates}'])
            t_lo = z80.header[55] + 256 * z80.header[56]
            t_hi = z80.header[57]
            t = 69887 - ((2 - t_hi) % 4) * 17472 - (t_lo % 17472)
            self.assertEqual(t, tstates % 69888)

    def test_tstates_128k(self):
        z80 = Z80()
        z80.header[34] = 4 # 128K
        for tstates in (0, 1000, 17726, 17727, 20000, 38000, 56000, 70907, 70908):
            z80.set_registers_and_state((), [f'tstates={tstates}'])
            t_lo = z80.header[55] + 256 * z80.header[56]
            t_hi = z80.header[57]
            t = 70907 - ((2 - t_hi) % 4) * 17727 - (t_lo % 17727)
            self.assertEqual(t, tstates % 70908)

    def test_issue2(self):
        z80 = Z80()
        for issue2 in (0, 1):
            z80.header[29] = 255
            z80.set_registers_and_state((), [f'issue2={issue2}'])
            self.assertEqual(z80.header[29], 251 + issue2 * 4)

    def test_7ffd_is_ignored_v1(self):
        ram = [0] * 0xC000
        z80file = self.write_z80_file(None, ram, version=1)
        z80 = Snapshot.get(z80file)
        exp_header = list(z80.header)
        z80.set_registers_and_state((), ['7ffd=7'])
        self.assertEqual(exp_header, z80.header)

    def test_fffd_is_ignored_v1(self):
        ram = [0] * 0xC000
        z80file = self.write_z80_file(None, ram, version=1)
        z80 = Snapshot.get(z80file)
        exp_header = list(z80.header)
        z80.set_registers_and_state((), ['fffd=8'])
        self.assertEqual(exp_header, z80.header)

    def test_ay_is_ignored_v1(self):
        ram = [0] * 0xC000
        z80file = self.write_z80_file(None, ram, version=1)
        z80 = Snapshot.get(z80file)
        exp_header = list(z80.header)
        z80.set_registers_and_state((), ('ay[0]=1', 'ay[15]=15'))
        self.assertEqual(exp_header, z80.header)

    def test_all(self):
        z80 = Z80()
        z80.header[12:58] = [255] * 46
        z80.header[34] = 4 # 128K
        state = (
            'iff=0', 'im=2', 'border=3', 'tstates=17726', 'issue2=0',
            '7ffd=1', 'fffd=2', 'ay[0]=3', 'ay[15]=4'
        )
        z80.set_registers_and_state((), state)
        self.assertEqual(z80.header[12], 247) # Border (bits 1-3)
        self.assertEqual(z80.header[27], 0) # IFF1
        self.assertEqual(z80.header[28], 0) # IFF2
        self.assertEqual(z80.header[29], 250) # IM (bits 0-1), issue 2 (bit 2)
        self.assertEqual(z80.header[35], 1) # Port 0x7ffd
        self.assertEqual(z80.header[38], 2) # Port 0xfffd
        self.assertEqual(z80.header[39], 3) # AY register 0
        self.assertEqual(z80.header[54], 4) # AY register 15
        self.assertEqual([0, 0, 3], z80.header[55:58]) # T-states

class Z80RegistersTest(SkoolKitTestCase):
    def test_8_bit_registers(self):
        reg = {
            'a': 1, 'f': 2, 'b': 3, 'c': 4, 'd': 5, 'e': 6, 'h': 7, 'l': 8, 'i': 9, 'r': 10,
            '^a': 11, '^f': 12, '^b': 13, '^c':14, '^d': 15, '^e': 16, '^h': 17, '^l': 18
        }
        for p, f in (('', 'd'), ('$', '02x'), ('0x', '02x'), ('%', '08b')):
            specs = [f'{r}={p}{v:{f}}' for r, v in reg.items()]
            z80 = Z80()
            z80.set_registers_and_state(specs, ())
            header = z80.header
            self.assertEqual(header[0], 1)   # A
            self.assertEqual(header[1], 2)   # F
            self.assertEqual(header[3], 3)   # B
            self.assertEqual(header[2], 4)   # C
            self.assertEqual(header[14], 5)  # D
            self.assertEqual(header[13], 6)  # E
            self.assertEqual(header[5], 7)   # H
            self.assertEqual(header[4], 8)   # L
            self.assertEqual(header[10], 9)  # I
            self.assertEqual(header[11], 10) # R
            self.assertEqual(header[12], 0)  # R (bit 7)
            self.assertEqual(header[21], 11) # A'
            self.assertEqual(header[22], 12) # F'
            self.assertEqual(header[16], 13) # B'
            self.assertEqual(header[15], 14) # C'
            self.assertEqual(header[18], 15) # D'
            self.assertEqual(header[17], 16) # E'
            self.assertEqual(header[20], 17) # H'
            self.assertEqual(header[19], 18) # L'

    def test_16_bit_registers(self):
        reg = {
            'bc': 513, 'de': 1027, 'hl': 1541, 'sp': 2055, 'ix': 2569, 'iy': 3083,
            '^bc': 3597, '^de': 4111, '^hl': 4625, 'pc': 5139
        }
        for p, f in (('', 'd'), ('$', '04x'), ('0x', '04x'), ('%', '016b')):
            specs = [f'{r}={p}{v:{f}}' for r, v in reg.items()]
            z80 = Z80()
            z80.set_registers_and_state(specs, ())
            header = z80.header
            self.assertEqual([1, 2], header[2:4])     # BC
            self.assertEqual([3, 4], header[13:15])   # DE
            self.assertEqual([5, 6], header[4:6])     # HL
            self.assertEqual([7, 8], header[8:10])    # SP
            self.assertEqual([9, 10], header[25:27])  # IX
            self.assertEqual([11, 12], header[23:25]) # IY
            self.assertEqual([13, 14], header[15:17]) # BC'
            self.assertEqual([15, 16], header[17:19]) # DE'
            self.assertEqual([17, 18], header[19:21]) # HL'
            self.assertEqual([19, 20], header[32:34]) # PC

    def test_r_with_bit_7_reset(self):
        z80 = Z80()
        z80.header[12] = 255
        z80.set_registers_and_state(['r=1'], ())
        self.assertEqual(z80.header[11], 1)
        self.assertEqual(z80.header[12], 254)

    def test_r_with_bit_7_set(self):
        z80 = Z80()
        z80.header[12] = 128
        z80.set_registers_and_state(['r=240'], ())
        self.assertEqual(z80.header[11], 240)
        self.assertEqual(z80.header[12], 129)

class SZXTest(SnapshotTest):
    def _test_szx(self, exp_ram, compress, machine_id=1, ch7ffd=0, pages={}, page=None):
        tmp_szx = self.write_szx(exp_ram, compress, machine_id, ch7ffd, pages)
        snapshot = get_snapshot(tmp_szx, page)
        ram = snapshot[16384:] if len(snapshot) == 65536 else snapshot
        self._check_ram(ram, exp_ram, machine_id, ch7ffd, pages, page)

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
        szx.extend(ram)
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

    def test_szx_128k_all_pages(self):
        exp_ram = [(n + 173) & 255 for n in range(49152)]
        pages = {p: [p] * 16384 for p in (1, 3, 4, 6, 7)}
        self._test_szx(exp_ram, False, machine_id=2, pages=pages, page=-1)

class WriteSnapshotTest(SkoolKitTestCase):
    def _normalise_registers(self, registers):
        r = {
            k: 0 for k in (
                'a', 'f', 'c', 'b', 'e', 'd', 'l', 'h',
                '^a', '^f', '^c', '^b', '^e', '^d', '^l', '^h',
                'ix', 'iy', 'sp', 'pc', 'i', 'r'
            )
        }
        for reg, value in registers.items():
            size = len(reg) - 1 if reg.startswith('^') else len(reg)
            if size == 1 or reg in ('ix', 'iy', 'sp', 'pc'):
                r[reg] = value
            elif reg.startswith('^'):
                r['^' + reg[1]], r['^' + reg[2]] = value // 256, value % 256
            else:
                r[reg[0]], r[reg[1]] = value // 256, value % 256
        return r

    def _fill_state(self, state):
        s = {
            '7ffd': 0,
            'ay[0]': 0,
            'ay[1]': 0,
            'ay[2]': 0,
            'ay[3]': 0,
            'ay[4]': 0,
            'ay[5]': 0,
            'ay[6]': 0,
            'ay[7]': 0,
            'ay[8]': 0,
            'ay[9]': 0,
            'ay[10]': 0,
            'ay[11]': 0,
            'ay[12]': 0,
            'ay[13]': 0,
            'ay[14]': 0,
            'ay[15]': 0,
            'border': 0,
            'fe': 0,
            'fffd': 0,
            'iff': 1,
            'im': 1,
            'issue2': 0,
            'tstates': 34943,
        }
        s.update(state)
        return s

    def _test_invalid_state(self):
        ram48 = [0] * 49152
        ram128 = [[0] * 16384] * 8
        self._test_bad_spec('Cannot parse integer: 7ffd=?', ram128, state=['7ffd=?'])
        self._test_bad_spec('Cannot parse integer: ay[q]=1', ram128, state=['ay[q]=1'])
        self._test_bad_spec('Cannot parse integer: ay[0]=.', ram128, state=['ay[0]=.'])
        self._test_bad_spec('Cannot parse integer: border=x', ram48, state=['border=x'])
        self._test_bad_spec('Cannot parse integer: fe=$', ram48, state=['fe=$'])
        self._test_bad_spec('Cannot parse integer: fffd=@', ram128, state=['fffd=@'])
        self._test_bad_spec('Cannot parse integer: iff=;', ram48, state=['iff=;'])
        self._test_bad_spec('Cannot parse integer: im=>', ram48, state=['im=>'])
        self._test_bad_spec('Cannot parse integer: issue2=:', ram48, state=['issue2=:'])
        self._test_bad_spec('Cannot parse integer: tstates=!', ram48, state=['tstates=!'])

    def _test_invalid_registers(self):
        ram = [0] * 49152
        self._test_bad_spec('Invalid register: g=1', ram, registers=['g=1'])
        self._test_bad_spec('Cannot parse register value: h=?', ram, registers=['h=?'])

    def test_write_unsupported_snapshot_type(self):
        with self.assertRaises(SnapshotError) as cm:
            write_snapshot('snap.slt', None, None, None)
        self.assertEqual(cm.exception.args[0], 'snap.slt: Unsupported snapshot type')

class WriteSZXTest(WriteSnapshotTest):
    def _check_ramp(self, blocks, exp_ram):
        if len(exp_ram) == 8:
            pages = {i: exp_ram[i] for i in range(8)}
        else:
            pages = {0: exp_ram[32768:], 2: exp_ram[16384:32768], 5: exp_ram[:16384]}
        self.assertIn('RAMP', blocks)
        self.assertEqual(len(blocks['RAMP']), len(pages))
        for ramp in blocks.pop('RAMP'):
            self.assertEqual(ramp[:2], (1, 0)) # wFlags
            self.assertEqual(bytes(pages[ramp[2]]), zlib.decompress(bytes(ramp[3:])))

    def _check_z80r(self, blocks, exp_registers, exp_state):
        self.assertIn('Z80R', blocks)
        self.assertEqual(len(blocks['Z80R']), 1)
        z80r = blocks.pop('Z80R')[0]
        self.assertEqual(len(z80r), 37)
        self.assertEqual(z80r[0], exp_registers['f'])
        self.assertEqual(z80r[1], exp_registers['a'])
        self.assertEqual(z80r[2], exp_registers['c'])
        self.assertEqual(z80r[3], exp_registers['b'])
        self.assertEqual(z80r[4], exp_registers['e'])
        self.assertEqual(z80r[5], exp_registers['d'])
        self.assertEqual(z80r[6], exp_registers['l'])
        self.assertEqual(z80r[7], exp_registers['h'])
        self.assertEqual(z80r[8], exp_registers['^f'])
        self.assertEqual(z80r[9], exp_registers['^a'])
        self.assertEqual(z80r[10], exp_registers['^c'])
        self.assertEqual(z80r[11], exp_registers['^b'])
        self.assertEqual(z80r[12], exp_registers['^e'])
        self.assertEqual(z80r[13], exp_registers['^d'])
        self.assertEqual(z80r[14], exp_registers['^l'])
        self.assertEqual(z80r[15], exp_registers['^h'])
        self.assertEqual(z80r[16] + 256 * z80r[17], exp_registers['ix'])
        self.assertEqual(z80r[18] + 256 * z80r[19], exp_registers['iy'])
        self.assertEqual(z80r[20] + 256 * z80r[21], exp_registers['sp'])
        self.assertEqual(z80r[22] + 256 * z80r[23], exp_registers['pc'])
        self.assertEqual(z80r[24], exp_registers['i'])
        self.assertEqual(z80r[25], exp_registers['r'])
        self.assertEqual(z80r[26], exp_state['iff'] % 256) # IFF1
        self.assertEqual(z80r[27], exp_state['iff'] % 256) # IFF2
        self.assertEqual(z80r[28], exp_state['im'] % 4)
        self.assertEqual(get_dword(z80r, 29), exp_state['tstates'] % 16777216)
        self.assertEqual(z80r[33], 0) # chHoldIntReqCycles
        self.assertEqual(z80r[34], 0) # chFlags
        self.assertEqual(z80r[35:37], (0, 0)) # wMemPtr

    def _check_spcr(self, blocks, exp_state):
        self.assertIn('SPCR', blocks)
        self.assertEqual(len(blocks['SPCR']), 1)
        spcr = blocks.pop('SPCR')[0]
        self.assertEqual(len(spcr), 8)
        self.assertEqual(spcr[0], exp_state['border'] % 8)
        self.assertEqual(spcr[1], exp_state['7ffd'] % 256)
        self.assertEqual(spcr[2], 0) # ch1ffd
        self.assertEqual(spcr[3], exp_state['fe'] % 256)
        self.assertEqual(spcr[4:], (0, 0, 0, 0)) # chReserved

    def _check_keyb(self, blocks, exp_state):
        self.assertIn('KEYB', blocks)
        self.assertEqual(len(blocks['KEYB']), 1)
        keyb = blocks.pop('KEYB')[0]
        self.assertEqual(len(keyb), 5)
        self.assertEqual(keyb[:4], (exp_state['issue2'] % 2, 0, 0, 0)) # dwFlags
        self.assertEqual(keyb[4], 0) # chKeyboardJoystick

    def _check_ay(self, blocks, exp_state):
        self.assertIn('AY', blocks)
        self.assertEqual(len(blocks['AY']), 1)
        ay = blocks.pop('AY')[0]
        self.assertEqual(len(ay), 18)
        self.assertEqual(ay[0], 0) # chFlags
        self.assertEqual(ay[1], exp_state['fffd'] % 256)
        for i in range(16):
            self.assertEqual(ay[2 + i], exp_state[f'ay[{i}]'] % 256)

    def _test_szx(self, ram, registers, state, machine=None):
        fname = '{}/test.szx'.format(self.make_directory())
        write_snapshot(fname, ram, [f'{k}={v}' for k, v in registers.items()], [f'{k}={v}' for k, v in state.items()], machine)
        with open(fname, 'rb') as f:
            szx = tuple(f.read())
        self.assertTrue(len(szx) > 8)
        self.assertEqual(bytes(szx[:4]), b'ZXST')
        is128k = len(ram) == 8
        if is128k:
            if machine == '+2':
                machine_id = 3
            else:
                machine_id = 2
        else:
            machine_id = 1
        self.assertEqual((1, 4, machine_id, 0), szx[4:8])

        blocks = defaultdict(list)
        i = 8
        while i < len(szx):
            block_id = ''.join(chr(b) for b in szx[i:i + 4] if b)
            length = get_dword(szx, i + 4)
            i += 8 + length
            blocks[block_id].append(szx[i - length:i])

        exp_registers = self._normalise_registers(registers)
        exp_state = self._fill_state(state)
        self._check_z80r(blocks, exp_registers, exp_state)
        self._check_spcr(blocks, exp_state)
        if is128k:
            self._check_ay(blocks, exp_state)
        else:
            self._check_keyb(blocks, exp_state)
        self._check_ramp(blocks, ram)
        self.assertEqual([], list(blocks.keys())) # Should be no other blocks

    def _test_bad_spec(self, exp_error, ram, registers=(), state=()):
        fname = '{}/test.szx'.format(self.make_directory())
        with self.assertRaises(SkoolKitError) as cm:
            write_snapshot(fname, ram, registers, state)
        self.assertEqual(cm.exception.args[0], exp_error)

    def test_write_szx_48k(self):
        ram = [n % 256 for n in range(49152)]
        registers = {
            'a': 1,
            'b': 2,
            'c': 3,
            'd': 4,
            'e': 5,
            'f': 6,
            'h': 7,
            'i': 8,
            'ix': 9000,
            'iy': 10000,
            'l': 11,
            'pc': 12000,
            'r': 13,
            'sp': 14000,
            '^a': 15,
            '^b': 16,
            '^c': 17,
            '^d': 18,
            '^e': 19,
            '^f': 20,
            '^h': 21,
            '^l': 22
        }
        state = {
            'border': 1,
            'fe': 24,
            'iff': 0,
            'im': 2,
            'issue2': 1,
            'tstates': 12345
        }
        self._test_szx(ram, registers, state)

    def test_write_szx_128k(self):
        ram = [[(i + j) % 256 for i in range(16384)] for j in range(8)]
        registers = {
            'a': 1,
            'bc': 2300,
            'de': 4500,
            'f': 6,
            'hl': 7800,
            'i': 9,
            'ix': 10,
            'iy': 11,
            'pc': 1200,
            'r': 13,
            'sp': 14,
            '^a': 15,
            '^bc': 1617,
            '^de': 1819,
            '^f': 20,
            '^hl': 2122
        }
        state = {
            '7ffd': 17,
            'ay[0]': 1,
            'ay[1]': 2,
            'ay[2]': 3,
            'ay[3]': 4,
            'ay[4]': 5,
            'ay[5]': 6,
            'ay[6]': 7,
            'ay[7]': 8,
            'ay[8]': 9,
            'ay[9]': 10,
            'ay[10]': 11,
            'ay[11]': 12,
            'ay[12]': 13,
            'ay[13]': 14,
            'ay[14]': 15,
            'ay[15]': 16,
            'border': 1,
            'fffd': 3,
            'iff': 0,
            'im': 2,
            'issue2': 1,
            'tstates': 12345
        }
        self._test_szx(ram, registers, state)

    def test_write_szx_plus2(self):
        ram = [[(i + j) % 256 for i in range(16384)] for j in range(8)]
        registers = {
            'a': 1,
            'bc': 2300,
            'de': 4500,
            'f': 6,
            'hl': 7800,
            'i': 9,
            'ix': 10,
            'iy': 11,
            'pc': 1200,
            'r': 13,
            'sp': 14,
            '^a': 15,
            '^bc': 1617,
            '^de': 1819,
            '^f': 20,
            '^hl': 2122
        }
        state = {
            '7ffd': 17,
            'ay[0]': 1,
            'ay[1]': 2,
            'ay[2]': 3,
            'ay[3]': 4,
            'ay[4]': 5,
            'ay[5]': 6,
            'ay[6]': 7,
            'ay[7]': 8,
            'ay[8]': 9,
            'ay[9]': 10,
            'ay[10]': 11,
            'ay[11]': 12,
            'ay[12]': 13,
            'ay[13]': 14,
            'ay[14]': 15,
            'ay[15]': 16,
            'border': 1,
            'fffd': 3,
            'iff': 0,
            'im': 2,
            'issue2': 1,
            'tstates': 12345
        }
        self._test_szx(ram, registers, state, '+2')

    def test_default_registers_and_state_48k(self):
        ram = [0] * 49152
        registers = {}
        state = {}
        self._test_szx(ram, registers, state)

    def test_default_registers_and_state_128k(self):
        ram = [[0] * 16384] * 8
        registers = {}
        state = {}
        self._test_szx(ram, registers, state)

    def test_invalid_state(self):
        self._test_invalid_state()

    def test_invalid_registers(self):
        self._test_invalid_registers()

class WriteZ80Test(WriteSnapshotTest):
    def _decompress_block(self, ramz):
        block = []
        i = 0
        while i < len(ramz):
            b = ramz[i]
            i += 1
            if b == 237 and i < len(ramz):
                c = ramz[i]
                i += 1
                if c == 237:
                    length, byte = ramz[i], ramz[i + 1]
                    if length == 0:
                        raise SnapshotError(f'Found ED ED 00 {byte:02X}')
                    block += [byte] * length
                    i += 2
                else:
                    block += [b, c]
            else:
                block.append(b)
        return block

    def _decompress_ram(self, ramz):
        pages = {}
        j = 0
        while j < len(ramz):
            length = ramz[j] + 256 * ramz[j + 1]
            page = ramz[j + 2] - 3
            j += 3 + length
            pages[page] = self._decompress_block(ramz[j - length:j])
        return pages

    def _check_ram(self, z80, exp_ram):
        if len(exp_ram) == 8:
            exp_pages = {i: exp_ram[i] for i in range(8)}
        else:
            exp_pages = {1: exp_ram[16384:32768], 2: exp_ram[32768:], 5: exp_ram[:16384]}
        pages = self._decompress_ram(z80[86:])
        for n, ram in exp_pages.items():
            self.assertEqual(ram, pages[n])

    def _check_header(self, z80, ram, exp_registers, exp_state, machine):
        is128k = len(ram) == 8
        hw_mod = 128 if is128k and machine == '+2' else 0
        self.assertEqual(z80[0], exp_registers['a'])
        self.assertEqual(z80[1], exp_registers['f'])
        self.assertEqual(z80[2], exp_registers['c'])
        self.assertEqual(z80[3], exp_registers['b'])
        self.assertEqual(z80[4], exp_registers['l'])
        self.assertEqual(z80[5], exp_registers['h'])
        self.assertEqual(z80[6:8], (0, 0)) # v3 Z80 snapshot
        self.assertEqual(z80[8] + 256 * z80[9], exp_registers['sp'])
        self.assertEqual(z80[10], exp_registers['i'])
        self.assertEqual(z80[11], exp_registers['r'])
        self.assertEqual(z80[12], (exp_registers['r'] // 128) + (exp_state['border'] % 8) * 2)
        self.assertEqual(z80[13], exp_registers['e'])
        self.assertEqual(z80[14], exp_registers['d'])
        self.assertEqual(z80[15], exp_registers['^c'])
        self.assertEqual(z80[16], exp_registers['^b'])
        self.assertEqual(z80[17], exp_registers['^e'])
        self.assertEqual(z80[18], exp_registers['^d'])
        self.assertEqual(z80[19], exp_registers['^l'])
        self.assertEqual(z80[20], exp_registers['^h'])
        self.assertEqual(z80[21], exp_registers['^a'])
        self.assertEqual(z80[22], exp_registers['^f'])
        self.assertEqual(z80[23] + 256 * z80[24], exp_registers['iy'])
        self.assertEqual(z80[25] + 256 * z80[26], exp_registers['ix'])
        self.assertEqual(z80[27], exp_state['iff'] % 256)
        self.assertEqual(z80[28], exp_state['iff'] % 256)
        self.assertEqual(z80[29], (exp_state['im'] % 4) + (exp_state['issue2'] % 2) * 4)
        self.assertEqual(z80[30:32], (54, 0)) # Length of additional header block
        self.assertEqual(z80[32] + 256 * z80[33], exp_registers['pc'])
        self.assertEqual(z80[34], 4 if is128k else 0) # Hardware mode
        self.assertEqual(z80[35], exp_state['7ffd'] % 256)
        self.assertEqual(z80[36], 0) # Various flags
        self.assertEqual(z80[37], hw_mod) # Hardware modifier
        self.assertEqual(z80[38], exp_state['fffd'] % 256)
        for i in range(16):
            self.assertEqual(z80[39 + i], exp_state[f'ay[{i}]'])
        frame_duration = 70908 if is128k else 69888
        qframe_duration = frame_duration // 4
        t1 = (z80[55] + 256 * z80[56]) % qframe_duration
        t2 = (2 - z80[57]) % 4
        tstates = frame_duration - 1 - t2 * qframe_duration - t1
        self.assertEqual(tstates, exp_state['tstates'] % frame_duration)
        self.assertEqual(z80[58:86], (0,) * 28) # Various flags

    def _test_z80(self, ram, registers, state, machine=None):
        fname = '{}/test.z80'.format(self.make_directory())
        write_snapshot(fname, ram, [f'{k}={v}' for k, v in registers.items()], [f'{k}={v}' for k, v in state.items()], machine)
        with open(fname, 'rb') as f:
            z80 = tuple(f.read())
        self._check_header(z80, ram, self._normalise_registers(registers), self._fill_state(state), machine)
        self._check_ram(z80, ram)

    def _test_bad_spec(self, exp_error, ram, registers=(), state=()):
        fname = '{}/test.szx'.format(self.make_directory())
        with self.assertRaises(SkoolKitError) as cm:
            write_snapshot(fname, ram, registers, state)
        self.assertEqual(cm.exception.args[0], exp_error)

    def test_write_z80_48k(self):
        ram = [n % 256 for n in range(49152)]
        registers = {
            'a': 1,
            'b': 2,
            'c': 3,
            'd': 4,
            'e': 5,
            'f': 6,
            'h': 7,
            'i': 8,
            'ix': 9000,
            'iy': 10000,
            'l': 11,
            'pc': 12000,
            'r': 13,
            'sp': 14000,
            '^a': 15,
            '^b': 16,
            '^c': 17,
            '^d': 18,
            '^e': 19,
            '^f': 20,
            '^h': 21,
            '^l': 22
        }
        state = {
            'border': 1,
            'iff': 0,
            'im': 2,
            'issue2': 1,
            'tstates': 12345
        }
        self._test_z80(ram, registers, state)

    def test_write_z80_128k(self):
        ram = [[(i + j) % 256 for i in range(16384)] for j in range(8)]
        registers = {
            'a': 1,
            'bc': 2300,
            'de': 4500,
            'f': 6,
            'hl': 7800,
            'i': 9,
            'ix': 1000,
            'iy': 1100,
            'pc': 1200,
            'r': 131,
            'sp': 14,
            '^a': 15,
            '^bc': 1617,
            '^de': 1819,
            '^f': 20,
            '^hl': 2122
        }
        state = {
            '7ffd': 17,
            'ay[0]': 1,
            'ay[1]': 2,
            'ay[2]': 3,
            'ay[3]': 4,
            'ay[4]': 5,
            'ay[5]': 6,
            'ay[6]': 7,
            'ay[7]': 8,
            'ay[8]': 9,
            'ay[9]': 10,
            'ay[10]': 11,
            'ay[11]': 12,
            'ay[12]': 13,
            'ay[13]': 14,
            'ay[14]': 15,
            'ay[15]': 16,
            'border': 1,
            'fffd': 3,
            'iff': 0,
            'im': 2,
            'issue2': 1,
            'tstates': 12345
        }
        self._test_z80(ram, registers, state)

    def test_write_z80_plus2(self):
        ram = [[(i + j) % 256 for i in range(16384)] for j in range(8)]
        registers = {
            'a': 1,
            'bc': 2300,
            'de': 4500,
            'f': 6,
            'hl': 7800,
            'i': 9,
            'ix': 1000,
            'iy': 1100,
            'pc': 1200,
            'r': 131,
            'sp': 14,
            '^a': 15,
            '^bc': 1617,
            '^de': 1819,
            '^f': 20,
            '^hl': 2122
        }
        state = {
            '7ffd': 17,
            'ay[0]': 1,
            'ay[1]': 2,
            'ay[2]': 3,
            'ay[3]': 4,
            'ay[4]': 5,
            'ay[5]': 6,
            'ay[6]': 7,
            'ay[7]': 8,
            'ay[8]': 9,
            'ay[9]': 10,
            'ay[10]': 11,
            'ay[11]': 12,
            'ay[12]': 13,
            'ay[13]': 14,
            'ay[14]': 15,
            'ay[15]': 16,
            'border': 1,
            'fffd': 3,
            'iff': 0,
            'im': 2,
            'issue2': 1,
            'tstates': 12345
        }
        self._test_z80(ram, registers, state, '+2')

    def test_invalid_state(self):
        self._test_invalid_state()

    def _test_invalid_registers(self):
        self._test_invalid_registers()
