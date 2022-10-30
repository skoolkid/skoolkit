import os
from textwrap import dedent
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import trace, SkoolKitError, VERSION

def mock_run(*args):
    global run_args
    run_args = args

class TraceTest(SkoolKitTestCase):
    @patch.object(trace, 'run', mock_run)
    def test_default_option_values(self):
        trace.main(('test.z80', '24576'))
        z80file, start, options = run_args
        self.assertEqual(z80file, 'test.z80')
        self.assertEqual(start, 24576)
        self.assertFalse(options.audio)
        self.assertEqual(options.depth, 2)
        self.assertIsNone(options.dump)
        self.assertEqual(options.end, -1)
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

    def test_option_audio(self):
        data = [
            6, 3,     # 32768 LD B,3
            211, 254, # 32770 OUT (254),A
            238, 16,  # 32772 XOR 16
            16, 250,  # 32774 DJNZ 32770
            201       # 32776 RET
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        addr = 32768
        output, error = self.run_trace(f'-o {addr} --audio {binfile} {addr}')
        self.assertEqual(error, '')
        exp_output = """
            Stopped at $0000: PUSH-POP count is -1
            Sound duration: 62 T-states (0.000s)
            Delays: [31]*2
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_dump(self):
        data = [
            50, 0, 128, # LD (32768),A
            201         # RET
        ]
        infile = self.write_bin_file(data, suffix='.bin')
        outfile = os.path.join(self.make_directory(), 'dump.bin')
        addr = 32768
        output, error = self.run_trace(f'-o {addr} --dump {outfile} {infile} {addr}')
        exp_output = f"""
            Stopped at $0000: PUSH-POP count is -1
            Snapshot dumped to {outfile}
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())
        with open(outfile, 'rb') as f:
            dump = list(f.read())
        self.assertEqual([0, 0, 128, 201], dump[16384:16388])

    def test_option_end(self):
        data = [
            0xAF, # XOR A
            0x3C, # INC A
            0xC9  # RET
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        addr = 32768
        output, error = self.run_trace(f'-o {addr} -v --end 32770 {binfile} {addr}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 AF       XOR A
            $8001 3C       INC A
            Stopped at $8002
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_max_operations(self):
        data = [
            0xAF, # XOR A
            0x3C, # INC A
            0xC9  # RET
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        addr = 32768
        output, error = self.run_trace(f'-o {addr} -v --max-operations 2 {binfile} {addr}')
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
            0xC9  # RET
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        addr = 32768
        output, error = self.run_trace(f'-o {addr} -v --max-tstates 8 {binfile} {addr}')
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
        addr = 32768
        output, error = self.run_trace(f'-o {addr} -vv -e 0x8004 --poke 49152,1 {binfile} {addr}')
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
        addr = 32768
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
        output, error = self.run_trace(f'-o {addr} -vv -e 0x8001 {reg_options} {binfile} {addr}')
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
        addr = 32768
        output, error = self.run_trace(f'-o {addr} --rom {romfile} -e 1 -v {binfile} {addr}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 C30000   JP $0000
            $0000 AF       XOR A
            Stopped at $0001
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_stats(self):
        data = [
            175, # XOR A
            60,  # INC A
            201  # RET
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        addr = 32768
        output, error = self.run_trace(f'-o {addr} --stats {binfile} {addr}')
        self.assertEqual(error, '')
        o_lines = output.split('\n')
        self.assertEqual(o_lines[0], 'Stopped at $0000: PUSH-POP count is -1')
        self.assertEqual(o_lines[1], 'Z80 execution time: 18 T-states (0.000s)')
        self.assertEqual(o_lines[2], 'Instructions executed: 3')
        self.assertEqual(o_lines[3][:17], 'Simulation time: ')

    def test_option_verbose(self):
        data = [
            0xAF, # XOR A
            0xC9  # RET
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        addr = 32768
        output, error = self.run_trace(f'-o {addr} --verbose {binfile} {addr}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 AF       XOR A
            $8001 C9       RET
            Stopped at $0000: PUSH-POP count is -1
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_vv(self):
        data = [
            0xAF, # XOR A
            0xC9  # RET
        ]
        binfile = self.write_bin_file(data, suffix='.bin')
        addr = 32768
        output, error = self.run_trace(f'-o {addr} -vv {binfile} {addr}')
        self.assertEqual(error, '')
        exp_output = """
            $8000 AF       XOR A            A=00 F=01000100 BC=0000 DE=0000 HL=0000 IX=0000 IY=5C3A IR=3F01
                                            A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C00
            $8001 C9       RET              A=00 F=01000100 BC=0000 DE=0000 HL=0000 IX=0000 IY=5C3A IR=3F02
                                            A'=00 F'=00000000 BC'=0000 DE'=0000 HL'=0000 SP=5C02
            Stopped at $0000: PUSH-POP count is -1
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
            self.run_trace(f'-o {addr} --reg A=x {binfile} {addr}')
        self.assertEqual(cm.exception.args[0], 'Cannot parse register value: A=x')
