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
                if reg == '(HL)':
                    hl = simulator.registers['L'] + 256 * simulator.registers['H']
                    rval = simulator.snapshot[hl]
                elif reg == '(IX+d)':
                    ix = simulator.registers['IXl'] + 256 * simulator.registers['IXh']
                    rval = simulator.snapshot[ix]
                elif reg == '(IY+d)':
                    iy = simulator.registers['IYl'] + 256 * simulator.registers['IYh']
                    rval = simulator.snapshot[iy]
                else:
                    rval = simulator.registers[reg]
                self.data.append(rval)
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
