import hashlib
import os
from textwrap import dedent
import urllib
from zipfile import ZipFile
from io import BytesIO
from unittest.mock import patch, Mock

from skoolkittest import (SkoolKitTestCase, Z80_REGISTERS, create_data_block,
                          create_tap_header_block, create_tap_data_block,
                          create_tzx_header_block, create_tzx_data_block,
                          create_tzx_turbo_data_block, create_tzx_pure_data_block)
from skoolkit import tap2sna, VERSION, SkoolKitError
from skoolkit.config import COMMANDS
from skoolkit.snapshot import get_snapshot

def mock_make_z80(*args):
    global make_z80_args
    make_z80_args = args

def mock_config(name):
    return {k: v[0] for k, v in COMMANDS[name].items()}

def mock_write_z80(ram, namespace, z80):
    global snapshot, options
    snapshot = [0] * 16384 + ram
    options = namespace

class Tap2SnaTest(SkoolKitTestCase):
    def _write_tap(self, blocks, zip_archive=False, tap_name=None):
        tap_data = []
        for block in blocks:
            tap_data.extend(block)
        if zip_archive:
            archive_fname = self.write_bin_file(suffix='.zip')
            with ZipFile(archive_fname, 'w') as archive:
                archive.writestr(tap_name or 'game.tap', bytearray(tap_data))
            return archive_fname
        return self.write_bin_file(tap_data, suffix='.tap')

    def _write_tzx(self, blocks):
        tzx_data = [ord(c) for c in "ZXTape!"]
        tzx_data.extend((26, 1, 20))
        for block in blocks:
            tzx_data.extend(block)
        return self.write_bin_file(tzx_data, suffix='.tzx')

    def _write_basic_loader(self, start, data, write=True, program='simloadbas', code='simloadbyt'):
        start_str = [ord(c) for c in str(start)]
        basic_data = [
            0, 10,            # Line 10
            16, 0,            # Line length
            239, 34, 34, 175, # LOAD ""CODE
            58,               # :
            249, 192, 176,    # RANDOMIZE USR VAL
            34,               # "
            *start_str,       # start address
            34,               # "
            13                # ENTER
        ]
        blocks = [
            create_tap_header_block(program, 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block(code, start, len(data)),
            create_tap_data_block(data)
        ]
        if write:
            return self._write_tap(blocks), basic_data
        return blocks, basic_data

    def _get_snapshot(self, start=16384, data=None, options='', load_options=None, blocks=None, tzx=False):
        if blocks is None:
            blocks = [create_tap_data_block(data)]
        if tzx:
            tape_file = self._write_tzx(blocks)
        else:
            tape_file = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        if load_options is None:
            load_options = '--ram load=1,{}'.format(start)
        output, error = self.run_tap2sna(f'{load_options} {options} {tape_file} {z80file}')
        self.assertEqual(output, 'Writing {}\n'.format(z80file))
        self.assertEqual(error, '')
        return get_snapshot(z80file)

    def _test_bad_spec(self, option, exp_error):
        odir = self.make_directory()
        tapfile = self._write_tap([create_tap_data_block([1])])
        z80fname = 'test.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna('--ram load=1,16384 {} -d {} {} {}'.format(option, odir, tapfile, z80fname))
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot {}: {}'.format(z80fname, exp_error))

    @patch.object(tap2sna, 'make_z80', mock_make_z80)
    def test_default_option_values(self):
        self.run_tap2sna('in.tap {}/out.z80'.format(self.make_directory()))
        options = make_z80_args[1]
        self.assertIsNone(options.output_dir)
        self.assertFalse(options.force)
        self.assertIsNone(options.stack)
        self.assertEqual([], options.ram_ops)
        self.assertEqual([], options.reg)
        self.assertIsNone(options.start)
        self.assertFalse(options.sim_load)
        self.assertEqual([], options.sim_load_config)
        self.assertEqual([], options.state)
        self.assertIsNone(options.tape_name)
        self.assertEqual(options.tape_start, 1)
        self.assertEqual(options.tape_stop, 0)
        self.assertIsNone(options.tape_sum)
        self.assertEqual(options.user_agent, '')
        self.assertEqual([], options.params)

    @patch.object(tap2sna, 'make_z80', mock_make_z80)
    def test_config_read_from_file(self):
        ini = """
            [tap2sna]
            TraceLine={pc} - {i}
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        self.run_tap2sna('in.tap out.z80')
        options, z80, config = make_z80_args[1:4]
        self.assertIsNone(options.output_dir)
        self.assertFalse(options.force)
        self.assertIsNone(options.stack)
        self.assertEqual([], options.ram_ops)
        self.assertEqual([], options.reg)
        self.assertIsNone(options.start)
        self.assertFalse(options.sim_load)
        self.assertEqual([], options.sim_load_config)
        self.assertEqual([], options.state)
        self.assertIsNone(options.tape_name)
        self.assertEqual(options.tape_start, 1)
        self.assertEqual(options.tape_stop, 0)
        self.assertIsNone(options.tape_sum)
        self.assertEqual(options.user_agent, '')
        self.assertEqual([], options.params)
        self.assertEqual(config['TraceLine'], '{pc} - {i}')

    def test_no_arguments(self):
        output, error = self.run_tap2sna(catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage:'))

    def test_one_argument(self):
        output, error = self.run_tap2sna('in.tap', catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage:'))

    def test_invalid_arguments(self):
        for args in ('--foo', '-k test.zip'):
            output, error = self.run_tap2sna(args, catch_exit=2)
            self.assertEqual(output, '')
            self.assertTrue(error.startswith('usage:'))

    def test_accelerator_unrecognised(self):
        blocks = [create_tap_data_block([0])]
        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'-c accelerator=nope --sim-load {tapfile} {z80file}')
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot out.z80: Unrecognised accelerator: nope')
        self.assertEqual(self.err.getvalue(), '')

    def test_unrecognised_sim_load_configuration_parameter(self):
        blocks = [create_tap_data_block([0])]
        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'-c foo=bar --sim-load {tapfile} {z80file}')
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot out.z80: Invalid sim-load configuration parameter: foo')
        self.assertEqual(self.err.getvalue(), '')

    def test_option_d(self):
        odir = '{}/tap2sna'.format(self.make_directory())
        tapfile = self._write_tap((
            create_tap_header_block(start=16384),
            create_tap_data_block([0])
        ))
        z80_fname = 'test.z80'
        for option in ('-d', '--output-dir'):
            output, error = self.run_tap2sna('{} {} {} {}'.format(option, odir, tapfile, z80_fname))
            self.assertEqual(len(error), 0)
            self.assertTrue(os.path.isfile(os.path.join(odir, z80_fname)))

    def test_option_f(self):
        z80file = self.write_bin_file(suffix='.z80')
        for option, b in (('-f', 1), ('--force', 255)):
            tapfile = self._write_tap((
                create_tap_header_block(start=16384),
                create_tap_data_block([b])
            ))
            output, error = self.run_tap2sna(f'{option} {tapfile} {z80file}')
            self.assertEqual(len(error), 0)
            snapshot = get_snapshot(z80file)
            self.assertEqual(snapshot[16384], b)

    @patch.object(tap2sna, 'make_z80', mock_make_z80)
    @patch.object(tap2sna, 'get_config', mock_config)
    def test_option_I(self):
        self.run_tap2sna('-I TraceLine=Hello in.tap out.z80')
        options, z80, config = make_z80_args[1:4]
        self.assertEqual(['TraceLine=Hello'], options.params)
        self.assertEqual(config['TraceLine'], 'Hello')

    @patch.object(tap2sna, 'make_z80', mock_make_z80)
    def test_option_I_overrides_config_read_from_file(self):
        ini = """
            [tap2sna]
            TraceLine=0x{pc:04x} {i}
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        self.run_tap2sna('--ini TraceLine=Goodbye in.tap out.z80')
        options, z80, config = make_z80_args[1:4]
        self.assertEqual(['TraceLine=Goodbye'], options.params)
        self.assertEqual(config['TraceLine'], 'Goodbye')

    @patch.object(tap2sna, 'make_z80', mock_make_z80)
    def test_options_p_stack(self):
        for option, stack in (('-p', 24576), ('--stack', 49152)):
            output, error = self.run_tap2sna('{} {} in.tap {}/out.z80'.format(option, stack, self.make_directory()))
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            options = make_z80_args[1]
            self.assertEqual(['sp={}'.format(stack)], options.reg)

    @patch.object(tap2sna, 'make_z80', mock_make_z80)
    def test_options_p_stack_with_hex_address(self):
        for option, stack in (('-p', '0x6ff0'), ('--stack', '0x9ABC')):
            output, error = self.run_tap2sna('{} {} in.tap {}/out.z80'.format(option, stack, self.make_directory()))
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            options = make_z80_args[1]
            self.assertEqual(['sp={}'.format(int(stack[2:], 16))], options.reg)

    def test_option_p(self):
        tapfile = self._write_tap((
            create_tap_header_block(start=16384),
            create_tap_data_block([0])
        ))
        z80file = '{}/out.z80'.format(self.make_directory())
        stack = 32768
        output, error = self.run_tap2sna(f'-p {stack} {tapfile} {z80file}')
        self.assertEqual(error, '')
        with open(z80file, 'rb') as f:
            z80_header = f.read(10)
        self.assertEqual(z80_header[8] + 256 * z80_header[9], stack)

    @patch.object(tap2sna, 'get_config', mock_config)
    def test_option_show_config(self):
        output, error = self.run_tap2sna('--show-config', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = r"""
            [tap2sna]
            TraceLine=${pc:04X} {i}
            TraceOperand=$,02X,04X
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_show_config_read_from_file(self):
        ini = """
            [tap2sna]
            TraceLine={pc:05} {i}
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        output, error = self.run_tap2sna('--show-config', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            [tap2sna]
            TraceLine={pc:05} {i}
            TraceOperand=$,02X,04X
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    @patch.object(tap2sna, 'make_z80', mock_make_z80)
    def test_options_s_start(self):
        start = 30000
        exp_reg = ['pc={}'.format(start)]
        for option in ('-s', '--start'):
            output, error = self.run_tap2sna('{} {} in.tap {}/out.z80'.format(option, start, self.make_directory()))
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            options = make_z80_args[1]
            self.assertEqual(exp_reg, options.reg)

    @patch.object(tap2sna, 'make_z80', mock_make_z80)
    def test_options_s_start_with_hex_address(self):
        start = 30000
        exp_reg = ['pc={}'.format(start)]
        for option in ('-s', '--start'):
            output, error = self.run_tap2sna('{} 0x{:04X} in.tap {}/out.z80'.format(option, start, self.make_directory()))
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            options = make_z80_args[1]
            self.assertEqual(exp_reg, options.reg)

    def test_option_s(self):
        tapfile = self._write_tap((
            create_tap_header_block(start=16384),
            create_tap_data_block([0])
        ))
        z80file = '{}/out.z80'.format(self.make_directory())
        start = 40000
        output, error = self.run_tap2sna(f'-s {start} {tapfile} {z80file}')
        self.assertEqual(error, '')
        with open(z80file, 'rb') as f:
            z80_header = f.read(34)
        self.assertEqual(z80_header[32] + 256 * z80_header[33], start)

    def test_option_tape_analysis_with_no_tape(self):
        output, error = self.run_tap2sna('--tape-analysis', catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage:'))

    def test_option_tape_analysis_with_tape_and_snapshot(self):
        output, error = self.run_tap2sna('--tape-analysis in.tap out.z80', catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage:'))

    def test_option_tape_analysis(self):
        blocks = [
            create_tap_header_block(start=0),
            create_tap_data_block([4, 5, 6]),
        ]
        tapfile = self._write_tap(blocks)
        output, error = self.run_tap2sna(f'--tape-analysis {tapfile}', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            T-states    Description
                 -2168  Tone (8063 x 2168 T-states)
              17478416  Pulse (667 T-states)
              17479083  Pulse (735 T-states)
              17479818  Data (19 bytes; 855/1710 T-states)
              17763678  Pause (3500000 T-states)
              21263678  Tone (3223 x 2168 T-states)
              28251142  Pulse (667 T-states)
              28251809  Pulse (735 T-states)
              28252544  Data (5 bytes; 855/1710 T-states)
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_analysis_with_tape_start(self):
        blocks = [
            create_tap_header_block(start=0),
            create_tap_data_block([4, 5, 6]),
        ]
        tapfile = self._write_tap(blocks)
        output, error = self.run_tap2sna(f'--tape-analysis --tape-start 2 {tapfile}', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            T-states    Description
                 -2168  Tone (3223 x 2168 T-states)
               6985296  Pulse (667 T-states)
               6985963  Pulse (735 T-states)
               6986698  Data (5 bytes; 855/1710 T-states)
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_analysis_with_tape_stop(self):
        blocks = [
            create_tap_header_block(start=0),
            create_tap_data_block([4, 5, 6]),
        ]
        tapfile = self._write_tap(blocks)
        output, error = self.run_tap2sna(f'--tape-analysis --tape-stop 2 {tapfile}', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            T-states    Description
                 -2168  Tone (8063 x 2168 T-states)
              17478416  Pulse (667 T-states)
              17479083  Pulse (735 T-states)
              17479818  Data (19 bytes; 855/1710 T-states)
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_analysis_with_first_edge(self):
        blocks = [
            create_tap_header_block(start=0),
            create_tap_data_block([4, 5, 6]),
        ]
        tapfile = self._write_tap(blocks)
        output, error = self.run_tap2sna(f'--tape-analysis -c first-edge=0 {tapfile}', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            T-states    Description
                     0  Tone (8063 x 2168 T-states)
              17480584  Pulse (667 T-states)
              17481251  Pulse (735 T-states)
              17481986  Data (19 bytes; 855/1710 T-states)
              17765846  Pause (3500000 T-states)
              21265846  Tone (3223 x 2168 T-states)
              28253310  Pulse (667 T-states)
              28253977  Pulse (735 T-states)
              28254712  Data (5 bytes; 855/1710 T-states)
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_analysis_with_unused_bits_in_last_byte(self):
        code = [1, 2, 3, 4]
        blocks = [create_tzx_turbo_data_block(code, used_bits=4)]
        tapfile = self._write_tzx(blocks)
        output, error = self.run_tap2sna(f'--tape-analysis {tapfile}', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            T-states    Description
                 -2168  Tone (3223 x 2168 T-states)
               6985296  Pulse (667 T-states)
               6985963  Pulse (735 T-states)
               6986698  Data (5 bytes + 4 bits; 855/1710 T-states)
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_analysis_with_pure_tone_and_pause_and_pulse_sequence_and_pure_data(self):
        blocks = []
        blocks.append((18, 76, 4, 208, 7)) # 0x12 Pure Tone
        blocks.append((32, 1, 0))          # 0x20 Pause
        blocks.append((19, 2, 0, 1, 0, 2)) # 0x13 Pulse sequence
        blocks.append(create_tzx_pure_data_block((1, 2, 3, 4), 500, 1000))
        tapfile = self._write_tzx(blocks)
        output, error = self.run_tap2sna(f'--tape-analysis {tapfile}', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            T-states    Description
                 -2168  Tone (2000 x 1100 T-states)
               2197832  Pause (3500 T-states)
               2201332  Pulse (256 T-states)
               2201588  Pulse (512 T-states)
               2202100  Data (4 bytes; 500/1000 T-states)
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_option_tape_name(self):
        code1 = [1, 2, 3, 4, 5]
        code1_start = 24576
        tap1_data = create_tap_header_block(start=code1_start) + create_tap_data_block(code1)
        tap1_fname = 'code1.tap'
        code2 = [6, 7, 8]
        code2_start = 32768
        tap2_data = create_tap_header_block(start=code2_start) + create_tap_data_block(code2)
        tap2_fname = 'code2.tap'
        zipfile = '{}/tapes.zip'.format(self.make_directory())
        with ZipFile(zipfile, 'w') as archive:
            archive.writestr(tap1_fname, bytearray(tap1_data))
            archive.writestr(tap2_fname, bytearray(tap2_data))
        output, error = self.run_tap2sna(f'--tape-name {tap2_fname} {zipfile} out.z80')
        self.assertEqual(error, '')
        self.assertEqual([0] * len(code1), snapshot[code1_start:code1_start + len(code1)])
        self.assertEqual(code2, snapshot[code2_start:code2_start + len(code2)])

    def test_option_tape_name_with_invalid_name(self):
        tap_data = create_tap_header_block(start=32768) + create_tap_data_block([1, 2, 3])
        zipfile = '{}/tape.zip'.format(self.make_directory())
        with ZipFile(zipfile, 'w') as archive:
            archive.writestr('data.tap', bytearray(tap_data))
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'--tape-name code.tap {zipfile} out.z80')
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot out.z80: No file named "code.tap" in the archive')
        self.assertEqual(self.err.getvalue(), '')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_option_tape_start_with_tap_file(self):
        code1_start = 24576
        code2_start = 32768
        code = [4, 5, 6]
        blocks = [
            create_tap_header_block(start=code1_start),
            create_tap_data_block(code),
            create_tap_header_block(start=code2_start),
            create_tap_data_block(code)
        ]
        tapfile = self._write_tap(blocks)
        output, error = self.run_tap2sna(f'--tape-start 3 {tapfile} out.z80')
        self.assertEqual(error, '')
        self.assertEqual([0] * len(code), snapshot[code1_start:code1_start + len(code)])
        self.assertEqual(code, snapshot[code2_start:code2_start + len(code)])

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_option_tape_start_with_tzx_file(self):
        code1_start = 24576
        code2_start = 32768
        code = [4, 5, 6]
        blocks = [
            create_tzx_header_block(start=code1_start),
            create_tzx_data_block(code),
            create_tzx_header_block(start=code2_start),
            create_tzx_data_block(code)
        ]
        tzxfile = self._write_tzx(blocks)
        output, error = self.run_tap2sna(f'--tape-start 3 {tzxfile} out.z80')
        self.assertEqual(error, '')
        self.assertEqual([0] * len(code), snapshot[code1_start:code1_start + len(code)])
        self.assertEqual(code, snapshot[code2_start:code2_start + len(code)])

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_option_tape_stop_with_tap_file(self):
        code1_start = 24576
        code2_start = 32768
        code = [4, 5, 6]
        blocks = [
            create_tap_header_block(start=code1_start),
            create_tap_data_block(code),
            create_tap_header_block(start=code2_start),
            create_tap_data_block(code)
        ]
        tapfile = self._write_tap(blocks)
        output, error = self.run_tap2sna(f'--tape-stop 3 {tapfile} out.z80')
        self.assertEqual(error, '')
        self.assertEqual(code, snapshot[code1_start:code1_start + len(code)])
        self.assertEqual([0] * len(code), snapshot[code2_start:code2_start + len(code)])

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_option_tape_stop_with_tzx_file(self):
        code1_start = 24576
        code2_start = 32768
        code = [4, 5, 6]
        blocks = [
            create_tzx_header_block(start=code1_start),
            create_tzx_data_block(code),
            create_tzx_header_block(start=code2_start),
            create_tzx_data_block(code)
        ]
        tzxfile = self._write_tzx(blocks)
        output, error = self.run_tap2sna(f'--tape-stop 3 {tzxfile} out.z80')
        self.assertEqual(error, '')
        self.assertEqual(code, snapshot[code1_start:code1_start + len(code)])
        self.assertEqual([0] * len(code), snapshot[code2_start:code2_start + len(code)])

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_option_tape_sum(self):
        code = [1, 2, 3]
        code_start = 49152
        tap_data = create_tap_header_block(start=code_start) + create_tap_data_block(code)
        md5sum = hashlib.md5(bytearray(tap_data)).hexdigest()
        zipfile = '{}/tape.zip'.format(self.make_directory())
        with ZipFile(zipfile, 'w') as archive:
            archive.writestr('data.tap', bytearray(tap_data))
        output, error = self.run_tap2sna(f'--tape-sum {md5sum} {zipfile} out.z80')
        self.assertEqual(error, '')
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])

    def test_option_tape_sum_with_incorrect_value(self):
        code = [1, 2, 3]
        code_start = 49152
        tap_data = create_tap_header_block(start=code_start) + create_tap_data_block(code)
        md5sum = hashlib.md5(bytearray(tap_data)).hexdigest()
        zipfile = '{}/tape.zip'.format(self.make_directory())
        wrongsum = '0' * 32
        with ZipFile(zipfile, 'w') as archive:
            archive.writestr('data.tap', bytearray(tap_data))
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'--tape-sum {wrongsum} {zipfile} out.z80')
        self.assertEqual(cm.exception.args[0], f'Error while getting snapshot out.z80: Checksum mismatch: Expected {wrongsum}, actually {md5sum}')
        self.assertEqual(self.err.getvalue(), '')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    @patch.object(tap2sna, 'urlopen')
    def test_option_u(self, mock_urlopen):
        mock_urlopen.return_value = BytesIO(bytes(create_tap_data_block([1])))
        url = 'http://example.com/test.tap'
        for option, user_agent in (('-u', 'Wget/1.18'), ('--user-agent', 'SkoolKit/6.3')):
            output, error = self.run_tap2sna('{} {} --ram load=1,23296 {} {}/test.z80'.format(option, user_agent, url, self.make_directory()))
            self.assertTrue(output.startswith('Downloading {}\n'.format(url)))
            self.assertEqual(error, '')
            request = mock_urlopen.call_args[0][0]
            self.assertEqual({'User-agent': user_agent}, request.headers)
            self.assertEqual(snapshot[23296], 1)
            mock_urlopen.return_value.seek(0)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_tap2sna(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))

    def test_nonexistent_tap_file(self):
        odir = self.make_directory()
        tap_fname = '{}/test.tap'.format(odir)
        z80_fname = 'test.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna('{} {}/{}'.format(tap_fname, odir, z80_fname))
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot {}: {}: file not found'.format(z80_fname, tap_fname))

    def test_load_nonexistent_block(self):
        tapfile = self._write_tap([create_tap_data_block([1])])
        block_num = 2
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna('--ram load={},16384 {} {}/test.z80'.format(block_num, tapfile, self.make_directory()))
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot test.z80: Block {} not found'.format(block_num))

    def test_zip_archive_with_no_tape_file(self):
        archive_fname = self.write_bin_file(suffix='.zip')
        with ZipFile(archive_fname, 'w') as archive:
            archive.writestr('game.txt', bytearray((1, 2)))
        z80_fname = 'test.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna('{} {}/{}'.format(archive_fname, self.make_directory(), z80_fname))
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot {}: No TAP or TZX file found'.format(z80_fname))

    def test_standard_load_from_tap_file(self):
        basic_data = [1, 2, 3]
        code_start = 32768
        code = [4, 5]
        blocks = [
            create_tap_header_block(data_type=0),
            create_tap_data_block(basic_data),
            create_tap_header_block(start=code_start),
            create_tap_data_block(code)
        ]

        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'{tapfile} {z80file}')
        self.assertEqual(error, '')
        snapshot = get_snapshot(z80file)
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])

    def test_standard_load_ignores_headerless_block(self):
        code_start = 16384
        code = [2]
        blocks = [
            create_tap_header_block(start=code_start),
            create_tap_data_block(code),
            create_tap_data_block([23]),
            create_tap_data_block([97])
        ]

        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'{tapfile} {z80file}')
        self.assertEqual(
            error,
            'WARNING: Ignoring headerless block 3\n'
            'WARNING: Ignoring headerless block 4\n'
        )
        snapshot = get_snapshot(z80file)
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])

    def test_standard_load_ignores_truncated_header_block(self):
        code_start = 30000
        code = [2, 3, 4]
        length = len(code)
        blocks = [
            create_tap_header_block(start=code_start)[:-1],
            create_tap_data_block(code),
        ]

        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'{tapfile} {z80file}')
        self.assertEqual(error, '')
        snapshot = get_snapshot(z80file)
        self.assertEqual([0] * length, snapshot[code_start:code_start + length])

    def test_standard_load_with_unknown_block_type(self):
        block_type = 1 # Array of numbers
        blocks = [
            create_tap_header_block(data_type=block_type),
            create_tap_data_block([1])
        ]

        tapfile = self._write_tap(blocks)
        z80file = 'out.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna('{} {}'.format(tapfile, z80file))
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot {}: Unknown block type ({}) in header block 1'.format(z80file, block_type))

    def test_standard_load_from_tzx_file(self):
        basic_data = [6, 7]
        code_start = 49152
        code = [8, 9, 10]
        blocks = [
            [48, 3, 65, 66, 67], # Text description block (0x30): ABC
            create_tzx_header_block(data_type=0),
            create_tzx_data_block(basic_data),
            create_tzx_header_block(start=code_start),
            create_tzx_data_block(code)
        ]

        tzxfile = self._write_tzx(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'{tzxfile} {z80file}')
        self.assertEqual(error, '')
        snapshot = get_snapshot(z80file)
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])

    def test_empty_standard_speed_data_block_in_tzx_file_is_ignored(self):
        basic_data = [6, 7]
        code_start = 49152
        code = [8, 9, 10]
        empty_block = [
            16,   # Standard speed data
            0, 0, # Pause (0ms)
            0, 0, # Data length (0)
        ]
        blocks = [
            create_tzx_header_block(data_type=0),
            create_tzx_data_block(basic_data),
            empty_block,
            create_tzx_header_block(start=code_start),
            create_tzx_data_block(code)
        ]

        tzxfile = self._write_tzx(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'{tzxfile} {z80file}')
        self.assertEqual(error, '')
        snapshot = get_snapshot(z80file)
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])

    def test_ram_call(self):
        ram_module = """
            def fix(snapshot):
                snapshot[65280:] = list(range(256))
        """
        module_dir = self.make_directory()
        module_path = os.path.join(module_dir, 'ram.py')
        module = self.write_text_file(dedent(ram_module).strip(), path=module_path)
        blocks = [
            create_tap_header_block(start=16384),
            create_tap_data_block([0])
        ]
        snapshot = self._get_snapshot(load_options=f'--ram call={module_dir}:ram.fix', blocks=blocks)
        self.assertEqual(list(range(256)), snapshot[65280:])

    def test_ram_call_nonexistent_module(self):
        self._test_bad_spec('--ram call=no:nope.never', "Failed to import object nope.never: No module named 'nope'")

    def test_ram_call_nonexistent_function(self):
        module_dir = self.make_directory()
        module_path = os.path.join(module_dir, 'ram.py')
        module = self.write_text_file(path=module_path)
        self._test_bad_spec(f'--ram call={module_dir}:ram.never', "No object named 'never' in module 'ram'")

    def test_ram_call_uncallable(self):
        ram_module = "fix = None"
        module_dir = self.make_directory()
        module_path = os.path.join(module_dir, 'uncallable.py')
        module = self.write_text_file(ram_module, path=module_path)
        self._test_bad_spec(f'--ram call={module_dir}:uncallable.fix', "'NoneType' object is not callable")

    def test_ram_call_function_with_no_arguments(self):
        ram_module = "def fix(): pass"
        module_dir = self.make_directory()
        module_path = os.path.join(module_dir, 'noargs.py')
        module = self.write_text_file(ram_module, path=module_path)
        self._test_bad_spec(f'--ram call={module_dir}:noargs.fix', "fix() takes 0 positional arguments but 1 was given")

    def test_ram_call_function_with_two_positional_arguments(self):
        ram_module = "def fix(snapshot, what): pass"
        module_dir = self.make_directory()
        module_path = os.path.join(module_dir, 'twoargs.py')
        module = self.write_text_file(ram_module, path=module_path)
        self._test_bad_spec(f'--ram call={module_dir}:twoargs.fix', "fix() missing 1 required positional argument: 'what'")

    def test_ram_load(self):
        start = 16384
        data = [237, 1, 1, 1, 1, 1]
        snapshot = self._get_snapshot(start, data)
        self.assertEqual(data, snapshot[start:start + len(data)])

    def test_ram_load_with_length(self):
        start = 16384
        data = [1, 2, 3, 4]
        length = 2
        snapshot = self._get_snapshot(start, data, load_options='--ram load=1,{},{}'.format(start, length))
        self.assertEqual(data[:length], snapshot[start:start + length])
        self.assertEqual([0] * (len(data) - length), snapshot[start + length:start + len(data)])

    def test_ram_load_with_step(self):
        start = 16385
        data = [5, 4, 3]
        step = 2
        snapshot = self._get_snapshot(start, data, load_options='--ram load=1,{},,{}'.format(start, step))
        self.assertEqual(data, snapshot[start:start + len(data) * step:step])

    def test_ram_load_with_offset(self):
        start = 16384
        data = [15, 16, 17]
        offset = 5
        snapshot = self._get_snapshot(start, data, load_options='--ram load=1,{},,,{}'.format(start, offset))
        self.assertEqual(data, snapshot[start + offset:start + offset + len(data)])

    def test_ram_load_with_increment(self):
        start = 65534
        data = [8, 9, 10]
        inc = 65533
        snapshot = self._get_snapshot(start, data, load_options='--ram load=1,{},,,,{}'.format(start, inc))
        self.assertEqual([data[2]] + data[:2], snapshot[65533:])

    def test_ram_load_wraparound_with_step(self):
        start = 65535
        data = [23, 24, 25]
        step = 8193
        snapshot = self._get_snapshot(start, data, load_options='--ram load=1,{},,{}'.format(start, step))
        self.assertEqual(snapshot[start], data[0])
        self.assertEqual(snapshot[(start + 2 * step) & 65535], data[2])

    def test_ram_load_with_hexadecimal_parameters(self):
        start = 30000
        data = [1, 2, 3]
        step = 2
        offset = 3
        inc = 0
        snapshot = self._get_snapshot(start, data, load_options='--ram load=1,0x{:04x},0x{:04x},0x{:04x},0x{:04x},0x{:04x}'.format(start, len(data), step, offset, inc))
        self.assertEqual(data, snapshot[30003:30008:2])

    def test_ram_load_bad_address(self):
        self._test_bad_spec('--ram load=1,abcde', 'Invalid integer in load spec: 1,abcde')

    def test_ram_poke_single_address(self):
        start = 16384
        data = [4, 5, 6]
        poke_addr = 16386
        poke_val = 255
        snapshot = self._get_snapshot(start, data, '--ram poke={},{}'.format(poke_addr, poke_val))
        self.assertEqual(data[:2], snapshot[start:start + 2])
        self.assertEqual(snapshot[poke_addr], poke_val)

    def test_ram_poke_address_range(self):
        start = 16384
        data = [1, 1, 1]
        poke_addr_start = 16384
        poke_addr_end = 16383 + len(data)
        poke_val = 254
        snapshot = self._get_snapshot(start, data, '--ram poke={}-{},{}'.format(poke_addr_start, poke_addr_end, poke_val))
        self.assertEqual([poke_val] * len(data), snapshot[poke_addr_start:poke_addr_end + 1])

    def test_ram_poke_address_range_with_xor(self):
        start = 30000
        data = [1, 2, 3]
        end = start + len(data) - 1
        xor_val = 129
        snapshot = self._get_snapshot(start, data, '--ram poke={}-{},^{}'.format(start, end, xor_val))
        exp_data = [b ^ xor_val for b in data]
        self.assertEqual(exp_data, snapshot[start:end + 1])

    def test_ram_poke_address_range_with_add(self):
        start = 40000
        data = [100, 200, 32]
        end = start + len(data) - 1
        add_val = 130
        snapshot = self._get_snapshot(start, data, '--ram poke={}-{},+{}'.format(start, end, add_val))
        exp_data = [(b + add_val) & 255 for b in data]
        self.assertEqual(exp_data, snapshot[start:end + 1])

    def test_ram_poke_address_range_with_step(self):
        snapshot = self._get_snapshot(16384, [2, 9, 2], '--ram poke=16384-16386-2,253')
        self.assertEqual([253, 9, 253], snapshot[16384:16387])

    def test_ram_poke_hex_address(self):
        address, value = 16385, 253
        snapshot = self._get_snapshot(16384, [1], '--ram poke=${:X},{}'.format(address, value))
        self.assertEqual(snapshot[address], value)

    def test_ram_poke_0x_hex_values(self):
        snapshot = self._get_snapshot(16384, [2, 1, 2], '--ram poke=0x4000-0x4002-0x02,0x2a')
        self.assertEqual([42, 1, 42], snapshot[16384:16387])

    def test_ram_poke_bad_value(self):
        self._test_bad_spec('--ram poke=1', 'Value missing in poke spec: 1')
        self._test_bad_spec('--ram poke=q', 'Value missing in poke spec: q')
        self._test_bad_spec('--ram poke=1,x', 'Invalid value in poke spec: 1,x')
        self._test_bad_spec('--ram poke=x,1', 'Invalid address range in poke spec: x,1')
        self._test_bad_spec('--ram poke=1-y,1', 'Invalid address range in poke spec: 1-y,1')
        self._test_bad_spec('--ram poke=1-3-z,1', 'Invalid address range in poke spec: 1-3-z,1')

    def test_ram_move(self):
        start = 16384
        data = [5, 6, 7]
        src = start
        size = len(data)
        dest = 16387
        snapshot = self._get_snapshot(start, data, '--ram move={},{},{}'.format(src, size, dest))
        self.assertEqual(data, snapshot[start:start + len(data)])
        self.assertEqual(data, snapshot[dest:dest + len(data)])

    def test_ram_move_hex_address(self):
        src, size, dest = 16384, 1, 16385
        value = 3
        snapshot = self._get_snapshot(src, [value], '--ram move=${:X},{},${:x}'.format(src, size, dest))
        self.assertEqual(snapshot[dest], value)

    def test_ram_move_0x_hex_values(self):
        src, size, dest = 16385, 1, 16384
        value = 2
        snapshot = self._get_snapshot(src, [value], '--ram move=0x{:X},0x{:X},0x{:x}'.format(src, size, dest))
        self.assertEqual(snapshot[dest], value)

    def test_ram_move_bad_address(self):
        self._test_bad_spec('--ram move=1', 'Not enough arguments in move spec (expected 3): 1')
        self._test_bad_spec('--ram move=1,2', 'Not enough arguments in move spec (expected 3): 1,2')
        self._test_bad_spec('--ram move=x,2,3', 'Invalid integer in move spec: x,2,3')
        self._test_bad_spec('--ram move=1,y,3', 'Invalid integer in move spec: 1,y,3')
        self._test_bad_spec('--ram move=1,2,z', 'Invalid integer in move spec: 1,2,z')

    def test_ram_sysvars(self):
        snapshot = self._get_snapshot(23552, [0], '--ram sysvars')
        self.assertEqual(sum(snapshot[23552:23755]), 7911)
        self.assertEqual(len(snapshot), 65536)

    def test_ram_invalid_operation(self):
        self._test_bad_spec('--ram foo=bar', 'Invalid operation: foo=bar')

    def test_ram_help(self):
        output, error = self.run_tap2sna('--ram help')
        self.assertTrue(output.startswith('Usage: --ram call=[/path/to/moduledir:]module.function\n'))
        self.assertEqual(error, '')

    def test_tap_file_in_zip_archive(self):
        data = [1]
        block = create_tap_data_block(data)
        tap_name = 'game.tap'
        zip_fname = self._write_tap([block], zip_archive=True, tap_name=tap_name)
        z80file = '{}/out.z80'.format(self.make_directory())
        start = 16385
        output, error = self.run_tap2sna(f'--ram load=1,{start} {zip_fname} {z80file}')
        self.assertEqual(output, 'Extracting {}\nWriting {}\n'.format(tap_name, z80file))
        self.assertEqual(error, '')
        snapshot = get_snapshot(z80file)
        self.assertEqual(data, snapshot[start:start + len(data)])

    def test_invalid_tzx_file(self):
        tzxfile = self.write_bin_file([1, 2, 3], suffix='.tzx')
        z80file = 'test.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna('{} {}/{}'.format(tzxfile, self.make_directory(), z80file))
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot {}: Not a TZX file'.format(z80file))

    def test_tzx_block_type_0x10(self):
        data = [1, 2, 4]
        start = 16386
        block = create_tzx_data_block(data)
        snapshot = self._get_snapshot(start, blocks=[block], tzx=True)
        self.assertEqual(data, snapshot[start:start + len(data)])

    def test_tzx_block_type_0x11(self):
        data = [2, 3, 5]
        block = [17] # Block ID
        block.extend([0] * 15)
        data_block = create_data_block(data)
        length = len(data_block)
        block.extend((length % 256, length // 256, 0))
        block.extend(data_block)
        start = 16387
        snapshot = self._get_snapshot(start, blocks=[block], tzx=True)
        self.assertEqual(data, snapshot[start:start + len(data)])

    def test_tzx_block_type_0x14(self):
        data = [7, 11, 13]
        block = [20] # Block ID
        block.extend([0] * 7)
        data_block = create_data_block(data)
        length = len(data_block)
        block.extend((length % 256, length // 256, 0))
        block.extend(data_block)
        start = 16388
        snapshot = self._get_snapshot(start, blocks=[block], tzx=True)
        self.assertEqual(data, snapshot[start:start + len(data)])

    def test_load_first_byte_of_block(self):
        data = [1, 2, 3, 4, 5]
        block = [20] # Block ID
        block.extend([0] * 7)
        length = len(data)
        block.extend((length % 256, length // 256, 0))
        block.extend(data)
        start = 16389
        load_options = '--ram load=+1,{}'.format(start)
        snapshot = self._get_snapshot(load_options=load_options, blocks=[block], tzx=True)
        exp_data = data[:-1]
        self.assertEqual(exp_data, snapshot[start:start + len(exp_data)])

    def test_load_last_byte_of_block(self):
        data = [1, 2, 3, 4, 5]
        block = [20] # Block ID
        block.extend([0] * 7)
        length = len(data)
        block.extend((length % 256, length // 256, 0))
        block.extend(data)
        start = 16390
        load_options = '--ram load=1+,{}'.format(start)
        snapshot = self._get_snapshot(load_options=load_options, blocks=[block], tzx=True)
        exp_data = data[1:]
        self.assertEqual(exp_data, snapshot[start:start + len(exp_data)])

    def test_load_first_and_last_bytes_of_block(self):
        data = [1, 2, 3, 4, 5]
        block = [20] # Block ID
        block.extend([0] * 7)
        length = len(data)
        block.extend((length % 256, length // 256, 0))
        block.extend(data)
        start = 16391
        load_options = '--ram load=+1+,{}'.format(start)
        snapshot = self._get_snapshot(load_options=load_options, blocks=[block], tzx=True)
        self.assertEqual(data, snapshot[start:start + len(data)])

    def test_tzx_with_unsupported_blocks(self):
        blocks = []
        blocks.append((18, 0, 0, 0, 0)) # 0x12 Pure Tone
        blocks.append((19, 2, 0, 0, 0, 0)) # 0x13 Pulse sequence
        blocks.append([21] + [0] * 5 + [1, 0, 0, 0]) # 0x15 Direct Recording
        blocks.append([24, 11] + [0] * 14) # 0x18 CSW Recording
        blocks.append([25, 20] + [0] * 23) # 0x19 Generalized Data Block
        blocks.append((32, 0, 0)) # 0x20 Pause (silence) or 'Stop the Tape' command
        blocks.append((33, 1, 32)) # 0x21 Group start
        blocks.append((34,)) # 0x22 - Group end
        blocks.append((35, 0, 0)) # 0x23 Jump to block
        blocks.append((36, 2, 0)) # 0x24 Loop start
        blocks.append((37,)) # 0x25 Loop end
        blocks.append((38, 1, 0, 0, 0)) # 0x26 Call sequence
        blocks.append((39,)) # 0x27 Return from sequence
        blocks.append((40, 5, 0, 1, 0, 0, 1, 32)) # 0x28 Select block
        blocks.append((42, 0, 0, 0, 0)) # 0x2A Stop the tape if in 48K mode
        blocks.append((43, 1, 0, 0, 0, 1)) # 0x2B Set signal level
        blocks.append((48, 1, 65)) # 0x30 Text description
        blocks.append((49, 0, 1, 66)) # 0x31 Message block
        blocks.append((50, 4, 0, 1, 0, 1, 33)) # 0x32 Archive info
        blocks.append((51, 1, 0, 0, 0)) # 0x33 Hardware type
        blocks.append([53] + [32] * 16 + [1] + [0] * 4) # 0x35 Custom info block
        blocks.append([90] + [0] * 9) # 0x5A "Glue" block
        data = [2, 4, 6]
        blocks.append(create_tzx_data_block(data))
        start = 16388
        load_options = '--ram load={},{}'.format(len(blocks), start)
        snapshot = self._get_snapshot(load_options=load_options, blocks=blocks, tzx=True)
        self.assertEqual(data, snapshot[start:start + len(data)])

    def test_tzx_with_unknown_block(self):
        block_id = 22
        block = [block_id, 0]
        tzxfile = self._write_tzx([block])
        z80file = 'test.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna('{} {}/{}'.format(tzxfile, self.make_directory(), z80file))
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot {}: Unknown TZX block ID: 0x{:X}'.format(z80file, block_id))

    def test_default_register_values(self):
        block = create_tap_data_block([0])
        tapfile = self._write_tap([block])
        z80file = '{}/out.z80'.format(self.make_directory())
        exp_reg_values = {
            'a': 0, 'f': 0, 'bc': 0, 'de': 0, 'hl': 0, 'i': 63, 'r': 0,
            '^bc': 0, '^de': 0, '^hl': 0, 'ix': 0, 'iy': 23610, 'sp': 0, 'pc': 0
        }
        output, error = self.run_tap2sna('--ram load=1,16384 {} {}'.format(tapfile, z80file))
        self.assertEqual(error, '')
        with open(z80file, 'rb') as f:
            z80_header = f.read(34)
        for reg, exp_value in exp_reg_values.items():
            offset = Z80_REGISTERS[reg]
            size = len(reg) - 1 if reg.startswith('^') else len(reg)
            if size == 1:
                value = z80_header[offset]
            else:
                value = z80_header[offset] + 256 * z80_header[offset + 1]
            self.assertEqual(value, exp_value)

    def test_reg(self):
        block = create_tap_data_block([1])
        tapfile = self._write_tap([block])
        reg_dicts = (
            {'^a': 1, '^b': 2, '^c': 3, '^d': 4, '^e': 5, '^f': 6, '^h': 7, '^l': 8},
            {'a': 9, 'b': 10, 'c': 11, 'd': 12, 'e': 13, 'f': 14, 'h': 15, 'l': 16, 'r': 129},
            {'^bc': 258, '^de': 515, '^hl': 65534, 'bc': 259, 'de': 516, 'hl': 65533},
            {'i': 13, 'ix': 1027, 'iy': 1284, 'pc': 1541, 'r': 23, 'sp': 32769}
        )
        for reg_dict in reg_dicts:
            reg_options = ' '.join(['--reg {}={}'.format(r, v) for r, v in reg_dict.items()])
            z80file = '{}/out.z80'.format(self.make_directory())
            output, error = self.run_tap2sna(f'--ram load=1,16384 {reg_options} {tapfile} {z80file}')
            self.assertEqual(error, '')
            with open(z80file, 'rb') as f:
                z80_header = f.read(34)
            for reg, exp_value in reg_dict.items():
                offset = Z80_REGISTERS[reg]
                size = len(reg) - 1 if reg.startswith('^') else len(reg)
                if size == 1:
                    value = z80_header[offset]
                else:
                    value = z80_header[offset] + 256 * z80_header[offset + 1]
                self.assertEqual(value, exp_value)
                if reg == 'r' and exp_value & 128:
                    self.assertEqual(z80_header[12] & 1, 1)

    def test_reg_hex_value(self):
        odir = self.make_directory()
        tapfile = self._write_tap([create_tap_data_block([1])])
        z80fname = 'test.z80'
        reg_value = 35487
        output, error = self.run_tap2sna('--ram load=1,16384 --reg bc=${:x} -d {} {} {}'.format(reg_value, odir, tapfile, z80fname))
        self.assertEqual(error, '')
        with open(os.path.join(odir, z80fname), 'rb') as f:
            z80_header = f.read(4)
        self.assertEqual(z80_header[2] + 256 * z80_header[3], reg_value)

    def test_reg_0x_hex_value(self):
        odir = self.make_directory()
        tapfile = self._write_tap([create_tap_data_block([1])])
        z80fname = 'test.z80'
        reg_value = 54873
        output, error = self.run_tap2sna('--ram load=1,16384 --reg hl=0x{:x} -d {} {} {}'.format(reg_value, odir, tapfile, z80fname))
        self.assertEqual(error, '')
        with open(os.path.join(odir, z80fname), 'rb') as f:
            z80_header = f.read(6)
        self.assertEqual(z80_header[4] + 256 * z80_header[5], reg_value)

    def test_reg_bad_value(self):
        self._test_bad_spec('--reg bc=A2', 'Cannot parse register value: bc=A2')

    def test_ram_invalid_register(self):
        self._test_bad_spec('--reg iz=1', 'Invalid register: iz=1')

    def test_reg_help(self):
        output, error = self.run_tap2sna('--reg help')
        self.assertTrue(output.startswith('Usage: --reg name=value\n'))
        self.assertEqual(error, '')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load(self):
        code_start = 32768
        code = [4, 5]
        tapfile, basic_data = self._write_basic_loader(code_start, code)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load {tapfile} {z80file}')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(options.reg))

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_initial_code_block(self):
        code_start = 65360 # Overwrite return address on stack with...
        code = [128, 128]  # ...32896
        blocks = [
            create_tap_header_block("\xafblock", code_start, len(code)),
            create_tap_data_block(code)
        ]
        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load {tapfile} {z80file}')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Bytes: CODE block    ',
            'Fast loading data block: 65360,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32896',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        exp_reg = set(('^F=129', 'SP=65362', 'IX=65362', 'IY=23610', 'PC=32896'))
        self.assertLessEqual(exp_reg, set(options.reg))

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_given_start_address(self):
        code_start = 32768
        start = 32769
        code = [175, 201]
        tapfile, basic_data = self._write_basic_loader(code_start, code)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load --start {start} {tapfile} {z80file}')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=32769',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32769'))
        self.assertLessEqual(exp_reg, set(options.reg))

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_character_array(self):
        code_start = 32768
        code_start_str = [ord(c) for c in str(code_start)]
        basic_data = [
            0, 10,            # Line 10
            25, 0,            # Line length
            239, 34, 34, 228, # LOAD "" DATA
            97, 36, 40, 41,   # a$()
            58,               # :
            239, 34, 34, 175, # LOAD ""CODE
            58,               # :
            249, 192, 176,    # RANDOMIZE USR VAL
            34,               # "
            *code_start_str,  # start address
            34,               # "
            13                # ENTER
        ]
        ca_name = "characters"
        ca_data = [193, 5, 0, 1, 2, 0, 97, 98]
        code = [4, 5]
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block(ca_name, length=len(ca_data), data_type=2),
            create_tap_data_block(ca_data),
            create_tap_header_block("simloadbyt", code_start, len(code)),
            create_tap_data_block(code)
        ]
        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load {tapfile} {z80file}')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,29',
            'Character array: characters',
            'Fast loading data block: 23787,8',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(ca_data, snapshot[23787:23787 + len(ca_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(options.reg))

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_number_array(self):
        code_start = 32768
        code_start_str = [ord(c) for c in str(code_start)]
        basic_data = [
            0, 10,            # Line 10
            24, 0,            # Line length
            239, 34, 34, 228, # LOAD "" DATA
            97, 40, 41,       # a()
            58,               # :
            239, 34, 34, 175, # LOAD ""CODE
            58,               # :
            249, 192, 176,    # RANDOMIZE USR VAL
            34,               # "
            *code_start_str,  # start address
            34,               # "
            13                # ENTER
        ]
        na_name = "numbers"
        na_data = [129, 13, 0, 1, 2, 0, 0, 0, 1, 0, 0, 0, 0, 2, 0, 0]
        code = [4, 5]
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block(na_name, length=len(na_data), data_type=1),
            create_tap_data_block(na_data),
            create_tap_header_block("simloadbyt", code_start, len(code)),
            create_tap_data_block(code)
        ]
        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load {tapfile} {z80file}')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,28',
            'Number array: numbers   ',
            'Fast loading data block: 23786,16',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(na_data, snapshot[23786:23786 + len(na_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(options.reg))

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_headerless_block(self):
        code_start = 32768
        code_start_str = [ord(c) for c in str(code_start)]
        basic_data = [
            0, 10,            # Line 10
            16, 0,            # Line length
            239, 34, 34, 175, # LOAD ""CODE
            58,               # :
            249, 192, 176,    # RANDOMIZE USR VAL
            34,               # "
            *code_start_str,  # start address
            34,               # "
            13                # ENTER
        ]
        code = [
            221, 33, 0, 192,  # LD IX,49152
            17, 2, 0,         # LD DE,2
            55,               # SCF
            159,              # SBC A,A
            221, 229,         # PUSH IX
            195, 86, 5        # JP 1366
        ]
        code2 = [128, 129]
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block("simloadbyt", code_start, len(code)),
            create_tap_data_block(code),
            create_tap_data_block(code2)
        ]
        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load {tapfile} {z80file}')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,14',
            'Fast loading data block: 49152,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=49152',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        self.assertEqual(code2, snapshot[49152:49152 + len(code2)])
        exp_reg = set(('^F=187', 'SP=65344', 'IX=49154', 'IY=23610', 'PC=49152'))
        self.assertLessEqual(exp_reg, set(options.reg))

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_overlong_blocks(self):
        code_start = 32768
        code_start_str = [ord(c) for c in str(code_start)]
        basic_data = [
            0, 10,            # Line 10
            16, 0,            # Line length
            239, 34, 34, 175, # LOAD ""CODE
            58,               # :
            249, 192, 176,    # RANDOMIZE USR VAL
            34,               # "
            *code_start_str,  # start address
            34,               # "
            13                # ENTER
        ]
        code = [4, 5]
        basic_header = create_tap_header_block("simloadbas", 10, len(basic_data), 0)
        basic_header[0] += 1
        basic_header.append(1)
        basic_data_block = create_tap_data_block(basic_data)
        basic_data_block[0] += 1
        basic_data_block.append(2)
        code_header = create_tap_header_block("simloadbyt", code_start, len(code))
        code_header[0] += 1
        code_header.append(3)
        code_data_block = create_tap_data_block(code)
        code_data_block[0] += 1
        code_data_block.append(4)
        blocks = [
            basic_header,
            basic_data_block,
            code_header,
            code_data_block
        ]
        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load {tapfile} {z80file}')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data + [128], snapshot[23755:23755 + len(basic_data) + 1])
        self.assertEqual(code + [0], snapshot[code_start:code_start + len(code) + 1])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(options.reg))

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_undersize_block(self):
        code2 = [201]
        code2_start = 49152
        code2_end = code2_start + len(code2)
        code = [
            221, 33, 0, 192,  # LD IX,49152
            221, 229,         # PUSH IX
            17, 5, 0,         # LD DE,5
            55,               # SCF
            159,              # SBC A,A
            195, 86, 5,       # JP 1366
        ]
        code_start = 32768
        code_start_str = [ord(c) for c in str(code_start)]
        basic_data = [
            0, 10,            # Line 10
            16, 0,            # Line length
            239, 34, 34, 175, # LOAD ""CODE
            58,               # :
            249, 192, 176,    # RANDOMIZE USR VAL
            34,               # "
            *code_start_str,  # start address
            34,               # "
            13                # ENTER
        ]
        code2_data_block = create_tap_data_block(code2)
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block("simloadbyt", code_start, len(code)),
            create_tap_data_block(code),
            code2_data_block
        ]
        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load {tapfile} {z80file}')

        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        self.assertEqual(code2, snapshot[code2_start:code2_end])
        self.assertEqual(snapshot[code2_end], code2_data_block[-1])
        exp_reg = set(('^F=187', 'SP=65344', f'IX={code2_end+1}', 'E=3', 'D=0', 'IY=23610', 'PC=49152', 'F=64'))
        self.assertLessEqual(exp_reg, set(options.reg))

        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,14',
            'Fast loading data block: 49152,5',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=49152'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_skips_blocks_with_wrong_flag_byte(self):
        code_start = 32768
        code_start_str = [ord(c) for c in str(code_start)]
        basic_data = [
            0, 10,            # Line 10
            16, 0,            # Line length
            239, 34, 34, 175, # LOAD ""CODE
            58,               # :
            249, 192, 176,    # RANDOMIZE USR VAL
            34,               # "
            *code_start_str,  # start address
            34,               # "
            13                # ENTER
        ]
        code = [
            221, 33, 0, 0,    # 32768 LD IX,0
            17, 2, 0,         # 32772 LD DE,2
            55,               # 32775 SCF
            159,              # 32776 SBC A,A
            205, 86, 5,       # 32777 CALL 1366
            221, 33, 0, 192,  # 32780 LD IX,49152
            48, 245,          # 32784 JR NC,32775
        ]
        code2 = [128, 129]
        blocks = [
            create_tap_data_block(code), # Skipped
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block("simloadbyt", code_start, len(code)),
            create_tap_data_block(code),
            create_tap_header_block("IGNORE ME", 49152, len(code2)), # Skipped
            create_tap_data_block(code2)
        ]
        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load {tapfile} {z80file}')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Data block (18 bytes) [skipped]',
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,18',
            'Bytes: IGNORE ME  [skipped]',
            'Fast loading data block: 49152,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32780',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        self.assertEqual(code2, snapshot[49152:49152 + len(code2)])
        exp_reg = set(('^F=187', 'SP=65344', 'IX=49154', 'IY=23610', 'PC=32780', 'F=1'))
        self.assertLessEqual(exp_reg, set(options.reg))

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_ignores_extra_byte_at_end_of_tape(self):
        code_start = 32768
        code = [4, 5]
        blocks, basic_data = self._write_basic_loader(code_start, code, False)
        tapfile = self._write_tap(blocks + [[0]])
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load {tapfile} {z80file}')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(options.reg))

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_preserves_border_colour(self):
        code_start = 32768
        code_start_str = [ord(c) for c in str(code_start)]
        basic_data = [
            0, 10,            # Line 10
            22, 0,            # Line length
            239, 34, 34, 175, # LOAD ""CODE
            58,               # :
            231, 176,         # BORDER VAL
            34, 51, 34,       # "3"
            58,               # :
            249, 192, 176,    # RANDOMIZE USR VAL
            34,               # "
            *code_start_str,  # start address
            34,               # "
            13                # ENTER
        ]
        code = [201]
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block("simloadbyt", code_start, len(code)),
            create_tap_data_block(code)
        ]
        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load {tapfile} {z80file}')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,26',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,1',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertIn('border=3', options.state)

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_preserves_interrupt_mode_and_flip_flop(self):
        code_start = 32768
        code = [
            243,              # 32768 DI
            237, 94,          # 32769 IM 2
            201,              # 32771 RET
        ]
        start = 32771
        tapfile, basic_data = self._write_basic_loader(code_start, code)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load --start {start} {tapfile} {z80file}')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,4',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=32771',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertIn('im=2', options.state)
        self.assertIn('iff=0', options.state)

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_fast_load_does_not_overwrite_rom(self):
        start_str = [ord(c) for c in "16384"]
        basic_data = [
            0, 10,            # Line 10
            16, 0,            # Line length
            239, 34, 34, 175, # LOAD ""CODE
            58,               # :
            249, 192, 176,    # RANDOMIZE USR VAL
            34,               # "
            *start_str,       # start address
            34,               # "
            13                # ENTER
        ]
        start = 16380
        code = [
            0x01, 0x02, 0x03, 0x04, # 16380 DEFB 1,2,3,4
            0x21, 0xFC, 0x3F,       # 16384 LD HL,16380
            0x11, 0x00, 0x80,       # 16387 LD DE,32768
            0x01, 0x04, 0x00,       # 16390 LD BC,4
            0xED, 0xB0,             # 16393 LDIR
            0xC9,                   # 16395 RET
        ]
        blocks = [
            create_tap_header_block('simloadbas', 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block('simloadrom', start, len(code)),
            create_tap_data_block(code)
        ]
        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load --start 16395 {tapfile} {z80file}')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadrom',
            'Fast loading data block: 16380,16',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=16395',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual([161, 153, 66, 60], snapshot[32768:32772])
        self.assertEqual(code[4:], snapshot[start + 4:start + len(code)])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=16396', 'IY=23610', 'PC=16395'))
        self.assertLessEqual(exp_reg, set(options.reg))

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_fast_load_checks_parity(self):
        code_start = 32768
        code_start_str = [ord(c) for c in str(code_start)]
        basic_data = [
            0, 10,            # Line 10
            16, 0,            # Line length
            239, 34, 34, 175, # LOAD ""CODE
            58,               # :
            249, 192, 176,    # RANDOMIZE USR VAL
            34,               # "
            *code_start_str,  # start address
            34,               # "
            13                # ENTER
        ]
        code = [
            221, 33, 0, 192,  # 32768 LD IX,49152
            17, 2, 0,         # 32772 LD DE,2
            55,               # 32775 SCF
            159,              # 32776 SBC A,A
            205, 86, 5,       # 32777 CALL 1366
            48, 2,            # 32780 JR NC,32787 ; Jump if load failed as expected
            22, 128,          # 32782 LD D,128    ; Signal test failure
            201               # 32784 RET
        ]
        code2 = [128, 129]
        code2_block = create_tap_data_block(code2)
        code2_block[-1] ^= 255 # Break parity check
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block("simloadbyt", code_start, len(code)),
            create_tap_data_block(code),
            code2_block
        ]
        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load --start 32784 {tapfile} {z80file}')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,17',
            'Fast loading data block: 49152,2',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=32784',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        self.assertEqual(code2, snapshot[49152:49152 + len(code2)])
        exp_reg = set(('^F=187', 'D=0', 'SP=65344', 'IX=49154', 'IY=23610', 'PC=32784'))
        self.assertLessEqual(exp_reg, set(options.reg))

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_ram_call(self):
        ram_module = """
            def fix(snapshot):
                snapshot[32768:32772] = [1, 2, 3, 4]
        """
        module_dir = self.make_directory()
        module_name = 'simloadram'
        module_path = os.path.join(module_dir, f'{module_name}.py')
        module = self.write_text_file(dedent(ram_module).strip(), path=module_path)
        code_start = 32768
        code = [4, 5]
        tapfile, basic_data = self._write_basic_loader(code_start, code)
        output, error = self.run_tap2sna(f'--sim-load --ram call={module_dir}:{module_name}.fix {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual([1, 2, 3, 4], snapshot[32768:32772])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(options.reg))

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_ram_move(self):
        code_start = 32768
        code = [4, 5]
        tapfile, basic_data = self._write_basic_loader(code_start, code)
        output, error = self.run_tap2sna(f'--sim-load --ram move=32768,2,32770 {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual([4, 5, 4, 5], snapshot[32768:32772])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(options.reg))

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_ram_poke(self):
        code_start = 32768
        code = [4, 5]
        tapfile, basic_data = self._write_basic_loader(code_start, code)
        output, error = self.run_tap2sna(f'--sim-load --ram poke=32768-32770-2,1 {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual([1, 5, 1], snapshot[32768:32771])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(options.reg))

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_ram_sysvars(self):
        code_start = 32768
        code = [4, 5]
        tapfile, basic_data = self._write_basic_loader(code_start, code)
        output, error = self.run_tap2sna(f'--sim-load --ram sysvars {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual([203, 92], snapshot[23627:23629]) # VARS=23755
        self.assertEqual([204, 92], snapshot[23641:23643]) # E-LINE=23756
        self.assertEqual([206, 92], snapshot[23649:23651]) # WORKSP=23758
        self.assertEqual([206, 92], snapshot[23651:23653]) # STKBOT=23758
        self.assertEqual([206, 92], snapshot[23653:23655]) # STKEND=23758
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(options.reg))

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_unexpected_end_of_tape(self):
        basic_data = [
            0, 10,       # Line 10
            4, 0,        # Line length
            239, 34, 34, # LOAD ""
            13           # ENTER
        ]
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
        ]
        tapfile = self._write_tap(blocks)
        z80file = '{}/out.z80'.format(self.make_directory())
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'--sim-load {tapfile} {z80file}')
        out_lines = self.out.getvalue().strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,8',
            'Tape finished'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot out.z80: Failed to fast load block: unexpected end of tape')
        self.assertEqual(self.err.getvalue(), '')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_tzx_block_type_0x15(self):
        block = [
            21,          # Block ID
            79, 0,       # T-states per sample
            0, 0,        # Pause
            8,           # Used bits in last byte
            3, 0, 0,     # Data length
            1, 2, 3,     # Data
        ]
        tzxfile = self._write_tzx([block])
        z80file = '{}/out.z80'.format(self.make_directory())
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'--sim-load {tzxfile} {z80file}')
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot out.z80: TZX Direct Recording (0x15) not supported')
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_tzx_block_type_0x18(self):
        block = [
            24,          # Block ID
            11, 0, 0, 0, # Block length
            0, 0,        # Pause
            68, 172,     # Sampling rate
            1,           # Compression type
            1, 0, 0, 0,  # Number of stored pulses
            1,           # CSW Data
        ]
        tzxfile = self._write_tzx([block])
        z80file = '{}/out.z80'.format(self.make_directory())
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'--sim-load {tzxfile} {z80file}')
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot out.z80: TZX CSW Recording (0x18) not supported')
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_tzx_block_type_0x19(self):
        block = [
            25,          # Block ID
            14, 0, 0, 0, # Block length
            0, 0,        # Pause
            0, 0, 0, 0,  # Number of symbols in pilot/sync block
            1,           # Maximum number of pulses per pilot/sync symbol
            1,           # Number of pilot/sync symbols in alphabet table
            0, 0, 0, 0,  # Number of symbols in data stream
            1,           # Maximum number of pulses per data symbol
            1,           # Number of data symbols in alphabet table
        ]
        tzxfile = self._write_tzx([block])
        z80file = '{}/out.z80'.format(self.make_directory())
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'--sim-load {tzxfile} {z80file}')
        self.assertEqual(cm.exception.args[0], 'Error while getting snapshot out.z80: TZX Generalized Data Block (0x19) not supported')
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_trace(self):
        basic_data = [
            0, 10,               # Line 10
            14, 0,               # Line length
            249, 192,            # RANDOMIZE USR
            51, 50, 55, 54, 56,  # 32768 in ASCII
            14, 0, 0, 0, 128, 0, # 32768 in floating point form
            13                   # ENTER
        ]
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
        ]
        tapfile = self._write_tap(blocks)
        tracefile = '{}/sim-load.trace'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load -c trace={tracefile} {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,18',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        exp_reg = set(('^F=69', 'SP=65344', 'IX=23773', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(options.reg))
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 8101)
        self.assertEqual(trace_lines[0], '$0605 POP AF')
        self.assertEqual(trace_lines[8100], '$34BB RET')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_sim_load_with_trace_and_self_modifying_code(self):
        code = [
            33, 55, 128,  # 32820 LD HL,32823
            117,          # 32823 LD (HL),L   ; -> 32823 SCF
            48, 253,      # 32824 JR NC,32823
        ]
        tapfile, basic_data = self._write_basic_loader(32820, code)
        tracefile = '{}/sim-load.trace'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load --start 32826 -c trace={tracefile} {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        self.assertIn('PC=32826', options.reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 19502)
        self.assertEqual(trace_lines[19497], '$8034 LD HL,$8037')
        self.assertEqual(trace_lines[19498], '$8037 LD (HL),L')
        self.assertEqual(trace_lines[19499], '$8038 JR NC,$8037')
        self.assertEqual(trace_lines[19500], '$8037 SCF')

    def test_sim_load_config_help(self):
        for option in ('-c', '--sim-load-config'):
            output, error = self.run_tap2sna(f'{option} help')
            self.assertTrue(output.startswith('Usage: --sim-load-config accelerate-dec-a=0/1/2\n'))
            self.assertEqual(error, '')

    def test_default_state(self):
        block = create_tap_data_block([0])
        tapfile = self._write_tap([block])
        z80file = '{}/out.z80'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--ram load=1,16384 {tapfile} {z80file}')
        self.assertEqual(error, '')
        with open(z80file, 'rb') as f:
            z80_header = f.read(30)
        self.assertEqual(z80_header[12] & 14, 0) # border=0
        self.assertEqual(z80_header[27], 1) # iff1=1
        self.assertEqual(z80_header[28], 1) # iff2=1
        self.assertEqual(z80_header[29] & 3, 1) # im=1

    def test_state_iff(self):
        block = create_tap_data_block([0])
        tapfile = self._write_tap([block])
        z80file = '{}/out.z80'.format(self.make_directory())
        iff_value = 0
        output, error = self.run_tap2sna(f'--ram load=1,16384 --state iff={iff_value} {tapfile} {z80file}')
        self.assertEqual(error, '')
        with open(z80file, 'rb') as f:
            z80_header = f.read(29)
        self.assertEqual(z80_header[27], iff_value)
        self.assertEqual(z80_header[28], iff_value)

    def test_state_iff_bad_value(self):
        self._test_bad_spec('--state iff=fa', 'Cannot parse integer: iff=fa')

    def test_state_im(self):
        block = create_tap_data_block([0])
        tapfile = self._write_tap([block])
        z80file = '{}/out.z80'.format(self.make_directory())
        im_value = 2
        output, error = self.run_tap2sna(f'--ram load=1,16384 --state im={im_value} {tapfile} {z80file}')
        self.assertEqual(error, '')
        with open(z80file, 'rb') as f:
            z80_header = f.read(30)
        self.assertEqual(z80_header[29] & 3, im_value)

    def test_state_im_bad_value(self):
        self._test_bad_spec('--state im=Q', 'Cannot parse integer: im=Q')

    def test_state_border(self):
        block = create_tap_data_block([0])
        tapfile = self._write_tap([block])
        z80file = '{}/out.z80'.format(self.make_directory())
        border = 4
        output, error = self.run_tap2sna(f'--ram load=1,16384 --state border={border} {tapfile} {z80file}')
        self.assertEqual(error, '')
        with open(z80file, 'rb') as f:
            z80_header = f.read(13)
        self.assertEqual((z80_header[12] // 2) & 7, border)

    def test_state_border_bad_value(self):
        self._test_bad_spec('--state border=x!', 'Cannot parse integer: border=x!')

    def test_state_tstates(self):
        block = create_tap_data_block([0])
        tapfile = self._write_tap([block])
        z80file = os.path.join(self.make_directory(), 'out.z80')
        tstates = 31445
        output, error = self.run_tap2sna(f'--ram load=1,16384 --state tstates={tstates} {tapfile} {z80file}')
        self.assertEqual(error, '')
        with open(z80file, 'rb') as f:
            z80_header = tuple(f.read(58))
        t1 = (z80_header[55] + 256 * z80_header[56]) % 17472
        t2 = (2 - z80_header[57]) % 4
        self.assertEqual(69887 - t2 * 17472 - t1, tstates)

    def test_state_tstates_bad_value(self):
        self._test_bad_spec('--state tstates=?', 'Cannot parse integer: tstates=?')

    def test_state_issue2(self):
        block = create_tap_data_block([0])
        tapfile = self._write_tap([block])
        for issue2 in (0, 1):
            z80file = os.path.join(self.make_directory(), 'out.z80')
            output, error = self.run_tap2sna(f'--ram load=1,16384 --state issue2={issue2} {tapfile} {z80file}')
            self.assertEqual(error, '')
            with open(z80file, 'rb') as f:
                z80_header = tuple(f.read(30))
            self.assertEqual((z80_header[29] // 4) & 1, issue2)

    def test_state_issue2_bad_value(self):
        self._test_bad_spec('--state issue2=*', 'Cannot parse integer: issue2=*')

    def test_state_invalid_parameter(self):
        self._test_bad_spec('--state baz=2', 'Invalid parameter: baz=2')

    def test_state_help(self):
        output, error = self.run_tap2sna('--state help')
        self.assertEqual(error, '')
        exp_output = """
            Usage: --state name=value

            Set a hardware state attribute. Recognised names and their default values are:

              border  - border colour (default=0)
              iff     - interrupt flip-flop: 0=disabled, 1=enabled (default=1)
              im      - interrupt mode (default=1)
              issue2  - issue 2 emulation: 0=disabled, 1=enabled (default=0)
              tstates - T-states elapsed since start of frame (default=34943)
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_config_TraceLine_read_from_file(self):
        ini = """
            [tap2sna]
            TraceLine={pc:05}: {i}
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        basic_data = [
            0, 10,               # Line 10
            2, 0,                # Line length
            234,                 # REM
            13                   # ENTER
        ]
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
        ]
        tapfile = self._write_tap(blocks)
        tracefile = '{}/sim-load.trace'.format(self.make_directory())
        output, error = self.run_tap2sna(f'--sim-load -c trace={tracefile} --start 1343 -c finish-tape=1 {tapfile} out.z80')
        self.assertEqual(error, '')
        self.assertIn('PC=1343', options.reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 7281)
        self.assertEqual(trace_lines[0], '01541: POP AF')
        self.assertEqual(trace_lines[7280], '01506: RET')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_config_TraceLine_set_on_command_line(self):
        basic_data = [
            0, 10,               # Line 10
            2, 0,                # Line length
            234,                 # REM
            13                   # ENTER
        ]
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
        ]
        tapfile = self._write_tap(blocks)
        tracefile = '{}/sim-load.trace'.format(self.make_directory())
        trace_line = '{pc:>5}:{i}'
        args = f'--sim-load -I TraceLine={trace_line} -c trace={tracefile} --start 1343 -c finish-tape=1 {tapfile} out.z80'
        output, error = self.run_tap2sna(args)
        self.assertEqual(error, '')
        self.assertIn('PC=1343', options.reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 7281)
        self.assertEqual(trace_lines[0], ' 1541:POP AF')
        self.assertEqual(trace_lines[7280], ' 1506:RET')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_config_TraceLine_with_register_values(self):
        tapfile = self._write_tap([create_tap_header_block("prog", 10, 1, 0)])
        tracefile = '{}/sim-load.trace'.format(self.make_directory())
        trace_line = "${pc:04X} {i:<13} AFBCDEHL={r[a]:02X}{r[f]:02X}{r[b]:02X}{r[c]:02X}{r[d]:02X}{r[e]:02X}{r[h]:02X}{r[l]:02X}"
        trace_line += " AFBCDEHL'={r[^a]:02X}{r[^f]:02X}{r[^b]:02X}{r[^c]:02X}{r[^d]:02X}{r[^e]:02X}{r[^h]:02X}{r[^l]:02X}"
        trace_line += " IX={r[ixh]:02X}{r[ixl]:02X} IY={r[iyh]:02X}{r[iyl]:02X} SP={r[sp]:04X} IR={r[i]:02X}{r[r]:02X} T={r[t]}"
        args = ('--sim-load', '-I', f'TraceLine={trace_line}', '-c', f'trace={tracefile}', '--start', '0x250E', tapfile, 'out.z80')
        tap2sna.main(args)
        self.assertEqual(self.err.getvalue(), '')
        self.assertIn('PC=9486', options.reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 31)
        self.assertEqual(trace_lines[0], "$0605 POP AF        AFBCDEHL=1B52000000000000 AFBCDEHL'=0000000000000000 IX=0000 IY=5C3A SP=FF52 IR=3F01 T=10")
        self.assertEqual(trace_lines[1], "$0606 LD A,($5C74)  AFBCDEHL=E152000000000000 AFBCDEHL'=0000000000000000 IX=0000 IY=5C3A SP=FF52 IR=3F02 T=23")
        self.assertEqual(trace_lines[2], "$0609 SUB $E0       AFBCDEHL=0102000000000000 AFBCDEHL'=0000000000000000 IX=0000 IY=5C3A SP=FF52 IR=3F03 T=30")
        self.assertEqual(trace_lines[28], "$250A LD B,$00      AFBCDEHL=2261002200002597 AFBCDEHL'=0000000000000000 IX=0000 IY=5C3A SP=FF4C IR=3F1D T=274")
        self.assertEqual(trace_lines[29], "$250C LD C,(HL)     AFBCDEHL=2261001C00002597 AFBCDEHL'=0000000000000000 IX=0000 IY=5C3A SP=FF4C IR=3F1E T=281")
        self.assertEqual(trace_lines[30], "$250D ADD HL,BC     AFBCDEHL=2260001C000025B3 AFBCDEHL'=0000000000000000 IX=0000 IY=5C3A SP=FF4C IR=3F1F T=292")

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_config_TraceOperand(self):
        tapfile = self._write_tap([create_tap_header_block("prog", 10, 1, 0)])
        tracefile = '{}/sim-load.trace'.format(self.make_directory())
        args = f'--sim-load -I TraceOperand=&,02x,04x -c trace={tracefile} --start 1343 {tapfile} out.z80'
        output, error = self.run_tap2sna(args)
        self.assertEqual(error, '')
        self.assertIn('PC=1343', options.reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 2265)
        self.assertEqual(trace_lines[1], '$0606 LD A,(&5c74)')
        self.assertEqual(trace_lines[2], '$0609 SUB &e0')
        self.assertEqual(trace_lines[2264], '$05E2 RET')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_config_TraceOperand_with_no_commas(self):
        tapfile = self._write_tap([create_tap_header_block("prog", 1, 1, 0)])
        tracefile = '{}/sim-load.trace'.format(self.make_directory())
        args = f'--sim-load -I TraceOperand=# -c trace={tracefile} --start 1547 {tapfile} out.z80'
        output, error = self.run_tap2sna(args)
        self.assertEqual(error, '')
        self.assertIn('PC=1547', options.reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 3)
        self.assertEqual(trace_lines[1], '$0606 LD A,(#23668)')
        self.assertEqual(trace_lines[2], '$0609 SUB #224')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_config_TraceOperand_with_one_comma(self):
        tapfile = self._write_tap([create_tap_header_block("prog", 1, 1, 0)])
        tracefile = '{}/sim-load.trace'.format(self.make_directory())
        args = f'--sim-load -I TraceOperand=+,02x -c trace={tracefile} --start 1547 {tapfile} out.z80'
        output, error = self.run_tap2sna(args)
        self.assertEqual(error, '')
        self.assertIn('PC=1547', options.reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 3)
        self.assertEqual(trace_lines[1], '$0606 LD A,(+23668)')
        self.assertEqual(trace_lines[2], '$0609 SUB +e0')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_config_TraceOperand_with_three_commas(self):
        tapfile = self._write_tap([create_tap_header_block("prog", 1, 1, 0)])
        tracefile = '{}/sim-load.trace'.format(self.make_directory())
        args = f'--sim-load -I TraceOperand=0x,02x,04x,??? -c trace={tracefile} --start 1547 {tapfile} out.z80'
        output, error = self.run_tap2sna(args)
        self.assertEqual(error, '')
        self.assertIn('PC=1547', options.reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 3)
        self.assertEqual(trace_lines[1], '$0606 LD A,(0x5c74)')
        self.assertEqual(trace_lines[2], '$0609 SUB 0xe0')

    def test_args_from_file(self):
        data = [1, 2, 3, 4]
        start = 49152
        args = """
            ; Comment
            # Another comment
            --force ; Overwrite
            --ram load=1,{} # Load first block
        """.format(start)
        args_file = self.write_text_file(dedent(args).strip(), suffix='.t2s')
        snapshot = self._get_snapshot(start, data, '@{}'.format(args_file))
        self.assertEqual(data, snapshot[start:start + len(data)])

    def test_quoted_args_from_file(self):
        code = [1, 2, 3]
        code_start = 24576
        tap_data = create_tap_header_block(start=code_start) + create_tap_data_block(code)
        odir = self.make_directory()
        tapfile = self.write_bin_file(tap_data, f'{odir}/all the data.tap')
        z80file = f'{odir}/my snapshot.z80'
        args = f"""
            --ram poke=32768,255
            "{tapfile}"
            '{z80file}'
        """
        args_file = self.write_text_file(dedent(args).strip(), suffix='.t2s')
        output, error = self.run_tap2sna(f'@{args_file}')
        self.assertEqual(error, '')
        snapshot = get_snapshot(z80file)
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        self.assertEqual(snapshot[32768], 255)

    @patch.object(tap2sna, 'urlopen', Mock(return_value=BytesIO(bytearray(create_tap_data_block([2, 3])))))
    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_remote_download(self):
        data = [2, 3]
        start = 17000
        url = 'http://example.com/test.tap'
        output, error = self.run_tap2sna('--ram load=1,{} {} {}/test.z80'.format(start, url, self.make_directory()))
        self.assertTrue(output.startswith('Downloading {}\n'.format(url)))
        self.assertEqual(error, '')
        self.assertEqual(data, snapshot[start:start + len(data)])

    @patch.object(tap2sna, 'urlopen', Mock(side_effect=urllib.error.HTTPError('', 403, 'Forbidden', None, None)))
    def test_http_error_on_remote_download(self):
        with self.assertRaisesRegex(SkoolKitError, '^Error while getting snapshot test.z80: HTTP Error 403: Forbidden$'):
            self.run_tap2sna('http://example.com/test.zip {}/test.z80'.format(self.make_directory()))

    def test_no_clobber(self):
        block = create_tap_data_block([0])
        tapfile = self._write_tap([block])
        z80file = self.write_bin_file(suffix='.z80')
        output, error = self.run_tap2sna('--ram load=1,16384 {} {}'.format(tapfile, z80file))
        self.assertTrue(output.startswith('{}: file already exists; use -f to overwrite\n'.format(z80file)))
        self.assertEqual(error, '')
