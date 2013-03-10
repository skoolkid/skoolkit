# -*- coding: utf-8 -*-
import os
import unittest

from skoolkittest import SkoolKitTestCase, PY3
from skoolkit import bin2tap, UsageError

TEST_FNAME = 'test-tap'
TEST_BIN = '{0}.bin'.format(TEST_FNAME)
TEST_TAP = '{0}.tap'.format(TEST_FNAME)

USAGE = """bin2tap.py [options] FILE.bin

  Convert a binary snapshot file into a TAP file.

Options:
  -o ORG      Set the origin (default: 65536 - length of FILE.bin)
  -s START    Set the start address to JP to (default: ORG)
  -p STACK    Set the stack pointer (default: ORG)
  -t TAPFILE  Set the TAP filename (default: FILE.tap)"""

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
            return [b for b in tap]
        return [ord(c) for c in tap]

    def _get_word(self, num):
        return (num % 256, num // 256)

    def _get_parity(self, data):
        parity = 0
        for b in data[2:]:
            parity ^= b
        return parity

    def _check_tap(self, tap_data, bin_data, org=None, start=None, stack=None, name=TEST_BIN):
        if org is None:
            org = 65536 - len(bin_data)
        if start is None:
            start = org
        if stack is None:
            stack = org

        title = [ord(c) for c in name[:10].ljust(10)]

        # BASIC loader header
        basic_loader_header = tap_data[:21]
        exp_header = [19, 0, 0, 0]
        exp_header += title
        exp_header += [27, 0, 10, 0, 27, 0]
        exp_header.append(self._get_parity(exp_header))
        self.assertEqual(basic_loader_header, exp_header)

        # BASIC loader data
        basic_loader_data = tap_data[21:52]
        exp_data = [29, 0, 255]
        exp_data += [0, 10, 5, 0, 239, 34, 34, 175, 13] # 10 LOAD ""CODE
        exp_data += [0, 20, 14, 0, 249, 192, 50, 51, 50, 57, 54, 14, 0, 0, 0, 91, 0, 13] # 20 RANDOMIZE USR 23296
        exp_data.append(self._get_parity(exp_data))
        self.assertEqual(basic_loader_data, exp_data)

        # Code loader header
        code_loader_header = tap_data[52:73]
        exp_header = [19, 0, 0, 3]
        exp_header += title
        exp_header += [19, 0, 0, 91, 0, 0]
        exp_header.append(self._get_parity(exp_header))
        self.assertEqual(code_loader_header, exp_header)

        # Code loader data
        code_loader_data = tap_data[73:96]
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
        data = tap_data[96:]
        exp_data = []
        exp_data.extend(self._get_word(len(bin_data) + 2))
        exp_data.append(255)
        exp_data.extend(bin_data)
        exp_data.append(self._get_parity(exp_data))
        self.assertEqual(data, exp_data)

    def test_default_option_values(self):
        data = [0] * 10
        binfile = self.write_bin_file(data, suffix='.bin')
        ram, org, start, stack, infile, tapfile = bin2tap.parse_args((binfile,))
        self.assertEqual(ram, bytearray(data))
        self.assertEqual(org, 65536 - len(data))
        self.assertEqual(start, org)
        self.assertEqual(stack, org)
        self.assertEqual(infile, binfile)
        self.assertEqual(tapfile, binfile[:-4] + '.tap')

    def test_no_arguments(self):
        try:
            self.run_bin2tap()
            self.fail()
        except UsageError as e:
            self.assertEqual(e.args[0], USAGE)

    def test_invalid_option(self):
        try:
            self.run_bin2tap('-x {0}'.format(TEST_BIN))
            self.fail()
        except UsageError as e:
            self.assertEqual(e.args[0], USAGE)

    def test_invalid_option_value(self):
        binfile = self.write_bin_file(suffix='.bin')
        for option, name, value in (('-o', 'ORG', 'ABC'), ('-s', 'START', '='), ('-p', 'STACK', 'q')):
            try:
                self.run_bin2tap('{0} {1} {2}'.format(option, value, binfile))
                self.fail()
            except UsageError as e:
                self.assertEqual(e.args[0], '{0} ({1}) must be an integer'.format(name, option))

    def test_no_options(self):
        bin_data = [1, 2, 3, 4, 5]
        tap_data = self._run(TEST_BIN, bin_data)
        self._check_tap(tap_data, bin_data)

    def test_nonstandard_bin_name(self):
        bin_data = [0]
        binfile = self.write_bin_file(bin_data, suffix='.ram')
        tapfile = '{0}.tap'.format(binfile)
        tap_data = self._run(binfile, tapfile=tapfile)
        self._check_tap(tap_data, bin_data, name=binfile)
        os.remove(tapfile)

    def test_o(self):
        org = 40000
        bin_data = [i for i in range(50)]
        tap_data = self._run('-o {0} {1}'.format(org, TEST_BIN), bin_data)
        self._check_tap(tap_data, bin_data, org=org)

    def test_s(self):
        bin_data = [i for i in range(100)]
        start = 65536 - len(bin_data) // 2
        tap_data = self._run('-s {0} {1}'.format(start, TEST_BIN), bin_data)
        self._check_tap(tap_data, bin_data, start=start)

    def test_p(self):
        stack = 32768
        bin_data = [i for i in range(64)]
        tap_data = self._run('-p {0} {1}'.format(stack, TEST_BIN), bin_data)
        self._check_tap(tap_data, bin_data, stack=stack)

    def test_t(self):
        tapfile = 'testtap.tap'
        bin_data = [i for i in range(32)]
        tap_data = self._run('-t {0} {1}'.format(tapfile, TEST_BIN), bin_data, tapfile)
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

if __name__ == '__main__':
    unittest.main()
