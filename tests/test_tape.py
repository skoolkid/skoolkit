from skoolkittest import SkoolKitTestCase, as_dword
from skoolkit.tape import TapeError, parse_pzx, parse_tzx, write_pzx, write_tap

def get_pzx_blocks(fname):
    blocks = []
    with open(fname, 'rb') as f:
        pzx = f.read()
    i = 0
    while i < len(pzx):
        block_id = ''.join(chr(b) for b in pzx[i:i + 4])
        i += 4
        block_len = pzx[i] + 256 * pzx[i + 1] + 65536 * pzx[i + 2] + 16777216 * pzx[i + 3]
        i += 4
        blocks.append((block_id, tuple(pzx[i:i + block_len])))
        i += block_len
    return blocks

def get_tap_blocks(fname):
    blocks = []
    with open(fname, 'rb') as f:
        tap = f.read()
    i = 0
    while i + 1 < len(tap):
        block_len = tap[i] + 256 * tap[i + 1]
        blocks.append(list(tap[i + 2:i + 2 + block_len]))
        i += block_len + 2
    return blocks

def to_pzx_data(data):
    bits = 0x80000000 + len(data) * 8
    return (
        *as_dword(bits), # Polarity and bit count
        177, 3,          # Tail pulse (945)
        2, 2,            # p0, p1
        87, 3, 87, 3,    # s0 (855, 855)
        174, 6, 174, 6,  # s1 (1710, 1710)
        *data            # Data
    )

