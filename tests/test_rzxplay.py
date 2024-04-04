import os
from textwrap import dedent
from unittest.mock import patch
import zlib

from skoolkittest import SkoolKitTestCase, RZX
from skoolkit import VERSION, SkoolKitError, rzxplay

class MockSimulator:
    def __init__(self, *args, **kwargs):
        global simulator
        simulator = self
        self.memory = [0] * 65536
        self.opcodes = [self.nop] * 256
        self.registers = [0] * 29

    def set_tracer(self, tracer, *args, **kwargs):
        pass

    def nop(self):
        pass

def mock_run(*args):
    global run_args
    run_args = args

def mock_write_snapshot(fname, ram, registers, state, machine):
    global s_fname, s_memory, s_banks, s_reg, s_state, s_machine
    s_fname = fname
    s_memory = [0] * 65536
    if len(ram) == 8:
        s_banks = ram
        page = 0
        for spec in state:
            if spec.startswith('7ffd='):
                page = int(spec[5:]) % 8
                break
        s_memory[0x4000:0x8000] = ram[5]
        s_memory[0x8000:0xC000] = ram[2]
        s_memory[0xC000:] = ram[page]
    else:
        s_banks = None
        s_memory[0x4000:] = ram
    s_reg = registers
    s_state = state
    s_machine = machine

