from skoolkittest import SkoolKitTestCase
from skoolkit.simulator import (Simulator,
                                A, F, B, C, D, E, H, L, IXh, IXl, IYh, IYl, SP, I, R,
                                xA, xF, xB, xC, xD, xE, xH, xL, PC, T)
from skoolkit.simulator import REGISTERS as SIMULATOR_REGISTERS

REGISTER_NAMES = {v: r for r, v in SIMULATOR_REGISTERS.items()}

REGISTERS = (('B', B), ('C', C), ('D', D), ('E', E), ('H', H), ('L', L), ('(HL)', -1), ('A', A))

REGISTER_PAIRS = (('BC', B, C), ('DE', D, E), ('HL', H, L), ('SP', 0, 0))

INDEX_REGISTERS = ((0xDD, 'IX', IXh, IXl), (0xFD, 'IY', IYh, IYl))

class InTestTracer:
    value = 0

    def read_port(self, registers, port):
        return self.value

class PortTracer:
    def __init__(self, in_value=0):
        self.in_value = in_value
        self.in_ports = []
        self.out_ports = []

    def read_port(self, registers, port):
        self.in_ports.append(port)
        return self.in_value

    def write_port(self, registers, port, value):
        self.out_ports.append((port, value))

class SimulatorTest(SkoolKitTestCase):
    def _test_instruction(self, simulator, inst, data, timing, reg_out=None, sna_out=None,
                          start=None, end=None, state_out=None):
        if start is None:
            start = 65530
        if end is None:
            end = start + len(data)
        d_end = start + len(data)
        if d_end <= 65536:
            simulator.memory[start:d_end] = data
        else:
            wrapped = d_end - 65536
            simulator.memory[start:] = data[:-wrapped]
            simulator.memory[:wrapped] = data[-wrapped:]
        data_hex = ''.join(f'{b:02X}' for b in data)
        exp_reg = {i: r for i, r in enumerate(simulator.registers[:PC])}
        regvals = ', '.join(f'{REGISTER_NAMES[r]}={v}' for r, v in exp_reg.items() if r in REGISTER_NAMES)
        if reg_out is None:
            reg_out = {}
        if R not in reg_out:
            r_in, r_inc = exp_reg[R], 2  if data[0] in (0xCB, 0xDD, 0xED, 0xFD) else 1
            reg_out[R] = (r_in & 0x80) + ((r_in + r_inc) & 0x7F)
        exp_reg.update(reg_out)
        simulator.registers[T] = 0
        simulator.run(start)
        self.assertEqual(simulator.registers[PC], end, f"End address mismatch for '{inst}' ({data_hex}); input: {regvals}")
        self.assertEqual(simulator.registers[T], timing, f"Timing mismatch for '{inst}' ({data_hex}); input: {regvals}")
        actual_reg = {i: r for i, r in enumerate(simulator.registers[:PC])}
        if actual_reg != exp_reg:
            reg_exp = {}
            reg_new = {}
            for r, v in actual_reg.items():
                if exp_reg[r] != v:
                    reg_name = REGISTER_NAMES[r]
                    reg_exp[reg_name] = exp_reg[r]
                    reg_new[reg_name] = v
            self.assertEqual(reg_new, reg_exp, f"Register mismatch for '{inst}' ({data_hex}); input: {regvals}")
        if sna_out:
            actual_memory = {a: simulator.memory[a] for a in sna_out}
            self.assertEqual(actual_memory, sna_out, f"Memory mismatch for '{inst}' ({data_hex}); input: {regvals}")
        if state_out:
            if 'im' in state_out:
                self.assertEqual(simulator.imode, state_out['im'])
            if 'iff' in state_out:
                self.assertEqual(simulator.iff, state_out['iff'])

    def _test_arithmetic(self, op, opcode1, opcode2, *specs):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory

        if op in ('AND', 'CP', 'OR', 'SUB', 'XOR'):
            op_a = op + ' '
        elif op in ('ADC', 'ADD', 'SBC'):
            op_a = op + ' A,'

        for a_in, opval, f_in, a_out, f_out in specs[0]:
            data = (opcode1, opval)
            registers[A] = a_in
            registers[F] = f_in
            reg_out = {A: a_out, F: f_out}
            self._test_instruction(simulator, f'{op_a}${opval:02X}', data, 7, reg_out)

        hl = 49152
        for i, (reg, r) in enumerate(REGISTERS):
            data = [opcode2 + i]
            operation = f'{op_a}{reg}'
            if reg == '(HL)':
                registers[H] = hl // 256
                registers[L] = hl % 256
                for a_in, opval, f_in, a_out, f_out in specs[0]:
                    registers[A] = a_in
                    registers[F] = f_in
                    reg_out = {A: a_out, F: f_out}
                    memory[hl] = opval
                    self._test_instruction(simulator, operation, data, 7, reg_out)
            elif reg == 'A':
                for a_in, f_in, a_out, f_out in specs[1]:
                    registers[A] = a_in
                    registers[F] = f_in
                    reg_out = {A: a_out, F: f_out}
                    self._test_instruction(simulator, operation, data, 4, reg_out)
            else:
                for a_in, opval, f_in, a_out, f_out in specs[0]:
                    registers[A] = a_in
                    registers[F] = f_in
                    registers[r] = opval
                    reg_out = {A: a_out, F: f_out}
                    self._test_instruction(simulator, operation, data, 4, reg_out)

        for prefix, reg, rh, rl in INDEX_REGISTERS:
            for opcode, half, i in ((opcode2 + 4, 'h', 0), (opcode2 + 5, 'l', 1)):
                for a_in, opval, f_in, a_out, f_out in specs[0]:
                    ireg = f'{reg}{half}'
                    operation = f'{op_a}{ireg}'
                    data = (prefix, opcode)
                    registers[A] = a_in
                    registers[F] = f_in
                    registers[(rh, rl)[i]] = opval
                    reg_out = {A: a_out, F: f_out}
                    self._test_instruction(simulator, operation, data, 8, reg_out)

        offset = -2
        for value, (prefix, reg, rh, rl) in enumerate(INDEX_REGISTERS, 32768):
            for a_in, opval, f_in, a_out, f_out in specs[0]:
                operation = f'{op_a}({reg}-${-offset:02X})'
                data = (prefix, opcode2 + 6, offset & 255)
                registers[A] = a_in
                registers[F] = f_in
                registers[rh] = value // 256
                registers[rl] = value % 256
                reg_out = {A: a_out, F: f_out}
                memory[value + offset] = opval
                self._test_instruction(simulator, operation, data, 19, reg_out)

    def _test_res_set(self, op):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory

        if op == 'RES':
            base_opcode = 128
            opval_in = 255
        else:
            base_opcode = 192
            opval_in = 0

        hl = 50000

        for bit in range(8):
            if op == 'RES':
                opval_out = (1 << bit) ^ 255
            else:
                opval_out = 1 << bit

            for i, (reg, r) in enumerate(REGISTERS):
                operation = f'{op} {bit},{reg}'
                data = (203, base_opcode + 8 * bit + i)
                if reg == '(HL)':
                    timing = 15
                    registers[H] = hl // 256
                    registers[L] = hl % 256
                    reg_out = {}
                    memory[hl] = opval_in
                    sna_out = {hl: opval_out}
                else:
                    timing = 8
                    registers[r] = opval_in
                    reg_out = {r: opval_out}
                    sna_out = {}
                self._test_instruction(simulator, operation, data, timing, reg_out, sna_out)

            offset = 4
            for value, (prefix, reg, rh, rl) in enumerate(INDEX_REGISTERS, 32768):
                operation = f'{op} {bit},({reg}+${offset:02X})'
                data = (prefix, 203, offset & 255, base_opcode + 8 * bit + 6)
                registers[rh] = value // 256
                registers[rl] = value % 256
                reg_out = {}
                memory[value + offset] = opval_in
                sna_out = {value + offset: opval_out}
                self._test_instruction(simulator, operation, data, 23, reg_out, sna_out)

    def _test_rotate_shift(self, op, opcode, specs):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory

        hl = 49152
        for i, (reg, r) in enumerate(REGISTERS):
            data = (203, opcode + i)
            operation = f'{op} {reg}'
            if reg == '(HL)':
                registers[H] = hl // 256
                registers[L] = hl % 256
                for r_in, f_in, r_out, f_out in specs:
                    registers[F] = f_in
                    reg_out = {F: f_out}
                    memory[hl] = r_in
                    sna_out = {hl: r_out}
                    self._test_instruction(simulator, operation, data, 15, reg_out, sna_out)
            else:
                for r_in, f_in, r_out, f_out in specs:
                    registers[r] = r_in
                    registers[F] = f_in
                    reg_out = {r: r_out, F: f_out}
                    self._test_instruction(simulator, operation, data, 8, reg_out)

        offset = 1
        for value, (prefix, reg, rh, rl) in enumerate(INDEX_REGISTERS, 32768):
            for r_in, f_in, r_out, f_out in specs:
                operation = f'{op} ({reg}+${offset:02X})'
                data = (prefix, 203, offset & 255, opcode + 6)
                registers[F] = f_in
                registers[rh] = value // 256
                registers[rl] = value % 256
                reg_out = {F: f_out}
                memory[value + offset] = r_in
                sna_out = {value + offset: r_out}
                self._test_instruction(simulator, operation, data, 23, reg_out, sna_out)

    def test_adc_a(self):
        self._test_arithmetic('ADC', 206, 136, (
                # ADC A,r
                # A in, operand value, F in, A out, F out
                #          SZ5H3PNC       SZ5H3PNC
                (1,   2, 0b00000000, 3, 0b00000000),
                (251, 9, 0b00000000, 4, 0b00010001),
                (249, 7, 0b00000000, 0, 0b01010001),
                (1,   2, 0b00000001, 4, 0b00000000),
            ), (
                # ADC A,A
                # A in, F in, A out, F out
                #       SZ5H3PNC         SZ5H3PNC
                (2,   0b00000000, 4,   0b00000000),
                (200, 0b00000000, 144, 0b10010001),
                (128, 0b00000000, 0,   0b01000101),
                (2,   0b00000001, 5,   0b00000000),
                (15,  0b00000000, 30,  0b00011000),
                (15,  0b00000001, 31,  0b00011000),
            )
        )

    def test_add_a(self):
        self._test_arithmetic('ADD', 198, 128, (
                # ADD A,r
                # A in, operand value, F in, A out, F out
                #          SZ5H3PNC       SZ5H3PNC
                (1,   2, 0b00000000, 3, 0b00000000),
                (251, 9, 0b00000000, 4, 0b00010001),
                (249, 7, 0b00000000, 0, 0b01010001),
                (1,   2, 0b00000001, 3, 0b00000000),
            ), (
                # ADD A,A
                # A in, F in, A out, F out
                #       SZ5H3PNC         SZ5H3PNC
                (2,   0b00000000, 4,   0b00000000),
                (200, 0b00000000, 144, 0b10010001),
                (128, 0b00000000, 0,   0b01000101),
                (2,   0b00000001, 4,   0b00000000),
            )
        )

    def test_and(self):
        self._test_arithmetic('AND', 230, 160, (
                # AND r
                # A in, operand value, F in, A out, F out
                #          SZ5H3PNC       SZ5H3PNC
                (1,   3, 0b00000000, 1, 0b00010000),
                (5,   2, 0b00000000, 0, 0b01010100),
                (7,   5, 0b00000001, 5, 0b00010100),
            ), (
                # AND A
                # A in, F in, A out, F out
                #     SZ5H3PNC       SZ5H3PNC
                (2, 0b00000000, 2, 0b00010000),
                (0, 0b00000000, 0, 0b01010100),
                (2, 0b00000001, 2, 0b00010000),
            )
        )

    def test_cp(self):
        self._test_arithmetic('CP', 254, 184, (
                # CP r
                # A in, operand value, F in, A out, F out
                #          SZ5H3PNC         SZ5H3PNC
                (1,   2, 0b00000000, 1,   0b10010011),
                (251, 9, 0b00000000, 251, 0b10001010),
                (7,   7, 0b00000000, 7,   0b01000010),
                (2,   1, 0b00000001, 2,   0b00000010),
            ), (
                # CP A
                # A in, F in, A out, F out
                #       SZ5H3PNC         SZ5H3PNC
                (2,   0b00000000, 2,   0b01000010),
            )
        )

    def test_or(self):
        self._test_arithmetic('OR', 246, 176, (
                # OR r
                # A in, operand value, F in, A out, F out
                #          SZ5H3PNC       SZ5H3PNC
                (1,   3, 0b00000000, 3, 0b00000100),
                (0,   0, 0b00000000, 0, 0b01000100),
                (7,   5, 0b00000001, 7, 0b00000000),
            ), (
                # OR A
                # A in, F in, A out, F out
                #     SZ5H3PNC       SZ5H3PNC
                (2, 0b00000000, 2, 0b00000000),
                (0, 0b00000000, 0, 0b01000100),
                (3, 0b00000001, 3, 0b00000100),
            )
        )

    def test_sbc(self):
        self._test_arithmetic('SBC', 222, 152, (
                # SBC A,r
                # A in, operand value, F in, A out, F out
                #          SZ5H3PNC         SZ5H3PNC
                (1,   2, 0b00000000, 255, 0b10111011),
                (251, 9, 0b00000000, 242, 0b10100010),
                (7,   7, 0b00000000, 0,   0b01000010),
                (2,   1, 0b00000001, 0,   0b01000010),
                (1, 128, 0b00000000, 129, 0b10000111),
            ), (
                # SBC A,A
                # A in, F in, A out, F out
                #       SZ5H3PNC         SZ5H3PNC
                (2,   0b00000000, 0,   0b01000010),
                (200, 0b00000001, 255, 0b10111011),
                (15,  0b00000001, 255, 0b10111011),
            )
        )

    def test_sub(self):
        self._test_arithmetic('SUB', 214, 144, (
                # SUB r
                # A in, operand value, F in, A out, F out
                #          SZ5H3PNC         SZ5H3PNC
                (1,   2, 0b00000000, 255, 0b10111011),
                (251, 9, 0b00000000, 242, 0b10100010),
                (7,   7, 0b00000000, 0,   0b01000010),
                (2,   1, 0b00000001, 1,   0b00000010),
                (1, 128, 0b00000000, 129, 0b10000111),
            ), (
                # SUB A
                # A in, F in, A out, F out
                #       SZ5H3PNC       SZ5H3PNC
                (2,   0b00000000, 0, 0b01000010),
                (200, 0b00000001, 0, 0b01000010),
            )
        )

    def test_xor(self):
        self._test_arithmetic('XOR', 238, 168, (
                # XOR r
                # A in, operand value, F in, A out, F out
                #          SZ5H3PNC       SZ5H3PNC
                (1,   3, 0b00000000, 2, 0b00000000),
                (0,   0, 0b00000000, 0, 0b01000100),
                (7,   5, 0b00000001, 2, 0b00000000),
            ), (
                # XOR A
                # A in, F in, A out, F out
                #     SZ5H3PNC       SZ5H3PNC
                (2, 0b00000000, 0, 0b01000100),
                (3, 0b00000001, 0, 0b01000100),
            )
        )

    def test_bit(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        hl = 50000

        for bit in range(8):
            mask = 1 << bit
            for bitval, opval in ((0, mask ^ 255), (1, mask)):
                for i, (reg, r) in enumerate(REGISTERS):
                    operation = f'BIT {bit},{reg}'
                    data = (203, 64 + 8 * bit + i)
                    f_out = 0b00010000 | (opval & 0b00101000)
                    if bitval:
                        if bit == 7:
                            f_out |= 0b10000000
                    else:
                        f_out |= 0b01000100
                    reg_out = {F: f_out}
                    if reg == '(HL)':
                        timing = 12
                        registers[H] = hl // 256
                        registers[L] = hl % 256
                        memory[hl] = opval
                    else:
                        timing = 8
                        registers[r] = opval
                    self._test_instruction(simulator, operation, data, timing, reg_out)

                offset = 3
                for value, (prefix, reg, rh, rl) in enumerate(INDEX_REGISTERS, 32768):
                    operation = f'BIT {bit},({reg}+${offset:02X})'
                    for opcode in range(0x40 + 8 * bit, 0x48 + 8 * bit):
                        data = (prefix, 0xCB, offset & 255, opcode)
                        registers[rh] = value // 256
                        registers[rl] = value % 256
                        if bitval:
                            f_out = 0b00010000
                            if bit == 7:
                                f_out |= 0b10000000
                        else:
                            f_out = 0b01010100
                        reg_out = {F: f_out}
                        memory[value + offset] = opval
                        self._test_instruction(simulator, operation, data, 20, reg_out)

    def test_res(self):
        self._test_res_set('RES')

    def test_res_with_dest_reg(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        ix = 32768
        at_ix = 255

        for i, (reg, r) in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            for bit in range(8):
                operation = f'RES {bit},(IX+$00),{reg}'
                data = (0xDD, 0xCB, 0x00, 0x80 + 8 * bit + i)
                registers[IXh] = ix // 256
                registers[IXl] = ix % 256
                reg_out = {r: 255 - (1 << bit)}
                memory[ix] = at_ix
                sna_out = {ix: 255 - (1 << bit)}
                self._test_instruction(simulator, operation, data, 23, reg_out, sna_out)

    def test_set(self):
        self._test_res_set('SET')

    def test_set_with_dest_reg(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        ix = 32768
        at_ix = 0

        for i, (reg, r) in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            for bit in range(8):
                operation = f'SET {bit},(IX+$00),{reg}'
                data = (0xDD, 0xCB, 0x00, 0xC0 + 8 * bit + i)
                registers[IXh] = ix // 256
                registers[IXl] = ix % 256
                reg_out = {r: 1 << bit}
                memory[ix] = at_ix
                sna_out = {ix: 1 << bit}
                self._test_instruction(simulator, operation, data, 23, reg_out, sna_out)

    def test_rl(self):
        self._test_rotate_shift('RL', 16, (
            # Operand in, F in, operand out, F out
            #       SZ5H3PNC         SZ5H3PNC
            (64,  0b00000000, 128, 0b10000000),
            (128, 0b00000000, 0,   0b01000101),
            (1,   0b00000001, 3,   0b00000100),
        ))

    def test_rl_with_dest_reg(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        ix = 32768
        at_ix = 35

        for i, (reg, r) in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'RL (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, 0x10 + i)
            registers[IXh] = ix // 256
            registers[IXl] = ix % 256
            registers[F] = 0b00000001
            reg_out = {r: (at_ix << 1) + 1, F: 0b00000100}
            memory[ix] = at_ix
            self._test_instruction(simulator, operation, data, 23, reg_out)

    def test_rlc(self):
        self._test_rotate_shift('RLC', 0, (
            # Operand in, F in, operand out, F out
            #       SZ5H3PNC         SZ5H3PNC
            (64,  0b00000000, 128, 0b10000000),
            (128, 0b00000000, 1,   0b00000001),
            (1,   0b00000001, 2,   0b00000000),
            (0,   0b00000001, 0,   0b01000100),
        ))

    def test_rlc_with_dest_reg(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        ix = 32768
        at_ix = 35

        for i, (reg, r) in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'RLC (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, i)
            registers[IXh] = ix // 256
            registers[IXl] = ix % 256
            registers[F] = 0b00000001
            reg_out = {r: at_ix << 1, F: 0b00000000}
            memory[ix] = at_ix
            self._test_instruction(simulator, operation, data, 23, reg_out)

    def test_rr(self):
        self._test_rotate_shift('RR', 24, (
            # Operand in, F in, operand out, F out
            #     SZ5H3PNC         SZ5H3PNC
            (2, 0b00000000, 1,   0b00000000),
            (1, 0b00000000, 0,   0b01000101),
            (4, 0b00000001, 130, 0b10000100),
        ))

    def test_rr_with_dest_reg(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        ix = 32768
        at_ix = 34

        for i, (reg, r) in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'RR (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, 0x18 + i)
            registers[IXh] = ix // 256
            registers[IXl] = ix % 256
            registers[F] = 0b00000001
            reg_out = {r: 0x80 + (at_ix >> 1), F: 0b10000000}
            memory[ix] = at_ix
            self._test_instruction(simulator, operation, data, 23, reg_out)

    def test_rrc(self):
        self._test_rotate_shift('RRC', 8, (
            # Operand in, F in, operand out, F out
            #     SZ5H3PNC         SZ5H3PNC
            (2, 0b00000000, 1,   0b00000000),
            (1, 0b00000000, 128, 0b10000001),
            (4, 0b00000001, 2,   0b00000000),
            (0, 0b00000001, 0,   0b01000100),
        ))

    def test_rrc_with_dest_reg(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        ix = 32768
        at_ix = 34

        for i, (reg, r) in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'RRC (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, 0x08 + i)
            registers[IXh] = ix // 256
            registers[IXl] = ix % 256
            registers[F] = 0b00000001
            reg_out = {r: at_ix >> 1, F: 0b00000100}
            memory[ix] = at_ix
            self._test_instruction(simulator, operation, data, 23, reg_out)

    def test_sla(self):
        self._test_rotate_shift('SLA', 32, (
            # Operand in, F in, operand out, F out
            #       SZ5H3PNC         SZ5H3PNC
            (64,  0b00000000, 128, 0b10000000),
            (128, 0b00000000, 0,   0b01000101),
            (1,   0b00000001, 2,   0b00000000),
        ))

    def test_sla_with_dest_reg(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        ix = 32768
        at_ix = 35

        for i, (reg, r) in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'SLA (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, 0x20 + i)
            registers[IXh] = ix // 256
            registers[IXl] = ix % 256
            reg_out = {r: at_ix << 1}
            memory[ix] = at_ix
            self._test_instruction(simulator, operation, data, 23, reg_out)

    def test_sll(self):
        self._test_rotate_shift('SLL', 48, (
            # Operand in, F in, operand out, F out
            #       SZ5H3PNC         SZ5H3PNC
            (64,  0b00000000, 129, 0b10000100),
            (128, 0b01000000, 1,   0b00000001),
            (1,   0b00000001, 3,   0b00000100),
        ))

    def test_sll_with_dest_reg(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        ix = 32768
        at_ix = 35

        for i, (reg, r) in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'SLL (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, 0x30 + i)
            registers[IXh] = ix // 256
            registers[IXl] = ix % 256
            reg_out = {r: (at_ix << 1) + 1, F: 0b00000100}
            memory[ix] = at_ix
            self._test_instruction(simulator, operation, data, 23, reg_out)

    def test_sra(self):
        self._test_rotate_shift('SRA', 40, (
            # Operand in, F in, operand out, F out
            #       SZ5H3PNC         SZ5H3PNC
            (2,   0b00000000, 1,   0b00000000),
            (130, 0b00000000, 193, 0b10000000),
            (1,   0b00000000, 0,   0b01000101),
            (129, 0b00000000, 192, 0b10000101),
            (2,   0b00000001, 1,   0b00000000),
        ))

    def test_sra_with_dest_reg(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        ix = 32768
        at_ix = 35

        for i, (reg, r) in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'SRA (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, 0x28 + i)
            registers[IXh] = ix // 256
            registers[IXl] = ix % 256
            reg_out = {r: at_ix >> 1, F: 0b00000101}
            memory[ix] = at_ix
            self._test_instruction(simulator, operation, data, 23, reg_out)

    def test_srl(self):
        self._test_rotate_shift('SRL', 56, (
            # Operand in, F in, operand out, F out
            #     SZ5H3PNC       SZ5H3PNC
            (2, 0b00000000, 1, 0b00000000),
            (1, 0b00000000, 0, 0b01000101),
            (4, 0b00000001, 2, 0b00000000),
        ))

    def test_srl_with_dest_reg(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        ix = 32768
        at_ix = 35

        for i, (reg, r) in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'SRL (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, 0x38 + i)
            registers[IXh] = ix // 256
            registers[IXl] = ix % 256
            reg_out = {r: at_ix >> 1, F: 0b00000101}
            memory[ix] = at_ix
            self._test_instruction(simulator, operation, data, 23, reg_out)

    def test_rla(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers

        for a_in, f_in, a_out, f_out in (
                # A in, F in, A out, F out
                #       SZ5H3PNC         SZ5H3PNC
                (64,  0b00000000, 128, 0b00000000),
                (128, 0b00000000, 0,   0b00000001),
                (1,   0b00000001, 3,   0b00000000),
        ):
            registers[A] = a_in
            registers[F] = f_in
            reg_out = {A: a_out, F: f_out}
            self._test_instruction(simulator, 'RLA', [23], 4, reg_out)

    def test_rlca(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers

        for a_in, f_in, a_out, f_out in (
                # A in, F in, A out, F out
                #       SZ5H3PNC         SZ5H3PNC
                (64,  0b00000000, 128, 0b00000000),
                (128, 0b00000000, 1,   0b00000001),
                (1,   0b00000001, 2,   0b00000000),
                (0,   0b00000001, 0,   0b00000000),
        ):
            registers[A] = a_in
            registers[F] = f_in
            reg_out = {A: a_out, F: f_out}
            self._test_instruction(simulator, 'RLCA', [7], 4, reg_out)

    def test_rra(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers

        for a_in, f_in, a_out, f_out in (
                # A in, F in, A out, F out
                #     SZ5H3PNC         SZ5H3PNC
                (2, 0b00000000, 1,   0b00000000),
                (1, 0b00000000, 0,   0b00000001),
                (4, 0b00000001, 130, 0b00000000),
        ):
            registers[A] = a_in
            registers[F] = f_in
            reg_out = {A: a_out, F: f_out}
            self._test_instruction(simulator, 'RRA', [31], 4, reg_out)

    def test_rrca(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers

        for a_in, f_in, a_out, f_out in (
                # A in, F in, A out, F out
                #     SZ5H3PNC         SZ5H3PNC
                (2, 0b00000000, 1,   0b00000000),
                (1, 0b00000000, 128, 0b00000001),
                (4, 0b00000001, 2,   0b00000000),
                (0, 0b00000001, 0,   0b00000000),
        ):
            registers[A] = a_in
            registers[F] = f_in
            reg_out = {A: a_out, F: f_out}
            self._test_instruction(simulator, 'RRCA', [15], 4, reg_out)

    def _test_inc_dec8(self, op, opcode, specs):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        hl = 49152

        for i, (reg, r) in enumerate(REGISTERS):
            data = [opcode + 8 * i]
            operation = f'{op} {reg}'
            if reg == '(HL)':
                registers[H] = hl // 256
                registers[L] = hl % 256
                for r_in, f_in, r_out, f_out in specs:
                    registers[F] = f_in
                    reg_out = {F: f_out}
                    memory[hl] = r_in
                    sna_out = {hl: r_out}
                    self._test_instruction(simulator, operation, data, 11, reg_out, sna_out)
            else:
                for r_in, f_in, r_out, f_out in specs:
                    registers[r] = r_in
                    registers[F] = f_in
                    reg_out = {r: r_out, F: f_out}
                    self._test_instruction(simulator, operation, data, 4, reg_out)

        for prefix, reg, rh, rl in INDEX_REGISTERS:
            for iopcode, half, i in ((opcode + 32, 'h', 0), (opcode + 40, 'l', 1)):
                for r_in, f_in, r_out, f_out in specs:
                    ireg = f'{reg}{half}'
                    operation = f'{op} {ireg}'
                    data = (prefix, iopcode)
                    registers[F] = f_in
                    ir = (rh, rl)[i]
                    registers[ir] = r_in
                    reg_out = {F: f_out, ir: r_out}
                    self._test_instruction(simulator, operation, data, 8, reg_out)

        offset = 2
        for value, (prefix, reg, rh, rl) in enumerate(INDEX_REGISTERS, 32768):
            for r_in, f_in, r_out, f_out in specs:
                operation = f'{op} ({reg}+${offset:02X})'
                data = (prefix, opcode + 48, offset & 255)
                registers[F] = f_in
                registers[rh] = value // 256
                registers[rl] = value % 256
                reg_out = {F: f_out}
                memory[value + offset] = r_in
                sna_out = {value + offset: r_out}
                self._test_instruction(simulator, operation, data, 23, reg_out, sna_out)

    def test_dec8(self):
        self._test_inc_dec8('DEC', 5, (
            # Operand in, F in, operand out, F out
            #       SZ5H3PNC         SZ5H3PNC
            (128, 0b00000000, 127, 0b00111110),
            (2,   0b00000000, 1,   0b00000010),
            (1,   0b00000000, 0,   0b01000010),
            (0,   0b00000000, 255, 0b10111010),
            (0,   0b00000001, 255, 0b10111011),
        ))

    def test_inc8(self):
        self._test_inc_dec8('INC', 4, (
            # Operand in, F in, operand out, F out
            #       SZ5H3PNC         SZ5H3PNC
            (127, 0b00000000, 128, 0b10010100),
            (254, 0b00000000, 255, 0b10101000),
            (255, 0b00000000, 0,   0b01010000),
            (0,   0b00000000, 1,   0b00000000),
            (0,   0b00000001, 1,   0b00000001),
        ))

    def test_dec16(self):
        # DEC BC/DE/HL/SP/IX/IY
        simulator = Simulator([0] * 65536)
        registers = simulator.registers

        for rr_in, rr_out in ((61276, 61275), (0, 65535)):
            for i, (reg, rh, rl) in enumerate(REGISTER_PAIRS):
                operation = f'DEC {reg}'
                data = [11 + i * 16]
                if reg == 'SP':
                    registers[SP] = rr_in
                    reg_out = {SP: rr_out}
                else:
                    registers[rh] = rr_in // 256
                    registers[rl] = rr_in % 256
                    reg_out = {rh: rr_out // 256, rl: rr_out % 256}
                self._test_instruction(simulator, operation, data, 6, reg_out)

        for rr_in, rr_out in ((61276, 61275), (0, 65535)):
            for prefix, reg, rh, rl in INDEX_REGISTERS:
                operation = f'DEC {reg}'
                data = (prefix, 43)
                registers[rh] = rr_in // 256
                registers[rl] = rr_in % 256
                reg_out = {rl: rr_out % 256, rh: rr_out // 256}
                self._test_instruction(simulator, operation, data, 10, reg_out)

    def test_inc16(self):
        # INC BC/DE/HL/SP/IX/IY
        simulator = Simulator([0] * 65536)
        registers = simulator.registers

        for rr_in, rr_out in ((61275, 61276), (65535, 0)):
            for i, (reg, rh, rl) in enumerate(REGISTER_PAIRS):
                operation = f'INC {reg}'
                data = [3 + i * 16]
                if reg == 'SP':
                    registers[SP] = rr_in
                    reg_out = {SP: rr_out}
                else:
                    registers[rh] = rr_in // 256
                    registers[rl] = rr_in % 256
                    reg_out = {rh: rr_out // 256, rl: rr_out % 256}
                self._test_instruction(simulator, operation, data, 6, reg_out)

        for rr_in, rr_out in ((61275, 61276), (65535, 0)):
            for prefix, reg, rh, rl in INDEX_REGISTERS:
                operation = f'INC {reg}'
                data = (prefix, 35)
                registers[rh] = rr_in // 256
                registers[rl] = rr_in % 256
                reg_out = {rl: rr_out % 256, rh: rr_out // 256}
                self._test_instruction(simulator, operation, data, 10, reg_out)

    def test_add16(self):
        # ADD HL/IX/IY,BC/DE/HL/SP/IX/IY
        simulator = Simulator([0] * 65536)
        registers = simulator.registers

        for r1, r2, f_out, f_out_hl in (
                #                SZ5H3PNC    SZ5H3PNC
                (3, 1056,      0b00000000, 0b00000000),
                (32887, 45172, 0b00100001, 0b00000001)
        ):
            for i, (reg, rh, rl) in enumerate(REGISTER_PAIRS):
                operation = f'ADD HL,{reg}'
                data = [9 + i * 16]
                registers[H] = r1 // 256
                registers[L] = r1 % 256
                registers[F] = 0b00000001
                if reg == 'HL':
                    s = r1 * 2
                    reg_out = {F: f_out_hl}
                else:
                    s = r1 + r2
                    if reg == 'SP':
                        registers[SP] = r2
                    else:
                        registers[rh] = r2 // 256
                        registers[rl] = r2 % 256
                    reg_out = {F: f_out}
                s &= 0xFFFF
                reg_out.update({H: s // 256, L: s % 256})
                self._test_instruction(simulator, operation, data, 11, reg_out)

            for prefix, reg, rh, rl in INDEX_REGISTERS:
                for i, (rr, rrh, rrl) in enumerate(REGISTER_PAIRS):
                    if rr == 'HL':
                        rr = reg
                    operation = f'ADD {reg},{rr}'
                    data = [prefix, 9 + i * 16]
                    registers[F] = 0b00000001
                    registers[rh] = r1 // 256
                    registers[rl] = r1 % 256
                    if rr == reg:
                        s = r1 * 2
                        reg_out = {F: f_out_hl}
                    else:
                        s = r1 + r2
                        if rr == 'SP':
                            registers[SP] = r2
                        else:
                            registers[rrh] = r2 // 256
                            registers[rrl] = r2 % 256
                        reg_out = {F: f_out}
                    s &= 0xFFFF
                    reg_out.update({rh: s // 256, rl: s % 256})
                    self._test_instruction(simulator, operation, data, 15, reg_out)

    def test_adc16(self):
        # ADC HL,BC/DE/HL/SP
        simulator = Simulator([0] * 65536)
        registers = simulator.registers

        for r1, r2, f_in, f_out, f_out_hl in (
                #                SZ5H3PNC    SZ5H3PNC    SZ5H3PNC
                (3, 1056,      0b00000000, 0b00000000, 0b00000000),
                (3, 1056,      0b00000001, 0b00000000, 0b00000000),
                (32887, 45172, 0b00000000, 0b00100101, 0b00000101),
                (32887, 45172, 0b00000001, 0b00100101, 0b00000101),
                (2048, 2048,   0b00000001, 0b00010000, 0b00010000),
                (16384, 16384, 0b00000001, 0b10000100, 0b10000100),
                (32768, 32768, 0b00000000, 0b01000101, 0b01000101)
        ):
            for i, (reg, rh, rl) in enumerate(REGISTER_PAIRS):
                operation = f'ADC HL,{reg}'
                data = (237, 74 + i * 16)
                registers[H] = r1 // 256
                registers[L] = r1 % 256
                registers[F] = f_in
                carry = f_in & 1
                if reg == 'HL':
                    s = r1 * 2 + carry
                    reg_out = {F: f_out_hl}
                else:
                    s = r1 + r2 + carry
                    if reg == 'SP':
                        registers[SP] = r2
                    else:
                        registers[rh] = r2 // 256
                        registers[rl] = r2 % 256
                    reg_out = {F: f_out}
                s &= 0xFFFF
                reg_out.update({H: s // 256, L: s % 256})
                self._test_instruction(simulator, operation, data, 15, reg_out)

    def test_sbc16(self):
        # SBC HL,BC/DE/HL/SP
        simulator = Simulator([0] * 65536)
        registers = simulator.registers

        for r1, r2, f_in, f_out, f_out_hl in (
                #                SZ5H3PNC    SZ5H3PNC    SZ5H3PNC
                (1056, 3,      0b00000000, 0b00000010, 0b01000010),
                (1056, 3,      0b00000001, 0b00000010, 0b10111011),
                (45172, 32887, 0b00000000, 0b00111010, 0b01000010),
                (45172, 32887, 0b00000001, 0b00111010, 0b10111011),
                (1, 32768,     0b00000000, 0b10000111, 0b01000010)
        ):
            for i, (reg, rh, rl) in enumerate(REGISTER_PAIRS):
                operation = f'SBC HL,{reg}'
                data = (237, 66 + i * 16)
                registers[H] = r1 // 256
                registers[L] = r1 % 256
                registers[F] = f_in
                carry = f_in & 1
                if reg == 'HL':
                    d = -carry & 65535
                    reg_out = {F: f_out_hl}
                else:
                    if reg == 'SP':
                        registers[SP] = r2
                    else:
                        registers[rh] = r2 // 256
                        registers[rl] = r2 % 256
                    d = (r1 - r2 - carry) & 65535
                    reg_out = {F: f_out}
                reg_out.update({H: d // 256, L: d % 256})
                self._test_instruction(simulator, operation, data, 15, reg_out)

    def test_ld_r_n(self):
        # LD r,n (r: A, B, C, D, E, H, L, (HL))
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        hl = 49152

        for i, (reg, r) in enumerate(REGISTERS):
            data = (6 + 8 * i, i)
            if reg == '(HL)':
                registers[H] = hl // 256
                registers[L] = hl % 256
                reg_out = {'H': hl // 256, 'L': hl % 256}
                memory[hl] = 255
                sna_out = {hl: i}
                self._test_instruction(simulator, f'LD {reg},${i:02X}', data, 10, reg_out, sna_out)
            else:
                registers[r] = 255
                reg_out = {r: i}
                self._test_instruction(simulator, f'LD {reg},${i:02X}', data, 7, reg_out)

    def test_ld_r_r(self):
        # LD r,r (r: A, B, C, D, E, H, L, (HL))
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        hl = 32768
        v1, v2 = 12, 56

        for i, (reg1, r1) in enumerate(REGISTERS):
            for j, (reg2, r2) in enumerate(REGISTERS):
                if reg1 == '(HL)' and reg2 == '(HL)':
                    continue
                data = [64 + 8 * i + j]
                if reg1 == '(HL)':
                    operation = f'LD (HL),{reg2}'
                    registers[H] = hl // 256
                    registers[L] = hl % 256
                    if r2 in (H, L):
                        v2 = registers[r2]
                    else:
                        registers[r2] = v2
                    memory[hl] = v1
                    reg_out = {H: hl // 256, L: hl % 256}
                    sna_out = {hl: v2}
                    self._test_instruction(simulator, operation, data, 7, reg_out, sna_out)
                elif reg2 == '(HL)':
                    operation = f'LD {reg1},(HL)'
                    registers[H] = hl // 256
                    registers[L] = hl % 256
                    if r1 not in (H, L):
                        registers[r1] = v1
                    memory[hl] = v2
                    reg_out = {r1: v2}
                    self._test_instruction(simulator, operation, data, 7, reg_out)
                else:
                    operation = f'LD {reg1},{reg2}'
                    registers[r1] = v1
                    registers[r2] = v2
                    reg_out = {r1: v2, r2: v2}
                    self._test_instruction(simulator, operation, data, 4, reg_out)

    def test_ld_r_n_with_ix_iy_halves(self):
        # LD r,n (r: IXh, IXl, IYh, IYl)
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        r_in, r_out = 37, 85

        for prefix, reg, rh, rl in INDEX_REGISTERS:
            for opcode, half, i in ((38, 'h', 0), (46, 'l', 1)):
                data = (prefix, opcode, r_out)
                ireg = f'{reg}{half}'
                operation = f'LD {ireg},${r_out:02X}'
                ir = (rh, rl)[i]
                registers[ir] = r_in
                reg_out = {ir: r_out}
                self._test_instruction(simulator, operation, data, 11, reg_out)

    def test_ld_r_r_with_ix_iy_halves(self):
        # LD r1,r2 (r1 or r2: IXh, IXl, IYh, IYl)
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        v1, v2 = 27, 99
        lookup = (B, C, D, E, H, L, None, A)

        for reg1, reg2 in (
                (A, H), (A, L), (H, A), (L, A),
                (B, H), (B, L), (H, B), (L, B),
                (C, H), (C, L), (H, C), (L, C),
                (D, H), (D, L), (H, D), (L, D),
                (E, H), (E, L), (H, E), (L, E),
                (H, H), (H, L), (H, H), (L, H),
                (L, H), (L, L), (H, L), (L, L),
        ):
            for prefix, reg, rh, rl in INDEX_REGISTERS:
                i = lookup.index(reg1)
                j = lookup.index(reg2)
                data = [prefix, 64 + 8 * i + j]
                if reg1 == H:
                    op1 = reg + 'h'
                    op1r = rh
                    registers[rh] = v1
                elif reg1 == L:
                    op1 = reg + 'l'
                    op1r = rl
                    registers[rl] = v1
                else:
                    op1 = REGISTER_NAMES[reg1]
                    op1r = reg1
                    registers[reg1] = v1
                if reg2 == H:
                    op2 = reg + 'h'
                    op2r = rh
                    registers[rh] = v2
                elif reg2 == L:
                    op2 = reg + 'l'
                    op2r = rl
                    registers[rl] = v2
                else:
                    op2 = REGISTER_NAMES[reg2]
                    op2r = reg2
                    registers[reg2] = v2
                reg_out = {op1r: v2, op2r: v2}
                operation = f'LD {op1},{op2}'
                self._test_instruction(simulator, operation, data, 8, reg_out)

    def test_ld_r_with_ix_iy_offsets(self):
        # LD r,(i+d); LD (i+d),r (i: IX, IY; r: A, B, C, D, E, H, L)
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        offset = 5
        r1, r2 = 14, 207

        for value, (prefix, reg, rh, rl) in enumerate(INDEX_REGISTERS, 32768):
            for i, (r8, r) in enumerate(REGISTERS):
                if r8 == '(HL)':
                    continue
                operation = f'LD {r8},({reg}+${offset:02X})'
                data = (prefix, 0x46 + 8 * i, offset)
                registers[r] = r1
                registers[rh] = value // 256
                registers[rl] = value % 256
                reg_out = {r: r2}
                memory[value + offset] = r2
                self._test_instruction(simulator, operation, data, 19, reg_out)

        offset = -3
        r1, r2 = 142, 27
        for value, (prefix, reg, rh, rl) in enumerate(INDEX_REGISTERS, 32768):
            for i, (r8, r) in enumerate(REGISTERS):
                if r8 == '(HL)':
                    continue
                operation = f'LD ({reg}+${offset:02X}),{r8}'
                data = (prefix, 0x70 + i, offset & 255)
                registers[r] = r2
                registers[rh] = value // 256
                registers[rl] = value % 256
                reg_out = {r: r2}
                memory[value + offset] = r1
                sna_out = {value + offset: r2}
                self._test_instruction(simulator, operation, data, 19, reg_out, sna_out)

    def test_ld_r_with_ix_iy_offsets_across_64K_boundary(self):
        # LD r,(i+d); LD (i+d),r (i: IX, IY; r: A, B, C, D, E, H, L)
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        r1, r2 = 14, 207

        for prefix, reg, rh, rl in INDEX_REGISTERS:
            for value, offset in ((65535, 2), (0, -2)):
                for i, (r8, r) in enumerate(REGISTERS):
                    if r8 == '(HL)':
                        continue
                    if offset < 0:
                        operand = offset + 256
                        operation = f'LD {r8},({reg}-${-offset:02X})'
                    else:
                        operand = offset
                        operation = f'LD {r8},({reg}+${offset:02X})'
                    data = (prefix, 0x46 + 8 * i, operand)
                    registers[r] = r1
                    registers[rh] = value // 256
                    registers[rl] = value % 256
                    reg_out = {r: r2}
                    memory[(value + offset) & 0xFFFF] = r2
                    self._test_instruction(simulator, operation, data, 19, reg_out)

    def test_ld_ix_iy_d_n(self):
        # LD (IX+d),n; LD (IY+d),n
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        offset, n = 7, 21

        for value, (prefix, reg, rh, rl) in enumerate(INDEX_REGISTERS, 32768):
            operation = f'LD ({reg}+${offset:02X}),${n:02X}'
            data = (prefix, 0x36, offset & 255, n)
            registers[rh] = value // 256
            registers[rl] = value % 256
            reg_out = {}
            memory[value + offset] = 255
            sna_out = {value + offset: n}
            self._test_instruction(simulator, operation, data, 19, reg_out, sna_out)

    def test_ld_a_addr(self):
        # LD (nn),A; LD A,(nn)
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        a, addr, n = 5, 41278, 17

        operation = f'LD (${addr:04X}),A'
        data = (50, addr % 256, addr // 256)
        registers[A] = a
        reg_out = {A: a}
        memory[addr] = n
        sna_out = {addr: a}
        self._test_instruction(simulator, operation, data, 13, reg_out, sna_out)

        operation = f'LD A,(${addr:04X})'
        data = (58, addr % 256, addr // 256)
        registers[A] = a
        reg_out = {A: n}
        memory[addr] = n
        sna_out = {addr: n}
        self._test_instruction(simulator, operation, data, 13, reg_out, sna_out)

    def test_ld_a_bc_de(self):
        # LD A,(BC); LD (BC),A; LD A,(DE); LD (DE),A
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        r1, r2, rr = 39, 102, 30000

        for opcode, reg1, reg2, rh, rl in (
                (2, '(BC)', 'A', B, C),
                (10, 'A', '(BC)', B, C),
                (18, '(DE)', 'A', D, E),
                (26, 'A', '(DE)', D, E),
        ):
            operation = f'LD {reg1},{reg2}'
            data = [opcode]
            if reg1 == 'A':
                registers[A] = r1
                registers[rh] = rr // 256
                registers[rl] = rr % 256
                reg_out = {A: r2}
                memory[rr] = r2
                sna_out = {}
            else:
                registers[A] = r2
                registers[rh] = rr // 256
                registers[rl] = rr % 256
                reg_out = {A: r2, rh: rr // 256, rl: rr % 256}
                memory[rr] = r1
                sna_out = {rr: r2}
            self._test_instruction(simulator, operation, data, 7, reg_out, sna_out)

    def test_ld_a_i(self):
        # LD A,I
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        a = 29
        data = (237, 87)

        for i_in, f_in, f_out in (
                # I     SZ5H3PNC    SZ5H3PNC
                (128, 0b00010110, 0b10000000),
                (0,   0b00000100, 0b01000000),
        ):
            operation = 'LD A,I'
            registers[A] = a
            registers[F] = f_in
            registers[I] = i_in
            reg_out = {A: i_in, F: f_out}
            self._test_instruction(simulator, operation, data, 9, reg_out)

    def test_ld_a_r(self):
        # LD A,R
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        a = 29
        data = (237, 95)

        for r_in, r_out, f_in, f_out in (
                #            SZ5H3PNC    SZ5H3PNC
                (126, 0,   0b10010110, 0b01000000),
                (128, 130, 0b00010110, 0b10000000),
                (254, 128, 0b00000100, 0b10000000),
        ):
            operation = 'LD A,R'
            registers[A] = a
            registers[F] = f_in
            registers[R] = r_in
            reg_out = {A: r_out, F: f_out}
            self._test_instruction(simulator, operation, data, 9, reg_out)

    def test_ld_special_a(self):
        # LD I,A; LD R,A
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        r, a = 2, 99

        for opcode, reg, ri in (
                (71, 'I', I),
                (79, 'R', R)
        ):
            operation = f'LD {reg},A'
            data = (237, opcode)
            registers[ri] = r
            registers[A] = a
            reg_out = {ri: a}
            self._test_instruction(simulator, operation, data, 9, reg_out)

    def test_ld_rr_nn(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        lsb, msb = 3, 6

        for i, (reg, rh, rl) in enumerate(REGISTER_PAIRS):
            operation = f'LD {reg},${lsb + 256 * msb:04X}'
            data = (1 + i * 16, lsb, msb)
            if reg == 'SP':
                registers[SP] = 0
                reg_out = {SP: lsb + 256 * msb}
            else:
                registers[rh] = 0
                registers[rl] = 0
                reg_out = {rl: lsb, rh: msb}
            self._test_instruction(simulator, operation, data, 10, reg_out)

        for prefix, reg, rh, rl in INDEX_REGISTERS:
            operation = f'LD {reg},${lsb + 256 * msb:04X}'
            data = (prefix, 33, lsb, msb)
            registers[rh] = 0
            registers[rl] = 0
            reg_out = {rl: lsb, rh: msb}
            self._test_instruction(simulator, operation, data, 14, reg_out)

    def test_ld_addr_rr(self):
        # LD (nn),BC/DE/HL/SP/IX/IY
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        rr, addr, nn = 35622, 52451, 257

        for opcodes, reg, rh, rl, timing in (
                ((237, 67), 'BC', B, C, 20),
                ((237, 83), 'DE', D, E, 20),
                ((34,), 'HL', H, L, 16),
                ((237, 115), 'SP', 0, 0, 20)
        ):
            operation = f'LD (${addr:04X}),{reg}'
            data = opcodes + (addr % 256, addr // 256)
            if reg == 'SP':
                registers[SP] = rr
            else:
                registers[rh] = rr // 256
                registers[rl] = rr % 256
            reg_out = {}
            memory[addr:addr + 2] = (nn % 256, nn // 256)
            sna_out = {addr: rr % 256, addr + 1: rr // 256}
            self._test_instruction(simulator, operation, data, timing, reg_out, sna_out)

        for prefix, reg, rh, rl in INDEX_REGISTERS:
            operation = f'LD (${addr:04X}),{reg}'
            data = (prefix, 34, addr % 256, addr // 256)
            registers[rh] = rr // 256
            registers[rl] = rr % 256
            reg_out = {}
            memory[addr:addr + 2] = (nn % 256, nn // 256)
            sna_out = {addr: rr % 256, addr + 1: rr // 256}
            self._test_instruction(simulator, operation, data, 20, reg_out, sna_out)

    def test_ld_rr_addr(self):
        # LD BC/DE/HL/SP/IX/IY,(nn)
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        rr, addr, nn = 35622, 52451, 41783

        for opcodes, reg, rh, rl, timing in (
                ((237, 75), 'BC', B, C, 20),
                ((237, 91), 'DE', D, E, 20),
                ((42,), 'HL', H, L, 16),
                ((237, 123), 'SP', 0, 0, 20)
        ):
            operation = f'LD {reg},(${addr:04X})'
            data = opcodes + (addr % 256, addr // 256)
            if reg == 'SP':
                registers[SP] = rr
                reg_out = {SP: nn}
            else:
                registers[rh] = rr // 256
                registers[rl] = rr % 256
                reg_out = {rh: nn // 256, rl: nn % 256}
            memory[addr:addr + 2] = (nn % 256, nn // 256)
            self._test_instruction(simulator, operation, data, timing, reg_out)

        for prefix, reg, rh, rl in INDEX_REGISTERS:
            operation = f'LD {reg},(${addr:04X})'
            data = (prefix, 42, addr % 256, addr // 256)
            registers[rh] = rr // 256
            registers[rl] = rr % 256
            reg_out = {rl: nn % 256, rh: nn // 256}
            memory[addr:addr + 2] = (nn % 256, nn // 256)
            self._test_instruction(simulator, operation, data, 20, reg_out)

    def test_ld_sp_rr(self):
        # LD SP,HL/IX/IY
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        sp, rr = 0, 55731

        operation = 'LD SP,HL'
        data = [249]
        registers[SP] = sp
        registers[H] = rr // 256
        registers[L] = rr % 256
        reg_out = {SP: rr}
        self._test_instruction(simulator, operation, data, 6, reg_out)

        for prefix, reg, rh, rl in INDEX_REGISTERS:
            operation = f'LD SP,{reg}'
            data = (prefix, 249)
            registers[SP] = sp
            registers[rh] = rr // 256
            registers[rl] = rr % 256
            reg_out = {SP: rr}
            self._test_instruction(simulator, operation, data, 10, reg_out)

    def test_pop(self):
        # POP BC/DE/HL/AF/IX/IY
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        sp = 49152

        r_in, r_out = 257, 51421
        for i, (reg, rh, rl) in enumerate((('BC', B, C), ('DE', D, E), ('HL', H, L), ('AF', A, F))):
            operation = f'POP {reg}'
            data = [193 + 16 * i]
            registers[rh] = r_in // 256
            registers[rl] = r_in % 256
            registers[SP] = sp
            reg_out = {rl: r_out % 256, rh: r_out // 256, SP: sp + 2}
            memory[sp:sp + 2] = (r_out % 256, r_out // 256)
            self._test_instruction(simulator, operation, data, 10, reg_out)

        for prefix, reg, rh, rl in INDEX_REGISTERS:
            operation = f'POP {reg}'
            data = (prefix, 225)
            registers[rh] = r_in // 256
            registers[rl] = r_in % 256
            registers[SP] = sp
            reg_out = {rh: r_out // 256, rl: r_out % 256, SP: sp + 2}
            memory[sp:sp + 2] = (r_out % 256, r_out // 256)
            self._test_instruction(simulator, operation, data, 14, reg_out)

    def test_push(self):
        # PUSH BC/DE/HL/AF/IX/IY
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        sp = 49152

        r_in, r_out = 257, 51421
        for i, (reg, rh, rl) in enumerate((('BC', B, C), ('DE', D, E), ('HL', H, L), ('AF', A, F))):
            operation = f'PUSH {reg}'
            data = [197 + 16 * i]
            registers[rh] = r_in // 256
            registers[rl] = r_in % 256
            registers[SP] = sp
            reg_out = {SP: sp - 2}
            memory[sp - 2:sp] = (r_out % 256, r_out // 256)
            sna_out = {sp - 1: r_in // 256, sp - 2: r_in % 256}
            self._test_instruction(simulator, operation, data, 11, reg_out, sna_out)

        for prefix, reg, rh, rl in INDEX_REGISTERS:
            operation = f'PUSH {reg}'
            data = (prefix, 229)
            registers[rh] = r_in // 256
            registers[rl] = r_in % 256
            registers[SP] = sp
            reg_out = {SP: sp - 2}
            memory[sp - 2:sp] = (r_out % 256, r_out // 256)
            sna_out = {sp - 1: r_in // 256, sp - 2: r_in % 256}
            self._test_instruction(simulator, operation, data, 15, reg_out, sna_out)

    def test_jp_rr(self):
        # JP (HL/IX/IY)
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        addr = 46327

        for prefix, reg, rh, rl in ((0, 'HL', H, L), (0xDD, 'IX', IXh, IXl), (0xFD, 'IY', IYh, IYl)):
            operation = f'JP ({reg})'
            if prefix:
                data = (prefix, 233)
                timing = 8
            else:
                data = [233]
                timing = 4
            registers[rh] = addr // 256
            registers[rl] = addr % 256
            self._test_instruction(simulator, operation, data, timing, end=addr)

    def test_jr_nn(self):
        simulator = Simulator([0] * 65536)
        start = 30000

        for offset in (13, -45):
            addr = start + 2 + offset
            operation = f'JR ${addr:04X}'
            data = (24, offset if offset >= 0 else offset + 256)
            self._test_instruction(simulator, operation, data, 12, start=start, end=addr)

    def test_jr_conditional(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        start = 30000

        for offset in (13, -45):
            addr = start + 2 + offset
            for opcode, condition, flags, end in (
                    #            SZ5H3PNC
                    (32, 'NZ', 0b00000000, addr),
                    (32, 'NZ', 0b01000000, start + 2),
                    (40, 'Z',  0b00000000, start + 2),
                    (40, 'Z',  0b01000000, addr),
                    (48, 'NC', 0b00000000, addr),
                    (48, 'NC', 0b00000001, start + 2),
                    (56, 'C',  0b00000000, start + 2),
                    (56, 'C',  0b00000001, addr)
            ):
                operation = f'JR {condition},${addr:04X}'
                data = (opcode, offset if offset >= 0 else offset + 256)
                timing = 12 if end == addr else 7
                registers[F] = flags
                self._test_instruction(simulator, operation, data, timing, start=start, end=end)

    def test_jr_jumping_across_64K_boundary(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers

        for start, opcode, condition, flags, offset, end in (
                #                   SZ5H3PNC
                (65526, 24, '',   0b00000000,  12, 4),     # $FFF6 JR $0004
                (65528, 32, 'NZ', 0b00000000,  12, 6),     # $FFF8 JR NZ,$0006
                (65530, 40, 'Z',  0b01000000,  12, 8),     # $FFFA JR Z,$0008
                (65532, 48, 'NC', 0b00000000,  12, 10),    # $FFFC JR NC,$000A
                (65534, 56, 'C',  0b00000001,  12, 12),    # $FFFE JR C,$000C
                (0,     24, '',   0b00000000, -12, 65526), # $0000 JR $FFF6
                (2,     32, 'NZ', 0b00000000, -12, 65528), # $0002 JR NZ,$FFF8
                (4,     40, 'Z',  0b01000000, -12, 65530), # $0004 JR Z,$FFFA
                (6,     48, 'NC', 0b00000000, -12, 65532), # $0006 JR NC,$FFFC
                (8,     56, 'C',  0b00000001, -12, 65534), # $0008 JR C,$FFFE
        ):
            if condition:
                operation = f'JR {condition},${end:04X}'
            else:
                operation = f'JR ${end:04X}'
            data = (opcode, offset if offset >= 0 else offset + 256)
            timing = 12
            registers[F] = flags
            self._test_instruction(simulator, operation, data, timing, start=start, end=end)

    def test_call_nn(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        start = 30000
        addr = 51426
        sp = 23456
        operation = f'CALL ${addr:04X}'
        data = (205, addr % 256, addr // 256)
        registers[SP] = sp
        reg_out = {SP: sp - 2}
        sna_out = {sp - 1: (start + 3) // 256, sp - 2: (start + 3) % 256}
        self._test_instruction(simulator, operation, data, 17, reg_out, sna_out, start=start, end=addr)

    def test_call_nn_overwriting_its_operand(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        start = 30000
        addr = 51426
        sp = start + 3
        operation = f'CALL ${addr:04X}'
        data = (205, addr % 256, addr // 256)
        registers[SP] = sp
        reg_out = {SP: sp - 2}
        sna_out = {sp - 1: (start + 3) // 256, sp - 2: (start + 3) % 256}
        self._test_instruction(simulator, operation, data, 17, reg_out, sna_out, start=start, end=addr)

    def test_call_conditional(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        start = 40000
        addr = 45271
        sp = 23456

        for opcode, condition, flags, end in (
                #             SZ5H3PNC
                (196, 'NZ', 0b00000000, addr),
                (196, 'NZ', 0b01000000, start + 3),
                (204, 'Z',  0b00000000, start + 3),
                (204, 'Z',  0b01000000, addr),
                (212, 'NC', 0b00000000, addr),
                (212, 'NC', 0b00000001, start + 3),
                (220, 'C',  0b00000000, start + 3),
                (220, 'C',  0b00000001, addr),
                (228, 'PO', 0b00000000, addr),
                (228, 'PO', 0b00000100, start + 3),
                (236, 'PE', 0b00000000, start + 3),
                (236, 'PE', 0b00000100, addr),
                (244, 'P',  0b00000000, addr),
                (244, 'P',  0b10000000, start + 3),
                (252, 'M',  0b00000000, start + 3),
                (252, 'M',  0b10000000, addr),
        ):
            operation = f'CALL {condition},${addr:04X}'
            registers[F] = flags
            registers[SP] = sp
            if end == addr:
                timing = 17
                reg_out = {SP: sp - 2}
                sna_out = {sp - 1: (start + 3) // 256, sp - 2: (start + 3) % 256}
            else:
                timing = 10
                reg_out = None
                sna_out = None
            data = (opcode, addr % 256, addr // 256)
            self._test_instruction(simulator, operation, data, timing, reg_out, sna_out, start=start, end=end)

    def test_call_conditional_overwriting_its_operand(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        start = 40000
        addr = 45271
        sp = start + 3

        for opcode, condition, flags in (
                #             SZ5H3PNC
                (196, 'NZ', 0b00000000),
                (204, 'Z',  0b01000000),
                (212, 'NC', 0b00000000),
                (220, 'C',  0b00000001),
                (228, 'PO', 0b00000000),
                (236, 'PE', 0b00000100),
                (244, 'P',  0b00000000),
                (252, 'M',  0b10000000),
        ):
            operation = f'CALL {condition},${addr:04X}'
            registers[F] = flags
            registers[SP] = sp
            reg_out = {SP: sp - 2}
            sna_out = {sp - 1: (start + 3) // 256, sp - 2: (start + 3) % 256}
            data = (opcode, addr % 256, addr // 256)
            self._test_instruction(simulator, operation, data, 17, reg_out, sna_out, start=start, end=addr)

    def test_jp_nn(self):
        simulator = Simulator([0] * 65536)
        start = 30000
        addr = 51426
        operation = f'JP ${addr:04X}'
        data = (195, addr % 256, addr // 256)
        self._test_instruction(simulator, operation, data, 10, start=start, end=addr)

    def test_jp_conditional(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        start = 40000
        addr = 45271

        for opcode, condition, flags, end in (
                #             SZ5H3PNC
                (194, 'NZ', 0b00000000, addr),
                (194, 'NZ', 0b01000000, start + 3),
                (202, 'Z',  0b00000000, start + 3),
                (202, 'Z',  0b01000000, addr),
                (210, 'NC', 0b00000000, addr),
                (210, 'NC', 0b00000001, start + 3),
                (218, 'C',  0b00000000, start + 3),
                (218, 'C',  0b00000001, addr),
                (226, 'PO', 0b00000000, addr),
                (226, 'PO', 0b00000100, start + 3),
                (234, 'PE', 0b00000000, start + 3),
                (234, 'PE', 0b00000100, addr),
                (242, 'P',  0b00000000, addr),
                (242, 'P',  0b10000000, start + 3),
                (250, 'M',  0b00000000, start + 3),
                (250, 'M',  0b10000000, addr),
        ):
            operation = f'JP {condition},${addr:04X}'
            registers[F] = flags
            data = (opcode, addr % 256, addr // 256)
            self._test_instruction(simulator, operation, data, 10, start=start, end=end)

    def test_ret(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        start = 40000
        end = 45271
        sp = 32517
        operation = 'RET'
        data = [201]
        registers[SP] = sp
        reg_out = {SP: sp + 2}
        memory[sp:sp + 2] = (end % 256, end // 256)
        self._test_instruction(simulator, operation, data, 10, reg_out, start=start, end=end)

    def test_ret_conditional(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        start = 40000
        addr = 45271
        sp = 32517

        for opcode, condition, flags, end in (
                #             SZ5H3PNC
                (192, 'NZ', 0b00000000, addr),
                (192, 'NZ', 0b01000000, start + 1),
                (200, 'Z',  0b00000000, start + 1),
                (200, 'Z',  0b01000000, addr),
                (208, 'NC', 0b00000000, addr),
                (208, 'NC', 0b00000001, start + 1),
                (216, 'C',  0b00000000, start + 1),
                (216, 'C',  0b00000001, addr),
                (224, 'PO', 0b00000000, addr),
                (224, 'PO', 0b00000100, start + 1),
                (232, 'PE', 0b00000000, start + 1),
                (232, 'PE', 0b00000100, addr),
                (240, 'P',  0b00000000, addr),
                (240, 'P',  0b10000000, start + 1),
                (248, 'M',  0b00000000, start + 1),
                (248, 'M',  0b10000000, addr),
        ):
            operation = f'RET {condition}'
            data = [opcode]
            registers[SP] = sp
            registers[F] = flags
            if end == addr:
                timing = 11
                reg_out = {SP: sp + 2}
            else:
                timing = 5
                reg_out = None
            memory[sp:sp + 2] = (addr % 256, addr // 256)
            self._test_instruction(simulator, operation, data, timing, reg_out, start=start, end=end)

    def test_rst(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        start = 30000
        sp = 23456

        for addr in range(0, 64, 8):
            operation = f'RST ${addr:02X}'
            data = [199 + addr]
            registers[SP] = sp
            reg_out = {SP: sp - 2}
            sna_out = {sp - 1: (start + 1) // 256, sp - 2: (start + 1) % 256}
            self._test_instruction(simulator, operation, data, 11, reg_out, sna_out, start=start, end=addr)

    def test_nop(self):
        simulator = Simulator([0] * 65536)
        operation = 'NOP'
        data = [0]
        self._test_instruction(simulator, operation, data, 4)

    def test_cpl(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        operation = 'CPL'
        data = [47]

        for a_in, f_in, f_out in (
                #       SZ5H3PNC    SZ5H3PNC
                (154, 0b01000000, 0b01110010),
                (0,   0b00000000, 0b00111010),
        ):
            registers[A] = a_in
            registers[F] = f_in
            reg_out = {A: a_in ^ 255, F: f_out}
            self._test_instruction(simulator, operation, data, 4, reg_out)

    def test_out_n_a(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        a = 128
        n = 56
        operation = f'OUT (${n:02X}),A'
        data = (211, 56)
        registers[A] = a
        self._test_instruction(simulator, operation, data, 11)

    def test_out_c_r(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        c = 128
        v = 56

        for i, (reg, r) in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'OUT (C),{reg}'
            data = (237, 65 + i * 8)
            registers[C] = c
            registers[r] = v
            self._test_instruction(simulator, operation, data, 12)

    def test_out_c_0(self):
        simulator = Simulator([0] * 65536)
        operation = 'OUT (C),0'
        data = (0xED, 0x71)
        self._test_instruction(simulator, operation, data, 12)

    def test_in_a_n(self):
        simulator = Simulator([0] * 65536)
        n = 56
        operation = f'IN A,(${n:02X})'
        data = (0xDB, n)
        reg_out = {A: 255}
        self._test_instruction(simulator, operation, data, 11, reg_out)

    def test_in_r_c(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        tracer = InTestTracer()
        simulator.set_tracer(tracer)
        in_value = 0
        c = 128

        for i, (reg, r) in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'IN {reg},(C)'
            data = (237, 64 + i * 8)
            registers[C] = c
            tracer.value = in_value
            reg_out = {r: in_value}
            if in_value == 0:
                reg_out[F] = 0b01000100
            else:
                reg_out[F] = 0b10101100
            in_value ^= 255
            self._test_instruction(simulator, operation, data, 12, reg_out)

    def test_in_f_c(self):
        simulator = Simulator([0] * 65536)
        operation = f'IN F,(C)'
        data = (0xED, 0x70)
        reg_out = {F: 0b10101100}
        self._test_instruction(simulator, operation, data, 12, reg_out)

    def test_djnz(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        addr = 35732

        for b, timing, end in ((34, 13, addr), (1, 8, addr + 2)):
            operation = f'DJNZ ${addr:04X}'
            data = (16, 254)
            registers[B] = b
            reg_out = {B: b - 1}
            self._test_instruction(simulator, operation, data, timing, reg_out, start=addr, end=end)

    def test_djnz_jumping_across_64K_boundary(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers

        for start, offset, end in (
                (65532, 12, 10),     # $FFFC DJNZ $000A
                (0,     -3, 65535),  # $0000 DJNZ $FFFF
        ):
            operation = f'DJNZ ${end:04X}'
            data = (16, offset if offset >= 0 else offset + 256)
            timing = 13
            registers[B] = 2
            reg_out = {B: 1}
            self._test_instruction(simulator, operation, data, timing, reg_out, start=start, end=end)

    def test_djnz_fast(self):
        simulator = Simulator([0] * 65536, config={'fast_djnz': True})
        registers = simulator.registers
        start = 35732

        for offset, b_in, b_out, timing, r_out, end in (
                (-2, 100, 0,   1295, 100, start + 2),
                (-2, 1,   0,   8,    1,   start + 2),
                (-2, 0,   0,   3323, 0,   start + 2),
                (-3, 100, 99,  13,   1,   start - 1),
                (-3, 1,   0,   8,    1,   start + 2),
                (-3, 0,   255, 13,   1,   start - 1),
        ):
            operation = f'DJNZ ${start + 2 + offset:04X}'
            data = (16, offset & 0xFF)
            registers[B] = b_in
            registers[R] = 0
            reg_out = {B: b_out, R: r_out}
            self._test_instruction(simulator, operation, data, timing, reg_out, start=start, end=end)

    def test_di(self):
        simulator = Simulator([0] * 65536, state={'iff': 1})
        operation = 'DI'
        data = [243]
        state_out = {'iff': 0}
        self._test_instruction(simulator, operation, data, 4, state_out=state_out)

    def test_ei(self):
        simulator = Simulator([0] * 65536, state={'iff': 0})
        operation = 'EI'
        data = [251]
        state_out = {'iff': 1}
        self._test_instruction(simulator, operation, data, 4, state_out=state_out)

    def test_halt(self):
        memory = [0] * 65536
        start = 40000
        memory[start] = 0x76
        simulator = Simulator(memory)
        simulator.run(start)
        self.assertEqual(simulator.registers[PC], start)
        self.assertEqual(simulator.registers[T], 4)

    def test_halt_repeats_until_frame_boundary(self):
        memory = [0] * 65536
        start = 40000
        memory[start] = 0x76
        simulator = Simulator(memory, state={'iff': 1, 'tstates': 69882})
        simulator.run(start)
        self.assertEqual(simulator.registers[PC], start)
        simulator.run()
        self.assertEqual(simulator.registers[PC], start + 1)

    def test_halt_repeats_at_frame_boundary_when_interrupts_disabled(self):
        memory = [0] * 65536
        start = 40000
        memory[start] = 0x76
        simulator = Simulator(memory, state={'iff': 0, 'tstates': 69882})
        simulator.run(start)
        self.assertEqual(simulator.registers[PC], start)
        simulator.run()
        self.assertEqual(simulator.registers[PC], start)

    def test_ccf(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        operation = 'CCF'
        data = [63]

        for f_in, f_out in (
                #  SZ5H3PNC    SZ5H3PNC
                (0b00010000, 0b00000001),
                (0b00000011, 0b00010000),
        ):
            registers[F] = f_in
            reg_out = {F: f_out}
            self._test_instruction(simulator, operation, data, 4, reg_out)

    def test_scf(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        operation = 'SCF'
        data = [55]

        for f_in, f_out in (
                #  SZ5H3PNC    SZ5H3PNC
                (0b00010000, 0b00000001),
                (0b00000011, 0b00000001),
        ):
            registers[F] = f_in
            reg_out = {F: f_out}
            self._test_instruction(simulator, operation, data, 4, reg_out)

    def _test_cpd_cpi(self, operation, opcode, inc, specs):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        data = (237, opcode)
        hl = 45287
        bc = 121

        for a, at_hl, f_out in specs:
            registers[A] = a
            registers[B] = bc // 256
            registers[C] = bc % 256
            registers[H] = hl // 256
            registers[L] = hl % 256
            reg_out = {
                B: (bc - 1) // 256,
                C: (bc - 1) % 256,
                H: (hl + inc) // 256,
                L: (hl + inc) % 256,
                F: f_out
            }
            memory[hl] = at_hl
            self._test_instruction(simulator, operation, data, 16, reg_out)

    def test_cpd(self):
        self._test_cpd_cpi('CPD', 169, -1, (
            # A in, (HL), F out
            #          SZ5H3PNC
            (17, 17, 0b01000110),
            (18, 6,  0b00111110),
        ))

    def test_cpi(self):
        self._test_cpd_cpi('CPI', 161, 1, (
            # A in, (HL), F out
            #          SZ5H3PNC
            (17, 17, 0b01000110),
            (18, 6,  0b00111110),
        ))

    def _test_cpdr_cpir(self, operation, opcode, inc, specs):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        data = (237, opcode)
        hl = 45287
        start = 61212

        for a, at_hl, bc, f_out, repeat in specs:
            if repeat:
                timing = 21
                end = start
            else:
                timing = 16
                end = start + 2
            registers[A] = a
            registers[B] = bc // 256
            registers[C] = bc % 256
            registers[H] = hl // 256
            registers[L] = hl % 256
            reg_out = {
                B: (bc - 1) // 256,
                C: (bc - 1) % 256,
                H: (hl + inc) // 256,
                L: (hl + inc) % 256,
                F: f_out
            }
            memory[hl] = at_hl
            self._test_instruction(simulator, operation, data, timing, reg_out, start=start, end=end)

    def test_cpdr(self):
        self._test_cpdr_cpir('CPDR', 185, -1, (
            # A in, (HL), BC, F out, repeat
            #           SZ5H3PNC
            (4, 4, 9, 0b01000110, False),
            (4, 5, 9, 0b10111110, True),
            (4, 4, 1, 0b01000010, False),
            (4, 5, 1, 0b10111010, False),
        ))

    def test_cpir(self):
        self._test_cpdr_cpir('CPIR', 177, 1, (
            # A in, (HL), BC, F out, repeat
            #           SZ5H3PNC
            (4, 4, 9, 0b01000110, False),
            (4, 5, 9, 0b10111110, True),
            (4, 4, 1, 0b01000010, False),
            (4, 5, 1, 0b10111010, False),
        ))

    def _test_block_in(self, operation, opcode, inc, repeat=False):
        simulator = Simulator([0] * 65536)
        tracer = InTestTracer()
        registers = simulator.registers
        data = (237, opcode)
        hl = 45287
        start = 34177

        for b, c, in_value, f_out_i, f_out_ir, f_out_d, f_out_dr in (
                #               SZ5H3PNC    SZ5H3PNC    SZ5H3PNC    SZ5H3PNC
                (2, 254,  127, 0b00010001, 0b00000101, 0b00010101, 0b00000001),
                (2, 254,  191, 0b00010011, 0b00000011, 0b00010111, 0b00000111),
                (2,   1, None, 0b00000110, 0b00000010, 0b00000110, 0b00000010),
                (1,   1, None, 0b01000010, 0b01000010, 0b01000010, 0b01000010),
                (0,   1, None, 0b10101010, 0b10000110, 0b10101010, 0b10000110),
        ):
            end = start + 2
            timing = 16
            if repeat and b != 1:
                timing = 21
                end = start
            registers[B] = b
            registers[C] = c
            registers[H] = hl // 256
            registers[L] = hl % 256
            if repeat:
                f_out = f_out_ir if inc > 0 else f_out_dr
            else:
                f_out = f_out_i if inc > 0 else f_out_d
            reg_out = {
                B: (b - 1) & 255,
                H: (hl + inc) // 256,
                L: (hl + inc) % 256,
                F: f_out
            }
            if in_value is None:
                simulator.set_tracer(None)
                in_value = 191
            else:
                simulator.set_tracer(tracer)
                tracer.value = in_value
            sna_out = {hl: in_value}
            self._test_instruction(simulator, operation, data, timing, reg_out, sna_out, start=start, end=end)

    def test_ind(self):
        self._test_block_in('IND', 170, -1)

    def test_ini(self):
        self._test_block_in('INI', 162, 1)

    def test_indr(self):
        self._test_block_in('INDR', 186, -1, True)

    def test_inir(self):
        self._test_block_in('INIR', 178, 1, True)

    def _test_block_ld(self, operation, opcode, inc, repeat=False):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        data = (237, opcode)
        hl = 31664
        de = 45331
        start = 54112
        at_hl = 147

        for bc, f_out, f_out_r in (
                #     SZ5H3PNC    SZ5H3PNC
                (2, 0b00100100, 0b00000100),
                (1, 0b00100000, 0b00100000),
                (0, 0b00100100, 0b00000100)
        ):
            end = start + 2
            timing = 16
            if repeat and bc != 1:
                timing = 21
                end = start
            registers[B] = bc // 256
            registers[C] = bc % 256
            registers[D] = de // 256
            registers[E] = de % 256
            registers[H] = hl // 256
            registers[L] = hl % 256
            bc_out = (bc - 1) & 65535
            reg_out = {
                B: bc_out // 256,
                C: bc_out % 256,
                D: (de + inc) // 256,
                E: (de + inc) % 256,
                H: (hl + inc) // 256,
                L: (hl + inc) % 256,
                F: f_out_r if repeat else f_out
            }
            memory[hl] = at_hl
            sna_out = {de: at_hl}
            self._test_instruction(simulator, operation, data, timing, reg_out, sna_out, start, end)

    def test_ldd(self):
        self._test_block_ld('LDD', 168, -1)

    def test_ldi(self):
        self._test_block_ld('LDI', 160, 1)

    def test_lddr(self):
        self._test_block_ld('LDDR', 184, -1, True)

    def test_ldir(self):
        self._test_block_ld('LDIR', 176, 1, True)

    def test_lddr_fast(self):
        simulator = Simulator([0] * 65536, config={'fast_ldir': True})
        registers = simulator.registers
        memory = simulator.memory
        data = (0xED, 0xB8)
        start = 30000
        at_hl = 250

        for bc_in, bc_out, de_in, de_out, hl_in, hl_out, f_out, r_out, timing, end in (
                #                                     SZ5H3PNC
                (52, 1, 30051, 30000, 40000, 39949, 0b00100100, 102,    1066, start),     # 0xB8 overwritten
                (51, 0, 30051, 30000, 40000, 39949, 0b00101000, 102,    1066, start + 2), # 0xB8 overwritten
                (50, 0, 30051, 30001, 40000, 39950, 0b00101000, 100,    1045, start + 2),
                ( 1, 0, 30051, 30050, 40000, 39999, 0b00101000,   2,      16, start + 2),
                ( 0, 1, 29999, 30000, 29999, 30000, 0b00100100, 126, 1376230, start),     # 0xB8 overwritten
        ):
            registers[B] = bc_in // 256
            registers[C] = bc_in % 256
            registers[D] = de_in // 256
            registers[E] = de_in % 256
            registers[H] = hl_in // 256
            registers[L] = hl_in % 256
            registers[R] = 0
            reg_out = {
                B: bc_out // 256,
                C: bc_out % 256,
                D: de_out // 256,
                E: de_out % 256,
                H: hl_out // 256,
                L: hl_out % 256,
                F: f_out,
                R: r_out
            }
            if bc_in:
                mem_read = list(range(hl_out + 1, hl_in + 1))
                for a in mem_read:
                    memory[a] = at_hl
                mem_written = list(range(de_out + 1, de_in + 1))
                sna_out = {a: at_hl for a in mem_written}
            else:
                sna_out = None
            self._test_instruction(simulator, 'LDDR', data, timing, reg_out, sna_out, start, end)

    def test_ldir_fast(self):
        simulator = Simulator([0] * 65536, config={'fast_ldir': True})
        registers = simulator.registers
        memory = simulator.memory
        data = (0xED, 0xB0)
        start = 30000
        at_hl = 250

        for bc_in, bc_out, de_in, de_out, hl_in, hl_out, f_out, r_out, timing, end in (
                #                                     SZ5H3PNC
                (52, 1, 29950, 30001, 40000, 40051, 0b00100100, 102,    1066, start),     # 0xED overwritten
                (51, 0, 29950, 30001, 40000, 40051, 0b00101000, 102,    1066, start + 2), # 0xED overwritten
                (50, 0, 29950, 30000, 40000, 40050, 0b00101000, 100,    1045, start + 2),
                ( 1, 0, 29950, 29951, 40000, 40001, 0b00101000,   2,      16, start + 2),
                ( 0, 1, 30002, 30001, 30002, 30001, 0b00100100, 126, 1376230, start),     # 0xED overwritten
        ):
            registers[B] = bc_in // 256
            registers[C] = bc_in % 256
            registers[D] = de_in // 256
            registers[E] = de_in % 256
            registers[H] = hl_in // 256
            registers[L] = hl_in % 256
            registers[R] = 0
            reg_out = {
                B: bc_out // 256,
                C: bc_out % 256,
                D: de_out // 256,
                E: de_out % 256,
                H: hl_out // 256,
                L: hl_out % 256,
                F: f_out,
                R: r_out
            }
            if bc_in:
                mem_read = list(range(hl_in, hl_out))
                for a in mem_read:
                    memory[a] = at_hl
                mem_written = list(range(de_in, de_out))
                sna_out = {a: at_hl for a in mem_written}
            else:
                sna_out = None
            self._test_instruction(simulator, 'LDIR', data, timing, reg_out, sna_out, start, end)

    def _test_block_out(self, operation, opcode, inc, repeat=False):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        data = (237, opcode)
        hl = 45287
        start = 41772

        for b, outval, f_out_i, f_out_ir, f_out_d, f_out_dr in (
                #          SZ5H3PNC    SZ5H3PNC    SZ5H3PNC    SZ5H3PNC
                (2, 255, 0b00010111, 0b00100111, 0b00010011, 0b00100011),
                (2, 127, 0b00010101, 0b00100001, 0b00010001, 0b00100101),
                (2, 0,   0b00000000, 0b00100100, 0b00000000, 0b00100100),
                (1, 128, 0b01010111, 0b01010111, 0b01010111, 0b01010111),
                (0, 0,   0b10101100, 0b10100000, 0b10101100, 0b10100000),
        ):
            end = start + 2
            timing = 16
            if repeat and b != 1:
                timing = 21
                end = start
            registers[B] = b
            registers[H] = hl // 256
            registers[L] = hl % 256
            if repeat:
                f_out = f_out_ir if inc > 0 else f_out_dr
            else:
                f_out = f_out_i if inc > 0 else f_out_d
            reg_out = {
                B: (b - 1) & 255,
                H: (hl + inc) // 256,
                L: (hl + inc) % 256,
                F: f_out
            }
            memory[hl] = outval
            self._test_instruction(simulator, operation, data, timing, reg_out, start=start, end=end)

    def test_outd(self):
        self._test_block_out('OUTD', 171, -1)

    def test_outi(self):
        self._test_block_out('OUTI', 163, 1)

    def test_otdr(self):
        self._test_block_out('OTDR', 187, -1, True)

    def test_otir(self):
        self._test_block_out('OTIR', 179, 1, True)

    def test_ex_sp(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        sp1, sp2 = 27, 231
        r1, r2 = 56, 89

        for prefix, reg, rh, rl in (((), 'HL', H, L), ((0xDD,), 'IX', IXh, IXl), ((0xFD,), 'IY', IYh, IYl)):
            for sp in (63312, 65535):
                operation = f'EX (SP),{reg}'
                data = prefix + (227,)
                timing = 23 if prefix else 19
                registers[SP] = sp
                registers[rh] = r2
                registers[rl] = r1
                reg_out = {rl: sp1, rh: sp2}
                memory[sp] = sp1
                memory[(sp + 1) & 0xFFFF] = sp2
                sna_out = {sp: r1}
                sp = (sp + 1) & 0xFFFF
                if sp > 0x3FFF:
                    sna_out[sp] = r2
                self._test_instruction(simulator, operation, data, timing, reg_out, sna_out)

    def test_exx(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        operation = 'EXX'
        data = [217]
        bc, de, hl = 36711, 5351, 16781
        xbc, xde, xhl = 35129, 61121, 41113
        registers[B] = bc // 256
        registers[C] = bc % 256
        registers[D] = de // 256
        registers[E] = de % 256
        registers[H] = hl // 256
        registers[L] = hl % 256
        registers[xB] = xbc // 256
        registers[xC] = xbc % 256
        registers[xD] = xde // 256
        registers[xE] = xde % 256
        registers[xH] = xhl // 256
        registers[xL] = xhl % 256
        reg_out = {
            B: xbc // 256, xB: bc // 256,
            C: xbc % 256, xC: bc % 256,
            D: xde // 256, xD: de // 256,
            E: xde % 256, xE: de % 256,
            H: xhl // 256, xH: hl // 256,
            L: xhl % 256, xL: hl % 256,
        }
        self._test_instruction(simulator, operation, data, 4, reg_out)

    def test_ex_af(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        operation = "EX AF,AF'"
        data = [8]
        a, f = 4, 154
        xa, xf = 37, 17
        registers[A] = a
        registers[F] = f
        registers[xA] = xa
        registers[xF] = xf
        reg_out = {A: xa, F: xf, xA: a, xF: f}
        self._test_instruction(simulator, operation, data, 4, reg_out)

    def test_ex_de_hl(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        operation = 'EX DE,HL'
        data = [235]
        de, hl = 28812, 56117
        registers[D] = de // 256
        registers[E] = de % 256
        registers[H] = hl // 256
        registers[L] = hl % 256
        reg_out = {D: hl // 256, E: hl % 256, H: de // 256, L: de % 256}
        self._test_instruction(simulator, operation, data, 4, reg_out)

    def test_neg(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        operation = 'NEG'

        for opcode in (0x44, 0x4C, 0x54, 0x5C, 0x64, 0x6C, 0x74, 0x7C):
            data = (0xED, opcode)
            for a_in in (0, 1, 128):
                a_out = (256 - a_in) & 255
                f_out = (a_out & 0b10101000) | 0b00000010
                if a_out == 0:
                    f_out |= 0b01000000 # Z
                if a_in & 0x0F:
                    f_out |= 0b00010000 # H
                if a_out == 0x80:
                    f_out |= 0b00000100 # P/V
                if a_out > 0:
                    f_out |= 0b00000001 # C
                registers[A] = a_in
                reg_out = {A: a_out, F: f_out}
                self._test_instruction(simulator, operation, data, 8, reg_out)

    def test_ret_from_interrupt(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        start = 40000
        end = 45271
        sp = 32517

        for operation, opcodes in (
                ('RETN', (0x45, 0x55, 0x5D, 0x65, 0x6D, 0x75, 0x7D)),
                ('RETI', (0x4D,))
        ):
            for opcode in opcodes:
                data = (0xED, opcode)
                registers[SP] = sp
                reg_out = {SP: sp + 2}
                memory[sp:sp + 2] = (end % 256, end // 256)
                self._test_instruction(simulator, operation, data, 14, reg_out, start=start, end=end)

    def test_im_n(self):
        memory = [0] * 65536
        for mode, opcodes in (
                (0, (0x46, 0x4E, 0x66, 0x6E)),
                (1, (0x56, 0x76)),
                (2, (0x5E, 0x7E))
        ):
            for opcode in opcodes:
                operation = f'IM {mode}'
                data = (0xED, opcode)
                simulator = Simulator(memory, state = {'im': mode ^ 3})
                state_out = {'im': mode}
                self._test_instruction(simulator, operation, data, 8, state_out=state_out)

    def test_rld(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        operation = 'RLD'
        data = (237, 111)
        hl = 54672

        for a, at_hl, a_out, at_hl_out, f_out in (
                #                                                  SZ5H3PNC
                (0b10101001, 0b11000101, 0b10101100, 0b01011001, 0b10101100),
                (0b00001001, 0b00000101, 0b00000000, 0b01011001, 0b01000100),
        ):
            registers[A] = a
            registers[H] = hl // 256
            registers[L] = hl % 256
            reg_out = {A: a_out, F: f_out}
            memory[hl] = at_hl
            sna_out = {hl: at_hl_out}
            self._test_instruction(simulator, operation, data, 18, reg_out, sna_out)

    def test_rrd(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        memory = simulator.memory
        operation = 'RRD'
        data = (237, 103)
        hl = 54672

        for a, at_hl, a_out, at_hl_out, f_out in (
                #                                                  SZ5H3PNC
                (0b10101001, 0b11000101, 0b10100101, 0b10011100, 0b10100100),
                (0b00001001, 0b11100000, 0b00000000, 0b10011110, 0b01000100),
        ):
            registers[A] = a
            registers[H] = hl // 256
            registers[L] = hl % 256
            reg_out = {A: a_out, F: f_out}
            memory[hl] = at_hl
            sna_out = {hl: at_hl_out}
            self._test_instruction(simulator, operation, data, 18, reg_out, sna_out)

    def test_daa(self):
        simulator = Simulator([0] * 65536)
        registers = simulator.registers
        operation = 'DAA'
        data = [39]

        for f_in, f_out, a_out in (
                #  SZ5H3PNC    SZ5H3PNC
                (0b00000000, 0b01000100, 0),
                (0b00000001, 0b00100101, 96),
                (0b00000010, 0b01000110, 0),
                (0b00000011, 0b10100111, 160),
                (0b00010000, 0b00000100, 6),
                (0b00010001, 0b00100101, 102),
                (0b00010010, 0b10111110, 250),
                (0b00010011, 0b10011111, 154),
        ):
            registers[A] = 0
            registers[F] = f_in
            reg_out = {A: a_out, F: f_out}
            self._test_instruction(simulator, operation, data, 4, reg_out)

    def test_after_dd_fd_nop_dd_fd(self):
        simulator = Simulator([0] * 65536)

        for opcode in (
                0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
                0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F,
                0x20, 0x27, 0x28, 0x2F, 0x30, 0x31, 0x32, 0x33, 0x37, 0x38, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F,
                0x40, 0x41, 0x42, 0x43, 0x47, 0x48, 0x49, 0x4A, 0x4B, 0x4F,
                0x50, 0x51, 0x52, 0x53, 0x57, 0x58, 0x59, 0x5A, 0x5B, 0x5F,
                0x76, 0x78, 0x79, 0x7A, 0x7B, 0x7F,
                0x80, 0x81, 0x82, 0x83, 0x87, 0x88, 0x89, 0x8A, 0x8B, 0x8F,
                0x90, 0x91, 0x92, 0x93, 0x97, 0x98, 0x99, 0x9A, 0x9B, 0x9F,
                0xA0, 0xA1, 0xA2, 0xA3, 0xA7, 0xA8, 0xA9, 0xAA, 0xAB, 0xAF,
                0xB0, 0xB1, 0xB2, 0xB3, 0xB7, 0xB8, 0xB9, 0xBA, 0xBB, 0xBF,
                0xC0, 0xC1, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9, 0xCA, 0xCC, 0xCD, 0xCE, 0xCF,
                0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xDB, 0xDC, 0xDD, 0xDE, 0xDF,
                0xE0, 0xE2, 0xE4, 0xE6, 0xE7, 0xE8, 0xEA, 0xEB, 0xEC, 0xED, 0xEE, 0xEF,
                0xF0, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF
        ):
            for prefix in (0xDD, 0xFD):
                operation = f'DEFB ${prefix:02X}'
                data = (prefix, opcode)
                start = 32768
                simulator.registers[R] = 0
                reg_out = {R: 1}
                self._test_instruction(simulator, operation, data, 4, reg_out, start=start, end=start + 1)

    def test_after_ed_nop_ed(self):
        simulator = Simulator([0] * 65536)

        for opcode in (
                0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
                0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F,
                0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F,
                0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F,
                0x77, 0x7F,
                0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x8B, 0x8C, 0x8D, 0x8E, 0x8F,
                0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0x9B, 0x9C, 0x9D, 0x9E, 0x9F,
                0xA4, 0xA5, 0xA6, 0xA7, 0xAC, 0xAD, 0xAE, 0xAF,
                0xB4, 0xB5, 0xB6, 0xB7, 0xBC, 0xBD, 0xBE, 0xBF,
                0xC0, 0xC1, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9, 0xCA, 0xCB, 0xCC, 0xCD, 0xCE, 0xCF,
                0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xDB, 0xDC, 0xDD, 0xDE, 0xDF,
                0xE0, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xEB, 0xEC, 0xED, 0xEE, 0xEF,
                0xF0, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF
        ):
            operation = f'DEFB $ED,${opcode:02X}'
            data = (0xED, opcode)
            start = 32768
            self._test_instruction(simulator, operation, data, 8, start=start, end=start + 2)

    def test_initial_registers(self):
        registers = {
            'A': 0,
            'F': 1,
            'B': 2,
            'C': 3,
            'D': 4,
            'E': 5,
            'H': 6,
            'L': 7,
            'IXh': 8,
            'IXl': 9,
            'IYh': 10,
            'IYl': 11,
            'I': 12,
            'R': 13,
            'SP': 14,
            '^A': 0,
            '^F': 1,
            '^B': 2,
            '^C': 3,
            '^D': 4,
            '^E': 5,
            '^H': 6,
            '^L': 7,
        }
        simulator = Simulator([0] * 65536, registers)
        self.assertEqual(simulator.registers[A], 0)
        self.assertEqual(simulator.registers[F], 1)
        self.assertEqual(simulator.registers[B], 2)
        self.assertEqual(simulator.registers[C], 3)
        self.assertEqual(simulator.registers[D], 4)
        self.assertEqual(simulator.registers[E], 5)
        self.assertEqual(simulator.registers[H], 6)
        self.assertEqual(simulator.registers[L], 7)
        self.assertEqual(simulator.registers[IXh], 8)
        self.assertEqual(simulator.registers[IXl], 9)
        self.assertEqual(simulator.registers[IYh], 10)
        self.assertEqual(simulator.registers[IYl], 11)
        self.assertEqual(simulator.registers[I], 12)
        self.assertEqual(simulator.registers[R], 13)
        self.assertEqual(simulator.registers[SP], 14)
        self.assertEqual(simulator.registers[xA], 0)
        self.assertEqual(simulator.registers[xF], 1)
        self.assertEqual(simulator.registers[xB], 2)
        self.assertEqual(simulator.registers[xC], 3)
        self.assertEqual(simulator.registers[xD], 4)
        self.assertEqual(simulator.registers[xE], 5)
        self.assertEqual(simulator.registers[xH], 6)
        self.assertEqual(simulator.registers[xL], 7)

    def test_initial_register_pairs(self):
        registers = {
            'AF': 256,
            'BC': 770,
            'DE': 1284,
            'HL': 1798,
            'IX': 2312,
            'IY': 2826,
            'IR': 3340,
            'SP': 14997,
            '^AF': 3854,
            '^BC': 4368,
            '^DE': 4882,
            '^HL': 5396,
        }
        exp_register_values = {
            A: 1,
            F: 0,
            B: 3,
            C: 2,
            D: 5,
            E: 4,
            H: 7,
            L: 6,
            IXh: 9,
            IXl: 8,
            IYh: 11,
            IYl: 10,
            I: 13,
            R: 12,
            SP: 14997,
            xA: 15,
            xF: 14,
            xB: 17,
            xC: 16,
            xD: 19,
            xE: 18,
            xH: 21,
            xL: 20,
        }
        simulator = Simulator([0] * 65536, registers)
        for r, v in exp_register_values.items():
            self.assertEqual(simulator.registers[r], v)

    def test_instruction_crossing_64K_boundary(self):
        simulator = Simulator([0] * 65536)
        operation = 'LD BC,$0302'
        data = (1, 2, 3)
        reg_out = {B: 3, C: 2}
        self._test_instruction(simulator, operation, data, 10, reg_out, start=65535, end=2)

    def test_no_tracer(self):
        memory = [0] * 65536
        simulator = Simulator(memory)
        simulator.run(0)
        self.assertEqual(simulator.registers[PC], 1)
        self.assertEqual(simulator.registers[T], 4)

    def test_port_reading(self):
        memory = [0] * 65536
        start = 49152
        code = (
            0xDB, 0xFE,       # IN A,(254)
            0xED, 0x50,       # IN D,(C)
            0xED, 0xA2,       # INI
            0xED, 0xAA,       # IND
            0x01, 0xFE, 0x01, # LD BC,510
            0xED, 0xB2,       # INIR
            0x04,             # INC B
            0xED, 0xBA,       # INDR
        )
        end = start + len(code)
        memory[start:end] = code
        simulator = Simulator(memory, {'A': 170, 'BC': 65311})
        value = 128
        tracer = PortTracer(value)
        simulator.set_tracer(tracer)
        simulator.run(start, end)
        exp_ports = [43774, 65311, 65311, 65055, 510, 510]
        self.assertEqual(tracer.in_ports, exp_ports)
        self.assertEqual(simulator.registers[A], value)
        self.assertEqual(simulator.registers[D], value)

    def test_port_writing(self):
        memory = [0] * 65536
        start = 49152
        port = 254
        code = (
            0xD3, 0xFE,       # OUT (254),A
            0xED, 0x79,       # OUT (C),A
            0xED, 0x71,       # OUT (C),0
            0xED, 0xA3,       # OUTI
            0xED, 0xAB,       # OUTD
            0x01, 0xFE, 0x01, # LD BC,510
            0xED, 0xB3,       # OTIR
            0x04,             # INC B
            0xED, 0xBB,       # OTDR
        )
        end = start + len(code)
        memory[start:end] = code
        hl = 30000
        memory[hl:hl + 2] = (1, 2)
        simulator = Simulator(memory, {'A': 171, 'BC': 65055, 'HL': hl})
        tracer = PortTracer()
        simulator.set_tracer(tracer)
        simulator.run(start, end)
        exp_outs = [
            (44030, 171),
            (65055, 171),
            (65055, 0),
            (64799, 1),
            (64543, 2),
            (254, 1),
            (254, 2)
        ]
        self.assertEqual(tracer.out_ports, exp_outs)

    def test_rom_not_writable(self):
        memory = [0] * 65536
        start = 49152
        code = (
            0x21, 0x01, 0x02,       # 49152 LD HL,513
            0x22, 0xFF, 0x3F,       # 49155 LD (16383),HL
            0x22, 0xFF, 0xFF,       # 49158 LD (65535),HL
        )
        end = start + len(code)
        memory[start:end] = code
        simulator = Simulator(memory)
        simulator.run(start, end)
        self.assertEqual(memory[0xFFFF], 0x01)
        self.assertEqual(memory[0x0000], 0x00)
        self.assertEqual(memory[0x3FFF], 0x00)
        self.assertEqual(memory[0x4000], 0x02)

    def test_resume(self):
        memory = [0] * 65536
        simulator = Simulator(memory)
        simulator.run(0)
        simulator.run()
        self.assertEqual(simulator.registers[PC], 2)
        self.assertEqual(simulator.registers[T], 8)

    def test_stop(self):
        memory = [0] * 65536
        simulator = Simulator(memory)
        simulator.run(0, 2)
        self.assertEqual(simulator.registers[PC], 2)
        self.assertEqual(simulator.registers[T], 8)

    def test_pc_register_value(self):
        memory = [0] * 65536
        simulator = Simulator(memory, {'PC': 1})
        simulator.run()
        self.assertEqual(simulator.registers[PC], 2)
        self.assertEqual(simulator.registers[T], 4)

    def test_initial_time(self):
        memory = [0] * 65536
        simulator = Simulator(memory, state={'tstates': 100})
        simulator.run(0)
        self.assertEqual(simulator.registers[PC], 1)
        self.assertEqual(simulator.registers[T], 104)

    def test_initial_iff(self):
        memory = [0] * 65536
        start = 32768
        memory[start:start + 2] = (0xED, 0x57) # LD A,I
        simulator = Simulator(memory, state={'iff': 1})
        simulator.run(start)
        self.assertEqual(simulator.registers[PC], start + 2)
        self.assertEqual(simulator.registers[F], 0b00101100)

    def test_accept_interrupt_mode_0(self):
        pc = 30000
        sp = 40000
        simulator = Simulator([0] * 65536, {'PC': pc, 'SP': sp}, {'iff': 1, 'im': 0})
        blocked = simulator.accept_interrupt(simulator.registers, simulator.memory, pc - 1)
        self.assertFalse(blocked)
        self.assertEqual(simulator.registers[T], 13)
        self.assertEqual(simulator.registers[PC], 56)
        self.assertEqual(simulator.registers[R], 1)
        self.assertEqual(simulator.registers[SP], sp - 2)
        self.assertEqual([pc % 256, pc // 256], simulator.memory[sp - 2:sp])
        self.assertEqual(simulator.iff, 0)

    def test_accept_interrupt_mode_1(self):
        pc = 40000
        sp = 50000
        simulator = Simulator([0] * 65536, {'PC': pc, 'SP': sp}, {'iff': 1, 'im': 1})
        blocked = simulator.accept_interrupt(simulator.registers, simulator.memory, pc - 1)
        self.assertFalse(blocked)
        self.assertEqual(simulator.registers[T], 13)
        self.assertEqual(simulator.registers[PC], 56)
        self.assertEqual(simulator.registers[R], 1)
        self.assertEqual(simulator.registers[SP], sp - 2)
        self.assertEqual([pc % 256, pc // 256], simulator.memory[sp - 2:sp])
        self.assertEqual(simulator.iff, 0)

    def test_accept_interrupt_mode_2(self):
        memory = [0] * 65536
        iaddr = 40000
        i = 64
        vaddr = 255 + 256 * i
        memory[vaddr:vaddr + 2] = (iaddr % 256, iaddr // 256)
        pc = 50000
        sp = 60000
        simulator = Simulator(memory, {'PC': pc, 'SP': sp, 'I': i}, {'iff': 1, 'im': 2})
        blocked = simulator.accept_interrupt(simulator.registers, simulator.memory, pc - 1)
        self.assertFalse(blocked)
        self.assertEqual(simulator.registers[T], 19)
        self.assertEqual(simulator.registers[PC], iaddr)
        self.assertEqual(simulator.registers[R], 1)
        self.assertEqual(simulator.registers[SP], sp - 2)
        self.assertEqual([pc % 256, pc // 256], simulator.memory[sp - 2:sp])
        self.assertEqual(simulator.iff, 0)

    def test_accept_interrupt_after_ei(self):
        memory = [0] * 65536
        pc = 30000
        sp = 40000
        memory[pc - 1] = 0xFB # EI
        simulator = Simulator(memory, {'PC': pc, 'SP': sp}, {'iff': 1, 'im': 1})
        blocked = simulator.accept_interrupt(simulator.registers, simulator.memory, pc - 1)
        self.assertTrue(blocked)
        self.assertEqual(simulator.registers[T], 0)
        self.assertEqual(simulator.registers[PC], pc)
        self.assertEqual(simulator.registers[R], 0)
        self.assertEqual(simulator.registers[SP], sp)
        self.assertEqual([0, 0], simulator.memory[sp - 2:sp])
        self.assertEqual(simulator.iff, 1)

    def test_accept_interrupt_after_dd_prefix(self):
        memory = [0] * 65536
        pc = 30000
        sp = 40000
        memory[pc - 1] = 0xDD
        simulator = Simulator(memory, {'PC': pc, 'SP': sp}, {'iff': 1, 'im': 1})
        blocked = simulator.accept_interrupt(simulator.registers, simulator.memory, pc - 1)
        self.assertTrue(blocked)
        self.assertEqual(simulator.registers[T], 0)
        self.assertEqual(simulator.registers[PC], pc)
        self.assertEqual(simulator.registers[R], 0)
        self.assertEqual(simulator.registers[SP], sp)
        self.assertEqual([0, 0], simulator.memory[sp - 2:sp])
        self.assertEqual(simulator.iff, 1)

    def test_accept_interrupt_after_fd_prefix(self):
        memory = [0] * 65536
        pc = 30000
        sp = 40000
        memory[pc - 1] = 0xFD
        simulator = Simulator(memory, {'PC': pc, 'SP': sp}, {'iff': 1, 'im': 1})
        blocked = simulator.accept_interrupt(simulator.registers, simulator.memory, pc - 1)
        self.assertTrue(blocked)
        self.assertEqual(simulator.registers[T], 0)
        self.assertEqual(simulator.registers[PC], pc)
        self.assertEqual(simulator.registers[R], 0)
        self.assertEqual(simulator.registers[SP], sp)
        self.assertEqual([0, 0], simulator.memory[sp - 2:sp])
        self.assertEqual(simulator.iff, 1)
