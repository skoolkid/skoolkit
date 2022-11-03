# Copyright 2022 Richard Dymond (rjdymond@gmail.com)
#
# This file is part of SkoolKit.
#
# SkoolKit is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# SkoolKit is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# SkoolKit. If not, see <http://www.gnu.org/licenses/>.

from functools import partial

PARITY = tuple((1 - bin(r).count('1') % 2) * 4 for r in range(256))

ADC = tuple(
    tuple(
        ((a + n + 1) & 0xA8)                                 # S.5.3.N.
        + ((a + n + 1) % 256 == 0) * 0x40                    # .Z......
        + (((a % 16) + ((n + 1) % 16)) & 0x10)               # ...H....
        + ((a ^ n ^ 0x80) & (a ^ (a + n + 1)) & 0x80) // 32  # .....P..
        + (a + n + 1 > 0xFF)                                 # .......C
        for n in range(256)
    ) for a in range(256)
)

ADD = tuple(
    tuple(
        ((a + n) & 0xA8)                                 # S.5.3.N.
        + ((a + n) % 256 == 0) * 0x40                    # .Z......
        + (((a % 16) + (n % 16)) & 0x10)                 # ...H....
        + ((a ^ n ^ 0x80) & (a ^ (a + n)) & 0x80) // 32  # .....P..
        + (a + n > 0xFF)                                 # .......C
        for n in range(256)
    ) for a in range(256)
)

AND = tuple(
    (a & 0xA8)           # S.5.3...
    + (a == 0) * 0x40    # .Z......
    + 0x10               # ...H....
    + PARITY[a]          # .....P..
    for a in range(256)
)

CP = tuple(
    tuple(
        ((a - n) & 0x80)                          # S.......
        + 0x40 * (a == n)                         # .Z......
        + (n & 0x28)                              # ..5.3...
        + (((a % 16) - (n % 16)) & 0x10)          # ...H....
        + ((a ^ n) & (a ^ (a - n)) & 0x80) // 32  # .....P..
        + 0x02                                    # ......N.
        + (n > a)                                 # .......C
        for n in range(256)
    ) for a in range(256)
)

DEC = tuple(
    (r & 0xA8)                 # S.5.3...
    + (r == 0) * 0x40          # .Z......
    + (r % 16 == 0x0F) * 0x10  # ...H....
    + (r == 0x7F) * 0x04       # .....P..
    + 0x02                     # ......N.
    for r in range(256)
)

INC = tuple(
    (r & 0xA8)                 # S.5.3.N.
    + (r == 0) * 0x40          # .Z......
    + (r % 16 == 0x00) * 0x10  # ...H....
    + (r == 0x80) * 0x04       # .....P..
    for r in range(256)
)

JR_OFFSETS = tuple(j + 2 if j < 128 else j - 254 for j in range(256))

NEG = tuple(
    ((256 - a) & 0xA8)     # S.5.3...
    + (a == 0) * 0x40      # .Z......
    + (a % 16 > 0) * 0x10  # ...H....
    + (a == 0x80) * 0x04   # .....P..
    + 0x02                 # ......N.
    + (a > 0)              # .......C
    for a in range(256)
)

R1 = tuple((r & 0x80) + ((r + 1) % 128) for r in range(256))

R2 = tuple((r & 0x80) + ((r + 2) % 128) for r in range(256))

RL = (
    tuple((r * 2) % 256 for r in range(256)),
    tuple((r * 2) % 256 + 1 for r in range(256))
)

