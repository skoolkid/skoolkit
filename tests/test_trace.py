import os
from textwrap import dedent
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import simulator, trace, SkoolKitError, VERSION

def mock_run(*args):
    global run_args
    run_args = args

def mock_write_z80v3(fname, ram, registers, state):
    global z80fname, snapshot, z80reg, z80state
    z80fname = fname
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
        z80file, options = run_args
        self.assertEqual(z80file, 'test.z80')
        self.assertIsNone(options.start)
        self.assertIsNone(options.stop)
        self.assertFalse(options.audio)
        self.assertEqual(options.depth, 2)
        self.assertIsNone(options.dump)
        self.assertFalse(options.interrupts)
        self.assertEqual(options.max_operations, 0)
        self.assertEqual(options.max_tstates, 0)
        self.assertIsNone(options.org)
        self.assertEqual(options.pokes, [])
        self.assertEqual(options.reg, [])
        self.assertIsNone(options.rom)
        self.assertFalse(options.stats)
        self.assertEqual(options.verbose, 0)

    def test_no_arguments(self):
        output, error = self.run_trace(catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage:'))

    @patch.object(trace, 'Simulator', TestSimulator)
    def test_sna(self):
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
            $6000 00       NOP              A=16 F=00010101 BC=0F0E DE=0D0C HL=0B0A IX=1312 IY=1110 IR=0115
                                            A'=09 F'=00001000 BC'=0706 DE'=0504 HL'=0302 SP=4002
            Stopped at $6001
        """
        self._test_trace(f'-vv -S 24577 {snafile}', exp_output)
        self.assertEqual(simulator.iff, 1)
        self.assertEqual(simulator.imode, 2)

    @patch.object(trace, 'Simulator', TestSimulator)
    def test_z80(self):
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
            $8000 00       NOP              A=01 F=00000010 BC=0304 DE=0506 HL=0708 IX=0B0C IY=090A IR=0D0F
                                            A'=0F F'=00010000 BC'=1112 DE'=1314 HL'=1516 SP=FFFF
            Stopped at $8001
        """
        self._test_trace(f'-vv -S 32769 {z80file}', exp_output)
        self.assertEqual(simulator.iff, 1)
        self.assertEqual(simulator.imode, 2)
        self.assertEqual(simulator.registers[25], 20004)

    @patch.object(trace, 'Simulator', TestSimulator)
    def test_szx(self):
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
        output, error = self.run_trace(f'-vv -S 49153 {szxfile}')
        self.assertEqual(error, '')
        exp_output = """
            $C000 00       NOP              A=02 F=00000001 BC=0403 DE=0605 HL=0807 IX=1211 IY=1413 IR=1517
                                            A'=0A F'=00001001 BC'=0C0B DE'=0E0D HL'=100F SP=8000
            Stopped at $C001
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())
        self.assertEqual(simulator.iff, 1)
        self.assertEqual(simulator.imode, 0)
        self.assertEqual(simulator.registers[25], 261)

    def test_no_snapshot(self):
        output, error = self.run_trace(f'-v -S 1 .')
        self.assertEqual(error, '')
        exp_output = """
            $0000 F3       DI
            Stopped at $0001
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_default_start_address_for_binary_file(self):
        data = [0xAF] # XOR A
        binfile = self.write_bin_file(data, suffix='.bin')
        output, error = self.run_trace(f'-v -S 0 {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $FFFF AF       XOR A
            Stopped at $0000
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

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
            65519 210787   LD HL,34567
            65522 0601     LD B,1
            65524 10FE     DJNZ 65524
            65526 DD7517   LD (IX+23),L
            65529 FD36C864 LD (IY-56),100
            65533 ED00     DEFB 237,0
            65535 C7       RST 0
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
            65499 013930   LD BC,12345      A=0   F=00000000 BC=12345 DE=0     HL=0     IX=0     IY=23610 I=63  R=1  
                                            A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552
            65502 11A05B   LD DE,23456      A=0   F=00000000 BC=12345 DE=23456 HL=0     IX=0     IY=23610 I=63  R=2  
                                            A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552
            65505 210787   LD HL,34567      A=0   F=00000000 BC=12345 DE=23456 HL=34567 IX=0     IY=23610 I=63  R=3  
                                            A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552
            65508 DD216EB2 LD IX,45678      A=0   F=00000000 BC=12345 DE=23456 HL=34567 IX=45678 IY=23610 I=63  R=5  
                                            A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552
            65512 FD21D5DD LD IY,56789      A=0   F=00000000 BC=12345 DE=23456 HL=34567 IX=45678 IY=56789 I=63  R=7  
                                            A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552
            65516 90       SUB B            A=208 F=10000011 BC=12345 DE=23456 HL=34567 IX=45678 IY=56789 I=63  R=8  
                                            A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552
            65517 ED4F     LD R,A           A=208 F=10000011 BC=12345 DE=23456 HL=34567 IX=45678 IY=56789 I=63  R=208
                                            A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552
            65519 ED47     LD I,A           A=208 F=10000011 BC=12345 DE=23456 HL=34567 IX=45678 IY=56789 I=208 R=210
                                            A'=0   F'=00000000 BC'=0     DE'=0     HL'=0     SP=23552
            65521 D9       EXX              A=208 F=10000011 BC=0     DE=0     HL=0     IX=45678 IY=56789 I=208 R=211
                                            A'=0   F'=00000000 BC'=12345 DE'=23456 HL'=34567 SP=23552
            65522 0198FF   LD BC,65432      A=208 F=10000011 BC=65432 DE=0     HL=0     IX=45678 IY=56789 I=208 R=212
                                            A'=0   F'=00000000 BC'=12345 DE'=23456 HL'=34567 SP=23552
            65525 1131D4   LD DE,54321      A=208 F=10000011 BC=65432 DE=54321 HL=0     IX=45678 IY=56789 I=208 R=213
                                            A'=0   F'=00000000 BC'=12345 DE'=23456 HL'=34567 SP=23552
            65528 21CAA8   LD HL,43210      A=208 F=10000011 BC=65432 DE=54321 HL=43210 IX=45678 IY=56789 I=208 R=214
                                            A'=0   F'=00000000 BC'=12345 DE'=23456 HL'=34567 SP=23552
            65531 08       EX AF,AF'        A=0   F=00000000 BC=65432 DE=54321 HL=43210 IX=45678 IY=56789 I=208 R=215
                                            A'=208 F'=10000011 BC'=12345 DE'=23456 HL'=34567 SP=23552
            65532 90       SUB B            A=1   F=00010011 BC=65432 DE=54321 HL=43210 IX=45678 IY=56789 I=208 R=216
                                            A'=208 F'=10000011 BC'=12345 DE'=23456 HL'=34567 SP=23552
            65533 316D7D   LD SP,32109      A=1   F=00010011 BC=65432 DE=54321 HL=43210 IX=45678 IY=56789 I=208 R=217
                                            A'=208 F'=10000011 BC'=12345 DE'=23456 HL'=34567 SP=32109
            Stopped at 0
        """
        for option in ('-D', '--decimal'):
            output, error = self.run_trace(f'-vv -S 0 {option} {binfile}')
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

    @patch.object(trace, 'write_z80v3', mock_write_z80v3)
    def test_option_dump(self):
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
            0x01, 0x77, 0x7D,       # $801F LD BC,$7D77
            0x31, 0xE9, 0xBE,       # $8022 LD SP,$BEE9
            0xDD, 0x21, 0x72, 0x0D, # $8025 LD IX,$0D72
            0xFD, 0x21, 0x2E, 0x27, # $8029 LD IY,$272E
        ]
        infile = self.write_bin_file(data, suffix='.bin')
        outfile = os.path.join(self.make_directory(), 'dump.z80')
        start = 32768
        stop = start + len(data)
        output, error = self.run_trace(f'-o {start} -S {stop} --dump {outfile} {infile}')
        exp_output = f"""
            Stopped at ${stop:04X}
            Z80 snapshot dumped to {outfile}
        """
        exp_reg = (
            'a=1',
            'f=16',
            'bc=32119',
            'de=5112',
            'hl=0',
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
        exp_state = ('border=1', 'iff=0', 'im=2', 'tstates=166')
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())
        self.assertEqual(z80fname, outfile)
        self.assertEqual(data, snapshot[start:stop])
        self.assertEqual(exp_reg, z80reg)
        self.assertEqual(exp_state, z80state)

    def test_option_interrupts_mode_0(self):
        data = [
            0xED, 0x46, # $8000 IM 0
            0x76,       # $8002 HALT
            0xAF,       # $8003 XOR A
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        start = 0x8000
        stop = 0x8004
        output, error = self.run_trace(f'--interrupts -o {start} -S {stop} -v {binfile}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 ED46     IM 0')
        self.assertEqual(output_lines[1:17471], ['$8002 76       HALT'] * 17470)
        self.assertEqual(output_lines[17471], '$0038 F5       PUSH AF')
        self.assertEqual(output_lines[17579], '$0052 C9       RET')
        self.assertEqual(output_lines[17580], '$8003 AF       XOR A')
        self.assertEqual(output_lines[17581], 'Stopped at $8004')

    def test_option_interrupts_mode_1(self):
        data = [
            0xED, 0x56, # $8000 IM 1
            0x76,       # $8002 HALT
            0xAF,       # $8003 XOR A
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        start = 0x8000
        stop = 0x8004
        output, error = self.run_trace(f'-i -o {start} -S {stop} -v {binfile}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 ED56     IM 1')
        self.assertEqual(output_lines[1:17471], ['$8002 76       HALT'] * 17470)
        self.assertEqual(output_lines[17471], '$0038 F5       PUSH AF')
        self.assertEqual(output_lines[17579], '$0052 C9       RET')
        self.assertEqual(output_lines[17580], '$8003 AF       XOR A')
        self.assertEqual(output_lines[17581], 'Stopped at $8004')

    def test_option_interrupts_mode_2(self):
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
        output, error = self.run_trace(f'--interrupts -S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$7FFB 76       HALT')
        self.assertEqual(output_lines[1], '$7FFB 76       HALT')
        self.assertEqual(output_lines[2], '$7FFE C9       RET')
        self.assertEqual(output_lines[3], '$7FFC AF       XOR A')
        self.assertEqual(output_lines[4], 'Stopped at $7FFD')

    def test_option_interrupts_without_halt(self):
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
        output, error = self.run_trace(f'-i -S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 00       NOP')
        self.assertEqual(output_lines[1], '$8001 00       NOP')
        self.assertEqual(output_lines[2], '$0038 F5       PUSH AF')
        self.assertEqual(output_lines[110], '$0052 C9       RET')
        self.assertEqual(output_lines[111], '$8002 00       NOP')
        self.assertEqual(output_lines[112], 'Stopped at $8003')

    def test_option_interrupts_with_ei(self):
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
        output, error = self.run_trace(f'--interrupts -S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 00       NOP')
        self.assertEqual(output_lines[1], '$8001 FB       EI')
        self.assertEqual(output_lines[2], '$8002 00       NOP')
        self.assertEqual(output_lines[3], '$0038 F5       PUSH AF')
        self.assertEqual(output_lines[111], '$0052 C9       RET')
        self.assertEqual(output_lines[112], '$8003 00       NOP')
        self.assertEqual(output_lines[113], 'Stopped at $8004')

    def test_option_interrupts_with_di(self):
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
        output, error = self.run_trace(f'--interrupts -S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 00       NOP')
        self.assertEqual(output_lines[1], '$8001 F3       DI')
        self.assertEqual(output_lines[2], '$8002 00       NOP')
        self.assertEqual(output_lines[3], '$8003 00       NOP')
        self.assertEqual(output_lines[4], 'Stopped at $8004')

    def test_option_interrupts_with_dd_prefix(self):
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
        output, error = self.run_trace(f'--interrupts -S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 DD       DEFB $DD')
        self.assertEqual(output_lines[1], '$8001 00       NOP')
        self.assertEqual(output_lines[2], '$0038 F5       PUSH AF')
        self.assertEqual(output_lines[102], '$0052 C9       RET')
        self.assertEqual(output_lines[103], '$8002 00       NOP')
        self.assertEqual(output_lines[104], 'Stopped at $8003')

    def test_option_interrupts_with_fd_prefix(self):
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
        output, error = self.run_trace(f'--interrupts -S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 FD       DEFB $FD')
        self.assertEqual(output_lines[1], '$8001 00       NOP')
        self.assertEqual(output_lines[2], '$0038 F5       PUSH AF')
        self.assertEqual(output_lines[102], '$0052 C9       RET')
        self.assertEqual(output_lines[103], '$8002 00       NOP')
        self.assertEqual(output_lines[104], 'Stopped at $8003')

    def test_option_interrupts_with_ddfd_chain(self):
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
        output, error = self.run_trace(f'--interrupts -S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 DD       DEFB $DD')
        self.assertEqual(output_lines[1], '$8001 FD       DEFB $FD')
        self.assertEqual(output_lines[2], '$8002 DD       DEFB $DD')
        self.assertEqual(output_lines[3], '$8003 FD       DEFB $FD')
        self.assertEqual(output_lines[4], '$8004 00       NOP')
        self.assertEqual(output_lines[5], '$0038 F5       PUSH AF')
        self.assertEqual(output_lines[105], '$0052 C9       RET')
        self.assertEqual(output_lines[106], '$8005 00       NOP')
        self.assertEqual(output_lines[107], 'Stopped at $8006')

    def test_option_interrupts_at_exact_frame_boundary(self):
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
        output, error = self.run_trace(f'--interrupts -S {stop} -v {z80file}')
        self.assertEqual(error, '')
        output_lines = output.split('\n')
        self.assertEqual(output_lines[0], '$8000 78       LD A,B')
        self.assertEqual(output_lines[1], '$0038 F5       PUSH AF')
        self.assertEqual(output_lines[109], '$0052 C9       RET')
        self.assertEqual(output_lines[110], '$8001 78       LD A,B')
        self.assertEqual(output_lines[111], 'Stopped at $8002')

    @patch.object(trace, 'write_z80v3', mock_write_z80v3)
    def test_option_interrupts_with_djnz(self):
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
        output, error = self.run_trace(f'--interrupts -S {stop} --dump {outfile} -v {z80file}')
        self.assertEqual(error, '')
        self.assertEqual(snapshot[0xc001], 2) # DJNZ interrupted when B=2

    @patch.object(trace, 'write_z80v3', mock_write_z80v3)
    def test_option_interrupts_with_ldir(self):
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
        output, error = self.run_trace(f'--interrupts -S {stop} --dump {outfile} -v {z80file}')
        self.assertEqual(error, '')
        self.assertEqual(snapshot[0xc000], 2) # LDIR interrupted when BC=2

    @patch.object(trace, 'write_z80v3', mock_write_z80v3)
    def test_option_interrupts_with_lddr(self):
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
        output, error = self.run_trace(f'--interrupts -S {stop} --dump {outfile} -v {z80file}')
        self.assertEqual(error, '')
        self.assertEqual(snapshot[0xc000], 2) # LDDR interrupted when BC=2

    def test_option_max_operations(self):
        data = [
            0xAF, # XOR A
            0x3C, # INC A
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        start = 32768
        output, error = self.run_trace(f'-o {start} -v --max-operations 2 {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 AF       XOR A
            $8001 3C       INC A
            Stopped at $8002: 2 operations
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_max_tstates(self):
        data = [
            0xAF, # XOR A
            0x3C, # INC A
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        start = 32768
        output, error = self.run_trace(f'-o {start} -v --max-tstates 8 {binfile}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 AF       XOR A
            $8001 3C       INC A
            Stopped at $8002: 8 T-states
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

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
            $8000 2100C0   LD HL,$C000      A=00 F=00000000 BC=0000 DE=0000 HL=C000 IX=0000 IY=5C3A IR=3F01
                                            A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00
            $8003 7E       LD A,(HL)        A=01 F=00000000 BC=0000 DE=0000 HL=C000 IX=0000 IY=5C3A IR=3F02
                                            A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00
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
            $8000 3C       INC A            A=51 F=00000001 BC=1234 DE=2345 HL=3456 IX=4567 IY=5678 IR=678A
                                            A'=98 F'=10101010 BC'=8765 DE'=7654 HL'=6543 SP=5432
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
            $8000 C30000   JP $0000
            $0000 AF       XOR A
            Stopped at $0001
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_start(self):
        ram = [0] * 49152
        z80file = self.write_z80_file(None, ram, registers={'PC': 16384})
        for option in ('-s 32768', '--start 0x8000'):
            output, error = self.run_trace(f'-v {option} -S 32769 {z80file}')
            self.assertEqual(error, '')
            exp_output = """
                $8000 00       NOP
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
            output, error = self.run_trace(f'-v -s 56 {option} .')
            self.assertEqual(error, '')
            exp_output = """
                $0038 F5       PUSH AF
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
            $8000 AF       XOR A
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
            $8000 AF       XOR A            A=00 F=01000100 BC=0000 DE=0000 HL=0000 IX=0000 IY=5C3A IR=3F01
                                            A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00
            $8001 3C       INC A            A=01 F=00000000 BC=0000 DE=0000 HL=0000 IX=0000 IY=5C3A IR=3F02
                                            A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00
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
            $8000 0602     LD B,$02
            $8002 10FE     DJNZ $8002
            $8002 10FE     DJNZ $8002
            $8004 2100C0   LD HL,$C000
            $8007 110060   LD DE,$6000
            $800A 0E02     LD C,$02
            $800C EDB0     LDIR
            $800C EDB0     LDIR
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
            $FF00 0602     LD B,$02         A=00 F=00000000 BC=0200 DE=0000 HL=0000 IX=0000 IY=5C3A IR=3F01
                                            A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00
            $FF02 10FE     DJNZ $FF02       A=00 F=00000000 BC=0100 DE=0000 HL=0000 IX=0000 IY=5C3A IR=3F02
                                            A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00
            $FF02 10FE     DJNZ $FF02       A=00 F=00000000 BC=0000 DE=0000 HL=0000 IX=0000 IY=5C3A IR=3F03
                                            A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00
            $FF04 2100C0   LD HL,$C000      A=00 F=00000000 BC=0000 DE=0000 HL=C000 IX=0000 IY=5C3A IR=3F04
                                            A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00
            $FF07 110060   LD DE,$6000      A=00 F=00000000 BC=0000 DE=6000 HL=C000 IX=0000 IY=5C3A IR=3F05
                                            A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00
            $FF0A 0E02     LD C,$02         A=00 F=00000000 BC=0002 DE=6000 HL=C000 IX=0000 IY=5C3A IR=3F06
                                            A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00
            $FF0C EDB0     LDIR             A=00 F=00101100 BC=0001 DE=6001 HL=C001 IX=0000 IY=5C3A IR=3F08
                                            A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00
            $FF0C EDB0     LDIR             A=00 F=00000000 BC=0000 DE=6002 HL=C002 IX=0000 IY=5C3A IR=3F0A
                                            A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00
            Stopped at $FF0E
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_trace(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))

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
            $8000 0602     LD B,$02
            $8002 210380   LD HL,$8003
            $8005 70       LD (HL),B
            $8006 10FA     DJNZ $8002
            $8002 210280   LD HL,$8002
            $8005 70       LD (HL),B
            $8006 10FA     DJNZ $8002
            Stopped at $8008
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_invalid_register_value(self):
        binfile = self.write_bin_file([201], suffix='.bin')
        addr = 32768
        with self.assertRaises(SkoolKitError) as cm:
            self.run_trace(f'-o {addr} --reg A=x {binfile}')
        self.assertEqual(cm.exception.args[0], 'Cannot parse register value: A=x')
