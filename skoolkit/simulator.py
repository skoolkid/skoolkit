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

from collections import namedtuple

Instruction = namedtuple('Instruction', 'time address operation data tstates')

PARITY = (
    1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1,
    0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0,
    0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0,
    1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1,
    0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0,
    1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1,
    1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1,
    0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0,
    0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0,
    1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1,
    1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1,
    0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0,
    1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1,
    0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0,
    0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0,
    1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1
)

FLAGS = {
    'C': 1,
    'N': 2,
    'P': 4,
    '3': 8,
    'H': 16,
    '5': 32,
    'Z': 64,
    'S': 128
}

CONDITIONS = {
    'NZ': -64,
    'Z': 64,
    'NC': -1,
    'C': 1,
    'PO': -4,
    'PE': 4,
    'P': -128,
    'M': 128
}

FRAME_DURATION = 69888

class Simulator:
    def __init__(self, snapshot, registers=None, state=None):
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
        self.iff2 = state.get('iff2', 0)
        self.tstates = state.get('tstates', 0)
        self.tracer = None

    def set_tracer(self, tracer):
        self.tracer = tracer

    def run(self, pc=None):
        if pc is not None:
            self.pc = pc
        while 1:
            opcode = self.snapshot[self.pc]
            r_inc = 2
            if opcode == 0xCB:
                timing, f, size, args = self.after_CB[self.snapshot[(self.pc + 1) & 0xFFFF]]
            elif opcode == 0xED:
                timing, f, size, args = self.after_ED[self.snapshot[(self.pc + 1) & 0xFFFF]]
            elif opcode in (0xDD, 0xFD):
                opcode2 = self.snapshot[(self.pc + 1) & 0xFFFF]
                if opcode2 == 0xCB:
                    timing, f, size, args = self.after_DDCB[self.snapshot[(self.pc + 3) & 0xFFFF]]
                else:
                    timing, f, size, args = self.after_DD[opcode2]
            else:
                r_inc = 1
                timing, f, size, args = self.opcodes[opcode]
            eidx = self.pc + size
            if eidx <= 65536:
                data = self.snapshot[self.pc:eidx]
            else:
                data = self.snapshot[self.pc:] + self.snapshot[:eidx & 0xFFFF]
            operation, pc, tstates = f(self, timing, data, *args)
            r = self.registers['R']
            self.registers['R'] = (r & 0x80) + ((r + r_inc) & 0x7F)
            if self.tracer:
                instruction = Instruction(self.tstates, self.pc, operation, data, tstates)
                self.pc = pc & 0xFFFF
                self.tstates += tstates
                if self.tracer.trace(self, instruction):
                    break
                self.pc = self.registers.get('PC', self.pc)
            else:
                self.pc = pc & 0xFFFF
                self.tstates += tstates
                break

    def set_registers(self, registers):
        for reg, value in registers.items():
            if reg == 'PC':
                self.pc = value
            elif reg == 'SP' or len(reg) == 1:
                self.registers[reg] = value
            elif reg in ('IX', 'IY'):
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

    def get_condition(self, condition):
        cbit = CONDITIONS[condition]
        value = self.registers['F'] & abs(cbit)
        if cbit < 0:
            return value == 0
        return value > 0

    def get_flag(self, flag):
        return int(self.registers['F'] & FLAGS[flag] > 0)

    def set_flag(self, flag, value):
        bit = FLAGS[flag]
        if value:
            self.registers['F'] |= bit
        else:
            self.registers['F'] &= 255 - bit

    def index(self, data):
        offset = data[2]
        if offset >= 128:
            offset -= 256
        if data[0] == 0xDD:
            addr = self.registers['IXl'] + 256 * self.registers['IXh'] + offset
            ireg = 'IX'
        else:
            addr = self.registers['IYl'] + 256 * self.registers['IYh'] + offset
            ireg = 'IY'
        if offset >= 0:
            return addr, f'({ireg}+${offset:02X})'
        return addr, f'({ireg}-${-offset:02X})'

    def get_operand_value(self, data, reg):
        operand = reg
        if reg in ('(HL)', '(DE)', '(BC)'):
            rr = self.registers[reg[2]] + 256 * self.registers[reg[1]]
            value = self.peek(rr)
        elif reg:
            if data[0] == 0xFD:
                operand = reg = reg.replace('X', 'Y')
            value = self.registers[reg]
        elif reg is None:
            value = data[-1]
            operand = f'${value:02X}'
        else:
            addr, operand = self.index(data)
            value = self.peek(addr)
        return operand, value

    def set_operand_value(self, data, reg, value):
        if reg in ('(HL)', '(DE)', '(BC)'):
            rr = self.registers[reg[2]] + 256 * self.registers[reg[1]]
            self.poke(rr, value)
        elif reg:
            if data[0] == 0xFD:
                reg = reg.replace('X', 'Y')
            self.registers[reg] = value
        else:
            addr, operand = self.index(data)
            self.poke(addr, value)

    def peek(self, address, count=1):
        if hasattr(self.tracer, 'read_memory'):
            self.tracer.read_memory(self, address, count)
        if count == 1:
            return self.snapshot[address]
        return self.snapshot[address], self.snapshot[(address + 1) & 0xFFFF]

    def poke(self, address, *values):
        if hasattr(self.tracer, 'write_memory'):
            self.tracer.write_memory(self, address, values)
        if address > 0x3FFF:
            self.snapshot[address] = values[0]
        if len(values) > 1:
            address = (address + 1) & 0xFFFF
            if address > 0x3FFF:
                self.snapshot[address] = values[1]

    def add_a(self, timing, data, reg=None, carry=0, mult=1):
        operand, value = self.get_operand_value(data, reg)
        if mult == 1:
            if carry:
                op = f'ADC A,{operand}'
            else:
                op = f'ADD A,{operand}'
        elif carry:
            op = f'SBC A,{operand}'
        else:
            op = f'SUB {operand}'

        old_c = self.get_flag('C')
        old_a = self.registers['A']
        addend = value + carry * old_c
        a = old_a + mult * addend
        if a < 0 or a > 255:
            a = a & 255
            self.set_flag('C', 1)
        else:
            self.set_flag('C', 0)
        self.set_flag('S', a & 0x80)
        self.set_flag('Z', a == 0)
        self.set_flag('5', a & 0x20)
        if mult == 1:
            s_value = value
            if op == 'ADC A,A' and old_a & 0x0F == 0x0F:
                self.set_flag('H', 1)
            else:
                self.set_flag('H', ((old_a & 0x0F) + (addend & 0x0F)) & 0x10)
        else:
            s_value = ~value # Flip sign bit when subtracting
            if op == 'SBC A,A' and old_a & 0x0F == 0x0F:
                self.set_flag('H', old_c)
            else:
                self.set_flag('H', ((old_a & 0x0F) - (addend & 0x0F)) & 0x10)
        self.set_flag('3', a & 0x08)
        if ((old_a ^ s_value) ^ 0x80) & 0x80:
            # Augend and addend signs are the same - overflow if their sign
            # differs from the sign of the result
            self.set_flag('P', (a ^ old_a) & 0x80)
        else:
            # Augend and addend signs are different - no overflow
            self.set_flag('P', 0)
        self.set_flag('N', mult < 0) # Set for SBC/SUB, reset otherwise
        self.registers['A'] = a

        return op, self.pc + len(data), timing

    def add16(self, timing, data, reg, carry=0, mult=1):
        if reg == 'SP':
            addend_v = self.registers['SP']
        if data[0] == 0xDD:
            augend = 'IX'
            augend_v = self.registers['IXl'] + 256 * self.registers['IXh']
            if reg == 'IX':
                addend_v = augend_v
            elif reg != 'SP':
                addend_v = self.registers[reg[1]] + 256 * self.registers[reg[0]]
        elif data[0] == 0xFD:
            augend = 'IY'
            augend_v = self.registers['IYl'] + 256 * self.registers['IYh']
            if reg == 'IX':
                addend_v = augend_v
                reg = 'IY'
            elif reg != 'SP':
                addend_v = self.registers[reg[1]] + 256 * self.registers[reg[0]]
        else:
            augend = 'HL'
            augend_v = self.registers['L'] + 256 * self.registers['H']
            if reg != 'SP':
                addend_v = self.registers[reg[1]] + 256 * self.registers[reg[0]]

        s_addend = addend_v
        addend_v += carry * self.get_flag('C')
        value = augend_v + mult * addend_v
        if value < 0 or value > 0xFFFF:
            value &= 0xFFFF
            self.set_flag('C', 1)
        else:
            self.set_flag('C', 0)

        if data[0] == 0xDD:
            self.registers['IXl'] = value % 256
            self.registers['IXh'] = value // 256
        elif data[0] == 0xFD:
            self.registers['IYl'] = value % 256
            self.registers['IYh'] = value // 256
        else:
            self.registers['L'] = value % 256
            self.registers['H'] = value // 256

        if mult == 1:
            self.set_flag('H', ((augend_v & 0x0FFF) + (addend_v & 0x0FFF)) & 0x1000)
            self.set_flag('N', 0)
            if carry:
                op = 'ADC'
            else:
                op = 'ADD'
        else:
            self.set_flag('N', 1)
            op = 'SBC'
            self.set_flag('H', ((augend_v & 0x0FFF) - (addend_v & 0x0FFF)) & 0x1000)
            s_addend = ~s_addend

        if op != 'ADD':
            self.set_flag('S', value & 0x8000)
            self.set_flag('Z', value == 0)
            if ((augend_v ^ s_addend) ^ 0x8000) & 0x8000:
                # Augend and addend signs are the same - overflow if their sign
                # differs from the sign of the result
                self.set_flag('P', (value ^ augend_v) & 0x8000)
            else:
                # Augend and addend signs are different - no overflow
                self.set_flag('P', 0)

        self.set_flag('5', value & 0x2000)
        self.set_flag('3', value & 0x0800)

        return f'{op} {augend},{reg}', self.pc + len(data), timing

    def anda(self, timing, data, reg=None):
        operand, value = self.get_operand_value(data, reg)
        self.registers['A'] &= value
        a = self.registers['A']
        self.set_flag('S', a & 0x80)
        self.set_flag('Z', a == 0)
        self.set_flag('5', a & 0x20)
        self.set_flag('H', 1)
        self.set_flag('3', a & 0x08)
        self.set_flag('P', PARITY[a])
        self.set_flag('N', 0)
        self.set_flag('C', 0)
        return f'AND {operand}', self.pc + len(data), timing

    def bit(self, timing, data, bit, reg):
        operand, value = self.get_operand_value(data, reg)
        bitval = (value >> bit) & 1
        self.set_flag('S', bit == 7 and bitval)
        self.set_flag('Z', bitval == 0)
        if reg:
            self.set_flag('5', value & 0x20)
            self.set_flag('3', value & 0x08)
        else:
            if data[0] == 0xDD:
                v = (self.registers['IXl'] + 256 * self.registers['IXh'] + data[2]) & 0xFFFF
            else:
                v = (self.registers['IYl'] + 256 * self.registers['IYh'] + data[2]) & 0xFFFF
            self.set_flag('5', v & 0x2000)
            self.set_flag('3', v & 0x0800)
        self.set_flag('H', 1)
        self.set_flag('P', bitval == 0)
        self.set_flag('N', 0)
        return f'BIT {bit},{operand}', self.pc + len(data), timing

    def block(self, timing, data, op, inc, repeat):
        hl = self.registers['L'] + 256 * self.registers['H']
        bc = self.registers['C'] + 256 * self.registers['B']
        b = self.registers['B']
        a = self.registers['A']
        tstates = timing
        addr = self.pc + 2
        bc_inc = -1

        if op.startswith('CP'):
            value = self.peek(hl)
            result = (a - value) & 0xFF
            self.set_flag('S', result & 0x80)
            self.set_flag('Z', result == 0)
            h = (((a & 0x0F) - (value & 0x0F)) & 0x10) >> 4
            n = a - value - h
            self.set_flag('5', n & 0x02)
            self.set_flag('H', h)
            self.set_flag('3', n & 0x08)
            self.set_flag('P', bc != 1)
            self.set_flag('N', 1)
            if repeat and a != value and bc > 1:
                addr = self.pc
        elif op.startswith('IN'):
            value = self._in(bc)
            self.poke(hl, value)
            bc_inc = -256
            if repeat and b != 1:
                addr = self.pc
            b1 = (b - 1) & 0xFF
            c1 = (self.registers['C'] + inc) & 0xFF
            j = value + c1
            self.set_flag('S', b1 & 0x80)
            self.set_flag('Z', b1 == 0)
            self.set_flag('5', b1 & 0x20)
            self.set_flag('H', j > 255)
            self.set_flag('3', b1 & 0x08)
            self.set_flag('P', PARITY[(j & 7) ^ b1])
            self.set_flag('N', value & 0x80)
            self.set_flag('C', j > 255)
        elif op.startswith('LD'):
            de = self.registers['E'] + 256 * self.registers['D']
            at_hl = self.peek(hl)
            self.poke(de, at_hl)
            de = (de + inc) & 0xFFFF
            self.registers['E'], self.registers['D'] = de % 256, de // 256
            if repeat and bc != 1:
                addr = self.pc
            n = (self.registers['A'] + at_hl) & 0xFF
            self.set_flag('5', n & 0x02)
            self.set_flag('H', 0)
            self.set_flag('3', n & 0x08)
            self.set_flag('P', bc != 1)
            self.set_flag('N', 0)
        elif op.startswith('O'):
            bc_inc = -256
            if repeat and b != 1:
                addr = self.pc
            outval = self.peek(hl)
            self._out((bc - 256) & 0xFFFF, outval)
            b1 = (b - 1) & 0xFF
            k = ((hl + inc) & 0xFF) + outval
            self.set_flag('S', b1 & 0x80)
            self.set_flag('Z', b1 == 0)
            self.set_flag('5', b1 & 0x20)
            self.set_flag('H', k > 255)
            self.set_flag('3', b1 & 0x08)
            self.set_flag('P', PARITY[(k & 7) ^ b1])
            self.set_flag('N', outval & 0x80)
            self.set_flag('C', k > 255)

        if repeat:
            if addr == self.pc:
                tstates = timing[0]
            else:
                tstates = timing[1]

        hl = (hl + inc) & 0xFFFF
        bc = (bc + bc_inc) & 0xFFFF
        self.registers['L'], self.registers['H'] = hl % 256, hl // 256
        self.registers['C'], self.registers['B'] = bc % 256, bc // 256

        return op, addr, tstates

    def call(self, timing, data, condition=None):
        addr = data[1] + 256 * data[2]
        ret_addr = (self.pc + 3) & 0xFFFF
        if condition:
            if self.get_condition(condition):
                pc = addr
                self._push(ret_addr % 256, ret_addr // 256)
                tstates = timing[0]
            else:
                pc = self.pc + 3
                tstates = timing[1]
            return f'CALL {condition},${addr:04X}', pc, tstates
        self._push(ret_addr % 256, ret_addr // 256)
        return f'CALL ${addr:04X}', addr, timing

    def cf(self, timing, data):
        if data[0] == 63:
            operation = 'CCF'
            old_c = self.get_flag('C')
            self.set_flag('H', old_c)
            self.set_flag('N', 0)
            self.set_flag('C', 1 - old_c)
        else:
            operation = 'SCF'
            self.set_flag('H', 0)
            self.set_flag('N', 0)
            self.set_flag('C', 1)
        a = self.registers['A']
        self.set_flag('5', a & 0x20)
        self.set_flag('3', a & 0x08)
        return operation, self.pc + 1, timing

    def cp(self, timing, data, reg=None):
        operand, value = self.get_operand_value(data, reg)
        a = self.registers['A']
        result = (a - value) & 0xFF
        self.set_flag('S', result & 0x80)
        self.set_flag('Z', result == 0)
        self.set_flag('5', value & 0x20)
        self.set_flag('H', ((a & 0x0F) - (value & 0x0F)) & 0x10)
        self.set_flag('3', value & 0x08)
        if ((a ^ ~value) ^ 0x80) & 0x80:
            # Operand signs are the same - overflow if their sign differs from
            # the sign of the result
            self.set_flag('P', (result ^ a) & 0x80)
        else:
            # Operand signs are different - no overflow
            self.set_flag('P', 0)
        self.set_flag('N', 1)
        self.set_flag('C', a < value)
        return f'CP {operand}', self.pc + len(data), timing

    def cpl(self, timing, data):
        a = self.registers['A'] ^ 255
        self.registers['A'] = a
        self.set_flag('H', 1)
        self.set_flag('5', a & 0x20)
        self.set_flag('3', a & 0x08)
        self.set_flag('N', 1)
        return 'CPL', self.pc + 1, timing

    def daa(self, timing, data):
        a = self.registers['A']
        h_flag = self.get_flag('H')
        n_flag = self.get_flag('N')
        t = 0

        if h_flag or (a & 15) > 0x09:
            t += 1
        if self.get_flag('C') or a > 0x99:
            t += 2
            self.set_flag('C', 1)

        if n_flag and not h_flag:
            self.set_flag('H', 0)
        elif n_flag and h_flag:
            self.set_flag('H', (a & 0x0F) < 6)
        else:
            self.set_flag('H', (a & 0x0F) >= 0x0A)

        if t == 1:
            if n_flag:
                a += 0xFA
            else:
                a += 0x06
        elif t == 2:
            if n_flag:
                a += 0xA0
            else:
                a += 0x60
        elif t == 3:
            if n_flag:
                a += 0x9A
            else:
                a += 0x66

        a &= 0xFF
        self.registers['A'] = a
        self.set_flag('S', a & 0x80)
        self.set_flag('Z', a == 0)
        self.set_flag('5', a & 0x20)
        self.set_flag('3', a & 0x08)
        self.set_flag('P', PARITY[a])

        return 'DAA', self.pc + 1, timing

    def defb(self, timing, data):
        values = ','.join(f'${b:02X}' for b in data)
        return f'DEFB {values}', self.pc + len(data), timing

    def di_ei(self, timing, data, op, iff2):
        self.iff2 = iff2
        return op, self.pc + 1, timing

    def djnz(self, timing, data):
        self.registers['B'] = (self.registers['B'] - 1) & 255
        offset = data[1]
        if offset & 128:
            offset -= 256
        addr = self.pc + 2 + offset
        if self.registers['B']:
            pc = addr
            tstates = timing[0]
        else:
            pc = self.pc + 2
            tstates = timing[1]
        return f'DJNZ ${addr:04X}', pc, tstates

    def ex_af(self, timing, data):
        for r in 'AF':
            self.registers[r], self.registers['^' + r] = self.registers['^' + r], self.registers[r]
        return "EX AF,AF'", self.pc + 1, timing

    def ex_de_hl(self, timing, data):
        for r1, r2 in (('D', 'H'), ('E', 'L')):
            self.registers[r1], self.registers[r2] = self.registers[r2], self.registers[r1]
        return 'EX DE,HL', self.pc + 1, timing

    def ex_sp(self, timing, data):
        sp = self.registers['SP']
        sp1, sp2 = self.peek(sp, 2)
        if data[0] == 0xDD:
            reg = 'IX'
            r1, r2 = 'IXl', 'IXh'
        elif data[0] == 0xFD:
            reg = 'IY'
            r1, r2 = 'IYl', 'IYh'
        else:
            reg = 'HL'
            r1, r2 = 'L', 'H'
        self.poke(sp, self.registers[r1], self.registers[r2])
        self.registers[r1] = sp1
        self.registers[r2] = sp2
        return f'EX (SP),{reg}', self.pc + len(data), timing

    def exx(self, timing, data):
        for r in 'BCDEHL':
            self.registers[r], self.registers['^' + r] = self.registers['^' + r], self.registers[r]
        return 'EXX', self.pc + 1, timing

    def halt(self, timing, data):
        pc = self.pc
        if self.iff2:
            t1 = self.tstates % FRAME_DURATION
            t2 = (self.tstates + timing) % FRAME_DURATION
            if t2 < t1:
                pc += 1
        return 'HALT', pc, timing

    def im(self, timing, data, mode):
        return f'IM {mode}', self.pc + 2, timing

    def _in(self, port):
        if hasattr(self.tracer, 'read_port'):
            return self.tracer.read_port(self, port)
        return 191

    def in_a(self, timing, data):
        port = data[1] + 256 * self.registers['A']
        self.registers['A'] = self._in(port)
        return f'IN A,(${data[1]:02X})', self.pc + 2, timing

    def in_c(self, timing, data, reg):
        value = self._in(self.registers['C'] + 256 * self.registers['B'])
        if reg != 'F':
            self.registers[reg] = value
        self.set_flag('S', value & 0x80)
        self.set_flag('Z', value == 0)
        self.set_flag('5', value & 0x20)
        self.set_flag('H', 0)
        self.set_flag('3', value & 0x08)
        self.set_flag('P', PARITY[value])
        self.set_flag('N', 0)
        return f'IN {reg},(C)', self.pc + 2, timing

    def inc_dec8(self, timing, data, op, reg):
        operand, o_value = self.get_operand_value(data, reg)
        if op == 'DEC':
            value = (o_value - 1) & 255
        else:
            value = (o_value + 1) & 255
        self.set_operand_value(data, reg, value)

        self.set_flag('S', value & 0x80)
        self.set_flag('Z', value == 0)
        self.set_flag('5', value & 0x20)
        if op == 'DEC':
            self.set_flag('H', o_value & 0x0F == 0x00)
            self.set_flag('P', value == 0x7F)
            self.set_flag('N', 1)
        else:
            self.set_flag('H', o_value & 0x0F == 0x0F)
            self.set_flag('P', value == 0x80)
            self.set_flag('N', 0)
        self.set_flag('3', value & 0x08)

        return f'{op} {operand}', self.pc + len(data), timing

    def inc_dec16(self, timing, data, op, reg):
        if op == 'DEC':
            inc = -1
        else:
            inc = 1
        if reg == 'SP':
            self.registers[reg] = (self.registers[reg] + inc) & 0xFFFF
        elif reg == 'IX':
            if data[0] == 0xFD:
                reg = 'IY'
            value = (self.registers[reg + 'l'] + 256 * self.registers[reg + 'h'] + inc) & 0xFFFF
            self.registers[reg + 'h'] = value // 256
            self.registers[reg + 'l'] = value % 256
        else:
            value = (self.registers[reg[1]] + 256 * self.registers[reg[0]] + inc) & 0xFFFF
            self.registers[reg[0]] = value // 256
            self.registers[reg[1]] = value % 256
        return f'{op} {reg}', self.pc + len(data), timing

    def jr(self, timing, data, condition):
        offset = data[1]
        if offset & 128:
            offset -= 256
        addr = self.pc + 2 + offset
        if condition:
            if self.get_condition(condition):
                pc = addr
                tstates = timing[0]
            else:
                pc = self.pc + 2
                tstates = timing[1]
            return f'JR {condition},${addr:04X}', pc, tstates
        return f'JR ${addr:04X}', addr, timing

    def jp(self, timing, data, condition=None):
        if data[0] == 0xDD:
            addr = self.registers['IXl'] + 256 * self.registers['IXh']
            return 'JP (IX)', addr, timing
        if data[0] == 0xFD:
            addr = self.registers['IYl'] + 256 * self.registers['IYh']
            return 'JP (IY)', addr, timing
        if data[0] == 0xE9:
            addr = self.registers['L'] + 256 * self.registers['H']
            return 'JP (HL)', addr, timing

        addr = data[1] + 256 * data[2]
        if condition:
            if self.get_condition(condition):
                pc = addr
            else:
                pc = self.pc + 3
            return f'JP {condition},${addr:04X}', pc, timing
        return f'JP ${addr:04X}', addr, timing

    def ld8(self, timing, data, reg, reg2=None):
        op1, v1 = self.get_operand_value(data, reg)
        op2, v2 = self.get_operand_value(data, reg2)
        self.set_operand_value(data, reg, v2)
        if reg2 and reg2 in 'IR':
            a = self.registers['A']
            self.set_flag('S', a & 0x80)
            self.set_flag('Z', a == 0)
            self.set_flag('5', a & 0x20)
            self.set_flag('H', 0)
            self.set_flag('3', a & 0x08)
            self.set_flag('P', self.iff2)
            self.set_flag('N', 0)
        return f'LD {op1},{op2}', self.pc + len(data), timing

    def ld16(self, timing, data, reg):
        value = data[-2] + 256 * data[-1]
        if reg == 'SP':
            self.registers['SP'] = value
        elif reg == 'IX':
            if data[0] == 0xDD:
                reg1, reg2 = 'IXl', 'IXh'
            else:
                reg = 'IY'
                reg1, reg2 = 'IYl', 'IYh'
            self.registers[reg1] = data[2]
            self.registers[reg2] = data[3]
        else:
            self.registers[reg[1]] = data[1]
            self.registers[reg[0]] = data[2]
        return f'LD {reg},${value:04X}', self.pc + len(data), timing

    def ld16addr(self, timing, data, reg, poke):
        addr = data[-2] + 256 * data[-1]
        if poke:
            if reg == 'SP':
                self.poke(addr, self.registers['SP'] % 256, self.registers['SP'] // 256)
            elif reg == 'IX':
                if data[0] == 0xFD:
                    reg = 'IY'
                self.poke(addr, self.registers[reg + 'l'], self.registers[reg + 'h'])
            else:
                self.poke(addr, self.registers[reg[1]], self.registers[reg[0]])
            op = f'LD (${addr:04X}),{reg}'
        else:
            if reg == 'SP':
                sp1, sp2 = self.peek(addr, 2)
                self.registers['SP'] = sp1 + 256 * sp2
            elif reg == 'IX':
                if data[0] == 0xFD:
                    reg = 'IY'
                self.registers[reg + 'l'], self.registers[reg + 'h'] = self.peek(addr, 2)
            else:
                self.registers[reg[1]], self.registers[reg[0]] = self.peek(addr, 2)
            op = f'LD {reg},(${addr:04X})'
        return op, self.pc + len(data), timing

    def ldann(self, timing, data):
        addr = data[1] + 256 * data[2]
        if data[0] == 0x3A:
            op = f'LD A,(${addr:04X})'
            self.registers['A'] = self.peek(addr)
        else:
            op = f'LD (${addr:04X}),A'
            self.poke(addr, self.registers['A'])
        return op, self.pc + 3, timing

    def ldsprr(self, timing, data, reg):
        if reg == 'HL':
            self.registers['SP'] = self.registers['L'] + 256 * self.registers['H']
        else:
            if data[0] == 0xFD:
                reg = 'IY'
            self.registers['SP'] = self.registers[reg + 'l'] + 256 * self.registers[reg + 'h']
        return f'LD SP,{reg}', self.pc + len(data), timing

    def neg(self, timing, data):
        old_a = self.registers['A']
        a = self.registers['A'] = (256 - old_a) & 255
        self.set_flag('S', a & 0x80)
        self.set_flag('Z', a == 0)
        self.set_flag('5', a & 0x20)
        self.set_flag('H', old_a & 0x0F)
        self.set_flag('3', a & 0x08)
        self.set_flag('P', a == 0x80)
        self.set_flag('N', 1)
        self.set_flag('C', a > 0)
        return 'NEG', self.pc + 2, timing

    def nop(self, timing, data):
        return 'NOP', self.pc + 1, timing

    def ora(self, timing, data, reg=None):
        operand, value = self.get_operand_value(data, reg)
        self.registers['A'] |= value
        a = self.registers['A']
        self.set_flag('S', a & 0x80)
        self.set_flag('Z', a == 0)
        self.set_flag('5', a & 0x20)
        self.set_flag('H', 0)
        self.set_flag('3', a & 0x08)
        self.set_flag('P', PARITY[a])
        self.set_flag('N', 0)
        self.set_flag('C', 0)
        return f'OR {operand}', self.pc + len(data), timing

    def _out(self, port, value):
        if hasattr(self.tracer, 'write_port'):
            self.tracer.write_port(self, port, value)

    def outa(self, timing, data):
        a = self.registers['A']
        port = data[1] + 256 * a
        self._out(port, a)
        return f'OUT (${data[1]:02X}),A', self.pc + 2, timing

    def outc(self, timing, data, reg):
        port = self.registers['C'] + 256 * self.registers['B']
        if reg:
            value = self.registers[reg]
        else:
            reg = value = 0
        self._out(port, value)
        return f'OUT (C),{reg}', self.pc + 2, timing

    def _pop(self):
        sp = self.registers['SP']
        lsb, msb = self.peek(sp, 2)
        self.registers['SP'] = (sp + 2) & 0xFFFF
        self.ppcount -= 1
        return lsb, msb

    def pop(self, timing, data, reg):
        if reg == 'IX':
            if data[0] == 0xFD:
                reg = 'IY'
            self.registers[reg + 'l'], self.registers[reg + 'h'] = self._pop()
        else:
            self.registers[reg[1]], self.registers[reg[0]] = self._pop()
        return f'POP {reg}', self.pc + len(data), timing

    def _push(self, lsb, msb):
        sp = (self.registers['SP'] - 2) & 0xFFFF
        self.poke(sp, lsb, msb)
        self.ppcount += 1
        self.registers['SP'] = sp

    def push(self, timing, data, reg):
        if reg == 'IX':
            if data[0] == 0xFD:
                reg = 'IY'
            self._push(self.registers[reg + 'l'], self.registers[reg + 'h'])
        else:
            self._push(self.registers[reg[1]], self.registers[reg[0]])
        return f'PUSH {reg}', self.pc + len(data), timing

    def ret(self, timing, data, condition=None):
        if condition:
            if self.get_condition(condition):
                lsb, msb = self._pop()
                pc = lsb + 256 * msb
                tstates = timing[0]
            else:
                pc = self.pc + 1
                tstates = timing[1]
            return f'RET {condition}', pc, tstates
        lsb, msb = self._pop()
        return 'RET', lsb + 256 * msb, timing

    def reti(self, timing, data, op):
        lsb, msb = self._pop()
        return op, lsb + 256 * msb, timing

    def res_set(self, timing, data, bit, reg, bitval, dest=''):
        operand, value = self.get_operand_value(data, reg)
        mask = 1 << bit
        if bitval:
            value |= mask
            op = f'SET {bit},{operand}'
        else:
            value &= mask ^ 255
            op = f'RES {bit},{operand}'
        self.set_operand_value(data, reg, value)
        if dest:
            self.registers[dest] = value
            op += f',{dest}'
        return op, self.pc + len(data), timing

    def rld(self, timing, data):
        hl = self.registers['L'] + 256 * self.registers['H']
        a = self.registers['A']
        at_hl = self.peek(hl)
        self.poke(hl, ((at_hl << 4) & 240) + (a & 15))
        a_out = self.registers['A'] = (a & 240) + ((at_hl >> 4) & 15)
        self.set_flag('S', a_out & 0x80)
        self.set_flag('Z', a_out == 0)
        self.set_flag('5', a_out & 0x20)
        self.set_flag('H', 0)
        self.set_flag('3', a_out & 0x08)
        self.set_flag('P', PARITY[a_out])
        self.set_flag('N', 0)
        return 'RLD', self.pc + 2, timing

    def rrd(self, timing, data):
        hl = self.registers['L'] + 256 * self.registers['H']
        a = self.registers['A']
        at_hl = self.peek(hl)
        self.poke(hl, ((a << 4) & 240) + (at_hl >> 4))
        a_out = self.registers['A'] = (a & 240) + (at_hl & 15)
        self.set_flag('S', a_out & 0x80)
        self.set_flag('Z', a_out == 0)
        self.set_flag('5', a_out & 0x20)
        self.set_flag('H', 0)
        self.set_flag('3', a_out & 0x08)
        self.set_flag('P', PARITY[a_out])
        self.set_flag('N', 0)
        return 'RRD', self.pc + 2, timing

    def rotate(self, timing, data, op, cbit, reg, carry='', dest=''):
        operand, value = self.get_operand_value(data, reg)
        old_carry = self.get_flag('C')
        self.set_flag('C', value & cbit)
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
        self.set_operand_value(data, reg, value)
        if dest:
            self.registers[dest] = value
            dest = ',' + dest
        if data[0] in (0x07, 0x0F, 0x17, 0x1F):
            # RLCA, RLA, RRCA, RRA
            op += 'A'
            self.set_flag('5', value & 0x20)
            self.set_flag('H', 0)
            self.set_flag('3', value & 0x08)
            self.set_flag('N', 0)
        else:
            op += f'{operand}{dest}'
            self.set_flag('S', value & 0x80)
            self.set_flag('Z', value == 0)
            self.set_flag('5', value & 0x20)
            self.set_flag('H', 0)
            self.set_flag('3', value & 0x08)
            self.set_flag('P', PARITY[value])
            self.set_flag('N', 0)
        return f'{op}', self.pc + len(data), timing

    def rst(self, timing, data, addr):
        ret_addr = (self.pc + 1) & 0xFFFF
        self._push(ret_addr % 256, ret_addr // 256)
        return f'RST ${addr:02X}', addr, timing

    def shift(self, timing, data, op, cbit, reg, dest=''):
        operand, value = self.get_operand_value(data, reg)
        ovalue = value
        self.set_flag('C', value & cbit)
        if cbit == 1:
            value >>= 1
        else:
            value <<= 1
        if op == 'SRA':
            value += ovalue & 128
        elif op == 'SLL':
            value |= 1
        value &= 255
        self.set_operand_value(data, reg, value)
        if dest:
            self.registers[dest] = value
            dest = ',' + dest
        self.set_flag('S', value & 0x80)
        self.set_flag('Z', value == 0)
        self.set_flag('5', value & 0x20)
        self.set_flag('H', 0)
        self.set_flag('3', value & 0x08)
        self.set_flag('P', PARITY[value])
        self.set_flag('N', 0)
        return f'{op} {operand}{dest}', self.pc + len(data), timing

    def xor(self, timing, data, reg=None):
        operand, value = self.get_operand_value(data, reg)
        self.registers['A'] ^= value
        a = self.registers['A']
        self.set_flag('S', a & 0x80)
        self.set_flag('Z', a == 0)
        self.set_flag('5', a & 0x20)
        self.set_flag('H', 0)
        self.set_flag('3', a & 0x08)
        self.set_flag('P', PARITY[a])
        self.set_flag('N', 0)
        self.set_flag('C', 0)
        return f'XOR {operand}', self.pc + len(data), timing

    opcodes = {
        0x00: (4, nop, 1, ()),                                # NOP
        0x01: (10, ld16, 3, ('BC',)),                         # LD BC,nn
        0x02: (7, ld8, 1, ('(BC)', 'A')),                     # LD (BC),A
        0x03: (6, inc_dec16, 1, ('INC', 'BC')),               # INC BC
        0x04: (4, inc_dec8, 1, ('INC', 'B')),                 # INC B
        0x05: (4, inc_dec8, 1, ('DEC', 'B')),                 # DEC B
        0x06: (7, ld8, 2, ('B',)),                            # LD B,n
        0x07: (4, rotate, 1, ('RLC', 128, 'A', 'C')),         # RLCA
        0x08: (4, ex_af, 1, ()),                              # EX AF,AF'
        0x09: (11, add16, 1, ('BC',)),                        # ADD HL,BC
        0x0A: (7, ld8, 1, ('A', '(BC)')),                     # LD A,(BC)
        0x0B: (6, inc_dec16, 1, ('DEC', 'BC')),               # DEC BC
        0x0C: (4, inc_dec8, 1, ('INC', 'C')),                 # INC C
        0x0D: (4, inc_dec8, 1, ('DEC', 'C')),                 # DEC C
        0x0E: (7, ld8, 2, ('C',)),                            # LD C,n
        0x0F: (4, rotate, 1, ('RRC', 1, 'A', 'C')),           # RRCA
        0x10: ((13, 8), djnz, 2, ()),                         # DJNZ nn
        0x11: (10, ld16, 3, ('DE',)),                         # LD DE,nn
        0x12: (7, ld8, 1, ('(DE)', 'A')),                     # LD (DE),A
        0x13: (6, inc_dec16, 1, ('INC', 'DE')),               # INC DE
        0x14: (4, inc_dec8, 1, ('INC', 'D')),                 # INC D
        0x15: (4, inc_dec8, 1, ('DEC', 'D')),                 # DEC D
        0x16: (7, ld8, 2, ('D',)),                            # LD D,n
        0x17: (4, rotate, 1, ('RL', 128, 'A')),               # RLA
        0x18: (12, jr, 2, ('',)),                             # JR nn
        0x19: (11, add16, 1, ('DE',)),                        # ADD HL,DE
        0x1A: (7, ld8, 1, ('A', '(DE)')),                     # LD A,(DE)
        0x1B: (6, inc_dec16, 1, ('DEC', 'DE')),               # DEC DE
        0x1C: (4, inc_dec8, 1, ('INC', 'E')),                 # INC E
        0x1D: (4, inc_dec8, 1, ('DEC', 'E')),                 # DEC E
        0x1E: (7, ld8, 2, ('E',)),                            # LD E,n
        0x1F: (4, rotate, 1, ('RR', 1, 'A')),                 # RRA
        0x20: ((12, 7), jr, 2, ('NZ',)),                      # JR NZ,nn
        0x21: (10, ld16, 3, ('HL',)),                         # LD HL,nn
        0x22: (16, ld16addr, 3, ('HL', 1)),                   # LD (nn),HL
        0x23: (6, inc_dec16, 1, ('INC', 'HL')),               # INC HL
        0x24: (4, inc_dec8, 1, ('INC', 'H')),                 # INC H
        0x25: (4, inc_dec8, 1, ('DEC', 'H')),                 # DEC H
        0x26: (7, ld8, 2, ('H',)),                            # LD H,n
        0x27: (4, daa, 1, ()),                                # DAA
        0x28: ((12, 7), jr, 2, ('Z',)),                       # JR Z,nn
        0x29: (11, add16, 1, ('HL',)),                        # ADD HL,HL
        0x2A: (16, ld16addr, 3, ('HL', 0)),                   # LD HL,(nn)
        0x2B: (6, inc_dec16, 1, ('DEC', 'HL')),               # DEC HL
        0x2C: (4, inc_dec8, 1, ('INC', 'L')),                 # INC L
        0x2D: (4, inc_dec8, 1, ('DEC', 'L')),                 # DEC L
        0x2E: (7, ld8, 2, ('L',)),                            # LD L,n
        0x2F: (4, cpl, 1, ()),                                # CPL
        0x30: ((12, 7), jr, 2, ('NC',)),                      # JR NC,nn
        0x31: (10, ld16, 3, ('SP',)),                         # LD SP,nn
        0x32: (13, ldann, 3, ()),                             # LD (nn),A
        0x33: (6, inc_dec16, 1, ('INC', 'SP')),               # INC SP
        0x34: (11, inc_dec8, 1, ('INC', '(HL)')),             # INC (HL)
        0x35: (11, inc_dec8, 1, ('DEC', '(HL)')),             # DEC (HL)
        0x36: (10, ld8, 2, ('(HL)',)),                        # LD (HL),n
        0x37: (4, cf, 1, ()),                                 # SCF
        0x38: ((12, 7), jr, 2, ('C',)),                       # JR C,nn
        0x39: (11, add16, 1, ('SP',)),                        # ADD HL,SP
        0x3A: (13, ldann, 3, ()),                             # LD A,(nn)
        0x3B: (6, inc_dec16, 1, ('DEC', 'SP')),               # DEC SP
        0x3C: (4, inc_dec8, 1, ('INC', 'A')),                 # INC A
        0x3D: (4, inc_dec8, 1, ('DEC', 'A')),                 # DEC A
        0x3E: (7, ld8, 2, ('A',)),                            # LD A,n
        0x3F: (4, cf, 1, ()),                                 # CCF
        0x40: (4, ld8, 1, ('B', 'B')),                        # LD B,B
        0x41: (4, ld8, 1, ('B', 'C')),                        # LD B,C
        0x42: (4, ld8, 1, ('B', 'D')),                        # LD B,D
        0x43: (4, ld8, 1, ('B', 'E')),                        # LD B,E
        0x44: (4, ld8, 1, ('B', 'H')),                        # LD B,H
        0x45: (4, ld8, 1, ('B', 'L')),                        # LD B,L
        0x46: (7, ld8, 1, ('B', '(HL)')),                     # LD B,(HL)
        0x47: (4, ld8, 1, ('B', 'A')),                        # LD B,A
        0x48: (4, ld8, 1, ('C', 'B')),                        # LD C,B
        0x49: (4, ld8, 1, ('C', 'C')),                        # LD C,C
        0x4A: (4, ld8, 1, ('C', 'D')),                        # LD C,D
        0x4B: (4, ld8, 1, ('C', 'E')),                        # LD C,E
        0x4C: (4, ld8, 1, ('C', 'H')),                        # LD C,H
        0x4D: (4, ld8, 1, ('C', 'L')),                        # LD C,L
        0x4E: (7, ld8, 1, ('C', '(HL)')),                     # LD C,(HL)
        0x4F: (4, ld8, 1, ('C', 'A')),                        # LD C,A
        0x50: (4, ld8, 1, ('D', 'B')),                        # LD D,B
        0x51: (4, ld8, 1, ('D', 'C')),                        # LD D,C
        0x52: (4, ld8, 1, ('D', 'D')),                        # LD D,D
        0x53: (4, ld8, 1, ('D', 'E')),                        # LD D,E
        0x54: (4, ld8, 1, ('D', 'H')),                        # LD D,H
        0x55: (4, ld8, 1, ('D', 'L')),                        # LD D,L
        0x56: (7, ld8, 1, ('D', '(HL)')),                     # LD D,(HL)
        0x57: (4, ld8, 1, ('D', 'A')),                        # LD D,A
        0x58: (4, ld8, 1, ('E', 'B')),                        # LD E,B
        0x59: (4, ld8, 1, ('E', 'C')),                        # LD E,C
        0x5A: (4, ld8, 1, ('E', 'D')),                        # LD E,D
        0x5B: (4, ld8, 1, ('E', 'E')),                        # LD E,E
        0x5C: (4, ld8, 1, ('E', 'H')),                        # LD E,H
        0x5D: (4, ld8, 1, ('E', 'L')),                        # LD E,L
        0x5E: (7, ld8, 1, ('E', '(HL)')),                     # LD E,(HL)
        0x5F: (4, ld8, 1, ('E', 'A')),                        # LD E,A
        0x60: (4, ld8, 1, ('H', 'B')),                        # LD H,B
        0x61: (4, ld8, 1, ('H', 'C')),                        # LD H,C
        0x62: (4, ld8, 1, ('H', 'D')),                        # LD H,D
        0x63: (4, ld8, 1, ('H', 'E')),                        # LD H,E
        0x64: (4, ld8, 1, ('H', 'H')),                        # LD H,H
        0x65: (4, ld8, 1, ('H', 'L')),                        # LD H,L
        0x66: (7, ld8, 1, ('H', '(HL)')),                     # LD H,(HL)
        0x67: (4, ld8, 1, ('H', 'A')),                        # LD H,A
        0x68: (4, ld8, 1, ('L', 'B')),                        # LD L,B
        0x69: (4, ld8, 1, ('L', 'C')),                        # LD L,C
        0x6A: (4, ld8, 1, ('L', 'D')),                        # LD L,D
        0x6B: (4, ld8, 1, ('L', 'E')),                        # LD L,E
        0x6C: (4, ld8, 1, ('L', 'H')),                        # LD L,H
        0x6D: (4, ld8, 1, ('L', 'L')),                        # LD L,L
        0x6E: (7, ld8, 1, ('L', '(HL)')),                     # LD L,(HL)
        0x6F: (4, ld8, 1, ('L', 'A')),                        # LD L,A
        0x70: (7, ld8, 1, ('(HL)', 'B')),                     # LD (HL),B
        0x71: (7, ld8, 1, ('(HL)', 'C')),                     # LD (HL),C
        0x72: (7, ld8, 1, ('(HL)', 'D')),                     # LD (HL),D
        0x73: (7, ld8, 1, ('(HL)', 'E')),                     # LD (HL),E
        0x74: (7, ld8, 1, ('(HL)', 'H')),                     # LD (HL),H
        0x75: (7, ld8, 1, ('(HL)', 'L')),                     # LD (HL),L
        0x76: (4, halt, 1, ()),                               # HALT
        0x77: (7, ld8, 1, ('(HL)', 'A')),                     # LD (HL),A
        0x78: (4, ld8, 1, ('A', 'B')),                        # LD A,B
        0x79: (4, ld8, 1, ('A', 'C')),                        # LD A,C
        0x7A: (4, ld8, 1, ('A', 'D')),                        # LD A,D
        0x7B: (4, ld8, 1, ('A', 'E')),                        # LD A,E
        0x7C: (4, ld8, 1, ('A', 'H')),                        # LD A,H
        0x7D: (4, ld8, 1, ('A', 'L')),                        # LD A,L
        0x7E: (7, ld8, 1, ('A', '(HL)')),                     # LD A,(HL)
        0x7F: (4, ld8, 1, ('A', 'A')),                        # LD A,A
        0x80: (4, add_a, 1, ('B',)),                          # ADD A,B
        0x81: (4, add_a, 1, ('C',)),                          # ADD A,C
        0x82: (4, add_a, 1, ('D',)),                          # ADD A,D
        0x83: (4, add_a, 1, ('E',)),                          # ADD A,E
        0x84: (4, add_a, 1, ('H',)),                          # ADD A,H
        0x85: (4, add_a, 1, ('L',)),                          # ADD A,L
        0x86: (7, add_a, 1, ('(HL)',)),                       # ADD A,(HL)
        0x87: (4, add_a, 1, ('A',)),                          # ADD A,A
        0x88: (4, add_a, 1, ('B', 1)),                        # ADC A,B
        0x89: (4, add_a, 1, ('C', 1)),                        # ADC A,C
        0x8A: (4, add_a, 1, ('D', 1)),                        # ADC A,D
        0x8B: (4, add_a, 1, ('E', 1)),                        # ADC A,E
        0x8C: (4, add_a, 1, ('H', 1)),                        # ADC A,H
        0x8D: (4, add_a, 1, ('L', 1)),                        # ADC A,L
        0x8E: (7, add_a, 1, ('(HL)', 1)),                     # ADC A,(HL)
        0x8F: (4, add_a, 1, ('A', 1)),                        # ADC A,A
        0x90: (4, add_a, 1, ('B', 0, -1)),                    # SUB B
        0x91: (4, add_a, 1, ('C', 0, -1)),                    # SUB C
        0x92: (4, add_a, 1, ('D', 0, -1)),                    # SUB D
        0x93: (4, add_a, 1, ('E', 0, -1)),                    # SUB E
        0x94: (4, add_a, 1, ('H', 0, -1)),                    # SUB H
        0x95: (4, add_a, 1, ('L', 0, -1)),                    # SUB L
        0x96: (7, add_a, 1, ('(HL)', 0, -1)),                 # SUB (HL)
        0x97: (4, add_a, 1, ('A', 0, -1)),                    # SUB A
        0x98: (4, add_a, 1, ('B', 1, -1)),                    # SBC A,B
        0x99: (4, add_a, 1, ('C', 1, -1)),                    # SBC A,C
        0x9A: (4, add_a, 1, ('D', 1, -1)),                    # SBC A,D
        0x9B: (4, add_a, 1, ('E', 1, -1)),                    # SBC A,E
        0x9C: (4, add_a, 1, ('H', 1, -1)),                    # SBC A,H
        0x9D: (4, add_a, 1, ('L', 1, -1)),                    # SBC A,L
        0x9E: (7, add_a, 1, ('(HL)', 1, -1)),                 # SBC A,(HL)
        0x9F: (4, add_a, 1, ('A', 1, -1)),                    # SBC A,A
        0xA0: (4, anda, 1, ('B',)),                           # AND B
        0xA1: (4, anda, 1, ('C',)),                           # AND C
        0xA2: (4, anda, 1, ('D',)),                           # AND D
        0xA3: (4, anda, 1, ('E',)),                           # AND E
        0xA4: (4, anda, 1, ('H',)),                           # AND H
        0xA5: (4, anda, 1, ('L',)),                           # AND L
        0xA6: (7, anda, 1, ('(HL)',)),                        # AND (HL)
        0xA7: (4, anda, 1, ('A',)),                           # AND A
        0xA8: (4, xor, 1, ('B',)),                            # XOR B
        0xA9: (4, xor, 1, ('C',)),                            # XOR C
        0xAA: (4, xor, 1, ('D',)),                            # XOR D
        0xAB: (4, xor, 1, ('E',)),                            # XOR E
        0xAC: (4, xor, 1, ('H',)),                            # XOR H
        0xAD: (4, xor, 1, ('L',)),                            # XOR L
        0xAE: (7, xor, 1, ('(HL)',)),                         # XOR (HL)
        0xAF: (4, xor, 1, ('A',)),                            # XOR A
        0xB0: (4, ora, 1, ('B',)),                            # OR B
        0xB1: (4, ora, 1, ('C',)),                            # OR C
        0xB2: (4, ora, 1, ('D',)),                            # OR D
        0xB3: (4, ora, 1, ('E',)),                            # OR E
        0xB4: (4, ora, 1, ('H',)),                            # OR H
        0xB5: (4, ora, 1, ('L',)),                            # OR L
        0xB6: (7, ora, 1, ('(HL)',)),                         # OR (HL)
        0xB7: (4, ora, 1, ('A',)),                            # OR A
        0xB8: (4, cp, 1, ('B',)),                             # CP B
        0xB9: (4, cp, 1, ('C',)),                             # CP C
        0xBA: (4, cp, 1, ('D',)),                             # CP D
        0xBB: (4, cp, 1, ('E',)),                             # CP E
        0xBC: (4, cp, 1, ('H',)),                             # CP H
        0xBD: (4, cp, 1, ('L',)),                             # CP L
        0xBE: (7, cp, 1, ('(HL)',)),                          # CP (HL)
        0xBF: (4, cp, 1, ('A',)),                             # CP A
        0xC0: ((11, 5), ret, 1, ('NZ',)),                     # RET NZ
        0xC1: (10, pop, 1, ('BC',)),                          # POP BC
        0xC2: (10, jp, 3, ('NZ',)),                           # JP NZ,nn
        0xC3: (10, jp, 3, ()),                                # JP nn
        0xC4: ((17, 10), call, 3, ('NZ',)),                   # CALL NZ,nn
        0xC5: (11, push, 1, ('BC',)),                         # PUSH BC
        0xC6: (7, add_a, 2, ()),                              # ADD A,n
        0xC7: (11, rst, 1, (0,)),                             # RST $00
        0xC8: ((11, 5), ret, 1, ('Z',)),                      # RET Z
        0xC9: (10, ret, 1, ()),                               # RET
        0xCA: (10, jp, 3, ('Z',)),                            # JP Z,nn
        0xCB: None,                                           # CB prefix
        0xCC: ((17, 10), call, 3, ('Z',)),                    # CALL Z,nn
        0xCD: (17, call, 3, ()),                              # CALL nn
        0xCE: (7, add_a, 2, (None, 1, 1)),                    # ADC A,n
        0xCF: (11, rst, 1, (8,)),                             # RST $08
        0xD0: ((11, 5), ret, 1, ('NC',)),                     # RET NC
        0xD1: (10, pop, 1, ('DE',)),                          # POP DE
        0xD2: (10, jp, 3, ('NC',)),                           # JP NC,nn
        0xD3: (11, outa, 2, ()),                              # OUT (n),A
        0xD4: ((17, 10), call, 3, ('NC',)),                   # CALL NC,nn
        0xD5: (11, push, 1, ('DE',)),                         # PUSH DE
        0xD6: (7, add_a, 2, (None, 0, -1)),                   # SUB n
        0xD7: (11, rst, 1, (16,)),                            # RST $10
        0xD8: ((11, 5), ret, 1, ('C',)),                      # RET C
        0xD9: (4, exx, 1, ()),                                # EXX
        0xDA: (10, jp, 3, ('C',)),                            # JP C,nn
        0xDB: (11, in_a, 2, ()),                              # IN A,(n)
        0xDC: ((17, 10), call, 3, ('C',)),                    # CALL C,nn
        0xDD: None,                                           # DD prefix
        0xDE: (7, add_a, 2, (None, 1, -1)),                   # SBC A,n
        0xDF: (11, rst, 1, (24,)),                            # RST $18
        0xE0: ((11, 5), ret, 1, ('PO',)),                     # RET PO
        0xE1: (10, pop, 1, ('HL',)),                          # POP HL
        0xE2: (10, jp, 3, ('PO',)),                           # JP PO,nn
        0xE3: (19, ex_sp, 1, ()),                             # EX (SP),HL
        0xE4: ((17, 10), call, 3, ('PO',)),                   # CALL PO,nn
        0xE5: (11, push, 1, ('HL',)),                         # PUSH HL
        0xE6: (7, anda, 2, ()),                               # AND n
        0xE7: (11, rst, 1, (32,)),                            # RST $20
        0xE8: ((11, 5), ret, 1, ('PE',)),                     # RET PE
        0xE9: (4, jp, 1, ()),                                 # JP (HL)
        0xEA: (10, jp, 3, ('PE',)),                           # JP PE,nn
        0xEB: (4, ex_de_hl, 1, ()),                           # EX DE,HL
        0xEC: ((17, 10), call, 3, ('PE',)),                   # CALL PE,nn
        0xED: None,                                           # ED prefix
        0xEE: (7, xor, 2, ()),                                # XOR n
        0xEF: (11, rst, 1, (40,)),                            # RST $28
        0xF0: ((11, 5), ret, 1, ('P',)),                      # RET P
        0xF1: (10, pop, 1, ('AF',)),                          # POP AF
        0xF2: (10, jp, 3, ('P',)),                            # JP P,nn
        0xF3: (4, di_ei, 1, ('DI', 0)),                       # DI
        0xF4: ((17, 10), call, 3, ('P',)),                    # CALL P,nn
        0xF5: (11, push, 1, ('AF',)),                         # PUSH AF
        0xF6: (7, ora, 2, ()),                                # OR n
        0xF7: (11, rst, 1, (48,)),                            # RST $30
        0xF8: ((11, 5), ret, 1, ('M',)),                      # RET M
        0xF9: (6, ldsprr, 1, ('HL',)),                        # LD SP,HL
        0xFA: (10, jp, 3, ('M',)),                            # JP M,nn
        0xFB: (4, di_ei, 1, ('EI', 1)),                       # EI
        0xFC: ((17, 10), call, 3, ('M',)),                    # CALL M,nn
        0xFD: None,                                           # FD prefix
        0xFE: (7, cp, 2, ()),                                 # CP n
        0xFF: (11, rst, 1, (56,))                             # RST $38
    }

    after_CB = {
        0x00: (8, rotate, 2, ('RLC ', 128, 'B', 'C')),        # RLC B
        0x01: (8, rotate, 2, ('RLC ', 128, 'C', 'C')),        # RLC C
        0x02: (8, rotate, 2, ('RLC ', 128, 'D', 'C')),        # RLC D
        0x03: (8, rotate, 2, ('RLC ', 128, 'E', 'C')),        # RLC E
        0x04: (8, rotate, 2, ('RLC ', 128, 'H', 'C')),        # RLC H
        0x05: (8, rotate, 2, ('RLC ', 128, 'L', 'C')),        # RLC L
        0x06: (15, rotate, 2, ('RLC ', 128, '(HL)', 'C')),    # RLC (HL)
        0x07: (8, rotate, 2, ('RLC ', 128, 'A', 'C')),        # RLC A
        0x08: (8, rotate, 2, ('RRC ', 1, 'B', 'C')),          # RRC B
        0x09: (8, rotate, 2, ('RRC ', 1, 'C', 'C')),          # RRC C
        0x0A: (8, rotate, 2, ('RRC ', 1, 'D', 'C')),          # RRC D
        0x0B: (8, rotate, 2, ('RRC ', 1, 'E', 'C')),          # RRC E
        0x0C: (8, rotate, 2, ('RRC ', 1, 'H', 'C')),          # RRC H
        0x0D: (8, rotate, 2, ('RRC ', 1, 'L', 'C')),          # RRC L
        0x0E: (15, rotate, 2, ('RRC ', 1, '(HL)', 'C')),      # RRC (HL)
        0x0F: (8, rotate, 2, ('RRC ', 1, 'A', 'C')),          # RRC A
        0x10: (8, rotate, 2, ('RL ', 128, 'B')),              # RL B
        0x11: (8, rotate, 2, ('RL ', 128, 'C')),              # RL C
        0x12: (8, rotate, 2, ('RL ', 128, 'D')),              # RL D
        0x13: (8, rotate, 2, ('RL ', 128, 'E')),              # RL E
        0x14: (8, rotate, 2, ('RL ', 128, 'H')),              # RL H
        0x15: (8, rotate, 2, ('RL ', 128, 'L')),              # RL L
        0x16: (15, rotate, 2, ('RL ', 128, '(HL)')),          # RL (HL)
        0x17: (8, rotate, 2, ('RL ', 128, 'A')),              # RL A
        0x18: (8, rotate, 2, ('RR ', 1, 'B')),                # RR B
        0x19: (8, rotate, 2, ('RR ', 1, 'C')),                # RR C
        0x1A: (8, rotate, 2, ('RR ', 1, 'D')),                # RR D
        0x1B: (8, rotate, 2, ('RR ', 1, 'E')),                # RR E
        0x1C: (8, rotate, 2, ('RR ', 1, 'H')),                # RR H
        0x1D: (8, rotate, 2, ('RR ', 1, 'L')),                # RR L
        0x1E: (15, rotate, 2, ('RR ', 1, '(HL)')),            # RR (HL)
        0x1F: (8, rotate, 2, ('RR ', 1, 'A')),                # RR A
        0x20: (8, shift, 2, ('SLA', 128, 'B')),               # SLA B
        0x21: (8, shift, 2, ('SLA', 128, 'C')),               # SLA C
        0x22: (8, shift, 2, ('SLA', 128, 'D')),               # SLA D
        0x23: (8, shift, 2, ('SLA', 128, 'E')),               # SLA E
        0x24: (8, shift, 2, ('SLA', 128, 'H')),               # SLA H
        0x25: (8, shift, 2, ('SLA', 128, 'L')),               # SLA L
        0x26: (15, shift, 2, ('SLA', 128, '(HL)')),           # SLA (HL)
        0x27: (8, shift, 2, ('SLA', 128, 'A')),               # SLA A
        0x28: (8, shift, 2, ('SRA', 1, 'B')),                 # SRA B
        0x29: (8, shift, 2, ('SRA', 1, 'C')),                 # SRA C
        0x2A: (8, shift, 2, ('SRA', 1, 'D')),                 # SRA D
        0x2B: (8, shift, 2, ('SRA', 1, 'E')),                 # SRA E
        0x2C: (8, shift, 2, ('SRA', 1, 'H')),                 # SRA H
        0x2D: (8, shift, 2, ('SRA', 1, 'L')),                 # SRA L
        0x2E: (15, shift, 2, ('SRA', 1, '(HL)')),             # SRA (HL)
        0x2F: (8, shift, 2, ('SRA', 1, 'A')),                 # SRA A
        0x30: (8, shift, 2, ('SLL', 128, 'B')),               # SLL B
        0x31: (8, shift, 2, ('SLL', 128, 'C')),               # SLL C
        0x32: (8, shift, 2, ('SLL', 128, 'D')),               # SLL D
        0x33: (8, shift, 2, ('SLL', 128, 'E')),               # SLL E
        0x34: (8, shift, 2, ('SLL', 128, 'H')),               # SLL H
        0x35: (8, shift, 2, ('SLL', 128, 'L')),               # SLL L
        0x36: (15, shift, 2, ('SLL', 128, '(HL)')),           # SLL (HL)
        0x37: (8, shift, 2, ('SLL', 128, 'A')),               # SLL A
        0x38: (8, shift, 2, ('SRL', 1, 'B')),                 # SRL B
        0x39: (8, shift, 2, ('SRL', 1, 'C')),                 # SRL C
        0x3A: (8, shift, 2, ('SRL', 1, 'D')),                 # SRL D
        0x3B: (8, shift, 2, ('SRL', 1, 'E')),                 # SRL E
        0x3C: (8, shift, 2, ('SRL', 1, 'H')),                 # SRL H
        0x3D: (8, shift, 2, ('SRL', 1, 'L')),                 # SRL L
        0x3E: (15, shift, 2, ('SRL', 1, '(HL)')),             # SRL (HL)
        0x3F: (8, shift, 2, ('SRL', 1, 'A')),                 # SRL A
        0x40: (8, bit, 2, (0, 'B')),                          # BIT 0,B
        0x41: (8, bit, 2, (0, 'C')),                          # BIT 0,C
        0x42: (8, bit, 2, (0, 'D')),                          # BIT 0,D
        0x43: (8, bit, 2, (0, 'E')),                          # BIT 0,E
        0x44: (8, bit, 2, (0, 'H')),                          # BIT 0,H
        0x45: (8, bit, 2, (0, 'L')),                          # BIT 0,L
        0x46: (12, bit, 2, (0, '(HL)')),                      # BIT 0,(HL)
        0x47: (8, bit, 2, (0, 'A')),                          # BIT 0,A
        0x48: (8, bit, 2, (1, 'B')),                          # BIT 1,B
        0x49: (8, bit, 2, (1, 'C')),                          # BIT 1,C
        0x4A: (8, bit, 2, (1, 'D')),                          # BIT 1,D
        0x4B: (8, bit, 2, (1, 'E')),                          # BIT 1,E
        0x4C: (8, bit, 2, (1, 'H')),                          # BIT 1,H
        0x4D: (8, bit, 2, (1, 'L')),                          # BIT 1,L
        0x4E: (12, bit, 2, (1, '(HL)')),                      # BIT 1,(HL)
        0x4F: (8, bit, 2, (1, 'A')),                          # BIT 1,A
        0x50: (8, bit, 2, (2, 'B')),                          # BIT 2,B
        0x51: (8, bit, 2, (2, 'C')),                          # BIT 2,C
        0x52: (8, bit, 2, (2, 'D')),                          # BIT 2,D
        0x53: (8, bit, 2, (2, 'E')),                          # BIT 2,E
        0x54: (8, bit, 2, (2, 'H')),                          # BIT 2,H
        0x55: (8, bit, 2, (2, 'L')),                          # BIT 2,L
        0x56: (12, bit, 2, (2, '(HL)')),                      # BIT 2,(HL)
        0x57: (8, bit, 2, (2, 'A')),                          # BIT 2,A
        0x58: (8, bit, 2, (3, 'B')),                          # BIT 3,B
        0x59: (8, bit, 2, (3, 'C')),                          # BIT 3,C
        0x5A: (8, bit, 2, (3, 'D')),                          # BIT 3,D
        0x5B: (8, bit, 2, (3, 'E')),                          # BIT 3,E
        0x5C: (8, bit, 2, (3, 'H')),                          # BIT 3,H
        0x5D: (8, bit, 2, (3, 'L')),                          # BIT 3,L
        0x5E: (12, bit, 2, (3, '(HL)')),                      # BIT 3,(HL)
        0x5F: (8, bit, 2, (3, 'A')),                          # BIT 3,A
        0x60: (8, bit, 2, (4, 'B')),                          # BIT 4,B
        0x61: (8, bit, 2, (4, 'C')),                          # BIT 4,C
        0x62: (8, bit, 2, (4, 'D')),                          # BIT 4,D
        0x63: (8, bit, 2, (4, 'E')),                          # BIT 4,E
        0x64: (8, bit, 2, (4, 'H')),                          # BIT 4,H
        0x65: (8, bit, 2, (4, 'L')),                          # BIT 4,L
        0x66: (12, bit, 2, (4, '(HL)')),                      # BIT 4,(HL)
        0x67: (8, bit, 2, (4, 'A')),                          # BIT 4,A
        0x68: (8, bit, 2, (5, 'B')),                          # BIT 5,B
        0x69: (8, bit, 2, (5, 'C')),                          # BIT 5,C
        0x6A: (8, bit, 2, (5, 'D')),                          # BIT 5,D
        0x6B: (8, bit, 2, (5, 'E')),                          # BIT 5,E
        0x6C: (8, bit, 2, (5, 'H')),                          # BIT 5,H
        0x6D: (8, bit, 2, (5, 'L')),                          # BIT 5,L
        0x6E: (12, bit, 2, (5, '(HL)')),                      # BIT 5,(HL)
        0x6F: (8, bit, 2, (5, 'A')),                          # BIT 5,A
        0x70: (8, bit, 2, (6, 'B')),                          # BIT 6,B
        0x71: (8, bit, 2, (6, 'C')),                          # BIT 6,C
        0x72: (8, bit, 2, (6, 'D')),                          # BIT 6,D
        0x73: (8, bit, 2, (6, 'E')),                          # BIT 6,E
        0x74: (8, bit, 2, (6, 'H')),                          # BIT 6,H
        0x75: (8, bit, 2, (6, 'L')),                          # BIT 6,L
        0x76: (12, bit, 2, (6, '(HL)')),                      # BIT 6,(HL)
        0x77: (8, bit, 2, (6, 'A')),                          # BIT 6,A
        0x78: (8, bit, 2, (7, 'B')),                          # BIT 7,B
        0x79: (8, bit, 2, (7, 'C')),                          # BIT 7,C
        0x7A: (8, bit, 2, (7, 'D')),                          # BIT 7,D
        0x7B: (8, bit, 2, (7, 'E')),                          # BIT 7,E
        0x7C: (8, bit, 2, (7, 'H')),                          # BIT 7,H
        0x7D: (8, bit, 2, (7, 'L')),                          # BIT 7,L
        0x7E: (12, bit, 2, (7, '(HL)')),                      # BIT 7,(HL)
        0x7F: (8, bit, 2, (7, 'A')),                          # BIT 7,A
        0x80: (8, res_set, 2, (0, 'B', 0)),                   # RES 0,B
        0x81: (8, res_set, 2, (0, 'C', 0)),                   # RES 0,C
        0x82: (8, res_set, 2, (0, 'D', 0)),                   # RES 0,D
        0x83: (8, res_set, 2, (0, 'E', 0)),                   # RES 0,E
        0x84: (8, res_set, 2, (0, 'H', 0)),                   # RES 0,H
        0x85: (8, res_set, 2, (0, 'L', 0)),                   # RES 0,L
        0x86: (15, res_set, 2, (0, '(HL)', 0)),               # RES 0,(HL)
        0x87: (8, res_set, 2, (0, 'A', 0)),                   # RES 0,A
        0x88: (8, res_set, 2, (1, 'B', 0)),                   # RES 1,B
        0x89: (8, res_set, 2, (1, 'C', 0)),                   # RES 1,C
        0x8A: (8, res_set, 2, (1, 'D', 0)),                   # RES 1,D
        0x8B: (8, res_set, 2, (1, 'E', 0)),                   # RES 1,E
        0x8C: (8, res_set, 2, (1, 'H', 0)),                   # RES 1,H
        0x8D: (8, res_set, 2, (1, 'L', 0)),                   # RES 1,L
        0x8E: (15, res_set, 2, (1, '(HL)', 0)),               # RES 1,(HL)
        0x8F: (8, res_set, 2, (1, 'A', 0)),                   # RES 1,A
        0x90: (8, res_set, 2, (2, 'B', 0)),                   # RES 2,B
        0x91: (8, res_set, 2, (2, 'C', 0)),                   # RES 2,C
        0x92: (8, res_set, 2, (2, 'D', 0)),                   # RES 2,D
        0x93: (8, res_set, 2, (2, 'E', 0)),                   # RES 2,E
        0x94: (8, res_set, 2, (2, 'H', 0)),                   # RES 2,H
        0x95: (8, res_set, 2, (2, 'L', 0)),                   # RES 2,L
        0x96: (15, res_set, 2, (2, '(HL)', 0)),               # RES 2,(HL)
        0x97: (8, res_set, 2, (2, 'A', 0)),                   # RES 2,A
        0x98: (8, res_set, 2, (3, 'B', 0)),                   # RES 3,B
        0x99: (8, res_set, 2, (3, 'C', 0)),                   # RES 3,C
        0x9A: (8, res_set, 2, (3, 'D', 0)),                   # RES 3,D
        0x9B: (8, res_set, 2, (3, 'E', 0)),                   # RES 3,E
        0x9C: (8, res_set, 2, (3, 'H', 0)),                   # RES 3,H
        0x9D: (8, res_set, 2, (3, 'L', 0)),                   # RES 3,L
        0x9E: (15, res_set, 2, (3, '(HL)', 0)),               # RES 3,(HL)
        0x9F: (8, res_set, 2, (3, 'A', 0)),                   # RES 3,A
        0xA0: (8, res_set, 2, (4, 'B', 0)),                   # RES 4,B
        0xA1: (8, res_set, 2, (4, 'C', 0)),                   # RES 4,C
        0xA2: (8, res_set, 2, (4, 'D', 0)),                   # RES 4,D
        0xA3: (8, res_set, 2, (4, 'E', 0)),                   # RES 4,E
        0xA4: (8, res_set, 2, (4, 'H', 0)),                   # RES 4,H
        0xA5: (8, res_set, 2, (4, 'L', 0)),                   # RES 4,L
        0xA6: (15, res_set, 2, (4, '(HL)', 0)),               # RES 4,(HL)
        0xA7: (8, res_set, 2, (4, 'A', 0)),                   # RES 4,A
        0xA8: (8, res_set, 2, (5, 'B', 0)),                   # RES 5,B
        0xA9: (8, res_set, 2, (5, 'C', 0)),                   # RES 5,C
        0xAA: (8, res_set, 2, (5, 'D', 0)),                   # RES 5,D
        0xAB: (8, res_set, 2, (5, 'E', 0)),                   # RES 5,E
        0xAC: (8, res_set, 2, (5, 'H', 0)),                   # RES 5,H
        0xAD: (8, res_set, 2, (5, 'L', 0)),                   # RES 5,L
        0xAE: (15, res_set, 2, (5, '(HL)', 0)),               # RES 5,(HL)
        0xAF: (8, res_set, 2, (5, 'A', 0)),                   # RES 5,A
        0xB0: (8, res_set, 2, (6, 'B', 0)),                   # RES 6,B
        0xB1: (8, res_set, 2, (6, 'C', 0)),                   # RES 6,C
        0xB2: (8, res_set, 2, (6, 'D', 0)),                   # RES 6,D
        0xB3: (8, res_set, 2, (6, 'E', 0)),                   # RES 6,E
        0xB4: (8, res_set, 2, (6, 'H', 0)),                   # RES 6,H
        0xB5: (8, res_set, 2, (6, 'L', 0)),                   # RES 6,L
        0xB6: (15, res_set, 2, (6, '(HL)', 0)),               # RES 6,(HL)
        0xB7: (8, res_set, 2, (6, 'A', 0)),                   # RES 6,A
        0xB8: (8, res_set, 2, (7, 'B', 0)),                   # RES 7,B
        0xB9: (8, res_set, 2, (7, 'C', 0)),                   # RES 7,C
        0xBA: (8, res_set, 2, (7, 'D', 0)),                   # RES 7,D
        0xBB: (8, res_set, 2, (7, 'E', 0)),                   # RES 7,E
        0xBC: (8, res_set, 2, (7, 'H', 0)),                   # RES 7,H
        0xBD: (8, res_set, 2, (7, 'L', 0)),                   # RES 7,L
        0xBE: (15, res_set, 2, (7, '(HL)', 0)),               # RES 7,(HL)
        0xBF: (8, res_set, 2, (7, 'A', 0)),                   # RES 7,A
        0xC0: (8, res_set, 2, (0, 'B', 1)),                   # SET 0,B
        0xC1: (8, res_set, 2, (0, 'C', 1)),                   # SET 0,C
        0xC2: (8, res_set, 2, (0, 'D', 1)),                   # SET 0,D
        0xC3: (8, res_set, 2, (0, 'E', 1)),                   # SET 0,E
        0xC4: (8, res_set, 2, (0, 'H', 1)),                   # SET 0,H
        0xC5: (8, res_set, 2, (0, 'L', 1)),                   # SET 0,L
        0xC6: (15, res_set, 2, (0, '(HL)', 1)),               # SET 0,(HL)
        0xC7: (8, res_set, 2, (0, 'A', 1)),                   # SET 0,A
        0xC8: (8, res_set, 2, (1, 'B', 1)),                   # SET 1,B
        0xC9: (8, res_set, 2, (1, 'C', 1)),                   # SET 1,C
        0xCA: (8, res_set, 2, (1, 'D', 1)),                   # SET 1,D
        0xCB: (8, res_set, 2, (1, 'E', 1)),                   # SET 1,E
        0xCC: (8, res_set, 2, (1, 'H', 1)),                   # SET 1,H
        0xCD: (8, res_set, 2, (1, 'L', 1)),                   # SET 1,L
        0xCE: (15, res_set, 2, (1, '(HL)', 1)),               # SET 1,(HL)
        0xCF: (8, res_set, 2, (1, 'A', 1)),                   # SET 1,A
        0xD0: (8, res_set, 2, (2, 'B', 1)),                   # SET 2,B
        0xD1: (8, res_set, 2, (2, 'C', 1)),                   # SET 2,C
        0xD2: (8, res_set, 2, (2, 'D', 1)),                   # SET 2,D
        0xD3: (8, res_set, 2, (2, 'E', 1)),                   # SET 2,E
        0xD4: (8, res_set, 2, (2, 'H', 1)),                   # SET 2,H
        0xD5: (8, res_set, 2, (2, 'L', 1)),                   # SET 2,L
        0xD6: (15, res_set, 2, (2, '(HL)', 1)),               # SET 2,(HL)
        0xD7: (8, res_set, 2, (2, 'A', 1)),                   # SET 2,A
        0xD8: (8, res_set, 2, (3, 'B', 1)),                   # SET 3,B
        0xD9: (8, res_set, 2, (3, 'C', 1)),                   # SET 3,C
        0xDA: (8, res_set, 2, (3, 'D', 1)),                   # SET 3,D
        0xDB: (8, res_set, 2, (3, 'E', 1)),                   # SET 3,E
        0xDC: (8, res_set, 2, (3, 'H', 1)),                   # SET 3,H
        0xDD: (8, res_set, 2, (3, 'L', 1)),                   # SET 3,L
        0xDE: (15, res_set, 2, (3, '(HL)', 1)),               # SET 3,(HL)
        0xDF: (8, res_set, 2, (3, 'A', 1)),                   # SET 3,A
        0xE0: (8, res_set, 2, (4, 'B', 1)),                   # SET 4,B
        0xE1: (8, res_set, 2, (4, 'C', 1)),                   # SET 4,C
        0xE2: (8, res_set, 2, (4, 'D', 1)),                   # SET 4,D
        0xE3: (8, res_set, 2, (4, 'E', 1)),                   # SET 4,E
        0xE4: (8, res_set, 2, (4, 'H', 1)),                   # SET 4,H
        0xE5: (8, res_set, 2, (4, 'L', 1)),                   # SET 4,L
        0xE6: (15, res_set, 2, (4, '(HL)', 1)),               # SET 4,(HL)
        0xE7: (8, res_set, 2, (4, 'A', 1)),                   # SET 4,A
        0xE8: (8, res_set, 2, (5, 'B', 1)),                   # SET 5,B
        0xE9: (8, res_set, 2, (5, 'C', 1)),                   # SET 5,C
        0xEA: (8, res_set, 2, (5, 'D', 1)),                   # SET 5,D
        0xEB: (8, res_set, 2, (5, 'E', 1)),                   # SET 5,E
        0xEC: (8, res_set, 2, (5, 'H', 1)),                   # SET 5,H
        0xED: (8, res_set, 2, (5, 'L', 1)),                   # SET 5,L
        0xEE: (15, res_set, 2, (5, '(HL)', 1)),               # SET 5,(HL)
        0xEF: (8, res_set, 2, (5, 'A', 1)),                   # SET 5,A
        0xF0: (8, res_set, 2, (6, 'B', 1)),                   # SET 6,B
        0xF1: (8, res_set, 2, (6, 'C', 1)),                   # SET 6,C
        0xF2: (8, res_set, 2, (6, 'D', 1)),                   # SET 6,D
        0xF3: (8, res_set, 2, (6, 'E', 1)),                   # SET 6,E
        0xF4: (8, res_set, 2, (6, 'H', 1)),                   # SET 6,H
        0xF5: (8, res_set, 2, (6, 'L', 1)),                   # SET 6,L
        0xF6: (15, res_set, 2, (6, '(HL)', 1)),               # SET 6,(HL)
        0xF7: (8, res_set, 2, (6, 'A', 1)),                   # SET 6,A
        0xF8: (8, res_set, 2, (7, 'B', 1)),                   # SET 7,B
        0xF9: (8, res_set, 2, (7, 'C', 1)),                   # SET 7,C
        0xFA: (8, res_set, 2, (7, 'D', 1)),                   # SET 7,D
        0xFB: (8, res_set, 2, (7, 'E', 1)),                   # SET 7,E
        0xFC: (8, res_set, 2, (7, 'H', 1)),                   # SET 7,H
        0xFD: (8, res_set, 2, (7, 'L', 1)),                   # SET 7,L
        0xFE: (15, res_set, 2, (7, '(HL)', 1)),               # SET 7,(HL)
        0xFF: (8, res_set, 2, (7, 'A', 1))                    # SET 7,A
    }

    after_DD = {
        0x00: (4, defb, 1, ()),
        0x01: (4, defb, 1, ()),
        0x02: (4, defb, 1, ()),
        0x03: (4, defb, 1, ()),
        0x04: (4, defb, 1, ()),
        0x05: (4, defb, 1, ()),
        0x06: (4, defb, 1, ()),
        0x07: (4, defb, 1, ()),
        0x08: (4, defb, 1, ()),
        0x09: (15, add16, 2, ('BC',)),                        # ADD IX,BC
        0x0A: (4, defb, 1, ()),
        0x0B: (4, defb, 1, ()),
        0x0C: (4, defb, 1, ()),
        0x0D: (4, defb, 1, ()),
        0x0E: (4, defb, 1, ()),
        0x0F: (4, defb, 1, ()),
        0x10: (4, defb, 1, ()),
        0x11: (4, defb, 1, ()),
        0x12: (4, defb, 1, ()),
        0x13: (4, defb, 1, ()),
        0x14: (4, defb, 1, ()),
        0x15: (4, defb, 1, ()),
        0x16: (4, defb, 1, ()),
        0x17: (4, defb, 1, ()),
        0x18: (4, defb, 1, ()),
        0x19: (15, add16, 2, ('DE',)),                        # ADD IX,DE
        0x1A: (4, defb, 1, ()),
        0x1B: (4, defb, 1, ()),
        0x1C: (4, defb, 1, ()),
        0x1D: (4, defb, 1, ()),
        0x1E: (4, defb, 1, ()),
        0x1F: (4, defb, 1, ()),
        0x20: (4, defb, 1, ()),
        0x21: (14, ld16, 4, ('IX',)),                         # LD IX,nn
        0x22: (20, ld16addr, 4, ('IX', 1)),                   # LD (nn),IX
        0x23: (10, inc_dec16, 2, ('INC', 'IX')),              # INC IX
        0x24: (8, inc_dec8, 2, ('INC', 'IXh')),               # INC IXh
        0x25: (8, inc_dec8, 2, ('DEC', 'IXh')),               # DEC IXh
        0x26: (11, ld8, 3, ('IXh',)),                         # LD IXh,n
        0x27: (4, defb, 1, ()),
        0x28: (4, defb, 1, ()),
        0x29: (15, add16, 2, ('IX',)),                        # ADD IX,IX
        0x2A: (20, ld16addr, 4, ('IX', 0)),                   # LD IX,(nn)
        0x2B: (10, inc_dec16, 2, ('DEC', 'IX')),              # DEC IX
        0x2C: (8, inc_dec8, 2, ('INC', 'IXl')),               # INC IXl
        0x2D: (8, inc_dec8, 2, ('DEC', 'IXl')),               # DEC IXl
        0x2E: (11, ld8, 3, ('IXl',)),                         # LD IXl,n
        0x2F: (4, defb, 1, ()),
        0x30: (4, defb, 1, ()),
        0x31: (4, defb, 1, ()),
        0x32: (4, defb, 1, ()),
        0x33: (4, defb, 1, ()),
        0x34: (23, inc_dec8, 3, ('INC', '')),                 # INC (IX+d)
        0x35: (23, inc_dec8, 3, ('DEC', '')),                 # DEC (IX+d)
        0x36: (19, ld8, 4, ('',)),                            # LD (IX+d),n
        0x37: (4, defb, 1, ()),
        0x38: (4, defb, 1, ()),
        0x39: (15, add16, 2, ('SP',)),                        # ADD IX,SP
        0x3A: (4, defb, 1, ()),
        0x3B: (4, defb, 1, ()),
        0x3C: (4, defb, 1, ()),
        0x3D: (4, defb, 1, ()),
        0x3E: (4, defb, 1, ()),
        0x3F: (4, defb, 1, ()),
        0x40: (4, defb, 1, ()),
        0x41: (4, defb, 1, ()),
        0x42: (4, defb, 1, ()),
        0x43: (4, defb, 1, ()),
        0x44: (8, ld8, 2, ('B', 'IXh')),                      # LD B,IXh
        0x45: (8, ld8, 2, ('B', 'IXl')),                      # LD B,IXl
        0x46: (19, ld8, 3, ('B', '')),                        # LD B,(IX+d)
        0x47: (4, defb, 1, ()),
        0x48: (4, defb, 1, ()),
        0x49: (4, defb, 1, ()),
        0x4A: (4, defb, 1, ()),
        0x4B: (4, defb, 1, ()),
        0x4C: (8, ld8, 2, ('C', 'IXh')),                      # LD C,IXh
        0x4D: (8, ld8, 2, ('C', 'IXl')),                      # LD C,IXl
        0x4E: (19, ld8, 3, ('C', '')),                        # LD C,(IX+d)
        0x4F: (4, defb, 1, ()),
        0x50: (4, defb, 1, ()),
        0x51: (4, defb, 1, ()),
        0x52: (4, defb, 1, ()),
        0x53: (4, defb, 1, ()),
        0x54: (8, ld8, 2, ('D', 'IXh')),                      # LD D,IXh
        0x55: (8, ld8, 2, ('D', 'IXl')),                      # LD D,IXl
        0x56: (19, ld8, 3, ('D', '')),                        # LD D,(IX+d)
        0x57: (4, defb, 1, ()),
        0x58: (4, defb, 1, ()),
        0x59: (4, defb, 1, ()),
        0x5A: (4, defb, 1, ()),
        0x5B: (4, defb, 1, ()),
        0x5C: (8, ld8, 2, ('E', 'IXh')),                      # LD E,IXh
        0x5D: (8, ld8, 2, ('E', 'IXl')),                      # LD E,IXl
        0x5E: (19, ld8, 3, ('E', '')),                        # LD E,(IX+d)
        0x5F: (4, defb, 1, ()),
        0x60: (8, ld8, 2, ('IXh', 'B')),                      # LD IXh,B
        0x61: (8, ld8, 2, ('IXh', 'C')),                      # LD IXh,C
        0x62: (8, ld8, 2, ('IXh', 'D')),                      # LD IXh,D
        0x63: (8, ld8, 2, ('IXh', 'E')),                      # LD IXh,E
        0x64: (8, ld8, 2, ('IXh', 'IXh')),                    # LD IXh,IXh
        0x65: (8, ld8, 2, ('IXh', 'IXl')),                    # LD IXh,IXl
        0x66: (19, ld8, 3, ('H', '')),                        # LD H,(IX+d)
        0x67: (8, ld8, 2, ('IXh', 'A')),                      # LD IXh,A
        0x68: (8, ld8, 2, ('IXl', 'B')),                      # LD IXl,B
        0x69: (8, ld8, 2, ('IXl', 'C')),                      # LD IXl,C
        0x6A: (8, ld8, 2, ('IXl', 'D')),                      # LD IXl,D
        0x6B: (8, ld8, 2, ('IXl', 'E')),                      # LD IXl,E
        0x6C: (8, ld8, 2, ('IXl', 'IXh')),                    # LD IXl,IXh
        0x6D: (8, ld8, 2, ('IXl', 'IXl')),                    # LD IXl,IXl
        0x6E: (19, ld8, 3, ('L', '')),                        # LD L,(IX+d)
        0x6F: (8, ld8, 2, ('IXl', 'A')),                      # LD IXl,A
        0x70: (19, ld8, 3, ('', 'B')),                        # LD (IX+d),B
        0x71: (19, ld8, 3, ('', 'C')),                        # LD (IX+d),C
        0x72: (19, ld8, 3, ('', 'D')),                        # LD (IX+d),D
        0x73: (19, ld8, 3, ('', 'E')),                        # LD (IX+d),E
        0x74: (19, ld8, 3, ('', 'H')),                        # LD (IX+d),H
        0x75: (19, ld8, 3, ('', 'L')),                        # LD (IX+d),L
        0x76: (4, defb, 1, ()),
        0x77: (19, ld8, 3, ('', 'A')),                        # LD (IX+d),A
        0x78: (4, defb, 1, ()),
        0x79: (4, defb, 1, ()),
        0x7A: (4, defb, 1, ()),
        0x7B: (4, defb, 1, ()),
        0x7C: (8, ld8, 2, ('A', 'IXh')),                      # LD A,IXh
        0x7D: (8, ld8, 2, ('A', 'IXl')),                      # LD A,IXl
        0x7E: (19, ld8, 3, ('A', '')),                        # LD A,(IX+d)
        0x7F: (4, defb, 1, ()),
        0x80: (4, defb, 1, ()),
        0x81: (4, defb, 1, ()),
        0x82: (4, defb, 1, ()),
        0x83: (4, defb, 1, ()),
        0x84: (8, add_a, 2, ('IXh',)),                        # ADD A,IXh
        0x85: (8, add_a, 2, ('IXl',)),                        # ADD A,IXl
        0x86: (19, add_a, 3, ('',)),                          # ADD A,(IX+d)
        0x87: (4, defb, 1, ()),
        0x88: (4, defb, 1, ()),
        0x89: (4, defb, 1, ()),
        0x8A: (4, defb, 1, ()),
        0x8B: (4, defb, 1, ()),
        0x8C: (8, add_a, 2, ('IXh', 1)),                      # ADC A,IXh
        0x8D: (8, add_a, 2, ('IXl', 1)),                      # ADC A,IXl
        0x8E: (19, add_a, 3, ('', 1)),                        # ADC A,(IX+d)
        0x8F: (4, defb, 1, ()),
        0x90: (4, defb, 1, ()),
        0x91: (4, defb, 1, ()),
        0x92: (4, defb, 1, ()),
        0x93: (4, defb, 1, ()),
        0x94: (8, add_a, 2, ('IXh', 0, -1)),                  # SUB IXh
        0x95: (8, add_a, 2, ('IXl', 0, -1)),                  # SUB IXl
        0x96: (19, add_a, 3, ('', 0, -1)),                    # SUB (IX+d)
        0x97: (4, defb, 1, ()),
        0x98: (4, defb, 1, ()),
        0x99: (4, defb, 1, ()),
        0x9A: (4, defb, 1, ()),
        0x9B: (4, defb, 1, ()),
        0x9C: (8, add_a, 2, ('IXh', 1, -1)),                  # SBC A,IXh
        0x9D: (8, add_a, 2, ('IXl', 1, -1)),                  # SBC A,IXl
        0x9E: (19, add_a, 3, ('', 1, -1)),                    # SBC A,(IX+d)
        0x9F: (4, defb, 1, ()),
        0xA0: (4, defb, 1, ()),
        0xA1: (4, defb, 1, ()),
        0xA2: (4, defb, 1, ()),
        0xA3: (4, defb, 1, ()),
        0xA4: (8, anda, 2, ('IXh',)),                         # AND IXh
        0xA5: (8, anda, 2, ('IXl',)),                         # AND IXl
        0xA6: (19, anda, 3, ('',)),                           # AND (IX+d)
        0xA7: (4, defb, 1, ()),
        0xA8: (4, defb, 1, ()),
        0xA9: (4, defb, 1, ()),
        0xAA: (4, defb, 1, ()),
        0xAB: (4, defb, 1, ()),
        0xAC: (8, xor, 2, ('IXh',)),                          # XOR IXh
        0xAD: (8, xor, 2, ('IXl',)),                          # XOR IXl
        0xAE: (19, xor, 3, ('',)),                            # XOR (IX+d)
        0xAF: (4, defb, 1, ()),
        0xB0: (4, defb, 1, ()),
        0xB1: (4, defb, 1, ()),
        0xB2: (4, defb, 1, ()),
        0xB3: (4, defb, 1, ()),
        0xB4: (8, ora, 2, ('IXh',)),                          # OR IXh
        0xB5: (8, ora, 2, ('IXl',)),                          # OR IXl
        0xB6: (19, ora, 3, ('',)),                            # OR (IX+d)
        0xB7: (4, defb, 1, ()),
        0xB8: (4, defb, 1, ()),
        0xB9: (4, defb, 1, ()),
        0xBA: (4, defb, 1, ()),
        0xBB: (4, defb, 1, ()),
        0xBC: (8, cp, 2, ('IXh',)),                           # CP IXh
        0xBD: (8, cp, 2, ('IXl',)),                           # CP IXl
        0xBE: (19, cp, 3, ('',)),                             # CP (IX+d)
        0xBF: (4, defb, 1, ()),
        0xC0: (4, defb, 1, ()),
        0xC1: (4, defb, 1, ()),
        0xC2: (4, defb, 1, ()),
        0xC3: (4, defb, 1, ()),
        0xC4: (4, defb, 1, ()),
        0xC5: (4, defb, 1, ()),
        0xC6: (4, defb, 1, ()),
        0xC7: (4, defb, 1, ()),
        0xC8: (4, defb, 1, ()),
        0xC9: (4, defb, 1, ()),
        0xCA: (4, defb, 1, ()),
        0xCB: None,                                           # DDCB prefix
        0xCC: (4, defb, 1, ()),
        0xCD: (4, defb, 1, ()),
        0xCE: (4, defb, 1, ()),
        0xCF: (4, defb, 1, ()),
        0xD0: (4, defb, 1, ()),
        0xD1: (4, defb, 1, ()),
        0xD2: (4, defb, 1, ()),
        0xD3: (4, defb, 1, ()),
        0xD4: (4, defb, 1, ()),
        0xD5: (4, defb, 1, ()),
        0xD6: (4, defb, 1, ()),
        0xD7: (4, defb, 1, ()),
        0xD8: (4, defb, 1, ()),
        0xD9: (4, defb, 1, ()),
        0xDA: (4, defb, 1, ()),
        0xDB: (4, defb, 1, ()),
        0xDC: (4, defb, 1, ()),
        0xDD: (4, defb, 1, ()),
        0xDE: (4, defb, 1, ()),
        0xDF: (4, defb, 1, ()),
        0xE0: (4, defb, 1, ()),
        0xE1: (14, pop, 2, ('IX',)),                          # POP IX
        0xE2: (4, defb, 1, ()),
        0xE3: (23, ex_sp, 2, ()),                             # EX (SP),IX
        0xE4: (4, defb, 1, ()),
        0xE5: (15, push, 2, ('IX',)),                         # PUSH IX
        0xE6: (4, defb, 1, ()),
        0xE7: (4, defb, 1, ()),
        0xE8: (4, defb, 1, ()),
        0xE9: (8, jp, 2, ()),                                 # JP (IX)
        0xEA: (4, defb, 1, ()),
        0xEB: (4, defb, 1, ()),
        0xEC: (4, defb, 1, ()),
        0xED: (4, defb, 1, ()),
        0xEE: (4, defb, 1, ()),
        0xEF: (4, defb, 1, ()),
        0xF0: (4, defb, 1, ()),
        0xF1: (4, defb, 1, ()),
        0xF2: (4, defb, 1, ()),
        0xF3: (4, defb, 1, ()),
        0xF4: (4, defb, 1, ()),
        0xF5: (4, defb, 1, ()),
        0xF6: (4, defb, 1, ()),
        0xF7: (4, defb, 1, ()),
        0xF8: (4, defb, 1, ()),
        0xF9: (10, ldsprr, 2, ('IX',)),                       # LD SP,IX
        0xFA: (4, defb, 1, ()),
        0xFB: (4, defb, 1, ()),
        0xFC: (4, defb, 1, ()),
        0xFD: (4, defb, 1, ()),
        0xFE: (4, defb, 1, ()),
        0xFF: (4, defb, 1, ())
    }

    after_ED = {
        0x00: (8, defb, 2, ()),
        0x01: (8, defb, 2, ()),
        0x02: (8, defb, 2, ()),
        0x03: (8, defb, 2, ()),
        0x04: (8, defb, 2, ()),
        0x05: (8, defb, 2, ()),
        0x06: (8, defb, 2, ()),
        0x07: (8, defb, 2, ()),
        0x08: (8, defb, 2, ()),
        0x09: (8, defb, 2, ()),
        0x0A: (8, defb, 2, ()),
        0x0B: (8, defb, 2, ()),
        0x0C: (8, defb, 2, ()),
        0x0D: (8, defb, 2, ()),
        0x0E: (8, defb, 2, ()),
        0x0F: (8, defb, 2, ()),
        0x10: (8, defb, 2, ()),
        0x11: (8, defb, 2, ()),
        0x12: (8, defb, 2, ()),
        0x13: (8, defb, 2, ()),
        0x14: (8, defb, 2, ()),
        0x15: (8, defb, 2, ()),
        0x16: (8, defb, 2, ()),
        0x17: (8, defb, 2, ()),
        0x18: (8, defb, 2, ()),
        0x19: (8, defb, 2, ()),
        0x1A: (8, defb, 2, ()),
        0x1B: (8, defb, 2, ()),
        0x1C: (8, defb, 2, ()),
        0x1D: (8, defb, 2, ()),
        0x1E: (8, defb, 2, ()),
        0x1F: (8, defb, 2, ()),
        0x20: (8, defb, 2, ()),
        0x21: (8, defb, 2, ()),
        0x22: (8, defb, 2, ()),
        0x23: (8, defb, 2, ()),
        0x24: (8, defb, 2, ()),
        0x25: (8, defb, 2, ()),
        0x26: (8, defb, 2, ()),
        0x27: (8, defb, 2, ()),
        0x28: (8, defb, 2, ()),
        0x29: (8, defb, 2, ()),
        0x2A: (8, defb, 2, ()),
        0x2B: (8, defb, 2, ()),
        0x2C: (8, defb, 2, ()),
        0x2D: (8, defb, 2, ()),
        0x2E: (8, defb, 2, ()),
        0x2F: (8, defb, 2, ()),
        0x30: (8, defb, 2, ()),
        0x31: (8, defb, 2, ()),
        0x32: (8, defb, 2, ()),
        0x33: (8, defb, 2, ()),
        0x34: (8, defb, 2, ()),
        0x35: (8, defb, 2, ()),
        0x36: (8, defb, 2, ()),
        0x37: (8, defb, 2, ()),
        0x38: (8, defb, 2, ()),
        0x39: (8, defb, 2, ()),
        0x3A: (8, defb, 2, ()),
        0x3B: (8, defb, 2, ()),
        0x3C: (8, defb, 2, ()),
        0x3D: (8, defb, 2, ()),
        0x3E: (8, defb, 2, ()),
        0x3F: (8, defb, 2, ()),
        0x40: (12, in_c, 2, ('B',)),                          # IN B,(C)
        0x41: (12, outc, 2, ('B',)),                          # OUT (C),B
        0x42: (15, add16, 2, ('BC', 1, -1)),                  # SBC HL,BC
        0x43: (20, ld16addr, 4, ('BC', 1)),                   # LD (nn),BC
        0x44: (8, neg, 2, ()),                                # NEG
        0x45: (14, reti, 2, ('RETN',)),                       # RETN
        0x46: (8, im, 2, (0,)),                               # IM 0
        0x47: (9, ld8, 2, ('I', 'A')),                        # LD I,A
        0x48: (12, in_c, 2, ('C',)),                          # IN C,(C)
        0x49: (12, outc, 2, ('C',)),                          # OUT (C),C
        0x4A: (15, add16, 2, ('BC', 1)),                      # ADC HL,BC
        0x4B: (20, ld16addr, 4, ('BC', 0)),                   # LD BC,(nn)
        0x4C: (8, neg, 2, ()),                                # NEG
        0x4D: (14, reti, 2, ('RETI',)),                       # RETI
        0x4E: (8, im, 2, (0,)),                               # IM 0
        0x4F: (9, ld8, 2, ('R', 'A')),                        # LD R,A
        0x50: (12, in_c, 2, ('D',)),                          # IN D,(C)
        0x51: (12, outc, 2, ('D',)),                          # OUT (C),D
        0x52: (15, add16, 2, ('DE', 1, -1)),                  # SBC HL,DE
        0x53: (20, ld16addr, 4, ('DE', 1)),                   # LD (nn),DE
        0x54: (8, neg, 2, ()),                                # NEG
        0x55: (14, reti, 2, ('RETN',)),                       # RETN
        0x56: (8, im, 2, (1,)),                               # IM 1
        0x57: (9, ld8, 2, ('A', 'I')),                        # LD A,I
        0x58: (12, in_c, 2, ('E',)),                          # IN E,(C)
        0x59: (12, outc, 2, ('E',)),                          # OUT (C),E
        0x5A: (15, add16, 2, ('DE', 1)),                      # ADC HL,DE
        0x5B: (20, ld16addr, 4, ('DE', 0)),                   # LD DE,(nn)
        0x5C: (8, neg, 2, ()),                                # NEG
        0x5D: (14, reti, 2, ('RETN',)),                       # RETN
        0x5E: (8, im, 2, (2,)),                               # IM 2
        0x5F: (9, ld8, 2, ('A', 'R')),                        # LD A,R
        0x60: (12, in_c, 2, ('H',)),                          # IN H,(C)
        0x61: (12, outc, 2, ('H',)),                          # OUT (C),H
        0x62: (15, add16, 2, ('HL', 1, -1)),                  # SBC HL,HL
        0x63: (20, ld16addr, 4, ('HL', 1)),                   # LD (nn),HL
        0x64: (8, neg, 2, ()),                                # NEG
        0x65: (14, reti, 2, ('RETN',)),                       # RETN
        0x66: (8, im, 2, (0,)),                               # IM 0
        0x67: (18, rrd, 2, ()),                               # RRD
        0x68: (12, in_c, 2, ('L',)),                          # IN L,(C)
        0x69: (12, outc, 2, ('L',)),                          # OUT (C),L
        0x6A: (15, add16, 2, ('HL', 1)),                      # ADC HL,HL
        0x6B: (20, ld16addr, 4, ('HL', 0)),                   # LD HL,(nn)
        0x6C: (8, neg, 2, ()),                                # NEG
        0x6D: (14, reti, 2, ('RETN',)),                       # RETN
        0x6E: (8, im, 2, (0,)),                               # IM 0
        0x6F: (18, rld, 2, ()),                               # RLD
        0x70: (12, in_c, 2, ('F',)),                          # IN F,(C)
        0x71: (12, outc, 2, ('',)),                           # OUT (C),0
        0x72: (15, add16, 2, ('SP', 1, -1)),                  # SBC HL,SP
        0x73: (20, ld16addr, 4, ('SP', 1)),                   # LD (nn),SP
        0x74: (8, neg, 2, ()),                                # NEG
        0x75: (14, reti, 2, ('RETN',)),                       # RETN
        0x76: (8, im, 2, (1,)),                               # IM 1
        0x77: (8, defb, 2, ()),
        0x78: (12, in_c, 2, ('A',)),                          # IN A,(C)
        0x79: (12, outc, 2, ('A',)),                          # OUT (C),A
        0x7A: (15, add16, 2, ('SP', 1)),                      # ADC HL,SP
        0x7B: (20, ld16addr, 4, ('SP', 0)),                   # LD SP,(nn)
        0x7C: (8, neg, 2, ()),                                # NEG
        0x7D: (14, reti, 2, ('RETN',)),                       # RETN
        0x7E: (8, im, 2, (2,)),                               # IM 2
        0x7F: (8, defb, 2, ()),
        0x80: (8, defb, 2, ()),
        0x81: (8, defb, 2, ()),
        0x82: (8, defb, 2, ()),
        0x83: (8, defb, 2, ()),
        0x84: (8, defb, 2, ()),
        0x85: (8, defb, 2, ()),
        0x86: (8, defb, 2, ()),
        0x87: (8, defb, 2, ()),
        0x88: (8, defb, 2, ()),
        0x89: (8, defb, 2, ()),
        0x8A: (8, defb, 2, ()),
        0x8B: (8, defb, 2, ()),
        0x8C: (8, defb, 2, ()),
        0x8D: (8, defb, 2, ()),
        0x8E: (8, defb, 2, ()),
        0x8F: (8, defb, 2, ()),
        0x90: (8, defb, 2, ()),
        0x91: (8, defb, 2, ()),
        0x92: (8, defb, 2, ()),
        0x93: (8, defb, 2, ()),
        0x94: (8, defb, 2, ()),
        0x95: (8, defb, 2, ()),
        0x96: (8, defb, 2, ()),
        0x97: (8, defb, 2, ()),
        0x98: (8, defb, 2, ()),
        0x99: (8, defb, 2, ()),
        0x9A: (8, defb, 2, ()),
        0x9B: (8, defb, 2, ()),
        0x9C: (8, defb, 2, ()),
        0x9D: (8, defb, 2, ()),
        0x9E: (8, defb, 2, ()),
        0x9F: (8, defb, 2, ()),
        0xA0: (16, block, 2, ('LDI', 1, 0)),                  # LDI
        0xA1: (16, block, 2, ('CPI', 1, 0)),                  # CPI
        0xA2: (16, block, 2, ('INI', 1, 0)),                  # INI
        0xA3: (16, block, 2, ('OUTI', 1, 0)),                 # OUTI
        0xA4: (8, defb, 2, ()),
        0xA5: (8, defb, 2, ()),
        0xA6: (8, defb, 2, ()),
        0xA7: (8, defb, 2, ()),
        0xA8: (16, block, 2, ('LDD', -1, 0)),                 # LDD
        0xA9: (16, block, 2, ('CPD', -1, 0)),                 # CPD
        0xAA: (16, block, 2, ('IND', -1, 0)),                 # IND
        0xAB: (16, block, 2, ('OUTD', -1, 0)),                # OUTD
        0xAC: (8, defb, 2, ()),
        0xAD: (8, defb, 2, ()),
        0xAE: (8, defb, 2, ()),
        0xAF: (8, defb, 2, ()),
        0xB0: ((21, 16), block, 2, ('LDIR', 1, 1)),           # LDIR
        0xB1: ((21, 16), block, 2, ('CPIR', 1, 1)),           # CPIR
        0xB2: ((21, 16), block, 2, ('INIR', 1, 1)),           # INIR
        0xB3: ((21, 16), block, 2, ('OTIR', 1, 1)),           # OTIR
        0xB4: (8, defb, 2, ()),
        0xB5: (8, defb, 2, ()),
        0xB6: (8, defb, 2, ()),
        0xB7: (8, defb, 2, ()),
        0xB8: ((21, 16), block, 2, ('LDDR', -1, 1)),          # LDDR
        0xB9: ((21, 16), block, 2, ('CPDR', -1, 1)),          # CPDR
        0xBA: ((21, 16), block, 2, ('INDR', -1, 1)),          # INDR
        0xBB: ((21, 16), block, 2, ('OTDR', -1, 1)),          # OTDR
        0xBC: (8, defb, 2, ()),
        0xBD: (8, defb, 2, ()),
        0xBE: (8, defb, 2, ()),
        0xBF: (8, defb, 2, ()),
        0xC0: (8, defb, 2, ()),
        0xC1: (8, defb, 2, ()),
        0xC2: (8, defb, 2, ()),
        0xC3: (8, defb, 2, ()),
        0xC4: (8, defb, 2, ()),
        0xC5: (8, defb, 2, ()),
        0xC6: (8, defb, 2, ()),
        0xC7: (8, defb, 2, ()),
        0xC8: (8, defb, 2, ()),
        0xC9: (8, defb, 2, ()),
        0xCA: (8, defb, 2, ()),
        0xCB: (8, defb, 2, ()),
        0xCC: (8, defb, 2, ()),
        0xCD: (8, defb, 2, ()),
        0xCE: (8, defb, 2, ()),
        0xCF: (8, defb, 2, ()),
        0xD0: (8, defb, 2, ()),
        0xD1: (8, defb, 2, ()),
        0xD2: (8, defb, 2, ()),
        0xD3: (8, defb, 2, ()),
        0xD4: (8, defb, 2, ()),
        0xD5: (8, defb, 2, ()),
        0xD6: (8, defb, 2, ()),
        0xD7: (8, defb, 2, ()),
        0xD8: (8, defb, 2, ()),
        0xD9: (8, defb, 2, ()),
        0xDA: (8, defb, 2, ()),
        0xDB: (8, defb, 2, ()),
        0xDC: (8, defb, 2, ()),
        0xDD: (8, defb, 2, ()),
        0xDE: (8, defb, 2, ()),
        0xDF: (8, defb, 2, ()),
        0xE0: (8, defb, 2, ()),
        0xE1: (8, defb, 2, ()),
        0xE2: (8, defb, 2, ()),
        0xE3: (8, defb, 2, ()),
        0xE4: (8, defb, 2, ()),
        0xE5: (8, defb, 2, ()),
        0xE6: (8, defb, 2, ()),
        0xE7: (8, defb, 2, ()),
        0xE8: (8, defb, 2, ()),
        0xE9: (8, defb, 2, ()),
        0xEA: (8, defb, 2, ()),
        0xEB: (8, defb, 2, ()),
        0xEC: (8, defb, 2, ()),
        0xED: (8, defb, 2, ()),
        0xEE: (8, defb, 2, ()),
        0xEF: (8, defb, 2, ()),
        0xF0: (8, defb, 2, ()),
        0xF1: (8, defb, 2, ()),
        0xF2: (8, defb, 2, ()),
        0xF3: (8, defb, 2, ()),
        0xF4: (8, defb, 2, ()),
        0xF5: (8, defb, 2, ()),
        0xF6: (8, defb, 2, ()),
        0xF7: (8, defb, 2, ()),
        0xF8: (8, defb, 2, ()),
        0xF9: (8, defb, 2, ()),
        0xFA: (8, defb, 2, ()),
        0xFB: (8, defb, 2, ()),
        0xFC: (8, defb, 2, ()),
        0xFD: (8, defb, 2, ()),
        0xFE: (8, defb, 2, ()),
        0xFF: (8, defb, 2, ())
    }

    after_DDCB = {
        0x00: (23, rotate, 4, ('RLC ', 128, '', 'C', 'B')),   # RLC (IX+d),B
        0x01: (23, rotate, 4, ('RLC ', 128, '', 'C', 'C')),   # RLC (IX+d),C
        0x02: (23, rotate, 4, ('RLC ', 128, '', 'C', 'D')),   # RLC (IX+d),D
        0x03: (23, rotate, 4, ('RLC ', 128, '', 'C', 'E')),   # RLC (IX+d),E
        0x04: (23, rotate, 4, ('RLC ', 128, '', 'C', 'H')),   # RLC (IX+d),H
        0x05: (23, rotate, 4, ('RLC ', 128, '', 'C', 'L')),   # RLC (IX+d),L
        0x06: (23, rotate, 4, ('RLC ', 128, '', 'C')),        # RLC (IX+d)
        0x07: (23, rotate, 4, ('RLC ', 128, '', 'C', 'A')),   # RLC (IX+d),A
        0x08: (23, rotate, 4, ('RRC ', 1, '', 'C', 'B')),     # RRC (IX+d),B
        0x09: (23, rotate, 4, ('RRC ', 1, '', 'C', 'C')),     # RRC (IX+d),C
        0x0A: (23, rotate, 4, ('RRC ', 1, '', 'C', 'D')),     # RRC (IX+d),D
        0x0B: (23, rotate, 4, ('RRC ', 1, '', 'C', 'E')),     # RRC (IX+d),E
        0x0C: (23, rotate, 4, ('RRC ', 1, '', 'C', 'H')),     # RRC (IX+d),H
        0x0D: (23, rotate, 4, ('RRC ', 1, '', 'C', 'L')),     # RRC (IX+d),L
        0x0E: (23, rotate, 4, ('RRC ', 1, '', 'C')),          # RRC (IX+d)
        0x0F: (23, rotate, 4, ('RRC ', 1, '', 'C', 'A')),     # RRC (IX+d),A
        0x10: (23, rotate, 4, ('RL ', 128, '', '', 'B')),     # RL (IX+d),B
        0x11: (23, rotate, 4, ('RL ', 128, '', '', 'C')),     # RL (IX+d),C
        0x12: (23, rotate, 4, ('RL ', 128, '', '', 'D')),     # RL (IX+d),D
        0x13: (23, rotate, 4, ('RL ', 128, '', '', 'E')),     # RL (IX+d),E
        0x14: (23, rotate, 4, ('RL ', 128, '', '', 'H')),     # RL (IX+d),H
        0x15: (23, rotate, 4, ('RL ', 128, '', '', 'L')),     # RL (IX+d),L
        0x16: (23, rotate, 4, ('RL ', 128, '')),              # RL (IX+d)
        0x17: (23, rotate, 4, ('RL ', 128, '', '', 'A')),     # RL (IX+d),A
        0x18: (23, rotate, 4, ('RR ', 1, '', '', 'B')),       # RR (IX+d),B
        0x19: (23, rotate, 4, ('RR ', 1, '', '', 'C')),       # RR (IX+d),C
        0x1A: (23, rotate, 4, ('RR ', 1, '', '', 'D')),       # RR (IX+d),D
        0x1B: (23, rotate, 4, ('RR ', 1, '', '', 'E')),       # RR (IX+d),E
        0x1C: (23, rotate, 4, ('RR ', 1, '', '', 'H')),       # RR (IX+d),H
        0x1D: (23, rotate, 4, ('RR ', 1, '', '', 'L')),       # RR (IX+d),L
        0x1E: (23, rotate, 4, ('RR ', 1, '')),                # RR (IX+d)
        0x1F: (23, rotate, 4, ('RR ', 1, '', '', 'A')),       # RR (IX+d),A
        0x20: (23, shift, 4, ('SLA', 128, '', 'B')),          # SLA (IX+d),B
        0x21: (23, shift, 4, ('SLA', 128, '', 'C')),          # SLA (IX+d),C
        0x22: (23, shift, 4, ('SLA', 128, '', 'D')),          # SLA (IX+d),D
        0x23: (23, shift, 4, ('SLA', 128, '', 'E')),          # SLA (IX+d),E
        0x24: (23, shift, 4, ('SLA', 128, '', 'H')),          # SLA (IX+d),H
        0x25: (23, shift, 4, ('SLA', 128, '', 'L')),          # SLA (IX+d),L
        0x26: (23, shift, 4, ('SLA', 128, '')),               # SLA (IX+d)
        0x27: (23, shift, 4, ('SLA', 128, '', 'A')),          # SLA (IX+d),A
        0x28: (23, shift, 4, ('SRA', 1, '', 'B')),            # SRA (IX+d),B
        0x29: (23, shift, 4, ('SRA', 1, '', 'C')),            # SRA (IX+d),C
        0x2A: (23, shift, 4, ('SRA', 1, '', 'D')),            # SRA (IX+d),D
        0x2B: (23, shift, 4, ('SRA', 1, '', 'E')),            # SRA (IX+d),E
        0x2C: (23, shift, 4, ('SRA', 1, '', 'H')),            # SRA (IX+d),H
        0x2D: (23, shift, 4, ('SRA', 1, '', 'L')),            # SRA (IX+d),L
        0x2E: (23, shift, 4, ('SRA', 1, '')),                 # SRA (IX+d)
        0x2F: (23, shift, 4, ('SRA', 1, '', 'A')),            # SRA (IX+d),A
        0x30: (23, shift, 4, ('SLL', 128, '', 'B')),          # SLL (IX+d),B
        0x31: (23, shift, 4, ('SLL', 128, '', 'C')),          # SLL (IX+d),C
        0x32: (23, shift, 4, ('SLL', 128, '', 'D')),          # SLL (IX+d),D
        0x33: (23, shift, 4, ('SLL', 128, '', 'E')),          # SLL (IX+d),E
        0x34: (23, shift, 4, ('SLL', 128, '', 'H')),          # SLL (IX+d),H
        0x35: (23, shift, 4, ('SLL', 128, '', 'L')),          # SLL (IX+d),L
        0x36: (23, shift, 4, ('SLL', 128, '')),               # SLL (IX+d)
        0x37: (23, shift, 4, ('SLL', 128, '', 'A')),          # SLL (IX+d),A
        0x38: (23, shift, 4, ('SRL', 1, '', 'B')),            # SRL (IX+d),B
        0x39: (23, shift, 4, ('SRL', 1, '', 'C')),            # SRL (IX+d),C
        0x3A: (23, shift, 4, ('SRL', 1, '', 'D')),            # SRL (IX+d),D
        0x3B: (23, shift, 4, ('SRL', 1, '', 'E')),            # SRL (IX+d),E
        0x3C: (23, shift, 4, ('SRL', 1, '', 'H')),            # SRL (IX+d),H
        0x3D: (23, shift, 4, ('SRL', 1, '', 'L')),            # SRL (IX+d),L
        0x3E: (23, shift, 4, ('SRL', 1, '')),                 # SRL (IX+d)
        0x3F: (23, shift, 4, ('SRL', 1, '', 'A')),            # SRL (IX+d),A
        0x40: (20, bit, 4, (0, '')),                          # BIT 0,(IX+d)
        0x41: (20, bit, 4, (0, '')),                          # BIT 0,(IX+d)
        0x42: (20, bit, 4, (0, '')),                          # BIT 0,(IX+d)
        0x43: (20, bit, 4, (0, '')),                          # BIT 0,(IX+d)
        0x44: (20, bit, 4, (0, '')),                          # BIT 0,(IX+d)
        0x45: (20, bit, 4, (0, '')),                          # BIT 0,(IX+d)
        0x46: (20, bit, 4, (0, '')),                          # BIT 0,(IX+d)
        0x47: (20, bit, 4, (0, '')),                          # BIT 0,(IX+d)
        0x48: (20, bit, 4, (1, '')),                          # BIT 1,(IX+d)
        0x49: (20, bit, 4, (1, '')),                          # BIT 1,(IX+d)
        0x4A: (20, bit, 4, (1, '')),                          # BIT 1,(IX+d)
        0x4B: (20, bit, 4, (1, '')),                          # BIT 1,(IX+d)
        0x4C: (20, bit, 4, (1, '')),                          # BIT 1,(IX+d)
        0x4D: (20, bit, 4, (1, '')),                          # BIT 1,(IX+d)
        0x4E: (20, bit, 4, (1, '')),                          # BIT 1,(IX+d)
        0x4F: (20, bit, 4, (1, '')),                          # BIT 1,(IX+d)
        0x50: (20, bit, 4, (2, '')),                          # BIT 2,(IX+d)
        0x51: (20, bit, 4, (2, '')),                          # BIT 2,(IX+d)
        0x52: (20, bit, 4, (2, '')),                          # BIT 2,(IX+d)
        0x53: (20, bit, 4, (2, '')),                          # BIT 2,(IX+d)
        0x54: (20, bit, 4, (2, '')),                          # BIT 2,(IX+d)
        0x55: (20, bit, 4, (2, '')),                          # BIT 2,(IX+d)
        0x56: (20, bit, 4, (2, '')),                          # BIT 2,(IX+d)
        0x57: (20, bit, 4, (2, '')),                          # BIT 2,(IX+d)
        0x58: (20, bit, 4, (3, '')),                          # BIT 3,(IX+d)
        0x59: (20, bit, 4, (3, '')),                          # BIT 3,(IX+d)
        0x5A: (20, bit, 4, (3, '')),                          # BIT 3,(IX+d)
        0x5B: (20, bit, 4, (3, '')),                          # BIT 3,(IX+d)
        0x5C: (20, bit, 4, (3, '')),                          # BIT 3,(IX+d)
        0x5D: (20, bit, 4, (3, '')),                          # BIT 3,(IX+d)
        0x5E: (20, bit, 4, (3, '')),                          # BIT 3,(IX+d)
        0x5F: (20, bit, 4, (3, '')),                          # BIT 3,(IX+d)
        0x60: (20, bit, 4, (4, '')),                          # BIT 4,(IX+d)
        0x61: (20, bit, 4, (4, '')),                          # BIT 4,(IX+d)
        0x62: (20, bit, 4, (4, '')),                          # BIT 4,(IX+d)
        0x63: (20, bit, 4, (4, '')),                          # BIT 4,(IX+d)
        0x64: (20, bit, 4, (4, '')),                          # BIT 4,(IX+d)
        0x65: (20, bit, 4, (4, '')),                          # BIT 4,(IX+d)
        0x66: (20, bit, 4, (4, '')),                          # BIT 4,(IX+d)
        0x67: (20, bit, 4, (4, '')),                          # BIT 4,(IX+d)
        0x68: (20, bit, 4, (5, '')),                          # BIT 5,(IX+d)
        0x69: (20, bit, 4, (5, '')),                          # BIT 5,(IX+d)
        0x6A: (20, bit, 4, (5, '')),                          # BIT 5,(IX+d)
        0x6B: (20, bit, 4, (5, '')),                          # BIT 5,(IX+d)
        0x6C: (20, bit, 4, (5, '')),                          # BIT 5,(IX+d)
        0x6D: (20, bit, 4, (5, '')),                          # BIT 5,(IX+d)
        0x6E: (20, bit, 4, (5, '')),                          # BIT 5,(IX+d)
        0x6F: (20, bit, 4, (5, '')),                          # BIT 5,(IX+d)
        0x70: (20, bit, 4, (6, '')),                          # BIT 6,(IX+d)
        0x71: (20, bit, 4, (6, '')),                          # BIT 6,(IX+d)
        0x72: (20, bit, 4, (6, '')),                          # BIT 6,(IX+d)
        0x73: (20, bit, 4, (6, '')),                          # BIT 6,(IX+d)
        0x74: (20, bit, 4, (6, '')),                          # BIT 6,(IX+d)
        0x75: (20, bit, 4, (6, '')),                          # BIT 6,(IX+d)
        0x76: (20, bit, 4, (6, '')),                          # BIT 6,(IX+d)
        0x77: (20, bit, 4, (6, '')),                          # BIT 6,(IX+d)
        0x78: (20, bit, 4, (7, '')),                          # BIT 7,(IX+d)
        0x79: (20, bit, 4, (7, '')),                          # BIT 7,(IX+d)
        0x7A: (20, bit, 4, (7, '')),                          # BIT 7,(IX+d)
        0x7B: (20, bit, 4, (7, '')),                          # BIT 7,(IX+d)
        0x7C: (20, bit, 4, (7, '')),                          # BIT 7,(IX+d)
        0x7D: (20, bit, 4, (7, '')),                          # BIT 7,(IX+d)
        0x7E: (20, bit, 4, (7, '')),                          # BIT 7,(IX+d)
        0x7F: (20, bit, 4, (7, '')),                          # BIT 7,(IX+d)
        0x80: (23, res_set, 4, (0, '', 0, 'B')),              # RES 0,(IX+d),B
        0x81: (23, res_set, 4, (0, '', 0, 'C')),              # RES 0,(IX+d),C
        0x82: (23, res_set, 4, (0, '', 0, 'D')),              # RES 0,(IX+d),D
        0x83: (23, res_set, 4, (0, '', 0, 'E')),              # RES 0,(IX+d),E
        0x84: (23, res_set, 4, (0, '', 0, 'H')),              # RES 0,(IX+d),H
        0x85: (23, res_set, 4, (0, '', 0, 'L')),              # RES 0,(IX+d),L
        0x86: (23, res_set, 4, (0, '', 0)),                   # RES 0,(IX+d)
        0x87: (23, res_set, 4, (0, '', 0, 'A')),              # RES 0,(IX+d),A
        0x88: (23, res_set, 4, (1, '', 0, 'B')),              # RES 1,(IX+d),B
        0x89: (23, res_set, 4, (1, '', 0, 'C')),              # RES 1,(IX+d),C
        0x8A: (23, res_set, 4, (1, '', 0, 'D')),              # RES 1,(IX+d),D
        0x8B: (23, res_set, 4, (1, '', 0, 'E')),              # RES 1,(IX+d),E
        0x8C: (23, res_set, 4, (1, '', 0, 'H')),              # RES 1,(IX+d),H
        0x8D: (23, res_set, 4, (1, '', 0, 'L')),              # RES 1,(IX+d),L
        0x8E: (23, res_set, 4, (1, '', 0)),                   # RES 1,(IX+d)
        0x8F: (23, res_set, 4, (1, '', 0, 'A')),              # RES 1,(IX+d),A
        0x90: (23, res_set, 4, (2, '', 0, 'B')),              # RES 2,(IX+d),B
        0x91: (23, res_set, 4, (2, '', 0, 'C')),              # RES 2,(IX+d),C
        0x92: (23, res_set, 4, (2, '', 0, 'D')),              # RES 2,(IX+d),D
        0x93: (23, res_set, 4, (2, '', 0, 'E')),              # RES 2,(IX+d),E
        0x94: (23, res_set, 4, (2, '', 0, 'H')),              # RES 2,(IX+d),H
        0x95: (23, res_set, 4, (2, '', 0, 'L')),              # RES 2,(IX+d),L
        0x96: (23, res_set, 4, (2, '', 0)),                   # RES 2,(IX+d)
        0x97: (23, res_set, 4, (2, '', 0, 'A')),              # RES 2,(IX+d),A
        0x98: (23, res_set, 4, (3, '', 0, 'B')),              # RES 3,(IX+d),B
        0x99: (23, res_set, 4, (3, '', 0, 'C')),              # RES 3,(IX+d),C
        0x9A: (23, res_set, 4, (3, '', 0, 'D')),              # RES 3,(IX+d),D
        0x9B: (23, res_set, 4, (3, '', 0, 'E')),              # RES 3,(IX+d),E
        0x9C: (23, res_set, 4, (3, '', 0, 'H')),              # RES 3,(IX+d),H
        0x9D: (23, res_set, 4, (3, '', 0, 'L')),              # RES 3,(IX+d),L
        0x9E: (23, res_set, 4, (3, '', 0)),                   # RES 3,(IX+d)
        0x9F: (23, res_set, 4, (3, '', 0, 'A')),              # RES 3,(IX+d),A
        0xA0: (23, res_set, 4, (4, '', 0, 'B')),              # RES 4,(IX+d),B
        0xA1: (23, res_set, 4, (4, '', 0, 'C')),              # RES 4,(IX+d),C
        0xA2: (23, res_set, 4, (4, '', 0, 'D')),              # RES 4,(IX+d),D
        0xA3: (23, res_set, 4, (4, '', 0, 'E')),              # RES 4,(IX+d),E
        0xA4: (23, res_set, 4, (4, '', 0, 'H')),              # RES 4,(IX+d),H
        0xA5: (23, res_set, 4, (4, '', 0, 'L')),              # RES 4,(IX+d),L
        0xA6: (23, res_set, 4, (4, '', 0)),                   # RES 4,(IX+d)
        0xA7: (23, res_set, 4, (4, '', 0, 'A')),              # RES 4,(IX+d),A
        0xA8: (23, res_set, 4, (5, '', 0, 'B')),              # RES 5,(IX+d),B
        0xA9: (23, res_set, 4, (5, '', 0, 'C')),              # RES 5,(IX+d),C
        0xAA: (23, res_set, 4, (5, '', 0, 'D')),              # RES 5,(IX+d),D
        0xAB: (23, res_set, 4, (5, '', 0, 'E')),              # RES 5,(IX+d),E
        0xAC: (23, res_set, 4, (5, '', 0, 'H')),              # RES 5,(IX+d),H
        0xAD: (23, res_set, 4, (5, '', 0, 'L')),              # RES 5,(IX+d),L
        0xAE: (23, res_set, 4, (5, '', 0)),                   # RES 5,(IX+d)
        0xAF: (23, res_set, 4, (5, '', 0, 'A')),              # RES 5,(IX+d),A
        0xB0: (23, res_set, 4, (6, '', 0, 'B')),              # RES 6,(IX+d),B
        0xB1: (23, res_set, 4, (6, '', 0, 'C')),              # RES 6,(IX+d),C
        0xB2: (23, res_set, 4, (6, '', 0, 'D')),              # RES 6,(IX+d),D
        0xB3: (23, res_set, 4, (6, '', 0, 'E')),              # RES 6,(IX+d),E
        0xB4: (23, res_set, 4, (6, '', 0, 'H')),              # RES 6,(IX+d),H
        0xB5: (23, res_set, 4, (6, '', 0, 'L')),              # RES 6,(IX+d),L
        0xB6: (23, res_set, 4, (6, '', 0)),                   # RES 6,(IX+d)
        0xB7: (23, res_set, 4, (6, '', 0, 'A')),              # RES 6,(IX+d),A
        0xB8: (23, res_set, 4, (7, '', 0, 'B')),              # RES 7,(IX+d),B
        0xB9: (23, res_set, 4, (7, '', 0, 'C')),              # RES 7,(IX+d),C
        0xBA: (23, res_set, 4, (7, '', 0, 'D')),              # RES 7,(IX+d),D
        0xBB: (23, res_set, 4, (7, '', 0, 'E')),              # RES 7,(IX+d),E
        0xBC: (23, res_set, 4, (7, '', 0, 'H')),              # RES 7,(IX+d),H
        0xBD: (23, res_set, 4, (7, '', 0, 'L')),              # RES 7,(IX+d),L
        0xBE: (23, res_set, 4, (7, '', 0)),                   # RES 7,(IX+d)
        0xBF: (23, res_set, 4, (7, '', 0, 'A')),              # RES 7,(IX+d),A
        0xC0: (23, res_set, 4, (0, '', 1, 'B')),              # SET 0,(IX+d),B
        0xC1: (23, res_set, 4, (0, '', 1, 'C')),              # SET 0,(IX+d),C
        0xC2: (23, res_set, 4, (0, '', 1, 'D')),              # SET 0,(IX+d),D
        0xC3: (23, res_set, 4, (0, '', 1, 'E')),              # SET 0,(IX+d),E
        0xC4: (23, res_set, 4, (0, '', 1, 'H')),              # SET 0,(IX+d),H
        0xC5: (23, res_set, 4, (0, '', 1, 'L')),              # SET 0,(IX+d),L
        0xC6: (23, res_set, 4, (0, '', 1)),                   # SET 0,(IX+d)
        0xC7: (23, res_set, 4, (0, '', 1, 'A')),              # SET 0,(IX+d),A
        0xC8: (23, res_set, 4, (1, '', 1, 'B')),              # SET 1,(IX+d),B
        0xC9: (23, res_set, 4, (1, '', 1, 'C')),              # SET 1,(IX+d),C
        0xCA: (23, res_set, 4, (1, '', 1, 'D')),              # SET 1,(IX+d),D
        0xCB: (23, res_set, 4, (1, '', 1, 'E')),              # SET 1,(IX+d),E
        0xCC: (23, res_set, 4, (1, '', 1, 'H')),              # SET 1,(IX+d),H
        0xCD: (23, res_set, 4, (1, '', 1, 'L')),              # SET 1,(IX+d),L
        0xCE: (23, res_set, 4, (1, '', 1)),                   # SET 1,(IX+d)
        0xCF: (23, res_set, 4, (1, '', 1, 'A')),              # SET 1,(IX+d),A
        0xD0: (23, res_set, 4, (2, '', 1, 'B')),              # SET 2,(IX+d),B
        0xD1: (23, res_set, 4, (2, '', 1, 'C')),              # SET 2,(IX+d),C
        0xD2: (23, res_set, 4, (2, '', 1, 'D')),              # SET 2,(IX+d),D
        0xD3: (23, res_set, 4, (2, '', 1, 'E')),              # SET 2,(IX+d),E
        0xD4: (23, res_set, 4, (2, '', 1, 'H')),              # SET 2,(IX+d),H
        0xD5: (23, res_set, 4, (2, '', 1, 'L')),              # SET 2,(IX+d),L
        0xD6: (23, res_set, 4, (2, '', 1)),                   # SET 2,(IX+d)
        0xD7: (23, res_set, 4, (2, '', 1, 'A')),              # SET 2,(IX+d),A
        0xD8: (23, res_set, 4, (3, '', 1, 'B')),              # SET 3,(IX+d),B
        0xD9: (23, res_set, 4, (3, '', 1, 'C')),              # SET 3,(IX+d),C
        0xDA: (23, res_set, 4, (3, '', 1, 'D')),              # SET 3,(IX+d),D
        0xDB: (23, res_set, 4, (3, '', 1, 'E')),              # SET 3,(IX+d),E
        0xDC: (23, res_set, 4, (3, '', 1, 'H')),              # SET 3,(IX+d),H
        0xDD: (23, res_set, 4, (3, '', 1, 'L')),              # SET 3,(IX+d),L
        0xDE: (23, res_set, 4, (3, '', 1)),                   # SET 3,(IX+d)
        0xDF: (23, res_set, 4, (3, '', 1, 'A')),              # SET 3,(IX+d),A
        0xE0: (23, res_set, 4, (4, '', 1, 'B')),              # SET 4,(IX+d),B
        0xE1: (23, res_set, 4, (4, '', 1, 'C')),              # SET 4,(IX+d),C
        0xE2: (23, res_set, 4, (4, '', 1, 'D')),              # SET 4,(IX+d),D
        0xE3: (23, res_set, 4, (4, '', 1, 'E')),              # SET 4,(IX+d),E
        0xE4: (23, res_set, 4, (4, '', 1, 'H')),              # SET 4,(IX+d),H
        0xE5: (23, res_set, 4, (4, '', 1, 'L')),              # SET 4,(IX+d),L
        0xE6: (23, res_set, 4, (4, '', 1)),                   # SET 4,(IX+d)
        0xE7: (23, res_set, 4, (4, '', 1, 'A')),              # SET 4,(IX+d),A
        0xE8: (23, res_set, 4, (5, '', 1, 'B')),              # SET 5,(IX+d),B
        0xE9: (23, res_set, 4, (5, '', 1, 'C')),              # SET 5,(IX+d),C
        0xEA: (23, res_set, 4, (5, '', 1, 'D')),              # SET 5,(IX+d),D
        0xEB: (23, res_set, 4, (5, '', 1, 'E')),              # SET 5,(IX+d),E
        0xEC: (23, res_set, 4, (5, '', 1, 'H')),              # SET 5,(IX+d),H
        0xED: (23, res_set, 4, (5, '', 1, 'L')),              # SET 5,(IX+d),L
        0xEE: (23, res_set, 4, (5, '', 1)),                   # SET 5,(IX+d)
        0xEF: (23, res_set, 4, (5, '', 1, 'A')),              # SET 5,(IX+d),A
        0xF0: (23, res_set, 4, (6, '', 1, 'B')),              # SET 6,(IX+d),B
        0xF1: (23, res_set, 4, (6, '', 1, 'C')),              # SET 6,(IX+d),C
        0xF2: (23, res_set, 4, (6, '', 1, 'D')),              # SET 6,(IX+d),D
        0xF3: (23, res_set, 4, (6, '', 1, 'E')),              # SET 6,(IX+d),E
        0xF4: (23, res_set, 4, (6, '', 1, 'H')),              # SET 6,(IX+d),H
        0xF5: (23, res_set, 4, (6, '', 1, 'L')),              # SET 6,(IX+d),L
        0xF6: (23, res_set, 4, (6, '', 1)),                   # SET 6,(IX+d)
        0xF7: (23, res_set, 4, (6, '', 1, 'A')),              # SET 6,(IX+d),A
        0xF8: (23, res_set, 4, (7, '', 1, 'B')),              # SET 7,(IX+d),B
        0xF9: (23, res_set, 4, (7, '', 1, 'C')),              # SET 7,(IX+d),C
        0xFA: (23, res_set, 4, (7, '', 1, 'D')),              # SET 7,(IX+d),D
        0xFB: (23, res_set, 4, (7, '', 1, 'E')),              # SET 7,(IX+d),E
        0xFC: (23, res_set, 4, (7, '', 1, 'H')),              # SET 7,(IX+d),H
        0xFD: (23, res_set, 4, (7, '', 1, 'L')),              # SET 7,(IX+d),L
        0xFE: (23, res_set, 4, (7, '', 1)),                   # SET 7,(IX+d)
        0xFF: (23, res_set, 4, (7, '', 1, 'A'))               # SET 7,(IX+d),A
    }
