import textwrap
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase, Z80_REGISTERS
from skoolkit import SkoolKitError, snapmod, read_bin_file, VERSION
from skoolkit.snapshot import get_snapshot

def mock_run(*args):
    global run_args
    run_args = args

class SnapmodTest(SkoolKitTestCase):
    def _get_header(self, version, compress=False):
        if version == 1:
            header = [0] * 30
            header[6] = 255 # PC > 0
            if compress:
                header[12] |= 32 # RAM block compressed
        elif version == 2:
            header = [0] * 55
            header[30] = 23
        else:
            header = [0] * 86
            header[30] = 54
        return header

    def _test_bad_spec(self, option, infile, exp_error):
        outfile = '{}-out.z80'.format(infile[:-4])
        self.tempfiles.append(outfile)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_snapmod('{} {} {}'.format(option, infile, outfile))
        self.assertEqual(cm.exception.args[0], exp_error)

    def _test_z80(self, options, header, exp_header, ram=None, exp_ram=None, version=3, compress=False):
        if ram is None:
            ram = [0] * 49152
        if exp_ram is None:
            exp_ram = ram
        infile = self.write_z80_file(header, ram, version, compress)
        outfile = '{}-out.z80'.format(infile[:-4])
        self.tempfiles.append(outfile)
        output, error = self.run_snapmod('{} {} {}'.format(options, infile, outfile))
        self.assertEqual(output, '')
        self.assertEqual(error, '')
        z80_header = list(read_bin_file(outfile, len(exp_header)))
        self.assertEqual(exp_header, z80_header)
        z80_ram = get_snapshot(outfile)[16384:]
        self.assertEqual(exp_ram, z80_ram)

    def _test_move(self, option, src, block, dest, version, compress, hex_prefix=None):
        size = len(block)
        if hex_prefix:
            options = '{0} {1}{2:04X},{1}{3:x},{1}{4:04x}'.format(option, hex_prefix, src, size, dest)
        else:
            options = '{} {},{},{}'.format(option, src, size, dest)
        header = self._get_header(version, compress)
        exp_header = header[:]
        if version == 1:
            exp_header[12] |= 32 # RAM block compressed
        ram = [0] * 49152
        ram[src - 16384:src - 16384 + size] = block
        exp_ram = ram[:]
        exp_ram[dest - 16384:dest - 16384 + size] = block
        self._test_z80(options, header, exp_header, ram, exp_ram, version, compress)

    def _test_reg(self, option, registers, version, hex_prefix=None):
        header = self._get_header(version)
        exp_header = header[:]
        options = []
        for reg, value in registers.items():
            if hex_prefix:
                options.append('{} {}={}{:x}'.format(option, reg, hex_prefix, value))
            else:
                options.append('{} {}={}'.format(option, reg, value))
            reg = reg.lower()
            if version == 1 and reg == 'pc':
                exp_header[6:8] = (value % 256, value // 256)
            elif len(reg.replace('^', '')) == 1:
                if reg == 'r':
                    exp_header[11] = value
                    exp_header[12] |= value // 128
                else:
                    exp_header[Z80_REGISTERS[reg]] = value
            else:
                index = Z80_REGISTERS[reg]
                exp_header[index:index + 2] = (value % 256, value // 256)
        if version == 1:
            exp_header[12] |= 32 # RAM block compressed
        self._test_z80(' '.join(options), header, exp_header, version=version, compress=False)

    def test_no_arguments(self):
        output, error = self.run_snapmod(catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: snapmod.py'))

    def test_invalid_option(self):
        output, error = self.run_snapmod('-x test.z80', catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: snapmod.py'))

    def test_unrecognised_snapshot_type(self):
        with self.assertRaisesRegex(SkoolKitError, 'Unrecognised input snapshot type$'):
            self.run_snapmod('unknown.snap')

    def test_nonexistent_input_file(self):
        infile = 'non-existent.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_snapmod('-r hl=0 {}'.format(infile))
        self.assertEqual(cm.exception.args[0], '{}: file not found'.format(infile))

    def test_no_clobber_input_file(self):
        infile = self.write_bin_file(suffix='.z80')
        output, error = self.run_snapmod('-p 16384,0 {}'.format(infile))
        self.assertEqual(output, '{}: file already exists; use -f to overwrite\n'.format(infile))
        self.assertEqual(error, '')

    def test_no_clobber_output_file(self):
        outfile = self.write_bin_file(suffix='.z80')
        output, error = self.run_snapmod('-p 16384,0 in.z80 {}'.format(outfile))
        self.assertEqual(output, '{}: file already exists; use -f to overwrite\n'.format(outfile))
        self.assertEqual(error, '')

    def test_option_f_clobber_input_file(self):
        header = [0] * 30
        header[6] = 1 # PC > 0
        exp_header = header[:]
        exp_header[12] |= 34 # RAM block compressed, BORDER 1
        ram = [0] * 49152
        infile = self.write_z80_file(header, ram, 1)
        output, error = self.run_snapmod('-f -s border=1 {}'.format(infile))
        self.assertEqual(output, '')
        self.assertEqual(error, '')
        z80_header = list(read_bin_file(infile, len(exp_header)))
        self.assertEqual(exp_header, z80_header)

    def test_option_force_clobber_output_file(self):
        header = [0] * 30
        header[6] = 1 # PC > 0
        exp_header = header[:]
        exp_header[12] |= 36 # RAM block compressed, BORDER 2
        ram = [0] * 49152
        infile = self.write_z80_file(header, ram, 1)
        outfile = self.write_bin_file(suffix='.z80')
        output, error = self.run_snapmod('--force -s border=2 {} {}'.format(infile, outfile))
        self.assertEqual(output, '')
        self.assertEqual(error, '')
        z80_header = list(read_bin_file(outfile, len(exp_header)))
        self.assertEqual(exp_header, z80_header)

    @patch.object(snapmod, 'run', mock_run)
    def test_options_m_move(self):
        for option in ('-m', '--move'):
            output, error = self.run_snapmod('{0} 30000,10,40000 {0} 50000,20,60000 test.z80'.format(option))
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            infile, options, outfile = run_args
            self.assertEqual(['30000,10,40000', '50000,20,60000'], options.moves)

    def test_option_m_z80v1_compressed(self):
        self._test_move('-m', 30000, [1] * 10, 40000, 1, True)

    def test_option_move_z80v2_compressed(self):
        self._test_move('--move', 40000, [2] * 10, 50000, 2, True)

    def test_option_m_z80v3_uncompressed(self):
        self._test_move('-m', 50000, [3] * 5, 60000, 3, False)

    def test_option_move_multiple(self):
        specs = ((34576, 2, 30000), (45678, 3, 40000), (56789, 4, 50000))
        header = [0] * 30
        header[6] = 1
        exp_header = header[:]
        exp_header[12] |= 32 # RAM block compressed
        ram = [0] * 49152
        for i, (src, size, dest) in enumerate(specs):
            ram[src - 16384:src - 16384 + size] = [i + 10] * size
        exp_ram = ram[:]
        for src, size, dest in specs:
            exp_ram[dest - 16384:dest - 16384 + size] = ram[src - 16384:src - 16384 + size]
        options = ' '.join(['--move {},{},{}'.format(*spec) for spec in specs])
        self._test_z80(options, header, exp_header, ram, exp_ram, 1, False)

    def test_option_m_hexadecimal_values(self):
        self._test_move('-m', 0x81AF, [203] * 3, 0x920D, 1, False, '$')
        self._test_move('-m', 0x91AF, [21] * 3, 0xA20D, 1, False, '0x')

    def test_option_m_invalid_values(self):
        infile = self.write_z80_file([1] * 30, [0] * 49152, 1)
        self._test_bad_spec('-m 1', infile, 'Not enough arguments in move spec (expected 3): 1')
        self._test_bad_spec('-m 1,2', infile, 'Not enough arguments in move spec (expected 3): 1,2')
        self._test_bad_spec('-m x,2,3', infile, 'Invalid integer in move spec: x,2,3')
        self._test_bad_spec('-m 1,y,3', infile, 'Invalid integer in move spec: 1,y,3')
        self._test_bad_spec('-m 1,2,z', infile, 'Invalid integer in move spec: 1,2,z')

    @patch.object(snapmod, 'run', mock_run)
    def test_options_p_poke(self):
        for option in ('-p', '--poke'):
            output, error = self.run_snapmod('{0} 32768,1 {0} 40000-40010,2 test.z80'.format(option))
            self.assertEqual(output, '')
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

    def test_option_p_0x_hexadecimal_values(self):
        addr1, addr2, step, value = 60000, 60006, 3, 201
        header = list(range(30))
        header[12] &= 223 # RAM block uncompressed
        ram = [0] * 49152
        exp_ram = ram[:]
        exp_ram[addr1 - 16384:addr2 - 16383:step] = [value] * 3
        exp_header = header[:]
        exp_header[12] |= 32 # RAM block compressed
        options = '-p 0x{:04X}-0x{:04x}-0x{:X},0x{:02x}'.format(addr1, addr2, step, value)
        self._test_z80(options, header, exp_header, ram, exp_ram, 1, False)

    def test_option_p_invalid_values(self):
        infile = self.write_z80_file([1] * 30, [0] * 49152, 1)
        self._test_bad_spec('-p 1', infile, 'Value missing in poke spec: 1')
        self._test_bad_spec('-p q', infile, 'Value missing in poke spec: q')
        self._test_bad_spec('-p 1,x', infile, 'Invalid value in poke spec: 1,x')
        self._test_bad_spec('-p x,1', infile, 'Invalid address range in poke spec: x,1')
        self._test_bad_spec('-p 1-y,1', infile, 'Invalid address range in poke spec: 1-y,1')
        self._test_bad_spec('-p 1-3-z,1', infile, 'Invalid address range in poke spec: 1-3-z,1')

    def test_option_r_z80v1_8_bit_registers(self):
        registers = {
            'a': 5, 'b': 24, 'c': 13, 'd': 105, 'e': 32, 'f': 205, 'h': 14, 'l': 7,
            '^a': 23, '^b': 2, '^c': 131, '^d': 5, '^e': 232, '^f': 5, '^h': 141, '^l': 72,
            'i': 54, 'r': 99
        }
        self._test_reg('-r', registers, 1)

    def test_option_reg_z80v1_register_pairs(self):
        registers = {
            'bc': 12345, 'de': 23456, 'hl': 34567,
            '^bc': 45678, '^de': 56789, '^hl': 54321,
            'ix': 43210, 'iy': 32109, 'sp': 21098, 'pc': 10987
        }
        self._test_reg('--reg', registers, 1)

    def test_option_r_z80v2_8_bit_registers(self):
        registers = {
            'A': 5, 'B': 24, 'C': 13, 'D': 105, 'E': 32, 'F': 205, 'H': 14, 'L': 7,
            '^A': 5, '^B': 24, '^C': 13, '^D': 105, '^E': 32, '^F': 205, '^H': 14, '^L': 7,
            'I': 54, 'R': 99
        }
        self._test_reg('-r', registers, 2)

    def test_option_reg_z80v2_register_pairs(self):
        registers = {
            'BC': 12345, 'DE': 23456, 'HL': 34567,
            '^BC': 45678, '^DE': 56789, '^HL': 54321,
            'IX': 43210, 'IY': 32109, 'SP': 21098, 'PC': 10987
        }
        self._test_reg('--reg', registers, 2)

    def test_option_r_z80v3_8_bit_registers(self):
        registers = {
            'A': 5, 'B': 24, 'C': 13, 'D': 105, 'E': 32, 'F': 205, 'H': 14, 'L': 7,
            '^a': 4, '^b': 23, '^c': 12, '^d': 104, '^e': 31, '^f': 204, '^h': 13, '^l': 6,
            'I': 254, 'r': 199
        }
        self._test_reg('-r', registers, 3)

    def test_option_reg_z80v3_register_pairs(self):
        registers = {
            'bc': 11111, 'de': 22222, 'hl': 33333,
            '^BC': 44444, '^DE': 55555, '^HL': 65432,
            'ix': 54321, 'iy': 43210, 'SP': 32109, 'PC': 21098
        }
        self._test_reg('--reg', registers, 3)

    def test_option_r_hexadecimal_values(self):
        registers = {'a': 0x1f, 'bc': 0xface}
        self._test_reg('-r', registers, 1, '$')

    def test_option_r_0x_hexadecimal_values(self):
        registers = {'a': 0x2e, 'bc': 0xaced}
        self._test_reg('-r', registers, 1, '0x')

    def test_option_r_invalid_values(self):
        infile = self.write_z80_file([1] * 30, [0] * 49152, 1)
        self._test_bad_spec('-r sp=j', infile, 'Cannot parse register value: sp=j')
        self._test_bad_spec('-r x=b', infile, 'Invalid register: x=b')

    def test_reg_help(self):
        output, error = self.run_snapmod('--reg help')
        self.assertEqual(error, '')
        exp_output = """
            Usage: -r name=value, --reg name=value

            Set the value of a register or register pair. For example:

              --reg hl=32768
              --reg b=17

            To set the value of an alternate (shadow) register, use the '^' prefix:

              --reg ^hl=10072

            Recognised register names are:

              ^a, ^b, ^bc, ^c, ^d, ^de, ^e, ^f, ^h, ^hl, ^l, a, b, bc, c, d, de, e,
              f, h, hl, i, ix, iy, l, pc, r, sp
        """
        self.assertEqual(textwrap.dedent(exp_output).lstrip(), output)

    @patch.object(snapmod, 'run', mock_run)
    def test_options_s_state(self):
        for option in ('-s', '--state'):
            output, error = self.run_snapmod('{0} im=1 {0} iff=1 test.z80'.format(option))
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            infile, options, outfile = run_args
            self.assertEqual(['im=1', 'iff=1'], options.state)

    def test_option_s(self):
        header = [0] * 86
        header[30] = 54 # Version 3
        exp_header = header[:]
        exp_header[12] |= 4 # BORDER 2
        exp_header[27] = 1 # IFF 1
        exp_header[28] = 1 # IFF 2
        exp_header[29] = (header[29] & 252) | 2 # IM 2
        options = '-s border=2 -s iff=1 -s im=2'
        self._test_z80(options, header, exp_header)

    def test_option_s_invalid_values(self):
        infile = self.write_z80_file([1] * 30, [0] * 49152, 1)
        self._test_bad_spec('-s border=k', infile, 'Cannot parse integer: border=k')
        self._test_bad_spec('-s iff=$', infile, 'Cannot parse integer: iff=$')
        self._test_bad_spec('-s im=?', infile, 'Cannot parse integer: im=?')
        self._test_bad_spec('-s bar=1', infile, 'Invalid parameter: bar=1')

    def test_state_help(self):
        output, error = self.run_snapmod('--state help')
        self.assertEqual(error, '')
        exp_output = """
            Usage: -s name=value, --state name=value

            Set a hardware state attribute. Recognised names and their default values are:

              border - border colour (default=0)
              iff    - interrupt flip-flop: 0=disabled, 1=enabled (default=1)
              im     - interrupt mode (default=1)
        """
        self.assertEqual(textwrap.dedent(exp_output).lstrip(), output)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_snapmod(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))