class PZXTest(SkoolKitTestCase):
    def _get_pzxt(self):
        return bytearray((
            80, 90, 88, 84, # PZXT
            2, 0, 0, 0,     # Block length (2)
            1, 0,           # Major/minor version number
        ))

    def test_pzx_file_too_short(self):
        pzx = b'PZXT'
        with self.assertRaises(TapeError) as cm:
            parse_pzx(pzx)
        self.assertEqual(cm.exception.args[0], 'Not a PZX file')

    def test_pzxt_block_missing_data(self):
        pzx = bytes((
            80, 90, 88, 84, # PZXT
            5, 0, 0, 0,     # Block length (5)
            0, 0            # 2 bytes instead of 5
        ))
        tape = parse_pzx(pzx)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, 'PZXT block missing 3 byte(s)')

    def test_pzxt_block_too_short(self):
        pzx = bytes((
            80, 90, 88, 84, # PZXT
            1, 0, 0, 0,     # Block length (1)
            0
        ))
        tape = parse_pzx(pzx)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, 'PZXT block length (1) is too small')

    def test_data_block_missing_data(self):
        pzx = self._get_pzxt()
        pzx.extend((
            68, 65, 84, 65, # DATA
            5, 0, 0, 0,     # Block length (5)
            0               # 1 byte instead of 5
        ))
        tape = parse_pzx(pzx)
        self.assertEqual(len(tape.blocks), 1)
        self.assertEqual(tape.error, 'DATA block missing 4 byte(s)')

    def test_data_block_too_short(self):
        pzx = self._get_pzxt()
        pzx.extend((
            68, 65, 84, 65, # DATA
            7, 0, 0, 0,     # Block length (7)
            1, 0, 0, 0,     # count
            0, 0,           # tail
            2               # p0
        ))
        tape = parse_pzx(pzx)
        self.assertEqual(len(tape.blocks), 1)
        self.assertEqual(tape.error, 'DATA block length (7) is too small')

    def test_data_block_missing_data_in_s0_field(self):
        pzx = self._get_pzxt()
        pzx.extend((
            68, 65, 84, 65, # DATA
            11, 0, 0, 0,    # Block length (11)
            1, 0, 0, 0,     # count
            0, 0,           # tail
            2,              # p0
            2,              # p1
            1, 0, 1         # s0 (1 byte short)
        ))
        tape = parse_pzx(pzx)
        self.assertEqual(len(tape.blocks), 1)
        self.assertEqual(tape.error, 'DATA block missing 1 byte(s) in s0 field')

    def test_data_block_missing_data_in_s1_field(self):
        pzx = self._get_pzxt()
        pzx.extend((
            68, 65, 84, 65, # DATA
            15, 0, 0, 0,    # Block length (15)
            1, 0, 0, 0,     # count
            0, 0,           # tail
            2,              # p0
            2,              # p1
            1, 0, 1, 0,     # s0
            2, 0, 2         # s1 (1 byte short)
        ))
        tape = parse_pzx(pzx)
        self.assertEqual(len(tape.blocks), 1)
        self.assertEqual(tape.error, 'DATA block missing 1 byte(s) in s1 field')

    def test_data_block_missing_data_in_data_field(self):
        pzx = self._get_pzxt()
        pzx.extend((
            68, 65, 84, 65, # DATA
            17, 0, 0, 0,    # Block length (17)
            16, 0, 0, 0,    # count
            0, 0,           # tail
            2,              # p0
            2,              # p1
            1, 0, 1, 0,     # s0
            2, 0, 2, 0,     # s1
            0               # data (1 byte short)
        ))
        tape = parse_pzx(pzx)
        self.assertEqual(len(tape.blocks), 1)
        self.assertEqual(tape.error, 'DATA block missing 1 byte(s) in data field')

    def test_puls_block_missing_data(self):
        pzx = self._get_pzxt()
        pzx.extend((
            80, 85, 76, 83, # PULS
            5, 0, 0, 0,     # Block length (5)
            0, 0, 0         # 3 bytes instead of 5
        ))
        tape = parse_pzx(pzx)
        self.assertEqual(len(tape.blocks), 1)
        self.assertEqual(tape.error, 'PULS block missing 2 byte(s)')

    def test_puls_block_missing_data_in_count_field(self):
        pzx = self._get_pzxt()
        pzx.extend((
            80, 85, 76, 83, # PULS
            1, 0, 0, 0,     # Block length (1)
            0               # count (1 byte short)
        ))
        tape = parse_pzx(pzx)
        self.assertEqual(len(tape.blocks), 1)
        self.assertEqual(tape.error, 'PULS block missing 1 byte(s) in count/duration1 field')

    def test_puls_block_missing_data_in_duration1_field(self):
        pzx = self._get_pzxt()
        pzx.extend((
            80, 85, 76, 83, # PULS
            3, 0, 0, 0,     # Block length (3)
            1, 128,         # count
            0               # duration1 (1 byte short)
        ))
        tape = parse_pzx(pzx)
        self.assertEqual(len(tape.blocks), 1)
        self.assertEqual(tape.error, 'PULS block missing 1 byte(s) in duration1 field')

    def test_puls_block_missing_data_in_duration2_field(self):
        pzx = self._get_pzxt()
        pzx.extend((
            80, 85, 76, 83, # PULS
            5, 0, 0, 0,     # Block length (5)
            1, 128,         # count
            1, 128,         # duration1
            0               # duration2 (1 byte short)
        ))
        tape = parse_pzx(pzx)
        self.assertEqual(len(tape.blocks), 1)
        self.assertEqual(tape.error, 'PULS block missing 1 byte(s) in duration2 field')

    def test_paus_block_missing_data(self):
        pzx = self._get_pzxt()
        pzx.extend((
            80, 65, 85, 83, # PAUS
            5, 0, 0, 0,     # Block length (5)
            0, 0            # 2 bytes instead of 5
        ))
        tape = parse_pzx(pzx)
        self.assertEqual(len(tape.blocks), 1)
        self.assertEqual(tape.error, 'PAUS block missing 3 byte(s)')

    def test_paus_block_too_short(self):
        pzx = self._get_pzxt()
        pzx.extend((
            80, 65, 85, 83, # PAUS
            3, 0, 0, 0,     # Block length (3)
            0, 0, 0
        ))
        tape = parse_pzx(pzx)
        self.assertEqual(len(tape.blocks), 1)
        self.assertEqual(tape.error, 'PAUS block length (3) is too small')

    def test_stop_block_missing_data(self):
        pzx = self._get_pzxt()
        pzx.extend((
            83, 84, 79, 80, # STOP
            5, 0, 0, 0,     # Block length (5)
            0, 0, 0, 0      # 4 bytes instead of 5
        ))
        tape = parse_pzx(pzx)
        self.assertEqual(len(tape.blocks), 1)
        self.assertEqual(tape.error, 'STOP block missing 1 byte(s)')

    def test_stop_block_too_short(self):
        pzx = self._get_pzxt()
        pzx.extend((
            83, 84, 79, 80, # STOP
            1, 0, 0, 0,     # Block length (1)
            0
        ))
        tape = parse_pzx(pzx)
        self.assertEqual(len(tape.blocks), 1)
        self.assertEqual(tape.error, 'STOP block length (1) is too small')

