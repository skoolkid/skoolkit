from skoolkittest import SkoolKitTestCase
from skoolkit.simulator import Simulator

REGISTERS = ('B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A')

class Tracer:
    def trace(self, simulator, instruction):
        self.operation = instruction.operation
        return True

class InTestTracer:
    value = 0

    def read_port(self, simulator, port):
        return self.value

class CountingTracer:
    def __init__(self, max_operations=1):
        self.max_operations = max_operations
        self.count = 0

    def trace(self, simulator, instruction):
        self.count += 1
        return self.count >= self.max_operations

class PushPopCountTracer:
    def trace(self, simulator, instruction):
        return simulator.ppcount < 0

class PortTracer:
    def __init__(self, in_value=0, end=-1):
        self.in_value = in_value
        self.end = end
        self.in_ports = []
        self.out_ports = []

    def trace(self, simulator, instruction):
        return self.end < 0 or simulator.pc == self.end

    def read_port(self, simulator, port):
        self.in_ports.append(port)
        return self.in_value

    def write_port(self, simulator, port, value):
        self.out_ports.append((port, value))

class MemoryTracer:
    def __init__(self, end):
        self.end = end
        self.read = []
        self.written = []

    def trace(self, simulator, instruction):
        return simulator.pc == self.end

    def read_memory(self, simulator, address, count):
        self.read.append((simulator.pc, address, count))

    def write_memory(self, simulator, address, values):
        self.written.append((simulator.pc, address, *values))

class ReadMemoryTracer:
    def __init__(self):
        self.read = []

    def read_memory(self, simulator, address, count):
        self.read.append((address, count))

class WriteMemoryTracer:
    def __init__(self):
        self.written = []

    def write_memory(self, simulator, address, values):
        self.written.append((address, values))

TRACER = Tracer()

