# -*- coding: utf-8 -*-
import os
import unittest
from zipfile import ZipFile
from io import BytesIO
try:
    from mock import patch, Mock
except ImportError:
    from unittest.mock import patch, Mock

from skoolkittest import SkoolKitTestCase
from skoolkit import tap2sna, VERSION, SkoolKitError
from skoolkit.snapshot import get_snapshot

def mock_write_z80(ram, namespace, z80):
    global snapshot
    snapshot = [0] * 16384 + ram

def _get_parity(data):
    parity = 0
    for b in data:
        parity ^= b
    return parity

def _create_data_block(data):
    parity = 0
    for b in data:
        parity ^= b
    return [255] + data + [_get_parity(data)]

def _create_tap_data_block(data):
    data_block = _create_data_block(data)
    length = len(data_block)
    return [length % 256, length // 256] + data_block

def _create_tap_bytes_header_block(start, length=0):
    header = []
    header.append(0)                             # Header block marker
    header.append(3)                             # Bytes
    header.extend([32] * 10)
    header.extend((length % 256, length // 256)) # Length
    header.extend((start % 256, start // 256))   # Start address
    header.extend((0, 0))
    header.append(_get_parity(header))
    return [19, 0] + header

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

    def _get_snapshot(self, start=16384, data=None, options='', load_options=None, blocks=None, tzx=False):
        if blocks is None:
            blocks = [_create_tap_data_block(data)]
        if tzx:
            tape_file = self._write_tzx(blocks)
        else:
            tape_file = self._write_tap(blocks)
        z80file = self.write_bin_file(suffix='.z80')
        if load_options is None:
            load_options = '--ram load=1,{}'.format(start)
        output, error = self.run_tap2sna('--force {} {} {} {}'.format(load_options, options, tape_file, z80file))
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], 'Writing {}'.format(z80file))
        self.assertEqual(error, '')
        return get_snapshot(z80file)

    def _test_bad_spec(self, option, bad_spec, exp_error):
        odir = self.make_directory()
        tapfile = self._write_tap([_create_tap_data_block([1])])
        z80fname = 'test.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna('--ram load=1,16384 {} {} -d {} {} {}'.format(option, bad_spec, odir, tapfile, z80fname))
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot {}: {}: {}'.format(z80fname, exp_error, bad_spec))

    def test_no_arguments(self):
        output, error = self.run_tap2sna(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage:'))

    def test_invalid_arguments(self):
        for args in ('--foo', '-k test.zip'):
            output, error = self.run_tap2sna(args, catch_exit=2)
            self.assertEqual(len(output), 0)
            self.assertTrue(error.startswith('usage:'))

    def test_option_d(self):
        odir = 'tap2sna-{}'.format(os.getpid())
        self.tempdirs.append(odir)
        block = _create_tap_data_block([0])
        tapfile = self._write_tap([block])
        z80_fname = 'test.z80'
        for option in ('-d', '--output-dir'):
            output, error = self.run_tap2sna('{} {} {} {}'.format(option, odir, tapfile, z80_fname))
            self.assertEqual(len(error), 0)
            self.assertTrue(os.path.isfile(os.path.join(odir, z80_fname)))

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_tap2sna(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

    def test_nonexistent_tap_file(self):
        tap_fname = 'test.tap'
        z80_fname = 'test.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna('{} {}'.format(tap_fname, z80_fname))
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot {}: {}: file not found'.format(z80_fname, tap_fname))

    def test_zip_archive_with_no_tape_file(self):
        archive_fname = self.write_bin_file(suffix='.zip')
        with ZipFile(archive_fname, 'w') as archive:
            archive.writestr('game.txt', bytes(bytearray((1, 2))))
        z80_fname = 'test.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna('{} {}'.format(archive_fname, z80_fname))
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot {}: No TAP or TZX file found'.format(z80_fname))

    def test_standard_load(self):
        basic_header = []
        basic_header.append(0)        # Header block marker
        basic_header.append(0)        # BASIC program follows
        basic_header.extend([0] * 10)
        basic_header.extend((1, 0))   # Length
        basic_header.extend([0] * 4)
        basic_header.append(_get_parity(basic_header))
        basic_data = [1]
        blocks = [[19, 0] + basic_header, _create_tap_data_block(basic_data)]
        code_start = 32768
        code_header = _create_tap_bytes_header_block(code_start)
        code = [2]
        blocks.append(code_header)
        blocks.append(_create_tap_data_block(code))

        tapfile = self._write_tap(blocks)
        z80file = self.write_bin_file(suffix='.z80')
        output, error = self.run_tap2sna('--force {} {}'.format(tapfile, z80file))
        self.assertEqual(error, '')
        snapshot = get_snapshot(z80file)
        self.assertEqual(snapshot[23755:23755 + len(basic_data)], basic_data)
        self.assertEqual(snapshot[code_start:code_start + len(code)], code)

    def test_standard_load_ignores_headerless_block(self):
        code_start = 16384
        code_header = _create_tap_bytes_header_block(code_start)
        code = [2]
        blocks = [code_header, _create_tap_data_block(code)]
        blocks.append(_create_tap_data_block([23]))

        tapfile = self._write_tap(blocks)
        z80file = self.write_bin_file(suffix='.z80')
        output, error = self.run_tap2sna('--force {} {}'.format(tapfile, z80file))
        self.assertEqual(error, '')
        snapshot = get_snapshot(z80file)
        self.assertEqual(snapshot[code_start:code_start + len(code)], code)

    def test_standard_load_with_unknown_block_type(self):
        block_type = 1 # Array of numbers
        header = []
        header.extend((19, 0))    # Length of header block
        header.append(0)          # Header block marker
        header.append(block_type)
        header.extend([0] * 16)
        header.append(_get_parity(header))
        data = [1]
        blocks = [header, _create_tap_data_block(data)]

        tapfile = self._write_tap(blocks)
        z80file = self.write_bin_file(suffix='.z80')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna('--force {} {}'.format(tapfile, z80file))
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot {}: Unknown block type ({}) in header block 1'.format(z80file, block_type))

    def test_ram_load(self):
        start = 16384
        data = [1, 2, 3]
        snapshot = self._get_snapshot(start, data)
        self.assertEqual(snapshot[start:start + len(data)], data)

    def test_ram_load_with_length(self):
        start = 16384
        data = [1, 2, 3, 4]
        length = 2
        snapshot = self._get_snapshot(start, data, load_options='--ram load=1,{},{}'.format(start, length))
        self.assertEqual(snapshot[start:start + length], data[:length])
        self.assertEqual(snapshot[start + length:start + len(data)], [0] * (len(data) - length))

    def test_ram_load_with_step(self):
        start = 16385
        data = [5, 4, 3]
        step = 2
        snapshot = self._get_snapshot(start, data, load_options='--ram load=1,{},,{}'.format(start, step))
        self.assertEqual(snapshot[start:start + len(data) * step:step], data)

    def test_ram_load_with_offset(self):
        start = 16384
        data = [15, 16, 17]
        offset = 5
        snapshot = self._get_snapshot(start, data, load_options='--ram load=1,{},,,{}'.format(start, offset))
        self.assertEqual(snapshot[start + offset:start + offset + len(data)], data)

    def test_ram_load_with_increment(self):
        start = 65534
        data = [8, 9, 10]
        inc = 65533
        snapshot = self._get_snapshot(start, data, load_options='--ram load=1,{},,,,{}'.format(start, inc))
        self.assertEqual(snapshot[65533:], [data[2]] + data[:2])

    def test_ram_load_wraparound_with_step(self):
        start = 65535
        data = [23, 24, 25]
        step = 8193
        snapshot = self._get_snapshot(start, data, load_options='--ram load=1,{},,{}'.format(start, step))
        self.assertEqual(snapshot[start], data[0])
        self.assertEqual(snapshot[(start + 2 * step) & 65535], data[2])

    def test_ram_load_bad_address(self):
        self._test_bad_spec('--ram', 'load=1,abcde', 'Cannot parse integer')

    def test_ram_poke_single_address(self):
        start = 16384
        data = [4, 5, 6]
        poke_addr = 16386
        poke_val = 255
        snapshot = self._get_snapshot(start, data, '--ram poke={},{}'.format(poke_addr, poke_val))
        self.assertEqual(snapshot[start:start + 2], data[:2])
        self.assertEqual(snapshot[poke_addr], poke_val)

    def test_ram_poke_address_range(self):
        start = 16384
        data = [1, 1, 1]
        poke_addr_start = 16384
        poke_addr_end = 16383 + len(data)
        poke_val = 254
        snapshot = self._get_snapshot(start, data, '--ram poke={}-{},{}'.format(poke_addr_start, poke_addr_end, poke_val))
        self.assertEqual(snapshot[poke_addr_start:poke_addr_end + 1], [poke_val] * len(data))

    def test_ram_poke_address_range_with_step(self):
        start = 16384
        data = [2, 9, 2]
        poke_addr_start = 16384
        poke_addr_end = 16386
        poke_step = 2
        poke_val = 253
        snapshot = self._get_snapshot(start, data, '--ram poke={}-{}-{},{}'.format(poke_addr_start, poke_addr_end, poke_step, poke_val))
        self.assertEqual(snapshot[poke_addr_start:poke_addr_end + 1:poke_step], [poke_val] * (1 + (poke_addr_end + 1 - poke_addr_start) // poke_step))

    def test_ram_poke_hex_address(self):
        address, value = 16385, 253
        snapshot = self._get_snapshot(16384, [1], '--ram poke=${:X},{}'.format(address, value))
        self.assertEqual(snapshot[address], value)

    def test_ram_poke_bad_value(self):
        self._test_bad_spec('--ram', 'poke=16384,$g', 'Cannot parse integer')

    def test_ram_move(self):
        start = 16384
        data = [5, 6, 7]
        src = start
        size = len(data)
        dest = 16387
        snapshot = self._get_snapshot(start, data, '--ram move={},{},{}'.format(src, size, dest))
        self.assertEqual(snapshot[start:start + len(data)], data)
        self.assertEqual(snapshot[dest:dest + len(data)], data)

    def test_ram_move_hex_address(self):
        src, size, dest = 16384, 1, 16385
        value = 3
        snapshot = self._get_snapshot(src, [value], '--ram move=${:X},{},${:x}'.format(src, size, dest))
        self.assertEqual(snapshot[dest], value)

    def test_ram_move_bad_address(self):
        self._test_bad_spec('--ram', 'move=16384,1,$800Z', 'Cannot parse integer')

    def test_ram_invalid_operation(self):
        self._test_bad_spec('--ram', 'foo=bar', 'Invalid operation')

    def test_ram_help(self):
        output, error = self.run_tap2sna('--ram help')
        self.assertEqual(output[0], 'Usage: --ram load=block,start[,length,step,offset,inc]')
        self.assertEqual(error, '')

    def test_tap_file_in_zip_archive(self):
        data = [1]
        block = _create_tap_data_block(data)
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

    def test_invalid_tzx_file(self):
        tzxfile = self.write_bin_file([1, 2, 3], suffix='.tzx')
        z80file = 'test.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna('{} {}'.format(tzxfile, z80file))
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot {}: Not a TZX file'.format(z80file))

    def test_tzx_block_0x10(self):
        data = [1, 2, 4]
        block = [16] # Block ID
        block.extend((0, 0)) # Pause duration
        data_block = _create_data_block(data)
        length = len(data_block)
        block.extend((length % 256, length // 256))
        block.extend(data_block)
        start = 16386
        snapshot = self._get_snapshot(start, blocks=[block], tzx=True)
        self.assertEqual(snapshot[start:start + len(data)], data)

    def test_tzx_block_0x11(self):
        data = [2, 3, 5]
        block = [17] # Block ID
        block.extend([0] * 15)
        data_block = _create_data_block(data)
        length = len(data_block)
        block.extend((length % 256, length // 256, 0))
        block.extend(data_block)
        start = 16387
        snapshot = self._get_snapshot(start, blocks=[block], tzx=True)
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
        data_block = _create_data_block(data)
        length = len(data_block)
        block.extend((length % 256, length // 256))
        block.extend(data_block)
        blocks.append(block)
        start = 16388
        snapshot = self._get_snapshot(start, blocks=blocks, tzx=True)
        self.assertEqual(snapshot[start:start + len(data)], data)

    def test_tzx_with_unknown_block(self):
        block_id = 22
        block = [block_id, 0]
        tzxfile = self._write_tzx([block])
        z80file = 'test.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna('{} {}'.format(tzxfile, z80file))
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot {}: Unknown TZX block ID: 0x{:X}'.format(z80file, block_id))

    def test_reg(self):
        z80_registers = {
            'a': 0, 'f': 1, 'bc': 2, 'c': 2, 'b': 3, 'hl': 4, 'l': 4, 'h': 5,
            'sp': 8, 'i': 10, 'r': 11, 'de': 13, 'e': 13, 'd': 14, '^bc': 15,
            '^c': 15, '^b': 16, '^de': 17, '^e': 17, '^d': 18, '^hl': 19,
            '^l': 19, '^h': 20, '^a': 21, '^f': 22, 'iy': 23, 'ix': 25,
            'pc': 32
        }
        block = _create_tap_data_block([1])
        tapfile = self._write_tap([block])
        z80file = self.write_bin_file(suffix='.z80')
        reg_dicts = (
            {'^a': 1, '^b': 2, '^c': 3, '^d': 4, '^e': 5, '^f': 6, '^h': 7, '^l': 8},
            {'a': 9, 'b': 10, 'c': 11, 'd': 12, 'e': 13, 'f': 14, 'h': 15, 'l': 16, 'r': 129},
            {'^bc': 258, '^de': 515, '^hl': 65534, 'bc': 259, 'de': 516, 'hl': 65533},
            {'i': 13, 'ix': 1027, 'iy': 1284, 'pc': 1541, 'r': 23, 'sp': 32769}
        )
        for reg_dict in reg_dicts:
            reg_options = ' '.join(['--reg {}={}'.format(r, v) for r, v in reg_dict.items()])
            output, error = self.run_tap2sna('--force --ram load=1,16384 {} {} {}'.format(reg_options, tapfile, z80file))
            self.assertEqual(error, '')
            with open(z80file, 'rb') as f:
                z80_header = bytearray(f.read(34))
            for reg, exp_value in reg_dict.items():
                offset = z80_registers[reg]
                size = len(reg) - 1 if reg.startswith('^') else len(reg)
                if size == 1:
                    value = z80_header[offset]
                else:
                    value = z80_header[offset] + 256 * z80_header[offset + 1]
                self.assertEqual(value, exp_value)
                if reg == 'r' and exp_value & 128:
                    self.assertEqual(z80_header[12] & 1, 1)

    def test_reg_hex_value(self):
        odir = self.make_directory()
        tapfile = self._write_tap([_create_tap_data_block([1])])
        z80fname = 'test.z80'
        reg_value = 35487
        output, error = self.run_tap2sna('--ram load=1,16384 --reg bc=${:x} -d {} {} {}'.format(reg_value, odir, tapfile, z80fname))
        self.assertEqual(error, '')
        with open(os.path.join(odir, z80fname), 'rb') as f:
            z80_header = bytearray(f.read(4))
        self.assertEqual(z80_header[2] + 256 * z80_header[3], reg_value)

    def test_reg_bad_value(self):
        self._test_bad_spec('--reg', 'bc=A2', 'Cannot parse register value')

    def test_ram_invalid_register(self):
        self._test_bad_spec('--reg', 'iz=1', 'Invalid register')

    def test_reg_help(self):
        output, error = self.run_tap2sna('--reg help')
        self.assertEqual(output[0], 'Usage: --reg name=value')
        self.assertEqual(error, '')

    def test_state_iff(self):
        block = _create_tap_data_block([0])
        tapfile = self._write_tap([block])
        z80file = self.write_bin_file(suffix='.z80')
        iff_value = 1
        output, error = self.run_tap2sna('--force --ram load=1,16384 --state iff={} {} {}'.format(iff_value, tapfile, z80file))
        self.assertEqual(error, '')
        with open(z80file, 'rb') as f:
            z80_header = bytearray(f.read(28))
        self.assertEqual(z80_header[27], iff_value)

    def test_state_iff_bad_value(self):
        self._test_bad_spec('--state', 'iff=fa', 'Cannot parse integer')

    def test_state_im(self):
        block = _create_tap_data_block([0])
        tapfile = self._write_tap([block])
        z80file = self.write_bin_file(suffix='.z80')
        im_value = 2
        output, error = self.run_tap2sna('--force --ram load=1,16384 --state im={} {} {}'.format(im_value, tapfile, z80file))
        self.assertEqual(error, '')
        with open(z80file, 'rb') as f:
            z80_header = bytearray(f.read(30))
        self.assertEqual(z80_header[29] & 3, im_value)

    def test_state_im_bad_value(self):
        self._test_bad_spec('--state', 'im=Q', 'Cannot parse integer')

    def test_state_border(self):
        block = _create_tap_data_block([0])
        tapfile = self._write_tap([block])
        z80file = self.write_bin_file(suffix='.z80')
        border = 4
        output, error = self.run_tap2sna('--force --ram load=1,16384 --state border={} {} {}'.format(border, tapfile, z80file))
        self.assertEqual(error, '')
        with open(z80file, 'rb') as f:
            z80_header = bytearray(f.read(13))
        self.assertEqual((z80_header[12] // 2) & 7, border)

    def test_state_border_bad_value(self):
        self._test_bad_spec('--state', 'border=x!', 'Cannot parse integer')

    def test_state_invalid_parameter(self):
        self._test_bad_spec('--state', 'baz=2', 'Invalid parameter')

    def test_state_help(self):
        output, error = self.run_tap2sna('--state help')
        self.assertEqual(output[0], 'Usage: --state name=value')
        self.assertEqual(error, '')

    def test_args_from_file(self):
        data = [1, 2, 3, 4]
        start = 49152
        args = '\n'.join((
            '; Comment',
            '# Another comment',
            '--force ; Overwrite',
            '--ram load=1,{} # Load first block'.format(start)
        ))
        args_file = self.write_text_file(args, suffix='.t2s')
        snapshot = self._get_snapshot(start, data, '@{}'.format(args_file))
        self.assertEqual(snapshot[start:start + len(data)], data)

    @patch.object(tap2sna, 'urlopen', Mock(return_value=BytesIO(bytearray(_create_tap_data_block([2, 3])))))
    @patch.object(tap2sna, 'write_z80', mock_write_z80)
    def test_remote_download(self):
        data = [2, 3]
        start = 17000
        url = 'http://example.com/test.tap'
        output, error = self.run_tap2sna('--ram load=1,{} {} test.z80'.format(start, url))
        self.assertEqual(output[0], 'Downloading {}'.format(url))
        self.assertEqual(error, '')
        self.assertEqual(snapshot[start:start + len(data)], data)

    def test_no_clobber(self):
        block = _create_tap_data_block([0])
        tapfile = self._write_tap([block])
        z80file = self.write_bin_file(suffix='.z80')
        output, error = self.run_tap2sna('--ram load=1,16384 {} {}'.format(tapfile, z80file))
        self.assertEqual(output[0], '{}: file already exists; use -f to overwrite'.format(z80file))
        self.assertEqual(error, '')

if __name__ == '__main__':
    unittest.main()
