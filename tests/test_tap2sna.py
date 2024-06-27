import hashlib
import os
from textwrap import dedent
import urllib
from zipfile import ZipFile
from io import BytesIO
from unittest.mock import patch, Mock

from skoolkittest import (SkoolKitTestCase, PZX, create_header_block,
                          create_data_block, create_tap_header_block,
                          create_tap_data_block, create_tzx_header_block,
                          create_tzx_data_block, create_tzx_turbo_data_block,
                          create_tzx_pure_data_block)
from skoolkit import tap2sna, VERSION, SkoolKitError, CSimulator, CCMIOSimulator
from skoolkit.cmiosimulator import CMIOSimulator
from skoolkit.config import COMMANDS
from skoolkit.loadtracer import LoadTracer
from skoolkit.simulator import Simulator

mock_memory = None

class MockSimulator:
    def __init__(self, *args, **kwargs):
        global simulator
        self.memory = mock_memory or [1] * 65536
        self.opcodes = [self.in_a_n] * 256
        self.registers = [0x80] * 28
        self.registers[26] = 0 # Interrupts disabled
        self.frame_duration = 69888
        self.int_active = 32
        self.config = kwargs.get('config') or args[3]

        # The NOP at 49151 is a dummy instruction that triggers LoadTracer's
        # read_port() (via in_a_n() below) and starts the tape running.
        self.registers[24] = 49151 # PC
        self.stop = max(a for a in range(49152, 65536) if self.memory[a]) + 2
        simulator = self

    def set_tracer(self, tracer, *args, **kwargs):
        self.tracer = tracer
        self.set_tracer_args = args

    def in_a_n(self):
        self.tracer.read_port(self.registers, 0xFE)
        self.registers[24] += 1 # PC
        if self.registers[24] == self.stop:
            self.registers[25] = self.tracer.edges[self.tracer.state[3]]
        else:
            self.registers[25] += 1000 # T-states

def mock_make_snapshot(*args):
    global make_snapshot_args
    make_snapshot_args = args

def mock_config(name):
    return {k: v[0] for k, v in COMMANDS[name].items()}

def mock_write_snapshot(fname, ram, registers, state):
    global s_fname, snapshot, s_banks, s_reg, s_state
    s_fname = fname
    snapshot = [0] * 65536
    if len(ram) == 8:
        s_banks = ram
        page = 0
        for spec in state:
            if spec.startswith('7ffd='):
                page = int(spec[5:]) % 8
                break
        snapshot[0x4000:0x8000] = ram[5]
        snapshot[0x8000:0xC000] = ram[2]
        snapshot[0xC000:] = ram[page]
    else:
        s_banks = None
        snapshot[0x4000:] = ram
    s_reg = registers
    s_state = state

class MockKeyboardTracer:
    def __init__(self, simulator, load, kb_delay):
        global kbtracer
        self.simulator = simulator
        self.load = load
        self.kb_delay = kb_delay
        self.run_called = False
        kbtracer = self

    def run(self, stop, timeout, tracefile, trace_line, prefix, byte_fmt, word_fmt):
        self.stop = stop
        self.timeout = timeout
        self.tracefile = tracefile
        self.trace_line = trace_line
        self.prefix = prefix
        self.byte_fmt = byte_fmt
        self.word_fmt = word_fmt
        self.border = id(self)
        self.out7ffd = 0
        self.outfffd = id(self) + 2
        self.ay = [id(self) + 3] * 16
        self.outfe = id(self) + 4
        self.simulator.registers[25] = 70000 * len(self.load)
        self.run_called = True

class MockLoadTracer:
    def __init__(self, simulator, blocks, accelerators, pause, first_edge, polarity,
                 in_min_addr, accel_dec_a, list_accelerators, border, out7ffd, outfffd, ay, outfe):
        global load_tracer
        self.simulator = simulator
        self.accelerators_in = accelerators
        self.blocks = blocks
        self.pause = pause
        self.first_edge = first_edge
        self.polarity = polarity
        self.in_min_addr = in_min_addr
        self.accel_dec_a = accel_dec_a
        self.list_accelerators = list_accelerators
        self.border = border
        self.out7ffd = out7ffd
        self.outfffd = outfffd
        self.ay = ay
        self.outfe = outfe
        self.accelerators = {'speedlock': 1, 'bleepload': 2}
        self.inc_b_misses = 3
        self.dec_b_misses = 4
        self.run_called = False
        load_tracer = self

    def run(self, stop, fast_load, finish_tape, timeout, tracefile, trace_line, prefix, byte_fmt, word_fmt):
        self.stop = stop
        self.fast_load = fast_load
        self.finish_tape = finish_tape
        self.timeout = timeout
        self.tracefile = tracefile
        self.trace_line = trace_line
        self.prefix = prefix
        self.byte_fmt = byte_fmt
        self.word_fmt = word_fmt
        self.run_called = True

class TestLoadTracer(LoadTracer):
    def __init__(self, simulator, blocks, accelerators, pause, first_edge, polarity,
                 in_min_addr, accel_dec_a, list_accelerators, border, out7ffd, outfffd, ay, outfe):
        # Ensure that accelerators are in a predictable order when testing the
        # {dec,inc}_b_auto() methods on LoadTracer
        acc_sorted = sorted(accelerators, key=lambda a: a.name)
        super().__init__(simulator, blocks, acc_sorted, pause, first_edge, polarity,
                 in_min_addr, accel_dec_a, list_accelerators, border, out7ffd, outfffd, ay, outfe)

class InterruptedTracer:
    def __init__(self, *args):
        self.border = 0
        self.out7ffd = 0
        self.outfffd = 0
        self.ay = [0] * 16
        self.outfe = 0

    def run(self, *args):
        raise KeyboardInterrupt()