class SimulatorTest(SkoolKitTestCase):
    def _test_instruction(self, inst, data, timing, reg_in=None, reg_out=None, sna_in=None, sna_out=None,
                          start=None, end=None, state_in=None, state_out=None, tracer=None, config=None):
        if start is None:
            start = 65530
        if end is None:
            end = start + len(data)
        snapshot = [0] * 65536
        d_end = start + len(data)
        if d_end <= 65536:
            snapshot[start:d_end] = data
        else:
            wrapped = d_end - 65536
            snapshot[start:] = data[:-wrapped]
            snapshot[:wrapped] = data[-wrapped:]
        data_hex = ''.join(f'{b:02X}' for b in data)
        if sna_in:
            for a, v in sna_in.items():
                snapshot[a] = v
        simulator = Simulator(snapshot, reg_in, state_in, config=config)
        simulator.add_tracer(TRACER)
        if isinstance(tracer, tuple):
            for t in tracer:
                simulator.add_tracer(t)
        elif tracer:
            simulator.add_tracer(tracer)
        exp_reg = simulator.registers.copy()
        if reg_out is None:
            reg_out = {}
        if 'R' not in reg_out:
            r_in, r_inc = exp_reg['R'], 2  if data[0] in (0xCB, 0xDD, 0xED, 0xFD) else 1
            reg_out['R'] = (r_in & 0x80) + ((r_in + r_inc) & 0x7F)
        exp_reg.update(reg_out)
        simulator.run(start)
        registers = [f'{r}={v}' for r, v in reg_in.items()] if reg_in else ()
        regvals = ', '.join(registers)
        self.assertEqual(inst, TRACER.operation, f"Operation mismatch for '{inst}' ({data_hex}); input: {regvals}")
        self.assertEqual(simulator.pc, end, f"End address mismatch for '{inst}' ({data_hex}); input: {regvals}")
        self.assertEqual(simulator.tstates, timing, f"Timing mismatch for '{inst}' ({data_hex}); input: {regvals}")
        if simulator.registers != exp_reg:
            reg_exp = {}
            reg_new = {}
            for r, v in simulator.registers.items():
                if exp_reg[r] != v:
                    reg_exp[r] = exp_reg[r]
                    reg_new[r] = v
            self.assertEqual(reg_new, reg_exp, f"Register mismatch for '{inst}' ({data_hex}); input: {regvals}")
        if sna_out:
            actual_snapshot = {a: simulator.snapshot[a] for a in sna_out}
            regvals = ', '.join(registers)
            self.assertEqual(actual_snapshot, sna_out, f"Snapshot mismatch for '{inst}' ({data_hex}); input: {regvals}")
        if state_out:
            if 'im' in state_out:
                self.assertEqual(simulator.imode, state_out['im'])
            if 'iff' in state_out:
                self.assertEqual(simulator.iff2, state_out['iff'])

    def _test_arithmetic(self, op, opcode1, opcode2, *specs):
        if op in ('AND', 'CP', 'OR', 'SUB', 'XOR'):
            op_a = op + ' '
        elif op in ('ADC', 'ADD', 'SBC'):
            op_a = op + ' A,'

        for a_in, opval, f_in, a_out, f_out in specs[0]:
            data = (opcode1, opval)
            reg_in = {'A': a_in, 'F': f_in}
            reg_out = {'A': a_out, 'F': f_out}
            self._test_instruction(f'{op_a}${opval:02X}', data, 7, reg_in, reg_out)

        hl = 49152
        for i, reg in enumerate(REGISTERS):
            data = [opcode2 + i]
            operation = f'{op_a}{reg}'
            if reg == '(HL)':
                reg_in = {'H': hl // 256, 'L': hl % 256}
                for a_in, opval, f_in, a_out, f_out in specs[0]:
                    reg_in.update({'A': a_in, 'F': f_in})
                    reg_out = {'A': a_out, 'F': f_out}
                    sna_in = {hl: opval}
                    self._test_instruction(operation, data, 7, reg_in, reg_out, sna_in)
            elif reg == 'A':
                for a_in, f_in, a_out, f_out in specs[1]:
                    reg_in = {'A': a_in, 'F': f_in}
                    reg_out = {'A': a_out, 'F': f_out}
                    self._test_instruction(operation, data, 4, reg_in, reg_out)
            else:
                for a_in, opval, f_in, a_out, f_out in specs[0]:
                    reg_in = {'A': a_in, 'F': f_in, reg: opval}
                    reg_out = {'A': a_out, 'F': f_out}
                    self._test_instruction(operation, data, 4, reg_in, reg_out)

        for prefix, reg in ((0xDD, 'IX'), (0xFD, 'IY')):
            for opcode, half in ((opcode2 + 4, 'h'), (opcode2 + 5, 'l')):
                for a_in, opval, f_in, a_out, f_out in specs[0]:
                    ireg = f'{reg}{half}'
                    operation = f'{op_a}{ireg}'
                    data = (prefix, opcode)
                    reg_in = {'A': a_in, 'F': f_in, ireg: opval}
                    reg_out = {'A': a_out, 'F': f_out}
                    self._test_instruction(operation, data, 8, reg_in, reg_out)

        offset = -2
        for prefix, reg, value in ((0xDD, 'IX', 32768), (0xFD, 'IY', 32769)):
            for a_in, opval, f_in, a_out, f_out in specs[0]:
                operation = f'{op_a}({reg}-${-offset:02X})'
                data = (prefix, opcode2 + 6, offset & 255)
                reg_in = {'A': a_in, 'F': f_in, reg: value}
                reg_out = {'A': a_out, 'F': f_out}
                sna_in = {value + offset: opval}
                self._test_instruction(operation, data, 19, reg_in, reg_out, sna_in)

    def _test_res_set(self, op):
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

            for i, reg in enumerate(REGISTERS):
                operation = f'{op} {bit},{reg}'
                data = (203, base_opcode + 8 * bit + i)
                if reg == '(HL)':
                    timing = 15
                    reg_in = {'H': hl // 256, 'L': hl % 256}
                    reg_out = {}
                    sna_in = {hl: opval_in}
                    sna_out = {hl: opval_out}
                else:
                    timing = 8
                    reg_in = {reg: opval_in}
                    reg_out = {reg: opval_out}
                    sna_in = {}
                    sna_out = {}
                self._test_instruction(operation, data, timing, reg_in, reg_out, sna_in, sna_out)

            offset = 4
            for prefix, reg, value in ((0xDD, 'IX', 32768), (0xFD, 'IY', 32769)):
                operation = f'{op} {bit},({reg}+${offset:02X})'
                data = (prefix, 203, offset & 255, base_opcode + 8 * bit + 6)
                reg_in = {reg: value}
                reg_out = {}
                sna_in = {value + offset: opval_in}
                sna_out = {value + offset: opval_out}
                self._test_instruction(operation, data, 23, reg_in, reg_out, sna_in, sna_out)

    def _test_rotate_shift(self, op, opcode, specs):
        hl = 49152
        for i, reg in enumerate(REGISTERS):
            data = (203, opcode + i)
            operation = f'{op} {reg}'
            if reg == '(HL)':
                reg_in = {'H': hl // 256, 'L': hl % 256}
                for r_in, f_in, r_out, f_out in specs:
                    reg_in.update({'F': f_in})
                    reg_out = {'F': f_out}
                    sna_in = {hl: r_in}
                    sna_out = {hl: r_out}
                    self._test_instruction(operation, data, 15, reg_in, reg_out, sna_in, sna_out)
            else:
                for r_in, f_in, r_out, f_out in specs:
                    reg_in = {reg: r_in, 'F': f_in}
                    reg_out = {reg: r_out, 'F': f_out}
                    self._test_instruction(operation, data, 8, reg_in, reg_out)

        offset = 1
        for prefix, reg, value in ((0xDD, 'IX', 32768), (0xFD, 'IY', 32769)):
            for r_in, f_in, r_out, f_out in specs:
                operation = f'{op} ({reg}+${offset:02X})'
                data = (prefix, 203, offset & 255, opcode + 6)
                reg_in = {'F': f_in, reg: value}
                reg_out = {'F': f_out}
                sna_in = {value + offset: r_in}
                sna_out = {value + offset: r_out}
                self._test_instruction(operation, data, 23, reg_in, reg_out, sna_in, sna_out)

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
        hl = 50000

        for bit in range(8):
            mask = 1 << bit
            for bitval, opval in ((0, mask ^ 255), (1, mask)):
                for i, reg in enumerate(REGISTERS):
                    operation = f'BIT {bit},{reg}'
                    data = (203, 64 + 8 * bit + i)
                    f_out = 0b00010000 | (opval & 0b00101000)
                    if bitval:
                        if bit == 7:
                            f_out |= 0b10000000
                    else:
                        f_out |= 0b01000100
                    reg_out = {'F': f_out}
                    if reg == '(HL)':
                        timing = 12
                        reg_in = {'H': hl // 256, 'L': hl % 256}
                        sna_in = {hl: opval}
                    else:
                        timing = 8
                        reg_in = {reg: opval}
                        sna_in = {}
                    self._test_instruction(operation, data, timing, reg_in, reg_out, sna_in)

                offset = 3
                for prefix, reg, value in ((0xDD, 'IX', 32768), (0xFD, 'IY', 32769)):
                    operation = f'BIT {bit},({reg}+${offset:02X})'
                    for opcode in range(0x40 + 8 * bit, 0x48 + 8 * bit):
                        data = (prefix, 0xCB, offset & 255, opcode)
                        reg_in = {reg: value}
                        if bitval:
                            f_out = 0b00010000
                            if bit == 7:
                                f_out |= 0b10000000
                        else:
                            f_out = 0b01010100
                        reg_out = {'F': f_out}
                        sna_in = {value + offset: opval}
                        self._test_instruction(operation, data, 20, reg_in, reg_out, sna_in)

    def test_res(self):
        self._test_res_set('RES')

    def test_res_with_dest_reg(self):
        for i, reg in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            for bit in range(8):
                operation = f'RES {bit},(IX+$00),{reg}'
                data = (0xDD, 0xCB, 0x00, 0x80 + 8 * bit + i)
                ix = 32768
                at_ix = 255
                reg_in = {'IX': ix}
                reg_out = {reg: 255 - (1 << bit)}
                sna_in = {ix: at_ix}
                sna_out = {ix: 255 - (1 << bit)}
                self._test_instruction(operation, data, 23, reg_in, reg_out, sna_in, sna_out)

    def test_set(self):
        self._test_res_set('SET')

    def test_set_with_dest_reg(self):
        for i, reg in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            for bit in range(8):
                operation = f'SET {bit},(IX+$00),{reg}'
                data = (0xDD, 0xCB, 0x00, 0xC0 + 8 * bit + i)
                ix = 32768
                at_ix = 0
                reg_in = {'IX': ix}
                reg_out = {reg: 1 << bit}
                sna_in = {ix: at_ix}
                sna_out = {ix: 1 << bit}
                self._test_instruction(operation, data, 23, reg_in, reg_out, sna_in, sna_out)

    def test_rl(self):
        self._test_rotate_shift('RL', 16, (
            # Operand in, F in, operand out, F out
            #       SZ5H3PNC         SZ5H3PNC
            (64,  0b00000000, 128, 0b10000000),
            (128, 0b00000000, 0,   0b01000101),
            (1,   0b00000001, 3,   0b00000100),
        ))

    def test_rl_with_dest_reg(self):
        for i, reg in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'RL (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, 0x10 + i)
            ix = 32768
            at_ix = 35
            reg_in = {'IX': ix, 'F': 0b00000001}
            reg_out = {reg: (at_ix << 1) + 1, 'F': 0b00000100}
            sna_in = {ix: at_ix}
            self._test_instruction(operation, data, 23, reg_in, reg_out, sna_in)

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
        for i, reg in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'RLC (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, i)
            ix = 32768
            at_ix = 35
            reg_in = {'IX': ix, 'F': 0b00000001}
            reg_out = {reg: at_ix << 1, 'F': 0b00000000}
            sna_in = {ix: at_ix}
            self._test_instruction(operation, data, 23, reg_in, reg_out, sna_in)

    def test_rr(self):
        self._test_rotate_shift('RR', 24, (
            # Operand in, F in, operand out, F out
            #     SZ5H3PNC         SZ5H3PNC
            (2, 0b00000000, 1,   0b00000000),
            (1, 0b00000000, 0,   0b01000101),
            (4, 0b00000001, 130, 0b10000100),
        ))

    def test_rr_with_dest_reg(self):
        for i, reg in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'RR (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, 0x18 + i)
            ix = 32768
            at_ix = 34
            reg_in = {'IX': ix, 'F': 0b00000001}
            reg_out = {reg: 0x80 + (at_ix >> 1), 'F': 0b10000000}
            sna_in = {ix: at_ix}
            self._test_instruction(operation, data, 23, reg_in, reg_out, sna_in)

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
        for i, reg in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'RRC (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, 0x08 + i)
            ix = 32768
            at_ix = 34
            reg_in = {'IX': ix, 'F': 0b00000001}
            reg_out = {reg: at_ix >> 1, 'F': 0b00000100}
            sna_in = {ix: at_ix}
            self._test_instruction(operation, data, 23, reg_in, reg_out, sna_in)

    def test_sla(self):
        self._test_rotate_shift('SLA', 32, (
            # Operand in, F in, operand out, F out
            #       SZ5H3PNC         SZ5H3PNC
            (64,  0b00000000, 128, 0b10000000),
            (128, 0b00000000, 0,   0b01000101),
            (1,   0b00000001, 2,   0b00000000),
        ))

    def test_sla_with_dest_reg(self):
        for i, reg in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'SLA (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, 0x20 + i)
            ix = 32768
            at_ix = 35
            reg_in = {'IX': ix}
            reg_out = {reg: at_ix << 1}
            sna_in = {ix: at_ix}
            self._test_instruction(operation, data, 23, reg_in, reg_out, sna_in)

    def test_sll(self):
        self._test_rotate_shift('SLL', 48, (
            # Operand in, F in, operand out, F out
            #       SZ5H3PNC         SZ5H3PNC
            (64,  0b00000000, 129, 0b10000100),
            (128, 0b01000000, 1,   0b00000001),
            (1,   0b00000001, 3,   0b00000100),
        ))

    def test_sll_with_dest_reg(self):
        for i, reg in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'SLL (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, 0x30 + i)
            ix = 32768
            at_ix = 35
            reg_in = {'IX': ix}
            reg_out = {reg: (at_ix << 1) + 1, 'F': 0b00000100}
            sna_in = {ix: at_ix}
            self._test_instruction(operation, data, 23, reg_in, reg_out, sna_in)

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
        for i, reg in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'SRA (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, 0x28 + i)
            ix = 32768
            at_ix = 35
            reg_in = {'IX': ix}
            reg_out = {reg: at_ix >> 1, 'F': 0b00000101}
            sna_in = {ix: at_ix}
            self._test_instruction(operation, data, 23, reg_in, reg_out, sna_in)

    def test_srl(self):
        self._test_rotate_shift('SRL', 56, (
            # Operand in, F in, operand out, F out
            #     SZ5H3PNC       SZ5H3PNC
            (2, 0b00000000, 1, 0b00000000),
            (1, 0b00000000, 0, 0b01000101),
            (4, 0b00000001, 2, 0b00000000),
        ))

    def test_srl_with_dest_reg(self):
        for i, reg in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'SRL (IX+$00),{reg}'
            data = (0xDD, 0xCB, 0x00, 0x38 + i)
            ix = 32768
            at_ix = 35
            reg_in = {'IX': ix}
            reg_out = {reg: at_ix >> 1, 'F': 0b00000101}
            sna_in = {ix: at_ix}
            self._test_instruction(operation, data, 23, reg_in, reg_out, sna_in)

    def test_rla(self):
        for a_in, f_in, a_out, f_out in (
                # A in, F in, A out, F out
                #       SZ5H3PNC         SZ5H3PNC
                (64,  0b00000000, 128, 0b00000000),
                (128, 0b00000000, 0,   0b00000001),
                (1,   0b00000001, 3,   0b00000000),
        ):
            reg_in = {'A': a_in, 'F': f_in}
            reg_out = {'A': a_out, 'F': f_out}
            self._test_instruction('RLA', [23], 4, reg_in, reg_out)

    def test_rlca(self):
        for a_in, f_in, a_out, f_out in (
                # A in, F in, A out, F out
                #       SZ5H3PNC         SZ5H3PNC
                (64,  0b00000000, 128, 0b00000000),
                (128, 0b00000000, 1,   0b00000001),
                (1,   0b00000001, 2,   0b00000000),
                (0,   0b00000001, 0,   0b00000000),
        ):
            reg_in = {'A': a_in, 'F': f_in}
            reg_out = {'A': a_out, 'F': f_out}
            self._test_instruction('RLCA', [7], 4, reg_in, reg_out)

    def test_rra(self):
        for a_in, f_in, a_out, f_out in (
                # A in, F in, A out, F out
                #     SZ5H3PNC         SZ5H3PNC
                (2, 0b00000000, 1,   0b00000000),
                (1, 0b00000000, 0,   0b00000001),
                (4, 0b00000001, 130, 0b00000000),
        ):
            reg_in = {'A': a_in, 'F': f_in}
            reg_out = {'A': a_out, 'F': f_out}
            self._test_instruction('RRA', [31], 4, reg_in, reg_out)

    def test_rrca(self):
        for a_in, f_in, a_out, f_out in (
                # A in, F in, A out, F out
                #     SZ5H3PNC         SZ5H3PNC
                (2, 0b00000000, 1,   0b00000000),
                (1, 0b00000000, 128, 0b00000001),
                (4, 0b00000001, 2,   0b00000000),
                (0, 0b00000001, 0,   0b00000000),
        ):
            reg_in = {'A': a_in, 'F': f_in}
            reg_out = {'A': a_out, 'F': f_out}
            self._test_instruction('RRCA', [15], 4, reg_in, reg_out)

    def _test_inc_dec8(self, op, opcode, specs):
        hl = 49152
        for i, reg in enumerate(REGISTERS):
            data = [opcode + 8 * i]
            operation = f'{op} {reg}'
            if reg == '(HL)':
                reg_in = {'H': hl // 256, 'L': hl % 256}
                for r_in, f_in, r_out, f_out in specs:
                    reg_in.update({'F': f_in})
                    reg_out = {'F': f_out}
                    sna_in = {hl: r_in}
                    sna_out = {hl: r_out}
                    self._test_instruction(operation, data, 11, reg_in, reg_out, sna_in, sna_out)
            else:
                for r_in, f_in, r_out, f_out in specs:
                    reg_in = {reg: r_in, 'F': f_in}
                    reg_out = {reg: r_out, 'F': f_out}
                    self._test_instruction(operation, data, 4, reg_in, reg_out)

        for prefix, reg in ((0xDD, 'IX'), (0xFD, 'IY')):
            for iopcode, half in ((opcode + 32, 'h'), (opcode + 40, 'l')):
                for r_in, f_in, r_out, f_out in specs:
                    ireg = f'{reg}{half}'
                    operation = f'{op} {ireg}'
                    data = (prefix, iopcode)
                    reg_in = {'F': f_in, ireg: r_in}
                    reg_out = {'F': f_out, ireg: r_out}
                    self._test_instruction(operation, data, 8, reg_in, reg_out)

        offset = 2
        for prefix, reg, value in ((0xDD, 'IX', 32768), (0xFD, 'IY', 32769)):
            for r_in, f_in, r_out, f_out in specs:
                operation = f'{op} ({reg}+${offset:02X})'
                data = (prefix, opcode + 48, offset & 255)
                reg_in = {'F': f_in, reg: value}
                reg_out = {'F': f_out}
                sna_in = {value + offset: r_in}
                sna_out = {value + offset: r_out}
                self._test_instruction(operation, data, 23, reg_in, reg_out, sna_in, sna_out)

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

        for rr_in, rr_out in ((61276, 61275), (0, 65535)):
            for i, reg in enumerate(('BC', 'DE', 'HL', 'SP')):
                operation = f'DEC {reg}'
                data = [11 + i * 16]
                reg_in = {reg: rr_in}
                if reg == 'SP':
                    reg_out = {reg: rr_out}
                else:
                    reg_out = {reg[0]: rr_out // 256, reg[1]: rr_out % 256}
                self._test_instruction(operation, data, 6, reg_in, reg_out)

        for rr_in, rr_out in ((61276, 61275), (0, 65535)):
            for prefix, reg in ((0xDD, 'IX'), (0xFD, 'IY')):
                operation = f'DEC {reg}'
                data = (prefix, 43)
                reg_in = {reg: rr_in}
                reg_out = {reg + 'l': rr_out % 256, reg + 'h': rr_out // 256}
                self._test_instruction(operation, data, 10, reg_in, reg_out)

    def test_inc16(self):
        # INC BC/DE/HL/SP/IX/IY
        for rr_in, rr_out in ((61275, 61276), (65535, 0)):
            for i, reg in enumerate(('BC', 'DE', 'HL', 'SP')):
                operation = f'INC {reg}'
                data = [3 + i * 16]
                reg_in = {reg: rr_in}
                if reg == 'SP':
                    reg_out = {reg: rr_out}
                else:
                    reg_out = {reg[0]: rr_out // 256, reg[1]: rr_out % 256}
                self._test_instruction(operation, data, 6, reg_in, reg_out)

        for rr_in, rr_out in ((61275, 61276), (65535, 0)):
            for prefix, reg in ((0xDD, 'IX'), (0xFD, 'IY')):
                operation = f'INC {reg}'
                data = (prefix, 35)
                reg_in = {reg: rr_in}
                reg_out = {reg + 'l': rr_out % 256, reg + 'h': rr_out // 256}
                self._test_instruction(operation, data, 10, reg_in, reg_out)

    def test_add16(self):
        # ADD HL/IX/IY,BC/DE/HL/SP/IX/IY
        for r1, r2, f_out, f_out_hl in (
                #                SZ5H3PNC    SZ5H3PNC
                (3, 1056,      0b00000000, 0b00000000),
                (32887, 45172, 0b00100001, 0b00000001)
        ):
            for i, reg in enumerate(('BC', 'DE', 'HL', 'SP')):
                operation = f'ADD HL,{reg}'
                data = [9 + i * 16]
                reg_in = {'HL': r1, 'F': 0b00000001}
                if reg == 'HL':
                    s = r1 * 2
                    reg_out = {'F': f_out_hl}
                else:
                    s = r1 + r2
                    reg_in[reg] = r2
                    reg_out = {'F': f_out}
                s &= 0xFFFF
                reg_out.update({'H': s // 256, 'L': s % 256})
                self._test_instruction(operation, data, 11, reg_in, reg_out)

            for prefix, reg in ((0xDD, 'IX'), (0xFD, 'IY')):
                for i, rr in enumerate(('BC', 'DE', 'HL', 'SP')):
                    if rr == 'HL':
                        rr = reg
                    operation = f'ADD {reg},{rr}'
                    data = [prefix, 9 + i * 16]
                    reg_in = {reg: r1, 'F': 0b00000001}
                    if rr == reg:
                        s = r1 * 2
                        reg_out = {'F': f_out_hl}
                    else:
                        s = r1 + r2
                        reg_in[rr] = r2
                        reg_out = {'F': f_out}
                    s &= 0xFFFF
                    reg_out.update({reg + 'h': s // 256, reg + 'l': s % 256})
                    self._test_instruction(operation, data, 15, reg_in, reg_out)

    def test_adc16(self):
        # ADC HL,BC/DE/HL/SP
        for r1, r2, f_in, f_out, f_out_hl in (
                #                SZ5H3PNC    SZ5H3PNC    SZ5H3PNC
                (3, 1056,      0b00000000, 0b00000000, 0b00000000),
                (3, 1056,      0b00000001, 0b00000000, 0b00000000),
                (32887, 45172, 0b00000000, 0b00100101, 0b00000101),
                (32887, 45172, 0b00000001, 0b00100101, 0b00000101)
        ):
            for i, reg in enumerate(('BC', 'DE', 'HL', 'SP')):
                operation = f'ADC HL,{reg}'
                data = (237, 74 + i * 16)
                reg_in = {'HL': r1, 'F': f_in}
                carry = f_in & 1
                if reg == 'HL':
                    s = r1 * 2 + carry
                    reg_out = {'F': f_out_hl}
                else:
                    s = r1 + r2 + carry
                    reg_in[reg] = r2
                    reg_out = {'F': f_out}
                s &= 0xFFFF
                reg_out.update({'H': s // 256, 'L': s % 256})
                self._test_instruction(operation, data, 15, reg_in, reg_out)

    def test_sbc16(self):
        # SBC HL,BC/DE/HL/SP
        for r1, r2, f_in, f_out, f_out_hl in (
                #                SZ5H3PNC    SZ5H3PNC    SZ5H3PNC
                (1056, 3,      0b00000000, 0b00000010, 0b01000010),
                (1056, 3,      0b00000001, 0b00000010, 0b10111011),
                (45172, 32887, 0b00000000, 0b00111010, 0b01000010),
                (45172, 32887, 0b00000001, 0b00111010, 0b10111011)
        ):
            for i, reg in enumerate(('BC', 'DE', 'HL', 'SP')):
                operation = f'SBC HL,{reg}'
                data = (237, 66 + i * 16)
                reg_in = {'HL': r1, 'F': f_in}
                carry = f_in & 1
                if reg == 'HL':
                    d = -carry & 65535
                    reg_out = {'F': f_out_hl}
                else:
                    reg_in[reg] = r2
                    d = (r1 - r2 - carry) & 65535
                    reg_out = {'F': f_out}
                reg_out.update({'H': d // 256, 'L': d % 256})
                self._test_instruction(operation, data, 15, reg_in, reg_out)

    def test_ld_r_n(self):
        # LD r,n (r: A, B, C, D, E, H, L, (HL))
        hl = 49152

        for i, reg in enumerate(REGISTERS):
            data = (6 + 8 * i, i)
            if reg == '(HL)':
                reg_in = {'H': hl // 256, 'L': hl % 256}
                reg_out = reg_in
                sna_in = {hl: 255}
                sna_out = {hl: i}
                self._test_instruction(f'LD {reg},${i:02X}', data, 10, reg_in, reg_out, sna_in, sna_out)
            else:
                reg_in = {reg: 255}
                reg_out = {reg: i}
                self._test_instruction(f'LD {reg},${i:02X}', data, 7, reg_in, reg_out)

    def test_ld_r_r(self):
        # LD r,r (r: A, B, C, D, E, H, L, (HL))
        hl = 32768
        r1, r2 = 12, 56

        for reg1 in REGISTERS:
            for reg2 in REGISTERS:
                if reg1 == '(HL)' and reg2 == '(HL)':
                    continue
                data = [64 + 8 * REGISTERS.index(reg1) + REGISTERS.index(reg2)]
                operation = f'LD {reg1},{reg2}'
                if reg1 == '(HL)':
                    reg_in = {'H': hl // 256, 'L': hl % 256}
                    if reg2 in 'HL':
                        r2 = reg_in[reg2]
                    else:
                        reg_in[reg2] = r2
                    sna_in = {hl: r1}
                    reg_out = reg_in
                    sna_out = {hl: r2}
                    self._test_instruction(operation, data, 7, reg_in, reg_out, sna_in, sna_out)
                elif reg2 == '(HL)':
                    reg_in = {'H': hl // 256, 'L': hl % 256}
                    if reg1 not in 'HL':
                        reg_in[reg1] = r1
                    sna_in = {hl: r2}
                    reg_out = {reg1: r2}
                    self._test_instruction(operation, data, 7, reg_in, reg_out, sna_in)
                else:
                    reg_in = {reg1: r1, reg2: r2}
                    reg_out = {reg1: r2, reg2: r2}
                    self._test_instruction(operation, data, 4, reg_in, reg_out)

    def test_ld_r_n_with_ix_iy_halves(self):
        # LD r,n (r: IXh, IXl, IYh, IYl)
        r_in, r_out = 37, 85
        for prefix, reg in ((0xDD, 'IX'), (0xFD, 'IY')):
            for opcode, half in ((38, 'h'), (46, 'l')):
                data = (prefix, opcode, r_out)
                ireg = f'{reg}{half}'
                operation = f'LD {ireg},${r_out:02X}'
                reg_in = {ireg: r_in}
                reg_out = {ireg: r_out}
                self._test_instruction(operation, data, 11, reg_in, reg_out)

    def test_ld_r_r_with_ix_iy_halves(self):
        # LD r1,r2 (r1 or r2: IXh, IXl, IYh, IYl)
        r1, r2 = 27, 99

        for reg1, reg2 in (
                ('A', 'H'), ('A', 'L'), ('H', 'A'), ('L', 'A'),
                ('B', 'H'), ('B', 'L'), ('H', 'B'), ('L', 'B'),
                ('C', 'H'), ('C', 'L'), ('H', 'C'), ('L', 'C'),
                ('D', 'H'), ('D', 'L'), ('H', 'D'), ('L', 'D'),
                ('E', 'H'), ('E', 'L'), ('H', 'E'), ('L', 'E'),
                ('H', 'H'), ('H', 'L'), ('H', 'H'), ('L', 'H'),
                ('L', 'H'), ('L', 'L'), ('H', 'L'), ('L', 'L'),
        ):
            for prefix, reg in ((0xDD, 'IX'), (0xFD, 'IY')):
                data = [prefix, 64 + 8 * REGISTERS.index(reg1) + REGISTERS.index(reg2)]
                reg_in = {}
                if reg1 in 'HL':
                    op1 = reg + reg1.lower()
                    reg_in[reg] = r1 if reg1 == 'L' else r1 * 256
                else:
                    op1 = reg1
                    reg_in[reg1] = r1
                if reg2 in 'HL':
                    op2 = reg + reg2.lower()
                    reg_in[reg] = r2 if reg2 == 'L' else r2 * 256
                else:
                    op2 = reg2
                    reg_in[reg2] = r2
                reg_out = {op1: r2, op2: r2}
                operation = f'LD {op1},{op2}'
                self._test_instruction(operation, data, 8, reg_in, reg_out)

    def test_ld_r_with_ix_iy_offsets(self):
        # LD r,(i+d); LD (i+d),r (i: IX, IY; r: A, B, C, D, E, H, L)
        offset = 5
        r1, r2 = 14, 207
        for prefix, reg, value in ((0xDD, 'IX', 32768), (0xFD, 'IY', 32769)):
            for r in ('B', 'C', 'D', 'E', 'H', 'L', 'A'):
                operation = f'LD {r},({reg}+${offset:02X})'
                data = (prefix, 0x46 + 8 * REGISTERS.index(r), offset)
                reg_in = {r: r1, reg: value}
                reg_out = {r: r2}
                sna_in = {value + offset: r2}
                self._test_instruction(operation, data, 19, reg_in, reg_out, sna_in)

        offset = 3
        r1, r2 = 142, 27
        for prefix, reg, value in ((0xDD, 'IX', 32768), (0xFD, 'IY', 32769)):
            for r in ('B', 'C', 'D', 'E', 'H', 'L', 'A'):
                operation = f'LD ({reg}+${offset:02X}),{r}'
                data = (prefix, 0x70 + REGISTERS.index(r), offset & 255)
                reg_in = {r: r2, reg: value}
                reg_out = {r: r2}
                sna_in = {value + offset: r1}
                sna_out = {value + offset: r2}
                self._test_instruction(operation, data, 19, reg_in, reg_out, sna_in, sna_out)

    def test_ld_r_with_ix_iy_offsets_across_64K_boundary(self):
        # LD r,(i+d); LD (i+d),r (i: IX, IY; r: A, B, C, D, E, H, L)
        r1, r2 = 14, 207
        for prefix, reg in ((0xDD, 'IX'), (0xFD, 'IY')):
            for value, offset in ((65535, 2), (0, -2)):
                for r in ('B', 'C', 'D', 'E', 'H', 'L', 'A'):
                    if offset < 0:
                        operand = offset + 256
                        operation = f'LD {r},({reg}-${-offset:02X})'
                    else:
                        operand = offset
                        operation = f'LD {r},({reg}+${offset:02X})'
                    data = (prefix, 0x46 + 8 * REGISTERS.index(r), operand)
                    reg_in = {r: r1, reg: value}
                    reg_out = {r: r2}
                    sna_in = {(value + offset) & 0xFFFF: r2}
                    self._test_instruction(operation, data, 19, reg_in, reg_out, sna_in)

    def test_ld_ix_iy_d_n(self):
        # LD (IX+d),n; LD (IY+d),n
        offset, n = 7, 21
        for prefix, reg, value in ((0xDD, 'IX', 32768), (0xFD, 'IY', 32769)):
            operation = f'LD ({reg}+${offset:02X}),${n:02X}'
            data = (prefix, 0x36, offset & 255, n)
            reg_in = {reg: value}
            reg_out = {}
            sna_in = {value + offset: 255}
            sna_out = {value + offset: n}
            self._test_instruction(operation, data, 19, reg_in, reg_out, sna_in, sna_out)

    def test_ld_a_addr(self):
        # LD (nn),A; LD A,(nn)
        a, addr, n = 5, 41278, 17

        operation = f'LD (${addr:04X}),A'
        data = (50, addr % 256, addr // 256)
        reg_in = reg_out = {'A': a}
        sna_in = {addr: n}
        sna_out = {addr: a}
        self._test_instruction(operation, data, 13, reg_in, reg_out, sna_in, sna_out)

        operation = f'LD A,(${addr:04X})'
        data = (58, addr % 256, addr // 256)
        reg_in = {'A': a}
        reg_out = {'A': n}
        sna_in = sna_out = {addr: n}
        self._test_instruction(operation, data, 13, reg_in, reg_out, sna_in, sna_out)

    def test_ld_a_bc_de(self):
        # LD A,(BC); LD (BC),A; LD A,(DE); LD (DE),A
        r1, r2, rr = 39, 102, 30000
        for opcode, reg1, reg2 in (
                (2, '(BC)', 'A'),
                (10, 'A', '(BC)'),
                (18, '(DE)', 'A'),
                (26, 'A', '(DE)'),
        ):
            operation = f'LD {reg1},{reg2}'
            data = [opcode]
            if reg1 == 'A':
                reg_in = {'A': r1, reg2[1]: rr // 256, reg2[2]: rr % 256}
                reg_out = {'A': r2}
                sna_in = {rr: r2}
                sna_out = {}
            else:
                reg_in = reg_out = {'A': r2, reg1[1]: rr // 256, reg1[2]: rr % 256}
                sna_in = {rr: r1}
                sna_out = {rr: r2}
            self._test_instruction(operation, data, 7, reg_in, reg_out, sna_in, sna_out)

    def test_ld_a_special(self):
        # LD A,I; LD A,R
        a = 29
        for opcode, reg in ((87, 'I'), (95, 'R')):
            for r_in, f_in, f_out in (
                    # I/R   SZ5H3PNC    SZ5H3PNC
                    (128, 0b00010110, 0b10000000),
                    (0,   0b00000100, 0b01000000),
            ):
                operation = f'LD A,{reg}'
                data = (237, opcode)
                reg_in = {'A': a, 'F': f_in, reg: r_in}
                reg_out = {'A': r_in, 'F': f_out}
                self._test_instruction(operation, data, 9, reg_in, reg_out)

    def test_ld_special_a(self):
        # LD I,A; LD R,A
        r, a = 2, 99
        for opcode, reg, r_out in (
                (71, 'I', a),
                (79, 'R', a + 2)
        ):
            operation = f'LD {reg},A'
            data = (237, opcode)
            reg_in = {reg: r, 'A': a}
            reg_out = {reg: r_out}
            self._test_instruction(operation, data, 9, reg_in, reg_out)

    def test_ld_rr_nn(self):
        lsb, msb = 3, 6

        for i, reg in enumerate(('BC', 'DE', 'HL', 'SP')):
            operation = f'LD {reg},${lsb + 256 * msb:04X}'
            data = (1 + i * 16, lsb, msb)
            reg_in = {reg: 0}
            if reg == 'SP':
                reg_out = {reg: lsb + 256 * msb}
            else:
                reg_out = {reg[1]: lsb, reg[0]: msb}
            self._test_instruction(operation, data, 10, reg_in, reg_out)

        for prefix, reg in ((0xDD, 'IX'), (0xFD, 'IY')):
            operation = f'LD {reg},${lsb + 256 * msb:04X}'
            data = (prefix, 33, lsb, msb)
            reg_in = {reg: 0}
            reg_out = {reg + 'l': lsb, reg + 'h': msb}
            self._test_instruction(operation, data, 14, reg_in, reg_out)

    def test_ld_addr_rr(self):
        # LD (nn),BC/DE/HL/SP/IX/IY
        rr, addr, nn = 35622, 52451, 257

        for opcodes, reg, timing in (
                ((237, 67), 'BC', 20),
                ((237, 83), 'DE', 20),
                ((34,), 'HL', 16),
                ((237, 115), 'SP', 20)
        ):
            operation = f'LD (${addr:04X}),{reg}'
            data = opcodes + (addr % 256, addr // 256)
            reg_in = {reg: rr}
            reg_out = {}
            sna_in = {addr: nn % 256, addr + 1: nn // 256}
            sna_out = {addr: rr % 256, addr + 1: rr // 256}
            self._test_instruction(operation, data, timing, reg_in, reg_out, sna_in, sna_out)

        for prefix, reg in ((0xDD, 'IX'), (0xFD, 'IY')):
            operation = f'LD (${addr:04X}),{reg}'
            data = (prefix, 34, addr % 256, addr // 256)
            reg_in = {reg: rr}
            reg_out = {}
            sna_in = {addr: nn % 256, addr + 1: nn // 256}
            sna_out = {addr: rr % 256, addr + 1: rr // 256}
            self._test_instruction(operation, data, 20, reg_in, reg_out, sna_in, sna_out)

    def test_ld_rr_addr(self):
        # LD BC/DE/HL/SP/IX/IY,(nn)
        rr, addr, nn = 35622, 52451, 41783

        for opcodes, reg, timing in (
                ((237, 75), 'BC', 20),
                ((237, 91), 'DE', 20),
                ((42,), 'HL', 16),
                ((237, 123), 'SP', 20)
        ):
            operation = f'LD {reg},(${addr:04X})'
            data = opcodes + (addr % 256, addr // 256)
            reg_in = {reg: rr}
            if reg == 'SP':
                reg_out = {reg: nn}
            else:
                reg_out = {reg[0]: nn // 256, reg[1]: nn % 256}
            sna_in = {addr: nn % 256, addr + 1: nn // 256}
            self._test_instruction(operation, data, timing, reg_in, reg_out, sna_in)

        for prefix, reg in ((0xDD, 'IX'), (0xFD, 'IY')):
            operation = f'LD {reg},(${addr:04X})'
            data = (prefix, 42, addr % 256, addr // 256)
            reg_in = {reg: rr}
            reg_out = {reg + 'l': nn % 256, reg + 'h': nn // 256}
            sna_in = {addr: nn % 256, addr + 1: nn // 256}
            self._test_instruction(operation, data, 20, reg_in, reg_out, sna_in)

    def test_ld_sp_rr(self):
        # LD SP,HL/IX/IY
        sp, rr = 0, 55731

        operation = 'LD SP,HL'
        data = [249]
        reg_in = {'SP': sp, 'HL': rr}
        reg_out = {'SP': rr}
        self._test_instruction(operation, data, 6, reg_in, reg_out)

        for prefix, reg in ((0xDD, 'IX'), (0xFD, 'IY')):
            operation = f'LD SP,{reg}'
            data = (prefix, 249)
            reg_in = {'SP': sp, reg: rr}
            reg_out = {'SP': rr}
            self._test_instruction(operation, data, 10, reg_in, reg_out)

    def test_pop(self):
        # POP BC/DE/HL/AF/IX/IY
        sp = 49152

        r_in, r_out = 257, 51421
        for i, reg in enumerate(('BC', 'DE', 'HL', 'AF')):
            operation = f'POP {reg}'
            data = [193 + 16 * i]
            reg_in = {reg[1]: r_in % 256, reg[0]: r_in // 256, 'SP': sp}
            reg_out = {reg[1]: r_out % 256, reg[0]: r_out // 256, 'SP': sp + 2}
            sna_in = {sp: r_out % 256, sp + 1: r_out // 256}
            self._test_instruction(operation, data, 10, reg_in, reg_out, sna_in)

        for prefix, reg in ((0xDD, 'IX'), (0xFD, 'IY')):
            operation = f'POP {reg}'
            data = (prefix, 225)
            reg_in = {'SP': sp, reg: r_in}
            reg_out = {reg + 'h': r_out // 256, reg + 'l': r_out % 256, 'SP': sp + 2}
            sna_in = {sp: r_out % 256, sp + 1: r_out // 256}
            self._test_instruction(operation, data, 14, reg_in, reg_out, sna_in)

    def test_push(self):
        # PUSH BC/DE/HL/AF/IX/IY
        sp = 49152

        r_in, r_out = 257, 51421
        for i, reg in enumerate(('BC', 'DE', 'HL', 'AF')):
            operation = f'PUSH {reg}'
            data = [197 + 16 * i]
            reg_in = {reg[1]: r_in % 256, reg[0]: r_in // 256, 'SP': sp}
            reg_out = {'SP': sp - 2}
            sna_in = {sp - 1: r_out // 256, sp - 2: r_out % 256}
            sna_out = {sp - 1: r_in // 256, sp - 2: r_in % 256}
            self._test_instruction(operation, data, 11, reg_in, reg_out, sna_in, sna_out)

        for prefix, reg in ((0xDD, 'IX'), (0xFD, 'IY')):
            operation = f'PUSH {reg}'
            data = (prefix, 229)
            reg_in = {'SP': sp, reg: r_in}
            reg_out = {'SP': sp - 2}
            sna_in = {sp - 1: r_out // 256, sp - 2: r_out % 256}
            sna_out = {sp - 1: r_in // 256, sp - 2: r_in % 256}
            self._test_instruction(operation, data, 15, reg_in, reg_out, sna_in, sna_out)

    def test_jp_rr(self):
        # JP (HL/IX/IY)
        addr = 46327
        for prefix, reg in ((0, 'HL'), (0xDD, 'IX'), (0xFD, 'IY')):
            operation = f'JP ({reg})'
            if prefix:
                data = (prefix, 233)
                timing = 8
            else:
                data = [233]
                timing = 4
            reg_in = {reg: addr}
            self._test_instruction(operation, data, timing, reg_in, end=addr)

    def test_jr_nn(self):
        start = 30000
        for offset in (13, -45):
            addr = start + 2 + offset
            operation = f'JR ${addr:04X}'
            data = (24, offset if offset >= 0 else offset + 256)
            self._test_instruction(operation, data, 12, start=start, end=addr)

    def test_jr_conditional(self):
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
                reg_in = {'F': flags}
                self._test_instruction(operation, data, timing, reg_in, start=start, end=end)

    def test_jr_jumping_across_64K_boundary(self):
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
            reg_in = {'F': flags}
            self._test_instruction(operation, data, timing, reg_in, start=start, end=end)

    def test_call_nn(self):
        start = 30000
        addr = 51426
        sp = 23456
        operation = f'CALL ${addr:04X}'
        data = (205, addr % 256, addr // 256)
        reg_in = {'SP': sp}
        reg_out = {'SP': sp - 2}
        sna_out = {sp - 1: (start + 3) // 256, sp - 2: (start + 3) % 256}
        self._test_instruction(operation, data, 17, reg_in, reg_out, sna_out=sna_out, start=start, end=addr)

    def test_call_conditional(self):
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
            reg_in = {'F': flags, 'SP': sp}
            if end == addr:
                timing = 17
                reg_out = {'SP': sp - 2}
                sna_out = {sp - 1: (start + 3) // 256, sp - 2: (start + 3) % 256}
            else:
                timing = 10
                reg_out = None
                sna_out = None
            data = (opcode, addr % 256, addr // 256)
            self._test_instruction(operation, data, timing, reg_in, reg_out, sna_out=sna_out, start=start, end=end)

    def test_jp_nn(self):
        start = 30000
        addr = 51426
        operation = f'JP ${addr:04X}'
        data = (195, addr % 256, addr // 256)
        self._test_instruction(operation, data, 10, start=start, end=addr)

    def test_jp_conditional(self):
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
            reg_in = {'F': flags}
            data = (opcode, addr % 256, addr // 256)
            self._test_instruction(operation, data, 10, reg_in, start=start, end=end)

    def test_ret(self):
        start = 40000
        end = 45271
        sp = 32517
        operation = 'RET'
        data = [201]
        reg_in = {'SP': sp}
        reg_out = {'SP': sp + 2}
        sna_in = {sp: end % 256, sp + 1: end // 256}
        self._test_instruction(operation, data, 10, reg_in, reg_out, sna_in, start=start, end=end)

    def test_ret_conditional(self):
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
            reg_in = {'SP': sp, 'F': flags}
            if end == addr:
                timing = 11
                reg_out = {'SP': sp + 2}
            else:
                timing = 5
                reg_out = None
            sna_in = {sp: addr % 256, sp + 1: addr // 256}
            self._test_instruction(operation, data, timing, reg_in, reg_out, sna_in, start=start, end=end)

    def test_rst(self):
        start = 30000
        sp = 23456
        for addr in range(0, 64, 8):
            operation = f'RST ${addr:02X}'
            data = [199 + addr]
            reg_in = {'SP': sp}
            reg_out = {'SP': sp - 2}
            sna_out = {sp - 1: (start + 1) // 256, sp - 2: (start + 1) % 256}
            self._test_instruction(operation, data, 11, reg_in, reg_out, sna_out=sna_out, start=start, end=addr)

    def test_nop(self):
        operation = 'NOP'
        data = [0]
        self._test_instruction(operation, data, 4)

    def test_cpl(self):
        operation = 'CPL'
        data = [47]
        for a_in, f_in, f_out in (
                #       SZ5H3PNC    SZ5H3PNC
                (154, 0b01000000, 0b01110010),
                (0,   0b00000000, 0b00111010),
        ):
            reg_in = {'A': a_in, 'F': f_in}
            reg_out = {'A': a_in ^ 255, 'F': f_out}
            self._test_instruction(operation, data, 4, reg_in, reg_out)

    def test_out_n_a(self):
        a = 128
        n = 56
        operation = f'OUT (${n:02X}),A'
        data = (211, 56)
        reg_in = {'A': a}
        self._test_instruction(operation, data, 11, reg_in)

    def test_out_c_r(self):
        c = 128
        r = 56
        for i, reg in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'OUT (C),{reg}'
            data = (237, 65 + i * 8)
            reg_in = {'C': c, reg: r}
            self._test_instruction(operation, data, 12, reg_in)

    def test_out_c_0(self):
        operation = 'OUT (C),0'
        data = (0xED, 0x71)
        self._test_instruction(operation, data, 12)

    def test_in_a_n(self):
        n = 56
        operation = f'IN A,(${n:02X})'
        data = (0xDB, n)
        reg_out = {'A': 191}
        self._test_instruction(operation, data, 11, reg_out=reg_out)

    def test_in_r_c(self):
        tracer = InTestTracer()
        in_value = 0
        c = 128
        for i, reg in enumerate(REGISTERS):
            if reg == '(HL)':
                continue
            operation = f'IN {reg},(C)'
            data = (237, 64 + i * 8)
            reg_in = {'C': c}
            tracer.value = in_value
            reg_out = {reg: in_value}
            if in_value == 0:
                reg_out['F'] = 0b01000100
            else:
                reg_out['F'] = 0b10101100
            in_value ^= 255
            self._test_instruction(operation, data, 12, reg_in, reg_out, tracer=tracer)

    def test_in_f_c(self):
        operation = f'IN F,(C)'
        data = (0xED, 0x70)
        reg_out = {'F': 0b10101000}
        self._test_instruction(operation, data, 12, reg_out=reg_out)

    def test_djnz(self):
        addr = 35732
        for b, timing, end in ((34, 13, addr), (1, 8, addr + 2)):
            operation = f'DJNZ ${addr:04X}'
            data = (16, 254)
            reg_in = {'B': b}
            reg_out = {'B': b - 1}
            self._test_instruction(operation, data, timing, reg_in, reg_out, start=addr, end=end)

    def test_djnz_jumping_across_64K_boundary(self):
        for start, offset, end in (
                (65532, 12, 10),     # $FFFC DJNZ $000A
                (0,     -3, 65535),  # $0000 DJNZ $FFFF
        ):
            operation = f'DJNZ ${end:04X}'
            data = (16, offset if offset >= 0 else offset + 256)
            timing = 13
            reg_in = {'B': 2}
            reg_out = {'B': 1}
            self._test_instruction(operation, data, timing, reg_in, reg_out, start=start, end=end)

    def test_djnz_fast(self):
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
            reg_in = {'B': b_in, 'R': 0}
            reg_out = {'B': b_out, 'R': r_out}
            self._test_instruction(operation, data, timing, reg_in, reg_out, start=start, end=end, config={'fast_djnz': True})

    def test_di(self):
        operation = 'DI'
        data = [243]
        state_in = {'iff': 1}
        state_out = {'iff': 0}
        self._test_instruction(operation, data, 4, state_in=state_in, state_out=state_out)

    def test_ei(self):
        operation = 'EI'
        data = [251]
        state_in = {'iff': 0}
        state_out = {'iff': 1}
        self._test_instruction(operation, data, 4, state_in=state_in, state_out=state_out)

    def test_halt(self):
        snapshot = [0] * 65536
        start = 40000
        snapshot[start] = 0x76
        simulator = Simulator(snapshot)
        tracer = Tracer()
        simulator.add_tracer(tracer)
        simulator.run(start)
        self.assertEqual(tracer.operation, 'HALT')

    def test_halt_repeats_until_frame_boundary(self):
        snapshot = [0] * 65536
        start = 40000
        snapshot[start] = 0x76
        simulator = Simulator(snapshot, state={'iff': 1, 'tstates': 69882})
        simulator.run(start)
        self.assertEqual(simulator.pc, start)
        simulator.run()
        self.assertEqual(simulator.pc, start + 1)

    def test_halt_repeats_at_frame_boundary_when_interrupts_disabled(self):
        snapshot = [0] * 65536
        start = 40000
        snapshot[start] = 0x76
        simulator = Simulator(snapshot, state={'iff': 0, 'tstates': 69882})
        simulator.run(start)
        self.assertEqual(simulator.pc, start)
        simulator.run()
        self.assertEqual(simulator.pc, start)

    def test_ccf(self):
        operation = 'CCF'
        data = [63]
        for f_in, f_out in (
                #  SZ5H3PNC    SZ5H3PNC
                (0b00010000, 0b00000001),
                (0b00000011, 0b00010000),
        ):
            reg_in = {'F': f_in}
            reg_out = {'F': f_out}
            self._test_instruction(operation, data, 4, reg_in, reg_out)

    def test_scf(self):
        operation = 'SCF'
        data = [55]
        for f_in, f_out in (
                #  SZ5H3PNC    SZ5H3PNC
                (0b00010000, 0b00000001),
                (0b00000011, 0b00000001),
        ):
            reg_in = {'F': f_in}
            reg_out = {'F': f_out}
            self._test_instruction(operation, data, 4, reg_in, reg_out)

    def _test_cpd_cpi(self, operation, opcode, inc, specs):
        data = (237, opcode)
        hl = 45287
        bc = 121

        for a, at_hl, f_out in specs:
            reg_in = {'A': a, 'BC': bc, 'HL': hl}
            reg_out = {
                'B': (bc - 1) // 256,
                'C': (bc - 1) % 256,
                'H': (hl + inc) // 256,
                'L': (hl + inc) % 256,
                'F': f_out
            }
            sna_in = {hl: at_hl}
            self._test_instruction(operation, data, 16, reg_in, reg_out, sna_in)

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
            reg_in = {'A': a, 'BC': bc, 'HL': hl}
            reg_out = {
                'B': (bc - 1) // 256,
                'C': (bc - 1) % 256,
                'H': (hl + inc) // 256,
                'L': (hl + inc) % 256,
                'F': f_out
            }
            sna_in = {hl: at_hl}
            self._test_instruction(operation, data, timing, reg_in, reg_out, sna_in, start=start, end=end)

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
        data = (237, opcode)
        hl = 45287
        start = 34177

        for b, f_out in (
                #     SZ5H3PNC
                (2, 0b00000110),
                (1, 0b01000010),
                (0, 0b10101010),
        ):
            end = start + 2
            timing = 16
            if repeat and b != 1:
                timing = 21
                end = start
            reg_in = {'B': b, 'C': 1, 'HL': hl}
            reg_out = {
                'B': (b - 1) & 255,
                'H': (hl + inc) // 256,
                'L': (hl + inc) % 256,
                'F': f_out
            }
            sna_out = {hl: 191}
            self._test_instruction(operation, data, timing, reg_in, reg_out, sna_out=sna_out, start=start, end=end)

    def test_ind(self):
        self._test_block_in('IND', 170, -1)

    def test_ini(self):
        self._test_block_in('INI', 162, 1)

    def test_indr(self):
        self._test_block_in('INDR', 186, -1, True)

    def test_inir(self):
        self._test_block_in('INIR', 178, 1, True)

    def _test_block_ld(self, operation, opcode, inc, repeat=False):
        data = (237, opcode)
        hl = 31664
        de = 45331
        start = 54112
        at_hl = 147

        for bc, f_out in (
                #     SZ5H3PNC
                (2, 0b00100100),
                (1, 0b00100000),
                (0, 0b00100100)
        ):
            end = start + 2
            timing = 16
            if repeat and bc != 1:
                timing = 21
                end = start
            reg_in = {'BC': bc, 'DE': de, 'HL': hl}
            bc_out = (bc - 1) & 65535
            reg_out = {
                'B': bc_out // 256,
                'C': bc_out % 256,
                'D': (de + inc) // 256,
                'E': (de + inc) % 256,
                'H': (hl + inc) // 256,
                'L': (hl + inc) % 256,
                'F': f_out
            }
            sna_in = {hl: at_hl}
            sna_out = {de: at_hl}
            self._test_instruction(operation, data, timing, reg_in, reg_out, sna_in, sna_out, start, end)

    def test_ldd(self):
        self._test_block_ld('LDD', 168, -1)

    def test_ldi(self):
        self._test_block_ld('LDI', 160, 1)

    def test_lddr(self):
        self._test_block_ld('LDDR', 184, -1, True)

    def test_ldir(self):
        self._test_block_ld('LDIR', 176, 1, True)

    def test_lddr_fast(self):
        data = (0xED, 0xB8)
        start = 30000
        at_hl = 250
        for bc_in, bc_out, de_in, de_out, hl_in, hl_out, f_out, r_out, timing, end in (
                #                                     SZ5H3PNC
                (52, 1, 30051, 30000, 40000, 39949, 0b00101100, 102,    1066, start),     # 0xB8 overwritten
                (51, 0, 30051, 30000, 40000, 39949, 0b00101000, 102,    1066, start + 2), # 0xB8 overwritten
                (50, 0, 30051, 30001, 40000, 39950, 0b00101000, 100,    1045, start + 2),
                ( 1, 0, 30051, 30050, 40000, 39999, 0b00101000,   2,      16, start + 2),
                ( 0, 1, 29999, 30000, 29999, 30000, 0b00001100, 126, 1376230, start),     # 0xB8 overwritten
        ):
            reg_in = {'BC': bc_in, 'DE': de_in, 'HL': hl_in, 'R': 0}
            reg_out = {}
            reg_out = {
                'B': bc_out // 256,
                'C': bc_out % 256,
                'D': de_out // 256,
                'E': de_out % 256,
                'H': hl_out // 256,
                'L': hl_out % 256,
                'F': f_out,
                'R': r_out
            }
            if bc_in:
                mem_read = list(range(hl_out + 1, hl_in + 1))
                sna_in = {a: at_hl for a in mem_read}
                mem_written = list(range(de_out + 1, de_in + 1))
                sna_out = {a: at_hl for a in mem_written}
                read_tracer = ReadMemoryTracer()
                write_tracer = WriteMemoryTracer()
                tracers = (read_tracer, write_tracer)
            else:
                sna_in = sna_out = None
                tracers = None
            self._test_instruction('LDDR', data, timing, reg_in, reg_out, sna_in, sna_out, start, end, tracer=tracers, config={'fast_ldir': True})
            if tracers:
                self.assertEqual([e[0] for e in reversed(read_tracer.read)], mem_read)
                self.assertEqual([e[0] for e in reversed(write_tracer.written)], mem_written)

    def test_ldir_fast(self):
        data = (0xED, 0xB0)
        start = 30000
        at_hl = 250
        for bc_in, bc_out, de_in, de_out, hl_in, hl_out, f_out, r_out, timing, end in (
                #                                     SZ5H3PNC
                (52, 1, 29950, 30001, 40000, 40051, 0b00101100, 102,    1066, start),     # 0xED overwritten
                (51, 0, 29950, 30001, 40000, 40051, 0b00101000, 102,    1066, start + 2), # 0xED overwritten
                (50, 0, 29950, 30000, 40000, 40050, 0b00101000, 100,    1045, start + 2),
                ( 1, 0, 29950, 29951, 40000, 40001, 0b00101000,   2,      16, start + 2),
                ( 0, 1, 30002, 30001, 30002, 30001, 0b00001100, 126, 1376230, start),     # 0xED overwritten
        ):
            reg_in = {'BC': bc_in, 'DE': de_in, 'HL': hl_in, 'R': 0}
            reg_out = {}
            reg_out = {
                'B': bc_out // 256,
                'C': bc_out % 256,
                'D': de_out // 256,
                'E': de_out % 256,
                'H': hl_out // 256,
                'L': hl_out % 256,
                'F': f_out,
                'R': r_out
            }
            if bc_in:
                mem_read = list(range(hl_in, hl_out))
                sna_in = {a: at_hl for a in mem_read}
                mem_written = list(range(de_in, de_out))
                sna_out = {a: at_hl for a in mem_written}
                read_tracer = ReadMemoryTracer()
                write_tracer = WriteMemoryTracer()
                tracers = (read_tracer, write_tracer)
            else:
                sna_in = sna_out = None
                tracers = None
            self._test_instruction('LDIR', data, timing, reg_in, reg_out, sna_in, sna_out, start, end, tracer=tracers, config={'fast_ldir': True})
            if tracers:
                self.assertEqual([e[0] for e in read_tracer.read], mem_read)
                self.assertEqual([e[0] for e in write_tracer.written], mem_written)

    def _test_block_out(self, operation, opcode, inc, repeat=False):
        data = (237, opcode)
        hl = 45287
        start = 41772

        for b, outval, f_out in (
                #          SZ5H3PNC
                (2, 0,   0b00000000),
                (1, 128, 0b01010111),
                (0, 0,   0b10101100),
        ):
            end = start + 2
            timing = 16
            if repeat and b != 1:
                timing = 21
                end = start
            reg_in = {'B': b, 'HL': hl}
            reg_out = {
                'B': (b - 1) & 255,
                'H': (hl + inc) // 256,
                'L': (hl + inc) % 256,
                'F': f_out
            }
            sna_in = {hl: outval}
            self._test_instruction(operation, data, timing, reg_in, reg_out, sna_in, start=start, end=end)

    def test_outd(self):
        self._test_block_out('OUTD', 171, -1)

    def test_outi(self):
        self._test_block_out('OUTI', 163, 1)

    def test_otdr(self):
        self._test_block_out('OTDR', 187, -1, True)

    def test_otir(self):
        self._test_block_out('OTIR', 179, 1, True)

    def test_ex_sp(self):
        sp1, sp2 = 27, 231
        r1, r2 = 56, 89
        for prefix, reg in (((), 'HL'), ((0xDD,), 'IX'), ((0xFD,), 'IY')):
            for sp in (63312, 65535):
                operation = f'EX (SP),{reg}'
                data = prefix + (227,)
                timing = 23 if prefix else 19
                reg_in = {'SP': sp, reg: r1 + 256 * r2}
                if reg == 'HL':
                    reg_out = {'L': sp1, 'H': sp2}
                else:
                    reg_out = {reg + 'l': sp1, reg + 'h': sp2}
                sna_in = {sp: sp1, (sp + 1) & 0xFFFF: sp2}
                sna_out = {sp: r1}
                sp = (sp + 1) & 0xFFFF
                if sp > 0x3FFF:
                    sna_out[sp] = r2
                self._test_instruction(operation, data, timing, reg_in, reg_out, sna_in, sna_out)

    def test_exx(self):
        operation = 'EXX'
        data = [217]
        bc, de, hl = 36711, 5351, 16781
        xbc, xde, xhl = 35129, 61121, 41113
        reg_in = {'BC': bc, 'DE': de, 'HL': hl, '^BC': xbc, '^DE': xde, '^HL': xhl}
        reg_out = {
            'B': xbc // 256, '^B': bc // 256,
            'C': xbc % 256, '^C': bc % 256,
            'D': xde // 256, '^D': de // 256,
            'E': xde % 256, '^E': de % 256,
            'H': xhl // 256, '^H': hl // 256,
            'L': xhl % 256, '^L': hl % 256,
        }
        self._test_instruction(operation, data, 4, reg_in, reg_out)

    def test_ex_af(self):
        operation = "EX AF,AF'"
        data = [8]
        a, f = 4, 154
        xa, xf = 37, 17
        reg_in = {'A': a, 'F': f, '^A': xa, '^F': xf}
        reg_out = {'A': xa, 'F': xf, '^A': a, '^F': f}
        self._test_instruction(operation, data, 4, reg_in, reg_out)

    def test_ex_de_hl(self):
        operation = 'EX DE,HL'
        data = [235]
        de, hl = 28812, 56117
        reg_in = {'DE': de, 'HL': hl}
        reg_out = {'D': hl // 256, 'E': hl % 256, 'H': de // 256, 'L': de % 256}
        self._test_instruction(operation, data, 4, reg_in, reg_out)

    def test_neg(self):
        operation = 'NEG'
        for opcode in (0x44, 0x4C, 0x54, 0x5C, 0x64, 0x6C, 0x74, 0x7C):
            data = (0xED, opcode)
            for a_in in range(256):
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
                reg_in = {'A': a_in}
                reg_out = {'A': a_out, 'F': f_out}
                self._test_instruction(operation, data, 8, reg_in, reg_out)

    def test_ret_from_interrupt(self):
        start = 40000
        end = 45271
        sp = 32517
        for operation, opcodes in (
                ('RETN', (0x45, 0x55, 0x5D, 0x65, 0x6D, 0x75, 0x7D)),
                ('RETI', (0x4D,))
        ):
            for opcode in opcodes:
                data = (0xED, opcode)
                reg_in = {'SP': sp}
                reg_out = {'SP': sp + 2}
                sna_in = {sp: end % 256, sp + 1: end // 256}
                self._test_instruction(operation, data, 14, reg_in, reg_out, sna_in, start=start, end=end)

    def test_im_n(self):
        for mode, opcodes in (
                (0, (0x46, 0x4E, 0x66, 0x6E)),
                (1, (0x56, 0x76)),
                (2, (0x5E, 0x7E))
        ):
            for opcode in opcodes:
                operation = f'IM {mode}'
                data = (0xED, opcode)
                state_in = {'im': mode ^ 3}
                state_out = {'im': mode}
                self._test_instruction(operation, data, 8, state_in=state_in, state_out=state_out)

    def test_rld(self):
        operation = 'RLD'
        data = (237, 111)
        hl = 54672
        for a, at_hl, a_out, at_hl_out, f_out in (
                #                                                  SZ5H3PNC
                (0b10101001, 0b11000101, 0b10101100, 0b01011001, 0b10101100),
                (0b00001001, 0b00000101, 0b00000000, 0b01011001, 0b01000100),
        ):
            reg_in = {'A': a, 'HL': hl}
            reg_out = {'A': a_out, 'F': f_out}
            sna_in = {hl: at_hl}
            sna_out = {hl: at_hl_out}
            self._test_instruction(operation, data, 18, reg_in, reg_out, sna_in, sna_out)

    def test_rrd(self):
        operation = 'RRD'
        data = (237, 103)
        hl = 54672
        for a, at_hl, a_out, at_hl_out, f_out in (
                #                                                  SZ5H3PNC
                (0b10101001, 0b11000101, 0b10100101, 0b10011100, 0b10100100),
                (0b00001001, 0b11100000, 0b00000000, 0b10011110, 0b01000100),
        ):
            reg_in = {'A': a, 'HL': hl}
            reg_out = {'A': a_out, 'F': f_out}
            sna_in = {hl: at_hl}
            sna_out = {hl: at_hl_out}
            self._test_instruction(operation, data, 18, reg_in, reg_out, sna_in, sna_out)

    def test_daa(self):
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
            reg_in = {'A': 0, 'F': f_in}
            reg_out = {'A': a_out, 'F': f_out}
            self._test_instruction(operation, data, 4, reg_in, reg_out)

    def test_after_dd_fd_no_ix_iy(self):
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
                self._test_instruction(operation, data, 4, start=start, end=start + 1)

    def test_after_ed_defb(self):
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
            self._test_instruction(operation, data, 8, start=start, end=start + 2)

    def test_instruction_crossing_64K_boundary(self):
        operation = 'LD BC,$0302'
        data = (1, 2, 3)
        reg_out = {'B': 3, 'C': 2}
        self._test_instruction(operation, data, 10, reg_out=reg_out, start=65535, end=2)

    def test_no_tracer(self):
        snapshot = [0] * 65536
        simulator = Simulator(snapshot)
        simulator.run(0)
        self.assertEqual(simulator.pc, 1)
        self.assertEqual(simulator.tstates, 4)

    def test_tracer_runs_two_instructions(self):
        snapshot = [0] * 65536
        simulator = Simulator(snapshot)
        tracer = CountingTracer(2)
        simulator.add_tracer(tracer)
        simulator.run(0)
        self.assertEqual(simulator.pc, 2)
        self.assertEqual(simulator.tstates, 8)

    def test_port_reading(self):
        snapshot = [0] * 65536
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
        snapshot[start:end] = code
        simulator = Simulator(snapshot, {'A': 170, 'BC': 65311})
        value = 128
        tracer = PortTracer(value, end)
        simulator.add_tracer(tracer)
        simulator.run(start)
        exp_ports = [43774, 65311, 65311, 65055, 510, 510]
        self.assertEqual(tracer.in_ports, exp_ports)
        self.assertEqual(simulator.registers['A'], value)
        self.assertEqual(simulator.registers['D'], value)

    def test_port_writing(self):
        snapshot = [0] * 65536
        start = 49152
        port = 254
        code = (
            0xD3, 0xFE,       # OUT (254),A
            0xED, 0x79,       # OUT (C),A
            0xED, 0xA3,       # OUTI
            0xED, 0xAB,       # OUTD
            0x01, 0xFE, 0x01, # LD BC,510
            0xED, 0xB3,       # OTIR
            0x04,             # INC B
            0xED, 0xBB,       # OTDR
        )
        end = start + len(code)
        snapshot[start:end] = code
        hl = 30000
        snapshot[hl:hl + 2] = (1, 2)
        simulator = Simulator(snapshot, {'A': 171, 'BC': 65055, 'HL': hl})
        tracer = PortTracer(end=end)
        simulator.add_tracer(tracer)
        simulator.run(start)
        exp_outs = [
            (44030, 171),
            (65055, 171),
            (64799, 1),
            (64543, 2),
            (254, 1),
            (254, 2)
        ]
        self.assertEqual(tracer.out_ports, exp_outs)

    def test_memory_reading(self):
        snapshot = [0] * 65536
        start = 49152
        code = (
            0x01, 0x00, 0x80,       # 49152 LD BC,32768
            0x21, 0x01, 0x80,       # 49155 LD HL,32769
            0x0A,                   # 49158 LD A,(BC)
            0xBE,                   # 49159 CP (HL)
            0xED, 0x5B, 0x02, 0x80, # 49160 LD DE,(32770)
        )
        end = start + len(code)
        snapshot[start:end] = code
        simulator = Simulator(snapshot)
        tracer = MemoryTracer(end)
        simulator.add_tracer(tracer)
        simulator.run(start)
        exp_addresses = [
            (49158, 32768, 1),
            (49159, 32769, 1),
            (49160, 32770, 2),
        ]
        self.assertEqual(tracer.read, exp_addresses)

    def test_memory_writing(self):
        snapshot = [0] * 65536
        start = 49152
        code = (
            0x01, 0x00, 0x80,       # 49152 LD BC,32768
            0x21, 0x01, 0x80,       # 49155 LD HL,32769
            0x3E, 0xFF,             # 49158 LD A,255
            0x02,                   # 49160 LD (BC),A
            0x70,                   # 49161 LD (HL),B
            0xED, 0x43, 0x02, 0x80, # 49162 LD (32770),BC
        )
        end = start + len(code)
        snapshot[start:end] = code
        simulator = Simulator(snapshot)
        tracer = MemoryTracer(end)
        simulator.add_tracer(tracer)
        simulator.run(start)
        exp_addresses = [
            (49160, 32768, 255),
            (49161, 32769, 128),
            (49162, 32770, 0, 128),
        ]
        self.assertEqual(tracer.written, exp_addresses)

    def test_multiple_tracers(self):
        snapshot = [0] * 65536
        snapshot[32768] = 64
        code = (
            0x21, 0x00, 0x80, # 40000 LD HL,32768
            0x34,             # 40003 INC (HL)
        )
        snapshot[40000:40000 + len(code)] = code
        simulator = Simulator(snapshot)
        tracer1 = ReadMemoryTracer()
        tracer2 = WriteMemoryTracer()
        simulator.add_tracer(tracer1)
        simulator.add_tracer(tracer2)
        simulator.run(40000)
        while simulator.pc != 40004:
            simulator.run()
        self.assertEqual(tracer1.read, [(32768, 1)])
        self.assertEqual(tracer2.written, [(32768, (65,))])

    def test_rom_not_writable(self):
        snapshot = [0] * 65536
        start = 49152
        code = (
            0x21, 0x01, 0x02,       # 49152 LD HL,513
            0x22, 0xFF, 0x3F,       # 49155 LD (16383),HL
            0x22, 0xFF, 0xFF,       # 49158 LD (65535),HL
        )
        end = start + len(code)
        snapshot[start:end] = code
        simulator = Simulator(snapshot)
        tracer = MemoryTracer(end)
        simulator.add_tracer(tracer)
        simulator.run(start)
        exp_addresses = [
            (49155, 16383, 1, 2),
            (49158, 65535, 1, 2),
        ]
        self.assertEqual(tracer.written, exp_addresses)
        self.assertEqual(snapshot[0], 0)
        self.assertEqual(snapshot[0x3FFF], 0)

    def test_resume(self):
        snapshot = [0] * 65536
        simulator = Simulator(snapshot)
        simulator.run(0)
        simulator.run()
        self.assertEqual(simulator.pc, 2)
        self.assertEqual(simulator.tstates, 8)

    def test_pc_register_value(self):
        snapshot = [0] * 65536
        simulator = Simulator(snapshot, {'PC': 1})
        simulator.run()
        self.assertEqual(simulator.pc, 2)
        self.assertEqual(simulator.tstates, 4)

    def test_initial_time(self):
        snapshot = [0] * 65536
        simulator = Simulator(snapshot, state={'tstates': 100})
        simulator.run(0)
        self.assertEqual(simulator.pc, 1)
        self.assertEqual(simulator.tstates, 104)

    def test_initial_ppcount(self):
        snapshot = [0] * 65536
        code = (
            0xC1,  # POP BC
            0xC1,  # POP BC
        )
        start = 32768
        end = start + len(code)
        snapshot[start:end] = code
        simulator = Simulator(snapshot, state={'ppcount': 1})
        tracer = PushPopCountTracer()
        simulator.add_tracer(tracer)
        simulator.run(start)
        self.assertEqual(simulator.pc, end)
        self.assertEqual(simulator.ppcount, -1)

    def test_initial_iff(self):
        snapshot = [0] * 65536
        start = 32768
        snapshot[start:start + 2] = (0xED, 0x57) # LD A,I
        simulator = Simulator(snapshot, state={'iff': 1})
        simulator.run(start)
        self.assertEqual(simulator.pc, start + 2)
        self.assertEqual(simulator.registers['F'], 0b00101100)
