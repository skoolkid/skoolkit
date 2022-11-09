import os
from textwrap import dedent
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import trace, SkoolKitError, VERSION

def mock_run(*args):
    global run_args
    run_args = args

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
            'PC': 32768
        }
        ram = [0] * 49152
        z80file = self.write_z80_file(None, ram, registers=registers)
        exp_output = """
            $8000 00       NOP              A=01 F=00000010 BC=0304 DE=0506 HL=0708 IX=0B0C IY=090A IR=0D0F
                                            A'=0F F'=00010000 BC'=1112 DE'=1314 HL'=1516 SP=FFFF
            Stopped at $8001
        """
        self._test_trace(f'-vv -S 32769 {z80file}', exp_output)

    def test_szx(self):
        registers = (
            1, 2,   # AF
            3, 4,   # BC
            5, 6,   # DE
            7, 8,   # HL
            9, 10,  # AF'
            11, 12, # BC'
            13, 14, # DE'
            15, 16, # HL'
            17, 18, # IX
            19, 20, # IY
            0, 128, # SP=32768
            0, 192, # PC=49152
            21,     # I
            22      # R

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

    def test_option_dump(self):
        data = [
            50, 0, 128, # LD (32768),A
        ]
        infile = self.write_bin_file(data, suffix='.bin')
        outfile = os.path.join(self.make_directory(), 'dump.bin')
        start, stop = 32768, 32771
        output, error = self.run_trace(f'-o {start} -S {stop} --dump {outfile} {infile}')
        exp_output = f"""
            Stopped at $8003
            Snapshot dumped to {outfile}
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())
        with open(outfile, 'rb') as f:
            dump = list(f.read())
        self.assertEqual([0, 0, 128], dump[16384:16387])

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

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_trace(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))

    def test_invalid_register_value(self):
        binfile = self.write_bin_file([201], suffix='.bin')
        addr = 32768
        with self.assertRaises(SkoolKitError) as cm:
            self.run_trace(f'-o {addr} --reg A=x {binfile}')
        self.assertEqual(cm.exception.args[0], 'Cannot parse register value: A=x')
