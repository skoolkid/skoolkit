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

class Instruction:
    time = None
    address = None
    operation = None
    tstates = None

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
            self.after_ED[0xB0] = partial(self.ldir_fast, 'LDIR', 1)
            self.after_ED[0xB8] = partial(self.ldir_fast, 'LDDR', -1)
        self.tracers = []
        self.i_tracers = None
        self.in_tracers = ()
        self.out_tracers = ()
        self.peek_tracers = ()
        self.poke_tracers = ()
        self.instruction = Instruction()

    def add_tracer(self, tracer):
        self.tracers.append(tracer)
        self.i_tracers = [t.trace for t in self.tracers if hasattr(t, 'trace')]
        self.in_tracers = [t.read_port for t in self.tracers if hasattr(t, 'read_port')]
        self.out_tracers = [t.write_port for t in self.tracers if hasattr(t, 'write_port')]
        self.peek_tracers = [t.read_memory for t in self.tracers if hasattr(t, 'read_memory')]
        self.poke_tracers = [t.write_memory for t in self.tracers if hasattr(t, 'write_memory')]

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
        i_tracers = self.i_tracers
        instruction = self.instruction
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
            operation, pc, tstates = method()
            r = registers['R']
            registers['R'] = (r & 0x80) + ((r + r_inc) & 0x7F)
            pc &= 0xFFFF
            if i_tracers:
                running = pc != stop
                instruction.time = self.tstates
                instruction.address = self.pc
                instruction.operation = operation
                instruction.tstates = tstates
                self.pc = pc
                self.tstates += tstates
                for method in i_tracers:
                    if method(self, instruction):
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
            addr = (self.registers['IXl'] + 256 * self.registers['IXh'] + offset) & 0xFFFF
            ireg = 'IX'
        else:
            addr = (self.registers['IYl'] + 256 * self.registers['IYh'] + offset) & 0xFFFF
            ireg = 'IY'
        if offset >= 0:
            return addr, f'({ireg}+${offset:02X})'
        return addr, f'({ireg}-${-offset:02X})'

    def get_operand_value(self, size, reg):
        if reg in self.registers:
            return reg, self.registers[reg]
        if reg in ('(HL)', '(DE)', '(BC)'):
            rr = self.registers[reg[2]] + 256 * self.registers[reg[1]]
            value = self.peek(rr)
            operand = reg
        elif reg in ('Xd', 'Yd'):
            addr, operand = self.index()
            value = self.peek(addr)
        else:
            value = self.snapshot[(self.pc + size - 1) & 0xFFFF]
            operand = f'${value:02X}'
        return operand, value

    def set_operand_value(self, reg, value):
        if reg in self.registers:
            self.registers[reg] = value
        elif reg in ('(HL)', '(DE)', '(BC)'):
            rr = self.registers[reg[2]] + 256 * self.registers[reg[1]]
            self.poke(rr, value)
        else:
            addr, operand = self.index()
            self.poke(addr, value)

    def peek(self, address, count=1):
        for method in self.peek_tracers:
            method(self, address, count)
        if count == 1:
            return self.snapshot[address]
        return self.snapshot[address], self.snapshot[(address + 1) & 0xFFFF]

    def poke(self, address, *values):
        for method in self.poke_tracers:
            method(self, address, values)
        if address > 0x3FFF:
            self.snapshot[address] = values[0]
        if len(values) > 1:
            address = (address + 1) & 0xFFFF
            if address > 0x3FFF:
                self.snapshot[address] = values[1]

    def add_a(self, timing, size, reg=None, carry=0, mult=1):
        operand, value = self.get_operand_value(size, reg)
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
            if carry:
                op = f'ADC A,{operand}'
            else:
                op = f'ADD A,{operand}'
            s_value = value
            # 0x8F: ADC A,A
            if (opcode == 0x8F and old_a & 0x0F == 0x0F) or ((old_a & 0x0F) + (addend & 0x0F)) & 0x10:
                f |= 0x10 # ...H....
        else:
            if carry:
                op = f'SBC A,{operand}'
            else:
                op = f'SUB {operand}'
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
            f |= 0x04 # .....P..
        self.registers['A'] = a
        self.registers['F'] = f

        return op, self.pc + size, timing

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
                op = 'ADC'
                f = 0
            else:
                op = 'ADD'
                f = old_f & 0b11000100 # Keep SZ...P..
        else:
            op = 'SBC'
            f = 0b00000010 # ......N.
            s_addend = ~s_addend

        if ((augend_v & 0x0FFF) + mult * (addend_v & 0x0FFF)) & 0x1000:
            f |= 0b00010000 # ...H....

        value = augend_v + mult * addend_v
        if value < 0 or value > 0xFFFF:
            value &= 0xFFFF
            f |= 0b00000001 # .......C

        if op != 'ADD':
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

        return f'{op} {augend},{reg}', self.pc + size, timing

    def and_n(self):
        n = self.snapshot[(self.pc + 1) & 0xFFFF]
        self.registers['A'] &= n
        a = self.registers['A']
        f = (a & 0xA8) | 0x10 | PARITY[a] # S.5H3PNC
        if a == 0:
            self.registers['F'] = f | 0x40 # .Z......
        else:
            self.registers['F'] = f
        return f'AND ${n:02X}', self.pc + 2, 7

    def and_r(self, r):
        self.registers['A'] &= self.registers[r]
        a = self.registers['A']
        f = (a & 0xA8) | 0x10 | PARITY[a] # S.5H3PNC
        if a == 0:
            self.registers['F'] = f | 0x40 # .Z......
        else:
            self.registers['F'] = f
        return f'AND {r}', self.pc + 1, 4

    def anda(self, timing, size, reg=None):
        operand, value = self.get_operand_value(size, reg)
        self.registers['A'] &= value
        a = self.registers['A']
        f = (a & 0xA8) | 0x10 | PARITY[a] # S.5H3PNC
        if a == 0:
            f |= 0x40 # .Z......
        self.registers['F'] = f
        return f'AND {operand}', self.pc + size, timing

    def bit(self, timing, size, bit, reg):
        operand, value = self.get_operand_value(size, reg)
        bitval = (value >> bit) & 1
        f = 0x10 | (self.registers['F'] & 0x01) # ...H..NC
        if bit == 7 and bitval:
            f |= 0x80 # S.......
        if bitval == 0:
            f |= 0x44 # .Z...P..
        if reg in ('Xd', 'Yd'):
            offset = self.snapshot[(self.pc + 2) & 0xFFFF]
            if self.snapshot[self.pc] == 0xDD:
                v = (self.registers['IXl'] + 256 * self.registers['IXh'] + offset) & 0xFFFF
            else:
                v = (self.registers['IYl'] + 256 * self.registers['IYh'] + offset) & 0xFFFF
            f |= (v >> 8) & 0x28 # ..5.3...
        else:
            f |= value & 0x28 # ..5.3...
        self.registers['F'] = f
        return f'BIT {bit},{operand}', self.pc + size, timing

    def block(self, op, inc, repeat):
        hl = self.registers['L'] + 256 * self.registers['H']
        bc = self.registers['C'] + 256 * self.registers['B']
        b = self.registers['B']
        a = self.registers['A']
        tstates = 16
        addr = self.pc + 2
        bc_inc = -1

        if op.startswith('CP'):
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
        elif op.startswith('IN'):
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
        elif op.startswith('LD'):
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
        elif op.startswith('O'):
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

        return op, addr, tstates

    def call(self, condition, c_and, c_xor):
        addr = self.snapshot[(self.pc + 1) & 0xFFFF] + 256 * self.snapshot[(self.pc + 2) & 0xFFFF]
        ret_addr = (self.pc + 3) & 0xFFFF
        if condition:
            if self.registers['F'] & c_and ^ c_xor:
                pc = addr
                self._push(ret_addr % 256, ret_addr // 256)
                tstates = 17
            else:
                pc = self.pc + 3
                tstates = 10
            return f'CALL {condition},${addr:04X}', pc, tstates
        self._push(ret_addr % 256, ret_addr // 256)
        return f'CALL ${addr:04X}', addr, 17

    def cf(self):
        f = self.registers['F'] & 0xC4 # SZ...PN.
        if self.snapshot[self.pc] == 63:
            operation = 'CCF'
            old_c = self.registers['F'] & 0x01
            if old_c:
                f |= 0x10 # ...H....
            else:
                f |= 0x01 # .......C
        else:
            operation = 'SCF'
            f |= 0x01 # .......C
        f |= self.registers['A'] & 0x28 # ..5.3...
        self.registers['F'] = f
        return operation, self.pc + 1, 4

    def cp(self, timing, size, reg=None):
        operand, value = self.get_operand_value(size, reg)
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
            f |= 0x01 # .......C
        self.registers['F'] = f
        return f'CP {operand}', self.pc + size, timing

    def cpl(self):
        a = self.registers['A'] ^ 255
        self.registers['A'] = a
        self.registers['F'] = (self.registers['F'] & 0xC5) | (a & 0x28) | 0x12
        return 'CPL', self.pc + 1, 4

    def daa(self):
        a = self.registers['A']
        hf = self.registers['F'] & 0x10
        nf = self.registers['F'] & 0x02
        t = 0
        f = nf

        if hf or a & 15 > 0x09:
            t += 1
        if self.registers['F'] & 0x01 or a > 0x99:
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
            f |= 0x40 # .Z......
        self.registers['F'] = f

        return 'DAA', self.pc + 1, 4

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
            f |= 0x40 # .Z......
        self.registers['F'] = f
        self.registers[reg] = value
        return 'DEC ' + reg, self.pc + 1, 4

    def defb(self, timing, size):
        end = self.pc + size
        values = ','.join(f'${self.snapshot[a & 0xFFFF]:02X}' for a in range(self.pc, end))
        return f'DEFB {values}', end, timing

    def di_ei(self, op, iff2):
        self.iff2 = iff2
        return op, self.pc + 1, 4

    def djnz(self):
        self.registers['B'] = (self.registers['B'] - 1) & 255
        offset = self.snapshot[(self.pc + 1) & 0xFFFF]
        if offset & 128:
            offset -= 256
        addr = (self.pc + 2 + offset) & 0xFFFF
        if self.registers['B']:
            pc = addr
            tstates = 13
        else:
            pc = self.pc + 2
            tstates = 8
        return f'DJNZ ${addr:04X}', pc, tstates

    def djnz_fast(self):
        if self.snapshot[(self.pc + 1) & 0xFFFF] == 0xFE:
            b = (self.registers['B'] - 1) & 0xFF
            self.registers['B'] = 0
            r = self.registers['R']
            self.registers['R'] = (r & 0x80) + ((r + b) & 0x7F)
            return f'DJNZ ${self.pc:04X}', self.pc + 2, b * 13 + 8
        return self.djnz()

    def ex_af(self):
        for r in 'AF':
            self.registers[r], self.registers['^' + r] = self.registers['^' + r], self.registers[r]
        return "EX AF,AF'", self.pc + 1, 4

    def ex_de_hl(self):
        for r1, r2 in (('D', 'H'), ('E', 'L')):
            self.registers[r1], self.registers[r2] = self.registers[r2], self.registers[r1]
        return 'EX DE,HL', self.pc + 1, 4

    def ex_sp(self, reg):
        sp = self.registers['SP']
        sp1, sp2 = self.peek(sp, 2)
        if reg == 'HL':
            r1, r2 = 'L', 'H'
            size, timing = 1, 19
        else:
            r1, r2 = reg + 'l', reg + 'h'
            size, timing = 2, 23
        self.poke(sp, self.registers[r1], self.registers[r2])
        self.registers[r1] = sp1
        self.registers[r2] = sp2
        return f'EX (SP),{reg}', self.pc + size, timing

    def exx(self):
        for r in 'BCDEHL':
            self.registers[r], self.registers['^' + r] = self.registers['^' + r], self.registers[r]
        return 'EXX', self.pc + 1, 4

    def halt(self):
        pc = self.pc
        if self.iff2:
            t1 = self.tstates % FRAME_DURATION
            t2 = (self.tstates + 4) % FRAME_DURATION
            if t2 < t1:
                pc += 1
        return 'HALT', pc, 4

    def im(self, mode):
        self.imode = mode
        return f'IM {mode}', self.pc + 2, 8

    def _in(self, port):
        reading = None
        for method in self.in_tracers:
            reading = method(self, port)
        if reading is None:
            return 191
        return reading

    def in_a(self):
        operand = self.snapshot[(self.pc + 1) & 0xFFFF]
        self.registers['A'] = self._in(operand + 256 * self.registers['A'])
        return f'IN A,(${operand:02X})', self.pc + 2, 11

    def in_c(self, reg):
        value = self._in(self.registers['C'] + 256 * self.registers['B'])
        if reg != 'F':
            self.registers[reg] = value
        f = (value & 0xA8) | PARITY[value] | (self.registers['F'] & 0x01) # S.5H3PNC
        if value == 0:
            f |= 0x40 # .Z......
        self.registers['F'] = f
        return f'IN {reg},(C)', self.pc + 2, 12

    def inc_r(self, reg):
        o_value = self.registers[reg]
        value = (o_value + 1) & 0xFF
        f = (self.registers['F'] & 0x01) | (value & 0xA8) # S.5.3..C
        if o_value & 0x0F == 0x0F:
            f |= 0x10 # ...H....
        if o_value == 0x7F:
            f |= 0x04 # .....P..
        if value == 0:
            f |= 0x40 # .Z......
        self.registers['F'] = f
        self.registers[reg] = value
        return 'INC ' + reg, self.pc + 1, 4

    def inc_dec8(self, timing, size, op, reg):
        operand, o_value = self.get_operand_value(size, reg)
        if op == 'DEC':
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
            f |= 0x40 # .Z......
        self.registers['F'] = f
        self.set_operand_value(reg, value)
        return f'{op} {operand}', self.pc + size, timing

    def inc_dec16(self, op, reg):
        if op == 'DEC':
            inc = -1
        else:
            inc = 1
        if reg == 'SP':
            self.registers[reg] = (self.registers[reg] + inc) & 0xFFFF
            size, timing = 1, 6
        elif reg in ('IX', 'IY'):
            value = (self.registers[reg + 'l'] + 256 * self.registers[reg + 'h'] + inc) & 0xFFFF
            self.registers[reg + 'h'] = value // 256
            self.registers[reg + 'l'] = value % 256
            size, timing = 2, 10
        else:
            value = (self.registers[reg[1]] + 256 * self.registers[reg[0]] + inc) & 0xFFFF
            self.registers[reg[0]] = value // 256
            self.registers[reg[1]] = value % 256
            size, timing = 1, 6
        return f'{op} {reg}', self.pc + size, timing

    def jr(self, condition, c_and, c_xor):
        offset = self.snapshot[(self.pc + 1) & 0xFFFF]
        if offset & 128:
            offset -= 256
        addr = (self.pc + 2 + offset) & 0xFFFF
        if condition:
            if self.registers['F'] & c_and ^ c_xor:
                pc = addr
                tstates = 12
            else:
                pc = self.pc + 2
                tstates = 7
            return f'JR {condition},${addr:04X}', pc, tstates
        return f'JR ${addr:04X}', addr, 12

    def jp(self, condition, c_and, c_xor):
        opcode = self.snapshot[self.pc]
        if opcode == 0xDD:
            addr = self.registers['IXl'] + 256 * self.registers['IXh']
            return 'JP (IX)', addr, 8
        if opcode == 0xFD:
            addr = self.registers['IYl'] + 256 * self.registers['IYh']
            return 'JP (IY)', addr, 8
        if opcode == 0xE9:
            addr = self.registers['L'] + 256 * self.registers['H']
            return 'JP (HL)', addr, 4

        addr = self.snapshot[(self.pc + 1) & 0xFFFF] + 256 * self.snapshot[(self.pc + 2) & 0xFFFF]
        if condition:
            if self.registers['F'] & c_and ^ c_xor:
                pc = addr
            else:
                pc = self.pc + 3
            return f'JP {condition},${addr:04X}', pc, 10
        return f'JP ${addr:04X}', addr, 10

    def ld_r_n(self, r):
        n = self.snapshot[(self.pc + 1) & 0xFFFF]
        self.registers[r] = n
        return f'LD {r},${n:02X}', self.pc + 2, 7

    def ld_r_r(self, op, r1, r2):
        self.registers[r1] = self.registers[r2]
        return op, self.pc + 1, 4

    def ld8(self, timing, size, reg, reg2=None):
        op1, v1 = self.get_operand_value(size, reg)
        op2, v2 = self.get_operand_value(size, reg2)
        self.set_operand_value(reg, v2)
        if reg2 and reg2 in 'IR':
            a = self.registers['A']
            f = (a & 0xA8) | (self.registers['F'] & 0x01) # S.5H3.NC
            if a == 0:
                f |= 0x40 # .Z......
            if self.iff2:
                f |= 0x04 # .....P..
            self.registers['F'] = f
        return f'LD {op1},{op2}', self.pc + size, timing

    def ld16(self, reg):
        if reg == 'SP':
            value = self.snapshot[(self.pc + 1) & 0xFFFF] + 256 * self.snapshot[(self.pc + 2) & 0xFFFF]
            size, timing = 3, 10
            self.registers['SP'] = value
        elif reg in ('IX', 'IY'):
            lsb, msb = self.snapshot[(self.pc + 2) & 0xFFFF], self.snapshot[(self.pc + 3) & 0xFFFF]
            value = lsb + 256 * msb
            size, timing = 4, 14
            self.registers[reg + 'l'], self.registers[reg + 'h'] = lsb, msb
        else:
            lsb, msb = self.snapshot[(self.pc + 1) & 0xFFFF], self.snapshot[(self.pc + 2) & 0xFFFF]
            value = lsb + 256 * msb
            size, timing = 3, 10
            self.registers[reg[1]], self.registers[reg[0]] = lsb, msb
        return f'LD {reg},${value:04X}', self.pc + size, timing

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
            op = f'LD (${addr:04X}),{reg}'
        else:
            if reg == 'SP':
                sp1, sp2 = self.peek(addr, 2)
                self.registers['SP'] = sp1 + 256 * sp2
            elif reg in ('IX', 'IY'):
                self.registers[reg + 'l'], self.registers[reg + 'h'] = self.peek(addr, 2)
            else:
                self.registers[reg[1]], self.registers[reg[0]] = self.peek(addr, 2)
            op = f'LD {reg},(${addr:04X})'
        return op, end, timing

    def ldann(self):
        addr = self.snapshot[(self.pc + 1) & 0xFFFF] + 256 * self.snapshot[(self.pc + 2) & 0xFFFF]
        if self.snapshot[self.pc] == 0x3A:
            op = f'LD A,(${addr:04X})'
            self.registers['A'] = self.peek(addr)
        else:
            op = f'LD (${addr:04X}),A'
            self.poke(addr, self.registers['A'])
        return op, self.pc + 3, 13

    def ldir_fast(self, op, inc):
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
        return op, pc, 21 * count - 5

    def ldsprr(self, reg):
        if reg == 'HL':
            self.registers['SP'] = self.registers['L'] + 256 * self.registers['H']
            size, timing = 1, 6
        else:
            self.registers['SP'] = self.registers[reg + 'l'] + 256 * self.registers[reg + 'h']
            size, timing = 2, 10
        return f'LD SP,{reg}', self.pc + size, timing

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
            f |= 0x01 # .......C
        self.registers['F'] = f
        return 'NEG', self.pc + 2, 8

    def nop(self):
        return 'NOP', self.pc + 1, 4

    def or_n(self):
        n = self.snapshot[(self.pc + 1) & 0xFFFF]
        self.registers['A'] |= n
        a = self.registers['A']
        f = (a & 0xA8) | PARITY[a] # S.5H3PNC
        if a == 0:
            self.registers['F'] = f | 0x40 # .Z......
        else:
            self.registers['F'] = f
        return f'OR ${n:02X}', self.pc + 2, 7

    def or_r(self, r):
        self.registers['A'] |= self.registers[r]
        a = self.registers['A']
        f = (a & 0xA8) | PARITY[a] # S.5H3PNC
        if a == 0:
            self.registers['F'] = f | 0x40 # .Z......
        else:
            self.registers['F'] = f
        return f'OR {r}', self.pc + 1, 4

    def ora(self, timing, size, reg=None):
        operand, value = self.get_operand_value(size, reg)
        self.registers['A'] |= value
        a = self.registers['A']
        f = (a & 0xA8) | PARITY[a] # S.5H3PNC
        if a == 0:
            f |= 0x40 # .Z......
        self.registers['F'] = f
        return f'OR {operand}', self.pc + size, timing

    def _out(self, port, value):
        for method in self.out_tracers:
            method(self, port, value)

    def outa(self):
        a = self.registers['A']
        operand = self.snapshot[(self.pc + 1) & 0xFFFF]
        self._out(operand + 256 * a, a)
        return f'OUT (${operand:02X}),A', self.pc + 2, 11

    def outc(self, reg):
        port = self.registers['C'] + 256 * self.registers['B']
        if reg:
            value = self.registers[reg]
        else:
            reg = value = 0
        self._out(port, value)
        return f'OUT (C),{reg}', self.pc + 2, 12

    def _pop(self):
        sp = self.registers['SP']
        lsb, msb = self.peek(sp, 2)
        self.registers['SP'] = (sp + 2) & 0xFFFF
        self.ppcount -= 1
        return lsb, msb

    def pop(self, reg):
        if reg in ('IX', 'IY'):
            self.registers[reg + 'l'], self.registers[reg + 'h'] = self._pop()
            size, timing = 2, 14
        else:
            self.registers[reg[1]], self.registers[reg[0]] = self._pop()
            size, timing = 1, 10
        return f'POP {reg}', self.pc + size, timing

    def _push(self, lsb, msb):
        sp = (self.registers['SP'] - 2) & 0xFFFF
        self.poke(sp, lsb, msb)
        self.ppcount += 1
        self.registers['SP'] = sp

    def push(self, reg):
        if reg in ('IX', 'IY'):
            self._push(self.registers[reg + 'l'], self.registers[reg + 'h'])
            size, timing = 2, 15
        else:
            self._push(self.registers[reg[1]], self.registers[reg[0]])
            size, timing = 1, 11
        return f'PUSH {reg}', self.pc + size, timing

    def ret(self, op, c_and, c_xor):
        if c_and:
            if self.registers['F'] & c_and ^ c_xor:
                lsb, msb = self._pop()
                pc = lsb + 256 * msb
                tstates = 11
            else:
                pc = self.pc + 1
                tstates = 5
            return op, pc, tstates
        lsb, msb = self._pop()
        return op, lsb + 256 * msb, 10

    def reti(self, op):
        lsb, msb = self._pop()
        return op, lsb + 256 * msb, 14

    def res_set(self, timing, size, bit, reg, bitval, dest=''):
        operand, value = self.get_operand_value(size, reg)
        mask = 1 << bit
        if bitval:
            value |= mask
            op = f'SET {bit},{operand}'
        else:
            value &= mask ^ 255
            op = f'RES {bit},{operand}'
        self.set_operand_value(reg, value)
        if dest:
            self.registers[dest] = value
            op += f',{dest}'
        return op, self.pc + size, timing

    def rld(self):
        hl = self.registers['L'] + 256 * self.registers['H']
        a = self.registers['A']
        at_hl = self.peek(hl)
        self.poke(hl, ((at_hl << 4) & 240) + (a & 15))
        a_out = self.registers['A'] = (a & 240) + ((at_hl >> 4) & 15)
        f = (a_out & 0xA8) | PARITY[a_out] | (self.registers['F'] & 0x01) # S.5H3PNC
        if a_out == 0:
            f |= 0x40 # .Z......
        self.registers['F'] = f
        return 'RLD', self.pc + 2, 18

    def rrd(self):
        hl = self.registers['L'] + 256 * self.registers['H']
        a = self.registers['A']
        at_hl = self.peek(hl)
        self.poke(hl, ((a << 4) & 240) + (at_hl >> 4))
        a_out = self.registers['A'] = (a & 240) + (at_hl & 15)
        f = (a_out & 0xA8) | PARITY[a_out] | (self.registers['F'] & 0x01) # S.5H3PNC
        if a_out == 0:
            f |= 0x40 # .Z......
        self.registers['F'] = f
        return 'RRD', self.pc + 2, 18

    def rotate_a(self, op, cbit, carry=0):
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
        return op, self.pc + 1, 4

    def rotate_r(self, op, cbit, reg, carry=0):
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
        return op, self.pc + 2, 8

    def rotate(self, timing, size, op, cbit, reg, carry=0, dest=''):
        operand, value = self.get_operand_value(size, reg)
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
            dest = ',' + dest
        f = (value & 0xA8) | PARITY[value] # S.5H3PN.
        if value == 0:
            f |= 0x40 # .Z......
        if new_carry:
            self.registers['F'] = f | 0x01 # .......C
        else:
            self.registers['F'] = f
        return f'{op} {operand}{dest}', self.pc + size, timing

    def rst(self, addr):
        ret_addr = (self.pc + 1) & 0xFFFF
        self._push(ret_addr % 256, ret_addr // 256)
        return f'RST ${addr:02X}', addr, 11

    def shift(self, timing, size, op, cbit, reg, dest=''):
        operand, value = self.get_operand_value(size, reg)
        ovalue = value
        if value & cbit:
            f = 0x01 # .......C
        else:
            f = 0x00 # .......C
        if cbit == 1:
            value >>= 1
        else:
            value <<= 1
        if op == 'SRA':
            value += ovalue & 128
        elif op == 'SLL':
            value |= 1
        value &= 255
        self.set_operand_value(reg, value)
        if dest:
            self.registers[dest] = value
            dest = ',' + dest
        f |= (value & 0xA8) | PARITY[value] # S.5H3PN.
        if value == 0:
            f |= 0x40 # .Z......
        self.registers['F'] = f
        return f'{op} {operand}{dest}', self.pc + size, timing

    def xor_n(self):
        n = self.snapshot[(self.pc + 1) & 0xFFFF]
        self.registers['A'] ^= n
        a = self.registers['A']
        f = (a & 0xA8) | PARITY[a] # S.5H3PNC
        if a == 0:
            self.registers['F'] = f | 0x40 # .Z......
        else:
            self.registers['F'] = f
        return f'XOR ${n:02X}', self.pc + 2, 7

    def xor_r(self, r):
        self.registers['A'] ^= self.registers[r]
        a = self.registers['A']
        f = (a & 0xA8) | PARITY[a] # S.5H3PNC
        if a == 0:
            self.registers['F'] = f | 0x40 # .Z......
        else:
            self.registers['F'] = f
        return f'XOR {r}', self.pc + 1, 4

    def xor(self, timing, size, reg=None):
        operand, value = self.get_operand_value(size, reg)
        self.registers['A'] ^= value
        a = self.registers['A']
        f = (a & 0xA8) | PARITY[a] # S.5H3PNC
        if a == 0:
            f |= 0x40 # .Z......
        self.registers['F'] = f
        return f'XOR {operand}', self.pc + size, timing

    def create_opcodes(self):
        self.opcodes = {
            0x00: self.nop,                                              # NOP
            0x01: partial(self.ld16, 'BC'),                              # LD BC,nn
            0x02: partial(self.ld8, 7, 1, '(BC)', 'A'),                  # LD (BC),A
            0x03: partial(self.inc_dec16, 'INC', 'BC'),                  # INC BC
            0x04: partial(self.inc_r, 'B'),                              # INC B
            0x05: partial(self.dec_r, 'B'),                              # DEC B
            0x06: partial(self.ld_r_n, 'B'),                             # LD B,n
            0x07: partial(self.rotate_a, 'RLCA', 128, 1),                # RLCA
            0x08: self.ex_af,                                            # EX AF,AF'
            0x09: partial(self.add16, 11, 1, 'HL', 'BC'),                # ADD HL,BC
            0x0A: partial(self.ld8, 7, 1, 'A', '(BC)'),                  # LD A,(BC)
            0x0B: partial(self.inc_dec16, 'DEC', 'BC'),                  # DEC BC
            0x0C: partial(self.inc_r, 'C'),                              # INC C
            0x0D: partial(self.dec_r, 'C'),                              # DEC C
            0x0E: partial(self.ld_r_n, 'C'),                             # LD C,n
            0x0F: partial(self.rotate_a, 'RRCA', 1, 1),                  # RRCA
            0x10: self.djnz,                                             # DJNZ nn
            0x11: partial(self.ld16, 'DE'),                              # LD DE,nn
            0x12: partial(self.ld8, 7, 1, '(DE)', 'A'),                  # LD (DE),A
            0x13: partial(self.inc_dec16, 'INC', 'DE'),                  # INC DE
            0x14: partial(self.inc_r, 'D'),                              # INC D
            0x15: partial(self.dec_r, 'D'),                              # DEC D
            0x16: partial(self.ld_r_n, 'D'),                             # LD D,n
            0x17: partial(self.rotate_a, 'RLA', 128),                    # RLA
            0x18: partial(self.jr, '', 0, 0),                            # JR nn
            0x19: partial(self.add16, 11, 1, 'HL', 'DE'),                # ADD HL,DE
            0x1A: partial(self.ld8, 7, 1, 'A', '(DE)'),                  # LD A,(DE)
            0x1B: partial(self.inc_dec16, 'DEC', 'DE'),                  # DEC DE
            0x1C: partial(self.inc_r, 'E'),                              # INC E
            0x1D: partial(self.dec_r, 'E'),                              # DEC E
            0x1E: partial(self.ld_r_n, 'E'),                             # LD E,n
            0x1F: partial(self.rotate_a, 'RRA', 1),                      # RRA
            0x20: partial(self.jr, 'NZ', 64, 64),                        # JR NZ,nn
            0x21: partial(self.ld16, 'HL'),                              # LD HL,nn
            0x22: partial(self.ld16addr, 16, 3, 'HL', 1),                # LD (nn),HL
            0x23: partial(self.inc_dec16, 'INC', 'HL'),                  # INC HL
            0x24: partial(self.inc_r, 'H'),                              # INC H
            0x25: partial(self.dec_r, 'H'),                              # DEC H
            0x26: partial(self.ld_r_n, 'H'),                             # LD H,n
            0x27: self.daa,                                              # DAA
            0x28: partial(self.jr, 'Z', 64, 0),                          # JR Z,nn
            0x29: partial(self.add16, 11, 1, 'HL', 'HL'),                # ADD HL,HL
            0x2A: partial(self.ld16addr, 16, 3, 'HL', 0),                # LD HL,(nn)
            0x2B: partial(self.inc_dec16, 'DEC', 'HL'),                  # DEC HL
            0x2C: partial(self.inc_r, 'L'),                              # INC L
            0x2D: partial(self.dec_r, 'L'),                              # DEC L
            0x2E: partial(self.ld_r_n, 'L'),                             # LD L,n
            0x2F: self.cpl,                                              # CPL
            0x30: partial(self.jr, 'NC', 1, 1),                          # JR NC,nn
            0x31: partial(self.ld16, 'SP'),                              # LD SP,nn
            0x32: self.ldann,                                            # LD (nn),A
            0x33: partial(self.inc_dec16, 'INC', 'SP'),                  # INC SP
            0x34: partial(self.inc_dec8, 11, 1, 'INC', '(HL)'),          # INC (HL)
            0x35: partial(self.inc_dec8, 11, 1, 'DEC', '(HL)'),          # DEC (HL)
            0x36: partial(self.ld8, 10, 2, '(HL)'),                      # LD (HL),n
            0x37: self.cf,                                               # SCF
            0x38: partial(self.jr, 'C', 1, 0),                           # JR C,nn
            0x39: partial(self.add16, 11, 1, 'HL', 'SP'),                # ADD HL,SP
            0x3A: self.ldann,                                            # LD A,(nn)
            0x3B: partial(self.inc_dec16, 'DEC', 'SP'),                  # DEC SP
            0x3C: partial(self.inc_r, 'A'),                              # INC A
            0x3D: partial(self.dec_r, 'A'),                              # DEC A
            0x3E: partial(self.ld_r_n, 'A'),                             # LD A,n
            0x3F: self.cf,                                               # CCF
            0x40: partial(self.ld_r_r, 'LD B,B', 'B', 'B'),              # LD B,B
            0x41: partial(self.ld_r_r, 'LD B,C', 'B', 'C'),              # LD B,C
            0x42: partial(self.ld_r_r, 'LD B,D', 'B', 'D'),              # LD B,D
            0x43: partial(self.ld_r_r, 'LD B,E', 'B', 'E'),              # LD B,E
            0x44: partial(self.ld_r_r, 'LD B,H', 'B', 'H'),              # LD B,H
            0x45: partial(self.ld_r_r, 'LD B,L', 'B', 'L'),              # LD B,L
            0x46: partial(self.ld8, 7, 1, 'B', '(HL)'),                  # LD B,(HL)
            0x47: partial(self.ld_r_r, 'LD B,A', 'B', 'A'),              # LD B,A
            0x48: partial(self.ld_r_r, 'LD C,B', 'C', 'B'),              # LD C,B
            0x49: partial(self.ld_r_r, 'LD C,C', 'C', 'C'),              # LD C,C
            0x4A: partial(self.ld_r_r, 'LD C,D', 'C', 'D'),              # LD C,D
            0x4B: partial(self.ld_r_r, 'LD C,E', 'C', 'E'),              # LD C,E
            0x4C: partial(self.ld_r_r, 'LD C,H', 'C', 'H'),              # LD C,H
            0x4D: partial(self.ld_r_r, 'LD C,L', 'C', 'L'),              # LD C,L
            0x4E: partial(self.ld8, 7, 1, 'C', '(HL)'),                  # LD C,(HL)
            0x4F: partial(self.ld_r_r, 'LD C,A', 'C', 'A'),              # LD C,A
            0x50: partial(self.ld_r_r, 'LD D,B', 'D', 'B'),              # LD D,B
            0x51: partial(self.ld_r_r, 'LD D,C', 'D', 'C'),              # LD D,C
            0x52: partial(self.ld_r_r, 'LD D,D', 'D', 'D'),              # LD D,D
            0x53: partial(self.ld_r_r, 'LD D,E', 'D', 'E'),              # LD D,E
            0x54: partial(self.ld_r_r, 'LD D,H', 'D', 'H'),              # LD D,H
            0x55: partial(self.ld_r_r, 'LD D,L', 'D', 'L'),              # LD D,L
            0x56: partial(self.ld8, 7, 1, 'D', '(HL)'),                  # LD D,(HL)
            0x57: partial(self.ld_r_r, 'LD D,A', 'D', 'A'),              # LD D,A
            0x58: partial(self.ld_r_r, 'LD E,B', 'E', 'B'),              # LD E,B
            0x59: partial(self.ld_r_r, 'LD E,C', 'E', 'C'),              # LD E,C
            0x5A: partial(self.ld_r_r, 'LD E,D', 'E', 'D'),              # LD E,D
            0x5B: partial(self.ld_r_r, 'LD E,E', 'E', 'E'),              # LD E,E
            0x5C: partial(self.ld_r_r, 'LD E,H', 'E', 'H'),              # LD E,H
            0x5D: partial(self.ld_r_r, 'LD E,L', 'E', 'L'),              # LD E,L
            0x5E: partial(self.ld8, 7, 1, 'E', '(HL)'),                  # LD E,(HL)
            0x5F: partial(self.ld_r_r, 'LD E,A', 'E', 'A'),              # LD E,A
            0x60: partial(self.ld_r_r, 'LD H,B', 'H', 'B'),              # LD H,B
            0x61: partial(self.ld_r_r, 'LD H,C', 'H', 'C'),              # LD H,C
            0x62: partial(self.ld_r_r, 'LD H,D', 'H', 'D'),              # LD H,D
            0x63: partial(self.ld_r_r, 'LD H,E', 'H', 'E'),              # LD H,E
            0x64: partial(self.ld_r_r, 'LD H,H', 'H', 'H'),              # LD H,H
            0x65: partial(self.ld_r_r, 'LD H,L', 'H', 'L'),              # LD H,L
            0x66: partial(self.ld8, 7, 1, 'H', '(HL)'),                  # LD H,(HL)
            0x67: partial(self.ld_r_r, 'LD H,A', 'H', 'A'),              # LD H,A
            0x68: partial(self.ld_r_r, 'LD L,B', 'L', 'B'),              # LD L,B
            0x69: partial(self.ld_r_r, 'LD L,C', 'L', 'C'),              # LD L,C
            0x6A: partial(self.ld_r_r, 'LD L,D', 'L', 'D'),              # LD L,D
            0x6B: partial(self.ld_r_r, 'LD L,E', 'L', 'E'),              # LD L,E
            0x6C: partial(self.ld_r_r, 'LD L,H', 'L', 'H'),              # LD L,H
            0x6D: partial(self.ld_r_r, 'LD L,L', 'L', 'L'),              # LD L,L
            0x6E: partial(self.ld8, 7, 1, 'L', '(HL)'),                  # LD L,(HL)
            0x6F: partial(self.ld_r_r, 'LD L,A', 'L', 'A'),              # LD L,A
            0x70: partial(self.ld8, 7, 1, '(HL)', 'B'),                  # LD (HL),B
            0x71: partial(self.ld8, 7, 1, '(HL)', 'C'),                  # LD (HL),C
            0x72: partial(self.ld8, 7, 1, '(HL)', 'D'),                  # LD (HL),D
            0x73: partial(self.ld8, 7, 1, '(HL)', 'E'),                  # LD (HL),E
            0x74: partial(self.ld8, 7, 1, '(HL)', 'H'),                  # LD (HL),H
            0x75: partial(self.ld8, 7, 1, '(HL)', 'L'),                  # LD (HL),L
            0x76: self.halt,                                             # HALT
            0x77: partial(self.ld8, 7, 1, '(HL)', 'A'),                  # LD (HL),A
            0x78: partial(self.ld_r_r, 'LD A,B', 'A', 'B'),              # LD A,B
            0x79: partial(self.ld_r_r, 'LD A,C', 'A', 'C'),              # LD A,C
            0x7A: partial(self.ld_r_r, 'LD A,D', 'A', 'D'),              # LD A,D
            0x7B: partial(self.ld_r_r, 'LD A,E', 'A', 'E'),              # LD A,E
            0x7C: partial(self.ld_r_r, 'LD A,H', 'A', 'H'),              # LD A,H
            0x7D: partial(self.ld_r_r, 'LD A,L', 'A', 'L'),              # LD A,L
            0x7E: partial(self.ld8, 7, 1, 'A', '(HL)'),                  # LD A,(HL)
            0x7F: partial(self.ld_r_r, 'LD A,A', 'A', 'A'),              # LD A,A
            0x80: partial(self.add_a, 4, 1, 'B'),                        # ADD A,B
            0x81: partial(self.add_a, 4, 1, 'C'),                        # ADD A,C
            0x82: partial(self.add_a, 4, 1, 'D'),                        # ADD A,D
            0x83: partial(self.add_a, 4, 1, 'E'),                        # ADD A,E
            0x84: partial(self.add_a, 4, 1, 'H'),                        # ADD A,H
            0x85: partial(self.add_a, 4, 1, 'L'),                        # ADD A,L
            0x86: partial(self.add_a, 7, 1, '(HL)'),                     # ADD A,(HL)
            0x87: partial(self.add_a, 4, 1, 'A'),                        # ADD A,A
            0x88: partial(self.add_a, 4, 1, 'B', 1),                     # ADC A,B
            0x89: partial(self.add_a, 4, 1, 'C', 1),                     # ADC A,C
            0x8A: partial(self.add_a, 4, 1, 'D', 1),                     # ADC A,D
            0x8B: partial(self.add_a, 4, 1, 'E', 1),                     # ADC A,E
            0x8C: partial(self.add_a, 4, 1, 'H', 1),                     # ADC A,H
            0x8D: partial(self.add_a, 4, 1, 'L', 1),                     # ADC A,L
            0x8E: partial(self.add_a, 7, 1, '(HL)', 1),                  # ADC A,(HL)
            0x8F: partial(self.add_a, 4, 1, 'A', 1),                     # ADC A,A
            0x90: partial(self.add_a, 4, 1, 'B', 0, -1),                 # SUB B
            0x91: partial(self.add_a, 4, 1, 'C', 0, -1),                 # SUB C
            0x92: partial(self.add_a, 4, 1, 'D', 0, -1),                 # SUB D
            0x93: partial(self.add_a, 4, 1, 'E', 0, -1),                 # SUB E
            0x94: partial(self.add_a, 4, 1, 'H', 0, -1),                 # SUB H
            0x95: partial(self.add_a, 4, 1, 'L', 0, -1),                 # SUB L
            0x96: partial(self.add_a, 7, 1, '(HL)', 0, -1),              # SUB (HL)
            0x97: partial(self.add_a, 4, 1, 'A', 0, -1),                 # SUB A
            0x98: partial(self.add_a, 4, 1, 'B', 1, -1),                 # SBC A,B
            0x99: partial(self.add_a, 4, 1, 'C', 1, -1),                 # SBC A,C
            0x9A: partial(self.add_a, 4, 1, 'D', 1, -1),                 # SBC A,D
            0x9B: partial(self.add_a, 4, 1, 'E', 1, -1),                 # SBC A,E
            0x9C: partial(self.add_a, 4, 1, 'H', 1, -1),                 # SBC A,H
            0x9D: partial(self.add_a, 4, 1, 'L', 1, -1),                 # SBC A,L
            0x9E: partial(self.add_a, 7, 1, '(HL)', 1, -1),              # SBC A,(HL)
            0x9F: partial(self.add_a, 4, 1, 'A', 1, -1),                 # SBC A,A
            0xA0: partial(self.and_r, 'B'),                              # AND B
            0xA1: partial(self.and_r, 'C'),                              # AND C
            0xA2: partial(self.and_r, 'D'),                              # AND D
            0xA3: partial(self.and_r, 'E'),                              # AND E
            0xA4: partial(self.and_r, 'H'),                              # AND H
            0xA5: partial(self.and_r, 'L'),                              # AND L
            0xA6: partial(self.anda, 7, 1, '(HL)'),                      # AND (HL)
            0xA7: partial(self.and_r, 'A'),                              # AND A
            0xA8: partial(self.xor_r, 'B'),                              # XOR B
            0xA9: partial(self.xor_r, 'C'),                              # XOR C
            0xAA: partial(self.xor_r, 'D'),                              # XOR D
            0xAB: partial(self.xor_r, 'E'),                              # XOR E
            0xAC: partial(self.xor_r, 'H'),                              # XOR H
            0xAD: partial(self.xor_r, 'L'),                              # XOR L
            0xAE: partial(self.xor, 7, 1, '(HL)'),                       # XOR (HL)
            0xAF: partial(self.xor_r, 'A'),                              # XOR A
            0xB0: partial(self.or_r, 'B'),                               # OR B
            0xB1: partial(self.or_r, 'C'),                               # OR C
            0xB2: partial(self.or_r, 'D'),                               # OR D
            0xB3: partial(self.or_r, 'E'),                               # OR E
            0xB4: partial(self.or_r, 'H'),                               # OR H
            0xB5: partial(self.or_r, 'L'),                               # OR L
            0xB6: partial(self.ora, 7, 1, '(HL)'),                       # OR (HL)
            0xB7: partial(self.or_r, 'A'),                               # OR A
            0xB8: partial(self.cp, 4, 1, 'B'),                           # CP B
            0xB9: partial(self.cp, 4, 1, 'C'),                           # CP C
            0xBA: partial(self.cp, 4, 1, 'D'),                           # CP D
            0xBB: partial(self.cp, 4, 1, 'E'),                           # CP E
            0xBC: partial(self.cp, 4, 1, 'H'),                           # CP H
            0xBD: partial(self.cp, 4, 1, 'L'),                           # CP L
            0xBE: partial(self.cp, 7, 1, '(HL)'),                        # CP (HL)
            0xBF: partial(self.cp, 4, 1, 'A'),                           # CP A
            0xC0: partial(self.ret, 'RET NZ', 64, 64),                   # RET NZ
            0xC1: partial(self.pop, 'BC'),                               # POP BC
            0xC2: partial(self.jp, 'NZ', 64, 64),                        # JP NZ,nn
            0xC3: partial(self.jp, '', 0, 0),                            # JP nn
            0xC4: partial(self.call, 'NZ', 64, 64),                      # CALL NZ,nn
            0xC5: partial(self.push, 'BC'),                              # PUSH BC
            0xC6: partial(self.add_a, 7, 2),                             # ADD A,n
            0xC7: partial(self.rst, 0),                                  # RST $00
            0xC8: partial(self.ret, 'RET Z', 64, 0),                     # RET Z
            0xC9: partial(self.ret, 'RET', 0, 0),                        # RET
            0xCA: partial(self.jp, 'Z', 64, 0),                          # JP Z,nn
            0xCB: None,                                                  # CB prefix
            0xCC: partial(self.call, 'Z', 64, 0),                        # CALL Z,nn
            0xCD: partial(self.call, '', 0, 0),                          # CALL nn
            0xCE: partial(self.add_a, 7, 2, None, 1, 1),                 # ADC A,n
            0xCF: partial(self.rst, 8),                                  # RST $08
            0xD0: partial(self.ret, 'RET NC', 1, 1),                     # RET NC
            0xD1: partial(self.pop, 'DE'),                               # POP DE
            0xD2: partial(self.jp, 'NC', 1, 1),                          # JP NC,nn
            0xD3: self.outa,                                             # OUT (n),A
            0xD4: partial(self.call, 'NC', 1, 1),                        # CALL NC,nn
            0xD5: partial(self.push, 'DE'),                              # PUSH DE
            0xD6: partial(self.add_a, 7, 2, None, 0, -1),                # SUB n
            0xD7: partial(self.rst, 16),                                 # RST $10
            0xD8: partial(self.ret, 'RET C', 1, 0),                      # RET C
            0xD9: self.exx,                                              # EXX
            0xDA: partial(self.jp, 'C', 1, 0),                           # JP C,nn
            0xDB: self.in_a,                                             # IN A,(n)
            0xDC: partial(self.call, 'C', 1, 0),                         # CALL C,nn
            0xDD: None,                                                  # DD prefix
            0xDE: partial(self.add_a, 7, 2, None, 1, -1),                # SBC A,n
            0xDF: partial(self.rst, 24),                                 # RST $18
            0xE0: partial(self.ret, 'RET PO', 4, 4),                     # RET PO
            0xE1: partial(self.pop, 'HL'),                               # POP HL
            0xE2: partial(self.jp, 'PO', 4, 4),                          # JP PO,nn
            0xE3: partial(self.ex_sp, 'HL'),                             # EX (SP),HL
            0xE4: partial(self.call, 'PO', 4, 4),                        # CALL PO,nn
            0xE5: partial(self.push, 'HL'),                              # PUSH HL
            0xE6: self.and_n,                                            # AND n
            0xE7: partial(self.rst, 32),                                 # RST $20
            0xE8: partial(self.ret, 'RET PE', 4, 0),                     # RET PE
            0xE9: partial(self.jp, '', 0, 0),                            # JP (HL)
            0xEA: partial(self.jp, 'PE', 4, 0),                          # JP PE,nn
            0xEB: self.ex_de_hl,                                         # EX DE,HL
            0xEC: partial(self.call, 'PE', 4, 0),                        # CALL PE,nn
            0xED: None,                                                  # ED prefix
            0xEE: self.xor_n,                                            # XOR n
            0xEF: partial(self.rst, 40),                                 # RST $28
            0xF0: partial(self.ret, 'RET P', 128, 128),                  # RET P
            0xF1: partial(self.pop, 'AF'),                               # POP AF
            0xF2: partial(self.jp, 'P', 128, 128),                       # JP P,nn
            0xF3: partial(self.di_ei, 'DI', 0),                          # DI
            0xF4: partial(self.call, 'P', 128, 128),                     # CALL P,nn
            0xF5: partial(self.push, 'AF'),                              # PUSH AF
            0xF6: self.or_n,                                             # OR n
            0xF7: partial(self.rst, 48),                                 # RST $30
            0xF8: partial(self.ret, 'RET M', 128, 0),                    # RET M
            0xF9: partial(self.ldsprr, 'HL'),                            # LD SP,HL
            0xFA: partial(self.jp, 'M', 128, 0),                         # JP M,nn
            0xFB: partial(self.di_ei, 'EI', 1),                          # EI
            0xFC: partial(self.call, 'M', 128, 0),                       # CALL M,nn
            0xFD: None,                                                  # FD prefix
            0xFE: partial(self.cp, 7, 2),                                # CP n
            0xFF: partial(self.rst, 56),                                 # RST $38
        }

        self.after_CB = {
            0x00: partial(self.rotate_r, 'RLC B', 128, 'B', 1),          # RLC B
            0x01: partial(self.rotate_r, 'RLC C', 128, 'C', 1),          # RLC C
            0x02: partial(self.rotate_r, 'RLC D', 128, 'D', 1),          # RLC D
            0x03: partial(self.rotate_r, 'RLC E', 128, 'E', 1),          # RLC E
            0x04: partial(self.rotate_r, 'RLC H', 128, 'H', 1),          # RLC H
            0x05: partial(self.rotate_r, 'RLC L', 128, 'L', 1),          # RLC L
            0x06: partial(self.rotate, 15, 2, 'RLC', 128, '(HL)', 1),    # RLC (HL)
            0x07: partial(self.rotate_r, 'RLC A', 128, 'A', 1),          # RLC A
            0x08: partial(self.rotate_r, 'RRC B', 1, 'B', 1),            # RRC B
            0x09: partial(self.rotate_r, 'RRC C', 1, 'C', 1),            # RRC C
            0x0A: partial(self.rotate_r, 'RRC D', 1, 'D', 1),            # RRC D
            0x0B: partial(self.rotate_r, 'RRC E', 1, 'E', 1),            # RRC E
            0x0C: partial(self.rotate_r, 'RRC H', 1, 'H', 1),            # RRC H
            0x0D: partial(self.rotate_r, 'RRC L', 1, 'L', 1),            # RRC L
            0x0E: partial(self.rotate, 15, 2, 'RRC', 1, '(HL)', 1),      # RRC (HL)
            0x0F: partial(self.rotate_r, 'RRC A', 1, 'A', 1),            # RRC A
            0x10: partial(self.rotate_r, 'RL B', 128, 'B'),              # RL B
            0x11: partial(self.rotate_r, 'RL C', 128, 'C'),              # RL C
            0x12: partial(self.rotate_r, 'RL D', 128, 'D'),              # RL D
            0x13: partial(self.rotate_r, 'RL E', 128, 'E'),              # RL E
            0x14: partial(self.rotate_r, 'RL H', 128, 'H'),              # RL H
            0x15: partial(self.rotate_r, 'RL L', 128, 'L'),              # RL L
            0x16: partial(self.rotate, 15, 2, 'RL', 128, '(HL)'),        # RL (HL)
            0x17: partial(self.rotate_r, 'RL A', 128, 'A'),              # RL A
            0x18: partial(self.rotate_r, 'RR B', 1, 'B'),                # RR B
            0x19: partial(self.rotate_r, 'RR C', 1, 'C'),                # RR C
            0x1A: partial(self.rotate_r, 'RR D', 1, 'D'),                # RR D
            0x1B: partial(self.rotate_r, 'RR E', 1, 'E'),                # RR E
            0x1C: partial(self.rotate_r, 'RR H', 1, 'H'),                # RR H
            0x1D: partial(self.rotate_r, 'RR L', 1, 'L'),                # RR L
            0x1E: partial(self.rotate, 15, 2, 'RR', 1, '(HL)'),          # RR (HL)
            0x1F: partial(self.rotate_r, 'RR A', 1, 'A'),                # RR A
            0x20: partial(self.shift, 8, 2, 'SLA', 128, 'B'),            # SLA B
            0x21: partial(self.shift, 8, 2, 'SLA', 128, 'C'),            # SLA C
            0x22: partial(self.shift, 8, 2, 'SLA', 128, 'D'),            # SLA D
            0x23: partial(self.shift, 8, 2, 'SLA', 128, 'E'),            # SLA E
            0x24: partial(self.shift, 8, 2, 'SLA', 128, 'H'),            # SLA H
            0x25: partial(self.shift, 8, 2, 'SLA', 128, 'L'),            # SLA L
            0x26: partial(self.shift, 15, 2, 'SLA', 128, '(HL)'),        # SLA (HL)
            0x27: partial(self.shift, 8, 2, 'SLA', 128, 'A'),            # SLA A
            0x28: partial(self.shift, 8, 2, 'SRA', 1, 'B'),              # SRA B
            0x29: partial(self.shift, 8, 2, 'SRA', 1, 'C'),              # SRA C
            0x2A: partial(self.shift, 8, 2, 'SRA', 1, 'D'),              # SRA D
            0x2B: partial(self.shift, 8, 2, 'SRA', 1, 'E'),              # SRA E
            0x2C: partial(self.shift, 8, 2, 'SRA', 1, 'H'),              # SRA H
            0x2D: partial(self.shift, 8, 2, 'SRA', 1, 'L'),              # SRA L
            0x2E: partial(self.shift, 15, 2, 'SRA', 1, '(HL)'),          # SRA (HL)
            0x2F: partial(self.shift, 8, 2, 'SRA', 1, 'A'),              # SRA A
            0x30: partial(self.shift, 8, 2, 'SLL', 128, 'B'),            # SLL B
            0x31: partial(self.shift, 8, 2, 'SLL', 128, 'C'),            # SLL C
            0x32: partial(self.shift, 8, 2, 'SLL', 128, 'D'),            # SLL D
            0x33: partial(self.shift, 8, 2, 'SLL', 128, 'E'),            # SLL E
            0x34: partial(self.shift, 8, 2, 'SLL', 128, 'H'),            # SLL H
            0x35: partial(self.shift, 8, 2, 'SLL', 128, 'L'),            # SLL L
            0x36: partial(self.shift, 15, 2, 'SLL', 128, '(HL)'),        # SLL (HL)
            0x37: partial(self.shift, 8, 2, 'SLL', 128, 'A'),            # SLL A
            0x38: partial(self.shift, 8, 2, 'SRL', 1, 'B'),              # SRL B
            0x39: partial(self.shift, 8, 2, 'SRL', 1, 'C'),              # SRL C
            0x3A: partial(self.shift, 8, 2, 'SRL', 1, 'D'),              # SRL D
            0x3B: partial(self.shift, 8, 2, 'SRL', 1, 'E'),              # SRL E
            0x3C: partial(self.shift, 8, 2, 'SRL', 1, 'H'),              # SRL H
            0x3D: partial(self.shift, 8, 2, 'SRL', 1, 'L'),              # SRL L
            0x3E: partial(self.shift, 15, 2, 'SRL', 1, '(HL)'),          # SRL (HL)
            0x3F: partial(self.shift, 8, 2, 'SRL', 1, 'A'),              # SRL A
            0x40: partial(self.bit, 8, 2, 0, 'B'),                       # BIT 0,B
            0x41: partial(self.bit, 8, 2, 0, 'C'),                       # BIT 0,C
            0x42: partial(self.bit, 8, 2, 0, 'D'),                       # BIT 0,D
            0x43: partial(self.bit, 8, 2, 0, 'E'),                       # BIT 0,E
            0x44: partial(self.bit, 8, 2, 0, 'H'),                       # BIT 0,H
            0x45: partial(self.bit, 8, 2, 0, 'L'),                       # BIT 0,L
            0x46: partial(self.bit, 12, 2, 0, '(HL)'),                   # BIT 0,(HL)
            0x47: partial(self.bit, 8, 2, 0, 'A'),                       # BIT 0,A
            0x48: partial(self.bit, 8, 2, 1, 'B'),                       # BIT 1,B
            0x49: partial(self.bit, 8, 2, 1, 'C'),                       # BIT 1,C
            0x4A: partial(self.bit, 8, 2, 1, 'D'),                       # BIT 1,D
            0x4B: partial(self.bit, 8, 2, 1, 'E'),                       # BIT 1,E
            0x4C: partial(self.bit, 8, 2, 1, 'H'),                       # BIT 1,H
            0x4D: partial(self.bit, 8, 2, 1, 'L'),                       # BIT 1,L
            0x4E: partial(self.bit, 12, 2, 1, '(HL)'),                   # BIT 1,(HL)
            0x4F: partial(self.bit, 8, 2, 1, 'A'),                       # BIT 1,A
            0x50: partial(self.bit, 8, 2, 2, 'B'),                       # BIT 2,B
            0x51: partial(self.bit, 8, 2, 2, 'C'),                       # BIT 2,C
            0x52: partial(self.bit, 8, 2, 2, 'D'),                       # BIT 2,D
            0x53: partial(self.bit, 8, 2, 2, 'E'),                       # BIT 2,E
            0x54: partial(self.bit, 8, 2, 2, 'H'),                       # BIT 2,H
            0x55: partial(self.bit, 8, 2, 2, 'L'),                       # BIT 2,L
            0x56: partial(self.bit, 12, 2, 2, '(HL)'),                   # BIT 2,(HL)
            0x57: partial(self.bit, 8, 2, 2, 'A'),                       # BIT 2,A
            0x58: partial(self.bit, 8, 2, 3, 'B'),                       # BIT 3,B
            0x59: partial(self.bit, 8, 2, 3, 'C'),                       # BIT 3,C
            0x5A: partial(self.bit, 8, 2, 3, 'D'),                       # BIT 3,D
            0x5B: partial(self.bit, 8, 2, 3, 'E'),                       # BIT 3,E
            0x5C: partial(self.bit, 8, 2, 3, 'H'),                       # BIT 3,H
            0x5D: partial(self.bit, 8, 2, 3, 'L'),                       # BIT 3,L
            0x5E: partial(self.bit, 12, 2, 3, '(HL)'),                   # BIT 3,(HL)
            0x5F: partial(self.bit, 8, 2, 3, 'A'),                       # BIT 3,A
            0x60: partial(self.bit, 8, 2, 4, 'B'),                       # BIT 4,B
            0x61: partial(self.bit, 8, 2, 4, 'C'),                       # BIT 4,C
            0x62: partial(self.bit, 8, 2, 4, 'D'),                       # BIT 4,D
            0x63: partial(self.bit, 8, 2, 4, 'E'),                       # BIT 4,E
            0x64: partial(self.bit, 8, 2, 4, 'H'),                       # BIT 4,H
            0x65: partial(self.bit, 8, 2, 4, 'L'),                       # BIT 4,L
            0x66: partial(self.bit, 12, 2, 4, '(HL)'),                   # BIT 4,(HL)
            0x67: partial(self.bit, 8, 2, 4, 'A'),                       # BIT 4,A
            0x68: partial(self.bit, 8, 2, 5, 'B'),                       # BIT 5,B
            0x69: partial(self.bit, 8, 2, 5, 'C'),                       # BIT 5,C
            0x6A: partial(self.bit, 8, 2, 5, 'D'),                       # BIT 5,D
            0x6B: partial(self.bit, 8, 2, 5, 'E'),                       # BIT 5,E
            0x6C: partial(self.bit, 8, 2, 5, 'H'),                       # BIT 5,H
            0x6D: partial(self.bit, 8, 2, 5, 'L'),                       # BIT 5,L
            0x6E: partial(self.bit, 12, 2, 5, '(HL)'),                   # BIT 5,(HL)
            0x6F: partial(self.bit, 8, 2, 5, 'A'),                       # BIT 5,A
            0x70: partial(self.bit, 8, 2, 6, 'B'),                       # BIT 6,B
            0x71: partial(self.bit, 8, 2, 6, 'C'),                       # BIT 6,C
            0x72: partial(self.bit, 8, 2, 6, 'D'),                       # BIT 6,D
            0x73: partial(self.bit, 8, 2, 6, 'E'),                       # BIT 6,E
            0x74: partial(self.bit, 8, 2, 6, 'H'),                       # BIT 6,H
            0x75: partial(self.bit, 8, 2, 6, 'L'),                       # BIT 6,L
            0x76: partial(self.bit, 12, 2, 6, '(HL)'),                   # BIT 6,(HL)
            0x77: partial(self.bit, 8, 2, 6, 'A'),                       # BIT 6,A
            0x78: partial(self.bit, 8, 2, 7, 'B'),                       # BIT 7,B
            0x79: partial(self.bit, 8, 2, 7, 'C'),                       # BIT 7,C
            0x7A: partial(self.bit, 8, 2, 7, 'D'),                       # BIT 7,D
            0x7B: partial(self.bit, 8, 2, 7, 'E'),                       # BIT 7,E
            0x7C: partial(self.bit, 8, 2, 7, 'H'),                       # BIT 7,H
            0x7D: partial(self.bit, 8, 2, 7, 'L'),                       # BIT 7,L
            0x7E: partial(self.bit, 12, 2, 7, '(HL)'),                   # BIT 7,(HL)
            0x7F: partial(self.bit, 8, 2, 7, 'A'),                       # BIT 7,A
            0x80: partial(self.res_set, 8, 2, 0, 'B', 0),                # RES 0,B
            0x81: partial(self.res_set, 8, 2, 0, 'C', 0),                # RES 0,C
            0x82: partial(self.res_set, 8, 2, 0, 'D', 0),                # RES 0,D
            0x83: partial(self.res_set, 8, 2, 0, 'E', 0),                # RES 0,E
            0x84: partial(self.res_set, 8, 2, 0, 'H', 0),                # RES 0,H
            0x85: partial(self.res_set, 8, 2, 0, 'L', 0),                # RES 0,L
            0x86: partial(self.res_set, 15, 2, 0, '(HL)', 0),            # RES 0,(HL)
            0x87: partial(self.res_set, 8, 2, 0, 'A', 0),                # RES 0,A
            0x88: partial(self.res_set, 8, 2, 1, 'B', 0),                # RES 1,B
            0x89: partial(self.res_set, 8, 2, 1, 'C', 0),                # RES 1,C
            0x8A: partial(self.res_set, 8, 2, 1, 'D', 0),                # RES 1,D
            0x8B: partial(self.res_set, 8, 2, 1, 'E', 0),                # RES 1,E
            0x8C: partial(self.res_set, 8, 2, 1, 'H', 0),                # RES 1,H
            0x8D: partial(self.res_set, 8, 2, 1, 'L', 0),                # RES 1,L
            0x8E: partial(self.res_set, 15, 2, 1, '(HL)', 0),            # RES 1,(HL)
            0x8F: partial(self.res_set, 8, 2, 1, 'A', 0),                # RES 1,A
            0x90: partial(self.res_set, 8, 2, 2, 'B', 0),                # RES 2,B
            0x91: partial(self.res_set, 8, 2, 2, 'C', 0),                # RES 2,C
            0x92: partial(self.res_set, 8, 2, 2, 'D', 0),                # RES 2,D
            0x93: partial(self.res_set, 8, 2, 2, 'E', 0),                # RES 2,E
            0x94: partial(self.res_set, 8, 2, 2, 'H', 0),                # RES 2,H
            0x95: partial(self.res_set, 8, 2, 2, 'L', 0),                # RES 2,L
            0x96: partial(self.res_set, 15, 2, 2, '(HL)', 0),            # RES 2,(HL)
            0x97: partial(self.res_set, 8, 2, 2, 'A', 0),                # RES 2,A
            0x98: partial(self.res_set, 8, 2, 3, 'B', 0),                # RES 3,B
            0x99: partial(self.res_set, 8, 2, 3, 'C', 0),                # RES 3,C
            0x9A: partial(self.res_set, 8, 2, 3, 'D', 0),                # RES 3,D
            0x9B: partial(self.res_set, 8, 2, 3, 'E', 0),                # RES 3,E
            0x9C: partial(self.res_set, 8, 2, 3, 'H', 0),                # RES 3,H
            0x9D: partial(self.res_set, 8, 2, 3, 'L', 0),                # RES 3,L
            0x9E: partial(self.res_set, 15, 2, 3, '(HL)', 0),            # RES 3,(HL)
            0x9F: partial(self.res_set, 8, 2, 3, 'A', 0),                # RES 3,A
            0xA0: partial(self.res_set, 8, 2, 4, 'B', 0),                # RES 4,B
            0xA1: partial(self.res_set, 8, 2, 4, 'C', 0),                # RES 4,C
            0xA2: partial(self.res_set, 8, 2, 4, 'D', 0),                # RES 4,D
            0xA3: partial(self.res_set, 8, 2, 4, 'E', 0),                # RES 4,E
            0xA4: partial(self.res_set, 8, 2, 4, 'H', 0),                # RES 4,H
            0xA5: partial(self.res_set, 8, 2, 4, 'L', 0),                # RES 4,L
            0xA6: partial(self.res_set, 15, 2, 4, '(HL)', 0),            # RES 4,(HL)
            0xA7: partial(self.res_set, 8, 2, 4, 'A', 0),                # RES 4,A
            0xA8: partial(self.res_set, 8, 2, 5, 'B', 0),                # RES 5,B
            0xA9: partial(self.res_set, 8, 2, 5, 'C', 0),                # RES 5,C
            0xAA: partial(self.res_set, 8, 2, 5, 'D', 0),                # RES 5,D
            0xAB: partial(self.res_set, 8, 2, 5, 'E', 0),                # RES 5,E
            0xAC: partial(self.res_set, 8, 2, 5, 'H', 0),                # RES 5,H
            0xAD: partial(self.res_set, 8, 2, 5, 'L', 0),                # RES 5,L
            0xAE: partial(self.res_set, 15, 2, 5, '(HL)', 0),            # RES 5,(HL)
            0xAF: partial(self.res_set, 8, 2, 5, 'A', 0),                # RES 5,A
            0xB0: partial(self.res_set, 8, 2, 6, 'B', 0),                # RES 6,B
            0xB1: partial(self.res_set, 8, 2, 6, 'C', 0),                # RES 6,C
            0xB2: partial(self.res_set, 8, 2, 6, 'D', 0),                # RES 6,D
            0xB3: partial(self.res_set, 8, 2, 6, 'E', 0),                # RES 6,E
            0xB4: partial(self.res_set, 8, 2, 6, 'H', 0),                # RES 6,H
            0xB5: partial(self.res_set, 8, 2, 6, 'L', 0),                # RES 6,L
            0xB6: partial(self.res_set, 15, 2, 6, '(HL)', 0),            # RES 6,(HL)
            0xB7: partial(self.res_set, 8, 2, 6, 'A', 0),                # RES 6,A
            0xB8: partial(self.res_set, 8, 2, 7, 'B', 0),                # RES 7,B
            0xB9: partial(self.res_set, 8, 2, 7, 'C', 0),                # RES 7,C
            0xBA: partial(self.res_set, 8, 2, 7, 'D', 0),                # RES 7,D
            0xBB: partial(self.res_set, 8, 2, 7, 'E', 0),                # RES 7,E
            0xBC: partial(self.res_set, 8, 2, 7, 'H', 0),                # RES 7,H
            0xBD: partial(self.res_set, 8, 2, 7, 'L', 0),                # RES 7,L
            0xBE: partial(self.res_set, 15, 2, 7, '(HL)', 0),            # RES 7,(HL)
            0xBF: partial(self.res_set, 8, 2, 7, 'A', 0),                # RES 7,A
            0xC0: partial(self.res_set, 8, 2, 0, 'B', 1),                # SET 0,B
            0xC1: partial(self.res_set, 8, 2, 0, 'C', 1),                # SET 0,C
            0xC2: partial(self.res_set, 8, 2, 0, 'D', 1),                # SET 0,D
            0xC3: partial(self.res_set, 8, 2, 0, 'E', 1),                # SET 0,E
            0xC4: partial(self.res_set, 8, 2, 0, 'H', 1),                # SET 0,H
            0xC5: partial(self.res_set, 8, 2, 0, 'L', 1),                # SET 0,L
            0xC6: partial(self.res_set, 15, 2, 0, '(HL)', 1),            # SET 0,(HL)
            0xC7: partial(self.res_set, 8, 2, 0, 'A', 1),                # SET 0,A
            0xC8: partial(self.res_set, 8, 2, 1, 'B', 1),                # SET 1,B
            0xC9: partial(self.res_set, 8, 2, 1, 'C', 1),                # SET 1,C
            0xCA: partial(self.res_set, 8, 2, 1, 'D', 1),                # SET 1,D
            0xCB: partial(self.res_set, 8, 2, 1, 'E', 1),                # SET 1,E
            0xCC: partial(self.res_set, 8, 2, 1, 'H', 1),                # SET 1,H
            0xCD: partial(self.res_set, 8, 2, 1, 'L', 1),                # SET 1,L
            0xCE: partial(self.res_set, 15, 2, 1, '(HL)', 1),            # SET 1,(HL)
            0xCF: partial(self.res_set, 8, 2, 1, 'A', 1),                # SET 1,A
            0xD0: partial(self.res_set, 8, 2, 2, 'B', 1),                # SET 2,B
            0xD1: partial(self.res_set, 8, 2, 2, 'C', 1),                # SET 2,C
            0xD2: partial(self.res_set, 8, 2, 2, 'D', 1),                # SET 2,D
            0xD3: partial(self.res_set, 8, 2, 2, 'E', 1),                # SET 2,E
            0xD4: partial(self.res_set, 8, 2, 2, 'H', 1),                # SET 2,H
            0xD5: partial(self.res_set, 8, 2, 2, 'L', 1),                # SET 2,L
            0xD6: partial(self.res_set, 15, 2, 2, '(HL)', 1),            # SET 2,(HL)
            0xD7: partial(self.res_set, 8, 2, 2, 'A', 1),                # SET 2,A
            0xD8: partial(self.res_set, 8, 2, 3, 'B', 1),                # SET 3,B
            0xD9: partial(self.res_set, 8, 2, 3, 'C', 1),                # SET 3,C
            0xDA: partial(self.res_set, 8, 2, 3, 'D', 1),                # SET 3,D
            0xDB: partial(self.res_set, 8, 2, 3, 'E', 1),                # SET 3,E
            0xDC: partial(self.res_set, 8, 2, 3, 'H', 1),                # SET 3,H
            0xDD: partial(self.res_set, 8, 2, 3, 'L', 1),                # SET 3,L
            0xDE: partial(self.res_set, 15, 2, 3, '(HL)', 1),            # SET 3,(HL)
            0xDF: partial(self.res_set, 8, 2, 3, 'A', 1),                # SET 3,A
            0xE0: partial(self.res_set, 8, 2, 4, 'B', 1),                # SET 4,B
            0xE1: partial(self.res_set, 8, 2, 4, 'C', 1),                # SET 4,C
            0xE2: partial(self.res_set, 8, 2, 4, 'D', 1),                # SET 4,D
            0xE3: partial(self.res_set, 8, 2, 4, 'E', 1),                # SET 4,E
            0xE4: partial(self.res_set, 8, 2, 4, 'H', 1),                # SET 4,H
            0xE5: partial(self.res_set, 8, 2, 4, 'L', 1),                # SET 4,L
            0xE6: partial(self.res_set, 15, 2, 4, '(HL)', 1),            # SET 4,(HL)
            0xE7: partial(self.res_set, 8, 2, 4, 'A', 1),                # SET 4,A
            0xE8: partial(self.res_set, 8, 2, 5, 'B', 1),                # SET 5,B
            0xE9: partial(self.res_set, 8, 2, 5, 'C', 1),                # SET 5,C
            0xEA: partial(self.res_set, 8, 2, 5, 'D', 1),                # SET 5,D
            0xEB: partial(self.res_set, 8, 2, 5, 'E', 1),                # SET 5,E
            0xEC: partial(self.res_set, 8, 2, 5, 'H', 1),                # SET 5,H
            0xED: partial(self.res_set, 8, 2, 5, 'L', 1),                # SET 5,L
            0xEE: partial(self.res_set, 15, 2, 5, '(HL)', 1),            # SET 5,(HL)
            0xEF: partial(self.res_set, 8, 2, 5, 'A', 1),                # SET 5,A
            0xF0: partial(self.res_set, 8, 2, 6, 'B', 1),                # SET 6,B
            0xF1: partial(self.res_set, 8, 2, 6, 'C', 1),                # SET 6,C
            0xF2: partial(self.res_set, 8, 2, 6, 'D', 1),                # SET 6,D
            0xF3: partial(self.res_set, 8, 2, 6, 'E', 1),                # SET 6,E
            0xF4: partial(self.res_set, 8, 2, 6, 'H', 1),                # SET 6,H
            0xF5: partial(self.res_set, 8, 2, 6, 'L', 1),                # SET 6,L
            0xF6: partial(self.res_set, 15, 2, 6, '(HL)', 1),            # SET 6,(HL)
            0xF7: partial(self.res_set, 8, 2, 6, 'A', 1),                # SET 6,A
            0xF8: partial(self.res_set, 8, 2, 7, 'B', 1),                # SET 7,B
            0xF9: partial(self.res_set, 8, 2, 7, 'C', 1),                # SET 7,C
            0xFA: partial(self.res_set, 8, 2, 7, 'D', 1),                # SET 7,D
            0xFB: partial(self.res_set, 8, 2, 7, 'E', 1),                # SET 7,E
            0xFC: partial(self.res_set, 8, 2, 7, 'H', 1),                # SET 7,H
            0xFD: partial(self.res_set, 8, 2, 7, 'L', 1),                # SET 7,L
            0xFE: partial(self.res_set, 15, 2, 7, '(HL)', 1),            # SET 7,(HL)
            0xFF: partial(self.res_set, 8, 2, 7, 'A', 1),                # SET 7,A
        }

        self.after_ED = {
            0x00: partial(self.defb, 8, 2),
            0x01: partial(self.defb, 8, 2),
            0x02: partial(self.defb, 8, 2),
            0x03: partial(self.defb, 8, 2),
            0x04: partial(self.defb, 8, 2),
            0x05: partial(self.defb, 8, 2),
            0x06: partial(self.defb, 8, 2),
            0x07: partial(self.defb, 8, 2),
            0x08: partial(self.defb, 8, 2),
            0x09: partial(self.defb, 8, 2),
            0x0A: partial(self.defb, 8, 2),
            0x0B: partial(self.defb, 8, 2),
            0x0C: partial(self.defb, 8, 2),
            0x0D: partial(self.defb, 8, 2),
            0x0E: partial(self.defb, 8, 2),
            0x0F: partial(self.defb, 8, 2),
            0x10: partial(self.defb, 8, 2),
            0x11: partial(self.defb, 8, 2),
            0x12: partial(self.defb, 8, 2),
            0x13: partial(self.defb, 8, 2),
            0x14: partial(self.defb, 8, 2),
            0x15: partial(self.defb, 8, 2),
            0x16: partial(self.defb, 8, 2),
            0x17: partial(self.defb, 8, 2),
            0x18: partial(self.defb, 8, 2),
            0x19: partial(self.defb, 8, 2),
            0x1A: partial(self.defb, 8, 2),
            0x1B: partial(self.defb, 8, 2),
            0x1C: partial(self.defb, 8, 2),
            0x1D: partial(self.defb, 8, 2),
            0x1E: partial(self.defb, 8, 2),
            0x1F: partial(self.defb, 8, 2),
            0x20: partial(self.defb, 8, 2),
            0x21: partial(self.defb, 8, 2),
            0x22: partial(self.defb, 8, 2),
            0x23: partial(self.defb, 8, 2),
            0x24: partial(self.defb, 8, 2),
            0x25: partial(self.defb, 8, 2),
            0x26: partial(self.defb, 8, 2),
            0x27: partial(self.defb, 8, 2),
            0x28: partial(self.defb, 8, 2),
            0x29: partial(self.defb, 8, 2),
            0x2A: partial(self.defb, 8, 2),
            0x2B: partial(self.defb, 8, 2),
            0x2C: partial(self.defb, 8, 2),
            0x2D: partial(self.defb, 8, 2),
            0x2E: partial(self.defb, 8, 2),
            0x2F: partial(self.defb, 8, 2),
            0x30: partial(self.defb, 8, 2),
            0x31: partial(self.defb, 8, 2),
            0x32: partial(self.defb, 8, 2),
            0x33: partial(self.defb, 8, 2),
            0x34: partial(self.defb, 8, 2),
            0x35: partial(self.defb, 8, 2),
            0x36: partial(self.defb, 8, 2),
            0x37: partial(self.defb, 8, 2),
            0x38: partial(self.defb, 8, 2),
            0x39: partial(self.defb, 8, 2),
            0x3A: partial(self.defb, 8, 2),
            0x3B: partial(self.defb, 8, 2),
            0x3C: partial(self.defb, 8, 2),
            0x3D: partial(self.defb, 8, 2),
            0x3E: partial(self.defb, 8, 2),
            0x3F: partial(self.defb, 8, 2),
            0x40: partial(self.in_c, 'B'),                               # IN B,(C)
            0x41: partial(self.outc, 'B'),                               # OUT (C),B
            0x42: partial(self.add16, 15, 2, 'HL', 'BC', 1, -1),         # SBC HL,BC
            0x43: partial(self.ld16addr, 20, 4, 'BC', 1),                # LD (nn),BC
            0x44: self.neg,                                              # NEG
            0x45: partial(self.reti, 'RETN'),                            # RETN
            0x46: partial(self.im, 0),                                   # IM 0
            0x47: partial(self.ld8, 9, 2, 'I', 'A'),                     # LD I,A
            0x48: partial(self.in_c, 'C'),                               # IN C,(C)
            0x49: partial(self.outc, 'C'),                               # OUT (C),C
            0x4A: partial(self.add16, 15, 2, 'HL', 'BC', 1),             # ADC HL,BC
            0x4B: partial(self.ld16addr, 20, 4, 'BC', 0),                # LD BC,(nn)
            0x4C: self.neg,                                              # NEG
            0x4D: partial(self.reti, 'RETI'),                            # RETI
            0x4E: partial(self.im, 0),                                   # IM 0
            0x4F: partial(self.ld8, 9, 2, 'R', 'A'),                     # LD R,A
            0x50: partial(self.in_c, 'D'),                               # IN D,(C)
            0x51: partial(self.outc, 'D'),                               # OUT (C),D
            0x52: partial(self.add16, 15, 2, 'HL', 'DE', 1, -1),         # SBC HL,DE
            0x53: partial(self.ld16addr, 20, 4, 'DE', 1),                # LD (nn),DE
            0x54: self.neg,                                              # NEG
            0x55: partial(self.reti, 'RETN'),                            # RETN
            0x56: partial(self.im, 1),                                   # IM 1
            0x57: partial(self.ld8, 9, 2, 'A', 'I'),                     # LD A,I
            0x58: partial(self.in_c, 'E'),                               # IN E,(C)
            0x59: partial(self.outc, 'E'),                               # OUT (C),E
            0x5A: partial(self.add16, 15, 2, 'HL', 'DE', 1),             # ADC HL,DE
            0x5B: partial(self.ld16addr, 20, 4, 'DE', 0),                # LD DE,(nn)
            0x5C: self.neg,                                              # NEG
            0x5D: partial(self.reti, 'RETN'),                            # RETN
            0x5E: partial(self.im, 2),                                   # IM 2
            0x5F: partial(self.ld8, 9, 2, 'A', 'R'),                     # LD A,R
            0x60: partial(self.in_c, 'H'),                               # IN H,(C)
            0x61: partial(self.outc, 'H'),                               # OUT (C),H
            0x62: partial(self.add16, 15, 2, 'HL', 'HL', 1, -1),         # SBC HL,HL
            0x63: partial(self.ld16addr, 20, 4, 'HL', 1),                # LD (nn),HL
            0x64: self.neg,                                              # NEG
            0x65: partial(self.reti, 'RETN'),                            # RETN
            0x66: partial(self.im, 0),                                   # IM 0
            0x67: self.rrd,                                              # RRD
            0x68: partial(self.in_c, 'L'),                               # IN L,(C)
            0x69: partial(self.outc, 'L'),                               # OUT (C),L
            0x6A: partial(self.add16, 15, 2, 'HL', 'HL', 1),             # ADC HL,HL
            0x6B: partial(self.ld16addr, 20, 4, 'HL', 0),                # LD HL,(nn)
            0x6C: self.neg,                                              # NEG
            0x6D: partial(self.reti, 'RETN'),                            # RETN
            0x6E: partial(self.im, 0),                                   # IM 0
            0x6F: self.rld,                                              # RLD
            0x70: partial(self.in_c, 'F'),                               # IN F,(C)
            0x71: partial(self.outc, ''),                                # OUT (C),0
            0x72: partial(self.add16, 15, 2, 'HL', 'SP', 1, -1),         # SBC HL,SP
            0x73: partial(self.ld16addr, 20, 4, 'SP', 1),                # LD (nn),SP
            0x74: self.neg,                                              # NEG
            0x75: partial(self.reti, 'RETN'),                            # RETN
            0x76: partial(self.im, 1),                                   # IM 1
            0x77: partial(self.defb, 8, 2),
            0x78: partial(self.in_c, 'A'),                               # IN A,(C)
            0x79: partial(self.outc, 'A'),                               # OUT (C),A
            0x7A: partial(self.add16, 15, 2, 'HL', 'SP', 1),             # ADC HL,SP
            0x7B: partial(self.ld16addr, 20, 4, 'SP', 0),                # LD SP,(nn)
            0x7C: self.neg,                                              # NEG
            0x7D: partial(self.reti, 'RETN'),                            # RETN
            0x7E: partial(self.im, 2),                                   # IM 2
            0x7F: partial(self.defb, 8, 2),
            0x80: partial(self.defb, 8, 2),
            0x81: partial(self.defb, 8, 2),
            0x82: partial(self.defb, 8, 2),
            0x83: partial(self.defb, 8, 2),
            0x84: partial(self.defb, 8, 2),
            0x85: partial(self.defb, 8, 2),
            0x86: partial(self.defb, 8, 2),
            0x87: partial(self.defb, 8, 2),
            0x88: partial(self.defb, 8, 2),
            0x89: partial(self.defb, 8, 2),
            0x8A: partial(self.defb, 8, 2),
            0x8B: partial(self.defb, 8, 2),
            0x8C: partial(self.defb, 8, 2),
            0x8D: partial(self.defb, 8, 2),
            0x8E: partial(self.defb, 8, 2),
            0x8F: partial(self.defb, 8, 2),
            0x90: partial(self.defb, 8, 2),
            0x91: partial(self.defb, 8, 2),
            0x92: partial(self.defb, 8, 2),
            0x93: partial(self.defb, 8, 2),
            0x94: partial(self.defb, 8, 2),
            0x95: partial(self.defb, 8, 2),
            0x96: partial(self.defb, 8, 2),
            0x97: partial(self.defb, 8, 2),
            0x98: partial(self.defb, 8, 2),
            0x99: partial(self.defb, 8, 2),
            0x9A: partial(self.defb, 8, 2),
            0x9B: partial(self.defb, 8, 2),
            0x9C: partial(self.defb, 8, 2),
            0x9D: partial(self.defb, 8, 2),
            0x9E: partial(self.defb, 8, 2),
            0x9F: partial(self.defb, 8, 2),
            0xA0: partial(self.block, 'LDI', 1, 0),                      # LDI
            0xA1: partial(self.block, 'CPI', 1, 0),                      # CPI
            0xA2: partial(self.block, 'INI', 1, 0),                      # INI
            0xA3: partial(self.block, 'OUTI', 1, 0),                     # OUTI
            0xA4: partial(self.defb, 8, 2),
            0xA5: partial(self.defb, 8, 2),
            0xA6: partial(self.defb, 8, 2),
            0xA7: partial(self.defb, 8, 2),
            0xA8: partial(self.block, 'LDD', -1, 0),                     # LDD
            0xA9: partial(self.block, 'CPD', -1, 0),                     # CPD
            0xAA: partial(self.block, 'IND', -1, 0),                     # IND
            0xAB: partial(self.block, 'OUTD', -1, 0),                    # OUTD
            0xAC: partial(self.defb, 8, 2),
            0xAD: partial(self.defb, 8, 2),
            0xAE: partial(self.defb, 8, 2),
            0xAF: partial(self.defb, 8, 2),
            0xB0: partial(self.block, 'LDIR', 1, 1),                     # LDIR
            0xB1: partial(self.block, 'CPIR', 1, 1),                     # CPIR
            0xB2: partial(self.block, 'INIR', 1, 1),                     # INIR
            0xB3: partial(self.block, 'OTIR', 1, 1),                     # OTIR
            0xB4: partial(self.defb, 8, 2),
            0xB5: partial(self.defb, 8, 2),
            0xB6: partial(self.defb, 8, 2),
            0xB7: partial(self.defb, 8, 2),
            0xB8: partial(self.block, 'LDDR', -1, 1),                    # LDDR
            0xB9: partial(self.block, 'CPDR', -1, 1),                    # CPDR
            0xBA: partial(self.block, 'INDR', -1, 1),                    # INDR
            0xBB: partial(self.block, 'OTDR', -1, 1),                    # OTDR
            0xBC: partial(self.defb, 8, 2),
            0xBD: partial(self.defb, 8, 2),
            0xBE: partial(self.defb, 8, 2),
            0xBF: partial(self.defb, 8, 2),
            0xC0: partial(self.defb, 8, 2),
            0xC1: partial(self.defb, 8, 2),
            0xC2: partial(self.defb, 8, 2),
            0xC3: partial(self.defb, 8, 2),
            0xC4: partial(self.defb, 8, 2),
            0xC5: partial(self.defb, 8, 2),
            0xC6: partial(self.defb, 8, 2),
            0xC7: partial(self.defb, 8, 2),
            0xC8: partial(self.defb, 8, 2),
            0xC9: partial(self.defb, 8, 2),
            0xCA: partial(self.defb, 8, 2),
            0xCB: partial(self.defb, 8, 2),
            0xCC: partial(self.defb, 8, 2),
            0xCD: partial(self.defb, 8, 2),
            0xCE: partial(self.defb, 8, 2),
            0xCF: partial(self.defb, 8, 2),
            0xD0: partial(self.defb, 8, 2),
            0xD1: partial(self.defb, 8, 2),
            0xD2: partial(self.defb, 8, 2),
            0xD3: partial(self.defb, 8, 2),
            0xD4: partial(self.defb, 8, 2),
            0xD5: partial(self.defb, 8, 2),
            0xD6: partial(self.defb, 8, 2),
            0xD7: partial(self.defb, 8, 2),
            0xD8: partial(self.defb, 8, 2),
            0xD9: partial(self.defb, 8, 2),
            0xDA: partial(self.defb, 8, 2),
            0xDB: partial(self.defb, 8, 2),
            0xDC: partial(self.defb, 8, 2),
            0xDD: partial(self.defb, 8, 2),
            0xDE: partial(self.defb, 8, 2),
            0xDF: partial(self.defb, 8, 2),
            0xE0: partial(self.defb, 8, 2),
            0xE1: partial(self.defb, 8, 2),
            0xE2: partial(self.defb, 8, 2),
            0xE3: partial(self.defb, 8, 2),
            0xE4: partial(self.defb, 8, 2),
            0xE5: partial(self.defb, 8, 2),
            0xE6: partial(self.defb, 8, 2),
            0xE7: partial(self.defb, 8, 2),
            0xE8: partial(self.defb, 8, 2),
            0xE9: partial(self.defb, 8, 2),
            0xEA: partial(self.defb, 8, 2),
            0xEB: partial(self.defb, 8, 2),
            0xEC: partial(self.defb, 8, 2),
            0xED: partial(self.defb, 8, 2),
            0xEE: partial(self.defb, 8, 2),
            0xEF: partial(self.defb, 8, 2),
            0xF0: partial(self.defb, 8, 2),
            0xF1: partial(self.defb, 8, 2),
            0xF2: partial(self.defb, 8, 2),
            0xF3: partial(self.defb, 8, 2),
            0xF4: partial(self.defb, 8, 2),
            0xF5: partial(self.defb, 8, 2),
            0xF6: partial(self.defb, 8, 2),
            0xF7: partial(self.defb, 8, 2),
            0xF8: partial(self.defb, 8, 2),
            0xF9: partial(self.defb, 8, 2),
            0xFA: partial(self.defb, 8, 2),
            0xFB: partial(self.defb, 8, 2),
            0xFC: partial(self.defb, 8, 2),
            0xFD: partial(self.defb, 8, 2),
            0xFE: partial(self.defb, 8, 2),
            0xFF: partial(self.defb, 8, 2),
        }

        self.after_DD = {
            0x00: partial(self.defb, 4, 1),
            0x01: partial(self.defb, 4, 1),
            0x02: partial(self.defb, 4, 1),
            0x03: partial(self.defb, 4, 1),
            0x04: partial(self.defb, 4, 1),
            0x05: partial(self.defb, 4, 1),
            0x06: partial(self.defb, 4, 1),
            0x07: partial(self.defb, 4, 1),
            0x08: partial(self.defb, 4, 1),
            0x09: partial(self.add16, 15, 2, 'IX', 'BC'),                # ADD IX,BC
            0x0A: partial(self.defb, 4, 1),
            0x0B: partial(self.defb, 4, 1),
            0x0C: partial(self.defb, 4, 1),
            0x0D: partial(self.defb, 4, 1),
            0x0E: partial(self.defb, 4, 1),
            0x0F: partial(self.defb, 4, 1),
            0x10: partial(self.defb, 4, 1),
            0x11: partial(self.defb, 4, 1),
            0x12: partial(self.defb, 4, 1),
            0x13: partial(self.defb, 4, 1),
            0x14: partial(self.defb, 4, 1),
            0x15: partial(self.defb, 4, 1),
            0x16: partial(self.defb, 4, 1),
            0x17: partial(self.defb, 4, 1),
            0x18: partial(self.defb, 4, 1),
            0x19: partial(self.add16, 15, 2, 'IX', 'DE'),                # ADD IX,DE
            0x1A: partial(self.defb, 4, 1),
            0x1B: partial(self.defb, 4, 1),
            0x1C: partial(self.defb, 4, 1),
            0x1D: partial(self.defb, 4, 1),
            0x1E: partial(self.defb, 4, 1),
            0x1F: partial(self.defb, 4, 1),
            0x20: partial(self.defb, 4, 1),
            0x21: partial(self.ld16, 'IX'),                              # LD IX,nn
            0x22: partial(self.ld16addr, 20, 4, 'IX', 1),                # LD (nn),IX
            0x23: partial(self.inc_dec16, 'INC', 'IX'),                  # INC IX
            0x24: partial(self.inc_dec8, 8, 2, 'INC', 'IXh'),            # INC IXh
            0x25: partial(self.inc_dec8, 8, 2, 'DEC', 'IXh'),            # DEC IXh
            0x26: partial(self.ld8, 11, 3, 'IXh'),                       # LD IXh,n
            0x27: partial(self.defb, 4, 1),
            0x28: partial(self.defb, 4, 1),
            0x29: partial(self.add16, 15, 2, 'IX', 'IX'),                # ADD IX,IX
            0x2A: partial(self.ld16addr, 20, 4, 'IX', 0),                # LD IX,(nn)
            0x2B: partial(self.inc_dec16, 'DEC', 'IX'),                  # DEC IX
            0x2C: partial(self.inc_dec8, 8, 2, 'INC', 'IXl'),            # INC IXl
            0x2D: partial(self.inc_dec8, 8, 2, 'DEC', 'IXl'),            # DEC IXl
            0x2E: partial(self.ld8, 11, 3, 'IXl'),                       # LD IXl,n
            0x2F: partial(self.defb, 4, 1),
            0x30: partial(self.defb, 4, 1),
            0x31: partial(self.defb, 4, 1),
            0x32: partial(self.defb, 4, 1),
            0x33: partial(self.defb, 4, 1),
            0x34: partial(self.inc_dec8, 23, 3, 'INC', 'Xd'),            # INC (IX+d)
            0x35: partial(self.inc_dec8, 23, 3, 'DEC', 'Xd'),            # DEC (IX+d)
            0x36: partial(self.ld8, 19, 4, 'Xd'),                        # LD (IX+d),n
            0x37: partial(self.defb, 4, 1),
            0x38: partial(self.defb, 4, 1),
            0x39: partial(self.add16, 15, 2, 'IX', 'SP'),                # ADD IX,SP
            0x3A: partial(self.defb, 4, 1),
            0x3B: partial(self.defb, 4, 1),
            0x3C: partial(self.defb, 4, 1),
            0x3D: partial(self.defb, 4, 1),
            0x3E: partial(self.defb, 4, 1),
            0x3F: partial(self.defb, 4, 1),
            0x40: partial(self.defb, 4, 1),
            0x41: partial(self.defb, 4, 1),
            0x42: partial(self.defb, 4, 1),
            0x43: partial(self.defb, 4, 1),
            0x44: partial(self.ld8, 8, 2, 'B', 'IXh'),                   # LD B,IXh
            0x45: partial(self.ld8, 8, 2, 'B', 'IXl'),                   # LD B,IXl
            0x46: partial(self.ld8, 19, 3, 'B', 'Xd'),                   # LD B,(IX+d)
            0x47: partial(self.defb, 4, 1),
            0x48: partial(self.defb, 4, 1),
            0x49: partial(self.defb, 4, 1),
            0x4A: partial(self.defb, 4, 1),
            0x4B: partial(self.defb, 4, 1),
            0x4C: partial(self.ld8, 8, 2, 'C', 'IXh'),                   # LD C,IXh
            0x4D: partial(self.ld8, 8, 2, 'C', 'IXl'),                   # LD C,IXl
            0x4E: partial(self.ld8, 19, 3, 'C', 'Xd'),                   # LD C,(IX+d)
            0x4F: partial(self.defb, 4, 1),
            0x50: partial(self.defb, 4, 1),
            0x51: partial(self.defb, 4, 1),
            0x52: partial(self.defb, 4, 1),
            0x53: partial(self.defb, 4, 1),
            0x54: partial(self.ld8, 8, 2, 'D', 'IXh'),                   # LD D,IXh
            0x55: partial(self.ld8, 8, 2, 'D', 'IXl'),                   # LD D,IXl
            0x56: partial(self.ld8, 19, 3, 'D', 'Xd'),                   # LD D,(IX+d)
            0x57: partial(self.defb, 4, 1),
            0x58: partial(self.defb, 4, 1),
            0x59: partial(self.defb, 4, 1),
            0x5A: partial(self.defb, 4, 1),
            0x5B: partial(self.defb, 4, 1),
            0x5C: partial(self.ld8, 8, 2, 'E', 'IXh'),                   # LD E,IXh
            0x5D: partial(self.ld8, 8, 2, 'E', 'IXl'),                   # LD E,IXl
            0x5E: partial(self.ld8, 19, 3, 'E', 'Xd'),                   # LD E,(IX+d)
            0x5F: partial(self.defb, 4, 1),
            0x60: partial(self.ld8, 8, 2, 'IXh', 'B'),                   # LD IXh,B
            0x61: partial(self.ld8, 8, 2, 'IXh', 'C'),                   # LD IXh,C
            0x62: partial(self.ld8, 8, 2, 'IXh', 'D'),                   # LD IXh,D
            0x63: partial(self.ld8, 8, 2, 'IXh', 'E'),                   # LD IXh,E
            0x64: partial(self.ld8, 8, 2, 'IXh', 'IXh'),                 # LD IXh,IXh
            0x65: partial(self.ld8, 8, 2, 'IXh', 'IXl'),                 # LD IXh,IXl
            0x66: partial(self.ld8, 19, 3, 'H', 'Xd'),                   # LD H,(IX+d)
            0x67: partial(self.ld8, 8, 2, 'IXh', 'A'),                   # LD IXh,A
            0x68: partial(self.ld8, 8, 2, 'IXl', 'B'),                   # LD IXl,B
            0x69: partial(self.ld8, 8, 2, 'IXl', 'C'),                   # LD IXl,C
            0x6A: partial(self.ld8, 8, 2, 'IXl', 'D'),                   # LD IXl,D
            0x6B: partial(self.ld8, 8, 2, 'IXl', 'E'),                   # LD IXl,E
            0x6C: partial(self.ld8, 8, 2, 'IXl', 'IXh'),                 # LD IXl,IXh
            0x6D: partial(self.ld8, 8, 2, 'IXl', 'IXl'),                 # LD IXl,IXl
            0x6E: partial(self.ld8, 19, 3, 'L', 'Xd'),                   # LD L,(IX+d)
            0x6F: partial(self.ld8, 8, 2, 'IXl', 'A'),                   # LD IXl,A
            0x70: partial(self.ld8, 19, 3, 'Xd', 'B'),                   # LD (IX+d),B
            0x71: partial(self.ld8, 19, 3, 'Xd', 'C'),                   # LD (IX+d),C
            0x72: partial(self.ld8, 19, 3, 'Xd', 'D'),                   # LD (IX+d),D
            0x73: partial(self.ld8, 19, 3, 'Xd', 'E'),                   # LD (IX+d),E
            0x74: partial(self.ld8, 19, 3, 'Xd', 'H'),                   # LD (IX+d),H
            0x75: partial(self.ld8, 19, 3, 'Xd', 'L'),                   # LD (IX+d),L
            0x76: partial(self.defb, 4, 1),
            0x77: partial(self.ld8, 19, 3, 'Xd', 'A'),                   # LD (IX+d),A
            0x78: partial(self.defb, 4, 1),
            0x79: partial(self.defb, 4, 1),
            0x7A: partial(self.defb, 4, 1),
            0x7B: partial(self.defb, 4, 1),
            0x7C: partial(self.ld8, 8, 2, 'A', 'IXh'),                   # LD A,IXh
            0x7D: partial(self.ld8, 8, 2, 'A', 'IXl'),                   # LD A,IXl
            0x7E: partial(self.ld8, 19, 3, 'A', 'Xd'),                   # LD A,(IX+d)
            0x7F: partial(self.defb, 4, 1),
            0x80: partial(self.defb, 4, 1),
            0x81: partial(self.defb, 4, 1),
            0x82: partial(self.defb, 4, 1),
            0x83: partial(self.defb, 4, 1),
            0x84: partial(self.add_a, 8, 2, 'IXh'),                      # ADD A,IXh
            0x85: partial(self.add_a, 8, 2, 'IXl'),                      # ADD A,IXl
            0x86: partial(self.add_a, 19, 3, 'Xd'),                      # ADD A,(IX+d)
            0x87: partial(self.defb, 4, 1),
            0x88: partial(self.defb, 4, 1),
            0x89: partial(self.defb, 4, 1),
            0x8A: partial(self.defb, 4, 1),
            0x8B: partial(self.defb, 4, 1),
            0x8C: partial(self.add_a, 8, 2, 'IXh', 1),                   # ADC A,IXh
            0x8D: partial(self.add_a, 8, 2, 'IXl', 1),                   # ADC A,IXl
            0x8E: partial(self.add_a, 19, 3, 'Xd', 1),                   # ADC A,(IX+d)
            0x8F: partial(self.defb, 4, 1),
            0x90: partial(self.defb, 4, 1),
            0x91: partial(self.defb, 4, 1),
            0x92: partial(self.defb, 4, 1),
            0x93: partial(self.defb, 4, 1),
            0x94: partial(self.add_a, 8, 2, 'IXh', 0, -1),               # SUB IXh
            0x95: partial(self.add_a, 8, 2, 'IXl', 0, -1),               # SUB IXl
            0x96: partial(self.add_a, 19, 3, 'Xd', 0, -1),               # SUB (IX+d)
            0x97: partial(self.defb, 4, 1),
            0x98: partial(self.defb, 4, 1),
            0x99: partial(self.defb, 4, 1),
            0x9A: partial(self.defb, 4, 1),
            0x9B: partial(self.defb, 4, 1),
            0x9C: partial(self.add_a, 8, 2, 'IXh', 1, -1),               # SBC A,IXh
            0x9D: partial(self.add_a, 8, 2, 'IXl', 1, -1),               # SBC A,IXl
            0x9E: partial(self.add_a, 19, 3, 'Xd', 1, -1),               # SBC A,(IX+d)
            0x9F: partial(self.defb, 4, 1),
            0xA0: partial(self.defb, 4, 1),
            0xA1: partial(self.defb, 4, 1),
            0xA2: partial(self.defb, 4, 1),
            0xA3: partial(self.defb, 4, 1),
            0xA4: partial(self.anda, 8, 2, 'IXh'),                       # AND IXh
            0xA5: partial(self.anda, 8, 2, 'IXl'),                       # AND IXl
            0xA6: partial(self.anda, 19, 3, 'Xd'),                       # AND (IX+d)
            0xA7: partial(self.defb, 4, 1),
            0xA8: partial(self.defb, 4, 1),
            0xA9: partial(self.defb, 4, 1),
            0xAA: partial(self.defb, 4, 1),
            0xAB: partial(self.defb, 4, 1),
            0xAC: partial(self.xor, 8, 2, 'IXh'),                        # XOR IXh
            0xAD: partial(self.xor, 8, 2, 'IXl'),                        # XOR IXl
            0xAE: partial(self.xor, 19, 3, 'Xd'),                        # XOR (IX+d)
            0xAF: partial(self.defb, 4, 1),
            0xB0: partial(self.defb, 4, 1),
            0xB1: partial(self.defb, 4, 1),
            0xB2: partial(self.defb, 4, 1),
            0xB3: partial(self.defb, 4, 1),
            0xB4: partial(self.ora, 8, 2, 'IXh'),                        # OR IXh
            0xB5: partial(self.ora, 8, 2, 'IXl'),                        # OR IXl
            0xB6: partial(self.ora, 19, 3, 'Xd'),                        # OR (IX+d)
            0xB7: partial(self.defb, 4, 1),
            0xB8: partial(self.defb, 4, 1),
            0xB9: partial(self.defb, 4, 1),
            0xBA: partial(self.defb, 4, 1),
            0xBB: partial(self.defb, 4, 1),
            0xBC: partial(self.cp, 8, 2, 'IXh'),                         # CP IXh
            0xBD: partial(self.cp, 8, 2, 'IXl'),                         # CP IXl
            0xBE: partial(self.cp, 19, 3, 'Xd'),                         # CP (IX+d)
            0xBF: partial(self.defb, 4, 1),
            0xC0: partial(self.defb, 4, 1),
            0xC1: partial(self.defb, 4, 1),
            0xC2: partial(self.defb, 4, 1),
            0xC3: partial(self.defb, 4, 1),
            0xC4: partial(self.defb, 4, 1),
            0xC5: partial(self.defb, 4, 1),
            0xC6: partial(self.defb, 4, 1),
            0xC7: partial(self.defb, 4, 1),
            0xC8: partial(self.defb, 4, 1),
            0xC9: partial(self.defb, 4, 1),
            0xCA: partial(self.defb, 4, 1),
            0xCB: None,                                                  # DDCB prefix
            0xCC: partial(self.defb, 4, 1),
            0xCD: partial(self.defb, 4, 1),
            0xCE: partial(self.defb, 4, 1),
            0xCF: partial(self.defb, 4, 1),
            0xD0: partial(self.defb, 4, 1),
            0xD1: partial(self.defb, 4, 1),
            0xD2: partial(self.defb, 4, 1),
            0xD3: partial(self.defb, 4, 1),
            0xD4: partial(self.defb, 4, 1),
            0xD5: partial(self.defb, 4, 1),
            0xD6: partial(self.defb, 4, 1),
            0xD7: partial(self.defb, 4, 1),
            0xD8: partial(self.defb, 4, 1),
            0xD9: partial(self.defb, 4, 1),
            0xDA: partial(self.defb, 4, 1),
            0xDB: partial(self.defb, 4, 1),
            0xDC: partial(self.defb, 4, 1),
            0xDD: partial(self.defb, 4, 1),
            0xDE: partial(self.defb, 4, 1),
            0xDF: partial(self.defb, 4, 1),
            0xE0: partial(self.defb, 4, 1),
            0xE1: partial(self.pop, 'IX'),                               # POP IX
            0xE2: partial(self.defb, 4, 1),
            0xE3: partial(self.ex_sp, 'IX'),                             # EX (SP),IX
            0xE4: partial(self.defb, 4, 1),
            0xE5: partial(self.push, 'IX'),                              # PUSH IX
            0xE6: partial(self.defb, 4, 1),
            0xE7: partial(self.defb, 4, 1),
            0xE8: partial(self.defb, 4, 1),
            0xE9: partial(self.jp, '', 0, 0),                            # JP (IX)
            0xEA: partial(self.defb, 4, 1),
            0xEB: partial(self.defb, 4, 1),
            0xEC: partial(self.defb, 4, 1),
            0xED: partial(self.defb, 4, 1),
            0xEE: partial(self.defb, 4, 1),
            0xEF: partial(self.defb, 4, 1),
            0xF0: partial(self.defb, 4, 1),
            0xF1: partial(self.defb, 4, 1),
            0xF2: partial(self.defb, 4, 1),
            0xF3: partial(self.defb, 4, 1),
            0xF4: partial(self.defb, 4, 1),
            0xF5: partial(self.defb, 4, 1),
            0xF6: partial(self.defb, 4, 1),
            0xF7: partial(self.defb, 4, 1),
            0xF8: partial(self.defb, 4, 1),
            0xF9: partial(self.ldsprr, 'IX'),                            # LD SP,IX
            0xFA: partial(self.defb, 4, 1),
            0xFB: partial(self.defb, 4, 1),
            0xFC: partial(self.defb, 4, 1),
            0xFD: partial(self.defb, 4, 1),
            0xFE: partial(self.defb, 4, 1),
            0xFF: partial(self.defb, 4, 1),
        }

        self.after_DDCB = {
            0x00: partial(self.rotate, 23, 4, 'RLC', 128, 'Xd', 1, 'B'), # RLC (IX+d),B
            0x01: partial(self.rotate, 23, 4, 'RLC', 128, 'Xd', 1, 'C'), # RLC (IX+d),C
            0x02: partial(self.rotate, 23, 4, 'RLC', 128, 'Xd', 1, 'D'), # RLC (IX+d),D
            0x03: partial(self.rotate, 23, 4, 'RLC', 128, 'Xd', 1, 'E'), # RLC (IX+d),E
            0x04: partial(self.rotate, 23, 4, 'RLC', 128, 'Xd', 1, 'H'), # RLC (IX+d),H
            0x05: partial(self.rotate, 23, 4, 'RLC', 128, 'Xd', 1, 'L'), # RLC (IX+d),L
            0x06: partial(self.rotate, 23, 4, 'RLC', 128, 'Xd', 1),      # RLC (IX+d)
            0x07: partial(self.rotate, 23, 4, 'RLC', 128, 'Xd', 1, 'A'), # RLC (IX+d),A
            0x08: partial(self.rotate, 23, 4, 'RRC', 1, 'Xd', 1, 'B'),   # RRC (IX+d),B
            0x09: partial(self.rotate, 23, 4, 'RRC', 1, 'Xd', 1, 'C'),   # RRC (IX+d),C
            0x0A: partial(self.rotate, 23, 4, 'RRC', 1, 'Xd', 1, 'D'),   # RRC (IX+d),D
            0x0B: partial(self.rotate, 23, 4, 'RRC', 1, 'Xd', 1, 'E'),   # RRC (IX+d),E
            0x0C: partial(self.rotate, 23, 4, 'RRC', 1, 'Xd', 1, 'H'),   # RRC (IX+d),H
            0x0D: partial(self.rotate, 23, 4, 'RRC', 1, 'Xd', 1, 'L'),   # RRC (IX+d),L
            0x0E: partial(self.rotate, 23, 4, 'RRC', 1, 'Xd', 1),        # RRC (IX+d)
            0x0F: partial(self.rotate, 23, 4, 'RRC', 1, 'Xd', 1, 'A'),   # RRC (IX+d),A
            0x10: partial(self.rotate, 23, 4, 'RL', 128, 'Xd', 0, 'B'),  # RL (IX+d),B
            0x11: partial(self.rotate, 23, 4, 'RL', 128, 'Xd', 0, 'C'),  # RL (IX+d),C
            0x12: partial(self.rotate, 23, 4, 'RL', 128, 'Xd', 0, 'D'),  # RL (IX+d),D
            0x13: partial(self.rotate, 23, 4, 'RL', 128, 'Xd', 0, 'E'),  # RL (IX+d),E
            0x14: partial(self.rotate, 23, 4, 'RL', 128, 'Xd', 0, 'H'),  # RL (IX+d),H
            0x15: partial(self.rotate, 23, 4, 'RL', 128, 'Xd', 0, 'L'),  # RL (IX+d),L
            0x16: partial(self.rotate, 23, 4, 'RL', 128, 'Xd'),          # RL (IX+d)
            0x17: partial(self.rotate, 23, 4, 'RL', 128, 'Xd', 0, 'A'),  # RL (IX+d),A
            0x18: partial(self.rotate, 23, 4, 'RR', 1, 'Xd', 0, 'B'),    # RR (IX+d),B
            0x19: partial(self.rotate, 23, 4, 'RR', 1, 'Xd', 0, 'C'),    # RR (IX+d),C
            0x1A: partial(self.rotate, 23, 4, 'RR', 1, 'Xd', 0, 'D'),    # RR (IX+d),D
            0x1B: partial(self.rotate, 23, 4, 'RR', 1, 'Xd', 0, 'E'),    # RR (IX+d),E
            0x1C: partial(self.rotate, 23, 4, 'RR', 1, 'Xd', 0, 'H'),    # RR (IX+d),H
            0x1D: partial(self.rotate, 23, 4, 'RR', 1, 'Xd', 0, 'L'),    # RR (IX+d),L
            0x1E: partial(self.rotate, 23, 4, 'RR', 1, 'Xd'),            # RR (IX+d)
            0x1F: partial(self.rotate, 23, 4, 'RR', 1, 'Xd', 0, 'A'),    # RR (IX+d),A
            0x20: partial(self.shift, 23, 4, 'SLA', 128, 'Xd', 'B'),     # SLA (IX+d),B
            0x21: partial(self.shift, 23, 4, 'SLA', 128, 'Xd', 'C'),     # SLA (IX+d),C
            0x22: partial(self.shift, 23, 4, 'SLA', 128, 'Xd', 'D'),     # SLA (IX+d),D
            0x23: partial(self.shift, 23, 4, 'SLA', 128, 'Xd', 'E'),     # SLA (IX+d),E
            0x24: partial(self.shift, 23, 4, 'SLA', 128, 'Xd', 'H'),     # SLA (IX+d),H
            0x25: partial(self.shift, 23, 4, 'SLA', 128, 'Xd', 'L'),     # SLA (IX+d),L
            0x26: partial(self.shift, 23, 4, 'SLA', 128, 'Xd'),          # SLA (IX+d)
            0x27: partial(self.shift, 23, 4, 'SLA', 128, 'Xd', 'A'),     # SLA (IX+d),A
            0x28: partial(self.shift, 23, 4, 'SRA', 1, 'Xd', 'B'),       # SRA (IX+d),B
            0x29: partial(self.shift, 23, 4, 'SRA', 1, 'Xd', 'C'),       # SRA (IX+d),C
            0x2A: partial(self.shift, 23, 4, 'SRA', 1, 'Xd', 'D'),       # SRA (IX+d),D
            0x2B: partial(self.shift, 23, 4, 'SRA', 1, 'Xd', 'E'),       # SRA (IX+d),E
            0x2C: partial(self.shift, 23, 4, 'SRA', 1, 'Xd', 'H'),       # SRA (IX+d),H
            0x2D: partial(self.shift, 23, 4, 'SRA', 1, 'Xd', 'L'),       # SRA (IX+d),L
            0x2E: partial(self.shift, 23, 4, 'SRA', 1, 'Xd'),            # SRA (IX+d)
            0x2F: partial(self.shift, 23, 4, 'SRA', 1, 'Xd', 'A'),       # SRA (IX+d),A
            0x30: partial(self.shift, 23, 4, 'SLL', 128, 'Xd', 'B'),     # SLL (IX+d),B
            0x31: partial(self.shift, 23, 4, 'SLL', 128, 'Xd', 'C'),     # SLL (IX+d),C
            0x32: partial(self.shift, 23, 4, 'SLL', 128, 'Xd', 'D'),     # SLL (IX+d),D
            0x33: partial(self.shift, 23, 4, 'SLL', 128, 'Xd', 'E'),     # SLL (IX+d),E
            0x34: partial(self.shift, 23, 4, 'SLL', 128, 'Xd', 'H'),     # SLL (IX+d),H
            0x35: partial(self.shift, 23, 4, 'SLL', 128, 'Xd', 'L'),     # SLL (IX+d),L
            0x36: partial(self.shift, 23, 4, 'SLL', 128, 'Xd'),          # SLL (IX+d)
            0x37: partial(self.shift, 23, 4, 'SLL', 128, 'Xd', 'A'),     # SLL (IX+d),A
            0x38: partial(self.shift, 23, 4, 'SRL', 1, 'Xd', 'B'),       # SRL (IX+d),B
            0x39: partial(self.shift, 23, 4, 'SRL', 1, 'Xd', 'C'),       # SRL (IX+d),C
            0x3A: partial(self.shift, 23, 4, 'SRL', 1, 'Xd', 'D'),       # SRL (IX+d),D
            0x3B: partial(self.shift, 23, 4, 'SRL', 1, 'Xd', 'E'),       # SRL (IX+d),E
            0x3C: partial(self.shift, 23, 4, 'SRL', 1, 'Xd', 'H'),       # SRL (IX+d),H
            0x3D: partial(self.shift, 23, 4, 'SRL', 1, 'Xd', 'L'),       # SRL (IX+d),L
            0x3E: partial(self.shift, 23, 4, 'SRL', 1, 'Xd'),            # SRL (IX+d)
            0x3F: partial(self.shift, 23, 4, 'SRL', 1, 'Xd', 'A'),       # SRL (IX+d),A
            0x40: partial(self.bit, 20, 4, 0, 'Xd'),                     # BIT 0,(IX+d)
            0x41: partial(self.bit, 20, 4, 0, 'Xd'),                     # BIT 0,(IX+d)
            0x42: partial(self.bit, 20, 4, 0, 'Xd'),                     # BIT 0,(IX+d)
            0x43: partial(self.bit, 20, 4, 0, 'Xd'),                     # BIT 0,(IX+d)
            0x44: partial(self.bit, 20, 4, 0, 'Xd'),                     # BIT 0,(IX+d)
            0x45: partial(self.bit, 20, 4, 0, 'Xd'),                     # BIT 0,(IX+d)
            0x46: partial(self.bit, 20, 4, 0, 'Xd'),                     # BIT 0,(IX+d)
            0x47: partial(self.bit, 20, 4, 0, 'Xd'),                     # BIT 0,(IX+d)
            0x48: partial(self.bit, 20, 4, 1, 'Xd'),                     # BIT 1,(IX+d)
            0x49: partial(self.bit, 20, 4, 1, 'Xd'),                     # BIT 1,(IX+d)
            0x4A: partial(self.bit, 20, 4, 1, 'Xd'),                     # BIT 1,(IX+d)
            0x4B: partial(self.bit, 20, 4, 1, 'Xd'),                     # BIT 1,(IX+d)
            0x4C: partial(self.bit, 20, 4, 1, 'Xd'),                     # BIT 1,(IX+d)
            0x4D: partial(self.bit, 20, 4, 1, 'Xd'),                     # BIT 1,(IX+d)
            0x4E: partial(self.bit, 20, 4, 1, 'Xd'),                     # BIT 1,(IX+d)
            0x4F: partial(self.bit, 20, 4, 1, 'Xd'),                     # BIT 1,(IX+d)
            0x50: partial(self.bit, 20, 4, 2, 'Xd'),                     # BIT 2,(IX+d)
            0x51: partial(self.bit, 20, 4, 2, 'Xd'),                     # BIT 2,(IX+d)
            0x52: partial(self.bit, 20, 4, 2, 'Xd'),                     # BIT 2,(IX+d)
            0x53: partial(self.bit, 20, 4, 2, 'Xd'),                     # BIT 2,(IX+d)
            0x54: partial(self.bit, 20, 4, 2, 'Xd'),                     # BIT 2,(IX+d)
            0x55: partial(self.bit, 20, 4, 2, 'Xd'),                     # BIT 2,(IX+d)
            0x56: partial(self.bit, 20, 4, 2, 'Xd'),                     # BIT 2,(IX+d)
            0x57: partial(self.bit, 20, 4, 2, 'Xd'),                     # BIT 2,(IX+d)
            0x58: partial(self.bit, 20, 4, 3, 'Xd'),                     # BIT 3,(IX+d)
            0x59: partial(self.bit, 20, 4, 3, 'Xd'),                     # BIT 3,(IX+d)
            0x5A: partial(self.bit, 20, 4, 3, 'Xd'),                     # BIT 3,(IX+d)
            0x5B: partial(self.bit, 20, 4, 3, 'Xd'),                     # BIT 3,(IX+d)
            0x5C: partial(self.bit, 20, 4, 3, 'Xd'),                     # BIT 3,(IX+d)
            0x5D: partial(self.bit, 20, 4, 3, 'Xd'),                     # BIT 3,(IX+d)
            0x5E: partial(self.bit, 20, 4, 3, 'Xd'),                     # BIT 3,(IX+d)
            0x5F: partial(self.bit, 20, 4, 3, 'Xd'),                     # BIT 3,(IX+d)
            0x60: partial(self.bit, 20, 4, 4, 'Xd'),                     # BIT 4,(IX+d)
            0x61: partial(self.bit, 20, 4, 4, 'Xd'),                     # BIT 4,(IX+d)
            0x62: partial(self.bit, 20, 4, 4, 'Xd'),                     # BIT 4,(IX+d)
            0x63: partial(self.bit, 20, 4, 4, 'Xd'),                     # BIT 4,(IX+d)
            0x64: partial(self.bit, 20, 4, 4, 'Xd'),                     # BIT 4,(IX+d)
            0x65: partial(self.bit, 20, 4, 4, 'Xd'),                     # BIT 4,(IX+d)
            0x66: partial(self.bit, 20, 4, 4, 'Xd'),                     # BIT 4,(IX+d)
            0x67: partial(self.bit, 20, 4, 4, 'Xd'),                     # BIT 4,(IX+d)
            0x68: partial(self.bit, 20, 4, 5, 'Xd'),                     # BIT 5,(IX+d)
            0x69: partial(self.bit, 20, 4, 5, 'Xd'),                     # BIT 5,(IX+d)
            0x6A: partial(self.bit, 20, 4, 5, 'Xd'),                     # BIT 5,(IX+d)
            0x6B: partial(self.bit, 20, 4, 5, 'Xd'),                     # BIT 5,(IX+d)
            0x6C: partial(self.bit, 20, 4, 5, 'Xd'),                     # BIT 5,(IX+d)
            0x6D: partial(self.bit, 20, 4, 5, 'Xd'),                     # BIT 5,(IX+d)
            0x6E: partial(self.bit, 20, 4, 5, 'Xd'),                     # BIT 5,(IX+d)
            0x6F: partial(self.bit, 20, 4, 5, 'Xd'),                     # BIT 5,(IX+d)
            0x70: partial(self.bit, 20, 4, 6, 'Xd'),                     # BIT 6,(IX+d)
            0x71: partial(self.bit, 20, 4, 6, 'Xd'),                     # BIT 6,(IX+d)
            0x72: partial(self.bit, 20, 4, 6, 'Xd'),                     # BIT 6,(IX+d)
            0x73: partial(self.bit, 20, 4, 6, 'Xd'),                     # BIT 6,(IX+d)
            0x74: partial(self.bit, 20, 4, 6, 'Xd'),                     # BIT 6,(IX+d)
            0x75: partial(self.bit, 20, 4, 6, 'Xd'),                     # BIT 6,(IX+d)
            0x76: partial(self.bit, 20, 4, 6, 'Xd'),                     # BIT 6,(IX+d)
            0x77: partial(self.bit, 20, 4, 6, 'Xd'),                     # BIT 6,(IX+d)
            0x78: partial(self.bit, 20, 4, 7, 'Xd'),                     # BIT 7,(IX+d)
            0x79: partial(self.bit, 20, 4, 7, 'Xd'),                     # BIT 7,(IX+d)
            0x7A: partial(self.bit, 20, 4, 7, 'Xd'),                     # BIT 7,(IX+d)
            0x7B: partial(self.bit, 20, 4, 7, 'Xd'),                     # BIT 7,(IX+d)
            0x7C: partial(self.bit, 20, 4, 7, 'Xd'),                     # BIT 7,(IX+d)
            0x7D: partial(self.bit, 20, 4, 7, 'Xd'),                     # BIT 7,(IX+d)
            0x7E: partial(self.bit, 20, 4, 7, 'Xd'),                     # BIT 7,(IX+d)
            0x7F: partial(self.bit, 20, 4, 7, 'Xd'),                     # BIT 7,(IX+d)
            0x80: partial(self.res_set, 23, 4, 0, 'Xd', 0, 'B'),         # RES 0,(IX+d),B
            0x81: partial(self.res_set, 23, 4, 0, 'Xd', 0, 'C'),         # RES 0,(IX+d),C
            0x82: partial(self.res_set, 23, 4, 0, 'Xd', 0, 'D'),         # RES 0,(IX+d),D
            0x83: partial(self.res_set, 23, 4, 0, 'Xd', 0, 'E'),         # RES 0,(IX+d),E
            0x84: partial(self.res_set, 23, 4, 0, 'Xd', 0, 'H'),         # RES 0,(IX+d),H
            0x85: partial(self.res_set, 23, 4, 0, 'Xd', 0, 'L'),         # RES 0,(IX+d),L
            0x86: partial(self.res_set, 23, 4, 0, 'Xd', 0),              # RES 0,(IX+d)
            0x87: partial(self.res_set, 23, 4, 0, 'Xd', 0, 'A'),         # RES 0,(IX+d),A
            0x88: partial(self.res_set, 23, 4, 1, 'Xd', 0, 'B'),         # RES 1,(IX+d),B
            0x89: partial(self.res_set, 23, 4, 1, 'Xd', 0, 'C'),         # RES 1,(IX+d),C
            0x8A: partial(self.res_set, 23, 4, 1, 'Xd', 0, 'D'),         # RES 1,(IX+d),D
            0x8B: partial(self.res_set, 23, 4, 1, 'Xd', 0, 'E'),         # RES 1,(IX+d),E
            0x8C: partial(self.res_set, 23, 4, 1, 'Xd', 0, 'H'),         # RES 1,(IX+d),H
            0x8D: partial(self.res_set, 23, 4, 1, 'Xd', 0, 'L'),         # RES 1,(IX+d),L
            0x8E: partial(self.res_set, 23, 4, 1, 'Xd', 0),              # RES 1,(IX+d)
            0x8F: partial(self.res_set, 23, 4, 1, 'Xd', 0, 'A'),         # RES 1,(IX+d),A
            0x90: partial(self.res_set, 23, 4, 2, 'Xd', 0, 'B'),         # RES 2,(IX+d),B
            0x91: partial(self.res_set, 23, 4, 2, 'Xd', 0, 'C'),         # RES 2,(IX+d),C
            0x92: partial(self.res_set, 23, 4, 2, 'Xd', 0, 'D'),         # RES 2,(IX+d),D
            0x93: partial(self.res_set, 23, 4, 2, 'Xd', 0, 'E'),         # RES 2,(IX+d),E
            0x94: partial(self.res_set, 23, 4, 2, 'Xd', 0, 'H'),         # RES 2,(IX+d),H
            0x95: partial(self.res_set, 23, 4, 2, 'Xd', 0, 'L'),         # RES 2,(IX+d),L
            0x96: partial(self.res_set, 23, 4, 2, 'Xd', 0),              # RES 2,(IX+d)
            0x97: partial(self.res_set, 23, 4, 2, 'Xd', 0, 'A'),         # RES 2,(IX+d),A
            0x98: partial(self.res_set, 23, 4, 3, 'Xd', 0, 'B'),         # RES 3,(IX+d),B
            0x99: partial(self.res_set, 23, 4, 3, 'Xd', 0, 'C'),         # RES 3,(IX+d),C
            0x9A: partial(self.res_set, 23, 4, 3, 'Xd', 0, 'D'),         # RES 3,(IX+d),D
            0x9B: partial(self.res_set, 23, 4, 3, 'Xd', 0, 'E'),         # RES 3,(IX+d),E
            0x9C: partial(self.res_set, 23, 4, 3, 'Xd', 0, 'H'),         # RES 3,(IX+d),H
            0x9D: partial(self.res_set, 23, 4, 3, 'Xd', 0, 'L'),         # RES 3,(IX+d),L
            0x9E: partial(self.res_set, 23, 4, 3, 'Xd', 0),              # RES 3,(IX+d)
            0x9F: partial(self.res_set, 23, 4, 3, 'Xd', 0, 'A'),         # RES 3,(IX+d),A
            0xA0: partial(self.res_set, 23, 4, 4, 'Xd', 0, 'B'),         # RES 4,(IX+d),B
            0xA1: partial(self.res_set, 23, 4, 4, 'Xd', 0, 'C'),         # RES 4,(IX+d),C
            0xA2: partial(self.res_set, 23, 4, 4, 'Xd', 0, 'D'),         # RES 4,(IX+d),D
            0xA3: partial(self.res_set, 23, 4, 4, 'Xd', 0, 'E'),         # RES 4,(IX+d),E
            0xA4: partial(self.res_set, 23, 4, 4, 'Xd', 0, 'H'),         # RES 4,(IX+d),H
            0xA5: partial(self.res_set, 23, 4, 4, 'Xd', 0, 'L'),         # RES 4,(IX+d),L
            0xA6: partial(self.res_set, 23, 4, 4, 'Xd', 0),              # RES 4,(IX+d)
            0xA7: partial(self.res_set, 23, 4, 4, 'Xd', 0, 'A'),         # RES 4,(IX+d),A
            0xA8: partial(self.res_set, 23, 4, 5, 'Xd', 0, 'B'),         # RES 5,(IX+d),B
            0xA9: partial(self.res_set, 23, 4, 5, 'Xd', 0, 'C'),         # RES 5,(IX+d),C
            0xAA: partial(self.res_set, 23, 4, 5, 'Xd', 0, 'D'),         # RES 5,(IX+d),D
            0xAB: partial(self.res_set, 23, 4, 5, 'Xd', 0, 'E'),         # RES 5,(IX+d),E
            0xAC: partial(self.res_set, 23, 4, 5, 'Xd', 0, 'H'),         # RES 5,(IX+d),H
            0xAD: partial(self.res_set, 23, 4, 5, 'Xd', 0, 'L'),         # RES 5,(IX+d),L
            0xAE: partial(self.res_set, 23, 4, 5, 'Xd', 0),              # RES 5,(IX+d)
            0xAF: partial(self.res_set, 23, 4, 5, 'Xd', 0, 'A'),         # RES 5,(IX+d),A
            0xB0: partial(self.res_set, 23, 4, 6, 'Xd', 0, 'B'),         # RES 6,(IX+d),B
            0xB1: partial(self.res_set, 23, 4, 6, 'Xd', 0, 'C'),         # RES 6,(IX+d),C
            0xB2: partial(self.res_set, 23, 4, 6, 'Xd', 0, 'D'),         # RES 6,(IX+d),D
            0xB3: partial(self.res_set, 23, 4, 6, 'Xd', 0, 'E'),         # RES 6,(IX+d),E
            0xB4: partial(self.res_set, 23, 4, 6, 'Xd', 0, 'H'),         # RES 6,(IX+d),H
            0xB5: partial(self.res_set, 23, 4, 6, 'Xd', 0, 'L'),         # RES 6,(IX+d),L
            0xB6: partial(self.res_set, 23, 4, 6, 'Xd', 0),              # RES 6,(IX+d)
            0xB7: partial(self.res_set, 23, 4, 6, 'Xd', 0, 'A'),         # RES 6,(IX+d),A
            0xB8: partial(self.res_set, 23, 4, 7, 'Xd', 0, 'B'),         # RES 7,(IX+d),B
            0xB9: partial(self.res_set, 23, 4, 7, 'Xd', 0, 'C'),         # RES 7,(IX+d),C
            0xBA: partial(self.res_set, 23, 4, 7, 'Xd', 0, 'D'),         # RES 7,(IX+d),D
            0xBB: partial(self.res_set, 23, 4, 7, 'Xd', 0, 'E'),         # RES 7,(IX+d),E
            0xBC: partial(self.res_set, 23, 4, 7, 'Xd', 0, 'H'),         # RES 7,(IX+d),H
            0xBD: partial(self.res_set, 23, 4, 7, 'Xd', 0, 'L'),         # RES 7,(IX+d),L
            0xBE: partial(self.res_set, 23, 4, 7, 'Xd', 0),              # RES 7,(IX+d)
            0xBF: partial(self.res_set, 23, 4, 7, 'Xd', 0, 'A'),         # RES 7,(IX+d),A
            0xC0: partial(self.res_set, 23, 4, 0, 'Xd', 1, 'B'),         # SET 0,(IX+d),B
            0xC1: partial(self.res_set, 23, 4, 0, 'Xd', 1, 'C'),         # SET 0,(IX+d),C
            0xC2: partial(self.res_set, 23, 4, 0, 'Xd', 1, 'D'),         # SET 0,(IX+d),D
            0xC3: partial(self.res_set, 23, 4, 0, 'Xd', 1, 'E'),         # SET 0,(IX+d),E
            0xC4: partial(self.res_set, 23, 4, 0, 'Xd', 1, 'H'),         # SET 0,(IX+d),H
            0xC5: partial(self.res_set, 23, 4, 0, 'Xd', 1, 'L'),         # SET 0,(IX+d),L
            0xC6: partial(self.res_set, 23, 4, 0, 'Xd', 1),              # SET 0,(IX+d)
            0xC7: partial(self.res_set, 23, 4, 0, 'Xd', 1, 'A'),         # SET 0,(IX+d),A
            0xC8: partial(self.res_set, 23, 4, 1, 'Xd', 1, 'B'),         # SET 1,(IX+d),B
            0xC9: partial(self.res_set, 23, 4, 1, 'Xd', 1, 'C'),         # SET 1,(IX+d),C
            0xCA: partial(self.res_set, 23, 4, 1, 'Xd', 1, 'D'),         # SET 1,(IX+d),D
            0xCB: partial(self.res_set, 23, 4, 1, 'Xd', 1, 'E'),         # SET 1,(IX+d),E
            0xCC: partial(self.res_set, 23, 4, 1, 'Xd', 1, 'H'),         # SET 1,(IX+d),H
            0xCD: partial(self.res_set, 23, 4, 1, 'Xd', 1, 'L'),         # SET 1,(IX+d),L
            0xCE: partial(self.res_set, 23, 4, 1, 'Xd', 1),              # SET 1,(IX+d)
            0xCF: partial(self.res_set, 23, 4, 1, 'Xd', 1, 'A'),         # SET 1,(IX+d),A
            0xD0: partial(self.res_set, 23, 4, 2, 'Xd', 1, 'B'),         # SET 2,(IX+d),B
            0xD1: partial(self.res_set, 23, 4, 2, 'Xd', 1, 'C'),         # SET 2,(IX+d),C
            0xD2: partial(self.res_set, 23, 4, 2, 'Xd', 1, 'D'),         # SET 2,(IX+d),D
            0xD3: partial(self.res_set, 23, 4, 2, 'Xd', 1, 'E'),         # SET 2,(IX+d),E
            0xD4: partial(self.res_set, 23, 4, 2, 'Xd', 1, 'H'),         # SET 2,(IX+d),H
            0xD5: partial(self.res_set, 23, 4, 2, 'Xd', 1, 'L'),         # SET 2,(IX+d),L
            0xD6: partial(self.res_set, 23, 4, 2, 'Xd', 1),              # SET 2,(IX+d)
            0xD7: partial(self.res_set, 23, 4, 2, 'Xd', 1, 'A'),         # SET 2,(IX+d),A
            0xD8: partial(self.res_set, 23, 4, 3, 'Xd', 1, 'B'),         # SET 3,(IX+d),B
            0xD9: partial(self.res_set, 23, 4, 3, 'Xd', 1, 'C'),         # SET 3,(IX+d),C
            0xDA: partial(self.res_set, 23, 4, 3, 'Xd', 1, 'D'),         # SET 3,(IX+d),D
            0xDB: partial(self.res_set, 23, 4, 3, 'Xd', 1, 'E'),         # SET 3,(IX+d),E
            0xDC: partial(self.res_set, 23, 4, 3, 'Xd', 1, 'H'),         # SET 3,(IX+d),H
            0xDD: partial(self.res_set, 23, 4, 3, 'Xd', 1, 'L'),         # SET 3,(IX+d),L
            0xDE: partial(self.res_set, 23, 4, 3, 'Xd', 1),              # SET 3,(IX+d)
            0xDF: partial(self.res_set, 23, 4, 3, 'Xd', 1, 'A'),         # SET 3,(IX+d),A
            0xE0: partial(self.res_set, 23, 4, 4, 'Xd', 1, 'B'),         # SET 4,(IX+d),B
            0xE1: partial(self.res_set, 23, 4, 4, 'Xd', 1, 'C'),         # SET 4,(IX+d),C
            0xE2: partial(self.res_set, 23, 4, 4, 'Xd', 1, 'D'),         # SET 4,(IX+d),D
            0xE3: partial(self.res_set, 23, 4, 4, 'Xd', 1, 'E'),         # SET 4,(IX+d),E
            0xE4: partial(self.res_set, 23, 4, 4, 'Xd', 1, 'H'),         # SET 4,(IX+d),H
            0xE5: partial(self.res_set, 23, 4, 4, 'Xd', 1, 'L'),         # SET 4,(IX+d),L
            0xE6: partial(self.res_set, 23, 4, 4, 'Xd', 1),              # SET 4,(IX+d)
            0xE7: partial(self.res_set, 23, 4, 4, 'Xd', 1, 'A'),         # SET 4,(IX+d),A
            0xE8: partial(self.res_set, 23, 4, 5, 'Xd', 1, 'B'),         # SET 5,(IX+d),B
            0xE9: partial(self.res_set, 23, 4, 5, 'Xd', 1, 'C'),         # SET 5,(IX+d),C
            0xEA: partial(self.res_set, 23, 4, 5, 'Xd', 1, 'D'),         # SET 5,(IX+d),D
            0xEB: partial(self.res_set, 23, 4, 5, 'Xd', 1, 'E'),         # SET 5,(IX+d),E
            0xEC: partial(self.res_set, 23, 4, 5, 'Xd', 1, 'H'),         # SET 5,(IX+d),H
            0xED: partial(self.res_set, 23, 4, 5, 'Xd', 1, 'L'),         # SET 5,(IX+d),L
            0xEE: partial(self.res_set, 23, 4, 5, 'Xd', 1),              # SET 5,(IX+d)
            0xEF: partial(self.res_set, 23, 4, 5, 'Xd', 1, 'A'),         # SET 5,(IX+d),A
            0xF0: partial(self.res_set, 23, 4, 6, 'Xd', 1, 'B'),         # SET 6,(IX+d),B
            0xF1: partial(self.res_set, 23, 4, 6, 'Xd', 1, 'C'),         # SET 6,(IX+d),C
            0xF2: partial(self.res_set, 23, 4, 6, 'Xd', 1, 'D'),         # SET 6,(IX+d),D
            0xF3: partial(self.res_set, 23, 4, 6, 'Xd', 1, 'E'),         # SET 6,(IX+d),E
            0xF4: partial(self.res_set, 23, 4, 6, 'Xd', 1, 'H'),         # SET 6,(IX+d),H
            0xF5: partial(self.res_set, 23, 4, 6, 'Xd', 1, 'L'),         # SET 6,(IX+d),L
            0xF6: partial(self.res_set, 23, 4, 6, 'Xd', 1),              # SET 6,(IX+d)
            0xF7: partial(self.res_set, 23, 4, 6, 'Xd', 1, 'A'),         # SET 6,(IX+d),A
            0xF8: partial(self.res_set, 23, 4, 7, 'Xd', 1, 'B'),         # SET 7,(IX+d),B
            0xF9: partial(self.res_set, 23, 4, 7, 'Xd', 1, 'C'),         # SET 7,(IX+d),C
            0xFA: partial(self.res_set, 23, 4, 7, 'Xd', 1, 'D'),         # SET 7,(IX+d),D
            0xFB: partial(self.res_set, 23, 4, 7, 'Xd', 1, 'E'),         # SET 7,(IX+d),E
            0xFC: partial(self.res_set, 23, 4, 7, 'Xd', 1, 'H'),         # SET 7,(IX+d),H
            0xFD: partial(self.res_set, 23, 4, 7, 'Xd', 1, 'L'),         # SET 7,(IX+d),L
            0xFE: partial(self.res_set, 23, 4, 7, 'Xd', 1),              # SET 7,(IX+d)
            0xFF: partial(self.res_set, 23, 4, 7, 'Xd', 1, 'A'),         # SET 7,(IX+d),A
        }

        self.after_FD = {
            0x00: partial(self.defb, 4, 1),
            0x01: partial(self.defb, 4, 1),
            0x02: partial(self.defb, 4, 1),
            0x03: partial(self.defb, 4, 1),
            0x04: partial(self.defb, 4, 1),
            0x05: partial(self.defb, 4, 1),
            0x06: partial(self.defb, 4, 1),
            0x07: partial(self.defb, 4, 1),
            0x08: partial(self.defb, 4, 1),
            0x09: partial(self.add16, 15, 2, 'IY', 'BC'),                # ADD IY,BC
            0x0A: partial(self.defb, 4, 1),
            0x0B: partial(self.defb, 4, 1),
            0x0C: partial(self.defb, 4, 1),
            0x0D: partial(self.defb, 4, 1),
            0x0E: partial(self.defb, 4, 1),
            0x0F: partial(self.defb, 4, 1),
            0x10: partial(self.defb, 4, 1),
            0x11: partial(self.defb, 4, 1),
            0x12: partial(self.defb, 4, 1),
            0x13: partial(self.defb, 4, 1),
            0x14: partial(self.defb, 4, 1),
            0x15: partial(self.defb, 4, 1),
            0x16: partial(self.defb, 4, 1),
            0x17: partial(self.defb, 4, 1),
            0x18: partial(self.defb, 4, 1),
            0x19: partial(self.add16, 15, 2, 'IY', 'DE'),                # ADD IY,DE
            0x1A: partial(self.defb, 4, 1),
            0x1B: partial(self.defb, 4, 1),
            0x1C: partial(self.defb, 4, 1),
            0x1D: partial(self.defb, 4, 1),
            0x1E: partial(self.defb, 4, 1),
            0x1F: partial(self.defb, 4, 1),
            0x20: partial(self.defb, 4, 1),
            0x21: partial(self.ld16, 'IY'),                              # LD IY,nn
            0x22: partial(self.ld16addr, 20, 4, 'IY', 1),                # LD (nn),IY
            0x23: partial(self.inc_dec16, 'INC', 'IY'),                  # INC IY
            0x24: partial(self.inc_dec8, 8, 2, 'INC', 'IYh'),            # INC IYh
            0x25: partial(self.inc_dec8, 8, 2, 'DEC', 'IYh'),            # DEC IYh
            0x26: partial(self.ld8, 11, 3, 'IYh'),                       # LD IYh,n
            0x27: partial(self.defb, 4, 1),
            0x28: partial(self.defb, 4, 1),
            0x29: partial(self.add16, 15, 2, 'IY', 'IY'),                # ADD IY,IY
            0x2A: partial(self.ld16addr, 20, 4, 'IY', 0),                # LD IY,(nn)
            0x2B: partial(self.inc_dec16, 'DEC', 'IY'),                  # DEC IY
            0x2C: partial(self.inc_dec8, 8, 2, 'INC', 'IYl'),            # INC IYl
            0x2D: partial(self.inc_dec8, 8, 2, 'DEC', 'IYl'),            # DEC IYl
            0x2E: partial(self.ld8, 11, 3, 'IYl'),                       # LD IYl,n
            0x2F: partial(self.defb, 4, 1),
            0x30: partial(self.defb, 4, 1),
            0x31: partial(self.defb, 4, 1),
            0x32: partial(self.defb, 4, 1),
            0x33: partial(self.defb, 4, 1),
            0x34: partial(self.inc_dec8, 23, 3, 'INC', 'Yd'),            # INC (IY+d)
            0x35: partial(self.inc_dec8, 23, 3, 'DEC', 'Yd'),            # DEC (IY+d)
            0x36: partial(self.ld8, 19, 4, 'Yd'),                        # LD (IY+d),n
            0x37: partial(self.defb, 4, 1),
            0x38: partial(self.defb, 4, 1),
            0x39: partial(self.add16, 15, 2, 'IY', 'SP'),                # ADD IY,SP
            0x3A: partial(self.defb, 4, 1),
            0x3B: partial(self.defb, 4, 1),
            0x3C: partial(self.defb, 4, 1),
            0x3D: partial(self.defb, 4, 1),
            0x3E: partial(self.defb, 4, 1),
            0x3F: partial(self.defb, 4, 1),
            0x40: partial(self.defb, 4, 1),
            0x41: partial(self.defb, 4, 1),
            0x42: partial(self.defb, 4, 1),
            0x43: partial(self.defb, 4, 1),
            0x44: partial(self.ld8, 8, 2, 'B', 'IYh'),                   # LD B,IYh
            0x45: partial(self.ld8, 8, 2, 'B', 'IYl'),                   # LD B,IYl
            0x46: partial(self.ld8, 19, 3, 'B', 'Yd'),                   # LD B,(IY+d)
            0x47: partial(self.defb, 4, 1),
            0x48: partial(self.defb, 4, 1),
            0x49: partial(self.defb, 4, 1),
            0x4A: partial(self.defb, 4, 1),
            0x4B: partial(self.defb, 4, 1),
            0x4C: partial(self.ld8, 8, 2, 'C', 'IYh'),                   # LD C,IYh
            0x4D: partial(self.ld8, 8, 2, 'C', 'IYl'),                   # LD C,IYl
            0x4E: partial(self.ld8, 19, 3, 'C', 'Yd'),                   # LD C,(IY+d)
            0x4F: partial(self.defb, 4, 1),
            0x50: partial(self.defb, 4, 1),
            0x51: partial(self.defb, 4, 1),
            0x52: partial(self.defb, 4, 1),
            0x53: partial(self.defb, 4, 1),
            0x54: partial(self.ld8, 8, 2, 'D', 'IYh'),                   # LD D,IYh
            0x55: partial(self.ld8, 8, 2, 'D', 'IYl'),                   # LD D,IYl
            0x56: partial(self.ld8, 19, 3, 'D', 'Yd'),                   # LD D,(IY+d)
            0x57: partial(self.defb, 4, 1),
            0x58: partial(self.defb, 4, 1),
            0x59: partial(self.defb, 4, 1),
            0x5A: partial(self.defb, 4, 1),
            0x5B: partial(self.defb, 4, 1),
            0x5C: partial(self.ld8, 8, 2, 'E', 'IYh'),                   # LD E,IYh
            0x5D: partial(self.ld8, 8, 2, 'E', 'IYl'),                   # LD E,IYl
            0x5E: partial(self.ld8, 19, 3, 'E', 'Yd'),                   # LD E,(IY+d)
            0x5F: partial(self.defb, 4, 1),
            0x60: partial(self.ld8, 8, 2, 'IYh', 'B'),                   # LD IYh,B
            0x61: partial(self.ld8, 8, 2, 'IYh', 'C'),                   # LD IYh,C
            0x62: partial(self.ld8, 8, 2, 'IYh', 'D'),                   # LD IYh,D
            0x63: partial(self.ld8, 8, 2, 'IYh', 'E'),                   # LD IYh,E
            0x64: partial(self.ld8, 8, 2, 'IYh', 'IYh'),                 # LD IYh,IYh
            0x65: partial(self.ld8, 8, 2, 'IYh', 'IYl'),                 # LD IYh,IYl
            0x66: partial(self.ld8, 19, 3, 'H', 'Yd'),                   # LD H,(IY+d)
            0x67: partial(self.ld8, 8, 2, 'IYh', 'A'),                   # LD IYh,A
            0x68: partial(self.ld8, 8, 2, 'IYl', 'B'),                   # LD IYl,B
            0x69: partial(self.ld8, 8, 2, 'IYl', 'C'),                   # LD IYl,C
            0x6A: partial(self.ld8, 8, 2, 'IYl', 'D'),                   # LD IYl,D
            0x6B: partial(self.ld8, 8, 2, 'IYl', 'E'),                   # LD IYl,E
            0x6C: partial(self.ld8, 8, 2, 'IYl', 'IYh'),                 # LD IYl,IYh
            0x6D: partial(self.ld8, 8, 2, 'IYl', 'IYl'),                 # LD IYl,IYl
            0x6E: partial(self.ld8, 19, 3, 'L', 'Yd'),                   # LD L,(IY+d)
            0x6F: partial(self.ld8, 8, 2, 'IYl', 'A'),                   # LD IYl,A
            0x70: partial(self.ld8, 19, 3, 'Yd', 'B'),                   # LD (IY+d),B
            0x71: partial(self.ld8, 19, 3, 'Yd', 'C'),                   # LD (IY+d),C
            0x72: partial(self.ld8, 19, 3, 'Yd', 'D'),                   # LD (IY+d),D
            0x73: partial(self.ld8, 19, 3, 'Yd', 'E'),                   # LD (IY+d),E
            0x74: partial(self.ld8, 19, 3, 'Yd', 'H'),                   # LD (IY+d),H
            0x75: partial(self.ld8, 19, 3, 'Yd', 'L'),                   # LD (IY+d),L
            0x76: partial(self.defb, 4, 1),
            0x77: partial(self.ld8, 19, 3, 'Yd', 'A'),                   # LD (IY+d),A
            0x78: partial(self.defb, 4, 1),
            0x79: partial(self.defb, 4, 1),
            0x7A: partial(self.defb, 4, 1),
            0x7B: partial(self.defb, 4, 1),
            0x7C: partial(self.ld8, 8, 2, 'A', 'IYh'),                   # LD A,IYh
            0x7D: partial(self.ld8, 8, 2, 'A', 'IYl'),                   # LD A,IYl
            0x7E: partial(self.ld8, 19, 3, 'A', 'Yd'),                   # LD A,(IY+d)
            0x7F: partial(self.defb, 4, 1),
            0x80: partial(self.defb, 4, 1),
            0x81: partial(self.defb, 4, 1),
            0x82: partial(self.defb, 4, 1),
            0x83: partial(self.defb, 4, 1),
            0x84: partial(self.add_a, 8, 2, 'IYh'),                      # ADD A,IYh
            0x85: partial(self.add_a, 8, 2, 'IYl'),                      # ADD A,IYl
            0x86: partial(self.add_a, 19, 3, 'Yd'),                      # ADD A,(IY+d)
            0x87: partial(self.defb, 4, 1),
            0x88: partial(self.defb, 4, 1),
            0x89: partial(self.defb, 4, 1),
            0x8A: partial(self.defb, 4, 1),
            0x8B: partial(self.defb, 4, 1),
            0x8C: partial(self.add_a, 8, 2, 'IYh', 1),                   # ADC A,IYh
            0x8D: partial(self.add_a, 8, 2, 'IYl', 1),                   # ADC A,IYl
            0x8E: partial(self.add_a, 19, 3, 'Yd', 1),                   # ADC A,(IY+d)
            0x8F: partial(self.defb, 4, 1),
            0x90: partial(self.defb, 4, 1),
            0x91: partial(self.defb, 4, 1),
            0x92: partial(self.defb, 4, 1),
            0x93: partial(self.defb, 4, 1),
            0x94: partial(self.add_a, 8, 2, 'IYh', 0, -1),               # SUB IYh
            0x95: partial(self.add_a, 8, 2, 'IYl', 0, -1),               # SUB IYl
            0x96: partial(self.add_a, 19, 3, 'Yd', 0, -1),               # SUB (IY+d)
            0x97: partial(self.defb, 4, 1),
            0x98: partial(self.defb, 4, 1),
            0x99: partial(self.defb, 4, 1),
            0x9A: partial(self.defb, 4, 1),
            0x9B: partial(self.defb, 4, 1),
            0x9C: partial(self.add_a, 8, 2, 'IYh', 1, -1),               # SBC A,IYh
            0x9D: partial(self.add_a, 8, 2, 'IYl', 1, -1),               # SBC A,IYl
            0x9E: partial(self.add_a, 19, 3, 'Yd', 1, -1),               # SBC A,(IY+d)
            0x9F: partial(self.defb, 4, 1),
            0xA0: partial(self.defb, 4, 1),
            0xA1: partial(self.defb, 4, 1),
            0xA2: partial(self.defb, 4, 1),
            0xA3: partial(self.defb, 4, 1),
            0xA4: partial(self.anda, 8, 2, 'IYh'),                       # AND IYh
            0xA5: partial(self.anda, 8, 2, 'IYl'),                       # AND IYl
            0xA6: partial(self.anda, 19, 3, 'Yd'),                       # AND (IY+d)
            0xA7: partial(self.defb, 4, 1),
            0xA8: partial(self.defb, 4, 1),
            0xA9: partial(self.defb, 4, 1),
            0xAA: partial(self.defb, 4, 1),
            0xAB: partial(self.defb, 4, 1),
            0xAC: partial(self.xor, 8, 2, 'IYh'),                        # XOR IYh
            0xAD: partial(self.xor, 8, 2, 'IYl'),                        # XOR IYl
            0xAE: partial(self.xor, 19, 3, 'Yd'),                        # XOR (IY+d)
            0xAF: partial(self.defb, 4, 1),
            0xB0: partial(self.defb, 4, 1),
            0xB1: partial(self.defb, 4, 1),
            0xB2: partial(self.defb, 4, 1),
            0xB3: partial(self.defb, 4, 1),
            0xB4: partial(self.ora, 8, 2, 'IYh'),                        # OR IYh
            0xB5: partial(self.ora, 8, 2, 'IYl'),                        # OR IYl
            0xB6: partial(self.ora, 19, 3, 'Yd'),                        # OR (IY+d)
            0xB7: partial(self.defb, 4, 1),
            0xB8: partial(self.defb, 4, 1),
            0xB9: partial(self.defb, 4, 1),
            0xBA: partial(self.defb, 4, 1),
            0xBB: partial(self.defb, 4, 1),
            0xBC: partial(self.cp, 8, 2, 'IYh'),                         # CP IYh
            0xBD: partial(self.cp, 8, 2, 'IYl'),                         # CP IYl
            0xBE: partial(self.cp, 19, 3, 'Yd'),                         # CP (IY+d)
            0xBF: partial(self.defb, 4, 1),
            0xC0: partial(self.defb, 4, 1),
            0xC1: partial(self.defb, 4, 1),
            0xC2: partial(self.defb, 4, 1),
            0xC3: partial(self.defb, 4, 1),
            0xC4: partial(self.defb, 4, 1),
            0xC5: partial(self.defb, 4, 1),
            0xC6: partial(self.defb, 4, 1),
            0xC7: partial(self.defb, 4, 1),
            0xC8: partial(self.defb, 4, 1),
            0xC9: partial(self.defb, 4, 1),
            0xCA: partial(self.defb, 4, 1),
            0xCB: None,                                                  # FDCB prefix
            0xCC: partial(self.defb, 4, 1),
            0xCD: partial(self.defb, 4, 1),
            0xCE: partial(self.defb, 4, 1),
            0xCF: partial(self.defb, 4, 1),
            0xD0: partial(self.defb, 4, 1),
            0xD1: partial(self.defb, 4, 1),
            0xD2: partial(self.defb, 4, 1),
            0xD3: partial(self.defb, 4, 1),
            0xD4: partial(self.defb, 4, 1),
            0xD5: partial(self.defb, 4, 1),
            0xD6: partial(self.defb, 4, 1),
            0xD7: partial(self.defb, 4, 1),
            0xD8: partial(self.defb, 4, 1),
            0xD9: partial(self.defb, 4, 1),
            0xDA: partial(self.defb, 4, 1),
            0xDB: partial(self.defb, 4, 1),
            0xDC: partial(self.defb, 4, 1),
            0xDD: partial(self.defb, 4, 1),
            0xDE: partial(self.defb, 4, 1),
            0xDF: partial(self.defb, 4, 1),
            0xE0: partial(self.defb, 4, 1),
            0xE1: partial(self.pop, 'IY'),                               # POP IY
            0xE2: partial(self.defb, 4, 1),
            0xE3: partial(self.ex_sp, 'IY'),                             # EX (SP),IY
            0xE4: partial(self.defb, 4, 1),
            0xE5: partial(self.push, 'IY'),                              # PUSH IY
            0xE6: partial(self.defb, 4, 1),
            0xE7: partial(self.defb, 4, 1),
            0xE8: partial(self.defb, 4, 1),
            0xE9: partial(self.jp, '', 0, 0),                            # JP (IY)
            0xEA: partial(self.defb, 4, 1),
            0xEB: partial(self.defb, 4, 1),
            0xEC: partial(self.defb, 4, 1),
            0xED: partial(self.defb, 4, 1),
            0xEE: partial(self.defb, 4, 1),
            0xEF: partial(self.defb, 4, 1),
            0xF0: partial(self.defb, 4, 1),
            0xF1: partial(self.defb, 4, 1),
            0xF2: partial(self.defb, 4, 1),
            0xF3: partial(self.defb, 4, 1),
            0xF4: partial(self.defb, 4, 1),
            0xF5: partial(self.defb, 4, 1),
            0xF6: partial(self.defb, 4, 1),
            0xF7: partial(self.defb, 4, 1),
            0xF8: partial(self.defb, 4, 1),
            0xF9: partial(self.ldsprr, 'IY'),                            # LD SP,IY
            0xFA: partial(self.defb, 4, 1),
            0xFB: partial(self.defb, 4, 1),
            0xFC: partial(self.defb, 4, 1),
            0xFD: partial(self.defb, 4, 1),
            0xFE: partial(self.defb, 4, 1),
            0xFF: partial(self.defb, 4, 1),
        }

        self.after_FDCB = {
            0x00: partial(self.rotate, 23, 4, 'RLC', 128, 'Yd', 1, 'B'), # RLC (IY+d),B
            0x01: partial(self.rotate, 23, 4, 'RLC', 128, 'Yd', 1, 'C'), # RLC (IY+d),C
            0x02: partial(self.rotate, 23, 4, 'RLC', 128, 'Yd', 1, 'D'), # RLC (IY+d),D
            0x03: partial(self.rotate, 23, 4, 'RLC', 128, 'Yd', 1, 'E'), # RLC (IY+d),E
            0x04: partial(self.rotate, 23, 4, 'RLC', 128, 'Yd', 1, 'H'), # RLC (IY+d),H
            0x05: partial(self.rotate, 23, 4, 'RLC', 128, 'Yd', 1, 'L'), # RLC (IY+d),L
            0x06: partial(self.rotate, 23, 4, 'RLC', 128, 'Yd', 1),      # RLC (IY+d)
            0x07: partial(self.rotate, 23, 4, 'RLC', 128, 'Yd', 1, 'A'), # RLC (IY+d),A
            0x08: partial(self.rotate, 23, 4, 'RRC', 1, 'Yd', 1, 'B'),   # RRC (IY+d),B
            0x09: partial(self.rotate, 23, 4, 'RRC', 1, 'Yd', 1, 'C'),   # RRC (IY+d),C
            0x0A: partial(self.rotate, 23, 4, 'RRC', 1, 'Yd', 1, 'D'),   # RRC (IY+d),D
            0x0B: partial(self.rotate, 23, 4, 'RRC', 1, 'Yd', 1, 'E'),   # RRC (IY+d),E
            0x0C: partial(self.rotate, 23, 4, 'RRC', 1, 'Yd', 1, 'H'),   # RRC (IY+d),H
            0x0D: partial(self.rotate, 23, 4, 'RRC', 1, 'Yd', 1, 'L'),   # RRC (IY+d),L
            0x0E: partial(self.rotate, 23, 4, 'RRC', 1, 'Yd', 1),        # RRC (IY+d)
            0x0F: partial(self.rotate, 23, 4, 'RRC', 1, 'Yd', 1, 'A'),   # RRC (IY+d),A
            0x10: partial(self.rotate, 23, 4, 'RL', 128, 'Yd', 0, 'B'),  # RL (IY+d),B
            0x11: partial(self.rotate, 23, 4, 'RL', 128, 'Yd', 0, 'C'),  # RL (IY+d),C
            0x12: partial(self.rotate, 23, 4, 'RL', 128, 'Yd', 0, 'D'),  # RL (IY+d),D
            0x13: partial(self.rotate, 23, 4, 'RL', 128, 'Yd', 0, 'E'),  # RL (IY+d),E
            0x14: partial(self.rotate, 23, 4, 'RL', 128, 'Yd', 0, 'H'),  # RL (IY+d),H
            0x15: partial(self.rotate, 23, 4, 'RL', 128, 'Yd', 0, 'L'),  # RL (IY+d),L
            0x16: partial(self.rotate, 23, 4, 'RL', 128, 'Yd'),          # RL (IY+d)
            0x17: partial(self.rotate, 23, 4, 'RL', 128, 'Yd', 0, 'A'),  # RL (IY+d),A
            0x18: partial(self.rotate, 23, 4, 'RR', 1, 'Yd', 0, 'B'),    # RR (IY+d),B
            0x19: partial(self.rotate, 23, 4, 'RR', 1, 'Yd', 0, 'C'),    # RR (IY+d),C
            0x1A: partial(self.rotate, 23, 4, 'RR', 1, 'Yd', 0, 'D'),    # RR (IY+d),D
            0x1B: partial(self.rotate, 23, 4, 'RR', 1, 'Yd', 0, 'E'),    # RR (IY+d),E
            0x1C: partial(self.rotate, 23, 4, 'RR', 1, 'Yd', 0, 'H'),    # RR (IY+d),H
            0x1D: partial(self.rotate, 23, 4, 'RR', 1, 'Yd', 0, 'L'),    # RR (IY+d),L
            0x1E: partial(self.rotate, 23, 4, 'RR', 1, 'Yd'),            # RR (IY+d)
            0x1F: partial(self.rotate, 23, 4, 'RR', 1, 'Yd', 0, 'A'),    # RR (IY+d),A
            0x20: partial(self.shift, 23, 4, 'SLA', 128, 'Yd', 'B'),     # SLA (IY+d),B
            0x21: partial(self.shift, 23, 4, 'SLA', 128, 'Yd', 'C'),     # SLA (IY+d),C
            0x22: partial(self.shift, 23, 4, 'SLA', 128, 'Yd', 'D'),     # SLA (IY+d),D
            0x23: partial(self.shift, 23, 4, 'SLA', 128, 'Yd', 'E'),     # SLA (IY+d),E
            0x24: partial(self.shift, 23, 4, 'SLA', 128, 'Yd', 'H'),     # SLA (IY+d),H
            0x25: partial(self.shift, 23, 4, 'SLA', 128, 'Yd', 'L'),     # SLA (IY+d),L
            0x26: partial(self.shift, 23, 4, 'SLA', 128, 'Yd'),          # SLA (IY+d)
            0x27: partial(self.shift, 23, 4, 'SLA', 128, 'Yd', 'A'),     # SLA (IY+d),A
            0x28: partial(self.shift, 23, 4, 'SRA', 1, 'Yd', 'B'),       # SRA (IY+d),B
            0x29: partial(self.shift, 23, 4, 'SRA', 1, 'Yd', 'C'),       # SRA (IY+d),C
            0x2A: partial(self.shift, 23, 4, 'SRA', 1, 'Yd', 'D'),       # SRA (IY+d),D
            0x2B: partial(self.shift, 23, 4, 'SRA', 1, 'Yd', 'E'),       # SRA (IY+d),E
            0x2C: partial(self.shift, 23, 4, 'SRA', 1, 'Yd', 'H'),       # SRA (IY+d),H
            0x2D: partial(self.shift, 23, 4, 'SRA', 1, 'Yd', 'L'),       # SRA (IY+d),L
            0x2E: partial(self.shift, 23, 4, 'SRA', 1, 'Yd'),            # SRA (IY+d)
            0x2F: partial(self.shift, 23, 4, 'SRA', 1, 'Yd', 'A'),       # SRA (IY+d),A
            0x30: partial(self.shift, 23, 4, 'SLL', 128, 'Yd', 'B'),     # SLL (IY+d),B
            0x31: partial(self.shift, 23, 4, 'SLL', 128, 'Yd', 'C'),     # SLL (IY+d),C
            0x32: partial(self.shift, 23, 4, 'SLL', 128, 'Yd', 'D'),     # SLL (IY+d),D
            0x33: partial(self.shift, 23, 4, 'SLL', 128, 'Yd', 'E'),     # SLL (IY+d),E
            0x34: partial(self.shift, 23, 4, 'SLL', 128, 'Yd', 'H'),     # SLL (IY+d),H
            0x35: partial(self.shift, 23, 4, 'SLL', 128, 'Yd', 'L'),     # SLL (IY+d),L
            0x36: partial(self.shift, 23, 4, 'SLL', 128, 'Yd'),          # SLL (IY+d)
            0x37: partial(self.shift, 23, 4, 'SLL', 128, 'Yd', 'A'),     # SLL (IY+d),A
            0x38: partial(self.shift, 23, 4, 'SRL', 1, 'Yd', 'B'),       # SRL (IY+d),B
            0x39: partial(self.shift, 23, 4, 'SRL', 1, 'Yd', 'C'),       # SRL (IY+d),C
            0x3A: partial(self.shift, 23, 4, 'SRL', 1, 'Yd', 'D'),       # SRL (IY+d),D
            0x3B: partial(self.shift, 23, 4, 'SRL', 1, 'Yd', 'E'),       # SRL (IY+d),E
            0x3C: partial(self.shift, 23, 4, 'SRL', 1, 'Yd', 'H'),       # SRL (IY+d),H
            0x3D: partial(self.shift, 23, 4, 'SRL', 1, 'Yd', 'L'),       # SRL (IY+d),L
            0x3E: partial(self.shift, 23, 4, 'SRL', 1, 'Yd'),            # SRL (IY+d)
            0x3F: partial(self.shift, 23, 4, 'SRL', 1, 'Yd', 'A'),       # SRL (IY+d),A
            0x40: partial(self.bit, 20, 4, 0, 'Yd'),                     # BIT 0,(IY+d)
            0x41: partial(self.bit, 20, 4, 0, 'Yd'),                     # BIT 0,(IY+d)
            0x42: partial(self.bit, 20, 4, 0, 'Yd'),                     # BIT 0,(IY+d)
            0x43: partial(self.bit, 20, 4, 0, 'Yd'),                     # BIT 0,(IY+d)
            0x44: partial(self.bit, 20, 4, 0, 'Yd'),                     # BIT 0,(IY+d)
            0x45: partial(self.bit, 20, 4, 0, 'Yd'),                     # BIT 0,(IY+d)
            0x46: partial(self.bit, 20, 4, 0, 'Yd'),                     # BIT 0,(IY+d)
            0x47: partial(self.bit, 20, 4, 0, 'Yd'),                     # BIT 0,(IY+d)
            0x48: partial(self.bit, 20, 4, 1, 'Yd'),                     # BIT 1,(IY+d)
            0x49: partial(self.bit, 20, 4, 1, 'Yd'),                     # BIT 1,(IY+d)
            0x4A: partial(self.bit, 20, 4, 1, 'Yd'),                     # BIT 1,(IY+d)
            0x4B: partial(self.bit, 20, 4, 1, 'Yd'),                     # BIT 1,(IY+d)
            0x4C: partial(self.bit, 20, 4, 1, 'Yd'),                     # BIT 1,(IY+d)
            0x4D: partial(self.bit, 20, 4, 1, 'Yd'),                     # BIT 1,(IY+d)
            0x4E: partial(self.bit, 20, 4, 1, 'Yd'),                     # BIT 1,(IY+d)
            0x4F: partial(self.bit, 20, 4, 1, 'Yd'),                     # BIT 1,(IY+d)
            0x50: partial(self.bit, 20, 4, 2, 'Yd'),                     # BIT 2,(IY+d)
            0x51: partial(self.bit, 20, 4, 2, 'Yd'),                     # BIT 2,(IY+d)
            0x52: partial(self.bit, 20, 4, 2, 'Yd'),                     # BIT 2,(IY+d)
            0x53: partial(self.bit, 20, 4, 2, 'Yd'),                     # BIT 2,(IY+d)
            0x54: partial(self.bit, 20, 4, 2, 'Yd'),                     # BIT 2,(IY+d)
            0x55: partial(self.bit, 20, 4, 2, 'Yd'),                     # BIT 2,(IY+d)
            0x56: partial(self.bit, 20, 4, 2, 'Yd'),                     # BIT 2,(IY+d)
            0x57: partial(self.bit, 20, 4, 2, 'Yd'),                     # BIT 2,(IY+d)
            0x58: partial(self.bit, 20, 4, 3, 'Yd'),                     # BIT 3,(IY+d)
            0x59: partial(self.bit, 20, 4, 3, 'Yd'),                     # BIT 3,(IY+d)
            0x5A: partial(self.bit, 20, 4, 3, 'Yd'),                     # BIT 3,(IY+d)
            0x5B: partial(self.bit, 20, 4, 3, 'Yd'),                     # BIT 3,(IY+d)
            0x5C: partial(self.bit, 20, 4, 3, 'Yd'),                     # BIT 3,(IY+d)
            0x5D: partial(self.bit, 20, 4, 3, 'Yd'),                     # BIT 3,(IY+d)
            0x5E: partial(self.bit, 20, 4, 3, 'Yd'),                     # BIT 3,(IY+d)
            0x5F: partial(self.bit, 20, 4, 3, 'Yd'),                     # BIT 3,(IY+d)
            0x60: partial(self.bit, 20, 4, 4, 'Yd'),                     # BIT 4,(IY+d)
            0x61: partial(self.bit, 20, 4, 4, 'Yd'),                     # BIT 4,(IY+d)
            0x62: partial(self.bit, 20, 4, 4, 'Yd'),                     # BIT 4,(IY+d)
            0x63: partial(self.bit, 20, 4, 4, 'Yd'),                     # BIT 4,(IY+d)
            0x64: partial(self.bit, 20, 4, 4, 'Yd'),                     # BIT 4,(IY+d)
            0x65: partial(self.bit, 20, 4, 4, 'Yd'),                     # BIT 4,(IY+d)
            0x66: partial(self.bit, 20, 4, 4, 'Yd'),                     # BIT 4,(IY+d)
            0x67: partial(self.bit, 20, 4, 4, 'Yd'),                     # BIT 4,(IY+d)
            0x68: partial(self.bit, 20, 4, 5, 'Yd'),                     # BIT 5,(IY+d)
            0x69: partial(self.bit, 20, 4, 5, 'Yd'),                     # BIT 5,(IY+d)
            0x6A: partial(self.bit, 20, 4, 5, 'Yd'),                     # BIT 5,(IY+d)
            0x6B: partial(self.bit, 20, 4, 5, 'Yd'),                     # BIT 5,(IY+d)
            0x6C: partial(self.bit, 20, 4, 5, 'Yd'),                     # BIT 5,(IY+d)
            0x6D: partial(self.bit, 20, 4, 5, 'Yd'),                     # BIT 5,(IY+d)
            0x6E: partial(self.bit, 20, 4, 5, 'Yd'),                     # BIT 5,(IY+d)
            0x6F: partial(self.bit, 20, 4, 5, 'Yd'),                     # BIT 5,(IY+d)
            0x70: partial(self.bit, 20, 4, 6, 'Yd'),                     # BIT 6,(IY+d)
            0x71: partial(self.bit, 20, 4, 6, 'Yd'),                     # BIT 6,(IY+d)
            0x72: partial(self.bit, 20, 4, 6, 'Yd'),                     # BIT 6,(IY+d)
            0x73: partial(self.bit, 20, 4, 6, 'Yd'),                     # BIT 6,(IY+d)
            0x74: partial(self.bit, 20, 4, 6, 'Yd'),                     # BIT 6,(IY+d)
            0x75: partial(self.bit, 20, 4, 6, 'Yd'),                     # BIT 6,(IY+d)
            0x76: partial(self.bit, 20, 4, 6, 'Yd'),                     # BIT 6,(IY+d)
            0x77: partial(self.bit, 20, 4, 6, 'Yd'),                     # BIT 6,(IY+d)
            0x78: partial(self.bit, 20, 4, 7, 'Yd'),                     # BIT 7,(IY+d)
            0x79: partial(self.bit, 20, 4, 7, 'Yd'),                     # BIT 7,(IY+d)
            0x7A: partial(self.bit, 20, 4, 7, 'Yd'),                     # BIT 7,(IY+d)
            0x7B: partial(self.bit, 20, 4, 7, 'Yd'),                     # BIT 7,(IY+d)
            0x7C: partial(self.bit, 20, 4, 7, 'Yd'),                     # BIT 7,(IY+d)
            0x7D: partial(self.bit, 20, 4, 7, 'Yd'),                     # BIT 7,(IY+d)
            0x7E: partial(self.bit, 20, 4, 7, 'Yd'),                     # BIT 7,(IY+d)
            0x7F: partial(self.bit, 20, 4, 7, 'Yd'),                     # BIT 7,(IY+d)
            0x80: partial(self.res_set, 23, 4, 0, 'Yd', 0, 'B'),         # RES 0,(IY+d),B
            0x81: partial(self.res_set, 23, 4, 0, 'Yd', 0, 'C'),         # RES 0,(IY+d),C
            0x82: partial(self.res_set, 23, 4, 0, 'Yd', 0, 'D'),         # RES 0,(IY+d),D
            0x83: partial(self.res_set, 23, 4, 0, 'Yd', 0, 'E'),         # RES 0,(IY+d),E
            0x84: partial(self.res_set, 23, 4, 0, 'Yd', 0, 'H'),         # RES 0,(IY+d),H
            0x85: partial(self.res_set, 23, 4, 0, 'Yd', 0, 'L'),         # RES 0,(IY+d),L
            0x86: partial(self.res_set, 23, 4, 0, 'Yd', 0),              # RES 0,(IY+d)
            0x87: partial(self.res_set, 23, 4, 0, 'Yd', 0, 'A'),         # RES 0,(IY+d),A
            0x88: partial(self.res_set, 23, 4, 1, 'Yd', 0, 'B'),         # RES 1,(IY+d),B
            0x89: partial(self.res_set, 23, 4, 1, 'Yd', 0, 'C'),         # RES 1,(IY+d),C
            0x8A: partial(self.res_set, 23, 4, 1, 'Yd', 0, 'D'),         # RES 1,(IY+d),D
            0x8B: partial(self.res_set, 23, 4, 1, 'Yd', 0, 'E'),         # RES 1,(IY+d),E
            0x8C: partial(self.res_set, 23, 4, 1, 'Yd', 0, 'H'),         # RES 1,(IY+d),H
            0x8D: partial(self.res_set, 23, 4, 1, 'Yd', 0, 'L'),         # RES 1,(IY+d),L
            0x8E: partial(self.res_set, 23, 4, 1, 'Yd', 0),              # RES 1,(IY+d)
            0x8F: partial(self.res_set, 23, 4, 1, 'Yd', 0, 'A'),         # RES 1,(IY+d),A
            0x90: partial(self.res_set, 23, 4, 2, 'Yd', 0, 'B'),         # RES 2,(IY+d),B
            0x91: partial(self.res_set, 23, 4, 2, 'Yd', 0, 'C'),         # RES 2,(IY+d),C
            0x92: partial(self.res_set, 23, 4, 2, 'Yd', 0, 'D'),         # RES 2,(IY+d),D
            0x93: partial(self.res_set, 23, 4, 2, 'Yd', 0, 'E'),         # RES 2,(IY+d),E
            0x94: partial(self.res_set, 23, 4, 2, 'Yd', 0, 'H'),         # RES 2,(IY+d),H
            0x95: partial(self.res_set, 23, 4, 2, 'Yd', 0, 'L'),         # RES 2,(IY+d),L
            0x96: partial(self.res_set, 23, 4, 2, 'Yd', 0),              # RES 2,(IY+d)
            0x97: partial(self.res_set, 23, 4, 2, 'Yd', 0, 'A'),         # RES 2,(IY+d),A
            0x98: partial(self.res_set, 23, 4, 3, 'Yd', 0, 'B'),         # RES 3,(IY+d),B
            0x99: partial(self.res_set, 23, 4, 3, 'Yd', 0, 'C'),         # RES 3,(IY+d),C
            0x9A: partial(self.res_set, 23, 4, 3, 'Yd', 0, 'D'),         # RES 3,(IY+d),D
            0x9B: partial(self.res_set, 23, 4, 3, 'Yd', 0, 'E'),         # RES 3,(IY+d),E
            0x9C: partial(self.res_set, 23, 4, 3, 'Yd', 0, 'H'),         # RES 3,(IY+d),H
            0x9D: partial(self.res_set, 23, 4, 3, 'Yd', 0, 'L'),         # RES 3,(IY+d),L
            0x9E: partial(self.res_set, 23, 4, 3, 'Yd', 0),              # RES 3,(IY+d)
            0x9F: partial(self.res_set, 23, 4, 3, 'Yd', 0, 'A'),         # RES 3,(IY+d),A
            0xA0: partial(self.res_set, 23, 4, 4, 'Yd', 0, 'B'),         # RES 4,(IY+d),B
            0xA1: partial(self.res_set, 23, 4, 4, 'Yd', 0, 'C'),         # RES 4,(IY+d),C
            0xA2: partial(self.res_set, 23, 4, 4, 'Yd', 0, 'D'),         # RES 4,(IY+d),D
            0xA3: partial(self.res_set, 23, 4, 4, 'Yd', 0, 'E'),         # RES 4,(IY+d),E
            0xA4: partial(self.res_set, 23, 4, 4, 'Yd', 0, 'H'),         # RES 4,(IY+d),H
            0xA5: partial(self.res_set, 23, 4, 4, 'Yd', 0, 'L'),         # RES 4,(IY+d),L
            0xA6: partial(self.res_set, 23, 4, 4, 'Yd', 0),              # RES 4,(IY+d)
            0xA7: partial(self.res_set, 23, 4, 4, 'Yd', 0, 'A'),         # RES 4,(IY+d),A
            0xA8: partial(self.res_set, 23, 4, 5, 'Yd', 0, 'B'),         # RES 5,(IY+d),B
            0xA9: partial(self.res_set, 23, 4, 5, 'Yd', 0, 'C'),         # RES 5,(IY+d),C
            0xAA: partial(self.res_set, 23, 4, 5, 'Yd', 0, 'D'),         # RES 5,(IY+d),D
            0xAB: partial(self.res_set, 23, 4, 5, 'Yd', 0, 'E'),         # RES 5,(IY+d),E
            0xAC: partial(self.res_set, 23, 4, 5, 'Yd', 0, 'H'),         # RES 5,(IY+d),H
            0xAD: partial(self.res_set, 23, 4, 5, 'Yd', 0, 'L'),         # RES 5,(IY+d),L
            0xAE: partial(self.res_set, 23, 4, 5, 'Yd', 0),              # RES 5,(IY+d)
            0xAF: partial(self.res_set, 23, 4, 5, 'Yd', 0, 'A'),         # RES 5,(IY+d),A
            0xB0: partial(self.res_set, 23, 4, 6, 'Yd', 0, 'B'),         # RES 6,(IY+d),B
            0xB1: partial(self.res_set, 23, 4, 6, 'Yd', 0, 'C'),         # RES 6,(IY+d),C
            0xB2: partial(self.res_set, 23, 4, 6, 'Yd', 0, 'D'),         # RES 6,(IY+d),D
            0xB3: partial(self.res_set, 23, 4, 6, 'Yd', 0, 'E'),         # RES 6,(IY+d),E
            0xB4: partial(self.res_set, 23, 4, 6, 'Yd', 0, 'H'),         # RES 6,(IY+d),H
            0xB5: partial(self.res_set, 23, 4, 6, 'Yd', 0, 'L'),         # RES 6,(IY+d),L
            0xB6: partial(self.res_set, 23, 4, 6, 'Yd', 0),              # RES 6,(IY+d)
            0xB7: partial(self.res_set, 23, 4, 6, 'Yd', 0, 'A'),         # RES 6,(IY+d),A
            0xB8: partial(self.res_set, 23, 4, 7, 'Yd', 0, 'B'),         # RES 7,(IY+d),B
            0xB9: partial(self.res_set, 23, 4, 7, 'Yd', 0, 'C'),         # RES 7,(IY+d),C
            0xBA: partial(self.res_set, 23, 4, 7, 'Yd', 0, 'D'),         # RES 7,(IY+d),D
            0xBB: partial(self.res_set, 23, 4, 7, 'Yd', 0, 'E'),         # RES 7,(IY+d),E
            0xBC: partial(self.res_set, 23, 4, 7, 'Yd', 0, 'H'),         # RES 7,(IY+d),H
            0xBD: partial(self.res_set, 23, 4, 7, 'Yd', 0, 'L'),         # RES 7,(IY+d),L
            0xBE: partial(self.res_set, 23, 4, 7, 'Yd', 0),              # RES 7,(IY+d)
            0xBF: partial(self.res_set, 23, 4, 7, 'Yd', 0, 'A'),         # RES 7,(IY+d),A
            0xC0: partial(self.res_set, 23, 4, 0, 'Yd', 1, 'B'),         # SET 0,(IY+d),B
            0xC1: partial(self.res_set, 23, 4, 0, 'Yd', 1, 'C'),         # SET 0,(IY+d),C
            0xC2: partial(self.res_set, 23, 4, 0, 'Yd', 1, 'D'),         # SET 0,(IY+d),D
            0xC3: partial(self.res_set, 23, 4, 0, 'Yd', 1, 'E'),         # SET 0,(IY+d),E
            0xC4: partial(self.res_set, 23, 4, 0, 'Yd', 1, 'H'),         # SET 0,(IY+d),H
            0xC5: partial(self.res_set, 23, 4, 0, 'Yd', 1, 'L'),         # SET 0,(IY+d),L
            0xC6: partial(self.res_set, 23, 4, 0, 'Yd', 1),              # SET 0,(IY+d)
            0xC7: partial(self.res_set, 23, 4, 0, 'Yd', 1, 'A'),         # SET 0,(IY+d),A
            0xC8: partial(self.res_set, 23, 4, 1, 'Yd', 1, 'B'),         # SET 1,(IY+d),B
            0xC9: partial(self.res_set, 23, 4, 1, 'Yd', 1, 'C'),         # SET 1,(IY+d),C
            0xCA: partial(self.res_set, 23, 4, 1, 'Yd', 1, 'D'),         # SET 1,(IY+d),D
            0xCB: partial(self.res_set, 23, 4, 1, 'Yd', 1, 'E'),         # SET 1,(IY+d),E
            0xCC: partial(self.res_set, 23, 4, 1, 'Yd', 1, 'H'),         # SET 1,(IY+d),H
            0xCD: partial(self.res_set, 23, 4, 1, 'Yd', 1, 'L'),         # SET 1,(IY+d),L
            0xCE: partial(self.res_set, 23, 4, 1, 'Yd', 1),              # SET 1,(IY+d)
            0xCF: partial(self.res_set, 23, 4, 1, 'Yd', 1, 'A'),         # SET 1,(IY+d),A
            0xD0: partial(self.res_set, 23, 4, 2, 'Yd', 1, 'B'),         # SET 2,(IY+d),B
            0xD1: partial(self.res_set, 23, 4, 2, 'Yd', 1, 'C'),         # SET 2,(IY+d),C
            0xD2: partial(self.res_set, 23, 4, 2, 'Yd', 1, 'D'),         # SET 2,(IY+d),D
            0xD3: partial(self.res_set, 23, 4, 2, 'Yd', 1, 'E'),         # SET 2,(IY+d),E
            0xD4: partial(self.res_set, 23, 4, 2, 'Yd', 1, 'H'),         # SET 2,(IY+d),H
            0xD5: partial(self.res_set, 23, 4, 2, 'Yd', 1, 'L'),         # SET 2,(IY+d),L
            0xD6: partial(self.res_set, 23, 4, 2, 'Yd', 1),              # SET 2,(IY+d)
            0xD7: partial(self.res_set, 23, 4, 2, 'Yd', 1, 'A'),         # SET 2,(IY+d),A
            0xD8: partial(self.res_set, 23, 4, 3, 'Yd', 1, 'B'),         # SET 3,(IY+d),B
            0xD9: partial(self.res_set, 23, 4, 3, 'Yd', 1, 'C'),         # SET 3,(IY+d),C
            0xDA: partial(self.res_set, 23, 4, 3, 'Yd', 1, 'D'),         # SET 3,(IY+d),D
            0xDB: partial(self.res_set, 23, 4, 3, 'Yd', 1, 'E'),         # SET 3,(IY+d),E
            0xDC: partial(self.res_set, 23, 4, 3, 'Yd', 1, 'H'),         # SET 3,(IY+d),H
            0xDD: partial(self.res_set, 23, 4, 3, 'Yd', 1, 'L'),         # SET 3,(IY+d),L
            0xDE: partial(self.res_set, 23, 4, 3, 'Yd', 1),              # SET 3,(IY+d)
            0xDF: partial(self.res_set, 23, 4, 3, 'Yd', 1, 'A'),         # SET 3,(IY+d),A
            0xE0: partial(self.res_set, 23, 4, 4, 'Yd', 1, 'B'),         # SET 4,(IY+d),B
            0xE1: partial(self.res_set, 23, 4, 4, 'Yd', 1, 'C'),         # SET 4,(IY+d),C
            0xE2: partial(self.res_set, 23, 4, 4, 'Yd', 1, 'D'),         # SET 4,(IY+d),D
            0xE3: partial(self.res_set, 23, 4, 4, 'Yd', 1, 'E'),         # SET 4,(IY+d),E
            0xE4: partial(self.res_set, 23, 4, 4, 'Yd', 1, 'H'),         # SET 4,(IY+d),H
            0xE5: partial(self.res_set, 23, 4, 4, 'Yd', 1, 'L'),         # SET 4,(IY+d),L
            0xE6: partial(self.res_set, 23, 4, 4, 'Yd', 1),              # SET 4,(IY+d)
            0xE7: partial(self.res_set, 23, 4, 4, 'Yd', 1, 'A'),         # SET 4,(IY+d),A
            0xE8: partial(self.res_set, 23, 4, 5, 'Yd', 1, 'B'),         # SET 5,(IY+d),B
            0xE9: partial(self.res_set, 23, 4, 5, 'Yd', 1, 'C'),         # SET 5,(IY+d),C
            0xEA: partial(self.res_set, 23, 4, 5, 'Yd', 1, 'D'),         # SET 5,(IY+d),D
            0xEB: partial(self.res_set, 23, 4, 5, 'Yd', 1, 'E'),         # SET 5,(IY+d),E
            0xEC: partial(self.res_set, 23, 4, 5, 'Yd', 1, 'H'),         # SET 5,(IY+d),H
            0xED: partial(self.res_set, 23, 4, 5, 'Yd', 1, 'L'),         # SET 5,(IY+d),L
            0xEE: partial(self.res_set, 23, 4, 5, 'Yd', 1),              # SET 5,(IY+d)
            0xEF: partial(self.res_set, 23, 4, 5, 'Yd', 1, 'A'),         # SET 5,(IY+d),A
            0xF0: partial(self.res_set, 23, 4, 6, 'Yd', 1, 'B'),         # SET 6,(IY+d),B
            0xF1: partial(self.res_set, 23, 4, 6, 'Yd', 1, 'C'),         # SET 6,(IY+d),C
            0xF2: partial(self.res_set, 23, 4, 6, 'Yd', 1, 'D'),         # SET 6,(IY+d),D
            0xF3: partial(self.res_set, 23, 4, 6, 'Yd', 1, 'E'),         # SET 6,(IY+d),E
            0xF4: partial(self.res_set, 23, 4, 6, 'Yd', 1, 'H'),         # SET 6,(IY+d),H
            0xF5: partial(self.res_set, 23, 4, 6, 'Yd', 1, 'L'),         # SET 6,(IY+d),L
            0xF6: partial(self.res_set, 23, 4, 6, 'Yd', 1),              # SET 6,(IY+d)
            0xF7: partial(self.res_set, 23, 4, 6, 'Yd', 1, 'A'),         # SET 6,(IY+d),A
            0xF8: partial(self.res_set, 23, 4, 7, 'Yd', 1, 'B'),         # SET 7,(IY+d),B
            0xF9: partial(self.res_set, 23, 4, 7, 'Yd', 1, 'C'),         # SET 7,(IY+d),C
            0xFA: partial(self.res_set, 23, 4, 7, 'Yd', 1, 'D'),         # SET 7,(IY+d),D
            0xFB: partial(self.res_set, 23, 4, 7, 'Yd', 1, 'E'),         # SET 7,(IY+d),E
            0xFC: partial(self.res_set, 23, 4, 7, 'Yd', 1, 'H'),         # SET 7,(IY+d),H
            0xFD: partial(self.res_set, 23, 4, 7, 'Yd', 1, 'L'),         # SET 7,(IY+d),L
            0xFE: partial(self.res_set, 23, 4, 7, 'Yd', 1),              # SET 7,(IY+d)
            0xFF: partial(self.res_set, 23, 4, 7, 'Yd', 1, 'A'),         # SET 7,(IY+d),A
        }
