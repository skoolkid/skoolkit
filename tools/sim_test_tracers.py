import hashlib

class BaseTracer:
    def __init__(self, start, watch='AF'):
        self.start = start
        self.watch = watch
        self.data = bytearray()
        self.checksum = None

    def collect_result(self, simulator, instruction):
        if instruction.time > 0:
            for reg in self.watch:
                if reg in ('(DE)', '(HL)'):
                    rr = simulator.registers[reg[2]] + 256 * simulator.registers[reg[1]]
                    rval = simulator.snapshot[rr]
                elif reg == '(IX+d)':
                    ix = simulator.registers['IXl'] + 256 * simulator.registers['IXh']
                    rval = simulator.snapshot[ix]
                elif reg == '(IY+d)':
                    iy = simulator.registers['IYl'] + 256 * simulator.registers['IYh']
                    rval = simulator.snapshot[iy]
                elif reg == 'SP':
                    sp = simulator.registers['SP']
                    rval = (sp // 256, sp % 256)
                else:
                    rval = simulator.registers[reg]
                if isinstance(rval, int):
                    self.data.append(rval)
                else:
                    self.data.extend(rval)
        if self.count < 0:
            self.checksum = hashlib.md5(self.data).hexdigest()
            return True

    def repeat(self, simulator):
        simulator.pc = self.start
        self.count -= 1

class AFRTracer(BaseTracer):
    def __init__(self, start, reg):
        super().__init__(start)
        self.reg = reg
        self.count = 0x1FFFF

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
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
        self.repeat(simulator)

class FRTracer(BaseTracer):
    def __init__(self, start, reg):
        super().__init__(start, (reg, 'F'))
        self.reg = reg
        self.count = 0xFFFF

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True
        simulator.registers['F'] = self.count >> 16
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
        else:
            simulator.registers[self.reg] = r
        self.repeat(simulator)

class AFTracer(BaseTracer):
    def __init__(self, start, count=0x1FF):
        super().__init__(start)
        self.count = count

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True
        simulator.registers['F'] = self.count >> 8
        simulator.registers['A'] = self.count & 0xFF
        self.repeat(simulator)

class FTracer(BaseTracer):
    def __init__(self, start):
        super().__init__(start, 'F')
        self.count = 0xFF

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True
        simulator.registers['F'] = self.count
        self.repeat(simulator)

class DAATracer(BaseTracer):
    def __init__(self, start):
        super().__init__(start)
        self.count = 0x7FF

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True
        hnc = self.count >> 8
        simulator.registers['F'] = (hnc & 0x03) | ((hnc & 0x04) << 2)
        simulator.registers['A'] = self.count & 0xFF
        self.repeat(simulator)

class HLRRFTracer(BaseTracer):
    def __init__(self, start, rr1, rr2):
        if isinstance(rr1, str):
            if rr2 == 'SP':
                super().__init__(start, (rr1[0], rr1[1], 'SP', 'F'))
            else:
                super().__init__(start, rr1 + rr2 + 'F')
            self.rr1 = rr1
        else:
            if rr2 == 'SP':
                super().__init__(start, rr1 + ('SP', 'F'))
            else:
                super().__init__(start, rr1 + (rr2[0], rr2[1], 'F'))
            self.rr1 = rr1[0][:2]
        self.rr2 = rr2
        self.count = 0x07FFFF

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True
        simulator.registers['F'] = self.count >> 18
        if self.rr2 == 'SP':
            simulator.registers['SP'] = self.count & 0xFFFF
        else:
            simulator.registers[self.rr2[0]] = (self.count >> 8) & 0xFF
            simulator.registers[self.rr2[1]] = self.count & 0xFF
        v = (self.count >> 16) & 0xFF
        b = (v & 0x01) + 16 * (v & 0x02)
        if self.rr1 == 'HL':
            simulator.registers['H'] = b
            simulator.registers['L'] = b
        else:
            simulator.registers[self.rr1 + 'h'] = b
            simulator.registers[self.rr1 + 'l'] = b
        self.repeat(simulator)

class HLFTracer(BaseTracer):
    def __init__(self, start, rr):
        if isinstance(rr, str):
            super().__init__(start, rr + 'F')
            self.rr = rr
        else:
            super().__init__(start, rr + ('F',))
            self.rr = rr[0][:2]
        self.count = 0x1FFFF

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True
        simulator.registers['F'] = self.count >> 16
        hi = (self.count >> 8) & 0xFF
        lo = self.count & 0xFF
        if self.rr == 'HL':
            simulator.registers['H'] = hi
            simulator.registers['L'] = lo
        else:
            simulator.registers[self.rr + 'h'] = hi
            simulator.registers[self.rr + 'l'] = lo
        self.repeat(simulator)

class BlockTracer(BaseTracer):
    def __init__(self, start):
        super().__init__(start, ('A', 'F', 'B', 'C', 'D', 'E', 'H', 'L', '(DE)', '(HL)'))
        self.count = 0x3FFFF

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True

        simulator.registers['A'] = 0x03
        if self.count & 0x20000:
            # LDIR should not touch the S, Z and C flags
            simulator.registers['F'] = 0xC1 # SZ.....C
        else:
            simulator.registers['F'] = 0x3E # ..5H3PN.
        bc = self.count & 0xFFFF
        simulator.registers['B'] = bc // 256
        simulator.registers['C'] = bc % 256
        de = 0xFE00
        simulator.registers['D'] = de // 256
        simulator.registers['E'] = de % 256
        hl = 0xFF00
        simulator.registers['H'] = hl // 256
        simulator.registers['L'] = hl % 256
        if self.count & 0x10000:
            simulator.snapshot[hl] = simulator.registers['A']
        else:
            simulator.snapshot[hl] = simulator.registers['A'] ^ 0xFF
        simulator.snapshot[de] = simulator.snapshot[hl] ^ 0xFF

        self.repeat(simulator)
