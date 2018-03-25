import os
import textwrap
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase, Z80_REGISTERS
from skoolkit import SkoolKitError, bin2sna, VERSION
from skoolkit.snapshot import get_snapshot

def mock_run(*args):
    global run_args
    run_args = args

class Bin2SnaTest(SkoolKitTestCase):
    def _run(self, args, outfile=None):
        infile = args.split()[-1]
        if outfile:
            args += ' ' + outfile
        elif infile.lower().endswith('.bin'):
            outfile = infile[:-3] + 'z80'
        elif infile == '-':
            outfile = 'program.z80'
        else:
            outfile = infile + '.z80'
        output, error = self.run_bin2sna(args)
        self.assertEqual(output, '')
        self.assertEqual(error, '')
        self.assertTrue(os.path.isfile(outfile))
        self.tempfiles.append(outfile)
        return outfile

    def _check_z80(self, z80file, data, org=None, sp=None, pc=None, border=7,
                   iff=1, im=1):
        with open(z80file, 'rb') as f:
            z80h = f.read(34)
        if org is None:
            org = 65536 - len(data)
        if sp is None:
            sp = org
        if pc is None:
            pc = org

        self.assertEqual((z80h[12] >> 1) & 7, border) # BORDER
        self.assertEqual(z80h[27], iff)               # IFF1
        self.assertEqual(z80h[28], iff)               # IFF2
        self.assertEqual(z80h[29] & 3, im)            # Interrupt mode

        self.assertEqual(z80h[8] + 256 * z80h[9], sp)      # SP
        self.assertEqual(z80h[10], 63)                     # I
        self.assertEqual(z80h[23] + 256 * z80h[24], 23610) # IY
        self.assertEqual(z80h[32] + 256 * z80h[33], pc)    # PC

        snapshot = get_snapshot(z80file)
        self.assertEqual(data, snapshot[org:org + len(data)])

    def _test_bad_spec(self, option, exp_error):
        binfile = self.write_bin_file([0], suffix='.bin')
        z80file = self.write_bin_file(suffix='.z80')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_bin2sna('{} {} {}'.format(option, binfile, z80file))
        self.assertEqual(cm.exception.args[0], exp_error)

    @patch.object(bin2sna, 'run', mock_run)
    def test_default_option_values(self):
        data = [0] * 10
        binfile = self.write_bin_file(data, suffix='.bin')
        bin2sna.main((binfile,))
        infile, outfile, options = run_args
        self.assertEqual(infile, binfile)
        self.assertEqual(outfile, binfile[:-3] + 'z80')
        self.assertEqual(options.border, 7)
        self.assertEqual(options.org, None)
        self.assertEqual([], options.pokes)
        self.assertEqual([], options.reg)
        self.assertEqual(options.stack, None)
        self.assertEqual(options.start, None)
        self.assertEqual([], options.state)

    def test_no_arguments(self):
        output, error = self.run_bin2sna(catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: bin2sna.py'))

    def test_invalid_option(self):
        output, error = self.run_bin2sna('-x test_invalid_option.bin', catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: bin2sna.py'))

    def test_invalid_option_value(self):
        binfile = self.write_bin_file(suffix='.bin')
        for option in ('-b !', '-o ABC', '-p Q', '-s ?'):
            output, error = self.run_bin2sna('{} {}'.format(option, binfile), catch_exit=2)
            self.assertEqual(output, '')
            self.assertTrue(error.startswith('usage: bin2sna.py'))

    def test_no_options(self):
        data = [1, 2, 3, 4, 5]
        binfile = self.write_bin_file(data, suffix='.bin')
        z80file = self._run(binfile)
        self._check_z80(z80file, data)

    def test_nonstandard_bin_name(self):
        data = [0]
        binfile = self.write_bin_file(data, suffix='.ram')
        z80file = self._run(binfile)
        self._check_z80(z80file, data)

    def test_bin_in_subdirectory(self):
        data = [1]
        subdir = self.make_directory()
        binfile = self.write_bin_file(data, '{}/game.bin'.format(subdir))
        z80file = self._run(binfile)
        self._check_z80(z80file, data)

    def test_z80_in_subdirectory(self):
        odir = 'bin2sna-{}'.format(os.getpid())
        self.tempdirs.append(odir)
        data = [1]
        binfile = self.write_bin_file(data, suffix='.bin')
        z80file = self._run(binfile, '{}/out.z80'.format(odir))
        self._check_z80(z80file, data)

    def test_read_from_standard_input(self):
        data = [1, 2, 3]
        self.write_stdin(bytearray(data))
        z80file = self._run('-')
        self._check_z80(z80file, data)

    def test_option_b(self):
        data = [0, 2, 4]
        binfile = self.write_bin_file(data, suffix='.bin')
        for option, border in (('-b', 2), ('--border', 4)):
            z80file = self._run("{} {} {}".format(option, border, binfile))
            self._check_z80(z80file, data, border=border)

    def test_option_o(self):
        data = [1, 2, 3]
        binfile = self.write_bin_file(data, suffix='.bin')
        for option, org in (('-o', 30000), ('--org', 40000)):
            z80file = self._run("{} {} {}".format(option, org, binfile))
            self._check_z80(z80file, data, org)

    def test_option_o_with_hex_address(self):
        data = [1, 2, 3]
        binfile = self.write_bin_file(data, suffix='.bin')
        for option, org in (('-o', '0x800d'), ('--org', '0xABCD')):
            z80file = self._run("{} {} {}".format(option, org, binfile))
            self._check_z80(z80file, data, int(org[2:], 16))

    def test_option_p(self):
        data = [1, 2, 4]
        binfile = self.write_bin_file(data, suffix='.bin')
        for option, stack in (('-p', 35000), ('--stack', 45000)):
            z80file = self._run("{} {} {}".format(option, stack, binfile))
            self._check_z80(z80file, data, sp=stack)

    def test_option_p_with_hex_address(self):
        data = [1, 2, 4]
        binfile = self.write_bin_file(data, suffix='.bin')
        for option, stack in (('-p', '0x7fff'), ('--stack', '0xC001')):
            z80file = self._run("{} {} {}".format(option, stack, binfile))
            self._check_z80(z80file, data, sp=int(stack[2:], 16))

    def _test_poke(self, option, address, exp_values):
        binfile = self.write_bin_file([0], suffix='.bin')
        z80file = self._run('{} {}'.format(option, binfile))
        self._check_z80(z80file, exp_values, address, 65535, 65535)

    def test_options_P_poke(self):
        for option, spec in (('-P', '32768,1'), ('--poke', '30000,5')):
            address, exp_value = [int(i) for i in spec.split(',')]
            self._test_poke('{} {}'.format(option, spec), address, [exp_value])

    def test_option_P_address_range(self):
        self._test_poke('-P 40000-40002,2', 40000, [2])

    def test_option_P_address_range_with_step(self):
        self._test_poke('-P 50000-50004-2,3', 50000, [3, 0, 3, 0, 3])

    def test_option_P_0x_hexadecimal_values(self):
        self._test_poke('-P 0xc350-0xC354-0x02,0x0f', 50000, [15, 0, 15, 0, 15])

    def test_option_P_with_add_operation(self):
        self._test_poke('-P 30000-30002,+4', 30000, [4] * 3)

    def test_option_P_with_xor_operation(self):
        self._test_poke('-P 60000-60002,^2', 60000, [2] * 3)

    def test_option_P_multiple(self):
        self._test_poke('-P 20000,5 --poke 20001,6', 20000, [5, 6])

    def test_option_P_invalid_values(self):
        self._test_bad_spec('-P 1', 'Value missing in poke spec: 1')
        self._test_bad_spec('-P q', 'Value missing in poke spec: q')
        self._test_bad_spec('-P 1,x', 'Invalid value in poke spec: 1,x')
        self._test_bad_spec('-P x,1', 'Invalid address range in poke spec: x,1')
        self._test_bad_spec('-P 1-y,1', 'Invalid address range in poke spec: 1-y,1')
        self._test_bad_spec('-P 1-3-z,1', 'Invalid address range in poke spec: 1-3-z,1')

    def test_option_r(self):
        binfile = self.write_bin_file([0], suffix='.bin')
        z80file = self.write_bin_file(suffix='.z80')
        reg_dicts = (
            {'^a': 1, '^b': 2, '^c': 3, '^d': 4, '^e': 5, '^f': 6, '^h': 7, '^l': 8},
            {'a': 9, 'b': 10, 'c': 11, 'd': 12, 'e': 13, 'f': 14, 'h': 15, 'l': 16, 'r': 129},
            {'^bc': 258, '^de': 515, '^hl': 65534, 'bc': 259, 'de': 516, 'hl': 65533},
            {'i': 13, 'ix': 1027, 'iy': 1284, 'pc': 1541, 'r': 23, 'sp': 32769}
        )
        for reg_dict in reg_dicts:
            options = []
            option = '--reg'
            for reg, value in reg_dict.items():
                options.append('{} {}={}'.format(option, reg, value))
                option = '-r' if option == '--reg' else '--reg'
            output, error = self.run_bin2sna('{} {} {}'.format(' '.join(options), binfile, z80file))
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

    def test_option_reg_with_hex_value(self):
        binfile = self.write_bin_file([0], suffix='.bin')
        z80file = self.write_bin_file(suffix='.z80')
        reg_value = 35487
        output, error = self.run_bin2sna('--reg bc=${:x} {} {}'.format(reg_value, binfile, z80file))
        self.assertEqual(error, '')
        with open(z80file, 'rb') as f:
            z80_header = f.read(4)
        self.assertEqual(z80_header[2] + 256 * z80_header[3], reg_value)

    def test_option_reg_with_0x_hex_value(self):
        binfile = self.write_bin_file([0], suffix='.bin')
        z80file = self.write_bin_file(suffix='.z80')
        reg_value = 43665
        output, error = self.run_bin2sna('--reg hl=0x{:X} {} {}'.format(reg_value, binfile, z80file))
        self.assertEqual(error, '')
        with open(z80file, 'rb') as f:
            z80_header = f.read(6)
        self.assertEqual(z80_header[4] + 256 * z80_header[5], reg_value)

    def test_option_reg_bad_value(self):
        self._test_bad_spec('--reg bc=A2', 'Cannot parse register value: bc=A2')

    def test_option_reg_invalid_register(self):
        self._test_bad_spec('--reg iz=1', 'Invalid register: iz=1')

    def test_option_reg_help(self):
        output, error = self.run_bin2sna('--reg help')
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

    def test_option_s(self):
        data = [2, 3, 4]
        binfile = self.write_bin_file(data, suffix='.bin')
        for option, start in (('-s', 50000), ('--start', 60000)):
            z80file = self._run("{} {} {}".format(option, start, binfile))
            self._check_z80(z80file, data, pc=start)

    def test_option_s_with_hex_address(self):
        data = [2, 3, 4]
        binfile = self.write_bin_file(data, suffix='.bin')
        for option, start in (('-s', '0x6f00'), ('--start', '0xD00A')):
            z80file = self._run("{} {} {}".format(option, start, binfile))
            self._check_z80(z80file, data, pc=int(start[2:], 16))

    def test_option_S(self):
        data = [0]
        binfile = self.write_bin_file(data, suffix='.bin')
        for option, border, iff, im in (('-S', 3, 0, 2), ('--state', 5, 1, 0)):
            z80file = self._run("{0} border={1} {0} iff={2} {0} im={3} {4}".format(option, border, iff, im, binfile))
            self._check_z80(z80file, data, border=border, iff=iff, im=im)

    def test_option_S_invalid_values(self):
        self._test_bad_spec('-S border=k', 'Cannot parse integer: border=k')
        self._test_bad_spec('--state iff=$', 'Cannot parse integer: iff=$')
        self._test_bad_spec('-S im=?', 'Cannot parse integer: im=?')
        self._test_bad_spec('--state bar=1', 'Invalid parameter: bar=1')

    def test_option_state_help(self):
        output, error = self.run_bin2sna('--state help')
        self.assertEqual(error, '')
        exp_output = """
            Usage: -S name=value, --state name=value

            Set a hardware state attribute. Recognised names and their default values are:

              border - border colour (default=0)
              iff    - interrupt flip-flop: 0=disabled, 1=enabled (default=1)
              im     - interrupt mode (default=1)
        """
        self.assertEqual(textwrap.dedent(exp_output).lstrip(), output)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_bin2sna(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))
