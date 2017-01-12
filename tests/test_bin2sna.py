import os
import unittest
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import bin2sna, VERSION
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
        self.assertEqual([], output)
        self.assertEqual(error, '')
        self.assertTrue(os.path.isfile(outfile))
        self.tempfiles.append(outfile)
        return outfile

    def _check_z80(self, z80file, data, org=None, sp=None, pc=None, border=7):
        with open(z80file, 'rb') as f:
            z80h = bytearray(f.read(34))
        if org is None:
            org = 65536 - len(data)
        if sp is None:
            sp = org
        if pc is None:
            pc = org

        self.assertEqual((z80h[12] >> 1) & 7, border) # BORDER
        self.assertEqual(z80h[27], 1)                 # IFF1
        self.assertEqual(z80h[28], 1)                 # IFF2
        self.assertEqual(z80h[29] & 3, 1)             # Interrupt mode

        self.assertEqual(z80h[8] + 256 * z80h[9], sp)      # SP
        self.assertEqual(z80h[10], 63)                     # I
        self.assertEqual(z80h[23] + 256 * z80h[24], 23610) # IY
        self.assertEqual(z80h[32] + 256 * z80h[33], pc)    # PC

        snapshot = get_snapshot(z80file)
        self.assertEqual(data, snapshot[org:org + len(data)])

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
        self.assertEqual(options.stack, None)
        self.assertEqual(options.start, None)

    def test_no_arguments(self):
        output, error = self.run_bin2sna(catch_exit=2)
        self.assertEqual([], output)
        self.assertTrue(error.startswith('usage: bin2sna.py'))

    def test_invalid_option(self):
        output, error = self.run_bin2sna('-x test_invalid_option.bin', catch_exit=2)
        self.assertEqual([], output)
        self.assertTrue(error.startswith('usage: bin2sna.py'))

    def test_invalid_option_value(self):
        binfile = self.write_bin_file(suffix='.bin')
        for option in ('-b !', '-o ABC', '-p Q', '-s ?'):
            output, error = self.run_bin2sna('{} {}'.format(option, binfile), catch_exit=2)
            self.assertEqual([], output)
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

    def test_option_p(self):
        data = [1, 2, 4]
        binfile = self.write_bin_file(data, suffix='.bin')
        for option, stack in (('-p', 35000), ('--stack', 45000)):
            z80file = self._run("{} {} {}".format(option, stack, binfile))
            self._check_z80(z80file, data, sp=stack)

    def test_option_s(self):
        data = [2, 3, 4]
        binfile = self.write_bin_file(data, suffix='.bin')
        for option, start in (('-s', 50000), ('--start', 60000)):
            z80file = self._run("{} {} {}".format(option, start, binfile))
            self._check_z80(z80file, data, pc=start)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_bin2sna(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

if __name__ == '__main__':
    unittest.main()
