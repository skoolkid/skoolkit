import textwrap
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError, bin2sna, VERSION

EMPTY_BANK = [0] * 0x4000

def mock_run(*args):
    global run_args
    run_args = args

def mock_write_snapshot(fname, memory, registers, state):
    global write_snapshot_args
    write_snapshot_args = (fname, memory, registers, state)

class Bin2SnaTest(SkoolKitTestCase):
    @patch.object(bin2sna, 'write_snapshot', mock_write_snapshot)
    def _check_write_snapshot(self, args, exp_ram=None, exp_state=None, exp_registers=None, exp_fname=None):
        output, error = self.run_bin2sna(args)
        self.assertEqual(output, '')
        self.assertEqual(error, '')
        fname, memory, registers, state = write_snapshot_args
        if exp_ram:
            if len(exp_ram) == 49152:
                self.assertEqual(exp_ram, memory)
            else:
                for i, (bank, exp_bank) in enumerate(zip(memory, exp_ram)):
                    self.assertEqual(exp_bank or EMPTY_BANK, bank, f'Mismatch in bank {i}')
        if exp_state is None:
            exp_state = []
        if not (exp_state and exp_state[0].startswith('border=')):
            exp_state.insert(0, 'border=7')
        self.assertEqual(exp_state, state)
        if exp_registers:
            self.assertEqual(exp_registers, registers)
        if exp_fname:
            self.assertEqual(fname, exp_fname)

    def _test_poke(self, option, address, exp_values):
        binfile = self.write_bin_file([0], suffix='.bin')
        args = f'{option} {binfile}'
        exp_ram = [0] * 49152
        exp_ram[address - 16384:address - 16384 + len(exp_values)] = exp_values
        self._check_write_snapshot(args, exp_ram)

    def _test_bad_spec(self, option, exp_error):
        binfile = self.write_bin_file([0], suffix='.bin')
        z80file = self.write_bin_file(suffix='.z80')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_bin2sna('{} {} {}'.format(option, binfile, z80file))
        self.assertEqual(cm.exception.args[0], exp_error)

    def _write_bank_files(self, exp_ram, banks):
        bank_options = []
        for bank, bank_data in banks:
            exp_ram[bank][:len(bank_data)] = bank_data
            bankfile = self.write_bin_file(bank_data, suffix='.bin')
            bank_options.append(f'--bank {bank},{bankfile}')
        return ' '.join(bank_options)

    @patch.object(bin2sna, 'run', mock_run)
    def test_default_option_values(self):
        data = [0] * 10
        binfile = self.write_bin_file(data, suffix='.bin')
        bin2sna.main((binfile,))
        infile, outfile, options = run_args
        self.assertEqual(infile, binfile)
        self.assertEqual(outfile, binfile[:-3] + 'z80')
        self.assertEqual([], options.bank)
        self.assertEqual(options.border, 7)
        self.assertEqual(options.org, None)
        self.assertIsNone(options.page)
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
        args = self.write_bin_file(data, suffix='.bin')
        exp_ram = [0] * (49152 - len(data)) + data
        self._check_write_snapshot(args, exp_ram)

    def test_128k_input_file(self):
        exp_ram = []
        data = []
        for i in range(8):
            exp_ram.append([i] * 0x4000)
            data.extend(exp_ram[-1])
        args = self.write_bin_file(data, suffix='.bin')
        self._check_write_snapshot(args, exp_ram)

    def test_nonstandard_bin_name(self):
        args = self.write_bin_file([0], suffix='.ram')
        exp_fname = args + '.z80'
        self._check_write_snapshot(args, exp_fname=exp_fname)

    def test_bin_in_subdirectory(self):
        args = self.write_bin_file([0], '{}/foo.bin'.format(self.make_directory()))
        exp_fname = 'foo.z80'
        self._check_write_snapshot(args, exp_fname=exp_fname)

    def test_nonstandard_bin_name_in_subdirectory(self):
        args = self.write_bin_file([0], '{}/foo.ram'.format(self.make_directory()))
        exp_fname = 'foo.ram.z80'
        self._check_write_snapshot(args, exp_fname=exp_fname)

    def test_z80_in_subdirectory(self):
        binfile = self.write_bin_file([0], suffix='.bin')
        exp_fname = z80file = 'bin2sna/out.z80'
        args = f'{binfile} {z80file}'
        self._check_write_snapshot(args, exp_fname=exp_fname)

    def test_read_from_standard_input(self):
        data = [1, 2, 3]
        self.write_stdin(bytearray(data))
        args = '-'
        exp_ram = [0] * (49152 - len(data)) + data
        exp_fname = 'program.z80'
        self._check_write_snapshot(args, exp_ram, exp_fname=exp_fname)

    def test_option_bank(self):
        page, data, org = 6, [1, 2, 3], 50000
        exp_ram = [None] * 8
        exp_ram[page] = [0] * 0x4000
        index = org % 0x4000
        exp_ram[page][index:index + len(data)] = data
        bank = 7
        exp_ram[bank] = [0] * 0x4000
        bank_option = self._write_bank_files(exp_ram, [(bank, (4, 5, 6))])
        binfile = self.write_bin_file(data, suffix='.bin')
        args = f'-o {org} --page {page} {bank_option} {binfile}'
        exp_state = [f'7ffd={page}']
        self._check_write_snapshot(args, exp_ram, exp_state)

    def test_option_bank_multiple(self):
        page, data, org = 0, [3, 2, 1], 50000
        banks = (
            (1, [1, 2, 3]),
            (3, [4, 5, 6]),
            (4, [7, 8, 9]),
            (6, [10, 11, 12]),
            (7, [13, 14, 15])
        )
        exp_ram = [[0] * 0x4000 for i in range(8)]
        index = org % 0x4000
        exp_ram[page][index:index + len(data)] = data
        bank_options = self._write_bank_files(exp_ram, banks)
        binfile = self.write_bin_file(data, suffix='.bin')
        args = f'-o {org} --page {page} {bank_options} {binfile}'
        exp_state = [f'7ffd={page}']
        self._check_write_snapshot(args, exp_ram, exp_state)

    def test_option_bank_overwrite(self):
        page, data, org = 0, [255], 49152
        banks = (
            (0, [254]),
            (2, [253]),
            (5, [252])
        )
        exp_ram = [[0] * 0x4000 for i in range(8)]
        bank_options = self._write_bank_files(exp_ram, banks)
        binfile = self.write_bin_file(data, suffix='.bin')
        args = f'-o {org} --page {page} {bank_options} {binfile}'
        exp_state = [f'7ffd={page}']
        self._check_write_snapshot(args, exp_ram, exp_state)

    def test_option_bank_invalid(self):
        for option, exp_error in (
                ('--bank 1', "invalid argument: '1'"),
                ('--bank x,foo.bin', "invalid integer 'x' in 'x,foo.bin'")
        ):
            output, error = self.run_bin2sna(f'--page 0 {option} infile.bin out.z80', catch_exit=2)
            self.assertEqual(output, '')
            self.assertTrue(error.startswith('usage: bin2sna.py [options] file.bin [OUTFILE]\n'))
            line = error.rstrip().split('\n')[-1]
            self.assertTrue(line.endswith('error: argument --bank: ' + exp_error), line)

    @patch.object(bin2sna, 'run', mock_run)
    def test_options_b_border(self):
        for option, border in (('-b', 2), ('--border', 4)):
            output, error = self.run_bin2sna("{} {} test.bin".format(option, border))
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual(options.border, border)

    def test_option_b(self):
        binfile = self.write_bin_file([0], suffix='.bin')
        args = f'-b 2 {binfile}'
        exp_state = ['border=2']
        self._check_write_snapshot(args, exp_state=exp_state)

    @patch.object(bin2sna, 'run', mock_run)
    def test_options_o_org(self):
        for option, org in (('-o', 30000), ('--org', 40000)):
            output, error = self.run_bin2sna("{} {} test.bin".format(option, org))
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual(options.org, org)

    @patch.object(bin2sna, 'run', mock_run)
    def test_options_o_org_with_hex_address(self):
        for option, org in (('-o', '0x800d'), ('--org', '0xABCD')):
            output, error = self.run_bin2sna("{} {} test.bin".format(option, org))
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual(options.org, int(org[2:], 16))

    def test_option_o(self):
        data = [1, 2, 3]
        binfile = self.write_bin_file(data, suffix='.bin')
        org = 30000
        args = f'-o {org} {binfile}'
        exp_ram = [0] * 49152
        exp_ram[org - 16384:org - 16384 + len(data)] = data
        self._check_write_snapshot(args, exp_ram)

    def test_option_page(self):
        page, data, org = 3, [1, 2, 3], 50000
        exp_ram = [None] * 8
        index = org % 0x4000
        exp_ram[page] = [0] * 0x4000
        exp_ram[page][index:index + len(data)] = data
        binfile = self.write_bin_file(data, suffix='.bin')
        args = f'-o {org} --page {page} {binfile}'
        exp_state = [f'7ffd={page}']
        self._check_write_snapshot(args, exp_ram, exp_state)

    def test_option_page_with_128k_input_file(self):
        exp_ram = []
        data = []
        for i in range(8):
            exp_ram.append([i] * 0x4000)
            data.extend(exp_ram[-1])
        binfile = self.write_bin_file(data, suffix='.bin')
        page = 1
        args = f'--page {page} {binfile}'
        exp_state = [f'7ffd={page}']
        self._check_write_snapshot(args, exp_ram, exp_state)

    def test_option_page_invalid(self):
        for option, exp_error in (
                ('--page 8', "invalid choice: 8 (choose from 0, 1, 2, 3, 4, 5, 6, 7)"),
                ('--page x', "invalid int value: 'x'")
        ):
            output, error = self.run_bin2sna(f'{option} in.bin', catch_exit=2)
            self.assertEqual(output, '')
            self.assertTrue(error.startswith('usage: bin2sna.py [options] file.bin [OUTFILE]\n'))
            line = error.rstrip().split('\n')[-1]
            self.assertTrue(line.endswith('error: argument --page: ' + exp_error), line)

    @patch.object(bin2sna, 'run', mock_run)
    def test_options_p_stack(self):
        for option, stack in (('-p', 35000), ('--stack', 45000)):
            output, error = self.run_bin2sna("{} {} test.bin".format(option, stack))
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual(options.stack, stack)

    @patch.object(bin2sna, 'run', mock_run)
    def test_options_p_stack_with_hex_address(self):
        for option, stack in (('-p', '0x7fff'), ('--stack', '0xC001')):
            output, error = self.run_bin2sna("{} {} test.bin".format(option, stack))
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual(options.stack, int(stack[2:], 16))

    def test_option_p(self):
        binfile = self.write_bin_file([0], suffix='.bin')
        sp = 49152
        args = f'-p {sp} {binfile}'
        exp_registers = [f'sp={sp}', 'pc=65535']
        self._check_write_snapshot(args, exp_registers=exp_registers)

    @patch.object(bin2sna, 'run', mock_run)
    def test_options_P_poke(self):
        for option, spec in (('-P', '32768,1'), ('--poke', '30000,5')):
            output, error = self.run_bin2sna("{} {} test.bin".format(option, spec))
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual([spec], options.pokes)

    def test_option_P(self):
        self._test_poke('-P 32768,1', 32768, [1])

    def test_option_P_address_range(self):
        self._test_poke('-P 40000-40002,2', 40000, [2] * 3)

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

    def test_option_P_128k(self):
        exp_ram = [[0] * 0x4000 for i in range(8)]
        exp_ram[5][0] = 1 # 16384,1 (bank 5)
        exp_ram[2][0] = 2 # 32768,2 (bank 2)
        exp_ram[7][0] = 3 # 49152,3 (bank 7)
        binfile = self.write_bin_file([0], suffix='.bin')
        args = f'--page 7 -P 16384,1 -P 32768,2 -P 49152,3 {binfile}'
        exp_state = ['7ffd=7']
        self._check_write_snapshot(args, exp_ram, exp_state)

    def test_option_P_with_page_number(self):
        exp_ram = [[0] * 0x4000 for i in range(8)]
        args = ['--page 5']
        for page, addr, value in (
                (0, 0, 255),
                (1, 16384, 254),
                (2, 32768, 253),
                (3, 49152, 252),
                (4, 65535, 251),
                (5, 49151, 250),
                (6, 32767, 249),
                (7, 16383, 248),
        ):
            exp_ram[page][addr % 0x4000] = value
            args.append(f'-P {page}:{addr},{value}')
        args.append(self.write_bin_file([0], suffix='.bin'))
        exp_state = ['7ffd=5']
        self._check_write_snapshot(' '.join(args), exp_ram, exp_state)

    def test_option_P_with_128k_input_file(self):
        exp_ram = []
        data = []
        for i in range(8):
            exp_ram.append([i] * 0x4000)
            data.extend(exp_ram[-1])
        binfile = self.write_bin_file(data, suffix='.bin')
        page = 3
        args = f'--page {page} -P 49152,255 {binfile}'
        exp_ram[page][0] = 255 # POKE 49152,255
        exp_state = [f'7ffd={page}']
        self._check_write_snapshot(args, exp_ram, exp_state)

    def test_option_P_invalid_values(self):
        self._test_bad_spec('-P 1', 'Value missing in poke spec: 1')
        self._test_bad_spec('-P q', 'Value missing in poke spec: q')
        self._test_bad_spec('-P p:1,0', 'Invalid page number in poke spec: p:1,0')
        self._test_bad_spec('-P 1,x', 'Invalid value in poke spec: 1,x')
        self._test_bad_spec('-P x,1', 'Invalid address range in poke spec: x,1')
        self._test_bad_spec('-P 1-y,1', 'Invalid address range in poke spec: 1-y,1')
        self._test_bad_spec('-P 1-3-z,1', 'Invalid address range in poke spec: 1-3-z,1')

    def test_option_r(self):
        binfile = self.write_bin_file([0], suffix='.bin')
        reg_dicts = (
            {'^a': 1, '^b': 2, '^c': 3, '^d': 4, '^e': 5, '^f': 6, '^h': 7, '^l': 8},
            {'a': 9, 'b': 10, 'c': 11, 'd': 12, 'e': 13, 'f': 14, 'h': 15, 'l': 16, 'r': 129},
            {'^bc': 258, '^de': 515, '^hl': 65534, 'bc': 259, 'de': 516, 'hl': 65533},
            {'i': 13, 'ix': 1027, 'iy': 1284, 'pc': 1541, 'r': 23, 'sp': 32769}
        )
        for reg_dict in reg_dicts:
            exp_registers = ['sp=65535', 'pc=65535']
            options = []
            option = '--reg'
            for reg, value in reg_dict.items():
                exp_registers.append(f'{reg}={value}')
                options.append(f'{option} {reg}={value}')
                option = '-r' if option == '--reg' else '--reg'
            args = ' '.join(options) + f' {binfile}'
            self._check_write_snapshot(args, exp_registers=exp_registers)

    def test_option_reg_with_hex_value(self):
        bc = '$8a9f'
        binfile = self.write_bin_file([0], suffix='.bin')
        args = f'--reg bc={bc} {binfile}'
        exp_registers = ['sp=65535', 'pc=65535', f'bc={bc}']
        self._check_write_snapshot(args, exp_registers=exp_registers)

    def test_option_reg_with_0x_hex_value(self):
        hl = '0xAA91'
        binfile = self.write_bin_file([0], suffix='.bin')
        args = f'--reg hl={hl} {binfile}'
        exp_registers = ['sp=65535', 'pc=65535', f'hl={hl}']
        self._check_write_snapshot(args, exp_registers=exp_registers)

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

    @patch.object(bin2sna, 'run', mock_run)
    def test_options_s_start(self):
        for option, start in (('-s', 50000), ('--start', 60000)):
            output, error = self.run_bin2sna("{} {} test.bin".format(option, start))
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual(options.start, start)

    @patch.object(bin2sna, 'run', mock_run)
    def test_options_s_start_with_hex_address(self):
        for option, start in (('-s', '0x6f00'), ('--start', '0xD00A')):
            output, error = self.run_bin2sna("{} {} test.bin".format(option, start))
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual(options.start, int(start[2:], 16))

    def test_option_s(self):
        pc = 50000
        binfile = self.write_bin_file([0], suffix='.bin')
        args = f'-s {pc} {binfile}'
        exp_registers = [f'sp=65535', f'pc={pc}']
        self._check_write_snapshot(args, exp_registers=exp_registers)

    @patch.object(bin2sna, 'run', mock_run)
    def test_options_S_state(self):
        for option, values in (('-S', ['border=3', 'iff=0', 'im=2']), ('--state', ['border=5', 'iff=1', 'im=0'])):
            output, error = self.run_bin2sna("{0} {1} {0} {2} {0} {3} test.bin".format(option, *values))
            self.assertEqual(output, '')
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual(values, options.state)

    def test_option_S(self):
        binfile = self.write_bin_file([0], suffix='.bin')
        border, iff, im, issue2, tstates = 3, 0, 2, 1, 100
        args = f'-S border={border} --state iff={iff} -S im={im} -S issue2={issue2} --state tstates={tstates} {binfile}'
        exp_state = ['border=7', f'border={border}', f'iff={iff}', f'im={im}', f'issue2={issue2}', f'tstates={tstates}']
        self._check_write_snapshot(args, exp_state=exp_state)

    def test_option_S_128k(self):
        binfile = self.write_bin_file([0], suffix='.bin')
        state = ['7ffd=3', 'fffd=7']
        state.extend(f'ay[{i}]={r}' for i, r in enumerate(range(34, 50)))
        state_options = ' '.join(f'-S {s}' for s in state)
        args = f'--page 0 {state_options} {binfile}'
        exp_state = ['7ffd=0'] + state
        self._check_write_snapshot(args, exp_state=exp_state)

    def test_option_S_invalid_values(self):
        self._test_bad_spec('-S border=k', 'Cannot parse integer: border=k')
        self._test_bad_spec('--state iff=$', 'Cannot parse integer: iff=$')
        self._test_bad_spec('-S im=?', 'Cannot parse integer: im=?')

    def test_option_state_help(self):
        output, error = self.run_bin2sna('--state help')
        self.assertEqual(error, '')
        exp_output = """
            Usage: -S name=value, --state name=value

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
        self.assertEqual(textwrap.dedent(exp_output).lstrip(), output)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_bin2sna(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))
