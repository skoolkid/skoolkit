import hashlib
import os
from textwrap import dedent
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import simulator, trace, SkoolKitError, VERSION
from skoolkit.config import COMMANDS

ROM0_MD5 = 'b4d2692115a9f2924df92a3cbfb358fb'
ROM1_MD5 = '6e09e5d3c4aef166601669feaaadc01c'

def mock_run(*args):
    global run_args
    run_args = args

def mock_config(name):
    return {k: v[0] for k, v in COMMANDS[name].items()}

def mock_write_snapshot(fname, ram, registers, state):
    global z80fname, snapshot, banks, z80reg, z80state
    z80fname = fname
    snapshot = [0] * 16384
    if len(ram) == 8:
        banks = ram
        page = 0
        for spec in state:
            if spec.startswith('7ffd='):
                page = int(spec[5:]) % 8
                break
        snapshot += ram[5] + ram[2] + ram[page]
    else:
        banks = None
        snapshot = [0] * 16384 + ram
    z80reg = registers
    z80state = state

class TestSimulator(simulator.Simulator):
    def __init__(self, memory, registers=None, state=None, config=None):
        global simulator
        simulator = self
        super().__init__(memory, registers, state, config)

class TraceTest(SkoolKitTestCase):
    def _test_trace(self, args, exp_output):
        output, error = self.run_trace(args)
        self.assertEqual(error, '')
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    @patch.object(trace, 'run', mock_run)
    def test_default_option_values(self):
        trace.main(('test.z80',))
        z80file, options, config = run_args
        self.assertEqual(z80file, 'test.z80')
        self.assertIsNone(options.start)
        self.assertIsNone(options.stop)
        self.assertFalse(options.audio)
        self.assertEqual(options.depth, 2)
        self.assertIsNone(options.dump)
        self.assertTrue(options.interrupts)
        self.assertEqual(options.max_operations, 0)
        self.assertEqual(options.max_tstates, 0)
        self.assertIsNone(options.org)
        self.assertEqual(options.params, [])
        self.assertEqual(options.pokes, [])
        self.assertEqual(options.reg, [])
        self.assertIsNone(options.rom)
        self.assertFalse(options.stats)
        self.assertEqual(options.verbose, 0)
        self.assertEqual(config['TraceLine'], '${pc:04X} {i}')
        self.assertEqual(
            config['TraceLine2'],
            "${pc:04X} {i:<15}  "
            "A={r[a]:02X}  F={r[f]:08b}  BC={r[bc]:04X}  DE={r[de]:04X}  HL={r[hl]:04X}  IX={r[ix]:04X} IY={r[iy]:04X}\\n                       "
            "A'={r[^a]:02X} F'={r[^f]:08b} BC'={r[^bc]:04X} DE'={r[^de]:04X} HL'={r[^hl]:04X} SP={r[sp]:04X} IR={r[i]:02X}{r[r]:02X}"
        )
        self.assertEqual(config['TraceLineDecimal'], '{pc:05} {i}')
        self.assertEqual(
            config['TraceLineDecimal2'],
            "{pc:05} {i:<15}  "
            "A={r[a]:<3}  F={r[f]:08b}  BC={r[bc]:<5}  DE={r[de]:<5}  HL={r[hl]:<5}  IX={r[ix]:<5} IY={r[iy]:<5}\\n                       "
            "A'={r[^a]:<3} F'={r[^f]:08b} BC'={r[^bc]:<5} DE'={r[^de]:<5} HL'={r[^hl]:<5} SP={r[sp]:<5} I={r[i]:<3} R={r[r]:<3}"
        )
        self.assertEqual(config['TraceOperand'], '$,02X,04X')
        self.assertEqual(config['TraceOperandDecimal'], ',,')

    @patch.object(trace, 'run', mock_run)
    def test_config_read_from_file(self):
        ini = """
            [trace]
            TraceLine=${pc:04x} - {i}
            TraceLine2=${pc:04x} {i} {r[a]}
            TraceLineDecimal={pc:05} - {i}
            TraceLineDecimal2={pc:05} {i} {r[a]}
            TraceOperand=&,02x,04x
            TraceOperandDecimal=,03,05
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        trace.main(('test.z80',))
        z80file, options, config = run_args
        self.assertEqual(z80file, 'test.z80')
        self.assertIsNone(options.start)
        self.assertIsNone(options.stop)
        self.assertFalse(options.audio)
        self.assertEqual(options.depth, 2)
        self.assertIsNone(options.dump)
        self.assertTrue(options.interrupts)
        self.assertEqual(options.max_operations, 0)
        self.assertEqual(options.max_tstates, 0)
        self.assertIsNone(options.org)
        self.assertEqual(options.params, [])
        self.assertEqual(options.pokes, [])
        self.assertEqual(options.reg, [])
        self.assertIsNone(options.rom)
        self.assertFalse(options.stats)
        self.assertEqual(options.verbose, 0)
        self.assertEqual(config['TraceLine'], '${pc:04x} - {i}')
        self.assertEqual(config['TraceLine2'],'${pc:04x} {i} {r[a]}')
        self.assertEqual(config['TraceLineDecimal'], '{pc:05} - {i}')
        self.assertEqual(config['TraceLineDecimal2'], '{pc:05} {i} {r[a]}')
        self.assertEqual(config['TraceOperand'], '&,02x,04x')
        self.assertEqual(config['TraceOperandDecimal'], ',03,05')

    def test_no_arguments(self):
        output, error = self.run_trace(catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage:'))

    @patch.object(trace, 'Simulator', TestSimulator)
    def test_sna_48k(self):
        header = [
            1,      # I
            2, 3,   # HL'
            4, 5,   # DE'
            6, 7,   # BC'
            8, 9,   # AF'
            10, 11, # HL
            12, 13, # DE
            14, 15, # BC
            16, 17, # IY
            18, 19, # IX
            4,      # iff2 (bit 2)
            20,     # R
            21, 22, # AF
            0, 64,  # SP=16384
            2,      # im
            5       # Border
        ]
        ram = [0] * 49152
        ram[:2] = (0, 96) # 16384 DEFW 24576 ; stack
        snafile = self.write_bin_file(header + ram, suffix='.sna')
        exp_output = """
            $6000 NOP              A=16  F=00010101  BC=0F0E  DE=0D0C  HL=0B0A  IX=1312 IY=1110
                                   A'=09 F'=00001000 BC'=0706 DE'=0504 HL'=0302 SP=4002 IR=0115
            Stopped at $6001
        """
        self._test_trace(f'-vv -S 24577 {snafile}', exp_output)
        self.assertEqual(simulator.iff, 1)
        self.assertEqual(simulator.imode, 2)

    @patch.object(trace, 'Simulator', TestSimulator)
    def test_sna_128k(self):
        sna = [0] * 131103
        sna[:27] = (
            1,         # I
            2, 3,      # HL'
            4, 5,      # DE'
            6, 7,      # BC'
            8, 9,      # AF'
            10, 11,    # HL
            12, 13,    # DE
            253, 127,  # BC
            16, 17,    # IY
            18, 19,    # IX
            4,         # iff2 (bit 2)
            20,        # R
            22,        # F
            17,        # A (page in bank 1 and ROM 1)
            0, 64,     # SP=16384
            2,         # im
            5          # Border
        )
        sna[8219:8221] = (
            0xED, 0x79 # $6000 OUT (C),A
        )
        sna[49179:49183] = (
            0, 96,     # PC ($6000)
            0,         # Port 0x7ffd
            0          # TR-DOS rom not paged
        )
        sna[49183:65567] = [1] * 16384 # Bank 1
        snafile = self.write_bin_file(sna, suffix='.sna')
        exp_output = """
            $6000 OUT (C),A        A=11  F=00010110  BC=7FFD  DE=0D0C  HL=0B0A  IX=1312 IY=1110
                                   A'=09 F'=00001000 BC'=0706 DE'=0504 HL'=0302 SP=4002 IR=0116
            Stopped at $6002
        """
        self._test_trace(f'-vv -S 24578 {snafile}', exp_output)
        self.assertEqual(simulator.iff, 1)
        self.assertEqual(simulator.imode, 2)
        self.assertTrue(all(b == 1 for b in simulator.memory[0xC000:0x10000]))
        self.assertEqual(hashlib.md5(bytes(simulator.memory[0x0000:0x4000])).hexdigest(), ROM1_MD5)

    @patch.object(trace, 'Simulator', TestSimulator)
    def test_z80_48k(self):
        registers = {
            'A': 1,
            'F': 2,
            'B': 3,
            'C': 4,
            'D': 5,
            'E': 6,
            'H': 7,
            'L': 8,
            'IXh': 9,
            'IXl': 10,
            'IYh': 11,
            'IYl': 12,
            'SP': 65535,
            'I': 13,
            'R': 14,
            '^A': 15,
            '^F': 16,
            '^B': 17,
            '^C': 18,
            '^D': 19,
            '^E': 20,
            '^H': 21,
            '^L': 22,
            'PC': 32768,
            'iff1': 1,
            'iff2': 1,
            'im': 2,
            'tstates': 20000
        }
        ram = [0] * 49152
        z80file = self.write_z80_file(None, ram, registers=registers)
        exp_output = """
            $8000 NOP              A=01  F=00000010  BC=0304  DE=0506  HL=0708  IX=0B0C IY=090A
                                   A'=0F F'=00010000 BC'=1112 DE'=1314 HL'=1516 SP=FFFF IR=0D0F
            Stopped at $8001
        """
        self._test_trace(f'-vv -S 32769 {z80file}', exp_output)
        self.assertEqual(simulator.iff, 1)
        self.assertEqual(simulator.imode, 2)
        self.assertEqual(simulator.registers[25], 20004)

    @patch.object(trace, 'Simulator', TestSimulator)
    def test_z80_128k(self):
        ram = [0] * 49152
        ram[8192:8194] = (0xED, 0x79) # $6000 OUT (C),A
        pages = {p: [p] * 16384 for p in (1, 3, 4, 6, 7)}
        registers = {
            'A': 1,
            'F': 2,
            'B': 127,
            'C': 253,
            'D': 5,
            'E': 6,
            'H': 7,
            'L': 8,
            'IXh': 9,
            'IXl': 10,
            'IYh': 11,
            'IYl': 12,
            'SP': 65535,
            'I': 13,
            'R': 14,
            '^A': 15,
            '^F': 16,
            '^B': 17,
            '^C': 18,
            '^D': 19,
            '^E': 20,
            '^H': 21,
            '^L': 22,
            'PC': 24576,
            'iff1': 1,
            'iff2': 1,
            'im': 2,
            'tstates': 20000
        }
        z80file = self.write_z80(ram, machine_id=4, out_7ffd=18, pages=pages, registers=registers)[1]
        exp_output = """
            $6000 OUT (C),A        A=01  F=00000010  BC=7FFD  DE=0506  HL=0708  IX=0B0C IY=090A
                                   A'=0F F'=00010000 BC'=1112 DE'=1314 HL'=1516 SP=FFFF IR=0D10
            Stopped at $6002
        """
        self._test_trace(f'-vv -S 24578 {z80file}', exp_output)
        self.assertEqual(simulator.iff, 1)
        self.assertEqual(simulator.imode, 2)
        self.assertEqual(simulator.registers[25], 20012)
        self.assertTrue(all(b == 1 for b in simulator.memory[0xC000:0x10000]))
        self.assertEqual(hashlib.md5(bytes(simulator.memory[0x0000:0x4000])).hexdigest(), ROM0_MD5)

    @patch.object(trace, 'Simulator', TestSimulator)
    def test_szx_48k(self):
        registers = (
            1, 2,       # AF
            3, 4,       # BC
            5, 6,       # DE
            7, 8,       # HL
            9, 10,      # AF'
            11, 12,     # BC'
            13, 14,     # DE'
            15, 16,     # HL'
            17, 18,     # IX
            19, 20,     # IY
            0, 128,     # SP=32768
            0, 192,     # PC=49152
            21,         # I
            22,         # R
            1, 1,       # iff1, iff2
            0,          # im
            1, 1, 0, 0, # dwCyclesStart=257
        )
        ram = [0] * 49152
        szxfile = self.write_szx(ram, registers=registers)
        exp_output = """
            $C000 NOP              A=02  F=00000001  BC=0403  DE=0605  HL=0807  IX=1211 IY=1413
                                   A'=0A F'=00001001 BC'=0C0B DE'=0E0D HL'=100F SP=8000 IR=1517
            Stopped at $C001
        """
        self._test_trace(f'-vv -S 49153 {szxfile}', exp_output)
        self.assertEqual(simulator.iff, 1)
        self.assertEqual(simulator.imode, 0)
        self.assertEqual(simulator.registers[25], 261)

    @patch.object(trace, 'Simulator', TestSimulator)
    def test_szx_128k(self):
        ram = [0] * 49152
        ram[8192:8194] = (
            0xED, 0x79  # $6000 OUT (C),A
        )
        pages = {p: [p] * 16384 for p in (1, 3, 4, 6, 7)}
        registers = (
            1, 19,      # AF
            253, 127,   # BC
            5, 6,       # DE
            7, 8,       # HL
            9, 10,      # AF'
            11, 12,     # BC'
            13, 14,     # DE'
            15, 16,     # HL'
            17, 18,     # IX
            19, 20,     # IY
            0, 128,     # SP=32768
            0, 96,      # PC=24576
            21,         # I
            22,         # R
            1, 1,       # iff1, iff2
            0,          # im
            1, 1, 0, 0, # dwCyclesStart=257
        )
        szxfile = self.write_szx(ram, machine_id=2, ch7ffd=4, pages=pages, registers=registers)
        exp_output = """
            $6000 OUT (C),A        A=13  F=00000001  BC=7FFD  DE=0605  HL=0807  IX=1211 IY=1413
                                   A'=0A F'=00001001 BC'=0C0B DE'=0E0D HL'=100F SP=8000 IR=1518
            Stopped at $6002
        """
        self._test_trace(f'-vv -S 24578 {szxfile}', exp_output)
        self.assertEqual(simulator.iff, 1)
        self.assertEqual(simulator.imode, 0)
        self.assertEqual(simulator.registers[25], 269)
        self.assertTrue(all(b == 3 for b in simulator.memory[0xC000:0x10000]))
        self.assertEqual(hashlib.md5(bytes(simulator.memory[0x0000:0x4000])).hexdigest(), ROM1_MD5)

    def test_no_snapshot_48k(self):
        output, error = self.run_trace(f'-v -S 2 48')
        self.assertEqual(error, '')
        exp_output = """
            $0000 DI
            $0001 XOR A
            Stopped at $0002
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_no_snapshot_128k(self):
        output, error = self.run_trace(f'-v -S 4 128')
        self.assertEqual(error, '')
        exp_output = """
            $0000 DI
            $0001 LD BC,$692B
            Stopped at $0004
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_default_start_address_for_binary_file(self):
        data = [0xAF] # XOR A
        binfile = self.write_bin_file(data, suffix='.bin')
        output, error = self.run_trace(f'-v -S 0 {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $FFFF XOR A
            Stopped at $0000
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_interrupt_mode_0(self):
        data = [
            0xED, 0x46, # $8000 IM 0
            0x76,       # $8002 HALT
            0xAF,       # $8003 XOR A
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        start = 0x8000
        stop = 0x8004
        output, error = self.run_trace(f'-o {start} -S {stop} -v {binfile}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 IM 0')
        self.assertEqual(output_lines[1:17471], ['$8002 HALT'] * 17470)
        self.assertEqual(output_lines[17471], '$0038 PUSH AF')
        self.assertEqual(output_lines[17579], '$0052 RET')
        self.assertEqual(output_lines[17580], '$8003 XOR A')
        self.assertEqual(output_lines[17581], 'Stopped at $8004')

    def test_interrupt_mode_1(self):
        data = [
            0xED, 0x56, # $8000 IM 1
            0x76,       # $8002 HALT
            0xAF,       # $8003 XOR A
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        start = 0x8000
        stop = 0x8004
        output, error = self.run_trace(f'-o {start} -S {stop} -v {binfile}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 IM 1')
        self.assertEqual(output_lines[1:17471], ['$8002 HALT'] * 17470)
        self.assertEqual(output_lines[17471], '$0038 PUSH AF')
        self.assertEqual(output_lines[17579], '$0052 RET')
        self.assertEqual(output_lines[17580], '$8003 XOR A')
        self.assertEqual(output_lines[17581], 'Stopped at $8004')

    def test_interrupt_mode_2(self):
        data = [
            0x76,       # $7FFB HALT
            0xAF,       # $7FFC XOR A
            0x00,       # $7FFD NOP
            0xC9,       # $7FFE RET
            0xFE, 0x7F, # $7FFF DEFW $7FFE
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        start = 0x7ffb
        stop = 0x7ffd
        ram = [0] * 49152
        ram[start - 0x4000:start - 0x4000 + len(data)] = data
        registers = {'PC': start, 'I': 127, 'iff2': 1, 'im': 2, 'tstates': 69882}
        z80file = self.write_z80_file(None, ram, registers=registers)
        output, error = self.run_trace(f'-S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$7FFB HALT')
        self.assertEqual(output_lines[1], '$7FFB HALT')
        self.assertEqual(output_lines[2], '$7FFE RET')
        self.assertEqual(output_lines[3], '$7FFC XOR A')
        self.assertEqual(output_lines[4], 'Stopped at $7FFD')

    def test_interrupt_without_halt(self):
        data = [
            0x00, # $8000 NOP ; t=69882
            0x00, # $8001 NOP ; t=69886 (interrupt follows)
            0x00, # $8002 NOP
        ]
        start = 0x8000
        stop = 0x8003
        ram = [0] * 49152
        ram[start - 0x4000:start - 0x4000 + len(data)] = data
        registers = {'PC': start, 'iff2': 1, 'im': 1, 'tstates': 69882}
        z80file = self.write_z80_file(None, ram, registers=registers)
        output, error = self.run_trace(f'-S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 NOP')
        self.assertEqual(output_lines[1], '$8001 NOP')
        self.assertEqual(output_lines[2], '$0038 PUSH AF')
        self.assertEqual(output_lines[110], '$0052 RET')
        self.assertEqual(output_lines[111], '$8002 NOP')
        self.assertEqual(output_lines[112], 'Stopped at $8003')

    def test_interrupt_with_ei(self):
        data = [
            0x00, # $8000 NOP ; t=69882
            0xFB, # $8001 EI  ; t=69886 (no interrupt accepted after EI)
            0x00, # $8002 NOP ; t=69890 (interrupt follows)
            0x00, # $8003 NOP
        ]
        start = 0x8000
        stop = 0x8004
        ram = [0] * 49152
        ram[start - 0x4000:start - 0x4000 + len(data)] = data
        registers = {'PC': start, 'iff2': 1, 'im': 1, 'tstates': 69882}
        z80file = self.write_z80_file(None, ram, registers=registers)
        output, error = self.run_trace(f'-S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 NOP')
        self.assertEqual(output_lines[1], '$8001 EI')
        self.assertEqual(output_lines[2], '$8002 NOP')
        self.assertEqual(output_lines[3], '$0038 PUSH AF')
        self.assertEqual(output_lines[111], '$0052 RET')
        self.assertEqual(output_lines[112], '$8003 NOP')
        self.assertEqual(output_lines[113], 'Stopped at $8004')

    def test_interrupt_with_di(self):
        data = [
            0x00, # $8000 NOP ; t=69882
            0xF3, # $8001 DI  ; t=69886 (no interrupt accepted after DI)
            0x00, # $8002 NOP ; t=69890
            0x00, # $8003 NOP ; t=69894
        ]
        start = 0x8000
        stop = 0x8004
        ram = [0] * 49152
        ram[start - 0x4000:start - 0x4000 + len(data)] = data
        registers = {'PC': start, 'iff2': 1, 'im': 1, 'tstates': 69882}
        z80file = self.write_z80_file(None, ram, registers=registers)
        output, error = self.run_trace(f'-S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 NOP')
        self.assertEqual(output_lines[1], '$8001 DI')
        self.assertEqual(output_lines[2], '$8002 NOP')
        self.assertEqual(output_lines[3], '$8003 NOP')
        self.assertEqual(output_lines[4], 'Stopped at $8004')

    def test_interrupt_with_dd_prefix(self):
        data = [
            0xDD, # $8000 DEFB $DD ; t=69886 (no interrupt accepted after DD)
            0x00, # $8001 NOP      ; t=69890 (interrupt follows)
            0x00, # $8002 NOP
        ]
        start = 0x8000
        stop = 0x8003
        ram = [0] * 49152
        ram[0x1C00] = ram[0x1C04] = 0xFF # KSTATE0/4
        ram[start - 0x4000:start - 0x4000 + len(data)] = data
        registers = {'PC': start, 'iff2': 1, 'im': 1, 'tstates': 69886}
        z80file = self.write_z80_file(None, ram, registers=registers)
        output, error = self.run_trace(f'-S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 DEFB $DD')
        self.assertEqual(output_lines[1], '$8001 NOP')
        self.assertEqual(output_lines[2], '$0038 PUSH AF')
        self.assertEqual(output_lines[102], '$0052 RET')
        self.assertEqual(output_lines[103], '$8002 NOP')
        self.assertEqual(output_lines[104], 'Stopped at $8003')

    def test_interrupt_with_fd_prefix(self):
        data = [
            0xFD, # $8000 DEFB $FD ; t=69886 (no interrupt accepted after FD)
            0x00, # $8001 NOP      ; t=69890 (interrupt follows)
            0x00, # $8002 NOP
        ]
        start = 0x8000
        stop = 0x8003
        ram = [0] * 49152
        ram[0x1C00] = ram[0x1C04] = 0xFF # KSTATE0/4
        ram[start - 0x4000:start - 0x4000 + len(data)] = data
        registers = {'PC': start, 'iff2': 1, 'im': 1, 'tstates': 69886}
        z80file = self.write_z80_file(None, ram, registers=registers)
        output, error = self.run_trace(f'-S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 DEFB $FD')
        self.assertEqual(output_lines[1], '$8001 NOP')
        self.assertEqual(output_lines[2], '$0038 PUSH AF')
        self.assertEqual(output_lines[102], '$0052 RET')
        self.assertEqual(output_lines[103], '$8002 NOP')
        self.assertEqual(output_lines[104], 'Stopped at $8003')

    def test_interrupt_with_ddfd_chain(self):
        data = [
            0xDD, # $8000 DEFB $DD ; t=69886 (no interrupt accepted after DD)
            0xFD, # $8001 DEFB $FD ; t=69890 (no interrupt accepted after FD)
            0xDD, # $8002 DEFB $DD ; t=69894 (no interrupt accepted after DD)
            0xFD, # $8003 DEFB $FD ; t=69898 (no interrupt accepted after FD)
            0x00, # $8004 NOP      ; t=69902 (interrupt follows)
            0x00, # $8005 NOP
        ]
        start = 0x8000
        stop = 0x8006
        ram = [0] * 49152
        ram[0x1C00] = ram[0x1C04] = 0xFF # KSTATE0/4
        ram[start - 0x4000:start - 0x4000 + len(data)] = data
        registers = {'PC': start, 'iff2': 1, 'im': 1, 'tstates': 69886}
        z80file = self.write_z80_file(None, ram, registers=registers)
        output, error = self.run_trace(f'-S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 DEFB $DD')
        self.assertEqual(output_lines[1], '$8001 DEFB $FD')
        self.assertEqual(output_lines[2], '$8002 DEFB $DD')
        self.assertEqual(output_lines[3], '$8003 DEFB $FD')
        self.assertEqual(output_lines[4], '$8004 NOP')
        self.assertEqual(output_lines[5], '$0038 PUSH AF')
        self.assertEqual(output_lines[105], '$0052 RET')
        self.assertEqual(output_lines[106], '$8005 NOP')
        self.assertEqual(output_lines[107], 'Stopped at $8006')

    def test_interrupt_at_exact_frame_boundary(self):
        data = [
            0x78, # $8000 LD A,B ; t=69884 (+4=69888: frame boundary)
            0x78, # $8001 LD A,B
        ]
        start = 0x8000
        stop = 0x8002
        ram = [0] * 49152
        ram[start - 0x4000:start - 0x4000 + len(data)] = data
        registers = {'PC': start, 'iff2': 1, 'im': 1, 'tstates': 69884}
        z80file = self.write_z80_file(None, ram, registers=registers)
        output, error = self.run_trace(f'-S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 LD A,B')
        self.assertEqual(output_lines[1], '$0038 PUSH AF')
        self.assertEqual(output_lines[109], '$0052 RET')
        self.assertEqual(output_lines[110], '$8001 LD A,B')
        self.assertEqual(output_lines[111], 'Stopped at $8002')

    @patch.object(trace, 'write_snapshot', mock_write_snapshot)
    def test_interrupt_with_djnz(self):
        data = [
            0x21, 0x00, 0x80,       # $7FEF LD HL,$8000   ; t=69805 T-states
            0x22, 0xFF, 0xFE,       # $7FF2 LD ($FEFF),HL ; t=69815
            0x3E, 0xFE,             # $7FF5 LD A,$FE      ; t=69831
            0xED, 0x47,             # $7FF7 LD I,A        ; t=69838
            0xED, 0x5E,             # $7FF9 IM 2          ; t=69847
            0x06, 0x04,             # $7FFB LD B,$04      ; t=69855
            0x10, 0xFE,             # $7FFD DJNZ $7FFD    ; t=69862/69875/interrupted
            0x00,                   # $7FFF NOP
            0xED, 0x43, 0x00, 0xC0, # $8000 LD ($C000),BC
            0xC9,                   # $8004 RET
        ]
        outfile = os.path.join(self.make_directory(), 'dump.z80')
        start = 0x7fef
        stop = 0x7fff
        ram = [0] * 49152
        ram[start - 0x4000:start - 0x4000 + len(data)] = data
        registers = {'PC': start, 'iff2': 1, 'im': 1, 'tstates': 69805}
        z80file = self.write_z80_file(None, ram, registers=registers)
        output, error = self.run_trace(f'-S {stop} -v {z80file} {outfile}')
        self.assertEqual(error, '')
        self.assertEqual(snapshot[0xc001], 2) # DJNZ interrupted when B=2

    @patch.object(trace, 'write_snapshot', mock_write_snapshot)
    def test_interrupt_with_ldir(self):
        data = [
            0x21, 0x00, 0x80,       # $7FEE LD HL,$8000   ; t=69805 T-states
            0x22, 0xFF, 0xFE,       # $7FF1 LD ($FEFF),HL ; t=69815
            0x3E, 0xFE,             # $7FF4 LD A,$FE      ; t=69831
            0xED, 0x47,             # $7FF6 LD I,A        ; t=69838
            0xED, 0x5E,             # $7FF8 IM 2          ; t=69847
            0x01, 0x04, 0x00,       # $7FFA LD BC,$0004   ; t=69855
            0xED, 0xB0,             # $7FFD LDIR          ; t=69865/69886/interrupted
            0x00,                   # $7FFF NOP
            0xED, 0x43, 0x00, 0xC0, # $8000 LD ($C000),BC
            0xC9,                   # $8004 RET
        ]
        outfile = os.path.join(self.make_directory(), 'dump.z80')
        start = 0x7fee
        stop = 0x7fff
        ram = [0] * 49152
        ram[start - 0x4000:start - 0x4000 + len(data)] = data
        registers = {'PC': start, 'iff2': 1, 'im': 1, 'tstates': 69805}
        z80file = self.write_z80_file(None, ram, registers=registers)
        output, error = self.run_trace(f'-S {stop} -v {z80file} {outfile}')
        self.assertEqual(error, '')
        self.assertEqual(snapshot[0xc000], 2) # LDIR interrupted when BC=2

    @patch.object(trace, 'write_snapshot', mock_write_snapshot)
    def test_interrupt_with_lddr(self):
        data = [
            0x21, 0x00, 0x80,       # $7FEE LD HL,$8000   ; t=69805 T-states
            0x22, 0xFF, 0xFE,       # $7FF1 LD ($FEFF),HL ; t=69815
            0x3E, 0xFE,             # $7FF4 LD A,$FE      ; t=69831
            0xED, 0x47,             # $7FF6 LD I,A        ; t=69838
            0xED, 0x5E,             # $7FF8 IM 2          ; t=69847
            0x01, 0x04, 0x00,       # $7FFA LD BC,$0004   ; t=69855
            0xED, 0xB8,             # $7FFD LDDR          ; t=69865/69886/interrupted
            0x00,                   # $7FFF NOP
            0xED, 0x43, 0x00, 0xC0, # $8000 LD ($C000),BC
            0xC9,                   # $8004 RET
        ]
        outfile = os.path.join(self.make_directory(), 'dump.z80')
        start = 0x7fee
        stop = 0x7fff
        ram = [0] * 49152
        ram[start - 0x4000:start - 0x4000 + len(data)] = data
        registers = {'PC': start, 'iff2': 1, 'im': 1, 'tstates': 69805}
        z80file = self.write_z80_file(None, ram, registers=registers)
        output, error = self.run_trace(f'-S {stop} -v {z80file} {outfile}')
        self.assertEqual(error, '')
        self.assertEqual(snapshot[0xc000], 2) # LDDR interrupted when BC=2

    def test_option_audio(self):
        data = [
            6, 3,     # 32768 LD B,3
            211, 254, # 32770 OUT (254),A
            238, 16,  # 32772 XOR 16
            16, 250,  # 32774 DJNZ 32770
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        start, stop = 32768, 32776
        output, error = self.run_trace(f'-o {start} -S {stop} --audio {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            Stopped at $8008
            Sound duration: 62 T-states (0.000s)
            Delays: [31]*2
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_decimal_verbose(self):
        data = (
            33, 7, 135,             # 65519 LD HL,34567
            6, 1,                   # 65522 LD B,1
            16, 254,                # 65524 DJNZ 65524
            221, 117, 23,           # 65526 LD (IX+23),L
            253, 54, 200, 100,      # 65529 LD (IY-56),100
            237, 0,                 # 65533 DEFB 237,0
            199,                    # 65535 RST 0
        )
        binfile = self.write_bin_file(data, suffix='.bin')
        exp_output = """
            65519 LD HL,34567
            65522 LD B,1
            65524 DJNZ 65524
            65526 LD (IX+23),L
            65529 LD (IY-56),100
            65533 DEFB 237,0
            65535 RST 0
            Stopped at 0
        """
        for option in ('-D', '--decimal'):
            output, error = self.run_trace(f'-v -S 0 {option} {binfile}')
            self.assertEqual(error, '')
            self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_decimal_more_verbose(self):
        data = (
            1, 57, 48,              # 65499 LD BC,12345
            17, 160, 91,            # 65502 LD DE,23456
            33, 7, 135,             # 65505 LD HL,34567
            221, 33, 110, 178,      # 65508 LD IX,45678
            253, 33, 213, 221,      # 65512 LD IY,56789
            144,                    # 65516 SUB B
            237, 79,                # 65517 LD R,A
            237, 71,                # 65519 LD I,A
            217,                    # 65521 EXX
            1, 152, 255,            # 65522 LD BC,65432
            17, 49, 212,            # 65525 LD DE,54321
            33, 202, 168,           # 65528 LD HL,43210
            8,                      # 65531 EX AF,AF'
            144,                    # 65532 SUB B
            49, 109, 125,           # 65533 LD SP,32109
        )
        binfile = self.write_bin_file(data, suffix='.bin')
        exp_output = """
            65499 LD BC,12345      A=0    F=00000000  BC=12345  DE=0      HL=0      IX=0     IY=23610
                                   A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552 I=63  R=100
            65502 LD DE,23456      A=0    F=00000000  BC=12345  DE=23456  HL=0      IX=0     IY=23610
                                   A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552 I=63  R=101
            65505 LD HL,34567      A=0    F=00000000  BC=12345  DE=23456  HL=34567  IX=0     IY=23610
                                   A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552 I=63  R=102
            65508 LD IX,45678      A=0    F=00000000  BC=12345  DE=23456  HL=34567  IX=45678 IY=23610
                                   A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552 I=63  R=104
            65512 LD IY,56789      A=0    F=00000000  BC=12345  DE=23456  HL=34567  IX=45678 IY=56789
                                   A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552 I=63  R=106
            65516 SUB B            A=208  F=10000011  BC=12345  DE=23456  HL=34567  IX=45678 IY=56789
                                   A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552 I=63  R=107
            65517 LD R,A           A=208  F=10000011  BC=12345  DE=23456  HL=34567  IX=45678 IY=56789
                                   A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552 I=63  R=208
            65519 LD I,A           A=208  F=10000011  BC=12345  DE=23456  HL=34567  IX=45678 IY=56789
                                   A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552 I=208 R=210
            65521 EXX              A=208  F=10000011  BC=0      DE=0      HL=0      IX=45678 IY=56789
                                   A'=0   F'=00000000 BC'=12345 DE'=23456 HL'=34567 SP=23552 I=208 R=211
            65522 LD BC,65432      A=208  F=10000011  BC=65432  DE=0      HL=0      IX=45678 IY=56789
                                   A'=0   F'=00000000 BC'=12345 DE'=23456 HL'=34567 SP=23552 I=208 R=212
            65525 LD DE,54321      A=208  F=10000011  BC=65432  DE=54321  HL=0      IX=45678 IY=56789
                                   A'=0   F'=00000000 BC'=12345 DE'=23456 HL'=34567 SP=23552 I=208 R=213
            65528 LD HL,43210      A=208  F=10000011  BC=65432  DE=54321  HL=43210  IX=45678 IY=56789
                                   A'=0   F'=00000000 BC'=12345 DE'=23456 HL'=34567 SP=23552 I=208 R=214
            65531 EX AF,AF'        A=0    F=00000000  BC=65432  DE=54321  HL=43210  IX=45678 IY=56789
                                   A'=208 F'=10000011 BC'=12345 DE'=23456 HL'=34567 SP=23552 I=208 R=215
            65532 SUB B            A=1    F=00010011  BC=65432  DE=54321  HL=43210  IX=45678 IY=56789
                                   A'=208 F'=10000011 BC'=12345 DE'=23456 HL'=34567 SP=23552 I=208 R=216
            65533 LD SP,32109      A=1    F=00010011  BC=65432  DE=54321  HL=43210  IX=45678 IY=56789
                                   A'=208 F'=10000011 BC'=12345 DE'=23456 HL'=34567 SP=32109 I=208 R=217
            Stopped at 0
        """
        for option in ('-D', '--decimal'):
            output, error = self.run_trace(f'-vv -r r=99 -S 0 {option} {binfile}')
            self.assertEqual(error, '')
            self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_depth_0(self):
        data = (
            6, 4,     # 32768 LD B,4
            211, 254, # 32770 OUT (254),A
            238, 16,  # 32772 XOR 16
            16, 250,  # 32774 DJNZ 32770
        )
        binfile = self.write_bin_file(data, suffix='.bin')
        start, stop = 32768, 32776
        output, error = self.run_trace(f'-o {start} -S {stop} --audio --depth 0 {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            Stopped at $8008
            Sound duration: 93 T-states (0.000s)
            Delays: 31, 31, 31
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_depth_1(self):
        data = (
            6, 4,     # 32768 LD B,4
            211, 254, # 32770 OUT (254),A
            238, 16,  # 32772 XOR 16
            16, 250,  # 32774 DJNZ 32770
        )
        binfile = self.write_bin_file(data, suffix='.bin')
        start, stop = 32768, 32776
        output, error = self.run_trace(f'-o {start} -S {stop} --audio --depth 1 {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            Stopped at $8008
            Sound duration: 93 T-states (0.000s)
            Delays: [31]*3
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_depth_2(self):
        data = (
            1, 16, 4, # 32768 LD BC,1040
            211, 254, # 32771 OUT (254),A
            238, 16,  # 32773 XOR 16
            211, 254, # 32775 OUT (254),A
            169,      # 32777 XOR C
            16, 247,  # 32778 DJNZ 32771
        )
        binfile = self.write_bin_file(data, suffix='.bin')
        start, stop = 32768, 32780
        output, error = self.run_trace(f'-o {start} -S {stop} --audio --depth 2 {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            Stopped at $800C
            Sound duration: 156 T-states (0.000s)
            Delays: [18, 28]*3, 18
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_depth_3(self):
        data = (
            1, 16, 4, # 32768 LD BC,1040
            211, 254, # 32771 OUT (254),A
            238, 16,  # 32773 XOR 16
            211, 254, # 32775 OUT (254),A
            169,      # 32777 XOR C
            211, 254, # 32778 OUT (254),A
            238, 16,  # 32780 XOR 16
            16, 243,  # 32782 DJNZ 32771
        )
        binfile = self.write_bin_file(data, suffix='.bin')
        start, stop = 32768, 32784
        output, error = self.run_trace(f'-o {start} -S {stop} --audio --depth 3 {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            Stopped at $8010
            Sound duration: 225 T-states (0.000s)
            Delays: [18, 15, 31]*3, 18, 15
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    @patch.object(trace, 'get_config', mock_config)
    @patch.object(trace, 'run', mock_run)
    def test_option_I(self):
        self.run_trace('-I TraceLine=Hello in.z80')
        z80file, options, config = run_args
        self.assertEqual(['TraceLine=Hello'], options.params)
        self.assertEqual(config['TraceLine'], 'Hello')

    @patch.object(trace, 'run', mock_run)
    def test_option_I_overrides_config_read_from_file(self):
        ini = """
            [trace]
            TraceLine=0x{pc:04x} {i}
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        self.run_trace('--ini TraceLine=Goodbye in.z80')
        z80file, options, config = run_args
        self.assertEqual(['TraceLine=Goodbye'], options.params)
        self.assertEqual(config['TraceLine'], 'Goodbye')

    def test_option_max_operations(self):
        data = [
            0xAF, # XOR A
            0x3C, # INC A
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        start = 32768
        exp_output = """
            $8000 XOR A
            $8001 INC A
            Stopped at $8002: 2 operations
        """
        for option in ('-m', '--max-operations'):
            output, error = self.run_trace(f'-o {start} -v {option} 2 {binfile}')
            self.assertEqual(error, '')
            self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_max_tstates(self):
        data = [
            0xAF, # XOR A
            0x3C, # INC A
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        start = 32768
        exp_output = """
            $8000 XOR A
            $8001 INC A
            Stopped at $8002: 8 T-states
        """
        for option in ('-M', '--max-tstates'):
            output, error = self.run_trace(f'-o {start} -v {option} 8 {binfile}')
            self.assertEqual(error, '')
            self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_no_interrupts(self):
        data = [
            0x00, # $8000 NOP ; t=69886 (interrupt would normally follow)
            0x00, # $8001 NOP
        ]
        start = 0x8000
        stop = 0x8002
        ram = [0] * 49152
        ram[start - 0x4000:start - 0x4000 + len(data)] = data
        registers = {'PC': start, 'iff2': 1, 'im': 1, 'tstates': 69886}
        z80file = self.write_z80_file(None, ram, registers=registers)
        exp_output = dedent("""
            $8000 NOP
            $8001 NOP
            Stopped at $8002
        """).strip()
        for option in ('-n', '--no-interrupts'):
            output, error = self.run_trace(f'{option} -S {stop} -v {z80file}')
            self.assertEqual(error, '')
            self.assertEqual(exp_output, output.rstrip())

    def test_option_poke(self):
        data = [
            33, 0, 192, # LD HL,49152
            126,        # LD A,(HL)
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        start, stop = 32768, 32772
        output, error = self.run_trace(f'-o {start} -S {stop} -vv --poke 49152,1 {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 LD HL,$C000      A=00  F=00000000  BC=0000  DE=0000  HL=C000  IX=0000 IY=5C3A
                                   A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00 IR=3F01
            $8003 LD A,(HL)        A=01  F=00000000  BC=0000  DE=0000  HL=C000  IX=0000 IY=5C3A
                                   A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00 IR=3F02
            Stopped at $8004
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_reg(self):
        data = [
            0x3C  # INC A
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        start, stop = 32768, 32769
        registers = {
            'A': 0x50,
            'F': 0b01000001,
            'BC': 0x1234,
            'DE': 0x2345,
            'HL': 0x3456,
            'IX': 0x4567,
            'IY': 0x5678,
            'I': 0x67,
            'R': 0x89,
            '^A': 0x98,
            '^F': 0b10101010,
            '^BC': 0x8765,
            '^DE': 0x7654,
            '^HL': 0x6543,
            'SP': 0x5432
        }
        reg_options = ' '.join(f'--reg {r}={v}' for r, v in registers.items())
        output, error = self.run_trace(f'-o {start} -S {stop} -vv {reg_options} {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 INC A            A=51  F=00000001  BC=1234  DE=2345  HL=3456  IX=4567 IY=5678
                                   A'=98 F'=10101010 BC'=8765 DE'=7654 HL'=6543 SP=5432 IR=678A
            Stopped at $8001
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_reg_help(self):
        output, error = self.run_trace('--reg help')
        self.assertTrue(output.startswith('Usage: --reg name=value\n'))
        self.assertEqual(error, '')

    def test_option_rom(self):
        romfile = self.write_bin_file([175], suffix='.bin')
        binfile = self.write_bin_file([195, 0, 0], suffix='.bin')
        start, stop = 32768, 1
        output, error = self.run_trace(f'-o {start} -S {stop} --rom {romfile} -v {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 JP $0000
            $0000 XOR A
            Stopped at $0001
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    @patch.object(trace, 'get_config', mock_config)
    def test_option_show_config(self):
        output, error = self.run_trace('--show-config', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = (
            "[trace]\n"
            "TraceLine=${pc:04X} {i}\n"
            "TraceLine2=${pc:04X} {i:<15}  "
            "A={r[a]:02X}  F={r[f]:08b}  BC={r[bc]:04X}  DE={r[de]:04X}  HL={r[hl]:04X}  IX={r[ix]:04X} IY={r[iy]:04X}\\n                       "
            "A'={r[^a]:02X} F'={r[^f]:08b} BC'={r[^bc]:04X} DE'={r[^de]:04X} HL'={r[^hl]:04X} SP={r[sp]:04X} IR={r[i]:02X}{r[r]:02X}\n"
            "TraceLineDecimal={pc:05} {i}\n"
            "TraceLineDecimal2={pc:05} {i:<15}  "
            "A={r[a]:<3}  F={r[f]:08b}  BC={r[bc]:<5}  DE={r[de]:<5}  HL={r[hl]:<5}  IX={r[ix]:<5} IY={r[iy]:<5}\\n                       "
            "A'={r[^a]:<3} F'={r[^f]:08b} BC'={r[^bc]:<5} DE'={r[^de]:<5} HL'={r[^hl]:<5} SP={r[sp]:<5} I={r[i]:<3} R={r[r]:<3}\n"
            "TraceOperand=$,02X,04X\n"
            "TraceOperandDecimal=,,"
        )
        self.assertEqual(exp_output, output.rstrip())

    def test_option_show_config_read_from_file(self):
        ini = """
            [trace]
            TraceLine2=${pc:04x} {i:<15} A={r[a]:02X}
            TraceLineDecimal2={pc:05} {i:<15} A={r[a]}
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        output, error = self.run_trace('--show-config', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            [trace]
            TraceLine=${pc:04X} {i}
            TraceLine2=${pc:04x} {i:<15} A={r[a]:02X}
            TraceLineDecimal={pc:05} {i}
            TraceLineDecimal2={pc:05} {i:<15} A={r[a]}
            TraceOperand=$,02X,04X
            TraceOperandDecimal=,,
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_start(self):
        ram = [0] * 49152
        z80file = self.write_z80_file(None, ram, registers={'PC': 16384})
        for option in ('-s 32768', '--start 0x8000'):
            output, error = self.run_trace(f'-v {option} -S 32769 {z80file}')
            self.assertEqual(error, '')
            exp_output = """
                $8000 NOP
                Stopped at $8001
            """
            self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_stats(self):
        data = [
            175, # XOR A
            60,  # INC A
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        start, stop = 32768, 32770
        output, error = self.run_trace(f'-o {start} -S {stop} --stats {binfile}')
        self.assertEqual(error, '')
        o_lines = output.split('\n')
        self.assertEqual(o_lines[0], 'Stopped at $8002')
        self.assertEqual(o_lines[1], 'Z80 execution time: 8 T-states (0.000s)')
        self.assertEqual(o_lines[2], 'Instructions executed: 2')
        self.assertEqual(o_lines[3][:17], 'Simulation time: ')

    def test_option_stats_with_non_zero_start_time(self):
        data = [
            175, # XOR A
            60,  # INC A
        ]
        start, stop = 32768, 32770
        ram = [0] * 49152
        ram[start - 0x4000:start - 0x4000 + len(data)] = data
        registers = {'PC': start, 'tstates': 10000}
        z80file = self.write_z80_file(None, ram, registers=registers)
        output, error = self.run_trace(f'-S {stop} --stats {z80file}')
        self.assertEqual(error, '')
        o_lines = output.split('\n')
        self.assertEqual(o_lines[0], 'Stopped at $8002')
        self.assertEqual(o_lines[1], 'Z80 execution time: 8 T-states (0.000s)')
        self.assertEqual(o_lines[2], 'Instructions executed: 2')
        self.assertEqual(o_lines[3][:17], 'Simulation time: ')

    def test_option_stop(self):
        for option in ('-S 57', '--stop 0x0039'):
            output, error = self.run_trace(f'-v -s 56 {option} 48')
            self.assertEqual(error, '')
            exp_output = """
                $0038 PUSH AF
                Stopped at $0039
            """
            self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_verbose(self):
        data = [
            0xAF, # XOR A
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        start, stop = 32768, 32769
        output, error = self.run_trace(f'-o {start} -S {stop} --verbose {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 XOR A
            Stopped at $8001
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_vv(self):
        data = [
            0xAF, # XOR A
            0x3C  # INC A
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        start, stop = 32768, 32770
        output, error = self.run_trace(f'-o {start} -S {stop} -vv {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 XOR A            A=00  F=01000100  BC=0000  DE=0000  HL=0000  IX=0000 IY=5C3A
                                   A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00 IR=3F01
            $8001 INC A            A=01  F=00000000  BC=0000  DE=0000  HL=0000  IX=0000 IY=5C3A
                                   A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00 IR=3F02
            Stopped at $8002
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_verbose_with_djnz_and_ldir(self):
        data = (
            0x06, 0x02,             # $8000 LD B,$02
            0x10, 0xFE,             # $8002 DJNZ $8002
            0x21, 0x00, 0xC0,       # $8004 LD HL,$C000
            0x11, 0x00, 0x60,       # $8007 LD DE,$6000
            0x0E, 0x02,             # $800A LD C,$02
            0xED, 0xB0,             # $800C LDIR
        )
        binfile = self.write_bin_file(data, suffix='.bin')
        output, error = self.run_trace(f'-o 0x8000 -S 0x800E -v {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 LD B,$02
            $8002 DJNZ $8002
            $8002 DJNZ $8002
            $8004 LD HL,$C000
            $8007 LD DE,$6000
            $800A LD C,$02
            $800C LDIR
            $800C LDIR
            Stopped at $800E
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_vv_with_djnz_and_ldir(self):
        data = (
            0x06, 0x02,             # $FF00 LD B,$02
            0x10, 0xFE,             # $FF02 DJNZ $FF02
            0x21, 0x00, 0xC0,       # $FF04 LD HL,$C000
            0x11, 0x00, 0x60,       # $FF07 LD DE,$6000
            0x0E, 0x02,             # $FF0A LD C,$02
            0xED, 0xB0,             # $FF0C LDIR
        )
        binfile = self.write_bin_file(data, suffix='.bin')
        output, error = self.run_trace(f'-o 0xff00 -S 0xff0E -vv {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $FF00 LD B,$02         A=00  F=00000000  BC=0200  DE=0000  HL=0000  IX=0000 IY=5C3A
                                   A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00 IR=3F01
            $FF02 DJNZ $FF02       A=00  F=00000000  BC=0100  DE=0000  HL=0000  IX=0000 IY=5C3A
                                   A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00 IR=3F02
            $FF02 DJNZ $FF02       A=00  F=00000000  BC=0000  DE=0000  HL=0000  IX=0000 IY=5C3A
                                   A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00 IR=3F03
            $FF04 LD HL,$C000      A=00  F=00000000  BC=0000  DE=0000  HL=C000  IX=0000 IY=5C3A
                                   A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00 IR=3F04
            $FF07 LD DE,$6000      A=00  F=00000000  BC=0000  DE=6000  HL=C000  IX=0000 IY=5C3A
                                   A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00 IR=3F05
            $FF0A LD C,$02         A=00  F=00000000  BC=0002  DE=6000  HL=C000  IX=0000 IY=5C3A
                                   A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00 IR=3F06
            $FF0C LDIR             A=00  F=00101100  BC=0001  DE=6001  HL=C001  IX=0000 IY=5C3A
                                   A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00 IR=3F08
            $FF0C LDIR             A=00  F=00000000  BC=0000  DE=6002  HL=C002  IX=0000 IY=5C3A
                                   A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00 IR=3F0A
            Stopped at $FF0E
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_trace(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))

    def test_config_TraceLine_read_from_file(self):
        ini = """
            [trace]
            TraceLine={t:06} ${pc:04X} {i}
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        code = (
            0x06, 0x02, # $8000 LD B,$02
            0x0E, 0x03, # $8002 LD C,$03
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        output, error = self.run_trace(f'-o {start} -S {stop} -v {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            000000 $8000 LD B,$02
            000007 $8002 LD C,$03
            Stopped at $8004
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceLine_set_on_command_line(self):
        code = (
            0x06, 0x02, # $8000 LD B,$02
            0x0E, 0x03, # $8002 LD C,$03
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        trace_line = '{pc}:{i}'
        output, error = self.run_trace(f'-I TraceLine={trace_line} -o {start} -S {stop} -v {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            32768:LD B,$02
            32770:LD C,$03
            Stopped at $8004
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceLine2_read_from_file(self):
        ini = """
            [trace]
            TraceLine2=${pc:04X} {i:<15} B={r[b]:02X} C={r[c]:02X} D={r[d]:02X} E={r[e]:02X} H={r[h]:02X} L={r[l]:02X}
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        code = (
            0x01, 0x02, 0x03, # $8000 LD BC,$0302
            0x11, 0x12, 0x13, # $8003 LD DE,$1312
            0x21, 0x22, 0x23, # $8006 LD HL,$2312
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        output, error = self.run_trace(f'-o {start} -S {stop} -vv {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 LD BC,$0302     B=03 C=02 D=00 E=00 H=00 L=00
            $8003 LD DE,$1312     B=03 C=02 D=13 E=12 H=00 L=00
            $8006 LD HL,$2322     B=03 C=02 D=13 E=12 H=23 L=22
            Stopped at $8009
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceLine2_set_on_command_line(self):
        code = (
            0x06, 0x02, # $8000 LD B,$02
            0x0E, 0x03, # $8002 LD C,$03
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        trace_line = '{pc:<6}{i:<12}BC={r[b]}{r[c]}'
        output, error = self.run_trace(f'-I TraceLine2={trace_line} -o {start} -S {stop} -vv {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            32768 LD B,$02    BC=20
            32770 LD C,$03    BC=23
            Stopped at $8004
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceLineDecimal_read_from_file(self):
        ini = """
            [trace]
            TraceLineDecimal={t:06} {pc} {i}
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        code = (
            0x16, 0x02, # $8000 LD D,$02
            0x1E, 0x03, # $8002 LD E,$03
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 32768
        stop = start + len(code)
        output, error = self.run_trace(f'-o {start} -S {stop} -Dv {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            000000 32768 LD D,2
            000007 32770 LD E,3
            Stopped at 32772
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceLineDecimal_set_on_command_line(self):
        code = (
            0x06, 0x02, # $8000 LD B,$02
            0x0E, 0x03, # $8002 LD C,$03
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        trace_line = '{pc}:{i}'
        output, error = self.run_trace(f'-I TraceLineDecimal={trace_line} -o {start} -S {stop} -Dv {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            32768:LD B,2
            32770:LD C,3
            Stopped at 32772
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceLineDecimal2_read_from_file(self):
        ini = """
            [trace]
            TraceLineDecimal2={pc} {i:<12} B'={r[^b]} C'={r[^c]} D'={r[^d]} E'={r[^e]} H'={r[^h]} L'={r[^l]} IXh={r[ixh]} IXl={r[ixl]} IYh={r[iyh]} IYl={r[iyl]}
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        code = (
            0x01, 0x34, 0x12,       # $8000 LD BC,$1234
            0x11, 0x45, 0x23,       # $8003 LD DE,$2345
            0x21, 0x56, 0x34,       # $8006 LD HL,$3456
            0xDD, 0x21, 0x67, 0x45, # $8009 LD IX,$4567
            0xFD, 0x21, 0x78, 0x56, # $800D LD IY,$5678
            0xD9,                   # $8011 EXX
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 32768
        stop = start + len(code)
        output, error = self.run_trace(f'-o {start} -S {stop} -Dvv {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            32768 LD BC,4660   B'=0 C'=0 D'=0 E'=0 H'=0 L'=0 IXh=0 IXl=0 IYh=92 IYl=58
            32771 LD DE,9029   B'=0 C'=0 D'=0 E'=0 H'=0 L'=0 IXh=0 IXl=0 IYh=92 IYl=58
            32774 LD HL,13398  B'=0 C'=0 D'=0 E'=0 H'=0 L'=0 IXh=0 IXl=0 IYh=92 IYl=58
            32777 LD IX,17767  B'=0 C'=0 D'=0 E'=0 H'=0 L'=0 IXh=69 IXl=103 IYh=92 IYl=58
            32781 LD IY,22136  B'=0 C'=0 D'=0 E'=0 H'=0 L'=0 IXh=69 IXl=103 IYh=86 IYl=120
            32785 EXX          B'=18 C'=52 D'=35 E'=69 H'=52 L'=86 IXh=69 IXl=103 IYh=86 IYl=120
            Stopped at 32786
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceLineDecimal2_set_on_command_line(self):
        code = (
            0x06, 0x02, # $8000 LD B,$02
            0x0E, 0x03, # $8002 LD C,$03
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        trace_line = '{pc:<6}{i:<12}BC={r[b]},{r[c]}'
        output, error = self.run_trace(f'-I TraceLineDecimal2={trace_line} -o {start} -S {stop} -Dvv {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            32768 LD B,2      BC=2,0
            32770 LD C,3      BC=2,3
            Stopped at 32772
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceOperand_read_from_file(self):
        ini = """
            [trace]
            TraceOperand=&,02x,04x
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        code = (
            0x06, 0x1A,       # $8000 LD B,$1A
            0x11, 0xFA, 0x0B, # $8002 LD DE,$0BFA
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        output, error = self.run_trace(f'-o {start} -S {stop} -v {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 LD B,&1a
            $8002 LD DE,&0bfa
            Stopped at &8005
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceOperand_set_on_command_line(self):
        code = (
            0x06, 0x1A,       # $8000 LD B,$1A
            0x11, 0xFA, 0x0B, # $8002 LD DE,$0BFA
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        output, error = self.run_trace(f'-I TraceOperand=#,02x,04x -o {start} -S {stop} -v {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 LD B,#1a
            $8002 LD DE,#0bfa
            Stopped at #8005
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceOperand_with_no_commas(self):
        code = (
            0x06, 0x1A,       # $8000 LD B,$1A
            0x11, 0xFA, 0x0B, # $8002 LD DE,$0BFA
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        output, error = self.run_trace(f'--ini TraceOperand=# -o {start} -S {stop} -v {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 LD B,#26
            $8002 LD DE,#3066
            Stopped at #32773
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceOperand_with_one_comma(self):
        code = (
            0x06, 0x1A,       # $8000 LD B,$1A
            0x11, 0xFA, 0x0B, # $8002 LD DE,$0BFA
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        output, error = self.run_trace(f'-I TraceOperand=#,02x -o {start} -S {stop} -v {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 LD B,#1a
            $8002 LD DE,#3066
            Stopped at #32773
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceOperand_with_three_commas(self):
        code = (
            0x06, 0x1A,       # $8000 LD B,$1A
            0x11, 0xFA, 0x0B, # $8002 LD DE,$0BFA
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        output, error = self.run_trace(f'--ini TraceOperand=#,02x,04x,??? -o {start} -S {stop} -v {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 LD B,#1a
            $8002 LD DE,#0bfa
            Stopped at #8005
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceOperandDecimal_read_from_file(self):
        ini = """
            [trace]
            TraceOperandDecimal=d,03,05
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        code = (
            0x06, 0x1A,       # $8000 LD B,$1A
            0x11, 0xFA, 0x0B, # $8002 LD DE,$0BFA
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        output, error = self.run_trace(f'-o {start} -S {stop} -Dv {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            32768 LD B,d026
            32770 LD DE,d03066
            Stopped at d32773
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceOperandDecimal_set_on_command_line(self):
        code = (
            0x06, 0x1A,       # $8000 LD B,$1A
            0x11, 0xFA, 0x0B, # $8002 LD DE,$0BFA
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        output, error = self.run_trace(f'-I TraceOperandDecimal=0d,03,05 -o {start} -S {stop} -Dv {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            32768 LD B,0d026
            32770 LD DE,0d03066
            Stopped at 0d32773
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceOperandDecimal_with_no_commas(self):
        code = (
            0x06, 0x1A,       # $8000 LD B,$1A
            0x11, 0xFA, 0x0B, # $8002 LD DE,$0BFA
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        output, error = self.run_trace(f'--ini TraceOperandDecimal=0d -o {start} -S {stop} -Dv {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            32768 LD B,0d26
            32770 LD DE,0d3066
            Stopped at 0d32773
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceOperandDecimal_with_one_comma(self):
        code = (
            0x06, 0x1A,       # $8000 LD B,$1A
            0x11, 0xFA, 0x0B, # $8002 LD DE,$0BFA
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        output, error = self.run_trace(f'-I TraceOperandDecimal=0d,03 -o {start} -S {stop} -Dv {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            32768 LD B,0d026
            32770 LD DE,0d3066
            Stopped at 0d32773
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_config_TraceOperandDecimal_with_three_commas(self):
        code = (
            0x06, 0x1A,       # $8000 LD B,$1A
            0x11, 0xFA, 0x0B, # $8002 LD DE,$0BFA
        )
        binfile = self.write_bin_file(code, suffix='.bin')
        start = 0x8000
        stop = start + len(code)
        output, error = self.run_trace(f'--ini TraceOperandDecimal=0d,03,05,??? -o {start} -S {stop} -Dv {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            32768 LD B,0d026
            32770 LD DE,0d03066
            Stopped at 0d32773
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_self_modifying_code(self):
        data = (
            0x06, 0x02,             # $8000 LD B,$02
            0x21, 0x03, 0x80,       # $8002 LD HL,$8003
            0x70,                   # $8005 LD (HL),B
            0x10, 0xFA,             # $8006 DJNZ $8002
        )
        binfile = self.write_bin_file(data, suffix='.bin')
        start, stop = 0x8000, 0x8008
        output, error = self.run_trace(f'-o {start} -S {stop} -v {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 LD B,$02
            $8002 LD HL,$8003
            $8005 LD (HL),B
            $8006 DJNZ $8002
            $8002 LD HL,$8002
            $8005 LD (HL),B
            $8006 DJNZ $8002
            Stopped at $8008
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    @patch.object(trace, 'write_snapshot', mock_write_snapshot)
    def test_128k_bank_5(self):
        sna = [0] * 131103
        start = 32768
        sna[49179:49181] = (start % 256, start // 256) # PC
        code = [
            0x01, 0xFD, 0x7F,       # $8000 LD BC,$7FFD
            0x3E, 0x05,             # $8003 LD A,$05
            0xED, 0x79,             # $8005 OUT (C),A
            0x32, 0x00, 0xC0,       # $8007 LD ($C000),A
        ]
        sna[start - 16357:start - 16357 + len(code)] = code
        snafile = self.write_bin_file(sna, suffix='.sna')
        outfile = os.path.join(self.make_directory(), 'out.z80')
        stop = start + len(code)
        output, error = self.run_trace(f'-S {stop} {snafile} {outfile}')
        exp_output = f"""
            Stopped at ${stop:04X}
            Wrote {outfile}
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())
        self.assertEqual(z80fname, outfile)
        self.assertEqual(snapshot[0x4000], 5)
        self.assertEqual(banks[5][0], 5)
        self.assertEqual(snapshot[0xC000], 5)
        self.assertEqual(banks[0][0], 0)

    @patch.object(trace, 'write_snapshot', mock_write_snapshot)
    def test_128k_bank_2(self):
        sna = [0] * 131103
        start = 32768
        sna[49179:49181] = (start % 256, start // 256) # PC
        code = [
            0x01, 0xFD, 0x7F,       # $8000 LD BC,$7FFD
            0x3E, 0x02,             # $8003 LD A,$02
            0xED, 0x79,             # $8005 OUT (C),A
            0x32, 0x00, 0xC0,       # $8007 LD ($C000),A
        ]
        sna[start - 16357:start - 16357 + len(code)] = code
        snafile = self.write_bin_file(sna, suffix='.sna')
        outfile = os.path.join(self.make_directory(), 'out.z80')
        stop = start + len(code)
        output, error = self.run_trace(f'-S {stop} {snafile} {outfile}')
        exp_output = f"""
            Stopped at ${stop:04X}
            Wrote {outfile}
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())
        self.assertEqual(z80fname, outfile)
        self.assertEqual(snapshot[0x8000], 2)
        self.assertEqual(banks[2][0], 2)
        self.assertEqual(snapshot[0xC000], 2)
        self.assertEqual(banks[0][0], 0)

    def test_invalid_register_value(self):
        binfile = self.write_bin_file([201], suffix='.bin')
        addr = 32768
        with self.assertRaises(SkoolKitError) as cm:
            self.run_trace(f'-o {addr} --reg A=x {binfile}')
        self.assertEqual(cm.exception.args[0], 'Cannot parse register value: A=x')

    @patch.object(trace, 'write_snapshot', mock_write_snapshot)
    def test_write_z80_48k(self):
        data = [
            0x37,                   # $8000 SCF
            0x9F,                   # $8001 SBC A,A
            0xF3,                   # $8002 DI
            0xED, 0x5E,             # $8003 IM 2
            0xED, 0x47,             # $8005 LD I,A
            0xED, 0x4F,             # $8007 LD R,A
            0x08,                   # $8009 EX AF,AF'
            0x3E, 0x01,             # $800A LD A,$01
            0xA7,                   # $800C AND A
            0xD3, 0xFE,             # $800D OUT ($FE),A
            0x01, 0x88, 0x10,       # $800F LD BC,$1088
            0x11, 0xB8, 0x53,       # $8012 LD DE,$53B8
            0x21, 0x57, 0x63,       # $8015 LD HL,$6357
            0xD9,                   # $8018 EXX
            0x01, 0x27, 0xEF,       # $8019 LD BC,$EF27
            0x11, 0xF8, 0x13,       # $801C LD DE,$13F8
            0x21, 0x77, 0x7D,       # $801F LD HL,$7D77
            0x31, 0xE9, 0xBE,       # $8022 LD SP,$BEE9
            0xDD, 0x21, 0x72, 0x0D, # $8025 LD IX,$0D72
            0xFD, 0x21, 0x2E, 0x27, # $8029 LD IY,$272E
        ]
        infile = self.write_bin_file(data, suffix='.bin')
        outfile = os.path.join(self.make_directory(), 'out.z80')
        start = 32768
        stop = start + len(data)
        output, error = self.run_trace(f'-o {start} -S {stop} {infile} {outfile}')
        exp_output = f"""
            Stopped at ${stop:04X}
            Wrote {outfile}
        """
        exp_reg = (
            'a=1',
            'f=16',
            'bc=61223',
            'de=5112',
            'hl=32119',
            'ix=3442',
            'iy=10030',
            'sp=48873',
            'i=255',
            'r=143',
            '^a=255',
            '^f=187',
            '^bc=4232',
            '^de=21432',
            '^hl=25431',
            f'pc={stop}'
        )
        exp_state = ['border=1', 'fe=1', 'iff=0', 'im=2', 'tstates=166']
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())
        self.assertEqual(z80fname, outfile)
        self.assertEqual(data, snapshot[start:stop])
        self.assertEqual(exp_reg, z80reg)
        self.assertEqual(exp_state, z80state)

    @patch.object(trace, 'write_snapshot', mock_write_snapshot)
    def test_write_z80_128k(self):
        sna = [0] * 131103
        start = 32768
        sna[49179:49181] = (start % 256, start // 256) # PC
        code = [
            0x37,                   # $8000 SCF
            0x9F,                   # $8001 SBC A,A
            0xF3,                   # $8002 DI
            0xED, 0x5E,             # $8003 IM 2
            0xED, 0x47,             # $8005 LD I,A
            0xED, 0x4F,             # $8007 LD R,A
            0x08,                   # $8009 EX AF,AF'
            0x3E, 0x01,             # $800A LD A,$01
            0xA7,                   # $800C AND A
            0xD3, 0xFE,             # $800D OUT ($FE),A
            0x01, 0xFD, 0x7F,       # $800F LD BC,$7FFD
            0xED, 0x79,             # $8012 OUT (C),A
            0x11, 0xB8, 0x53,       # $8014 LD DE,$53B8
            0x21, 0x57, 0x63,       # $8017 LD HL,$6357
            0xD9,                   # $801A EXX
            0x01, 0x27, 0xEF,       # $801C LD BC,$EF27
            0x11, 0xF8, 0x13,       # $801E LD DE,$13F8
            0x21, 0x77, 0x7D,       # $8021 LD HL,$7D77
            0x31, 0xE9, 0xBE,       # $8024 LD SP,$BEE9
            0xDD, 0x21, 0x72, 0x0D, # $8027 LD IX,$0D72
            0xFD, 0x21, 0x2E, 0x27, # $802B LD IY,$272E
        ]
        sna[start - 16357:start - 16357 + len(code)] = code
        sna[49183:65567] = [1] * 16384 # Bank 1
        snafile = self.write_bin_file(sna, suffix='.sna')
        outfile = os.path.join(self.make_directory(), 'out.z80')
        stop = start + len(code)
        output, error = self.run_trace(f'-S {stop} {snafile} {outfile}')
        exp_output = f"""
            Stopped at ${stop:04X}
            Wrote {outfile}
        """
        exp_reg = (
            'a=1',
            'f=16',
            'bc=61223',
            'de=5112',
            'hl=32119',
            'ix=3442',
            'iy=10030',
            'sp=48873',
            'i=255',
            'r=145',
            '^a=255',
            '^f=187',
            '^bc=32765',
            '^de=21432',
            '^hl=25431',
            f'pc={stop}'
        )
        exp_state = [f'ay[{n}]=0' for n in range(16)]
        exp_state.extend(('7ffd=1', 'fffd=0', 'border=1', 'fe=1', 'iff=0', 'im=2', 'tstates=178'))
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())
        self.assertEqual(z80fname, outfile)
        self.assertEqual(code, snapshot[start:stop])
        self.assertTrue(all(b == 1 for b in snapshot[0xC000:0x10000]))
        self.assertEqual(exp_reg, z80reg)
        self.assertEqual(exp_state, z80state)

    @patch.object(trace, 'write_snapshot', mock_write_snapshot)
    def test_ay_tracing_from_z80(self):
        code = [
            0x21, 0x10, 0xFF,       # $8000 LD HL,$FF10
            0x01, 0xFD, 0xFF,       # $8003 LD BC,$FFFD
            0xED, 0x78,             # $8006 IN A,(C)    ; Store value of
            0x77,                   # $8008 LD (HL),A   ; current AY register.
            0x2D,                   # $8009 DEC L
            0xED, 0x69,             # $800A OUT (C),L   ; Switch AY register.
            0xED, 0x78,             # $800C IN A,(C)    ; Store value of this
            0x77,                   # $800E LD (HL),A   ; AY register.
            0x06, 0xBF,             # $800F LD B,$BF    ; BC=$BFFD.
            0x3C,                   # $8011 INC A       ; Increment value of
            0xED, 0x79,             # $8012 OUT (C),A   ; this AY register.
            0x44,                   # $8014 LD B,H      ; BC=$FFFD.
            0x2D,                   # $8015 DEC L       ; Next AY register.
            0xF2, 0x0A, 0x80,       # $8016 JP P,$800A
        ]
        ram = [0] * 49152
        start = 32768
        ram[start - 0x4000:start - 0x4000 + len(code)] = code
        stop = start + len(code)
        ay = [5] + [128 + n for n in range(16)]
        z80file = self.write_z80(ram, machine_id=4, ay=ay)[1]
        output, error = self.run_trace(f'-s {start} -S {stop} {z80file} out.z80')
        exp_state = [f'ay[{n}]={v + 1}' for n, v in enumerate(ay[1:])]
        exp_state.append('fffd=0')
        self.assertEqual(snapshot[0xff10], ay[1 + ay[0]])   # Input: current AY register value
        self.assertEqual(ay[1:], snapshot[0xff00:0xff10])   # Input: all AY register values
        self.assertLessEqual(set(exp_state), set(z80state)) # Output: AY state

    @patch.object(trace, 'write_snapshot', mock_write_snapshot)
    def test_ay_tracing_from_szx(self):
        code = [
            0x21, 0x10, 0xFF,       # $8000 LD HL,$FF10
            0x01, 0xFD, 0xFF,       # $8003 LD BC,$FFFD
            0xED, 0x78,             # $8006 IN A,(C)    ; Store value of
            0x77,                   # $8008 LD (HL),A   ; current AY register.
            0x2D,                   # $8009 DEC L
            0xED, 0x69,             # $800A OUT (C),L   ; Switch AY register.
            0xED, 0x78,             # $800C IN A,(C)    ; Store value of this
            0x77,                   # $800E LD (HL),A   ; AY register.
            0x06, 0xBF,             # $800F LD B,$BF    ; BC=$BFFD.
            0x3C,                   # $8011 INC A       ; Increment value of
            0xED, 0x79,             # $8012 OUT (C),A   ; this AY register.
            0x44,                   # $8014 LD B,H      ; BC=$FFFD.
            0x2D,                   # $8015 DEC L       ; Next AY register.
            0xF2, 0x0A, 0x80,       # $8016 JP P,$800A
        ]
        ram = [0] * 49152
        start = 32768
        ram[start - 0x4000:start - 0x4000 + len(code)] = code
        stop = start + len(code)
        ay = [7] + [192 + n for n in range(16)]
        szxfile = self.write_szx(ram, machine_id=2, ay=ay)
        output, error = self.run_trace(f'-s {start} -S {stop} {szxfile} out.z80')
        exp_state = [f'ay[{n}]={v + 1}' for n, v in enumerate(ay[1:])]
        exp_state.append('fffd=0')
        self.assertEqual(snapshot[0xff10], ay[1 + ay[0]])   # Input: current AY register value
        self.assertEqual(ay[1:], snapshot[0xff00:0xff10])   # Input: all AY register values
        self.assertLessEqual(set(exp_state), set(z80state)) # Output: AY state
