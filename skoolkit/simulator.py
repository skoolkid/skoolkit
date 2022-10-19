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

PARITY = (
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4,
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4,
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4
)

FRAME_DURATION = 69888

CONFIG = {
    'fast_djnz': False,
    'fast_ldir': False,
}

class Simulator:
    def __init__(self, snapshot, registers=None, state=None, config=None):
        self.snapshot = snapshot
        self.registers = {
            'A': 0,
            'B': 0,
            'C': 0,
            'D': 0,
            'E': 0,
            'F': 0,
            'H': 0,
            'I': 63,
            'L': 0,
            'R': 0,
            'SP': 23552,
            'IXh': 0,
            'IXl': 0,
            'IYh': 92,
            'IYl': 58,
            '^A': 0,
            '^B': 0,
            '^C': 0,
            '^D': 0,
            '^E': 0,
            '^F': 0,
            '^H': 0,
            '^L': 0
        }
        self.pc = 0
        if registers:
            self.set_registers(registers)
        if state is None:
            state = {}
        self.ppcount = state.get('ppcount', 0)
        self.imode = state.get('im', 1)
        self.iff2 = state.get('iff', 0)
        self.tstates = state.get('tstates', 0)
        cfg = CONFIG.copy()
        if config:
            cfg.update(config)
        self.create_opcodes()
        if cfg['fast_djnz']:
            self.opcodes[0x10] = self.djnz_fast
        if cfg['fast_ldir']:
            self.after_ED[0xB0] = partial(self.ldir_fast, 1)
            self.after_ED[0xB8] = partial(self.ldir_fast, -1)
        self.itracer = None
        self.in_tracer = None
        self.out_tracer = None
        self.peek_tracer = None
        self.poke_tracer = None

    def set_tracer(self, tracer):
        if hasattr(tracer, 'trace'):
            self.itracer = partial(tracer.trace, self)
        else:
            self.itracer = None
        if hasattr(tracer, 'read_port'):
            self.in_tracer = partial(tracer.read_port, self)
        else:
            self.in_tracer = None
        if hasattr(tracer, 'write_port'):
            self.out_tracer = partial(tracer.write_port, self)
        else:
            self.out_tracer = None
        if hasattr(tracer, 'read_memory'):
            self.peek_tracer = partial(tracer.read_memory, self)
        else:
            self.peek_tracer = None
        if hasattr(tracer, 'write_memory'):
            self.poke_tracer = partial(tracer.write_memory, self)
        else:
            self.poke_tracer = None

    def run(self, start=None, stop=None):
        if start is None:
            pc = self.pc
        else:
            self.pc = start
            pc = start
        opcodes = self.opcodes
        after_CB = self.after_CB
        after_DD = self.after_DD
        after_DDCB = self.after_DDCB
        after_ED = self.after_ED
        after_FD = self.after_FD
        after_FDCB = self.after_FDCB
        snapshot = self.snapshot
        registers = self.registers
        itracer = self.itracer
        running = True
        while running:
            opcode = snapshot[pc]
            method = opcodes[opcode]
            if method:
                r_inc = 1
            elif opcode == 0xCB:
                r_inc = 2
                method = after_CB[snapshot[(pc + 1) & 0xFFFF]]
            elif opcode == 0xED:
                r_inc = 2
                method = after_ED[snapshot[(pc + 1) & 0xFFFF]]
            elif opcode == 0xDD:
                r_inc = 2
                method = after_DD[snapshot[(pc + 1) & 0xFFFF]]
                if method is None:
                    method = after_DDCB[snapshot[(pc + 3) & 0xFFFF]]
            else:
                r_inc = 2
                method = after_FD[snapshot[(pc + 1) & 0xFFFF]]
                if method is None:
                    method = after_FDCB[snapshot[(pc + 3) & 0xFFFF]]
            pc, tstates = method()
            r = registers['R']
            registers['R'] = (r & 0x80) + ((r + r_inc) & 0x7F)
            pc &= 0xFFFF
            if itracer:
                running = pc != stop
                address = self.pc
                self.pc = pc
                self.tstates += tstates
                if itracer(address):
                    running = False
                pc = self.pc
            else:
                if stop is None:
                    running = False
                else:
                    running = pc != stop
                self.pc = pc
                self.tstates += tstates

    def set_registers(self, registers):
        for reg, value in registers.items():
            if reg == 'PC':
                self.pc = value
            elif reg == 'SP' or len(reg) == 1:
                self.registers[reg] = value
            elif reg.startswith(('IX', 'IY')):
                if len(reg) == 3:
                    self.registers[reg] = value
                else:
                    self.registers[reg + 'h'] = value // 256
                    self.registers[reg + 'l'] = value % 256
            elif reg.startswith('^'):
                if len(reg) == 2:
                    self.registers[reg] = value
                else:
                    self.registers['^' + reg[1]] = value // 256
                    self.registers['^' + reg[2]] = value % 256
            elif len(reg) == 2:
                self.registers[reg[0]] = value // 256
                self.registers[reg[1]] = value % 256

    def index(self):
        offset = self.snapshot[(self.pc + 2) & 0xFFFF]
        if offset >= 128:
            offset -= 256
        if self.snapshot[self.pc] == 0xDD:
            return (self.registers['IXl'] + 256 * self.registers['IXh'] + offset) & 0xFFFF
        return (self.registers['IYl'] + 256 * self.registers['IYh'] + offset) & 0xFFFF

    def get_operand_value(self, size, reg):
        if reg in self.registers:
            return self.registers[reg]
        if reg in ('(HL)', '(DE)', '(BC)'):
            return self.peek(self.registers[reg[2]] + 256 * self.registers[reg[1]])
        if reg in ('Xd', 'Yd'):
            return self.peek(self.index())
        return self.snapshot[(self.pc + size - 1) & 0xFFFF]

    def set_operand_value(self, reg, value):
        if reg in self.registers:
            self.registers[reg] = value
        elif reg in ('(HL)', '(DE)', '(BC)'):
            self.poke(self.registers[reg[2]] + 256 * self.registers[reg[1]], value)
        else:
            self.poke(self.index(), value)

    def peek(self, address, count=1):
        if self.peek_tracer:
            self.peek_tracer(address, count)
        if count == 1:
            return self.snapshot[address]
        return self.snapshot[address], self.snapshot[(address + 1) & 0xFFFF]

    def poke(self, address, *values):
        if self.poke_tracer:
            self.poke_tracer(address, values)
        if address > 0x3FFF:
            self.snapshot[address] = values[0]
        if len(values) > 1:
            address = (address + 1) & 0xFFFF
            if address > 0x3FFF:
                self.snapshot[address] = values[1]

    def add_a(self, timing, size, reg=None, carry=0, mult=1):
        value = self.get_operand_value(size, reg)
        old_c = self.registers['F'] & 0x01
        old_a = self.registers['A']
        addend = value + carry * old_c
        a = old_a + mult * addend
        if a < 0 or a > 255:
            a = a & 255
            f = (a & 0xA8) | 0x01 # S.5.3..C
        else:
            f = a & 0xA8          # S.5.3..C
        if a == 0:
            f |= 0x40 # .Z......
        opcode = self.snapshot[self.pc]
        if mult == 1:
            s_value = value
            # 0x8F: ADC A,A
            if (opcode == 0x8F and old_a & 0x0F == 0x0F) or ((old_a & 0x0F) + (addend & 0x0F)) & 0x10:
                f |= 0x10 # ...H....
        else:
            s_value = ~value # Flip sign bit when subtracting
            # 0x9F: SBC A,A
            if opcode == 0x9F and old_a & 0x0F == 0x0F:
                f |= old_c << 4 # ...H....
            elif ((old_a & 0x0F) - (addend & 0x0F)) & 0x10:
                f |= 0x10       # ...H....
            f |= 0x02 # ......N. set for SBC/SUB, reset otherwise
        if ((old_a ^ s_value) ^ 0x80) & 0x80 and (a ^ old_a) & 0x80:
            # Augend and addend signs are the same - overflow if their sign
            # differs from the sign of the result
            self.registers['F'] = f | 0x04 # .....P..
        else:
            self.registers['F'] = f
        self.registers['A'] = a

        return self.pc + size, timing

    def add16(self, timing, size, augend, reg, carry=0, mult=1):
        if reg == 'SP':
            addend_v = self.registers['SP']
        opcode = self.snapshot[self.pc]
        if opcode == 0xDD:
            augend_v = self.registers['IXl'] + 256 * self.registers['IXh']
            if reg == 'IX':
                addend_v = augend_v
            elif reg != 'SP':
                addend_v = self.registers[reg[1]] + 256 * self.registers[reg[0]]
        elif opcode == 0xFD:
            augend_v = self.registers['IYl'] + 256 * self.registers['IYh']
            if reg == 'IY':
                addend_v = augend_v
            elif reg != 'SP':
                addend_v = self.registers[reg[1]] + 256 * self.registers[reg[0]]
        else:
            augend_v = self.registers['L'] + 256 * self.registers['H']
            if reg != 'SP':
                addend_v = self.registers[reg[1]] + 256 * self.registers[reg[0]]

        s_addend = addend_v
        old_f = self.registers['F']
        addend_v += carry * (old_f & 0x01)

        if mult == 1:
            if carry:
                f = 0
            else:
                f = old_f & 0b11000100 # Keep SZ...P..
        else:
            f = 0b00000010 # ......N.
            s_addend = ~s_addend

        if ((augend_v & 0x0FFF) + mult * (addend_v & 0x0FFF)) & 0x1000:
            f |= 0b00010000 # ...H....

        value = augend_v + mult * addend_v
        if value < 0 or value > 0xFFFF:
            value &= 0xFFFF
            f |= 0b00000001 # .......C

        if carry:
            # ADC, SBC
            if value & 0x8000:
                f |= 0b10000000 # S.......
            if value == 0:
                f |= 0b01000000 # .Z......
            if ((augend_v ^ s_addend) ^ 0x8000) & 0x8000 and (value ^ augend_v) & 0x8000:
                # Augend and addend signs are the same - overflow if their sign
                # differs from the sign of the result
                f |= 0b00000100 # .....P..

        f |= (value >> 8) & 0x28 # ..5.3...
        self.registers['F'] = f

        if opcode == 0xDD:
            self.registers['IXl'] = value % 256
            self.registers['IXh'] = value // 256
        elif opcode == 0xFD:
            self.registers['IYl'] = value % 256
            self.registers['IYh'] = value // 256
        else:
            self.registers['L'] = value % 256
            self.registers['H'] = value // 256

        return self.pc + size, timing

    def and_n(self):
        self.registers['A'] &= self.snapshot[(self.pc + 1) & 0xFFFF]
        a = self.registers['A']
        if a == 0:
            self.registers['F'] = 0x54 # SZ5H3PNC
        else:
            self.registers['F'] = (a & 0xA8) | 0x10 | PARITY[a] # SZ5H3PNC
        return self.pc + 2, 7

    def and_r(self, r):
        self.registers['A'] &= self.registers[r]
        a = self.registers['A']
        if a == 0:
            self.registers['F'] = 0x54 # SZ5H3PNC
        else:
            self.registers['F'] = (a & 0xA8) | 0x10 | PARITY[a] # SZ5H3PNC
        return self.pc + 1, 4

    def anda(self, timing, size, reg=None):
        self.registers['A'] &= self.get_operand_value(size, reg)
        a = self.registers['A']
        if a == 0:
            self.registers['F'] = 0x54 # SZ5H3PNC
        else:
            self.registers['F'] = (a & 0xA8) | 0x10 | PARITY[a] # SZ5H3PNC
        return self.pc + size, timing

    def bit(self, timing, size, mask, reg):
        value = self.get_operand_value(size, reg)
        bitval = value & mask
        f = 0x10 | (self.registers['F'] & 0x01) # ...H..NC
        if mask == 128 and bitval:
            f |= 0x80 # S.......
        if bitval == 0:
            f |= 0x44 # .Z...P..
        if reg in ('Xd', 'Yd'):
            offset = self.snapshot[(self.pc + 2) & 0xFFFF]
            if self.snapshot[self.pc] == 0xDD:
                v = (self.registers['IXl'] + 256 * self.registers['IXh'] + offset) & 0xFFFF
            else:
                v = (self.registers['IYl'] + 256 * self.registers['IYh'] + offset) & 0xFFFF
            self.registers['F'] = f | (v >> 8) & 0x28 # ..5.3...
        else:
            self.registers['F'] = f | value & 0x28 # ..5.3...
        return self.pc + size, timing

    def block(self, btype, inc, repeat):
        hl = self.registers['L'] + 256 * self.registers['H']
        bc = self.registers['C'] + 256 * self.registers['B']
        b = self.registers['B']
        a = self.registers['A']
        tstates = 16
        addr = self.pc + 2
        bc_inc = -1

        if btype == 0:
            # LDI, LDD, LDIR, LDDR
            de = self.registers['E'] + 256 * self.registers['D']
            at_hl = self.peek(hl)
            self.poke(de, at_hl)
            de = (de + inc) & 0xFFFF
            self.registers['E'], self.registers['D'] = de % 256, de // 256
            if repeat and bc != 1:
                addr = self.pc
                tstates = 21
            n = self.registers['A'] + at_hl
            f = (self.registers['F'] & 0xC1) | (n & 0x08) # SZ.H3.NC
            if n & 0x02:
                f |= 0x20 # ..5.....
            if bc != 1:
                f |= 0x04 # .....P..
        elif btype == 1:
            # CPI, CPD, CPIR, CPDR
            value = self.peek(hl)
            result = (a - value) & 0xFF
            hf = ((a & 0x0F) - (value & 0x0F)) & 0x10
            n = a - value - hf // 16
            f = (result & 0x80) | hf | 0x02 | (self.registers['F'] & 0x01) # S..H..NC
            if result == 0:
                f |= 0x40 # .Z......
            if n & 0x02:
                f |= 0x20 # ..5.....
            if n & 0x08:
                f |= 0x08 # ....3...
            if bc != 1:
                f |= 0x04 # .....P..
            if repeat and a != value and bc > 1:
                addr = self.pc
                tstates = 21
        elif btype == 2:
            # INI, IND, INIR, INDR
            value = self._in(bc)
            self.poke(hl, value)
            bc_inc = -256
            if repeat and b != 1:
                addr = self.pc
                tstates = 21
            b1 = (b - 1) & 0xFF
            j = value + ((self.registers['C'] + inc) & 0xFF)
            f = (b1 & 0xA8) | PARITY[(j & 7) ^ b1] # S.5.3P..
            if b1 == 0:
                f |= 0x40 # .Z......
            if j > 255:
                f |= 0x11 # ...H...C
            if value & 0x80:
                f |= 0x02 # ......N.
        else:
            # OUTI, OUTD, OTIR, OTDR
            bc_inc = -256
            if repeat and b != 1:
                addr = self.pc
                tstates = 21
            outval = self.peek(hl)
            self._out((bc - 256) & 0xFFFF, outval)
            b1 = (b - 1) & 0xFF
            k = ((hl + inc) & 0xFF) + outval
            f = (b1 & 0xA8) | PARITY[(k & 7) ^ b1] # S.5.3P..
            if b1 == 0:
                f |= 0x40 # .Z......
            if k > 255:
                f |= 0x11 # ...H...C
            if outval & 0x80:
                f |= 0x02 # ......N.

        hl = (hl + inc) & 0xFFFF
        bc = (bc + bc_inc) & 0xFFFF
        self.registers['L'], self.registers['H'] = hl % 256, hl // 256
        self.registers['C'], self.registers['B'] = bc % 256, bc // 256
        self.registers['F'] = f

        return addr, tstates

    def call(self, c_and, c_xor):
        if c_and and self.registers['F'] & c_and ^ c_xor == 0:
            return self.pc + 3, 10
        ret_addr = (self.pc + 3) & 0xFFFF
        self._push(ret_addr % 256, ret_addr // 256)
        return self.snapshot[(self.pc + 1) & 0xFFFF] + 256 * self.snapshot[(self.pc + 2) & 0xFFFF], 17

    def cf(self):
        f = self.registers['F'] & 0xC4 # SZ...PN.
        if self.snapshot[self.pc] == 0x3F:
            # CCF
            if self.registers['F'] & 0x01:
                f |= 0x10 # ...H....
            else:
                f |= 0x01 # .......C
        else:
            f |= 0x01 # .......C
        self.registers['F'] = f | self.registers['A'] & 0x28 # ..5.3...
        return self.pc + 1, 4

    def cp(self, timing, size, reg=None):
        value = self.get_operand_value(size, reg)
        a = self.registers['A']
        result = (a - value) & 0xFF
        f = (result & 0x80) | (value & 0x28) | 0x02 # S.5.3.N.
        if result == 0:
            f |= 0x40 # .Z......
        if ((a & 0x0F) - (value & 0x0F)) & 0x10:
            f |= 0x10 # ...H....
        if ((a ^ ~value) ^ 0x80) & 0x80 and (result ^ a) & 0x80:
            # Operand signs are the same - overflow if their sign differs from
            # the sign of the result
            f |= 0x04 # .....P..
        if a < value:
            self.registers['F'] = f | 0x01 # .......C
        else:
            self.registers['F'] = f
        return self.pc + size, timing

    def cpl(self):
        a = self.registers['A'] ^ 255
        self.registers['A'] = a
        self.registers['F'] = (self.registers['F'] & 0xC5) | (a & 0x28) | 0x12
        return self.pc + 1, 4

    def daa(self):
        a = self.registers['A']
        old_f = self.registers['F']
        hf = old_f & 0x10
        nf = old_f & 0x02
        t = 0
        f = nf

        if hf or a & 15 > 0x09:
            t += 1
        if old_f & 0x01 or a > 0x99:
            t += 2
            f |= 0x01 # .......C

        if (nf and hf and a & 0x0F < 6) or (nf == 0 and a & 0x0F >= 0x0A):
            f |= 0x10 # ...H....

        if t == 1:
            if nf:
                a += 0xFA
            else:
                a += 0x06
        elif t == 2:
            if nf:
                a += 0xA0
            else:
                a += 0x60
        elif t == 3:
            if nf:
                a += 0x9A
            else:
                a += 0x66

        a &= 0xFF
        self.registers['A'] = a
        f |= (a & 0xA8) | PARITY[a] # S.5.3P..
        if a == 0:
            self.registers['F'] = f | 0x40 # .Z......
        else:
            self.registers['F'] = f

        return self.pc + 1, 4

    def dec_r(self, reg):
        o_value = self.registers[reg]
        value = (o_value - 1) & 0xFF
        f = (self.registers['F'] & 0x01) | (value & 0xA8) # S.5.3..C
        if o_value & 0x0F == 0x00:
            f |= 0x10 # ...H....
        if o_value == 0x80:
            f |= 0x04 # .....P..
        f |= 0x02 # ......N.
        if value == 0:
            self.registers['F'] = f | 0x40 # .Z......
        else:
            self.registers['F'] = f
        self.registers[reg] = value
        return self.pc + 1, 4

    def defb(self, timing, size):
        return self.pc + size, timing

    def di_ei(self, iff2):
        self.iff2 = iff2
        return self.pc + 1, 4

    def djnz(self):
        b = (self.registers['B'] - 1) & 0xFF
        self.registers['B'] = b
        if b:
            offset = self.snapshot[(self.pc + 1) & 0xFFFF]
            if offset & 128:
                return (self.pc - 254 + offset) & 0xFFFF, 13
            return (self.pc + 2 + offset) & 0xFFFF, 13
        return self.pc + 2, 8

    def djnz_fast(self):
        if self.snapshot[(self.pc + 1) & 0xFFFF] == 0xFE:
            b = (self.registers['B'] - 1) & 0xFF
            self.registers['B'] = 0
            r = self.registers['R']
            self.registers['R'] = (r & 0x80) + ((r + b) & 0x7F)
            return self.pc + 2, b * 13 + 8
        return self.djnz()

    def ex_af(self):
        for r in 'AF':
            self.registers[r], self.registers['^' + r] = self.registers['^' + r], self.registers[r]
        return self.pc + 1, 4

    def ex_de_hl(self):
        for r1, r2 in (('D', 'H'), ('E', 'L')):
            self.registers[r1], self.registers[r2] = self.registers[r2], self.registers[r1]
        return self.pc + 1, 4

    def ex_sp(self, reg):
        sp = self.registers['SP']
        sp1, sp2 = self.peek(sp, 2)
        if reg == 'HL':
            self.poke(sp, self.registers['L'], self.registers['H'])
            self.registers['L'] = sp1
            self.registers['H'] = sp2
            return self.pc + 1, 19
        r1, r2 = reg + 'l', reg + 'h'
        self.poke(sp, self.registers[r1], self.registers[r2])
        self.registers[r1] = sp1
        self.registers[r2] = sp2
        return self.pc + 2, 23

    def exx(self):
        for r in 'BCDEHL':
            self.registers[r], self.registers['^' + r] = self.registers['^' + r], self.registers[r]
        return self.pc + 1, 4

    def halt(self):
        if self.iff2:
            t = self.tstates
            if (t + 4) % FRAME_DURATION < t % FRAME_DURATION:
                return self.pc + 1, 4
        return self.pc, 4

    def im(self, mode):
        self.imode = mode
        return self.pc + 2, 8

    def _in(self, port):
        if self.in_tracer:
            reading = self.in_tracer(port)
        else:
            reading = None
        if reading is None:
            return 191
        return reading

    def in_a(self):
        operand = self.snapshot[(self.pc + 1) & 0xFFFF]
        self.registers['A'] = self._in(operand + 256 * self.registers['A'])
        return self.pc + 2, 11

    def in_c(self, reg):
        value = self._in(self.registers['C'] + 256 * self.registers['B'])
        if reg != 'F':
            self.registers[reg] = value
        f = (value & 0xA8) | PARITY[value] | (self.registers['F'] & 0x01) # S.5H3PNC
        if value == 0:
            self.registers['F'] = f | 0x40 # .Z......
        else:
            self.registers['F'] = f
        return self.pc + 2, 12

    def inc_r(self, reg):
        o_value = self.registers[reg]
        value = (o_value + 1) & 0xFF
        f = (self.registers['F'] & 0x01) | (value & 0xA8) # S.5.3..C
        if o_value & 0x0F == 0x0F:
            f |= 0x10 # ...H....
        if o_value == 0x7F:
            f |= 0x04 # .....P..
        if value == 0:
            self.registers['F'] = f | 0x40 # .Z......
        else:
            self.registers['F'] = f
        self.registers[reg] = value
        return self.pc + 1, 4

    def inc_dec8(self, timing, size, inc, reg):
        o_value = self.get_operand_value(size, reg)
        if inc < 0:
            value = (o_value - 1) & 255
            f = (self.registers['F'] & 0x01) | (value & 0xA8) # S.5.3..C
            if o_value & 0x0F == 0x00:
                f |= 0x10 # ...H....
            if o_value == 0x80:
                f |= 0x04 # .....P..
            f |= 0x02 # ......N.
        else:
            value = (o_value + 1) & 255
            f = (self.registers['F'] & 0x01) | (value & 0xA8) # S.5.3.NC
            if o_value & 0x0F == 0x0F:
                f |= 0x10 # ...H....
            if o_value == 0x7F:
                f |= 0x04 # .....P..
        if value == 0:
            self.registers['F'] = f | 0x40 # .Z......
        else:
            self.registers['F'] = f
        self.set_operand_value(reg, value)
        return self.pc + size, timing

    def inc_dec16(self, inc, reg):
        if reg == 'SP':
            self.registers[reg] = (self.registers[reg] + inc) & 0xFFFF
            return self.pc + 1, 6
        if reg in ('IX', 'IY'):
            value = (self.registers[reg + 'l'] + 256 * self.registers[reg + 'h'] + inc) & 0xFFFF
            self.registers[reg + 'h'] = value // 256
            self.registers[reg + 'l'] = value % 256
            return self.pc + 2, 10
        value = (self.registers[reg[1]] + 256 * self.registers[reg[0]] + inc) & 0xFFFF
        self.registers[reg[0]] = value // 256
        self.registers[reg[1]] = value % 256
        return self.pc + 1, 6

    def jr(self, c_and, c_xor):
        if c_and and self.registers['F'] & c_and ^ c_xor == 0:
            return self.pc + 2, 7
        offset = self.snapshot[(self.pc + 1) & 0xFFFF]
        if offset & 128:
            return (self.pc - 254 + offset) & 0xFFFF, 12
        return (self.pc + 2 + offset) & 0xFFFF, 12

    def jp(self, c_and, c_xor):
        if c_and and self.registers['F'] & c_and ^ c_xor == 0:
            return self.pc + 3, 10

        opcode = self.snapshot[self.pc]
        if opcode == 0xDD:
            return self.registers['IXl'] + 256 * self.registers['IXh'], 8
        if opcode == 0xFD:
            return self.registers['IYl'] + 256 * self.registers['IYh'], 8
        if opcode == 0xE9:
            return self.registers['L'] + 256 * self.registers['H'], 4

        return self.snapshot[(self.pc + 1) & 0xFFFF] + 256 * self.snapshot[(self.pc + 2) & 0xFFFF], 10

    def ld_r_n(self, r):
        self.registers[r] = self.snapshot[(self.pc + 1) & 0xFFFF]
        return self.pc + 2, 7

    def ld_r_r(self, r1, r2):
        self.registers[r1] = self.registers[r2]
        return self.pc + 1, 4

    def ld8(self, timing, size, reg, reg2=None):
        self.set_operand_value(reg, self.get_operand_value(size, reg2))
        if reg2 and reg2 in 'IR':
            a = self.registers['A']
            f = (a & 0xA8) | (self.registers['F'] & 0x01) # S.5H3.NC
            if a == 0:
                f |= 0x40 # .Z......
            if self.iff2:
                self.registers['F'] = f | 0x04 # .....P..
            else:
                self.registers['F'] = f
        return self.pc + size, timing

    def ld16(self, reg):
        if reg == 'SP':
            self.registers['SP'] = self.snapshot[(self.pc + 1) & 0xFFFF] + 256 * self.snapshot[(self.pc + 2) & 0xFFFF]
            return self.pc + 3, 10
        if reg in ('IX', 'IY'):
            self.registers[reg + 'l'] = self.snapshot[(self.pc + 2) & 0xFFFF]
            self.registers[reg + 'h'] = self.snapshot[(self.pc + 3) & 0xFFFF]
            return self.pc + 4, 14
        self.registers[reg[1]] = self.snapshot[(self.pc + 1) & 0xFFFF]
        self.registers[reg[0]] = self.snapshot[(self.pc + 2) & 0xFFFF]
        return self.pc + 3, 10

    def ld16addr(self, timing, size, reg, poke):
        end = self.pc + size
        addr = self.snapshot[(end - 2) & 0xFFFF] + 256 * self.snapshot[(end - 1) & 0xFFFF]
        if poke:
            if reg == 'SP':
                self.poke(addr, self.registers['SP'] % 256, self.registers['SP'] // 256)
            elif reg in ('IX', 'IY'):
                self.poke(addr, self.registers[reg + 'l'], self.registers[reg + 'h'])
            else:
                self.poke(addr, self.registers[reg[1]], self.registers[reg[0]])
        else:
            if reg == 'SP':
                sp1, sp2 = self.peek(addr, 2)
                self.registers['SP'] = sp1 + 256 * sp2
            elif reg in ('IX', 'IY'):
                self.registers[reg + 'l'], self.registers[reg + 'h'] = self.peek(addr, 2)
            else:
                self.registers[reg[1]], self.registers[reg[0]] = self.peek(addr, 2)
        return end, timing

    def ldann(self):
        addr = self.snapshot[(self.pc + 1) & 0xFFFF] + 256 * self.snapshot[(self.pc + 2) & 0xFFFF]
        if self.snapshot[self.pc] == 0x3A:
            self.registers['A'] = self.peek(addr)
        else:
            self.poke(addr, self.registers['A'])
        return self.pc + 3, 13

    def ldir_fast(self, inc):
        de = self.registers['E'] + 256 * self.registers['D']
        bc = self.registers['C'] + 256 * self.registers['B']
        hl = self.registers['L'] + 256 * self.registers['H']
        count = 0
        repeat = True
        while repeat:
            self.poke(de, self.peek(hl))
            bc = (bc - 1) & 0xFFFF
            if bc == 0 or self.pc <= de <= self.pc + 1:
                repeat = False
            de = (de + inc) & 0xFFFF
            hl = (hl + inc) & 0xFFFF
            count += 1
        self.registers['C'], self.registers['B'] = bc % 256, bc // 256
        self.registers['E'], self.registers['D'] = de % 256, de // 256
        self.registers['L'], self.registers['H'] = hl % 256, hl // 256
        r = self.registers['R']
        self.registers['R'] = (r & 0x80) + ((r + 2 * (count - 1)) & 0x7F)
        n = self.registers['A'] + self.snapshot[(hl - inc) & 0xFFFF]
        f = (self.registers['F'] & 0xC1) | (n & 0x08) # SZ.H3.NC
        if bc:
            f |= 0x04 # .....P..
            pc = self.pc
        else:
            pc = self.pc + 2
        if n & 0x02:
            self.registers['F'] = f | 0x20 # ..5.....
        else:
            self.registers['F'] = f
        return pc, 21 * count - 5

    def ldsprr(self, reg):
        if reg == 'HL':
            self.registers['SP'] = self.registers['L'] + 256 * self.registers['H']
            return self.pc + 1, 6
        self.registers['SP'] = self.registers[reg + 'l'] + 256 * self.registers[reg + 'h']
        return self.pc + 2, 10

    def neg(self):
        old_a = self.registers['A']
        a = self.registers['A'] = (256 - old_a) & 255
        f = (a & 0xA8) | 0x02 # S.5.3.N.
        if a == 0:
            f |= 0x40 # .Z......
        if old_a & 0x0F:
            f |= 0x10 # ...H....
        if a == 0x80:
            f |= 0x04 # .....P..
        if a > 0:
            self.registers['F'] = f | 0x01 # .......C
        else:
            self.registers['F'] = f
        return self.pc + 2, 8

    def nop(self):
        return self.pc + 1, 4

    def or_n(self):
        self.registers['A'] |= self.snapshot[(self.pc + 1) & 0xFFFF]
        a = self.registers['A']
        if a == 0:
            self.registers['F'] = 0x44 # SZ5H3PNC
        else:
            self.registers['F'] = (a & 0xA8) | PARITY[a] # SZ5H3PNC
        return self.pc + 2, 7

    def or_r(self, r):
        self.registers['A'] |= self.registers[r]
        a = self.registers['A']
        if a == 0:
            self.registers['F'] = 0x44 # SZ5H3PNC
        else:
            self.registers['F'] = (a & 0xA8) | PARITY[a] # SZ5H3PNC
        return self.pc + 1, 4

    def ora(self, timing, size, reg=None):
        self.registers['A'] |= self.get_operand_value(size, reg)
        a = self.registers['A']
        if a == 0:
            self.registers['F'] = 0x44 # SZ5H3PNC
        else:
            self.registers['F'] = (a & 0xA8) | PARITY[a] # SZ5H3PNC
        return self.pc + size, timing

    def _out(self, port, value):
        if self.out_tracer:
            self.out_tracer(port, value)

    def outa(self):
        a = self.registers['A']
        self._out(self.snapshot[(self.pc + 1) & 0xFFFF] + 256 * a, a)
        return self.pc + 2, 11

    def outc(self, reg):
        port = self.registers['C'] + 256 * self.registers['B']
        if reg:
            self._out(port, self.registers[reg])
        else:
            self._out(port, 0)
        return self.pc + 2, 12

    def _pop(self):
        sp = self.registers['SP']
        lsb, msb = self.peek(sp, 2)
        self.registers['SP'] = (sp + 2) & 0xFFFF
        self.ppcount -= 1
        return lsb, msb

    def pop(self, reg):
        if reg in ('IX', 'IY'):
            self.registers[reg + 'l'], self.registers[reg + 'h'] = self._pop()
            return self.pc + 2, 14
        self.registers[reg[1]], self.registers[reg[0]] = self._pop()
        return self.pc + 1, 10

    def _push(self, lsb, msb):
        sp = (self.registers['SP'] - 2) & 0xFFFF
        self.poke(sp, lsb, msb)
        self.ppcount += 1
        self.registers['SP'] = sp

    def push(self, reg):
        if reg in ('IX', 'IY'):
            self._push(self.registers[reg + 'l'], self.registers[reg + 'h'])
            return self.pc + 2, 15
        self._push(self.registers[reg[1]], self.registers[reg[0]])
        return self.pc + 1, 11

    def ret(self, c_and, c_xor):
        if c_and:
            if self.registers['F'] & c_and ^ c_xor:
                lsb, msb = self._pop()
                return lsb + 256 * msb, 11
            return self.pc + 1, 5
        lsb, msb = self._pop()
        return lsb + 256 * msb, 10

    def reti(self):
        lsb, msb = self._pop()
        return lsb + 256 * msb, 14

    def res_set(self, timing, size, bit, reg, bitval, dest=''):
        if bitval:
            value = self.get_operand_value(size, reg) | bit
        else:
            value = self.get_operand_value(size, reg) & bit
        self.set_operand_value(reg, value)
        if dest:
            self.registers[dest] = value
        return self.pc + size, timing

    def rld(self):
        hl = self.registers['L'] + 256 * self.registers['H']
        a = self.registers['A']
        at_hl = self.peek(hl)
        self.poke(hl, ((at_hl << 4) & 240) + (a & 15))
        a_out = self.registers['A'] = (a & 240) + ((at_hl >> 4) & 15)
        f = (a_out & 0xA8) | PARITY[a_out] | (self.registers['F'] & 0x01) # S.5H3PNC
        if a_out == 0:
            self.registers['F'] = f | 0x40 # .Z......
        else:
            self.registers['F'] = f
        return self.pc + 2, 18

    def rrd(self):
        hl = self.registers['L'] + 256 * self.registers['H']
        a = self.registers['A']
        at_hl = self.peek(hl)
        self.poke(hl, ((a << 4) & 240) + (at_hl >> 4))
        a_out = self.registers['A'] = (a & 240) + (at_hl & 15)
        f = (a_out & 0xA8) | PARITY[a_out] | (self.registers['F'] & 0x01) # S.5H3PNC
        if a_out == 0:
            self.registers['F'] = f | 0x40 # .Z......
        else:
            self.registers['F'] = f
        return self.pc + 2, 18

    def rotate_a(self, cbit, carry=0):
        a = self.registers['A']
        old_f = self.registers['F']
        if carry:
            if cbit == 1:
                # RRCA
                value = ((a << 7) & 0x80) | ((a >> 1) & 0x7F)
            else:
                # RLCA
                value = (a >> 7) | ((a << 1) & 0xFE)
        elif cbit == 1:
            # RRA
            value = (old_f << 7) | (a >> 1)
        else:
            # RLA
            value = (old_f & 0x01) | (a << 1)
        self.registers['A'] = value & 0xFF
        f = (old_f & 0xC4) | (value & 0x28) # SZ5H3PN.
        if a & cbit:
            self.registers['F'] = f | 0x01 # .......C
        else:
            self.registers['F'] = f
        return self.pc + 1, 4

    def rotate_r(self, cbit, reg, carry=0):
        r = self.registers[reg]
        if carry:
            if cbit == 1:
                # RRC r
                value = ((r << 7) & 0x80) | ((r >> 1) & 0x7F)
            else:
                # RLC r
                value = (r >> 7) | ((r << 1) & 0xFE)
        elif cbit == 1:
            # RR r
            value = ((self.registers['F'] << 7) | (r >> 1)) & 0xFF
        else:
            # RL r
            value = ((self.registers['F'] & 0x01) | (r << 1)) & 0xFF
        self.registers[reg] = value
        f = (value & 0xA8) | PARITY[value] # S.5H3PN.
        if value == 0:
            f |= 0x40 # .Z......
        if r & cbit:
            self.registers['F'] = f | 0x01 # .......C
        else:
            self.registers['F'] = f
        return self.pc + 2, 8

    def rotate(self, timing, size, cbit, reg, carry=0, dest=''):
        value = self.get_operand_value(size, reg)
        old_carry = self.registers['F'] & 0x01
        new_carry = value & cbit
        if cbit == 1:
            cvalue = (value << 7) & 128
            value >>= 1
            old_carry *= 128
        else:
            cvalue = value >> 7
            value <<= 1
        if carry:
            value += cvalue
        else:
            value += old_carry
        value &= 255
        self.set_operand_value(reg, value)
        if dest:
            self.registers[dest] = value
        f = (value & 0xA8) | PARITY[value] # S.5H3PN.
        if value == 0:
            f |= 0x40 # .Z......
        if new_carry:
            self.registers['F'] = f | 0x01 # .......C
        else:
            self.registers['F'] = f
        return self.pc + size, timing

    def rst(self, addr):
        ret_addr = (self.pc + 1) & 0xFFFF
        self._push(ret_addr % 256, ret_addr // 256)
        return addr, 11

    def shift(self, timing, size, stype, cbit, reg, dest=''):
        value = self.get_operand_value(size, reg)
        ovalue = value
        if value & cbit:
            f = 0x01 # .......C
        else:
            f = 0x00 # .......C
        if cbit == 1:
            value >>= 1
        else:
            value <<= 1
        if stype == 1:
            # SRA
            value += ovalue & 128
        elif stype == 2:
            # SLL
            value |= 1
        value &= 255
        self.set_operand_value(reg, value)
        if dest:
            self.registers[dest] = value
        f |= (value & 0xA8) | PARITY[value] # S.5H3PN.
        if value == 0:
            self.registers['F'] = f | 0x40 # .Z......
        else:
            self.registers['F'] = f
        return self.pc + size, timing

    def xor_n(self):
        self.registers['A'] ^= self.snapshot[(self.pc + 1) & 0xFFFF]
        a = self.registers['A']
        if a == 0:
            self.registers['F'] = 0x44 # SZ5H3PNC
        else:
            self.registers['F'] = (a & 0xA8) | PARITY[a] # SZ5H3PNC
        return self.pc + 2, 7

    def xor_r(self, r):
        self.registers['A'] ^= self.registers[r]
        a = self.registers['A']
        if a == 0:
            self.registers['F'] = 0x44 # SZ5H3PNC
        else:
            self.registers['F'] = (a & 0xA8) | PARITY[a] # SZ5H3PNC
        return self.pc + 1, 4

    def xor(self, timing, size, reg=None):
        self.registers['A'] ^= self.get_operand_value(size, reg)
        a = self.registers['A']
        if a == 0:
            self.registers['F'] = 0x44 # SZ5H3PNC
        else:
            self.registers['F'] = (a & 0xA8) | PARITY[a] # SZ5H3PNC
        return self.pc + size, timing

    def create_opcodes(self):
        self.opcodes = [
            self.nop,                                        # 0x00 NOP
            partial(self.ld16, 'BC'),                        # 0x01 LD BC,nn
            partial(self.ld8, 7, 1, '(BC)', 'A'),            # 0x02 LD (BC),A
            partial(self.inc_dec16, 1, 'BC'),                # 0x03 INC BC
            partial(self.inc_r, 'B'),                        # 0x04 INC B
            partial(self.dec_r, 'B'),                        # 0x05 DEC B
            partial(self.ld_r_n, 'B'),                       # 0x06 LD B,n
            partial(self.rotate_a, 128, 1),                  # 0x07 RLCA
            self.ex_af,                                      # 0x08 EX AF,AF'
            partial(self.add16, 11, 1, 'HL', 'BC'),          # 0x09 ADD HL,BC
            partial(self.ld8, 7, 1, 'A', '(BC)'),            # 0x0A LD A,(BC)
            partial(self.inc_dec16, -1, 'BC'),               # 0x0B DEC BC
            partial(self.inc_r, 'C'),                        # 0x0C INC C
            partial(self.dec_r, 'C'),                        # 0x0D DEC C
            partial(self.ld_r_n, 'C'),                       # 0x0E LD C,n
            partial(self.rotate_a, 1, 1),                    # 0x0F RRCA
            self.djnz,                                       # 0x10 DJNZ nn
            partial(self.ld16, 'DE'),                        # 0x11 LD DE,nn
            partial(self.ld8, 7, 1, '(DE)', 'A'),            # 0x12 LD (DE),A
            partial(self.inc_dec16, 1, 'DE'),                # 0x13 INC DE
            partial(self.inc_r, 'D'),                        # 0x14 INC D
            partial(self.dec_r, 'D'),                        # 0x15 DEC D
            partial(self.ld_r_n, 'D'),                       # 0x16 LD D,n
            partial(self.rotate_a, 128),                     # 0x17 RLA
            partial(self.jr, 0, 0),                          # 0x18 JR nn
            partial(self.add16, 11, 1, 'HL', 'DE'),          # 0x19 ADD HL,DE
            partial(self.ld8, 7, 1, 'A', '(DE)'),            # 0x1A LD A,(DE)
            partial(self.inc_dec16, -1, 'DE'),               # 0x1B DEC DE
            partial(self.inc_r, 'E'),                        # 0x1C INC E
            partial(self.dec_r, 'E'),                        # 0x1D DEC E
            partial(self.ld_r_n, 'E'),                       # 0x1E LD E,n
            partial(self.rotate_a, 1),                       # 0x1F RRA
            partial(self.jr, 64, 64),                        # 0x20 JR NZ,nn
            partial(self.ld16, 'HL'),                        # 0x21 LD HL,nn
            partial(self.ld16addr, 16, 3, 'HL', 1),          # 0x22 LD (nn),HL
            partial(self.inc_dec16, 1, 'HL'),                # 0x23 INC HL
            partial(self.inc_r, 'H'),                        # 0x24 INC H
            partial(self.dec_r, 'H'),                        # 0x25 DEC H
            partial(self.ld_r_n, 'H'),                       # 0x26 LD H,n
            self.daa,                                        # 0x27 DAA
            partial(self.jr, 64, 0),                         # 0x28 JR Z,nn
            partial(self.add16, 11, 1, 'HL', 'HL'),          # 0x29 ADD HL,HL
            partial(self.ld16addr, 16, 3, 'HL', 0),          # 0x2A LD HL,(nn)
            partial(self.inc_dec16, -1, 'HL'),               # 0x2B DEC HL
            partial(self.inc_r, 'L'),                        # 0x2C INC L
            partial(self.dec_r, 'L'),                        # 0x2D DEC L
            partial(self.ld_r_n, 'L'),                       # 0x2E LD L,n
            self.cpl,                                        # 0x2F CPL
            partial(self.jr, 1, 1),                          # 0x30 JR NC,nn
            partial(self.ld16, 'SP'),                        # 0x31 LD SP,nn
            self.ldann,                                      # 0x32 LD (nn),A
            partial(self.inc_dec16, 1, 'SP'),                # 0x33 INC SP
            partial(self.inc_dec8, 11, 1, 1, '(HL)'),        # 0x34 INC (HL)
            partial(self.inc_dec8, 11, 1, -1, '(HL)'),       # 0x35 DEC (HL)
            partial(self.ld8, 10, 2, '(HL)'),                # 0x36 LD (HL),n
            self.cf,                                         # 0x37 SCF
            partial(self.jr, 1, 0),                          # 0x38 JR C,nn
            partial(self.add16, 11, 1, 'HL', 'SP'),          # 0x39 ADD HL,SP
            self.ldann,                                      # 0x3A LD A,(nn)
            partial(self.inc_dec16, -1, 'SP'),               # 0x3B DEC SP
            partial(self.inc_r, 'A'),                        # 0x3C INC A
            partial(self.dec_r, 'A'),                        # 0x3D DEC A
            partial(self.ld_r_n, 'A'),                       # 0x3E LD A,n
            self.cf,                                         # 0x3F CCF
            partial(self.ld_r_r, 'B', 'B'),                  # 0x40 LD B,B
            partial(self.ld_r_r, 'B', 'C'),                  # 0x41 LD B,C
            partial(self.ld_r_r, 'B', 'D'),                  # 0x42 LD B,D
            partial(self.ld_r_r, 'B', 'E'),                  # 0x43 LD B,E
            partial(self.ld_r_r, 'B', 'H'),                  # 0x44 LD B,H
            partial(self.ld_r_r, 'B', 'L'),                  # 0x45 LD B,L
            partial(self.ld8, 7, 1, 'B', '(HL)'),            # 0x46 LD B,(HL)
            partial(self.ld_r_r, 'B', 'A'),                  # 0x47 LD B,A
            partial(self.ld_r_r, 'C', 'B'),                  # 0x48 LD C,B
            partial(self.ld_r_r, 'C', 'C'),                  # 0x49 LD C,C
            partial(self.ld_r_r, 'C', 'D'),                  # 0x4A LD C,D
            partial(self.ld_r_r, 'C', 'E'),                  # 0x4B LD C,E
            partial(self.ld_r_r, 'C', 'H'),                  # 0x4C LD C,H
            partial(self.ld_r_r, 'C', 'L'),                  # 0x4D LD C,L
            partial(self.ld8, 7, 1, 'C', '(HL)'),            # 0x4E LD C,(HL)
            partial(self.ld_r_r, 'C', 'A'),                  # 0x4F LD C,A
            partial(self.ld_r_r, 'D', 'B'),                  # 0x50 LD D,B
            partial(self.ld_r_r, 'D', 'C'),                  # 0x51 LD D,C
            partial(self.ld_r_r, 'D', 'D'),                  # 0x52 LD D,D
            partial(self.ld_r_r, 'D', 'E'),                  # 0x53 LD D,E
            partial(self.ld_r_r, 'D', 'H'),                  # 0x54 LD D,H
            partial(self.ld_r_r, 'D', 'L'),                  # 0x55 LD D,L
            partial(self.ld8, 7, 1, 'D', '(HL)'),            # 0x56 LD D,(HL)
            partial(self.ld_r_r, 'D', 'A'),                  # 0x57 LD D,A
            partial(self.ld_r_r, 'E', 'B'),                  # 0x58 LD E,B
            partial(self.ld_r_r, 'E', 'C'),                  # 0x59 LD E,C
            partial(self.ld_r_r, 'E', 'D'),                  # 0x5A LD E,D
            partial(self.ld_r_r, 'E', 'E'),                  # 0x5B LD E,E
            partial(self.ld_r_r, 'E', 'H'),                  # 0x5C LD E,H
            partial(self.ld_r_r, 'E', 'L'),                  # 0x5D LD E,L
            partial(self.ld8, 7, 1, 'E', '(HL)'),            # 0x5E LD E,(HL)
            partial(self.ld_r_r, 'E', 'A'),                  # 0x5F LD E,A
            partial(self.ld_r_r, 'H', 'B'),                  # 0x60 LD H,B
            partial(self.ld_r_r, 'H', 'C'),                  # 0x61 LD H,C
            partial(self.ld_r_r, 'H', 'D'),                  # 0x62 LD H,D
            partial(self.ld_r_r, 'H', 'E'),                  # 0x63 LD H,E
            partial(self.ld_r_r, 'H', 'H'),                  # 0x64 LD H,H
            partial(self.ld_r_r, 'H', 'L'),                  # 0x65 LD H,L
            partial(self.ld8, 7, 1, 'H', '(HL)'),            # 0x66 LD H,(HL)
            partial(self.ld_r_r, 'H', 'A'),                  # 0x67 LD H,A
            partial(self.ld_r_r, 'L', 'B'),                  # 0x68 LD L,B
            partial(self.ld_r_r, 'L', 'C'),                  # 0x69 LD L,C
            partial(self.ld_r_r, 'L', 'D'),                  # 0x6A LD L,D
            partial(self.ld_r_r, 'L', 'E'),                  # 0x6B LD L,E
            partial(self.ld_r_r, 'L', 'H'),                  # 0x6C LD L,H
            partial(self.ld_r_r, 'L', 'L'),                  # 0x6D LD L,L
            partial(self.ld8, 7, 1, 'L', '(HL)'),            # 0x6E LD L,(HL)
            partial(self.ld_r_r, 'L', 'A'),                  # 0x6F LD L,A
            partial(self.ld8, 7, 1, '(HL)', 'B'),            # 0x70 LD (HL),B
            partial(self.ld8, 7, 1, '(HL)', 'C'),            # 0x71 LD (HL),C
            partial(self.ld8, 7, 1, '(HL)', 'D'),            # 0x72 LD (HL),D
            partial(self.ld8, 7, 1, '(HL)', 'E'),            # 0x73 LD (HL),E
            partial(self.ld8, 7, 1, '(HL)', 'H'),            # 0x74 LD (HL),H
            partial(self.ld8, 7, 1, '(HL)', 'L'),            # 0x75 LD (HL),L
            self.halt,                                       # 0x76 HALT
            partial(self.ld8, 7, 1, '(HL)', 'A'),            # 0x77 LD (HL),A
            partial(self.ld_r_r, 'A', 'B'),                  # 0x78 LD A,B
            partial(self.ld_r_r, 'A', 'C'),                  # 0x79 LD A,C
            partial(self.ld_r_r, 'A', 'D'),                  # 0x7A LD A,D
            partial(self.ld_r_r, 'A', 'E'),                  # 0x7B LD A,E
            partial(self.ld_r_r, 'A', 'H'),                  # 0x7C LD A,H
            partial(self.ld_r_r, 'A', 'L'),                  # 0x7D LD A,L
            partial(self.ld8, 7, 1, 'A', '(HL)'),            # 0x7E LD A,(HL)
            partial(self.ld_r_r, 'A', 'A'),                  # 0x7F LD A,A
            partial(self.add_a, 4, 1, 'B'),                  # 0x80 ADD A,B
            partial(self.add_a, 4, 1, 'C'),                  # 0x81 ADD A,C
            partial(self.add_a, 4, 1, 'D'),                  # 0x82 ADD A,D
            partial(self.add_a, 4, 1, 'E'),                  # 0x83 ADD A,E
            partial(self.add_a, 4, 1, 'H'),                  # 0x84 ADD A,H
            partial(self.add_a, 4, 1, 'L'),                  # 0x85 ADD A,L
            partial(self.add_a, 7, 1, '(HL)'),               # 0x86 ADD A,(HL)
            partial(self.add_a, 4, 1, 'A'),                  # 0x87 ADD A,A
            partial(self.add_a, 4, 1, 'B', 1),               # 0x88 ADC A,B
            partial(self.add_a, 4, 1, 'C', 1),               # 0x89 ADC A,C
            partial(self.add_a, 4, 1, 'D', 1),               # 0x8A ADC A,D
            partial(self.add_a, 4, 1, 'E', 1),               # 0x8B ADC A,E
            partial(self.add_a, 4, 1, 'H', 1),               # 0x8C ADC A,H
            partial(self.add_a, 4, 1, 'L', 1),               # 0x8D ADC A,L
            partial(self.add_a, 7, 1, '(HL)', 1),            # 0x8E ADC A,(HL)
            partial(self.add_a, 4, 1, 'A', 1),               # 0x8F ADC A,A
            partial(self.add_a, 4, 1, 'B', 0, -1),           # 0x90 SUB B
            partial(self.add_a, 4, 1, 'C', 0, -1),           # 0x91 SUB C
            partial(self.add_a, 4, 1, 'D', 0, -1),           # 0x92 SUB D
            partial(self.add_a, 4, 1, 'E', 0, -1),           # 0x93 SUB E
            partial(self.add_a, 4, 1, 'H', 0, -1),           # 0x94 SUB H
            partial(self.add_a, 4, 1, 'L', 0, -1),           # 0x95 SUB L
            partial(self.add_a, 7, 1, '(HL)', 0, -1),        # 0x96 SUB (HL)
            partial(self.add_a, 4, 1, 'A', 0, -1),           # 0x97 SUB A
            partial(self.add_a, 4, 1, 'B', 1, -1),           # 0x98 SBC A,B
            partial(self.add_a, 4, 1, 'C', 1, -1),           # 0x99 SBC A,C
            partial(self.add_a, 4, 1, 'D', 1, -1),           # 0x9A SBC A,D
            partial(self.add_a, 4, 1, 'E', 1, -1),           # 0x9B SBC A,E
            partial(self.add_a, 4, 1, 'H', 1, -1),           # 0x9C SBC A,H
            partial(self.add_a, 4, 1, 'L', 1, -1),           # 0x9D SBC A,L
            partial(self.add_a, 7, 1, '(HL)', 1, -1),        # 0x9E SBC A,(HL)
            partial(self.add_a, 4, 1, 'A', 1, -1),           # 0x9F SBC A,A
            partial(self.and_r, 'B'),                        # 0xA0 AND B
            partial(self.and_r, 'C'),                        # 0xA1 AND C
            partial(self.and_r, 'D'),                        # 0xA2 AND D
            partial(self.and_r, 'E'),                        # 0xA3 AND E
            partial(self.and_r, 'H'),                        # 0xA4 AND H
            partial(self.and_r, 'L'),                        # 0xA5 AND L
            partial(self.anda, 7, 1, '(HL)'),                # 0xA6 AND (HL)
            partial(self.and_r, 'A'),                        # 0xA7 AND A
            partial(self.xor_r, 'B'),                        # 0xA8 XOR B
            partial(self.xor_r, 'C'),                        # 0xA9 XOR C
            partial(self.xor_r, 'D'),                        # 0xAA XOR D
            partial(self.xor_r, 'E'),                        # 0xAB XOR E
            partial(self.xor_r, 'H'),                        # 0xAC XOR H
            partial(self.xor_r, 'L'),                        # 0xAD XOR L
            partial(self.xor, 7, 1, '(HL)'),                 # 0xAE XOR (HL)
            partial(self.xor_r, 'A'),                        # 0xAF XOR A
            partial(self.or_r, 'B'),                         # 0xB0 OR B
            partial(self.or_r, 'C'),                         # 0xB1 OR C
            partial(self.or_r, 'D'),                         # 0xB2 OR D
            partial(self.or_r, 'E'),                         # 0xB3 OR E
            partial(self.or_r, 'H'),                         # 0xB4 OR H
            partial(self.or_r, 'L'),                         # 0xB5 OR L
            partial(self.ora, 7, 1, '(HL)'),                 # 0xB6 OR (HL)
            partial(self.or_r, 'A'),                         # 0xB7 OR A
            partial(self.cp, 4, 1, 'B'),                     # 0xB8 CP B
            partial(self.cp, 4, 1, 'C'),                     # 0xB9 CP C
            partial(self.cp, 4, 1, 'D'),                     # 0xBA CP D
            partial(self.cp, 4, 1, 'E'),                     # 0xBB CP E
            partial(self.cp, 4, 1, 'H'),                     # 0xBC CP H
            partial(self.cp, 4, 1, 'L'),                     # 0xBD CP L
            partial(self.cp, 7, 1, '(HL)'),                  # 0xBE CP (HL)
            partial(self.cp, 4, 1, 'A'),                     # 0xBF CP A
            partial(self.ret, 64, 64),                       # 0xC0 RET NZ
            partial(self.pop, 'BC'),                         # 0xC1 POP BC
            partial(self.jp, 64, 64),                        # 0xC2 JP NZ,nn
            partial(self.jp, 0, 0),                          # 0xC3 JP nn
            partial(self.call, 64, 64),                      # 0xC4 CALL NZ,nn
            partial(self.push, 'BC'),                        # 0xC5 PUSH BC
            partial(self.add_a, 7, 2),                       # 0xC6 ADD A,n
            partial(self.rst, 0),                            # 0xC7 RST $00
            partial(self.ret, 64, 0),                        # 0xC8 RET Z
            partial(self.ret, 0, 0),                         # 0xC9 RET
            partial(self.jp, 64, 0),                         # 0xCA JP Z,nn
            None,                                            # 0xCB CB prefix
            partial(self.call, 64, 0),                       # 0xCC CALL Z,nn
            partial(self.call, 0, 0),                        # 0xCD CALL nn
            partial(self.add_a, 7, 2, None, 1, 1),           # 0xCE ADC A,n
            partial(self.rst, 8),                            # 0xCF RST $08
            partial(self.ret, 1, 1),                         # 0xD0 RET NC
            partial(self.pop, 'DE'),                         # 0xD1 POP DE
            partial(self.jp, 1, 1),                          # 0xD2 JP NC,nn
            self.outa,                                       # 0xD3 OUT (n),A
            partial(self.call, 1, 1),                        # 0xD4 CALL NC,nn
            partial(self.push, 'DE'),                        # 0xD5 PUSH DE
            partial(self.add_a, 7, 2, None, 0, -1),          # 0xD6 SUB n
            partial(self.rst, 16),                           # 0xD7 RST $10
            partial(self.ret, 1, 0),                         # 0xD8 RET C
            self.exx,                                        # 0xD9 EXX
            partial(self.jp, 1, 0),                          # 0xDA JP C,nn
            self.in_a,                                       # 0xDB IN A,(n)
            partial(self.call, 1, 0),                        # 0xDC CALL C,nn
            None,                                            # 0xDD DD prefix
            partial(self.add_a, 7, 2, None, 1, -1),          # 0xDE SBC A,n
            partial(self.rst, 24),                           # 0xDF RST $18
            partial(self.ret, 4, 4),                         # 0xE0 RET PO
            partial(self.pop, 'HL'),                         # 0xE1 POP HL
            partial(self.jp, 4, 4),                          # 0xE2 JP PO,nn
            partial(self.ex_sp, 'HL'),                       # 0xE3 EX (SP),HL
            partial(self.call, 4, 4),                        # 0xE4 CALL PO,nn
            partial(self.push, 'HL'),                        # 0xE5 PUSH HL
            self.and_n,                                      # 0xE6 AND n
            partial(self.rst, 32),                           # 0xE7 RST $20
            partial(self.ret, 4, 0),                         # 0xE8 RET PE
            partial(self.jp, 0, 0),                          # 0xE9 JP (HL)
            partial(self.jp, 4, 0),                          # 0xEA JP PE,nn
            self.ex_de_hl,                                   # 0xEB EX DE,HL
            partial(self.call, 4, 0),                        # 0xEC CALL PE,nn
            None,                                            # 0xED ED prefix
            self.xor_n,                                      # 0xEE XOR n
            partial(self.rst, 40),                           # 0xEF RST $28
            partial(self.ret, 128, 128),                     # 0xF0 RET P
            partial(self.pop, 'AF'),                         # 0xF1 POP AF
            partial(self.jp, 128, 128),                      # 0xF2 JP P,nn
            partial(self.di_ei, 0),                          # 0xF3 DI
            partial(self.call, 128, 128),                    # 0xF4 CALL P,nn
            partial(self.push, 'AF'),                        # 0xF5 PUSH AF
            self.or_n,                                       # 0xF6 OR n
            partial(self.rst, 48),                           # 0xF7 RST $30
            partial(self.ret, 128, 0),                       # 0xF8 RET M
            partial(self.ldsprr, 'HL'),                      # 0xF9 LD SP,HL
            partial(self.jp, 128, 0),                        # 0xFA JP M,nn
            partial(self.di_ei, 1),                          # 0xFB EI
            partial(self.call, 128, 0),                      # 0xFC CALL M,nn
            None,                                            # 0xFD FD prefix
            partial(self.cp, 7, 2),                          # 0xFE CP n
            partial(self.rst, 56),                           # 0xFF RST $38
        ]

        self.after_CB = [
            partial(self.rotate_r, 128, 'B', 1),             # 0x00 RLC B
            partial(self.rotate_r, 128, 'C', 1),             # 0x01 RLC C
            partial(self.rotate_r, 128, 'D', 1),             # 0x02 RLC D
            partial(self.rotate_r, 128, 'E', 1),             # 0x03 RLC E
            partial(self.rotate_r, 128, 'H', 1),             # 0x04 RLC H
            partial(self.rotate_r, 128, 'L', 1),             # 0x05 RLC L
            partial(self.rotate, 15, 2, 128, '(HL)', 1),     # 0x06 RLC (HL)
            partial(self.rotate_r, 128, 'A', 1),             # 0x07 RLC A
            partial(self.rotate_r, 1, 'B', 1),               # 0x08 RRC B
            partial(self.rotate_r, 1, 'C', 1),               # 0x09 RRC C
            partial(self.rotate_r, 1, 'D', 1),               # 0x0A RRC D
            partial(self.rotate_r, 1, 'E', 1),               # 0x0B RRC E
            partial(self.rotate_r, 1, 'H', 1),               # 0x0C RRC H
            partial(self.rotate_r, 1, 'L', 1),               # 0x0D RRC L
            partial(self.rotate, 15, 2, 1, '(HL)', 1),       # 0x0E RRC (HL)
            partial(self.rotate_r, 1, 'A', 1),               # 0x0F RRC A
            partial(self.rotate_r, 128, 'B'),                # 0x10 RL B
            partial(self.rotate_r, 128, 'C'),                # 0x11 RL C
            partial(self.rotate_r, 128, 'D'),                # 0x12 RL D
            partial(self.rotate_r, 128, 'E'),                # 0x13 RL E
            partial(self.rotate_r, 128, 'H'),                # 0x14 RL H
            partial(self.rotate_r, 128, 'L'),                # 0x15 RL L
            partial(self.rotate, 15, 2, 128, '(HL)'),        # 0x16 RL (HL)
            partial(self.rotate_r, 128, 'A'),                # 0x17 RL A
            partial(self.rotate_r, 1, 'B'),                  # 0x18 RR B
            partial(self.rotate_r, 1, 'C'),                  # 0x19 RR C
            partial(self.rotate_r, 1, 'D'),                  # 0x1A RR D
            partial(self.rotate_r, 1, 'E'),                  # 0x1B RR E
            partial(self.rotate_r, 1, 'H'),                  # 0x1C RR H
            partial(self.rotate_r, 1, 'L'),                  # 0x1D RR L
            partial(self.rotate, 15, 2, 1, '(HL)'),          # 0x1E RR (HL)
            partial(self.rotate_r, 1, 'A'),                  # 0x1F RR A
            partial(self.shift, 8, 2, 0, 128, 'B'),          # 0x20 SLA B
            partial(self.shift, 8, 2, 0, 128, 'C'),          # 0x21 SLA C
            partial(self.shift, 8, 2, 0, 128, 'D'),          # 0x22 SLA D
            partial(self.shift, 8, 2, 0, 128, 'E'),          # 0x23 SLA E
            partial(self.shift, 8, 2, 0, 128, 'H'),          # 0x24 SLA H
            partial(self.shift, 8, 2, 0, 128, 'L'),          # 0x25 SLA L
            partial(self.shift, 15, 2, 0, 128, '(HL)'),      # 0x26 SLA (HL)
            partial(self.shift, 8, 2, 0, 128, 'A'),          # 0x27 SLA A
            partial(self.shift, 8, 2, 1, 1, 'B'),            # 0x28 SRA B
            partial(self.shift, 8, 2, 1, 1, 'C'),            # 0x29 SRA C
            partial(self.shift, 8, 2, 1, 1, 'D'),            # 0x2A SRA D
            partial(self.shift, 8, 2, 1, 1, 'E'),            # 0x2B SRA E
            partial(self.shift, 8, 2, 1, 1, 'H'),            # 0x2C SRA H
            partial(self.shift, 8, 2, 1, 1, 'L'),            # 0x2D SRA L
            partial(self.shift, 15, 2, 1, 1, '(HL)'),        # 0x2E SRA (HL)
            partial(self.shift, 8, 2, 1, 1, 'A'),            # 0x2F SRA A
            partial(self.shift, 8, 2, 2, 128, 'B'),          # 0x30 SLL B
            partial(self.shift, 8, 2, 2, 128, 'C'),          # 0x31 SLL C
            partial(self.shift, 8, 2, 2, 128, 'D'),          # 0x32 SLL D
            partial(self.shift, 8, 2, 2, 128, 'E'),          # 0x33 SLL E
            partial(self.shift, 8, 2, 2, 128, 'H'),          # 0x34 SLL H
            partial(self.shift, 8, 2, 2, 128, 'L'),          # 0x35 SLL L
            partial(self.shift, 15, 2, 2, 128, '(HL)'),      # 0x36 SLL (HL)
            partial(self.shift, 8, 2, 2, 128, 'A'),          # 0x37 SLL A
            partial(self.shift, 8, 2, 3, 1, 'B'),            # 0x38 SRL B
            partial(self.shift, 8, 2, 3, 1, 'C'),            # 0x39 SRL C
            partial(self.shift, 8, 2, 3, 1, 'D'),            # 0x3A SRL D
            partial(self.shift, 8, 2, 3, 1, 'E'),            # 0x3B SRL E
            partial(self.shift, 8, 2, 3, 1, 'H'),            # 0x3C SRL H
            partial(self.shift, 8, 2, 3, 1, 'L'),            # 0x3D SRL L
            partial(self.shift, 15, 2, 3, 1, '(HL)'),        # 0x3E SRL (HL)
            partial(self.shift, 8, 2, 3, 1, 'A'),            # 0x3F SRL A
            partial(self.bit, 8, 2, 1, 'B'),                 # 0x40 BIT 0,B
            partial(self.bit, 8, 2, 1, 'C'),                 # 0x41 BIT 0,C
            partial(self.bit, 8, 2, 1, 'D'),                 # 0x42 BIT 0,D
            partial(self.bit, 8, 2, 1, 'E'),                 # 0x43 BIT 0,E
            partial(self.bit, 8, 2, 1, 'H'),                 # 0x44 BIT 0,H
            partial(self.bit, 8, 2, 1, 'L'),                 # 0x45 BIT 0,L
            partial(self.bit, 12, 2, 1, '(HL)'),             # 0x46 BIT 0,(HL)
            partial(self.bit, 8, 2, 1, 'A'),                 # 0x47 BIT 0,A
            partial(self.bit, 8, 2, 2, 'B'),                 # 0x48 BIT 1,B
            partial(self.bit, 8, 2, 2, 'C'),                 # 0x49 BIT 1,C
            partial(self.bit, 8, 2, 2, 'D'),                 # 0x4A BIT 1,D
            partial(self.bit, 8, 2, 2, 'E'),                 # 0x4B BIT 1,E
            partial(self.bit, 8, 2, 2, 'H'),                 # 0x4C BIT 1,H
            partial(self.bit, 8, 2, 2, 'L'),                 # 0x4D BIT 1,L
            partial(self.bit, 12, 2, 2, '(HL)'),             # 0x4E BIT 1,(HL)
            partial(self.bit, 8, 2, 2, 'A'),                 # 0x4F BIT 1,A
            partial(self.bit, 8, 2, 4, 'B'),                 # 0x50 BIT 2,B
            partial(self.bit, 8, 2, 4, 'C'),                 # 0x51 BIT 2,C
            partial(self.bit, 8, 2, 4, 'D'),                 # 0x52 BIT 2,D
            partial(self.bit, 8, 2, 4, 'E'),                 # 0x53 BIT 2,E
            partial(self.bit, 8, 2, 4, 'H'),                 # 0x54 BIT 2,H
            partial(self.bit, 8, 2, 4, 'L'),                 # 0x55 BIT 2,L
            partial(self.bit, 12, 2, 4, '(HL)'),             # 0x56 BIT 2,(HL)
            partial(self.bit, 8, 2, 4, 'A'),                 # 0x57 BIT 2,A
            partial(self.bit, 8, 2, 8, 'B'),                 # 0x58 BIT 3,B
            partial(self.bit, 8, 2, 8, 'C'),                 # 0x59 BIT 3,C
            partial(self.bit, 8, 2, 8, 'D'),                 # 0x5A BIT 3,D
            partial(self.bit, 8, 2, 8, 'E'),                 # 0x5B BIT 3,E
            partial(self.bit, 8, 2, 8, 'H'),                 # 0x5C BIT 3,H
            partial(self.bit, 8, 2, 8, 'L'),                 # 0x5D BIT 3,L
            partial(self.bit, 12, 2, 8, '(HL)'),             # 0x5E BIT 3,(HL)
            partial(self.bit, 8, 2, 8, 'A'),                 # 0x5F BIT 3,A
            partial(self.bit, 8, 2, 16, 'B'),                # 0x60 BIT 4,B
            partial(self.bit, 8, 2, 16, 'C'),                # 0x61 BIT 4,C
            partial(self.bit, 8, 2, 16, 'D'),                # 0x62 BIT 4,D
            partial(self.bit, 8, 2, 16, 'E'),                # 0x63 BIT 4,E
            partial(self.bit, 8, 2, 16, 'H'),                # 0x64 BIT 4,H
            partial(self.bit, 8, 2, 16, 'L'),                # 0x65 BIT 4,L
            partial(self.bit, 12, 2, 16, '(HL)'),            # 0x66 BIT 4,(HL)
            partial(self.bit, 8, 2, 16, 'A'),                # 0x67 BIT 4,A
            partial(self.bit, 8, 2, 32, 'B'),                # 0x68 BIT 5,B
            partial(self.bit, 8, 2, 32, 'C'),                # 0x69 BIT 5,C
            partial(self.bit, 8, 2, 32, 'D'),                # 0x6A BIT 5,D
            partial(self.bit, 8, 2, 32, 'E'),                # 0x6B BIT 5,E
            partial(self.bit, 8, 2, 32, 'H'),                # 0x6C BIT 5,H
            partial(self.bit, 8, 2, 32, 'L'),                # 0x6D BIT 5,L
            partial(self.bit, 12, 2, 32, '(HL)'),            # 0x6E BIT 5,(HL)
            partial(self.bit, 8, 2, 32, 'A'),                # 0x6F BIT 5,A
            partial(self.bit, 8, 2, 64, 'B'),                # 0x70 BIT 6,B
            partial(self.bit, 8, 2, 64, 'C'),                # 0x71 BIT 6,C
            partial(self.bit, 8, 2, 64, 'D'),                # 0x72 BIT 6,D
            partial(self.bit, 8, 2, 64, 'E'),                # 0x73 BIT 6,E
            partial(self.bit, 8, 2, 64, 'H'),                # 0x74 BIT 6,H
            partial(self.bit, 8, 2, 64, 'L'),                # 0x75 BIT 6,L
            partial(self.bit, 12, 2, 64, '(HL)'),            # 0x76 BIT 6,(HL)
            partial(self.bit, 8, 2, 64, 'A'),                # 0x77 BIT 6,A
            partial(self.bit, 8, 2, 128, 'B'),               # 0x78 BIT 7,B
            partial(self.bit, 8, 2, 128, 'C'),               # 0x79 BIT 7,C
            partial(self.bit, 8, 2, 128, 'D'),               # 0x7A BIT 7,D
            partial(self.bit, 8, 2, 128, 'E'),               # 0x7B BIT 7,E
            partial(self.bit, 8, 2, 128, 'H'),               # 0x7C BIT 7,H
            partial(self.bit, 8, 2, 128, 'L'),               # 0x7D BIT 7,L
            partial(self.bit, 12, 2, 128, '(HL)'),           # 0x7E BIT 7,(HL)
            partial(self.bit, 8, 2, 128, 'A'),               # 0x7F BIT 7,A
            partial(self.res_set, 8, 2, 254, 'B', 0),        # 0x80 RES 0,B
            partial(self.res_set, 8, 2, 254, 'C', 0),        # 0x81 RES 0,C
            partial(self.res_set, 8, 2, 254, 'D', 0),        # 0x82 RES 0,D
            partial(self.res_set, 8, 2, 254, 'E', 0),        # 0x83 RES 0,E
            partial(self.res_set, 8, 2, 254, 'H', 0),        # 0x84 RES 0,H
            partial(self.res_set, 8, 2, 254, 'L', 0),        # 0x85 RES 0,L
            partial(self.res_set, 15, 2, 254, '(HL)', 0),    # 0x86 RES 0,(HL)
            partial(self.res_set, 8, 2, 254, 'A', 0),        # 0x87 RES 0,A
            partial(self.res_set, 8, 2, 253, 'B', 0),        # 0x88 RES 1,B
            partial(self.res_set, 8, 2, 253, 'C', 0),        # 0x89 RES 1,C
            partial(self.res_set, 8, 2, 253, 'D', 0),        # 0x8A RES 1,D
            partial(self.res_set, 8, 2, 253, 'E', 0),        # 0x8B RES 1,E
            partial(self.res_set, 8, 2, 253, 'H', 0),        # 0x8C RES 1,H
            partial(self.res_set, 8, 2, 253, 'L', 0),        # 0x8D RES 1,L
            partial(self.res_set, 15, 2, 253, '(HL)', 0),    # 0x8E RES 1,(HL)
            partial(self.res_set, 8, 2, 253, 'A', 0),        # 0x8F RES 1,A
            partial(self.res_set, 8, 2, 251, 'B', 0),        # 0x90 RES 2,B
            partial(self.res_set, 8, 2, 251, 'C', 0),        # 0x91 RES 2,C
            partial(self.res_set, 8, 2, 251, 'D', 0),        # 0x92 RES 2,D
            partial(self.res_set, 8, 2, 251, 'E', 0),        # 0x93 RES 2,E
            partial(self.res_set, 8, 2, 251, 'H', 0),        # 0x94 RES 2,H
            partial(self.res_set, 8, 2, 251, 'L', 0),        # 0x95 RES 2,L
            partial(self.res_set, 15, 2, 251, '(HL)', 0),    # 0x96 RES 2,(HL)
            partial(self.res_set, 8, 2, 251, 'A', 0),        # 0x97 RES 2,A
            partial(self.res_set, 8, 2, 247, 'B', 0),        # 0x98 RES 3,B
            partial(self.res_set, 8, 2, 247, 'C', 0),        # 0x99 RES 3,C
            partial(self.res_set, 8, 2, 247, 'D', 0),        # 0x9A RES 3,D
            partial(self.res_set, 8, 2, 247, 'E', 0),        # 0x9B RES 3,E
            partial(self.res_set, 8, 2, 247, 'H', 0),        # 0x9C RES 3,H
            partial(self.res_set, 8, 2, 247, 'L', 0),        # 0x9D RES 3,L
            partial(self.res_set, 15, 2, 247, '(HL)', 0),    # 0x9E RES 3,(HL)
            partial(self.res_set, 8, 2, 247, 'A', 0),        # 0x9F RES 3,A
            partial(self.res_set, 8, 2, 239, 'B', 0),        # 0xA0 RES 4,B
            partial(self.res_set, 8, 2, 239, 'C', 0),        # 0xA1 RES 4,C
            partial(self.res_set, 8, 2, 239, 'D', 0),        # 0xA2 RES 4,D
            partial(self.res_set, 8, 2, 239, 'E', 0),        # 0xA3 RES 4,E
            partial(self.res_set, 8, 2, 239, 'H', 0),        # 0xA4 RES 4,H
            partial(self.res_set, 8, 2, 239, 'L', 0),        # 0xA5 RES 4,L
            partial(self.res_set, 15, 2, 239, '(HL)', 0),    # 0xA6 RES 4,(HL)
            partial(self.res_set, 8, 2, 239, 'A', 0),        # 0xA7 RES 4,A
            partial(self.res_set, 8, 2, 223, 'B', 0),        # 0xA8 RES 5,B
            partial(self.res_set, 8, 2, 223, 'C', 0),        # 0xA9 RES 5,C
            partial(self.res_set, 8, 2, 223, 'D', 0),        # 0xAA RES 5,D
            partial(self.res_set, 8, 2, 223, 'E', 0),        # 0xAB RES 5,E
            partial(self.res_set, 8, 2, 223, 'H', 0),        # 0xAC RES 5,H
            partial(self.res_set, 8, 2, 223, 'L', 0),        # 0xAD RES 5,L
            partial(self.res_set, 15, 2, 223, '(HL)', 0),    # 0xAE RES 5,(HL)
            partial(self.res_set, 8, 2, 223, 'A', 0),        # 0xAF RES 5,A
            partial(self.res_set, 8, 2, 191, 'B', 0),        # 0xB0 RES 6,B
            partial(self.res_set, 8, 2, 191, 'C', 0),        # 0xB1 RES 6,C
            partial(self.res_set, 8, 2, 191, 'D', 0),        # 0xB2 RES 6,D
            partial(self.res_set, 8, 2, 191, 'E', 0),        # 0xB3 RES 6,E
            partial(self.res_set, 8, 2, 191, 'H', 0),        # 0xB4 RES 6,H
            partial(self.res_set, 8, 2, 191, 'L', 0),        # 0xB5 RES 6,L
            partial(self.res_set, 15, 2, 191, '(HL)', 0),    # 0xB6 RES 6,(HL)
            partial(self.res_set, 8, 2, 191, 'A', 0),        # 0xB7 RES 6,A
            partial(self.res_set, 8, 2, 127, 'B', 0),        # 0xB8 RES 7,B
            partial(self.res_set, 8, 2, 127, 'C', 0),        # 0xB9 RES 7,C
            partial(self.res_set, 8, 2, 127, 'D', 0),        # 0xBA RES 7,D
            partial(self.res_set, 8, 2, 127, 'E', 0),        # 0xBB RES 7,E
            partial(self.res_set, 8, 2, 127, 'H', 0),        # 0xBC RES 7,H
            partial(self.res_set, 8, 2, 127, 'L', 0),        # 0xBD RES 7,L
            partial(self.res_set, 15, 2, 127, '(HL)', 0),    # 0xBE RES 7,(HL)
            partial(self.res_set, 8, 2, 127, 'A', 0),        # 0xBF RES 7,A
            partial(self.res_set, 8, 2, 1, 'B', 1),          # 0xC0 SET 0,B
            partial(self.res_set, 8, 2, 1, 'C', 1),          # 0xC1 SET 0,C
            partial(self.res_set, 8, 2, 1, 'D', 1),          # 0xC2 SET 0,D
            partial(self.res_set, 8, 2, 1, 'E', 1),          # 0xC3 SET 0,E
            partial(self.res_set, 8, 2, 1, 'H', 1),          # 0xC4 SET 0,H
            partial(self.res_set, 8, 2, 1, 'L', 1),          # 0xC5 SET 0,L
            partial(self.res_set, 15, 2, 1, '(HL)', 1),      # 0xC6 SET 0,(HL)
            partial(self.res_set, 8, 2, 1, 'A', 1),          # 0xC7 SET 0,A
            partial(self.res_set, 8, 2, 2, 'B', 1),          # 0xC8 SET 1,B
            partial(self.res_set, 8, 2, 2, 'C', 1),          # 0xC9 SET 1,C
            partial(self.res_set, 8, 2, 2, 'D', 1),          # 0xCA SET 1,D
            partial(self.res_set, 8, 2, 2, 'E', 1),          # 0xCB SET 1,E
            partial(self.res_set, 8, 2, 2, 'H', 1),          # 0xCC SET 1,H
            partial(self.res_set, 8, 2, 2, 'L', 1),          # 0xCD SET 1,L
            partial(self.res_set, 15, 2, 2, '(HL)', 1),      # 0xCE SET 1,(HL)
            partial(self.res_set, 8, 2, 2, 'A', 1),          # 0xCF SET 1,A
            partial(self.res_set, 8, 2, 4, 'B', 1),          # 0xD0 SET 2,B
            partial(self.res_set, 8, 2, 4, 'C', 1),          # 0xD1 SET 2,C
            partial(self.res_set, 8, 2, 4, 'D', 1),          # 0xD2 SET 2,D
            partial(self.res_set, 8, 2, 4, 'E', 1),          # 0xD3 SET 2,E
            partial(self.res_set, 8, 2, 4, 'H', 1),          # 0xD4 SET 2,H
            partial(self.res_set, 8, 2, 4, 'L', 1),          # 0xD5 SET 2,L
            partial(self.res_set, 15, 2, 4, '(HL)', 1),      # 0xD6 SET 2,(HL)
            partial(self.res_set, 8, 2, 4, 'A', 1),          # 0xD7 SET 2,A
            partial(self.res_set, 8, 2, 8, 'B', 1),          # 0xD8 SET 3,B
            partial(self.res_set, 8, 2, 8, 'C', 1),          # 0xD9 SET 3,C
            partial(self.res_set, 8, 2, 8, 'D', 1),          # 0xDA SET 3,D
            partial(self.res_set, 8, 2, 8, 'E', 1),          # 0xDB SET 3,E
            partial(self.res_set, 8, 2, 8, 'H', 1),          # 0xDC SET 3,H
            partial(self.res_set, 8, 2, 8, 'L', 1),          # 0xDD SET 3,L
            partial(self.res_set, 15, 2, 8, '(HL)', 1),      # 0xDE SET 3,(HL)
            partial(self.res_set, 8, 2, 8, 'A', 1),          # 0xDF SET 3,A
            partial(self.res_set, 8, 2, 16, 'B', 1),         # 0xE0 SET 4,B
            partial(self.res_set, 8, 2, 16, 'C', 1),         # 0xE1 SET 4,C
            partial(self.res_set, 8, 2, 16, 'D', 1),         # 0xE2 SET 4,D
            partial(self.res_set, 8, 2, 16, 'E', 1),         # 0xE3 SET 4,E
            partial(self.res_set, 8, 2, 16, 'H', 1),         # 0xE4 SET 4,H
            partial(self.res_set, 8, 2, 16, 'L', 1),         # 0xE5 SET 4,L
            partial(self.res_set, 15, 2, 16, '(HL)', 1),     # 0xE6 SET 4,(HL)
            partial(self.res_set, 8, 2, 16, 'A', 1),         # 0xE7 SET 4,A
            partial(self.res_set, 8, 2, 32, 'B', 1),         # 0xE8 SET 5,B
            partial(self.res_set, 8, 2, 32, 'C', 1),         # 0xE9 SET 5,C
            partial(self.res_set, 8, 2, 32, 'D', 1),         # 0xEA SET 5,D
            partial(self.res_set, 8, 2, 32, 'E', 1),         # 0xEB SET 5,E
            partial(self.res_set, 8, 2, 32, 'H', 1),         # 0xEC SET 5,H
            partial(self.res_set, 8, 2, 32, 'L', 1),         # 0xED SET 5,L
            partial(self.res_set, 15, 2, 32, '(HL)', 1),     # 0xEE SET 5,(HL)
            partial(self.res_set, 8, 2, 32, 'A', 1),         # 0xEF SET 5,A
            partial(self.res_set, 8, 2, 64, 'B', 1),         # 0xF0 SET 6,B
            partial(self.res_set, 8, 2, 64, 'C', 1),         # 0xF1 SET 6,C
            partial(self.res_set, 8, 2, 64, 'D', 1),         # 0xF2 SET 6,D
            partial(self.res_set, 8, 2, 64, 'E', 1),         # 0xF3 SET 6,E
            partial(self.res_set, 8, 2, 64, 'H', 1),         # 0xF4 SET 6,H
            partial(self.res_set, 8, 2, 64, 'L', 1),         # 0xF5 SET 6,L
            partial(self.res_set, 15, 2, 64, '(HL)', 1),     # 0xF6 SET 6,(HL)
            partial(self.res_set, 8, 2, 64, 'A', 1),         # 0xF7 SET 6,A
            partial(self.res_set, 8, 2, 128, 'B', 1),        # 0xF8 SET 7,B
            partial(self.res_set, 8, 2, 128, 'C', 1),        # 0xF9 SET 7,C
            partial(self.res_set, 8, 2, 128, 'D', 1),        # 0xFA SET 7,D
            partial(self.res_set, 8, 2, 128, 'E', 1),        # 0xFB SET 7,E
            partial(self.res_set, 8, 2, 128, 'H', 1),        # 0xFC SET 7,H
            partial(self.res_set, 8, 2, 128, 'L', 1),        # 0xFD SET 7,L
            partial(self.res_set, 15, 2, 128, '(HL)', 1),    # 0xFE SET 7,(HL)
            partial(self.res_set, 8, 2, 128, 'A', 1),        # 0xFF SET 7,A
        ]

        self.after_ED = [
            partial(self.defb, 8, 2),                        # 0x00
            partial(self.defb, 8, 2),                        # 0x01
            partial(self.defb, 8, 2),                        # 0x02
            partial(self.defb, 8, 2),                        # 0x03
            partial(self.defb, 8, 2),                        # 0x04
            partial(self.defb, 8, 2),                        # 0x05
            partial(self.defb, 8, 2),                        # 0x06
            partial(self.defb, 8, 2),                        # 0x07
            partial(self.defb, 8, 2),                        # 0x08
            partial(self.defb, 8, 2),                        # 0x09
            partial(self.defb, 8, 2),                        # 0x0A
            partial(self.defb, 8, 2),                        # 0x0B
            partial(self.defb, 8, 2),                        # 0x0C
            partial(self.defb, 8, 2),                        # 0x0D
            partial(self.defb, 8, 2),                        # 0x0E
            partial(self.defb, 8, 2),                        # 0x0F
            partial(self.defb, 8, 2),                        # 0x10
            partial(self.defb, 8, 2),                        # 0x11
            partial(self.defb, 8, 2),                        # 0x12
            partial(self.defb, 8, 2),                        # 0x13
            partial(self.defb, 8, 2),                        # 0x14
            partial(self.defb, 8, 2),                        # 0x15
            partial(self.defb, 8, 2),                        # 0x16
            partial(self.defb, 8, 2),                        # 0x17
            partial(self.defb, 8, 2),                        # 0x18
            partial(self.defb, 8, 2),                        # 0x19
            partial(self.defb, 8, 2),                        # 0x1A
            partial(self.defb, 8, 2),                        # 0x1B
            partial(self.defb, 8, 2),                        # 0x1C
            partial(self.defb, 8, 2),                        # 0x1D
            partial(self.defb, 8, 2),                        # 0x1E
            partial(self.defb, 8, 2),                        # 0x1F
            partial(self.defb, 8, 2),                        # 0x20
            partial(self.defb, 8, 2),                        # 0x21
            partial(self.defb, 8, 2),                        # 0x22
            partial(self.defb, 8, 2),                        # 0x23
            partial(self.defb, 8, 2),                        # 0x24
            partial(self.defb, 8, 2),                        # 0x25
            partial(self.defb, 8, 2),                        # 0x26
            partial(self.defb, 8, 2),                        # 0x27
            partial(self.defb, 8, 2),                        # 0x28
            partial(self.defb, 8, 2),                        # 0x29
            partial(self.defb, 8, 2),                        # 0x2A
            partial(self.defb, 8, 2),                        # 0x2B
            partial(self.defb, 8, 2),                        # 0x2C
            partial(self.defb, 8, 2),                        # 0x2D
            partial(self.defb, 8, 2),                        # 0x2E
            partial(self.defb, 8, 2),                        # 0x2F
            partial(self.defb, 8, 2),                        # 0x30
            partial(self.defb, 8, 2),                        # 0x31
            partial(self.defb, 8, 2),                        # 0x32
            partial(self.defb, 8, 2),                        # 0x33
            partial(self.defb, 8, 2),                        # 0x34
            partial(self.defb, 8, 2),                        # 0x35
            partial(self.defb, 8, 2),                        # 0x36
            partial(self.defb, 8, 2),                        # 0x37
            partial(self.defb, 8, 2),                        # 0x38
            partial(self.defb, 8, 2),                        # 0x39
            partial(self.defb, 8, 2),                        # 0x3A
            partial(self.defb, 8, 2),                        # 0x3B
            partial(self.defb, 8, 2),                        # 0x3C
            partial(self.defb, 8, 2),                        # 0x3D
            partial(self.defb, 8, 2),                        # 0x3E
            partial(self.defb, 8, 2),                        # 0x3F
            partial(self.in_c, 'B'),                         # 0x40 IN B,(C)
            partial(self.outc, 'B'),                         # 0x41 OUT (C),B
            partial(self.add16, 15, 2, 'HL', 'BC', 1, -1),   # 0x42 SBC HL,BC
            partial(self.ld16addr, 20, 4, 'BC', 1),          # 0x43 LD (nn),BC
            self.neg,                                        # 0x44 NEG
            self.reti,                                       # 0x45 RETN
            partial(self.im, 0),                             # 0x46 IM 0
            partial(self.ld8, 9, 2, 'I', 'A'),               # 0x47 LD I,A
            partial(self.in_c, 'C'),                         # 0x48 IN C,(C)
            partial(self.outc, 'C'),                         # 0x49 OUT (C),C
            partial(self.add16, 15, 2, 'HL', 'BC', 1),       # 0x4A ADC HL,BC
            partial(self.ld16addr, 20, 4, 'BC', 0),          # 0x4B LD BC,(nn)
            self.neg,                                        # 0x4C NEG
            self.reti,                                       # 0x4D RETI
            partial(self.im, 0),                             # 0x4E IM 0
            partial(self.ld8, 9, 2, 'R', 'A'),               # 0x4F LD R,A
            partial(self.in_c, 'D'),                         # 0x50 IN D,(C)
            partial(self.outc, 'D'),                         # 0x51 OUT (C),D
            partial(self.add16, 15, 2, 'HL', 'DE', 1, -1),   # 0x52 SBC HL,DE
            partial(self.ld16addr, 20, 4, 'DE', 1),          # 0x53 LD (nn),DE
            self.neg,                                        # 0x54 NEG
            self.reti,                                       # 0x55 RETN
            partial(self.im, 1),                             # 0x56 IM 1
            partial(self.ld8, 9, 2, 'A', 'I'),               # 0x57 LD A,I
            partial(self.in_c, 'E'),                         # 0x58 IN E,(C)
            partial(self.outc, 'E'),                         # 0x59 OUT (C),E
            partial(self.add16, 15, 2, 'HL', 'DE', 1),       # 0x5A ADC HL,DE
            partial(self.ld16addr, 20, 4, 'DE', 0),          # 0x5B LD DE,(nn)
            self.neg,                                        # 0x5C NEG
            self.reti,                                       # 0x5D RETN
            partial(self.im, 2),                             # 0x5E IM 2
            partial(self.ld8, 9, 2, 'A', 'R'),               # 0x5F LD A,R
            partial(self.in_c, 'H'),                         # 0x60 IN H,(C)
            partial(self.outc, 'H'),                         # 0x61 OUT (C),H
            partial(self.add16, 15, 2, 'HL', 'HL', 1, -1),   # 0x62 SBC HL,HL
            partial(self.ld16addr, 20, 4, 'HL', 1),          # 0x63 LD (nn),HL
            self.neg,                                        # 0x64 NEG
            self.reti,                                       # 0x65 RETN
            partial(self.im, 0),                             # 0x66 IM 0
            self.rrd,                                        # 0x67 RRD
            partial(self.in_c, 'L'),                         # 0x68 IN L,(C)
            partial(self.outc, 'L'),                         # 0x69 OUT (C),L
            partial(self.add16, 15, 2, 'HL', 'HL', 1),       # 0x6A ADC HL,HL
            partial(self.ld16addr, 20, 4, 'HL', 0),          # 0x6B LD HL,(nn)
            self.neg,                                        # 0x6C NEG
            self.reti,                                       # 0x6D RETN
            partial(self.im, 0),                             # 0x6E IM 0
            self.rld,                                        # 0x6F RLD
            partial(self.in_c, 'F'),                         # 0x70 IN F,(C)
            partial(self.outc, ''),                          # 0x71 OUT (C),0
            partial(self.add16, 15, 2, 'HL', 'SP', 1, -1),   # 0x72 SBC HL,SP
            partial(self.ld16addr, 20, 4, 'SP', 1),          # 0x73 LD (nn),SP
            self.neg,                                        # 0x74 NEG
            self.reti,                                       # 0x75 RETN
            partial(self.im, 1),                             # 0x76 IM 1
            partial(self.defb, 8, 2),                        # 0x77
            partial(self.in_c, 'A'),                         # 0x78 IN A,(C)
            partial(self.outc, 'A'),                         # 0x79 OUT (C),A
            partial(self.add16, 15, 2, 'HL', 'SP', 1),       # 0x7A ADC HL,SP
            partial(self.ld16addr, 20, 4, 'SP', 0),          # 0x7B LD SP,(nn)
            self.neg,                                        # 0x7C NEG
            self.reti,                                       # 0x7D RETN
            partial(self.im, 2),                             # 0x7E IM 2
            partial(self.defb, 8, 2),                        # 0x7F
            partial(self.defb, 8, 2),                        # 0x80
            partial(self.defb, 8, 2),                        # 0x81
            partial(self.defb, 8, 2),                        # 0x82
            partial(self.defb, 8, 2),                        # 0x83
            partial(self.defb, 8, 2),                        # 0x84
            partial(self.defb, 8, 2),                        # 0x85
            partial(self.defb, 8, 2),                        # 0x86
            partial(self.defb, 8, 2),                        # 0x87
            partial(self.defb, 8, 2),                        # 0x88
            partial(self.defb, 8, 2),                        # 0x89
            partial(self.defb, 8, 2),                        # 0x8A
            partial(self.defb, 8, 2),                        # 0x8B
            partial(self.defb, 8, 2),                        # 0x8C
            partial(self.defb, 8, 2),                        # 0x8D
            partial(self.defb, 8, 2),                        # 0x8E
            partial(self.defb, 8, 2),                        # 0x8F
            partial(self.defb, 8, 2),                        # 0x90
            partial(self.defb, 8, 2),                        # 0x91
            partial(self.defb, 8, 2),                        # 0x92
            partial(self.defb, 8, 2),                        # 0x93
            partial(self.defb, 8, 2),                        # 0x94
            partial(self.defb, 8, 2),                        # 0x95
            partial(self.defb, 8, 2),                        # 0x96
            partial(self.defb, 8, 2),                        # 0x97
            partial(self.defb, 8, 2),                        # 0x98
            partial(self.defb, 8, 2),                        # 0x99
            partial(self.defb, 8, 2),                        # 0x9A
            partial(self.defb, 8, 2),                        # 0x9B
            partial(self.defb, 8, 2),                        # 0x9C
            partial(self.defb, 8, 2),                        # 0x9D
            partial(self.defb, 8, 2),                        # 0x9E
            partial(self.defb, 8, 2),                        # 0x9F
            partial(self.block, 0, 1, 0),                    # 0xA0 LDI
            partial(self.block, 1, 1, 0),                    # 0xA1 CPI
            partial(self.block, 2, 1, 0),                    # 0xA2 INI
            partial(self.block, 3, 1, 0),                    # 0xA3 OUTI
            partial(self.defb, 8, 2),                        # 0xA4
            partial(self.defb, 8, 2),                        # 0xA5
            partial(self.defb, 8, 2),                        # 0xA6
            partial(self.defb, 8, 2),                        # 0xA7
            partial(self.block, 0, -1, 0),                   # 0xA8 LDD
            partial(self.block, 1, -1, 0),                   # 0xA9 CPD
            partial(self.block, 2, -1, 0),                   # 0xAA IND
            partial(self.block, 3, -1, 0),                   # 0xAB OUTD
            partial(self.defb, 8, 2),                        # 0xAC
            partial(self.defb, 8, 2),                        # 0xAD
            partial(self.defb, 8, 2),                        # 0xAE
            partial(self.defb, 8, 2),                        # 0xAF
            partial(self.block, 0, 1, 1),                    # 0xB0 LDIR
            partial(self.block, 1, 1, 1),                    # 0xB1 CPIR
            partial(self.block, 2, 1, 1),                    # 0xB2 INIR
            partial(self.block, 3, 1, 1),                    # 0xB3 OTIR
            partial(self.defb, 8, 2),                        # 0xB4
            partial(self.defb, 8, 2),                        # 0xB5
            partial(self.defb, 8, 2),                        # 0xB6
            partial(self.defb, 8, 2),                        # 0xB7
            partial(self.block, 0, -1, 1),                   # 0xB8 LDDR
            partial(self.block, 1, -1, 1),                   # 0xB9 CPDR
            partial(self.block, 2, -1, 1),                   # 0xBA INDR
            partial(self.block, 3, -1, 1),                   # 0xBB OTDR
            partial(self.defb, 8, 2),                        # 0xBC
            partial(self.defb, 8, 2),                        # 0xBD
            partial(self.defb, 8, 2),                        # 0xBE
            partial(self.defb, 8, 2),                        # 0xBF
            partial(self.defb, 8, 2),                        # 0xC0
            partial(self.defb, 8, 2),                        # 0xC1
            partial(self.defb, 8, 2),                        # 0xC2
            partial(self.defb, 8, 2),                        # 0xC3
            partial(self.defb, 8, 2),                        # 0xC4
            partial(self.defb, 8, 2),                        # 0xC5
            partial(self.defb, 8, 2),                        # 0xC6
            partial(self.defb, 8, 2),                        # 0xC7
            partial(self.defb, 8, 2),                        # 0xC8
            partial(self.defb, 8, 2),                        # 0xC9
            partial(self.defb, 8, 2),                        # 0xCA
            partial(self.defb, 8, 2),                        # 0xCB
            partial(self.defb, 8, 2),                        # 0xCC
            partial(self.defb, 8, 2),                        # 0xCD
            partial(self.defb, 8, 2),                        # 0xCE
            partial(self.defb, 8, 2),                        # 0xCF
            partial(self.defb, 8, 2),                        # 0xD0
            partial(self.defb, 8, 2),                        # 0xD1
            partial(self.defb, 8, 2),                        # 0xD2
            partial(self.defb, 8, 2),                        # 0xD3
            partial(self.defb, 8, 2),                        # 0xD4
            partial(self.defb, 8, 2),                        # 0xD5
            partial(self.defb, 8, 2),                        # 0xD6
            partial(self.defb, 8, 2),                        # 0xD7
            partial(self.defb, 8, 2),                        # 0xD8
            partial(self.defb, 8, 2),                        # 0xD9
            partial(self.defb, 8, 2),                        # 0xDA
            partial(self.defb, 8, 2),                        # 0xDB
            partial(self.defb, 8, 2),                        # 0xDC
            partial(self.defb, 8, 2),                        # 0xDD
            partial(self.defb, 8, 2),                        # 0xDE
            partial(self.defb, 8, 2),                        # 0xDF
            partial(self.defb, 8, 2),                        # 0xE0
            partial(self.defb, 8, 2),                        # 0xE1
            partial(self.defb, 8, 2),                        # 0xE2
            partial(self.defb, 8, 2),                        # 0xE3
            partial(self.defb, 8, 2),                        # 0xE4
            partial(self.defb, 8, 2),                        # 0xE5
            partial(self.defb, 8, 2),                        # 0xE6
            partial(self.defb, 8, 2),                        # 0xE7
            partial(self.defb, 8, 2),                        # 0xE8
            partial(self.defb, 8, 2),                        # 0xE9
            partial(self.defb, 8, 2),                        # 0xEA
            partial(self.defb, 8, 2),                        # 0xEB
            partial(self.defb, 8, 2),                        # 0xEC
            partial(self.defb, 8, 2),                        # 0xED
            partial(self.defb, 8, 2),                        # 0xEE
            partial(self.defb, 8, 2),                        # 0xEF
            partial(self.defb, 8, 2),                        # 0xF0
            partial(self.defb, 8, 2),                        # 0xF1
            partial(self.defb, 8, 2),                        # 0xF2
            partial(self.defb, 8, 2),                        # 0xF3
            partial(self.defb, 8, 2),                        # 0xF4
            partial(self.defb, 8, 2),                        # 0xF5
            partial(self.defb, 8, 2),                        # 0xF6
            partial(self.defb, 8, 2),                        # 0xF7
            partial(self.defb, 8, 2),                        # 0xF8
            partial(self.defb, 8, 2),                        # 0xF9
            partial(self.defb, 8, 2),                        # 0xFA
            partial(self.defb, 8, 2),                        # 0xFB
            partial(self.defb, 8, 2),                        # 0xFC
            partial(self.defb, 8, 2),                        # 0xFD
            partial(self.defb, 8, 2),                        # 0xFE
            partial(self.defb, 8, 2),                        # 0xFF
        ]

        self.after_DD = [
            partial(self.defb, 4, 1),                        # 0x00
            partial(self.defb, 4, 1),                        # 0x01
            partial(self.defb, 4, 1),                        # 0x02
            partial(self.defb, 4, 1),                        # 0x03
            partial(self.defb, 4, 1),                        # 0x04
            partial(self.defb, 4, 1),                        # 0x05
            partial(self.defb, 4, 1),                        # 0x06
            partial(self.defb, 4, 1),                        # 0x07
            partial(self.defb, 4, 1),                        # 0x08
            partial(self.add16, 15, 2, 'IX', 'BC'),          # 0x09 ADD IX,BC
            partial(self.defb, 4, 1),                        # 0x0A
            partial(self.defb, 4, 1),                        # 0x0B
            partial(self.defb, 4, 1),                        # 0x0C
            partial(self.defb, 4, 1),                        # 0x0D
            partial(self.defb, 4, 1),                        # 0x0E
            partial(self.defb, 4, 1),                        # 0x0F
            partial(self.defb, 4, 1),                        # 0x10
            partial(self.defb, 4, 1),                        # 0x11
            partial(self.defb, 4, 1),                        # 0x12
            partial(self.defb, 4, 1),                        # 0x13
            partial(self.defb, 4, 1),                        # 0x14
            partial(self.defb, 4, 1),                        # 0x15
            partial(self.defb, 4, 1),                        # 0x16
            partial(self.defb, 4, 1),                        # 0x17
            partial(self.defb, 4, 1),                        # 0x18
            partial(self.add16, 15, 2, 'IX', 'DE'),          # 0x19 ADD IX,DE
            partial(self.defb, 4, 1),                        # 0x1A
            partial(self.defb, 4, 1),                        # 0x1B
            partial(self.defb, 4, 1),                        # 0x1C
            partial(self.defb, 4, 1),                        # 0x1D
            partial(self.defb, 4, 1),                        # 0x1E
            partial(self.defb, 4, 1),                        # 0x1F
            partial(self.defb, 4, 1),                        # 0x20
            partial(self.ld16, 'IX'),                        # 0x21 LD IX,nn
            partial(self.ld16addr, 20, 4, 'IX', 1),          # 0x22 LD (nn),IX
            partial(self.inc_dec16, 1, 'IX'),                # 0x23 INC IX
            partial(self.inc_dec8, 8, 2, 1, 'IXh'),          # 0x24 INC IXh
            partial(self.inc_dec8, 8, 2, -1, 'IXh'),         # 0x25 DEC IXh
            partial(self.ld8, 11, 3, 'IXh'),                 # 0x26 LD IXh,n
            partial(self.defb, 4, 1),                        # 0x27
            partial(self.defb, 4, 1),                        # 0x28
            partial(self.add16, 15, 2, 'IX', 'IX'),          # 0x29 ADD IX,IX
            partial(self.ld16addr, 20, 4, 'IX', 0),          # 0x2A LD IX,(nn)
            partial(self.inc_dec16, -1, 'IX'),               # 0x2B DEC IX
            partial(self.inc_dec8, 8, 2, 1, 'IXl'),          # 0x2C INC IXl
            partial(self.inc_dec8, 8, 2, -1, 'IXl'),         # 0x2D DEC IXl
            partial(self.ld8, 11, 3, 'IXl'),                 # 0x2E LD IXl,n
            partial(self.defb, 4, 1),                        # 0x2F
            partial(self.defb, 4, 1),                        # 0x30
            partial(self.defb, 4, 1),                        # 0x31
            partial(self.defb, 4, 1),                        # 0x32
            partial(self.defb, 4, 1),                        # 0x33
            partial(self.inc_dec8, 23, 3, 1, 'Xd'),          # 0x34 INC (IX+d)
            partial(self.inc_dec8, 23, 3, -1, 'Xd'),         # 0x35 DEC (IX+d)
            partial(self.ld8, 19, 4, 'Xd'),                  # 0x36 LD (IX+d),n
            partial(self.defb, 4, 1),                        # 0x37
            partial(self.defb, 4, 1),                        # 0x38
            partial(self.add16, 15, 2, 'IX', 'SP'),          # 0x39 ADD IX,SP
            partial(self.defb, 4, 1),                        # 0x3A
            partial(self.defb, 4, 1),                        # 0x3B
            partial(self.defb, 4, 1),                        # 0x3C
            partial(self.defb, 4, 1),                        # 0x3D
            partial(self.defb, 4, 1),                        # 0x3E
            partial(self.defb, 4, 1),                        # 0x3F
            partial(self.defb, 4, 1),                        # 0x40
            partial(self.defb, 4, 1),                        # 0x41
            partial(self.defb, 4, 1),                        # 0x42
            partial(self.defb, 4, 1),                        # 0x43
            partial(self.ld8, 8, 2, 'B', 'IXh'),             # 0x44 LD B,IXh
            partial(self.ld8, 8, 2, 'B', 'IXl'),             # 0x45 LD B,IXl
            partial(self.ld8, 19, 3, 'B', 'Xd'),             # 0x46 LD B,(IX+d)
            partial(self.defb, 4, 1),                        # 0x47
            partial(self.defb, 4, 1),                        # 0x48
            partial(self.defb, 4, 1),                        # 0x49
            partial(self.defb, 4, 1),                        # 0x4A
            partial(self.defb, 4, 1),                        # 0x4B
            partial(self.ld8, 8, 2, 'C', 'IXh'),             # 0x4C LD C,IXh
            partial(self.ld8, 8, 2, 'C', 'IXl'),             # 0x4D LD C,IXl
            partial(self.ld8, 19, 3, 'C', 'Xd'),             # 0x4E LD C,(IX+d)
            partial(self.defb, 4, 1),                        # 0x4F
            partial(self.defb, 4, 1),                        # 0x50
            partial(self.defb, 4, 1),                        # 0x51
            partial(self.defb, 4, 1),                        # 0x52
            partial(self.defb, 4, 1),                        # 0x53
            partial(self.ld8, 8, 2, 'D', 'IXh'),             # 0x54 LD D,IXh
            partial(self.ld8, 8, 2, 'D', 'IXl'),             # 0x55 LD D,IXl
            partial(self.ld8, 19, 3, 'D', 'Xd'),             # 0x56 LD D,(IX+d)
            partial(self.defb, 4, 1),                        # 0x57
            partial(self.defb, 4, 1),                        # 0x58
            partial(self.defb, 4, 1),                        # 0x59
            partial(self.defb, 4, 1),                        # 0x5A
            partial(self.defb, 4, 1),                        # 0x5B
            partial(self.ld8, 8, 2, 'E', 'IXh'),             # 0x5C LD E,IXh
            partial(self.ld8, 8, 2, 'E', 'IXl'),             # 0x5D LD E,IXl
            partial(self.ld8, 19, 3, 'E', 'Xd'),             # 0x5E LD E,(IX+d)
            partial(self.defb, 4, 1),                        # 0x5F
            partial(self.ld8, 8, 2, 'IXh', 'B'),             # 0x60 LD IXh,B
            partial(self.ld8, 8, 2, 'IXh', 'C'),             # 0x61 LD IXh,C
            partial(self.ld8, 8, 2, 'IXh', 'D'),             # 0x62 LD IXh,D
            partial(self.ld8, 8, 2, 'IXh', 'E'),             # 0x63 LD IXh,E
            partial(self.ld8, 8, 2, 'IXh', 'IXh'),           # 0x64 LD IXh,IXh
            partial(self.ld8, 8, 2, 'IXh', 'IXl'),           # 0x65 LD IXh,IXl
            partial(self.ld8, 19, 3, 'H', 'Xd'),             # 0x66 LD H,(IX+d)
            partial(self.ld8, 8, 2, 'IXh', 'A'),             # 0x67 LD IXh,A
            partial(self.ld8, 8, 2, 'IXl', 'B'),             # 0x68 LD IXl,B
            partial(self.ld8, 8, 2, 'IXl', 'C'),             # 0x69 LD IXl,C
            partial(self.ld8, 8, 2, 'IXl', 'D'),             # 0x6A LD IXl,D
            partial(self.ld8, 8, 2, 'IXl', 'E'),             # 0x6B LD IXl,E
            partial(self.ld8, 8, 2, 'IXl', 'IXh'),           # 0x6C LD IXl,IXh
            partial(self.ld8, 8, 2, 'IXl', 'IXl'),           # 0x6D LD IXl,IXl
            partial(self.ld8, 19, 3, 'L', 'Xd'),             # 0x6E LD L,(IX+d)
            partial(self.ld8, 8, 2, 'IXl', 'A'),             # 0x6F LD IXl,A
            partial(self.ld8, 19, 3, 'Xd', 'B'),             # 0x70 LD (IX+d),B
            partial(self.ld8, 19, 3, 'Xd', 'C'),             # 0x71 LD (IX+d),C
            partial(self.ld8, 19, 3, 'Xd', 'D'),             # 0x72 LD (IX+d),D
            partial(self.ld8, 19, 3, 'Xd', 'E'),             # 0x73 LD (IX+d),E
            partial(self.ld8, 19, 3, 'Xd', 'H'),             # 0x74 LD (IX+d),H
            partial(self.ld8, 19, 3, 'Xd', 'L'),             # 0x75 LD (IX+d),L
            partial(self.defb, 4, 1),                        # 0x76
            partial(self.ld8, 19, 3, 'Xd', 'A'),             # 0x77 LD (IX+d),A
            partial(self.defb, 4, 1),                        # 0x78
            partial(self.defb, 4, 1),                        # 0x79
            partial(self.defb, 4, 1),                        # 0x7A
            partial(self.defb, 4, 1),                        # 0x7B
            partial(self.ld8, 8, 2, 'A', 'IXh'),             # 0x7C LD A,IXh
            partial(self.ld8, 8, 2, 'A', 'IXl'),             # 0x7D LD A,IXl
            partial(self.ld8, 19, 3, 'A', 'Xd'),             # 0x7E LD A,(IX+d)
            partial(self.defb, 4, 1),                        # 0x7F
            partial(self.defb, 4, 1),                        # 0x80
            partial(self.defb, 4, 1),                        # 0x81
            partial(self.defb, 4, 1),                        # 0x82
            partial(self.defb, 4, 1),                        # 0x83
            partial(self.add_a, 8, 2, 'IXh'),                # 0x84 ADD A,IXh
            partial(self.add_a, 8, 2, 'IXl'),                # 0x85 ADD A,IXl
            partial(self.add_a, 19, 3, 'Xd'),                # 0x86 ADD A,(IX+d)
            partial(self.defb, 4, 1),                        # 0x87
            partial(self.defb, 4, 1),                        # 0x88
            partial(self.defb, 4, 1),                        # 0x89
            partial(self.defb, 4, 1),                        # 0x8A
            partial(self.defb, 4, 1),                        # 0x8B
            partial(self.add_a, 8, 2, 'IXh', 1),             # 0x8C ADC A,IXh
            partial(self.add_a, 8, 2, 'IXl', 1),             # 0x8D ADC A,IXl
            partial(self.add_a, 19, 3, 'Xd', 1),             # 0x8E ADC A,(IX+d)
            partial(self.defb, 4, 1),                        # 0x8F
            partial(self.defb, 4, 1),                        # 0x90
            partial(self.defb, 4, 1),                        # 0x91
            partial(self.defb, 4, 1),                        # 0x92
            partial(self.defb, 4, 1),                        # 0x93
            partial(self.add_a, 8, 2, 'IXh', 0, -1),         # 0x94 SUB IXh
            partial(self.add_a, 8, 2, 'IXl', 0, -1),         # 0x95 SUB IXl
            partial(self.add_a, 19, 3, 'Xd', 0, -1),         # 0x96 SUB (IX+d)
            partial(self.defb, 4, 1),                        # 0x97
            partial(self.defb, 4, 1),                        # 0x98
            partial(self.defb, 4, 1),                        # 0x99
            partial(self.defb, 4, 1),                        # 0x9A
            partial(self.defb, 4, 1),                        # 0x9B
            partial(self.add_a, 8, 2, 'IXh', 1, -1),         # 0x9C SBC A,IXh
            partial(self.add_a, 8, 2, 'IXl', 1, -1),         # 0x9D SBC A,IXl
            partial(self.add_a, 19, 3, 'Xd', 1, -1),         # 0x9E SBC A,(IX+d)
            partial(self.defb, 4, 1),                        # 0x9F
            partial(self.defb, 4, 1),                        # 0xA0
            partial(self.defb, 4, 1),                        # 0xA1
            partial(self.defb, 4, 1),                        # 0xA2
            partial(self.defb, 4, 1),                        # 0xA3
            partial(self.anda, 8, 2, 'IXh'),                 # 0xA4 AND IXh
            partial(self.anda, 8, 2, 'IXl'),                 # 0xA5 AND IXl
            partial(self.anda, 19, 3, 'Xd'),                 # 0xA6 AND (IX+d)
            partial(self.defb, 4, 1),                        # 0xA7
            partial(self.defb, 4, 1),                        # 0xA8
            partial(self.defb, 4, 1),                        # 0xA9
            partial(self.defb, 4, 1),                        # 0xAA
            partial(self.defb, 4, 1),                        # 0xAB
            partial(self.xor, 8, 2, 'IXh'),                  # 0xAC XOR IXh
            partial(self.xor, 8, 2, 'IXl'),                  # 0xAD XOR IXl
            partial(self.xor, 19, 3, 'Xd'),                  # 0xAE XOR (IX+d)
            partial(self.defb, 4, 1),                        # 0xAF
            partial(self.defb, 4, 1),                        # 0xB0
            partial(self.defb, 4, 1),                        # 0xB1
            partial(self.defb, 4, 1),                        # 0xB2
            partial(self.defb, 4, 1),                        # 0xB3
            partial(self.ora, 8, 2, 'IXh'),                  # 0xB4 OR IXh
            partial(self.ora, 8, 2, 'IXl'),                  # 0xB5 OR IXl
            partial(self.ora, 19, 3, 'Xd'),                  # 0xB6 OR (IX+d)
            partial(self.defb, 4, 1),                        # 0xB7
            partial(self.defb, 4, 1),                        # 0xB8
            partial(self.defb, 4, 1),                        # 0xB9
            partial(self.defb, 4, 1),                        # 0xBA
            partial(self.defb, 4, 1),                        # 0xBB
            partial(self.cp, 8, 2, 'IXh'),                   # 0xBC CP IXh
            partial(self.cp, 8, 2, 'IXl'),                   # 0xBD CP IXl
            partial(self.cp, 19, 3, 'Xd'),                   # 0xBE CP (IX+d)
            partial(self.defb, 4, 1),                        # 0xBF
            partial(self.defb, 4, 1),                        # 0xC0
            partial(self.defb, 4, 1),                        # 0xC1
            partial(self.defb, 4, 1),                        # 0xC2
            partial(self.defb, 4, 1),                        # 0xC3
            partial(self.defb, 4, 1),                        # 0xC4
            partial(self.defb, 4, 1),                        # 0xC5
            partial(self.defb, 4, 1),                        # 0xC6
            partial(self.defb, 4, 1),                        # 0xC7
            partial(self.defb, 4, 1),                        # 0xC8
            partial(self.defb, 4, 1),                        # 0xC9
            partial(self.defb, 4, 1),                        # 0xCA
            None,                                            # 0xCB DDCB prefix
            partial(self.defb, 4, 1),                        # 0xCC
            partial(self.defb, 4, 1),                        # 0xCD
            partial(self.defb, 4, 1),                        # 0xCE
            partial(self.defb, 4, 1),                        # 0xCF
            partial(self.defb, 4, 1),                        # 0xD0
            partial(self.defb, 4, 1),                        # 0xD1
            partial(self.defb, 4, 1),                        # 0xD2
            partial(self.defb, 4, 1),                        # 0xD3
            partial(self.defb, 4, 1),                        # 0xD4
            partial(self.defb, 4, 1),                        # 0xD5
            partial(self.defb, 4, 1),                        # 0xD6
            partial(self.defb, 4, 1),                        # 0xD7
            partial(self.defb, 4, 1),                        # 0xD8
            partial(self.defb, 4, 1),                        # 0xD9
            partial(self.defb, 4, 1),                        # 0xDA
            partial(self.defb, 4, 1),                        # 0xDB
            partial(self.defb, 4, 1),                        # 0xDC
            partial(self.defb, 4, 1),                        # 0xDD
            partial(self.defb, 4, 1),                        # 0xDE
            partial(self.defb, 4, 1),                        # 0xDF
            partial(self.defb, 4, 1),                        # 0xE0
            partial(self.pop, 'IX'),                         # 0xE1 POP IX
            partial(self.defb, 4, 1),                        # 0xE2
            partial(self.ex_sp, 'IX'),                       # 0xE3 EX (SP),IX
            partial(self.defb, 4, 1),                        # 0xE4
            partial(self.push, 'IX'),                        # 0xE5 PUSH IX
            partial(self.defb, 4, 1),                        # 0xE6
            partial(self.defb, 4, 1),                        # 0xE7
            partial(self.defb, 4, 1),                        # 0xE8
            partial(self.jp, 0, 0),                          # 0xE9 JP (IX)
            partial(self.defb, 4, 1),                        # 0xEA
            partial(self.defb, 4, 1),                        # 0xEB
            partial(self.defb, 4, 1),                        # 0xEC
            partial(self.defb, 4, 1),                        # 0xED
            partial(self.defb, 4, 1),                        # 0xEE
            partial(self.defb, 4, 1),                        # 0xEF
            partial(self.defb, 4, 1),                        # 0xF0
            partial(self.defb, 4, 1),                        # 0xF1
            partial(self.defb, 4, 1),                        # 0xF2
            partial(self.defb, 4, 1),                        # 0xF3
            partial(self.defb, 4, 1),                        # 0xF4
            partial(self.defb, 4, 1),                        # 0xF5
            partial(self.defb, 4, 1),                        # 0xF6
            partial(self.defb, 4, 1),                        # 0xF7
            partial(self.defb, 4, 1),                        # 0xF8
            partial(self.ldsprr, 'IX'),                      # 0xF9 LD SP,IX
            partial(self.defb, 4, 1),                        # 0xFA
            partial(self.defb, 4, 1),                        # 0xFB
            partial(self.defb, 4, 1),                        # 0xFC
            partial(self.defb, 4, 1),                        # 0xFD
            partial(self.defb, 4, 1),                        # 0xFE
            partial(self.defb, 4, 1),                        # 0xFF
        ]

        self.after_DDCB = [
            partial(self.rotate, 23, 4, 128, 'Xd', 1, 'B'),  # 0x00 RLC (IX+d),B
            partial(self.rotate, 23, 4, 128, 'Xd', 1, 'C'),  # 0x01 RLC (IX+d),C
            partial(self.rotate, 23, 4, 128, 'Xd', 1, 'D'),  # 0x02 RLC (IX+d),D
            partial(self.rotate, 23, 4, 128, 'Xd', 1, 'E'),  # 0x03 RLC (IX+d),E
            partial(self.rotate, 23, 4, 128, 'Xd', 1, 'H'),  # 0x04 RLC (IX+d),H
            partial(self.rotate, 23, 4, 128, 'Xd', 1, 'L'),  # 0x05 RLC (IX+d),L
            partial(self.rotate, 23, 4, 128, 'Xd', 1),       # 0x06 RLC (IX+d)
            partial(self.rotate, 23, 4, 128, 'Xd', 1, 'A'),  # 0x07 RLC (IX+d),A
            partial(self.rotate, 23, 4, 1, 'Xd', 1, 'B'),    # 0x08 RRC (IX+d),B
            partial(self.rotate, 23, 4, 1, 'Xd', 1, 'C'),    # 0x09 RRC (IX+d),C
            partial(self.rotate, 23, 4, 1, 'Xd', 1, 'D'),    # 0x0A RRC (IX+d),D
            partial(self.rotate, 23, 4, 1, 'Xd', 1, 'E'),    # 0x0B RRC (IX+d),E
            partial(self.rotate, 23, 4, 1, 'Xd', 1, 'H'),    # 0x0C RRC (IX+d),H
            partial(self.rotate, 23, 4, 1, 'Xd', 1, 'L'),    # 0x0D RRC (IX+d),L
            partial(self.rotate, 23, 4, 1, 'Xd', 1),         # 0x0E RRC (IX+d)
            partial(self.rotate, 23, 4, 1, 'Xd', 1, 'A'),    # 0x0F RRC (IX+d),A
            partial(self.rotate, 23, 4, 128, 'Xd', 0, 'B'),  # 0x10 RL (IX+d),B
            partial(self.rotate, 23, 4, 128, 'Xd', 0, 'C'),  # 0x11 RL (IX+d),C
            partial(self.rotate, 23, 4, 128, 'Xd', 0, 'D'),  # 0x12 RL (IX+d),D
            partial(self.rotate, 23, 4, 128, 'Xd', 0, 'E'),  # 0x13 RL (IX+d),E
            partial(self.rotate, 23, 4, 128, 'Xd', 0, 'H'),  # 0x14 RL (IX+d),H
            partial(self.rotate, 23, 4, 128, 'Xd', 0, 'L'),  # 0x15 RL (IX+d),L
            partial(self.rotate, 23, 4, 128, 'Xd'),          # 0x16 RL (IX+d)
            partial(self.rotate, 23, 4, 128, 'Xd', 0, 'A'),  # 0x17 RL (IX+d),A
            partial(self.rotate, 23, 4, 1, 'Xd', 0, 'B'),    # 0x18 RR (IX+d),B
            partial(self.rotate, 23, 4, 1, 'Xd', 0, 'C'),    # 0x19 RR (IX+d),C
            partial(self.rotate, 23, 4, 1, 'Xd', 0, 'D'),    # 0x1A RR (IX+d),D
            partial(self.rotate, 23, 4, 1, 'Xd', 0, 'E'),    # 0x1B RR (IX+d),E
            partial(self.rotate, 23, 4, 1, 'Xd', 0, 'H'),    # 0x1C RR (IX+d),H
            partial(self.rotate, 23, 4, 1, 'Xd', 0, 'L'),    # 0x1D RR (IX+d),L
            partial(self.rotate, 23, 4, 1, 'Xd'),            # 0x1E RR (IX+d)
            partial(self.rotate, 23, 4, 1, 'Xd', 0, 'A'),    # 0x1F RR (IX+d),A
            partial(self.shift, 23, 4, 0, 128, 'Xd', 'B'),   # 0x20 SLA (IX+d),B
            partial(self.shift, 23, 4, 0, 128, 'Xd', 'C'),   # 0x21 SLA (IX+d),C
            partial(self.shift, 23, 4, 0, 128, 'Xd', 'D'),   # 0x22 SLA (IX+d),D
            partial(self.shift, 23, 4, 0, 128, 'Xd', 'E'),   # 0x23 SLA (IX+d),E
            partial(self.shift, 23, 4, 0, 128, 'Xd', 'H'),   # 0x24 SLA (IX+d),H
            partial(self.shift, 23, 4, 0, 128, 'Xd', 'L'),   # 0x25 SLA (IX+d),L
            partial(self.shift, 23, 4, 0, 128, 'Xd'),        # 0x26 SLA (IX+d)
            partial(self.shift, 23, 4, 0, 128, 'Xd', 'A'),   # 0x27 SLA (IX+d),A
            partial(self.shift, 23, 4, 1, 1, 'Xd', 'B'),     # 0x28 SRA (IX+d),B
            partial(self.shift, 23, 4, 1, 1, 'Xd', 'C'),     # 0x29 SRA (IX+d),C
            partial(self.shift, 23, 4, 1, 1, 'Xd', 'D'),     # 0x2A SRA (IX+d),D
            partial(self.shift, 23, 4, 1, 1, 'Xd', 'E'),     # 0x2B SRA (IX+d),E
            partial(self.shift, 23, 4, 1, 1, 'Xd', 'H'),     # 0x2C SRA (IX+d),H
            partial(self.shift, 23, 4, 1, 1, 'Xd', 'L'),     # 0x2D SRA (IX+d),L
            partial(self.shift, 23, 4, 1, 1, 'Xd'),          # 0x2E SRA (IX+d)
            partial(self.shift, 23, 4, 1, 1, 'Xd', 'A'),     # 0x2F SRA (IX+d),A
            partial(self.shift, 23, 4, 2, 128, 'Xd', 'B'),   # 0x30 SLL (IX+d),B
            partial(self.shift, 23, 4, 2, 128, 'Xd', 'C'),   # 0x31 SLL (IX+d),C
            partial(self.shift, 23, 4, 2, 128, 'Xd', 'D'),   # 0x32 SLL (IX+d),D
            partial(self.shift, 23, 4, 2, 128, 'Xd', 'E'),   # 0x33 SLL (IX+d),E
            partial(self.shift, 23, 4, 2, 128, 'Xd', 'H'),   # 0x34 SLL (IX+d),H
            partial(self.shift, 23, 4, 2, 128, 'Xd', 'L'),   # 0x35 SLL (IX+d),L
            partial(self.shift, 23, 4, 2, 128, 'Xd'),        # 0x36 SLL (IX+d)
            partial(self.shift, 23, 4, 2, 128, 'Xd', 'A'),   # 0x37 SLL (IX+d),A
            partial(self.shift, 23, 4, 3, 1, 'Xd', 'B'),     # 0x38 SRL (IX+d),B
            partial(self.shift, 23, 4, 3, 1, 'Xd', 'C'),     # 0x39 SRL (IX+d),C
            partial(self.shift, 23, 4, 3, 1, 'Xd', 'D'),     # 0x3A SRL (IX+d),D
            partial(self.shift, 23, 4, 3, 1, 'Xd', 'E'),     # 0x3B SRL (IX+d),E
            partial(self.shift, 23, 4, 3, 1, 'Xd', 'H'),     # 0x3C SRL (IX+d),H
            partial(self.shift, 23, 4, 3, 1, 'Xd', 'L'),     # 0x3D SRL (IX+d),L
            partial(self.shift, 23, 4, 3, 1, 'Xd'),          # 0x3E SRL (IX+d)
            partial(self.shift, 23, 4, 3, 1, 'Xd', 'A'),     # 0x3F SRL (IX+d),A
            partial(self.bit, 20, 4, 1, 'Xd'),               # 0x40 BIT 0,(IX+d)
            partial(self.bit, 20, 4, 1, 'Xd'),               # 0x41 BIT 0,(IX+d)
            partial(self.bit, 20, 4, 1, 'Xd'),               # 0x42 BIT 0,(IX+d)
            partial(self.bit, 20, 4, 1, 'Xd'),               # 0x43 BIT 0,(IX+d)
            partial(self.bit, 20, 4, 1, 'Xd'),               # 0x44 BIT 0,(IX+d)
            partial(self.bit, 20, 4, 1, 'Xd'),               # 0x45 BIT 0,(IX+d)
            partial(self.bit, 20, 4, 1, 'Xd'),               # 0x46 BIT 0,(IX+d)
            partial(self.bit, 20, 4, 1, 'Xd'),               # 0x47 BIT 0,(IX+d)
            partial(self.bit, 20, 4, 2, 'Xd'),               # 0x48 BIT 1,(IX+d)
            partial(self.bit, 20, 4, 2, 'Xd'),               # 0x49 BIT 1,(IX+d)
            partial(self.bit, 20, 4, 2, 'Xd'),               # 0x4A BIT 1,(IX+d)
            partial(self.bit, 20, 4, 2, 'Xd'),               # 0x4B BIT 1,(IX+d)
            partial(self.bit, 20, 4, 2, 'Xd'),               # 0x4C BIT 1,(IX+d)
            partial(self.bit, 20, 4, 2, 'Xd'),               # 0x4D BIT 1,(IX+d)
            partial(self.bit, 20, 4, 2, 'Xd'),               # 0x4E BIT 1,(IX+d)
            partial(self.bit, 20, 4, 2, 'Xd'),               # 0x4F BIT 1,(IX+d)
            partial(self.bit, 20, 4, 4, 'Xd'),               # 0x50 BIT 2,(IX+d)
            partial(self.bit, 20, 4, 4, 'Xd'),               # 0x51 BIT 2,(IX+d)
            partial(self.bit, 20, 4, 4, 'Xd'),               # 0x52 BIT 2,(IX+d)
            partial(self.bit, 20, 4, 4, 'Xd'),               # 0x53 BIT 2,(IX+d)
            partial(self.bit, 20, 4, 4, 'Xd'),               # 0x54 BIT 2,(IX+d)
            partial(self.bit, 20, 4, 4, 'Xd'),               # 0x55 BIT 2,(IX+d)
            partial(self.bit, 20, 4, 4, 'Xd'),               # 0x56 BIT 2,(IX+d)
            partial(self.bit, 20, 4, 4, 'Xd'),               # 0x57 BIT 2,(IX+d)
            partial(self.bit, 20, 4, 8, 'Xd'),               # 0x58 BIT 3,(IX+d)
            partial(self.bit, 20, 4, 8, 'Xd'),               # 0x59 BIT 3,(IX+d)
            partial(self.bit, 20, 4, 8, 'Xd'),               # 0x5A BIT 3,(IX+d)
            partial(self.bit, 20, 4, 8, 'Xd'),               # 0x5B BIT 3,(IX+d)
            partial(self.bit, 20, 4, 8, 'Xd'),               # 0x5C BIT 3,(IX+d)
            partial(self.bit, 20, 4, 8, 'Xd'),               # 0x5D BIT 3,(IX+d)
            partial(self.bit, 20, 4, 8, 'Xd'),               # 0x5E BIT 3,(IX+d)
            partial(self.bit, 20, 4, 8, 'Xd'),               # 0x5F BIT 3,(IX+d)
            partial(self.bit, 20, 4, 16, 'Xd'),              # 0x60 BIT 4,(IX+d)
            partial(self.bit, 20, 4, 16, 'Xd'),              # 0x61 BIT 4,(IX+d)
            partial(self.bit, 20, 4, 16, 'Xd'),              # 0x62 BIT 4,(IX+d)
            partial(self.bit, 20, 4, 16, 'Xd'),              # 0x63 BIT 4,(IX+d)
            partial(self.bit, 20, 4, 16, 'Xd'),              # 0x64 BIT 4,(IX+d)
            partial(self.bit, 20, 4, 16, 'Xd'),              # 0x65 BIT 4,(IX+d)
            partial(self.bit, 20, 4, 16, 'Xd'),              # 0x66 BIT 4,(IX+d)
            partial(self.bit, 20, 4, 16, 'Xd'),              # 0x67 BIT 4,(IX+d)
            partial(self.bit, 20, 4, 32, 'Xd'),              # 0x68 BIT 5,(IX+d)
            partial(self.bit, 20, 4, 32, 'Xd'),              # 0x69 BIT 5,(IX+d)
            partial(self.bit, 20, 4, 32, 'Xd'),              # 0x6A BIT 5,(IX+d)
            partial(self.bit, 20, 4, 32, 'Xd'),              # 0x6B BIT 5,(IX+d)
            partial(self.bit, 20, 4, 32, 'Xd'),              # 0x6C BIT 5,(IX+d)
            partial(self.bit, 20, 4, 32, 'Xd'),              # 0x6D BIT 5,(IX+d)
            partial(self.bit, 20, 4, 32, 'Xd'),              # 0x6E BIT 5,(IX+d)
            partial(self.bit, 20, 4, 32, 'Xd'),              # 0x6F BIT 5,(IX+d)
            partial(self.bit, 20, 4, 64, 'Xd'),              # 0x70 BIT 6,(IX+d)
            partial(self.bit, 20, 4, 64, 'Xd'),              # 0x71 BIT 6,(IX+d)
            partial(self.bit, 20, 4, 64, 'Xd'),              # 0x72 BIT 6,(IX+d)
            partial(self.bit, 20, 4, 64, 'Xd'),              # 0x73 BIT 6,(IX+d)
            partial(self.bit, 20, 4, 64, 'Xd'),              # 0x74 BIT 6,(IX+d)
            partial(self.bit, 20, 4, 64, 'Xd'),              # 0x75 BIT 6,(IX+d)
            partial(self.bit, 20, 4, 64, 'Xd'),              # 0x76 BIT 6,(IX+d)
            partial(self.bit, 20, 4, 64, 'Xd'),              # 0x77 BIT 6,(IX+d)
            partial(self.bit, 20, 4, 128, 'Xd'),             # 0x78 BIT 7,(IX+d)
            partial(self.bit, 20, 4, 128, 'Xd'),             # 0x79 BIT 7,(IX+d)
            partial(self.bit, 20, 4, 128, 'Xd'),             # 0x7A BIT 7,(IX+d)
            partial(self.bit, 20, 4, 128, 'Xd'),             # 0x7B BIT 7,(IX+d)
            partial(self.bit, 20, 4, 128, 'Xd'),             # 0x7C BIT 7,(IX+d)
            partial(self.bit, 20, 4, 128, 'Xd'),             # 0x7D BIT 7,(IX+d)
            partial(self.bit, 20, 4, 128, 'Xd'),             # 0x7E BIT 7,(IX+d)
            partial(self.bit, 20, 4, 128, 'Xd'),             # 0x7F BIT 7,(IX+d)
            partial(self.res_set, 23, 4, 254, 'Xd', 0, 'B'), # 0x80 RES 0,(IX+d),B
            partial(self.res_set, 23, 4, 254, 'Xd', 0, 'C'), # 0x81 RES 0,(IX+d),C
            partial(self.res_set, 23, 4, 254, 'Xd', 0, 'D'), # 0x82 RES 0,(IX+d),D
            partial(self.res_set, 23, 4, 254, 'Xd', 0, 'E'), # 0x83 RES 0,(IX+d),E
            partial(self.res_set, 23, 4, 254, 'Xd', 0, 'H'), # 0x84 RES 0,(IX+d),H
            partial(self.res_set, 23, 4, 254, 'Xd', 0, 'L'), # 0x85 RES 0,(IX+d),L
            partial(self.res_set, 23, 4, 254, 'Xd', 0),      # 0x86 RES 0,(IX+d)
            partial(self.res_set, 23, 4, 254, 'Xd', 0, 'A'), # 0x87 RES 0,(IX+d),A
            partial(self.res_set, 23, 4, 253, 'Xd', 0, 'B'), # 0x88 RES 1,(IX+d),B
            partial(self.res_set, 23, 4, 253, 'Xd', 0, 'C'), # 0x89 RES 1,(IX+d),C
            partial(self.res_set, 23, 4, 253, 'Xd', 0, 'D'), # 0x8A RES 1,(IX+d),D
            partial(self.res_set, 23, 4, 253, 'Xd', 0, 'E'), # 0x8B RES 1,(IX+d),E
            partial(self.res_set, 23, 4, 253, 'Xd', 0, 'H'), # 0x8C RES 1,(IX+d),H
            partial(self.res_set, 23, 4, 253, 'Xd', 0, 'L'), # 0x8D RES 1,(IX+d),L
            partial(self.res_set, 23, 4, 253, 'Xd', 0),      # 0x8E RES 1,(IX+d)
            partial(self.res_set, 23, 4, 253, 'Xd', 0, 'A'), # 0x8F RES 1,(IX+d),A
            partial(self.res_set, 23, 4, 251, 'Xd', 0, 'B'), # 0x90 RES 2,(IX+d),B
            partial(self.res_set, 23, 4, 251, 'Xd', 0, 'C'), # 0x91 RES 2,(IX+d),C
            partial(self.res_set, 23, 4, 251, 'Xd', 0, 'D'), # 0x92 RES 2,(IX+d),D
            partial(self.res_set, 23, 4, 251, 'Xd', 0, 'E'), # 0x93 RES 2,(IX+d),E
            partial(self.res_set, 23, 4, 251, 'Xd', 0, 'H'), # 0x94 RES 2,(IX+d),H
            partial(self.res_set, 23, 4, 251, 'Xd', 0, 'L'), # 0x95 RES 2,(IX+d),L
            partial(self.res_set, 23, 4, 251, 'Xd', 0),      # 0x96 RES 2,(IX+d)
            partial(self.res_set, 23, 4, 251, 'Xd', 0, 'A'), # 0x97 RES 2,(IX+d),A
            partial(self.res_set, 23, 4, 247, 'Xd', 0, 'B'), # 0x98 RES 3,(IX+d),B
            partial(self.res_set, 23, 4, 247, 'Xd', 0, 'C'), # 0x99 RES 3,(IX+d),C
            partial(self.res_set, 23, 4, 247, 'Xd', 0, 'D'), # 0x9A RES 3,(IX+d),D
            partial(self.res_set, 23, 4, 247, 'Xd', 0, 'E'), # 0x9B RES 3,(IX+d),E
            partial(self.res_set, 23, 4, 247, 'Xd', 0, 'H'), # 0x9C RES 3,(IX+d),H
            partial(self.res_set, 23, 4, 247, 'Xd', 0, 'L'), # 0x9D RES 3,(IX+d),L
            partial(self.res_set, 23, 4, 247, 'Xd', 0),      # 0x9E RES 3,(IX+d)
            partial(self.res_set, 23, 4, 247, 'Xd', 0, 'A'), # 0x9F RES 3,(IX+d),A
            partial(self.res_set, 23, 4, 239, 'Xd', 0, 'B'), # 0xA0 RES 4,(IX+d),B
            partial(self.res_set, 23, 4, 239, 'Xd', 0, 'C'), # 0xA1 RES 4,(IX+d),C
            partial(self.res_set, 23, 4, 239, 'Xd', 0, 'D'), # 0xA2 RES 4,(IX+d),D
            partial(self.res_set, 23, 4, 239, 'Xd', 0, 'E'), # 0xA3 RES 4,(IX+d),E
            partial(self.res_set, 23, 4, 239, 'Xd', 0, 'H'), # 0xA4 RES 4,(IX+d),H
            partial(self.res_set, 23, 4, 239, 'Xd', 0, 'L'), # 0xA5 RES 4,(IX+d),L
            partial(self.res_set, 23, 4, 239, 'Xd', 0),      # 0xA6 RES 4,(IX+d)
            partial(self.res_set, 23, 4, 239, 'Xd', 0, 'A'), # 0xA7 RES 4,(IX+d),A
            partial(self.res_set, 23, 4, 223, 'Xd', 0, 'B'), # 0xA8 RES 5,(IX+d),B
            partial(self.res_set, 23, 4, 223, 'Xd', 0, 'C'), # 0xA9 RES 5,(IX+d),C
            partial(self.res_set, 23, 4, 223, 'Xd', 0, 'D'), # 0xAA RES 5,(IX+d),D
            partial(self.res_set, 23, 4, 223, 'Xd', 0, 'E'), # 0xAB RES 5,(IX+d),E
            partial(self.res_set, 23, 4, 223, 'Xd', 0, 'H'), # 0xAC RES 5,(IX+d),H
            partial(self.res_set, 23, 4, 223, 'Xd', 0, 'L'), # 0xAD RES 5,(IX+d),L
            partial(self.res_set, 23, 4, 223, 'Xd', 0),      # 0xAE RES 5,(IX+d)
            partial(self.res_set, 23, 4, 223, 'Xd', 0, 'A'), # 0xAF RES 5,(IX+d),A
            partial(self.res_set, 23, 4, 191, 'Xd', 0, 'B'), # 0xB0 RES 6,(IX+d),B
            partial(self.res_set, 23, 4, 191, 'Xd', 0, 'C'), # 0xB1 RES 6,(IX+d),C
            partial(self.res_set, 23, 4, 191, 'Xd', 0, 'D'), # 0xB2 RES 6,(IX+d),D
            partial(self.res_set, 23, 4, 191, 'Xd', 0, 'E'), # 0xB3 RES 6,(IX+d),E
            partial(self.res_set, 23, 4, 191, 'Xd', 0, 'H'), # 0xB4 RES 6,(IX+d),H
            partial(self.res_set, 23, 4, 191, 'Xd', 0, 'L'), # 0xB5 RES 6,(IX+d),L
            partial(self.res_set, 23, 4, 191, 'Xd', 0),      # 0xB6 RES 6,(IX+d)
            partial(self.res_set, 23, 4, 191, 'Xd', 0, 'A'), # 0xB7 RES 6,(IX+d),A
            partial(self.res_set, 23, 4, 127, 'Xd', 0, 'B'), # 0xB8 RES 7,(IX+d),B
            partial(self.res_set, 23, 4, 127, 'Xd', 0, 'C'), # 0xB9 RES 7,(IX+d),C
            partial(self.res_set, 23, 4, 127, 'Xd', 0, 'D'), # 0xBA RES 7,(IX+d),D
            partial(self.res_set, 23, 4, 127, 'Xd', 0, 'E'), # 0xBB RES 7,(IX+d),E
            partial(self.res_set, 23, 4, 127, 'Xd', 0, 'H'), # 0xBC RES 7,(IX+d),H
            partial(self.res_set, 23, 4, 127, 'Xd', 0, 'L'), # 0xBD RES 7,(IX+d),L
            partial(self.res_set, 23, 4, 127, 'Xd', 0),      # 0xBE RES 7,(IX+d)
            partial(self.res_set, 23, 4, 127, 'Xd', 0, 'A'), # 0xBF RES 7,(IX+d),A
            partial(self.res_set, 23, 4, 1, 'Xd', 1, 'B'),   # 0xC0 SET 0,(IX+d),B
            partial(self.res_set, 23, 4, 1, 'Xd', 1, 'C'),   # 0xC1 SET 0,(IX+d),C
            partial(self.res_set, 23, 4, 1, 'Xd', 1, 'D'),   # 0xC2 SET 0,(IX+d),D
            partial(self.res_set, 23, 4, 1, 'Xd', 1, 'E'),   # 0xC3 SET 0,(IX+d),E
            partial(self.res_set, 23, 4, 1, 'Xd', 1, 'H'),   # 0xC4 SET 0,(IX+d),H
            partial(self.res_set, 23, 4, 1, 'Xd', 1, 'L'),   # 0xC5 SET 0,(IX+d),L
            partial(self.res_set, 23, 4, 1, 'Xd', 1),        # 0xC6 SET 0,(IX+d)
            partial(self.res_set, 23, 4, 1, 'Xd', 1, 'A'),   # 0xC7 SET 0,(IX+d),A
            partial(self.res_set, 23, 4, 2, 'Xd', 1, 'B'),   # 0xC8 SET 1,(IX+d),B
            partial(self.res_set, 23, 4, 2, 'Xd', 1, 'C'),   # 0xC9 SET 1,(IX+d),C
            partial(self.res_set, 23, 4, 2, 'Xd', 1, 'D'),   # 0xCA SET 1,(IX+d),D
            partial(self.res_set, 23, 4, 2, 'Xd', 1, 'E'),   # 0xCB SET 1,(IX+d),E
            partial(self.res_set, 23, 4, 2, 'Xd', 1, 'H'),   # 0xCC SET 1,(IX+d),H
            partial(self.res_set, 23, 4, 2, 'Xd', 1, 'L'),   # 0xCD SET 1,(IX+d),L
            partial(self.res_set, 23, 4, 2, 'Xd', 1),        # 0xCE SET 1,(IX+d)
            partial(self.res_set, 23, 4, 2, 'Xd', 1, 'A'),   # 0xCF SET 1,(IX+d),A
            partial(self.res_set, 23, 4, 4, 'Xd', 1, 'B'),   # 0xD0 SET 2,(IX+d),B
            partial(self.res_set, 23, 4, 4, 'Xd', 1, 'C'),   # 0xD1 SET 2,(IX+d),C
            partial(self.res_set, 23, 4, 4, 'Xd', 1, 'D'),   # 0xD2 SET 2,(IX+d),D
            partial(self.res_set, 23, 4, 4, 'Xd', 1, 'E'),   # 0xD3 SET 2,(IX+d),E
            partial(self.res_set, 23, 4, 4, 'Xd', 1, 'H'),   # 0xD4 SET 2,(IX+d),H
            partial(self.res_set, 23, 4, 4, 'Xd', 1, 'L'),   # 0xD5 SET 2,(IX+d),L
            partial(self.res_set, 23, 4, 4, 'Xd', 1),        # 0xD6 SET 2,(IX+d)
            partial(self.res_set, 23, 4, 4, 'Xd', 1, 'A'),   # 0xD7 SET 2,(IX+d),A
            partial(self.res_set, 23, 4, 8, 'Xd', 1, 'B'),   # 0xD8 SET 3,(IX+d),B
            partial(self.res_set, 23, 4, 8, 'Xd', 1, 'C'),   # 0xD9 SET 3,(IX+d),C
            partial(self.res_set, 23, 4, 8, 'Xd', 1, 'D'),   # 0xDA SET 3,(IX+d),D
            partial(self.res_set, 23, 4, 8, 'Xd', 1, 'E'),   # 0xDB SET 3,(IX+d),E
            partial(self.res_set, 23, 4, 8, 'Xd', 1, 'H'),   # 0xDC SET 3,(IX+d),H
            partial(self.res_set, 23, 4, 8, 'Xd', 1, 'L'),   # 0xDD SET 3,(IX+d),L
            partial(self.res_set, 23, 4, 8, 'Xd', 1),        # 0xDE SET 3,(IX+d)
            partial(self.res_set, 23, 4, 8, 'Xd', 1, 'A'),   # 0xDF SET 3,(IX+d),A
            partial(self.res_set, 23, 4, 16, 'Xd', 1, 'B'),  # 0xE0 SET 4,(IX+d),B
            partial(self.res_set, 23, 4, 16, 'Xd', 1, 'C'),  # 0xE1 SET 4,(IX+d),C
            partial(self.res_set, 23, 4, 16, 'Xd', 1, 'D'),  # 0xE2 SET 4,(IX+d),D
            partial(self.res_set, 23, 4, 16, 'Xd', 1, 'E'),  # 0xE3 SET 4,(IX+d),E
            partial(self.res_set, 23, 4, 16, 'Xd', 1, 'H'),  # 0xE4 SET 4,(IX+d),H
            partial(self.res_set, 23, 4, 16, 'Xd', 1, 'L'),  # 0xE5 SET 4,(IX+d),L
            partial(self.res_set, 23, 4, 16, 'Xd', 1),       # 0xE6 SET 4,(IX+d)
            partial(self.res_set, 23, 4, 16, 'Xd', 1, 'A'),  # 0xE7 SET 4,(IX+d),A
            partial(self.res_set, 23, 4, 32, 'Xd', 1, 'B'),  # 0xE8 SET 5,(IX+d),B
            partial(self.res_set, 23, 4, 32, 'Xd', 1, 'C'),  # 0xE9 SET 5,(IX+d),C
            partial(self.res_set, 23, 4, 32, 'Xd', 1, 'D'),  # 0xEA SET 5,(IX+d),D
            partial(self.res_set, 23, 4, 32, 'Xd', 1, 'E'),  # 0xEB SET 5,(IX+d),E
            partial(self.res_set, 23, 4, 32, 'Xd', 1, 'H'),  # 0xEC SET 5,(IX+d),H
            partial(self.res_set, 23, 4, 32, 'Xd', 1, 'L'),  # 0xED SET 5,(IX+d),L
            partial(self.res_set, 23, 4, 32, 'Xd', 1),       # 0xEE SET 5,(IX+d)
            partial(self.res_set, 23, 4, 32, 'Xd', 1, 'A'),  # 0xEF SET 5,(IX+d),A
            partial(self.res_set, 23, 4, 64, 'Xd', 1, 'B'),  # 0xF0 SET 6,(IX+d),B
            partial(self.res_set, 23, 4, 64, 'Xd', 1, 'C'),  # 0xF1 SET 6,(IX+d),C
            partial(self.res_set, 23, 4, 64, 'Xd', 1, 'D'),  # 0xF2 SET 6,(IX+d),D
            partial(self.res_set, 23, 4, 64, 'Xd', 1, 'E'),  # 0xF3 SET 6,(IX+d),E
            partial(self.res_set, 23, 4, 64, 'Xd', 1, 'H'),  # 0xF4 SET 6,(IX+d),H
            partial(self.res_set, 23, 4, 64, 'Xd', 1, 'L'),  # 0xF5 SET 6,(IX+d),L
            partial(self.res_set, 23, 4, 64, 'Xd', 1),       # 0xF6 SET 6,(IX+d)
            partial(self.res_set, 23, 4, 64, 'Xd', 1, 'A'),  # 0xF7 SET 6,(IX+d),A
            partial(self.res_set, 23, 4, 128, 'Xd', 1, 'B'), # 0xF8 SET 7,(IX+d),B
            partial(self.res_set, 23, 4, 128, 'Xd', 1, 'C'), # 0xF9 SET 7,(IX+d),C
            partial(self.res_set, 23, 4, 128, 'Xd', 1, 'D'), # 0xFA SET 7,(IX+d),D
            partial(self.res_set, 23, 4, 128, 'Xd', 1, 'E'), # 0xFB SET 7,(IX+d),E
            partial(self.res_set, 23, 4, 128, 'Xd', 1, 'H'), # 0xFC SET 7,(IX+d),H
            partial(self.res_set, 23, 4, 128, 'Xd', 1, 'L'), # 0xFD SET 7,(IX+d),L
            partial(self.res_set, 23, 4, 128, 'Xd', 1),      # 0xFE SET 7,(IX+d)
            partial(self.res_set, 23, 4, 128, 'Xd', 1, 'A'), # 0xFF SET 7,(IX+d),A
        ]

        self.after_FD = [
            partial(self.defb, 4, 1),                        # 0x00
            partial(self.defb, 4, 1),                        # 0x01
            partial(self.defb, 4, 1),                        # 0x02
            partial(self.defb, 4, 1),                        # 0x03
            partial(self.defb, 4, 1),                        # 0x04
            partial(self.defb, 4, 1),                        # 0x05
            partial(self.defb, 4, 1),                        # 0x06
            partial(self.defb, 4, 1),                        # 0x07
            partial(self.defb, 4, 1),                        # 0x08
            partial(self.add16, 15, 2, 'IY', 'BC'),          # 0x09 ADD IY,BC
            partial(self.defb, 4, 1),                        # 0x0A
            partial(self.defb, 4, 1),                        # 0x0B
            partial(self.defb, 4, 1),                        # 0x0C
            partial(self.defb, 4, 1),                        # 0x0D
            partial(self.defb, 4, 1),                        # 0x0E
            partial(self.defb, 4, 1),                        # 0x0F
            partial(self.defb, 4, 1),                        # 0x10
            partial(self.defb, 4, 1),                        # 0x11
            partial(self.defb, 4, 1),                        # 0x12
            partial(self.defb, 4, 1),                        # 0x13
            partial(self.defb, 4, 1),                        # 0x14
            partial(self.defb, 4, 1),                        # 0x15
            partial(self.defb, 4, 1),                        # 0x16
            partial(self.defb, 4, 1),                        # 0x17
            partial(self.defb, 4, 1),                        # 0x18
            partial(self.add16, 15, 2, 'IY', 'DE'),          # 0x19 ADD IY,DE
            partial(self.defb, 4, 1),                        # 0x1A
            partial(self.defb, 4, 1),                        # 0x1B
            partial(self.defb, 4, 1),                        # 0x1C
            partial(self.defb, 4, 1),                        # 0x1D
            partial(self.defb, 4, 1),                        # 0x1E
            partial(self.defb, 4, 1),                        # 0x1F
            partial(self.defb, 4, 1),                        # 0x20
            partial(self.ld16, 'IY'),                        # 0x21 LD IY,nn
            partial(self.ld16addr, 20, 4, 'IY', 1),          # 0x22 LD (nn),IY
            partial(self.inc_dec16, 1, 'IY'),                # 0x23 INC IY
            partial(self.inc_dec8, 8, 2, 1, 'IYh'),          # 0x24 INC IYh
            partial(self.inc_dec8, 8, 2, -1, 'IYh'),         # 0x25 DEC IYh
            partial(self.ld8, 11, 3, 'IYh'),                 # 0x26 LD IYh,n
            partial(self.defb, 4, 1),                        # 0x27
            partial(self.defb, 4, 1),                        # 0x28
            partial(self.add16, 15, 2, 'IY', 'IY'),          # 0x29 ADD IY,IY
            partial(self.ld16addr, 20, 4, 'IY', 0),          # 0x2A LD IY,(nn)
            partial(self.inc_dec16, -1, 'IY'),               # 0x2B DEC IY
            partial(self.inc_dec8, 8, 2, 1, 'IYl'),          # 0x2C INC IYl
            partial(self.inc_dec8, 8, 2, -1, 'IYl'),         # 0x2D DEC IYl
            partial(self.ld8, 11, 3, 'IYl'),                 # 0x2E LD IYl,n
            partial(self.defb, 4, 1),                        # 0x2F
            partial(self.defb, 4, 1),                        # 0x30
            partial(self.defb, 4, 1),                        # 0x31
            partial(self.defb, 4, 1),                        # 0x32
            partial(self.defb, 4, 1),                        # 0x33
            partial(self.inc_dec8, 23, 3, 1, 'Yd'),          # 0x34 INC (IY+d)
            partial(self.inc_dec8, 23, 3, -1, 'Yd'),         # 0x35 DEC (IY+d)
            partial(self.ld8, 19, 4, 'Yd'),                  # 0x36 LD (IY+d),n
            partial(self.defb, 4, 1),                        # 0x37
            partial(self.defb, 4, 1),                        # 0x38
            partial(self.add16, 15, 2, 'IY', 'SP'),          # 0x39 ADD IY,SP
            partial(self.defb, 4, 1),                        # 0x3A
            partial(self.defb, 4, 1),                        # 0x3B
            partial(self.defb, 4, 1),                        # 0x3C
            partial(self.defb, 4, 1),                        # 0x3D
            partial(self.defb, 4, 1),                        # 0x3E
            partial(self.defb, 4, 1),                        # 0x3F
            partial(self.defb, 4, 1),                        # 0x40
            partial(self.defb, 4, 1),                        # 0x41
            partial(self.defb, 4, 1),                        # 0x42
            partial(self.defb, 4, 1),                        # 0x43
            partial(self.ld8, 8, 2, 'B', 'IYh'),             # 0x44 LD B,IYh
            partial(self.ld8, 8, 2, 'B', 'IYl'),             # 0x45 LD B,IYl
            partial(self.ld8, 19, 3, 'B', 'Yd'),             # 0x46 LD B,(IY+d)
            partial(self.defb, 4, 1),                        # 0x47
            partial(self.defb, 4, 1),                        # 0x48
            partial(self.defb, 4, 1),                        # 0x49
            partial(self.defb, 4, 1),                        # 0x4A
            partial(self.defb, 4, 1),                        # 0x4B
            partial(self.ld8, 8, 2, 'C', 'IYh'),             # 0x4C LD C,IYh
            partial(self.ld8, 8, 2, 'C', 'IYl'),             # 0x4D LD C,IYl
            partial(self.ld8, 19, 3, 'C', 'Yd'),             # 0x4E LD C,(IY+d)
            partial(self.defb, 4, 1),                        # 0x4F
            partial(self.defb, 4, 1),                        # 0x50
            partial(self.defb, 4, 1),                        # 0x51
            partial(self.defb, 4, 1),                        # 0x52
            partial(self.defb, 4, 1),                        # 0x53
            partial(self.ld8, 8, 2, 'D', 'IYh'),             # 0x54 LD D,IYh
            partial(self.ld8, 8, 2, 'D', 'IYl'),             # 0x55 LD D,IYl
            partial(self.ld8, 19, 3, 'D', 'Yd'),             # 0x56 LD D,(IY+d)
            partial(self.defb, 4, 1),                        # 0x57
            partial(self.defb, 4, 1),                        # 0x58
            partial(self.defb, 4, 1),                        # 0x59
            partial(self.defb, 4, 1),                        # 0x5A
            partial(self.defb, 4, 1),                        # 0x5B
            partial(self.ld8, 8, 2, 'E', 'IYh'),             # 0x5C LD E,IYh
            partial(self.ld8, 8, 2, 'E', 'IYl'),             # 0x5D LD E,IYl
            partial(self.ld8, 19, 3, 'E', 'Yd'),             # 0x5E LD E,(IY+d)
            partial(self.defb, 4, 1),                        # 0x5F
            partial(self.ld8, 8, 2, 'IYh', 'B'),             # 0x60 LD IYh,B
            partial(self.ld8, 8, 2, 'IYh', 'C'),             # 0x61 LD IYh,C
            partial(self.ld8, 8, 2, 'IYh', 'D'),             # 0x62 LD IYh,D
            partial(self.ld8, 8, 2, 'IYh', 'E'),             # 0x63 LD IYh,E
            partial(self.ld8, 8, 2, 'IYh', 'IYh'),           # 0x64 LD IYh,IYh
            partial(self.ld8, 8, 2, 'IYh', 'IYl'),           # 0x65 LD IYh,IYl
            partial(self.ld8, 19, 3, 'H', 'Yd'),             # 0x66 LD H,(IY+d)
            partial(self.ld8, 8, 2, 'IYh', 'A'),             # 0x67 LD IYh,A
            partial(self.ld8, 8, 2, 'IYl', 'B'),             # 0x68 LD IYl,B
            partial(self.ld8, 8, 2, 'IYl', 'C'),             # 0x69 LD IYl,C
            partial(self.ld8, 8, 2, 'IYl', 'D'),             # 0x6A LD IYl,D
            partial(self.ld8, 8, 2, 'IYl', 'E'),             # 0x6B LD IYl,E
            partial(self.ld8, 8, 2, 'IYl', 'IYh'),           # 0x6C LD IYl,IYh
            partial(self.ld8, 8, 2, 'IYl', 'IYl'),           # 0x6D LD IYl,IYl
            partial(self.ld8, 19, 3, 'L', 'Yd'),             # 0x6E LD L,(IY+d)
            partial(self.ld8, 8, 2, 'IYl', 'A'),             # 0x6F LD IYl,A
            partial(self.ld8, 19, 3, 'Yd', 'B'),             # 0x70 LD (IY+d),B
            partial(self.ld8, 19, 3, 'Yd', 'C'),             # 0x71 LD (IY+d),C
            partial(self.ld8, 19, 3, 'Yd', 'D'),             # 0x72 LD (IY+d),D
            partial(self.ld8, 19, 3, 'Yd', 'E'),             # 0x73 LD (IY+d),E
            partial(self.ld8, 19, 3, 'Yd', 'H'),             # 0x74 LD (IY+d),H
            partial(self.ld8, 19, 3, 'Yd', 'L'),             # 0x75 LD (IY+d),L
            partial(self.defb, 4, 1),                        # 0x76
            partial(self.ld8, 19, 3, 'Yd', 'A'),             # 0x77 LD (IY+d),A
            partial(self.defb, 4, 1),                        # 0x78
            partial(self.defb, 4, 1),                        # 0x79
            partial(self.defb, 4, 1),                        # 0x7A
            partial(self.defb, 4, 1),                        # 0x7B
            partial(self.ld8, 8, 2, 'A', 'IYh'),             # 0x7C LD A,IYh
            partial(self.ld8, 8, 2, 'A', 'IYl'),             # 0x7D LD A,IYl
            partial(self.ld8, 19, 3, 'A', 'Yd'),             # 0x7E LD A,(IY+d)
            partial(self.defb, 4, 1),                        # 0x7F
            partial(self.defb, 4, 1),                        # 0x80
            partial(self.defb, 4, 1),                        # 0x81
            partial(self.defb, 4, 1),                        # 0x82
            partial(self.defb, 4, 1),                        # 0x83
            partial(self.add_a, 8, 2, 'IYh'),                # 0x84 ADD A,IYh
            partial(self.add_a, 8, 2, 'IYl'),                # 0x85 ADD A,IYl
            partial(self.add_a, 19, 3, 'Yd'),                # 0x86 ADD A,(IY+d)
            partial(self.defb, 4, 1),                        # 0x87
            partial(self.defb, 4, 1),                        # 0x88
            partial(self.defb, 4, 1),                        # 0x89
            partial(self.defb, 4, 1),                        # 0x8A
            partial(self.defb, 4, 1),                        # 0x8B
            partial(self.add_a, 8, 2, 'IYh', 1),             # 0x8C ADC A,IYh
            partial(self.add_a, 8, 2, 'IYl', 1),             # 0x8D ADC A,IYl
            partial(self.add_a, 19, 3, 'Yd', 1),             # 0x8E ADC A,(IY+d)
            partial(self.defb, 4, 1),                        # 0x8F
            partial(self.defb, 4, 1),                        # 0x90
            partial(self.defb, 4, 1),                        # 0x91
            partial(self.defb, 4, 1),                        # 0x92
            partial(self.defb, 4, 1),                        # 0x93
            partial(self.add_a, 8, 2, 'IYh', 0, -1),         # 0x94 SUB IYh
            partial(self.add_a, 8, 2, 'IYl', 0, -1),         # 0x95 SUB IYl
            partial(self.add_a, 19, 3, 'Yd', 0, -1),         # 0x96 SUB (IY+d)
            partial(self.defb, 4, 1),                        # 0x97
            partial(self.defb, 4, 1),                        # 0x98
            partial(self.defb, 4, 1),                        # 0x99
            partial(self.defb, 4, 1),                        # 0x9A
            partial(self.defb, 4, 1),                        # 0x9B
            partial(self.add_a, 8, 2, 'IYh', 1, -1),         # 0x9C SBC A,IYh
            partial(self.add_a, 8, 2, 'IYl', 1, -1),         # 0x9D SBC A,IYl
            partial(self.add_a, 19, 3, 'Yd', 1, -1),         # 0x9E SBC A,(IY+d)
            partial(self.defb, 4, 1),                        # 0x9F
            partial(self.defb, 4, 1),                        # 0xA0
            partial(self.defb, 4, 1),                        # 0xA1
            partial(self.defb, 4, 1),                        # 0xA2
            partial(self.defb, 4, 1),                        # 0xA3
            partial(self.anda, 8, 2, 'IYh'),                 # 0xA4 AND IYh
            partial(self.anda, 8, 2, 'IYl'),                 # 0xA5 AND IYl
            partial(self.anda, 19, 3, 'Yd'),                 # 0xA6 AND (IY+d)
            partial(self.defb, 4, 1),                        # 0xA7
            partial(self.defb, 4, 1),                        # 0xA8
            partial(self.defb, 4, 1),                        # 0xA9
            partial(self.defb, 4, 1),                        # 0xAA
            partial(self.defb, 4, 1),                        # 0xAB
            partial(self.xor, 8, 2, 'IYh'),                  # 0xAC XOR IYh
            partial(self.xor, 8, 2, 'IYl'),                  # 0xAD XOR IYl
            partial(self.xor, 19, 3, 'Yd'),                  # 0xAE XOR (IY+d)
            partial(self.defb, 4, 1),                        # 0xAF
            partial(self.defb, 4, 1),                        # 0xB0
            partial(self.defb, 4, 1),                        # 0xB1
            partial(self.defb, 4, 1),                        # 0xB2
            partial(self.defb, 4, 1),                        # 0xB3
            partial(self.ora, 8, 2, 'IYh'),                  # 0xB4 OR IYh
            partial(self.ora, 8, 2, 'IYl'),                  # 0xB5 OR IYl
            partial(self.ora, 19, 3, 'Yd'),                  # 0xB6 OR (IY+d)
            partial(self.defb, 4, 1),                        # 0xB7
            partial(self.defb, 4, 1),                        # 0xB8
            partial(self.defb, 4, 1),                        # 0xB9
            partial(self.defb, 4, 1),                        # 0xBA
            partial(self.defb, 4, 1),                        # 0xBB
            partial(self.cp, 8, 2, 'IYh'),                   # 0xBC CP IYh
            partial(self.cp, 8, 2, 'IYl'),                   # 0xBD CP IYl
            partial(self.cp, 19, 3, 'Yd'),                   # 0xBE CP (IY+d)
            partial(self.defb, 4, 1),                        # 0xBF
            partial(self.defb, 4, 1),                        # 0xC0
            partial(self.defb, 4, 1),                        # 0xC1
            partial(self.defb, 4, 1),                        # 0xC2
            partial(self.defb, 4, 1),                        # 0xC3
            partial(self.defb, 4, 1),                        # 0xC4
            partial(self.defb, 4, 1),                        # 0xC5
            partial(self.defb, 4, 1),                        # 0xC6
            partial(self.defb, 4, 1),                        # 0xC7
            partial(self.defb, 4, 1),                        # 0xC8
            partial(self.defb, 4, 1),                        # 0xC9
            partial(self.defb, 4, 1),                        # 0xCA
            None,                                            # 0xCB FDCB prefix
            partial(self.defb, 4, 1),                        # 0xCC
            partial(self.defb, 4, 1),                        # 0xCD
            partial(self.defb, 4, 1),                        # 0xCE
            partial(self.defb, 4, 1),                        # 0xCF
            partial(self.defb, 4, 1),                        # 0xD0
            partial(self.defb, 4, 1),                        # 0xD1
            partial(self.defb, 4, 1),                        # 0xD2
            partial(self.defb, 4, 1),                        # 0xD3
            partial(self.defb, 4, 1),                        # 0xD4
            partial(self.defb, 4, 1),                        # 0xD5
            partial(self.defb, 4, 1),                        # 0xD6
            partial(self.defb, 4, 1),                        # 0xD7
            partial(self.defb, 4, 1),                        # 0xD8
            partial(self.defb, 4, 1),                        # 0xD9
            partial(self.defb, 4, 1),                        # 0xDA
            partial(self.defb, 4, 1),                        # 0xDB
            partial(self.defb, 4, 1),                        # 0xDC
            partial(self.defb, 4, 1),                        # 0xDD
            partial(self.defb, 4, 1),                        # 0xDE
            partial(self.defb, 4, 1),                        # 0xDF
            partial(self.defb, 4, 1),                        # 0xE0
            partial(self.pop, 'IY'),                         # 0xE1 POP IY
            partial(self.defb, 4, 1),                        # 0xE2
            partial(self.ex_sp, 'IY'),                       # 0xE3 EX (SP),IY
            partial(self.defb, 4, 1),                        # 0xE4
            partial(self.push, 'IY'),                        # 0xE5 PUSH IY
            partial(self.defb, 4, 1),                        # 0xE6
            partial(self.defb, 4, 1),                        # 0xE7
            partial(self.defb, 4, 1),                        # 0xE8
            partial(self.jp, 0, 0),                          # 0xE9 JP (IY)
            partial(self.defb, 4, 1),                        # 0xEA
            partial(self.defb, 4, 1),                        # 0xEB
            partial(self.defb, 4, 1),                        # 0xEC
            partial(self.defb, 4, 1),                        # 0xED
            partial(self.defb, 4, 1),                        # 0xEE
            partial(self.defb, 4, 1),                        # 0xEF
            partial(self.defb, 4, 1),                        # 0xF0
            partial(self.defb, 4, 1),                        # 0xF1
            partial(self.defb, 4, 1),                        # 0xF2
            partial(self.defb, 4, 1),                        # 0xF3
            partial(self.defb, 4, 1),                        # 0xF4
            partial(self.defb, 4, 1),                        # 0xF5
            partial(self.defb, 4, 1),                        # 0xF6
            partial(self.defb, 4, 1),                        # 0xF7
            partial(self.defb, 4, 1),                        # 0xF8
            partial(self.ldsprr, 'IY'),                      # 0xF9 LD SP,IY
            partial(self.defb, 4, 1),                        # 0xFA
            partial(self.defb, 4, 1),                        # 0xFB
            partial(self.defb, 4, 1),                        # 0xFC
            partial(self.defb, 4, 1),                        # 0xFD
            partial(self.defb, 4, 1),                        # 0xFE
            partial(self.defb, 4, 1),                        # 0xFF
        ]

        self.after_FDCB = [
            partial(self.rotate, 23, 4, 128, 'Yd', 1, 'B'),  # 0x00 RLC (IY+d),B
            partial(self.rotate, 23, 4, 128, 'Yd', 1, 'C'),  # 0x01 RLC (IY+d),C
            partial(self.rotate, 23, 4, 128, 'Yd', 1, 'D'),  # 0x02 RLC (IY+d),D
            partial(self.rotate, 23, 4, 128, 'Yd', 1, 'E'),  # 0x03 RLC (IY+d),E
            partial(self.rotate, 23, 4, 128, 'Yd', 1, 'H'),  # 0x04 RLC (IY+d),H
            partial(self.rotate, 23, 4, 128, 'Yd', 1, 'L'),  # 0x05 RLC (IY+d),L
            partial(self.rotate, 23, 4, 128, 'Yd', 1),       # 0x06 RLC (IY+d)
            partial(self.rotate, 23, 4, 128, 'Yd', 1, 'A'),  # 0x07 RLC (IY+d),A
            partial(self.rotate, 23, 4, 1, 'Yd', 1, 'B'),    # 0x08 RRC (IY+d),B
            partial(self.rotate, 23, 4, 1, 'Yd', 1, 'C'),    # 0x09 RRC (IY+d),C
            partial(self.rotate, 23, 4, 1, 'Yd', 1, 'D'),    # 0x0A RRC (IY+d),D
            partial(self.rotate, 23, 4, 1, 'Yd', 1, 'E'),    # 0x0B RRC (IY+d),E
            partial(self.rotate, 23, 4, 1, 'Yd', 1, 'H'),    # 0x0C RRC (IY+d),H
            partial(self.rotate, 23, 4, 1, 'Yd', 1, 'L'),    # 0x0D RRC (IY+d),L
            partial(self.rotate, 23, 4, 1, 'Yd', 1),         # 0x0E RRC (IY+d)
            partial(self.rotate, 23, 4, 1, 'Yd', 1, 'A'),    # 0x0F RRC (IY+d),A
            partial(self.rotate, 23, 4, 128, 'Yd', 0, 'B'),  # 0x10 RL (IY+d),B
            partial(self.rotate, 23, 4, 128, 'Yd', 0, 'C'),  # 0x11 RL (IY+d),C
            partial(self.rotate, 23, 4, 128, 'Yd', 0, 'D'),  # 0x12 RL (IY+d),D
            partial(self.rotate, 23, 4, 128, 'Yd', 0, 'E'),  # 0x13 RL (IY+d),E
            partial(self.rotate, 23, 4, 128, 'Yd', 0, 'H'),  # 0x14 RL (IY+d),H
            partial(self.rotate, 23, 4, 128, 'Yd', 0, 'L'),  # 0x15 RL (IY+d),L
            partial(self.rotate, 23, 4, 128, 'Yd'),          # 0x16 RL (IY+d)
            partial(self.rotate, 23, 4, 128, 'Yd', 0, 'A'),  # 0x17 RL (IY+d),A
            partial(self.rotate, 23, 4, 1, 'Yd', 0, 'B'),    # 0x18 RR (IY+d),B
            partial(self.rotate, 23, 4, 1, 'Yd', 0, 'C'),    # 0x19 RR (IY+d),C
            partial(self.rotate, 23, 4, 1, 'Yd', 0, 'D'),    # 0x1A RR (IY+d),D
            partial(self.rotate, 23, 4, 1, 'Yd', 0, 'E'),    # 0x1B RR (IY+d),E
            partial(self.rotate, 23, 4, 1, 'Yd', 0, 'H'),    # 0x1C RR (IY+d),H
            partial(self.rotate, 23, 4, 1, 'Yd', 0, 'L'),    # 0x1D RR (IY+d),L
            partial(self.rotate, 23, 4, 1, 'Yd'),            # 0x1E RR (IY+d)
            partial(self.rotate, 23, 4, 1, 'Yd', 0, 'A'),    # 0x1F RR (IY+d),A
            partial(self.shift, 23, 4, 0, 128, 'Yd', 'B'),   # 0x20 SLA (IY+d),B
            partial(self.shift, 23, 4, 0, 128, 'Yd', 'C'),   # 0x21 SLA (IY+d),C
            partial(self.shift, 23, 4, 0, 128, 'Yd', 'D'),   # 0x22 SLA (IY+d),D
            partial(self.shift, 23, 4, 0, 128, 'Yd', 'E'),   # 0x23 SLA (IY+d),E
            partial(self.shift, 23, 4, 0, 128, 'Yd', 'H'),   # 0x24 SLA (IY+d),H
            partial(self.shift, 23, 4, 0, 128, 'Yd', 'L'),   # 0x25 SLA (IY+d),L
            partial(self.shift, 23, 4, 0, 128, 'Yd'),        # 0x26 SLA (IY+d)
            partial(self.shift, 23, 4, 0, 128, 'Yd', 'A'),   # 0x27 SLA (IY+d),A
            partial(self.shift, 23, 4, 1, 1, 'Yd', 'B'),     # 0x28 SRA (IY+d),B
            partial(self.shift, 23, 4, 1, 1, 'Yd', 'C'),     # 0x29 SRA (IY+d),C
            partial(self.shift, 23, 4, 1, 1, 'Yd', 'D'),     # 0x2A SRA (IY+d),D
            partial(self.shift, 23, 4, 1, 1, 'Yd', 'E'),     # 0x2B SRA (IY+d),E
            partial(self.shift, 23, 4, 1, 1, 'Yd', 'H'),     # 0x2C SRA (IY+d),H
            partial(self.shift, 23, 4, 1, 1, 'Yd', 'L'),     # 0x2D SRA (IY+d),L
            partial(self.shift, 23, 4, 1, 1, 'Yd'),          # 0x2E SRA (IY+d)
            partial(self.shift, 23, 4, 1, 1, 'Yd', 'A'),     # 0x2F SRA (IY+d),A
            partial(self.shift, 23, 4, 2, 128, 'Yd', 'B'),   # 0x30 SLL (IY+d),B
            partial(self.shift, 23, 4, 2, 128, 'Yd', 'C'),   # 0x31 SLL (IY+d),C
            partial(self.shift, 23, 4, 2, 128, 'Yd', 'D'),   # 0x32 SLL (IY+d),D
            partial(self.shift, 23, 4, 2, 128, 'Yd', 'E'),   # 0x33 SLL (IY+d),E
            partial(self.shift, 23, 4, 2, 128, 'Yd', 'H'),   # 0x34 SLL (IY+d),H
            partial(self.shift, 23, 4, 2, 128, 'Yd', 'L'),   # 0x35 SLL (IY+d),L
            partial(self.shift, 23, 4, 2, 128, 'Yd'),        # 0x36 SLL (IY+d)
            partial(self.shift, 23, 4, 2, 128, 'Yd', 'A'),   # 0x37 SLL (IY+d),A
            partial(self.shift, 23, 4, 3, 1, 'Yd', 'B'),     # 0x38 SRL (IY+d),B
            partial(self.shift, 23, 4, 3, 1, 'Yd', 'C'),     # 0x39 SRL (IY+d),C
            partial(self.shift, 23, 4, 3, 1, 'Yd', 'D'),     # 0x3A SRL (IY+d),D
            partial(self.shift, 23, 4, 3, 1, 'Yd', 'E'),     # 0x3B SRL (IY+d),E
            partial(self.shift, 23, 4, 3, 1, 'Yd', 'H'),     # 0x3C SRL (IY+d),H
            partial(self.shift, 23, 4, 3, 1, 'Yd', 'L'),     # 0x3D SRL (IY+d),L
            partial(self.shift, 23, 4, 3, 1, 'Yd'),          # 0x3E SRL (IY+d)
            partial(self.shift, 23, 4, 3, 1, 'Yd', 'A'),     # 0x3F SRL (IY+d),A
            partial(self.bit, 20, 4, 1, 'Yd'),               # 0x40 BIT 0,(IY+d)
            partial(self.bit, 20, 4, 1, 'Yd'),               # 0x41 BIT 0,(IY+d)
            partial(self.bit, 20, 4, 1, 'Yd'),               # 0x42 BIT 0,(IY+d)
            partial(self.bit, 20, 4, 1, 'Yd'),               # 0x43 BIT 0,(IY+d)
            partial(self.bit, 20, 4, 1, 'Yd'),               # 0x44 BIT 0,(IY+d)
            partial(self.bit, 20, 4, 1, 'Yd'),               # 0x45 BIT 0,(IY+d)
            partial(self.bit, 20, 4, 1, 'Yd'),               # 0x46 BIT 0,(IY+d)
            partial(self.bit, 20, 4, 1, 'Yd'),               # 0x47 BIT 0,(IY+d)
            partial(self.bit, 20, 4, 2, 'Yd'),               # 0x48 BIT 1,(IY+d)
            partial(self.bit, 20, 4, 2, 'Yd'),               # 0x49 BIT 1,(IY+d)
            partial(self.bit, 20, 4, 2, 'Yd'),               # 0x4A BIT 1,(IY+d)
            partial(self.bit, 20, 4, 2, 'Yd'),               # 0x4B BIT 1,(IY+d)
            partial(self.bit, 20, 4, 2, 'Yd'),               # 0x4C BIT 1,(IY+d)
            partial(self.bit, 20, 4, 2, 'Yd'),               # 0x4D BIT 1,(IY+d)
            partial(self.bit, 20, 4, 2, 'Yd'),               # 0x4E BIT 1,(IY+d)
            partial(self.bit, 20, 4, 2, 'Yd'),               # 0x4F BIT 1,(IY+d)
            partial(self.bit, 20, 4, 4, 'Yd'),               # 0x50 BIT 2,(IY+d)
            partial(self.bit, 20, 4, 4, 'Yd'),               # 0x51 BIT 2,(IY+d)
            partial(self.bit, 20, 4, 4, 'Yd'),               # 0x52 BIT 2,(IY+d)
            partial(self.bit, 20, 4, 4, 'Yd'),               # 0x53 BIT 2,(IY+d)
            partial(self.bit, 20, 4, 4, 'Yd'),               # 0x54 BIT 2,(IY+d)
            partial(self.bit, 20, 4, 4, 'Yd'),               # 0x55 BIT 2,(IY+d)
            partial(self.bit, 20, 4, 4, 'Yd'),               # 0x56 BIT 2,(IY+d)
            partial(self.bit, 20, 4, 4, 'Yd'),               # 0x57 BIT 2,(IY+d)
            partial(self.bit, 20, 4, 8, 'Yd'),               # 0x58 BIT 3,(IY+d)
            partial(self.bit, 20, 4, 8, 'Yd'),               # 0x59 BIT 3,(IY+d)
            partial(self.bit, 20, 4, 8, 'Yd'),               # 0x5A BIT 3,(IY+d)
            partial(self.bit, 20, 4, 8, 'Yd'),               # 0x5B BIT 3,(IY+d)
            partial(self.bit, 20, 4, 8, 'Yd'),               # 0x5C BIT 3,(IY+d)
            partial(self.bit, 20, 4, 8, 'Yd'),               # 0x5D BIT 3,(IY+d)
            partial(self.bit, 20, 4, 8, 'Yd'),               # 0x5E BIT 3,(IY+d)
            partial(self.bit, 20, 4, 8, 'Yd'),               # 0x5F BIT 3,(IY+d)
            partial(self.bit, 20, 4, 16, 'Yd'),              # 0x60 BIT 4,(IY+d)
            partial(self.bit, 20, 4, 16, 'Yd'),              # 0x61 BIT 4,(IY+d)
            partial(self.bit, 20, 4, 16, 'Yd'),              # 0x62 BIT 4,(IY+d)
            partial(self.bit, 20, 4, 16, 'Yd'),              # 0x63 BIT 4,(IY+d)
            partial(self.bit, 20, 4, 16, 'Yd'),              # 0x64 BIT 4,(IY+d)
            partial(self.bit, 20, 4, 16, 'Yd'),              # 0x65 BIT 4,(IY+d)
            partial(self.bit, 20, 4, 16, 'Yd'),              # 0x66 BIT 4,(IY+d)
            partial(self.bit, 20, 4, 16, 'Yd'),              # 0x67 BIT 4,(IY+d)
            partial(self.bit, 20, 4, 32, 'Yd'),              # 0x68 BIT 5,(IY+d)
            partial(self.bit, 20, 4, 32, 'Yd'),              # 0x69 BIT 5,(IY+d)
            partial(self.bit, 20, 4, 32, 'Yd'),              # 0x6A BIT 5,(IY+d)
            partial(self.bit, 20, 4, 32, 'Yd'),              # 0x6B BIT 5,(IY+d)
            partial(self.bit, 20, 4, 32, 'Yd'),              # 0x6C BIT 5,(IY+d)
            partial(self.bit, 20, 4, 32, 'Yd'),              # 0x6D BIT 5,(IY+d)
            partial(self.bit, 20, 4, 32, 'Yd'),              # 0x6E BIT 5,(IY+d)
            partial(self.bit, 20, 4, 32, 'Yd'),              # 0x6F BIT 5,(IY+d)
            partial(self.bit, 20, 4, 64, 'Yd'),              # 0x70 BIT 6,(IY+d)
            partial(self.bit, 20, 4, 64, 'Yd'),              # 0x71 BIT 6,(IY+d)
            partial(self.bit, 20, 4, 64, 'Yd'),              # 0x72 BIT 6,(IY+d)
            partial(self.bit, 20, 4, 64, 'Yd'),              # 0x73 BIT 6,(IY+d)
            partial(self.bit, 20, 4, 64, 'Yd'),              # 0x74 BIT 6,(IY+d)
            partial(self.bit, 20, 4, 64, 'Yd'),              # 0x75 BIT 6,(IY+d)
            partial(self.bit, 20, 4, 64, 'Yd'),              # 0x76 BIT 6,(IY+d)
            partial(self.bit, 20, 4, 64, 'Yd'),              # 0x77 BIT 6,(IY+d)
            partial(self.bit, 20, 4, 128, 'Yd'),             # 0x78 BIT 7,(IY+d)
            partial(self.bit, 20, 4, 128, 'Yd'),             # 0x79 BIT 7,(IY+d)
            partial(self.bit, 20, 4, 128, 'Yd'),             # 0x7A BIT 7,(IY+d)
            partial(self.bit, 20, 4, 128, 'Yd'),             # 0x7B BIT 7,(IY+d)
            partial(self.bit, 20, 4, 128, 'Yd'),             # 0x7C BIT 7,(IY+d)
            partial(self.bit, 20, 4, 128, 'Yd'),             # 0x7D BIT 7,(IY+d)
            partial(self.bit, 20, 4, 128, 'Yd'),             # 0x7E BIT 7,(IY+d)
            partial(self.bit, 20, 4, 128, 'Yd'),             # 0x7F BIT 7,(IY+d)
            partial(self.res_set, 23, 4, 254, 'Yd', 0, 'B'), # 0x80 RES 0,(IY+d),B
            partial(self.res_set, 23, 4, 254, 'Yd', 0, 'C'), # 0x81 RES 0,(IY+d),C
            partial(self.res_set, 23, 4, 254, 'Yd', 0, 'D'), # 0x82 RES 0,(IY+d),D
            partial(self.res_set, 23, 4, 254, 'Yd', 0, 'E'), # 0x83 RES 0,(IY+d),E
            partial(self.res_set, 23, 4, 254, 'Yd', 0, 'H'), # 0x84 RES 0,(IY+d),H
            partial(self.res_set, 23, 4, 254, 'Yd', 0, 'L'), # 0x85 RES 0,(IY+d),L
            partial(self.res_set, 23, 4, 254, 'Yd', 0),      # 0x86 RES 0,(IY+d)
            partial(self.res_set, 23, 4, 254, 'Yd', 0, 'A'), # 0x87 RES 0,(IY+d),A
            partial(self.res_set, 23, 4, 253, 'Yd', 0, 'B'), # 0x88 RES 1,(IY+d),B
            partial(self.res_set, 23, 4, 253, 'Yd', 0, 'C'), # 0x89 RES 1,(IY+d),C
            partial(self.res_set, 23, 4, 253, 'Yd', 0, 'D'), # 0x8A RES 1,(IY+d),D
            partial(self.res_set, 23, 4, 253, 'Yd', 0, 'E'), # 0x8B RES 1,(IY+d),E
            partial(self.res_set, 23, 4, 253, 'Yd', 0, 'H'), # 0x8C RES 1,(IY+d),H
            partial(self.res_set, 23, 4, 253, 'Yd', 0, 'L'), # 0x8D RES 1,(IY+d),L
            partial(self.res_set, 23, 4, 253, 'Yd', 0),      # 0x8E RES 1,(IY+d)
            partial(self.res_set, 23, 4, 253, 'Yd', 0, 'A'), # 0x8F RES 1,(IY+d),A
            partial(self.res_set, 23, 4, 251, 'Yd', 0, 'B'), # 0x90 RES 2,(IY+d),B
            partial(self.res_set, 23, 4, 251, 'Yd', 0, 'C'), # 0x91 RES 2,(IY+d),C
            partial(self.res_set, 23, 4, 251, 'Yd', 0, 'D'), # 0x92 RES 2,(IY+d),D
            partial(self.res_set, 23, 4, 251, 'Yd', 0, 'E'), # 0x93 RES 2,(IY+d),E
            partial(self.res_set, 23, 4, 251, 'Yd', 0, 'H'), # 0x94 RES 2,(IY+d),H
            partial(self.res_set, 23, 4, 251, 'Yd', 0, 'L'), # 0x95 RES 2,(IY+d),L
            partial(self.res_set, 23, 4, 251, 'Yd', 0),      # 0x96 RES 2,(IY+d)
            partial(self.res_set, 23, 4, 251, 'Yd', 0, 'A'), # 0x97 RES 2,(IY+d),A
            partial(self.res_set, 23, 4, 247, 'Yd', 0, 'B'), # 0x98 RES 3,(IY+d),B
            partial(self.res_set, 23, 4, 247, 'Yd', 0, 'C'), # 0x99 RES 3,(IY+d),C
            partial(self.res_set, 23, 4, 247, 'Yd', 0, 'D'), # 0x9A RES 3,(IY+d),D
            partial(self.res_set, 23, 4, 247, 'Yd', 0, 'E'), # 0x9B RES 3,(IY+d),E
            partial(self.res_set, 23, 4, 247, 'Yd', 0, 'H'), # 0x9C RES 3,(IY+d),H
            partial(self.res_set, 23, 4, 247, 'Yd', 0, 'L'), # 0x9D RES 3,(IY+d),L
            partial(self.res_set, 23, 4, 247, 'Yd', 0),      # 0x9E RES 3,(IY+d)
            partial(self.res_set, 23, 4, 247, 'Yd', 0, 'A'), # 0x9F RES 3,(IY+d),A
            partial(self.res_set, 23, 4, 239, 'Yd', 0, 'B'), # 0xA0 RES 4,(IY+d),B
            partial(self.res_set, 23, 4, 239, 'Yd', 0, 'C'), # 0xA1 RES 4,(IY+d),C
            partial(self.res_set, 23, 4, 239, 'Yd', 0, 'D'), # 0xA2 RES 4,(IY+d),D
            partial(self.res_set, 23, 4, 239, 'Yd', 0, 'E'), # 0xA3 RES 4,(IY+d),E
            partial(self.res_set, 23, 4, 239, 'Yd', 0, 'H'), # 0xA4 RES 4,(IY+d),H
            partial(self.res_set, 23, 4, 239, 'Yd', 0, 'L'), # 0xA5 RES 4,(IY+d),L
            partial(self.res_set, 23, 4, 239, 'Yd', 0),      # 0xA6 RES 4,(IY+d)
            partial(self.res_set, 23, 4, 239, 'Yd', 0, 'A'), # 0xA7 RES 4,(IY+d),A
            partial(self.res_set, 23, 4, 223, 'Yd', 0, 'B'), # 0xA8 RES 5,(IY+d),B
            partial(self.res_set, 23, 4, 223, 'Yd', 0, 'C'), # 0xA9 RES 5,(IY+d),C
            partial(self.res_set, 23, 4, 223, 'Yd', 0, 'D'), # 0xAA RES 5,(IY+d),D
            partial(self.res_set, 23, 4, 223, 'Yd', 0, 'E'), # 0xAB RES 5,(IY+d),E
            partial(self.res_set, 23, 4, 223, 'Yd', 0, 'H'), # 0xAC RES 5,(IY+d),H
            partial(self.res_set, 23, 4, 223, 'Yd', 0, 'L'), # 0xAD RES 5,(IY+d),L
            partial(self.res_set, 23, 4, 223, 'Yd', 0),      # 0xAE RES 5,(IY+d)
            partial(self.res_set, 23, 4, 223, 'Yd', 0, 'A'), # 0xAF RES 5,(IY+d),A
            partial(self.res_set, 23, 4, 191, 'Yd', 0, 'B'), # 0xB0 RES 6,(IY+d),B
            partial(self.res_set, 23, 4, 191, 'Yd', 0, 'C'), # 0xB1 RES 6,(IY+d),C
            partial(self.res_set, 23, 4, 191, 'Yd', 0, 'D'), # 0xB2 RES 6,(IY+d),D
            partial(self.res_set, 23, 4, 191, 'Yd', 0, 'E'), # 0xB3 RES 6,(IY+d),E
            partial(self.res_set, 23, 4, 191, 'Yd', 0, 'H'), # 0xB4 RES 6,(IY+d),H
            partial(self.res_set, 23, 4, 191, 'Yd', 0, 'L'), # 0xB5 RES 6,(IY+d),L
            partial(self.res_set, 23, 4, 191, 'Yd', 0),      # 0xB6 RES 6,(IY+d)
            partial(self.res_set, 23, 4, 191, 'Yd', 0, 'A'), # 0xB7 RES 6,(IY+d),A
            partial(self.res_set, 23, 4, 127, 'Yd', 0, 'B'), # 0xB8 RES 7,(IY+d),B
            partial(self.res_set, 23, 4, 127, 'Yd', 0, 'C'), # 0xB9 RES 7,(IY+d),C
            partial(self.res_set, 23, 4, 127, 'Yd', 0, 'D'), # 0xBA RES 7,(IY+d),D
            partial(self.res_set, 23, 4, 127, 'Yd', 0, 'E'), # 0xBB RES 7,(IY+d),E
            partial(self.res_set, 23, 4, 127, 'Yd', 0, 'H'), # 0xBC RES 7,(IY+d),H
            partial(self.res_set, 23, 4, 127, 'Yd', 0, 'L'), # 0xBD RES 7,(IY+d),L
            partial(self.res_set, 23, 4, 127, 'Yd', 0),      # 0xBE RES 7,(IY+d)
            partial(self.res_set, 23, 4, 127, 'Yd', 0, 'A'), # 0xBF RES 7,(IY+d),A
            partial(self.res_set, 23, 4, 1, 'Yd', 1, 'B'),   # 0xC0 SET 0,(IY+d),B
            partial(self.res_set, 23, 4, 1, 'Yd', 1, 'C'),   # 0xC1 SET 0,(IY+d),C
            partial(self.res_set, 23, 4, 1, 'Yd', 1, 'D'),   # 0xC2 SET 0,(IY+d),D
            partial(self.res_set, 23, 4, 1, 'Yd', 1, 'E'),   # 0xC3 SET 0,(IY+d),E
            partial(self.res_set, 23, 4, 1, 'Yd', 1, 'H'),   # 0xC4 SET 0,(IY+d),H
            partial(self.res_set, 23, 4, 1, 'Yd', 1, 'L'),   # 0xC5 SET 0,(IY+d),L
            partial(self.res_set, 23, 4, 1, 'Yd', 1),        # 0xC6 SET 0,(IY+d)
            partial(self.res_set, 23, 4, 1, 'Yd', 1, 'A'),   # 0xC7 SET 0,(IY+d),A
            partial(self.res_set, 23, 4, 2, 'Yd', 1, 'B'),   # 0xC8 SET 1,(IY+d),B
            partial(self.res_set, 23, 4, 2, 'Yd', 1, 'C'),   # 0xC9 SET 1,(IY+d),C
            partial(self.res_set, 23, 4, 2, 'Yd', 1, 'D'),   # 0xCA SET 1,(IY+d),D
            partial(self.res_set, 23, 4, 2, 'Yd', 1, 'E'),   # 0xCB SET 1,(IY+d),E
            partial(self.res_set, 23, 4, 2, 'Yd', 1, 'H'),   # 0xCC SET 1,(IY+d),H
            partial(self.res_set, 23, 4, 2, 'Yd', 1, 'L'),   # 0xCD SET 1,(IY+d),L
            partial(self.res_set, 23, 4, 2, 'Yd', 1),        # 0xCE SET 1,(IY+d)
            partial(self.res_set, 23, 4, 2, 'Yd', 1, 'A'),   # 0xCF SET 1,(IY+d),A
            partial(self.res_set, 23, 4, 4, 'Yd', 1, 'B'),   # 0xD0 SET 2,(IY+d),B
            partial(self.res_set, 23, 4, 4, 'Yd', 1, 'C'),   # 0xD1 SET 2,(IY+d),C
            partial(self.res_set, 23, 4, 4, 'Yd', 1, 'D'),   # 0xD2 SET 2,(IY+d),D
            partial(self.res_set, 23, 4, 4, 'Yd', 1, 'E'),   # 0xD3 SET 2,(IY+d),E
            partial(self.res_set, 23, 4, 4, 'Yd', 1, 'H'),   # 0xD4 SET 2,(IY+d),H
            partial(self.res_set, 23, 4, 4, 'Yd', 1, 'L'),   # 0xD5 SET 2,(IY+d),L
            partial(self.res_set, 23, 4, 4, 'Yd', 1),        # 0xD6 SET 2,(IY+d)
            partial(self.res_set, 23, 4, 4, 'Yd', 1, 'A'),   # 0xD7 SET 2,(IY+d),A
            partial(self.res_set, 23, 4, 8, 'Yd', 1, 'B'),   # 0xD8 SET 3,(IY+d),B
            partial(self.res_set, 23, 4, 8, 'Yd', 1, 'C'),   # 0xD9 SET 3,(IY+d),C
            partial(self.res_set, 23, 4, 8, 'Yd', 1, 'D'),   # 0xDA SET 3,(IY+d),D
            partial(self.res_set, 23, 4, 8, 'Yd', 1, 'E'),   # 0xDB SET 3,(IY+d),E
            partial(self.res_set, 23, 4, 8, 'Yd', 1, 'H'),   # 0xDC SET 3,(IY+d),H
            partial(self.res_set, 23, 4, 8, 'Yd', 1, 'L'),   # 0xDD SET 3,(IY+d),L
            partial(self.res_set, 23, 4, 8, 'Yd', 1),        # 0xDE SET 3,(IY+d)
            partial(self.res_set, 23, 4, 8, 'Yd', 1, 'A'),   # 0xDF SET 3,(IY+d),A
            partial(self.res_set, 23, 4, 16, 'Yd', 1, 'B'),  # 0xE0 SET 4,(IY+d),B
            partial(self.res_set, 23, 4, 16, 'Yd', 1, 'C'),  # 0xE1 SET 4,(IY+d),C
            partial(self.res_set, 23, 4, 16, 'Yd', 1, 'D'),  # 0xE2 SET 4,(IY+d),D
            partial(self.res_set, 23, 4, 16, 'Yd', 1, 'E'),  # 0xE3 SET 4,(IY+d),E
            partial(self.res_set, 23, 4, 16, 'Yd', 1, 'H'),  # 0xE4 SET 4,(IY+d),H
            partial(self.res_set, 23, 4, 16, 'Yd', 1, 'L'),  # 0xE5 SET 4,(IY+d),L
            partial(self.res_set, 23, 4, 16, 'Yd', 1),       # 0xE6 SET 4,(IY+d)
            partial(self.res_set, 23, 4, 16, 'Yd', 1, 'A'),  # 0xE7 SET 4,(IY+d),A
            partial(self.res_set, 23, 4, 32, 'Yd', 1, 'B'),  # 0xE8 SET 5,(IY+d),B
            partial(self.res_set, 23, 4, 32, 'Yd', 1, 'C'),  # 0xE9 SET 5,(IY+d),C
            partial(self.res_set, 23, 4, 32, 'Yd', 1, 'D'),  # 0xEA SET 5,(IY+d),D
            partial(self.res_set, 23, 4, 32, 'Yd', 1, 'E'),  # 0xEB SET 5,(IY+d),E
            partial(self.res_set, 23, 4, 32, 'Yd', 1, 'H'),  # 0xEC SET 5,(IY+d),H
            partial(self.res_set, 23, 4, 32, 'Yd', 1, 'L'),  # 0xED SET 5,(IY+d),L
            partial(self.res_set, 23, 4, 32, 'Yd', 1),       # 0xEE SET 5,(IY+d)
            partial(self.res_set, 23, 4, 32, 'Yd', 1, 'A'),  # 0xEF SET 5,(IY+d),A
            partial(self.res_set, 23, 4, 64, 'Yd', 1, 'B'),  # 0xF0 SET 6,(IY+d),B
            partial(self.res_set, 23, 4, 64, 'Yd', 1, 'C'),  # 0xF1 SET 6,(IY+d),C
            partial(self.res_set, 23, 4, 64, 'Yd', 1, 'D'),  # 0xF2 SET 6,(IY+d),D
            partial(self.res_set, 23, 4, 64, 'Yd', 1, 'E'),  # 0xF3 SET 6,(IY+d),E
            partial(self.res_set, 23, 4, 64, 'Yd', 1, 'H'),  # 0xF4 SET 6,(IY+d),H
            partial(self.res_set, 23, 4, 64, 'Yd', 1, 'L'),  # 0xF5 SET 6,(IY+d),L
            partial(self.res_set, 23, 4, 64, 'Yd', 1),       # 0xF6 SET 6,(IY+d)
            partial(self.res_set, 23, 4, 64, 'Yd', 1, 'A'),  # 0xF7 SET 6,(IY+d),A
            partial(self.res_set, 23, 4, 128, 'Yd', 1, 'B'), # 0xF8 SET 7,(IY+d),B
            partial(self.res_set, 23, 4, 128, 'Yd', 1, 'C'), # 0xF9 SET 7,(IY+d),C
            partial(self.res_set, 23, 4, 128, 'Yd', 1, 'D'), # 0xFA SET 7,(IY+d),D
            partial(self.res_set, 23, 4, 128, 'Yd', 1, 'E'), # 0xFB SET 7,(IY+d),E
            partial(self.res_set, 23, 4, 128, 'Yd', 1, 'H'), # 0xFC SET 7,(IY+d),H
            partial(self.res_set, 23, 4, 128, 'Yd', 1, 'L'), # 0xFD SET 7,(IY+d),L
            partial(self.res_set, 23, 4, 128, 'Yd', 1),      # 0xFE SET 7,(IY+d)
            partial(self.res_set, 23, 4, 128, 'Yd', 1, 'A'), # 0xFF SET 7,(IY+d),A
        ]
