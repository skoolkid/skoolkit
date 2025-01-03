from skoolkittest import SkoolKitTestCase
from skoolkit.pagingtracer import Memory

class MemoryTest(SkoolKitTestCase):
    def test_read_write(self):
        memory = Memory()
        for addr, value in ((0x421C, 0x09), (0x89F9, 0xF5), (0xEA1B, 0x2A)):
            memory[addr] = value
            self.assertEqual(memory[addr], value)

    def test_read_address_range(self):
        memory = Memory()
        start = 0xA135
        values = [0x44, 0x36, 0xF4, 0x21, 0x6A, 0x9F]
        end = start + len(values)
        addr = start
        for v in values:
            memory[addr] = v
            addr += 1
        self.assertEqual(values, [memory[a] for a in range(start, end)])
        self.assertEqual(values, memory[start:end])

    def test_read_address_range_with_step(self):
        memory = Memory([[0] * 0x4000 for b in range(8)])
        start = 0x4174
        values = [0x46, 0x38, 0xF6, 0x23, 0x6C, 0xA1]
        step = (0xFFFF - start) // len(values)
        end = start + len(values) * step
        addr = start
        for v in values:
            memory[addr] = v
            addr += step
        self.assertEqual(values, [memory[a] for a in range(start, end, step)])
        self.assertEqual(values, memory[start:end:step])

    def test_128k_roms(self):
        memory = Memory()
        self.assertEqual(memory.machine, '128K')
        self.assertEqual(memory[0x09A2], 0xFF)
        memory.out7ffd(0x10)
        self.assertEqual(memory[0x09A2], 0x53)

    def test_plus2_roms(self):
        memory = Memory(machine='+2')
        self.assertEqual(memory.machine, '+2')
        self.assertEqual(memory[0x09A2], 0x1B)
        memory.out7ffd(0x10)
        self.assertEqual(memory[0x09A2], 0x50)

    def test_len(self):
        self.assertEqual(len(Memory()), 0x20000)

    def test_out7ffd(self):
        memory = Memory([[b] * 0x4000 for b in range(8)])
        for b in range(8):
            memory.out7ffd(b)
            self.assertEqual(memory[0xC000], b)
            self.assertEqual(memory.o7ffd, b)

    def test_convert(self):
        memory = Memory([[b] * 0x4000 for b in range(8)], 0x13)
        memory.convert()
        for r, v in ((0, 0x01), (1, 0xAF)):
            self.assertTrue(isinstance(memory.roms[r], bytearray))
            self.assertEqual(memory.roms[r][1], v)
        for b in range(8):
            self.assertTrue(all(v == b for v in memory.banks[b]))
            self.assertTrue(isinstance(memory.banks[b], bytearray))
        self.assertIs(memory.memory[0], memory.roms[1])
        self.assertIs(memory.memory[1], memory.banks[5])
        self.assertIs(memory.memory[2], memory.banks[2])
        self.assertIs(memory.memory[3], memory.banks[3])