class RzxplayTest(SkoolKitTestCase):
    def _test_rzx(self, rzx, exp_output, options='', exp_trace=None, outfile=None, exp_error=''):
        if isinstance(rzx, str):
            rzxfile = rzx
        else:
            rzxfile = self.write_rzx_file(rzx)
        logfile = 'trace.log'
        if exp_trace:
            options += f' --trace {logfile}'
        args = f'{options} {rzxfile}'
        if outfile:
            args += f' {outfile}'
        output, error = self.run_rzxplay(args)
        self.assertEqual(dedent(exp_error).lstrip(), error)
        self.assertEqual(dedent(exp_output).lstrip(), output)
        if exp_trace:
            self.assertTrue(os.path.isfile(logfile))
            with open(logfile) as f:
                trace = f.read()
            self.assertEqual(dedent(exp_trace).lstrip(), trace)

    def _check_rzx_snapshot(self, rzxfile):
        with open(rzxfile, 'rb') as f:
            data = f.read()
        i = 10
        ext, sdata = None, None
        while i < len(data):
            block_id = data[i]
            block_len = data[i + 1] + 256 * data[i + 2] + 65536 * data[i + 3] + 16777216 * data[i + 4]
            if block_id == 0x30:
                # Snapshot
                ext = ''.join(chr(b) for b in data[i + 9:i + 13] if b)
                sdata = zlib.decompress(data[i + 17:i + block_len])
                break
            i += block_len
        return ext, sdata

    @patch.object(rzxplay, 'run', mock_run)
    def test_default_option_values(self):
        rzxplay.main(['test.rzx'])
        rzxfile, options = run_args
        self.assertEqual(rzxfile, 'test.rzx')
        self.assertFalse(options.force)
        self.assertEqual(options.fps, 50)
        self.assertTrue(options.screen)
        self.assertFalse(options.python)
        self.assertFalse(options.quiet)
        self.assertEqual(options.scale, 2)
        self.assertIsNone(options.stop)
        self.assertIsNone(options.trace)

    def test_sna(self):
        ram = [0] * 0xC000
        header = [0] * 27
        sp = 0x8000
        pc = 0xC000
        header[23:25] = (sp % 256, sp // 256)
        ram[0x4000:0x4002] = (pc % 256, pc // 256)
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        sna = header + ram
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(sna, 'sna', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_z80v1(self):
        ram = [0] * 0xC000
        pc = 0xD000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=1, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_z80v2(self):
        ram = [0] * 0xC000
        pc = 0xE000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=2, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_z80v3(self):
        ram = [0] * 0xC000
        pc = 0xF000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=3, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_szx(self):
        ram = [0] * 0xC000
        pc = 0x8000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = [0] * 37
        registers[22:24] = (pc % 256, pc // 256)
        szxdata = self.write_szx(ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(szxdata, 'szx', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_z80v2_unsupported_hardware(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=2, machine_id=4, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_error = 'WARNING: Unsupported hardware (IF1)\n'
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_error=exp_error)

    def test_z80v3_unsupported_hardware(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=3, machine_id=5, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_error = 'WARNING: Unsupported hardware (IF1 or MGT)\n'
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_error=exp_error)

    def test_z80v3_unsupported_hardware_with_hardware_modifier(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=3, machine_id=5, modify=True, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_error = 'WARNING: Unsupported hardware (IF1 or MGT)\n'
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_error=exp_error)

    def test_szx_unsupported_block(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = [0] * 37
        registers[22:24] = (pc % 256, pc // 256)
        covx = [0] * 12
        covx[:4] = [ord(c) for c in 'COVX']
        covx[4] = 4 # Block size
        szxdata = self.write_szx(ram, machine_id=3, registers=registers, blocks=[covx], ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(szxdata, 'szx', frames)
        exp_output = ''
        exp_error = 'WARNING: Unsupported block(s) (COVX) in SZX snapshot\n'
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_error=exp_error)

    def test_szx_unsupported_blocks(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = [0] * 37
        registers[22:24] = (pc % 256, pc // 256)
        if1 = [0] * 24
        if1[:3] = [ord(c) for c in 'IF1']
        if1[4] = 16 # Block size
        covx = [0] * 12
        covx[:4] = [ord(c) for c in 'COVX']
        covx[4] = 4 # Block size
        szxdata = self.write_szx(ram, machine_id=3, registers=registers, blocks=[if1, covx], ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(szxdata, 'szx', frames)
        exp_output = ''
        exp_error = 'WARNING: Unsupported block(s) (COVX, IF1) in SZX snapshot\n'
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_error=exp_error)

    def test_compressed_snapshot(self):
        ram = [0] * 0xC000
        header = [0] * 27
        sp = 0x8000
        pc = 0x6000
        header[23:25] = (sp % 256, sp // 256)
        ram[0x4000:0x4002] = (pc % 256, pc // 256)
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        sna = header + ram
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(sna, 'sna', frames, flags=2)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_repeated_port_readings(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE, # IN A,($FE)
            0xDB, 0xFE, # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191]), (1, 65535, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_multiple_snapshots(self):
        pc = 0xC000
        code = (
            [0xAF], # XOR A
            [0xA8], # XOR B
        )
        frames = (
            [(1, 0, [])],
            [(1, 0, [])]
        )
        rzx = RZX()
        for c, f in zip(code, frames):
            ram = [0] * 0xC000
            ram[pc - 0x4000:pc - 0x4000 + len(c)] = c
            registers = {'PC': pc, 'iff1': 1}
            z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
            rzx.add_snapshot(z80data, 'z80', f)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $C000 XOR A
            F:1 C:00001 I:00000 $C000 XOR B
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_sequence_of_input_recording_blocks(self):
        pc = 0x7000
        code = (
            0xAF,       # XOR A
            0xDB, 0xFE, # IN A,($FE)
            0xA8,       # XOR B
        )
        rzx = RZX()
        ram = [0] * 0xC000
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        input_recs = (
            [(1, 0, [])],
            [(1, 1, [191])],
            [(1, 0, [])]
        )
        rzx.add_snapshot(z80data, 'z80', input_recs[0])
        rzx.add_snapshot(frames=input_recs[1])
        rzx.add_snapshot(frames=input_recs[2])
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $7000 XOR A
            F:1 C:00001 I:00001 $7001 IN A,($FE)
            F:2 C:00001 I:00000 $7003 XOR B
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_unsupported_snapshot_at_end_of_file_is_ignored(self):
        ram1 = [0] * 0xC000
        pc = 0xF000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram1[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram1, registers=registers, ret_data=True)
        rzx = RZX()
        frames1 = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames1)
        ram2 = [0] * 0xC000
        szxdata = self.write_szx(ram2, machine_id=6, ret_data=True)
        frames2 = ()
        rzx.add_snapshot(szxdata, 'szx', frames2)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_halt_waits_for_rzx_frame_boundary(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0x76, # HALT
            0x76, # HALT
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc, 'iff1': 1}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(2, 0, []), (2, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames, tstates=69886)
        exp_output = ''
        exp_trace = """
            F:0 C:00002 I:00000 $C000 HALT
            F:0 C:00001 I:00000 $C000 HALT
            F:1 C:00002 I:00000 $0038 PUSH AF
            F:1 C:00001 I:00000 $0039 PUSH HL
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_ld_a_i_at_frame_boundary_default(self):
        ram = [0] * 0xC000
        pc = 0xFEFA
        code = (
            0xED, 0x57,       # $FEFA LD A,I      ; Set bit 2 of F
            0xEA, 0xFA, 0xFE, # $FEFC JP PE,$FEFA ; This jump is made
            0x01, 0xFF,       # $FEFF DEFW $FF01  ; Interrupt vector
            0xC9,             # $FF01 RET         ; Interrupt routine
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc, 'I': 0xFE, 'iff1': 1, 'im': 2}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (3, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $FEFA LD A,I
            F:1 C:00003 I:00000 $FF01 RET
            F:1 C:00002 I:00000 $FEFC JP PE,$FEFA
            F:1 C:00001 I:00000 $FEFA LD A,I
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_ld_a_i_at_frame_boundary_when_flags_bit_0_set(self):
        ram = [0] * 0xC000
        pc = 0xFEFA
        code = (
            0xED, 0x57,       # $FEFA LD A,I      ; Reset bit 2 of F
            0xE2, 0xFA, 0xFE, # $FEFC JP PO,$FEFA ; This jump is made
            0x01, 0xFF,       # $FEFF DEFW $FF01  ; Interrupt vector
            0xC9,             # $FF01 RET         ; Interrupt routine
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc, 'I': 0xFE, 'iff1': 1, 'im': 2}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (3, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $FEFA LD A,I
            F:1 C:00003 I:00000 $FF01 RET
            F:1 C:00002 I:00000 $FEFC JP PO,$FEFA
            F:1 C:00001 I:00000 $FEFA LD A,I
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen --flags 1', exp_trace)

    def test_ld_a_r_at_frame_boundary_default(self):
        ram = [0] * 0xC000
        pc = 0xFEFA
        code = (
            0xED, 0x5F,       # $FEFA LD A,R      ; Set bit 2 of F
            0xEA, 0xFA, 0xFE, # $FEFC JP PE,$FEFA ; This jump is made
            0x01, 0xFF,       # $FEFF DEFW $FF01  ; Interrupt vector
            0xC9,             # $FF01 RET         ; Interrupt routine
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc, 'I': 0xFE, 'iff1': 1, 'im': 2}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (3, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $FEFA LD A,R
            F:1 C:00003 I:00000 $FF01 RET
            F:1 C:00002 I:00000 $FEFC JP PE,$FEFA
            F:1 C:00001 I:00000 $FEFA LD A,R
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_ld_a_r_at_frame_boundary_when_flags_bit_0_set(self):
        ram = [0] * 0xC000
        pc = 0xFEFA
        code = (
            0xED, 0x5F,       # $FEFA LD A,R      ; Reset bit 2 of F
            0xE2, 0xFA, 0xFE, # $FEFC JP PO,$FEFA ; This jump is made
            0x01, 0xFF,       # $FEFF DEFW $FF01  ; Interrupt vector
            0xC9,             # $FF01 RET         ; Interrupt routine
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc, 'I': 0xFE, 'iff1': 1, 'im': 2}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (3, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $FEFA LD A,R
            F:1 C:00003 I:00000 $FF01 RET
            F:1 C:00002 I:00000 $FEFC JP PO,$FEFA
            F:1 C:00001 I:00000 $FEFA LD A,R
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen --flags 1', exp_trace)

    def test_ei_does_not_block_interrupt_before_frame_with_fetch_count_1_default(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xFB, # EI
            0xAF, # XOR A
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (1, 0, []), (2, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $C000 EI
            F:1 C:00001 I:00000 $0038 PUSH AF
            F:2 C:00002 I:00000 $0039 PUSH HL
            F:2 C:00001 I:00000 $003A LD HL,($5C78)
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_ei_does_not_block_interrupt_before_frame_with_fetch_count_2_default(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xFB, # EI
            0xAF, # XOR A
            0xA8, # XOR B
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (2, 0, []), (1, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $C000 EI
            F:1 C:00002 I:00000 $0038 PUSH AF
            F:1 C:00001 I:00000 $0039 PUSH HL
            F:2 C:00001 I:00000 $003A LD HL,($5C78)
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_ei_blocks_interrupt_before_frame_with_fetch_count_1_when_flags_bit_1_set(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xFB, # EI
            0xAF, # XOR A
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (1, 0, []), (3, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $C000 EI
            F:1 C:00001 I:00000 $C001 XOR A
            F:2 C:00003 I:00000 $0038 PUSH AF
            F:2 C:00002 I:00000 $0039 PUSH HL
            F:2 C:00001 I:00000 $003A LD HL,($5C78)
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen --flags 2', exp_trace)

    def test_ei_blocks_interrupt_before_frame_with_fetch_count_2_when_flags_bit_1_set(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xFB, # EI
            0xAF, # XOR A
            0xA8, # XOR B
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (2, 0, []), (3, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $C000 EI
            F:1 C:00002 I:00000 $C001 XOR A
            F:1 C:00001 I:00000 $C002 XOR B
            F:2 C:00003 I:00000 $0038 PUSH AF
            F:2 C:00002 I:00000 $0039 PUSH HL
            F:2 C:00001 I:00000 $003A LD HL,($5C78)
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen --flags 2', exp_trace)

    def test_ei_does_not_block_interrupt_before_frame_with_fetch_count_3_when_flags_bit_1_set(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xFB, # EI
            0xAF, # XOR A
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (3, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $C000 EI
            F:1 C:00003 I:00000 $0038 PUSH AF
            F:1 C:00002 I:00000 $0039 PUSH HL
            F:1 C:00001 I:00000 $003A LD HL,($5C78)
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen --flags 2', exp_trace)

    def test_empty_frame_at_start_of_input_recording_block(self):
        ram = [0] * 0xC000
        pc = 0x8000
        code = (
            0xAF, # XOR A
            0xA8, # XOR B
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(0, 0, []), (1, 0, []), (1, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:1 C:00001 I:00000 $8000 XOR A
            F:2 C:00001 I:00000 $8001 XOR B
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_empty_frame_in_middle_of_input_recording_block(self):
        ram = [0] * 0xC000
        pc = 0x8000
        code = (
            0xAF, # XOR A
            0xA8, # XOR B
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (0, 0, []), (1, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $8000 XOR A
            F:2 C:00001 I:00000 $8001 XOR B
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_empty_frame_at_end_of_input_recording_block(self):
        ram = [0] * 0xC000
        pc = 0x8000
        code = (
            0xAF, # XOR A
            0xA8, # XOR B
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (1, 0, []), (0, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $8000 XOR A
            F:1 C:00001 I:00000 $8001 XOR B
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_empty_frames_throughout_input_recording_block(self):
        ram = [0] * 0xC000
        pc = 0x9000
        code = (
            0xAF, # XOR A
            0xA8, # XOR B
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(0, 0, [])] * 3
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_empty_frame_does_not_block_interrupt(self):
        ram = [0] * 0xC000
        pc = 0xFEFD
        code = (
            0x76,       # $FEFD HALT
            0xAF,       # $FEFE XOR A
            0x01, 0xFF, # $FEFF DEFW $FF01 ; Interrupt vector
            0xC9,       # $FF01 RET        ; Interrupt routine
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc, 'I': 0xFE, 'iff1': 1, 'im': 2}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (0, 0, []), (2, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $FEFD HALT
            F:2 C:00002 I:00000 $FF01 RET
            F:2 C:00001 I:00000 $FEFE XOR A
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_ld_r_a_counts_as_two_fetches(self):
        ram = [0] * 0xC000
        pc = 0xC000
        a = 1
        code = (
            0xED, 0x4F, # LD R,A
            0xAF,       # XOR A
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc, 'a': a}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(3, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00003 I:00000 $C000 LD R,A
            F:0 C:00001 I:00000 $C002 XOR A
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_bank_switching(self):
        ram = [0] * 0xC000
        pc = 0xBFFE
        a = 7
        bc = 0x7FFD
        code = (
            0xED, 0x79, # $BFFE OUT (C),A
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        pages = {a: [0] * 0x4000}
        pages[a][0] = 0xAF # $C000 XOR A
        registers = {'A': a, 'B': bc // 256, 'C': bc % 256, 'PC': pc, 'iff1': 1}
        z80data = self.write_z80_file(None, ram, machine_id=4, out7ffd=4, pages=pages, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(3, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00003 I:00000 $BFFE OUT (C),A
            F:0 C:00001 I:00000 $C000 XOR A
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_printing_progress(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xAF, # XOR A
            0xA8, # XOR B
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (1, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = "[ 50.0%]\x08\x08\x08\x08\x08\x08\x08\x08[100.0%]\x08\x08\x08\x08\x08\x08\x08\x08"
        self._test_rzx(rzx, exp_output, '--no-screen')

    def test_printing_progress_with_stop_option(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xAF, # XOR A
            0xA8, # XOR B
            0xA9, # XOR C
            0xAA, # XOR D
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, [])] * 4
        rzx.add_snapshot(z80data, 'z80', frames)
        b = '\x08\x08\x08\x08\x08\x08\x08\x08'
        exp_output = f'[ 33.3%]{b}[ 66.7%]{b}[100.0%]{b}'
        self._test_rzx(rzx, exp_output, '--stop 3 --no-screen')

    @patch.object(rzxplay, 'write_snapshot', mock_write_snapshot)
    def test_write_48k_snapshot(self):
        ram = [0] * 0xC000
        pc = 0xF000
        code = [
            0xDB, 0xFE, # IN A,($FE)
        ]
        end = pc + len(code)
        ram[pc - 0x4000:end - 0x4000] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        outfile = 'out.z80'
        exp_output = f'Wrote {outfile}\n'
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', outfile=outfile)
        self.assertEqual(s_fname, outfile)
        self.assertLessEqual({'A=191', f'PC={end}'}, set(s_reg))
        self.assertIn('tstates=0', s_state)
        self.assertIsNone(s_banks)
        self.assertEqual(code, s_memory[pc:end])

    @patch.object(rzxplay, 'write_snapshot', mock_write_snapshot)
    def test_write_128k_snapshot(self):
        ram = [0] * 0xC000
        pc = 0xF000
        code = [
            0xDB, 0xFE, # IN A,($FE)
        ]
        end = pc + len(code)
        ram[pc - 0x4000:end - 0x4000] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, machine_id=4, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        outfile = 'out.z80'
        exp_output = f'Wrote {outfile}\n'
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', outfile=outfile)
        self.assertEqual(s_fname, outfile)
        self.assertLessEqual({'A=191', f'PC={end}'}, set(s_reg))
        self.assertIn('tstates=0', s_state)
        self.assertIsNotNone(s_banks)
        self.assertEqual(s_machine, '128K')
        self.assertEqual(code, s_memory[pc:end])

    @patch.object(rzxplay, 'write_snapshot', mock_write_snapshot)
    def test_write_plus2_snapshot(self):
        ram = [0] * 0xC000
        pc = 0xF000
        code = [
            0xDB, 0xFE, # IN A,($FE)
        ]
        end = pc + len(code)
        ram[pc - 0x4000:end - 0x4000] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, machine_id=4, modify=True, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        outfile = 'out.z80'
        exp_output = f'Wrote {outfile}\n'
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', outfile=outfile)
        self.assertEqual(s_fname, outfile)
        self.assertLessEqual({'A=191', f'PC={end}'}, set(s_reg))
        self.assertIn('tstates=0', s_state)
        self.assertIsNotNone(s_banks)
        self.assertEqual(s_machine, '+2')
        self.assertEqual(code, s_memory[pc:end])

    def test_write_rzx_file(self):
        pc = 0xF000
        code = (
            0xAF,       # XOR A
            0xA8,       # XOR B
            0xED, 0x78, # IN A,(C)
        )
        rzx = RZX()
        ram = [0] * 0xC000
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        frames = ((1, 0, []), (1, 0, []), (1, 1, [0]))
        rzx.add_snapshot(z80data, 'z80', frames)
        outfile = 'out.rzx'
        exp_output = f'Wrote {outfile}\n'
        exp_trace = """
            F:0 C:00001 I:00000 $F000 XOR A
        """
        self._test_rzx(rzx, exp_output, '--stop 1 --quiet --no-screen', exp_trace, outfile)

        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $F001 XOR B
            F:1 C:00001 I:00001 $F002 IN A,(C)
        """
        self._test_rzx(outfile, exp_output, '--quiet --no-screen', exp_trace)

    def test_write_rzx_file_with_two_snapshots(self):
        spec = (
            (0xF000, [(1, 0, []), (1, 0, [])], (
                0xAF,       # XOR A
                0xA8,       # XOR B
            )),
            (0xF002, [(1, 1, [0])], (
                0xED, 0x78, # IN A,(C)
            ))
        )
        rzx = RZX()
        for pc, frames, code in spec:
            ram = [0] * 0xC000
            ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
            registers = {'PC': pc}
            z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
            rzx.add_snapshot(z80data, 'z80', frames)

        outfile = 'out.rzx'
        exp_output = f'Wrote {outfile}\n'
        exp_trace = """
            F:0 C:00001 I:00000 $F000 XOR A
        """
        self._test_rzx(rzx, exp_output, '--stop 1 --quiet --no-screen', exp_trace, outfile)

        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $F001 XOR B
            F:1 C:00001 I:00001 $F002 IN A,(C)
        """
        self._test_rzx(outfile, exp_output, '--quiet --no-screen', exp_trace)

    def test_write_rzx_file_containing_z80v1_snapshot(self):
        pc = 0xD000
        code = (
            0xB7, # OR A
            0xB0, # OR B
        )
        rzx = RZX()
        ram = [0] * 0xC000
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=1, registers=registers, ret_data=True)
        frames = [(1, 0, []), (1, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)

        outfile = 'out.rzx'
        exp_output = f'Wrote {outfile}\n'
        exp_trace = """
            F:0 C:00001 I:00000 $D000 OR A
        """
        self._test_rzx(rzx, exp_output, '--stop 1 --quiet --no-screen', exp_trace, outfile)

        ext, sdata = self._check_rzx_snapshot(outfile)
        self.assertEqual(ext, 'z80')
        self.assertEqual(sdata[6] + 256 * sdata[7], pc + 1) # PC

        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $D001 OR B
        """
        self._test_rzx(outfile, exp_output, '--quiet --no-screen', exp_trace)

    def test_write_rzx_file_containing_z80v2_snapshot(self):
        pc = 0xD000
        code = (
            0xB7, # OR A
            0xB0, # OR B
        )
        rzx = RZX()
        ram = [0] * 0xC000
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=2, registers=registers, ret_data=True)
        frames = [(1, 0, []), (1, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)

        outfile = 'out.rzx'
        exp_output = f'Wrote {outfile}\n'
        exp_trace = """
            F:0 C:00001 I:00000 $D000 OR A
        """
        self._test_rzx(rzx, exp_output, '--stop 1 --quiet --no-screen', exp_trace, outfile)

        ext, sdata = self._check_rzx_snapshot(outfile)
        self.assertEqual(ext, 'z80')
        self.assertEqual(sdata[6] + sdata[7], 0)
        self.assertEqual(sdata[30], 23) # Version 2

        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $D001 OR B
        """
        self._test_rzx(outfile, exp_output, '--quiet --no-screen', exp_trace)

    def test_write_rzx_file_containing_128k_snapshot(self):
        pc = 0xD000
        code = (
            0x21, 0xFD, 0x3F, # LD HL,$3FFD
            0x7E,             # LD A,(HL)
            0xB7,             # OR A
            0xC2, 0x9A, 0x00, # JP NZ,$009A
        )
        rzx = RZX()
        ram = [0] * 0xC000
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, machine_id=4, registers=registers, ret_data=True)
        frames = [(1, 0, []), (4, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)

        outfile = 'out.rzx'
        exp_output = f'Wrote {outfile}\n'
        exp_trace = """
            F:0 C:00001 I:00000 $D000 LD HL,$3FFD
        """
        self._test_rzx(rzx, exp_output, '--stop 1 --quiet --no-screen', exp_trace, outfile)

        exp_output = ''
        exp_trace = """
            F:0 C:00004 I:00000 $D003 LD A,(HL)
            F:0 C:00003 I:00000 $D004 OR A
            F:0 C:00002 I:00000 $D005 JP NZ,$009A
            F:0 C:00001 I:00000 $009A LD HL,$06D8
        """
        self._test_rzx(outfile, exp_output, '--quiet --no-screen', exp_trace)

    def test_write_rzx_file_containing_plus2_snapshot(self):
        pc = 0xD000
        code = (
            0x21, 0xFD, 0x3F, # LD HL,$3FFD
            0x7E,             # LD A,(HL)
            0xB7,             # OR A
            0xCA, 0x9A, 0x00, # JP Z,$009A
        )
        rzx = RZX()
        ram = [0] * 0xC000
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, machine_id=4, modify=True, registers=registers, ret_data=True)
        frames = [(1, 0, []), (4, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)

        outfile = 'out.rzx'
        exp_output = f'Wrote {outfile}\n'
        exp_trace = """
            F:0 C:00001 I:00000 $D000 LD HL,$3FFD
        """
        self._test_rzx(rzx, exp_output, '--stop 1 --quiet --no-screen', exp_trace, outfile)

        exp_output = ''
        exp_trace = """
            F:0 C:00004 I:00000 $D003 LD A,(HL)
            F:0 C:00003 I:00000 $D004 OR A
            F:0 C:00002 I:00000 $D005 JP Z,$009A
            F:0 C:00001 I:00000 $009A LD HL,$06F7
        """
        self._test_rzx(outfile, exp_output, '--quiet --no-screen', exp_trace)

    def test_write_rzx_file_containing_z80_snapshot_with_unsupported_hardware(self):
        pc = 0xD000
        code = (
            0xB7, # OR A
            0xB0, # OR B
        )
        rzx = RZX()
        ram = [0] * 0xC000
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, machine_id=1, registers=registers, ret_data=True)
        frames = [(1, 0, []), (1, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)

        outfile = 'out.rzx'
        exp_output = f'Wrote {outfile}\n'
        exp_error = 'WARNING: Unsupported hardware (IF1 or MGT)\n'
        self._test_rzx(rzx, exp_output, '--stop 1 --quiet --no-screen', outfile=outfile, exp_error=exp_error)

        ext, sdata = self._check_rzx_snapshot(outfile)
        self.assertEqual(ext, 'z80')
        self.assertEqual(sdata[34], 1) # Machine ID

    def test_write_rzx_file_containing_szx_snapshot(self):
        pc = 0xD000
        code = (
            0xB7, # OR A
            0xB0, # OR B
        )
        rzx = RZX()
        ram = [0] * 0xC000
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = [0] * 37
        registers[22:24] = (pc % 256, pc // 256)
        szxdata = self.write_szx(ram, registers=registers, ret_data=True)
        frames = [(1, 0, []), (1, 0, [])]
        rzx.add_snapshot(szxdata, 'szx', frames)

        outfile = 'out.rzx'
        exp_output = f'Wrote {outfile}\n'
        exp_trace = """
            F:0 C:00001 I:00000 $D000 OR A
        """
        self._test_rzx(rzx, exp_output, '--stop 1 --quiet --no-screen', exp_trace, outfile)

        ext, sdata = self._check_rzx_snapshot(outfile)
        self.assertEqual(ext, 'szx')

        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $D001 OR B
        """
        self._test_rzx(outfile, exp_output, '--quiet --no-screen', exp_trace)

    def test_write_rzx_file_containing_szx_snapshot_with_unsupported_hardware(self):
        pc = 0xD000
        code = (
            0xB7, # OR A
            0xB0, # OR B
        )
        rzx = RZX()
        ram = [0] * 0xC000
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = [0] * 37
        registers[22:24] = (pc % 256, pc // 256)
        covx = [0] * 12
        covx[:4] = [ord(c) for c in 'COVX']
        covx[4] = 4 # Block size
        szxdata = self.write_szx(ram, registers=registers, blocks=[covx], ret_data=True)
        frames = [(1, 0, [])]
        rzx.add_snapshot(szxdata, 'szx', frames)

        outfile = 'out.rzx'
        exp_output = f'Wrote {outfile}\n'
        exp_error = 'WARNING: Unsupported block(s) (COVX) in SZX snapshot\n'
        self._test_rzx(rzx, exp_output, '--stop 1 --quiet --no-screen', outfile=outfile, exp_error=exp_error)

        ext, sdata = self._check_rzx_snapshot(outfile)
        self.assertEqual(ext, 'szx')
        i = 8
        found_covx = False
        while i + 8 <= len(sdata):
            block_id = sdata[i:i + 4]
            if block_id == b'COVX':
                found_covx = True
                break
            block_len = sdata[i + 4] + 256 * sdata[i + 5] + 65536 * sdata[i + 6] + 16777216 * sdata[i + 7]
            i += 8 + block_len
        self.assertTrue(found_covx)

    def test_write_unsupported_file_type(self):
        ram = [0] * 0xC000
        pc = 0x6000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen {rzxfile} out.slt')
        self.assertEqual(cm.exception.args[0], 'Unknown file type: slt')

    def test_szx_unsupported_machine(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = [0] * 37
        registers[22:24] = (pc % 256, pc // 256)
        szxdata = self.write_szx(ram, machine_id=4, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(szxdata, 'szx', frames)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Unsupported machine type')

    def test_too_many_port_readings(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE, # IN A,($FE)
            0x00,       # NOP
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191]), (1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], '1 port reading(s) left for frame 1')

    def test_too_many_port_readings_with_sequence_of_input_recording_blocks(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE, # IN A,($FE) ; Frame 0
            0xDB, 0xFE, # IN A,($FE) ; Frame 1
            0x00,       # NOP
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        input_recs = (
            [(1, 1, [191])],     # Frame 0
            [(2, 2, [191, 191])] # Frame 1
        )
        rzx.add_snapshot(z80data, 'z80', input_recs[0])
        rzx.add_snapshot(frames=input_recs[1])
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], '1 port reading(s) left for frame 1')

    def test_too_few_port_readings(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE, # IN A,($FE)
            0xDB, 0xFE, # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191]), (1, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Port readings exhausted for frame 1')

    def test_too_few_port_readings_with_sequence_of_input_recording_blocks(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xAF,       # XOR A      ; Frame 0
            0xDB, 0xFE, # IN A,($FE) ; Frame 1
            0xDB, 0xFE, # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        input_recs = (
            [(1, 0, [])],   # Frame 0
            [(2, 1, [191])] # Frame 1
        )
        rzx.add_snapshot(z80data, 'z80', input_recs[0])
        rzx.add_snapshot(frames=input_recs[1])
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Port readings exhausted for frame 1')

    def test_malformed_sna(self):
        sna = [0] * 28
        rzx = RZX()
        rzx.add_snapshot(sna, 'sna')
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Invalid SNA file')

    def test_malformed_szx(self):
        szx = [128] * 8
        rzx = RZX()
        rzx.add_snapshot(szx, 'szx')
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Invalid SZX file')

    def test_malformed_z80(self):
        z80 = [255] * 31
        rzx = RZX()
        rzx.add_snapshot(z80, 'z80')
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'RAM is 0 bytes (should be 49152)')

    def test_corrupted_snapshot_block(self):
        sna = [0] * 49179
        rzx = RZX()
        rzx.add_snapshot(sna, 'sna', flags=2)
        snapshot_block = rzx.snapshots[0][0]
        snapshot_block[17:] = [0] * (len(snapshot_block) - 17)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Failed to decompress snapshot: Error -3 while decompressing data: unknown compression method')

    def test_corrupted_input_recording_block(self):
        rzx = RZX()
        rzx.add_snapshot(frames=[(1, 1, [0])], io_flags=2)
        io_block = rzx.snapshots[0][1]
        io_block[18:] = [0] * (len(io_block) - 18)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Failed to decompress input recording block: Error -3 while decompressing data: unknown compression method')

    def test_invalid_rzx_file(self):
        data = [0, 1, 2, 4]
        rzxfile = self.write_bin_file(data, suffix='.rzx')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Not an RZX file')

    def test_nonexistent_rzx_file(self):
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen nonexistent.rzx')
        self.assertEqual(cm.exception.args[0], 'nonexistent.rzx: file not found')

    def test_external_snapshot(self):
        rzx = RZX()
        esdata = [0] * 4 + [ord(c) for c in 'external.sna'] + [0]
        rzx.add_snapshot(esdata, 'sna', flags=1)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Missing snapshot')

    def test_input_recording_before_snapshot(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        rzx.add_snapshot(None, None)
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Missing snapshot')

    def test_unsupported_snapshot(self):
        rzx = RZX()
        sdata = [0xFF] * 10
        rzx.add_snapshot(sdata, 'slt')
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Unsupported snapshot type')

    def test_invalid_option(self):
        output, error = self.run_rzxplay('-x test.rzx', catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: rzxplay.py'))

    def test_option_flags_help(self):
        output, error = self.run_rzxplay('--flags help')
        self.assertTrue(output.startswith('Usage: --flags FLAGS\n'))
        self.assertEqual(error, '')

    def test_option_force(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=3, machine_id=5, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--force --quiet --no-screen')

    def test_option_map(self):
        ram = [0] * 0xC000
        pc = 0xFF00
        code = (
            0x06, 0x02,       # $FF00 LD B,2
            0xCD, 0x52, 0x00, # $FF02 CALL $0052
            0x10, 0xFB,       # $FF05 DJNZ $FF02
            0x18, 0xF7,       # $FF07 JR $FF00
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(9, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        mapfile = 'out.map'
        self._test_rzx(rzx, exp_output, f'--map {mapfile} --quiet --no-screen')
        exp_map = """
            $0052
            $FF00
            $FF02
            $FF05
            $FF07
        """
        with open(mapfile) as f:
            map_contents = f.read()
        self.assertEqual(dedent(exp_map).lstrip(), map_contents)

    def test_option_map_with_existing_file(self):
        ram = [0] * 0xC000
        pc = 0x6006
        code = (
            0x06, 0x02,       # $6006 LD B,2
            0xCD, 0x52, 0x00, # $6008 CALL $0052
            0x10, 0xFB,       # $600B DJNZ $6008
            0x18, 0xF7,       # $600D JR $6006
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(9, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        existing_map = """
            $0052
            $6000
            $6003
            $6006
        """
        mapfile = self.write_text_file(dedent(existing_map).lstrip(), suffix='.map')
        exp_output = ''
        self._test_rzx(rzx, exp_output, f'--map {mapfile} --quiet --no-screen')
        exp_map = """
            $0052
            $6000
            $6003
            $6006
            $6008
            $600B
            $600D
        """
        with open(mapfile) as f:
            map_contents = f.read()
        self.assertEqual(dedent(exp_map).lstrip(), map_contents)

    @patch.object(rzxplay, 'Simulator', MockSimulator)
    def test_option_python(self):
        global simulator
        simulator = None
        ram = [0] * 0xC000
        pc = 0xF000
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--python --quiet --no-screen')
        self.assertIsNotNone(simulator)

    def test_option_snapshot(self):
        ram = [0] * 0xC000
        pc = 0x9000
        code = (
            0xAF, # XOR A
            0xA8, # XOR B
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80file = self.write_z80_file(None, ram, registers=registers)
        rzx = RZX()
        esdata = [0] * 4 + [ord(c) for c in 'external.z80'] + [0]
        frames = [(2, 0, [])]
        rzx.add_snapshot(esdata, 'z80', frames, flags=1)
        exp_output = ''
        exp_trace = """
            F:0 C:00002 I:00000 $9000 XOR A
            F:0 C:00001 I:00000 $9001 XOR B
        """
        self._test_rzx(rzx, exp_output, f'--snapshot {z80file} --quiet --no-screen', exp_trace)

    def test_option_snapshot_with_unsupported_snapshot(self):
        sltfile = self.write_bin_file([0], suffix='.slt')
        rzx = RZX()
        esdata = [0] * 4 + [ord(c) for c in 'external.slt'] + [0]
        rzx.add_snapshot(esdata, 'slt', flags=1)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--snapshot {sltfile} --quiet --no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Unsupported snapshot type')

    def test_option_stop(self):
        ram = [0] * 0xC000
        pc = 0xF000
        code = (
            0xAF, # XOR A
            0xA8, # XOR B
            0xA9, # XOR C
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (1, 0, []), (1, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $F000 XOR A
            F:1 C:00001 I:00000 $F001 XOR B
        """
        self._test_rzx(rzx, exp_output, '--stop 2 --quiet --no-screen', exp_trace)

    def test_option_stop_with_empty_frame(self):
        ram = [0] * 0xC000
        pc = 0xE000
        code = (
            0xAF, # XOR A
            0xA8, # XOR B
            0xA9, # XOR C
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (0, 0, []), (2, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $E000 XOR A
        """
        self._test_rzx(rzx, exp_output, '--stop 1 --quiet --no-screen', exp_trace)

    def test_option_trace_uses_minimal_width_for_frame_number_field(self):
        ram = [0] * 0xC000
        pc = 0xF000
        code = (
            0x06, 0x00, # LD B,$00
            0x06, 0x01, # LD B,$01
            0x06, 0x02, # LD B,$02
            0x06, 0x03, # LD B,$03
            0x06, 0x04, # LD B,$04
            0x06, 0x05, # LD B,$05
            0x06, 0x06, # LD B,$06
            0x06, 0x07, # LD B,$07
            0x06, 0x08, # LD B,$08
            0x06, 0x09, # LD B,$09
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, [])] * 10
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 C:00001 I:00000 $F000 LD B,$00
            F:1 C:00001 I:00000 $F002 LD B,$01
            F:2 C:00001 I:00000 $F004 LD B,$02
            F:3 C:00001 I:00000 $F006 LD B,$03
            F:4 C:00001 I:00000 $F008 LD B,$04
            F:5 C:00001 I:00000 $F00A LD B,$05
            F:6 C:00001 I:00000 $F00C LD B,$06
            F:7 C:00001 I:00000 $F00E LD B,$07
            F:8 C:00001 I:00000 $F010 LD B,$08
            F:9 C:00001 I:00000 $F012 LD B,$09
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_rzxplay(option, catch_exit=0)
            self.assertEqual(output, f'SkoolKit {VERSION}\n')
