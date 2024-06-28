from skoolkittest import SkoolKitTestCase, as_dword
from skoolkit.tape import write_pzx, write_tap

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

class TapeTest(SkoolKitTestCase):
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
