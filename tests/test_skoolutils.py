from skoolkittest import SkoolKitTestCase
from skoolkit.skoolutils import Memory

class MemoryTest(SkoolKitTestCase):
    def test_48k(self):
        memory = Memory()
        for addr, value in ((0x0001, 0x53), (0x421A, 0x07), (0x89F7, 0xF3), (0xEA19, 0x28)):
            memory[addr] = value
            self.assertEqual(memory[addr], value)

    def test_128k(self):
        memory = Memory([[0] * 0x4000 for b in range(8)])
        for addr, value in ((0x0003, 0x55), (0x421C, 0x09), (0x89F9, 0xF5), (0xEA1B, 0x2A)):
            memory[addr] = value
            self.assertEqual(memory[addr], value)

    def test_48k_banks(self):
        memory = Memory([[b] * 0x4000 if b in (0, 2, 5) else None for b in range(8)])
        for bank, addr, value in ((None, 0x0002, 0x54), (5, 0x421B, 0x08), (2, 0x89F8, 0xF4), (0, 0xEA1A, 0x29)):
            if bank is not None:
                self.assertEqual(memory[addr], bank)
            memory[addr] = value
            self.assertEqual(memory[addr], value)

    def test_128k_banks(self):
        memory = Memory([[b] * 0x4000 for b in range(8)])
        memory.bank(6)
        for bank, addr, value in ((None, 0x0004, 0x56), (5, 0x421D, 0x0A), (2, 0x89FA, 0xF6), (6, 0xEA1C, 0x2B)):
            if bank is not None:
                self.assertEqual(memory[addr], bank)
            memory[addr] = value
            self.assertEqual(memory[addr], value)

    def test_48k_address_range(self):
        memory = Memory()
        start = 0xA135
        values = [0x43, 0x35, 0xF3, 0x20, 0x69, 0x9E]
        end = start + len(values)
        memory[start:end] = values
        self.assertEqual(values, [memory[a] for a in range(start, end)])
        self.assertEqual(values, memory[start:end])

    def test_128k_address_range(self):
        memory = Memory([[0] * 0x4000 for b in range(8)])
        start = 0xA135
        values = [0x44, 0x36, 0xF4, 0x21, 0x6A, 0x9F]
        end = start + len(values)
        memory[start:end] = values
        self.assertEqual(values, [memory[a] for a in range(start, end)])
        self.assertEqual(values, memory[start:end])

    def test_48k_address_range_with_step(self):
        memory = Memory()
        start = 0x4173
        values = [0x45, 0x37, 0xF5, 0x22, 0x6B, 0xA0]
        step = (0xFFFF - start) // len(values)
        end = start + len(values) * step
        memory[start:end:step] = values
        self.assertEqual(values, [memory[a] for a in range(start, end, step)])
        self.assertEqual(values, memory[start:end:step])

    def test_128k_address_range_with_step(self):
        memory = Memory([[0] * 0x4000 for b in range(8)])
        start = 0x4174
        values = [0x46, 0x38, 0xF6, 0x23, 0x6C, 0xA1]
        step = (0xFFFF - start) // len(values)
        end = start + len(values) * step
        memory[start:end:step] = values
        self.assertEqual(values, [memory[a] for a in range(start, end, step)])
        self.assertEqual(values, memory[start:end:step])

    def test_48k_len(self):
        memory = Memory()
        self.assertEqual(len(memory), 0x10000)

    def test_128k_len(self):
        memory = Memory([[0] * 0x4000 for b in range(8)])
        self.assertEqual(len(memory), 0x20000)

    def test_128k_bank(self):
        memory = Memory([[b] * 0x4000 for b in range(8)])
        memory.bank(6)
        self.assertEqual(memory[0xC000], 6)

    def test_128k_bank_with_data(self):
        memory = Memory([[b] * 0x4000 for b in range(8)])
        memory.bank(4, [8] * 0x4000)
        self.assertEqual(memory[0xC000], 0) # Bank 4 not paged in yet
        memory.bank(4)
        self.assertEqual(memory[0xC000], 8) # Bank 4 paged in now

    def test_48k_copy(self):
        memory = Memory([[b] * 0x4000 if b in (0, 2, 5) else None for b in range(8)])
        memory[:0x4000] = [8] * 0x4000
        mcopy = memory.copy()
        self.assertTrue(all(v == 8 for v in memory[:0x4000]))
        for i in range(4):
            self.assertIsNot(memory.memory[i], mcopy.memory[i])
        for b in (0, 2, 5):
            self.assertTrue(all(v == b for v in mcopy.banks[b]))
            self.assertIsNot(memory.banks[b], mcopy.banks[b])

    def test_128k_copy(self):
        memory = Memory([[b] * 0x4000 for b in range(8)])
        memory.out7ffd(0x11) # ROM 1, bank 1
        mcopy = memory.copy()
        self.assertEqual(mcopy[0x0001], 0xAF) # ROM 1 paged in
        self.assertIs(mcopy.memory[0], mcopy.roms[1])
        for r in range(2):
            self.assertIsNot(memory.roms[r], mcopy.roms[r])
        for b in range(8):
            self.assertTrue(all(v == b for v in mcopy.banks[b]))
            self.assertIsNot(memory.banks[b], mcopy.banks[b])
        for i in range(4):
            self.assertIsNot(memory.memory[i], mcopy.memory[i])
        self.assertEqual(mcopy[0xC000], 1) # Bank 1 paged in

    def test_128k_out7ffd(self):
        memory = Memory([[b] * 0x4000 for b in range(8)])
        memory.out7ffd(7)
        self.assertEqual(memory[0xC000], 7)

    def test_128k_convert(self):
        memory = Memory([[b] * 0x4000 for b in range(8)])
        memory.out7ffd(0x13)
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