RLC = tuple(r // 128 + ((r * 2) % 256) for r in range(256))

RR = (
    tuple(r // 2 for r in range(256)),
    tuple(128 + r // 2 for r in range(256))
)

RRC = tuple(((r * 128) % 256) + r // 2 for r in range(256))

SBC = tuple(
    tuple(
        ((a - n - 1) & 0xA8)                          # S.5.3...
        + (a == (n + 1) % 256) * 0x40                 # .Z......
        + (((a % 16) - ((n + 1) % 16)) & 0x10)        # ...H....
        + ((a ^ n) & (a ^ (a - n - 1)) & 0x80) // 32  # .....P..
        + 0x02                                        # ......N.
        + (n + 1 > a) for n in range(256)             # .......C
    ) for a in range(256)
)

SLA = RL[0]

SLL = RL[1]

SRA = tuple((r & 0x80) + r // 2 for r in range(256))

SRL = RR[0]

SUB = tuple(
    tuple(
        ((a - n) & 0xA8)                          # S.5.3...
        + (a == n) * 0x40                         # .Z......
        + (((a % 16) - (n % 16)) & 0x10)          # ...H....
        + ((a ^ n) & (a ^ (a - n)) & 0x80) // 32  # .....P..
        + 0x02                                    # ......N.
        + (n > a) for n in range(256)             # .......C
    ) for a in range(256)
)

SZ53P = tuple(
    (r & 0xA8)           # S.5.3...
    + (r == 0) * 0x40    # .Z......
    + PARITY[r]          # .....P..
    for r in range(256)
)

FRAME_DURATION = 69888

CONFIG = {
    'fast_djnz': False,
    'fast_ldir': False,
}

A = 0
F = 1
B = 2
C = 3
D = 4
E = 5
H = 6
L = 7
IXh = 8
IXl = 9
IYh = 10
IYl = 11
SP = 12
I = 14
R = 15
xA = 16
xF = 17
xB = 18
xC = 19
xD = 20
xE = 21
xH = 22
xL = 23
PC = 24
T = 25
Bd = 26
Dd = 28
Hd = 30
Xd = 32
Yd = 33
N = 34

REGISTERS = {
    'A': A,
    'F': F,
    'B': B,
    'C': C,
    'D': D,
    'E': E,
    'H': H,
    'L': L,
    'IXh': IXh,
    'IXl': IXl,
    'IYh': IYh,
    'IYl': IYl,
    'SP': SP,
    'I': I,
    'R': R,
    '^A': xA,
    '^F': xF,
    '^B': xB,
    '^C': xC,
    '^D': xD,
    '^E': xE,
    '^H': xH,
    '^L': xL,
    'PC': PC,
    'T': T
}

class Simulator:
    def __init__(self, memory, registers=None, state=None, config=None):
        self.memory = memory
        self.registers = [
            0,     # A
            0,     # F
            0,     # B
            0,     # C
            0,     # D
            0,     # E
            0,     # H
            0,     # L
            0,     # IXh
            0,     # IXl
            92,    # IYh
            58,    # IYl
            23552, # SP
            0,     # Unused
            63,    # I
            0,     # R
            0,     # xA
            0,     # xF
            0,     # xB
            0,     # xC
            0,     # xD
            0,     # xE
            0,     # xH
            0,     # xL
            0,     # PC
            0      # T (T-states)
        ]
        if registers:
            self.set_registers(registers)
        if state is None:
            state = {}
        self.ppcount = 0
        self.imode = state.get('im', 1)
        self.iff2 = state.get('iff', 0)
        self.registers[25] = state.get('tstates', 0)
        cfg = CONFIG.copy()
        if config:
            cfg.update(config)
        self.create_opcodes()
        if cfg['fast_djnz']:
            self.opcodes[0x10] = partial(self.djnz_fast, self.registers, self.memory)
        if cfg['fast_ldir']:
            self.after_ED[0xB0] = partial(self.ldir_fast, self.registers, self.memory, 1)
            self.after_ED[0xB8] = partial(self.ldir_fast, self.registers, self.memory, -1)
        self.in_tracer = None
        self.out_tracer = None

    def set_tracer(self, tracer):
        if hasattr(tracer, 'read_port'):
            self.in_tracer = partial(tracer.read_port, self)
        else:
            self.in_tracer = None
        if hasattr(tracer, 'write_port'):
            self.out_tracer = partial(tracer.write_port, self)
        else:
            self.out_tracer = None

    def run(self, start=None, stop=None):
        opcodes = self.opcodes
        memory = self.memory
        registers = self.registers
        if start is not None:
            registers[24] = start
        pc = registers[24]

        if stop is None:
            opcodes[memory[pc]]()
        else:
            while True:
                opcodes[memory[pc]]()
                pc = registers[24]
                if pc == stop:
                    break

    def set_registers(self, registers):
        for reg, value in registers.items():
            if reg in REGISTERS:
                self.registers[REGISTERS[reg]] = value
            elif reg in ('IX', 'IY'):
                rh = REGISTERS[reg + 'h']
                self.registers[rh] = value // 256
                self.registers[rh + 1] = value % 256
            elif reg.startswith('^'):
                rh = REGISTERS[reg[:2]]
                self.registers[rh] = value // 256
                self.registers[rh + 1] = value % 256
            elif len(reg) == 2:
                rh = REGISTERS[reg[0]]
                self.registers[rh] = value // 256
                self.registers[rh + 1] = value % 256

    def prefix(self, opcodes, registers, memory):
        opcodes[memory[(registers[24] + 1) % 65536]]()

    def prefix2(self, opcodes, registers, memory):
        opcodes[memory[(registers[24] + 3) % 65536]]()

    def get_operand_value(self, registers, memory, size, reg):
        if reg < 16:
            return registers[reg]
        if reg < 32:
            return memory[registers[reg - 23] + 256 * registers[reg - 24]]
        if reg == 34:
            return memory[(registers[24] + size - 1) % 65536]
        offset = memory[(registers[24] + 2) % 65536]
        if offset >= 128:
            offset -= 256
        if reg == 32:
            return memory[(registers[9] + 256 * registers[8] + offset) % 65536]
        return memory[(registers[11] + 256 * registers[10] + offset) % 65536]

    def set_operand_value(self, registers, memory, reg, value):
        if reg < 16:
            registers[reg] = value
        elif reg < 32:
            self.poke(memory, registers[reg - 23] + 256 * registers[reg - 24], value)
        else:
            offset = memory[(registers[24] + 2) % 65536]
            if offset >= 128:
                offset -= 256
            if reg == 32:
                self.poke(memory, (registers[9] + 256 * registers[8] + offset) % 65536, value)
            else:
                self.poke(memory, (registers[11] + 256 * registers[10] + offset) % 65536, value)

    def poke(self, memory, address, *values):
        if address > 0x3FFF:
            memory[address] = values[0]
        if len(values) > 1:
            address = (address + 1) % 65536
            if address > 0x3FFF:
                memory[address] = values[1]

    def adc_a_a(self, registers):
        a = registers[0]
        if registers[1] % 2:
            registers[0] = (a * 2 + 1) % 256
            if a % 16 == 0x0F:
                registers[1] = ADC[a][a] + 0x10
            else:
                registers[1] = ADC[a][a]
        else:
            registers[0] = (a * 2) % 256
            registers[1] = ADD[a][a]
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def adc_a(self, registers, memory, r_inc, timing, size, reg):
        addend = self.get_operand_value(registers, memory, size, reg)
        a = registers[0]
        if registers[1] % 2:
            registers[0] = (a + addend + 1) % 256
            registers[1] = ADC[a][addend]
        else:
            registers[0] = (a + addend) % 256
            registers[1] = ADD[a][addend]
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def adc_hl(self, registers, reg):
        if reg == 12:
            rr = registers[12]
        else:
            rr = registers[reg + 1] + 256 * registers[reg]
        hl = registers[7] + 256 * registers[6]
        rr_c = rr + registers[1] % 2
        result = hl + rr_c

        if result > 0xFFFF:
            result %= 65536
            f = 0x01 # .......C
        else:
            f = 0
        if ((hl % 4096) + (rr_c % 4096)) & 0x1000:
            f += 0x10 # ...H....
        if result & 0x8000:
            f += 0x80 # S.......
        elif result == 0:
            f += 0x40 # .Z......
        if (hl ^ rr) & 0x8000 == 0 and (result ^ hl) & 0x8000:
            # Augend and addend signs are the same - overflow if their sign
            # differs from the sign of the result
            f += 0x04 # .....P..

        h = result // 256
        registers[1] = f + (h & 0x28)
        registers[7] = result % 256
        registers[6] = h

        registers[15] = R2[registers[15]]
        registers[25] += 15
        registers[24] = (registers[24] + 2) % 65536

    def add_a(self, registers, memory, r_inc, timing, size, reg):
        addend = self.get_operand_value(registers, memory, size, reg)
        a = registers[0]
        registers[0] = (a + addend) % 256
        registers[1] = ADD[a][addend]
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def add16(self, registers, r_inc, timing, size, augend, reg):
        if reg == 12:
            addend_v = registers[12]
        else:
            addend_v = registers[reg + 1] + 256 * registers[reg]
        augend_v = registers[augend + 1] + 256 * registers[augend]
        result = augend_v + addend_v

        if result > 0xFFFF:
            result %= 65536
            f = (registers[1] & 0xC4) + 0x01 # SZ...P.C
        else:
            f = registers[1] & 0xC4 # SZ...P..
        if ((augend_v % 4096) + (addend_v % 4096)) & 0x1000:
            f += 0x10 # ...H....

        result_hi = result // 256
        registers[1] = f + (result_hi & 0x28)
        registers[augend + 1] = result % 256
        registers[augend] = result_hi

        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def and_n(self, registers, memory):
        pcn = registers[24] + 1
        a = registers[0] & memory[pcn % 65536]
        registers[0] = a
        registers[1] = AND[a]
        registers[15] = R1[registers[15]]
        registers[25] += 7
        registers[24] = (pcn + 1) % 65536

    def and_r(self, registers, r):
        a = registers[0] & registers[r]
        registers[0] = a
        registers[1] = AND[a]
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def anda(self, registers, memory, r_inc, timing, size, reg):
        a = registers[0] & self.get_operand_value(registers, memory, size, reg)
        registers[0] = a
        registers[1] = AND[a]
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def bit(self, registers, memory, timing, size, mask, reg):
        value = self.get_operand_value(registers, memory, size, reg)
        f = 0x10 + (registers[1] % 2) # ...H..NC
        if value & mask == 0:
            f += 0x44 # .Z...P..
        elif mask == 128:
            f += 0x80 # S.......
        if reg >= 32:
            offset = memory[(registers[24] + 2) % 65536]
            if reg == 32:
                value = (registers[9] + 256 * registers[8] + offset) // 256
            else:
                value = (registers[11] + 256 * registers[10] + offset) // 256
        registers[1] = f + (value & 0x28)
        registers[15] = R2[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def call(self, registers, memory, c_and, c_val):
        if c_and and registers[1] & c_and == c_val:
            registers[25] += 10
            registers[24] = (registers[24] + 3) % 65536
        else:
            pc = registers[24]
            ret_addr = (pc + 3) % 65536
            self.ppcount += 1
            sp = (registers[12] - 2) % 65536
            registers[12] = sp
            self.poke(memory, sp, ret_addr % 256, ret_addr // 256)
            registers[25] += 17
            registers[24] = memory[(pc + 1) % 65536] + 256 * memory[(pc + 2) % 65536]
        registers[15] = R1[registers[15]]

    def cf(self, registers, flip):
        f = registers[1] & 0xC4 # SZ...PN.
        if flip and registers[1] % 2:
            registers[1] = f + (registers[0] & 0x28) + 0x10
        else:
            registers[1] = f + (registers[0] & 0x28) + 0x01
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def cp(self, registers, memory, r_inc, timing, size, reg):
        registers[1] = CP[registers[0]][self.get_operand_value(registers, memory, size, reg)]
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def cpi(self, registers, memory, inc, repeat):
        # CPI, CPD, CPIR, CPDR
        hl = registers[7] + 256 * registers[6]
        bc = registers[3] + 256 * registers[2]
        a = registers[0]

        value = memory[hl]
        result = (a - value) % 256
        hf = ((a % 16) - (value % 16)) & 0x10
        n = a - value - hf // 16
        f = (result & 0x80) + hf + 0x02 + (registers[1] % 2) # S..H..NC
        if result == 0:
            f += 0x40 # .Z......
        if n & 0x02:
            f += 0x20 # ..5.....
        if n & 0x08:
            f += 0x08 # ....3...

        hl = (hl + inc) % 65536
        bc = (bc - 1) % 65536
        registers[7] = hl % 256
        registers[6] = hl // 256
        registers[3] = bc % 256
        registers[2] = bc // 256
        if bc:
            registers[1] = f + 0x04
        else:
            registers[1] = f

        if repeat and result and bc:
            registers[25] += 21
        else:
            registers[25] += 16
            registers[24] = (registers[24] + 2) % 65536
        registers[15] = R2[registers[15]]

    def cpl(self, registers):
        a = registers[0] ^ 255
        registers[0] = a
        registers[1] = (registers[1] & 0xC5) + (a & 0x28) + 0x12
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def daa(self, registers):
        a = registers[0]
        old_f = registers[1]
        hf = old_f & 0x10
        nf = old_f & 0x02
        t = 0
        f = nf

        if hf or a % 16 > 0x09:
            t += 1
        if old_f % 2 or a > 0x99:
            t += 2
            f += 0x01 # .......C

        if (nf and hf and a % 16 < 6) or (nf == 0 and a % 16 >= 0x0A):
            f += 0x10 # ...H....

        if t == 1:
            if nf:
                a = (a + 0xFA) % 256
            else:
                a = (a + 0x06) % 256
        elif t == 2:
            if nf:
                a = (a + 0xA0) % 256
            else:
                a = (a + 0x60) % 256
        elif t == 3:
            if nf:
                a = (a + 0x9A) % 256
            else:
                a = (a + 0x66) % 256

        registers[0] = a
        registers[1] = f + SZ53P[a]
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def dec_r(self, registers, reg):
        value = (registers[reg] - 1) % 256
        registers[1] = (registers[1] % 2) + DEC[value]
        registers[reg] = value
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def di_ei(self, registers, iff2):
        self.iff2 = iff2
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def djnz(self, registers, memory):
        b = (registers[2] - 1) % 256
        registers[2] = b
        if b:
            registers[25] += 13
            pc = registers[24]
            registers[24] = (pc + JR_OFFSETS[memory[(pc + 1) % 65536]]) % 65536
        else:
            registers[25] += 8
            registers[24] = (registers[24] + 2) % 65536
        registers[15] = R1[registers[15]]

    def djnz_fast(self, registers, memory):
        if memory[(registers[24] + 1) % 65536] == 0xFE:
            b = (registers[2] - 1) % 256
            registers[2] = 0
            r = registers[15]
            registers[15] = (r & 0x80) + ((r + b + 1) % 128)
            registers[25] += b * 13 + 8
            registers[24] = (registers[24] + 2) % 65536
        else:
            self.djnz(registers, memory)

    def ex_af(self, registers):
        registers[0], registers[16] = registers[16], registers[0]
        registers[1], registers[17] = registers[17], registers[1]
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def ex_de_hl(self, registers):
        registers[4], registers[6] = registers[6], registers[4]
        registers[5], registers[7] = registers[7], registers[5]
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def ex_sp(self, registers, memory, reg):
        sp = registers[12]
        sp1 = memory[sp]
        sp2 = memory[(sp + 1) % 65536]
        self.poke(memory, sp, registers[reg + 1], registers[reg])
        registers[reg + 1] = sp1
        registers[reg] = sp2
        if reg == 6:
            registers[15] = R1[registers[15]]
            registers[25] += 19
            registers[24] = (registers[24] + 1) % 65536
        else:
            registers[15] = R2[registers[15]]
            registers[25] += 23
            registers[24] = (registers[24] + 2) % 65536

    def exx(self, registers):
        registers[2], registers[18] = registers[18], registers[2]
        registers[3], registers[19] = registers[19], registers[3]
        registers[4], registers[20] = registers[20], registers[4]
        registers[5], registers[21] = registers[21], registers[5]
        registers[6], registers[22] = registers[22], registers[6]
        registers[7], registers[23] = registers[23], registers[7]
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def halt(self, registers):
        if self.iff2:
            t = registers[25]
            if (t + 4) % FRAME_DURATION < t % FRAME_DURATION:
                registers[24] = (registers[24] + 1) % 65536
        registers[15] = R1[registers[15]]
        registers[25] += 4

    def im(self, registers, mode):
        self.imode = mode
        registers[15] = R2[registers[15]]
        registers[25] += 8
        registers[24] = (registers[24] + 2) % 65536

    def in_a(self, registers, memory):
        pcn = registers[24] + 1
        if self.in_tracer:
            registers[0] = self.in_tracer(memory[pcn % 65536] + 256 * registers[0])
        else:
            registers[0] = 191
        registers[15] = R1[registers[15]]
        registers[25] += 11
        registers[24] = (pcn + 1) % 65536

    def in_c(self, registers, reg):
        if self.in_tracer:
            value = self.in_tracer(registers[3] + 256 * registers[2])
        else:
            value = 191
        if reg != F:
            registers[reg] = value
        registers[1] = SZ53P[value] + (registers[1] % 2)
        registers[15] = R2[registers[15]]
        registers[25] += 12
        registers[24] = (registers[24] + 2) % 65536

    def inc_r(self, registers, reg):
        value = (registers[reg] + 1) % 256
        registers[1] = (registers[1] % 2) + INC[value]
        registers[reg] = value
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def inc_dec8(self, registers, memory, r_inc, timing, size, inc, flags, reg):
        value = (self.get_operand_value(registers, memory, size, reg) + inc) % 256
        registers[1] = (registers[1] % 2) + flags[value]
        self.set_operand_value(registers, memory, reg, value)
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def inc_dec16(self, registers, r_inc, timing, size, inc, reg):
        if reg == 12:
            registers[12] = (registers[12] + inc) % 65536
        else:
            value = (registers[reg + 1] + 256 * registers[reg] + inc) % 65536
            registers[reg] = value // 256
            registers[reg + 1] = value % 256
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def ini(self, registers, memory, inc, repeat):
        # INI, IND, INIR, INDR
        hl = registers[7] + 256 * registers[6]
        b = registers[2]
        c = registers[3]
        a = registers[0]

        if self.in_tracer:
            value = self.in_tracer(c + 256 * b)
        else:
            value = 191
        self.poke(memory, hl, value)
        b = (b - 1) % 256
        j = value + ((c + inc) % 256)
        f = (b & 0xA8) + PARITY[(j % 8) ^ b] # S.5.3P..
        if value & 0x80:
            f += 0x02  # ......N.
        if j > 255:
            f += 0x11 # ...H...C
        if b == 0:
            registers[1] = f + 0x40 # .Z......
        else:
            registers[1] = f

        hl = (hl + inc) % 65536
        registers[7] = hl % 256
        registers[6] = hl // 256
        registers[2] = b

        if repeat and b:
            registers[25] += 21
        else:
            registers[24] = (registers[24] + 2) % 65536
            registers[25] += 16
        registers[15] = R2[registers[15]]

    def jp(self, registers, memory, r_inc, timing, c_and, c_val):
        if c_and:
            if registers[1] & c_and == c_val:
                registers[24] = (registers[24] + 3) % 65536
            else:
                registers[24] = memory[(registers[24] + 1) % 65536] + 256 * memory[(registers[24] + 2) % 65536]
        elif c_val == 0:
            registers[24] = memory[(registers[24] + 1) % 65536] + 256 * memory[(registers[24] + 2) % 65536]
        elif c_val == 6:
            registers[24] = registers[7] + 256 * registers[6]
        else:
            registers[24] = registers[c_val + 1] + 256 * registers[c_val]
        registers[15] = r_inc[registers[15]]
        registers[25] += timing

    def jr(self, registers, memory, c_and, c_val):
        if registers[1] & c_and == c_val:
            registers[25] += 12
            pc = registers[24]
            registers[24] = (pc + JR_OFFSETS[memory[(pc + 1) % 65536]]) % 65536
        else:
            registers[25] += 7
            registers[24] = (registers[24] + 2) % 65536
        registers[15] = R1[registers[15]]

    def ld_r_n(self, registers, memory, r):
        pcn = registers[24] + 1
        registers[r] = memory[pcn % 65536]
        registers[15] = R1[registers[15]]
        registers[25] += 7
        registers[24] = (pcn + 1) % 65536

    def ld_r_r(self, registers, r1, r2):
        registers[r1] = registers[r2]
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def ld8(self, registers, memory, r_inc, timing, size, reg, reg2):
        self.set_operand_value(registers, memory, reg, self.get_operand_value(registers, memory, size, reg2))
        if reg2 in (14, 15):
            # LD A,I and LD A,R
            a = registers[0]
            if a == 0:
                f = 0x40 + (registers[1] % 2) # .Z.....C
            else:
                f = (a & 0xA8) + (registers[1] % 2) # S.5H3.NC
            if self.iff2:
                registers[1] = f + 0x04
            else:
                registers[1] = f
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def ld16(self, registers, memory, r_inc, timing, size, reg):
        end = registers[24] + size
        if reg == 12:
            registers[12] = memory[(end - 2) % 65536] + 256 * memory[(end - 1) % 65536]
        else:
            registers[reg + 1] = memory[(end - 2) % 65536]
            registers[reg] = memory[(end - 1) % 65536]
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = end % 65536

    def ld16addr(self, registers, memory, r_inc, timing, size, reg, poke):
        end = registers[24] + size
        addr = memory[(end - 2) % 65536] + 256 * memory[(end - 1) % 65536]
        if poke:
            if reg == 12:
                self.poke(memory, addr, registers[12] % 256, registers[12] // 256)
            else:
                self.poke(memory, addr, registers[reg + 1], registers[reg])
        elif reg == 12:
            registers[12] = memory[addr] + 256 * memory[(addr + 1) % 65536]
        else:
            registers[reg + 1] = memory[addr]
            registers[reg] = memory[(addr + 1) % 65536]
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = end % 65536

    def ldann(self, registers, memory, poke):
        pcn = registers[24] + 1
        if poke:
            self.poke(memory, memory[pcn % 65536] + 256 * memory[(pcn + 1) % 65536], registers[0])
        else:
            registers[0] = memory[memory[pcn % 65536] + 256 * memory[(pcn + 1) % 65536]]
        registers[15] = R1[registers[15]]
        registers[25] += 13
        registers[24] = (pcn + 2) % 65536

    def ldi(self, registers, memory, inc, repeat):
        # LDI, LDD, LDIR, LDDR
        hl = registers[7] + 256 * registers[6]
        de = registers[5] + 256 * registers[4]
        bc = registers[3] + 256 * registers[2]

        at_hl = memory[hl]
        self.poke(memory, de, at_hl)
        n = registers[0] + at_hl
        f = (registers[1] & 0xC1) + (n & 0x08) # SZ.H3.NC
        if n & 0x02:
            f += 0x20 # ..5.....

        hl = (hl + inc) % 65536
        de = (de + inc) % 65536
        bc = (bc - 1) % 65536
        registers[7] = hl % 256
        registers[6] = hl // 256
        registers[5] = de % 256
        registers[4] = de // 256
        registers[3] = bc % 256
        registers[2] = bc // 256
        if bc:
            registers[1] = f + 0x04 # .....P..
        else:
            registers[1] = f

        if repeat and bc:
            registers[25] += 21
        else:
            registers[25] += 16
            registers[24] = (registers[24] + 2) % 65536
        registers[15] = R2[registers[15]]

    def ldir_fast(self, registers, memory, inc):
        de = registers[5] + 256 * registers[4]
        bc = registers[3] + 256 * registers[2]
        hl = registers[7] + 256 * registers[6]
        count = 0
        repeat = True
        while repeat:
            self.poke(memory, de, memory[hl])
            bc = (bc - 1) % 65536
            if bc == 0 or registers[24] <= de <= registers[24] + 1:
                repeat = False
            de = (de + inc) % 65536
            hl = (hl + inc) % 65536
            count += 1
        registers[3], registers[2] = bc % 256, bc // 256
        registers[5], registers[4] = de % 256, de // 256
        registers[7], registers[6] = hl % 256, hl // 256
        r = registers[15]
        registers[15] = (r & 0x80) + ((r + 2 * count) % 128)
        n = registers[0] + memory[(hl - inc) % 65536]
        f = (registers[1] & 0xC1) + (n & 0x08) # SZ.H3.NC
        if bc:
            f += 0x04 # .....P..
        else:
            registers[24] = (registers[24] + 2) % 65536
        if n & 0x02:
            registers[1] = f + 0x20
        else:
            registers[1] = f
        registers[25] += 21 * count - 5

    def ldsprr(self, registers, r_inc, timing, size, reg):
        registers[12] = registers[reg + 1] + 256 * registers[reg]
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def neg(self, registers):
        a = registers[0]
        registers[0] = (256 - a) % 256
        registers[1] = NEG[a]
        registers[15] = R2[registers[15]]
        registers[25] += 8
        registers[24] = (registers[24] + 2) % 65536

    def nop(self, registers):
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def nop_dd_fd(self, registers):
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def nop_ed(self, registers):
        registers[15] = R2[registers[15]]
        registers[25] += 8
        registers[24] = (registers[24] + 2) % 65536

    def or_n(self, registers, memory):
        pcn = registers[24] + 1
        a = registers[0] | memory[pcn % 65536]
        registers[0] = a
        registers[1] = SZ53P[a]
        registers[15] = R1[registers[15]]
        registers[25] += 7
        registers[24] = (pcn + 1) % 65536

    def or_r(self, registers, r):
        a = registers[0] | registers[r]
        registers[0] = a
        registers[1] = SZ53P[a]
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def ora(self, registers, memory, r_inc, timing, size, reg):
        a = registers[0] | self.get_operand_value(registers, memory, size, reg)
        registers[0] = a
        registers[1] = SZ53P[a]
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def outa(self, registers, memory):
        pcn = registers[24] + 1
        if self.out_tracer:
            a = registers[0]
            self.out_tracer(memory[pcn % 65536] + 256 * a, a)
        registers[15] = R1[registers[15]]
        registers[25] += 11
        registers[24] = (pcn + 1) % 65536

    def outc(self, registers, reg):
        if self.out_tracer:
            if reg >= 0:
                self.out_tracer(registers[3] + 256 * registers[2], registers[reg])
            else:
                self.out_tracer(registers[3] + 256 * registers[2], 0)
        registers[15] = R2[registers[15]]
        registers[25] += 12
        registers[24] = (registers[24] + 2) % 65536

    def outi(self, registers, memory, inc, repeat):
        # OUTI, OUTD, OTIR, OTDR
        hl = registers[7] + 256 * registers[6]
        b = (registers[2] - 1) % 256

        outval = memory[hl]
        if self.out_tracer:
            self.out_tracer(registers[3] + 256 * b, outval)
        hl = (hl + inc) % 65536
        k = (hl % 256) + outval
        f = (b & 0xA8) + PARITY[(k % 8) ^ b] # S.5.3P..
        if b == 0:
            f += 0x40 # .Z......
        if k > 255:
            f += 0x11 # ...H...C

        registers[7] = hl % 256
        registers[6] = hl // 256
        registers[2] = b
        if outval & 0x80:
            registers[1] = f + 0x02 # ......N.
        else:
            registers[1] = f

        if repeat and b:
            registers[25] += 21
        else:
            registers[25] += 16
            registers[24] = (registers[24] + 2) % 65536
        registers[15] = R2[registers[15]]

    def pop(self, registers, memory, r_inc, timing, size, reg):
        self.ppcount -= 1
        sp = registers[12]
        registers[12] = (sp + 2) % 65536
        registers[reg + 1] = memory[sp]
        registers[reg] = memory[(sp + 1) % 65536]
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def push(self, registers, memory, r_inc, timing, size, reg):
        self.ppcount += 1
        sp = (registers[12] - 2) % 65536
        registers[12] = sp
        self.poke(memory, sp, registers[reg + 1], registers[reg])
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def ret(self, registers, memory, c_and, c_val):
        if c_and:
            if registers[1] & c_and == c_val:
                registers[25] += 5
                registers[24] = (registers[24] + 1) % 65536
            else:
                registers[25] += 11
                self.ppcount -= 1
                sp = registers[12]
                registers[12] = (sp + 2) % 65536
                registers[24] = memory[sp] + 256 * memory[(sp + 1) % 65536]
        else:
            registers[25] += 10
            self.ppcount -= 1
            sp = registers[12]
            registers[12] = (sp + 2) % 65536
            registers[24] = memory[sp] + 256 * memory[(sp + 1) % 65536]
        registers[15] = R1[registers[15]]

    def reti(self, registers, memory):
        self.ppcount -= 1
        registers[15] = R2[registers[15]]
        registers[25] += 14
        sp = registers[12]
        registers[12] = (sp + 2) % 65536
        registers[24] = memory[sp] + 256 * memory[(sp + 1) % 65536]

    def res_set(self, registers, memory, timing, size, bit, reg, bitval, dest=-1):
        if bitval:
            value = self.get_operand_value(registers, memory, size, reg) | bit
        else:
            value = self.get_operand_value(registers, memory, size, reg) & bit
        self.set_operand_value(registers, memory, reg, value)
        if dest >= 0:
            registers[dest] = value
        registers[15] = R2[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def rld(self, registers, memory):
        hl = registers[7] + 256 * registers[6]
        a = registers[0]
        at_hl = memory[hl]
        self.poke(memory, hl, ((at_hl * 16) % 256) + (a % 16))
        a_out = registers[0] = (a & 240) + ((at_hl // 16) % 16)
        registers[1] = SZ53P[a_out] + (registers[1] % 2)
        registers[15] = R2[registers[15]]
        registers[25] += 18
        registers[24] = (registers[24] + 2) % 65536

    def rrd(self, registers, memory):
        hl = registers[7] + 256 * registers[6]
        a = registers[0]
        at_hl = memory[hl]
        self.poke(memory, hl, ((a * 16) % 256) + (at_hl // 16))
        a_out = registers[0] = (a & 240) + (at_hl % 16)
        registers[1] = SZ53P[a_out] + (registers[1] % 2)
        registers[15] = R2[registers[15]]
        registers[25] += 18
        registers[24] = (registers[24] + 2) % 65536

    def rotate_a(self, registers, cbit, rotate, circular=0):
        a = registers[0]
        old_f = registers[1]
        if circular:
            value = rotate[a]
        else:
            value = rotate[old_f % 2][a]
        registers[0] = value
        if a & cbit:
            registers[1] = (old_f & 0xC4) + (value & 0x28) + 0x01
        else:
            registers[1] = (old_f & 0xC4) + (value & 0x28)
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def rotate_r(self, registers, cbit, rotate, reg, circular=0):
        r = registers[reg]
        if circular:
            value = rotate[r]
        else:
            value = rotate[registers[1] % 2][r]
        registers[reg] = value
        if r & cbit:
            registers[1] = SZ53P[value] + 0x01
        else:
            registers[1] = SZ53P[value]
        registers[15] = R2[registers[15]]
        registers[25] += 8
        registers[24] = (registers[24] + 2) % 65536

    def rotate(self, registers, memory, timing, size, cbit, rotate, reg, circular=0, dest=-1):
        r = self.get_operand_value(registers, memory, size, reg)
        if circular:
            value = rotate[r]
        else:
            value = rotate[registers[1] % 2][r]
        self.set_operand_value(registers, memory, reg, value)
        if dest >= 0:
            registers[dest] = value
        if r & cbit:
            registers[1] = SZ53P[value] + 0x01
        else:
            registers[1] = SZ53P[value]
        registers[15] = R2[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def rst(self, registers, memory, addr):
        self.ppcount += 1
        sp = (registers[12] - 2) % 65536
        registers[12] = sp
        ret_addr = (registers[24] + 1) % 65536
        self.poke(memory, sp, ret_addr % 256, ret_addr // 256)
        registers[15] = R1[registers[15]]
        registers[25] += 11
        registers[24] = addr

    def sbc_a_a(self, registers):
        if registers[1] % 2:
            registers[0] = 0xFF
            registers[1] = 0xBB
        else:
            registers[0] = 0x00
            registers[1] = 0x42
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def sbc_a(self, registers, memory, r_inc, timing, size, reg):
        subtrahend = self.get_operand_value(registers, memory, size, reg)
        a = registers[0]
        if registers[1] % 2:
            registers[1] = SBC[a][subtrahend]
            registers[0] = (a - subtrahend - 1) % 256
        else:
            registers[1] = SUB[a][subtrahend]
            registers[0] = (a - subtrahend) % 256
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def sbc_hl(self, registers, r_inc, reg):
        if reg == 12:
            rr = registers[12]
        else:
            rr = registers[reg + 1] + 256 * registers[reg]
        hl = registers[7] + 256 * registers[6]
        rr_c = rr + (registers[1] % 2)
        result = hl - rr_c

        if result < 0:
            result %= 65536
            f = 0x03 # ......NC
        else:
            f = 0x02 # ......N.
        if ((hl % 4096) - (rr_c % 4096)) & 0x1000:
            f += 0x10 # ...H....
        if result & 0x8000:
            f += 0x80 # S.......
        elif result == 0:
            f += 0x40 # .Z......
        if (hl ^ rr) & 0x8000 and (hl ^ result) & 0x8000:
            # Minuend and subtrahend signs are different - overflow if the
            # minuend's sign differs from the sign of the result
            f += 0x04 # .....P..

        h = result // 256
        registers[1] = f + (h & 0x28)
        registers[7] = result % 256
        registers[6] = h
        registers[15] = r_inc[registers[15]]
        registers[25] += 15
        registers[24] = (registers[24] + 2) % 65536

    def shift(self, registers, memory, timing, size, shift, cbit, reg, dest=-1):
        r = self.get_operand_value(registers, memory, size, reg)
        value = shift[r]
        self.set_operand_value(registers, memory, reg, value)
        if dest >= 0:
            registers[dest] = value
        if r & cbit:
            registers[1] = SZ53P[value] + 0x01
        else:
            registers[1] = SZ53P[value]
        registers[15] = R2[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def sub(self, registers, memory, r_inc, timing, size, reg):
        subtrahend = self.get_operand_value(registers, memory, size, reg)
        a = registers[0]
        registers[1] = SUB[a][subtrahend]
        registers[0] = (a - subtrahend) % 256
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def xor_n(self, registers, memory):
        pcn = registers[24] + 1
        a = registers[0] ^ memory[pcn % 65536]
        registers[0] = a
        registers[1] = SZ53P[a]
        registers[15] = R1[registers[15]]
        registers[25] += 7
        registers[24] = (pcn + 1) % 65536

    def xor_r(self, registers, r):
        a = registers[0] ^ registers[r]
        registers[0] = a
        registers[1] = SZ53P[a]
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def xor(self, registers, memory, r_inc, timing, size, reg):
        a = registers[0] ^ self.get_operand_value(registers, memory, size, reg)
        registers[0] = a
        registers[1] = SZ53P[a]
        registers[15] = r_inc[registers[15]]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def create_opcodes(self):
        r = self.registers
        m = self.memory

        self.after_DDCB = [
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1, B), # DDCB..00 RLC (IX+d),B
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1, C), # DDCB..01 RLC (IX+d),C
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1, D), # DDCB..02 RLC (IX+d),D
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1, E), # DDCB..03 RLC (IX+d),E
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1, H), # DDCB..04 RLC (IX+d),H
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1, L), # DDCB..05 RLC (IX+d),L
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1),    # DDCB..06 RLC (IX+d)
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1, A), # DDCB..07 RLC (IX+d),A
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1, B),   # DDCB..08 RRC (IX+d),B
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1, C),   # DDCB..09 RRC (IX+d),C
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1, D),   # DDCB..0A RRC (IX+d),D
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1, E),   # DDCB..0B RRC (IX+d),E
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1, H),   # DDCB..0C RRC (IX+d),H
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1, L),   # DDCB..0D RRC (IX+d),L
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1),      # DDCB..0E RRC (IX+d)
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1, A),   # DDCB..0F RRC (IX+d),A
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd, 0, B),  # DDCB..10 RL (IX+d),B
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd, 0, C),  # DDCB..11 RL (IX+d),C
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd, 0, D),  # DDCB..12 RL (IX+d),D
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd, 0, E),  # DDCB..13 RL (IX+d),E
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd, 0, H),  # DDCB..14 RL (IX+d),H
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd, 0, L),  # DDCB..15 RL (IX+d),L
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd),        # DDCB..16 RL (IX+d)
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd, 0, A),  # DDCB..17 RL (IX+d),A
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd, 0, B),    # DDCB..18 RR (IX+d),B
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd, 0, C),    # DDCB..19 RR (IX+d),C
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd, 0, D),    # DDCB..1A RR (IX+d),D
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd, 0, E),    # DDCB..1B RR (IX+d),E
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd, 0, H),    # DDCB..1C RR (IX+d),H
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd, 0, L),    # DDCB..1D RR (IX+d),L
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd),          # DDCB..1E RR (IX+d)
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd, 0, A),    # DDCB..1F RR (IX+d),A
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd, B),     # DDCB..20 SLA (IX+d),B
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd, C),     # DDCB..21 SLA (IX+d),C
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd, D),     # DDCB..22 SLA (IX+d),D
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd, E),     # DDCB..23 SLA (IX+d),E
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd, H),     # DDCB..24 SLA (IX+d),H
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd, L),     # DDCB..25 SLA (IX+d),L
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd),        # DDCB..26 SLA (IX+d)
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd, A),     # DDCB..27 SLA (IX+d),A
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd, B),       # DDCB..28 SRA (IX+d),B
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd, C),       # DDCB..29 SRA (IX+d),C
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd, D),       # DDCB..2A SRA (IX+d),D
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd, E),       # DDCB..2B SRA (IX+d),E
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd, H),       # DDCB..2C SRA (IX+d),H
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd, L),       # DDCB..2D SRA (IX+d),L
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd),          # DDCB..2E SRA (IX+d)
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd, A),       # DDCB..2F SRA (IX+d),A
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd, B),     # DDCB..30 SLL (IX+d),B
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd, C),     # DDCB..31 SLL (IX+d),C
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd, D),     # DDCB..32 SLL (IX+d),D
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd, E),     # DDCB..33 SLL (IX+d),E
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd, H),     # DDCB..34 SLL (IX+d),H
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd, L),     # DDCB..35 SLL (IX+d),L
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd),        # DDCB..36 SLL (IX+d)
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd, A),     # DDCB..37 SLL (IX+d),A
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd, B),       # DDCB..38 SRL (IX+d),B
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd, C),       # DDCB..39 SRL (IX+d),C
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd, D),       # DDCB..3A SRL (IX+d),D
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd, E),       # DDCB..3B SRL (IX+d),E
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd, H),       # DDCB..3C SRL (IX+d),H
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd, L),       # DDCB..3D SRL (IX+d),L
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd),          # DDCB..3E SRL (IX+d)
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd, A),       # DDCB..3F SRL (IX+d),A
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # DDCB..40 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # DDCB..41 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # DDCB..42 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # DDCB..43 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # DDCB..44 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # DDCB..45 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # DDCB..46 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # DDCB..47 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # DDCB..48 BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # DDCB..49 BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # DDCB..4A BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # DDCB..4B BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # DDCB..4C BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # DDCB..4D BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # DDCB..4E BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # DDCB..4F BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # DDCB..50 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # DDCB..51 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # DDCB..52 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # DDCB..53 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # DDCB..54 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # DDCB..55 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # DDCB..56 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # DDCB..57 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # DDCB..58 BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # DDCB..59 BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # DDCB..5A BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # DDCB..5B BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # DDCB..5C BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # DDCB..5D BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # DDCB..5E BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # DDCB..5F BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # DDCB..60 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # DDCB..61 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # DDCB..62 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # DDCB..63 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # DDCB..64 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # DDCB..65 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # DDCB..66 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # DDCB..67 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # DDCB..68 BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # DDCB..69 BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # DDCB..6A BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # DDCB..6B BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # DDCB..6C BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # DDCB..6D BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # DDCB..6E BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # DDCB..6F BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # DDCB..70 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # DDCB..71 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # DDCB..72 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # DDCB..73 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # DDCB..74 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # DDCB..75 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # DDCB..76 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # DDCB..77 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # DDCB..78 BIT 7,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # DDCB..79 BIT 7,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # DDCB..7A BIT 7,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # DDCB..7B BIT 7,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # DDCB..7C BIT 7,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # DDCB..7D BIT 7,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # DDCB..7E BIT 7,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # DDCB..7F BIT 7,(IX+d)
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0, B),     # DDCB..80 RES 0,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0, C),     # DDCB..81 RES 0,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0, D),     # DDCB..82 RES 0,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0, E),     # DDCB..83 RES 0,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0, H),     # DDCB..84 RES 0,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0, L),     # DDCB..85 RES 0,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0),        # DDCB..86 RES 0,(IX+d)
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0, A),     # DDCB..87 RES 0,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0, B),     # DDCB..88 RES 1,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0, C),     # DDCB..89 RES 1,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0, D),     # DDCB..8A RES 1,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0, E),     # DDCB..8B RES 1,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0, H),     # DDCB..8C RES 1,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0, L),     # DDCB..8D RES 1,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0),        # DDCB..8E RES 1,(IX+d)
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0, A),     # DDCB..8F RES 1,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0, B),     # DDCB..90 RES 2,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0, C),     # DDCB..91 RES 2,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0, D),     # DDCB..92 RES 2,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0, E),     # DDCB..93 RES 2,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0, H),     # DDCB..94 RES 2,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0, L),     # DDCB..95 RES 2,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0),        # DDCB..96 RES 2,(IX+d)
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0, A),     # DDCB..97 RES 2,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0, B),     # DDCB..98 RES 3,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0, C),     # DDCB..99 RES 3,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0, D),     # DDCB..9A RES 3,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0, E),     # DDCB..9B RES 3,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0, H),     # DDCB..9C RES 3,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0, L),     # DDCB..9D RES 3,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0),        # DDCB..9E RES 3,(IX+d)
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0, A),     # DDCB..9F RES 3,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0, B),     # DDCB..A0 RES 4,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0, C),     # DDCB..A1 RES 4,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0, D),     # DDCB..A2 RES 4,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0, E),     # DDCB..A3 RES 4,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0, H),     # DDCB..A4 RES 4,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0, L),     # DDCB..A5 RES 4,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0),        # DDCB..A6 RES 4,(IX+d)
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0, A),     # DDCB..A7 RES 4,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0, B),     # DDCB..A8 RES 5,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0, C),     # DDCB..A9 RES 5,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0, D),     # DDCB..AA RES 5,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0, E),     # DDCB..AB RES 5,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0, H),     # DDCB..AC RES 5,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0, L),     # DDCB..AD RES 5,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0),        # DDCB..AE RES 5,(IX+d)
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0, A),     # DDCB..AF RES 5,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0, B),     # DDCB..B0 RES 6,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0, C),     # DDCB..B1 RES 6,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0, D),     # DDCB..B2 RES 6,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0, E),     # DDCB..B3 RES 6,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0, H),     # DDCB..B4 RES 6,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0, L),     # DDCB..B5 RES 6,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0),        # DDCB..B6 RES 6,(IX+d)
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0, A),     # DDCB..B7 RES 6,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0, B),     # DDCB..B8 RES 7,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0, C),     # DDCB..B9 RES 7,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0, D),     # DDCB..BA RES 7,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0, E),     # DDCB..BB RES 7,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0, H),     # DDCB..BC RES 7,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0, L),     # DDCB..BD RES 7,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0),        # DDCB..BE RES 7,(IX+d)
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0, A),     # DDCB..BF RES 7,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1, B),       # DDCB..C0 SET 0,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1, C),       # DDCB..C1 SET 0,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1, D),       # DDCB..C2 SET 0,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1, E),       # DDCB..C3 SET 0,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1, H),       # DDCB..C4 SET 0,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1, L),       # DDCB..C5 SET 0,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1),          # DDCB..C6 SET 0,(IX+d)
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1, A),       # DDCB..C7 SET 0,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1, B),       # DDCB..C8 SET 1,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1, C),       # DDCB..C9 SET 1,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1, D),       # DDCB..CA SET 1,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1, E),       # DDCB..CB SET 1,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1, H),       # DDCB..CC SET 1,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1, L),       # DDCB..CD SET 1,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1),          # DDCB..CE SET 1,(IX+d)
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1, A),       # DDCB..CF SET 1,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1, B),       # DDCB..D0 SET 2,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1, C),       # DDCB..D1 SET 2,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1, D),       # DDCB..D2 SET 2,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1, E),       # DDCB..D3 SET 2,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1, H),       # DDCB..D4 SET 2,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1, L),       # DDCB..D5 SET 2,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1),          # DDCB..D6 SET 2,(IX+d)
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1, A),       # DDCB..D7 SET 2,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1, B),       # DDCB..D8 SET 3,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1, C),       # DDCB..D9 SET 3,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1, D),       # DDCB..DA SET 3,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1, E),       # DDCB..DB SET 3,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1, H),       # DDCB..DC SET 3,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1, L),       # DDCB..DD SET 3,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1),          # DDCB..DE SET 3,(IX+d)
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1, A),       # DDCB..DF SET 3,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1, B),      # DDCB..E0 SET 4,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1, C),      # DDCB..E1 SET 4,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1, D),      # DDCB..E2 SET 4,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1, E),      # DDCB..E3 SET 4,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1, H),      # DDCB..E4 SET 4,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1, L),      # DDCB..E5 SET 4,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1),         # DDCB..E6 SET 4,(IX+d)
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1, A),      # DDCB..E7 SET 4,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1, B),      # DDCB..E8 SET 5,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1, C),      # DDCB..E9 SET 5,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1, D),      # DDCB..EA SET 5,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1, E),      # DDCB..EB SET 5,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1, H),      # DDCB..EC SET 5,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1, L),      # DDCB..ED SET 5,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1),         # DDCB..EE SET 5,(IX+d)
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1, A),      # DDCB..EF SET 5,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1, B),      # DDCB..F0 SET 6,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1, C),      # DDCB..F1 SET 6,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1, D),      # DDCB..F2 SET 6,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1, E),      # DDCB..F3 SET 6,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1, H),      # DDCB..F4 SET 6,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1, L),      # DDCB..F5 SET 6,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1),         # DDCB..F6 SET 6,(IX+d)
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1, A),      # DDCB..F7 SET 6,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1, B),     # DDCB..F8 SET 7,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1, C),     # DDCB..F9 SET 7,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1, D),     # DDCB..FA SET 7,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1, E),     # DDCB..FB SET 7,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1, H),     # DDCB..FC SET 7,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1, L),     # DDCB..FD SET 7,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1),        # DDCB..FE SET 7,(IX+d)
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1, A),     # DDCB..FF SET 7,(IX+d),A
        ]

        self.after_FDCB = [
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1, B), # FDCB..00 RLC (IY+d),B
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1, C), # FDCB..01 RLC (IY+d),C
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1, D), # FDCB..02 RLC (IY+d),D
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1, E), # FDCB..03 RLC (IY+d),E
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1, H), # FDCB..04 RLC (IY+d),H
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1, L), # FDCB..05 RLC (IY+d),L
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1),    # FDCB..06 RLC (IY+d)
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1, A), # FDCB..07 RLC (IY+d),A
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1, B),   # FDCB..08 RRC (IY+d),B
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1, C),   # FDCB..09 RRC (IY+d),C
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1, D),   # FDCB..0A RRC (IY+d),D
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1, E),   # FDCB..0B RRC (IY+d),E
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1, H),   # FDCB..0C RRC (IY+d),H
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1, L),   # FDCB..0D RRC (IY+d),L
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1),      # FDCB..0E RRC (IY+d)
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1, A),   # FDCB..0F RRC (IY+d),A
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd, 0, B),  # FDCB..10 RL (IY+d),B
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd, 0, C),  # FDCB..11 RL (IY+d),C
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd, 0, D),  # FDCB..12 RL (IY+d),D
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd, 0, E),  # FDCB..13 RL (IY+d),E
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd, 0, H),  # FDCB..14 RL (IY+d),H
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd, 0, L),  # FDCB..15 RL (IY+d),L
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd),        # FDCB..16 RL (IY+d)
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd, 0, A),  # FDCB..17 RL (IY+d),A
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd, 0, B),    # FDCB..18 RR (IY+d),B
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd, 0, C),    # FDCB..19 RR (IY+d),C
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd, 0, D),    # FDCB..1A RR (IY+d),D
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd, 0, E),    # FDCB..1B RR (IY+d),E
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd, 0, H),    # FDCB..1C RR (IY+d),H
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd, 0, L),    # FDCB..1D RR (IY+d),L
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd),          # FDCB..1E RR (IY+d)
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd, 0, A),    # FDCB..1F RR (IY+d),A
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd, B),     # FDCB..20 SLA (IY+d),B
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd, C),     # FDCB..21 SLA (IY+d),C
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd, D),     # FDCB..22 SLA (IY+d),D
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd, E),     # FDCB..23 SLA (IY+d),E
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd, H),     # FDCB..24 SLA (IY+d),H
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd, L),     # FDCB..25 SLA (IY+d),L
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd),        # FDCB..26 SLA (IY+d)
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd, A),     # FDCB..27 SLA (IY+d),A
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd, B),       # FDCB..28 SRA (IY+d),B
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd, C),       # FDCB..29 SRA (IY+d),C
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd, D),       # FDCB..2A SRA (IY+d),D
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd, E),       # FDCB..2B SRA (IY+d),E
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd, H),       # FDCB..2C SRA (IY+d),H
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd, L),       # FDCB..2D SRA (IY+d),L
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd),          # FDCB..2E SRA (IY+d)
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd, A),       # FDCB..2F SRA (IY+d),A
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd, B),     # FDCB..30 SLL (IY+d),B
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd, C),     # FDCB..31 SLL (IY+d),C
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd, D),     # FDCB..32 SLL (IY+d),D
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd, E),     # FDCB..33 SLL (IY+d),E
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd, H),     # FDCB..34 SLL (IY+d),H
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd, L),     # FDCB..35 SLL (IY+d),L
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd),        # FDCB..36 SLL (IY+d)
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd, A),     # FDCB..37 SLL (IY+d),A
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd, B),       # FDCB..38 SRL (IY+d),B
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd, C),       # FDCB..39 SRL (IY+d),C
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd, D),       # FDCB..3A SRL (IY+d),D
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd, E),       # FDCB..3B SRL (IY+d),E
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd, H),       # FDCB..3C SRL (IY+d),H
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd, L),       # FDCB..3D SRL (IY+d),L
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd),          # FDCB..3E SRL (IY+d)
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd, A),       # FDCB..3F SRL (IY+d),A
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # FDCB..40 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # FDCB..41 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # FDCB..42 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # FDCB..43 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # FDCB..44 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # FDCB..45 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # FDCB..46 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # FDCB..47 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # FDCB..48 BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # FDCB..49 BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # FDCB..4A BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # FDCB..4B BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # FDCB..4C BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # FDCB..4D BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # FDCB..4E BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # FDCB..4F BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # FDCB..50 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # FDCB..51 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # FDCB..52 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # FDCB..53 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # FDCB..54 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # FDCB..55 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # FDCB..56 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # FDCB..57 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # FDCB..58 BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # FDCB..59 BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # FDCB..5A BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # FDCB..5B BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # FDCB..5C BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # FDCB..5D BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # FDCB..5E BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # FDCB..5F BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # FDCB..60 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # FDCB..61 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # FDCB..62 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # FDCB..63 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # FDCB..64 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # FDCB..65 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # FDCB..66 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # FDCB..67 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # FDCB..68 BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # FDCB..69 BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # FDCB..6A BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # FDCB..6B BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # FDCB..6C BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # FDCB..6D BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # FDCB..6E BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # FDCB..6F BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # FDCB..70 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # FDCB..71 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # FDCB..72 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # FDCB..73 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # FDCB..74 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # FDCB..75 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # FDCB..76 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # FDCB..77 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # FDCB..78 BIT 7,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # FDCB..79 BIT 7,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # FDCB..7A BIT 7,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # FDCB..7B BIT 7,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # FDCB..7C BIT 7,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # FDCB..7D BIT 7,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # FDCB..7E BIT 7,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # FDCB..7F BIT 7,(IY+d)
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0, B),     # FDCB..80 RES 0,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0, C),     # FDCB..81 RES 0,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0, D),     # FDCB..82 RES 0,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0, E),     # FDCB..83 RES 0,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0, H),     # FDCB..84 RES 0,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0, L),     # FDCB..85 RES 0,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0),        # FDCB..86 RES 0,(IY+d)
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0, A),     # FDCB..87 RES 0,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0, B),     # FDCB..88 RES 1,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0, C),     # FDCB..89 RES 1,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0, D),     # FDCB..8A RES 1,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0, E),     # FDCB..8B RES 1,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0, H),     # FDCB..8C RES 1,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0, L),     # FDCB..8D RES 1,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0),        # FDCB..8E RES 1,(IY+d)
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0, A),     # FDCB..8F RES 1,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0, B),     # FDCB..90 RES 2,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0, C),     # FDCB..91 RES 2,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0, D),     # FDCB..92 RES 2,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0, E),     # FDCB..93 RES 2,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0, H),     # FDCB..94 RES 2,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0, L),     # FDCB..95 RES 2,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0),        # FDCB..96 RES 2,(IY+d)
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0, A),     # FDCB..97 RES 2,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0, B),     # FDCB..98 RES 3,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0, C),     # FDCB..99 RES 3,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0, D),     # FDCB..9A RES 3,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0, E),     # FDCB..9B RES 3,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0, H),     # FDCB..9C RES 3,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0, L),     # FDCB..9D RES 3,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0),        # FDCB..9E RES 3,(IY+d)
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0, A),     # FDCB..9F RES 3,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0, B),     # FDCB..A0 RES 4,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0, C),     # FDCB..A1 RES 4,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0, D),     # FDCB..A2 RES 4,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0, E),     # FDCB..A3 RES 4,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0, H),     # FDCB..A4 RES 4,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0, L),     # FDCB..A5 RES 4,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0),        # FDCB..A6 RES 4,(IY+d)
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0, A),     # FDCB..A7 RES 4,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0, B),     # FDCB..A8 RES 5,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0, C),     # FDCB..A9 RES 5,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0, D),     # FDCB..AA RES 5,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0, E),     # FDCB..AB RES 5,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0, H),     # FDCB..AC RES 5,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0, L),     # FDCB..AD RES 5,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0),        # FDCB..AE RES 5,(IY+d)
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0, A),     # FDCB..AF RES 5,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0, B),     # FDCB..B0 RES 6,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0, C),     # FDCB..B1 RES 6,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0, D),     # FDCB..B2 RES 6,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0, E),     # FDCB..B3 RES 6,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0, H),     # FDCB..B4 RES 6,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0, L),     # FDCB..B5 RES 6,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0),        # FDCB..B6 RES 6,(IY+d)
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0, A),     # FDCB..B7 RES 6,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0, B),     # FDCB..B8 RES 7,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0, C),     # FDCB..B9 RES 7,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0, D),     # FDCB..BA RES 7,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0, E),     # FDCB..BB RES 7,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0, H),     # FDCB..BC RES 7,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0, L),     # FDCB..BD RES 7,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0),        # FDCB..BE RES 7,(IY+d)
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0, A),     # FDCB..BF RES 7,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1, B),       # FDCB..C0 SET 0,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1, C),       # FDCB..C1 SET 0,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1, D),       # FDCB..C2 SET 0,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1, E),       # FDCB..C3 SET 0,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1, H),       # FDCB..C4 SET 0,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1, L),       # FDCB..C5 SET 0,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1),          # FDCB..C6 SET 0,(IY+d)
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1, A),       # FDCB..C7 SET 0,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1, B),       # FDCB..C8 SET 1,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1, C),       # FDCB..C9 SET 1,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1, D),       # FDCB..CA SET 1,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1, E),       # FDCB..CB SET 1,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1, H),       # FDCB..CC SET 1,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1, L),       # FDCB..CD SET 1,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1),          # FDCB..CE SET 1,(IY+d)
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1, A),       # FDCB..CF SET 1,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1, B),       # FDCB..D0 SET 2,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1, C),       # FDCB..D1 SET 2,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1, D),       # FDCB..D2 SET 2,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1, E),       # FDCB..D3 SET 2,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1, H),       # FDCB..D4 SET 2,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1, L),       # FDCB..D5 SET 2,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1),          # FDCB..D6 SET 2,(IY+d)
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1, A),       # FDCB..D7 SET 2,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1, B),       # FDCB..D8 SET 3,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1, C),       # FDCB..D9 SET 3,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1, D),       # FDCB..DA SET 3,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1, E),       # FDCB..DB SET 3,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1, H),       # FDCB..DC SET 3,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1, L),       # FDCB..DD SET 3,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1),          # FDCB..DE SET 3,(IY+d)
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1, A),       # FDCB..DF SET 3,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1, B),      # FDCB..E0 SET 4,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1, C),      # FDCB..E1 SET 4,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1, D),      # FDCB..E2 SET 4,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1, E),      # FDCB..E3 SET 4,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1, H),      # FDCB..E4 SET 4,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1, L),      # FDCB..E5 SET 4,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1),         # FDCB..E6 SET 4,(IY+d)
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1, A),      # FDCB..E7 SET 4,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1, B),      # FDCB..E8 SET 5,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1, C),      # FDCB..E9 SET 5,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1, D),      # FDCB..EA SET 5,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1, E),      # FDCB..EB SET 5,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1, H),      # FDCB..EC SET 5,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1, L),      # FDCB..ED SET 5,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1),         # FDCB..EE SET 5,(IY+d)
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1, A),      # FDCB..EF SET 5,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1, B),      # FDCB..F0 SET 6,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1, C),      # FDCB..F1 SET 6,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1, D),      # FDCB..F2 SET 6,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1, E),      # FDCB..F3 SET 6,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1, H),      # FDCB..F4 SET 6,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1, L),      # FDCB..F5 SET 6,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1),         # FDCB..F6 SET 6,(IY+d)
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1, A),      # FDCB..F7 SET 6,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1, B),     # FDCB..F8 SET 7,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1, C),     # FDCB..F9 SET 7,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1, D),     # FDCB..FA SET 7,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1, E),     # FDCB..FB SET 7,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1, H),     # FDCB..FC SET 7,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1, L),     # FDCB..FD SET 7,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1),        # FDCB..FE SET 7,(IY+d)
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1, A),     # FDCB..FF SET 7,(IY+d),A
        ]

        self.after_CB = [
            partial(self.rotate_r, r, 128, RLC, B, 1),             # CB00 RLC B
            partial(self.rotate_r, r, 128, RLC, C, 1),             # CB01 RLC C
            partial(self.rotate_r, r, 128, RLC, D, 1),             # CB02 RLC D
            partial(self.rotate_r, r, 128, RLC, E, 1),             # CB03 RLC E
            partial(self.rotate_r, r, 128, RLC, H, 1),             # CB04 RLC H
            partial(self.rotate_r, r, 128, RLC, L, 1),             # CB05 RLC L
            partial(self.rotate, r, m, 15, 2, 128, RLC, Hd, 1),    # CB06 RLC (HL)
            partial(self.rotate_r, r, 128, RLC, A, 1),             # CB07 RLC A
            partial(self.rotate_r, r, 1, RRC, B, 1),               # CB08 RRC B
            partial(self.rotate_r, r, 1, RRC, C, 1),               # CB09 RRC C
            partial(self.rotate_r, r, 1, RRC, D, 1),               # CB0A RRC D
            partial(self.rotate_r, r, 1, RRC, E, 1),               # CB0B RRC E
            partial(self.rotate_r, r, 1, RRC, H, 1),               # CB0C RRC H
            partial(self.rotate_r, r, 1, RRC, L, 1),               # CB0D RRC L
            partial(self.rotate, r, m, 15, 2, 1, RRC, Hd, 1),      # CB0E RRC (HL)
            partial(self.rotate_r, r, 1, RRC, A, 1),               # CB0F RRC A
            partial(self.rotate_r, r, 128, RL, B),                 # CB10 RL B
            partial(self.rotate_r, r, 128, RL, C),                 # CB11 RL C
            partial(self.rotate_r, r, 128, RL, D),                 # CB12 RL D
            partial(self.rotate_r, r, 128, RL, E),                 # CB13 RL E
            partial(self.rotate_r, r, 128, RL, H),                 # CB14 RL H
            partial(self.rotate_r, r, 128, RL, L),                 # CB15 RL L
            partial(self.rotate, r, m, 15, 2, 128, RL, Hd),        # CB16 RL (HL)
            partial(self.rotate_r, r, 128, RL, A),                 # CB17 RL A
            partial(self.rotate_r, r, 1, RR, B),                   # CB18 RR B
            partial(self.rotate_r, r, 1, RR, C),                   # CB19 RR C
            partial(self.rotate_r, r, 1, RR, D),                   # CB1A RR D
            partial(self.rotate_r, r, 1, RR, E),                   # CB1B RR E
            partial(self.rotate_r, r, 1, RR, H),                   # CB1C RR H
            partial(self.rotate_r, r, 1, RR, L),                   # CB1D RR L
            partial(self.rotate, r, m, 15, 2, 1, RR, Hd),          # CB1E RR (HL)
            partial(self.rotate_r, r, 1, RR, A),                   # CB1F RR A
            partial(self.shift, r, m, 8, 2, SLA, 128, B),          # CB20 SLA B
            partial(self.shift, r, m, 8, 2, SLA, 128, C),          # CB21 SLA C
            partial(self.shift, r, m, 8, 2, SLA, 128, D),          # CB22 SLA D
            partial(self.shift, r, m, 8, 2, SLA, 128, E),          # CB23 SLA E
            partial(self.shift, r, m, 8, 2, SLA, 128, H),          # CB24 SLA H
            partial(self.shift, r, m, 8, 2, SLA, 128, L),          # CB25 SLA L
            partial(self.shift, r, m, 15, 2, SLA, 128, Hd),        # CB26 SLA (HL)
            partial(self.shift, r, m, 8, 2, SLA, 128, A),          # CB27 SLA A
            partial(self.shift, r, m, 8, 2, SRA, 1, B),            # CB28 SRA B
            partial(self.shift, r, m, 8, 2, SRA, 1, C),            # CB29 SRA C
            partial(self.shift, r, m, 8, 2, SRA, 1, D),            # CB2A SRA D
            partial(self.shift, r, m, 8, 2, SRA, 1, E),            # CB2B SRA E
            partial(self.shift, r, m, 8, 2, SRA, 1, H),            # CB2C SRA H
            partial(self.shift, r, m, 8, 2, SRA, 1, L),            # CB2D SRA L
            partial(self.shift, r, m, 15, 2, SRA, 1, Hd),          # CB2E SRA (HL)
            partial(self.shift, r, m, 8, 2, SRA, 1, A),            # CB2F SRA A
            partial(self.shift, r, m, 8, 2, SLL, 128, B),          # CB30 SLL B
            partial(self.shift, r, m, 8, 2, SLL, 128, C),          # CB31 SLL C
            partial(self.shift, r, m, 8, 2, SLL, 128, D),          # CB32 SLL D
            partial(self.shift, r, m, 8, 2, SLL, 128, E),          # CB33 SLL E
            partial(self.shift, r, m, 8, 2, SLL, 128, H),          # CB34 SLL H
            partial(self.shift, r, m, 8, 2, SLL, 128, L),          # CB35 SLL L
            partial(self.shift, r, m, 15, 2, SLL, 128, Hd),        # CB36 SLL (HL)
            partial(self.shift, r, m, 8, 2, SLL, 128, A),          # CB37 SLL A
            partial(self.shift, r, m, 8, 2, SRL, 1, B),            # CB38 SRL B
            partial(self.shift, r, m, 8, 2, SRL, 1, C),            # CB39 SRL C
            partial(self.shift, r, m, 8, 2, SRL, 1, D),            # CB3A SRL D
            partial(self.shift, r, m, 8, 2, SRL, 1, E),            # CB3B SRL E
            partial(self.shift, r, m, 8, 2, SRL, 1, H),            # CB3C SRL H
            partial(self.shift, r, m, 8, 2, SRL, 1, L),            # CB3D SRL L
            partial(self.shift, r, m, 15, 2, SRL, 1, Hd),          # CB3E SRL (HL)
            partial(self.shift, r, m, 8, 2, SRL, 1, A),            # CB3F SRL A
            partial(self.bit, r, m, 8, 2, 1, B),                   # CB40 BIT 0,B
            partial(self.bit, r, m, 8, 2, 1, C),                   # CB41 BIT 0,C
            partial(self.bit, r, m, 8, 2, 1, D),                   # CB42 BIT 0,D
            partial(self.bit, r, m, 8, 2, 1, E),                   # CB43 BIT 0,E
            partial(self.bit, r, m, 8, 2, 1, H),                   # CB44 BIT 0,H
            partial(self.bit, r, m, 8, 2, 1, L),                   # CB45 BIT 0,L
            partial(self.bit, r, m, 12, 2, 1, Hd),                 # CB46 BIT 0,(HL)
            partial(self.bit, r, m, 8, 2, 1, A),                   # CB47 BIT 0,A
            partial(self.bit, r, m, 8, 2, 2, B),                   # CB48 BIT 1,B
            partial(self.bit, r, m, 8, 2, 2, C),                   # CB49 BIT 1,C
            partial(self.bit, r, m, 8, 2, 2, D),                   # CB4A BIT 1,D
            partial(self.bit, r, m, 8, 2, 2, E),                   # CB4B BIT 1,E
            partial(self.bit, r, m, 8, 2, 2, H),                   # CB4C BIT 1,H
            partial(self.bit, r, m, 8, 2, 2, L),                   # CB4D BIT 1,L
            partial(self.bit, r, m, 12, 2, 2, Hd),                 # CB4E BIT 1,(HL)
            partial(self.bit, r, m, 8, 2, 2, A),                   # CB4F BIT 1,A
            partial(self.bit, r, m, 8, 2, 4, B),                   # CB50 BIT 2,B
            partial(self.bit, r, m, 8, 2, 4, C),                   # CB51 BIT 2,C
            partial(self.bit, r, m, 8, 2, 4, D),                   # CB52 BIT 2,D
            partial(self.bit, r, m, 8, 2, 4, E),                   # CB53 BIT 2,E
            partial(self.bit, r, m, 8, 2, 4, H),                   # CB54 BIT 2,H
            partial(self.bit, r, m, 8, 2, 4, L),                   # CB55 BIT 2,L
            partial(self.bit, r, m, 12, 2, 4, Hd),                 # CB56 BIT 2,(HL)
            partial(self.bit, r, m, 8, 2, 4, A),                   # CB57 BIT 2,A
            partial(self.bit, r, m, 8, 2, 8, B),                   # CB58 BIT 3,B
            partial(self.bit, r, m, 8, 2, 8, C),                   # CB59 BIT 3,C
            partial(self.bit, r, m, 8, 2, 8, D),                   # CB5A BIT 3,D
            partial(self.bit, r, m, 8, 2, 8, E),                   # CB5B BIT 3,E
            partial(self.bit, r, m, 8, 2, 8, H),                   # CB5C BIT 3,H
            partial(self.bit, r, m, 8, 2, 8, L),                   # CB5D BIT 3,L
            partial(self.bit, r, m, 12, 2, 8, Hd),                 # CB5E BIT 3,(HL)
            partial(self.bit, r, m, 8, 2, 8, A),                   # CB5F BIT 3,A
            partial(self.bit, r, m, 8, 2, 16, B),                  # CB60 BIT 4,B
            partial(self.bit, r, m, 8, 2, 16, C),                  # CB61 BIT 4,C
            partial(self.bit, r, m, 8, 2, 16, D),                  # CB62 BIT 4,D
            partial(self.bit, r, m, 8, 2, 16, E),                  # CB63 BIT 4,E
            partial(self.bit, r, m, 8, 2, 16, H),                  # CB64 BIT 4,H
            partial(self.bit, r, m, 8, 2, 16, L),                  # CB65 BIT 4,L
            partial(self.bit, r, m, 12, 2, 16, Hd),                # CB66 BIT 4,(HL)
            partial(self.bit, r, m, 8, 2, 16, A),                  # CB67 BIT 4,A
            partial(self.bit, r, m, 8, 2, 32, B),                  # CB68 BIT 5,B
            partial(self.bit, r, m, 8, 2, 32, C),                  # CB69 BIT 5,C
            partial(self.bit, r, m, 8, 2, 32, D),                  # CB6A BIT 5,D
            partial(self.bit, r, m, 8, 2, 32, E),                  # CB6B BIT 5,E
            partial(self.bit, r, m, 8, 2, 32, H),                  # CB6C BIT 5,H
            partial(self.bit, r, m, 8, 2, 32, L),                  # CB6D BIT 5,L
            partial(self.bit, r, m, 12, 2, 32, Hd),                # CB6E BIT 5,(HL)
            partial(self.bit, r, m, 8, 2, 32, A),                  # CB6F BIT 5,A
            partial(self.bit, r, m, 8, 2, 64, B),                  # CB70 BIT 6,B
            partial(self.bit, r, m, 8, 2, 64, C),                  # CB71 BIT 6,C
            partial(self.bit, r, m, 8, 2, 64, D),                  # CB72 BIT 6,D
            partial(self.bit, r, m, 8, 2, 64, E),                  # CB73 BIT 6,E
            partial(self.bit, r, m, 8, 2, 64, H),                  # CB74 BIT 6,H
            partial(self.bit, r, m, 8, 2, 64, L),                  # CB75 BIT 6,L
            partial(self.bit, r, m, 12, 2, 64, Hd),                # CB76 BIT 6,(HL)
            partial(self.bit, r, m, 8, 2, 64, A),                  # CB77 BIT 6,A
            partial(self.bit, r, m, 8, 2, 128, B),                 # CB78 BIT 7,B
            partial(self.bit, r, m, 8, 2, 128, C),                 # CB79 BIT 7,C
            partial(self.bit, r, m, 8, 2, 128, D),                 # CB7A BIT 7,D
            partial(self.bit, r, m, 8, 2, 128, E),                 # CB7B BIT 7,E
            partial(self.bit, r, m, 8, 2, 128, H),                 # CB7C BIT 7,H
            partial(self.bit, r, m, 8, 2, 128, L),                 # CB7D BIT 7,L
            partial(self.bit, r, m, 12, 2, 128, Hd),               # CB7E BIT 7,(HL)
            partial(self.bit, r, m, 8, 2, 128, A),                 # CB7F BIT 7,A
            partial(self.res_set, r, m, 8, 2, 254, B, 0),          # CB80 RES 0,B
            partial(self.res_set, r, m, 8, 2, 254, C, 0),          # CB81 RES 0,C
            partial(self.res_set, r, m, 8, 2, 254, D, 0),          # CB82 RES 0,D
            partial(self.res_set, r, m, 8, 2, 254, E, 0),          # CB83 RES 0,E
            partial(self.res_set, r, m, 8, 2, 254, H, 0),          # CB84 RES 0,H
            partial(self.res_set, r, m, 8, 2, 254, L, 0),          # CB85 RES 0,L
            partial(self.res_set, r, m, 15, 2, 254, Hd, 0),        # CB86 RES 0,(HL)
            partial(self.res_set, r, m, 8, 2, 254, A, 0),          # CB87 RES 0,A
            partial(self.res_set, r, m, 8, 2, 253, B, 0),          # CB88 RES 1,B
            partial(self.res_set, r, m, 8, 2, 253, C, 0),          # CB89 RES 1,C
            partial(self.res_set, r, m, 8, 2, 253, D, 0),          # CB8A RES 1,D
            partial(self.res_set, r, m, 8, 2, 253, E, 0),          # CB8B RES 1,E
            partial(self.res_set, r, m, 8, 2, 253, H, 0),          # CB8C RES 1,H
            partial(self.res_set, r, m, 8, 2, 253, L, 0),          # CB8D RES 1,L
            partial(self.res_set, r, m, 15, 2, 253, Hd, 0),        # CB8E RES 1,(HL)
            partial(self.res_set, r, m, 8, 2, 253, A, 0),          # CB8F RES 1,A
            partial(self.res_set, r, m, 8, 2, 251, B, 0),          # CB90 RES 2,B
            partial(self.res_set, r, m, 8, 2, 251, C, 0),          # CB91 RES 2,C
            partial(self.res_set, r, m, 8, 2, 251, D, 0),          # CB92 RES 2,D
            partial(self.res_set, r, m, 8, 2, 251, E, 0),          # CB93 RES 2,E
            partial(self.res_set, r, m, 8, 2, 251, H, 0),          # CB94 RES 2,H
            partial(self.res_set, r, m, 8, 2, 251, L, 0),          # CB95 RES 2,L
            partial(self.res_set, r, m, 15, 2, 251, Hd, 0),        # CB96 RES 2,(HL)
            partial(self.res_set, r, m, 8, 2, 251, A, 0),          # CB97 RES 2,A
            partial(self.res_set, r, m, 8, 2, 247, B, 0),          # CB98 RES 3,B
            partial(self.res_set, r, m, 8, 2, 247, C, 0),          # CB99 RES 3,C
            partial(self.res_set, r, m, 8, 2, 247, D, 0),          # CB9A RES 3,D
            partial(self.res_set, r, m, 8, 2, 247, E, 0),          # CB9B RES 3,E
            partial(self.res_set, r, m, 8, 2, 247, H, 0),          # CB9C RES 3,H
            partial(self.res_set, r, m, 8, 2, 247, L, 0),          # CB9D RES 3,L
            partial(self.res_set, r, m, 15, 2, 247, Hd, 0),        # CB9E RES 3,(HL)
            partial(self.res_set, r, m, 8, 2, 247, A, 0),          # CB9F RES 3,A
            partial(self.res_set, r, m, 8, 2, 239, B, 0),          # CBA0 RES 4,B
            partial(self.res_set, r, m, 8, 2, 239, C, 0),          # CBA1 RES 4,C
            partial(self.res_set, r, m, 8, 2, 239, D, 0),          # CBA2 RES 4,D
            partial(self.res_set, r, m, 8, 2, 239, E, 0),          # CBA3 RES 4,E
            partial(self.res_set, r, m, 8, 2, 239, H, 0),          # CBA4 RES 4,H
            partial(self.res_set, r, m, 8, 2, 239, L, 0),          # CBA5 RES 4,L
            partial(self.res_set, r, m, 15, 2, 239, Hd, 0),        # CBA6 RES 4,(HL)
            partial(self.res_set, r, m, 8, 2, 239, A, 0),          # CBA7 RES 4,A
            partial(self.res_set, r, m, 8, 2, 223, B, 0),          # CBA8 RES 5,B
            partial(self.res_set, r, m, 8, 2, 223, C, 0),          # CBA9 RES 5,C
            partial(self.res_set, r, m, 8, 2, 223, D, 0),          # CBAA RES 5,D
            partial(self.res_set, r, m, 8, 2, 223, E, 0),          # CBAB RES 5,E
            partial(self.res_set, r, m, 8, 2, 223, H, 0),          # CBAC RES 5,H
            partial(self.res_set, r, m, 8, 2, 223, L, 0),          # CBAD RES 5,L
            partial(self.res_set, r, m, 15, 2, 223, Hd, 0),        # CBAE RES 5,(HL)
            partial(self.res_set, r, m, 8, 2, 223, A, 0),          # CBAF RES 5,A
            partial(self.res_set, r, m, 8, 2, 191, B, 0),          # CBB0 RES 6,B
            partial(self.res_set, r, m, 8, 2, 191, C, 0),          # CBB1 RES 6,C
            partial(self.res_set, r, m, 8, 2, 191, D, 0),          # CBB2 RES 6,D
            partial(self.res_set, r, m, 8, 2, 191, E, 0),          # CBB3 RES 6,E
            partial(self.res_set, r, m, 8, 2, 191, H, 0),          # CBB4 RES 6,H
            partial(self.res_set, r, m, 8, 2, 191, L, 0),          # CBB5 RES 6,L
            partial(self.res_set, r, m, 15, 2, 191, Hd, 0),        # CBB6 RES 6,(HL)
            partial(self.res_set, r, m, 8, 2, 191, A, 0),          # CBB7 RES 6,A
            partial(self.res_set, r, m, 8, 2, 127, B, 0),          # CBB8 RES 7,B
            partial(self.res_set, r, m, 8, 2, 127, C, 0),          # CBB9 RES 7,C
            partial(self.res_set, r, m, 8, 2, 127, D, 0),          # CBBA RES 7,D
            partial(self.res_set, r, m, 8, 2, 127, E, 0),          # CBBB RES 7,E
            partial(self.res_set, r, m, 8, 2, 127, H, 0),          # CBBC RES 7,H
            partial(self.res_set, r, m, 8, 2, 127, L, 0),          # CBBD RES 7,L
            partial(self.res_set, r, m, 15, 2, 127, Hd, 0),        # CBBE RES 7,(HL)
            partial(self.res_set, r, m, 8, 2, 127, A, 0),          # CBBF RES 7,A
            partial(self.res_set, r, m, 8, 2, 1, B, 1),            # CBC0 SET 0,B
            partial(self.res_set, r, m, 8, 2, 1, C, 1),            # CBC1 SET 0,C
            partial(self.res_set, r, m, 8, 2, 1, D, 1),            # CBC2 SET 0,D
            partial(self.res_set, r, m, 8, 2, 1, E, 1),            # CBC3 SET 0,E
            partial(self.res_set, r, m, 8, 2, 1, H, 1),            # CBC4 SET 0,H
            partial(self.res_set, r, m, 8, 2, 1, L, 1),            # CBC5 SET 0,L
            partial(self.res_set, r, m, 15, 2, 1, Hd, 1),          # CBC6 SET 0,(HL)
            partial(self.res_set, r, m, 8, 2, 1, A, 1),            # CBC7 SET 0,A
            partial(self.res_set, r, m, 8, 2, 2, B, 1),            # CBC8 SET 1,B
            partial(self.res_set, r, m, 8, 2, 2, C, 1),            # CBC9 SET 1,C
            partial(self.res_set, r, m, 8, 2, 2, D, 1),            # CBCA SET 1,D
            partial(self.res_set, r, m, 8, 2, 2, E, 1),            # CBCB SET 1,E
            partial(self.res_set, r, m, 8, 2, 2, H, 1),            # CBCC SET 1,H
            partial(self.res_set, r, m, 8, 2, 2, L, 1),            # CBCD SET 1,L
            partial(self.res_set, r, m, 15, 2, 2, Hd, 1),          # CBCE SET 1,(HL)
            partial(self.res_set, r, m, 8, 2, 2, A, 1),            # CBCF SET 1,A
            partial(self.res_set, r, m, 8, 2, 4, B, 1),            # CBD0 SET 2,B
            partial(self.res_set, r, m, 8, 2, 4, C, 1),            # CBD1 SET 2,C
            partial(self.res_set, r, m, 8, 2, 4, D, 1),            # CBD2 SET 2,D
            partial(self.res_set, r, m, 8, 2, 4, E, 1),            # CBD3 SET 2,E
            partial(self.res_set, r, m, 8, 2, 4, H, 1),            # CBD4 SET 2,H
            partial(self.res_set, r, m, 8, 2, 4, L, 1),            # CBD5 SET 2,L
            partial(self.res_set, r, m, 15, 2, 4, Hd, 1),          # CBD6 SET 2,(HL)
            partial(self.res_set, r, m, 8, 2, 4, A, 1),            # CBD7 SET 2,A
            partial(self.res_set, r, m, 8, 2, 8, B, 1),            # CBD8 SET 3,B
            partial(self.res_set, r, m, 8, 2, 8, C, 1),            # CBD9 SET 3,C
            partial(self.res_set, r, m, 8, 2, 8, D, 1),            # CBDA SET 3,D
            partial(self.res_set, r, m, 8, 2, 8, E, 1),            # CBDB SET 3,E
            partial(self.res_set, r, m, 8, 2, 8, H, 1),            # CBDC SET 3,H
            partial(self.res_set, r, m, 8, 2, 8, L, 1),            # CBDD SET 3,L
            partial(self.res_set, r, m, 15, 2, 8, Hd, 1),          # CBDE SET 3,(HL)
            partial(self.res_set, r, m, 8, 2, 8, A, 1),            # CBDF SET 3,A
            partial(self.res_set, r, m, 8, 2, 16, B, 1),           # CBE0 SET 4,B
            partial(self.res_set, r, m, 8, 2, 16, C, 1),           # CBE1 SET 4,C
            partial(self.res_set, r, m, 8, 2, 16, D, 1),           # CBE2 SET 4,D
            partial(self.res_set, r, m, 8, 2, 16, E, 1),           # CBE3 SET 4,E
            partial(self.res_set, r, m, 8, 2, 16, H, 1),           # CBE4 SET 4,H
            partial(self.res_set, r, m, 8, 2, 16, L, 1),           # CBE5 SET 4,L
            partial(self.res_set, r, m, 15, 2, 16, Hd, 1),         # CBE6 SET 4,(HL)
            partial(self.res_set, r, m, 8, 2, 16, A, 1),           # CBE7 SET 4,A
            partial(self.res_set, r, m, 8, 2, 32, B, 1),           # CBE8 SET 5,B
            partial(self.res_set, r, m, 8, 2, 32, C, 1),           # CBE9 SET 5,C
            partial(self.res_set, r, m, 8, 2, 32, D, 1),           # CBEA SET 5,D
            partial(self.res_set, r, m, 8, 2, 32, E, 1),           # CBEB SET 5,E
            partial(self.res_set, r, m, 8, 2, 32, H, 1),           # CBEC SET 5,H
            partial(self.res_set, r, m, 8, 2, 32, L, 1),           # CBED SET 5,L
            partial(self.res_set, r, m, 15, 2, 32, Hd, 1),         # CBEE SET 5,(HL)
            partial(self.res_set, r, m, 8, 2, 32, A, 1),           # CBEF SET 5,A
            partial(self.res_set, r, m, 8, 2, 64, B, 1),           # CBF0 SET 6,B
            partial(self.res_set, r, m, 8, 2, 64, C, 1),           # CBF1 SET 6,C
            partial(self.res_set, r, m, 8, 2, 64, D, 1),           # CBF2 SET 6,D
            partial(self.res_set, r, m, 8, 2, 64, E, 1),           # CBF3 SET 6,E
            partial(self.res_set, r, m, 8, 2, 64, H, 1),           # CBF4 SET 6,H
            partial(self.res_set, r, m, 8, 2, 64, L, 1),           # CBF5 SET 6,L
            partial(self.res_set, r, m, 15, 2, 64, Hd, 1),         # CBF6 SET 6,(HL)
            partial(self.res_set, r, m, 8, 2, 64, A, 1),           # CBF7 SET 6,A
            partial(self.res_set, r, m, 8, 2, 128, B, 1),          # CBF8 SET 7,B
            partial(self.res_set, r, m, 8, 2, 128, C, 1),          # CBF9 SET 7,C
            partial(self.res_set, r, m, 8, 2, 128, D, 1),          # CBFA SET 7,D
            partial(self.res_set, r, m, 8, 2, 128, E, 1),          # CBFB SET 7,E
            partial(self.res_set, r, m, 8, 2, 128, H, 1),          # CBFC SET 7,H
            partial(self.res_set, r, m, 8, 2, 128, L, 1),          # CBFD SET 7,L
            partial(self.res_set, r, m, 15, 2, 128, Hd, 1),        # CBFE SET 7,(HL)
            partial(self.res_set, r, m, 8, 2, 128, A, 1),          # CBFF SET 7,A
        ]

        self.after_DD = [
            partial(self.nop_dd_fd, r),                            # DD00
            partial(self.nop_dd_fd, r),                            # DD01
            partial(self.nop_dd_fd, r),                            # DD02
            partial(self.nop_dd_fd, r),                            # DD03
            partial(self.nop_dd_fd, r),                            # DD04
            partial(self.nop_dd_fd, r),                            # DD05
            partial(self.nop_dd_fd, r),                            # DD06
            partial(self.nop_dd_fd, r),                            # DD07
            partial(self.nop_dd_fd, r),                            # DD08
            partial(self.add16, r, R2, 15, 2, IXh, B),             # DD09 ADD IX,BC
            partial(self.nop_dd_fd, r),                            # DD0A
            partial(self.nop_dd_fd, r),                            # DD0B
            partial(self.nop_dd_fd, r),                            # DD0C
            partial(self.nop_dd_fd, r),                            # DD0D
            partial(self.nop_dd_fd, r),                            # DD0E
            partial(self.nop_dd_fd, r),                            # DD0F
            partial(self.nop_dd_fd, r),                            # DD10
            partial(self.nop_dd_fd, r),                            # DD11
            partial(self.nop_dd_fd, r),                            # DD12
            partial(self.nop_dd_fd, r),                            # DD13
            partial(self.nop_dd_fd, r),                            # DD14
            partial(self.nop_dd_fd, r),                            # DD15
            partial(self.nop_dd_fd, r),                            # DD16
            partial(self.nop_dd_fd, r),                            # DD17
            partial(self.nop_dd_fd, r),                            # DD18
            partial(self.add16, r, R2, 15, 2, IXh, D),             # DD19 ADD IX,DE
            partial(self.nop_dd_fd, r),                            # DD1A
            partial(self.nop_dd_fd, r),                            # DD1B
            partial(self.nop_dd_fd, r),                            # DD1C
            partial(self.nop_dd_fd, r),                            # DD1D
            partial(self.nop_dd_fd, r),                            # DD1E
            partial(self.nop_dd_fd, r),                            # DD1F
            partial(self.nop_dd_fd, r),                            # DD20
            partial(self.ld16, r, m, R2, 14, 4, IXh),              # DD21 LD IX,nn
            partial(self.ld16addr, r, m, R2, 20, 4, IXh, 1),       # DD22 LD (nn),IX
            partial(self.inc_dec16, r, R2, 10, 2, 1, IXh),         # DD23 INC IX
            partial(self.inc_dec8, r, m, R2, 8, 2, 1, INC, IXh),   # DD24 INC IXh
            partial(self.inc_dec8, r, m, R2, 8, 2, -1, DEC, IXh),  # DD25 DEC IXh
            partial(self.ld8, r, m, R2, 11, 3, IXh, N),            # DD26 LD IXh,n
            partial(self.nop_dd_fd, r),                            # DD27
            partial(self.nop_dd_fd, r),                            # DD28
            partial(self.add16, r, R2, 15, 2, IXh, IXh),           # DD29 ADD IX,IX
            partial(self.ld16addr, r, m, R2, 20, 4, IXh, 0),       # DD2A LD IX,(nn)
            partial(self.inc_dec16, r, R2, 10, 2, -1, IXh),        # DD2B DEC IX
            partial(self.inc_dec8, r, m, R2, 8, 2, 1, INC, IXl),   # DD2C INC IXl
            partial(self.inc_dec8, r, m, R2, 8, 2, -1, DEC, IXl),  # DD2D DEC IXl
            partial(self.ld8, r, m, R2, 11, 3, IXl, N),            # DD2E LD IXl,n
            partial(self.nop_dd_fd, r),                            # DD2F
            partial(self.nop_dd_fd, r),                            # DD30
            partial(self.nop_dd_fd, r),                            # DD31
            partial(self.nop_dd_fd, r),                            # DD32
            partial(self.nop_dd_fd, r),                            # DD33
            partial(self.inc_dec8, r, m, R2, 23, 3, 1, INC, Xd),   # DD34 INC (IX+d)
            partial(self.inc_dec8, r, m, R2, 23, 3, -1, DEC, Xd),  # DD35 DEC (IX+d)
            partial(self.ld8, r, m, R2, 19, 4, Xd, N),             # DD36 LD (IX+d),n
            partial(self.nop_dd_fd, r),                            # DD37
            partial(self.nop_dd_fd, r),                            # DD38
            partial(self.add16, r, R2, 15, 2, IXh, SP),            # DD39 ADD IX,SP
            partial(self.nop_dd_fd, r),                            # DD3A
            partial(self.nop_dd_fd, r),                            # DD3B
            partial(self.nop_dd_fd, r),                            # DD3C
            partial(self.nop_dd_fd, r),                            # DD3D
            partial(self.nop_dd_fd, r),                            # DD3E
            partial(self.nop_dd_fd, r),                            # DD3F
            partial(self.nop_dd_fd, r),                            # DD40
            partial(self.nop_dd_fd, r),                            # DD41
            partial(self.nop_dd_fd, r),                            # DD42
            partial(self.nop_dd_fd, r),                            # DD43
            partial(self.ld8, r, m, R2, 8, 2, B, IXh),             # DD44 LD B,IXh
            partial(self.ld8, r, m, R2, 8, 2, B, IXl),             # DD45 LD B,IXl
            partial(self.ld8, r, m, R2, 19, 3, B, Xd),             # DD46 LD B,(IX+d)
            partial(self.nop_dd_fd, r),                            # DD47
            partial(self.nop_dd_fd, r),                            # DD48
            partial(self.nop_dd_fd, r),                            # DD49
            partial(self.nop_dd_fd, r),                            # DD4A
            partial(self.nop_dd_fd, r),                            # DD4B
            partial(self.ld8, r, m, R2, 8, 2, C, IXh),             # DD4C LD C,IXh
            partial(self.ld8, r, m, R2, 8, 2, C, IXl),             # DD4D LD C,IXl
            partial(self.ld8, r, m, R2, 19, 3, C, Xd),             # DD4E LD C,(IX+d)
            partial(self.nop_dd_fd, r),                            # DD4F
            partial(self.nop_dd_fd, r),                            # DD50
            partial(self.nop_dd_fd, r),                            # DD51
            partial(self.nop_dd_fd, r),                            # DD52
            partial(self.nop_dd_fd, r),                            # DD53
            partial(self.ld8, r, m, R2, 8, 2, D, IXh),             # DD54 LD D,IXh
            partial(self.ld8, r, m, R2, 8, 2, D, IXl),             # DD55 LD D,IXl
            partial(self.ld8, r, m, R2, 19, 3, D, Xd),             # DD56 LD D,(IX+d)
            partial(self.nop_dd_fd, r),                            # DD57
            partial(self.nop_dd_fd, r),                            # DD58
            partial(self.nop_dd_fd, r),                            # DD59
            partial(self.nop_dd_fd, r),                            # DD5A
            partial(self.nop_dd_fd, r),                            # DD5B
            partial(self.ld8, r, m, R2, 8, 2, E, IXh),             # DD5C LD E,IXh
            partial(self.ld8, r, m, R2, 8, 2, E, IXl),             # DD5D LD E,IXl
            partial(self.ld8, r, m, R2, 19, 3, E, Xd),             # DD5E LD E,(IX+d)
            partial(self.nop_dd_fd, r),                            # DD5F
            partial(self.ld8, r, m, R2, 8, 2, IXh, B),             # DD60 LD IXh,B
            partial(self.ld8, r, m, R2, 8, 2, IXh, C),             # DD61 LD IXh,C
            partial(self.ld8, r, m, R2, 8, 2, IXh, D),             # DD62 LD IXh,D
            partial(self.ld8, r, m, R2, 8, 2, IXh, E),             # DD63 LD IXh,E
            partial(self.ld8, r, m, R2, 8, 2, IXh, IXh),           # DD64 LD IXh,IXh
            partial(self.ld8, r, m, R2, 8, 2, IXh, IXl),           # DD65 LD IXh,IXl
            partial(self.ld8, r, m, R2, 19, 3, H, Xd),             # DD66 LD H,(IX+d)
            partial(self.ld8, r, m, R2, 8, 2, IXh, A),             # DD67 LD IXh,A
            partial(self.ld8, r, m, R2, 8, 2, IXl, B),             # DD68 LD IXl,B
            partial(self.ld8, r, m, R2, 8, 2, IXl, C),             # DD69 LD IXl,C
            partial(self.ld8, r, m, R2, 8, 2, IXl, D),             # DD6A LD IXl,D
            partial(self.ld8, r, m, R2, 8, 2, IXl, E),             # DD6B LD IXl,E
            partial(self.ld8, r, m, R2, 8, 2, IXl, IXh),           # DD6C LD IXl,IXh
            partial(self.ld8, r, m, R2, 8, 2, IXl, IXl),           # DD6D LD IXl,IXl
            partial(self.ld8, r, m, R2, 19, 3, L, Xd),             # DD6E LD L,(IX+d)
            partial(self.ld8, r, m, R2, 8, 2, IXl, A),             # DD6F LD IXl,A
            partial(self.ld8, r, m, R2, 19, 3, Xd, B),             # DD70 LD (IX+d),B
            partial(self.ld8, r, m, R2, 19, 3, Xd, C),             # DD71 LD (IX+d),C
            partial(self.ld8, r, m, R2, 19, 3, Xd, D),             # DD72 LD (IX+d),D
            partial(self.ld8, r, m, R2, 19, 3, Xd, E),             # DD73 LD (IX+d),E
            partial(self.ld8, r, m, R2, 19, 3, Xd, H),             # DD74 LD (IX+d),H
            partial(self.ld8, r, m, R2, 19, 3, Xd, L),             # DD75 LD (IX+d),L
            partial(self.nop_dd_fd, r),                            # DD76
            partial(self.ld8, r, m, R2, 19, 3, Xd, A),             # DD77 LD (IX+d),A
            partial(self.nop_dd_fd, r),                            # DD78
            partial(self.nop_dd_fd, r),                            # DD79
            partial(self.nop_dd_fd, r),                            # DD7A
            partial(self.nop_dd_fd, r),                            # DD7B
            partial(self.ld8, r, m, R2, 8, 2, A, IXh),             # DD7C LD A,IXh
            partial(self.ld8, r, m, R2, 8, 2, A, IXl),             # DD7D LD A,IXl
            partial(self.ld8, r, m, R2, 19, 3, A, Xd),             # DD7E LD A,(IX+d)
            partial(self.nop_dd_fd, r),                            # DD7F
            partial(self.nop_dd_fd, r),                            # DD80
            partial(self.nop_dd_fd, r),                            # DD81
            partial(self.nop_dd_fd, r),                            # DD82
            partial(self.nop_dd_fd, r),                            # DD83
            partial(self.add_a, r, m, R2, 8, 2, IXh),              # DD84 ADD A,IXh
            partial(self.add_a, r, m, R2, 8, 2, IXl),              # DD85 ADD A,IXl
            partial(self.add_a, r, m, R2, 19, 3, Xd),              # DD86 ADD A,(IX+d)
            partial(self.nop_dd_fd, r),                            # DD87
            partial(self.nop_dd_fd, r),                            # DD88
            partial(self.nop_dd_fd, r),                            # DD89
            partial(self.nop_dd_fd, r),                            # DD8A
            partial(self.nop_dd_fd, r),                            # DD8B
            partial(self.adc_a, r, m, R2, 8, 2, IXh),              # DD8C ADC A,IXh
            partial(self.adc_a, r, m, R2, 8, 2, IXl),              # DD8D ADC A,IXl
            partial(self.adc_a, r, m, R2, 19, 3, Xd),              # DD8E ADC A,(IX+d)
            partial(self.nop_dd_fd, r),                            # DD8F
            partial(self.nop_dd_fd, r),                            # DD90
            partial(self.nop_dd_fd, r),                            # DD91
            partial(self.nop_dd_fd, r),                            # DD92
            partial(self.nop_dd_fd, r),                            # DD93
            partial(self.sub, r, m, R2, 8, 2, IXh),                # DD94 SUB IXh
            partial(self.sub, r, m, R2, 8, 2, IXl),                # DD95 SUB IXl
            partial(self.sub, r, m, R2, 19, 3, Xd),                # DD96 SUB (IX+d)
            partial(self.nop_dd_fd, r),                            # DD97
            partial(self.nop_dd_fd, r),                            # DD98
            partial(self.nop_dd_fd, r),                            # DD99
            partial(self.nop_dd_fd, r),                            # DD9A
            partial(self.nop_dd_fd, r),                            # DD9B
            partial(self.sbc_a, r, m, R2, 8, 2, IXh),              # DD9C SBC A,IXh
            partial(self.sbc_a, r, m, R2, 8, 2, IXl),              # DD9D SBC A,IXl
            partial(self.sbc_a, r, m, R2, 19, 3, Xd),              # DD9E SBC A,(IX+d)
            partial(self.nop_dd_fd, r),                            # DD9F
            partial(self.nop_dd_fd, r),                            # DDA0
            partial(self.nop_dd_fd, r),                            # DDA1
            partial(self.nop_dd_fd, r),                            # DDA2
            partial(self.nop_dd_fd, r),                            # DDA3
            partial(self.anda, r, m, R2, 8, 2, IXh),               # DDA4 AND IXh
            partial(self.anda, r, m, R2, 8, 2, IXl),               # DDA5 AND IXl
            partial(self.anda, r, m, R2, 19, 3, Xd),               # DDA6 AND (IX+d)
            partial(self.nop_dd_fd, r),                            # DDA7
            partial(self.nop_dd_fd, r),                            # DDA8
            partial(self.nop_dd_fd, r),                            # DDA9
            partial(self.nop_dd_fd, r),                            # DDAA
            partial(self.nop_dd_fd, r),                            # DDAB
            partial(self.xor, r, m, R2, 8, 2, IXh),                # DDAC XOR IXh
            partial(self.xor, r, m, R2, 8, 2, IXl),                # DDAD XOR IXl
            partial(self.xor, r, m, R2, 19, 3, Xd),                # DDAE XOR (IX+d)
            partial(self.nop_dd_fd, r),                            # DDAF
            partial(self.nop_dd_fd, r),                            # DDB0
            partial(self.nop_dd_fd, r),                            # DDB1
            partial(self.nop_dd_fd, r),                            # DDB2
            partial(self.nop_dd_fd, r),                            # DDB3
            partial(self.ora, r, m, R2, 8, 2, IXh),                # DDB4 OR IXh
            partial(self.ora, r, m, R2, 8, 2, IXl),                # DDB5 OR IXl
            partial(self.ora, r, m, R2, 19, 3, Xd),                # DDB6 OR (IX+d)
            partial(self.nop_dd_fd, r),                            # DDB7
            partial(self.nop_dd_fd, r),                            # DDB8
            partial(self.nop_dd_fd, r),                            # DDB9
            partial(self.nop_dd_fd, r),                            # DDBA
            partial(self.nop_dd_fd, r),                            # DDBB
            partial(self.cp, r, m, R2, 8, 2, IXh),                 # DDBC CP IXh
            partial(self.cp, r, m, R2, 8, 2, IXl),                 # DDBD CP IXl
            partial(self.cp, r, m, R2, 19, 3, Xd),                 # DDBE CP (IX+d)
            partial(self.nop_dd_fd, r),                            # DDBF
            partial(self.nop_dd_fd, r),                            # DDC0
            partial(self.nop_dd_fd, r),                            # DDC1
            partial(self.nop_dd_fd, r),                            # DDC2
            partial(self.nop_dd_fd, r),                            # DDC3
            partial(self.nop_dd_fd, r),                            # DDC4
            partial(self.nop_dd_fd, r),                            # DDC5
            partial(self.nop_dd_fd, r),                            # DDC6
            partial(self.nop_dd_fd, r),                            # DDC7
            partial(self.nop_dd_fd, r),                            # DDC8
            partial(self.nop_dd_fd, r),                            # DDC9
            partial(self.nop_dd_fd, r),                            # DDCA
            partial(self.prefix2, self.after_DDCB, r, m),          # DDCB prefix
            partial(self.nop_dd_fd, r),                            # DDCC
            partial(self.nop_dd_fd, r),                            # DDCD
            partial(self.nop_dd_fd, r),                            # DDCE
            partial(self.nop_dd_fd, r),                            # DDCF
            partial(self.nop_dd_fd, r),                            # DDD0
            partial(self.nop_dd_fd, r),                            # DDD1
            partial(self.nop_dd_fd, r),                            # DDD2
            partial(self.nop_dd_fd, r),                            # DDD3
            partial(self.nop_dd_fd, r),                            # DDD4
            partial(self.nop_dd_fd, r),                            # DDD5
            partial(self.nop_dd_fd, r),                            # DDD6
            partial(self.nop_dd_fd, r),                            # DDD7
            partial(self.nop_dd_fd, r),                            # DDD8
            partial(self.nop_dd_fd, r),                            # DDD9
            partial(self.nop_dd_fd, r),                            # DDDA
            partial(self.nop_dd_fd, r),                            # DDDB
            partial(self.nop_dd_fd, r),                            # DDDC
            partial(self.nop_dd_fd, r),                            # DDDD
            partial(self.nop_dd_fd, r),                            # DDDE
            partial(self.nop_dd_fd, r),                            # DDDF
            partial(self.nop_dd_fd, r),                            # DDE0
            partial(self.pop, r, m, R2, 14, 2, IXh),               # DDE1 POP IX
            partial(self.nop_dd_fd, r),                            # DDE2
            partial(self.ex_sp, r, m, IXh),                        # DDE3 EX (SP),IX
            partial(self.nop_dd_fd, r),                            # DDE4
            partial(self.push, r, m, R2, 15, 2, IXh),              # DDE5 PUSH IX
            partial(self.nop_dd_fd, r),                            # DDE6
            partial(self.nop_dd_fd, r),                            # DDE7
            partial(self.nop_dd_fd, r),                            # DDE8
            partial(self.jp, r, m, R2, 8, 0, IXh),                 # DDE9 JP (IX)
            partial(self.nop_dd_fd, r),                            # DDEA
            partial(self.nop_dd_fd, r),                            # DDEB
            partial(self.nop_dd_fd, r),                            # DDEC
            partial(self.nop_dd_fd, r),                            # DDED
            partial(self.nop_dd_fd, r),                            # DDEE
            partial(self.nop_dd_fd, r),                            # DDEF
            partial(self.nop_dd_fd, r),                            # DDF0
            partial(self.nop_dd_fd, r),                            # DDF1
            partial(self.nop_dd_fd, r),                            # DDF2
            partial(self.nop_dd_fd, r),                            # DDF3
            partial(self.nop_dd_fd, r),                            # DDF4
            partial(self.nop_dd_fd, r),                            # DDF5
            partial(self.nop_dd_fd, r),                            # DDF6
            partial(self.nop_dd_fd, r),                            # DDF7
            partial(self.nop_dd_fd, r),                            # DDF8
            partial(self.ldsprr, r, R2, 10, 2, IXh),               # DDF9 LD SP,IX
            partial(self.nop_dd_fd, r),                            # DDFA
            partial(self.nop_dd_fd, r),                            # DDFB
            partial(self.nop_dd_fd, r),                            # DDFC
            partial(self.nop_dd_fd, r),                            # DDFD
            partial(self.nop_dd_fd, r),                            # DDFE
            partial(self.nop_dd_fd, r),                            # DDFF
        ]

        self.after_ED = [
            partial(self.nop_ed, r),                               # ED00
            partial(self.nop_ed, r),                               # ED01
            partial(self.nop_ed, r),                               # ED02
            partial(self.nop_ed, r),                               # ED03
            partial(self.nop_ed, r),                               # ED04
            partial(self.nop_ed, r),                               # ED05
            partial(self.nop_ed, r),                               # ED06
            partial(self.nop_ed, r),                               # ED07
            partial(self.nop_ed, r),                               # ED08
            partial(self.nop_ed, r),                               # ED09
            partial(self.nop_ed, r),                               # ED0A
            partial(self.nop_ed, r),                               # ED0B
            partial(self.nop_ed, r),                               # ED0C
            partial(self.nop_ed, r),                               # ED0D
            partial(self.nop_ed, r),                               # ED0E
            partial(self.nop_ed, r),                               # ED0F
            partial(self.nop_ed, r),                               # ED10
            partial(self.nop_ed, r),                               # ED11
            partial(self.nop_ed, r),                               # ED12
            partial(self.nop_ed, r),                               # ED13
            partial(self.nop_ed, r),                               # ED14
            partial(self.nop_ed, r),                               # ED15
            partial(self.nop_ed, r),                               # ED16
            partial(self.nop_ed, r),                               # ED17
            partial(self.nop_ed, r),                               # ED18
            partial(self.nop_ed, r),                               # ED19
            partial(self.nop_ed, r),                               # ED1A
            partial(self.nop_ed, r),                               # ED1B
            partial(self.nop_ed, r),                               # ED1C
            partial(self.nop_ed, r),                               # ED1D
            partial(self.nop_ed, r),                               # ED1E
            partial(self.nop_ed, r),                               # ED1F
            partial(self.nop_ed, r),                               # ED20
            partial(self.nop_ed, r),                               # ED21
            partial(self.nop_ed, r),                               # ED22
            partial(self.nop_ed, r),                               # ED23
            partial(self.nop_ed, r),                               # ED24
            partial(self.nop_ed, r),                               # ED25
            partial(self.nop_ed, r),                               # ED26
            partial(self.nop_ed, r),                               # ED27
            partial(self.nop_ed, r),                               # ED28
            partial(self.nop_ed, r),                               # ED29
            partial(self.nop_ed, r),                               # ED2A
            partial(self.nop_ed, r),                               # ED2B
            partial(self.nop_ed, r),                               # ED2C
            partial(self.nop_ed, r),                               # ED2D
            partial(self.nop_ed, r),                               # ED2E
            partial(self.nop_ed, r),                               # ED2F
            partial(self.nop_ed, r),                               # ED30
            partial(self.nop_ed, r),                               # ED31
            partial(self.nop_ed, r),                               # ED32
            partial(self.nop_ed, r),                               # ED33
            partial(self.nop_ed, r),                               # ED34
            partial(self.nop_ed, r),                               # ED35
            partial(self.nop_ed, r),                               # ED36
            partial(self.nop_ed, r),                               # ED37
            partial(self.nop_ed, r),                               # ED38
            partial(self.nop_ed, r),                               # ED39
            partial(self.nop_ed, r),                               # ED3A
            partial(self.nop_ed, r),                               # ED3B
            partial(self.nop_ed, r),                               # ED3C
            partial(self.nop_ed, r),                               # ED3D
            partial(self.nop_ed, r),                               # ED3E
            partial(self.nop_ed, r),                               # ED3F
            partial(self.in_c, r, B),                              # ED40 IN B,(C)
            partial(self.outc, r, B),                              # ED41 OUT (C),B
            partial(self.sbc_hl, r, R2, B),                        # ED42 SBC HL,BC
            partial(self.ld16addr, r, m, R2, 20, 4, B, 1),         # ED43 LD (nn),BC
            partial(self.neg, r),                                  # ED44 NEG
            partial(self.reti, r, m),                              # ED45 RETN
            partial(self.im, r, 0),                                # ED46 IM 0
            partial(self.ld8, r, m, R2, 9, 2, I, A),               # ED47 LD I,A
            partial(self.in_c, r, C),                              # ED48 IN C,(C)
            partial(self.outc, r, C),                              # ED49 OUT (C),C
            partial(self.adc_hl, r, B),                            # ED4A ADC HL,BC
            partial(self.ld16addr, r, m, R2, 20, 4, B, 0),         # ED4B LD BC,(nn)
            partial(self.neg, r),                                  # ED4C NEG
            partial(self.reti, r, m),                              # ED4D RETI
            partial(self.im, r, 0),                                # ED4E IM 0
            partial(self.ld8, r, m, R2, 9, 2, R, A),               # ED4F LD R,A
            partial(self.in_c, r, D),                              # ED50 IN D,(C)
            partial(self.outc, r, D),                              # ED51 OUT (C),D
            partial(self.sbc_hl, r, R2, D),                        # ED52 SBC HL,DE
            partial(self.ld16addr, r, m, R2, 20, 4, D, 1),         # ED53 LD (nn),DE
            partial(self.neg, r),                                  # ED54 NEG
            partial(self.reti, r, m),                              # ED55 RETN
            partial(self.im, r, 1),                                # ED56 IM 1
            partial(self.ld8, r, m, R2, 9, 2, A, I),               # ED57 LD A,I
            partial(self.in_c, r, E),                              # ED58 IN E,(C)
            partial(self.outc, r, E),                              # ED59 OUT (C),E
            partial(self.adc_hl, r, D),                            # ED5A ADC HL,DE
            partial(self.ld16addr, r, m, R2, 20, 4, D, 0),         # ED5B LD DE,(nn)
            partial(self.neg, r),                                  # ED5C NEG
            partial(self.reti, r, m),                              # ED5D RETN
            partial(self.im, r, 2),                                # ED5E IM 2
            partial(self.ld8, r, m, R2, 9, 2, A, R),               # ED5F LD A,R
            partial(self.in_c, r, H),                              # ED60 IN H,(C)
            partial(self.outc, r, H),                              # ED61 OUT (C),H
            partial(self.sbc_hl, r, R2, H),                        # ED62 SBC HL,HL
            partial(self.ld16addr, r, m, R2, 20, 4, H, 1),         # ED63 LD (nn),HL
            partial(self.neg, r),                                  # ED64 NEG
            partial(self.reti, r, m),                              # ED65 RETN
            partial(self.im, r, 0),                                # ED66 IM 0
            partial(self.rrd, r, m),                               # ED67 RRD
            partial(self.in_c, r, L),                              # ED68 IN L,(C)
            partial(self.outc, r, L),                              # ED69 OUT (C),L
            partial(self.adc_hl, r, H),                            # ED6A ADC HL,HL
            partial(self.ld16addr, r, m, R2, 20, 4, H, 0),         # ED6B LD HL,(nn)
            partial(self.neg, r),                                  # ED6C NEG
            partial(self.reti, r, m),                              # ED6D RETN
            partial(self.im, r, 0),                                # ED6E IM 0
            partial(self.rld, r, m),                               # ED6F RLD
            partial(self.in_c, r, F),                              # ED70 IN F,(C)
            partial(self.outc, r, -1),                             # ED71 OUT (C),0
            partial(self.sbc_hl, r, R2, SP),                       # ED72 SBC HL,SP
            partial(self.ld16addr, r, m, R2, 20, 4, SP, 1),        # ED73 LD (nn),SP
            partial(self.neg, r),                                  # ED74 NEG
            partial(self.reti, r, m),                              # ED75 RETN
            partial(self.im, r, 1),                                # ED76 IM 1
            partial(self.nop_ed, r),                               # ED77
            partial(self.in_c, r, A),                              # ED78 IN A,(C)
            partial(self.outc, r, A),                              # ED79 OUT (C),A
            partial(self.adc_hl, r, SP),                           # ED7A ADC HL,SP
            partial(self.ld16addr, r, m, R2, 20, 4, SP, 0),        # ED7B LD SP,(nn)
            partial(self.neg, r),                                  # ED7C NEG
            partial(self.reti, r, m),                              # ED7D RETN
            partial(self.im, r, 2),                                # ED7E IM 2
            partial(self.nop_ed, r),                               # ED7F
            partial(self.nop_ed, r),                               # ED80
            partial(self.nop_ed, r),                               # ED81
            partial(self.nop_ed, r),                               # ED82
            partial(self.nop_ed, r),                               # ED83
            partial(self.nop_ed, r),                               # ED84
            partial(self.nop_ed, r),                               # ED85
            partial(self.nop_ed, r),                               # ED86
            partial(self.nop_ed, r),                               # ED87
            partial(self.nop_ed, r),                               # ED88
            partial(self.nop_ed, r),                               # ED89
            partial(self.nop_ed, r),                               # ED8A
            partial(self.nop_ed, r),                               # ED8B
            partial(self.nop_ed, r),                               # ED8C
            partial(self.nop_ed, r),                               # ED8D
            partial(self.nop_ed, r),                               # ED8E
            partial(self.nop_ed, r),                               # ED8F
            partial(self.nop_ed, r),                               # ED90
            partial(self.nop_ed, r),                               # ED91
            partial(self.nop_ed, r),                               # ED92
            partial(self.nop_ed, r),                               # ED93
            partial(self.nop_ed, r),                               # ED94
            partial(self.nop_ed, r),                               # ED95
            partial(self.nop_ed, r),                               # ED96
            partial(self.nop_ed, r),                               # ED97
            partial(self.nop_ed, r),                               # ED98
            partial(self.nop_ed, r),                               # ED99
            partial(self.nop_ed, r),                               # ED9A
            partial(self.nop_ed, r),                               # ED9B
            partial(self.nop_ed, r),                               # ED9C
            partial(self.nop_ed, r),                               # ED9D
            partial(self.nop_ed, r),                               # ED9E
            partial(self.nop_ed, r),                               # ED9F
            partial(self.ldi, r, m, 1, 0),                         # EDA0 LDI
            partial(self.cpi, r, m, 1, 0),                         # EDA1 CPI
            partial(self.ini, r, m, 1, 0),                         # EDA2 INI
            partial(self.outi, r, m, 1, 0),                        # EDA3 OUTI
            partial(self.nop_ed, r),                               # EDA4
            partial(self.nop_ed, r),                               # EDA5
            partial(self.nop_ed, r),                               # EDA6
            partial(self.nop_ed, r),                               # EDA7
            partial(self.ldi, r, m, -1, 0),                        # EDA8 LDD
            partial(self.cpi, r, m, -1, 0),                        # EDA9 CPD
            partial(self.ini, r, m, -1, 0),                        # EDAA IND
            partial(self.outi, r, m, -1, 0),                       # EDAB OUTD
            partial(self.nop_ed, r),                               # EDAC
            partial(self.nop_ed, r),                               # EDAD
            partial(self.nop_ed, r),                               # EDAE
            partial(self.nop_ed, r),                               # EDAF
            partial(self.ldi, r, m, 1, 1),                         # EDB0 LDIR
            partial(self.cpi, r, m, 1, 1),                         # EDB1 CPIR
            partial(self.ini, r, m, 1, 1),                         # EDB2 INIR
            partial(self.outi, r, m, 1, 1),                        # EDB3 OTIR
            partial(self.nop_ed, r),                               # EDB4
            partial(self.nop_ed, r),                               # EDB5
            partial(self.nop_ed, r),                               # EDB6
            partial(self.nop_ed, r),                               # EDB7
            partial(self.ldi, r, m, -1, 1),                        # EDB8 LDDR
            partial(self.cpi, r, m, -1, 1),                        # EDB9 CPDR
            partial(self.ini, r, m, -1, 1),                        # EDBA INDR
            partial(self.outi, r, m, -1, 1),                       # EDBB OTDR
            partial(self.nop_ed, r),                               # EDBC
            partial(self.nop_ed, r),                               # EDBD
            partial(self.nop_ed, r),                               # EDBE
            partial(self.nop_ed, r),                               # EDBF
            partial(self.nop_ed, r),                               # EDC0
            partial(self.nop_ed, r),                               # EDC1
            partial(self.nop_ed, r),                               # EDC2
            partial(self.nop_ed, r),                               # EDC3
            partial(self.nop_ed, r),                               # EDC4
            partial(self.nop_ed, r),                               # EDC5
            partial(self.nop_ed, r),                               # EDC6
            partial(self.nop_ed, r),                               # EDC7
            partial(self.nop_ed, r),                               # EDC8
            partial(self.nop_ed, r),                               # EDC9
            partial(self.nop_ed, r),                               # EDCA
            partial(self.nop_ed, r),                               # EDCB
            partial(self.nop_ed, r),                               # EDCC
            partial(self.nop_ed, r),                               # EDCD
            partial(self.nop_ed, r),                               # EDCE
            partial(self.nop_ed, r),                               # EDCF
            partial(self.nop_ed, r),                               # EDD0
            partial(self.nop_ed, r),                               # EDD1
            partial(self.nop_ed, r),                               # EDD2
            partial(self.nop_ed, r),                               # EDD3
            partial(self.nop_ed, r),                               # EDD4
            partial(self.nop_ed, r),                               # EDD5
            partial(self.nop_ed, r),                               # EDD6
            partial(self.nop_ed, r),                               # EDD7
            partial(self.nop_ed, r),                               # EDD8
            partial(self.nop_ed, r),                               # EDD9
            partial(self.nop_ed, r),                               # EDDA
            partial(self.nop_ed, r),                               # EDDB
            partial(self.nop_ed, r),                               # EDDC
            partial(self.nop_ed, r),                               # EDDD
            partial(self.nop_ed, r),                               # EDDE
            partial(self.nop_ed, r),                               # EDDF
            partial(self.nop_ed, r),                               # EDE0
            partial(self.nop_ed, r),                               # EDE1
            partial(self.nop_ed, r),                               # EDE2
            partial(self.nop_ed, r),                               # EDE3
            partial(self.nop_ed, r),                               # EDE4
            partial(self.nop_ed, r),                               # EDE5
            partial(self.nop_ed, r),                               # EDE6
            partial(self.nop_ed, r),                               # EDE7
            partial(self.nop_ed, r),                               # EDE8
            partial(self.nop_ed, r),                               # EDE9
            partial(self.nop_ed, r),                               # EDEA
            partial(self.nop_ed, r),                               # EDEB
            partial(self.nop_ed, r),                               # EDEC
            partial(self.nop_ed, r),                               # EDED
            partial(self.nop_ed, r),                               # EDEE
            partial(self.nop_ed, r),                               # EDEF
            partial(self.nop_ed, r),                               # EDF0
            partial(self.nop_ed, r),                               # EDF1
            partial(self.nop_ed, r),                               # EDF2
            partial(self.nop_ed, r),                               # EDF3
            partial(self.nop_ed, r),                               # EDF4
            partial(self.nop_ed, r),                               # EDF5
            partial(self.nop_ed, r),                               # EDF6
            partial(self.nop_ed, r),                               # EDF7
            partial(self.nop_ed, r),                               # EDF8
            partial(self.nop_ed, r),                               # EDF9
            partial(self.nop_ed, r),                               # EDFA
            partial(self.nop_ed, r),                               # EDFB
            partial(self.nop_ed, r),                               # EDFC
            partial(self.nop_ed, r),                               # EDFD
            partial(self.nop_ed, r),                               # EDFE
            partial(self.nop_ed, r),                               # EDFF
        ]

        self.after_FD = [
            partial(self.nop_dd_fd, r),                            # FD00
            partial(self.nop_dd_fd, r),                            # FD01
            partial(self.nop_dd_fd, r),                            # FD02
            partial(self.nop_dd_fd, r),                            # FD03
            partial(self.nop_dd_fd, r),                            # FD04
            partial(self.nop_dd_fd, r),                            # FD05
            partial(self.nop_dd_fd, r),                            # FD06
            partial(self.nop_dd_fd, r),                            # FD07
            partial(self.nop_dd_fd, r),                            # FD08
            partial(self.add16, r, R2, 15, 2, IYh, B),             # FD09 ADD IY,BC
            partial(self.nop_dd_fd, r),                            # FD0A
            partial(self.nop_dd_fd, r),                            # FD0B
            partial(self.nop_dd_fd, r),                            # FD0C
            partial(self.nop_dd_fd, r),                            # FD0D
            partial(self.nop_dd_fd, r),                            # FD0E
            partial(self.nop_dd_fd, r),                            # FD0F
            partial(self.nop_dd_fd, r),                            # FD10
            partial(self.nop_dd_fd, r),                            # FD11
            partial(self.nop_dd_fd, r),                            # FD12
            partial(self.nop_dd_fd, r),                            # FD13
            partial(self.nop_dd_fd, r),                            # FD14
            partial(self.nop_dd_fd, r),                            # FD15
            partial(self.nop_dd_fd, r),                            # FD16
            partial(self.nop_dd_fd, r),                            # FD17
            partial(self.nop_dd_fd, r),                            # FD18
            partial(self.add16, r, R2, 15, 2, IYh, D),             # FD19 ADD IY,DE
            partial(self.nop_dd_fd, r),                            # FD1A
            partial(self.nop_dd_fd, r),                            # FD1B
            partial(self.nop_dd_fd, r),                            # FD1C
            partial(self.nop_dd_fd, r),                            # FD1D
            partial(self.nop_dd_fd, r),                            # FD1E
            partial(self.nop_dd_fd, r),                            # FD1F
            partial(self.nop_dd_fd, r),                            # FD20
            partial(self.ld16, r, m, R2, 14, 4, IYh),              # FD21 LD IY,nn
            partial(self.ld16addr, r, m, R2, 20, 4, IYh, 1),       # FD22 LD (nn),IY
            partial(self.inc_dec16, r, R2, 10, 2, 1, IYh),         # FD23 INC IY
            partial(self.inc_dec8, r, m, R2, 8, 2, 1, INC, IYh),   # FD24 INC IYh
            partial(self.inc_dec8, r, m, R2, 8, 2, -1, DEC, IYh),  # FD25 DEC IYh
            partial(self.ld8, r, m, R2, 11, 3, IYh, N),            # FD26 LD IYh,n
            partial(self.nop_dd_fd, r),                            # FD27
            partial(self.nop_dd_fd, r),                            # FD28
            partial(self.add16, r, R2, 15, 2, IYh, IYh),           # FD29 ADD IY,IY
            partial(self.ld16addr, r, m, R2, 20, 4, IYh, 0),       # FD2A LD IY,(nn)
            partial(self.inc_dec16, r, R2, 10, 2, -1, IYh),        # FD2B DEC IY
            partial(self.inc_dec8, r, m, R2, 8, 2, 1, INC, IYl),   # FD2C INC IYl
            partial(self.inc_dec8, r, m, R2, 8, 2, -1, DEC, IYl),  # FD2D DEC IYl
            partial(self.ld8, r, m, R2, 11, 3, IYl, N),            # FD2E LD IYl,n
            partial(self.nop_dd_fd, r),                            # FD2F
            partial(self.nop_dd_fd, r),                            # FD30
            partial(self.nop_dd_fd, r),                            # FD31
            partial(self.nop_dd_fd, r),                            # FD32
            partial(self.nop_dd_fd, r),                            # FD33
            partial(self.inc_dec8, r, m, R2, 23, 3, 1, INC, Yd),   # FD34 INC (IY+d)
            partial(self.inc_dec8, r, m, R2, 23, 3, -1, DEC, Yd),  # FD35 DEC (IY+d)
            partial(self.ld8, r, m, R2, 19, 4, Yd, N),             # FD36 LD (IY+d),n
            partial(self.nop_dd_fd, r),                            # FD37
            partial(self.nop_dd_fd, r),                            # FD38
            partial(self.add16, r, R2, 15, 2, IYh, SP),            # FD39 ADD IY,SP
            partial(self.nop_dd_fd, r),                            # FD3A
            partial(self.nop_dd_fd, r),                            # FD3B
            partial(self.nop_dd_fd, r),                            # FD3C
            partial(self.nop_dd_fd, r),                            # FD3D
            partial(self.nop_dd_fd, r),                            # FD3E
            partial(self.nop_dd_fd, r),                            # FD3F
            partial(self.nop_dd_fd, r),                            # FD40
            partial(self.nop_dd_fd, r),                            # FD41
            partial(self.nop_dd_fd, r),                            # FD42
            partial(self.nop_dd_fd, r),                            # FD43
            partial(self.ld8, r, m, R2, 8, 2, B, IYh),             # FD44 LD B,IYh
            partial(self.ld8, r, m, R2, 8, 2, B, IYl),             # FD45 LD B,IYl
            partial(self.ld8, r, m, R2, 19, 3, B, Yd),             # FD46 LD B,(IY+d)
            partial(self.nop_dd_fd, r),                            # FD47
            partial(self.nop_dd_fd, r),                            # FD48
            partial(self.nop_dd_fd, r),                            # FD49
            partial(self.nop_dd_fd, r),                            # FD4A
            partial(self.nop_dd_fd, r),                            # FD4B
            partial(self.ld8, r, m, R2, 8, 2, C, IYh),             # FD4C LD C,IYh
            partial(self.ld8, r, m, R2, 8, 2, C, IYl),             # FD4D LD C,IYl
            partial(self.ld8, r, m, R2, 19, 3, C, Yd),             # FD4E LD C,(IY+d)
            partial(self.nop_dd_fd, r),                            # FD4F
            partial(self.nop_dd_fd, r),                            # FD50
            partial(self.nop_dd_fd, r),                            # FD51
            partial(self.nop_dd_fd, r),                            # FD52
            partial(self.nop_dd_fd, r),                            # FD53
            partial(self.ld8, r, m, R2, 8, 2, D, IYh),             # FD54 LD D,IYh
            partial(self.ld8, r, m, R2, 8, 2, D, IYl),             # FD55 LD D,IYl
            partial(self.ld8, r, m, R2, 19, 3, D, Yd),             # FD56 LD D,(IY+d)
            partial(self.nop_dd_fd, r),                            # FD57
            partial(self.nop_dd_fd, r),                            # FD58
            partial(self.nop_dd_fd, r),                            # FD59
            partial(self.nop_dd_fd, r),                            # FD5A
            partial(self.nop_dd_fd, r),                            # FD5B
            partial(self.ld8, r, m, R2, 8, 2, E, IYh),             # FD5C LD E,IYh
            partial(self.ld8, r, m, R2, 8, 2, E, IYl),             # FD5D LD E,IYl
            partial(self.ld8, r, m, R2, 19, 3, E, Yd),             # FD5E LD E,(IY+d)
            partial(self.nop_dd_fd, r),                            # FD5F
            partial(self.ld8, r, m, R2, 8, 2, IYh, B),             # FD60 LD IYh,B
            partial(self.ld8, r, m, R2, 8, 2, IYh, C),             # FD61 LD IYh,C
            partial(self.ld8, r, m, R2, 8, 2, IYh, D),             # FD62 LD IYh,D
            partial(self.ld8, r, m, R2, 8, 2, IYh, E),             # FD63 LD IYh,E
            partial(self.ld8, r, m, R2, 8, 2, IYh, IYh),           # FD64 LD IYh,IYh
            partial(self.ld8, r, m, R2, 8, 2, IYh, IYl),           # FD65 LD IYh,IYl
            partial(self.ld8, r, m, R2, 19, 3, H, Yd),             # FD66 LD H,(IY+d)
            partial(self.ld8, r, m, R2, 8, 2, IYh, A),             # FD67 LD IYh,A
            partial(self.ld8, r, m, R2, 8, 2, IYl, B),             # FD68 LD IYl,B
            partial(self.ld8, r, m, R2, 8, 2, IYl, C),             # FD69 LD IYl,C
            partial(self.ld8, r, m, R2, 8, 2, IYl, D),             # FD6A LD IYl,D
            partial(self.ld8, r, m, R2, 8, 2, IYl, E),             # FD6B LD IYl,E
            partial(self.ld8, r, m, R2, 8, 2, IYl, IYh),           # FD6C LD IYl,IYh
            partial(self.ld8, r, m, R2, 8, 2, IYl, IYl),           # FD6D LD IYl,IYl
            partial(self.ld8, r, m, R2, 19, 3, L, Yd),             # FD6E LD L,(IY+d)
            partial(self.ld8, r, m, R2, 8, 2, IYl, A),             # FD6F LD IYl,A
            partial(self.ld8, r, m, R2, 19, 3, Yd, B),             # FD70 LD (IY+d),B
            partial(self.ld8, r, m, R2, 19, 3, Yd, C),             # FD71 LD (IY+d),C
            partial(self.ld8, r, m, R2, 19, 3, Yd, D),             # FD72 LD (IY+d),D
            partial(self.ld8, r, m, R2, 19, 3, Yd, E),             # FD73 LD (IY+d),E
            partial(self.ld8, r, m, R2, 19, 3, Yd, H),             # FD74 LD (IY+d),H
            partial(self.ld8, r, m, R2, 19, 3, Yd, L),             # FD75 LD (IY+d),L
            partial(self.nop_dd_fd, r),                            # FD76
            partial(self.ld8, r, m, R2, 19, 3, Yd, A),             # FD77 LD (IY+d),A
            partial(self.nop_dd_fd, r),                            # FD78
            partial(self.nop_dd_fd, r),                            # FD79
            partial(self.nop_dd_fd, r),                            # FD7A
            partial(self.nop_dd_fd, r),                            # FD7B
            partial(self.ld8, r, m, R2, 8, 2, A, IYh),             # FD7C LD A,IYh
            partial(self.ld8, r, m, R2, 8, 2, A, IYl),             # FD7D LD A,IYl
            partial(self.ld8, r, m, R2, 19, 3, A, Yd),             # FD7E LD A,(IY+d)
            partial(self.nop_dd_fd, r),                            # FD7F
            partial(self.nop_dd_fd, r),                            # FD80
            partial(self.nop_dd_fd, r),                            # FD81
            partial(self.nop_dd_fd, r),                            # FD82
            partial(self.nop_dd_fd, r),                            # FD83
            partial(self.add_a, r, m, R2, 8, 2, IYh),              # FD84 ADD A,IYh
            partial(self.add_a, r, m, R2, 8, 2, IYl),              # FD85 ADD A,IYl
            partial(self.add_a, r, m, R2, 19, 3, Yd),              # FD86 ADD A,(IY+d)
            partial(self.nop_dd_fd, r),                            # FD87
            partial(self.nop_dd_fd, r),                            # FD88
            partial(self.nop_dd_fd, r),                            # FD89
            partial(self.nop_dd_fd, r),                            # FD8A
            partial(self.nop_dd_fd, r),                            # FD8B
            partial(self.adc_a, r, m, R2, 8, 2, IYh),              # FD8C ADC A,IYh
            partial(self.adc_a, r, m, R2, 8, 2, IYl),              # FD8D ADC A,IYl
            partial(self.adc_a, r, m, R2, 19, 3, Yd),              # FD8E ADC A,(IY+d)
            partial(self.nop_dd_fd, r),                            # FD8F
            partial(self.nop_dd_fd, r),                            # FD90
            partial(self.nop_dd_fd, r),                            # FD91
            partial(self.nop_dd_fd, r),                            # FD92
            partial(self.nop_dd_fd, r),                            # FD93
            partial(self.sub, r, m, R2, 8, 2, IYh),                # FD94 SUB IYh
            partial(self.sub, r, m, R2, 8, 2, IYl),                # FD95 SUB IYl
            partial(self.sub, r, m, R2, 19, 3, Yd),                # FD96 SUB (IY+d)
            partial(self.nop_dd_fd, r),                            # FD97
            partial(self.nop_dd_fd, r),                            # FD98
            partial(self.nop_dd_fd, r),                            # FD99
            partial(self.nop_dd_fd, r),                            # FD9A
            partial(self.nop_dd_fd, r),                            # FD9B
            partial(self.sbc_a, r, m, R2, 8, 2, IYh),              # FD9C SBC A,IYh
            partial(self.sbc_a, r, m, R2, 8, 2, IYl),              # FD9D SBC A,IYl
            partial(self.sbc_a, r, m, R2, 19, 3, Yd),              # FD9E SBC A,(IY+d)
            partial(self.nop_dd_fd, r),                            # FD9F
            partial(self.nop_dd_fd, r),                            # FDA0
            partial(self.nop_dd_fd, r),                            # FDA1
            partial(self.nop_dd_fd, r),                            # FDA2
            partial(self.nop_dd_fd, r),                            # FDA3
            partial(self.anda, r, m, R2, 8, 2, IYh),               # FDA4 AND IYh
            partial(self.anda, r, m, R2, 8, 2, IYl),               # FDA5 AND IYl
            partial(self.anda, r, m, R2, 19, 3, Yd),               # FDA6 AND (IY+d)
            partial(self.nop_dd_fd, r),                            # FDA7
            partial(self.nop_dd_fd, r),                            # FDA8
            partial(self.nop_dd_fd, r),                            # FDA9
            partial(self.nop_dd_fd, r),                            # FDAA
            partial(self.nop_dd_fd, r),                            # FDAB
            partial(self.xor, r, m, R2, 8, 2, IYh),                # FDAC XOR IYh
            partial(self.xor, r, m, R2, 8, 2, IYl),                # FDAD XOR IYl
            partial(self.xor, r, m, R2, 19, 3, Yd),                # FDAE XOR (IY+d)
            partial(self.nop_dd_fd, r),                            # FDAF
            partial(self.nop_dd_fd, r),                            # FDB0
            partial(self.nop_dd_fd, r),                            # FDB1
            partial(self.nop_dd_fd, r),                            # FDB2
            partial(self.nop_dd_fd, r),                            # FDB3
            partial(self.ora, r, m, R2, 8, 2, IYh),                # FDB4 OR IYh
            partial(self.ora, r, m, R2, 8, 2, IYl),                # FDB5 OR IYl
            partial(self.ora, r, m, R2, 19, 3, Yd),                # FDB6 OR (IY+d)
            partial(self.nop_dd_fd, r),                            # FDB7
            partial(self.nop_dd_fd, r),                            # FDB8
            partial(self.nop_dd_fd, r),                            # FDB9
            partial(self.nop_dd_fd, r),                            # FDBA
            partial(self.nop_dd_fd, r),                            # FDBB
            partial(self.cp, r, m, R2, 8, 2, IYh),                 # FDBC CP IYh
            partial(self.cp, r, m, R2, 8, 2, IYl),                 # FDBD CP IYl
            partial(self.cp, r, m, R2, 19, 3, Yd),                 # FDBE CP (IY+d)
            partial(self.nop_dd_fd, r),                            # FDBF
            partial(self.nop_dd_fd, r),                            # FDC0
            partial(self.nop_dd_fd, r),                            # FDC1
            partial(self.nop_dd_fd, r),                            # FDC2
            partial(self.nop_dd_fd, r),                            # FDC3
            partial(self.nop_dd_fd, r),                            # FDC4
            partial(self.nop_dd_fd, r),                            # FDC5
            partial(self.nop_dd_fd, r),                            # FDC6
            partial(self.nop_dd_fd, r),                            # FDC7
            partial(self.nop_dd_fd, r),                            # FDC8
            partial(self.nop_dd_fd, r),                            # FDC9
            partial(self.nop_dd_fd, r),                            # FDCA
            partial(self.prefix2, self.after_FDCB, r, m),          # FDCB prefix
            partial(self.nop_dd_fd, r),                            # FDCC
            partial(self.nop_dd_fd, r),                            # FDCD
            partial(self.nop_dd_fd, r),                            # FDCE
            partial(self.nop_dd_fd, r),                            # FDCF
            partial(self.nop_dd_fd, r),                            # FDD0
            partial(self.nop_dd_fd, r),                            # FDD1
            partial(self.nop_dd_fd, r),                            # FDD2
            partial(self.nop_dd_fd, r),                            # FDD3
            partial(self.nop_dd_fd, r),                            # FDD4
            partial(self.nop_dd_fd, r),                            # FDD5
            partial(self.nop_dd_fd, r),                            # FDD6
            partial(self.nop_dd_fd, r),                            # FDD7
            partial(self.nop_dd_fd, r),                            # FDD8
            partial(self.nop_dd_fd, r),                            # FDD9
            partial(self.nop_dd_fd, r),                            # FDDA
            partial(self.nop_dd_fd, r),                            # FDDB
            partial(self.nop_dd_fd, r),                            # FDDC
            partial(self.nop_dd_fd, r),                            # FDDD
            partial(self.nop_dd_fd, r),                            # FDDE
            partial(self.nop_dd_fd, r),                            # FDDF
            partial(self.nop_dd_fd, r),                            # FDE0
            partial(self.pop, r, m, R2, 14, 2, IYh),               # FDE1 POP IY
            partial(self.nop_dd_fd, r),                            # FDE2
            partial(self.ex_sp, r, m, IYh),                        # FDE3 EX (SP),IY
            partial(self.nop_dd_fd, r),                            # FDE4
            partial(self.push, r, m, R2, 15, 2, IYh),              # FDE5 PUSH IY
            partial(self.nop_dd_fd, r),                            # FDE6
            partial(self.nop_dd_fd, r),                            # FDE7
            partial(self.nop_dd_fd, r),                            # FDE8
            partial(self.jp, r, m, R2, 8, 0, IYh),                 # FDE9 JP (IY)
            partial(self.nop_dd_fd, r),                            # FDEA
            partial(self.nop_dd_fd, r),                            # FDEB
            partial(self.nop_dd_fd, r),                            # FDEC
            partial(self.nop_dd_fd, r),                            # FDED
            partial(self.nop_dd_fd, r),                            # FDEE
            partial(self.nop_dd_fd, r),                            # FDEF
            partial(self.nop_dd_fd, r),                            # FDF0
            partial(self.nop_dd_fd, r),                            # FDF1
            partial(self.nop_dd_fd, r),                            # FDF2
            partial(self.nop_dd_fd, r),                            # FDF3
            partial(self.nop_dd_fd, r),                            # FDF4
            partial(self.nop_dd_fd, r),                            # FDF5
            partial(self.nop_dd_fd, r),                            # FDF6
            partial(self.nop_dd_fd, r),                            # FDF7
            partial(self.nop_dd_fd, r),                            # FDF8
            partial(self.ldsprr, r, R2, 10, 2, IYh),               # FDF9 LD SP,IY
            partial(self.nop_dd_fd, r),                            # FDFA
            partial(self.nop_dd_fd, r),                            # FDFB
            partial(self.nop_dd_fd, r),                            # FDFC
            partial(self.nop_dd_fd, r),                            # FDFD
            partial(self.nop_dd_fd, r),                            # FDFE
            partial(self.nop_dd_fd, r),                            # FDFF
        ]

        self.opcodes = [
            partial(self.nop, r),                                  # 00 NOP
            partial(self.ld16, r, m, R1, 10, 3, B),                # 01 LD BC,nn
            partial(self.ld8, r, m, R1, 7, 1, Bd, A),              # 02 LD (BC),A
            partial(self.inc_dec16, r, R1, 6, 1, 1, B),            # 03 INC BC
            partial(self.inc_r, r, B),                             # 04 INC B
            partial(self.dec_r, r, B),                             # 05 DEC B
            partial(self.ld_r_n, r, m, B),                         # 06 LD B,n
            partial(self.rotate_a, r, 128, RLC, 1),                # 07 RLCA
            partial(self.ex_af, r),                                # 08 EX AF,AF'
            partial(self.add16, r, R1, 11, 1, H, B),               # 09 ADD HL,BC
            partial(self.ld8, r, m, R1, 7, 1, A, Bd),              # 0A LD A,(BC)
            partial(self.inc_dec16, r, R1, 6, 1, -1, B),           # 0B DEC BC
            partial(self.inc_r, r, C),                             # 0C INC C
            partial(self.dec_r, r, C),                             # 0D DEC C
            partial(self.ld_r_n, r, m, C),                         # 0E LD C,n
            partial(self.rotate_a, r, 1, RRC, 1),                  # 0F RRCA
            partial(self.djnz, r, m),                              # 10 DJNZ nn
            partial(self.ld16, r, m, R1, 10, 3, D),                # 11 LD DE,nn
            partial(self.ld8, r, m, R1, 7, 1, Dd, A),              # 12 LD (DE),A
            partial(self.inc_dec16, r, R1, 6, 1, 1, D),            # 13 INC DE
            partial(self.inc_r, r, D),                             # 14 INC D
            partial(self.dec_r, r, D),                             # 15 DEC D
            partial(self.ld_r_n, r, m, D),                         # 16 LD D,n
            partial(self.rotate_a, r, 128, RL),                    # 17 RLA
            partial(self.jr, r, m, 0, 0),                          # 18 JR nn
            partial(self.add16, r, R1, 11, 1, H, D),               # 19 ADD HL,DE
            partial(self.ld8, r, m, R1, 7, 1, A, Dd),              # 1A LD A,(DE)
            partial(self.inc_dec16, r, R1, 6, 1, -1, D),           # 1B DEC DE
            partial(self.inc_r, r, E),                             # 1C INC E
            partial(self.dec_r, r, E),                             # 1D DEC E
            partial(self.ld_r_n, r, m, E),                         # 1E LD E,n
            partial(self.rotate_a, r, 1, RR),                      # 1F RRA
            partial(self.jr, r, m, 64, 0),                         # 20 JR NZ,nn
            partial(self.ld16, r, m, R1, 10, 3, H),                # 21 LD HL,nn
            partial(self.ld16addr, r, m, R1, 16, 3, H, 1),         # 22 LD (nn),HL
            partial(self.inc_dec16, r, R1, 6, 1, 1, H),            # 23 INC HL
            partial(self.inc_r, r, H),                             # 24 INC H
            partial(self.dec_r, r, H),                             # 25 DEC H
            partial(self.ld_r_n, r, m, H),                         # 26 LD H,n
            partial(self.daa, r),                                  # 27 DAA
            partial(self.jr, r, m, 64, 64),                        # 28 JR Z,nn
            partial(self.add16, r, R1, 11, 1, H, H),               # 29 ADD HL,HL
            partial(self.ld16addr, r, m, R1, 16, 3, H, 0),         # 2A LD HL,(nn)
            partial(self.inc_dec16, r, R1, 6, 1, -1, H),           # 2B DEC HL
            partial(self.inc_r, r, L),                             # 2C INC L
            partial(self.dec_r, r, L),                             # 2D DEC L
            partial(self.ld_r_n, r, m, L),                         # 2E LD L,n
            partial(self.cpl, r),                                  # 2F CPL
            partial(self.jr, r, m, 1, 0),                          # 30 JR NC,nn
            partial(self.ld16, r, m, R1, 10, 3, SP),               # 31 LD SP,nn
            partial(self.ldann, r, m, 1),                          # 32 LD (nn),A
            partial(self.inc_dec16, r, R1, 6, 1, 1, SP),           # 33 INC SP
            partial(self.inc_dec8, r, m, R1, 11, 1, 1, INC, Hd),   # 34 INC (HL)
            partial(self.inc_dec8, r, m, R1, 11, 1, -1, DEC, Hd),  # 35 DEC (HL)
            partial(self.ld8, r, m, R1, 10, 2, Hd, N),             # 36 LD (HL),n
            partial(self.cf, r, 0),                                # 37 SCF
            partial(self.jr, r, m, 1, 1),                          # 38 JR C,nn
            partial(self.add16, r, R1, 11, 1, H, SP),              # 39 ADD HL,SP
            partial(self.ldann, r, m, 0),                          # 3A LD A,(nn)
            partial(self.inc_dec16, r, R1, 6, 1, -1, SP),          # 3B DEC SP
            partial(self.inc_r, r, A),                             # 3C INC A
            partial(self.dec_r, r, A),                             # 3D DEC A
            partial(self.ld_r_n, r, m, A),                         # 3E LD A,n
            partial(self.cf, r, 1),                                # 3F CCF
            partial(self.ld_r_r, r, B, B),                         # 40 LD B,B
            partial(self.ld_r_r, r, B, C),                         # 41 LD B,C
            partial(self.ld_r_r, r, B, D),                         # 42 LD B,D
            partial(self.ld_r_r, r, B, E),                         # 43 LD B,E
            partial(self.ld_r_r, r, B, H),                         # 44 LD B,H
            partial(self.ld_r_r, r, B, L),                         # 45 LD B,L
            partial(self.ld8, r, m, R1, 7, 1, B, Hd),              # 46 LD B,(HL)
            partial(self.ld_r_r, r, B, A),                         # 47 LD B,A
            partial(self.ld_r_r, r, C, B),                         # 48 LD C,B
            partial(self.ld_r_r, r, C, C),                         # 49 LD C,C
            partial(self.ld_r_r, r, C, D),                         # 4A LD C,D
            partial(self.ld_r_r, r, C, E),                         # 4B LD C,E
            partial(self.ld_r_r, r, C, H),                         # 4C LD C,H
            partial(self.ld_r_r, r, C, L),                         # 4D LD C,L
            partial(self.ld8, r, m, R1, 7, 1, C, Hd),              # 4E LD C,(HL)
            partial(self.ld_r_r, r, C, A),                         # 4F LD C,A
            partial(self.ld_r_r, r, D, B),                         # 50 LD D,B
            partial(self.ld_r_r, r, D, C),                         # 51 LD D,C
            partial(self.ld_r_r, r, D, D),                         # 52 LD D,D
            partial(self.ld_r_r, r, D, E),                         # 53 LD D,E
            partial(self.ld_r_r, r, D, H),                         # 54 LD D,H
            partial(self.ld_r_r, r, D, L),                         # 55 LD D,L
            partial(self.ld8, r, m, R1, 7, 1, D, Hd),              # 56 LD D,(HL)
            partial(self.ld_r_r, r, D, A),                         # 57 LD D,A
            partial(self.ld_r_r, r, E, B),                         # 58 LD E,B
            partial(self.ld_r_r, r, E, C),                         # 59 LD E,C
            partial(self.ld_r_r, r, E, D),                         # 5A LD E,D
            partial(self.ld_r_r, r, E, E),                         # 5B LD E,E
            partial(self.ld_r_r, r, E, H),                         # 5C LD E,H
            partial(self.ld_r_r, r, E, L),                         # 5D LD E,L
            partial(self.ld8, r, m, R1, 7, 1, E, Hd),              # 5E LD E,(HL)
            partial(self.ld_r_r, r, E, A),                         # 5F LD E,A
            partial(self.ld_r_r, r, H, B),                         # 60 LD H,B
            partial(self.ld_r_r, r, H, C),                         # 61 LD H,C
            partial(self.ld_r_r, r, H, D),                         # 62 LD H,D
            partial(self.ld_r_r, r, H, E),                         # 63 LD H,E
            partial(self.ld_r_r, r, H, H),                         # 64 LD H,H
            partial(self.ld_r_r, r, H, L),                         # 65 LD H,L
            partial(self.ld8, r, m, R1, 7, 1, H, Hd),              # 66 LD H,(HL)
            partial(self.ld_r_r, r, H, A),                         # 67 LD H,A
            partial(self.ld_r_r, r, L, B),                         # 68 LD L,B
            partial(self.ld_r_r, r, L, C),                         # 69 LD L,C
            partial(self.ld_r_r, r, L, D),                         # 6A LD L,D
            partial(self.ld_r_r, r, L, E),                         # 6B LD L,E
            partial(self.ld_r_r, r, L, H),                         # 6C LD L,H
            partial(self.ld_r_r, r, L, L),                         # 6D LD L,L
            partial(self.ld8, r, m, R1, 7, 1, L, Hd),              # 6E LD L,(HL)
            partial(self.ld_r_r, r, L, A),                         # 6F LD L,A
            partial(self.ld8, r, m, R1, 7, 1, Hd, B),              # 70 LD (HL),B
            partial(self.ld8, r, m, R1, 7, 1, Hd, C),              # 71 LD (HL),C
            partial(self.ld8, r, m, R1, 7, 1, Hd, D),              # 72 LD (HL),D
            partial(self.ld8, r, m, R1, 7, 1, Hd, E),              # 73 LD (HL),E
            partial(self.ld8, r, m, R1, 7, 1, Hd, H),              # 74 LD (HL),H
            partial(self.ld8, r, m, R1, 7, 1, Hd, L),              # 75 LD (HL),L
            partial(self.halt, r),                                 # 76 HALT
            partial(self.ld8, r, m, R1, 7, 1, Hd, A),              # 77 LD (HL),A
            partial(self.ld_r_r, r, A, B),                         # 78 LD A,B
            partial(self.ld_r_r, r, A, C),                         # 79 LD A,C
            partial(self.ld_r_r, r, A, D),                         # 7A LD A,D
            partial(self.ld_r_r, r, A, E),                         # 7B LD A,E
            partial(self.ld_r_r, r, A, H),                         # 7C LD A,H
            partial(self.ld_r_r, r, A, L),                         # 7D LD A,L
            partial(self.ld8, r, m, R1, 7, 1, A, Hd),              # 7E LD A,(HL)
            partial(self.ld_r_r, r, A, A),                         # 7F LD A,A
            partial(self.add_a, r, m, R1, 4, 1, B),                # 80 ADD A,B
            partial(self.add_a, r, m, R1, 4, 1, C),                # 81 ADD A,C
            partial(self.add_a, r, m, R1, 4, 1, D),                # 82 ADD A,D
            partial(self.add_a, r, m, R1, 4, 1, E),                # 83 ADD A,E
            partial(self.add_a, r, m, R1, 4, 1, H),                # 84 ADD A,H
            partial(self.add_a, r, m, R1, 4, 1, L),                # 85 ADD A,L
            partial(self.add_a, r, m, R1, 7, 1, Hd),               # 86 ADD A,(HL)
            partial(self.add_a, r, m, R1, 4, 1, A),                # 87 ADD A,A
            partial(self.adc_a, r, m, R1, 4, 1, B),                # 88 ADC A,B
            partial(self.adc_a, r, m, R1, 4, 1, C),                # 89 ADC A,C
            partial(self.adc_a, r, m, R1, 4, 1, D),                # 8A ADC A,D
            partial(self.adc_a, r, m, R1, 4, 1, E),                # 8B ADC A,E
            partial(self.adc_a, r, m, R1, 4, 1, H),                # 8C ADC A,H
            partial(self.adc_a, r, m, R1, 4, 1, L),                # 8D ADC A,L
            partial(self.adc_a, r, m, R1, 7, 1, Hd),               # 8E ADC A,(HL)
            partial(self.adc_a_a, r),                              # 8F ADC A,A
            partial(self.sub, r, m, R1, 4, 1, B),                  # 90 SUB B
            partial(self.sub, r, m, R1, 4, 1, C),                  # 91 SUB C
            partial(self.sub, r, m, R1, 4, 1, D),                  # 92 SUB D
            partial(self.sub, r, m, R1, 4, 1, E),                  # 93 SUB E
            partial(self.sub, r, m, R1, 4, 1, H),                  # 94 SUB H
            partial(self.sub, r, m, R1, 4, 1, L),                  # 95 SUB L
            partial(self.sub, r, m, R1, 7, 1, Hd),                 # 96 SUB (HL)
            partial(self.sub, r, m, R1, 4, 1, A),                  # 97 SUB A
            partial(self.sbc_a, r, m, R1, 4, 1, B),                # 98 SBC A,B
            partial(self.sbc_a, r, m, R1, 4, 1, C),                # 99 SBC A,C
            partial(self.sbc_a, r, m, R1, 4, 1, D),                # 9A SBC A,D
            partial(self.sbc_a, r, m, R1, 4, 1, E),                # 9B SBC A,E
            partial(self.sbc_a, r, m, R1, 4, 1, H),                # 9C SBC A,H
            partial(self.sbc_a, r, m, R1, 4, 1, L),                # 9D SBC A,L
            partial(self.sbc_a, r, m, R1, 7, 1, Hd),               # 9E SBC A,(HL)
            partial(self.sbc_a_a, r),                              # 9F SBC A,A
            partial(self.and_r, r, B),                             # A0 AND B
            partial(self.and_r, r, C),                             # A1 AND C
            partial(self.and_r, r, D),                             # A2 AND D
            partial(self.and_r, r, E),                             # A3 AND E
            partial(self.and_r, r, H),                             # A4 AND H
            partial(self.and_r, r, L),                             # A5 AND L
            partial(self.anda, r, m, R1, 7, 1, Hd),                # A6 AND (HL)
            partial(self.and_r, r, A),                             # A7 AND A
            partial(self.xor_r, r, B),                             # A8 XOR B
            partial(self.xor_r, r, C),                             # A9 XOR C
            partial(self.xor_r, r, D),                             # AA XOR D
            partial(self.xor_r, r, E),                             # AB XOR E
            partial(self.xor_r, r, H),                             # AC XOR H
            partial(self.xor_r, r, L),                             # AD XOR L
            partial(self.xor, r, m, R1, 7, 1, Hd),                 # AE XOR (HL)
            partial(self.xor_r, r, A),                             # AF XOR A
            partial(self.or_r, r, B),                              # B0 OR B
            partial(self.or_r, r, C),                              # B1 OR C
            partial(self.or_r, r, D),                              # B2 OR D
            partial(self.or_r, r, E),                              # B3 OR E
            partial(self.or_r, r, H),                              # B4 OR H
            partial(self.or_r, r, L),                              # B5 OR L
            partial(self.ora, r, m, R1, 7, 1, Hd),                 # B6 OR (HL)
            partial(self.or_r, r, A),                              # B7 OR A
            partial(self.cp, r, m, R1, 4, 1, B),                   # B8 CP B
            partial(self.cp, r, m, R1, 4, 1, C),                   # B9 CP C
            partial(self.cp, r, m, R1, 4, 1, D),                   # BA CP D
            partial(self.cp, r, m, R1, 4, 1, E),                   # BB CP E
            partial(self.cp, r, m, R1, 4, 1, H),                   # BC CP H
            partial(self.cp, r, m, R1, 4, 1, L),                   # BD CP L
            partial(self.cp, r, m, R1, 7, 1, Hd),                  # BE CP (HL)
            partial(self.cp, r, m, R1, 4, 1, A),                   # BF CP A
            partial(self.ret, r, m, 64, 64),                       # C0 RET NZ
            partial(self.pop, r, m, R1, 10, 1, B),                 # C1 POP BC
            partial(self.jp, r, m, R1, 10, 64, 64),                # C2 JP NZ,nn
            partial(self.jp, r, m, R1, 10, 0, 0),                  # C3 JP nn
            partial(self.call, r, m, 64, 64),                      # C4 CALL NZ,nn
            partial(self.push, r, m, R1, 11, 1, B),                # C5 PUSH BC
            partial(self.add_a, r, m, R1, 7, 2, N),                # C6 ADD A,n
            partial(self.rst, r, m, 0),                            # C7 RST $00
            partial(self.ret, r, m, 64, 0),                        # C8 RET Z
            partial(self.ret, r, m, 0, 0),                         # C9 RET
            partial(self.jp, r, m, R1, 10, 64, 0),                 # CA JP Z,nn
            partial(self.prefix, self.after_CB, r, m),             # CB prefix
            partial(self.call, r, m, 64, 0),                       # CC CALL Z,nn
            partial(self.call, r, m, 0, 0),                        # CD CALL nn
            partial(self.adc_a, r, m, R1, 7, 2, N),                # CE ADC A,n
            partial(self.rst, r, m, 8),                            # CF RST $08
            partial(self.ret, r, m, 1, 1),                         # D0 RET NC
            partial(self.pop, r, m, R1, 10, 1, D),                 # D1 POP DE
            partial(self.jp, r, m, R1, 10, 1, 1),                  # D2 JP NC,nn
            partial(self.outa, r, m),                              # D3 OUT (n),A
            partial(self.call, r, m, 1, 1),                        # D4 CALL NC,nn
            partial(self.push, r, m, R1, 11, 1, D),                # D5 PUSH DE
            partial(self.sub, r, m, R1, 7, 2, N),                  # D6 SUB n
            partial(self.rst, r, m, 16),                           # D7 RST $10
            partial(self.ret, r, m, 1, 0),                         # D8 RET C
            partial(self.exx, r),                                  # D9 EXX
            partial(self.jp, r, m, R1, 10, 1, 0),                  # DA JP C,nn
            partial(self.in_a, r, m),                              # DB IN A,(n)
            partial(self.call, r, m, 1, 0),                        # DC CALL C,nn
            partial(self.prefix, self.after_DD, r, m),             # DD prefix
            partial(self.sbc_a, r, m, R1, 7, 2, N),                # DE SBC A,n
            partial(self.rst, r, m, 24),                           # DF RST $18
            partial(self.ret, r, m, 4, 4),                         # E0 RET PO
            partial(self.pop, r, m, R1, 10, 1, H),                 # E1 POP HL
            partial(self.jp, r, m, R1, 10, 4, 4),                  # E2 JP PO,nn
            partial(self.ex_sp, r, m, H),                          # E3 EX (SP),HL
            partial(self.call, r, m, 4, 4),                        # E4 CALL PO,nn
            partial(self.push, r, m, R1, 11, 1, H),                # E5 PUSH HL
            partial(self.and_n, r, m),                             # E6 AND n
            partial(self.rst, r, m, 32),                           # E7 RST $20
            partial(self.ret, r, m, 4, 0),                         # E8 RET PE
            partial(self.jp, r, m, R1, 4, 0, H),                   # E9 JP (HL)
            partial(self.jp, r, m, R1, 10, 4, 0),                  # EA JP PE,nn
            partial(self.ex_de_hl, r),                             # EB EX DE,HL
            partial(self.call, r, m, 4, 0),                        # EC CALL PE,nn
            partial(self.prefix, self.after_ED, r, m),             # ED prefix
            partial(self.xor_n, r, m),                             # EE XOR n
            partial(self.rst, r, m, 40),                           # EF RST $28
            partial(self.ret, r, m, 128, 128),                     # F0 RET P
            partial(self.pop, r, m, R1, 10, 1, A),                 # F1 POP AF
            partial(self.jp, r, m, R1, 10, 128, 128),              # F2 JP P,nn
            partial(self.di_ei, r, 0),                             # F3 DI
            partial(self.call, r, m, 128, 128),                    # F4 CALL P,nn
            partial(self.push, r, m, R1, 11, 1, A),                # F5 PUSH AF
            partial(self.or_n, r, m),                              # F6 OR n
            partial(self.rst, r, m, 48),                           # F7 RST $30
            partial(self.ret, r, m, 128, 0),                       # F8 RET M
            partial(self.ldsprr, r, R1, 6, 1, H),                  # F9 LD SP,HL
            partial(self.jp, r, m, R1, 10, 128, 0),                # FA JP M,nn
            partial(self.di_ei, r, 1),                             # FB EI
            partial(self.call, r, m, 128, 0),                      # FC CALL M,nn
            partial(self.prefix, self.after_FD, r, m),             # FD prefix
            partial(self.cp, r, m, R1, 7, 2, N),                   # FE CP n
            partial(self.rst, r, m, 56),                           # FF RST $38
        ]
