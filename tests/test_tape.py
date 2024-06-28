from skoolkittest import SkoolKitTestCase
from skoolkit.tape import write_tap

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

class TapeTest(SkoolKitTestCase):
    def test_write_tap(self):
        blocks = ([0, 1, 2], [3, 4, 5, 6, 7])
        tapfile = 'test_write_tap.tap'
        write_tap(tapfile, blocks)
        tap_blocks = get_tap_blocks(tapfile)
        self.assertEqual(len(tap_blocks), len(blocks))
        self.assertEqual(blocks[0], tap_blocks[0])
        self.assertEqual(blocks[1], tap_blocks[1])
