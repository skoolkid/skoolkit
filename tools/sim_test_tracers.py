import hashlib

class AFRTracer:
    def __init__(self, start, reg):
        self.start = start
        self.reg = reg
        self.count = 0x1FFFF
        self.data = bytearray()
        self.checksum = None

    def trace(self, simulator, instruction):
        if instruction.time > 0:
            self.data.extend((simulator.registers['A'], simulator.registers['F']))
        if self.count < 0:
            self.checksum = hashlib.md5(self.data).hexdigest()
            return True
        simulator.registers['F'] = self.count >> 16
        simulator.registers['A'] = (self.count >> 8) & 0xFF
        r = self.count & 0xFF
        if self.reg == '(HL)':
            hl = simulator.registers['L'] + 256 * simulator.registers['H']
            simulator.snapshot[hl] = r
        elif self.reg == '(IX+d)':
            ix = simulator.registers['IXl'] + 256 * simulator.registers['IXh']
            simulator.snapshot[ix] = r
        elif self.reg == '(IY+d)':
            iy = simulator.registers['IYl'] + 256 * simulator.registers['IYh']
            simulator.snapshot[iy] = r
        elif self.reg == 'n':
            simulator.snapshot[self.start + 1] = r
        else:
            simulator.registers[self.reg] = r
        simulator.registers['PC'] = self.start
        self.count -= 1

class AFTracer:
    def __init__(self, start):
        self.start = start
        self.count = 0x1FF
        self.data = bytearray()
        self.checksum = None

    def trace(self, simulator, instruction):
        if instruction.time > 0:
            self.data.extend((simulator.registers['A'], simulator.registers['F']))
        if self.count < 0:
            self.checksum = hashlib.md5(self.data).hexdigest()
            return True
        simulator.registers['F'] = self.count >> 8
        simulator.registers['A'] = self.count & 0xFF
        simulator.registers['PC'] = self.start
        self.count -= 1

class DAATracer:
    def __init__(self, start):
        self.start = start
        self.count = 0x7FF
        self.data = bytearray()
        self.checksum = None

    def trace(self, simulator, instruction):
        if instruction.time > 0:
            self.data.extend((simulator.registers['A'], simulator.registers['F']))
        if self.count < 0:
            self.checksum = hashlib.md5(self.data).hexdigest()
            return True
        hnc = self.count >> 8
        simulator.registers['F'] = (hnc & 0x03) | ((hnc & 0x04) << 2)
        simulator.registers['A'] = self.count & 0xFF
        simulator.registers['PC'] = self.start
        self.count -= 1
