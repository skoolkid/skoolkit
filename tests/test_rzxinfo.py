import os
from textwrap import dedent

from skoolkittest import SkoolKitTestCase, RZX
from skoolkit import VERSION, SkoolKitError

class RzxinfoTest(SkoolKitTestCase):
    def _test_rzx(self, rzx, exp_output, options=''):
        if not rzx.creator:
            rzx.set_creator('SkoolKit', 9, 2)
        rzxfile = self.write_rzx_file(rzx)
        output, error = self.run_rzxinfo(f'{options} {rzxfile}')
        self.assertEqual(error, '')
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_sna_48k(self):
        sna = [0] * 49179
        rzx = RZX()
        rzx.add_snapshot(sna, 'sna')
        exp_output = """
            Version: 0.13
            Signed: No
            Creator information:
              ID: SkoolKit 9.2
            Snapshot:
              Filename extension: sna
              Size: 49179 bytes
              Machine: 48K Spectrum
              Start address: 0
            Input recording
              Number of frames: 1 (0h00m00s)
              T-states: 0
              Encrypted: No
        """
        self._test_rzx(rzx, exp_output)

    def test_sna_128k(self):
        sna = [0] * 131103
        rzx = RZX()
        rzx.add_snapshot(sna, 'sna')
        exp_output = """
            Version: 0.13
            Signed: No
            Creator information:
              ID: SkoolKit 9.2
            Snapshot:
              Filename extension: sna
              Size: 131103 bytes
              Machine: 128K Spectrum
              Start address: 0
            Input recording
              Number of frames: 1 (0h00m00s)
              T-states: 0
              Encrypted: No
        """
        self._test_rzx(rzx, exp_output)

    def test_z80(self):
        ram = [0] * 49152
        z80data = self.write_z80_file(None, ram, ret_data=True)
        rzx = RZX()
        rzx.add_snapshot(z80data, 'z80')
        exp_output = """
            Version: 0.13
            Signed: No
            Creator information:
              ID: SkoolKit 9.2
            Snapshot:
              Filename extension: z80
              Size: 49247 bytes
              Machine: 48K Spectrum
              Start address: 0
            Input recording
              Number of frames: 1 (0h00m00s)
              T-states: 0
              Encrypted: No
        """
        self._test_rzx(rzx, exp_output)

    def test_szx(self):
        ram = [0] * 49152
        szxdata = self.write_szx(ram, ret_data=True)
        rzx = RZX()
        rzx.add_snapshot(szxdata, 'szx')
        exp_output = """
            Version: 0.13
            Signed: No
            Creator information:
              ID: SkoolKit 9.2
            Snapshot:
              Filename extension: szx
              Size: 174 bytes
              Machine: 48K ZX Spectrum
              Start address: 0
            Input recording
              Number of frames: 1 (0h00m00s)
              T-states: 0
              Encrypted: No
        """
        self._test_rzx(rzx, exp_output)

    def test_sna_compressed(self):
        sna = [0] * 49179
        rzx = RZX()
        rzx.add_snapshot(sna, 'sna', flags=2)
        exp_output = """
            Version: 0.13
            Signed: No
            Creator information:
              ID: SkoolKit 9.2
            Snapshot:
              Filename extension: sna
              Size: 49179 bytes
              Machine: 48K Spectrum
              Start address: 0
            Input recording
              Number of frames: 1 (0h00m00s)
              T-states: 0
              Encrypted: No
        """
        self._test_rzx(rzx, exp_output)

    def test_external_snapshot(self):
        rzx = RZX()
        descriptor = [0] * 4
        descriptor.extend(ord(c) for c in 'game.sna')
        descriptor.append(0)
        rzx.add_snapshot(descriptor, 'sna', flags=1)
        exp_output = """
            Version: 0.13
            Signed: No
            Creator information:
              ID: SkoolKit 9.2
            Snapshot:
              Filename extension: sna
              Size: 13 bytes
              External snapshot: game.sna
            Input recording
              Number of frames: 1 (0h00m00s)
              T-states: 0
              Encrypted: No
        """
        self._test_rzx(rzx, exp_output)

    def test_security(self):
        rzx = RZX()
        rzx.set_security()
        rzx.set_signature((1, 2, 3), (4, 5, 6))
        exp_output = """
            Version: 0.13
            Signed: No
            Creator information:
              ID: SkoolKit 9.2
            Security information
            Security signature
        """
        self._test_rzx(rzx, exp_output)

    def test_unknown_snapshot_type(self):
        rzx = RZX()
        rzx.add_snapshot([0] * 10, 'ust')
        exp_output = """
            Version: 0.13
            Signed: No
            Creator information:
              ID: SkoolKit 9.2
            Snapshot:
              Filename extension: ust
              Size: 10 bytes
              Machine: Unknown
              Start address: Unknown
            Input recording
              Number of frames: 1 (0h00m00s)
              T-states: 0
              Encrypted: No
        """
        self._test_rzx(rzx, exp_output)

    def test_unknown_block(self):
        rzx = RZX()
        rzx.set_security()
        rzx.set_signature((1, 2), (3, 4))
        rzx.signature[0] = 0xFF # Change block ID
        exp_output = """
            Version: 0.13
            Signed: No
            Creator information:
              ID: SkoolKit 9.2
            Security information
            Unknown block ID: 0xFF
        """
        self._test_rzx(rzx, exp_output)

    def test_invalid_option(self):
        output, error = self.run_rzxinfo('-x test.rzx', catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: rzxinfo.py'))

    def test_invalid_rzx(self):
        invalid_rzx = self.write_text_file('This is not an RZX file', suffix='.rzx')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxinfo(invalid_rzx)
        self.assertEqual(cm.exception.args[0], 'Not an RZX file')

    def test_option_extract(self):
        sna = [0] * 49179
        rzx = RZX()
        rzx.add_snapshot(sna, 'sna')
        rzxfile = self.write_rzx_file(rzx)
        output, error = self.run_rzxinfo(f'--extract {rzxfile}')
        self.assertEqual(error, '')
        exp_fname = f'{rzxfile}.001.sna'
        self.assertEqual(output, f'Extracted {exp_fname}\n')
        self.assertTrue(os.path.isfile(exp_fname))
        with open(exp_fname, 'rb') as f:
            self.assertEqual(sum(f.read()), 0)

    def test_option_extract_no_snapshots(self):
        sna = [0] * 49179
        rzx = RZX()
        rzx.set_creator('SkoolKit', 9, 2)
        rzxfile = self.write_rzx_file(rzx)
        output, error = self.run_rzxinfo(f'--extract {rzxfile}')
        self.assertEqual(error, '')
        self.assertEqual(output, f'No snapshots found\n')

    def test_option_extract_compressed_snapshot(self):
        sna = [0] * 49179
        rzx = RZX()
        rzx.add_snapshot(sna, 'sna', flags=2)
        rzxfile = self.write_rzx_file(rzx)
        output, error = self.run_rzxinfo(f'--extract {rzxfile}')
        self.assertEqual(error, '')
        exp_fname = f'{rzxfile}.001.sna'
        self.assertEqual(output, f'Extracted {exp_fname}\n')
        self.assertTrue(os.path.isfile(exp_fname))
        with open(exp_fname, 'rb') as f:
            self.assertEqual(sum(f.read()), 0)

    def test_option_frames(self):
        sna = [0] * 49179
        rzx = RZX()
        frames = (
            (1, 2, (3, 4)),     # Frame 0
            (10, 11, [5] * 11), # Frame 1
            (20, 65535, ()),    # Frame 2
        )
        rzx.add_snapshot(sna, 'sna', frames)
        exp_output = """
            Version: 0.13
            Signed: No
            Creator information:
              ID: SkoolKit 9.2
            Snapshot:
              Filename extension: sna
              Size: 49179 bytes
              Machine: 48K Spectrum
              Start address: 0
            Input recording
              Number of frames: 3 (0h00m00s)
              T-states: 0
              Encrypted: No
              Frame 0:
                Fetch counter: 1
                IN counter: 2
                Port readings: 3, 4
              Frame 1:
                Fetch counter: 10
                IN counter: 11
                Port readings: 5, 5, 5, 5, 5, 5, 5, 5, 5, 5...
              Frame 2:
                Fetch counter: 20
                IN counter: 65535
                Port readings: 5, 5, 5, 5, 5, 5, 5, 5, 5, 5...
        """
        self._test_rzx(rzx, exp_output, '--frames')

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_rzxinfo(option, catch_exit=0)
            self.assertEqual(output, f'SkoolKit {VERSION}\n')
