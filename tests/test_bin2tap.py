# -*- coding: utf-8 -*-
import sys
import os
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import bin2tap, SkoolKitError, VERSION

PY3 = sys.version_info >= (3,)

def mock_run(*args):
    global run_args
    run_args = args

class Bin2TapTest(SkoolKitTestCase):
    def _run(self, args, tapfile=None):
        if tapfile is None:
            tapfile = args.split()[-1][:-4] + '.tap'
        output, error = self.run_bin2tap(args)
        self.assertEqual(output, [])
        self.assertEqual(error, '')
        self.assertTrue(os.path.isfile(tapfile))
        self.tempfiles.append(tapfile)
        with open(tapfile, 'rb') as f:
            tap = f.read()
        if PY3:
            return list(tap)
        return map(ord, tap)

    def _get_word(self, num):
        return (num % 256, num // 256)

    def _get_parity(self, data):
        parity = 0
        for b in data[2:]:
            parity ^= b
        return parity

    def _get_str(self, chars):
        return [ord(c) for c in chars]

    def _check_tap(self, tap_data, bin_data, infile, org=None, start=None, stack=None, name=None):
        if org is None:
            org = 65536 - len(bin_data)
        if start is None:
            start = org
        if stack is None:
            stack = org
        if name is None:
            if infile == '-':
                name = 'program'
            else:
                name = os.path.basename(infile)
                if name.lower().endswith(('.bin', '.sna', '.szx', '.z80')):
                    name = name[:-4]
        title = [ord(c) for c in name[:10].ljust(10)]

        # BASIC loader header
        i, j = 0, 21
        basic_loader_header = tap_data[i:j]
        loader_length = 20
        exp_header = [19, 0, 0, 0]
        exp_header += title
        exp_header += [loader_length, 0, 10, 0, loader_length, 0]
        exp_header.append(self._get_parity(exp_header))
        self.assertEqual(exp_header, basic_loader_header)

        # BASIC loader data
        i, j = j, j + loader_length + 4
        basic_loader_data = tap_data[i:j]
        start_addr = self._get_str('"23296"')
        exp_data = [loader_length + 2, 0, 255]
        exp_data += [0, 10, 16, 0]
        exp_data += [239, 34, 34, 175]            # LOAD ""CODE
        exp_data.append(58)                       # :
        exp_data += [249, 192, 176] + start_addr  # RANDOMIZE USR VAL "23296"
        exp_data.append(13)                       # ENTER
        exp_data.append(self._get_parity(exp_data))
        self.assertEqual(exp_data, basic_loader_data)

        # Code loader header
        i, j = j, j + 21
        code_loader_header = tap_data[i:j]
        exp_header = [19, 0, 0, 3]
        exp_header += title
        exp_header += [19, 0, 0, 91, 0, 0]
        exp_header.append(self._get_parity(exp_header))
        self.assertEqual(exp_header, code_loader_header)

        # Code loader data
        i, j = j, j + 23
        code_loader_data = tap_data[i:j]
        exp_data = [21, 0, 255, 221, 33]
        exp_data.extend(self._get_word(org))
        exp_data.append(17)
        exp_data.extend(self._get_word(len(bin_data)))
        exp_data += [55, 159, 49]
        exp_data.extend(self._get_word(stack))
        exp_data.append(1)
        exp_data.extend(self._get_word(start))
        exp_data += [197, 195, 86, 5]
        exp_data.append(self._get_parity(exp_data))

        # Data
        data = tap_data[j:]
        exp_data = []
        exp_data.extend(self._get_word(len(bin_data) + 2))
        exp_data.append(255)
        exp_data.extend(bin_data)
        exp_data.append(self._get_parity(exp_data))
        self.assertEqual(exp_data, data)

    def _check_tap_with_clear_command(self, tap_data, bin_data, infile, clear, org=None, start=None):
        if org is None:
            org = 65536 - len(bin_data)
        if start is None:
            start = org

        name = os.path.basename(infile)
        if name.lower().endswith(('.bin', '.sna', '.szx', '.z80')):
            name = name[:-4]
        title = self._get_str(name[:10].ljust(10))

        # BASIC loader data
        exp_data = [0, 0, 255]
        clear_addr = self._get_str('"{}"'.format(clear))
        start_addr = self._get_str('"{}"'.format(start))
        line_length = 12 + len(clear_addr) + len(start_addr)
        exp_data += [0, 10, line_length, 0]
        exp_data += [253, 176] + clear_addr       # CLEAR VAL "address"
        exp_data.append(58)                       # :
        exp_data += [239, 34, 34, 175]            # LOAD ""CODE
        exp_data.append(58)                       # :
        exp_data += [249, 192, 176] + start_addr  # RANDOMIZE USR VAL "address"
        exp_data.append(13)                       # ENTER
        exp_data.append(self._get_parity(exp_data))
        length = len(exp_data)
        loader_length = length - 4
        exp_data[0] = length - 2
        index = 21 + length
        basic_loader_data = tap_data[21:index]
        self.assertEqual(exp_data, basic_loader_data)

        # BASIC loader header
        basic_loader_header = tap_data[:21]
        exp_header = [19, 0, 0, 0]
        exp_header += title
        exp_header += self._get_word(loader_length)
        exp_header += [10, 0]
        exp_header += self._get_word(loader_length)
        exp_header.append(self._get_parity(exp_header))
        self.assertEqual(exp_header, basic_loader_header)

        # Code loader header
        code_loader_header = tap_data[index:index + 21]
        exp_header = [19, 0, 0, 3]
        exp_header += title
        exp_header += self._get_word(len(bin_data))
        exp_header += self._get_word(org)
        exp_header += [0, 0]
        exp_header.append(self._get_parity(exp_header))
        self.assertEqual(exp_header, code_loader_header)
        index = index + 21

        # Data
        data = tap_data[index:]
        exp_data = []
        exp_data.extend(self._get_word(len(bin_data) + 2))
        exp_data.append(255)
        exp_data.extend(bin_data)
        exp_data.append(self._get_parity(exp_data))
        self.assertEqual(exp_data, data)

    @patch.object(bin2tap, 'run', mock_run)
    def test_default_option_values(self):
        data = [0] * 10
        binfile = self.write_bin_file(data, suffix='.bin')
        bin2tap.main((binfile,))
        ram, clear, org, start, stack, tapfile = run_args
        self.assertEqual(ram, bytearray(data))
        self.assertIsNone(clear)
        self.assertEqual(org, 65536 - len(data))
        self.assertEqual(start, org)
        self.assertEqual(stack, org)
        self.assertEqual(tapfile, binfile[:-4] + '.tap')

    def test_no_arguments(self):
        output, error = self.run_bin2tap(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: bin2tap.py'))

    def test_invalid_option(self):
        output, error = self.run_bin2tap('-x test_invalid_option.bin', catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: bin2tap.py'))

    def test_invalid_option_value(self):
        binfile = self.write_bin_file(suffix='.bin')
        for option in ('-o ABC', '-s =', '-p q'):
            output, error = self.run_bin2tap('{0} {1}'.format(option, binfile), catch_exit=2)
            self.assertEqual(len(output), 0)
            self.assertTrue(error.startswith('usage: bin2tap.py'))

    def test_empty_bin(self):
        binfile = self.write_bin_file(suffix='.bin')
        with self.assertRaisesRegexp(SkoolKitError, '^{} is empty$'.format(binfile)):
            self.run_bin2tap(binfile)

    def test_invalid_end_address(self):
        with self.assertRaisesRegexp(SkoolKitError, '^End address must be greater than 16384$'):
            self.run_bin2tap('-e 16384 file.z80')
        with self.assertRaisesRegexp(SkoolKitError, '^End address must be greater than 24576$'):
            self.run_bin2tap('-o 24576 -e 23296 file.sna')

    def test_no_options(self):
        bin_data = [1, 2, 3, 4, 5]
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        tap_data = self._run(binfile)
        self._check_tap(tap_data, bin_data, binfile)

    def test_nonstandard_bin_name(self):
        bin_data = [0]
        binfile = self.write_bin_file(bin_data, suffix='.ram')
        tapfile = '{0}.tap'.format(binfile)
        tap_data = self._run(binfile, tapfile)
        self._check_tap(tap_data, bin_data, binfile)

    def test_bin_in_subdirectory(self):
        bin_data = [1]
        subdir = self.make_directory()
        binfile = self.write_bin_file(bin_data, '{}/game.bin'.format(subdir))
        tap_data = self._run(binfile)
        self._check_tap(tap_data, bin_data, binfile)

    def test_read_from_standard_input(self):
        bin_data = [1, 2, 3]
        self.write_stdin(bytearray(bin_data))
        binfile = '-'
        tap_data = self._run(binfile, 'program.tap')
        self._check_tap(tap_data, bin_data, binfile)

    def test_specified_tapfile(self):
        bin_data = [4, 5, 6]
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        tapfile = '{}.tap'.format(os.getpid())
        tap_data = self._run('{} {}'.format(binfile, tapfile), tapfile)
        self._check_tap(tap_data, bin_data, binfile, name=tapfile[:-4])

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_bin2tap(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

    def test_option_c(self):
        org = 40000
        bin_data = list(range(25))
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        clear = org - 1
        start = org + 10
        for option in ('-c', '--clear'):
            tap_data = self._run('{} {} -o {} -s {} {}'.format(option, clear, org, start, binfile))
            self._check_tap_with_clear_command(tap_data, bin_data, binfile, clear, org, start)

    def test_option_o(self):
        org = 40000
        bin_data = [i for i in range(50)]
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        for option in ('-o', '--org'):
            tap_data = self._run('{} {} {}'.format(option, org, binfile))
            self._check_tap(tap_data, bin_data, binfile, org=org)

    def test_option_s(self):
        bin_data = [i for i in range(100)]
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        start = 65536 - len(bin_data) // 2
        for option in ('-s', '--start'):
            tap_data = self._run('{} {} {}'.format(option, start, binfile))
            self._check_tap(tap_data, bin_data, binfile, start=start)

    def test_option_p(self):
        stack = 32768
        bin_data = [i for i in range(64)]
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        for option in ('-p', '--stack'):
            tap_data = self._run('{} {} {}'.format(option, stack, binfile))
            self._check_tap(tap_data, bin_data, binfile, stack=stack)

    def test_option_t(self):
        tapfile = 'testtap-{0}.tap'.format(os.getpid())
        self.tempfiles.append(tapfile)
        bin_data = [i for i in range(32)]
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        for option in ('-t', '--tapfile'):
            tap_data = self._run('{} {} {}'.format(option, tapfile, binfile), tapfile)
            self._check_tap(tap_data, bin_data, binfile, name=tapfile[:-4])

    def test_data_overwrites_stack(self):
        bin_data = [0] * 10
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        org = 65536 - len(bin_data)
        index = 5
        stack = org + index
        tap_data = self._run('-p {} {}'.format(stack, binfile))
        bin_data[index - 4:index] = [
            63, 5,                # 1343 (SA/LD-RET)
            org % 256, org // 256 # start=org
        ]
        self._check_tap(tap_data, bin_data, binfile, stack=stack)

    def test_option_e_with_z80(self):
        ram = [0] * 49152
        data = list(range(20))
        org = 32768
        end = org + len(data)
        ram[org - 16384:end - 16384] = data
        z80 = self.write_z80(ram)[1]
        tap_data = self._run('-o {} -e {} {}'.format(org, end, z80))
        self._check_tap(tap_data, data, z80)

    def test_option_e_with_szx(self):
        ram = [0] * 49152
        data = list(range(17))
        org = 50000
        end = org + len(data)
        ram[org - 16384:end - 16384] = data
        szx = self.write_szx(ram)
        tap_data = self._run('-o {} -e {} {}'.format(org, end, szx))
        self._check_tap(tap_data, data, szx)

    def test_option_end_with_sna(self):
        ram = [0] * 49152
        data = list(range(15))
        org = 40000
        end = org + len(data)
        ram[org - 16384:end - 16384] = data
        sna = self.write_bin_file([0] * 27 + ram, suffix='.sna')
        tap_data = self._run('-o {} --end {} {}'.format(org, end, sna))
        self._check_tap(tap_data, data, sna)

if __name__ == '__main__':
    unittest.main()
