# Copyright 2024 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit.simulator import Simulator, JR_OFFSETS, OFFSETS, R1, R2

DELAYS_48K = [0] * 69888
for row in range(64, 256):
    for i in range(16):
        t = row * 224 - 1 + i * 8
        DELAYS_48K[t:t + 6] = (6, 5, 4, 3, 2, 1)

DELAYS_128K = [0] * 70908
for row in range(63, 255):
    for i in range(16):
        t = row * 228 - 3 + i * 8
        DELAYS_128K[t:t + 6] = (6, 5, 4, 3, 2, 1)

class CMIOSimulator(Simulator):
    def __init__(self, memory, registers=None, state=None, config=None):
        if config is None:
            config = {}
        config['fast_djnz'] = False
        config['fast_ldir'] = False
        super().__init__(memory, registers, state, config)
        if len(memory) == 0x20000:
            self.t0 = 14361 - 23
            self.t1 = 14361 + 228 * 191 + 126
            self.contend = self.contend_128k
            self.io_contention = self.io_contention_128k
        else:
            self.t0 = 14335 - 23
            self.t1 = 14335 + 224 * 191 + 126
            self.contend = self.contend_48k
            self.io_contention = self.io_contention_48k

    def contend_48k(self, t, timings):
        delay = 0
        for address, tstates in timings:
            if 0x4000 <= address < 0x8000:
                delay += DELAYS_48K[t % 69888]
                t += DELAYS_48K[t % 69888]
            t += tstates
        return delay

    def io_contention_48k(self, port):
        if port % 2:
            # Low bit set
            if 0x4000 <= port < 0x8000:
                return ((0x4000, 1), (0x4000, 1), (0x4000, 1), (0x4000, 1))
            return ((0, 4),)
        # Low bit reset (ULA port)
        if 0x4000 <= port < 0x8000:
            return ((0x4000, 1), (0x4000, 3))
        return ((0, 1), (0x4000, 3))

    def contend_128k(self, t, timings):
        c = self.memory.o7ffd % 2
        delay = 0
        for address, tstates in timings:
            if 0x4000 <= address < 0x8000 or (c and address >= 0xC000):
                delay += DELAYS_128K[t % 70908]
                t += DELAYS_128K[t % 70908]
            t += tstates
        return delay

    def io_contention_128k(self, port):
        if port % 2:
            # Low bit set
            if 0x4000 <= port < 0x8000 or (self.memory.o7ffd % 2 and port >= 0xC000):
                return ((0x4000, 1), (0x4000, 1), (0x4000, 1), (0x4000, 1))
            return ((0, 4),)
        # Low bit reset (ULA port)
        if 0x4000 <= port < 0x8000 or (self.memory.o7ffd % 2 and port >= 0xC000):
            return ((0x4000, 1), (0x4000, 3))
        return ((0, 1), (0x4000, 3))

    def af_hl(self, registers, memory, af):
        # ADD A,(HL) / AND (HL) / CP (HL) / OR (HL) / SUB (HL) / XOR (HL)
        pc = registers[24]
        hl = registers[7] + 256 * registers[6]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), (hl, 3)))
        else:
            delay = 0
        registers[:2] = af[registers[0]][memory[hl]]
        registers[15] = R1[registers[15]] # R
        registers[25] += 7 + delay # T-states
        registers[24] = (pc + 1) % 65536 # PC

    def af_n(self, registers, memory, af):
        # ADD A,n / AND n / CP n / OR n / SUB n / XOR n
        pc = registers[24]
        pc1 = (pc + 1) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), (pc1, 3)))
        else:
            delay = 0
        registers[:2] = af[registers[0]][memory[pc1]]
        registers[15] = R1[registers[15]] # R
        registers[25] += 7 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def af_r(self, registers, r_inc, timing, size, af, r):
        # ADD A,r / AND r / CP r / OR r / SUB r / XOR r
        # CPL / DAA / RLA / RLCA / RRA / RRCA
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 1:
                # CPL / DAA / RLA / RLCA / RRA / RRCA; r = A/B/C/D/E/H/L
                delay = self.contend(registers[25], ((pc, 4),))
            else:
                # r = IXh/IXl/IYh/IYl
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        registers[:2] = af[registers[0]][registers[r]]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing + delay # T-states
        registers[24] = (pc + size) % 65536 # PC

    def af_xy(self, registers, memory, af, xyh, xyl):
        # ADD A,(IX/Y+d) / AND (IX/Y+d) / CP (IX/Y+d) / OR (IX/Y+d)
        # SUB (IX/Y+d) / XOR (IX/Y+d)
        pc = registers[24]
        pc2 = (pc + 2) % 65536
        xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (xy, 3)))
        else:
            delay = 0
        registers[:2] = af[registers[0]][memory[xy]]
        registers[15] = R2[registers[15]] # R
        registers[25] += 19 + delay # T-states
        registers[24] = (pc + 3) % 65536 # PC

    def afc_hl(self, registers, memory, afc):
        # ADC/SBC A,(HL)
        pc = registers[24]
        hl = registers[7] + 256 * registers[6]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), (hl, 3)))
        else:
            delay = 0
        registers[:2] = afc[registers[1] % 2][registers[0]][memory[hl]]
        registers[15] = R1[registers[15]] # R
        registers[25] += 7 + delay # T-states
        registers[24] = (pc + 1) % 65536 # PC

    def afc_n(self, registers, memory, afc):
        # ADC/SBC A,n
        pc = registers[24]
        pc1 = (pc + 1) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), (pc1, 3)))
        else:
            delay = 0
        registers[:2] = afc[registers[1] % 2][registers[0]][memory[pc1]]
        registers[15] = R1[registers[15]] # R
        registers[25] += 7 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def afc_r(self, registers, r_inc, timing, size, afc, r):
        # ADC/SBC A,r (r != A)
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 1:
                # r = B/C/D/E/H/L
                delay = self.contend(registers[25], ((pc, 4),))
            else:
                # r = IXh/IXl/IYh/IYl
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        registers[:2] = afc[registers[1] % 2][registers[0]][registers[r]]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing + delay # T-states
        registers[24] = (pc + size) % 65536 # PC

    def afc_xy(self, registers, memory, afc, xyh, xyl):
        # ADC/SBC A,(IX/Y+d)
        pc = registers[24]
        pc2 = (pc + 2) % 65536
        xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (xy, 3)))
        else:
            delay = 0
        registers[:2] = afc[registers[1] % 2][registers[0]][memory[xy]]
        registers[15] = R2[registers[15]] # R
        registers[25] += 19 + delay # T-states
        registers[24] = (pc + 3) % 65536 # PC

    def f_hl(self, registers, memory, f):
        # RLC/RRC/SLA/SLL/SRA/SRL (HL)
        pc = registers[24]
        hl = registers[7] + 256 * registers[6]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 3)))
        else:
            delay = 0
        value, registers[1] = f[memory[hl]]
        if hl > 0x3FFF:
            memory[hl] = value
        registers[15] = R2[registers[15]] # R
        registers[25] += 15 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def f_r(self, registers, f, r):
        # RLC/RRC/SLA/SLL/SRA/SRL r
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        registers[r], registers[1] = f[registers[r]]
        registers[15] = R2[registers[15]] # R
        registers[25] += 8 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def f_xy(self, registers, memory, f, xyh, xyl, dest=-1):
        # RLC/RRC/SLA/SLL/SRA/SRL (IX/Y+d)[,r]
        pc = registers[24]
        pc2 = (pc + 2) % 65536
        xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc3 = (pc + 3) % 65536
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc3, 3), (pc3, 1), (pc3, 1), (xy, 3), (xy, 1), (xy, 3)))
        else:
            delay = 0
        value, registers[1] = f[memory[xy]]
        if xy > 0x3FFF:
            memory[xy] = value
        if dest >= 0:
            registers[dest] = value
        registers[15] = R2[registers[15]] # R
        registers[25] += 23 + delay # T-states
        registers[24] = (pc + 4) % 65536 # PC

    def fc_hl(self, registers, memory, r_inc, timing, size, fc):
        # DEC/INC/RL/RR (HL)
        pc = registers[24]
        hl = registers[7] + 256 * registers[6]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 2:
                # RL/RR (HL)
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 3)))
            else:
                # DEC/INC (HL)
                delay = self.contend(registers[25], ((pc, 4), (hl, 3), (hl, 1), (hl, 3)))
        else:
            delay = 0
        value, registers[1] = fc[registers[1] % 2][memory[hl]]
        if hl > 0x3FFF:
            memory[hl] = value
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing + delay # T-states
        registers[24] = (pc + size) % 65536 # PC

    def fc_r(self, registers, r_inc, timing, size, fc, r):
        # DEC/INC/RL/RR r / ADC A,A / SBC A,A
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 1:
                # DEC/INC r / ADC A,A / SBC A,A
                delay = self.contend(registers[25], ((pc, 4),))
            else:
                # RL/RR r
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        registers[r], registers[1] = fc[registers[1] % 2][registers[r]]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing + delay # T-states
        registers[24] = (pc + size) % 65536 # PC

    def fc_xy(self, registers, memory, size, fc, xyh, xyl, dest=-1):
        # DEC/INC/RL/RR (IX/Y+d)[,r]
        pc = registers[24]
        pc2 = (pc + 2) % 65536
        xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 3:
                # DEC/INC (IX/Y+d)
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (xy, 3), (xy, 1), (xy, 3)))
            else:
                # RL/RR (IX/Y+d)[,r]
                pc3 = (pc + 3) % 65536
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc3, 3), (pc3, 1), (pc3, 1), (xy, 3), (xy, 1), (xy, 3)))
        else:
            delay = 0
        value, registers[1] = fc[registers[1] % 2][memory[xy]]
        if xy > 0x3FFF:
            memory[xy] = value
        if dest >= 0:
            registers[dest] = value
        registers[15] = R2[registers[15]] # R
        registers[25] += 23 + delay # T-states
        registers[24] = (pc + size) % 65536 # PC

    def adc_hl(self, registers, rh, rl):
        # ADC HL,BC/DE/HL/SP
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            ir = registers[15] + 256 * registers[14]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1)))
        else:
            delay = 0
        rr = registers[rl] + 256 * registers[rh]
        h = registers[6]
        hl = registers[7] + 256 * h
        result = hl + rr + registers[1] % 2
        if result > 0xFFFF:
            result %= 65536
            f = 0x01 # .......C
        else:
            f = 0
        if result == 0:
            f += 0x40 # .Z......
        r_h = result // 256
        f += (h ^ (rr // 256) ^ r_h) & 0x10 # ...H....
        if hl ^ rr < 0x8000 and hl ^ result > 0x7FFF:
            f += 0x04 # .....P..
        registers[1] = f + (r_h & 0xA8)
        registers[7] = result % 256
        registers[6] = r_h
        registers[15] = R2[registers[15]] # R
        registers[25] += 15 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def add_rr(self, registers, r_inc, timing, size, ah, al, rh, rl):
        # ADD HL/IX/IY,BC/DE/HL/SP/IX/IY
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            ir = registers[15] + 256 * registers[14]
            if size == 1:
                # ADD HL,BC/DE/HL/SP
                delay = self.contend(registers[25], ((pc, 4), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1)))
            else:
                # ADD IX/IY,BC/DE/SP/IX/IY
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1)))
        else:
            delay = 0
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
        registers[25] += timing + delay # T-states
        registers[24] = (pc + size) % 65536 # PC

    def bit_hl(self, registers, memory, bit, b):
        # BIT n,(HL)
        pc = registers[24]
        hl = registers[7] + 256 * registers[6]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1)))
        else:
            delay = 0
        registers[1] = bit[registers[1] % 2][b][memory[hl]]
        registers[15] = R2[registers[15]] # R
        registers[25] += 12 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def bit_r(self, registers, bit, b, reg):
        # BIT n,r
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        registers[1] = bit[registers[1] % 2][b][registers[reg]]
        registers[15] = R2[registers[15]] # R
        registers[25] += 8 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def bit_xy(self, registers, memory, bit, b, xyh, xyl):
        # BIT n,(IX/Y+d)
        pc = registers[24]
        pc2 = (pc + 2) % 65536
        xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc3 = (pc + 3) % 65536
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc3, 3), (pc3, 1), (pc3, 1), (xy, 3), (xy, 1)))
        else:
            delay = 0
        registers[1] = (bit[registers[1] % 2][b][memory[xy]] & 0xD7) + ((xy // 256) & 0x28)
        registers[15] = R2[registers[15]] # R
        registers[25] += 20 + delay # T-states
        registers[24] = (pc + 4) % 65536 # PC

    def call(self, registers, memory, c_and, c_val):
        # CALL nn / CALL cc,nn
        pc = registers[24]
        pc1 = (pc + 1) % 65536
        pc2 = (pc + 2) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if c_and and registers[1] & c_and == c_val:
                # Condition not met
                delay = self.contend(registers[25], ((pc, 4), (pc1, 3), (pc2, 3)))
            else:
                # Condition met
                sp = registers[12]
                delay = self.contend(registers[25], ((pc, 4), (pc1, 3), (pc2, 3), (pc2, 1), ((sp - 1) % 65536, 3), ((sp - 2) % 65536, 3)))
        else:
            delay = 0
        if c_and and registers[1] & c_and == c_val:
            registers[25] += 10 + delay # T-states
            registers[24] = (pc + 3) % 65536 # PC
        else:
            registers[24] = memory[pc1] + 256 * memory[pc2] # PC
            ret_addr = (pc + 3) % 65536
            sp = (registers[12] - 2) % 65536
            registers[12] = sp
            if sp > 0x3FFF:
                memory[sp] = ret_addr % 256
            sp = (sp + 1) % 65536
            if sp > 0x3FFF:
                memory[sp] = ret_addr // 256
            registers[25] += 17 + delay # T-states
        registers[15] = R1[registers[15]] # R

    def cf(self, registers, cf):
        # CCF / SCF
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4),))
        else:
            delay = 0
        registers[1] = cf[registers[1]][registers[0]]
        registers[15] = R1[registers[15]] # R
        registers[25] += 4 + delay # T-states
        registers[24] = (pc + 1) % 65536 # PC

    def cpi(self, registers, memory, inc, repeat):
        # CPI / CPD / CPIR / CPDR
        pc = registers[24]
        hl = registers[7] + 256 * registers[6]
        bc = registers[3] + 256 * registers[2]
        a = registers[0]
        value = memory[hl]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if repeat and a != value and bc != 1:
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1)))
            else:
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1)))
        else:
            delay = 0
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
            registers[1] = f + ((pc // 256) & 0x28) + 0x04 # .Z5.3P..
            registers[25] += 21 + delay # T-states
        else:
            n = cp - hf
            registers[1] = f + (cp == 0) * 0x40 + (n & 0x02) * 16 + (n & 0x08) + (bc > 0) * 0x04 # .Z5.3P..
            registers[25] += 16 + delay # T-states
            registers[24] = (pc + 2) % 65536 # PC
        registers[15] = R2[registers[15]] # R

    def di_ei(self, registers, iff):
        # DI / EI
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4),))
        else:
            delay = 0
        registers[26] = iff
        registers[15] = R1[registers[15]] # R
        registers[25] += 4 + delay # T-states
        registers[24] = (pc + 1) % 65536 # PC

    def djnz(self, registers, memory):
        # DJNZ nn
        pc = registers[24]
        pc1 = (pc + 1) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if registers[2] != 1:
                delay = self.contend(registers[25], ((pc, 4), (registers[15] + 256 * registers[14], 1), (pc1, 3), (pc1, 1), (pc1, 1), (pc1, 1), (pc1, 1), (pc1, 1)))
            else:
                delay = self.contend(registers[25], ((pc, 4), (registers[15] + 256 * registers[14], 1), (pc1, 3)))
        else:
            delay = 0
        b = (registers[2] - 1) % 256
        registers[2] = b
        if b:
            registers[25] += 13 + delay # T-states
            registers[24] = (pc + JR_OFFSETS[memory[pc1]]) % 65536 # PC
        else:
            registers[25] += 8 + delay # T-states
            registers[24] = (pc + 2) % 65536 # PC
        registers[15] = R1[registers[15]] # R

    def ex_af(self, registers):
        # EX AF,AF'
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4),))
        else:
            delay = 0
        registers[0], registers[16] = registers[16], registers[0]
        registers[1], registers[17] = registers[17], registers[1]
        registers[15] = R1[registers[15]] # R
        registers[25] += 4 + delay # T-states
        registers[24] = (pc + 1) % 65536 # PC

    def ex_de_hl(self, registers):
        # EX DE,HL
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4),))
        else:
            delay = 0
        registers[4], registers[6] = registers[6], registers[4]
        registers[5], registers[7] = registers[7], registers[5]
        registers[15] = R1[registers[15]] # R
        registers[25] += 4 + delay # T-states
        registers[24] = (pc + 1) % 65536 # PC

    def ex_sp(self, registers, memory, r_inc, timing, size, rh, rl):
        # EX (SP),HL/IX/IY
        pc = registers[24]
        sp = registers[12]
        sp1 = (sp + 1) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 1:
                # EX (SP),HL
                delay = self.contend(registers[25], ((pc, 4), (sp, 3), (sp1, 3), (sp1, 1), (sp1, 3), (sp, 3), (sp, 1), (sp, 1)))
            else:
                # EX (SP),IX/IY
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (sp, 3), (sp1, 3), (sp1, 1), (sp1, 3), (sp, 3), (sp, 1), (sp, 1)))
        else:
            delay = 0
        v1 = memory[sp]
        if sp > 0x3FFF:
            memory[sp] = registers[rl]
        v2 = memory[sp1]
        if sp1 > 0x3FFF:
            memory[sp1] = registers[rh]
        registers[rl] = v1
        registers[rh] = v2
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing + delay # T-states
        registers[24] = (pc + size) % 65536 # PC

    def exx(self, registers):
        # EXX
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4),))
        else:
            delay = 0
        registers[2:8], registers[18:24] = registers[18:24], registers[2:8]
        registers[15] = R1[registers[15]] # R
        registers[25] += 4 + delay # T-states
        registers[24] = (pc + 1) % 65536 # PC

    def halt(self, registers):
        # HALT
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if registers[28]:
                delay = self.contend(registers[25], (((pc + 1) % 65536, 4),))
            else:
                delay = self.contend(registers[25], ((pc, 4),))
        else:
            delay = 0
        registers[25] += 4 + delay # T-states
        if registers[26] and registers[25] % self.frame_duration < self.int_active:
            registers[24] = (pc + 1) % 65536 # PC
            registers[28] = 0 # HALT state
        else:
            registers[28] = 1 # HALT state
        registers[15] = R1[registers[15]] # R

    def im(self, registers, mode):
        # IM 0/1/2
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        registers[27] = mode
        registers[15] = R2[registers[15]] # R
        registers[25] += 8 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def in_a(self, registers, memory):
        # IN A,(n)
        pc = registers[24]
        pc1 = (pc + 1) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            io_c = self.io_contention(memory[pc1] + 256 * registers[0])
            delay = self.contend(registers[25], ((pc, 4), (pc1, 3), *io_c))
        else:
            delay = 0
        if self.in_a_n_tracer:
            registers[0] = self.in_a_n_tracer(memory[pc1] + 256 * registers[0])
        else:
            registers[0] = 255
        registers[15] = R1[registers[15]] # R
        registers[25] += 11 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def in_c(self, registers, reg, sz53p):
        # IN r,(C)
        pc = registers[24]
        bc = registers[3] + 256 * registers[2]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            io_c = self.io_contention(bc)
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), *io_c))
        else:
            delay = 0
        if self.in_r_c_tracer:
            value = self.in_r_c_tracer(bc)
        else:
            value = 255
        if reg != 1:
            registers[reg] = value
        registers[1] = sz53p[value] + (registers[1] % 2)
        registers[15] = R2[registers[15]] # R
        registers[25] += 12 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def inc_dec_rr(self, registers, r_inc, timing, size, inc, rh, rl):
        # INC/DEC BC/DE/HL/SP/IX/IY
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            ir = registers[15] + 256 * registers[14]
            if size == 1:
                # INC/DEC BC/DE/HL/SP
                delay = self.contend(registers[25], ((pc, 4), (ir, 1), (ir, 1)))
            else:
                # INC/DEC IX/IY
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (ir, 1), (ir, 1)))
        else:
            delay = 0
        if rl == 12:
            registers[12] = (registers[12] + inc) % 65536
        else:
            value = (registers[rl] + 256 * registers[rh] + inc) % 65536
            registers[rh] = value // 256
            registers[rl] = value % 256
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing + delay # T-states
        registers[24] = (pc + size) % 65536 # PC

    def ini(self, registers, memory, inc, repeat, parity):
        # INI / IND / INIR / INDR
        pc = registers[24]
        hl = registers[7] + 256 * registers[6]
        b = registers[2]
        c = registers[3]
        bc = c + 256 * b
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            io_c = self.io_contention(bc)
            if repeat and b != 1:
                # 21 T-states
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[15] + 256 * registers[14], 1), *io_c, (hl, 3), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1)))
            else:
                # 16 T-states
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[15] + 256 * registers[14], 1), *io_c, (hl, 3)))
        else:
            delay = 0
        if self.ini_tracer:
            value = self.ini_tracer(bc)
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
            registers[1] = (b & 0x80) + ((pc // 256) & 0x28) + h + p + n + c
            registers[25] += 21 + delay # T-states
        else:
            registers[1] = (b & 0xA8) + (b == 0) * 0x40 + c * 0x11 + parity[(j % 8) ^ b] + n
            registers[24] = (pc + 2) % 65536 # PC
            registers[25] += 16 + delay # T-states
        registers[15] = R2[registers[15]] # R

    def jp(self, registers, memory, c_and, c_val):
        # JP nn / JP cc,nn
        pc = registers[24]
        pc1 = (pc + 1) % 65536
        pc2 = (pc + 2) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), (pc1, 3), (pc2, 3)))
        else:
            delay = 0
        if registers[1] & c_and == c_val:
            registers[24] = memory[pc1] + 256 * memory[pc2] # PC
        else:
            registers[24] = (pc + 3) % 65536 # PC
        registers[15] = R1[registers[15]] # R
        registers[25] += 10 + delay # T-states

    def jp_rr(self, registers, r_inc, timing, rh, rl):
        # JP (HL/IX/IY)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if timing == 4:
                # JP (HL)
                delay = self.contend(registers[25], ((registers[24], 4),))
            else:
                # JP (IX/IY)
                pc = registers[24]
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing + delay # T-states
        registers[24] = registers[rl] + 256 * registers[rh] # PC

    def jr(self, registers, memory, c_and, c_val):
        # JR nn / JR cc,nn
        pc = registers[24]
        pc1 = (pc + 1) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if registers[1] & c_and == c_val:
                # Condition met
                delay = self.contend(registers[25], ((pc, 4), (pc1, 3), (pc1, 1), (pc1, 1), (pc1, 1), (pc1, 1), (pc1, 1)))
            else:
                # Condition not met
                delay = self.contend(registers[25], ((pc, 4), (pc1, 3)))
        else:
            delay = 0
        if registers[1] & c_and == c_val:
            registers[25] += 12 + delay # T-states
            registers[24] = (pc + JR_OFFSETS[memory[pc1]]) % 65536 # PC
        else:
            registers[25] += 7 + delay # T-states
            registers[24] = (pc + 2) % 65536 # PC
        registers[15] = R1[registers[15]] # R

    def ld_a_ir(self, registers, r):
        # LD A,I/R
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[15] + 256 * registers[14], 1)))
        else:
            delay = 0
        registers[15] = R2[registers[15]] # R
        a = registers[r]
        registers[0] = a
        registers[25] += 9 + delay # T-states
        if registers[26] and registers[25] % self.frame_duration < self.int_active:
            registers[1] = (a & 0xA8) + (a == 0) * 0x40 + (registers[1] % 2)
        else:
            registers[1] = (a & 0xA8) + (a == 0) * 0x40 + registers[26] * 0x04 + (registers[1] % 2)
        registers[24] = (pc + 2) % 65536 # PC

    def ld_hl_n(self, registers, memory):
        # LD (HL),n
        pc = registers[24]
        pc1 = (pc + 1) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), (pc1, 3), (registers[7] + 256 * registers[6], 3)))
        else:
            delay = 0
        addr = registers[7] + 256 * registers[6]
        if addr > 0x3FFF:
            memory[addr] = memory[pc1]
        registers[15] = R1[registers[15]] # R
        registers[25] += 10 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def ld_r_n(self, registers, memory, r_inc, timing, size, r):
        # LD r,n
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 2:
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 3)))
            else:
                # LD IXh/IXl/IYh/IYl,n
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), ((pc + 2) % 65536, 3)))
        else:
            delay = 0
        end = pc + size
        registers[r] = memory[(end - 1) % 65536]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing + delay # T-states
        registers[24] = end % 65536 # PC

    def ld_r_r(self, registers, r_inc, timing, size, r1, r2):
        # LD r,r
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 1:
                delay = self.contend(registers[25], ((pc, 4),))
            elif timing == 8:
                # LD r,IXh/IXl/IYh/IYl / LD IXh/IXl/IYh/IYl,r
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
            else:
                # LD I/R,A
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[15] + 256 * registers[14], 1)))
        else:
            delay = 0
        registers[15] = r_inc[registers[15]] # R
        registers[r1] = registers[r2]
        registers[25] += timing + delay # T-states
        registers[24] = (pc + size) % 65536 # PC

    def ld_r_rr(self, registers, memory, r, rh, rl):
        # LD r,(HL/DE/BC)
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), (registers[rl] + 256 * registers[rh], 3)))
        else:
            delay = 0
        registers[r] = memory[registers[rl] + 256 * registers[rh]]
        registers[15] = R1[registers[15]] # R
        registers[25] += 7 + delay # T-states
        registers[24] = (pc + 1) % 65536 # PC

    def ld_rr_r(self, registers, memory, rh, rl, r):
        # LD (HL/DE/BC),r
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), (registers[rl] + 256 * registers[rh], 3)))
        else:
            delay = 0
        addr = registers[rl] + 256 * registers[rh]
        if addr > 0x3FFF:
            memory[addr] = registers[r]
        registers[15] = R1[registers[15]] # R
        registers[25] += 7 + delay # T-states
        registers[24] = (pc + 1) % 65536 # PC

    def ld_r_xy(self, registers, memory, r, xyh, xyl):
        # LD r,(IX/Y+d)
        pc = registers[24]
        pc2 = (pc + 2) % 65536
        xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (xy, 3)))
        else:
            delay = 0
        registers[r] = memory[xy]
        registers[15] = R2[registers[15]] # R
        registers[25] += 19 + delay # T-states
        registers[24] = (pc + 3) % 65536 # PC

    def ld_xy_n(self, registers, memory, xyh, xyl):
        # LD (IX/Y+d),n
        pc = registers[24]
        pc2 = (pc + 2) % 65536
        pc3 = (pc + 3) % 65536
        xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc3, 3), (pc3, 1), (pc3, 1), (xy, 3)))
        else:
            delay = 0
        if xy > 0x3FFF:
            memory[xy] = memory[pc3]
        registers[15] = R2[registers[15]] # R
        registers[25] += 19 + delay # T-states
        registers[24] = (pc + 4) % 65536 # PC

    def ld_xy_r(self, registers, memory, xyh, xyl, r):
        # LD (IX/Y+d),r
        pc = registers[24]
        pc2 = (pc + 2) % 65536
        xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (xy, 3)))
        else:
            delay = 0
        if xy > 0x3FFF:
            memory[xy] = registers[r]
        registers[15] = R2[registers[15]] # R
        registers[25] += 19 + delay # T-states
        registers[24] = (pc + 3) % 65536 # PC

    def ld_rr_nn(self, registers, memory, r_inc, timing, size, rh, rl):
        # LD BC/DE/HL/SP/IX/IY,nn
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 3:
                # LD BC/DE/HL/SP,nn
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 3), ((pc + 2) % 65536, 3)))
            else:
                # LD IX/IY,nn
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), ((pc + 2) % 65536, 3), ((pc + 3) % 65536, 3)))
        else:
            delay = 0
        end = pc + size
        if rl == 12:
            registers[12] = memory[(end - 2) % 65536] + 256 * memory[(end - 1) % 65536]
        else:
            registers[rl] = memory[(end - 2) % 65536]
            registers[rh] = memory[(end - 1) % 65536]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing + delay # T-states
        registers[24] = end % 65536 # PC

    def ld_a_m(self, registers, memory):
        # LD A,(nn)
        pc = registers[24]
        pc1 = (pc + 1) % 65536
        pc2 = (pc + 2) % 65536
        nn = memory[pc1] + 256 * memory[pc2]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), (pc1, 3), (pc2, 3), (nn, 3)))
        else:
            delay = 0
        registers[0] = memory[nn]
        registers[15] = R1[registers[15]] # R
        registers[25] += 13 + delay # T-states
        registers[24] = (pc + 3) % 65536 # PC

    def ld_m_a(self, registers, memory):
        # LD (nn),A
        pc = registers[24]
        pc1 = (pc + 1) % 65536
        pc2 = (pc + 2) % 65536
        nn = memory[pc1] + 256 * memory[pc2]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), (pc1, 3), (pc2, 3), (nn, 3)))
        else:
            delay = 0
        if nn > 0x3FFF:
            memory[nn] = registers[0]
        registers[15] = R1[registers[15]] # R
        registers[25] += 13 + delay # T-states
        registers[24] = (pc + 3) % 65536 # PC

    def ld_rr_mm(self, registers, memory, r_inc, timing, size, rh, rl):
        # LD BC/DE/HL/SP/IX/IY,(nn)
        pc = registers[24]
        end = pc + size
        nn = memory[(end - 2) % 65536] + 256 * memory[(end - 1) % 65536]
        nn1 = (nn + 1) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc1 = (pc + 1) % 65536
            pc2 = (pc + 2) % 65536
            if size == 3:
                # LD HL,(nn) (unprefixed)
                delay = self.contend(registers[25], ((pc, 4), (pc1, 3), (pc2, 3), (nn, 3), (nn1, 3)))
            else:
                # LD BC/DE/SP/IX/IY,(nn) (and prefixed LD HL,(nn))
                pc3 = (pc + 3) % 65536
                delay = self.contend(registers[25], ((pc, 4), (pc1, 4), (pc2, 3), (pc3, 3), (nn, 3), (nn1, 3)))
        else:
            delay = 0
        if rl == 12:
            registers[12] = memory[nn] + 256 * memory[nn1]
        else:
            registers[rl] = memory[nn]
            registers[rh] = memory[nn1]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing + delay # T-states
        registers[24] = end % 65536 # PC

    def ld_mm_rr(self, registers, memory, r_inc, timing, size, rh, rl):
        # LD (nn),BC/DE/HL/SP/IX/IY
        pc = registers[24]
        end = pc + size
        nn = memory[(end - 2) % 65536] + 256 * memory[(end - 1) % 65536]
        nn1 = (nn + 1) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc1 = (pc + 1) % 65536
            pc2 = (pc + 2) % 65536
            if size == 3:
                # LD (nn),HL (unprefixed)
                delay = self.contend(registers[25], ((pc, 4), (pc1, 3), (pc2, 3), (nn, 3), (nn1, 3)))
            else:
                # LD (nn),BC/DE/SP/IX/IY (and prefixed LD (nn),HL)
                pc3 = (pc + 3) % 65536
                delay = self.contend(registers[25], ((pc, 4), (pc1, 4), (pc2, 3), (pc3, 3), (nn, 3), (nn1, 3)))
        else:
            delay = 0
        if rl == 12:
            sp = registers[12]
            if nn > 0x3FFF:
                memory[nn] = sp % 256
            if nn1 > 0x3FFF:
                memory[nn1] = sp // 256
        else:
            if nn > 0x3FFF:
                memory[nn] = registers[rl]
            if nn1 > 0x3FFF:
                memory[nn1] = registers[rh]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing + delay # T-states
        registers[24] = end % 65536 # PC

    def ldi(self, registers, memory, inc, repeat):
        # LDI / LDD / LDIR / LDDR
        pc = registers[24]
        hl = registers[7] + 256 * registers[6]
        de = registers[5] + 256 * registers[4]
        bc = registers[3] + 256 * registers[2]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if repeat and bc != 1:
                # 21 T-states
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (de, 3), (de, 1), (de, 1), (de, 1), (de, 1), (de, 1), (de, 1), (de, 1)))
            else:
                # 16 T-states
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (de, 3), (de, 1), (de, 1)))
        else:
            delay = 0
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
            registers[1] = (registers[1] & 0xC1) + ((pc // 256) & 0x28) + 0x04
            registers[25] += 21 + delay # T-states
        else:
            n = registers[0] + at_hl
            registers[1] = (registers[1] & 0xC1) + (n & 0x02) * 16 + (n & 0x08) + (bc > 0) * 0x04
            registers[25] += 16 + delay # T-states
            registers[24] = (pc + 2) % 65536 # PC
        registers[15] = R2[registers[15]] # R

    def ld_sp_rr(self, registers, r_inc, timing, size, rh, rl):
        # LD SP,HL/IX/IY
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            ir = registers[15] + 256 * registers[14]
            if size == 1:
                # LD SP,HL
                delay = self.contend(registers[25], ((pc, 4), (ir, 1), (ir, 1)))
            else:
                # LD SP,IX/IY
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (ir, 1), (ir, 1)))
        else:
            delay = 0
        registers[12] = registers[rl] + 256 * registers[rh]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing + delay # T-states
        registers[24] = (pc + size) % 65536 # PC

    def neg(self, registers, neg):
        # NEG
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        registers[:2] = neg[registers[0]]
        registers[15] = R2[registers[15]] # R
        registers[25] += 8 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def nop(self, registers, r_inc, timing, size):
        # NOP and equivalents
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 1:
                delay = self.contend(registers[25], ((pc, 4),))
            else:
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing + delay # T-states
        registers[24] = (pc + size) % 65536 # PC

    def out_a(self, registers, memory):
        # OUT (n),A
        pc = registers[24]
        pc1 = (pc + 1) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            io_c = self.io_contention(memory[pc1] + 256 * registers[0])
            delay = self.contend(registers[25], ((pc, 4), (pc1, 3), *io_c))
        else:
            delay = 0
        if self.out_tracer:
            a = registers[0]
            self.out_tracer(memory[pc1] + 256 * a, a)
        registers[15] = R1[registers[15]] # R
        registers[25] += 11 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def out_c(self, registers, reg):
        # OUT (C),r/0
        pc = registers[24]
        bc = registers[3] + 256 * registers[2]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            io_c = self.io_contention(bc)
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), *io_c))
        else:
            delay = 0
        if self.out_tracer:
            if reg >= 0:
                self.out_tracer(bc, registers[reg])
            else:
                self.out_tracer(bc, 0)
        registers[15] = R2[registers[15]] # R
        registers[25] += 12 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def outi(self, registers, memory, inc, repeat, parity):
        # OUTI / OUTD / OTIR / OTDR
        pc = registers[24]
        b = registers[2]
        bc = registers[3] + 256 * b
        port = (bc - 256) % 65536
        hl = registers[7] + 256 * registers[6]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            io_c = self.io_contention(port)
            if repeat and b != 1:
                # 21 T-states
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[15] + 256 * registers[14], 1), (hl, 3), *io_c, (bc, 1), (bc, 1), (bc, 1), (bc, 1), (bc, 1)))
            else:
                # 16 T-states
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[15] + 256 * registers[14], 1), (hl, 3), *io_c))
        else:
            delay = 0
        b = (b - 1) % 256
        value = memory[hl]
        if self.out_tracer:
            self.out_tracer(port, value)
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
            registers[1] = (b & 0x80) + ((pc // 256) & 0x28) + h + p + n + c
            registers[25] += 21 + delay # T-states
        else:
            registers[1] = (b & 0xA8) + (b == 0) * 0x40 + c * 0x11 + parity[(j % 8) ^ b] + n
            registers[24] = (pc + 2) % 65536 # PC
            registers[25] += 16 + delay # T-states
        registers[15] = R2[registers[15]] # R

    def pop(self, registers, memory, r_inc, timing, size, rh, rl):
        # POP AF/BC/DE/HL/IX/IY
        pc = registers[24]
        sp = registers[12]
        sp1 = (sp + 1) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 1:
                # POP AF/BC/DE/HL
                delay = self.contend(registers[25], ((pc, 4), (sp, 3), (sp1, 3)))
            else:
                # POP IX/IY
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (sp, 3), (sp1, 3)))
        else:
            delay = 0
        registers[12] = (sp + 2) % 65536
        registers[rl] = memory[sp]
        registers[rh] = memory[sp1]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing + delay # T-states
        registers[24] = (pc + size) % 65536 # PC

    def push(self, registers, memory, r_inc, timing, size, rh, rl):
        # PUSH AF/BC/DE/HL/IX/IY
        pc = registers[24]
        sp = registers[12]
        sp1 = (sp - 1) % 65536
        sp2 = (sp - 2) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 1:
                # PUSH AF/BC/DE/HL
                delay = self.contend(registers[25], ((pc, 4), (registers[15] + 256 * registers[14], 1), (sp1, 3), (sp2, 3)))
            else:
                # PUSH IX/IY
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[15] + 256 * registers[14], 1), (sp1, 3), (sp2, 3)))
        else:
            delay = 0
        registers[12] = sp2
        if sp2 > 0x3FFF:
            memory[sp2] = registers[rl]
        if sp1 > 0x3FFF:
            memory[sp1] = registers[rh]
        registers[15] = r_inc[registers[15]] # R
        registers[25] += timing + delay # T-states
        registers[24] = (pc + size) % 65536 # PC

    def res_hl(self, registers, memory, bit):
        # RES n,(HL)
        pc = registers[24]
        hl = registers[7] + 256 * registers[6]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 3)))
        else:
            delay = 0
        if hl > 0x3FFF:
            memory[hl] &= bit
        registers[15] = R2[registers[15]] # R
        registers[25] += 15 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def res_r(self, registers, bit, reg):
        # RES n,r
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        registers[reg] &= bit
        registers[15] = R2[registers[15]] # R
        registers[25] += 8 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def res_xy(self, registers, memory, bit, xyh, xyl, dest=-1):
        # RES n,(IX/Y+d)
        pc = registers[24]
        pc2 = (pc + 2) % 65536
        xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc3 = (pc + 3) % 65536
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc3, 3), (pc3, 1), (pc3, 1), (xy, 3), (xy, 1), (xy, 3)))
        else:
            delay = 0
        value = memory[xy] & bit
        if xy > 0x3FFF:
            memory[xy] = value
        if dest >= 0:
            registers[dest] = value
        registers[15] = R2[registers[15]] # R
        registers[25] += 23 + delay # T-states
        registers[24] = (pc + 4) % 65536 # PC

    def ret(self, registers, memory, c_and, c_val):
        # RET / RET cc
        sp = registers[12]
        sp1 = (sp + 1) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if c_and:
                if registers[1] & c_and == c_val:
                    # Condition not met
                    delay = self.contend(registers[25], ((registers[24], 4), (registers[15] + 256 * registers[14], 1)))
                else:
                    # Condition met
                    delay = self.contend(registers[25], ((registers[24], 4), (registers[15] + 256 * registers[14], 1), (sp, 3), (sp1, 3)))
            else:
                # RET
                delay = self.contend(registers[25], ((registers[24], 4), (sp, 3), (sp1, 3)))
        else:
            delay = 0
        if c_and:
            if registers[1] & c_and == c_val:
                registers[25] += 5 + delay # T-states
                registers[24] = (registers[24] + 1) % 65536 # PC
            else:
                registers[25] += 11 + delay # T-states
                registers[12] = (sp + 2) % 65536
                registers[24] = memory[sp] + 256 * memory[sp1] # PC
        else:
            registers[25] += 10 + delay # T-states
            registers[12] = (sp + 2) % 65536
            registers[24] = memory[sp] + 256 * memory[sp1] # PC
        registers[15] = R1[registers[15]] # R

    def reti(self, registers, memory):
        # RETI / RETN
        sp = registers[12]
        sp1 = (sp + 1) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (sp, 3), (sp1, 3)))
        else:
            delay = 0
        registers[15] = R2[registers[15]] # R
        registers[25] += 14 + delay # T-states
        registers[12] = (sp + 2) % 65536
        registers[24] = memory[sp] + 256 * memory[sp1] # PC

    def rld(self, registers, memory, sz53p):
        # RLD
        pc = registers[24]
        hl = registers[7] + 256 * registers[6]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 3)))
        else:
            delay = 0
        a = registers[0]
        at_hl = memory[hl]
        if hl > 0x3FFF:
            memory[hl] = ((at_hl * 16) % 256) + (a % 16)
        a_out = registers[0] = (a & 240) + at_hl // 16
        registers[1] = sz53p[a_out] + (registers[1] % 2)
        registers[15] = R2[registers[15]] # R
        registers[25] += 18 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def rrd(self, registers, memory, sz53p):
        # RRD
        pc = registers[24]
        hl = registers[7] + 256 * registers[6]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 3)))
        else:
            delay = 0
        a = registers[0]
        at_hl = memory[hl]
        if hl > 0x3FFF:
            memory[hl] = ((a * 16) % 256) + (at_hl // 16)
        a_out = registers[0] = (a & 240) + (at_hl % 16)
        registers[1] = sz53p[a_out] + (registers[1] % 2)
        registers[15] = R2[registers[15]] # R
        registers[25] += 18 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def rst(self, registers, memory, addr):
        # RST n
        pc = registers[24]
        sp = registers[12]
        sp1 = (sp - 1) % 65536
        sp2 = (sp - 2) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), (registers[15] + 256 * registers[14], 1), (sp1, 3), (sp2, 3)))
        else:
            delay = 0
        registers[12] = sp2
        ret_addr = (pc + 1) % 65536
        if sp2 > 0x3FFF:
            memory[sp2] = ret_addr % 256
        if sp1 > 0x3FFF:
            memory[sp1] = ret_addr // 256
        registers[15] = R1[registers[15]] # R
        registers[25] += 11 + delay # T-states
        registers[24] = addr # PC

    def sbc_hl(self, registers, rh, rl):
        # SBC HL,BC/DE/HL/SP
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            ir = registers[15] + 256 * registers[14]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1)))
        else:
            delay = 0
        rr = registers[rl] + 256 * registers[rh]
        h = registers[6]
        hl = registers[7] + 256 * h
        rr_c = rr + (registers[1] % 2)
        result = (hl - rr_c) % 65536
        r_h = result // 256
        if hl < rr_c:
            f = 0x03 # ......NC
        else:
            f = 0x02 # ......N.
        if result == 0:
            f += 0x40 # .Z......
        f += (h ^ (rr // 256) ^ r_h) & 0x10 # ...H....
        if hl ^ rr > 0x7FFF and hl ^ result > 0x7FFF:
            f += 0x04 # .....P..
        registers[1] = f + (r_h & 0xA8)
        registers[7] = result % 256
        registers[6] = r_h
        registers[15] = R2[registers[15]] # R
        registers[25] += 15 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def set_hl(self, registers, memory, bit):
        # SET n,(HL)
        pc = registers[24]
        hl = registers[7] + 256 * registers[6]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 3)))
        else:
            delay = 0
        if hl > 0x3FFF:
            memory[hl] |= bit
        registers[15] = R2[registers[15]] # R
        registers[25] += 15 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def set_r(self, registers, bit, reg):
        # SET n,r
        pc = registers[24]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        registers[reg] |= bit
        registers[15] = R2[registers[15]] # R
        registers[25] += 8 + delay # T-states
        registers[24] = (pc + 2) % 65536 # PC

    def set_xy(self, registers, memory, bit, xyh, xyl, dest=-1):
        # SET n,(IX/Y+d)
        pc = registers[24]
        pc2 = (pc + 2) % 65536
        xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc3 = (pc + 3) % 65536
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc3, 3), (pc3, 1), (pc3, 1), (xy, 3), (xy, 1), (xy, 3)))
        else:
            delay = 0
        value = memory[xy] | bit
        if xy > 0x3FFF:
            memory[xy] = value
        if dest >= 0:
            registers[dest] = value
        registers[15] = R2[registers[15]] # R
        registers[25] += 23 + delay # T-states
        registers[24] = (pc + 4) % 65536 # PC
