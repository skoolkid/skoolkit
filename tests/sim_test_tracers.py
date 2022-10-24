import hashlib
from os.path import abspath, dirname
import sys

SKOOLKIT_HOME = abspath(dirname(dirname(__file__)))
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit.simulator import REGISTERS, A, F, B, C, D, E, H, L, IXh, IXl, IYh, IYl, SP, I, R

class BaseTracer:
    def __init__(self, start, watch=(A, F)):
        self.start = start
        self.watch = watch
        self.data = bytearray()
        self.checksum = None
        self.operations = 0

    def collect_result(self, simulator, address):
        if self.operations:
            for reg in self.watch:
                if reg == '(DE)':
                    rr = simulator.registers[E] + 256 * simulator.registers[D]
                    rval = simulator.memory[rr]
                elif reg == '(HL)':
                    rr = simulator.registers[L] + 256 * simulator.registers[H]
                    rval = simulator.memory[rr]
                elif reg == '(IX+d)':
                    ix = simulator.registers[IXl] + 256 * simulator.registers[IXh]
                    rval = simulator.memory[ix]
                elif reg == '(IY+d)':
                    iy = simulator.registers[IYl] + 256 * simulator.registers[IYh]
                    rval = simulator.memory[iy]
                elif reg == 'SP':
                    sp = simulator.registers[SP]
                    rval = (sp // 256, sp % 256)
                else:
                    rval = simulator.registers[reg]
                if isinstance(rval, int):
                    self.data.append(rval)
                else:
                    self.data.extend(rval)
        self.operations += 1
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
        simulator.registers[F] = self.count >> 16
        simulator.registers[A] = (self.count >> 8) & 0xFF
        r = self.count & 0xFF
        if self.reg == '(HL)':
            hl = simulator.registers[L] + 256 * simulator.registers[H]
            simulator.memory[hl] = r
        elif self.reg == '(IX+d)':
            ix = simulator.registers[IXl] + 256 * simulator.registers[IXh]
            simulator.memory[ix] = r
        elif self.reg == '(IY+d)':
            iy = simulator.registers[IYl] + 256 * simulator.registers[IYh]
            simulator.memory[iy] = r
        elif self.reg == 'n':
            simulator.memory[self.start + 1] = r
        else:
            simulator.registers[self.reg] = r
        self.repeat(simulator)

class FRTracer(BaseTracer):
    def __init__(self, start, reg):
        super().__init__(start, (reg, F))
        self.reg = reg
        self.count = 0xFFFF

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True
        simulator.registers[F] = self.count >> 16
        r = self.count & 0xFF
        if self.reg == '(HL)':
            hl = simulator.registers[L] + 256 * simulator.registers[H]
            simulator.memory[hl] = r
        elif self.reg == '(IX+d)':
            ix = simulator.registers[IXl] + 256 * simulator.registers[IXh]
            simulator.memory[ix] = r
        elif self.reg == '(IY+d)':
            iy = simulator.registers[IYl] + 256 * simulator.registers[IYh]
            simulator.memory[iy] = r
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
        simulator.registers[F] = self.count >> 8
        simulator.registers[A] = self.count & 0xFF
        self.repeat(simulator)

class FTracer(BaseTracer):
    def __init__(self, start):
        super().__init__(start, (F,))
        self.count = 0xFF

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True
        simulator.registers[F] = self.count
        self.repeat(simulator)

class DAATracer(BaseTracer):
    def __init__(self, start):
        super().__init__(start)
        self.count = 0x7FF

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True
        hnc = self.count >> 8
        simulator.registers[F] = (hnc & 0x03) | ((hnc & 0x04) << 2)
        simulator.registers[A] = self.count & 0xFF
        self.repeat(simulator)

class HLRRFTracer(BaseTracer):
    def __init__(self, start, rr1, rr2):
        if isinstance(rr1, str):
            self.rr1 = (REGISTERS[rr1[0]], REGISTERS[rr1[1]])
        else:
            self.rr1 = rr1
        if rr2 == 'SP':
            self.rr2 = rr2
            super().__init__(start, (*self.rr1, 'SP', F))
        else:
            self.rr2 = (REGISTERS[rr2[0]], REGISTERS[rr2[1]])
            super().__init__(start, (*self.rr1, *self.rr2, F))
        self.count = 0x07FFFF

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True
        simulator.registers[F] = self.count >> 18
        if self.rr2 == 'SP':
            simulator.registers[SP] = self.count & 0xFFFF
        else:
            simulator.registers[self.rr2[0]] = (self.count >> 8) & 0xFF
            simulator.registers[self.rr2[1]] = self.count & 0xFF
        v = (self.count >> 16) & 0xFF
        b = (v & 0x01) + 16 * (v & 0x02)
        simulator.registers[self.rr1[0]] = b
        simulator.registers[self.rr1[1]] = b
        self.repeat(simulator)

class HLFTracer(BaseTracer):
    def __init__(self, start, rr):
        if isinstance(rr, str):
            self.rr = (REGISTERS[rr[0]], REGISTERS[rr[1]])
        else:
            self.rr = rr
        super().__init__(start, (*self.rr, F))
        self.count = 0x1FFFF

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True
        simulator.registers[F] = self.count >> 16
        hi = (self.count >> 8) & 0xFF
        lo = self.count & 0xFF
        simulator.registers[self.rr[0]] = hi
        simulator.registers[self.rr[1]] = lo
        self.repeat(simulator)

class BlockTracer(BaseTracer):
    def __init__(self, start):
        super().__init__(start, (A, F, B, C, D, E, H, L, '(DE)', '(HL)'))
        self.count = 0x3FFFF

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True

        simulator.registers[A] = 0x03
        if self.count & 0x20000:
            # LDIR should not touch the S, Z and C flags
            simulator.registers[F] = 0xC1 # SZ.....C
        else:
            simulator.registers[F] = 0x3E # ..5H3PN.
        bc = self.count & 0xFFFF
        simulator.registers[B] = bc // 256
        simulator.registers[C] = bc % 256
        de = 0xFE00
        simulator.registers[D] = de // 256
        simulator.registers[E] = de % 256
        hl = 0xFF00
        simulator.registers[H] = hl // 256
        simulator.registers[L] = hl % 256
        if self.count & 0x10000:
            simulator.memory[hl] = simulator.registers[A]
        else:
            simulator.memory[hl] = simulator.registers[A] ^ 0xFF
        simulator.memory[de] = simulator.memory[hl] ^ 0xFF

        self.repeat(simulator)

class BitTracer(BaseTracer):
    def __init__(self, start, reg):
        super().__init__(start, (reg, F))
        self.reg = reg
        self.bit = 7
        self.rval = 0xFF
        if reg in ('(IX+d)', '(IY+d)'):
            self.index = 3
        else:
            self.index = -1
        self.count = 0xFFFFFFFF
        self.registers = (B, C, D, E, H, L, '(HL)', A)

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True

        simulator.registers[F] = 0

        if self.reg in ('(IX+d)', '(IY+d)'):
            rr = 0x6000
            if self.index & 0x02:
                rr |= 0x2000
            if self.index & 0x01:
                rr |= 0x0800
            if self.reg == '(IX+d)':
                simulator.registers[IXl] = rr % 256
                simulator.registers[IXh] = rr // 256
            else:
                simulator.registers[IYl] = rr % 256
                simulator.registers[IYh] = rr // 256
            simulator.memory[rr] = self.rval
        elif self.reg == '(HL)':
            hl = 0x6000
            simulator.registers[L] = hl % 256
            simulator.registers[H] = hl // 256
            simulator.memory[hl] = self.rval
        else:
            simulator.registers[self.reg] = self.rval

        if self.reg in ('(IX+d)', '(IY+d)'):
            r = simulator.memory[self.start + 3] & 0x07
            opcode = 0x40 + 8 * self.bit + r
            simulator.memory[self.start + 3] = opcode
        else:
            opcode = 0x40 + 8 * self.bit + self.registers.index(self.reg)
            simulator.memory[self.start + 1] = opcode

        if self.rval > 0:
            self.rval -= 1
        else:
            self.rval = 0xFF
            self.bit -= 1

        if self.bit < 0:
            if self.index > 0:
                self.index -= 1
                self.bit = 7
            else:
                self.count = 0 # Finished

        self.repeat(simulator)

class RRDRLDTracer(BaseTracer):
    def __init__(self, start):
        super().__init__(start, (A, F, '(HL)'))
        self.count = 0xFFFF

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True
        simulator.registers[A] = (self.count >> 8) & 0xFF
        simulator.registers[F] = 0
        hl = 0x6000
        simulator.registers[H] = hl // 256
        simulator.registers[L] = hl % 256
        simulator.memory[hl] = self.count & 0xFF
        self.repeat(simulator)

class InTracer(BaseTracer):
    def __init__(self, start, reg):
        super().__init__(start, (reg, F))
        self.count = 0xFF
        self.value = 0

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True
        simulator.registers[B] = 0xAA
        simulator.registers[C] = 0xFE
        simulator.registers[F] = 0
        self.value = self.count
        self.repeat(simulator)

    def read_port(self, simulator, port):
        return self.value

class AIRTracer(BaseTracer):
    def __init__(self, start, reg):
        super().__init__(start, (A, F, reg))
        self.reg = reg
        self.count = 0x1FF

    def trace(self, simulator, instruction):
        if self.collect_result(simulator, instruction):
            return True
        simulator.registers[F] = (self.count >> 8) * 0xFF
        simulator.registers[self.reg] = self.count & 0xFF
        self.repeat(simulator)
