from skoolkittest import SkoolKitTestCase
from skoolkit.snapshot import get_snapshot, make_z80_ram_block, set_z80_registers, set_z80_state, SnapshotError

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
        with self.assertRaisesRegex(SnapshotError, "{}: Unknown file type".format(snapshot_file)):
            get_snapshot(snapshot_file)

    def test_bad_ram_size(self):
        ram_size = 3
        with self.assertRaisesRegex(SnapshotError, 'RAM size is {}'.format(ram_size)):
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
        block = make_z80_ram_block(data, 0)
        exp_data = [len(data), 0, 0] + data
        self.assertEqual(exp_data, block)

    def test_single_ED_followed_by_six_identical_values(self):
        data = [237, 2, 2, 2, 2, 2, 2]
        block = make_z80_ram_block(data, 0)
        exp_data = [6, 0, 0, 237, 2, 237, 237, 5, 2]
        self.assertEqual(exp_data, block)

    def test_block_ending_with_single_ED(self):
        data = [0, 237]
        exp_data = [2, 0, 0, 0, 237]
        self.assertEqual(exp_data, make_z80_ram_block(data, 0))

class Z80StateTest(SkoolKitTestCase):
    def test_iff(self):
        header = [255] * 30
        for iff in (0, 1):
            set_z80_state(header, f'iff={iff}')
            self.assertEqual([iff, iff], header[27:29])

    def test_im(self):
        header = [255] * 30
        for im in (0, 1, 2):
            set_z80_state(header, f'im={im}')
            self.assertEqual(header[29], 252 + im)

    def test_border(self):
        header = [255] * 30
        for border in range(8):
            set_z80_state(header, f'border={border}')
            self.assertEqual(header[12], 241 + border * 2)

    def test_tstates(self):
        header = [255] * 58
        for tstates in (0, 1000, 17471, 17472, 20000, 38000, 56000, 69887, 69888):
            set_z80_state(header, f'tstates={tstates}')
            t_lo = header[55] + 256 * header[56]
            t_hi = header[57]
            t = 69887 - ((2 - t_hi) % 4) * 17472 - (t_lo % 17472)
            self.assertEqual(t, tstates % 69888)

    def test_issue2(self):
        header = [255] * 30
        for issue2 in (0, 1):
            set_z80_state(header, f'issue2={issue2}')
            self.assertEqual(header[29], 251 + issue2 * 4)

    def test_all(self):
        header = [255] * 58
        set_z80_state(header, 'iff=0', 'im=2', 'border=3', 'tstates=17471', 'issue2=0')
        self.assertEqual(header[27], 0) # IFF1
        self.assertEqual(header[28], 0) # IFF2
        self.assertEqual(header[29], 250) # IM (bits 0-1), issue 2 (bit 2)
        self.assertEqual(header[12], 247) # Border (bits 1-3)
        self.assertEqual([0, 0, 3], header[55:58]) # T-states

class Z80RegistersTest(SkoolKitTestCase):
    def test_8_bit_registers(self):
        reg = {
            'a': 1, 'f': 2, 'b': 3, 'c': 4, 'd': 5, 'e': 6, 'h': 7, 'l': 8, 'i': 9, 'r': 10,
            '^a': 11, '^f': 12, '^b': 13, '^c':14, '^d': 15, '^e': 16, '^h': 17, '^l': 18
        }
        for p, f in (('', 'd'), ('$', '02x'), ('0x', '02x'), ('%', '08b')):
            header = [0] * 33
            specs = [f'{r}={p}{v:{f}}' for r, v in reg.items()]
            set_z80_registers(header, *specs)
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
            header = [0] * 33
            specs = [f'{r}={p}{v:{f}}' for r, v in reg.items()]
            set_z80_registers(header, *specs)
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
        header = [255] * 33
        set_z80_registers(header, 'r=1')
        self.assertEqual(header[11], 1)
        self.assertEqual(header[12], 254)

    def test_r_with_bit_7_set(self):
        header = [0] * 33
        set_z80_registers(header, 'r=240')
        self.assertEqual(header[11], 240)
        self.assertEqual(header[12], 1)

class SZXTest(SnapshotTest):
    def _test_szx(self, exp_ram, compress, machine_id=1, ch7ffd=0, pages={}, page=None):
        tmp_szx = self.write_szx(exp_ram, compress, machine_id, ch7ffd, pages)
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
