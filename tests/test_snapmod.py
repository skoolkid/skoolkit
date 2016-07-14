# -*- coding: utf-8 -*-
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError, snapmod, read_bin_file, VERSION
from skoolkit.snapshot import get_snapshot

def mock_run(*args):
    global run_args
    run_args = args

class SnapmodTest(SkoolKitTestCase):
    def _test_z80(self, options, header, exp_header=None, ram=None, exp_ram=None, version=3, compress=False):
        if exp_header is None:
            exp_header = header
        if ram is None:
            ram = [0] * 49152
        if exp_ram is None:
            exp_ram = ram
        infile = self.write_z80_file(header, ram, version, compress)
        outfile = self.write_bin_file(suffix='.z80')
        output, error = self.run_snapmod('-f {} {} {}'.format(options, infile, outfile))
        self.assertEqual([], output)
        self.assertEqual(error, '')
        z80_header = list(read_bin_file(outfile, len(exp_header)))
        self.assertEqual(exp_header, z80_header)
        z80_ram = get_snapshot(outfile)[16384:]
        self.assertEqual(exp_ram, z80_ram)

    def test_no_arguments(self):
        output, error = self.run_snapmod(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: snapmod.py'))

    def test_invalid_option(self):
        output, error = self.run_snapmod('-x test.z80', catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: snapmod.py'))

    def test_unrecognised_snapshot_type(self):
        with self.assertRaisesRegexp(SkoolKitError, 'Unrecognised input snapshot type$'):
            self.run_snapmod('unknown.snap')

    def test_no_clobber_input_file(self):
        infile = self.write_bin_file(suffix='.z80')
        output, error = self.run_snapmod('-p 16384,0 {}'.format(infile))
        self.assertEqual(output[0], '{}: file already exists; use -f to overwrite'.format(infile))
        self.assertEqual(error, '')

    def test_no_clobber_output_file(self):
        outfile = self.write_bin_file(suffix='.z80')
        output, error = self.run_snapmod('-p 16384,0 in.z80 {}'.format(outfile))
        self.assertEqual(output[0], '{}: file already exists; use -f to overwrite'.format(outfile))
        self.assertEqual(error, '')

    @patch.object(snapmod, 'run', mock_run)
    def test_options_m_move(self):
        for option in ('-m', '--move'):
            output, error = self.run_snapmod('{0} 30000,10,40000 {0} 50000,20,60000 test.z80'.format(option))
            self.assertEqual([], output)
            self.assertEqual(error, '')
            infile, options, outfile = run_args
            self.assertEqual(['30000,10,40000', '50000,20,60000'], options.moves)

    def test_option_m_z80v1(self):
        src, size, dest = 30000, 10, 40000
        header = list(range(30))
        header[12] &= 223 # RAM block uncompressed
        ram = [0] * 49152
        block = [1] * size
        ram[src - 16384:src - 16384 + size] = block
        exp_ram = ram[:]
        exp_ram[dest - 16384:dest - 16384 + size] = block
        exp_header = header[:]
        exp_header[12] |= 32 # RAM block compressed
        options = '-m {},{},{}'.format(src, size, dest)
        self._test_z80(options, header, exp_header, ram, exp_ram, 1, False)

    @patch.object(snapmod, 'run', mock_run)
    def test_options_p_poke(self):
        for option in ('-p', '--poke'):
            output, error = self.run_snapmod('{0} 32768,1 {0} 40000-40010,2 test.z80'.format(option))
            self.assertEqual([], output)
            self.assertEqual(error, '')
            infile, options, outfile = run_args
            self.assertEqual(['32768,1', '40000-40010,2'], options.pokes)

    def test_option_p_z80v1_uncompressed(self):
        address, value = 49152, 55
        header = list(range(30))
        header[12] &= 223 # RAM block uncompressed
        ram = [0] * 49152
        exp_ram = ram[:]
        exp_ram[address - 16384] = value
        exp_header = header[:]
        exp_header[12] |= 32 # RAM block compressed
        options = '-p {},{}'.format(address, value)
        self._test_z80(options, header, exp_header, ram, exp_ram, 1, False)

    def test_option_poke_z80v2_uncompressed_address_range_plus(self):
        addr1, addr2, inc = 30000, 30004, 100
        header = [0] * 55
        header[30] = 23 # Version 2
        ram = [0] * 49152
        values = (1, 22, 103, 204, 55)
        i, j = addr1 - 16384, addr2 - 16383
        ram[i:j] = values
        exp_ram = ram[:]
        exp_ram[i:j] = [(b + inc) & 255 for b in values]
        exp_header = header[:]
        options = '--poke {}-{},+{}'.format(addr1, addr2, inc)
        self._test_z80(options, header, exp_header, ram, exp_ram, 2, False)

    def test_option_p_z80v3_compressed_address_range_step_xor(self):
        addr1, addr2, step, xor = 40000, 40010, 2, 170
        header = [0] * 86
        header[30] = 54 # Version 3
        ram = [0] * 49152
        values = (9, 43, 99, 198, 203, 241)
        i, j = addr1 - 16384, addr2 - 16383
        ram[i:j:step] = values
        exp_ram = ram[:]
        exp_ram[i:j:step] = [b ^ xor for b in values]
        exp_header = header[:]
        options = '--poke {}-{}-{},^{}'.format(addr1, addr2, step, xor)
        self._test_z80(options, header, exp_header, ram, exp_ram, 3, True)

    def test_option_poke_multiple(self):
        pokes = ((24576, 1), (32768, 34), (49152, 205))
        header = list(range(30))
        header[12] &= 223 # RAM block uncompressed
        ram = [0] * 49152
        exp_ram = ram[:]
        for address, value in pokes:
            exp_ram[address - 16384] = value
        exp_header = header[:]
        exp_header[12] |= 32 # RAM block compressed
        options = ' '.join(['--poke {},{}'.format(a, v) for a, v in pokes])
        self._test_z80(options, header, exp_header, ram, exp_ram, 1, False)

    def test_option_p_hexadecimal_values(self):
        addr1, addr2, step, value = 50000, 50006, 3, 200
        header = list(range(30))
        header[12] &= 223 # RAM block uncompressed
        ram = [0] * 49152
        exp_ram = ram[:]
        exp_ram[addr1 - 16384:addr2 - 16383:step] = [value] * 3
        exp_header = header[:]
        exp_header[12] |= 32 # RAM block compressed
        options = '-p ${:04X}-${:04x}-${:X},${:02x}'.format(addr1, addr2, step, value)
        self._test_z80(options, header, exp_header, ram, exp_ram, 1, False)

    def test_reg_help(self):
        output, error = self.run_snapmod('--reg help')
        self.assertEqual(error, '')
        exp_output = [
            'Usage: --r name=value, --reg name=value',
            '',
            'Set the value of a register or register pair. For example:',
            '',
            '  --reg hl=32768',
            '  --reg b=17',
            '',
            "To set the value of an alternate (shadow) register, use the '^' prefix:",
            '',
            '  --reg ^hl=10072',
            '',
            'Recognised register names are:',
            '',
            '  ^a, ^b, ^bc, ^c, ^d, ^de, ^e, ^f, ^h, ^hl, ^l, a, b, bc, c, d, de, e,',
            '  f, h, hl, i, ix, iy, l, pc, r, sp'
        ]
        self.assertEqual(exp_output, output)

    @patch.object(snapmod, 'run', mock_run)
    def test_options_s_state(self):
        for option in ('-s', '--state'):
            output, error = self.run_snapmod('{0} im=1 {0} iff=1 test.z80'.format(option))
            self.assertEqual([], output)
            self.assertEqual(error, '')
            infile, options, outfile = run_args
            self.assertEqual(['im=1', 'iff=1'], options.state)

    def test_option_s(self):
        header = [0] * 86
        header[30] = 54 # Version 3
        ram = [0] * 49152
        infile = self.write_z80_file(header, ram)
        exp_header = header[:]
        exp_header[12] |= 4 # BORDER 2
        exp_header[27] = 1 # IFF 1
        exp_header[28] = 1 # IFF 2
        exp_header[29] = (header[29] & 252) | 2 # IM 2
        outfile = self.write_bin_file(suffix='.z80')
        output, error = self.run_snapmod('-f -s border=2 -s iff=1 -s im=2 {} {}'.format(infile, outfile))
        self.assertEqual([], output)
        self.assertEqual(error, '')
        z80_header = list(read_bin_file(outfile, 86))
        self.assertEqual(exp_header, z80_header)
        z80_ram = get_snapshot(outfile)[16384:]
        self.assertEqual(ram, z80_ram, "RAM was not preserved")

    def test_state_help(self):
        output, error = self.run_snapmod('--state help')
        self.assertEqual(error, '')
        exp_output = [
            'Usage: -s name=value, --state name=value',
            '',
            'Set a hardware state attribute. Recognised names and their default values are:',
            '',
            '  border - border colour (default=0)',
            '  iff    - interrupt flip-flop: 0=disabled, 1=enabled (default=1)',
            '  im     - interrupt mode (default=1)'
        ]
        self.assertEqual(exp_output, output)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_snapmod(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

if __name__ == '__main__':
    unittest.main()