class TZXTest(SkoolKitTestCase):
    def _get_header(self):
        return bytearray((
            90, 88, 84, 97, 112, 101, 33, # ZXTape!
            26,                           # End marker
            1, 20                         # Major/minor version number
        ))

    def test_blocks_too_short(self):
        min_block_lengths = {
            0x10: 4,
            0x11: 18,
            0x12: 4,
            0x13: 1,
            0x14: 10,
            0x15: 8,
            0x16: 4,
            0x17: 4,
            0x18: 14,
            0x19: 18,
            0x20: 2,
            0x21: 1,
            0x23: 2,
            0x24: 2,
            0x26: 2,
            0x28: 3,
            0x2A: 4,
            0x2B: 5,
            0x30: 1,
            0x31: 2,
            0x32: 3,
            0x33: 1,
            0x34: 8,
            0x35: 20,
            0x40: 4,
            0x5A: 9
        }
        for block_id, min_len in min_block_lengths.items():
            tzx = self._get_header()
            tzx.append(block_id)
            tzx.extend([0] * (min_len - 1)) # 1 byte too short
            tape = parse_tzx(tzx)
            self.assertEqual(len(tape.blocks), 0)
            self.assertEqual(tape.error, f'Block 1 (0x{block_id:02X}) is too short')

    def test_block_0x10_missing_data(self):
        tzx = self._get_header()
        tzx.extend((
            0x10, # Block ID
            0, 0, # Pause duration
            4, 0, # Data length (4)
            0, 0  # 2 data bytes
        ))
        tape = parse_tzx(tzx, info=False)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x10) missing 2 byte(s)')

    def test_block_0x11_missing_data(self):
        tzx = self._get_header()
        tzx.append(0x11)
        tzx.extend([0] * 15)
        tzx.extend((
            5, 0, 0, # Data length (5)
            0, 0     # 2 data bytes
        ))
        tape = parse_tzx(tzx, info=False)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x11) missing 3 byte(s)')

    def test_block_0x13_missing_data(self):
        tzx = self._get_header()
        tzx.extend((
            0x13,      # Block ID
            6,         # 6 pulses = 12 bytes
            0, 0, 0, 0 # 4 bytes
        ))
        tape = parse_tzx(tzx, info=False)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x13) missing 8 byte(s)')

    def test_block_0x14_missing_data(self):
        tzx = self._get_header()
        tzx.append(0x14)
        tzx.extend([0] * 7)
        tzx.extend((
            6, 0, 0, # Data length (6)
            0, 0     # 2 data bytes
        ))
        tape = parse_tzx(tzx, info=False)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x14) missing 4 byte(s)')

    def test_block_0x15_missing_data(self):
        tzx = self._get_header()
        tzx.append(0x15)
        tzx.extend([0] * 5)
        tzx.extend((
            6, 0, 0, # Data length (6)
            0, 0, 0  # 3 data bytes
        ))
        tape = parse_tzx(tzx, info=False)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x15) missing 3 byte(s)')

    def test_block_0x16_missing_data(self):
        tzx = self._get_header()
        tzx.extend((
            0x16,       # Block ID
            7, 0, 0, 0, # Block length (7)
            0, 0, 0     # 3 bytes
        ))
        tape = parse_tzx(tzx)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x16) missing 4 byte(s)')

    def test_block_0x17_missing_data(self):
        tzx = self._get_header()
        tzx.extend((
            0x17,       # Block ID
            8, 0, 0, 0, # Block length (8)
            0, 0, 0     # 3 bytes
        ))
        tape = parse_tzx(tzx)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x17) missing 5 byte(s)')

    def test_block_0x18_missing_data(self):
        tzx = self._get_header()
        tzx.extend((
            0x18,        # Block ID
            13, 0, 0, 0, # Block length (13)
            0, 0, 0, 0,
            0, 0, 0, 0,
            0, 0, 0, 0,
        ))
        tape = parse_tzx(tzx, info=False)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x18) missing 1 byte(s)')

    def test_block_0x19_missing_data(self):
        tzx = self._get_header()
        tzx.extend((
            0x19,        # Block ID
            17, 0, 0, 0, # Block length (17)
            0, 0, 0, 0,
            0, 0, 0, 0,
            0, 0, 0, 0,
            0, 0, 0, 0,
        ))
        tape = parse_tzx(tzx)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x19) missing 1 byte(s)')

    def test_block_0x21_missing_data(self):
        tzx = self._get_header()
        tzx.extend((
            0x21, # Block ID
            6,    # Group name length (6)
            0, 0
        ))
        tape = parse_tzx(tzx, info=False)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x21) missing 4 byte(s)')

    def test_block_0x26_missing_data(self):
        tzx = self._get_header()
        tzx.extend((
            0x26,      # Block ID
            5, 0,      # 5 calls = 10 bytes
            0, 0, 0, 0 # 4 bytes
        ))
        tape = parse_tzx(tzx)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x26) missing 6 byte(s)')

    def test_block_0x28_unexpected_eof(self):
        tzx = self._get_header()
        tzx.extend((
            0x28, # Block ID
            3, 0, # Block length (3)
            1,    # 1 selection (>=3 bytes)
            0, 0  # 2 bytes
        ))
        tape = parse_tzx(tzx)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Unexpected end of file')

    def test_block_0x28_missing_data(self):
        tzx = self._get_header()
        tzx.extend((
            0x28,      # Block ID
            11, 0,     # Block length (11)
            0, 0, 0, 0 # 4 bytes
        ))
        tape = parse_tzx(tzx, info=False)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x28) missing 7 byte(s)')

    def test_block_0x30_missing_data(self):
        tzx = self._get_header()
        tzx.extend((
            0x30, # Block ID
            6,    # Message length (6)
            0, 0
        ))
        tape = parse_tzx(tzx, info=False)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x30) missing 4 byte(s)')

    def test_block_0x31_missing_data(self):
        tzx = self._get_header()
        tzx.extend((
            0x31, # Block ID
            0,    # Display time
            7,    # Message length (7)
            0, 0
        ))
        tape = parse_tzx(tzx, info=False)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x31) missing 5 byte(s)')

    def test_block_0x32_missing_data(self):
        tzx = self._get_header()
        tzx.extend((
            0x32,      # Block ID
            9, 0,      # Block length (9)
            0, 0, 0, 0 # 4 bytes
        ))
        tape = parse_tzx(tzx, info=False)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x32) missing 5 byte(s)')

    def test_block_0x33_unexpected_eof(self):
        tzx = self._get_header()
        tzx.extend((
            0x33, # Block ID
            1,    # 1 entry = 3 bytes
            0, 0  # 2 bytes
        ))
        tape = parse_tzx(tzx)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, 'Unexpected end of file')

    def test_block_0x33_missing_data(self):
        tzx = self._get_header()
        tzx.extend((
            0x33,      # Block ID
            2,         # 2 entries = 6 bytes
            0, 0, 0, 0 # 4 bytes
        ))
        tape = parse_tzx(tzx, info=False)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x33) missing 2 byte(s)')

    def test_block_0x35_missing_data(self):
        tzx = self._get_header()
        tzx.append(0x35)
        tzx.extend([0] * 16)
        tzx.extend((
            6, 0, 0, 0, # Length  of custom info (6)
            0, 0, 0     # 3 bytes
        ))
        tape = parse_tzx(tzx, info=False)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x35) missing 3 byte(s)')

    def test_block_0x40_missing_data(self):
        tzx = self._get_header()
        tzx.extend((
            0x40,    # Block ID
            0,       # Snapshot type
            7, 0, 0, # Snapshot length (7)
            0, 0     # 2 bytes
        ))
        tape = parse_tzx(tzx, info=False)
        self.assertEqual(len(tape.blocks), 0)
        self.assertEqual(tape.error, f'Block 1 (0x40) missing 5 byte(s)')

