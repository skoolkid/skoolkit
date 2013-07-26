# -*- coding: utf-8 -*-
import unittest
from zipfile import ZipFile

from skoolkittest import SkoolKitTestCase
from skoolkit import tap2sna, VERSION
from skoolkit.snapshot import get_snapshot

class Tap2SnaTest(SkoolKitTestCase):
    def _write_tap(self, blocks, zip_archive=False, tap_name=None):
        tap_data = []
        for block in blocks:
            tap_data.extend(block)
        if zip_archive:
            archive_fname = self.write_bin_file(suffix='.zip')
            with ZipFile(archive_fname, 'w') as archive:
                archive.writestr(tap_name or 'game.tap', bytes(bytearray(tap_data)))
            return archive_fname
        return self.write_bin_file(tap_data, suffix='.tap')

    def _write_tzx(self, blocks, zip_archive=False, tzx_name=None):
        tzx_data = [ord(c) for c in "ZXTape!"]
        tzx_data.extend((26, 1, 20))
        for block in blocks:
            tzx_data.extend(block)
        if zip_archive:
            archive_fname = self.write_bin_file(suffix='.zip')
            with ZipFile(archive_fname, 'w') as archive:
                archive.writestr(tzx_name or 'game.tzx', bytes(bytearray(tzx_data)))
            return archive_fname
        return self.write_bin_file(tzx_data, suffix='.tzx')

    def _create_data_block(self, data):
        parity = 0
        for b in data:
            parity ^= b
        return [255] + data + [parity]

    def _create_tap_data_block(self, data):
        data_block = self._create_data_block(data)
        length = len(data_block)
        return [length % 256, length // 256] + data_block

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

    def test_tap_file_in_zip_archive(self):
        data = [1]
        block = self._create_tap_data_block(data)
        tap_name = 'game.tap'
        zip_fname = self._write_tap([block], zip_archive=True, tap_name=tap_name)
        z80file = self.write_bin_file(suffix='.z80')
        start = 16385
        output, error = self.run_tap2sna('--force --ram load=1,{} {} {}'.format(start, zip_fname, z80file))
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0], 'Extracting {}'.format(tap_name))
        self.assertEqual(output[1], 'Writing {}'.format(z80file))
        self.assertEqual(error, '')
        snapshot = get_snapshot(z80file)
        self.assertEqual(snapshot[start:start + len(data)], data)

    def test_tzx_block_0x10(self):
        data = [1, 2, 4]
        block = [16] # Block ID
        block.extend((0, 0)) # Pause duration
        data_block = self._create_data_block(data)
        length = len(data_block)
        block.extend((length % 256, length // 256))
        block.extend(data_block)
        tzxfile = self._write_tzx([block])
        z80file = self.write_bin_file(suffix='.z80')
        start = 16386
        output, error = self.run_tap2sna('--force --ram load=1,{} {} {}'.format(start, tzxfile, z80file))
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], 'Writing {}'.format(z80file))
        self.assertEqual(error, '')
        snapshot = get_snapshot(z80file)
        self.assertEqual(snapshot[start:start + len(data)], data)

    def test_tzx_block_0x11(self):
        data = [2, 3, 5]
        block = [17] # Block ID
        block.extend([0] * 15)
        data_block = self._create_data_block(data)
        length = len(data_block)
        block.extend((length % 256, length // 256, 0))
        block.extend(data_block)
        tzxfile = self._write_tzx([block])
        z80file = self.write_bin_file(suffix='.z80')
        start = 16387
        output, error = self.run_tap2sna('--force --ram load=1,{} {} {}'.format(start, tzxfile, z80file))
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], 'Writing {}'.format(z80file))
        self.assertEqual(error, '')
        snapshot = get_snapshot(z80file)
        self.assertEqual(snapshot[start:start + len(data)], data)

    def test_tzx_with_unsupported_blocks(self):
        blocks = []
        blocks.append((18, 0, 0, 0, 0)) # 0x12 Pure Tone
        blocks.append((19, 2, 0, 0, 0, 0)) # 0x13 Pulse sequence
        blocks.append([20] + [0] * 7 + [1, 0, 0, 0]) # 0x14 Pure Data Block
        blocks.append([21] + [0] * 5 + [1, 0, 0, 0]) # 0x15 Direct Recording
        blocks.append([24, 11] + [0] * 14) # 0x18 CSW Recording
        blocks.append([25, 20] + [0] * 23) # 0x19 Generalized Data Block
        blocks.append((32, 0, 0)) # 0x20 Pause (silence) or 'Stop the Tape' command
        blocks.append((33, 1, 32)) # 0x21 Group start
        blocks.append((34,)) # 0x22 - Group end
        blocks.append((35, 0, 0)) # 0x23 Jump to block
        blocks.append((36, 2, 0)) # 0x24 Loop start
        blocks.append((37,)) # 0x25 Loop end
        blocks.append((38, 1, 0, 0, 0)) # 0x26 Call sequence
        blocks.append((39,)) # 0x27 Return from sequence
        blocks.append((40, 5, 0, 1, 0, 0, 1, 32)) # 0x28 Select block
        blocks.append((42, 0, 0, 0, 0)) # 0x2A Stop the tape if in 48K mode
        blocks.append((43, 1, 0, 0, 0, 1)) # 0x2B Set signal level
        blocks.append((48, 1, 65)) # 0x30 Text description
        blocks.append((49, 0, 1, 66)) # 0x31 Message block
        blocks.append((50, 4, 0, 1, 0, 1, 33)) # 0x32 Archive info
        blocks.append((51, 1, 0, 0, 0)) # 0x33 Hardware type
        blocks.append([53] + [32] * 16 + [1] + [0] * 4) # 0x35 Custom info block
        blocks.append([90] + [0] * 9) # 0x5A "Glue" block
        data = [2, 4, 6]
        block = [16] # Block ID
        block.extend((0, 0)) # Pause duration
        data_block = self._create_data_block(data)
        length = len(data_block)
        block.extend((length % 256, length // 256))
        block.extend(data_block)
        blocks.append(block)
        tzxfile = self._write_tzx(blocks)
        z80file = self.write_bin_file(suffix='.z80')
        start = 16388
        output, error = self.run_tap2sna('--force --ram load=1,{} {} {}'.format(start, tzxfile, z80file))
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], 'Writing {}'.format(z80file))
        self.assertEqual(error, '')
        snapshot = get_snapshot(z80file)
        self.assertEqual(snapshot[start:start + len(data)], data)

if __name__ == '__main__':
    unittest.main()
