# Copyright 2022, 2023 Richard Dymond (rjdymond@gmail.com)
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

JR_OFFSETS = tuple(j + 2 if j < 128 else j - 254 for j in range(256))

OFFSETS = tuple(d if d < 128 else d - 256 for d in range(256))

R1 = tuple((r & 0x80) + ((r + 1) % 128) for r in range(256))

R2 = tuple((r & 0x80) + ((r + 2) % 128) for r in range(256))

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
SP2 = 13
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
            0,     # SP2 (must be 0)
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
        self.imode = state.get('im', 1)
        self.iff = state.get('iff', 0)
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
        self.set_tracer(None)

    def set_tracer(self, tracer, in_r_c=True, ini=True):
        self.in_a_n_tracer = None
        self.in_r_c_tracer = None
        self.ini_tracer = None
        self.out_tracer = None
        if hasattr(tracer, 'read_port'):
            self.in_a_n_tracer = partial(tracer.read_port, self.registers)
            if in_r_c:
                self.in_r_c_tracer = partial(tracer.read_port, self.registers)
            if ini:
                self.ini_tracer = partial(tracer.read_port, self.registers)
        if hasattr(tracer, 'write_port'):
            self.out_tracer = partial(tracer.write_port, self.registers)

    def run(self, start=None, stop=None):
        opcodes = self.opcodes
        memory = self.memory
        registers = self.registers
        if start is not None:
            registers[24] = start # PC
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

    def accept_interrupt(self, registers, memory, prev_pc):
        opcode = memory[prev_pc]
        pc = registers[24]
        if opcode == 0xFB or (opcode in (0xDD, 0xFD) and prev_pc == (pc - 1) % 65536):
            return True
        if self.imode == 2:
            vaddr = 255 + 256 * registers[14]
            iaddr = memory[vaddr] + 256 * memory[(vaddr + 1) % 65536]
            registers[25] += 19 # T-states
        else:
            iaddr = 56
            registers[25] += 13 # T-states
        sp = (registers[12] - 2) % 65536
        registers[12] = sp
        if sp > 0x3FFF:
            memory[sp] = pc % 256
        sp = (sp + 1) % 65536
        if sp > 0x3FFF:
            memory[sp] = pc // 256
        registers[15] = R1[registers[15]] # R
        registers[24] = iaddr # PC
        self.iff = 0
        return False

    def prefix(self, opcodes, registers, memory):
        opcodes[memory[(registers[24] + 1) % 65536]]()

    def prefix2(self, opcodes, registers, memory):
        opcodes[memory[(registers[24] + 3) % 65536]]()

    def af_hl(self, registers, memory, af):
        # ADD A,(HL) / AND (HL) / CP (HL) / OR (HL) / SUB (HL) / XOR (HL)
        registers[:2] = af[registers[0]][memory[registers[7] + 256 * registers[6]]]
        registers[15] = R1[registers[15]] # R
        registers[25] += 7 # T-states
        registers[24] = (registers[24] + 1) % 65536 # PC

    def af_n(self, registers, memory, af):
        # ADD A,n / AND n / CP n / OR n / SUB n / XOR n
        pcn = registers[24] + 1
        registers[:2] = af[registers[0]][memory[pcn % 65536]]
        registers[15] = R1[registers[15]] # R
        registers[25] += 7 # T-states
        registers[24] = (pcn + 1) % 65536 # PC

    def af_r(self, registers, r_inc, timing, size, af, r):
        # ADD A,r / AND r / CP r / OR r / SUB r / XOR r
        # CPL / DAA / RLA / RLCA / RRA / RRCA
        registers[:2] = af[registers[0]][registers[r]]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = (registers[24] + size) % 65536 # PC

    def af_xy(self, registers, memory, af, xyh, xyl):
        # ADD A,(IX/Y+d) / AND (IX/Y+d) / CP (IX/Y+d) / OR (IX/Y+d)
        # SUB (IX/Y+d) / XOR (IX/Y+d)
        pcn = registers[24] + 3
        registers[:2] = af[registers[0]][memory[(registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[(pcn - 1) % 65536]]) % 65536]]
        registers[15] = R2[registers[15]] # R
        registers[25] += 19 # T-states
        registers[24] = pcn % 65536 # PC

    def afc_hl(self, registers, memory, afc):
        # ADC/SBC A,(HL)
        registers[:2] = afc[registers[1] % 2][registers[0]][memory[registers[7] + 256 * registers[6]]]
        registers[15] = R1[registers[15]] # R
        registers[25] += 7 # T-states
        registers[24] = (registers[24] + 1) % 65536 # PC

    def afc_n(self, registers, memory, afc):
        # ADC/SBC A,n
        pcn = registers[24] + 1
        registers[:2] = afc[registers[1] % 2][registers[0]][memory[pcn % 65536]]
        registers[15] = R1[registers[15]] # R
        registers[25] += 7 # T-states
        registers[24] = (pcn + 1) % 65536 # PC

    def afc_r(self, registers, r_inc, timing, size, afc, r):
        # ADC/SBC A,r (r != A)
        registers[:2] = afc[registers[1] % 2][registers[0]][registers[r]]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = (registers[24] + size) % 65536 # PC

    def afc_xy(self, registers, memory, afc, xyh, xyl):
        # ADC/SBC A,(IX/Y+d)
        pcn = registers[24] + 3
        registers[:2] = afc[registers[1] % 2][registers[0]][memory[(registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[(pcn - 1) % 65536]]) % 65536]]
        registers[15] = R2[registers[15]] # R
        registers[25] += 19 # T-states
        registers[24] = pcn % 65536 # PC

    def f_hl(self, registers, memory, f):
        # RLC/RRC/SLA/SLL/SRA/SRL (HL)
        hl = registers[7] + 256 * registers[6]
        value, registers[1] = f[memory[hl]]
        if hl > 0x3FFF:
            memory[hl] = value
        registers[15] = R2[registers[15]] # R
        registers[25] += 15 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def f_r(self, registers, f, r):
        # RLC/RRC/SLA/SLL/SRA/SRL r
        registers[r], registers[1] = f[registers[r]]
        registers[15] = R2[registers[15]] # R
        registers[25] += 8 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def f_xy(self, registers, memory, f, xyh, xyl, dest=-1):
        # RLC/RRC/SLA/SLL/SRA/SRL (IX/Y+d)[,r]
        pcn = registers[24] + 4
        addr = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[(pcn - 2) % 65536]]) % 65536
        value, registers[1] = f[memory[addr]]
        if addr > 0x3FFF:
            memory[addr] = value
        if dest >= 0:
            registers[dest] = value
        registers[15] = R2[registers[15]] # R
        registers[25] += 23 # T-states
        registers[24] = pcn % 65536 # PC

    def fc_hl(self, registers, memory, r_inc, timing, size, fc):
        # DEC/INC/RL/RR (HL)
        hl = registers[7] + 256 * registers[6]
        value, registers[1] = fc[registers[1] % 2][memory[hl]]
        if hl > 0x3FFF:
            memory[hl] = value
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = (registers[24] + size) % 65536 # PC

    def fc_r(self, registers, r_inc, timing, size, fc, r):
        # DEC/INC/RL/RR r / ADC A,A / SBC A,A
        registers[r], registers[1] = fc[registers[1] % 2][registers[r]]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = (registers[24] + size) % 65536 # PC

    def fc_xy(self, registers, memory, size, fc, xyh, xyl, dest=-1):
        # DEC/INC/RL/RR (IX/Y+d)[,r]
        pc = registers[24]
        addr = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[(pc + 2) % 65536]]) % 65536
        value, registers[1] = fc[registers[1] % 2][memory[addr]]
        if addr > 0x3FFF:
            memory[addr] = value
        if dest >= 0:
            registers[dest] = value
        registers[15] = R2[registers[15]] # R
        registers[25] += 23 # T-states
        registers[24] = (pc + size) % 65536 # PC

    def adc_hl(self, registers, rh, rl):
        # ADC HL,BC/DE/HL/SP
        rr = registers[rl] + 256 * registers[rh]
        hl = registers[7] + 256 * registers[6]
        rr_c = rr + registers[1] % 2
        result = hl + rr_c

        if result > 0xFFFF:
            result %= 65536
            f = 0x01 # .......C
        else:
            f = 0
        if result == 0:
            f += 0x40 # .Z......
        if (hl % 4096) + (rr_c % 4096) > 0x0FFF:
            f += 0x10 # ...H....
        if hl ^ rr < 0x8000 and hl ^ result > 0x7FFF:
            # Augend and addend signs are the same - overflow if their sign
            # differs from the sign of the result
            f += 0x04 # .....P..

        h = result // 256
        registers[1] = f + (h & 0xA8)
        registers[7] = result % 256
        registers[6] = h
        registers[15] = R2[registers[15]] # R
        registers[25] += 15 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def add_rr(self, registers, r_inc, timing, size, ah, al, rh, rl):
        # ADD HL/IX/IY,BC/DE/HL/SP/IX/IY
        addend_v = registers[rl] + 256 * registers[rh]
        augend_v = registers[al] + 256 * registers[ah]
        result = augend_v + addend_v

        if result > 0xFFFF:
            result %= 65536
            f = (registers[1] & 0xC4) + 0x01 # SZ...P.C
        else:
            f = registers[1] & 0xC4 # SZ...P..
        if (augend_v % 4096) + (addend_v % 4096) > 0x0FFF:
            f += 0x10 # ...H....

        result_hi = result // 256
        registers[1] = f + (result_hi & 0x28)
        registers[al] = result % 256
        registers[ah] = result_hi
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = (registers[24] + size) % 65536 # PC

    def bit_hl(self, registers, memory, bit, b):
        # BIT n,(HL)
        registers[1] = bit[registers[1] % 2][b][memory[registers[7] + 256 * registers[6]]]
        registers[15] = R2[registers[15]] # R
        registers[25] += 12 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def bit_r(self, registers, bit, b, reg):
        # BIT n,r
        registers[1] = bit[registers[1] % 2][b][registers[reg]]
        registers[15] = R2[registers[15]] # R
        registers[25] += 8 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def bit_xy(self, registers, memory, bit, b, xyh, xyl):
        # BIT n,(IX/Y+d)
        xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[(registers[24] + 2) % 65536]]) % 65536
        registers[1] = (bit[registers[1] % 2][b][memory[xy]] & 0xD7) + ((xy // 256) & 0x28)
        registers[15] = R2[registers[15]] # R
        registers[25] += 20 # T-states
        registers[24] = (registers[24] + 4) % 65536 # PC

    def call(self, registers, memory, c_and, c_val):
        # CALL nn / CALL cc,nn
        if c_and and registers[1] & c_and == c_val:
            registers[25] += 10 # T-states
            registers[24] = (registers[24] + 3) % 65536 # PC
        else:
            pc = registers[24]
            registers[24] = memory[(pc + 1) % 65536] + 256 * memory[(pc + 2) % 65536] # PC
            ret_addr = (pc + 3) % 65536
            sp = (registers[12] - 2) % 65536
            registers[12] = sp
            if sp > 0x3FFF:
                memory[sp] = ret_addr % 256
            sp = (sp + 1) % 65536
            if sp > 0x3FFF:
                memory[sp] = ret_addr // 256
            registers[25] += 17 # T-states
        registers[15] = R1[registers[15]] # R

    def cf(self, registers, cf):
        # CCF / SCF
        registers[1] = cf[registers[1]][registers[0]]
        registers[15] = R1[registers[15]] # R
        registers[25] += 4 # T-states
        registers[24] = (registers[24] + 1) % 65536 # PC

    def cpi(self, registers, memory, inc, repeat):
        # CPI / CPD / CPIR / CPDR
        hl = registers[7] + 256 * registers[6]
        bc = registers[3] + 256 * registers[2]
        a = registers[0]
        value = memory[hl]
        hl = (hl + inc) % 65536
        bc = (bc - 1) % 65536
        registers[7] = hl % 256
        registers[6] = hl // 256
        registers[3] = bc % 256
        registers[2] = bc // 256

        cp = a - value
        hf = a % 16 < value % 16
        f = (cp & 0x80) + hf * 0x10 + 0x02 + (registers[1] % 2) # S..H..NC
        if repeat and cp and bc:
            registers[1] = f + ((registers[24] // 256) & 0x28) + 0x04 # .Z5.3P..
            registers[25] += 21 # T-states
        else:
            n = cp - hf
            registers[1] = f + (cp == 0) * 0x40 + (n & 0x02) * 16 + (n & 0x08) + (bc > 0) * 0x04 # .Z5.3P..
            registers[25] += 16 # T-states
            registers[24] = (registers[24] + 2) % 65536 # PC
        registers[15] = R2[registers[15]] # R

    def di_ei(self, registers, iff):
        # DI / EI
        self.iff = iff
        registers[15] = R1[registers[15]] # R
        registers[25] += 4 # T-states
        registers[24] = (registers[24] + 1) % 65536 # PC

    def djnz(self, registers, memory):
        # DJNZ nn
        b = (registers[2] - 1) % 256
        registers[2] = b
        if b:
            registers[25] += 13 # T-states
            pc = registers[24]
            registers[24] = (pc + JR_OFFSETS[memory[(pc + 1) % 65536]]) % 65536 # PC
        else:
            registers[25] += 8 # T-states
            registers[24] = (registers[24] + 2) % 65536 # PC
        registers[15] = R1[registers[15]] # R

    def djnz_fast(self, registers, memory):
        if memory[(registers[24] + 1) % 65536] == 0xFE:
            b = (registers[2] - 1) % 256
            registers[2] = 0
            r = registers[15]
            registers[15] = (r & 0x80) + ((r + b + 1) % 128) # R
            registers[25] += b * 13 + 8 # T-states
            registers[24] = (registers[24] + 2) % 65536 # PC
        else:
            self.djnz(registers, memory)

    def ex_af(self, registers):
        # EX AF,AF'
        registers[0], registers[16] = registers[16], registers[0]
        registers[1], registers[17] = registers[17], registers[1]
        registers[15] = R1[registers[15]] # R
        registers[25] += 4 # T-states
        registers[24] = (registers[24] + 1) % 65536 # PC

    def ex_de_hl(self, registers):
        # EX DE,HL
        registers[4], registers[6] = registers[6], registers[4]
        registers[5], registers[7] = registers[7], registers[5]
        registers[15] = R1[registers[15]] # R
        registers[25] += 4 # T-states
        registers[24] = (registers[24] + 1) % 65536 # PC

    def ex_sp(self, registers, memory, r_inc, timing, size, rh, rl):
        # EX (SP),HL/IX/IY
        sp = registers[12]
        sp1 = memory[sp]
        if sp > 0x3FFF:
            memory[sp] = registers[rl]
        sp = (sp + 1) % 65536
        sp2 = memory[sp]
        if sp > 0x3FFF:
            memory[sp] = registers[rh]
        registers[rl] = sp1
        registers[rh] = sp2
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = (registers[24] + size) % 65536 # PC

    def exx(self, registers):
        # EXX
        registers[2:8], registers[18:24] = registers[18:24], registers[2:8]
        registers[15] = R1[registers[15]] # R
        registers[25] += 4 # T-states
        registers[24] = (registers[24] + 1) % 65536 # PC

    def halt(self, registers):
        # HALT
        if self.iff:
            t = registers[25]
            if (t + 4) // FRAME_DURATION > t // FRAME_DURATION:
                registers[24] = (registers[24] + 1) % 65536 # PC
        registers[15] = R1[registers[15]] # R
        registers[25] += 4 # T-states

    def im(self, registers, mode):
        # IM 0/1/2
        self.imode = mode
        registers[15] = R2[registers[15]] # R
        registers[25] += 8 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def in_a(self, registers, memory):
        # IN A,(n)
        pcn = registers[24] + 1
        if self.in_a_n_tracer:
            registers[0] = self.in_a_n_tracer(memory[pcn % 65536] + 256 * registers[0])
        else:
            registers[0] = 255
        registers[15] = R1[registers[15]] # R
        registers[25] += 11 # T-states
        registers[24] = (pcn + 1) % 65536 # PC

    def in_c(self, registers, reg, sz53p):
        # IN r,(C)
        if self.in_r_c_tracer:
            value = self.in_r_c_tracer(registers[3] + 256 * registers[2])
        else:
            value = 255
        if reg != 1:
            registers[reg] = value
        registers[1] = sz53p[value] + (registers[1] % 2)
        registers[15] = R2[registers[15]] # R
        registers[25] += 12 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def inc_dec_rr(self, registers, r_inc, timing, size, inc, rh, rl):
        # INC/DEC BC/DE/HL/SP/IX/IY
        if rl == 12:
            registers[12] = (registers[12] + inc) % 65536
        else:
            value = (registers[rl] + 256 * registers[rh] + inc) % 65536
            registers[rh] = value // 256
            registers[rl] = value % 256
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = (registers[24] + size) % 65536 # PC

    def ini(self, registers, memory, inc, repeat, parity):
        # INI / IND / INIR / INDR
        hl = registers[7] + 256 * registers[6]
        b = registers[2]
        c = registers[3]

        if self.ini_tracer:
            value = self.ini_tracer(c + 256 * b)
        else:
            value = 191
        if hl > 0x3FFF:
            memory[hl] = value
        b = (b - 1) % 256
        hl = (hl + inc) % 65536
        registers[7] = hl % 256
        registers[6] = hl // 256
        registers[2] = b

        j = value + ((c + inc) % 256)
        n = (value & 0x80) // 64
        c = j > 0xFF
        if repeat and b:
            if c:
                if n:
                    h = (b % 16 == 0) * 0x10
                    p = parity[(j % 8) ^ b ^ ((b - 1) % 8)]
                else:
                    h = (b % 16 == 15) * 0x10
                    p = parity[(j % 8) ^ b ^ ((b + 1) % 8)]
            else:
                h = 0
                p = parity[(j % 8) ^ b ^ (b % 8)]
            registers[1] = (b & 0x80) + ((registers[24] // 256) & 0x28) + h + p + n + c
            registers[25] += 21 # T-states
        else:
            registers[1] = (b & 0xA8) + (b == 0) * 0x40 + c * 0x11 + parity[(j % 8) ^ b] + n
            registers[24] = (registers[24] + 2) % 65536 # PC
            registers[25] += 16 # T-states
        registers[15] = R2[registers[15]] # R

    def jp(self, registers, memory, c_and, c_val):
        # JP nn / JP cc,nn
        if registers[1] & c_and == c_val:
            registers[24] = memory[(registers[24] + 1) % 65536] + 256 * memory[(registers[24] + 2) % 65536] # PC
        else:
            registers[24] = (registers[24] + 3) % 65536 # PC
        registers[15] = R1[registers[15]] # R
        registers[25] += 10 # T-states

    def jp_rr(self, registers, r_inc, timing, rh, rl):
        # JP (HL/IX/IY)
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = registers[rl] + 256 * registers[rh] # PC

    def jr(self, registers, memory, c_and, c_val):
        # JR nn / JR cc,nn
        if registers[1] & c_and == c_val:
            registers[25] += 12 # T-states
            pc = registers[24]
            registers[24] = (pc + JR_OFFSETS[memory[(pc + 1) % 65536]]) % 65536 # PC
        else:
            registers[25] += 7 # T-states
            registers[24] = (registers[24] + 2) % 65536 # PC
        registers[15] = R1[registers[15]] # R

    def ld_a_ir(self, registers, r):
        # LD A,I/R
        registers[15] = R2[registers[15]] # R
        a = registers[r]
        registers[0] = a
        registers[1] = (a & 0xA8) + (a == 0) * 0x40 + self.iff * 0x04 + (registers[1] % 2)
        registers[25] += 9 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def ld_hl_n(self, registers, memory):
        # LD (HL),n
        pcn = registers[24] + 1
        addr = registers[7] + 256 * registers[6]
        if addr > 0x3FFF:
            memory[addr] = memory[pcn % 65536]
        registers[15] = R1[registers[15]] # R
        registers[25] += 10 # T-states
        registers[24] = (pcn + 1) % 65536 # PC

    def ld_r_n(self, registers, memory, r_inc, timing, size, r):
        # LD r,n
        end = registers[24] + size
        registers[r] = memory[(end - 1) % 65536]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = end % 65536 # PC

    def ld_r_r(self, registers, r_inc, timing, size, r1, r2):
        # LD r,r
        registers[15] = r_inc[registers[15]] # R
        registers[r1] = registers[r2]
        registers[25] += timing # T-states
        registers[24] = (registers[24] + size) % 65536 # PC

    def ld_r_rr(self, registers, memory, r, rh, rl):
        # LD r,(HL/DE/BC)
        registers[r] = memory[registers[rl] + 256 * registers[rh]]
        registers[15] = R1[registers[15]] # R
        registers[25] += 7 # T-states
        registers[24] = (registers[24] + 1) % 65536 # PC

    def ld_rr_r(self, registers, memory, rh, rl, r):
        # LD (HL/DE/BC),r
        addr = registers[rl] + 256 * registers[rh]
        if addr > 0x3FFF:
            memory[addr] = registers[r]
        registers[15] = R1[registers[15]] # R
        registers[25] += 7 # T-states
        registers[24] = (registers[24] + 1) % 65536 # PC

    def ld_r_xy(self, registers, memory, r, xyh, xyl):
        # LD r,(IX/Y+d)
        pcn = registers[24] + 3
        registers[r] = memory[(registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[(pcn - 1) % 65536]]) % 65536]
        registers[15] = R2[registers[15]] # R
        registers[25] += 19 # T-states
        registers[24] = pcn % 65536 # PC

    def ld_xy_n(self, registers, memory, xyh, xyl):
        # LD (IX/Y+d),n
        pcn = registers[24] + 4
        addr = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[(pcn - 2) % 65536]]) % 65536
        if addr > 0x3FFF:
            memory[addr] = memory[(pcn - 1) % 65536]
        registers[15] = R2[registers[15]] # R
        registers[25] += 19 # T-states
        registers[24] = pcn % 65536 # PC

    def ld_xy_r(self, registers, memory, xyh, xyl, r):
        # LD (IX/Y+d),r
        pcn = registers[24] + 3
        addr = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[(pcn - 1) % 65536]]) % 65536
        if addr > 0x3FFF:
            memory[addr] = registers[r]
        registers[15] = R2[registers[15]] # R
        registers[25] += 19 # T-states
        registers[24] = pcn % 65536 # PC

    def ld_rr_nn(self, registers, memory, r_inc, timing, size, rh, rl):
        # LD BC/DE/HL/SP/IX/IY,nn
        end = registers[24] + size
        if rl == 12:
            registers[12] = memory[(end - 2) % 65536] + 256 * memory[(end - 1) % 65536]
        else:
            registers[rl] = memory[(end - 2) % 65536]
            registers[rh] = memory[(end - 1) % 65536]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = end % 65536 # PC

    def ld_a_m(self, registers, memory):
        # LD A,(nn)
        pcn = registers[24] + 1
        registers[0] = memory[memory[pcn % 65536] + 256 * memory[(pcn + 1) % 65536]]
        registers[15] = R1[registers[15]] # R
        registers[25] += 13 # T-states
        registers[24] = (pcn + 2) % 65536 # PC

    def ld_m_a(self, registers, memory):
        # LD (nn),A
        pcn = registers[24] + 1
        addr = memory[pcn % 65536] + 256 * memory[(pcn + 1) % 65536]
        if addr > 0x3FFF:
            memory[addr] = registers[0]
        registers[15] = R1[registers[15]] # R
        registers[25] += 13 # T-states
        registers[24] = (pcn + 2) % 65536 # PC

    def ld_rr_mm(self, registers, memory, r_inc, timing, size, rh, rl):
        # LD BC/DE/HL/SP/IX/IY,(nn)
        end = registers[24] + size
        addr = memory[(end - 2) % 65536] + 256 * memory[(end - 1) % 65536]
        if rl == 12:
            registers[12] = memory[addr] + 256 * memory[(addr + 1) % 65536]
        else:
            registers[rl] = memory[addr]
            registers[rh] = memory[(addr + 1) % 65536]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = end % 65536 # PC

    def ld_mm_rr(self, registers, memory, r_inc, timing, size, rh, rl):
        # LD (nn),BC/DE/HL/SP/IX/IY
        end = registers[24] + size
        addr = memory[(end - 2) % 65536] + 256 * memory[(end - 1) % 65536]
        if rl == 12:
            sp = registers[12]
            if addr > 0x3FFF:
                memory[addr] = sp % 256
            addr = (addr + 1) % 65536
            if addr > 0x3FFF:
                memory[addr] = sp // 256
        else:
            if addr > 0x3FFF:
                memory[addr] = registers[rl]
            addr = (addr + 1) % 65536
            if addr > 0x3FFF:
                memory[addr] = registers[rh]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = end % 65536 # PC

    def ldi(self, registers, memory, inc, repeat):
        # LDI / LDD / LDIR / LDDR
        hl = registers[7] + 256 * registers[6]
        de = registers[5] + 256 * registers[4]
        bc = registers[3] + 256 * registers[2]

        at_hl = memory[hl]
        if de > 0x3FFF:
            memory[de] = at_hl

        hl = (hl + inc) % 65536
        de = (de + inc) % 65536
        bc = (bc - 1) % 65536
        registers[7] = hl % 256
        registers[6] = hl // 256
        registers[5] = de % 256
        registers[4] = de // 256
        registers[3] = bc % 256
        registers[2] = bc // 256

        if repeat and bc:
            registers[1] = (registers[1] & 0xC1) + ((registers[24] // 256) & 0x28) + 0x04
            registers[25] += 21 # T-states
        else:
            n = registers[0] + at_hl
            registers[1] = (registers[1] & 0xC1) + (n & 0x02) * 16 + (n & 0x08) + (bc > 0) * 0x04
            registers[25] += 16 # T-states
            registers[24] = (registers[24] + 2) % 65536 # PC
        registers[15] = R2[registers[15]] # R

    def ldir_fast(self, registers, memory, inc):
        de = registers[5] + 256 * registers[4]
        bc = registers[3] + 256 * registers[2]
        hl = registers[7] + 256 * registers[6]
        count = 0
        repeat = True
        while repeat:
            if de > 0x3FFF:
                memory[de] = memory[hl]
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
        registers[15] = (r & 0x80) + ((r + 2 * count) % 128) # R
        if bc:
            registers[1] = (registers[1] & 0xC1) + ((registers[24] // 256) & 0x28) + 0x04
        else:
            n = registers[0] + memory[(hl - inc) % 65536]
            registers[1] = (registers[1] & 0xC1) + (n & 0x02) * 16 + (n & 0x08)
            registers[24] = (registers[24] + 2) % 65536 # PC
        registers[25] += 21 * count - 5 # T-states

    def ld_sp_rr(self, registers, r_inc, timing, size, rh, rl):
        # LD SP,HL/IX/IY
        registers[12] = registers[rl] + 256 * registers[rh]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = (registers[24] + size) % 65536 # PC

    def neg(self, registers, neg):
        # NEG
        registers[:2] = neg[registers[0]]
        registers[15] = R2[registers[15]] # R
        registers[25] += 8 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def nop(self, registers, r_inc, timing, size):
        # NOP and equivalents
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = (registers[24] + size) % 65536 # PC

    def out_a(self, registers, memory):
        # OUT (n),A
        pcn = registers[24] + 1
        if self.out_tracer:
            a = registers[0]
            self.out_tracer(memory[pcn % 65536] + 256 * a, a)
        registers[15] = R1[registers[15]] # R
        registers[25] += 11 # T-states
        registers[24] = (pcn + 1) % 65536 # PC

    def out_c(self, registers, reg):
        # OUT (C),r/0
        if self.out_tracer:
            if reg >= 0:
                self.out_tracer(registers[3] + 256 * registers[2], registers[reg])
            else:
                self.out_tracer(registers[3] + 256 * registers[2], 0)
        registers[15] = R2[registers[15]] # R
        registers[25] += 12 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def outi(self, registers, memory, inc, repeat, parity):
        # OUTI / OUTD / OTIR / OTDR
        hl = registers[7] + 256 * registers[6]
        b = (registers[2] - 1) % 256

        value = memory[hl]
        if self.out_tracer:
            self.out_tracer(registers[3] + 256 * b, value)
        hl = (hl + inc) % 65536
        l = hl % 256
        registers[7] = l
        registers[6] = hl // 256
        registers[2] = b

        j = l + value
        n = (value & 0x80) // 64
        c = j > 0xFF
        if repeat and b:
            if c:
                if n:
                    h = (b % 16 == 0) * 0x10
                    p = parity[(j % 8) ^ b ^ ((b - 1) % 8)]
                else:
                    h = (b % 16 == 15) * 0x10
                    p = parity[(j % 8) ^ b ^ ((b + 1) % 8)]
            else:
                h = 0
                p = parity[(j % 8) ^ b ^ (b % 8)]
            registers[1] = (b & 0x80) + ((registers[24] // 256) & 0x28) + h + p + n + c
            registers[25] += 21 # T-states
        else:
            registers[1] = (b & 0xA8) + (b == 0) * 0x40 + c * 0x11 + parity[(j % 8) ^ b] + n
            registers[24] = (registers[24] + 2) % 65536 # PC
            registers[25] += 16 # T-states
        registers[15] = R2[registers[15]] # R

    def pop(self, registers, memory, r_inc, timing, size, rh, rl):
        # POP AF/BC/DE/HL/IX/IY
        sp = registers[12]
        registers[12] = (sp + 2) % 65536
        registers[rl] = memory[sp]
        registers[rh] = memory[(sp + 1) % 65536]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = (registers[24] + size) % 65536 # PC

    def push(self, registers, memory, r_inc, timing, size, rh, rl):
        # PUSH AF/BC/DE/HL/IX/IY
        sp = (registers[12] - 2) % 65536
        registers[12] = sp
        if sp > 0x3FFF:
            memory[sp] = registers[rl]
        sp = (sp + 1) % 65536
        if sp > 0x3FFF:
            memory[sp] = registers[rh]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing # T-states
        registers[24] = (registers[24] + size) % 65536 # PC

    def res_hl(self, registers, memory, bit):
        # RES n,(HL)
        addr = registers[7] + 256 * registers[6]
        if addr > 0x3FFF:
            memory[addr] &= bit
        registers[15] = R2[registers[15]] # R
        registers[25] += 15 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def res_r(self, registers, bit, reg):
        # RES n,r
        registers[reg] &= bit
        registers[15] = R2[registers[15]] # R
        registers[25] += 8 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def res_xy(self, registers, memory, bit, xyh, xyl, dest=-1):
        # RES n,(IX/Y+d)
        addr = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[(registers[24] + 2) % 65536]]) % 65536
        value = memory[addr] & bit
        if addr > 0x3FFF:
            memory[addr] = value
        if dest >= 0:
            registers[dest] = value
        registers[15] = R2[registers[15]] # R
        registers[25] += 23 # T-states
        registers[24] = (registers[24] + 4) % 65536 # PC

    def ret(self, registers, memory, c_and, c_val):
        # RET / RET cc
        if c_and:
            if registers[1] & c_and == c_val:
                registers[25] += 5 # T-states
                registers[24] = (registers[24] + 1) % 65536 # PC
            else:
                registers[25] += 11 # T-states
                sp = registers[12]
                registers[12] = (sp + 2) % 65536
                registers[24] = memory[sp] + 256 * memory[(sp + 1) % 65536] # PC
        else:
            registers[25] += 10 # T-states
            sp = registers[12]
            registers[12] = (sp + 2) % 65536
            registers[24] = memory[sp] + 256 * memory[(sp + 1) % 65536] # PC
        registers[15] = R1[registers[15]] # R

    def reti(self, registers, memory):
        # RETI / RETN
        registers[15] = R2[registers[15]] # R
        registers[25] += 14 # T-states
        sp = registers[12]
        registers[12] = (sp + 2) % 65536
        registers[24] = memory[sp] + 256 * memory[(sp + 1) % 65536] # PC

    def rld(self, registers, memory, sz53p):
        # RLD
        hl = registers[7] + 256 * registers[6]
        a = registers[0]
        at_hl = memory[hl]
        if hl > 0x3FFF:
            memory[hl] = ((at_hl * 16) % 256) + (a % 16)
        a_out = registers[0] = (a & 240) + at_hl // 16
        registers[1] = sz53p[a_out] + (registers[1] % 2)
        registers[15] = R2[registers[15]] # R
        registers[25] += 18 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def rrd(self, registers, memory, sz53p):
        # RRD
        hl = registers[7] + 256 * registers[6]
        a = registers[0]
        at_hl = memory[hl]
        if hl > 0x3FFF:
            memory[hl] = ((a * 16) % 256) + (at_hl // 16)
        a_out = registers[0] = (a & 240) + (at_hl % 16)
        registers[1] = sz53p[a_out] + (registers[1] % 2)
        registers[15] = R2[registers[15]] # R
        registers[25] += 18 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def rst(self, registers, memory, addr):
        # RST n
        sp = (registers[12] - 2) % 65536
        registers[12] = sp
        ret_addr = (registers[24] + 1) % 65536
        if sp > 0x3FFF:
            memory[sp] = ret_addr % 256
        sp = (sp + 1) % 65536
        if sp > 0x3FFF:
            memory[sp] = ret_addr // 256
        registers[15] = R1[registers[15]] # R
        registers[25] += 11 # T-states
        registers[24] = addr # PC

    def sbc_hl(self, registers, rh, rl):
        # SBC HL,BC/DE/HL/SP
        rr = registers[rl] + 256 * registers[rh]
        hl = registers[7] + 256 * registers[6]
        rr_c = rr + (registers[1] % 2)
        result = (hl - rr_c) % 65536

        if hl < rr_c:
            f = 0x03 # ......NC
        else:
            f = 0x02 # ......N.
        if result == 0:
            f += 0x40 # .Z......
        if hl % 4096 < rr_c % 4096:
            f += 0x10 # ...H....
        if hl ^ rr > 0x7FFF and hl ^ result > 0x7FFF:
            # Minuend and subtrahend signs are different - overflow if the
            # minuend's sign differs from the sign of the result
            f += 0x04 # .....P..

        h = result // 256
        registers[1] = f + (h & 0xA8)
        registers[7] = result % 256
        registers[6] = h
        registers[15] = R2[registers[15]] # R
        registers[25] += 15 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def set_hl(self, registers, memory, bit):
        # SET n,(HL)
        addr = registers[7] + 256 * registers[6]
        if addr > 0x3FFF:
            memory[addr] |= bit
        registers[15] = R2[registers[15]] # R
        registers[25] += 15 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def set_r(self, registers, bit, reg):
        # SET n,r
        registers[reg] |= bit
        registers[15] = R2[registers[15]] # R
        registers[25] += 8 # T-states
        registers[24] = (registers[24] + 2) % 65536 # PC

    def set_xy(self, registers, memory, bit, xyh, xyl, dest=-1):
        # SET n,(IX/Y+d)
        addr = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[(registers[24] + 2) % 65536]]) % 65536
        value = memory[addr] | bit
        if addr > 0x3FFF:
            memory[addr] = value
        if dest >= 0:
            registers[dest] = value
        registers[15] = R2[registers[15]] # R
        registers[25] += 23 # T-states
        registers[24] = (registers[24] + 4) % 65536 # PC

    def create_opcodes(self):
        from skoolkit.simtables import (
            ADC, ADC_A_A, ADD, AND, BIT, CCF, CP, CPL, DAA, DEC, INC, NEG, OR,
            PARITY, RL, RLC, RR, RRC, RLA, RLCA, RRA, RRCA, SBC, SBC_A_A, SCF,
            SLA, SLL, SRA, SRL, SUB, SZ53P, XOR
        )
        r = self.registers
        m = self.memory

        self.after_DDCB = [
            partial(self.f_xy, r, m, RLC, IXh, IXl, B),             # DDCB..00 RLC (IX+d),B
            partial(self.f_xy, r, m, RLC, IXh, IXl, C),             # DDCB..01 RLC (IX+d),C
            partial(self.f_xy, r, m, RLC, IXh, IXl, D),             # DDCB..02 RLC (IX+d),D
            partial(self.f_xy, r, m, RLC, IXh, IXl, E),             # DDCB..03 RLC (IX+d),E
            partial(self.f_xy, r, m, RLC, IXh, IXl, H),             # DDCB..04 RLC (IX+d),H
            partial(self.f_xy, r, m, RLC, IXh, IXl, L),             # DDCB..05 RLC (IX+d),L
            partial(self.f_xy, r, m, RLC, IXh, IXl),                # DDCB..06 RLC (IX+d)
            partial(self.f_xy, r, m, RLC, IXh, IXl, A),             # DDCB..07 RLC (IX+d),A
            partial(self.f_xy, r, m, RRC, IXh, IXl, B),             # DDCB..08 RRC (IX+d),B
            partial(self.f_xy, r, m, RRC, IXh, IXl, C),             # DDCB..09 RRC (IX+d),C
            partial(self.f_xy, r, m, RRC, IXh, IXl, D),             # DDCB..0A RRC (IX+d),D
            partial(self.f_xy, r, m, RRC, IXh, IXl, E),             # DDCB..0B RRC (IX+d),E
            partial(self.f_xy, r, m, RRC, IXh, IXl, H),             # DDCB..0C RRC (IX+d),H
            partial(self.f_xy, r, m, RRC, IXh, IXl, L),             # DDCB..0D RRC (IX+d),L
            partial(self.f_xy, r, m, RRC, IXh, IXl),                # DDCB..0E RRC (IX+d)
            partial(self.f_xy, r, m, RRC, IXh, IXl, A),             # DDCB..0F RRC (IX+d),A
            partial(self.fc_xy, r, m, 4, RL, IXh, IXl, B),          # DDCB..10 RL (IX+d),B
            partial(self.fc_xy, r, m, 4, RL, IXh, IXl, C),          # DDCB..11 RL (IX+d),C
            partial(self.fc_xy, r, m, 4, RL, IXh, IXl, D),          # DDCB..12 RL (IX+d),D
            partial(self.fc_xy, r, m, 4, RL, IXh, IXl, E),          # DDCB..13 RL (IX+d),E
            partial(self.fc_xy, r, m, 4, RL, IXh, IXl, H),          # DDCB..14 RL (IX+d),H
            partial(self.fc_xy, r, m, 4, RL, IXh, IXl, L),          # DDCB..15 RL (IX+d),L
            partial(self.fc_xy, r, m, 4, RL, IXh, IXl),             # DDCB..16 RL (IX+d)
            partial(self.fc_xy, r, m, 4, RL, IXh, IXl, A),          # DDCB..17 RL (IX+d),A
            partial(self.fc_xy, r, m, 4, RR, IXh, IXl, B),          # DDCB..18 RR (IX+d),B
            partial(self.fc_xy, r, m, 4, RR, IXh, IXl, C),          # DDCB..19 RR (IX+d),C
            partial(self.fc_xy, r, m, 4, RR, IXh, IXl, D),          # DDCB..1A RR (IX+d),D
            partial(self.fc_xy, r, m, 4, RR, IXh, IXl, E),          # DDCB..1B RR (IX+d),E
            partial(self.fc_xy, r, m, 4, RR, IXh, IXl, H),          # DDCB..1C RR (IX+d),H
            partial(self.fc_xy, r, m, 4, RR, IXh, IXl, L),          # DDCB..1D RR (IX+d),L
            partial(self.fc_xy, r, m, 4, RR, IXh, IXl),             # DDCB..1E RR (IX+d)
            partial(self.fc_xy, r, m, 4, RR, IXh, IXl, A),          # DDCB..1F RR (IX+d),A
            partial(self.f_xy, r, m, SLA, IXh, IXl, B),             # DDCB..20 SLA (IX+d),B
            partial(self.f_xy, r, m, SLA, IXh, IXl, C),             # DDCB..21 SLA (IX+d),C
            partial(self.f_xy, r, m, SLA, IXh, IXl, D),             # DDCB..22 SLA (IX+d),D
            partial(self.f_xy, r, m, SLA, IXh, IXl, E),             # DDCB..23 SLA (IX+d),E
            partial(self.f_xy, r, m, SLA, IXh, IXl, H),             # DDCB..24 SLA (IX+d),H
            partial(self.f_xy, r, m, SLA, IXh, IXl, L),             # DDCB..25 SLA (IX+d),L
            partial(self.f_xy, r, m, SLA, IXh, IXl),                # DDCB..26 SLA (IX+d)
            partial(self.f_xy, r, m, SLA, IXh, IXl, A),             # DDCB..27 SLA (IX+d),A
            partial(self.f_xy, r, m, SRA, IXh, IXl, B),             # DDCB..28 SRA (IX+d),B
            partial(self.f_xy, r, m, SRA, IXh, IXl, C),             # DDCB..29 SRA (IX+d),C
            partial(self.f_xy, r, m, SRA, IXh, IXl, D),             # DDCB..2A SRA (IX+d),D
            partial(self.f_xy, r, m, SRA, IXh, IXl, E),             # DDCB..2B SRA (IX+d),E
            partial(self.f_xy, r, m, SRA, IXh, IXl, H),             # DDCB..2C SRA (IX+d),H
            partial(self.f_xy, r, m, SRA, IXh, IXl, L),             # DDCB..2D SRA (IX+d),L
            partial(self.f_xy, r, m, SRA, IXh, IXl),                # DDCB..2E SRA (IX+d)
            partial(self.f_xy, r, m, SRA, IXh, IXl, A),             # DDCB..2F SRA (IX+d),A
            partial(self.f_xy, r, m, SLL, IXh, IXl, B),             # DDCB..30 SLL (IX+d),B
            partial(self.f_xy, r, m, SLL, IXh, IXl, C),             # DDCB..31 SLL (IX+d),C
            partial(self.f_xy, r, m, SLL, IXh, IXl, D),             # DDCB..32 SLL (IX+d),D
            partial(self.f_xy, r, m, SLL, IXh, IXl, E),             # DDCB..33 SLL (IX+d),E
            partial(self.f_xy, r, m, SLL, IXh, IXl, H),             # DDCB..34 SLL (IX+d),H
            partial(self.f_xy, r, m, SLL, IXh, IXl, L),             # DDCB..35 SLL (IX+d),L
            partial(self.f_xy, r, m, SLL, IXh, IXl),                # DDCB..36 SLL (IX+d)
            partial(self.f_xy, r, m, SLL, IXh, IXl, A),             # DDCB..37 SLL (IX+d),A
            partial(self.f_xy, r, m, SRL, IXh, IXl, B),             # DDCB..38 SRL (IX+d),B
            partial(self.f_xy, r, m, SRL, IXh, IXl, C),             # DDCB..39 SRL (IX+d),C
            partial(self.f_xy, r, m, SRL, IXh, IXl, D),             # DDCB..3A SRL (IX+d),D
            partial(self.f_xy, r, m, SRL, IXh, IXl, E),             # DDCB..3B SRL (IX+d),E
            partial(self.f_xy, r, m, SRL, IXh, IXl, H),             # DDCB..3C SRL (IX+d),H
            partial(self.f_xy, r, m, SRL, IXh, IXl, L),             # DDCB..3D SRL (IX+d),L
            partial(self.f_xy, r, m, SRL, IXh, IXl),                # DDCB..3E SRL (IX+d)
            partial(self.f_xy, r, m, SRL, IXh, IXl, A),             # DDCB..3F SRL (IX+d),A
            partial(self.bit_xy, r, m, BIT, 0, IXh, IXl),           # DDCB..40 BIT 0,(IX+d)
            partial(self.bit_xy, r, m, BIT, 0, IXh, IXl),           # DDCB..41 BIT 0,(IX+d)
            partial(self.bit_xy, r, m, BIT, 0, IXh, IXl),           # DDCB..42 BIT 0,(IX+d)
            partial(self.bit_xy, r, m, BIT, 0, IXh, IXl),           # DDCB..43 BIT 0,(IX+d)
            partial(self.bit_xy, r, m, BIT, 0, IXh, IXl),           # DDCB..44 BIT 0,(IX+d)
            partial(self.bit_xy, r, m, BIT, 0, IXh, IXl),           # DDCB..45 BIT 0,(IX+d)
            partial(self.bit_xy, r, m, BIT, 0, IXh, IXl),           # DDCB..46 BIT 0,(IX+d)
            partial(self.bit_xy, r, m, BIT, 0, IXh, IXl),           # DDCB..47 BIT 0,(IX+d)
            partial(self.bit_xy, r, m, BIT, 1, IXh, IXl),           # DDCB..48 BIT 1,(IX+d)
            partial(self.bit_xy, r, m, BIT, 1, IXh, IXl),           # DDCB..49 BIT 1,(IX+d)
            partial(self.bit_xy, r, m, BIT, 1, IXh, IXl),           # DDCB..4A BIT 1,(IX+d)
            partial(self.bit_xy, r, m, BIT, 1, IXh, IXl),           # DDCB..4B BIT 1,(IX+d)
            partial(self.bit_xy, r, m, BIT, 1, IXh, IXl),           # DDCB..4C BIT 1,(IX+d)
            partial(self.bit_xy, r, m, BIT, 1, IXh, IXl),           # DDCB..4D BIT 1,(IX+d)
            partial(self.bit_xy, r, m, BIT, 1, IXh, IXl),           # DDCB..4E BIT 1,(IX+d)
            partial(self.bit_xy, r, m, BIT, 1, IXh, IXl),           # DDCB..4F BIT 1,(IX+d)
            partial(self.bit_xy, r, m, BIT, 2, IXh, IXl),           # DDCB..50 BIT 2,(IX+d)
            partial(self.bit_xy, r, m, BIT, 2, IXh, IXl),           # DDCB..51 BIT 2,(IX+d)
            partial(self.bit_xy, r, m, BIT, 2, IXh, IXl),           # DDCB..52 BIT 2,(IX+d)
            partial(self.bit_xy, r, m, BIT, 2, IXh, IXl),           # DDCB..53 BIT 2,(IX+d)
            partial(self.bit_xy, r, m, BIT, 2, IXh, IXl),           # DDCB..54 BIT 2,(IX+d)
            partial(self.bit_xy, r, m, BIT, 2, IXh, IXl),           # DDCB..55 BIT 2,(IX+d)
            partial(self.bit_xy, r, m, BIT, 2, IXh, IXl),           # DDCB..56 BIT 2,(IX+d)
            partial(self.bit_xy, r, m, BIT, 2, IXh, IXl),           # DDCB..57 BIT 2,(IX+d)
            partial(self.bit_xy, r, m, BIT, 3, IXh, IXl),           # DDCB..58 BIT 3,(IX+d)
            partial(self.bit_xy, r, m, BIT, 3, IXh, IXl),           # DDCB..59 BIT 3,(IX+d)
            partial(self.bit_xy, r, m, BIT, 3, IXh, IXl),           # DDCB..5A BIT 3,(IX+d)
            partial(self.bit_xy, r, m, BIT, 3, IXh, IXl),           # DDCB..5B BIT 3,(IX+d)
            partial(self.bit_xy, r, m, BIT, 3, IXh, IXl),           # DDCB..5C BIT 3,(IX+d)
            partial(self.bit_xy, r, m, BIT, 3, IXh, IXl),           # DDCB..5D BIT 3,(IX+d)
            partial(self.bit_xy, r, m, BIT, 3, IXh, IXl),           # DDCB..5E BIT 3,(IX+d)
            partial(self.bit_xy, r, m, BIT, 3, IXh, IXl),           # DDCB..5F BIT 3,(IX+d)
            partial(self.bit_xy, r, m, BIT, 4, IXh, IXl),           # DDCB..60 BIT 4,(IX+d)
            partial(self.bit_xy, r, m, BIT, 4, IXh, IXl),           # DDCB..61 BIT 4,(IX+d)
            partial(self.bit_xy, r, m, BIT, 4, IXh, IXl),           # DDCB..62 BIT 4,(IX+d)
            partial(self.bit_xy, r, m, BIT, 4, IXh, IXl),           # DDCB..63 BIT 4,(IX+d)
            partial(self.bit_xy, r, m, BIT, 4, IXh, IXl),           # DDCB..64 BIT 4,(IX+d)
            partial(self.bit_xy, r, m, BIT, 4, IXh, IXl),           # DDCB..65 BIT 4,(IX+d)
            partial(self.bit_xy, r, m, BIT, 4, IXh, IXl),           # DDCB..66 BIT 4,(IX+d)
            partial(self.bit_xy, r, m, BIT, 4, IXh, IXl),           # DDCB..67 BIT 4,(IX+d)
            partial(self.bit_xy, r, m, BIT, 5, IXh, IXl),           # DDCB..68 BIT 5,(IX+d)
            partial(self.bit_xy, r, m, BIT, 5, IXh, IXl),           # DDCB..69 BIT 5,(IX+d)
            partial(self.bit_xy, r, m, BIT, 5, IXh, IXl),           # DDCB..6A BIT 5,(IX+d)
            partial(self.bit_xy, r, m, BIT, 5, IXh, IXl),           # DDCB..6B BIT 5,(IX+d)
            partial(self.bit_xy, r, m, BIT, 5, IXh, IXl),           # DDCB..6C BIT 5,(IX+d)
            partial(self.bit_xy, r, m, BIT, 5, IXh, IXl),           # DDCB..6D BIT 5,(IX+d)
            partial(self.bit_xy, r, m, BIT, 5, IXh, IXl),           # DDCB..6E BIT 5,(IX+d)
            partial(self.bit_xy, r, m, BIT, 5, IXh, IXl),           # DDCB..6F BIT 5,(IX+d)
            partial(self.bit_xy, r, m, BIT, 6, IXh, IXl),           # DDCB..70 BIT 6,(IX+d)
            partial(self.bit_xy, r, m, BIT, 6, IXh, IXl),           # DDCB..71 BIT 6,(IX+d)
            partial(self.bit_xy, r, m, BIT, 6, IXh, IXl),           # DDCB..72 BIT 6,(IX+d)
            partial(self.bit_xy, r, m, BIT, 6, IXh, IXl),           # DDCB..73 BIT 6,(IX+d)
            partial(self.bit_xy, r, m, BIT, 6, IXh, IXl),           # DDCB..74 BIT 6,(IX+d)
            partial(self.bit_xy, r, m, BIT, 6, IXh, IXl),           # DDCB..75 BIT 6,(IX+d)
            partial(self.bit_xy, r, m, BIT, 6, IXh, IXl),           # DDCB..76 BIT 6,(IX+d)
            partial(self.bit_xy, r, m, BIT, 6, IXh, IXl),           # DDCB..77 BIT 6,(IX+d)
            partial(self.bit_xy, r, m, BIT, 7, IXh, IXl),           # DDCB..78 BIT 7,(IX+d)
            partial(self.bit_xy, r, m, BIT, 7, IXh, IXl),           # DDCB..79 BIT 7,(IX+d)
            partial(self.bit_xy, r, m, BIT, 7, IXh, IXl),           # DDCB..7A BIT 7,(IX+d)
            partial(self.bit_xy, r, m, BIT, 7, IXh, IXl),           # DDCB..7B BIT 7,(IX+d)
            partial(self.bit_xy, r, m, BIT, 7, IXh, IXl),           # DDCB..7C BIT 7,(IX+d)
            partial(self.bit_xy, r, m, BIT, 7, IXh, IXl),           # DDCB..7D BIT 7,(IX+d)
            partial(self.bit_xy, r, m, BIT, 7, IXh, IXl),           # DDCB..7E BIT 7,(IX+d)
            partial(self.bit_xy, r, m, BIT, 7, IXh, IXl),           # DDCB..7F BIT 7,(IX+d)
            partial(self.res_xy, r, m, 254, IXh, IXl, B),           # DDCB..80 RES 0,(IX+d),B
            partial(self.res_xy, r, m, 254, IXh, IXl, C),           # DDCB..81 RES 0,(IX+d),C
            partial(self.res_xy, r, m, 254, IXh, IXl, D),           # DDCB..82 RES 0,(IX+d),D
            partial(self.res_xy, r, m, 254, IXh, IXl, E),           # DDCB..83 RES 0,(IX+d),E
            partial(self.res_xy, r, m, 254, IXh, IXl, H),           # DDCB..84 RES 0,(IX+d),H
            partial(self.res_xy, r, m, 254, IXh, IXl, L),           # DDCB..85 RES 0,(IX+d),L
            partial(self.res_xy, r, m, 254, IXh, IXl),              # DDCB..86 RES 0,(IX+d)
            partial(self.res_xy, r, m, 254, IXh, IXl, A),           # DDCB..87 RES 0,(IX+d),A
            partial(self.res_xy, r, m, 253, IXh, IXl, B),           # DDCB..88 RES 1,(IX+d),B
            partial(self.res_xy, r, m, 253, IXh, IXl, C),           # DDCB..89 RES 1,(IX+d),C
            partial(self.res_xy, r, m, 253, IXh, IXl, D),           # DDCB..8A RES 1,(IX+d),D
            partial(self.res_xy, r, m, 253, IXh, IXl, E),           # DDCB..8B RES 1,(IX+d),E
            partial(self.res_xy, r, m, 253, IXh, IXl, H),           # DDCB..8C RES 1,(IX+d),H
            partial(self.res_xy, r, m, 253, IXh, IXl, L),           # DDCB..8D RES 1,(IX+d),L
            partial(self.res_xy, r, m, 253, IXh, IXl),              # DDCB..8E RES 1,(IX+d)
            partial(self.res_xy, r, m, 253, IXh, IXl, A),           # DDCB..8F RES 1,(IX+d),A
            partial(self.res_xy, r, m, 251, IXh, IXl, B),           # DDCB..90 RES 2,(IX+d),B
            partial(self.res_xy, r, m, 251, IXh, IXl, C),           # DDCB..91 RES 2,(IX+d),C
            partial(self.res_xy, r, m, 251, IXh, IXl, D),           # DDCB..92 RES 2,(IX+d),D
            partial(self.res_xy, r, m, 251, IXh, IXl, E),           # DDCB..93 RES 2,(IX+d),E
            partial(self.res_xy, r, m, 251, IXh, IXl, H),           # DDCB..94 RES 2,(IX+d),H
            partial(self.res_xy, r, m, 251, IXh, IXl, L),           # DDCB..95 RES 2,(IX+d),L
            partial(self.res_xy, r, m, 251, IXh, IXl),              # DDCB..96 RES 2,(IX+d)
            partial(self.res_xy, r, m, 251, IXh, IXl, A),           # DDCB..97 RES 2,(IX+d),A
            partial(self.res_xy, r, m, 247, IXh, IXl, B),           # DDCB..98 RES 3,(IX+d),B
            partial(self.res_xy, r, m, 247, IXh, IXl, C),           # DDCB..99 RES 3,(IX+d),C
            partial(self.res_xy, r, m, 247, IXh, IXl, D),           # DDCB..9A RES 3,(IX+d),D
            partial(self.res_xy, r, m, 247, IXh, IXl, E),           # DDCB..9B RES 3,(IX+d),E
            partial(self.res_xy, r, m, 247, IXh, IXl, H),           # DDCB..9C RES 3,(IX+d),H
            partial(self.res_xy, r, m, 247, IXh, IXl, L),           # DDCB..9D RES 3,(IX+d),L
            partial(self.res_xy, r, m, 247, IXh, IXl),              # DDCB..9E RES 3,(IX+d)
            partial(self.res_xy, r, m, 247, IXh, IXl, A),           # DDCB..9F RES 3,(IX+d),A
            partial(self.res_xy, r, m, 239, IXh, IXl, B),           # DDCB..A0 RES 4,(IX+d),B
            partial(self.res_xy, r, m, 239, IXh, IXl, C),           # DDCB..A1 RES 4,(IX+d),C
            partial(self.res_xy, r, m, 239, IXh, IXl, D),           # DDCB..A2 RES 4,(IX+d),D
            partial(self.res_xy, r, m, 239, IXh, IXl, E),           # DDCB..A3 RES 4,(IX+d),E
            partial(self.res_xy, r, m, 239, IXh, IXl, H),           # DDCB..A4 RES 4,(IX+d),H
            partial(self.res_xy, r, m, 239, IXh, IXl, L),           # DDCB..A5 RES 4,(IX+d),L
            partial(self.res_xy, r, m, 239, IXh, IXl),              # DDCB..A6 RES 4,(IX+d)
            partial(self.res_xy, r, m, 239, IXh, IXl, A),           # DDCB..A7 RES 4,(IX+d),A
            partial(self.res_xy, r, m, 223, IXh, IXl, B),           # DDCB..A8 RES 5,(IX+d),B
            partial(self.res_xy, r, m, 223, IXh, IXl, C),           # DDCB..A9 RES 5,(IX+d),C
            partial(self.res_xy, r, m, 223, IXh, IXl, D),           # DDCB..AA RES 5,(IX+d),D
            partial(self.res_xy, r, m, 223, IXh, IXl, E),           # DDCB..AB RES 5,(IX+d),E
            partial(self.res_xy, r, m, 223, IXh, IXl, H),           # DDCB..AC RES 5,(IX+d),H
            partial(self.res_xy, r, m, 223, IXh, IXl, L),           # DDCB..AD RES 5,(IX+d),L
            partial(self.res_xy, r, m, 223, IXh, IXl),              # DDCB..AE RES 5,(IX+d)
            partial(self.res_xy, r, m, 223, IXh, IXl, A),           # DDCB..AF RES 5,(IX+d),A
            partial(self.res_xy, r, m, 191, IXh, IXl, B),           # DDCB..B0 RES 6,(IX+d),B
            partial(self.res_xy, r, m, 191, IXh, IXl, C),           # DDCB..B1 RES 6,(IX+d),C
            partial(self.res_xy, r, m, 191, IXh, IXl, D),           # DDCB..B2 RES 6,(IX+d),D
            partial(self.res_xy, r, m, 191, IXh, IXl, E),           # DDCB..B3 RES 6,(IX+d),E
            partial(self.res_xy, r, m, 191, IXh, IXl, H),           # DDCB..B4 RES 6,(IX+d),H
            partial(self.res_xy, r, m, 191, IXh, IXl, L),           # DDCB..B5 RES 6,(IX+d),L
            partial(self.res_xy, r, m, 191, IXh, IXl),              # DDCB..B6 RES 6,(IX+d)
            partial(self.res_xy, r, m, 191, IXh, IXl, A),           # DDCB..B7 RES 6,(IX+d),A
            partial(self.res_xy, r, m, 127, IXh, IXl, B),           # DDCB..B8 RES 7,(IX+d),B
            partial(self.res_xy, r, m, 127, IXh, IXl, C),           # DDCB..B9 RES 7,(IX+d),C
            partial(self.res_xy, r, m, 127, IXh, IXl, D),           # DDCB..BA RES 7,(IX+d),D
            partial(self.res_xy, r, m, 127, IXh, IXl, E),           # DDCB..BB RES 7,(IX+d),E
            partial(self.res_xy, r, m, 127, IXh, IXl, H),           # DDCB..BC RES 7,(IX+d),H
            partial(self.res_xy, r, m, 127, IXh, IXl, L),           # DDCB..BD RES 7,(IX+d),L
            partial(self.res_xy, r, m, 127, IXh, IXl),              # DDCB..BE RES 7,(IX+d)
            partial(self.res_xy, r, m, 127, IXh, IXl, A),           # DDCB..BF RES 7,(IX+d),A
            partial(self.set_xy, r, m, 1, IXh, IXl, B),             # DDCB..C0 SET 0,(IX+d),B
            partial(self.set_xy, r, m, 1, IXh, IXl, C),             # DDCB..C1 SET 0,(IX+d),C
            partial(self.set_xy, r, m, 1, IXh, IXl, D),             # DDCB..C2 SET 0,(IX+d),D
            partial(self.set_xy, r, m, 1, IXh, IXl, E),             # DDCB..C3 SET 0,(IX+d),E
            partial(self.set_xy, r, m, 1, IXh, IXl, H),             # DDCB..C4 SET 0,(IX+d),H
            partial(self.set_xy, r, m, 1, IXh, IXl, L),             # DDCB..C5 SET 0,(IX+d),L
            partial(self.set_xy, r, m, 1, IXh, IXl),                # DDCB..C6 SET 0,(IX+d)
            partial(self.set_xy, r, m, 1, IXh, IXl, A),             # DDCB..C7 SET 0,(IX+d),A
            partial(self.set_xy, r, m, 2, IXh, IXl, B),             # DDCB..C8 SET 1,(IX+d),B
            partial(self.set_xy, r, m, 2, IXh, IXl, C),             # DDCB..C9 SET 1,(IX+d),C
            partial(self.set_xy, r, m, 2, IXh, IXl, D),             # DDCB..CA SET 1,(IX+d),D
            partial(self.set_xy, r, m, 2, IXh, IXl, E),             # DDCB..CB SET 1,(IX+d),E
            partial(self.set_xy, r, m, 2, IXh, IXl, H),             # DDCB..CC SET 1,(IX+d),H
            partial(self.set_xy, r, m, 2, IXh, IXl, L),             # DDCB..CD SET 1,(IX+d),L
            partial(self.set_xy, r, m, 2, IXh, IXl),                # DDCB..CE SET 1,(IX+d)
            partial(self.set_xy, r, m, 2, IXh, IXl, A),             # DDCB..CF SET 1,(IX+d),A
            partial(self.set_xy, r, m, 4, IXh, IXl, B),             # DDCB..D0 SET 2,(IX+d),B
            partial(self.set_xy, r, m, 4, IXh, IXl, C),             # DDCB..D1 SET 2,(IX+d),C
            partial(self.set_xy, r, m, 4, IXh, IXl, D),             # DDCB..D2 SET 2,(IX+d),D
            partial(self.set_xy, r, m, 4, IXh, IXl, E),             # DDCB..D3 SET 2,(IX+d),E
            partial(self.set_xy, r, m, 4, IXh, IXl, H),             # DDCB..D4 SET 2,(IX+d),H
            partial(self.set_xy, r, m, 4, IXh, IXl, L),             # DDCB..D5 SET 2,(IX+d),L
            partial(self.set_xy, r, m, 4, IXh, IXl),                # DDCB..D6 SET 2,(IX+d)
            partial(self.set_xy, r, m, 4, IXh, IXl, A),             # DDCB..D7 SET 2,(IX+d),A
            partial(self.set_xy, r, m, 8, IXh, IXl, B),             # DDCB..D8 SET 3,(IX+d),B
            partial(self.set_xy, r, m, 8, IXh, IXl, C),             # DDCB..D9 SET 3,(IX+d),C
            partial(self.set_xy, r, m, 8, IXh, IXl, D),             # DDCB..DA SET 3,(IX+d),D
            partial(self.set_xy, r, m, 8, IXh, IXl, E),             # DDCB..DB SET 3,(IX+d),E
            partial(self.set_xy, r, m, 8, IXh, IXl, H),             # DDCB..DC SET 3,(IX+d),H
            partial(self.set_xy, r, m, 8, IXh, IXl, L),             # DDCB..DD SET 3,(IX+d),L
            partial(self.set_xy, r, m, 8, IXh, IXl),                # DDCB..DE SET 3,(IX+d)
            partial(self.set_xy, r, m, 8, IXh, IXl, A),             # DDCB..DF SET 3,(IX+d),A
            partial(self.set_xy, r, m, 16, IXh, IXl, B),            # DDCB..E0 SET 4,(IX+d),B
            partial(self.set_xy, r, m, 16, IXh, IXl, C),            # DDCB..E1 SET 4,(IX+d),C
            partial(self.set_xy, r, m, 16, IXh, IXl, D),            # DDCB..E2 SET 4,(IX+d),D
            partial(self.set_xy, r, m, 16, IXh, IXl, E),            # DDCB..E3 SET 4,(IX+d),E
            partial(self.set_xy, r, m, 16, IXh, IXl, H),            # DDCB..E4 SET 4,(IX+d),H
            partial(self.set_xy, r, m, 16, IXh, IXl, L),            # DDCB..E5 SET 4,(IX+d),L
            partial(self.set_xy, r, m, 16, IXh, IXl),               # DDCB..E6 SET 4,(IX+d)
            partial(self.set_xy, r, m, 16, IXh, IXl, A),            # DDCB..E7 SET 4,(IX+d),A
            partial(self.set_xy, r, m, 32, IXh, IXl, B),            # DDCB..E8 SET 5,(IX+d),B
            partial(self.set_xy, r, m, 32, IXh, IXl, C),            # DDCB..E9 SET 5,(IX+d),C
            partial(self.set_xy, r, m, 32, IXh, IXl, D),            # DDCB..EA SET 5,(IX+d),D
            partial(self.set_xy, r, m, 32, IXh, IXl, E),            # DDCB..EB SET 5,(IX+d),E
            partial(self.set_xy, r, m, 32, IXh, IXl, H),            # DDCB..EC SET 5,(IX+d),H
            partial(self.set_xy, r, m, 32, IXh, IXl, L),            # DDCB..ED SET 5,(IX+d),L
            partial(self.set_xy, r, m, 32, IXh, IXl),               # DDCB..EE SET 5,(IX+d)
            partial(self.set_xy, r, m, 32, IXh, IXl, A),            # DDCB..EF SET 5,(IX+d),A
            partial(self.set_xy, r, m, 64, IXh, IXl, B),            # DDCB..F0 SET 6,(IX+d),B
            partial(self.set_xy, r, m, 64, IXh, IXl, C),            # DDCB..F1 SET 6,(IX+d),C
            partial(self.set_xy, r, m, 64, IXh, IXl, D),            # DDCB..F2 SET 6,(IX+d),D
            partial(self.set_xy, r, m, 64, IXh, IXl, E),            # DDCB..F3 SET 6,(IX+d),E
            partial(self.set_xy, r, m, 64, IXh, IXl, H),            # DDCB..F4 SET 6,(IX+d),H
            partial(self.set_xy, r, m, 64, IXh, IXl, L),            # DDCB..F5 SET 6,(IX+d),L
            partial(self.set_xy, r, m, 64, IXh, IXl),               # DDCB..F6 SET 6,(IX+d)
            partial(self.set_xy, r, m, 64, IXh, IXl, A),            # DDCB..F7 SET 6,(IX+d),A
            partial(self.set_xy, r, m, 128, IXh, IXl, B),           # DDCB..F8 SET 7,(IX+d),B
            partial(self.set_xy, r, m, 128, IXh, IXl, C),           # DDCB..F9 SET 7,(IX+d),C
            partial(self.set_xy, r, m, 128, IXh, IXl, D),           # DDCB..FA SET 7,(IX+d),D
            partial(self.set_xy, r, m, 128, IXh, IXl, E),           # DDCB..FB SET 7,(IX+d),E
            partial(self.set_xy, r, m, 128, IXh, IXl, H),           # DDCB..FC SET 7,(IX+d),H
            partial(self.set_xy, r, m, 128, IXh, IXl, L),           # DDCB..FD SET 7,(IX+d),L
            partial(self.set_xy, r, m, 128, IXh, IXl),              # DDCB..FE SET 7,(IX+d)
            partial(self.set_xy, r, m, 128, IXh, IXl, A),           # DDCB..FF SET 7,(IX+d),A
        ]

        self.after_FDCB = [
            partial(self.f_xy, r, m, RLC, IYh, IYl, B),             # FDCB..00 RLC (IY+d),B
            partial(self.f_xy, r, m, RLC, IYh, IYl, C),             # FDCB..01 RLC (IY+d),C
            partial(self.f_xy, r, m, RLC, IYh, IYl, D),             # FDCB..02 RLC (IY+d),D
            partial(self.f_xy, r, m, RLC, IYh, IYl, E),             # FDCB..03 RLC (IY+d),E
            partial(self.f_xy, r, m, RLC, IYh, IYl, H),             # FDCB..04 RLC (IY+d),H
            partial(self.f_xy, r, m, RLC, IYh, IYl, L),             # FDCB..05 RLC (IY+d),L
            partial(self.f_xy, r, m, RLC, IYh, IYl),                # FDCB..06 RLC (IY+d)
            partial(self.f_xy, r, m, RLC, IYh, IYl, A),             # FDCB..07 RLC (IY+d),A
            partial(self.f_xy, r, m, RRC, IYh, IYl, B),             # FDCB..08 RRC (IY+d),B
            partial(self.f_xy, r, m, RRC, IYh, IYl, C),             # FDCB..09 RRC (IY+d),C
            partial(self.f_xy, r, m, RRC, IYh, IYl, D),             # FDCB..0A RRC (IY+d),D
            partial(self.f_xy, r, m, RRC, IYh, IYl, E),             # FDCB..0B RRC (IY+d),E
            partial(self.f_xy, r, m, RRC, IYh, IYl, H),             # FDCB..0C RRC (IY+d),H
            partial(self.f_xy, r, m, RRC, IYh, IYl, L),             # FDCB..0D RRC (IY+d),L
            partial(self.f_xy, r, m, RRC, IYh, IYl),                # FDCB..0E RRC (IY+d)
            partial(self.f_xy, r, m, RRC, IYh, IYl, A),             # FDCB..0F RRC (IY+d),A
            partial(self.fc_xy, r, m, 4, RL, IYh, IYl, B),          # FDCB..10 RL (IY+d),B
            partial(self.fc_xy, r, m, 4, RL, IYh, IYl, C),          # FDCB..11 RL (IY+d),C
            partial(self.fc_xy, r, m, 4, RL, IYh, IYl, D),          # FDCB..12 RL (IY+d),D
            partial(self.fc_xy, r, m, 4, RL, IYh, IYl, E),          # FDCB..13 RL (IY+d),E
            partial(self.fc_xy, r, m, 4, RL, IYh, IYl, H),          # FDCB..14 RL (IY+d),H
            partial(self.fc_xy, r, m, 4, RL, IYh, IYl, L),          # FDCB..15 RL (IY+d),L
            partial(self.fc_xy, r, m, 4, RL, IYh, IYl),             # FDCB..16 RL (IY+d)
            partial(self.fc_xy, r, m, 4, RL, IYh, IYl, A),          # FDCB..17 RL (IY+d),A
            partial(self.fc_xy, r, m, 4, RR, IYh, IYl, B),          # FDCB..18 RR (IY+d),B
            partial(self.fc_xy, r, m, 4, RR, IYh, IYl, C),          # FDCB..19 RR (IY+d),C
            partial(self.fc_xy, r, m, 4, RR, IYh, IYl, D),          # FDCB..1A RR (IY+d),D
            partial(self.fc_xy, r, m, 4, RR, IYh, IYl, E),          # FDCB..1B RR (IY+d),E
            partial(self.fc_xy, r, m, 4, RR, IYh, IYl, H),          # FDCB..1C RR (IY+d),H
            partial(self.fc_xy, r, m, 4, RR, IYh, IYl, L),          # FDCB..1D RR (IY+d),L
            partial(self.fc_xy, r, m, 4, RR, IYh, IYl),             # FDCB..1E RR (IY+d)
            partial(self.fc_xy, r, m, 4, RR, IYh, IYl, A),          # FDCB..1F RR (IY+d),A
            partial(self.f_xy, r, m, SLA, IYh, IYl, B),             # FDCB..20 SLA (IY+d),B
            partial(self.f_xy, r, m, SLA, IYh, IYl, C),             # FDCB..21 SLA (IY+d),C
            partial(self.f_xy, r, m, SLA, IYh, IYl, D),             # FDCB..22 SLA (IY+d),D
            partial(self.f_xy, r, m, SLA, IYh, IYl, E),             # FDCB..23 SLA (IY+d),E
            partial(self.f_xy, r, m, SLA, IYh, IYl, H),             # FDCB..24 SLA (IY+d),H
            partial(self.f_xy, r, m, SLA, IYh, IYl, L),             # FDCB..25 SLA (IY+d),L
            partial(self.f_xy, r, m, SLA, IYh, IYl),                # FDCB..26 SLA (IY+d)
            partial(self.f_xy, r, m, SLA, IYh, IYl, A),             # FDCB..27 SLA (IY+d),A
            partial(self.f_xy, r, m, SRA, IYh, IYl, B),             # FDCB..28 SRA (IY+d),B
            partial(self.f_xy, r, m, SRA, IYh, IYl, C),             # FDCB..29 SRA (IY+d),C
            partial(self.f_xy, r, m, SRA, IYh, IYl, D),             # FDCB..2A SRA (IY+d),D
            partial(self.f_xy, r, m, SRA, IYh, IYl, E),             # FDCB..2B SRA (IY+d),E
            partial(self.f_xy, r, m, SRA, IYh, IYl, H),             # FDCB..2C SRA (IY+d),H
            partial(self.f_xy, r, m, SRA, IYh, IYl, L),             # FDCB..2D SRA (IY+d),L
            partial(self.f_xy, r, m, SRA, IYh, IYl),                # FDCB..2E SRA (IY+d)
            partial(self.f_xy, r, m, SRA, IYh, IYl, A),             # FDCB..2F SRA (IY+d),A
            partial(self.f_xy, r, m, SLL, IYh, IYl, B),             # FDCB..30 SLL (IY+d),B
            partial(self.f_xy, r, m, SLL, IYh, IYl, C),             # FDCB..31 SLL (IY+d),C
            partial(self.f_xy, r, m, SLL, IYh, IYl, D),             # FDCB..32 SLL (IY+d),D
            partial(self.f_xy, r, m, SLL, IYh, IYl, E),             # FDCB..33 SLL (IY+d),E
            partial(self.f_xy, r, m, SLL, IYh, IYl, H),             # FDCB..34 SLL (IY+d),H
            partial(self.f_xy, r, m, SLL, IYh, IYl, L),             # FDCB..35 SLL (IY+d),L
            partial(self.f_xy, r, m, SLL, IYh, IYl),                # FDCB..36 SLL (IY+d)
            partial(self.f_xy, r, m, SLL, IYh, IYl, A),             # FDCB..37 SLL (IY+d),A
            partial(self.f_xy, r, m, SRL, IYh, IYl, B),             # FDCB..38 SRL (IY+d),B
            partial(self.f_xy, r, m, SRL, IYh, IYl, C),             # FDCB..39 SRL (IY+d),C
            partial(self.f_xy, r, m, SRL, IYh, IYl, D),             # FDCB..3A SRL (IY+d),D
            partial(self.f_xy, r, m, SRL, IYh, IYl, E),             # FDCB..3B SRL (IY+d),E
            partial(self.f_xy, r, m, SRL, IYh, IYl, H),             # FDCB..3C SRL (IY+d),H
            partial(self.f_xy, r, m, SRL, IYh, IYl, L),             # FDCB..3D SRL (IY+d),L
            partial(self.f_xy, r, m, SRL, IYh, IYl),                # FDCB..3E SRL (IY+d)
            partial(self.f_xy, r, m, SRL, IYh, IYl, A),             # FDCB..3F SRL (IY+d),A
            partial(self.bit_xy, r, m, BIT, 0, IYh, IYl),           # FDCB..40 BIT 0,(IY+d)
            partial(self.bit_xy, r, m, BIT, 0, IYh, IYl),           # FDCB..41 BIT 0,(IY+d)
            partial(self.bit_xy, r, m, BIT, 0, IYh, IYl),           # FDCB..42 BIT 0,(IY+d)
            partial(self.bit_xy, r, m, BIT, 0, IYh, IYl),           # FDCB..43 BIT 0,(IY+d)
            partial(self.bit_xy, r, m, BIT, 0, IYh, IYl),           # FDCB..44 BIT 0,(IY+d)
            partial(self.bit_xy, r, m, BIT, 0, IYh, IYl),           # FDCB..45 BIT 0,(IY+d)
            partial(self.bit_xy, r, m, BIT, 0, IYh, IYl),           # FDCB..46 BIT 0,(IY+d)
            partial(self.bit_xy, r, m, BIT, 0, IYh, IYl),           # FDCB..47 BIT 0,(IY+d)
            partial(self.bit_xy, r, m, BIT, 1, IYh, IYl),           # FDCB..48 BIT 1,(IY+d)
            partial(self.bit_xy, r, m, BIT, 1, IYh, IYl),           # FDCB..49 BIT 1,(IY+d)
            partial(self.bit_xy, r, m, BIT, 1, IYh, IYl),           # FDCB..4A BIT 1,(IY+d)
            partial(self.bit_xy, r, m, BIT, 1, IYh, IYl),           # FDCB..4B BIT 1,(IY+d)
            partial(self.bit_xy, r, m, BIT, 1, IYh, IYl),           # FDCB..4C BIT 1,(IY+d)
            partial(self.bit_xy, r, m, BIT, 1, IYh, IYl),           # FDCB..4D BIT 1,(IY+d)
            partial(self.bit_xy, r, m, BIT, 1, IYh, IYl),           # FDCB..4E BIT 1,(IY+d)
            partial(self.bit_xy, r, m, BIT, 1, IYh, IYl),           # FDCB..4F BIT 1,(IY+d)
            partial(self.bit_xy, r, m, BIT, 2, IYh, IYl),           # FDCB..50 BIT 2,(IY+d)
            partial(self.bit_xy, r, m, BIT, 2, IYh, IYl),           # FDCB..51 BIT 2,(IY+d)
            partial(self.bit_xy, r, m, BIT, 2, IYh, IYl),           # FDCB..52 BIT 2,(IY+d)
            partial(self.bit_xy, r, m, BIT, 2, IYh, IYl),           # FDCB..53 BIT 2,(IY+d)
            partial(self.bit_xy, r, m, BIT, 2, IYh, IYl),           # FDCB..54 BIT 2,(IY+d)
            partial(self.bit_xy, r, m, BIT, 2, IYh, IYl),           # FDCB..55 BIT 2,(IY+d)
            partial(self.bit_xy, r, m, BIT, 2, IYh, IYl),           # FDCB..56 BIT 2,(IY+d)
            partial(self.bit_xy, r, m, BIT, 2, IYh, IYl),           # FDCB..57 BIT 2,(IY+d)
            partial(self.bit_xy, r, m, BIT, 3, IYh, IYl),           # FDCB..58 BIT 3,(IY+d)
            partial(self.bit_xy, r, m, BIT, 3, IYh, IYl),           # FDCB..59 BIT 3,(IY+d)
            partial(self.bit_xy, r, m, BIT, 3, IYh, IYl),           # FDCB..5A BIT 3,(IY+d)
            partial(self.bit_xy, r, m, BIT, 3, IYh, IYl),           # FDCB..5B BIT 3,(IY+d)
            partial(self.bit_xy, r, m, BIT, 3, IYh, IYl),           # FDCB..5C BIT 3,(IY+d)
            partial(self.bit_xy, r, m, BIT, 3, IYh, IYl),           # FDCB..5D BIT 3,(IY+d)
            partial(self.bit_xy, r, m, BIT, 3, IYh, IYl),           # FDCB..5E BIT 3,(IY+d)
            partial(self.bit_xy, r, m, BIT, 3, IYh, IYl),           # FDCB..5F BIT 3,(IY+d)
            partial(self.bit_xy, r, m, BIT, 4, IYh, IYl),           # FDCB..60 BIT 4,(IY+d)
            partial(self.bit_xy, r, m, BIT, 4, IYh, IYl),           # FDCB..61 BIT 4,(IY+d)
            partial(self.bit_xy, r, m, BIT, 4, IYh, IYl),           # FDCB..62 BIT 4,(IY+d)
            partial(self.bit_xy, r, m, BIT, 4, IYh, IYl),           # FDCB..63 BIT 4,(IY+d)
            partial(self.bit_xy, r, m, BIT, 4, IYh, IYl),           # FDCB..64 BIT 4,(IY+d)
            partial(self.bit_xy, r, m, BIT, 4, IYh, IYl),           # FDCB..65 BIT 4,(IY+d)
            partial(self.bit_xy, r, m, BIT, 4, IYh, IYl),           # FDCB..66 BIT 4,(IY+d)
            partial(self.bit_xy, r, m, BIT, 4, IYh, IYl),           # FDCB..67 BIT 4,(IY+d)
            partial(self.bit_xy, r, m, BIT, 5, IYh, IYl),           # FDCB..68 BIT 5,(IY+d)
            partial(self.bit_xy, r, m, BIT, 5, IYh, IYl),           # FDCB..69 BIT 5,(IY+d)
            partial(self.bit_xy, r, m, BIT, 5, IYh, IYl),           # FDCB..6A BIT 5,(IY+d)
            partial(self.bit_xy, r, m, BIT, 5, IYh, IYl),           # FDCB..6B BIT 5,(IY+d)
            partial(self.bit_xy, r, m, BIT, 5, IYh, IYl),           # FDCB..6C BIT 5,(IY+d)
            partial(self.bit_xy, r, m, BIT, 5, IYh, IYl),           # FDCB..6D BIT 5,(IY+d)
            partial(self.bit_xy, r, m, BIT, 5, IYh, IYl),           # FDCB..6E BIT 5,(IY+d)
            partial(self.bit_xy, r, m, BIT, 5, IYh, IYl),           # FDCB..6F BIT 5,(IY+d)
            partial(self.bit_xy, r, m, BIT, 6, IYh, IYl),           # FDCB..70 BIT 6,(IY+d)
            partial(self.bit_xy, r, m, BIT, 6, IYh, IYl),           # FDCB..71 BIT 6,(IY+d)
            partial(self.bit_xy, r, m, BIT, 6, IYh, IYl),           # FDCB..72 BIT 6,(IY+d)
            partial(self.bit_xy, r, m, BIT, 6, IYh, IYl),           # FDCB..73 BIT 6,(IY+d)
            partial(self.bit_xy, r, m, BIT, 6, IYh, IYl),           # FDCB..74 BIT 6,(IY+d)
            partial(self.bit_xy, r, m, BIT, 6, IYh, IYl),           # FDCB..75 BIT 6,(IY+d)
            partial(self.bit_xy, r, m, BIT, 6, IYh, IYl),           # FDCB..76 BIT 6,(IY+d)
            partial(self.bit_xy, r, m, BIT, 6, IYh, IYl),           # FDCB..77 BIT 6,(IY+d)
            partial(self.bit_xy, r, m, BIT, 7, IYh, IYl),           # FDCB..78 BIT 7,(IY+d)
            partial(self.bit_xy, r, m, BIT, 7, IYh, IYl),           # FDCB..79 BIT 7,(IY+d)
            partial(self.bit_xy, r, m, BIT, 7, IYh, IYl),           # FDCB..7A BIT 7,(IY+d)
            partial(self.bit_xy, r, m, BIT, 7, IYh, IYl),           # FDCB..7B BIT 7,(IY+d)
            partial(self.bit_xy, r, m, BIT, 7, IYh, IYl),           # FDCB..7C BIT 7,(IY+d)
            partial(self.bit_xy, r, m, BIT, 7, IYh, IYl),           # FDCB..7D BIT 7,(IY+d)
            partial(self.bit_xy, r, m, BIT, 7, IYh, IYl),           # FDCB..7E BIT 7,(IY+d)
            partial(self.bit_xy, r, m, BIT, 7, IYh, IYl),           # FDCB..7F BIT 7,(IY+d)
            partial(self.res_xy, r, m, 254, IYh, IYl, B),           # FDCB..80 RES 0,(IY+d),B
            partial(self.res_xy, r, m, 254, IYh, IYl, C),           # FDCB..81 RES 0,(IY+d),C
            partial(self.res_xy, r, m, 254, IYh, IYl, D),           # FDCB..82 RES 0,(IY+d),D
            partial(self.res_xy, r, m, 254, IYh, IYl, E),           # FDCB..83 RES 0,(IY+d),E
            partial(self.res_xy, r, m, 254, IYh, IYl, H),           # FDCB..84 RES 0,(IY+d),H
            partial(self.res_xy, r, m, 254, IYh, IYl, L),           # FDCB..85 RES 0,(IY+d),L
            partial(self.res_xy, r, m, 254, IYh, IYl),              # FDCB..86 RES 0,(IY+d)
            partial(self.res_xy, r, m, 254, IYh, IYl, A),           # FDCB..87 RES 0,(IY+d),A
            partial(self.res_xy, r, m, 253, IYh, IYl, B),           # FDCB..88 RES 1,(IY+d),B
            partial(self.res_xy, r, m, 253, IYh, IYl, C),           # FDCB..89 RES 1,(IY+d),C
            partial(self.res_xy, r, m, 253, IYh, IYl, D),           # FDCB..8A RES 1,(IY+d),D
            partial(self.res_xy, r, m, 253, IYh, IYl, E),           # FDCB..8B RES 1,(IY+d),E
            partial(self.res_xy, r, m, 253, IYh, IYl, H),           # FDCB..8C RES 1,(IY+d),H
            partial(self.res_xy, r, m, 253, IYh, IYl, L),           # FDCB..8D RES 1,(IY+d),L
            partial(self.res_xy, r, m, 253, IYh, IYl),              # FDCB..8E RES 1,(IY+d)
            partial(self.res_xy, r, m, 253, IYh, IYl, A),           # FDCB..8F RES 1,(IY+d),A
            partial(self.res_xy, r, m, 251, IYh, IYl, B),           # FDCB..90 RES 2,(IY+d),B
            partial(self.res_xy, r, m, 251, IYh, IYl, C),           # FDCB..91 RES 2,(IY+d),C
            partial(self.res_xy, r, m, 251, IYh, IYl, D),           # FDCB..92 RES 2,(IY+d),D
            partial(self.res_xy, r, m, 251, IYh, IYl, E),           # FDCB..93 RES 2,(IY+d),E
            partial(self.res_xy, r, m, 251, IYh, IYl, H),           # FDCB..94 RES 2,(IY+d),H
            partial(self.res_xy, r, m, 251, IYh, IYl, L),           # FDCB..95 RES 2,(IY+d),L
            partial(self.res_xy, r, m, 251, IYh, IYl),              # FDCB..96 RES 2,(IY+d)
            partial(self.res_xy, r, m, 251, IYh, IYl, A),           # FDCB..97 RES 2,(IY+d),A
            partial(self.res_xy, r, m, 247, IYh, IYl, B),           # FDCB..98 RES 3,(IY+d),B
            partial(self.res_xy, r, m, 247, IYh, IYl, C),           # FDCB..99 RES 3,(IY+d),C
            partial(self.res_xy, r, m, 247, IYh, IYl, D),           # FDCB..9A RES 3,(IY+d),D
            partial(self.res_xy, r, m, 247, IYh, IYl, E),           # FDCB..9B RES 3,(IY+d),E
            partial(self.res_xy, r, m, 247, IYh, IYl, H),           # FDCB..9C RES 3,(IY+d),H
            partial(self.res_xy, r, m, 247, IYh, IYl, L),           # FDCB..9D RES 3,(IY+d),L
            partial(self.res_xy, r, m, 247, IYh, IYl),              # FDCB..9E RES 3,(IY+d)
            partial(self.res_xy, r, m, 247, IYh, IYl, A),           # FDCB..9F RES 3,(IY+d),A
            partial(self.res_xy, r, m, 239, IYh, IYl, B),           # FDCB..A0 RES 4,(IY+d),B
            partial(self.res_xy, r, m, 239, IYh, IYl, C),           # FDCB..A1 RES 4,(IY+d),C
            partial(self.res_xy, r, m, 239, IYh, IYl, D),           # FDCB..A2 RES 4,(IY+d),D
            partial(self.res_xy, r, m, 239, IYh, IYl, E),           # FDCB..A3 RES 4,(IY+d),E
            partial(self.res_xy, r, m, 239, IYh, IYl, H),           # FDCB..A4 RES 4,(IY+d),H
            partial(self.res_xy, r, m, 239, IYh, IYl, L),           # FDCB..A5 RES 4,(IY+d),L
            partial(self.res_xy, r, m, 239, IYh, IYl),              # FDCB..A6 RES 4,(IY+d)
            partial(self.res_xy, r, m, 239, IYh, IYl, A),           # FDCB..A7 RES 4,(IY+d),A
            partial(self.res_xy, r, m, 223, IYh, IYl, B),           # FDCB..A8 RES 5,(IY+d),B
            partial(self.res_xy, r, m, 223, IYh, IYl, C),           # FDCB..A9 RES 5,(IY+d),C
            partial(self.res_xy, r, m, 223, IYh, IYl, D),           # FDCB..AA RES 5,(IY+d),D
            partial(self.res_xy, r, m, 223, IYh, IYl, E),           # FDCB..AB RES 5,(IY+d),E
            partial(self.res_xy, r, m, 223, IYh, IYl, H),           # FDCB..AC RES 5,(IY+d),H
            partial(self.res_xy, r, m, 223, IYh, IYl, L),           # FDCB..AD RES 5,(IY+d),L
            partial(self.res_xy, r, m, 223, IYh, IYl),              # FDCB..AE RES 5,(IY+d)
            partial(self.res_xy, r, m, 223, IYh, IYl, A),           # FDCB..AF RES 5,(IY+d),A
            partial(self.res_xy, r, m, 191, IYh, IYl, B),           # FDCB..B0 RES 6,(IY+d),B
            partial(self.res_xy, r, m, 191, IYh, IYl, C),           # FDCB..B1 RES 6,(IY+d),C
            partial(self.res_xy, r, m, 191, IYh, IYl, D),           # FDCB..B2 RES 6,(IY+d),D
            partial(self.res_xy, r, m, 191, IYh, IYl, E),           # FDCB..B3 RES 6,(IY+d),E
            partial(self.res_xy, r, m, 191, IYh, IYl, H),           # FDCB..B4 RES 6,(IY+d),H
            partial(self.res_xy, r, m, 191, IYh, IYl, L),           # FDCB..B5 RES 6,(IY+d),L
            partial(self.res_xy, r, m, 191, IYh, IYl),              # FDCB..B6 RES 6,(IY+d)
            partial(self.res_xy, r, m, 191, IYh, IYl, A),           # FDCB..B7 RES 6,(IY+d),A
            partial(self.res_xy, r, m, 127, IYh, IYl, B),           # FDCB..B8 RES 7,(IY+d),B
            partial(self.res_xy, r, m, 127, IYh, IYl, C),           # FDCB..B9 RES 7,(IY+d),C
            partial(self.res_xy, r, m, 127, IYh, IYl, D),           # FDCB..BA RES 7,(IY+d),D
            partial(self.res_xy, r, m, 127, IYh, IYl, E),           # FDCB..BB RES 7,(IY+d),E
            partial(self.res_xy, r, m, 127, IYh, IYl, H),           # FDCB..BC RES 7,(IY+d),H
            partial(self.res_xy, r, m, 127, IYh, IYl, L),           # FDCB..BD RES 7,(IY+d),L
            partial(self.res_xy, r, m, 127, IYh, IYl),              # FDCB..BE RES 7,(IY+d)
            partial(self.res_xy, r, m, 127, IYh, IYl, A),           # FDCB..BF RES 7,(IY+d),A
            partial(self.set_xy, r, m, 1, IYh, IYl, B),             # FDCB..C0 SET 0,(IY+d),B
            partial(self.set_xy, r, m, 1, IYh, IYl, C),             # FDCB..C1 SET 0,(IY+d),C
            partial(self.set_xy, r, m, 1, IYh, IYl, D),             # FDCB..C2 SET 0,(IY+d),D
            partial(self.set_xy, r, m, 1, IYh, IYl, E),             # FDCB..C3 SET 0,(IY+d),E
            partial(self.set_xy, r, m, 1, IYh, IYl, H),             # FDCB..C4 SET 0,(IY+d),H
            partial(self.set_xy, r, m, 1, IYh, IYl, L),             # FDCB..C5 SET 0,(IY+d),L
            partial(self.set_xy, r, m, 1, IYh, IYl),                # FDCB..C6 SET 0,(IY+d)
            partial(self.set_xy, r, m, 1, IYh, IYl, A),             # FDCB..C7 SET 0,(IY+d),A
            partial(self.set_xy, r, m, 2, IYh, IYl, B),             # FDCB..C8 SET 1,(IY+d),B
            partial(self.set_xy, r, m, 2, IYh, IYl, C),             # FDCB..C9 SET 1,(IY+d),C
            partial(self.set_xy, r, m, 2, IYh, IYl, D),             # FDCB..CA SET 1,(IY+d),D
            partial(self.set_xy, r, m, 2, IYh, IYl, E),             # FDCB..CB SET 1,(IY+d),E
            partial(self.set_xy, r, m, 2, IYh, IYl, H),             # FDCB..CC SET 1,(IY+d),H
            partial(self.set_xy, r, m, 2, IYh, IYl, L),             # FDCB..CD SET 1,(IY+d),L
            partial(self.set_xy, r, m, 2, IYh, IYl),                # FDCB..CE SET 1,(IY+d)
            partial(self.set_xy, r, m, 2, IYh, IYl, A),             # FDCB..CF SET 1,(IY+d),A
            partial(self.set_xy, r, m, 4, IYh, IYl, B),             # FDCB..D0 SET 2,(IY+d),B
            partial(self.set_xy, r, m, 4, IYh, IYl, C),             # FDCB..D1 SET 2,(IY+d),C
            partial(self.set_xy, r, m, 4, IYh, IYl, D),             # FDCB..D2 SET 2,(IY+d),D
            partial(self.set_xy, r, m, 4, IYh, IYl, E),             # FDCB..D3 SET 2,(IY+d),E
            partial(self.set_xy, r, m, 4, IYh, IYl, H),             # FDCB..D4 SET 2,(IY+d),H
            partial(self.set_xy, r, m, 4, IYh, IYl, L),             # FDCB..D5 SET 2,(IY+d),L
            partial(self.set_xy, r, m, 4, IYh, IYl),                # FDCB..D6 SET 2,(IY+d)
            partial(self.set_xy, r, m, 4, IYh, IYl, A),             # FDCB..D7 SET 2,(IY+d),A
            partial(self.set_xy, r, m, 8, IYh, IYl, B),             # FDCB..D8 SET 3,(IY+d),B
            partial(self.set_xy, r, m, 8, IYh, IYl, C),             # FDCB..D9 SET 3,(IY+d),C
            partial(self.set_xy, r, m, 8, IYh, IYl, D),             # FDCB..DA SET 3,(IY+d),D
            partial(self.set_xy, r, m, 8, IYh, IYl, E),             # FDCB..DB SET 3,(IY+d),E
            partial(self.set_xy, r, m, 8, IYh, IYl, H),             # FDCB..DC SET 3,(IY+d),H
            partial(self.set_xy, r, m, 8, IYh, IYl, L),             # FDCB..DD SET 3,(IY+d),L
            partial(self.set_xy, r, m, 8, IYh, IYl),                # FDCB..DE SET 3,(IY+d)
            partial(self.set_xy, r, m, 8, IYh, IYl, A),             # FDCB..DF SET 3,(IY+d),A
            partial(self.set_xy, r, m, 16, IYh, IYl, B),            # FDCB..E0 SET 4,(IY+d),B
            partial(self.set_xy, r, m, 16, IYh, IYl, C),            # FDCB..E1 SET 4,(IY+d),C
            partial(self.set_xy, r, m, 16, IYh, IYl, D),            # FDCB..E2 SET 4,(IY+d),D
            partial(self.set_xy, r, m, 16, IYh, IYl, E),            # FDCB..E3 SET 4,(IY+d),E
            partial(self.set_xy, r, m, 16, IYh, IYl, H),            # FDCB..E4 SET 4,(IY+d),H
            partial(self.set_xy, r, m, 16, IYh, IYl, L),            # FDCB..E5 SET 4,(IY+d),L
            partial(self.set_xy, r, m, 16, IYh, IYl),               # FDCB..E6 SET 4,(IY+d)
            partial(self.set_xy, r, m, 16, IYh, IYl, A),            # FDCB..E7 SET 4,(IY+d),A
            partial(self.set_xy, r, m, 32, IYh, IYl, B),            # FDCB..E8 SET 5,(IY+d),B
            partial(self.set_xy, r, m, 32, IYh, IYl, C),            # FDCB..E9 SET 5,(IY+d),C
            partial(self.set_xy, r, m, 32, IYh, IYl, D),            # FDCB..EA SET 5,(IY+d),D
            partial(self.set_xy, r, m, 32, IYh, IYl, E),            # FDCB..EB SET 5,(IY+d),E
            partial(self.set_xy, r, m, 32, IYh, IYl, H),            # FDCB..EC SET 5,(IY+d),H
            partial(self.set_xy, r, m, 32, IYh, IYl, L),            # FDCB..ED SET 5,(IY+d),L
            partial(self.set_xy, r, m, 32, IYh, IYl),               # FDCB..EE SET 5,(IY+d)
            partial(self.set_xy, r, m, 32, IYh, IYl, A),            # FDCB..EF SET 5,(IY+d),A
            partial(self.set_xy, r, m, 64, IYh, IYl, B),            # FDCB..F0 SET 6,(IY+d),B
            partial(self.set_xy, r, m, 64, IYh, IYl, C),            # FDCB..F1 SET 6,(IY+d),C
            partial(self.set_xy, r, m, 64, IYh, IYl, D),            # FDCB..F2 SET 6,(IY+d),D
            partial(self.set_xy, r, m, 64, IYh, IYl, E),            # FDCB..F3 SET 6,(IY+d),E
            partial(self.set_xy, r, m, 64, IYh, IYl, H),            # FDCB..F4 SET 6,(IY+d),H
            partial(self.set_xy, r, m, 64, IYh, IYl, L),            # FDCB..F5 SET 6,(IY+d),L
            partial(self.set_xy, r, m, 64, IYh, IYl),               # FDCB..F6 SET 6,(IY+d)
            partial(self.set_xy, r, m, 64, IYh, IYl, A),            # FDCB..F7 SET 6,(IY+d),A
            partial(self.set_xy, r, m, 128, IYh, IYl, B),           # FDCB..F8 SET 7,(IY+d),B
            partial(self.set_xy, r, m, 128, IYh, IYl, C),           # FDCB..F9 SET 7,(IY+d),C
            partial(self.set_xy, r, m, 128, IYh, IYl, D),           # FDCB..FA SET 7,(IY+d),D
            partial(self.set_xy, r, m, 128, IYh, IYl, E),           # FDCB..FB SET 7,(IY+d),E
            partial(self.set_xy, r, m, 128, IYh, IYl, H),           # FDCB..FC SET 7,(IY+d),H
            partial(self.set_xy, r, m, 128, IYh, IYl, L),           # FDCB..FD SET 7,(IY+d),L
            partial(self.set_xy, r, m, 128, IYh, IYl),              # FDCB..FE SET 7,(IY+d)
            partial(self.set_xy, r, m, 128, IYh, IYl, A),           # FDCB..FF SET 7,(IY+d),A
        ]

        self.after_CB = [
            partial(self.f_r, r, RLC, B),                           # CB00 RLC B
            partial(self.f_r, r, RLC, C),                           # CB01 RLC C
            partial(self.f_r, r, RLC, D),                           # CB02 RLC D
            partial(self.f_r, r, RLC, E),                           # CB03 RLC E
            partial(self.f_r, r, RLC, H),                           # CB04 RLC H
            partial(self.f_r, r, RLC, L),                           # CB05 RLC L
            partial(self.f_hl, r, m, RLC),                          # CB06 RLC (HL)
            partial(self.f_r, r, RLC, A),                           # CB07 RLC A
            partial(self.f_r, r, RRC, B),                           # CB08 RRC B
            partial(self.f_r, r, RRC, C),                           # CB09 RRC C
            partial(self.f_r, r, RRC, D),                           # CB0A RRC D
            partial(self.f_r, r, RRC, E),                           # CB0B RRC E
            partial(self.f_r, r, RRC, H),                           # CB0C RRC H
            partial(self.f_r, r, RRC, L),                           # CB0D RRC L
            partial(self.f_hl, r, m, RRC),                          # CB0E RRC (HL)
            partial(self.f_r, r, RRC, A),                           # CB0F RRC A
            partial(self.fc_r, r, R2, 8, 2, RL, B),                 # CB10 RL B
            partial(self.fc_r, r, R2, 8, 2, RL, C),                 # CB11 RL C
            partial(self.fc_r, r, R2, 8, 2, RL, D),                 # CB12 RL D
            partial(self.fc_r, r, R2, 8, 2, RL, E),                 # CB13 RL E
            partial(self.fc_r, r, R2, 8, 2, RL, H),                 # CB14 RL H
            partial(self.fc_r, r, R2, 8, 2, RL, L),                 # CB15 RL L
            partial(self.fc_hl, r, m, R2, 15, 2, RL),               # CB16 RL (HL)
            partial(self.fc_r, r, R2, 8, 2, RL, A),                 # CB17 RL A
            partial(self.fc_r, r, R2, 8, 2, RR, B),                 # CB18 RR B
            partial(self.fc_r, r, R2, 8, 2, RR, C),                 # CB19 RR C
            partial(self.fc_r, r, R2, 8, 2, RR, D),                 # CB1A RR D
            partial(self.fc_r, r, R2, 8, 2, RR, E),                 # CB1B RR E
            partial(self.fc_r, r, R2, 8, 2, RR, H),                 # CB1C RR H
            partial(self.fc_r, r, R2, 8, 2, RR, L),                 # CB1D RR L
            partial(self.fc_hl, r, m, R2, 15, 2, RR),               # CB1E RR (HL)
            partial(self.fc_r, r, R2, 8, 2, RR, A),                 # CB1F RR A
            partial(self.f_r, r, SLA, B),                           # CB20 SLA B
            partial(self.f_r, r, SLA, C),                           # CB21 SLA C
            partial(self.f_r, r, SLA, D),                           # CB22 SLA D
            partial(self.f_r, r, SLA, E),                           # CB23 SLA E
            partial(self.f_r, r, SLA, H),                           # CB24 SLA H
            partial(self.f_r, r, SLA, L),                           # CB25 SLA L
            partial(self.f_hl, r, m, SLA),                          # CB26 SLA (HL)
            partial(self.f_r, r, SLA, A),                           # CB27 SLA A
            partial(self.f_r, r, SRA, B),                           # CB28 SRA B
            partial(self.f_r, r, SRA, C),                           # CB29 SRA C
            partial(self.f_r, r, SRA, D),                           # CB2A SRA D
            partial(self.f_r, r, SRA, E),                           # CB2B SRA E
            partial(self.f_r, r, SRA, H),                           # CB2C SRA H
            partial(self.f_r, r, SRA, L),                           # CB2D SRA L
            partial(self.f_hl, r, m, SRA),                          # CB2E SRA (HL)
            partial(self.f_r, r, SRA, A),                           # CB2F SRA A
            partial(self.f_r, r, SLL, B),                           # CB30 SLL B
            partial(self.f_r, r, SLL, C),                           # CB31 SLL C
            partial(self.f_r, r, SLL, D),                           # CB32 SLL D
            partial(self.f_r, r, SLL, E),                           # CB33 SLL E
            partial(self.f_r, r, SLL, H),                           # CB34 SLL H
            partial(self.f_r, r, SLL, L),                           # CB35 SLL L
            partial(self.f_hl, r, m, SLL),                          # CB36 SLL (HL)
            partial(self.f_r, r, SLL, A),                           # CB37 SLL A
            partial(self.f_r, r, SRL, B),                           # CB38 SRL B
            partial(self.f_r, r, SRL, C),                           # CB39 SRL C
            partial(self.f_r, r, SRL, D),                           # CB3A SRL D
            partial(self.f_r, r, SRL, E),                           # CB3B SRL E
            partial(self.f_r, r, SRL, H),                           # CB3C SRL H
            partial(self.f_r, r, SRL, L),                           # CB3D SRL L
            partial(self.f_hl, r, m, SRL),                          # CB3E SRL (HL)
            partial(self.f_r, r, SRL, A),                           # CB3F SRL A
            partial(self.bit_r, r, BIT, 0, B),                      # CB40 BIT 0,B
            partial(self.bit_r, r, BIT, 0, C),                      # CB41 BIT 0,C
            partial(self.bit_r, r, BIT, 0, D),                      # CB42 BIT 0,D
            partial(self.bit_r, r, BIT, 0, E),                      # CB43 BIT 0,E
            partial(self.bit_r, r, BIT, 0, H),                      # CB44 BIT 0,H
            partial(self.bit_r, r, BIT, 0, L),                      # CB45 BIT 0,L
            partial(self.bit_hl, r, m, BIT, 0),                     # CB46 BIT 0,(HL)
            partial(self.bit_r, r, BIT, 0, A),                      # CB47 BIT 0,A
            partial(self.bit_r, r, BIT, 1, B),                      # CB48 BIT 1,B
            partial(self.bit_r, r, BIT, 1, C),                      # CB49 BIT 1,C
            partial(self.bit_r, r, BIT, 1, D),                      # CB4A BIT 1,D
            partial(self.bit_r, r, BIT, 1, E),                      # CB4B BIT 1,E
            partial(self.bit_r, r, BIT, 1, H),                      # CB4C BIT 1,H
            partial(self.bit_r, r, BIT, 1, L),                      # CB4D BIT 1,L
            partial(self.bit_hl, r, m, BIT, 1),                     # CB4E BIT 1,(HL)
            partial(self.bit_r, r, BIT, 1, A),                      # CB4F BIT 1,A
            partial(self.bit_r, r, BIT, 2, B),                      # CB50 BIT 2,B
            partial(self.bit_r, r, BIT, 2, C),                      # CB51 BIT 2,C
            partial(self.bit_r, r, BIT, 2, D),                      # CB52 BIT 2,D
            partial(self.bit_r, r, BIT, 2, E),                      # CB53 BIT 2,E
            partial(self.bit_r, r, BIT, 2, H),                      # CB54 BIT 2,H
            partial(self.bit_r, r, BIT, 2, L),                      # CB55 BIT 2,L
            partial(self.bit_hl, r, m, BIT, 2),                     # CB56 BIT 2,(HL)
            partial(self.bit_r, r, BIT, 2, A),                      # CB57 BIT 2,A
            partial(self.bit_r, r, BIT, 3, B),                      # CB58 BIT 3,B
            partial(self.bit_r, r, BIT, 3, C),                      # CB59 BIT 3,C
            partial(self.bit_r, r, BIT, 3, D),                      # CB5A BIT 3,D
            partial(self.bit_r, r, BIT, 3, E),                      # CB5B BIT 3,E
            partial(self.bit_r, r, BIT, 3, H),                      # CB5C BIT 3,H
            partial(self.bit_r, r, BIT, 3, L),                      # CB5D BIT 3,L
            partial(self.bit_hl, r, m, BIT, 3),                     # CB5E BIT 3,(HL)
            partial(self.bit_r, r, BIT, 3, A),                      # CB5F BIT 3,A
            partial(self.bit_r, r, BIT, 4, B),                      # CB60 BIT 4,B
            partial(self.bit_r, r, BIT, 4, C),                      # CB61 BIT 4,C
            partial(self.bit_r, r, BIT, 4, D),                      # CB62 BIT 4,D
            partial(self.bit_r, r, BIT, 4, E),                      # CB63 BIT 4,E
            partial(self.bit_r, r, BIT, 4, H),                      # CB64 BIT 4,H
            partial(self.bit_r, r, BIT, 4, L),                      # CB65 BIT 4,L
            partial(self.bit_hl, r, m, BIT, 4),                     # CB66 BIT 4,(HL)
            partial(self.bit_r, r, BIT, 4, A),                      # CB67 BIT 4,A
            partial(self.bit_r, r, BIT, 5, B),                      # CB68 BIT 5,B
            partial(self.bit_r, r, BIT, 5, C),                      # CB69 BIT 5,C
            partial(self.bit_r, r, BIT, 5, D),                      # CB6A BIT 5,D
            partial(self.bit_r, r, BIT, 5, E),                      # CB6B BIT 5,E
            partial(self.bit_r, r, BIT, 5, H),                      # CB6C BIT 5,H
            partial(self.bit_r, r, BIT, 5, L),                      # CB6D BIT 5,L
            partial(self.bit_hl, r, m, BIT, 5),                     # CB6E BIT 5,(HL)
            partial(self.bit_r, r, BIT, 5, A),                      # CB6F BIT 5,A
            partial(self.bit_r, r, BIT, 6, B),                      # CB70 BIT 6,B
            partial(self.bit_r, r, BIT, 6, C),                      # CB71 BIT 6,C
            partial(self.bit_r, r, BIT, 6, D),                      # CB72 BIT 6,D
            partial(self.bit_r, r, BIT, 6, E),                      # CB73 BIT 6,E
            partial(self.bit_r, r, BIT, 6, H),                      # CB74 BIT 6,H
            partial(self.bit_r, r, BIT, 6, L),                      # CB75 BIT 6,L
            partial(self.bit_hl, r, m, BIT, 6),                     # CB76 BIT 6,(HL)
            partial(self.bit_r, r, BIT, 6, A),                      # CB77 BIT 6,A
            partial(self.bit_r, r, BIT, 7, B),                      # CB78 BIT 7,B
            partial(self.bit_r, r, BIT, 7, C),                      # CB79 BIT 7,C
            partial(self.bit_r, r, BIT, 7, D),                      # CB7A BIT 7,D
            partial(self.bit_r, r, BIT, 7, E),                      # CB7B BIT 7,E
            partial(self.bit_r, r, BIT, 7, H),                      # CB7C BIT 7,H
            partial(self.bit_r, r, BIT, 7, L),                      # CB7D BIT 7,L
            partial(self.bit_hl, r, m, BIT, 7),                     # CB7E BIT 7,(HL)
            partial(self.bit_r, r, BIT, 7, A),                      # CB7F BIT 7,A
            partial(self.res_r, r, 254, B),                         # CB80 RES 0,B
            partial(self.res_r, r, 254, C),                         # CB81 RES 0,C
            partial(self.res_r, r, 254, D),                         # CB82 RES 0,D
            partial(self.res_r, r, 254, E),                         # CB83 RES 0,E
            partial(self.res_r, r, 254, H),                         # CB84 RES 0,H
            partial(self.res_r, r, 254, L),                         # CB85 RES 0,L
            partial(self.res_hl, r, m, 254),                        # CB86 RES 0,(HL)
            partial(self.res_r, r, 254, A),                         # CB87 RES 0,A
            partial(self.res_r, r, 253, B),                         # CB88 RES 1,B
            partial(self.res_r, r, 253, C),                         # CB89 RES 1,C
            partial(self.res_r, r, 253, D),                         # CB8A RES 1,D
            partial(self.res_r, r, 253, E),                         # CB8B RES 1,E
            partial(self.res_r, r, 253, H),                         # CB8C RES 1,H
            partial(self.res_r, r, 253, L),                         # CB8D RES 1,L
            partial(self.res_hl, r, m, 253),                        # CB8E RES 1,(HL)
            partial(self.res_r, r, 253, A),                         # CB8F RES 1,A
            partial(self.res_r, r, 251, B),                         # CB90 RES 2,B
            partial(self.res_r, r, 251, C),                         # CB91 RES 2,C
            partial(self.res_r, r, 251, D),                         # CB92 RES 2,D
            partial(self.res_r, r, 251, E),                         # CB93 RES 2,E
            partial(self.res_r, r, 251, H),                         # CB94 RES 2,H
            partial(self.res_r, r, 251, L),                         # CB95 RES 2,L
            partial(self.res_hl, r, m, 251),                        # CB96 RES 2,(HL)
            partial(self.res_r, r, 251, A),                         # CB97 RES 2,A
            partial(self.res_r, r, 247, B),                         # CB98 RES 3,B
            partial(self.res_r, r, 247, C),                         # CB99 RES 3,C
            partial(self.res_r, r, 247, D),                         # CB9A RES 3,D
            partial(self.res_r, r, 247, E),                         # CB9B RES 3,E
            partial(self.res_r, r, 247, H),                         # CB9C RES 3,H
            partial(self.res_r, r, 247, L),                         # CB9D RES 3,L
            partial(self.res_hl, r, m, 247),                        # CB9E RES 3,(HL)
            partial(self.res_r, r, 247, A),                         # CB9F RES 3,A
            partial(self.res_r, r, 239, B),                         # CBA0 RES 4,B
            partial(self.res_r, r, 239, C),                         # CBA1 RES 4,C
            partial(self.res_r, r, 239, D),                         # CBA2 RES 4,D
            partial(self.res_r, r, 239, E),                         # CBA3 RES 4,E
            partial(self.res_r, r, 239, H),                         # CBA4 RES 4,H
            partial(self.res_r, r, 239, L),                         # CBA5 RES 4,L
            partial(self.res_hl, r, m, 239),                        # CBA6 RES 4,(HL)
            partial(self.res_r, r, 239, A),                         # CBA7 RES 4,A
            partial(self.res_r, r, 223, B),                         # CBA8 RES 5,B
            partial(self.res_r, r, 223, C),                         # CBA9 RES 5,C
            partial(self.res_r, r, 223, D),                         # CBAA RES 5,D
            partial(self.res_r, r, 223, E),                         # CBAB RES 5,E
            partial(self.res_r, r, 223, H),                         # CBAC RES 5,H
            partial(self.res_r, r, 223, L),                         # CBAD RES 5,L
            partial(self.res_hl, r, m, 223),                        # CBAE RES 5,(HL)
            partial(self.res_r, r, 223, A),                         # CBAF RES 5,A
            partial(self.res_r, r, 191, B),                         # CBB0 RES 6,B
            partial(self.res_r, r, 191, C),                         # CBB1 RES 6,C
            partial(self.res_r, r, 191, D),                         # CBB2 RES 6,D
            partial(self.res_r, r, 191, E),                         # CBB3 RES 6,E
            partial(self.res_r, r, 191, H),                         # CBB4 RES 6,H
            partial(self.res_r, r, 191, L),                         # CBB5 RES 6,L
            partial(self.res_hl, r, m, 191),                        # CBB6 RES 6,(HL)
            partial(self.res_r, r, 191, A),                         # CBB7 RES 6,A
            partial(self.res_r, r, 127, B),                         # CBB8 RES 7,B
            partial(self.res_r, r, 127, C),                         # CBB9 RES 7,C
            partial(self.res_r, r, 127, D),                         # CBBA RES 7,D
            partial(self.res_r, r, 127, E),                         # CBBB RES 7,E
            partial(self.res_r, r, 127, H),                         # CBBC RES 7,H
            partial(self.res_r, r, 127, L),                         # CBBD RES 7,L
            partial(self.res_hl, r, m, 127),                        # CBBE RES 7,(HL)
            partial(self.res_r, r, 127, A),                         # CBBF RES 7,A
            partial(self.set_r, r, 1, B),                           # CBC0 SET 0,B
            partial(self.set_r, r, 1, C),                           # CBC1 SET 0,C
            partial(self.set_r, r, 1, D),                           # CBC2 SET 0,D
            partial(self.set_r, r, 1, E),                           # CBC3 SET 0,E
            partial(self.set_r, r, 1, H),                           # CBC4 SET 0,H
            partial(self.set_r, r, 1, L),                           # CBC5 SET 0,L
            partial(self.set_hl, r, m, 1),                          # CBC6 SET 0,(HL)
            partial(self.set_r, r, 1, A),                           # CBC7 SET 0,A
            partial(self.set_r, r, 2, B),                           # CBC8 SET 1,B
            partial(self.set_r, r, 2, C),                           # CBC9 SET 1,C
            partial(self.set_r, r, 2, D),                           # CBCA SET 1,D
            partial(self.set_r, r, 2, E),                           # CBCB SET 1,E
            partial(self.set_r, r, 2, H),                           # CBCC SET 1,H
            partial(self.set_r, r, 2, L),                           # CBCD SET 1,L
            partial(self.set_hl, r, m, 2),                          # CBCE SET 1,(HL)
            partial(self.set_r, r, 2, A),                           # CBCF SET 1,A
            partial(self.set_r, r, 4, B),                           # CBD0 SET 2,B
            partial(self.set_r, r, 4, C),                           # CBD1 SET 2,C
            partial(self.set_r, r, 4, D),                           # CBD2 SET 2,D
            partial(self.set_r, r, 4, E),                           # CBD3 SET 2,E
            partial(self.set_r, r, 4, H),                           # CBD4 SET 2,H
            partial(self.set_r, r, 4, L),                           # CBD5 SET 2,L
            partial(self.set_hl, r, m, 4),                          # CBD6 SET 2,(HL)
            partial(self.set_r, r, 4, A),                           # CBD7 SET 2,A
            partial(self.set_r, r, 8, B),                           # CBD8 SET 3,B
            partial(self.set_r, r, 8, C),                           # CBD9 SET 3,C
            partial(self.set_r, r, 8, D),                           # CBDA SET 3,D
            partial(self.set_r, r, 8, E),                           # CBDB SET 3,E
            partial(self.set_r, r, 8, H),                           # CBDC SET 3,H
            partial(self.set_r, r, 8, L),                           # CBDD SET 3,L
            partial(self.set_hl, r, m, 8),                          # CBDE SET 3,(HL)
            partial(self.set_r, r, 8, A),                           # CBDF SET 3,A
            partial(self.set_r, r, 16, B),                          # CBE0 SET 4,B
            partial(self.set_r, r, 16, C),                          # CBE1 SET 4,C
            partial(self.set_r, r, 16, D),                          # CBE2 SET 4,D
            partial(self.set_r, r, 16, E),                          # CBE3 SET 4,E
            partial(self.set_r, r, 16, H),                          # CBE4 SET 4,H
            partial(self.set_r, r, 16, L),                          # CBE5 SET 4,L
            partial(self.set_hl, r, m, 16),                         # CBE6 SET 4,(HL)
            partial(self.set_r, r, 16, A),                          # CBE7 SET 4,A
            partial(self.set_r, r, 32, B),                          # CBE8 SET 5,B
            partial(self.set_r, r, 32, C),                          # CBE9 SET 5,C
            partial(self.set_r, r, 32, D),                          # CBEA SET 5,D
            partial(self.set_r, r, 32, E),                          # CBEB SET 5,E
            partial(self.set_r, r, 32, H),                          # CBEC SET 5,H
            partial(self.set_r, r, 32, L),                          # CBED SET 5,L
            partial(self.set_hl, r, m, 32),                         # CBEE SET 5,(HL)
            partial(self.set_r, r, 32, A),                          # CBEF SET 5,A
            partial(self.set_r, r, 64, B),                          # CBF0 SET 6,B
            partial(self.set_r, r, 64, C),                          # CBF1 SET 6,C
            partial(self.set_r, r, 64, D),                          # CBF2 SET 6,D
            partial(self.set_r, r, 64, E),                          # CBF3 SET 6,E
            partial(self.set_r, r, 64, H),                          # CBF4 SET 6,H
            partial(self.set_r, r, 64, L),                          # CBF5 SET 6,L
            partial(self.set_hl, r, m, 64),                         # CBF6 SET 6,(HL)
            partial(self.set_r, r, 64, A),                          # CBF7 SET 6,A
            partial(self.set_r, r, 128, B),                         # CBF8 SET 7,B
            partial(self.set_r, r, 128, C),                         # CBF9 SET 7,C
            partial(self.set_r, r, 128, D),                         # CBFA SET 7,D
            partial(self.set_r, r, 128, E),                         # CBFB SET 7,E
            partial(self.set_r, r, 128, H),                         # CBFC SET 7,H
            partial(self.set_r, r, 128, L),                         # CBFD SET 7,L
            partial(self.set_hl, r, m, 128),                        # CBFE SET 7,(HL)
            partial(self.set_r, r, 128, A),                         # CBFF SET 7,A
        ]

        self.after_DD = [
            partial(self.nop, r, R1, 4, 1),                         # DD00
            partial(self.nop, r, R1, 4, 1),                         # DD01
            partial(self.nop, r, R1, 4, 1),                         # DD02
            partial(self.nop, r, R1, 4, 1),                         # DD03
            partial(self.nop, r, R1, 4, 1),                         # DD04
            partial(self.nop, r, R1, 4, 1),                         # DD05
            partial(self.nop, r, R1, 4, 1),                         # DD06
            partial(self.nop, r, R1, 4, 1),                         # DD07
            partial(self.nop, r, R1, 4, 1),                         # DD08
            partial(self.add_rr, r, R2, 15, 2, IXh, IXl, B, C),     # DD09 ADD IX,BC
            partial(self.nop, r, R1, 4, 1),                         # DD0A
            partial(self.nop, r, R1, 4, 1),                         # DD0B
            partial(self.nop, r, R1, 4, 1),                         # DD0C
            partial(self.nop, r, R1, 4, 1),                         # DD0D
            partial(self.nop, r, R1, 4, 1),                         # DD0E
            partial(self.nop, r, R1, 4, 1),                         # DD0F
            partial(self.nop, r, R1, 4, 1),                         # DD10
            partial(self.nop, r, R1, 4, 1),                         # DD11
            partial(self.nop, r, R1, 4, 1),                         # DD12
            partial(self.nop, r, R1, 4, 1),                         # DD13
            partial(self.nop, r, R1, 4, 1),                         # DD14
            partial(self.nop, r, R1, 4, 1),                         # DD15
            partial(self.nop, r, R1, 4, 1),                         # DD16
            partial(self.nop, r, R1, 4, 1),                         # DD17
            partial(self.nop, r, R1, 4, 1),                         # DD18
            partial(self.add_rr, r, R2, 15, 2, IXh, IXl, D, E),     # DD19 ADD IX,DE
            partial(self.nop, r, R1, 4, 1),                         # DD1A
            partial(self.nop, r, R1, 4, 1),                         # DD1B
            partial(self.nop, r, R1, 4, 1),                         # DD1C
            partial(self.nop, r, R1, 4, 1),                         # DD1D
            partial(self.nop, r, R1, 4, 1),                         # DD1E
            partial(self.nop, r, R1, 4, 1),                         # DD1F
            partial(self.nop, r, R1, 4, 1),                         # DD20
            partial(self.ld_rr_nn, r, m, R2, 14, 4, IXh, IXl),      # DD21 LD IX,nn
            partial(self.ld_mm_rr, r, m, R2, 20, 4, IXh, IXl),      # DD22 LD (nn),IX
            partial(self.inc_dec_rr, r, R2, 10, 2, 1, IXh, IXl),    # DD23 INC IX
            partial(self.fc_r, r, R2, 8, 2, INC, IXh),              # DD24 INC IXh
            partial(self.fc_r, r, R2, 8, 2, DEC, IXh),              # DD25 DEC IXh
            partial(self.ld_r_n, r, m, R2, 11, 3, IXh),             # DD26 LD IXh,n
            partial(self.nop, r, R1, 4, 1),                         # DD27
            partial(self.nop, r, R1, 4, 1),                         # DD28
            partial(self.add_rr, r, R2, 15, 2, IXh, IXl, IXh, IXl), # DD29 ADD IX,IX
            partial(self.ld_rr_mm, r, m, R2, 20, 4, IXh, IXl),      # DD2A LD IX,(nn)
            partial(self.inc_dec_rr, r, R2, 10, 2, -1, IXh, IXl),   # DD2B DEC IX
            partial(self.fc_r, r, R2, 8, 2, INC, IXl),              # DD2C INC IXl
            partial(self.fc_r, r, R2, 8, 2, DEC, IXl),              # DD2D DEC IXl
            partial(self.ld_r_n, r, m, R2, 11, 3, IXl),             # DD2E LD IXl,n
            partial(self.nop, r, R1, 4, 1),                         # DD2F
            partial(self.nop, r, R1, 4, 1),                         # DD30
            partial(self.nop, r, R1, 4, 1),                         # DD31
            partial(self.nop, r, R1, 4, 1),                         # DD32
            partial(self.nop, r, R1, 4, 1),                         # DD33
            partial(self.fc_xy, r, m, 3, INC, IXh, IXl),            # DD34 INC (IX+d)
            partial(self.fc_xy, r, m, 3, DEC, IXh, IXl),            # DD35 DEC (IX+d)
            partial(self.ld_xy_n, r, m, IXh, IXl),                  # DD36 LD (IX+d),n
            partial(self.nop, r, R1, 4, 1),                         # DD37
            partial(self.nop, r, R1, 4, 1),                         # DD38
            partial(self.add_rr, r, R2, 15, 2, IXh, IXl, SP2, SP),  # DD39 ADD IX,SP
            partial(self.nop, r, R1, 4, 1),                         # DD3A
            partial(self.nop, r, R1, 4, 1),                         # DD3B
            partial(self.nop, r, R1, 4, 1),                         # DD3C
            partial(self.nop, r, R1, 4, 1),                         # DD3D
            partial(self.nop, r, R1, 4, 1),                         # DD3E
            partial(self.nop, r, R1, 4, 1),                         # DD3F
            partial(self.nop, r, R1, 4, 1),                         # DD40
            partial(self.nop, r, R1, 4, 1),                         # DD41
            partial(self.nop, r, R1, 4, 1),                         # DD42
            partial(self.nop, r, R1, 4, 1),                         # DD43
            partial(self.ld_r_r, r, R2, 8, 2, B, IXh),              # DD44 LD B,IXh
            partial(self.ld_r_r, r, R2, 8, 2, B, IXl),              # DD45 LD B,IXl
            partial(self.ld_r_xy, r, m, B, IXh, IXl),               # DD46 LD B,(IX+d)
            partial(self.nop, r, R1, 4, 1),                         # DD47
            partial(self.nop, r, R1, 4, 1),                         # DD48
            partial(self.nop, r, R1, 4, 1),                         # DD49
            partial(self.nop, r, R1, 4, 1),                         # DD4A
            partial(self.nop, r, R1, 4, 1),                         # DD4B
            partial(self.ld_r_r, r, R2, 8, 2, C, IXh),              # DD4C LD C,IXh
            partial(self.ld_r_r, r, R2, 8, 2, C, IXl),              # DD4D LD C,IXl
            partial(self.ld_r_xy, r, m, C, IXh, IXl),               # DD4E LD C,(IX+d)
            partial(self.nop, r, R1, 4, 1),                         # DD4F
            partial(self.nop, r, R1, 4, 1),                         # DD50
            partial(self.nop, r, R1, 4, 1),                         # DD51
            partial(self.nop, r, R1, 4, 1),                         # DD52
            partial(self.nop, r, R1, 4, 1),                         # DD53
            partial(self.ld_r_r, r, R2, 8, 2, D, IXh),              # DD54 LD D,IXh
            partial(self.ld_r_r, r, R2, 8, 2, D, IXl),              # DD55 LD D,IXl
            partial(self.ld_r_xy, r, m, D, IXh, IXl),               # DD56 LD D,(IX+d)
            partial(self.nop, r, R1, 4, 1),                         # DD57
            partial(self.nop, r, R1, 4, 1),                         # DD58
            partial(self.nop, r, R1, 4, 1),                         # DD59
            partial(self.nop, r, R1, 4, 1),                         # DD5A
            partial(self.nop, r, R1, 4, 1),                         # DD5B
            partial(self.ld_r_r, r, R2, 8, 2, E, IXh),              # DD5C LD E,IXh
            partial(self.ld_r_r, r, R2, 8, 2, E, IXl),              # DD5D LD E,IXl
            partial(self.ld_r_xy, r, m, E, IXh, IXl),               # DD5E LD E,(IX+d)
            partial(self.nop, r, R1, 4, 1),                         # DD5F
            partial(self.ld_r_r, r, R2, 8, 2, IXh, B),              # DD60 LD IXh,B
            partial(self.ld_r_r, r, R2, 8, 2, IXh, C),              # DD61 LD IXh,C
            partial(self.ld_r_r, r, R2, 8, 2, IXh, D),              # DD62 LD IXh,D
            partial(self.ld_r_r, r, R2, 8, 2, IXh, E),              # DD63 LD IXh,E
            partial(self.nop, r, R2, 8, 2),                         # DD64 LD IXh,IXh
            partial(self.ld_r_r, r, R2, 8, 2, IXh, IXl),            # DD65 LD IXh,IXl
            partial(self.ld_r_xy, r, m, H, IXh, IXl),               # DD66 LD H,(IX+d)
            partial(self.ld_r_r, r, R2, 8, 2, IXh, A),              # DD67 LD IXh,A
            partial(self.ld_r_r, r, R2, 8, 2, IXl, B),              # DD68 LD IXl,B
            partial(self.ld_r_r, r, R2, 8, 2, IXl, C),              # DD69 LD IXl,C
            partial(self.ld_r_r, r, R2, 8, 2, IXl, D),              # DD6A LD IXl,D
            partial(self.ld_r_r, r, R2, 8, 2, IXl, E),              # DD6B LD IXl,E
            partial(self.ld_r_r, r, R2, 8, 2, IXl, IXh),            # DD6C LD IXl,IXh
            partial(self.nop, r, R2, 8, 2),                         # DD6D LD IXl,IXl
            partial(self.ld_r_xy, r, m, L, IXh, IXl),               # DD6E LD L,(IX+d)
            partial(self.ld_r_r, r, R2, 8, 2, IXl, A),              # DD6F LD IXl,A
            partial(self.ld_xy_r, r, m, IXh, IXl, B),               # DD70 LD (IX+d),B
            partial(self.ld_xy_r, r, m, IXh, IXl, C),               # DD71 LD (IX+d),C
            partial(self.ld_xy_r, r, m, IXh, IXl, D),               # DD72 LD (IX+d),D
            partial(self.ld_xy_r, r, m, IXh, IXl, E),               # DD73 LD (IX+d),E
            partial(self.ld_xy_r, r, m, IXh, IXl, H),               # DD74 LD (IX+d),H
            partial(self.ld_xy_r, r, m, IXh, IXl, L),               # DD75 LD (IX+d),L
            partial(self.nop, r, R1, 4, 1),                         # DD76
            partial(self.ld_xy_r, r, m, IXh, IXl, A),               # DD77 LD (IX+d),A
            partial(self.nop, r, R1, 4, 1),                         # DD78
            partial(self.nop, r, R1, 4, 1),                         # DD79
            partial(self.nop, r, R1, 4, 1),                         # DD7A
            partial(self.nop, r, R1, 4, 1),                         # DD7B
            partial(self.ld_r_r, r, R2, 8, 2, A, IXh),              # DD7C LD A,IXh
            partial(self.ld_r_r, r, R2, 8, 2, A, IXl),              # DD7D LD A,IXl
            partial(self.ld_r_xy, r, m, A, IXh, IXl),               # DD7E LD A,(IX+d)
            partial(self.nop, r, R1, 4, 1),                         # DD7F
            partial(self.nop, r, R1, 4, 1),                         # DD80
            partial(self.nop, r, R1, 4, 1),                         # DD81
            partial(self.nop, r, R1, 4, 1),                         # DD82
            partial(self.nop, r, R1, 4, 1),                         # DD83
            partial(self.af_r, r, R2, 8, 2, ADD, IXh),              # DD84 ADD A,IXh
            partial(self.af_r, r, R2, 8, 2, ADD, IXl),              # DD85 ADD A,IXl
            partial(self.af_xy, r, m, ADD, IXh, IXl),               # DD86 ADD A,(IX+d)
            partial(self.nop, r, R1, 4, 1),                         # DD87
            partial(self.nop, r, R1, 4, 1),                         # DD88
            partial(self.nop, r, R1, 4, 1),                         # DD89
            partial(self.nop, r, R1, 4, 1),                         # DD8A
            partial(self.nop, r, R1, 4, 1),                         # DD8B
            partial(self.afc_r, r, R2, 8, 2, ADC, IXh),             # DD8C ADC A,IXh
            partial(self.afc_r, r, R2, 8, 2, ADC, IXl),             # DD8D ADC A,IXl
            partial(self.afc_xy, r, m, ADC, IXh, IXl),              # DD8E ADC A,(IX+d)
            partial(self.nop, r, R1, 4, 1),                         # DD8F
            partial(self.nop, r, R1, 4, 1),                         # DD90
            partial(self.nop, r, R1, 4, 1),                         # DD91
            partial(self.nop, r, R1, 4, 1),                         # DD92
            partial(self.nop, r, R1, 4, 1),                         # DD93
            partial(self.af_r, r, R2, 8, 2, SUB, IXh),              # DD94 SUB IXh
            partial(self.af_r, r, R2, 8, 2, SUB, IXl),              # DD95 SUB IXl
            partial(self.af_xy, r, m, SUB, IXh, IXl),               # DD96 SUB (IX+d)
            partial(self.nop, r, R1, 4, 1),                         # DD97
            partial(self.nop, r, R1, 4, 1),                         # DD98
            partial(self.nop, r, R1, 4, 1),                         # DD99
            partial(self.nop, r, R1, 4, 1),                         # DD9A
            partial(self.nop, r, R1, 4, 1),                         # DD9B
            partial(self.afc_r, r, R2, 8, 2, SBC, IXh),             # DD9C SBC A,IXh
            partial(self.afc_r, r, R2, 8, 2, SBC, IXl),             # DD9D SBC A,IXl
            partial(self.afc_xy, r, m, SBC, IXh, IXl),              # DD9E SBC A,(IX+d)
            partial(self.nop, r, R1, 4, 1),                         # DD9F
            partial(self.nop, r, R1, 4, 1),                         # DDA0
            partial(self.nop, r, R1, 4, 1),                         # DDA1
            partial(self.nop, r, R1, 4, 1),                         # DDA2
            partial(self.nop, r, R1, 4, 1),                         # DDA3
            partial(self.af_r, r, R2, 8, 2, AND, IXh),              # DDA4 AND IXh
            partial(self.af_r, r, R2, 8, 2, AND, IXl),              # DDA5 AND IXl
            partial(self.af_xy, r, m, AND, IXh, IXl),               # DDA6 AND (IX+d)
            partial(self.nop, r, R1, 4, 1),                         # DDA7
            partial(self.nop, r, R1, 4, 1),                         # DDA8
            partial(self.nop, r, R1, 4, 1),                         # DDA9
            partial(self.nop, r, R1, 4, 1),                         # DDAA
            partial(self.nop, r, R1, 4, 1),                         # DDAB
            partial(self.af_r, r, R2, 8, 2, XOR, IXh),              # DDAC XOR IXh
            partial(self.af_r, r, R2, 8, 2, XOR, IXl),              # DDAD XOR IXl
            partial(self.af_xy, r, m, XOR, IXh, IXl),               # DDAE XOR (IX+d)
            partial(self.nop, r, R1, 4, 1),                         # DDAF
            partial(self.nop, r, R1, 4, 1),                         # DDB0
            partial(self.nop, r, R1, 4, 1),                         # DDB1
            partial(self.nop, r, R1, 4, 1),                         # DDB2
            partial(self.nop, r, R1, 4, 1),                         # DDB3
            partial(self.af_r, r, R2, 8, 2, OR, IXh),               # DDB4 OR IXh
            partial(self.af_r, r, R2, 8, 2, OR, IXl),               # DDB5 OR IXl
            partial(self.af_xy, r, m, OR, IXh, IXl),                # DDB6 OR (IX+d)
            partial(self.nop, r, R1, 4, 1),                         # DDB7
            partial(self.nop, r, R1, 4, 1),                         # DDB8
            partial(self.nop, r, R1, 4, 1),                         # DDB9
            partial(self.nop, r, R1, 4, 1),                         # DDBA
            partial(self.nop, r, R1, 4, 1),                         # DDBB
            partial(self.af_r, r, R2, 8, 2, CP, IXh),               # DDBC CP IXh
            partial(self.af_r, r, R2, 8, 2, CP, IXl),               # DDBD CP IXl
            partial(self.af_xy, r, m, CP, IXh, IXl),                # DDBE CP (IX+d)
            partial(self.nop, r, R1, 4, 1),                         # DDBF
            partial(self.nop, r, R1, 4, 1),                         # DDC0
            partial(self.nop, r, R1, 4, 1),                         # DDC1
            partial(self.nop, r, R1, 4, 1),                         # DDC2
            partial(self.nop, r, R1, 4, 1),                         # DDC3
            partial(self.nop, r, R1, 4, 1),                         # DDC4
            partial(self.nop, r, R1, 4, 1),                         # DDC5
            partial(self.nop, r, R1, 4, 1),                         # DDC6
            partial(self.nop, r, R1, 4, 1),                         # DDC7
            partial(self.nop, r, R1, 4, 1),                         # DDC8
            partial(self.nop, r, R1, 4, 1),                         # DDC9
            partial(self.nop, r, R1, 4, 1),                         # DDCA
            partial(self.prefix2, self.after_DDCB, r, m),           # DDCB prefix
            partial(self.nop, r, R1, 4, 1),                         # DDCC
            partial(self.nop, r, R1, 4, 1),                         # DDCD
            partial(self.nop, r, R1, 4, 1),                         # DDCE
            partial(self.nop, r, R1, 4, 1),                         # DDCF
            partial(self.nop, r, R1, 4, 1),                         # DDD0
            partial(self.nop, r, R1, 4, 1),                         # DDD1
            partial(self.nop, r, R1, 4, 1),                         # DDD2
            partial(self.nop, r, R1, 4, 1),                         # DDD3
            partial(self.nop, r, R1, 4, 1),                         # DDD4
            partial(self.nop, r, R1, 4, 1),                         # DDD5
            partial(self.nop, r, R1, 4, 1),                         # DDD6
            partial(self.nop, r, R1, 4, 1),                         # DDD7
            partial(self.nop, r, R1, 4, 1),                         # DDD8
            partial(self.nop, r, R1, 4, 1),                         # DDD9
            partial(self.nop, r, R1, 4, 1),                         # DDDA
            partial(self.nop, r, R1, 4, 1),                         # DDDB
            partial(self.nop, r, R1, 4, 1),                         # DDDC
            partial(self.nop, r, R1, 4, 1),                         # DDDD
            partial(self.nop, r, R1, 4, 1),                         # DDDE
            partial(self.nop, r, R1, 4, 1),                         # DDDF
            partial(self.nop, r, R1, 4, 1),                         # DDE0
            partial(self.pop, r, m, R2, 14, 2, IXh, IXl),           # DDE1 POP IX
            partial(self.nop, r, R1, 4, 1),                         # DDE2
            partial(self.ex_sp, r, m, R2, 23, 2, IXh, IXl),         # DDE3 EX (SP),IX
            partial(self.nop, r, R1, 4, 1),                         # DDE4
            partial(self.push, r, m, R2, 15, 2, IXh, IXl),          # DDE5 PUSH IX
            partial(self.nop, r, R1, 4, 1),                         # DDE6
            partial(self.nop, r, R1, 4, 1),                         # DDE7
            partial(self.nop, r, R1, 4, 1),                         # DDE8
            partial(self.jp_rr, r, R2, 8, IXh, IXl),                # DDE9 JP (IX)
            partial(self.nop, r, R1, 4, 1),                         # DDEA
            partial(self.nop, r, R1, 4, 1),                         # DDEB
            partial(self.nop, r, R1, 4, 1),                         # DDEC
            partial(self.nop, r, R1, 4, 1),                         # DDED
            partial(self.nop, r, R1, 4, 1),                         # DDEE
            partial(self.nop, r, R1, 4, 1),                         # DDEF
            partial(self.nop, r, R1, 4, 1),                         # DDF0
            partial(self.nop, r, R1, 4, 1),                         # DDF1
            partial(self.nop, r, R1, 4, 1),                         # DDF2
            partial(self.nop, r, R1, 4, 1),                         # DDF3
            partial(self.nop, r, R1, 4, 1),                         # DDF4
            partial(self.nop, r, R1, 4, 1),                         # DDF5
            partial(self.nop, r, R1, 4, 1),                         # DDF6
            partial(self.nop, r, R1, 4, 1),                         # DDF7
            partial(self.nop, r, R1, 4, 1),                         # DDF8
            partial(self.ld_sp_rr, r, R2, 10, 2, IXh, IXl),         # DDF9 LD SP,IX
            partial(self.nop, r, R1, 4, 1),                         # DDFA
            partial(self.nop, r, R1, 4, 1),                         # DDFB
            partial(self.nop, r, R1, 4, 1),                         # DDFC
            partial(self.nop, r, R1, 4, 1),                         # DDFD
            partial(self.nop, r, R1, 4, 1),                         # DDFE
            partial(self.nop, r, R1, 4, 1),                         # DDFF
        ]

        self.after_ED = [
            partial(self.nop, r, R2, 8, 2),                         # ED00
            partial(self.nop, r, R2, 8, 2),                         # ED01
            partial(self.nop, r, R2, 8, 2),                         # ED02
            partial(self.nop, r, R2, 8, 2),                         # ED03
            partial(self.nop, r, R2, 8, 2),                         # ED04
            partial(self.nop, r, R2, 8, 2),                         # ED05
            partial(self.nop, r, R2, 8, 2),                         # ED06
            partial(self.nop, r, R2, 8, 2),                         # ED07
            partial(self.nop, r, R2, 8, 2),                         # ED08
            partial(self.nop, r, R2, 8, 2),                         # ED09
            partial(self.nop, r, R2, 8, 2),                         # ED0A
            partial(self.nop, r, R2, 8, 2),                         # ED0B
            partial(self.nop, r, R2, 8, 2),                         # ED0C
            partial(self.nop, r, R2, 8, 2),                         # ED0D
            partial(self.nop, r, R2, 8, 2),                         # ED0E
            partial(self.nop, r, R2, 8, 2),                         # ED0F
            partial(self.nop, r, R2, 8, 2),                         # ED10
            partial(self.nop, r, R2, 8, 2),                         # ED11
            partial(self.nop, r, R2, 8, 2),                         # ED12
            partial(self.nop, r, R2, 8, 2),                         # ED13
            partial(self.nop, r, R2, 8, 2),                         # ED14
            partial(self.nop, r, R2, 8, 2),                         # ED15
            partial(self.nop, r, R2, 8, 2),                         # ED16
            partial(self.nop, r, R2, 8, 2),                         # ED17
            partial(self.nop, r, R2, 8, 2),                         # ED18
            partial(self.nop, r, R2, 8, 2),                         # ED19
            partial(self.nop, r, R2, 8, 2),                         # ED1A
            partial(self.nop, r, R2, 8, 2),                         # ED1B
            partial(self.nop, r, R2, 8, 2),                         # ED1C
            partial(self.nop, r, R2, 8, 2),                         # ED1D
            partial(self.nop, r, R2, 8, 2),                         # ED1E
            partial(self.nop, r, R2, 8, 2),                         # ED1F
            partial(self.nop, r, R2, 8, 2),                         # ED20
            partial(self.nop, r, R2, 8, 2),                         # ED21
            partial(self.nop, r, R2, 8, 2),                         # ED22
            partial(self.nop, r, R2, 8, 2),                         # ED23
            partial(self.nop, r, R2, 8, 2),                         # ED24
            partial(self.nop, r, R2, 8, 2),                         # ED25
            partial(self.nop, r, R2, 8, 2),                         # ED26
            partial(self.nop, r, R2, 8, 2),                         # ED27
            partial(self.nop, r, R2, 8, 2),                         # ED28
            partial(self.nop, r, R2, 8, 2),                         # ED29
            partial(self.nop, r, R2, 8, 2),                         # ED2A
            partial(self.nop, r, R2, 8, 2),                         # ED2B
            partial(self.nop, r, R2, 8, 2),                         # ED2C
            partial(self.nop, r, R2, 8, 2),                         # ED2D
            partial(self.nop, r, R2, 8, 2),                         # ED2E
            partial(self.nop, r, R2, 8, 2),                         # ED2F
            partial(self.nop, r, R2, 8, 2),                         # ED30
            partial(self.nop, r, R2, 8, 2),                         # ED31
            partial(self.nop, r, R2, 8, 2),                         # ED32
            partial(self.nop, r, R2, 8, 2),                         # ED33
            partial(self.nop, r, R2, 8, 2),                         # ED34
            partial(self.nop, r, R2, 8, 2),                         # ED35
            partial(self.nop, r, R2, 8, 2),                         # ED36
            partial(self.nop, r, R2, 8, 2),                         # ED37
            partial(self.nop, r, R2, 8, 2),                         # ED38
            partial(self.nop, r, R2, 8, 2),                         # ED39
            partial(self.nop, r, R2, 8, 2),                         # ED3A
            partial(self.nop, r, R2, 8, 2),                         # ED3B
            partial(self.nop, r, R2, 8, 2),                         # ED3C
            partial(self.nop, r, R2, 8, 2),                         # ED3D
            partial(self.nop, r, R2, 8, 2),                         # ED3E
            partial(self.nop, r, R2, 8, 2),                         # ED3F
            partial(self.in_c, r, B, SZ53P),                        # ED40 IN B,(C)
            partial(self.out_c, r, B),                              # ED41 OUT (C),B
            partial(self.sbc_hl, r, B, C),                          # ED42 SBC HL,BC
            partial(self.ld_mm_rr, r, m, R2, 20, 4, B, C),          # ED43 LD (nn),BC
            partial(self.neg, r, NEG),                              # ED44 NEG
            partial(self.reti, r, m),                               # ED45 RETN
            partial(self.im, r, 0),                                 # ED46 IM 0
            partial(self.ld_r_r, r, R2, 9, 2, I, A),                # ED47 LD I,A
            partial(self.in_c, r, C, SZ53P),                        # ED48 IN C,(C)
            partial(self.out_c, r, C),                              # ED49 OUT (C),C
            partial(self.adc_hl, r, B, C),                          # ED4A ADC HL,BC
            partial(self.ld_rr_mm, r, m, R2, 20, 4, B, C),          # ED4B LD BC,(nn)
            partial(self.neg, r, NEG),                              # ED4C NEG
            partial(self.reti, r, m),                               # ED4D RETI
            partial(self.im, r, 0),                                 # ED4E IM 0
            partial(self.ld_r_r, r, R2, 9, 2, R, A),                # ED4F LD R,A
            partial(self.in_c, r, D, SZ53P),                        # ED50 IN D,(C)
            partial(self.out_c, r, D),                              # ED51 OUT (C),D
            partial(self.sbc_hl, r, D, E),                          # ED52 SBC HL,DE
            partial(self.ld_mm_rr, r, m, R2, 20, 4, D, E),          # ED53 LD (nn),DE
            partial(self.neg, r, NEG),                              # ED54 NEG
            partial(self.reti, r, m),                               # ED55 RETN
            partial(self.im, r, 1),                                 # ED56 IM 1
            partial(self.ld_a_ir, r, I),                            # ED57 LD A,I
            partial(self.in_c, r, E, SZ53P),                        # ED58 IN E,(C)
            partial(self.out_c, r, E),                              # ED59 OUT (C),E
            partial(self.adc_hl, r, D, E),                          # ED5A ADC HL,DE
            partial(self.ld_rr_mm, r, m, R2, 20, 4, D, E),          # ED5B LD DE,(nn)
            partial(self.neg, r, NEG),                              # ED5C NEG
            partial(self.reti, r, m),                               # ED5D RETN
            partial(self.im, r, 2),                                 # ED5E IM 2
            partial(self.ld_a_ir, r, R),                            # ED5F LD A,R
            partial(self.in_c, r, H, SZ53P),                        # ED60 IN H,(C)
            partial(self.out_c, r, H),                              # ED61 OUT (C),H
            partial(self.sbc_hl, r, H, L),                          # ED62 SBC HL,HL
            partial(self.ld_mm_rr, r, m, R2, 20, 4, H, L),          # ED63 LD (nn),HL
            partial(self.neg, r, NEG),                              # ED64 NEG
            partial(self.reti, r, m),                               # ED65 RETN
            partial(self.im, r, 0),                                 # ED66 IM 0
            partial(self.rrd, r, m, SZ53P),                         # ED67 RRD
            partial(self.in_c, r, L, SZ53P),                        # ED68 IN L,(C)
            partial(self.out_c, r, L),                              # ED69 OUT (C),L
            partial(self.adc_hl, r, H, L),                          # ED6A ADC HL,HL
            partial(self.ld_rr_mm, r, m, R2, 20, 4, H, L),          # ED6B LD HL,(nn)
            partial(self.neg, r, NEG),                              # ED6C NEG
            partial(self.reti, r, m),                               # ED6D RETN
            partial(self.im, r, 0),                                 # ED6E IM 0
            partial(self.rld, r, m, SZ53P),                         # ED6F RLD
            partial(self.in_c, r, F, SZ53P),                        # ED70 IN F,(C)
            partial(self.out_c, r, -1),                             # ED71 OUT (C),0
            partial(self.sbc_hl, r, SP2, SP),                       # ED72 SBC HL,SP
            partial(self.ld_mm_rr, r, m, R2, 20, 4, SP2, SP),       # ED73 LD (nn),SP
            partial(self.neg, r, NEG),                              # ED74 NEG
            partial(self.reti, r, m),                               # ED75 RETN
            partial(self.im, r, 1),                                 # ED76 IM 1
            partial(self.nop, r, R2, 8, 2),                         # ED77
            partial(self.in_c, r, A, SZ53P),                        # ED78 IN A,(C)
            partial(self.out_c, r, A),                              # ED79 OUT (C),A
            partial(self.adc_hl, r, SP2, SP),                       # ED7A ADC HL,SP
            partial(self.ld_rr_mm, r, m, R2, 20, 4, SP2, SP),       # ED7B LD SP,(nn)
            partial(self.neg, r, NEG),                              # ED7C NEG
            partial(self.reti, r, m),                               # ED7D RETN
            partial(self.im, r, 2),                                 # ED7E IM 2
            partial(self.nop, r, R2, 8, 2),                         # ED7F
            partial(self.nop, r, R2, 8, 2),                         # ED80
            partial(self.nop, r, R2, 8, 2),                         # ED81
            partial(self.nop, r, R2, 8, 2),                         # ED82
            partial(self.nop, r, R2, 8, 2),                         # ED83
            partial(self.nop, r, R2, 8, 2),                         # ED84
            partial(self.nop, r, R2, 8, 2),                         # ED85
            partial(self.nop, r, R2, 8, 2),                         # ED86
            partial(self.nop, r, R2, 8, 2),                         # ED87
            partial(self.nop, r, R2, 8, 2),                         # ED88
            partial(self.nop, r, R2, 8, 2),                         # ED89
            partial(self.nop, r, R2, 8, 2),                         # ED8A
            partial(self.nop, r, R2, 8, 2),                         # ED8B
            partial(self.nop, r, R2, 8, 2),                         # ED8C
            partial(self.nop, r, R2, 8, 2),                         # ED8D
            partial(self.nop, r, R2, 8, 2),                         # ED8E
            partial(self.nop, r, R2, 8, 2),                         # ED8F
            partial(self.nop, r, R2, 8, 2),                         # ED90
            partial(self.nop, r, R2, 8, 2),                         # ED91
            partial(self.nop, r, R2, 8, 2),                         # ED92
            partial(self.nop, r, R2, 8, 2),                         # ED93
            partial(self.nop, r, R2, 8, 2),                         # ED94
            partial(self.nop, r, R2, 8, 2),                         # ED95
            partial(self.nop, r, R2, 8, 2),                         # ED96
            partial(self.nop, r, R2, 8, 2),                         # ED97
            partial(self.nop, r, R2, 8, 2),                         # ED98
            partial(self.nop, r, R2, 8, 2),                         # ED99
            partial(self.nop, r, R2, 8, 2),                         # ED9A
            partial(self.nop, r, R2, 8, 2),                         # ED9B
            partial(self.nop, r, R2, 8, 2),                         # ED9C
            partial(self.nop, r, R2, 8, 2),                         # ED9D
            partial(self.nop, r, R2, 8, 2),                         # ED9E
            partial(self.nop, r, R2, 8, 2),                         # ED9F
            partial(self.ldi, r, m, 1, 0),                          # EDA0 LDI
            partial(self.cpi, r, m, 1, 0),                          # EDA1 CPI
            partial(self.ini, r, m, 1, 0, PARITY),                  # EDA2 INI
            partial(self.outi, r, m, 1, 0, PARITY),                 # EDA3 OUTI
            partial(self.nop, r, R2, 8, 2),                         # EDA4
            partial(self.nop, r, R2, 8, 2),                         # EDA5
            partial(self.nop, r, R2, 8, 2),                         # EDA6
            partial(self.nop, r, R2, 8, 2),                         # EDA7
            partial(self.ldi, r, m, -1, 0),                         # EDA8 LDD
            partial(self.cpi, r, m, -1, 0),                         # EDA9 CPD
            partial(self.ini, r, m, -1, 0, PARITY),                 # EDAA IND
            partial(self.outi, r, m, -1, 0, PARITY),                # EDAB OUTD
            partial(self.nop, r, R2, 8, 2),                         # EDAC
            partial(self.nop, r, R2, 8, 2),                         # EDAD
            partial(self.nop, r, R2, 8, 2),                         # EDAE
            partial(self.nop, r, R2, 8, 2),                         # EDAF
            partial(self.ldi, r, m, 1, 1),                          # EDB0 LDIR
            partial(self.cpi, r, m, 1, 1),                          # EDB1 CPIR
            partial(self.ini, r, m, 1, 1, PARITY),                  # EDB2 INIR
            partial(self.outi, r, m, 1, 1, PARITY),                 # EDB3 OTIR
            partial(self.nop, r, R2, 8, 2),                         # EDB4
            partial(self.nop, r, R2, 8, 2),                         # EDB5
            partial(self.nop, r, R2, 8, 2),                         # EDB6
            partial(self.nop, r, R2, 8, 2),                         # EDB7
            partial(self.ldi, r, m, -1, 1),                         # EDB8 LDDR
            partial(self.cpi, r, m, -1, 1),                         # EDB9 CPDR
            partial(self.ini, r, m, -1, 1, PARITY),                 # EDBA INDR
            partial(self.outi, r, m, -1, 1, PARITY),                # EDBB OTDR
            partial(self.nop, r, R2, 8, 2),                         # EDBC
            partial(self.nop, r, R2, 8, 2),                         # EDBD
            partial(self.nop, r, R2, 8, 2),                         # EDBE
            partial(self.nop, r, R2, 8, 2),                         # EDBF
            partial(self.nop, r, R2, 8, 2),                         # EDC0
            partial(self.nop, r, R2, 8, 2),                         # EDC1
            partial(self.nop, r, R2, 8, 2),                         # EDC2
            partial(self.nop, r, R2, 8, 2),                         # EDC3
            partial(self.nop, r, R2, 8, 2),                         # EDC4
            partial(self.nop, r, R2, 8, 2),                         # EDC5
            partial(self.nop, r, R2, 8, 2),                         # EDC6
            partial(self.nop, r, R2, 8, 2),                         # EDC7
            partial(self.nop, r, R2, 8, 2),                         # EDC8
            partial(self.nop, r, R2, 8, 2),                         # EDC9
            partial(self.nop, r, R2, 8, 2),                         # EDCA
            partial(self.nop, r, R2, 8, 2),                         # EDCB
            partial(self.nop, r, R2, 8, 2),                         # EDCC
            partial(self.nop, r, R2, 8, 2),                         # EDCD
            partial(self.nop, r, R2, 8, 2),                         # EDCE
            partial(self.nop, r, R2, 8, 2),                         # EDCF
            partial(self.nop, r, R2, 8, 2),                         # EDD0
            partial(self.nop, r, R2, 8, 2),                         # EDD1
            partial(self.nop, r, R2, 8, 2),                         # EDD2
            partial(self.nop, r, R2, 8, 2),                         # EDD3
            partial(self.nop, r, R2, 8, 2),                         # EDD4
            partial(self.nop, r, R2, 8, 2),                         # EDD5
            partial(self.nop, r, R2, 8, 2),                         # EDD6
            partial(self.nop, r, R2, 8, 2),                         # EDD7
            partial(self.nop, r, R2, 8, 2),                         # EDD8
            partial(self.nop, r, R2, 8, 2),                         # EDD9
            partial(self.nop, r, R2, 8, 2),                         # EDDA
            partial(self.nop, r, R2, 8, 2),                         # EDDB
            partial(self.nop, r, R2, 8, 2),                         # EDDC
            partial(self.nop, r, R2, 8, 2),                         # EDDD
            partial(self.nop, r, R2, 8, 2),                         # EDDE
            partial(self.nop, r, R2, 8, 2),                         # EDDF
            partial(self.nop, r, R2, 8, 2),                         # EDE0
            partial(self.nop, r, R2, 8, 2),                         # EDE1
            partial(self.nop, r, R2, 8, 2),                         # EDE2
            partial(self.nop, r, R2, 8, 2),                         # EDE3
            partial(self.nop, r, R2, 8, 2),                         # EDE4
            partial(self.nop, r, R2, 8, 2),                         # EDE5
            partial(self.nop, r, R2, 8, 2),                         # EDE6
            partial(self.nop, r, R2, 8, 2),                         # EDE7
            partial(self.nop, r, R2, 8, 2),                         # EDE8
            partial(self.nop, r, R2, 8, 2),                         # EDE9
            partial(self.nop, r, R2, 8, 2),                         # EDEA
            partial(self.nop, r, R2, 8, 2),                         # EDEB
            partial(self.nop, r, R2, 8, 2),                         # EDEC
            partial(self.nop, r, R2, 8, 2),                         # EDED
            partial(self.nop, r, R2, 8, 2),                         # EDEE
            partial(self.nop, r, R2, 8, 2),                         # EDEF
            partial(self.nop, r, R2, 8, 2),                         # EDF0
            partial(self.nop, r, R2, 8, 2),                         # EDF1
            partial(self.nop, r, R2, 8, 2),                         # EDF2
            partial(self.nop, r, R2, 8, 2),                         # EDF3
            partial(self.nop, r, R2, 8, 2),                         # EDF4
            partial(self.nop, r, R2, 8, 2),                         # EDF5
            partial(self.nop, r, R2, 8, 2),                         # EDF6
            partial(self.nop, r, R2, 8, 2),                         # EDF7
            partial(self.nop, r, R2, 8, 2),                         # EDF8
            partial(self.nop, r, R2, 8, 2),                         # EDF9
            partial(self.nop, r, R2, 8, 2),                         # EDFA
            partial(self.nop, r, R2, 8, 2),                         # EDFB
            partial(self.nop, r, R2, 8, 2),                         # EDFC
            partial(self.nop, r, R2, 8, 2),                         # EDFD
            partial(self.nop, r, R2, 8, 2),                         # EDFE
            partial(self.nop, r, R2, 8, 2),                         # EDFF
        ]

        self.after_FD = [
            partial(self.nop, r, R1, 4, 1),                         # FD00
            partial(self.nop, r, R1, 4, 1),                         # FD01
            partial(self.nop, r, R1, 4, 1),                         # FD02
            partial(self.nop, r, R1, 4, 1),                         # FD03
            partial(self.nop, r, R1, 4, 1),                         # FD04
            partial(self.nop, r, R1, 4, 1),                         # FD05
            partial(self.nop, r, R1, 4, 1),                         # FD06
            partial(self.nop, r, R1, 4, 1),                         # FD07
            partial(self.nop, r, R1, 4, 1),                         # FD08
            partial(self.add_rr, r, R2, 15, 2, IYh, IYl, B, C),     # FD09 ADD IY,BC
            partial(self.nop, r, R1, 4, 1),                         # FD0A
            partial(self.nop, r, R1, 4, 1),                         # FD0B
            partial(self.nop, r, R1, 4, 1),                         # FD0C
            partial(self.nop, r, R1, 4, 1),                         # FD0D
            partial(self.nop, r, R1, 4, 1),                         # FD0E
            partial(self.nop, r, R1, 4, 1),                         # FD0F
            partial(self.nop, r, R1, 4, 1),                         # FD10
            partial(self.nop, r, R1, 4, 1),                         # FD11
            partial(self.nop, r, R1, 4, 1),                         # FD12
            partial(self.nop, r, R1, 4, 1),                         # FD13
            partial(self.nop, r, R1, 4, 1),                         # FD14
            partial(self.nop, r, R1, 4, 1),                         # FD15
            partial(self.nop, r, R1, 4, 1),                         # FD16
            partial(self.nop, r, R1, 4, 1),                         # FD17
            partial(self.nop, r, R1, 4, 1),                         # FD18
            partial(self.add_rr, r, R2, 15, 2, IYh, IYl, D, E),     # FD19 ADD IY,DE
            partial(self.nop, r, R1, 4, 1),                         # FD1A
            partial(self.nop, r, R1, 4, 1),                         # FD1B
            partial(self.nop, r, R1, 4, 1),                         # FD1C
            partial(self.nop, r, R1, 4, 1),                         # FD1D
            partial(self.nop, r, R1, 4, 1),                         # FD1E
            partial(self.nop, r, R1, 4, 1),                         # FD1F
            partial(self.nop, r, R1, 4, 1),                         # FD20
            partial(self.ld_rr_nn, r, m, R2, 14, 4, IYh, IYl),      # FD21 LD IY,nn
            partial(self.ld_mm_rr, r, m, R2, 20, 4, IYh, IYl),      # FD22 LD (nn),IY
            partial(self.inc_dec_rr, r, R2, 10, 2, 1, IYh, IYl),    # FD23 INC IY
            partial(self.fc_r, r, R2, 8, 2, INC, IYh),              # FD24 INC IYh
            partial(self.fc_r, r, R2, 8, 2, DEC, IYh),              # FD25 DEC IYh
            partial(self.ld_r_n, r, m, R2, 11, 3, IYh),             # FD26 LD IYh,n
            partial(self.nop, r, R1, 4, 1),                         # FD27
            partial(self.nop, r, R1, 4, 1),                         # FD28
            partial(self.add_rr, r, R2, 15, 2, IYh, IYl, IYh, IYl), # FD29 ADD IY,IY
            partial(self.ld_rr_mm, r, m, R2, 20, 4, IYh, IYl),      # FD2A LD IY,(nn)
            partial(self.inc_dec_rr, r, R2, 10, 2, -1, IYh, IYl),   # FD2B DEC IY
            partial(self.fc_r, r, R2, 8, 2, INC, IYl),              # FD2C INC IYl
            partial(self.fc_r, r, R2, 8, 2, DEC, IYl),              # FD2D DEC IYl
            partial(self.ld_r_n, r, m, R2, 11, 3, IYl),             # FD2E LD IYl,n
            partial(self.nop, r, R1, 4, 1),                         # FD2F
            partial(self.nop, r, R1, 4, 1),                         # FD30
            partial(self.nop, r, R1, 4, 1),                         # FD31
            partial(self.nop, r, R1, 4, 1),                         # FD32
            partial(self.nop, r, R1, 4, 1),                         # FD33
            partial(self.fc_xy, r, m, 3, INC, IYh, IYl),            # FD34 INC (IY+d)
            partial(self.fc_xy, r, m, 3, DEC, IYh, IYl),            # FD35 DEC (IY+d)
            partial(self.ld_xy_n, r, m, IYh, IYl),                  # FD36 LD (IY+d),n
            partial(self.nop, r, R1, 4, 1),                         # FD37
            partial(self.nop, r, R1, 4, 1),                         # FD38
            partial(self.add_rr, r, R2, 15, 2, IYh, IYl, SP2, SP),  # FD39 ADD IY,SP
            partial(self.nop, r, R1, 4, 1),                         # FD3A
            partial(self.nop, r, R1, 4, 1),                         # FD3B
            partial(self.nop, r, R1, 4, 1),                         # FD3C
            partial(self.nop, r, R1, 4, 1),                         # FD3D
            partial(self.nop, r, R1, 4, 1),                         # FD3E
            partial(self.nop, r, R1, 4, 1),                         # FD3F
            partial(self.nop, r, R1, 4, 1),                         # FD40
            partial(self.nop, r, R1, 4, 1),                         # FD41
            partial(self.nop, r, R1, 4, 1),                         # FD42
            partial(self.nop, r, R1, 4, 1),                         # FD43
            partial(self.ld_r_r, r, R2, 8, 2, B, IYh),              # FD44 LD B,IYh
            partial(self.ld_r_r, r, R2, 8, 2, B, IYl),              # FD45 LD B,IYl
            partial(self.ld_r_xy, r, m, B, IYh, IYl),               # FD46 LD B,(IY+d)
            partial(self.nop, r, R1, 4, 1),                         # FD47
            partial(self.nop, r, R1, 4, 1),                         # FD48
            partial(self.nop, r, R1, 4, 1),                         # FD49
            partial(self.nop, r, R1, 4, 1),                         # FD4A
            partial(self.nop, r, R1, 4, 1),                         # FD4B
            partial(self.ld_r_r, r, R2, 8, 2, C, IYh),              # FD4C LD C,IYh
            partial(self.ld_r_r, r, R2, 8, 2, C, IYl),              # FD4D LD C,IYl
            partial(self.ld_r_xy, r, m, C, IYh, IYl),               # FD4E LD C,(IY+d)
            partial(self.nop, r, R1, 4, 1),                         # FD4F
            partial(self.nop, r, R1, 4, 1),                         # FD50
            partial(self.nop, r, R1, 4, 1),                         # FD51
            partial(self.nop, r, R1, 4, 1),                         # FD52
            partial(self.nop, r, R1, 4, 1),                         # FD53
            partial(self.ld_r_r, r, R2, 8, 2, D, IYh),              # FD54 LD D,IYh
            partial(self.ld_r_r, r, R2, 8, 2, D, IYl),              # FD55 LD D,IYl
            partial(self.ld_r_xy, r, m, D, IYh, IYl),               # FD56 LD D,(IY+d)
            partial(self.nop, r, R1, 4, 1),                         # FD57
            partial(self.nop, r, R1, 4, 1),                         # FD58
            partial(self.nop, r, R1, 4, 1),                         # FD59
            partial(self.nop, r, R1, 4, 1),                         # FD5A
            partial(self.nop, r, R1, 4, 1),                         # FD5B
            partial(self.ld_r_r, r, R2, 8, 2, E, IYh),              # FD5C LD E,IYh
            partial(self.ld_r_r, r, R2, 8, 2, E, IYl),              # FD5D LD E,IYl
            partial(self.ld_r_xy, r, m, E, IYh, IYl),               # FD5E LD E,(IY+d)
            partial(self.nop, r, R1, 4, 1),                         # FD5F
            partial(self.ld_r_r, r, R2, 8, 2, IYh, B),              # FD60 LD IYh,B
            partial(self.ld_r_r, r, R2, 8, 2, IYh, C),              # FD61 LD IYh,C
            partial(self.ld_r_r, r, R2, 8, 2, IYh, D),              # FD62 LD IYh,D
            partial(self.ld_r_r, r, R2, 8, 2, IYh, E),              # FD63 LD IYh,E
            partial(self.nop, r, R2, 8, 2),                         # FD64 LD IYh,IYh
            partial(self.ld_r_r, r, R2, 8, 2, IYh, IYl),            # FD65 LD IYh,IYl
            partial(self.ld_r_xy, r, m, H, IYh, IYl),               # FD66 LD H,(IY+d)
            partial(self.ld_r_r, r, R2, 8, 2, IYh, A),              # FD67 LD IYh,A
            partial(self.ld_r_r, r, R2, 8, 2, IYl, B),              # FD68 LD IYl,B
            partial(self.ld_r_r, r, R2, 8, 2, IYl, C),              # FD69 LD IYl,C
            partial(self.ld_r_r, r, R2, 8, 2, IYl, D),              # FD6A LD IYl,D
            partial(self.ld_r_r, r, R2, 8, 2, IYl, E),              # FD6B LD IYl,E
            partial(self.ld_r_r, r, R2, 8, 2, IYl, IYh),            # FD6C LD IYl,IYh
            partial(self.nop, r, R2, 8, 2),                         # FD6D LD IYl,IYl
            partial(self.ld_r_xy, r, m, L, IYh, IYl),               # FD6E LD L,(IY+d)
            partial(self.ld_r_r, r, R2, 8, 2, IYl, A),              # FD6F LD IYl,A
            partial(self.ld_xy_r, r, m, IYh, IYl, B),               # FD70 LD (IY+d),B
            partial(self.ld_xy_r, r, m, IYh, IYl, C),               # FD71 LD (IY+d),C
            partial(self.ld_xy_r, r, m, IYh, IYl, D),               # FD72 LD (IY+d),D
            partial(self.ld_xy_r, r, m, IYh, IYl, E),               # FD73 LD (IY+d),E
            partial(self.ld_xy_r, r, m, IYh, IYl, H),               # FD74 LD (IY+d),H
            partial(self.ld_xy_r, r, m, IYh, IYl, L),               # FD75 LD (IY+d),L
            partial(self.nop, r, R1, 4, 1),                         # FD76
            partial(self.ld_xy_r, r, m, IYh, IYl, A),               # FD77 LD (IY+d),A
            partial(self.nop, r, R1, 4, 1),                         # FD78
            partial(self.nop, r, R1, 4, 1),                         # FD79
            partial(self.nop, r, R1, 4, 1),                         # FD7A
            partial(self.nop, r, R1, 4, 1),                         # FD7B
            partial(self.ld_r_r, r, R2, 8, 2, A, IYh),              # FD7C LD A,IYh
            partial(self.ld_r_r, r, R2, 8, 2, A, IYl),              # FD7D LD A,IYl
            partial(self.ld_r_xy, r, m, A, IYh, IYl),               # FD7E LD A,(IY+d)
            partial(self.nop, r, R1, 4, 1),                         # FD7F
            partial(self.nop, r, R1, 4, 1),                         # FD80
            partial(self.nop, r, R1, 4, 1),                         # FD81
            partial(self.nop, r, R1, 4, 1),                         # FD82
            partial(self.nop, r, R1, 4, 1),                         # FD83
            partial(self.af_r, r, R2, 8, 2, ADD, IYh),              # FD84 ADD A,IYh
            partial(self.af_r, r, R2, 8, 2, ADD, IYl),              # FD85 ADD A,IYl
            partial(self.af_xy, r, m, ADD, IYh, IYl),               # FD86 ADD A,(IY+d)
            partial(self.nop, r, R1, 4, 1),                         # FD87
            partial(self.nop, r, R1, 4, 1),                         # FD88
            partial(self.nop, r, R1, 4, 1),                         # FD89
            partial(self.nop, r, R1, 4, 1),                         # FD8A
            partial(self.nop, r, R1, 4, 1),                         # FD8B
            partial(self.afc_r, r, R2, 8, 2, ADC, IYh),             # FD8C ADC A,IYh
            partial(self.afc_r, r, R2, 8, 2, ADC, IYl),             # FD8D ADC A,IYl
            partial(self.afc_xy, r, m, ADC, IYh, IYl),              # FD8E ADC A,(IY+d)
            partial(self.nop, r, R1, 4, 1),                         # FD8F
            partial(self.nop, r, R1, 4, 1),                         # FD90
            partial(self.nop, r, R1, 4, 1),                         # FD91
            partial(self.nop, r, R1, 4, 1),                         # FD92
            partial(self.nop, r, R1, 4, 1),                         # FD93
            partial(self.af_r, r, R2, 8, 2, SUB, IYh),              # FD94 SUB IYh
            partial(self.af_r, r, R2, 8, 2, SUB, IYl),              # FD95 SUB IYl
            partial(self.af_xy, r, m, SUB, IYh, IYl),               # FD96 SUB (IY+d)
            partial(self.nop, r, R1, 4, 1),                         # FD97
            partial(self.nop, r, R1, 4, 1),                         # FD98
            partial(self.nop, r, R1, 4, 1),                         # FD99
            partial(self.nop, r, R1, 4, 1),                         # FD9A
            partial(self.nop, r, R1, 4, 1),                         # FD9B
            partial(self.afc_r, r, R2, 8, 2, SBC, IYh),             # FD9C SBC A,IYh
            partial(self.afc_r, r, R2, 8, 2, SBC, IYl),             # FD9D SBC A,IYl
            partial(self.afc_xy, r, m, SBC, IYh, IYl),              # FD9E SBC A,(IY+d)
            partial(self.nop, r, R1, 4, 1),                         # FD9F
            partial(self.nop, r, R1, 4, 1),                         # FDA0
            partial(self.nop, r, R1, 4, 1),                         # FDA1
            partial(self.nop, r, R1, 4, 1),                         # FDA2
            partial(self.nop, r, R1, 4, 1),                         # FDA3
            partial(self.af_r, r, R2, 8, 2, AND, IYh),              # FDA4 AND IYh
            partial(self.af_r, r, R2, 8, 2, AND, IYl),              # FDA5 AND IYl
            partial(self.af_xy, r, m, AND, IYh, IYl),               # FDA6 AND (IY+d)
            partial(self.nop, r, R1, 4, 1),                         # FDA7
            partial(self.nop, r, R1, 4, 1),                         # FDA8
            partial(self.nop, r, R1, 4, 1),                         # FDA9
            partial(self.nop, r, R1, 4, 1),                         # FDAA
            partial(self.nop, r, R1, 4, 1),                         # FDAB
            partial(self.af_r, r, R2, 8, 2, XOR, IYh),              # FDAC XOR IYh
            partial(self.af_r, r, R2, 8, 2, XOR, IYl),              # FDAD XOR IYl
            partial(self.af_xy, r, m, XOR, IYh, IYl),               # FDAE XOR (IY+d)
            partial(self.nop, r, R1, 4, 1),                         # FDAF
            partial(self.nop, r, R1, 4, 1),                         # FDB0
            partial(self.nop, r, R1, 4, 1),                         # FDB1
            partial(self.nop, r, R1, 4, 1),                         # FDB2
            partial(self.nop, r, R1, 4, 1),                         # FDB3
            partial(self.af_r, r, R2, 8, 2, OR, IYh),               # FDB4 OR IYh
            partial(self.af_r, r, R2, 8, 2, OR, IYl),               # FDB5 OR IYl
            partial(self.af_xy, r, m, OR, IYh, IYl),                # FDB6 OR (IY+d)
            partial(self.nop, r, R1, 4, 1),                         # FDB7
            partial(self.nop, r, R1, 4, 1),                         # FDB8
            partial(self.nop, r, R1, 4, 1),                         # FDB9
            partial(self.nop, r, R1, 4, 1),                         # FDBA
            partial(self.nop, r, R1, 4, 1),                         # FDBB
            partial(self.af_r, r, R2, 8, 2, CP, IYh),               # FDBC CP IYh
            partial(self.af_r, r, R2, 8, 2, CP, IYl),               # FDBD CP IYl
            partial(self.af_xy, r, m, CP, IYh, IYl),                # FDBE CP (IY+d)
            partial(self.nop, r, R1, 4, 1),                         # FDBF
            partial(self.nop, r, R1, 4, 1),                         # FDC0
            partial(self.nop, r, R1, 4, 1),                         # FDC1
            partial(self.nop, r, R1, 4, 1),                         # FDC2
            partial(self.nop, r, R1, 4, 1),                         # FDC3
            partial(self.nop, r, R1, 4, 1),                         # FDC4
            partial(self.nop, r, R1, 4, 1),                         # FDC5
            partial(self.nop, r, R1, 4, 1),                         # FDC6
            partial(self.nop, r, R1, 4, 1),                         # FDC7
            partial(self.nop, r, R1, 4, 1),                         # FDC8
            partial(self.nop, r, R1, 4, 1),                         # FDC9
            partial(self.nop, r, R1, 4, 1),                         # FDCA
            partial(self.prefix2, self.after_FDCB, r, m),           # FDCB prefix
            partial(self.nop, r, R1, 4, 1),                         # FDCC
            partial(self.nop, r, R1, 4, 1),                         # FDCD
            partial(self.nop, r, R1, 4, 1),                         # FDCE
            partial(self.nop, r, R1, 4, 1),                         # FDCF
            partial(self.nop, r, R1, 4, 1),                         # FDD0
            partial(self.nop, r, R1, 4, 1),                         # FDD1
            partial(self.nop, r, R1, 4, 1),                         # FDD2
            partial(self.nop, r, R1, 4, 1),                         # FDD3
            partial(self.nop, r, R1, 4, 1),                         # FDD4
            partial(self.nop, r, R1, 4, 1),                         # FDD5
            partial(self.nop, r, R1, 4, 1),                         # FDD6
            partial(self.nop, r, R1, 4, 1),                         # FDD7
            partial(self.nop, r, R1, 4, 1),                         # FDD8
            partial(self.nop, r, R1, 4, 1),                         # FDD9
            partial(self.nop, r, R1, 4, 1),                         # FDDA
            partial(self.nop, r, R1, 4, 1),                         # FDDB
            partial(self.nop, r, R1, 4, 1),                         # FDDC
            partial(self.nop, r, R1, 4, 1),                         # FDDD
            partial(self.nop, r, R1, 4, 1),                         # FDDE
            partial(self.nop, r, R1, 4, 1),                         # FDDF
            partial(self.nop, r, R1, 4, 1),                         # FDE0
            partial(self.pop, r, m, R2, 14, 2, IYh, IYl),           # FDE1 POP IY
            partial(self.nop, r, R1, 4, 1),                         # FDE2
            partial(self.ex_sp, r, m, R2, 23, 2, IYh, IYl),         # FDE3 EX (SP),IY
            partial(self.nop, r, R1, 4, 1),                         # FDE4
            partial(self.push, r, m, R2, 15, 2, IYh, IYl),          # FDE5 PUSH IY
            partial(self.nop, r, R1, 4, 1),                         # FDE6
            partial(self.nop, r, R1, 4, 1),                         # FDE7
            partial(self.nop, r, R1, 4, 1),                         # FDE8
            partial(self.jp_rr, r, R2, 8, IYh, IYl),                # FDE9 JP (IY)
            partial(self.nop, r, R1, 4, 1),                         # FDEA
            partial(self.nop, r, R1, 4, 1),                         # FDEB
            partial(self.nop, r, R1, 4, 1),                         # FDEC
            partial(self.nop, r, R1, 4, 1),                         # FDED
            partial(self.nop, r, R1, 4, 1),                         # FDEE
            partial(self.nop, r, R1, 4, 1),                         # FDEF
            partial(self.nop, r, R1, 4, 1),                         # FDF0
            partial(self.nop, r, R1, 4, 1),                         # FDF1
            partial(self.nop, r, R1, 4, 1),                         # FDF2
            partial(self.nop, r, R1, 4, 1),                         # FDF3
            partial(self.nop, r, R1, 4, 1),                         # FDF4
            partial(self.nop, r, R1, 4, 1),                         # FDF5
            partial(self.nop, r, R1, 4, 1),                         # FDF6
            partial(self.nop, r, R1, 4, 1),                         # FDF7
            partial(self.nop, r, R1, 4, 1),                         # FDF8
            partial(self.ld_sp_rr, r, R2, 10, 2, IYh, IYl),         # FDF9 LD SP,IY
            partial(self.nop, r, R1, 4, 1),                         # FDFA
            partial(self.nop, r, R1, 4, 1),                         # FDFB
            partial(self.nop, r, R1, 4, 1),                         # FDFC
            partial(self.nop, r, R1, 4, 1),                         # FDFD
            partial(self.nop, r, R1, 4, 1),                         # FDFE
            partial(self.nop, r, R1, 4, 1),                         # FDFF
        ]

        self.opcodes = [
            partial(self.nop, r, R1, 4, 1),                         # 00 NOP
            partial(self.ld_rr_nn, r, m, R1, 10, 3, B, C),          # 01 LD BC,nn
            partial(self.ld_rr_r, r, m, B, C, A),                   # 02 LD (BC),A
            partial(self.inc_dec_rr, r, R1, 6, 1, 1, B, C),         # 03 INC BC
            partial(self.fc_r, r, R1, 4, 1, INC, B),                # 04 INC B
            partial(self.fc_r, r, R1, 4, 1, DEC, B),                # 05 DEC B
            partial(self.ld_r_n, r, m, R1, 7, 2, B),                # 06 LD B,n
            partial(self.af_r, r, R1, 4, 1, RLCA, F),               # 07 RLCA
            partial(self.ex_af, r),                                 # 08 EX AF,AF'
            partial(self.add_rr, r, R1, 11, 1, H, L, B, C),         # 09 ADD HL,BC
            partial(self.ld_r_rr, r, m, A, B, C),                   # 0A LD A,(BC)
            partial(self.inc_dec_rr, r, R1, 6, 1, -1, B, C),        # 0B DEC BC
            partial(self.fc_r, r, R1, 4, 1, INC, C),                # 0C INC C
            partial(self.fc_r, r, R1, 4, 1, DEC, C),                # 0D DEC C
            partial(self.ld_r_n, r, m, R1, 7, 2, C),                # 0E LD C,n
            partial(self.af_r, r, R1, 4, 1, RRCA, F),               # 0F RRCA
            partial(self.djnz, r, m),                               # 10 DJNZ nn
            partial(self.ld_rr_nn, r, m, R1, 10, 3, D, E),          # 11 LD DE,nn
            partial(self.ld_rr_r, r, m, D, E, A),                   # 12 LD (DE),A
            partial(self.inc_dec_rr, r, R1, 6, 1, 1, D, E),         # 13 INC DE
            partial(self.fc_r, r, R1, 4, 1, INC, D),                # 14 INC D
            partial(self.fc_r, r, R1, 4, 1, DEC, D),                # 15 DEC D
            partial(self.ld_r_n, r, m, R1, 7, 2, D),                # 16 LD D,n
            partial(self.af_r, r, R1, 4, 1, RLA, F),                # 17 RLA
            partial(self.jr, r, m, 0, 0),                           # 18 JR nn
            partial(self.add_rr, r, R1, 11, 1, H, L, D, E),         # 19 ADD HL,DE
            partial(self.ld_r_rr, r, m, A, D, E),                   # 1A LD A,(DE)
            partial(self.inc_dec_rr, r, R1, 6, 1, -1, D, E),        # 1B DEC DE
            partial(self.fc_r, r, R1, 4, 1, INC, E),                # 1C INC E
            partial(self.fc_r, r, R1, 4, 1, DEC, E),                # 1D DEC E
            partial(self.ld_r_n, r, m, R1, 7, 2, E),                # 1E LD E,n
            partial(self.af_r, r, R1, 4, 1, RRA, F),                # 1F RRA
            partial(self.jr, r, m, 64, 0),                          # 20 JR NZ,nn
            partial(self.ld_rr_nn, r, m, R1, 10, 3, H, L),          # 21 LD HL,nn
            partial(self.ld_mm_rr, r, m, R1, 16, 3, H, L),          # 22 LD (nn),HL
            partial(self.inc_dec_rr, r, R1, 6, 1, 1, H, L),         # 23 INC HL
            partial(self.fc_r, r, R1, 4, 1, INC, H),                # 24 INC H
            partial(self.fc_r, r, R1, 4, 1, DEC, H),                # 25 DEC H
            partial(self.ld_r_n, r, m, R1, 7, 2, H),                # 26 LD H,n
            partial(self.af_r, r, R1, 4, 1, DAA, F),                # 27 DAA
            partial(self.jr, r, m, 64, 64),                         # 28 JR Z,nn
            partial(self.add_rr, r, R1, 11, 1, H, L, H, L),         # 29 ADD HL,HL
            partial(self.ld_rr_mm, r, m, R1, 16, 3, H, L),          # 2A LD HL,(nn)
            partial(self.inc_dec_rr, r, R1, 6, 1, -1, H, L),        # 2B DEC HL
            partial(self.fc_r, r, R1, 4, 1, INC, L),                # 2C INC L
            partial(self.fc_r, r, R1, 4, 1, DEC, L),                # 2D DEC L
            partial(self.ld_r_n, r, m, R1, 7, 2, L),                # 2E LD L,n
            partial(self.af_r, r, R1, 4, 1, CPL, F),                # 2F CPL
            partial(self.jr, r, m, 1, 0),                           # 30 JR NC,nn
            partial(self.ld_rr_nn, r, m, R1, 10, 3, SP2, SP),       # 31 LD SP,nn
            partial(self.ld_m_a, r, m),                             # 32 LD (nn),A
            partial(self.inc_dec_rr, r, R1, 6, 1, 1, SP2, SP),      # 33 INC SP
            partial(self.fc_hl, r, m, R1, 11, 1, INC),              # 34 INC (HL)
            partial(self.fc_hl, r, m, R1, 11, 1, DEC),              # 35 DEC (HL)
            partial(self.ld_hl_n, r, m),                            # 36 LD (HL),n
            partial(self.cf, r, SCF),                               # 37 SCF
            partial(self.jr, r, m, 1, 1),                           # 38 JR C,nn
            partial(self.add_rr, r, R1, 11, 1, H, L, SP2, SP),      # 39 ADD HL,SP
            partial(self.ld_a_m, r, m),                             # 3A LD A,(nn)
            partial(self.inc_dec_rr, r, R1, 6, 1, -1, SP2, SP),     # 3B DEC SP
            partial(self.fc_r, r, R1, 4, 1, INC, A),                # 3C INC A
            partial(self.fc_r, r, R1, 4, 1, DEC, A),                # 3D DEC A
            partial(self.ld_r_n, r, m, R1, 7, 2, A),                # 3E LD A,n
            partial(self.cf, r, CCF),                               # 3F CCF
            partial(self.nop, r, R1, 4, 1),                         # 40 LD B,B
            partial(self.ld_r_r, r, R1, 4, 1, B, C),                # 41 LD B,C
            partial(self.ld_r_r, r, R1, 4, 1, B, D),                # 42 LD B,D
            partial(self.ld_r_r, r, R1, 4, 1, B, E),                # 43 LD B,E
            partial(self.ld_r_r, r, R1, 4, 1, B, H),                # 44 LD B,H
            partial(self.ld_r_r, r, R1, 4, 1, B, L),                # 45 LD B,L
            partial(self.ld_r_rr, r, m, B, H, L),                   # 46 LD B,(HL)
            partial(self.ld_r_r, r, R1, 4, 1, B, A),                # 47 LD B,A
            partial(self.ld_r_r, r, R1, 4, 1, C, B),                # 48 LD C,B
            partial(self.nop, r, R1, 4, 1),                         # 49 LD C,C
            partial(self.ld_r_r, r, R1, 4, 1, C, D),                # 4A LD C,D
            partial(self.ld_r_r, r, R1, 4, 1, C, E),                # 4B LD C,E
            partial(self.ld_r_r, r, R1, 4, 1, C, H),                # 4C LD C,H
            partial(self.ld_r_r, r, R1, 4, 1, C, L),                # 4D LD C,L
            partial(self.ld_r_rr, r, m, C, H, L),                   # 4E LD C,(HL)
            partial(self.ld_r_r, r, R1, 4, 1, C, A),                # 4F LD C,A
            partial(self.ld_r_r, r, R1, 4, 1, D, B),                # 50 LD D,B
            partial(self.ld_r_r, r, R1, 4, 1, D, C),                # 51 LD D,C
            partial(self.nop, r, R1, 4, 1),                         # 52 LD D,D
            partial(self.ld_r_r, r, R1, 4, 1, D, E),                # 53 LD D,E
            partial(self.ld_r_r, r, R1, 4, 1, D, H),                # 54 LD D,H
            partial(self.ld_r_r, r, R1, 4, 1, D, L),                # 55 LD D,L
            partial(self.ld_r_rr, r, m, D, H, L),                   # 56 LD D,(HL)
            partial(self.ld_r_r, r, R1, 4, 1, D, A),                # 57 LD D,A
            partial(self.ld_r_r, r, R1, 4, 1, E, B),                # 58 LD E,B
            partial(self.ld_r_r, r, R1, 4, 1, E, C),                # 59 LD E,C
            partial(self.ld_r_r, r, R1, 4, 1, E, D),                # 5A LD E,D
            partial(self.nop, r, R1, 4, 1),                         # 5B LD E,E
            partial(self.ld_r_r, r, R1, 4, 1, E, H),                # 5C LD E,H
            partial(self.ld_r_r, r, R1, 4, 1, E, L),                # 5D LD E,L
            partial(self.ld_r_rr, r, m, E, H, L),                   # 5E LD E,(HL)
            partial(self.ld_r_r, r, R1, 4, 1, E, A),                # 5F LD E,A
            partial(self.ld_r_r, r, R1, 4, 1, H, B),                # 60 LD H,B
            partial(self.ld_r_r, r, R1, 4, 1, H, C),                # 61 LD H,C
            partial(self.ld_r_r, r, R1, 4, 1, H, D),                # 62 LD H,D
            partial(self.ld_r_r, r, R1, 4, 1, H, E),                # 63 LD H,E
            partial(self.nop, r, R1, 4, 1),                         # 64 LD H,H
            partial(self.ld_r_r, r, R1, 4, 1, H, L),                # 65 LD H,L
            partial(self.ld_r_rr, r, m, H, H, L),                   # 66 LD H,(HL)
            partial(self.ld_r_r, r, R1, 4, 1, H, A),                # 67 LD H,A
            partial(self.ld_r_r, r, R1, 4, 1, L, B),                # 68 LD L,B
            partial(self.ld_r_r, r, R1, 4, 1, L, C),                # 69 LD L,C
            partial(self.ld_r_r, r, R1, 4, 1, L, D),                # 6A LD L,D
            partial(self.ld_r_r, r, R1, 4, 1, L, E),                # 6B LD L,E
            partial(self.ld_r_r, r, R1, 4, 1, L, H),                # 6C LD L,H
            partial(self.nop, r, R1, 4, 1),                         # 6D LD L,L
            partial(self.ld_r_rr, r, m, L, H, L),                   # 6E LD L,(HL)
            partial(self.ld_r_r, r, R1, 4, 1, L, A),                # 6F LD L,A
            partial(self.ld_rr_r, r, m, H, L, B),                   # 70 LD (HL),B
            partial(self.ld_rr_r, r, m, H, L, C),                   # 71 LD (HL),C
            partial(self.ld_rr_r, r, m, H, L, D),                   # 72 LD (HL),D
            partial(self.ld_rr_r, r, m, H, L, E),                   # 73 LD (HL),E
            partial(self.ld_rr_r, r, m, H, L, H),                   # 74 LD (HL),H
            partial(self.ld_rr_r, r, m, H, L, L),                   # 75 LD (HL),L
            partial(self.halt, r),                                  # 76 HALT
            partial(self.ld_rr_r, r, m, H, L, A),                   # 77 LD (HL),A
            partial(self.ld_r_r, r, R1, 4, 1, A, B),                # 78 LD A,B
            partial(self.ld_r_r, r, R1, 4, 1, A, C),                # 79 LD A,C
            partial(self.ld_r_r, r, R1, 4, 1, A, D),                # 7A LD A,D
            partial(self.ld_r_r, r, R1, 4, 1, A, E),                # 7B LD A,E
            partial(self.ld_r_r, r, R1, 4, 1, A, H),                # 7C LD A,H
            partial(self.ld_r_r, r, R1, 4, 1, A, L),                # 7D LD A,L
            partial(self.ld_r_rr, r, m, A, H, L),                   # 7E LD A,(HL)
            partial(self.nop, r, R1, 4, 1),                         # 7F LD A,A
            partial(self.af_r, r, R1, 4, 1, ADD, B),                # 80 ADD A,B
            partial(self.af_r, r, R1, 4, 1, ADD, C),                # 81 ADD A,C
            partial(self.af_r, r, R1, 4, 1, ADD, D),                # 82 ADD A,D
            partial(self.af_r, r, R1, 4, 1, ADD, E),                # 83 ADD A,E
            partial(self.af_r, r, R1, 4, 1, ADD, H),                # 84 ADD A,H
            partial(self.af_r, r, R1, 4, 1, ADD, L),                # 85 ADD A,L
            partial(self.af_hl, r, m, ADD),                         # 86 ADD A,(HL)
            partial(self.af_r, r, R1, 4, 1, ADD, A),                # 87 ADD A,A
            partial(self.afc_r, r, R1, 4, 1, ADC, B),               # 88 ADC A,B
            partial(self.afc_r, r, R1, 4, 1, ADC, C),               # 89 ADC A,C
            partial(self.afc_r, r, R1, 4, 1, ADC, D),               # 8A ADC A,D
            partial(self.afc_r, r, R1, 4, 1, ADC, E),               # 8B ADC A,E
            partial(self.afc_r, r, R1, 4, 1, ADC, H),               # 8C ADC A,H
            partial(self.afc_r, r, R1, 4, 1, ADC, L),               # 8D ADC A,L
            partial(self.afc_hl, r, m, ADC),                        # 8E ADC A,(HL)
            partial(self.fc_r, r, R1, 4, 1, ADC_A_A, A),            # 8F ADC A,A
            partial(self.af_r, r, R1, 4, 1, SUB, B),                # 90 SUB B
            partial(self.af_r, r, R1, 4, 1, SUB, C),                # 91 SUB C
            partial(self.af_r, r, R1, 4, 1, SUB, D),                # 92 SUB D
            partial(self.af_r, r, R1, 4, 1, SUB, E),                # 93 SUB E
            partial(self.af_r, r, R1, 4, 1, SUB, H),                # 94 SUB H
            partial(self.af_r, r, R1, 4, 1, SUB, L),                # 95 SUB L
            partial(self.af_hl, r, m, SUB),                         # 96 SUB (HL)
            partial(self.af_r, r, R1, 4, 1, SUB, A),                # 97 SUB A
            partial(self.afc_r, r, R1, 4, 1, SBC, B),               # 98 SBC A,B
            partial(self.afc_r, r, R1, 4, 1, SBC, C),               # 99 SBC A,C
            partial(self.afc_r, r, R1, 4, 1, SBC, D),               # 9A SBC A,D
            partial(self.afc_r, r, R1, 4, 1, SBC, E),               # 9B SBC A,E
            partial(self.afc_r, r, R1, 4, 1, SBC, H),               # 9C SBC A,H
            partial(self.afc_r, r, R1, 4, 1, SBC, L),               # 9D SBC A,L
            partial(self.afc_hl, r, m, SBC),                        # 9E SBC A,(HL)
            partial(self.fc_r, r, R1, 4, 1, SBC_A_A, A),            # 9F SBC A,A
            partial(self.af_r, r, R1, 4, 1, AND, B),                # A0 AND B
            partial(self.af_r, r, R1, 4, 1, AND, C),                # A1 AND C
            partial(self.af_r, r, R1, 4, 1, AND, D),                # A2 AND D
            partial(self.af_r, r, R1, 4, 1, AND, E),                # A3 AND E
            partial(self.af_r, r, R1, 4, 1, AND, H),                # A4 AND H
            partial(self.af_r, r, R1, 4, 1, AND, L),                # A5 AND L
            partial(self.af_hl, r, m, AND),                         # A6 AND (HL)
            partial(self.af_r, r, R1, 4, 1, AND, A),                # A7 AND A
            partial(self.af_r, r, R1, 4, 1, XOR, B),                # A8 XOR B
            partial(self.af_r, r, R1, 4, 1, XOR, C),                # A9 XOR C
            partial(self.af_r, r, R1, 4, 1, XOR, D),                # AA XOR D
            partial(self.af_r, r, R1, 4, 1, XOR, E),                # AB XOR E
            partial(self.af_r, r, R1, 4, 1, XOR, H),                # AC XOR H
            partial(self.af_r, r, R1, 4, 1, XOR, L),                # AD XOR L
            partial(self.af_hl, r, m, XOR),                         # AE XOR (HL)
            partial(self.af_r, r, R1, 4, 1, XOR, A),                # AF XOR A
            partial(self.af_r, r, R1, 4, 1, OR, B),                 # B0 OR B
            partial(self.af_r, r, R1, 4, 1, OR, C),                 # B1 OR C
            partial(self.af_r, r, R1, 4, 1, OR, D),                 # B2 OR D
            partial(self.af_r, r, R1, 4, 1, OR, E),                 # B3 OR E
            partial(self.af_r, r, R1, 4, 1, OR, H),                 # B4 OR H
            partial(self.af_r, r, R1, 4, 1, OR, L),                 # B5 OR L
            partial(self.af_hl, r, m, OR),                          # B6 OR (HL)
            partial(self.af_r, r, R1, 4, 1, OR, A),                 # B7 OR A
            partial(self.af_r, r, R1, 4, 1, CP, B),                 # B8 CP B
            partial(self.af_r, r, R1, 4, 1, CP, C),                 # B9 CP C
            partial(self.af_r, r, R1, 4, 1, CP, D),                 # BA CP D
            partial(self.af_r, r, R1, 4, 1, CP, E),                 # BB CP E
            partial(self.af_r, r, R1, 4, 1, CP, H),                 # BC CP H
            partial(self.af_r, r, R1, 4, 1, CP, L),                 # BD CP L
            partial(self.af_hl, r, m, CP),                          # BE CP (HL)
            partial(self.af_r, r, R1, 4, 1, CP, A),                 # BF CP A
            partial(self.ret, r, m, 64, 64),                        # C0 RET NZ
            partial(self.pop, r, m, R1, 10, 1, B, C),               # C1 POP BC
            partial(self.jp, r, m, 64, 0),                          # C2 JP NZ,nn
            partial(self.jp, r, m, 0, 0),                           # C3 JP nn
            partial(self.call, r, m, 64, 64),                       # C4 CALL NZ,nn
            partial(self.push, r, m, R1, 11, 1, B, C),              # C5 PUSH BC
            partial(self.af_n, r, m, ADD),                          # C6 ADD A,n
            partial(self.rst, r, m, 0),                             # C7 RST $00
            partial(self.ret, r, m, 64, 0),                         # C8 RET Z
            partial(self.ret, r, m, 0, 0),                          # C9 RET
            partial(self.jp, r, m, 64, 64),                         # CA JP Z,nn
            partial(self.prefix, self.after_CB, r, m),              # CB prefix
            partial(self.call, r, m, 64, 0),                        # CC CALL Z,nn
            partial(self.call, r, m, 0, 0),                         # CD CALL nn
            partial(self.afc_n, r, m, ADC),                         # CE ADC A,n
            partial(self.rst, r, m, 8),                             # CF RST $08
            partial(self.ret, r, m, 1, 1),                          # D0 RET NC
            partial(self.pop, r, m, R1, 10, 1, D, E),               # D1 POP DE
            partial(self.jp, r, m, 1, 0),                           # D2 JP NC,nn
            partial(self.out_a, r, m),                              # D3 OUT (n),A
            partial(self.call, r, m, 1, 1),                         # D4 CALL NC,nn
            partial(self.push, r, m, R1, 11, 1, D, E),              # D5 PUSH DE
            partial(self.af_n, r, m, SUB),                          # D6 SUB n
            partial(self.rst, r, m, 16),                            # D7 RST $10
            partial(self.ret, r, m, 1, 0),                          # D8 RET C
            partial(self.exx, r),                                   # D9 EXX
            partial(self.jp, r, m, 1, 1),                           # DA JP C,nn
            partial(self.in_a, r, m),                               # DB IN A,(n)
            partial(self.call, r, m, 1, 0),                         # DC CALL C,nn
            partial(self.prefix, self.after_DD, r, m),              # DD prefix
            partial(self.afc_n, r, m, SBC),                         # DE SBC A,n
            partial(self.rst, r, m, 24),                            # DF RST $18
            partial(self.ret, r, m, 4, 4),                          # E0 RET PO
            partial(self.pop, r, m, R1, 10, 1, H, L),               # E1 POP HL
            partial(self.jp, r, m, 4, 0),                           # E2 JP PO,nn
            partial(self.ex_sp, r, m, R1, 19, 1, H, L),             # E3 EX (SP),HL
            partial(self.call, r, m, 4, 4),                         # E4 CALL PO,nn
            partial(self.push, r, m, R1, 11, 1, H, L),              # E5 PUSH HL
            partial(self.af_n, r, m, AND),                          # E6 AND n
            partial(self.rst, r, m, 32),                            # E7 RST $20
            partial(self.ret, r, m, 4, 0),                          # E8 RET PE
            partial(self.jp_rr, r, R1, 4, H, L),                    # E9 JP (HL)
            partial(self.jp, r, m, 4, 4),                           # EA JP PE,nn
            partial(self.ex_de_hl, r),                              # EB EX DE,HL
            partial(self.call, r, m, 4, 0),                         # EC CALL PE,nn
            partial(self.prefix, self.after_ED, r, m),              # ED prefix
            partial(self.af_n, r, m, XOR),                          # EE XOR n
            partial(self.rst, r, m, 40),                            # EF RST $28
            partial(self.ret, r, m, 128, 128),                      # F0 RET P
            partial(self.pop, r, m, R1, 10, 1, A, F),               # F1 POP AF
            partial(self.jp, r, m, 128, 0),                         # F2 JP P,nn
            partial(self.di_ei, r, 0),                              # F3 DI
            partial(self.call, r, m, 128, 128),                     # F4 CALL P,nn
            partial(self.push, r, m, R1, 11, 1, A, F),              # F5 PUSH AF
            partial(self.af_n, r, m, OR),                           # F6 OR n
            partial(self.rst, r, m, 48),                            # F7 RST $30
            partial(self.ret, r, m, 128, 0),                        # F8 RET M
            partial(self.ld_sp_rr, r, R1, 6, 1, H, L),              # F9 LD SP,HL
            partial(self.jp, r, m, 128, 128),                       # FA JP M,nn
            partial(self.di_ei, r, 1),                              # FB EI
            partial(self.call, r, m, 128, 0),                       # FC CALL M,nn
            partial(self.prefix, self.after_FD, r, m),              # FD prefix
            partial(self.af_n, r, m, CP),                           # FE CP n
            partial(self.rst, r, m, 56),                            # FF RST $38
        ]
