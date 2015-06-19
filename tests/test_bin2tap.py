# -*- coding: utf-8 -*-
import sys
import os
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import bin2tap, VERSION

PY3 = sys.version_info >= (3,)

TEST_FNAME = 'test-tap'
TEST_BIN = '{0}.bin'.format(TEST_FNAME)
TEST_TAP = '{0}.tap'.format(TEST_FNAME)

def mock_run(*args):
    global run_args
    run_args = args

class Bin2TapTest(SkoolKitTestCase):
    def _run(self, args, data=None, tapfile=TEST_TAP):
        if data is not None:
            self.write_bin_file(data, TEST_BIN)
        output, error = self.run_bin2tap(args)
        self.assertEqual(output, [])
        self.assertEqual(error, '')
        self.assertTrue(os.path.isfile(tapfile))
        self.tempfiles.append(tapfile)
        with open(tapfile, 'rb') as f:
            tap = f.read()
        if PY3:
            return list(tap)
        return [ord(c) for c in tap]

    def _get_word(self, num):
        return (num % 256, num // 256)

    def _get_parity(self, data):
        parity = 0
        for b in data[2:]:
            parity ^= b
        return parity

    def _get_str(self, chars):
        return [ord(c) for c in chars]

    def _check_tap(self, tap_data, bin_data, org=None, start=None, stack=None, infile=TEST_BIN):
        if org is None:
            org = 65536 - len(bin_data)
        if start is None:
            start = org
        if stack is None:
            stack = org

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

    def _check_tap_with_clear_command(self, tap_data, bin_data, clear, org=None, start=None, infile=TEST_BIN):
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
        ram, clear, org, start, stack, infile, tapfile = run_args
        self.assertEqual(ram, bytearray(data))
        self.assertIsNone(clear)
        self.assertEqual(org, 65536 - len(data))
        self.assertEqual(start, org)
        self.assertEqual(stack, org)
        self.assertEqual(infile, binfile)
        self.assertEqual(tapfile, binfile[:-4] + '.tap')

    def test_no_arguments(self):
        output, error = self.run_bin2tap(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: bin2tap.py'))

    def test_invalid_option(self):
        output, error = self.run_bin2tap('-x {0}'.format(TEST_BIN), catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: bin2tap.py'))

    def test_invalid_option_value(self):
        binfile = self.write_bin_file(suffix='.bin')
        for option in ('-o ABC', '-s =', '-p q'):
            output, error = self.run_bin2tap('{0} {1}'.format(option, binfile), catch_exit=2)
            self.assertEqual(len(output), 0)
            self.assertTrue(error.startswith('usage: bin2tap.py'))

    def test_no_options(self):
        bin_data = [1, 2, 3, 4, 5]
        tap_data = self._run(TEST_BIN, bin_data)
        self._check_tap(tap_data, bin_data)

    def test_nonstandard_bin_name(self):
        bin_data = [0]
        binfile = self.write_bin_file(bin_data, suffix='.ram')
        tapfile = '{0}.tap'.format(binfile)
        tap_data = self._run(binfile, tapfile=tapfile)
        self._check_tap(tap_data, bin_data, infile=binfile)
        os.remove(tapfile)

    def test_bin_in_subdirectory(self):
        bin_data = [1]
        subdir = self.make_directory()
        binfile = self.write_bin_file(bin_data, '{}/game.bin'.format(subdir))
        tapfile = binfile[:-4] + '.tap'
        tap_data = self._run(binfile, tapfile=tapfile)
        self._check_tap(tap_data, bin_data, infile=binfile)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_bin2tap(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

    def test_option_c(self):
        org = 40000
        bin_data = list(range(25))
        clear = org - 1
        start = org + 10
        for option in ('-c', '--clear'):
            tap_data = self._run('{} {} -o {} -s {} {}'.format(option, clear, org, start, TEST_BIN), bin_data)
            self._check_tap_with_clear_command(tap_data, bin_data, clear, org, start)

    def test_option_o(self):
        org = 40000
        bin_data = [i for i in range(50)]
        for option in ('-o', '--org'):
            tap_data = self._run('{0} {1} {2}'.format(option, org, TEST_BIN), bin_data)
            self._check_tap(tap_data, bin_data, org=org)

    def test_option_s(self):
        bin_data = [i for i in range(100)]
        start = 65536 - len(bin_data) // 2
        for option in ('-s', '--start'):
            tap_data = self._run('{0} {1} {2}'.format(option, start, TEST_BIN), bin_data)
            self._check_tap(tap_data, bin_data, start=start)

    def test_option_p(self):
        stack = 32768
        bin_data = [i for i in range(64)]
        for option in ('-p', '--stack'):
            tap_data = self._run('{0} {1} {2}'.format(option, stack, TEST_BIN), bin_data)
            self._check_tap(tap_data, bin_data, stack=stack)

    def test_option_t(self):
        tapfile = 'testtap-{0}.tap'.format(os.getpid())
        self.tempfiles.append(tapfile)
        bin_data = [i for i in range(32)]
        for option in ('-t', '--tapfile'):
            tap_data = self._run('{0} {1} {2}'.format(option, tapfile, TEST_BIN), bin_data, tapfile)
            self._check_tap(tap_data, bin_data)
            os.remove(tapfile)

    def test_data_overwrites_stack(self):
        bin_data = [0] * 10
        org = 65536 - len(bin_data)
        index = 5
        stack = org + index
        tap_data = self._run('-p {0} {1}'.format(stack, TEST_BIN), bin_data)
        bin_data[index - 4:index] = [
            63, 5,                # 1343 (SA/LD-RET)
            org % 256, org // 256 # start=org
        ]
        self._check_tap(tap_data, bin_data, stack=stack)

    def test_option_e_with_z80(self):
        ram = [0] * 49152
        data = list(range(20))
        org = 32768
        end = org + len(data)
        ram[org - 16384:end - 16384] = data
        z80 = self.write_z80(ram)[1]
        tapfile = z80[:-4] + '.tap'
        tap_data = self._run('-o {} -e {} {}'.format(org, end, z80), tapfile=tapfile)
        self._check_tap(tap_data, data, infile=z80)

    def test_option_e_with_szx(self):
        ram = [0] * 49152
        data = list(range(17))
        org = 50000
        end = org + len(data)
        ram[org - 16384:end - 16384] = data
        szx = self.write_szx(ram)
        tapfile = szx[:-4] + '.tap'
        tap_data = self._run('-o {} -e {} {}'.format(org, end, szx), tapfile=tapfile)
        self._check_tap(tap_data, data, infile=szx)

    def test_option_end_with_sna(self):
        ram = [0] * 49152
        data = list(range(15))
        org = 40000
        end = org + len(data)
        ram[org - 16384:end - 16384] = data
        sna = self.write_bin_file([0] * 27 + ram, suffix='.sna')
        tapfile = sna[:-4] + '.tap'
        tap_data = self._run('-o {} --end {} {}'.format(org, end, sna), tapfile=tapfile)
        self._check_tap(tap_data, data, infile=sna)

if __name__ == '__main__':
    unittest.main()
