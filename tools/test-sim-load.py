#!/usr/bin/env python3
import hashlib
import os
import sys
import tempfile
import unittest
from urllib.request import Request, urlopen
import zipfile

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, f'{SKOOLKIT_HOME}')

from skoolkit import tap2sna

class SimLoadTest(unittest.TestCase):
    def _test_sim_load(self, url, tapname, tapsum, z80sum, *options):
        r = Request(url)
        u = urlopen(r, timeout=30)
        with tempfile.NamedTemporaryFile() as f:
            while 1:
                data = bytearray(u.read(4096))
                if not data:
                    break
                f.write(data)
            z = zipfile.ZipFile(f)
            tape = z.open(tapname)
            data = bytearray(tape.read())
            md5sum = hashlib.md5(data).hexdigest()
            if md5sum != tapsum:
                self.fail(f'Checksum failure for {tapname}: expected {tapsum}, got {md5sum}')

        with tempfile.TemporaryDirectory() as d:
            tapfile = f'{d}/{tapname}'
            with open(tapfile, 'wb') as t:
                t.write(data)
            z80file = f'{d}/{tapname[:-4]}.z80'
            tap2sna.main(('--sim-load', *options, tapfile, z80file))
            with open(z80file, 'rb') as z:
                data = z.read()
            md5sum = hashlib.md5(data).hexdigest()
            if md5sum != z80sum:
                self.fail(f'Checksum failure for {z80file}: expected {z80sum}, got {md5sum}')

    def test_black_lamp(self):
        # Firebird BleepLoad
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BlackLamp.tzx.zip',
            'Black Lamp.tzx',
            'fc9dd17a32679eeff80504af26e81d9b',
            'c057416bf9337be90cb4975b27ba8f82',
            '--start', '32768'
        )

    def test_fairlight(self):
        # Alcatraz
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/f/Fairlight48V1.tzx.zip',
            'Fairlight - 48k - Release 1.tzx',
            '1dba2ac53fd25f4cc1065e18e31a7b96',
            'ff5a6c268b0750e9f445874964aaf8f7',
            '--start', '50300'
        )

    def test_skool_daze(self):
        # Microsphere
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/s/SkoolDaze.tzx.zip',
            'Skool Daze.tzx',
            '61d29396661cc0acfa8f3514010f641d',
            '03a148f65e1d6c4c0a131cb97ae8cf91',
            '--start', '24288'
        )

    def test_the_great_escape(self):
        # Speedlock 2
        self._test_sim_load(
            'http://www.worldofspectrum.org/pub/sinclair/games/g/GreatEscapeThe.tzx.zip',
            'The Great Escape.tzx',
            '58d273a2c719da21a25b4af3d008c951',
            'a1b300af35e7103ca221459adcb04196',
            '--start', '61795'
        )

if __name__ == '__main__':
    unittest.main()