class TapeWriteTest(SkoolKitTestCase):
    def test_write_pzx(self):
        blocks = ([0, 1, 2], [255, 4, 5, 6, 7], [255, 8, 9, 10])
        pzxfile = 'test_write_pzx.pzx'
        write_pzx(pzxfile, blocks)
        pzx_blocks = get_pzx_blocks(pzxfile)
        puls_long = (127, 159, 120, 8, 155, 2, 223, 2)
        puls_short = (151, 140, 120, 8, 155, 2, 223, 2)
        paus = (224, 103, 53, 0) # 3500000 T-states
        exp_blocks = (
            ('PZXT', (1, 0)),
            ('PULS', puls_long),
            ('DATA', to_pzx_data(blocks[0])),
            ('PAUS', paus),
            ('PULS', puls_short),
            ('DATA', to_pzx_data(blocks[1])),
            ('PAUS', paus),
            ('PULS', puls_short),
            ('DATA', to_pzx_data(blocks[2]))
        )
        self.assertEqual(len(pzx_blocks), len(exp_blocks))
        for (exp_id, exp_data), (block_id, data) in zip(exp_blocks, pzx_blocks):
            self.assertEqual(block_id, exp_id)
            self.assertEqual(exp_data, data)

    def test_write_tap(self):
        blocks = ([0, 1, 2], [3, 4, 5, 6, 7])
        tapfile = 'test_write_tap.tap'
        write_tap(tapfile, blocks)
        tap_blocks = get_tap_blocks(tapfile)
        self.assertEqual(len(tap_blocks), len(blocks))
        self.assertEqual(blocks[0], tap_blocks[0])
        self.assertEqual(blocks[1], tap_blocks[1])
