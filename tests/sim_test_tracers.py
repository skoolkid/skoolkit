import hashlib
from os.path import abspath, dirname
import sys

SKOOLKIT_HOME = abspath(dirname(dirname(__file__)))
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit.simulator import (REGISTERS, A, F, B, C, D, E, H, L, IXh, IXl,
                                IYh, IYl, SP, I, R, PC)

Hd = 30
Xd = 32
Yd = 33
N = 34

INITIAL_REGISTERS = [0] * (PC + 1)

class BaseTracer:
    def __init__(self, max_count, opcodes):
        self.count = max_count
        self.max_count = max_count
        self.opcodes = opcodes
        self.index = 0
        self.max_index = len(opcodes)
        self.data = bytearray()
        self.checksum = None

    def run(self, simulator, csimulator_cls):
        opcodes = simulator.opcodes
        memory = simulator.memory
        registers = simulator.registers
        csimulator = csimulator_cls.from_simulator(simulator) if csimulator_cls else None

        while True:
            for i in range(PC + 1):
                registers[i] = INITIAL_REGISTERS[i]
            registers[SP] = 32768
            registers[B] = 129
            registers[D] = 130
            registers[H] = 131
            registers[IXh] = 132
            registers[IYh] = 133
            self.prepare(simulator)
            if csimulator:
                csimulator.run()
            else:
                opcodes[memory[registers[24]]]()
            self.collect_result(simulator)
            self.count -= 1
            if self.count < 0:
                self.index += 1
                self.count = self.max_count
                if self.index >= self.max_index:
                    self.checksum = hashlib.md5(self.data).hexdigest()
                    break

    def collect_result(self, simulator):
        data = self.data
        registers = simulator.registers
        memory = simulator.memory
        bc = registers[C] + 256 * registers[B]
        de = registers[E] + 256 * registers[D]
        hl = registers[L] + 256 * registers[H]
        ix = registers[IXl] + 256 * registers[IXh]
        iy = registers[IYl] + 256 * registers[IYh]
        sp = registers[SP]
        for i in range(SP):
            data.append(registers[i])
        data.extend((sp // 256, sp % 256))
        for i in range(SP + 2, PC):
            data.append(registers[i])
        data.extend(memory[bc:bc + 2])
        data.extend(memory[de:de + 2])
        data.extend(memory[hl:hl + 2])
        data.extend(memory[ix:ix + 2])
        data.extend(memory[iy:iy + 2])
        data.extend(memory[sp - 2:sp + 2])

class AFRTracer(BaseTracer):
    def __init__(self, base_opcode):
        opcodes = (
            (B, (base_opcode,)),               # B
            (C, (base_opcode + 1,)),           # C
            (D, (base_opcode + 2,)),           # D
            (E, (base_opcode + 3,)),           # E
            (H, (base_opcode + 4,)),           # H
            (L, (base_opcode + 5,)),           # L
            (Hd, (base_opcode + 6,)),          # (HL)
            (N, (base_opcode + 0x46,)),        # n
            (IXh, (0xDD, base_opcode + 4)),    # IXh
            (IXl, (0xDD, base_opcode + 5)),    # IXl
            (IYh, (0xFD, base_opcode + 4)),    # IYh
            (IYl, (0xFD, base_opcode + 5)),    # IYl
            (Xd, (0xDD, base_opcode + 6, 0)),  # (IX+0)
            (Yd, (0xFD, base_opcode + 6, 0)),  # (IY+0)
        )
        super().__init__(0x1FFFF, opcodes)

    def prepare(self, simulator):
        registers = simulator.registers
        registers[F] = (self.count // 65536) * 255
        registers[A] = (self.count >> 8) & 0xFF
        r = self.count & 0xFF
        reg, opcodes = self.opcodes[self.index]
        simulator.memory[:len(opcodes)] = opcodes
        if reg == Hd:
            hl = registers[L] + 256 * registers[H]
            simulator.memory[hl] = r
        elif reg == Xd:
            ix = registers[IXl] + 256 * registers[IXh]
            simulator.memory[ix] = r
        elif reg == Yd:
            iy = registers[IYl] + 256 * registers[IYh]
            simulator.memory[iy] = r
        elif reg == N:
            simulator.memory[1] = r
        else:
            simulator.registers[reg] = r

class FRTracer(BaseTracer):
    def __init__(self, *base_opcodes):
        if len(base_opcodes) == 2:
            p = base_opcodes[0]
            base_opcode = base_opcodes[1]
            opcodes = (
                (B, (p, base_opcode)),                # B
                (C, (p, base_opcode + 1)),            # C
                (D, (p, base_opcode + 2)),            # D
                (E, (p, base_opcode + 3)),            # E
                (H, (p, base_opcode + 4)),            # H
                (L, (p, base_opcode + 5)),            # L
                (Hd, (p, base_opcode + 6)),           # (HL)
                (A, (p, base_opcode + 7)),            # A
                (IXh, (0xDD, p, base_opcode + 4)),    # IXh
                (IXl, (0xDD, p, base_opcode + 5)),    # IXl
                (IYh, (0xFD, p, base_opcode + 4)),    # IYh
                (IYl, (0xFD, p, base_opcode + 5)),    # IYl
                (Xd, (0xDD, p, base_opcode + 6, 0)),  # (IX+0)
                (Yd, (0xFD, p, base_opcode + 6, 0)),  # (IY+0)
            )
        else:
            base_opcode = base_opcodes[0]
            opcodes = (
                (B, (base_opcode,)),                  # B
                (C, (base_opcode + 1,)),              # C
                (D, (base_opcode + 2,)),              # D
                (E, (base_opcode + 3,)),              # E
                (H, (base_opcode + 4,)),              # H
                (L, (base_opcode + 5,)),              # L
                (Hd, (base_opcode + 6,)),             # (HL)
                (A, (base_opcode + 7,)),              # A
                (IXh, (0xDD, base_opcode + 4)),       # IXh
                (IXl, (0xDD, base_opcode + 5)),       # IXl
                (IYh, (0xFD, base_opcode + 4)),       # IYh
                (IYl, (0xFD, base_opcode + 5)),       # IYl
                (Xd, (0xDD, base_opcode + 6, 0)),     # (IX+0)
                (Yd, (0xFD, base_opcode + 6, 0)),     # (IY+0)
            )
        super().__init__(0xFFFF, opcodes)

    def prepare(self, simulator):
        simulator.registers[F] = self.count // 256
        r = self.count % 256
        reg, opcodes = self.opcodes[self.index]
        simulator.memory[:len(opcodes)] = opcodes
        if reg == Hd:
            hl = simulator.registers[L] + 256 * simulator.registers[H]
            simulator.memory[hl] = r
        elif reg == Xd:
            ix = simulator.registers[IXl] + 256 * simulator.registers[IXh]
            simulator.memory[ix] = r
        elif reg == Yd:
            iy = simulator.registers[IYl] + 256 * simulator.registers[IYh]
            simulator.memory[iy] = r
        else:
            simulator.registers[reg] = r

class RSTracer(BaseTracer):
    def __init__(self, base_opcode):
        opcodes = (
            (IXh, B, (0xDD, 0xCB, 0, base_opcode)),     # (IX+0),B
            (IXh, C, (0xDD, 0xCB, 0, base_opcode + 1)), # (IX+0),C
            (IXh, D, (0xDD, 0xCB, 0, base_opcode + 2)), # (IX+0),D
            (IXh, E, (0xDD, 0xCB, 0, base_opcode + 3)), # (IX+0),E
            (IXh, H, (0xDD, 0xCB, 0, base_opcode + 4)), # (IX+0),H
            (IXh, L, (0xDD, 0xCB, 0, base_opcode + 5)), # (IX+0),L
            (IXh, A, (0xDD, 0xCB, 0, base_opcode + 7)), # (IX+0),A
            (IYh, B, (0xFD, 0xCB, 0, base_opcode)),     # (IY+0),B
            (IYh, C, (0xFD, 0xCB, 0, base_opcode + 1)), # (IY+0),C
            (IYh, D, (0xFD, 0xCB, 0, base_opcode + 2)), # (IY+0),D
            (IYh, E, (0xFD, 0xCB, 0, base_opcode + 3)), # (IY+0),E
            (IYh, H, (0xFD, 0xCB, 0, base_opcode + 4)), # (IY+0),H
            (IYh, L, (0xFD, 0xCB, 0, base_opcode + 5)), # (IY+0),L
            (IYh, A, (0xFD, 0xCB, 0, base_opcode + 7)), # (IY+0),A
        )
        super().__init__(0x3FF, opcodes)

    def prepare(self, simulator):
        reg, dest, opcodes = self.opcodes[self.index]
        simulator.memory[:len(opcodes)] = opcodes
        simulator.registers[F] = (self.count // 512) * 255
        simulator.registers[dest] = ((self.count // 256) % 2) * 255
        xy = simulator.registers[reg] * 256 + simulator.registers[reg + 1]
        simulator.memory[xy] = self.count % 256

class AFTracer(BaseTracer):
    def __init__(self, *opcodes):
        super().__init__(0xFFFF, [opcodes])

    def prepare(self, simulator):
        simulator.memory[:len(self.opcodes[0])] = self.opcodes[0]
        simulator.registers[F] = self.count // 256
        simulator.registers[A] = self.count % 256

class FTracer(BaseTracer):
    def __init__(self, opcode):
        super().__init__(0xFF, [[opcode]])

    def prepare(self, simulator):
        simulator.memory[:1] = self.opcodes[0]
        simulator.registers[F] = self.count

class HLRRFTracer(BaseTracer):
    def __init__(self, *base_opcodes):
        if len(base_opcodes) == 1:
            base_opcode = base_opcodes[0]
            opcodes = (
                (H, B, (base_opcode,)),              # HL,BC
                (H, D, (base_opcode + 16,)),         # HL,DE
                (H, SP, (base_opcode + 48,)),        # HL,SP
                (IXh, B, (0xDD, base_opcode)),       # IX,BC
                (IXh, D, (0xDD, base_opcode + 16)),  # IX,DE
                (IXh, SP, (0xDD, base_opcode + 48)), # IX,SP
                (IYh, B, (0xFD, base_opcode)),       # IY,BC
                (IYh, D, (0xFD, base_opcode + 16)),  # IY,DE
                (IYh, SP, (0xFD, base_opcode + 48)), # IY,SP
            )
        else:
            p = base_opcodes[0]
            base_opcode = base_opcodes[1]
            opcodes = (
                (H, B, (p, base_opcode)),            # HL,BC
                (H, D, (p, base_opcode + 16)),       # HL,DE
                (H, SP, (p, base_opcode + 48)),      # HL,SP
            )
        super().__init__(0x07FFFF, opcodes)

    def prepare(self, simulator):
        r1h, r2h, opcodes = self.opcodes[self.index]
        simulator.memory[:len(opcodes)] = opcodes
        simulator.registers[F] = (self.count >> 18) * 255
        if r2h == SP:
            simulator.registers[SP] = self.count % 65536
        else:
            simulator.registers[r2h] = (self.count & 0xFF00) // 256
            simulator.registers[r2h + 1] = self.count % 256
        v = (self.count // 65536) & 0xFF
        b = (v & 0x01) + 16 * (v & 0x02)
        simulator.registers[r1h] = b
        simulator.registers[r1h + 1] = b

class HLFTracer(BaseTracer):
    def __init__(self, *base_opcodes):
        if len(base_opcodes) == 1:
            base_opcode = base_opcodes[0]
            opcodes = (
                (H, (base_opcode,)),           # HL,HL
                (IXh, (0xDD, base_opcode)),    # IX,IX
                (IYh, (0xFD, base_opcode)),    # IY,IY
            )
        else:
            p = base_opcodes[0]
            base_opcode = base_opcodes[1]
            opcodes = (
                (H, (p, base_opcode)),         # HL,HL
                (IXh, (0xDD, p, base_opcode)), # IX,IX
                (IYh, (0xDD, p, base_opcode)), # IY,IY
            )
        super().__init__(0x1FFFF, opcodes)

    def prepare(self, simulator):
        rh, opcodes = self.opcodes[self.index]
        simulator.memory[:len(opcodes)] = opcodes
        simulator.registers[F] = (self.count // 65536) * 255
        simulator.registers[rh] = (self.count // 256) % 256
        simulator.registers[rh + 1] = self.count % 256

class BlockTracer(BaseTracer):
    def __init__(self, *opcodes):
        super().__init__(0x3FFFF, [opcodes])

    def prepare(self, simulator):
        registers, memory = simulator.registers, simulator.memory
        memory[:2] = self.opcodes[0]
        registers[A] = 0x03
        if self.count & 0x20000:
            # LDIR should not touch the S, Z and C flags
            registers[F] = 0xC1 # SZ.....C
        else:
            registers[F] = 0x3E # ..5H3PN.
        bc = self.count % 65536
        registers[B] = bc // 256
        registers[C] = bc % 256
        de = 0xFE00
        registers[D] = de // 256
        registers[E] = de % 256
        hl = 0xFF00
        registers[H] = hl // 256
        registers[L] = hl % 256
        if self.count & 0x10000:
            memory[hl] = registers[A]
        else:
            memory[hl] = registers[A] ^ 0xFF
        simulator.memory[de] = simulator.memory[hl] ^ 0xFF

class BitTracer(BaseTracer):
    def __init__(self):
        base_opcodes = (
            (B, (0xCB, 0x40)),           # B
            (C, (0xCB, 0x41)),           # C
            (D, (0xCB, 0x42)),           # D
            (E, (0xCB, 0x43)),           # E
            (H, (0xCB, 0x44)),           # H
            (L, (0xCB, 0x45)),           # L
            (Hd, (0xCB, 0x46)),          # (HL)
            (A, (0xCB, 0x47)),           # A
            (Xd, (0xDD, 0xCB, 0, 0x40)), # (IX+0)
            (Xd, (0xDD, 0xCB, 0, 0x41)), # (IX+0)
            (Xd, (0xDD, 0xCB, 0, 0x42)), # (IX+0)
            (Xd, (0xDD, 0xCB, 0, 0x43)), # (IX+0)
            (Xd, (0xDD, 0xCB, 0, 0x44)), # (IX+0)
            (Xd, (0xDD, 0xCB, 0, 0x45)), # (IX+0)
            (Xd, (0xDD, 0xCB, 0, 0x46)), # (IX+0)
            (Xd, (0xDD, 0xCB, 0, 0x47)), # (IX+0)
            (Yd, (0xFD, 0xCB, 0, 0x40)), # (IY+0)
            (Yd, (0xFD, 0xCB, 0, 0x41)), # (IY+0)
            (Yd, (0xFD, 0xCB, 0, 0x42)), # (IY+0)
            (Yd, (0xFD, 0xCB, 0, 0x43)), # (IY+0)
            (Yd, (0xFD, 0xCB, 0, 0x44)), # (IY+0)
            (Yd, (0xFD, 0xCB, 0, 0x45)), # (IY+0)
            (Yd, (0xFD, 0xCB, 0, 0x46)), # (IY+0)
            (Yd, (0xFD, 0xCB, 0, 0x47)), # (IY+0)
        )
        opcodes = []
        for bit in range(8):
            for reg, values in base_opcodes:
                opcodes.append((reg, (*values[:-1], values[-1] + bit * 8)))
        super().__init__(0x1FF, opcodes)

    def prepare(self, simulator):
        registers, memory = simulator.registers, simulator.memory
        reg, opcodes = self.opcodes[self.index]
        memory[:len(opcodes)] = opcodes
        registers[F] = (self.count // 256) * 255
        if reg in (Xd, Yd):
            rr = 0x6000
            if self.count & 0x02:
                rr |= 0x2000
            if self.count & 0x01:
                rr |= 0x0800
            if reg == Xd:
                registers[IXl] = rr % 256
                registers[IXh] = rr // 256
            else:
                registers[IYl] = rr % 256
                registers[IYh] = rr // 256
            memory[rr] = self.count % 256
        elif reg == Hd:
            hl = 0x6000
            registers[L] = hl % 256
            registers[H] = hl // 256
            memory[hl] = self.count % 256
        else:
            registers[reg] = self.count % 256

class RRDRLDTracer(BaseTracer):
    def __init__(self, *opcodes):
        super().__init__(0x1FFFF, [opcodes])

    def prepare(self, simulator):
        registers, memory = simulator.registers, simulator.memory
        memory[:2] = self.opcodes[0]
        registers[A] = (self.count // 256) % 256
        registers[F] = (self.count // 65536) * 255
        hl = 0x6000
        registers[H] = hl // 256
        registers[L] = hl % 256
        memory[hl] = self.count % 256

class InTracer(BaseTracer):
    def __init__(self):
        opcodes = (
            (0xED, 0x40), # IN B,(C)
            (0xED, 0x48), # IN C,(C)
            (0xED, 0x50), # IN D,(C)
            (0xED, 0x58), # IN E,(C)
            (0xED, 0x60), # IN H,(C)
            (0xED, 0x68), # IN L,(C)
            (0xED, 0x70), # IN F,(C)
            (0xED, 0x78), # IN A,(C)
        )
        super().__init__(0x1FF, opcodes)
        self.value = 0

    def prepare(self, simulator):
        simulator.memory[:2] = self.opcodes[self.index]
        simulator.registers[B] = 0xAA
        simulator.registers[C] = 0xFE
        simulator.registers[F] = (self.count // 256) * 255
        self.value = self.count % 256

    def read_port(self, registers, port):
        return self.value

class AIRTracer(BaseTracer):
    def __init__(self, reg, *opcodes):
        super().__init__(0x1FF, [opcodes])
        self.reg = reg

    def prepare(self, simulator):
        simulator.memory[:2] = self.opcodes[0]
        simulator.registers[F] = (self.count // 256) * 255
        simulator.registers[self.reg] = self.count % 256

SUITES = {
    'ALO': (
        'Arithmetic/logic operations on the accumulator',
        ('ADD_A_r', AFRTracer, (0x80,)),
        ('ADD_A_A', AFTracer,  (0x87,)),
        ('ADC_A_r', AFRTracer, (0x88,)),
        ('ADC_A_A', AFTracer,  (0x8F,)),
        ('SUB_r',   AFRTracer, (0x90,)),
        ('SUB_A',   AFTracer,  (0x97,)),
        ('SBC_A_r', AFRTracer, (0x98,)),
        ('SBC_A_A', AFTracer,  (0x9F,)),
        ('AND_r',   AFRTracer, (0xA0,)),
        ('AND_A',   AFTracer,  (0xA7,)),
        ('XOR_r',   AFRTracer, (0xA8,)),
        ('XOR_A',   AFTracer,  (0xAF,)),
        ('OR_r',    AFRTracer, (0xB0,)),
        ('OR_A',    AFTracer,  (0xB7,)),
        ('CP_r',    AFRTracer, (0xB8,)),
        ('CP_A',    AFTracer,  (0xBF,)),
    ),
    'DAA': (
        'DAA instruction',
        ('DAA', AFTracer, (0x27,)),
    ),
    'SCF': (
        'SCF/CCF instructions',
        ('SCF', FTracer, (0x37,)),
        ('CCF', FTracer, (0x3F,)),
    ),
    'CPL': (
        'CPL instruction',
        ('CPL', AFTracer, (0x2F,)),
    ),
    'NEG': (
        'NEG instruction',
        ('NEG', AFTracer, (0xED, 0x44)),
    ),
    'RA1': (
        'RLCA/RRCA/RLA/RRA instructions',
        ('RLCA', AFTracer, (0x07,)),
        ('RRCA', AFTracer, (0x0F,)),
        ('RLA',  AFTracer, (0x17,)),
        ('RRA',  AFTracer, (0x1F,)),
    ),
    'SRO': (
        'Shift/rotate instructions',
        ('RLC_r', FRTracer, (0xCB, 0x00)),
        ('RRC_r', FRTracer, (0xCB, 0x08)),
        ('RL_r',  FRTracer, (0xCB, 0x10)),
        ('RR_r',  FRTracer, (0xCB, 0x18)),
        ('SLA_r', FRTracer, (0xCB, 0x20)),
        ('SRA_r', FRTracer, (0xCB, 0x28)),
        ('SLL_r', FRTracer, (0xCB, 0x30)),
        ('SRL_r', FRTracer, (0xCB, 0x38)),
        ('RLC_r_r', RSTracer, (0x00,)),
        ('RRC_r_r', RSTracer, (0x08,)),
        ('RL_r_r',  RSTracer, (0x10,)),
        ('RR_r_r',  RSTracer, (0x18,)),
        ('SLA_r_r', RSTracer, (0x20,)),
        ('SRA_r_r', RSTracer, (0x28,)),
        ('SLL_r_r', RSTracer, (0x30,)),
        ('SRL_r_r', RSTracer, (0x38,)),
    ),
    'INC': (
        'INC/DEC instructions',
        ('INC_r', FRTracer, (0x04,)),
        ('DEC_r', FRTracer, (0x05,)),
    ),
    'AHL': (
        '16-bit ADD/ADC/SBC instructions',
        ('ADD_HL_rr', HLRRFTracer, (0x09,)),
        ('ADC_HL_rr', HLRRFTracer, (0xED, 0x4A)),
        ('SBC_HL_rr', HLRRFTracer, (0xED, 0x42)),
        ('ADD_HL_HL', HLFTracer, (0x29,)),
        ('ADC_HL_HL', HLFTracer, (0xED, 0x6A)),
        ('SBC_HL_HL', HLFTracer, (0xED, 0x62)),
    ),
    'BLK': (
        'Block LD/CP/IN/OUT instructions',
        ('LDI',  BlockTracer, (0xED, 0xA0)),
        ('LDD',  BlockTracer, (0xED, 0xA8)),
        ('CPI',  BlockTracer, (0xED, 0xA1)),
        ('CPD',  BlockTracer, (0xED, 0xA9)),
        ('INI',  BlockTracer, (0xED, 0xA2)),
        ('IND',  BlockTracer, (0xED, 0xAA)),
        ('OUTI', BlockTracer, (0xED, 0xA3)),
        ('OUTD', BlockTracer, (0xED, 0xAB)),
    ),
    'BIT': (
        'BIT n,[r,xy] instructions',
        ('BIT_n', BitTracer, ()),
    ),
    'RRD': (
        'RRD/RLD instructions',
        ('RRD', RRDRLDTracer, (0xED, 0x67)),
        ('RLD', RRDRLDTracer, (0xED, 0x6F)),
    ),
    'INR': (
        'IN r,(C) instructions',
        ('IN_r_C', InTracer, ()),
    ),
    'AIR': (
        'LD A,I/R instructions',
        ('LD_A_I', AIRTracer, (I, 0xED, 0x57)),
        ('LD_A_R', AIRTracer, (R, 0xED, 0x5F)),
    ),
}
