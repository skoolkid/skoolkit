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

from skoolkit.simulator import Simulator, OFFSETS

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
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((registers[24], 4), (registers[7] + 256 * registers[6], 3)))
        else:
            delay = 0
        super().af_hl(registers, memory, af)
        registers[25] += delay

    def af_n(self, registers, memory, af):
        # ADD A,n / AND n / CP n / OR n / SUB n / XOR n
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 3)))
        else:
            delay = 0
        super().af_n(registers, memory, af)
        registers[25] += delay

    def af_r(self, registers, r_inc, timing, size, af, r):
        # ADD A,r / AND r / CP r / OR r / SUB r / XOR r
        # CPL / DAA / RLA / RLCA / RRA / RRCA
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 1:
                # CPL / DAA / RLA / RLCA / RRA / RRCA; r = A/B/C/D/E/H/L
                delay = self.contend(registers[25], ((registers[24], 4),))
            else:
                # r = IXh/IXl/IYh/IYl
                pc = registers[24]
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        super().af_r(registers, r_inc, timing, size, af, r)
        registers[25] += delay

    def af_xy(self, registers, memory, af, xyh, xyl):
        # ADD A,(IX/Y+d) / AND (IX/Y+d) / CP (IX/Y+d) / OR (IX/Y+d)
        # SUB (IX/Y+d) / XOR (IX/Y+d)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc2 = (pc + 2) % 65536
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), ((registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536, 3)))
        else:
            delay = 0
        super().af_xy(registers, memory, af, xyh, xyl)
        registers[25] += delay

    def afc_hl(self, registers, memory, afc):
        # ADC/SBC A,(HL)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((registers[24], 4), (registers[7] + 256 * registers[6], 3)))
        else:
            delay = 0
        super().afc_hl(registers, memory, afc)
        registers[25] += delay

    def afc_n(self, registers, memory, afc):
        # ADC/SBC A,n
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 3)))
        else:
            delay = 0
        super().afc_n(registers, memory, afc)
        registers[25] += delay

    def afc_r(self, registers, r_inc, timing, size, afc, r):
        # ADC/SBC A,r (r != A)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 1:
                # r = B/C/D/E/H/L
                delay = self.contend(registers[25], ((registers[24], 4),))
            else:
                # r = IXh/IXl/IYh/IYl
                pc = registers[24]
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        super().afc_r(registers, r_inc, timing, size, afc, r)
        registers[25] += delay

    def afc_xy(self, registers, memory, afc, xyh, xyl):
        # ADC/SBC A,(IX/Y+d)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc2 = (pc + 2) % 65536
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), ((registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536, 3)))
        else:
            delay = 0
        super().afc_xy(registers, memory, afc, xyh, xyl)
        registers[25] += delay

    def f_hl(self, registers, memory, f):
        # RLC/RRC/SLA/SLL/SRA/SRL (HL)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            hl = registers[7] + 256 * registers[6]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 3)))
        else:
            delay = 0
        super().f_hl(registers, memory, f)
        registers[25] += delay

    def f_r(self, registers, f, r):
        # RLC/RRC/SLA/SLL/SRA/SRL r
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        super().f_r(registers, f, r)
        registers[25] += delay

    def f_xy(self, registers, memory, f, xyh, xyl, dest=-1):
        # RLC/RRC/SLA/SLL/SRA/SRL (IX/Y+d)[,r]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc2 = (pc + 2) % 65536
            pc3 = (pc + 3) % 65536
            xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc3, 3), (pc3, 1), (pc3, 1), (xy, 3), (xy, 1), (xy, 3)))
        else:
            delay = 0
        super().f_xy(registers, memory, f, xyh, xyl, dest)
        registers[25] += delay

    def fc_hl(self, registers, memory, r_inc, timing, size, fc):
        # DEC/INC/RL/RR (HL)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            hl = registers[7] + 256 * registers[6]
            if size == 2:
                # RL/RR (HL)
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 3)))
            else:
                # DEC/INC (HL)
                delay = self.contend(registers[25], ((pc, 4), (hl, 3), (hl, 1), (hl, 3)))
        else:
            delay = 0
        super().fc_hl(registers, memory, r_inc, timing, size, fc)
        registers[25] += delay

    def fc_r(self, registers, r_inc, timing, size, fc, r):
        # DEC/INC/RL/RR r / ADC A,A / SBC A,A
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 1:
                # DEC/INC r / ADC A,A / SBC A,A
                delay = self.contend(registers[25], ((registers[24], 4),))
            else:
                # RL/RR r
                pc = registers[24]
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        super().fc_r(registers, r_inc, timing, size, fc, r)
        registers[25] += delay

    def fc_xy(self, registers, memory, size, fc, xyh, xyl, dest=-1):
        # DEC/INC/RL/RR (IX/Y+d)[,r]
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc2 = (pc + 2) % 65536
            xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536
            if size == 3:
                # DEC/INC (IX/Y+d)
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (xy, 3), (xy, 1), (xy, 3)))
            else:
                # RL/RR (IX/Y+d)[,r]
                pc3 = (pc + 3) % 65536
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc3, 3), (pc3, 1), (pc3, 1), (xy, 3), (xy, 1), (xy, 3)))
        else:
            delay = 0
        super().fc_xy(registers, memory, size, fc, xyh, xyl, dest)
        registers[25] += delay

    def adc_hl(self, registers, rh, rl):
        # ADC HL,BC/DE/HL/SP
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            ir = registers[15] + 256 * registers[14]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1)))
        else:
            delay = 0
        super().adc_hl(registers, rh, rl)
        registers[25] += delay

    def add_rr(self, registers, r_inc, timing, size, ah, al, rh, rl):
        # ADD HL/IX/IY,BC/DE/HL/SP/IX/IY
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            ir = registers[15] + 256 * registers[14]
            if size == 1:
                # ADD HL,BC/DE/HL/SP
                delay = self.contend(registers[25], ((registers[24], 4), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1)))
            else:
                # ADD IX/IY,BC/DE/SP/IX/IY
                pc = registers[24]
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1)))
        else:
            delay = 0
        super().add_rr(registers, r_inc, timing, size, ah, al, rh, rl)
        registers[25] += delay

    def bit_hl(self, registers, memory, bit, b):
        # BIT n,(HL)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            hl = registers[7] + 256 * registers[6]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1)))
        else:
            delay = 0
        super().bit_hl(registers, memory, bit, b)
        registers[25] += delay

    def bit_r(self, registers, bit, b, reg):
        # BIT n,r
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        super().bit_r(registers, bit, b, reg)
        registers[25] += delay

    def bit_xy(self, registers, memory, bit, b, xyh, xyl):
        # BIT n,(IX/Y+d)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc2 = (pc + 2) % 65536
            pc3 = (pc + 3) % 65536
            xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc3, 3), (pc3, 1), (pc3, 1), (xy, 3), (xy, 1)))
        else:
            delay = 0
        super().bit_xy(registers, memory, bit, b, xyh, xyl)
        registers[25] += delay

    def call(self, registers, memory, c_and, c_val):
        # CALL nn / CALL cc,nn
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            if c_and and registers[1] & c_and == c_val:
                # Condition not met
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 3), ((pc + 2) % 65536, 3)))
            else:
                # Condition met
                sp = registers[12]
                pc2 = (pc + 2) % 65536
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 3), (pc2, 3), (pc2, 1), ((sp - 1) % 65536, 3), ((sp - 2) % 65536, 3)))
        else:
            delay = 0
        super().call(registers, memory, c_and, c_val)
        registers[25] += delay

    def cf(self, registers, cf):
        # CCF / SCF
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((registers[24], 4),))
        else:
            delay = 0
        super().cf(registers, cf)
        registers[25] += delay

    def cpi(self, registers, memory, inc, repeat):
        # CPI / CPD / CPIR / CPDR
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            hl = registers[7] + 256 * registers[6]
            if repeat and registers[0] != memory[hl] and registers[3] + 256 * registers[2] != 1:
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1)))
            else:
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1)))
        else:
            delay = 0
        super().cpi(registers, memory, inc, repeat)
        registers[25] += delay

    def di_ei(self, registers, iff):
        # DI / EI
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((registers[24], 4),))
        else:
            delay = 0
        super().di_ei(registers, iff)
        registers[25] += delay

    def djnz(self, registers, memory):
        # DJNZ nn
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            if registers[2] != 1:
                pc1 = (pc + 1) % 65536
                delay = self.contend(registers[25], ((pc, 4), (registers[15] + 256 * registers[14], 1), (pc1, 3), (pc1, 1), (pc1, 1), (pc1, 1), (pc1, 1), (pc1, 1)))
            else:
                delay = self.contend(registers[25], ((pc, 4), (registers[15] + 256 * registers[14], 1), ((pc + 1) % 65536, 3)))
        else:
            delay = 0
        super().djnz(registers, memory)
        registers[25] += delay

    def ex_af(self, registers):
        # EX AF,AF'
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((registers[24], 4),))
        else:
            delay = 0
        super().ex_af(registers)
        registers[25] += delay

    def ex_de_hl(self, registers):
        # EX DE,HL
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((registers[24], 4),))
        else:
            delay = 0
        super().ex_de_hl(registers)
        registers[25] += delay

    def ex_sp(self, registers, memory, r_inc, timing, size, rh, rl):
        # EX (SP),HL/IX/IY
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            sp = registers[12]
            sp1 = (sp + 1) % 65536
            if size == 1:
                # EX (SP),HL
                delay = self.contend(registers[25], ((registers[24], 4), (sp, 3), (sp1, 3), (sp1, 1), (sp1, 3), (sp, 3), (sp, 1), (sp, 1)))
            else:
                # EX (SP),IX/IY
                pc = registers[24]
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (sp, 3), (sp1, 3), (sp1, 1), (sp1, 3), (sp, 3), (sp, 1), (sp, 1)))
        else:
            delay = 0
        super().ex_sp(registers, memory, r_inc, timing, size, rh, rl)
        registers[25] += delay

    def exx(self, registers):
        # EXX
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((registers[24], 4),))
        else:
            delay = 0
        super().exx(registers)
        registers[25] += delay

    def halt(self, registers):
        # HALT
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if registers[28]:
                delay = self.contend(registers[25], (((registers[24] + 1) % 65536, 4),))
            else:
                delay = self.contend(registers[25], ((registers[24], 4),))
        else:
            delay = 0
        super().halt(registers)
        registers[25] += delay

    def im(self, registers, mode):
        # IM 0/1/2
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        super().im(registers, mode)
        registers[25] += delay

    def in_a(self, registers, memory):
        # IN A,(n)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc1 = (pc + 1) % 65536
            io_c = self.io_contention(memory[pc1] + 256 * registers[0])
            delay = self.contend(registers[25], ((pc, 4), (pc1, 3), *io_c))
        else:
            delay = 0
        super().in_a(registers, memory)
        registers[25] += delay

    def in_c(self, registers, reg, sz53p):
        # IN r,(C)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            io_c = self.io_contention(registers[3] + 256 * registers[2])
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), *io_c))
        else:
            delay = 0
        super().in_c(registers, reg, sz53p)
        registers[25] += delay

    def inc_dec_rr(self, registers, r_inc, timing, size, inc, rh, rl):
        # INC/DEC BC/DE/HL/SP/IX/IY
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            ir = registers[15] + 256 * registers[14]
            if size == 1:
                # INC/DEC BC/DE/HL/SP
                delay = self.contend(registers[25], ((registers[24], 4), (ir, 1), (ir, 1)))
            else:
                # INC/DEC IX/IY
                pc = registers[24]
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (ir, 1), (ir, 1)))
        else:
            delay = 0
        super().inc_dec_rr(registers, r_inc, timing, size, inc, rh, rl)
        registers[25] += delay

    def ini(self, registers, memory, inc, repeat, parity):
        # INI / IND / INIR / INDR
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            hl = registers[7] + 256 * registers[6]
            b = registers[2]
            io_c = self.io_contention(registers[3] + 256 * b)
            if repeat and b != 1:
                # 21 T-states
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[15] + 256 * registers[14], 1), *io_c, (hl, 3), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 1)))
            else:
                # 16 T-states
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[15] + 256 * registers[14], 1), *io_c, (hl, 3)))
        else:
            delay = 0
        super().ini(registers, memory, inc, repeat, parity)
        registers[25] += delay

    def jp(self, registers, memory, c_and, c_val):
        # JP nn / JP cc,nn
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 3), ((pc + 2) % 65536, 3)))
        else:
            delay = 0
        super().jp(registers, memory, c_and, c_val)
        registers[25] += delay

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
        super().jp_rr(registers, r_inc, timing, rh, rl)
        registers[25] += delay

    def jr(self, registers, memory, c_and, c_val):
        # JR nn / JR cc,nn
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            if registers[1] & c_and == c_val:
                # Condition met
                pc1 = (pc + 1) % 65536
                delay = self.contend(registers[25], ((pc, 4), (pc1, 3), (pc1, 1), (pc1, 1), (pc1, 1), (pc1, 1), (pc1, 1)))
            else:
                # Condition not met
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 3)))
        else:
            delay = 0
        super().jr(registers, memory, c_and, c_val)
        registers[25] += delay

    def ld_a_ir(self, registers, r):
        # LD A,I/R
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[15] + 256 * registers[14], 1)))
        else:
            delay = 0
        super().ld_a_ir(registers, r)
        registers[25] += delay

    def ld_hl_n(self, registers, memory):
        # LD (HL),n
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 3), (registers[7] + 256 * registers[6], 3)))
        else:
            delay = 0
        super().ld_hl_n(registers, memory)
        registers[25] += delay

    def ld_r_n(self, registers, memory, r_inc, timing, size, r):
        # LD r,n
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            if size == 2:
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 3)))
            else:
                # LD IXh/IXl/IYh/IYl,n
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), ((pc + 2) % 65536, 3)))
        else:
            delay = 0
        super().ld_r_n(registers, memory, r_inc, timing, size, r)
        registers[25] += delay

    def ld_r_r(self, registers, r_inc, timing, size, r1, r2):
        # LD r,r
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 1:
                delay = self.contend(registers[25], ((registers[24], 4),))
            elif timing == 8:
                # LD r,IXh/IXl/IYh/IYl / LD IXh/IXl/IYh/IYl,r
                pc = registers[24]
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
            else:
                # LD I/R,A
                pc = registers[24]
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[15] + 256 * registers[14], 1)))
        else:
            delay = 0
        super().ld_r_r(registers, r_inc, timing, size, r1, r2)
        registers[25] += delay

    def ld_r_rr(self, registers, memory, r, rh, rl):
        # LD r,(HL/DE/BC)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((registers[24], 4), (registers[rl] + 256 * registers[rh], 3)))
        else:
            delay = 0
        super().ld_r_rr(registers, memory, r, rh, rl)
        registers[25] += delay

    def ld_rr_r(self, registers, memory, rh, rl, r):
        # LD (HL/DE/BC),r
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            delay = self.contend(registers[25], ((registers[24], 4), (registers[rl] + 256 * registers[rh], 3)))
        else:
            delay = 0
        super().ld_rr_r(registers, memory, rh, rl, r)
        registers[25] += delay

    def ld_r_xy(self, registers, memory, r, xyh, xyl):
        # LD r,(IX/Y+d)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc2 = (pc + 2) % 65536
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), ((registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536, 3)))
        else:
            delay = 0
        super().ld_r_xy(registers, memory, r, xyh, xyl)
        registers[25] += delay

    def ld_xy_n(self, registers, memory, xyh, xyl):
        # LD (IX/Y+d),n
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc2 = (pc + 2) % 65536
            pc3 = (pc + 3) % 65536
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc3, 3), (pc3, 1), (pc3, 1), ((registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536, 3)))
        else:
            delay = 0
        super().ld_xy_n(registers, memory, xyh, xyl)
        registers[25] += delay

    def ld_xy_r(self, registers, memory, xyh, xyl, r):
        # LD (IX/Y+d),r
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc2 = (pc + 2) % 65536
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), (pc2, 1), ((registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536, 3)))
        else:
            delay = 0
        super().ld_xy_r(registers, memory, xyh, xyl, r)
        registers[25] += delay

    def ld_rr_nn(self, registers, memory, r_inc, timing, size, rh, rl):
        # LD BC/DE/HL/SP/IX/IY,nn
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            if size == 3:
                # LD BC/DE/HL/SP,nn
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 3), ((pc + 2) % 65536, 3)))
            else:
                # LD IX/IY,nn
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), ((pc + 2) % 65536, 3), ((pc + 3) % 65536, 3)))
        else:
            delay = 0
        super().ld_rr_nn(registers, memory, r_inc, timing, size, rh, rl)
        registers[25] += delay

    def ld_a_m(self, registers, memory):
        # LD A,(nn)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc1 = (pc + 1) % 65536
            pc2 = (pc + 2) % 65536
            delay = self.contend(registers[25], ((pc, 4), (pc1, 3), (pc2, 3), (memory[pc1] + 256 * memory[pc2], 3)))
        else:
            delay = 0
        super().ld_a_m(registers, memory)
        registers[25] += delay

    def ld_m_a(self, registers, memory):
        # LD (nn),A
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc1 = (pc + 1) % 65536
            pc2 = (pc + 2) % 65536
            delay = self.contend(registers[25], ((pc, 4), (pc1, 3), (pc2, 3), (memory[pc1] + 256 * memory[pc2], 3)))
        else:
            delay = 0
        super().ld_m_a(registers, memory)
        registers[25] += delay

    def ld_rr_mm(self, registers, memory, r_inc, timing, size, rh, rl):
        # LD BC/DE/HL/SP/IX/IY,(nn)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc1 = (pc + 1) % 65536
            pc2 = (pc + 2) % 65536
            if size == 3:
                # LD HL,(nn) (unprefixed)
                addr = memory[pc1] + 256 * memory[pc2]
                delay = self.contend(registers[25], ((pc, 4), (pc1, 3), (pc2, 3), (addr, 3), ((addr + 1) % 65536, 3)))
            else:
                # LD BC/DE/SP/IX/IY,(nn) (and prefixed LD HL,(nn))
                pc3 = (pc + 3) % 65536
                addr = memory[pc2] + 256 * memory[pc3]
                delay = self.contend(registers[25], ((pc, 4), (pc1, 4), (pc2, 3), (pc3, 3), (addr, 3), ((addr + 1) % 65536, 3)))
        else:
            delay = 0
        super().ld_rr_mm(registers, memory, r_inc, timing, size, rh, rl)
        registers[25] += delay

    def ld_mm_rr(self, registers, memory, r_inc, timing, size, rh, rl):
        # LD (nn),BC/DE/HL/SP/IX/IY
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc1 = (pc + 1) % 65536
            pc2 = (pc + 2) % 65536
            if size == 3:
                # LD (nn),HL (unprefixed)
                addr = memory[pc1] + 256 * memory[pc2]
                delay = self.contend(registers[25], ((pc, 4), (pc1, 3), (pc2, 3), (addr, 3), ((addr + 1) % 65536, 3)))
            else:
                # LD (nn),BC/DE/SP/IX/IY (and prefixed LD (nn),HL)
                pc3 = (pc + 3) % 65536
                addr = memory[pc2] + 256 * memory[pc3]
                delay = self.contend(registers[25], ((pc, 4), (pc1, 4), (pc2, 3), (pc3, 3), (addr, 3), ((addr + 1) % 65536, 3)))
        else:
            delay = 0
        super().ld_mm_rr(registers, memory, r_inc, timing, size, rh, rl)
        registers[25] += delay

    def ldi(self, registers, memory, inc, repeat):
        # LDI / LDD / LDIR / LDDR
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            de = registers[5] + 256 * registers[4]
            if repeat and registers[3] + 256 * registers[2] != 1:
                # 21 T-states
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[7] + 256 * registers[6], 3), (de, 3), (de, 1), (de, 1), (de, 1), (de, 1), (de, 1), (de, 1), (de, 1)))
            else:
                # 16 T-states
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[7] + 256 * registers[6], 3), (de, 3), (de, 1), (de, 1)))
        else:
            delay = 0
        super().ldi(registers, memory, inc, repeat)
        registers[25] += delay

    def ld_sp_rr(self, registers, r_inc, timing, size, rh, rl):
        # LD SP,HL/IX/IY
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            ir = registers[15] + 256 * registers[14]
            if size == 1:
                # LD SP,HL
                delay = self.contend(registers[25], ((registers[24], 4), (ir, 1), (ir, 1)))
            else:
                # LD SP,IX/IY
                pc = registers[24]
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (ir, 1), (ir, 1)))
        else:
            delay = 0
        super().ld_sp_rr(registers, r_inc, timing, size, rh, rl)
        registers[25] += delay

    def neg(self, registers, neg):
        # NEG
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        super().neg(registers, neg)
        registers[25] += delay

    def nop(self, registers, r_inc, timing, size):
        # NOP and equivalents
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if size == 1:
                delay = self.contend(registers[25], ((registers[24], 4),))
            else:
                pc = registers[24]
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        super().nop(registers, r_inc, timing, size)
        registers[25] += delay

    def out_a(self, registers, memory):
        # OUT (n),A
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc1 = (pc + 1) % 65536
            io_c = self.io_contention(memory[pc1] + 256 * registers[0])
            delay = self.contend(registers[25], ((pc, 4), (pc1, 3), *io_c))
        else:
            delay = 0
        super().out_a(registers, memory)
        registers[25] += delay

    def out_c(self, registers, reg):
        # OUT (C),r/0
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            io_c = self.io_contention(registers[3] + 256 * registers[2])
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), *io_c))
        else:
            delay = 0
        super().out_c(registers, reg)
        registers[25] += delay

    def outi(self, registers, memory, inc, repeat, parity):
        # OUTI / OUTD / OTIR / OTDR
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            b = registers[2]
            bc = registers[3] + 256 * b
            io_c = self.io_contention((bc - 256) % 65536)
            if repeat and b != 1:
                # 21 T-states
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[15] + 256 * registers[14], 1), (registers[7] + 256 * registers[6], 3), *io_c, (bc, 1), (bc, 1), (bc, 1), (bc, 1), (bc, 1)))
            else:
                # 16 T-states
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[15] + 256 * registers[14], 1), (registers[7] + 256 * registers[6], 3), *io_c))
        else:
            delay = 0
        super().outi(registers, memory, inc, repeat, parity)
        registers[25] += delay

    def pop(self, registers, memory, r_inc, timing, size, rh, rl):
        # POP AF/BC/DE/HL/IX/IY
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            sp = registers[12]
            if size == 1:
                # POP AF/BC/DE/HL
                delay = self.contend(registers[25], ((registers[24], 4), (sp, 3), ((sp + 1) % 65536, 3)))
            else:
                # POP IX/IY
                pc = registers[24]
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (sp, 3), ((sp + 1) % 65536, 3)))
        else:
            delay = 0
        super().pop(registers, memory, r_inc, timing, size, rh, rl)
        registers[25] += delay

    def push(self, registers, memory, r_inc, timing, size, rh, rl):
        # PUSH AF/BC/DE/HL/IX/IY
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            sp = registers[12]
            if size == 1:
                # PUSH AF/BC/DE/HL
                delay = self.contend(registers[25], ((registers[24], 4), (registers[15] + 256 * registers[14], 1), ((sp - 1) % 65536, 3), ((sp - 2) % 65536, 3)))
            else:
                # PUSH IX/IY
                pc = registers[24]
                delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (registers[15] + 256 * registers[14], 1), ((sp - 1) % 65536, 3), ((sp - 2) % 65536, 3)))
        else:
            delay = 0
        super().push(registers, memory, r_inc, timing, size, rh, rl)
        registers[25] += delay

    def res_hl(self, registers, memory, bit):
        # RES n,(HL)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            hl = registers[7] + 256 * registers[6]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 3)))
        else:
            delay = 0
        super().res_hl(registers, memory, bit)
        registers[25] += delay

    def res_r(self, registers, bit, reg):
        # RES n,r
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        super().res_r(registers, bit, reg)
        registers[25] += delay

    def res_xy(self, registers, memory, bit, xyh, xyl, dest=-1):
        # RES n,(IX/Y+d)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc2 = (pc + 2) % 65536
            pc3 = (pc + 3) % 65536
            xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc3, 3), (pc3, 1), (pc3, 1), (xy, 3), (xy, 1), (xy, 3)))
        else:
            delay = 0
        super().res_xy(registers, memory, bit, xyh, xyl, dest)
        registers[25] += delay

    def ret(self, registers, memory, c_and, c_val):
        # RET / RET cc
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            if c_and:
                if registers[1] & c_and == c_val:
                    # Condition not met
                    delay = self.contend(registers[25], ((registers[24], 4), (registers[15] + 256 * registers[14], 1)))
                else:
                    # Condition met
                    sp = registers[12]
                    delay = self.contend(registers[25], ((registers[24], 4), (registers[15] + 256 * registers[14], 1), (sp, 3), ((sp + 1) % 65536, 3)))
            else:
                # RET
                sp = registers[12]
                delay = self.contend(registers[25], ((registers[24], 4), (sp, 3), ((sp + 1) % 65536, 3)))
        else:
            delay = 0
        super().ret(registers, memory, c_and, c_val)
        registers[25] += delay

    def reti(self, registers, memory):
        # RETI / RETN
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            sp = registers[12]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (sp, 3), ((sp + 1) % 65536, 3)))
        else:
            delay = 0
        super().reti(registers, memory)
        registers[25] += delay

    def rld(self, registers, memory, sz53p):
        # RLD
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            hl = registers[7] + 256 * registers[6]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 3)))
        else:
            delay = 0
        super().rld(registers, memory, sz53p)
        registers[25] += delay

    def rrd(self, registers, memory, sz53p):
        # RRD
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            hl = registers[7] + 256 * registers[6]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 1), (hl, 1), (hl, 1), (hl, 3)))
        else:
            delay = 0
        super().rrd(registers, memory, sz53p)
        registers[25] += delay

    def rst(self, registers, memory, addr):
        # RST n
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            sp = registers[12]
            delay = self.contend(registers[25], ((registers[24], 4), (registers[15] + 256 * registers[14], 1), ((sp - 1) % 65536, 3), ((sp - 2) % 65536, 3)))
        else:
            delay = 0
        super().rst(registers, memory, addr)
        registers[25] += delay

    def sbc_hl(self, registers, rh, rl):
        # SBC HL,BC/DE/HL/SP
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            ir = registers[15] + 256 * registers[14]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1), (ir, 1)))
        else:
            delay = 0
        super().sbc_hl(registers, rh, rl)
        registers[25] += delay

    def set_hl(self, registers, memory, bit):
        # SET n,(HL)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            hl = registers[7] + 256 * registers[6]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (hl, 3), (hl, 1), (hl, 3)))
        else:
            delay = 0
        super().set_hl(registers, memory, bit)
        registers[25] += delay

    def set_r(self, registers, bit, reg):
        # SET n,r
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4)))
        else:
            delay = 0
        super().set_r(registers, bit, reg)
        registers[25] += delay

    def set_xy(self, registers, memory, bit, xyh, xyl, dest=-1):
        # SET n,(IX/Y+d)
        if self.t0 < registers[25] % self.frame_duration < self.t1:
            pc = registers[24]
            pc2 = (pc + 2) % 65536
            pc3 = (pc + 3) % 65536
            xy = (registers[xyl] + 256 * registers[xyh] + OFFSETS[memory[pc2]]) % 65536
            delay = self.contend(registers[25], ((pc, 4), ((pc + 1) % 65536, 4), (pc2, 3), (pc3, 3), (pc3, 1), (pc3, 1), (xy, 3), (xy, 1), (xy, 3)))
        else:
            delay = 0
        super().set_xy(registers, memory, bit, xyh, xyl, dest)
        registers[25] += delay