class Tap2SnaTest(SkoolKitTestCase):
    def setUp(self):
        global kbtracer, load_tracer, simulator
        super().setUp()
        kbtracer = load_tracer = simulator = None

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

    def _load_tape(self, start=16384, data=None, options='', load_options=None, blocks=None, tzx=False, pzx=None):
        if pzx:
            tape_file = self.write_bin_file(pzx.data, suffix='.pzx')
        else:
            if blocks is None:
                blocks = [create_tap_data_block(data)]
            if tzx:
                tape_file = self._write_tzx(blocks)
            else:
                tape_file = self._write_tap(blocks)
        if load_options is None:
            load_options = f'--ram load=1,{start}'
        output, error = self.run_tap2sna(f'{load_options} {options} {tape_file} out.z80')
        self.assertEqual(output, 'Writing out.z80\n')
        self.assertEqual(error, '')

    def _test_bad_spec(self, option, exp_error):
        tapfile = self._write_tap([create_tap_data_block([1])])
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'--ram load=1,16384 {option} {tapfile} test.z80')
        self.assertEqual(cm.exception.args[0], f'Error while converting {tapfile}: {exp_error}')

    def _format_output(self, text):
        out_lines = []
        for line in text.strip().split('\n'):
            if '\x08' in line:
                shown = []
                index = 0
                for c in line:
                    if c == '\x08':
                        index -= 1
                    elif index < len(shown):
                        shown[index] = c
                        index += 1
                    else:
                        shown.append(c)
                        index += 1
                out_lines.append(''.join(shown).rstrip())
            else:
                out_lines.append(line.rstrip())
        return out_lines

    @patch.object(tap2sna, 'make_snapshot', mock_make_snapshot)
    def test_default_option_values(self):
        self.run_tap2sna('in.tap out.z80')
        options = make_snapshot_args[1]
        self.assertIsNone(options.output_dir)
        self.assertIsNone(options.stack)
        self.assertEqual([], options.ram_ops)
        self.assertEqual([], options.reg)
        self.assertIsNone(options.start)
        self.assertEqual([], options.sim_load_config)
        self.assertEqual([], options.state)
        self.assertIsNone(options.tape_name)
        self.assertEqual(options.tape_start, 1)
        self.assertEqual(options.tape_stop, 0)
        self.assertIsNone(options.tape_sum)
        self.assertEqual(options.user_agent, '')
        self.assertEqual([], options.params)

    @patch.object(tap2sna, 'make_snapshot', mock_make_snapshot)
    def test_config_read_from_file(self):
        ini = """
            [tap2sna]
            TraceLine={pc} - {i}
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        self.run_tap2sna('in.tap out.z80')
        options, z80, config = make_snapshot_args[1:4]
        self.assertIsNone(options.output_dir)
        self.assertIsNone(options.stack)
        self.assertEqual([], options.ram_ops)
        self.assertEqual([], options.reg)
        self.assertIsNone(options.start)
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

    def test_invalid_arguments(self):
        for args in ('--foo', '-k test.zip'):
            output, error = self.run_tap2sna(args, catch_exit=2)
            self.assertEqual(output, '')
            self.assertTrue(error.startswith('usage:'))

    def test_accelerator_unrecognised(self):
        blocks = [create_tap_data_block([0])]
        tapfile = self._write_tap(blocks)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'-c accelerator=nope {tapfile} out.z80')
        self.assertEqual(cm.exception.args[0], f'Error while converting {tapfile}: Unrecognised accelerator: nope')
        self.assertEqual(self.err.getvalue(), '')

    def test_unrecognised_sim_load_configuration_parameter(self):
        blocks = [create_tap_data_block([0])]
        tapfile = self._write_tap(blocks)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'-c foo=bar {tapfile} out.z80')
        self.assertEqual(cm.exception.args[0], f'Error while converting {tapfile}: Invalid sim-load configuration parameter: foo')
        self.assertEqual(self.err.getvalue(), '')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_no_snapshot_argument_with_tap_file(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        exp_z80_fname = tapfile[:-4] + '.z80'
        output, error = self.run_tap2sna(f'--ram load=1,16384 {tapfile}')
        self.assertEqual(len(error), 0)
        self.assertEqual(s_fname, exp_z80_fname)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_no_snapshot_argument_with_tzx_file(self):
        tzxfile = self._write_tzx([create_tzx_data_block([0])])
        exp_z80_fname = tzxfile[:-4] + '.z80'
        output, error = self.run_tap2sna(f'--ram load=1,16384 {tzxfile}')
        self.assertEqual(len(error), 0)
        self.assertEqual(s_fname, exp_z80_fname)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_no_snapshot_argument_with_zip_file(self):
        zipfile = self._write_tap([create_tap_data_block([0])], True, 'great_game.tap')
        exp_z80_fname = 'great_game.z80'
        output, error = self.run_tap2sna(f'--ram load=1,16384 {zipfile}')
        self.assertEqual(len(error), 0)
        self.assertEqual(s_fname, exp_z80_fname)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_no_snapshot_argument_with_unconventionally_named_tap_file(self):
        tapfile = self.write_bin_file(create_tap_data_block([0]), suffix='.tape')
        exp_z80_fname = tapfile + '.z80'
        output, error = self.run_tap2sna(f'--ram load=1,16384 {tapfile}')
        self.assertEqual(len(error), 0)
        self.assertEqual(s_fname, exp_z80_fname)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    @patch.object(tap2sna, 'urlopen', Mock(return_value=BytesIO(bytearray(create_tap_data_block([1])))))
    def test_no_snapshot_argument_with_remote_download(self):
        url = 'http://example.com/test.tap'
        exp_z80_fname = 'test.z80'
        output, error = self.run_tap2sna(f'--ram load=1,16384 {url}')
        self.assertEqual(error, '')
        self.assertEqual(s_fname, exp_z80_fname)
        self.assertEqual(snapshot[16384], 1)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_tape_file_with_hash_in_name(self):
        code = [1, 2, 3, 4, 5]
        start = 24576
        tap_data = create_tap_data_block(code)
        tapfile = 'game#2.tap'
        self.write_bin_file(tap_data, tapfile)
        output, error = self.run_tap2sna(f'--ram load=1,{start} {tapfile} out.z80')
        self.assertEqual(error, '')
        self.assertEqual(code, snapshot[start:start + len(code)])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_option_d(self):
        odir = 'tap2sna'
        tapfile = self._write_tap([create_tap_data_block([0])])
        z80_fname = 'test.z80'
        for option in ('-d', '--output-dir'):
            output, error = self.run_tap2sna(f'{option} {odir} --ram load=1,16384 {tapfile} {z80_fname}')
            self.assertEqual(len(error), 0)
            self.assertEqual(s_fname, os.path.join(odir, z80_fname))

    @patch.object(tap2sna, 'make_snapshot', mock_make_snapshot)
    @patch.object(tap2sna, 'get_config', mock_config)
    def test_option_I(self):
        self.run_tap2sna('-I TraceLine=Hello in.tap out.z80')
        options, z80, config = make_snapshot_args[1:4]
        self.assertEqual(['TraceLine=Hello'], options.params)
        self.assertEqual(config['TraceLine'], 'Hello')

    @patch.object(tap2sna, 'make_snapshot', mock_make_snapshot)
    def test_option_I_overrides_config_read_from_file(self):
        ini = """
            [tap2sna]
            TraceLine=0x{pc:04x} {i}
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        self.run_tap2sna('--ini TraceLine=Goodbye in.tap out.z80')
        options, z80, config = make_snapshot_args[1:4]
        self.assertEqual(['TraceLine=Goodbye'], options.params)
        self.assertEqual(config['TraceLine'], 'Goodbye')

    @patch.object(tap2sna, 'make_snapshot', mock_make_snapshot)
    def test_options_p_stack(self):
        for option, stack in (('-p', 24576), ('--stack', 49152)):
            output, error = self.run_tap2sna(f'{option} {stack} in.tap out.z80')
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            options = make_snapshot_args[1]
            self.assertEqual([f'sp={stack}'], options.reg)

    @patch.object(tap2sna, 'make_snapshot', mock_make_snapshot)
    def test_options_p_stack_with_hex_address(self):
        for option, stack in (('-p', '0x6ff0'), ('--stack', '0x9ABC')):
            output, error = self.run_tap2sna(f'{option} {stack} in.tap out.z80')
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            options = make_snapshot_args[1]
            self.assertEqual(['sp={}'.format(int(stack[2:], 16))], options.reg)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_option_p(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        stack = 32768
        output, error = self.run_tap2sna(f'-p {stack} --ram load=1,16384 {tapfile} out.z80')
        self.assertEqual(error, '')
        self.assertIn(f'sp={stack}', s_reg)

    @patch.object(tap2sna, 'get_config', mock_config)
    def test_option_show_config(self):
        output, error = self.run_tap2sna('--show-config', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = r"""
            [tap2sna]
            DefaultSnapshotFormat=z80
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
            DefaultSnapshotFormat=z80
            TraceLine={pc:05} {i}
            TraceOperand=$,02X,04X
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    @patch.object(tap2sna, 'make_snapshot', mock_make_snapshot)
    def test_options_s_start(self):
        start = 30000
        exp_reg = [f'pc={start}']
        for option in ('-s', '--start'):
            output, error = self.run_tap2sna(f'{option} {start} --ram load=1,32768 in.tap out.z80')
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            options = make_snapshot_args[1]
            self.assertEqual(exp_reg, options.reg)

    @patch.object(tap2sna, 'make_snapshot', mock_make_snapshot)
    def test_options_s_start_with_hex_address(self):
        start = 30000
        exp_reg = [f'pc={start}']
        for option in ('-s', '--start'):
            output, error = self.run_tap2sna(f'{option} 0x{start:04X} --ram load=1,32768 in.tap out.z80')
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            options = make_snapshot_args[1]
            self.assertEqual(exp_reg, options.reg)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_option_s(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        start = 40000
        output, error = self.run_tap2sna(f'-s {start} --ram load=1,16384 {tapfile} out.z80')
        self.assertEqual(error, '')
        self.assertIn(f'pc={start}', s_reg)

    def test_option_tape_analysis_with_no_tape(self):
        output, error = self.run_tap2sna('--tape-analysis', catch_exit=2)
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
            T-states    EAR  Description
                     0    0  Tone (8063 x 2168 T-states)
              17480584    1  Pulse (667 T-states)
              17481251    0  Pulse (735 T-states)
              17481986    1  Data (19 bytes; 855,855/1710,1710 T-states)
              17765846    1  Pause (3500000 T-states)
              21265846    1  Tone (3223 x 2168 T-states)
              28253310    0  Pulse (667 T-states)
              28253977    1  Pulse (735 T-states)
              28254712    0  Data (5 bytes; 855,855/1710,1710 T-states)
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
            T-states    EAR  Description
                     0    0  Tone (3223 x 2168 T-states)
               6987464    1  Pulse (667 T-states)
               6988131    0  Pulse (735 T-states)
               6988866    1  Data (5 bytes; 855,855/1710,1710 T-states)
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
            T-states    EAR  Description
                     0    0  Tone (8063 x 2168 T-states)
              17480584    1  Pulse (667 T-states)
              17481251    0  Pulse (735 T-states)
              17481986    1  Data (19 bytes; 855,855/1710,1710 T-states)
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_analysis_with_first_edge(self):
        blocks = [
            create_tap_header_block(start=0),
            create_tap_data_block([4, 5, 6]),
        ]
        tapfile = self._write_tap(blocks)
        output, error = self.run_tap2sna(f'--tape-analysis -c first-edge=1 {tapfile}', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            T-states    EAR  Description
                     1    0  Tone (8063 x 2168 T-states)
              17480585    1  Pulse (667 T-states)
              17481252    0  Pulse (735 T-states)
              17481987    1  Data (19 bytes; 855,855/1710,1710 T-states)
              17765847    1  Pause (3500000 T-states)
              21265847    1  Tone (3223 x 2168 T-states)
              28253311    0  Pulse (667 T-states)
              28253978    1  Pulse (735 T-states)
              28254713    0  Data (5 bytes; 855,855/1710,1710 T-states)
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_analysis_with_polarity(self):
        blocks = [
            create_tap_header_block(start=0),
            create_tap_data_block([4, 5, 6]),
        ]
        tapfile = self._write_tap(blocks)
        output, error = self.run_tap2sna(f'--tape-analysis -c polarity=1 {tapfile}', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            T-states    EAR  Description
                     0    1  Tone (8063 x 2168 T-states)
              17480584    0  Pulse (667 T-states)
              17481251    1  Pulse (735 T-states)
              17481986    0  Data (19 bytes; 855,855/1710,1710 T-states)
              17765846    0  Pause (3500000 T-states)
              21265846    0  Tone (3223 x 2168 T-states)
              28253310    1  Pulse (667 T-states)
              28253977    0  Pulse (735 T-states)
              28254712    1  Data (5 bytes; 855,855/1710,1710 T-states)
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_analysis_with_unused_bits_in_last_byte(self):
        code = [1, 2, 3, 4]
        blocks = [create_tzx_turbo_data_block(code, used_bits=4)]
        tapfile = self._write_tzx(blocks)
        output, error = self.run_tap2sna(f'--tape-analysis {tapfile}', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            T-states    EAR  Description
                     0    0  Tone (3223 x 2168 T-states)
               6987464    1  Pulse (667 T-states)
               6988131    0  Pulse (735 T-states)
               6988866    1  Data (5 bytes + 4 bits; 855,855/1710,1710 T-states)
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
            T-states    EAR  Description
                     0    0  Tone (2000 x 1100 T-states)
               2200000    0  Pause (3500 T-states)
               2203500    0  Pulse (256 T-states)
               2203756    1  Pulse (512 T-states)
               2204268    0  Data (4 bytes; 500,500/1000,1000 T-states)
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_analysis_pzx_file(self):
        pzx = PZX()
        pzx.add_puls(2)
        pzx.add_data((1, 2, 3, 4, 5))
        pzx.add_paus()
        pzx.add_puls(1)
        pzx.add_data((6, 7, 8, 9, 10))
        pzx.add_paus()
        pzx.add_puls(pulse_counts=((5000, 2168), (1, 430), (1, 870)))
        pzx.add_data((11, 12, 13, 14, 15), (570, 570), (1050, 1050), tail=0, used_bits=5, polarity=0)
        pzx.add_puls(pulse_counts=((2000, 1234), (2, 500), (1, 1000)))
        pzx.add_data((16, 17, 18, 19, 20), (80, 0), (0, 80), tail=0)
        pzx.add_puls(pulses=(0, 1000, 1000, 1000))
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tap2sna(f'--tape-analysis {pzxfile}', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            T-states    EAR  Description
                     0    0  Tone (8063 x 2168 T-states)
              17480584    1  Pulse (667 T-states)
              17481251    0  Pulse (735 T-states)
              17481986    1  Data (5 bytes; 855,855/1710,1710 T-states)
              17562356    1  Tail pulse (945 T-states)
              17563301    0  Pause (3500000 T-states)
              21063301    0  Tone (3223 x 2168 T-states)
              28050765    1  Pulse (667 T-states)
              28051432    0  Pulse (735 T-states)
              28052167    1  Data (5 bytes; 855,855/1710,1710 T-states)
              28137667    1  Tail pulse (945 T-states)
              28138612    0  Pause (3500000 T-states)
              31638612    0  Tone (5000 x 2168 T-states)
              42478612    0  Pulse (430 T-states)
              42479042    1  Pulse (870 T-states)
              42479912    0  Data (4 bytes + 5 bits; 570,570/1050,1050 T-states)
              42533612    0  Tone (2000 x 1234 T-states)
              45001612    0  Tone (2 x 500 T-states)
              45002612    0  Pulse (1000 T-states)
              45003612    1  Data (5 bytes; 80,0/0,80 T-states)
              45006812    1  Tone (3 x 1000 T-states)
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_analysis_pzx_file_with_polarity_adjustments(self):
        pzx = PZX()
        pzx.add_puls(2)
        pzx.add_data((1, 2, 3, 4, 5), polarity=0)
        pzx.add_paus()
        pzx.add_puls(1)
        pzx.add_data((6, 7, 8, 9, 10), tail=0)
        pzx.add_paus(polarity=1)
        pzx.add_puls(1)
        pzx.add_data((11, 12, 13))
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tap2sna(f'--tape-analysis {pzxfile}', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            T-states    EAR  Description
                     0    0  Tone (8063 x 2168 T-states)
              17480584    1  Pulse (667 T-states)
              17481251    0  Pulse (735 T-states)
              17481986    1  Polarity adjustment (1->0)
              17481986    0  Data (5 bytes; 855,855/1710,1710 T-states)
              17562356    0  Tail pulse (945 T-states)
              17563301    1  Polarity adjustment (1->0)
              17563301    0  Pause (3500000 T-states)
              21063301    0  Tone (3223 x 2168 T-states)
              28050765    1  Pulse (667 T-states)
              28051432    0  Pulse (735 T-states)
              28052167    1  Data (5 bytes; 855,855/1710,1710 T-states)
              28137667    1  Pause (3500000 T-states)
              31637667    1  Polarity adjustment (1->0)
              31637667    0  Tone (3223 x 2168 T-states)
              38625131    1  Pulse (667 T-states)
              38625798    0  Pulse (735 T-states)
              38626533    1  Data (3 bytes; 855,855/1710,1710 T-states)
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_analysis_pzx_file_with_polarity_inverted(self):
        pzx = PZX()
        pzx.add_puls(2)
        pzx.add_data((1, 2, 3, 4, 5), polarity=0)
        pzx.add_paus()
        pzx.add_puls(1)
        pzx.add_data((6, 7, 8, 9, 10), tail=0)
        pzx.add_paus(polarity=1)
        pzx.add_puls(1)
        pzx.add_data((11, 12, 13))
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tap2sna(f'--tape-analysis -c polarity=1 {pzxfile}', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            T-states    EAR  Description
                     0    1  Tone (8063 x 2168 T-states)
              17480584    0  Pulse (667 T-states)
              17481251    1  Pulse (735 T-states)
              17481986    0  Polarity adjustment (0->1)
              17481986    1  Data (5 bytes; 855,855/1710,1710 T-states)
              17562356    1  Tail pulse (945 T-states)
              17563301    0  Polarity adjustment (0->1)
              17563301    1  Pause (3500000 T-states)
              21063301    1  Tone (3223 x 2168 T-states)
              28050765    0  Pulse (667 T-states)
              28051432    1  Pulse (735 T-states)
              28052167    0  Data (5 bytes; 855,855/1710,1710 T-states)
              28137667    0  Pause (3500000 T-states)
              31637667    0  Polarity adjustment (0->1)
              31637667    1  Tone (3223 x 2168 T-states)
              38625131    0  Pulse (667 T-states)
              38625798    1  Pulse (735 T-states)
              38626533    0  Data (3 bytes; 855,855/1710,1710 T-states)
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_option_tape_name(self):
        code1 = [1, 2, 3, 4, 5]
        code1_start = 24576
        tap1_data = create_tap_data_block(code1)
        tap1_fname = 'code1.tap'
        code2 = [6, 7, 8]
        code2_start = 32768
        tap2_data = create_tap_data_block(code2)
        tap2_fname = 'code2.tap'
        zipfile = 'tapes.zip'
        with ZipFile(zipfile, 'w') as archive:
            archive.writestr(tap1_fname, bytearray(tap1_data))
            archive.writestr(tap2_fname, bytearray(tap2_data))
        output, error = self.run_tap2sna(f'--tape-name {tap2_fname} --ram load=1,{code2_start} {zipfile} out.z80')
        self.assertEqual(error, '')
        self.assertEqual(code2, snapshot[code2_start:code2_start + len(code2)])

    def test_option_tape_name_with_invalid_name(self):
        tap_data = create_tap_header_block(start=32768) + create_tap_data_block([1, 2, 3])
        zipfile = 'tape.zip'
        with ZipFile(zipfile, 'w') as archive:
            archive.writestr('data.tap', bytearray(tap_data))
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'--tape-name code.tap {zipfile} out.z80')
        self.assertEqual(cm.exception.args[0], f'Error while converting tape.zip: No file named "code.tap" in the archive')
        self.assertEqual(self.err.getvalue(), '')

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_option_tape_start_with_pzx(self):
        pzx = PZX()
        pzx.add_puls()
        pzx.add_data(create_header_block())
        pzx.add_puls()
        data = create_data_block([4, 5, 6])
        pzx.add_data(data)
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tap2sna(f'--tape-start 4 {pzxfile}')
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 2)
        self.assertEqual(data, list(load_tracer.blocks[1].data))

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_option_tape_start_with_tap(self):
        blocks = [
            create_tap_header_block(),
            create_tap_data_block([4, 5, 6]),
        ]
        tapfile = self._write_tap(blocks)
        output, error = self.run_tap2sna(f'--tape-start 2 {tapfile}')
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 1)

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_option_tape_start_with_tzx(self):
        blocks = [
            create_tzx_header_block(),
            create_tzx_data_block([4, 5, 6]),
        ]
        tzxfile = self._write_tzx(blocks)
        output, error = self.run_tap2sna(f'--tape-start 2 {tzxfile}')
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 1)

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_option_tape_stop_with_pzx(self):
        pzx = PZX()
        pzx.add_puls()
        data = create_header_block()
        pzx.add_data(data)
        pzx.add_puls()
        pzx.add_data(create_data_block([4, 5, 6]))
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tap2sna(f'--tape-stop 4 {pzxfile}')
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 2)
        self.assertEqual(data, list(load_tracer.blocks[1].data))

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_option_tape_stop_with_tap(self):
        blocks = [
            create_tap_header_block(),
            create_tap_data_block([4, 5, 6]),
        ]
        tapfile = self._write_tap(blocks)
        output, error = self.run_tap2sna(f'--tape-stop 2 {tapfile}')
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 1)

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_option_tape_stop_with_tzx(self):
        blocks = [
            create_tzx_header_block(),
            create_tzx_data_block([4, 5, 6]),
        ]
        tzxfile = self._write_tzx(blocks)
        output, error = self.run_tap2sna(f'--tape-stop 2 {tzxfile}')
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 1)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_option_tape_sum(self):
        code = [1, 2, 3]
        code_start = 49152
        tap_data = create_tap_data_block(code)
        md5sum = hashlib.md5(bytearray(tap_data)).hexdigest()
        zipfile = 'tape.zip'
        with ZipFile(zipfile, 'w') as archive:
            archive.writestr('data.tap', bytearray(tap_data))
        output, error = self.run_tap2sna(f'--tape-sum {md5sum} --ram load=1,{code_start} {zipfile} out.z80')
        self.assertEqual(error, '')
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])

    def test_option_tape_sum_with_incorrect_value(self):
        code = [1, 2, 3]
        code_start = 49152
        tap_data = create_tap_header_block(start=code_start) + create_tap_data_block(code)
        md5sum = hashlib.md5(bytearray(tap_data)).hexdigest()
        zipfile = 'tape.zip'
        wrongsum = '0' * 32
        with ZipFile(zipfile, 'w') as archive:
            archive.writestr('data.tap', bytearray(tap_data))
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'--tape-sum {wrongsum} {zipfile} out.z80')
        self.assertEqual(cm.exception.args[0], f'Error while converting tape.zip: Checksum mismatch: Expected {wrongsum}, actually {md5sum}')
        self.assertEqual(self.err.getvalue(), '')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    @patch.object(tap2sna, 'urlopen')
    def test_option_u(self, mock_urlopen):
        tap_data = bytes(create_tap_data_block([1]))
        url = 'http://example.com/test.tap'
        for option, user_agent in (('-u', 'Wget/1.18'), ('--user-agent', 'SkoolKit/6.3')):
            mock_urlopen.return_value = BytesIO(tap_data)
            output, error = self.run_tap2sna(f'{option} {user_agent} --ram load=1,23296 {url} test.z80')
            self.assertTrue(output.startswith(f'Downloading {url}\n'))
            self.assertEqual(error, '')
            request = mock_urlopen.call_args[0][0]
            self.assertEqual({'User-agent': user_agent}, request.headers)
            self.assertEqual(snapshot[23296], 1)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_tap2sna(option, catch_exit=0)
            self.assertEqual(output, f'SkoolKit {VERSION}\n')

    def test_nonexistent_tap_file(self):
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'non-existent.tap test.z80')
        self.assertEqual(cm.exception.args[0], f'Error while converting non-existent.tap: non-existent.tap: file not found')

    def test_load_nonexistent_block(self):
        tapfile = self._write_tap([create_tap_data_block([1])])
        block_num = 2
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'--ram load={block_num},16384 {tapfile} test.z80')
        self.assertEqual(cm.exception.args[0], f'Error while converting {tapfile}: Block {block_num} not found')

    def test_zip_archive_with_no_tape_file(self):
        archive_fname = self.write_bin_file(suffix='.zip')
        with ZipFile(archive_fname, 'w') as archive:
            archive.writestr('game.txt', bytearray((1, 2)))
        z80_fname = 'test.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'{archive_fname} out.z80')
        self.assertEqual(cm.exception.args[0], f'Error while converting {archive_fname}: No PZX, TAP or TZX file found')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_call(self):
        ram_module = """
            def fix(snapshot):
                snapshot[65280:] = list(range(256))
        """
        module_dir = self.make_directory()
        module_path = os.path.join(module_dir, 'ram.py')
        module = self.write_text_file(dedent(ram_module).strip(), path=module_path)
        blocks = [create_tap_data_block([0])]
        load_options = f'--ram load=1,16384 --ram call={module_dir}:ram.fix'
        self._load_tape(load_options=load_options, blocks=blocks)
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

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_load(self):
        start = 16384
        data = [237, 1, 1, 1, 1, 1]
        self._load_tape(start, data)
        self.assertEqual(data, snapshot[start:start + len(data)])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_load_pzx(self):
        start = 32768
        data = [1, 4, 9, 16, 25]
        pzx = PZX()
        pzx.add_puls()
        pzx.add_data(create_data_block(data))
        self._load_tape(start, load_options=f'--ram load=3,{start}', pzx=pzx)
        self.assertEqual(data, snapshot[start:start + len(data)])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_load_with_length(self):
        start = 16384
        data = [1, 2, 3, 4]
        length = 2
        self._load_tape(start, data, load_options=f'--ram load=1,{start},{length}')
        self.assertEqual(data[:length], snapshot[start:start + length])
        self.assertEqual([0] * (len(data) - length), snapshot[start + length:start + len(data)])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_load_with_step(self):
        start = 16385
        data = [5, 4, 3]
        step = 2
        self._load_tape(start, data, load_options=f'--ram load=1,{start},,{step}')
        self.assertEqual(data, snapshot[start:start + len(data) * step:step])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_load_with_offset(self):
        start = 16384
        data = [15, 16, 17]
        offset = 5
        self._load_tape(start, data, load_options=f'--ram load=1,{start},,,{offset}')
        self.assertEqual(data, snapshot[start + offset:start + offset + len(data)])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_load_with_increment(self):
        start = 65534
        data = [8, 9, 10]
        inc = 65533
        self._load_tape(start, data, load_options=f'--ram load=1,{start},,,,{inc}')
        self.assertEqual([data[2]] + data[:2], snapshot[65533:])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_load_wraparound_with_step(self):
        start = 65535
        data = [23, 24, 25]
        step = 8193
        self._load_tape(start, data, load_options=f'--ram load=1,{start},,{step}')
        self.assertEqual(snapshot[start], data[0])
        self.assertEqual(snapshot[(start + 2 * step) & 65535], data[2])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_load_with_hexadecimal_parameters(self):
        start = 30000
        data = [1, 2, 3]
        step = 2
        offset = 3
        inc = 0
        self._load_tape(start, data, load_options=f'--ram load=1,0x{start:04x},0x{len(data):04x},0x{step:04x},0x{offset:04x},0x{inc:04x}')
        self.assertEqual(data, snapshot[30003:30008:2])

    def test_ram_load_bad_address(self):
        self._test_bad_spec('--ram load=1,abcde', 'Invalid integer in load spec: 1,abcde')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_poke_single_address(self):
        start = 16384
        data = [4, 5, 6]
        poke_addr = 16386
        poke_val = 255
        self._load_tape(start, data, f'--ram poke={poke_addr},{poke_val}')
        self.assertEqual(data[:2], snapshot[start:start + 2])
        self.assertEqual(snapshot[poke_addr], poke_val)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_poke_address_range(self):
        start = 16384
        data = [1, 1, 1]
        poke_addr_start = 16384
        poke_addr_end = 16383 + len(data)
        poke_val = 254
        self._load_tape(start, data, f'--ram poke={poke_addr_start}-{poke_addr_end},{poke_val}')
        self.assertEqual([poke_val] * len(data), snapshot[poke_addr_start:poke_addr_end + 1])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_poke_address_range_with_xor(self):
        start = 30000
        data = [1, 2, 3]
        end = start + len(data) - 1
        xor_val = 129
        self._load_tape(start, data, f'--ram poke={start}-{end},^{xor_val}')
        exp_data = [b ^ xor_val for b in data]
        self.assertEqual(exp_data, snapshot[start:end + 1])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_poke_address_range_with_add(self):
        start = 40000
        data = [100, 200, 32]
        end = start + len(data) - 1
        add_val = 130
        self._load_tape(start, data, f'--ram poke={start}-{end},+{add_val}')
        exp_data = [(b + add_val) & 255 for b in data]
        self.assertEqual(exp_data, snapshot[start:end + 1])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_poke_address_range_with_step(self):
        self._load_tape(16384, [2, 9, 2], '--ram poke=16384-16386-2,253')
        self.assertEqual([253, 9, 253], snapshot[16384:16387])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_poke_hex_address(self):
        address, value = 16385, 253
        self._load_tape(16384, [1], f'--ram poke=${address:X},{value}')
        self.assertEqual(snapshot[address], value)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_poke_0x_hex_values(self):
        self._load_tape(16384, [2, 1, 2], '--ram poke=0x4000-0x4002-0x02,0x2a')
        self.assertEqual([42, 1, 42], snapshot[16384:16387])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_poke_with_page_number(self):
        data = [0]
        basic_data = [
            0, 10,  # Line 10
            2, 0,   # Line length
            234,    # REM
            13      # ENTER
        ]
        blocks = [
            create_tap_header_block('basicprog', 10, len(basic_data), 0),
            create_tap_data_block(basic_data)
        ]
        tapfile = self._write_tap(blocks)
        pokes = (
            (0, 0x0000, 255),
            (1, 0x4000, 254),
            (2, 0x8000, 253),
            (3, 0xC000, 252),
            (4, 0x3FFF, 251),
            (5, 0x7FFF, 250),
            (6, 0xBFFF, 249),
            (7, 0xFFFF, 248),
        )
        poke_opts = ' '.join(f'--ram poke={p}:{a},{v}' for p, a, v in pokes)
        output, error = self.run_tap2sna(f'-c machine=128 {poke_opts} {tapfile} out.z80')
        self.assertTrue(output.endswith(f'\nWriting out.z80\n'))
        self.assertEqual(error, '')
        for p, a, v in pokes:
            self.assertEqual(s_banks[p][a % 0x4000], v)

    def test_ram_poke_bad_value(self):
        self._test_bad_spec('--ram poke=1', 'Value missing in poke spec: 1')
        self._test_bad_spec('--ram poke=q', 'Value missing in poke spec: q')
        self._test_bad_spec('--ram poke=p:1,1', 'Invalid page number in poke spec: p:1,1')
        self._test_bad_spec('--ram poke=1,x', 'Invalid value in poke spec: 1,x')
        self._test_bad_spec('--ram poke=x,1', 'Invalid address range in poke spec: x,1')
        self._test_bad_spec('--ram poke=1-y,1', 'Invalid address range in poke spec: 1-y,1')
        self._test_bad_spec('--ram poke=1-3-z,1', 'Invalid address range in poke spec: 1-3-z,1')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_move(self):
        start = 16384
        data = [5, 6, 7]
        src = start
        size = len(data)
        dest = 16387
        self._load_tape(start, data, f'--ram move={src},{size},{dest}')
        self.assertEqual(data, snapshot[start:start + len(data)])
        self.assertEqual(data, snapshot[dest:dest + len(data)])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_move_hex_address(self):
        src, size, dest = 16384, 1, 16385
        value = 3
        self._load_tape(src, [value], f'--ram move=${src:X},{size},${dest:x}')
        self.assertEqual(snapshot[dest], value)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_move_0x_hex_values(self):
        src, size, dest = 16385, 1, 16384
        value = 2
        self._load_tape(src, [value], f'--ram move=0x{src:X},0x{size:X},0x{dest:x}')
        self.assertEqual(snapshot[dest], value)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_move_with_page_number(self):
        data = [0]
        basic_data = [
            0, 10,  # Line 10
            2, 0,   # Line length
            234,    # REM
            13      # ENTER
        ]
        blocks = [
            create_tap_header_block('basicprog', 10, len(basic_data), 0),
            create_tap_data_block(basic_data)
        ]
        tapfile = self._write_tap(blocks)
        moves = (
            (5, 22528, 8, 1, 0),
            (5, 17440, 8, 3, 0),
            (5, 17440, 8, None, 8),
            (0, 16376, 8, 4, 49152),
        )
        move_opts = []
        for src_page, src, length, dest_page, dest in moves:
            if dest_page:
                move_opts.append(f'--ram move={src_page}:{src},{length},{dest_page}:{dest}')
            else:
                move_opts.append(f'--ram move={src_page}:{src},{length},{dest}')
        move_opts = ' '.join(move_opts)
        output, error = self.run_tap2sna(f'-c machine=128 {move_opts} {tapfile} out.z80')
        self.assertTrue(output.endswith(f'\nWriting out.z80\n'))
        self.assertEqual(error, '')
        for src_page, src, length, dest_page, dest in moves:
            s = src % 0x4000
            d = dest % 0x4000
            if dest_page is None:
                dest_page = src_page
            self.assertEqual(s_banks[src_page][s:s + length], s_banks[dest_page][d:d + length])

    def test_ram_move_bad_address(self):
        self._test_bad_spec('--ram move=1', 'Not enough arguments in move spec (expected 3): 1')
        self._test_bad_spec('--ram move=1,2', 'Not enough arguments in move spec (expected 3): 1,2')
        self._test_bad_spec('--ram move=x,2,3', 'Invalid integer in move spec: x,2,3')
        self._test_bad_spec('--ram move=1,y,3', 'Invalid integer in move spec: 1,y,3')
        self._test_bad_spec('--ram move=1,2,z', 'Invalid integer in move spec: 1,2,z')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_sysvars(self):
        self._load_tape(23552, [0], '--ram sysvars')
        self.assertEqual(sum(snapshot[23552:23755]), 7911)
        self.assertEqual(len(snapshot), 65536)

    def test_ram_invalid_operation(self):
        self._test_bad_spec('--ram foo=bar', 'Invalid operation: foo=bar')

    def test_ram_help(self):
        output, error = self.run_tap2sna('--ram help')
        self.assertTrue(output.startswith('Usage: --ram call=[/path/to/moduledir:]module.function\n'))
        self.assertEqual(error, '')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_tap_file_in_zip_archive(self):
        data = [1]
        block = create_tap_data_block(data)
        tap_name = 'game.tap'
        zip_fname = self._write_tap([block], zip_archive=True, tap_name=tap_name)
        start = 16385
        output, error = self.run_tap2sna(f'--ram load=1,{start} {zip_fname} out.z80')
        self.assertEqual(output, f'Extracting {tap_name}\nWriting out.z80\n')
        self.assertEqual(error, '')
        self.assertEqual(data, snapshot[start:start + len(data)])

    def test_invalid_tzx_file(self):
        tzxfile = self.write_bin_file([1, 2, 3], suffix='.tzx')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'{tzxfile} test.z80')
        self.assertEqual(cm.exception.args[0], f'Error while converting {tzxfile}: Not a TZX file')

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_tape_stops_at_pzx_48k_stop_block_in_48k_mode(self):
        pzx = PZX()
        pzx.add_puls()
        pzx.add_data(create_header_block())
        pzx.add_puls()
        pzx.add_data(create_data_block([1, 2, 3]))
        pzx.add_stop(False)
        pzx.add_puls()
        pzx.add_data(create_data_block([4, 5, 6]))
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tap2sna(pzxfile)
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 4)

    @patch.object(tap2sna, 'KeyboardTracer', MockKeyboardTracer)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_tape_does_not_stop_at_pzx_48k_stop_block_in_128k_mode(self):
        pzx = PZX()
        pzx.add_puls()
        pzx.add_data(create_header_block())
        pzx.add_puls()
        pzx.add_data(create_data_block([1, 2, 3]))
        pzx.add_stop(False)
        pzx.add_puls()
        pzx.add_data(create_data_block([4, 5, 6]))
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tap2sna(f'-c machine=128 {pzxfile}')
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 6)

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_tape_stops_at_pzx_always_stop_block_in_48k_mode(self):
        pzx = PZX()
        pzx.add_puls()
        pzx.add_data(create_header_block())
        pzx.add_puls()
        pzx.add_data(create_data_block([1, 2, 3]))
        pzx.add_stop(True)
        pzx.add_puls()
        pzx.add_data(create_data_block([4, 5, 6]))
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tap2sna(pzxfile)
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 4)

    @patch.object(tap2sna, 'KeyboardTracer', MockKeyboardTracer)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_tape_stops_at_pzx_always_stop_block_in_128k_mode(self):
        pzx = PZX()
        pzx.add_puls()
        pzx.add_data(create_header_block())
        pzx.add_puls()
        pzx.add_data(create_data_block([1, 2, 3]))
        pzx.add_stop(True)
        pzx.add_puls()
        pzx.add_data(create_data_block([4, 5, 6]))
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tap2sna(f'-c machine=128 {pzxfile}')
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 4)

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_tape_stops_at_pause_block_with_duration_0(self):
        blocks = [
            create_tzx_header_block(),
            create_tzx_data_block([1, 2, 3]),
            (0x20, 0, 0), # 0x20 Pause 0ms
            create_tzx_data_block([4, 5, 6]),
        ]
        output, error = self.run_tap2sna(self._write_tzx(blocks))
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 2)

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_tzx_loop(self):
        blocks = [
            (0x24, 2, 0), # 0x24 Loop start
            create_tzx_header_block(),
            create_tzx_data_block([1, 2, 3]),
            (0x25,), # 0x25 Loop end
        ]
        output, error = self.run_tap2sna(self._write_tzx(blocks))
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 4)

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_tape_stops_at_tzx_block_type_0x2A_in_48k_mode(self):
        blocks = [
            create_tzx_header_block(),
            create_tzx_data_block([1, 2, 3]),
            (0x2A, 0, 0, 0, 0), # 0x2A Stop the tape if in 48K mode
            create_tzx_data_block([4, 5, 6]),
        ]
        output, error = self.run_tap2sna(self._write_tzx(blocks))
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 2)

    @patch.object(tap2sna, 'KeyboardTracer', MockKeyboardTracer)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_tape_does_not_stop_at_tzx_block_type_0x2A_in_128k_mode(self):
        blocks = [
            create_tzx_header_block(),
            create_tzx_data_block([1, 2, 3]),
            (0x2A, 0, 0, 0, 0), # 0x2A Stop the tape if in 48K mode
            create_tzx_data_block([4, 5, 6]),
        ]
        tzxfile = self._write_tzx(blocks)
        output, error = self.run_tap2sna(f'-c machine=128 {tzxfile}')
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 3)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_tzx_block_type_0x10(self):
        data = [1, 2, 4]
        start = 16386
        block = create_tzx_data_block(data)
        self._load_tape(start, blocks=[block], tzx=True)
        self.assertEqual(data, snapshot[start:start + len(data)])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_tzx_block_type_0x11(self):
        data = [2, 3, 5]
        block = [17] # Block ID
        block.extend([0] * 15)
        data_block = create_data_block(data)
        length = len(data_block)
        block.extend((length % 256, length // 256, 0))
        block.extend(data_block)
        start = 16387
        self._load_tape(start, blocks=[block], tzx=True)
        self.assertEqual(data, snapshot[start:start + len(data)])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_tzx_block_type_0x14(self):
        data = [7, 11, 13]
        block = [20] # Block ID
        block.extend([0] * 7)
        data_block = create_data_block(data)
        length = len(data_block)
        block.extend((length % 256, length // 256, 0))
        block.extend(data_block)
        start = 16388
        self._load_tape(start, blocks=[block], tzx=True)
        self.assertEqual(data, snapshot[start:start + len(data)])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_load_first_byte_of_block(self):
        data = [1, 2, 3, 4, 5]
        block = [20] # Block ID
        block.extend([0] * 7)
        length = len(data)
        block.extend((length % 256, length // 256, 0))
        block.extend(data)
        start = 16389
        load_options = f'--ram load=+1,{start}'
        self._load_tape(load_options=load_options, blocks=[block], tzx=True)
        exp_data = data[:-1]
        self.assertEqual(exp_data, snapshot[start:start + len(exp_data)])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_load_last_byte_of_block(self):
        data = [1, 2, 3, 4, 5]
        block = [20] # Block ID
        block.extend([0] * 7)
        length = len(data)
        block.extend((length % 256, length // 256, 0))
        block.extend(data)
        start = 16390
        load_options = f'--ram load=1+,{start}'
        self._load_tape(load_options=load_options, blocks=[block], tzx=True)
        exp_data = data[1:]
        self.assertEqual(exp_data, snapshot[start:start + len(exp_data)])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_load_first_and_last_bytes_of_block(self):
        data = [1, 2, 3, 4, 5]
        block = [20] # Block ID
        block.extend([0] * 7)
        length = len(data)
        block.extend((length % 256, length // 256, 0))
        block.extend(data)
        start = 16391
        load_options = f'--ram load=+1+,{start}'
        self._load_tape(load_options=load_options, blocks=[block], tzx=True)
        self.assertEqual(data, snapshot[start:start + len(data)])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_ram_load_tzx_with_unsupported_blocks(self):
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
        load_options = f'--ram load={len(blocks)},{start}'
        self._load_tape(load_options=load_options, blocks=blocks, tzx=True)
        self.assertEqual(data, snapshot[start:start + len(data)])

    def test_tzx_with_unknown_block(self):
        block_id = 0x29
        block = [block_id, 0]
        tzxfile = self._write_tzx([block])
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'{tzxfile} test.z80')
        self.assertEqual(cm.exception.args[0], f'Error while converting {tzxfile}: Unknown TZX block ID: 0x{block_id:X}')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_default_register_values(self):
        block = create_tap_data_block([0])
        tapfile = self._write_tap([block])
        output, error = self.run_tap2sna(f'--ram load=1,16384 {tapfile} out.z80')
        self.assertEqual(error, '')
        self.assertEqual([], s_reg)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
            exp_reg = [f'{r}={v}' for r, v in reg_dict.items()]
            reg_options = ' '.join([f'--reg {spec}' for spec in exp_reg])
            output, error = self.run_tap2sna(f'--ram load=1,16384 {reg_options} {tapfile} out.z80')
            self.assertEqual(error, '')
            self.assertEqual(exp_reg, s_reg)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_reg_hex_value(self):
        tapfile = self._write_tap([create_tap_data_block([1])])
        reg_value = 35487
        output, error = self.run_tap2sna(f'--ram load=1,16384 --reg bc=${reg_value:x} {tapfile} test.z80')
        self.assertEqual(error, '')
        self.assertIn(f'bc=${reg_value:x}', s_reg)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_reg_0x_hex_value(self):
        tapfile = self._write_tap([create_tap_data_block([1])])
        reg_value = 54873
        output, error = self.run_tap2sna(f'--ram load=1,16384 --reg hl=0x{reg_value:x} {tapfile} test.z80')
        self.assertEqual(error, '')
        self.assertIn(f'hl=0x{reg_value:x}', s_reg)

    def test_reg_bad_value(self):
        self._test_bad_spec('--reg bc=A2', 'Cannot parse register value: bc=A2')

    def test_ram_invalid_register(self):
        self._test_bad_spec('--reg iz=1', 'Invalid register: iz=1')

    def test_reg_help(self):
        output, error = self.run_tap2sna('--reg help')
        self.assertTrue(output.startswith('Usage: --reg name=value\n'))
        self.assertEqual(error, '')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load(self):
        code_start = 32768
        code = [4, 5]
        tapfile, basic_data = self._write_basic_loader(code_start, code)
        output, error = self.run_tap2sna(f'{tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(s_reg))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_with_initial_code_block(self):
        code_start = 65360 # Overwrite return address on stack with...
        code = [128, 128]  # ...32896
        blocks = [
            create_tap_header_block("\xafblock", code_start, len(code)),
            create_tap_data_block(code)
        ]
        tapfile = self._write_tap(blocks)
        output, error = self.run_tap2sna(f'{tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Bytes: CODE block    ',
            'Fast loading data block: 65360,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32896',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        exp_reg = set(('^F=129', 'SP=65362', 'IX=65362', 'IY=23610', 'PC=32896'))
        self.assertLessEqual(exp_reg, set(s_reg))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_with_given_start_address(self):
        code_start = 32768
        start = 32769
        code = [175, 201]
        tapfile, basic_data = self._write_basic_loader(code_start, code)
        output, error = self.run_tap2sna(f'--start {start} {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=32769',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32769'))
        self.assertLessEqual(exp_reg, set(s_reg))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
        output, error = self.run_tap2sna(f'{tapfile} out.z80')
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
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(ca_data, snapshot[23787:23787 + len(ca_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(s_reg))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
        output, error = self.run_tap2sna(f'{tapfile} out.z80')
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
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(na_data, snapshot[23786:23786 + len(na_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(s_reg))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
        output, error = self.run_tap2sna(f'{tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,14',
            'Fast loading data block: 49152,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=49152',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        self.assertEqual(code2, snapshot[49152:49152 + len(code2)])
        exp_reg = set(('^F=187', 'SP=65344', 'IX=49154', 'IY=23610', 'PC=49152'))
        self.assertLessEqual(exp_reg, set(s_reg))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
        output, error = self.run_tap2sna(f'{tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data + [128], snapshot[23755:23755 + len(basic_data) + 1])
        self.assertEqual(code + [0], snapshot[code_start:code_start + len(code) + 1])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(s_reg))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
        output, error = self.run_tap2sna(f'{tapfile} out.z80')

        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        self.assertEqual(code2, snapshot[code2_start:code2_end])
        self.assertEqual(snapshot[code2_end], code2_data_block[-1])
        exp_reg = {'^F=187', 'SP=65344', f'IX={code2_end+1}', 'DE=3', 'IY=23610', 'PC=49152', 'F=64'}
        self.assertLessEqual(exp_reg, set(s_reg))

        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,14',
            'Fast loading data block: 49152,5',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=49152',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
        output, error = self.run_tap2sna(f'{tapfile} out.z80')
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
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        self.assertEqual(code2, snapshot[49152:49152 + len(code2)])
        exp_reg = set(('^F=187', 'SP=65344', 'IX=49154', 'IY=23610', 'PC=32780', 'F=1'))
        self.assertLessEqual(exp_reg, set(s_reg))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_ignores_extra_byte_at_end_of_tape(self):
        code_start = 32768
        code = [4, 5]
        blocks, basic_data = self._write_basic_loader(code_start, code, False)
        tapfile = self._write_tap(blocks + [[0]])
        output, error = self.run_tap2sna(f'{tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(s_reg))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
        output, error = self.run_tap2sna(f'{tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,26',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,1',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertIn('border=3', s_state)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_preserves_interrupt_mode_and_flip_flop(self):
        code_start = 32768
        code = [
            243,              # 32768 DI
            237, 94,          # 32769 IM 2
            201,              # 32771 RET
        ]
        start = 32771
        tapfile, basic_data = self._write_basic_loader(code_start, code)
        output, error = self.run_tap2sna(f'--start {start} {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,4',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=32771',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertIn('im=2', s_state)
        self.assertIn('iff=0', s_state)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
        output, error = self.run_tap2sna(f'--start 16395 {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadrom',
            'Fast loading data block: 16380,16',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=16395',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual([161, 153, 66, 60], snapshot[32768:32772])
        self.assertEqual(code[4:], snapshot[start + 4:start + len(code)])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=16396', 'IY=23610', 'PC=16395'))
        self.assertLessEqual(exp_reg, set(s_reg))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
        output, error = self.run_tap2sna(f'--start 32784 {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,17',
            'Fast loading data block: 49152,2',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=32784',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        self.assertEqual(code2, snapshot[49152:49152 + len(code2)])
        exp_reg = {'^F=187', 'DE=0', 'SP=65344', 'IX=49154', 'IY=23610', 'PC=32784'}
        self.assertLessEqual(exp_reg, set(s_reg))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
        output, error = self.run_tap2sna(f'--ram call={module_dir}:{module_name}.fix {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual([1, 2, 3, 4], snapshot[32768:32772])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(s_reg))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_with_ram_move(self):
        code_start = 32768
        code = [4, 5]
        tapfile, basic_data = self._write_basic_loader(code_start, code)
        output, error = self.run_tap2sna(f'--ram move=32768,2,32770 {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual([4, 5, 4, 5], snapshot[32768:32772])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(s_reg))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_with_ram_poke(self):
        code_start = 32768
        code = [4, 5]
        tapfile, basic_data = self._write_basic_loader(code_start, code)
        output, error = self.run_tap2sna(f'--ram poke=32768-32770-2,1 {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual([1, 5, 1], snapshot[32768:32771])
        exp_reg = set(('^F=129', 'SP=65344', 'IX=32770', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(s_reg))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_with_ram_sysvars(self):
        code_start = 32768
        code = [4, 5]
        tapfile, basic_data = self._write_basic_loader(code_start, code)
        output, error = self.run_tap2sna(f'--ram sysvars {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,2',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
            'Writing out.z80'
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
        self.assertLessEqual(exp_reg, set(s_reg))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_with_initial_pause_block(self):
        pause_block = [
            32,    # Block ID
            1, 0,  # Pause (1ms)
        ]
        tzxfile = self._write_tzx([
            pause_block,
            create_tzx_header_block("simloadbas", 10, 1, 0),
        ])
        output, error = self.run_tap2sna(f'--start 1343 {tzxfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=1343',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'{tapfile} out.z80')
        out_lines = self.out.getvalue().strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,8',
            'Tape finished'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(cm.exception.args[0], f'Error while converting {tapfile}: Failed to fast load block: unexpected end of tape')
        self.assertEqual(self.err.getvalue(), '')

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_with_tzx_block_type_0x15_first_bit_0(self):
        direct_recording_block = (
            21,          # Block ID
            50, 0,       # T-states per sample
            0, 0,        # Pause
            8,           # Used bits in last byte
            3, 0, 0,     # Data length
            0b00000001,  # Data...
            0b00000010,
            0b00000011
        )
        tzxfile = self._write_tzx([direct_recording_block])
        output, error = self.run_tap2sna(tzxfile)
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 1)
        block = load_tracer.blocks[0]
        self.assertEqual([], block.data)
        self.assertEqual([(1, 350), (1, 50), (1, 300), (1, 50), (1, 350), (1, 100)], block.timings.pulses)

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_with_tzx_block_type_0x15_first_bit_1(self):
        direct_recording_block = (
            21,          # Block ID
            10, 0,       # T-states per sample
            0, 0,        # Pause
            8,           # Used bits in last byte
            3, 0, 0,     # Data length
            0b10000000,  # Data...
            0b00000010,
            0b00000011
        )
        tzxfile = self._write_tzx([direct_recording_block])
        output, error = self.run_tap2sna(tzxfile)
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 1)
        block = load_tracer.blocks[0]
        self.assertEqual([], block.data)
        self.assertEqual([(1, 0), (1, 10), (1, 130), (1, 10), (1, 70), (1, 20)], block.timings.pulses)

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_with_tzx_block_type_0x15_unused_bits_in_last_byte(self):
        direct_recording_block = (
            21,          # Block ID
            100, 0,      # T-states per sample
            0, 0,        # Pause
            4,           # Used bits in last byte
            3, 0, 0,     # Data length
            0b00000001,  # Data...
            0b00000010,
            0b11110000
        )
        tzxfile = self._write_tzx([direct_recording_block])
        output, error = self.run_tap2sna(tzxfile)
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 1)
        block = load_tracer.blocks[0]
        self.assertEqual([], block.data)
        self.assertEqual([(1, 700), (1, 100), (1, 600), (1, 100), (1, 100), (1, 400)], block.timings.pulses)

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_with_tzx_block_type_0x15_followed_by_bytes(self):
        direct_recording_block = (
            21,          # Block ID
            50, 0,       # T-states per sample
            0, 0,        # Pause
            8,           # Used bits in last byte
            1, 0, 0,     # Data length
            0,           # Data
        )
        blocks = [
            direct_recording_block,
            create_tzx_header_block(data_type=3),
            create_tzx_data_block([4, 5, 6]),
        ]
        tzxfile = self._write_tzx(blocks)
        output, error = self.run_tap2sna(tzxfile)
        self.assertEqual(error, '')
        load_cmd = [239, 34, 34, 13] # LOAD "" ENTER
        self.assertEqual(load_cmd, list(load_tracer.simulator.memory[23756:23760]))

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_with_tzx_block_type_0x16(self):
        block = [
            22,         # Block ID
            4, 0, 0, 0, # Block length
            0, 0, 0, 0, # Contents
        ]
        tzxfile = self._write_tzx([block])
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'{tzxfile} out.z80')
        self.assertEqual(cm.exception.args[0], f'Error while converting {tzxfile}: TZX C64 ROM type data (0x16) not supported')
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_with_tzx_block_type_0x17(self):
        block = [
            23,         # Block ID
            4, 0, 0, 0, # Block length
            0, 0, 0, 0, # Contents
        ]
        tzxfile = self._write_tzx([block])
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'{tzxfile} out.z80')
        self.assertEqual(cm.exception.args[0], f'Error while converting {tzxfile}: TZX C64 turbo tape data (0x17) not supported')
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_with_tzx_block_type_0x18(self):
        block = [
            24,          # Block ID
            10, 0, 0, 0, # Block length
            0, 0,        # Pause
            68, 172,     # Sampling rate
            1,           # Compression type
            1, 0, 0, 0,  # Number of stored pulses
            1,           # CSW Data
        ]
        tzxfile = self._write_tzx([block])
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'{tzxfile} out.z80')
        self.assertEqual(cm.exception.args[0], f'Error while converting {tzxfile}: TZX CSW Recording (0x18) not supported')
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_can_ignore_tzx_block_type_0x18(self):
        csw_recording_block = (
            24,          # Block ID
            10, 0, 0, 0, # Block length
            0, 0,        # Pause
            68, 172,     # Sampling rate
            1,           # Compression type
            1, 0, 0, 0,  # Number of stored pulses
            1,           # CSW Data
        )
        tzxfile = self._write_tzx((
            csw_recording_block,
            create_tzx_header_block()
        ))
        output, error = self.run_tap2sna(f'--tape-start 2 {tzxfile}')
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 1)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'{tzxfile} out.z80')
        self.assertEqual(cm.exception.args[0], f'Error while converting {tzxfile}: TZX Generalized Data Block (0x19) not supported')
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')

    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_can_ignore_tzx_block_type_0x19(self):
        generalized_data_block = (
            25,          # Block ID
            14, 0, 0, 0, # Block length
            0, 0,        # Pause
            0, 0, 0, 0,  # Number of symbols in pilot/sync block
            1,           # Maximum number of pulses per pilot/sync symbol
            1,           # Number of pilot/sync symbols in alphabet table
            0, 0, 0, 0,  # Number of symbols in data stream
            1,           # Maximum number of pulses per data symbol
            1,           # Number of data symbols in alphabet table
        )
        tzxfile = self._write_tzx((
            generalized_data_block,
            create_tzx_header_block()
        ))
        output, error = self.run_tap2sna(f'--tape-start 2 {tzxfile}')
        self.assertEqual(error, '')
        self.assertEqual(len(load_tracer.blocks), 1)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
        tracefile = 'sim-load.trace'
        output, error = self.run_tap2sna(f'-c trace={tracefile} {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,18',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        exp_reg = set(('^F=69', 'SP=65344', 'IX=23773', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(s_reg))
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 8101)
        self.assertEqual(trace_lines[0], '$0605 POP AF')
        self.assertEqual(trace_lines[8100], '$34BB RET')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_with_trace_and_self_modifying_code(self):
        code = [
            33, 55, 128,  # 32820 LD HL,32823
            117,          # 32823 LD (HL),L   ; -> 32823 SCF
            48, 253,      # 32824 JR NC,32823
        ]
        tapfile, basic_data = self._write_basic_loader(32820, code)
        tracefile = 'sim-load.trace'
        output, error = self.run_tap2sna(f'--start 32826 -c trace={tracefile} {tapfile} out.z80')
        out_lines = output.strip().split('\n')
        self.assertIn('PC=32826', s_reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 19502)
        self.assertEqual(trace_lines[19497], '$8034 LD HL,$8037')
        self.assertEqual(trace_lines[19498], '$8037 LD (HL),L')
        self.assertEqual(trace_lines[19499], '$8038 JR NC,$8037')
        self.assertEqual(trace_lines[19500], '$8037 SCF')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_with_trace_and_interrupts_and_timestamps(self):
        basic_data = [
            0, 10,             # Line 10
            9, 0,              # Line length
            242,               # PAUSE
            48,                # 0 in ASCII
            14, 0, 0, 0, 0, 0, # 0 in floating point form
            13                 # ENTER
        ]
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
        ]
        tapfile = self._write_tap(blocks)
        tracefile = 'sim-load.trace'
        trace_line = 'TraceLine={t} ${pc:04X} {i}'
        output, error = self.run_tap2sna(('-I', trace_line, '-c', f'trace={tracefile}', '--start', '57', tapfile, 'out.z80'))
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,13',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=57',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        exp_reg = set(('IX=23768', 'IY=23610', 'PC=57'))
        self.assertLessEqual(exp_reg, set(s_reg))
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 11187)
        self.assertEqual(trace_lines[11185], '17891327 $1F3D HALT')
        self.assertEqual(trace_lines[11186], '17891344 $0038 PUSH AF')

    def test_sim_load_config_help(self):
        for option in ('-c', '--sim-load-config'):
            output, error = self.run_tap2sna(f'{option} help')
            self.assertTrue(output.startswith('Usage: --sim-load-config accelerate-dec-a=0/1/2\n'))
            self.assertEqual(error, '')

    def test_sim_load_config_help_specific_parameter(self):
        for param in (
                'accelerate-dec-a', 'accelerator', 'cmio', 'fast-load',
                'finish-tape', 'first-edge', 'in-flags', 'load', 'machine',
                'pause', 'polarity', 'python', 'timeout', 'trace'
        ):
            for option in ('-c', '--sim-load-config'):
                output, error = self.run_tap2sna(f'{option} help-{param}')
                self.assertTrue(output.startswith(f'--sim-load-config {param}='))
                self.assertEqual(error, '')

    def test_sim_load_config_help_invalid_parameter(self):
        for option in ('-c', '--sim-load-config'):
            output, error = self.run_tap2sna(f'{option} help-foo')
            self.assertTrue(output.startswith('Usage: --sim-load-config accelerate-dec-a=0/1/2\n'))
            self.assertEqual(error, '')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_default_state(self):
        block = create_tap_data_block([0])
        tapfile = self._write_tap([block])
        output, error = self.run_tap2sna(f'--ram load=1,16384 {tapfile} out.z80')
        self.assertEqual(error, '')
        self.assertEqual([], s_state)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_state_iff(self):
        block = create_tap_data_block([0])
        tapfile = self._write_tap([block])
        output, error = self.run_tap2sna(f'--ram load=1,16384 --state iff=0 {tapfile} out.z80')
        self.assertEqual(error, '')
        self.assertEqual(['iff=0'], s_state)

    def test_state_iff_bad_value(self):
        self._test_bad_spec('--state iff=fa', 'Cannot parse integer: iff=fa')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_state_im(self):
        block = create_tap_data_block([0])
        tapfile = self._write_tap([block])
        output, error = self.run_tap2sna(f'--ram load=1,16384 --state im=2 {tapfile} out.z80')
        self.assertEqual(error, '')
        self.assertEqual(['im=2'], s_state)

    def test_state_im_bad_value(self):
        self._test_bad_spec('--state im=Q', 'Cannot parse integer: im=Q')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_state_border(self):
        block = create_tap_data_block([0])
        tapfile = self._write_tap([block])
        output, error = self.run_tap2sna(f'--ram load=1,16384 --state border=4 {tapfile} out.z80')
        self.assertEqual(error, '')
        self.assertEqual(['border=4'], s_state)

    def test_state_border_bad_value(self):
        self._test_bad_spec('--state border=x!', 'Cannot parse integer: border=x!')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_state_tstates(self):
        block = create_tap_data_block([0])
        tapfile = self._write_tap([block])
        output, error = self.run_tap2sna(f'--ram load=1,16384 --state tstates=31445 {tapfile} out.z80')
        self.assertEqual(error, '')
        self.assertEqual(['tstates=31445'], s_state)

    def test_state_tstates_bad_value(self):
        self._test_bad_spec('--state tstates=?', 'Cannot parse integer: tstates=?')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_state_issue2(self):
        block = create_tap_data_block([0])
        tapfile = self._write_tap([block])
        for issue2 in (0, 1):
            output, error = self.run_tap2sna(f'--ram load=1,16384 --state issue2={issue2} {tapfile} out.z80')
            self.assertEqual(error, '')
            self.assertEqual([f'issue2={issue2}'], s_state)

    def test_state_issue2_bad_value(self):
        self._test_bad_spec('--state issue2=*', 'Cannot parse integer: issue2=*')

    def test_state_help(self):
        output, error = self.run_tap2sna('--state help')
        self.assertEqual(error, '')
        exp_output = """
            Usage: --state name=value

            Set a hardware state attribute. Recognised names and their default values are:

              7ffd    - last OUT to port 0x7ffd (128K only)
              ay[N]   - contents of AY register N (N=0-15; 128K only)
              border  - border colour (default=0)
              fe      - last OUT to port 0xfe (SZX only)
              fffd    - last OUT to port 0xfffd (128K only)
              iff     - interrupt flip-flop: 0=disabled, 1=enabled (default=1)
              im      - interrupt mode (default=1)
              issue2  - issue 2 emulation: 0=disabled, 1=enabled (default=0)
              tstates - T-states elapsed since start of frame (default=34943)
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    @patch.object(tap2sna, 'KeyboardTracer', MockKeyboardTracer)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_config_parameter_default_values(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        output, error = self.run_tap2sna(tapfile)
        self.assertEqual(error, '')
        self.assertIsNone(kbtracer)
        self.assertIs(load_tracer.simulator.__class__, CSimulator or Simulator)
        self.assertEqual(len(load_tracer.accelerators_in), 46)
        self.assertTrue(load_tracer.pause)
        self.assertEqual(load_tracer.first_edge, 0)
        self.assertEqual(load_tracer.polarity, 0)
        self.assertEqual(load_tracer.finish_tape, 0)
        self.assertEqual(load_tracer.in_min_addr, 0x8000)
        self.assertEqual(load_tracer.accel_dec_a, 1)
        self.assertFalse(load_tracer.list_accelerators)
        self.assertEqual(load_tracer.border, 7)
        self.assertEqual(load_tracer.out7ffd, 0)
        self.assertEqual(load_tracer.outfffd, 0)
        self.assertEqual([0] * 16, load_tracer.ay)
        self.assertEqual(load_tracer.outfe, 0)
        self.assertTrue(load_tracer.run_called)
        self.assertIsNone(load_tracer.stop)
        self.assertEqual(load_tracer.fast_load, 1)
        self.assertEqual(load_tracer.timeout, 3150000000)
        self.assertIsNone(load_tracer.tracefile)
        self.assertIsNone(load_tracer.trace_line)
        self.assertIsNone(load_tracer.prefix)
        self.assertIsNone(load_tracer.byte_fmt)
        self.assertIsNone(load_tracer.word_fmt)

    @patch.object(tap2sna, 'KeyboardTracer', MockKeyboardTracer)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_config_parameters(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        trace_log = 'trace.log'
        params = (
            'accelerate-dec-a=2',
            'accelerator=speedlock',
            'cmio=0',
            'fast-load=0',
            'finish-tape=1',
            'first-edge=1234',
            'in-flags=0',
            'load=RUN',
            'machine=128',
            'pause=0',
            'polarity=1',
            'timeout=1000',
            f'trace={trace_log}'
        )
        options = ' '.join(f'-c {p}' for p in params)
        output, error = self.run_tap2sna(f'{options} {tapfile}')
        self.assertEqual(error, '')
        self.assertEqual(['RUN', 'ENTER'], kbtracer.load)
        self.assertEqual(kbtracer.kb_delay, 13)
        self.assertTrue(kbtracer.run_called)
        self.assertEqual(kbtracer.stop, 0x13BE)
        self.assertEqual(kbtracer.timeout, 3500000000)
        self.assertEqual(kbtracer.tracefile.name, trace_log)
        self.assertEqual(kbtracer.trace_line, '${pc:04X} {i}\n')
        self.assertEqual(kbtracer.prefix, '$')
        self.assertEqual(kbtracer.byte_fmt, '02X')
        self.assertEqual(kbtracer.word_fmt, '04X')
        self.assertIs(load_tracer.simulator.__class__, CSimulator or Simulator)
        self.assertEqual(['speedlock'], [a.name for a in load_tracer.accelerators_in])
        self.assertEqual(load_tracer.pause, 0)
        self.assertEqual(load_tracer.first_edge, 1234)
        self.assertEqual(load_tracer.polarity, 1)
        self.assertEqual(load_tracer.finish_tape, 1)
        self.assertEqual(load_tracer.in_min_addr, 0x8000)
        self.assertEqual(load_tracer.accel_dec_a, 2)
        self.assertFalse(load_tracer.list_accelerators)
        self.assertEqual(load_tracer.border, kbtracer.border)
        self.assertEqual(load_tracer.out7ffd, kbtracer.out7ffd)
        self.assertEqual(load_tracer.outfffd, kbtracer.outfffd)
        self.assertEqual(load_tracer.ay, kbtracer.ay)
        self.assertEqual(load_tracer.outfe, kbtracer.outfe)
        self.assertTrue(load_tracer.run_called)
        self.assertIsNone(load_tracer.stop)
        self.assertEqual(load_tracer.fast_load, 0)
        self.assertTrue(load_tracer.timeout < 3500000000)
        self.assertEqual(load_tracer.tracefile.name, trace_log)
        self.assertEqual(load_tracer.trace_line, '${pc:04X} {i}\n')
        self.assertEqual(load_tracer.prefix, '$')
        self.assertEqual(load_tracer.byte_fmt, '02X')
        self.assertEqual(load_tracer.word_fmt, '04X')

    @patch.object(tap2sna, 'CSimulator', MockSimulator)
    @patch.object(tap2sna, 'Simulator', MockSimulator)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_enables_fast_djnz_ldir(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        output, error = self.run_tap2sna(tapfile)
        self.assertEqual(error, '')
        self.assertTrue(simulator.config.get('fast_djnz'))
        self.assertTrue(simulator.config.get('fast_ldir'))

    @patch.object(tap2sna, 'CSimulator', MockSimulator)
    @patch.object(tap2sna, 'Simulator', MockSimulator)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_sim_load_disables_fast_djnz_ldir_when_tracing(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        output, error = self.run_tap2sna(f'-c trace=load.log {tapfile}')
        self.assertEqual(error, '')
        self.assertFalse(simulator.config.get('fast_djnz'))
        self.assertFalse(simulator.config.get('fast_ldir'))

    @patch.object(tap2sna, 'KeyboardTracer', MockKeyboardTracer)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_cmio_1_disables_acceleration(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        trace_log = 'trace.log'
        params = (
            'accelerate-dec-a=2',
            'accelerator=speedlock',
            'cmio=1'
        )
        options = ' '.join(f'-c {p}' for p in params)
        output, error = self.run_tap2sna(f'{options} {tapfile}')
        self.assertEqual(error, '')
        self.assertIs(load_tracer.simulator.__class__, CCMIOSimulator or CMIOSimulator)
        self.assertEqual(set(), load_tracer.accelerators_in)
        self.assertEqual(load_tracer.accel_dec_a, 0)

    @patch.object(tap2sna, 'CSimulator', MockSimulator)
    @patch.object(tap2sna, 'Simulator', MockSimulator)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_in_flags_parameter_bit_0(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        output, error = self.run_tap2sna(f'-c in-flags=1 {tapfile}')
        self.assertEqual(error, '')
        self.assertEqual(load_tracer.in_min_addr, 0x4000)
        set_tracer_args = load_tracer.simulator.set_tracer_args
        self.assertFalse(set_tracer_args[0])
        self.assertFalse(set_tracer_args[1])

    @patch.object(tap2sna, 'CSimulator', MockSimulator)
    @patch.object(tap2sna, 'Simulator', MockSimulator)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_in_flags_parameter_bit_1(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        output, error = self.run_tap2sna(f'-c in-flags=2 {tapfile}')
        self.assertEqual(error, '')
        self.assertEqual(load_tracer.in_min_addr, 0x10000)
        set_tracer_args = load_tracer.simulator.set_tracer_args
        self.assertFalse(set_tracer_args[0])
        self.assertFalse(set_tracer_args[1])

    @patch.object(tap2sna, 'CSimulator', MockSimulator)
    @patch.object(tap2sna, 'Simulator', MockSimulator)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_in_flags_parameter_bit_2(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        output, error = self.run_tap2sna(f'-c in-flags=4 {tapfile}')
        self.assertEqual(error, '')
        self.assertEqual(load_tracer.in_min_addr, 0x8000)
        set_tracer_args = load_tracer.simulator.set_tracer_args
        self.assertTrue(set_tracer_args[0])
        self.assertFalse(set_tracer_args[1])

    @patch.object(tap2sna, 'KeyboardTracer', MockKeyboardTracer)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_load_parameter_defaults_to_enter_for_128k(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        output, error = self.run_tap2sna(f'-c machine=128 {tapfile}')
        self.assertEqual(error, '')
        self.assertEqual(['ENTER'], kbtracer.load)

    @patch.object(tap2sna, 'KeyboardTracer', MockKeyboardTracer)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_load_parameter_with_pc(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        output, error = self.run_tap2sna(f'-c load=PC=16384 {tapfile}')
        self.assertEqual(error, '')
        self.assertEqual(['ENTER'], kbtracer.load)
        self.assertTrue(kbtracer.run_called)
        self.assertEqual(kbtracer.stop, 16384)

    @patch.object(tap2sna, 'KeyboardTracer', MockKeyboardTracer)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_keyboard_tracer_config_for_48k(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        output, error = self.run_tap2sna(f'-c load=RUN {tapfile}')
        self.assertEqual(error, '')
        self.assertEqual(len(kbtracer.simulator.memory), 65536)
        self.assertEqual(['RUN', 'ENTER'], kbtracer.load)
        self.assertEqual(kbtracer.kb_delay, 4)
        self.assertTrue(kbtracer.run_called)
        self.assertEqual(kbtracer.stop, 0x0605)

    @patch.object(tap2sna, 'KeyboardTracer', MockKeyboardTracer)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_keyboard_tracer_config_for_128k(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        output, error = self.run_tap2sna(f'-c machine=128 {tapfile}')
        self.assertEqual(error, '')
        self.assertEqual(len(kbtracer.simulator.memory), 0x20000)
        self.assertEqual(['ENTER'], kbtracer.load)
        self.assertEqual(kbtracer.kb_delay, 13)
        self.assertTrue(kbtracer.run_called)
        self.assertEqual(kbtracer.stop, 0x13BE)

    @patch.object(tap2sna, 'Simulator', MockSimulator)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_python_parameter(self):
        global mock_memory
        mock_memory = [1] * 65536
        tapfile = self._write_tap([create_tap_data_block([0])])
        output, error = self.run_tap2sna(f'-c python=1 {tapfile}')
        self.assertEqual(error, '')
        self.assertIs(load_tracer.simulator.__class__, MockSimulator)

    @patch.object(tap2sna, 'CMIOSimulator', MockSimulator)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_python_parameter_with_cmio(self):
        global mock_memory
        mock_memory = [1] * 65536
        tapfile = self._write_tap([create_tap_data_block([0])])
        output, error = self.run_tap2sna(f'-c python=1 -c cmio=1 {tapfile}')
        self.assertEqual(error, '')
        self.assertIs(load_tracer.simulator.__class__, MockSimulator)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_empty_tape(self):
        tapfile = self._write_tap([])
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(tapfile)
        self.assertEqual(cm.exception.args[0], f"Error while converting {tapfile}: Tape is empty")

    def test_load_parameter_with_invalid_pc(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tap2sna(f'-c load=PC=? {tapfile}')
        self.assertEqual(cm.exception.args[0], f"Error while converting {tapfile}: Invalid integer in 'load' parameter: PC=?")

    @patch.object(tap2sna, 'KeyboardTracer', MockKeyboardTracer)
    @patch.object(tap2sna, 'LoadTracer', MockLoadTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_keyboard_tracer_timed_out(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        load = ' '.join(['a'] * 50)
        output, error = self.run_tap2sna(('-c', 'timeout=1', '-c', f'load={load}', tapfile))
        self.assertEqual(error, '')
        self.assertTrue(kbtracer.run_called)
        self.assertEqual(kbtracer.timeout, 3500000)
        self.assertIn('Simulation stopped (timed out): PC=4608\n', output)

    @patch.object(tap2sna, 'KeyboardTracer', InterruptedTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_interrupted_keyboard_tracer(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        output, error = self.run_tap2sna(f'-c load=RUN {tapfile}')
        self.assertEqual(error, '')
        self.assertIn('Simulation stopped (interrupted): PC=4608\n', output)

    @patch.object(tap2sna, 'LoadTracer', InterruptedTracer)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_interrupted_load_tracer(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        output, error = self.run_tap2sna(tapfile)
        self.assertEqual(error, '')
        self.assertIn('Simulation stopped (interrupted): PC=1541\n', output)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_config_DefaultSnapshotFormat_read_from_file(self):
        ini = """
            [tap2sna]
            DefaultSnapshotFormat=szx
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        tapfile = self._write_tap([create_tap_data_block([0])])
        exp_outfile = tapfile[:-4] + '.szx'
        output, error = self.run_tap2sna(f'--ram load=1,16384 {tapfile}')
        self.assertEqual(len(error), 0)
        self.assertEqual(s_fname, exp_outfile)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_config_DefaultSnapshotFormat_set_on_command_line(self):
        tapfile = self._write_tap([create_tap_data_block([0])])
        exp_outfile = tapfile[:-4] + '.szx'
        output, error = self.run_tap2sna(f'--ram load=1,16384 -I DefaultSnapshotFormat=szx {tapfile}')
        self.assertEqual(len(error), 0)
        self.assertEqual(s_fname, exp_outfile)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
        tracefile = 'sim-load.trace'
        output, error = self.run_tap2sna(f'-c trace={tracefile} --start 1343 -c finish-tape=1 {tapfile} out.z80')
        self.assertEqual(error, '')
        self.assertIn('PC=1343', s_reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 7281)
        self.assertEqual(trace_lines[0], '01541: POP AF')
        self.assertEqual(trace_lines[7280], '01506: RET')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
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
        tracefile = 'sim-load.trace'
        trace_line = '{pc:>5}:{i}'
        args = f'-I TraceLine={trace_line} -c trace={tracefile} --start 1343 -c finish-tape=1 {tapfile} out.z80'
        output, error = self.run_tap2sna(args)
        self.assertEqual(error, '')
        self.assertIn('PC=1343', s_reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 7281)
        self.assertEqual(trace_lines[0], ' 1541:POP AF')
        self.assertEqual(trace_lines[7280], ' 1506:RET')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_config_TraceLine_with_register_values(self):
        tapfile = self._write_tap([create_tap_header_block("prog", 10, 1, 0)])
        tracefile = 'sim-load.trace'
        trace_line = "{t:>3} ${pc:04X} {i:<13} AFBCDEHL={r[a]:02X}{r[f]:02X}{r[b]:02X}{r[c]:02X}{r[d]:02X}{r[e]:02X}{r[h]:02X}{r[l]:02X}"
        trace_line += " AFBCDEHL'={r[^a]:02X}{r[^f]:02X}{r[^b]:02X}{r[^c]:02X}{r[^d]:02X}{r[^e]:02X}{r[^h]:02X}{r[^l]:02X}"
        trace_line += " IX={r[ixh]:02X}{r[ixl]:02X} IY={r[iyh]:02X}{r[iyl]:02X} SP={r[sp]:04X} IR={r[i]:02X}{r[r]:02X}"
        args = ('-I', f'TraceLine={trace_line}', '-c', f'trace={tracefile}', '--start', '0x250E', tapfile, 'out.z80')
        tap2sna.main(args)
        self.assertEqual(self.err.getvalue(), '')
        self.assertIn('PC=9486', s_reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 31)
        self.assertEqual(trace_lines[0], "  0 $0605 POP AF        AFBCDEHL=1B52000000000000 AFBCDEHL'=0000000000000000 IX=0000 IY=5C3A SP=FF52 IR=3F01")
        self.assertEqual(trace_lines[1], " 10 $0606 LD A,($5C74)  AFBCDEHL=E152000000000000 AFBCDEHL'=0000000000000000 IX=0000 IY=5C3A SP=FF52 IR=3F02")
        self.assertEqual(trace_lines[2], " 23 $0609 SUB $E0       AFBCDEHL=0102000000000000 AFBCDEHL'=0000000000000000 IX=0000 IY=5C3A SP=FF52 IR=3F03")
        self.assertEqual(trace_lines[28], "267 $250A LD B,$00      AFBCDEHL=2261002200002597 AFBCDEHL'=0000000000000000 IX=0000 IY=5C3A SP=FF4C IR=3F1D")
        self.assertEqual(trace_lines[29], "274 $250C LD C,(HL)     AFBCDEHL=2261001C00002597 AFBCDEHL'=0000000000000000 IX=0000 IY=5C3A SP=FF4C IR=3F1E")
        self.assertEqual(trace_lines[30], "281 $250D ADD HL,BC     AFBCDEHL=2260001C000025B3 AFBCDEHL'=0000000000000000 IX=0000 IY=5C3A SP=FF4C IR=3F1F")

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_config_TraceLine_with_register_pairs(self):
        tapfile = self._write_tap([create_tap_header_block("prog", 10, 1, 0)])
        tracefile = 'sim-load.trace'
        trace_line = "${pc:04X} {i:<13} BCDEHL={r[bc]:04X}{r[de]:04X}{r[hl]:04X}"
        trace_line += " BCDEHL'={r[^bc]:04X}{r[^de]:04X}{r[^hl]:04X}"
        trace_line += " IX={r[ix]:04X} IY={r[iy]:04X}"
        args = ('-I', f'TraceLine={trace_line}', '-c', f'trace={tracefile}', '--start', '0x250E', tapfile, 'out.z80')
        tap2sna.main(args)
        self.assertEqual(self.err.getvalue(), '')
        self.assertIn('PC=9486', s_reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 31)
        self.assertEqual(trace_lines[0], "$0605 POP AF        BCDEHL=000000000000 BCDEHL'=000000000000 IX=0000 IY=5C3A")
        self.assertEqual(trace_lines[1], "$0606 LD A,($5C74)  BCDEHL=000000000000 BCDEHL'=000000000000 IX=0000 IY=5C3A")
        self.assertEqual(trace_lines[2], "$0609 SUB $E0       BCDEHL=000000000000 BCDEHL'=000000000000 IX=0000 IY=5C3A")
        self.assertEqual(trace_lines[28], "$250A LD B,$00      BCDEHL=002200002597 BCDEHL'=000000000000 IX=0000 IY=5C3A")
        self.assertEqual(trace_lines[29], "$250C LD C,(HL)     BCDEHL=001C00002597 BCDEHL'=000000000000 IX=0000 IY=5C3A")
        self.assertEqual(trace_lines[30], "$250D ADD HL,BC     BCDEHL=001C000025B3 BCDEHL'=000000000000 IX=0000 IY=5C3A")

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_config_TraceLine_with_memory_contents(self):
        tapfile = self._write_tap([create_tap_header_block("prog", 10, 1, 0)])
        tracefile = 'sim-load.trace'
        trace_line = "${pc:04X} {i:<13} (23668)={m[23668]}"
        args = ('-I', f'TraceLine={trace_line}', '-c', f'trace={tracefile}', '--start', '0x060E', tapfile, 'out.z80')
        exp_trace = """
            $0605 POP AF        (23668)=225
            $0606 LD A,($5C74)  (23668)=225
            $0609 SUB $E0       (23668)=225
            $060B LD ($5C74),A  (23668)=1
        """
        tap2sna.main(args)
        self.assertEqual(self.err.getvalue(), '')
        self.assertIn('PC=1550', s_reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip()
        self.assertEqual(dedent(exp_trace).strip(), trace_lines)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_config_TraceLine_with_memory_contents_using_hex_address(self):
        tapfile = self._write_tap([create_tap_header_block("prog", 10, 1, 0)])
        tracefile = 'sim-load.trace'
        trace_line = "${pc:04X} {i:<13} ($5C74)=${m[$5c74]:02X}"
        args = ('-I', f'TraceLine={trace_line}', '-c', f'trace={tracefile}', '--start', '0x060E', tapfile, 'out.z80')
        exp_trace = """
            $0605 POP AF        ($5C74)=$E1
            $0606 LD A,($5C74)  ($5C74)=$E1
            $0609 SUB $E0       ($5C74)=$E1
            $060B LD ($5C74),A  ($5C74)=$01
        """
        tap2sna.main(args)
        self.assertEqual(self.err.getvalue(), '')
        self.assertIn('PC=1550', s_reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip()
        self.assertEqual(dedent(exp_trace).strip(), trace_lines)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_config_TraceLine_with_memory_contents_using_0x_prefixed_hex_address(self):
        tapfile = self._write_tap([create_tap_header_block("prog", 10, 1, 0)])
        tracefile = 'sim-load.trace'
        trace_line = "${pc:04X} {i:<13} (0x5C74)=0x{m[0x5c74]:02X}"
        args = ('-I', f'TraceLine={trace_line}', '-c', f'trace={tracefile}', '--start', '0x060E', tapfile, 'out.z80')
        exp_trace = """
            $0605 POP AF        (0x5C74)=0xE1
            $0606 LD A,($5C74)  (0x5C74)=0xE1
            $0609 SUB $E0       (0x5C74)=0xE1
            $060B LD ($5C74),A  (0x5C74)=0x01
        """
        tap2sna.main(args)
        self.assertEqual(self.err.getvalue(), '')
        self.assertIn('PC=1550', s_reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip()
        self.assertEqual(dedent(exp_trace).strip(), trace_lines)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_config_TraceLine_with_memory_contents_using_escaped_braces(self):
        tapfile = self._write_tap([create_tap_header_block("prog", 10, 1, 0)])
        tracefile = 'sim-load.trace'
        trace_line = "${pc:04X} {i:<13} {{m[0x5C74]}}={{{m[0x5c74]:02X}}}"
        args = ('-I', f'TraceLine={trace_line}', '-c', f'trace={tracefile}', '--start', '0x060E', tapfile, 'out.z80')
        exp_trace = """
            $0605 POP AF        {m[0x5C74]}={E1}
            $0606 LD A,($5C74)  {m[0x5C74]}={E1}
            $0609 SUB $E0       {m[0x5C74]}={E1}
            $060B LD ($5C74),A  {m[0x5C74]}={01}
        """
        tap2sna.main(args)
        self.assertEqual(self.err.getvalue(), '')
        self.assertIn('PC=1550', s_reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip()
        self.assertEqual(dedent(exp_trace).strip(), trace_lines)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_config_TraceOperand(self):
        tapfile = self._write_tap([create_tap_header_block("prog", 10, 1, 0)])
        tracefile = 'sim-load.trace'
        args = f'-I TraceOperand=&,02x,04x -c trace={tracefile} --start 1343 {tapfile} out.z80'
        output, error = self.run_tap2sna(args)
        self.assertEqual(error, '')
        self.assertIn('PC=1343', s_reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 2265)
        self.assertEqual(trace_lines[1], '$0606 LD A,(&5c74)')
        self.assertEqual(trace_lines[2], '$0609 SUB &e0')
        self.assertEqual(trace_lines[2264], '$05E2 RET')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_config_TraceOperand_with_no_commas(self):
        tapfile = self._write_tap([create_tap_header_block("prog", 1, 1, 0)])
        tracefile = 'sim-load.trace'
        args = f'-I TraceOperand=# -c trace={tracefile} --start 1547 {tapfile} out.z80'
        output, error = self.run_tap2sna(args)
        self.assertEqual(error, '')
        self.assertIn('PC=1547', s_reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 3)
        self.assertEqual(trace_lines[1], '$0606 LD A,(#23668)')
        self.assertEqual(trace_lines[2], '$0609 SUB #224')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_config_TraceOperand_with_one_comma(self):
        tapfile = self._write_tap([create_tap_header_block("prog", 1, 1, 0)])
        tracefile = 'sim-load.trace'
        args = f'-I TraceOperand=+,02x -c trace={tracefile} --start 1547 {tapfile} out.z80'
        output, error = self.run_tap2sna(args)
        self.assertEqual(error, '')
        self.assertIn('PC=1547', s_reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 3)
        self.assertEqual(trace_lines[1], '$0606 LD A,(+23668)')
        self.assertEqual(trace_lines[2], '$0609 SUB +e0')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_config_TraceOperand_with_three_commas(self):
        tapfile = self._write_tap([create_tap_header_block("prog", 1, 1, 0)])
        tracefile = 'sim-load.trace'
        args = f'-I TraceOperand=0x,02x,04x,??? -c trace={tracefile} --start 1547 {tapfile} out.z80'
        output, error = self.run_tap2sna(args)
        self.assertEqual(error, '')
        self.assertIn('PC=1547', s_reg)
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 3)
        self.assertEqual(trace_lines[1], '$0606 LD A,(0x5c74)')
        self.assertEqual(trace_lines[2], '$0609 SUB 0xe0')

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_args_from_file(self):
        data = [1, 2, 3, 4]
        start = 49152
        args = f"""
            ; Comment
            # Another comment
            --ram load=1,{start} # Load first block
            --ram poke=32768,255 ; POKE 32768,255
        """
        args_file = self.write_text_file(dedent(args).strip(), suffix='.t2s')
        self._load_tape(start, data, f'@{args_file}')
        self.assertEqual(data, snapshot[start:start + len(data)])
        self.assertEqual(snapshot[32768], 255)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_quoted_args_from_file(self):
        code = [1, 2, 3]
        code_start = 24576
        tap_data = create_tap_data_block(code)
        tapfile = self.write_bin_file(tap_data, 'all the data.tap')
        z80file = 'my snapshot.z80'
        args = f"""
            --ram load=1,{code_start}
            --ram poke=32768,255
            "{tapfile}"
            '{z80file}'
        """
        args_file = self.write_text_file(dedent(args).strip(), suffix='.t2s')
        output, error = self.run_tap2sna(f'@{args_file}')
        self.assertEqual(error, '')
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        self.assertEqual(snapshot[32768], 255)

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_t2s_file_with_default_snapshot_filename(self):
        code = [3, 2, 1]
        code_start = 32768
        tap_data = create_tap_data_block(code)
        tapfile = self.write_bin_file(tap_data)
        args = f"""
            "{tapfile}"
            --ram load=1,{code_start}
        """
        args_file = self.write_text_file(dedent(args).strip(), suffix='.t2s')
        exp_z80 = f'{args_file[:-4]}.z80'
        output, error = self.run_tap2sna(f'@{args_file}')
        self.assertEqual(error, '')
        self.assertEqual(s_fname, exp_z80)
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_t2s_file_in_subdirectory_with_default_snapshot_filename(self):
        code = [3, 2, 1]
        code_start = 32768
        tap_data = create_tap_data_block(code)
        tapfile = self.write_bin_file(tap_data)
        args = f"""
            "{tapfile}"
            --ram load=1,{code_start}
        """
        subdir = 'foo/bar/baz'
        t2s_name = 'game'
        os.makedirs(subdir)
        args_file = self.write_text_file(dedent(args).strip(), f'{subdir}/{t2s_name}.t2s')
        exp_z80 = f'{t2s_name}.z80'
        output, error = self.run_tap2sna(f'@{args_file}')
        self.assertEqual(error, '')
        self.assertEqual(s_fname, exp_z80)
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_t2s_file_with_default_snapshot_filename_in_szx_format(self):
        code = [3, 2, 1]
        code_start = 32768
        tap_data = create_tap_data_block(code)
        tapfile = self.write_bin_file(tap_data)
        args = f"""
            "{tapfile}"
            --ram load=1,{code_start}
            --ini DefaultSnapshotFormat=szx
        """
        args_file = self.write_text_file(dedent(args).strip(), suffix='.t2s')
        exp_szx = f'{args_file[:-4]}.szx'
        output, error = self.run_tap2sna(f'@{args_file}')
        self.assertEqual(error, '')
        self.assertEqual(s_fname, exp_szx)
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])

    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_t2s_file_with_snapshot_filename_given_on_command_line(self):
        code = [3, 2, 1]
        code_start = 32768
        tap_data = create_tap_data_block(code)
        tapfile = self.write_bin_file(tap_data)
        args = f"""
            "{tapfile}"
            --ram load=1,{code_start}
        """
        args_file = self.write_text_file(dedent(args).strip(), suffix='.t2s')
        output, error = self.run_tap2sna(f'@{args_file} out.z80')
        self.assertEqual(error, '')
        self.assertEqual(s_fname, 'out.z80')
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])

    @patch.object(tap2sna, 'urlopen', Mock(return_value=BytesIO(bytearray(create_tap_data_block([2, 3])))))
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_remote_download(self):
        data = [2, 3]
        start = 17000
        url = 'http://example.com/test.tap'
        output, error = self.run_tap2sna(f'--ram load=1,{start} {url} test.z80')
        self.assertTrue(output.startswith(f'Downloading {url}\n'))
        self.assertEqual(error, '')
        self.assertEqual(data, snapshot[start:start + len(data)])

    @patch.object(tap2sna, 'urlopen', Mock(side_effect=urllib.error.HTTPError('', 403, 'Forbidden', None, None)))
    def test_http_error_on_remote_download(self):
        with self.assertRaisesRegex(SkoolKitError, '^Error while converting test.zip: HTTP Error 403: Forbidden$'):
            self.run_tap2sna('http://example.com/test.zip test.z80')

    @patch.object(tap2sna, 'CSimulator', MockSimulator)
    @patch.object(tap2sna, 'Simulator', MockSimulator)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_dec_a_jr(self):
        global mock_memory
        mock_memory = [0] * 65536
        code = (
            0x3D,       # $C000 DEC A
            0x20, 0xFD, # $C001 JR NZ,$C000
        )
        mock_memory[0xC000:0xC000 + len(code)] = code
        tapfile = self._write_tap([create_tap_header_block('bytes', 32768, 1)])
        output, error = self.run_tap2sna(f'{tapfile} out.z80')
        exp_out_lines = [
            'Data (19 bytes)',
            'Tape finished',
            'Simulation stopped (end of tape): PC=49158',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, self._format_output(output))
        self.assertEqual(error, '')
        self.assertEqual(simulator.registers[0], 0)

    @patch.object(tap2sna, 'CSimulator', MockSimulator)
    @patch.object(tap2sna, 'Simulator', MockSimulator)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_dec_a_jp(self):
        global mock_memory
        mock_memory = [0] * 65536
        code = (
            0x3D,             # $C000 DEC A
            0x3D,             # $C001 DEC A
            0xC2, 0x01, 0xC0, # $C002 JP NZ,$C001
        )
        mock_memory[0xC000:0xC000 + len(code)] = code
        tapfile = self._write_tap([create_tap_header_block('bytes', 32768, 1)])
        output, error = self.run_tap2sna(f'-c accelerate-dec-a=2 {tapfile} out.z80')
        exp_out_lines = [
            'Data (19 bytes)',
            'Tape finished',
            'Simulation stopped (end of tape): PC=49160',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, self._format_output(output))
        self.assertEqual(error, '')
        self.assertEqual(simulator.registers[0], 0)

    @patch.object(tap2sna, 'CSimulator', MockSimulator)
    @patch.object(tap2sna, 'Simulator', MockSimulator)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_dec_b(self):
        global mock_memory
        mock_memory = [0] * 65536
        code = (
            0x05,             # $C000 DEC B
            0xC8,             # $C001 RET Z
            0xDB, 0xFE,       # $C002 IN A,($FE)
            0xA9,             # $C004 XOR C
            0xE6, 0x40,       # $C005 AND $40
            0xCA, 0x01, 0x80  # $C007 JP Z,$C000
        )
        mock_memory[0xC000:0xC000 + len(code)] = code
        tapfile = self._write_tap([create_tap_header_block('bytes', 32768, 1)])
        output, error = self.run_tap2sna(f'-c accelerator=digital-integration {tapfile} out.z80')
        exp_out_lines = [
            'Data (19 bytes)',
            'Tape finished',
            'Simulation stopped (end of tape): PC=49165',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, self._format_output(output))
        self.assertEqual(error, '')
        self.assertEqual(simulator.registers[2], 98)

    @patch.object(tap2sna, 'LoadTracer', TestLoadTracer)
    @patch.object(tap2sna, 'CSimulator', MockSimulator)
    @patch.object(tap2sna, 'Simulator', MockSimulator)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_dec_b_auto(self):
        global mock_memory
        mock_memory = [0] * 65536
        code = (
            0x3E, 0x7F, # $C000 LD A,$7F
            0xDB, 0xFE, # $C002 IN A,($FE)
            0xA9,       # $C004 XOR C
            0xE6, 0x40, # $C005 AND $40
            0x20, 0x04, # $C007 JR NZ,$C00C
            0x05,       # $C009 DEC B
            0x20, 0xF4  # $C00A JR NZ,$C000
        )
        mock_memory[0xC000:0xC000 + len(code)] = code
        tapfile = self._write_tap([create_tap_header_block('bytes', 32768, 1)])
        output, error = self.run_tap2sna(f'{tapfile} out.z80')
        exp_out_lines = [
            'Data (19 bytes)',
            'Tape finished',
            'Simulation stopped (end of tape): PC=49167',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, self._format_output(output))
        self.assertEqual(error, '')
        self.assertEqual(simulator.registers[2], 93)

    @patch.object(tap2sna, 'CSimulator', MockSimulator)
    @patch.object(tap2sna, 'Simulator', MockSimulator)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_inc_b(self):
        global mock_memory
        mock_memory = [0] * 65536
        code = (
            0x04,       # $C000 INC B
            0xC8,       # $C001 RET Z
            0xDB, 0xFE, # $C002 IN A,($FE)
            0xA9,       # $C004 XOR C
            0xE6, 0x40, # $C005 AND $40
            0x28, 0xF7  # $C007 JR Z,$C000
        )
        mock_memory[0xC000:0xC000 + len(code)] = code
        tapfile = self._write_tap([create_tap_header_block('bytes', 32768, 1)])
        output, error = self.run_tap2sna(f'-c accelerator=tiny {tapfile} out.z80')
        exp_out_lines = [
            'Data (19 bytes)',
            'Tape finished',
            'Simulation stopped (end of tape): PC=49164',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, self._format_output(output))
        self.assertEqual(error, '')
        self.assertEqual(simulator.registers[2], 156)

    @patch.object(tap2sna, 'CSimulator', MockSimulator)
    @patch.object(tap2sna, 'Simulator', MockSimulator)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_inc_b_none(self):
        global mock_memory
        mock_memory = [0] * 65536
        code = (
            0x04,             # $C000 INC B
            0x20, 0x03,       # $C001 JR NZ,$C007
            0x00, 0x00, 0x00, # $C003 DEFS 3
            0xDB, 0xFE,       # $C006 IN A,($FE)
            0x1F,             # $C008 RRA
            0xC8,             # $C009 RET Z
            0xA9,             # $C00A XOR C
            0xE6, 0x20,       # $C00B AND $20
            0x28, 0xF1        # $C00D JR Z,$C000
        )
        mock_memory[0xC000:0xC000 + len(code)] = code
        tapfile = self._write_tap([create_tap_header_block('bytes', 32768, 1)])
        output, error = self.run_tap2sna(f'-c accelerator=alkatraz {tapfile} out.z80')
        exp_out_lines = [
            'Data (19 bytes)',
            'Tape finished',
            'Simulation stopped (end of tape): PC=49170',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, self._format_output(output))
        self.assertEqual(error, '')
        self.assertEqual(simulator.registers[2], 149)

    @patch.object(tap2sna, 'LoadTracer', TestLoadTracer)
    @patch.object(tap2sna, 'CSimulator', MockSimulator)
    @patch.object(tap2sna, 'Simulator', MockSimulator)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_inc_b_auto(self):
        global mock_memory
        mock_memory = [0] * 65536
        code = (
            0x04,       # $C000 INC B
            0xC8,       # $C001 RET Z
            0xDB, 0xFE, # $C002 IN A,($FE)
            0xA9,       # $C004 XOR C
            0xE6, 0x40, # $C005 AND $40
            0x28, 0xF7  # $C007 JR Z,$C000
        )
        mock_memory[0xC000:0xC000 + len(code)] = code
        tapfile = self._write_tap([create_tap_header_block('bytes', 32768, 1)])
        output, error = self.run_tap2sna(f'{tapfile} out.z80')
        exp_out_lines = [
            'Data (19 bytes)',
            'Tape finished',
            'Simulation stopped (end of tape): PC=49164',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, self._format_output(output))
        self.assertEqual(error, '')
        self.assertEqual(simulator.registers[2], 156)

    @patch.object(tap2sna, 'CSimulator', MockSimulator)
    @patch.object(tap2sna, 'Simulator', MockSimulator)
    @patch.object(tap2sna, 'write_snapshot', mock_write_snapshot)
    def test_list_accelerators(self):
        global mock_memory
        mock_memory = [0] * 65536
        code = (
            0x04,             # $C000 INC B
            0xC8,             # $C001 RET Z
            0xDB, 0xFE,       # $C002 IN A,($FE)
            0xA9,             # $C004 XOR C
            0xE6, 0x40,       # $C005 AND $40
            0x28, 0xF7,       # $C007 JR Z,$C000
            0x04,             # $C009 INC B       ; INC B miss
            0x05,             # $C00A DEC B       ; DEC B miss
            0x3D,             # $C00B DEC A       ; DEC A miss
            0x3D,             # $C00C DEC A       ; DEC A; JR NZ,$-1 hit
            0x20, 0xFD,       # $C00D JR NZ,$C00C ;
            0x3D,             # $C00F DEC A       ; DEC A; JP NZ,$-1 hit
            0xC2, 0x0F, 0xC0, # $C010 JP NZ,$C00F ;
        )
        mock_memory[0xC000:0xC000 + len(code)] = code
        tapfile = self._write_tap([create_tap_header_block('bytes', 32768, 1)])
        output, error = self.run_tap2sna(f'-c accelerator=list {tapfile} out.z80')
        exp_out_lines = [
            'Data (19 bytes)',
            'Tape finished',
            'Simulation stopped (end of tape): PC=49174',
            'Accelerators: tiny: 1; misses: 1/1; dec-a: 1/1/1',
            'Writing out.z80'
        ]
        self.assertEqual(exp_out_lines, self._format_output(output))
        self.assertEqual(error, '')
        self.assertEqual(simulator.registers[0], 255)
        self.assertEqual(simulator.registers[2], 156)
