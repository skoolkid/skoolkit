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
    def _test_sim_load(self, url, tapname, tapsum, z80sum, options):
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
            tap2sna.main((*options.split(), '--reg', 'r=0', tapfile, z80file))
            with open(z80file, 'rb') as z:
                data = z.read()
            md5sum = hashlib.md5(data).hexdigest()
            if md5sum != z80sum:
                self.fail(f'Checksum failure for {z80file}: expected {z80sum}, got {md5sum}')

    def test_alcatraz(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/f/Fairlight48V1.tzx.zip',
            'Fairlight - 48k - Release 1.tzx',
            '1dba2ac53fd25f4cc1065e18e31a7b96',
            '551cd2d5ba4bf912987ccb1733c8e144',
            '--sim-load --start 50300'
        )

    def test_digital_integration(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/t/Tomahawk.tzx.zip',
            'Tomahawk.tzx',
            '3189a34157750d9e4ad01d5a7b2e5722',
            '8f7492f7f6030ef945b4045f2f2eefab',
            '--sim-load --start 57349'
        )

    def test_edge(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BrianBloodaxe.tzx.zip',
            'Brian Bloodaxe.tzx',
            '01b9b9454fc40eec0db0ba16ef2e6552',
            '423156b42f6f4ca4f50aa47a099c7432',
            '--sim-load'
        )

    def test_elite_uni_loader(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BombJackII.tzx.zip',
            'Bomb Jack 2.tzx',
            'a481286503c7eb94a7d8e62a73088fb6',
            '5addc5d94939d579cd8205a082329ad1',
            '--sim-load --start 30720',
        )

    def test_firebird_bleepload(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BlackLamp.tzx.zip',
            'Black Lamp.tzx',
            'fc9dd17a32679eeff80504af26e81d9b',
            '88fa2befca525004ae0aec8e6ac25ab6',
            '--sim-load --start 32768'
        )

    def test_ftl(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/h/Hydrofool.tzx.zip',
            'Hydrofool.tzx',
            'd3267bd1facb761c02efe0ddf4438ab4',
            '45c4c04e69303c97d44f962474dfaf73',
            '--sim-load --start 40252'
        )

    def test_headerless_block(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/g/GalacticPatrol.tzx.zip',
            'Galactic Patrol.tzx',
            '94827dbfba53fa26396d2d218990ed5b',
            '492741f99234886dd4f4275f506deb5b',
            '--sim-load'
        )

    def test_hewson_slowload(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/c/Cybernoid.tzx.zip',
            'Cybernoid.tzx',
            '50921a76ee625feb31c4195aac63d020',
            '300bc544ff0f6194156b49eec4887780',
            '--sim-load --start 65105'
        )

    def test_injectaload(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/o/Outcast.tzx.zip',
            'Outcast.tzx',
            'c01b3ac0075f46f6a0b16d75c163b6b3',
            '8326a1ad896440cb476acbd73830e56a',
            '--sim-load --start 23296'
        )

    def test_load_code(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/g/Gobstopper.tzx.zip',
            'Gob Stopper (Calisto).tzx',
            '43803187b78421dfe88bbfe3aa218b8d',
            'e2f9a35c6df859fa42ec518becfddc11',
            '--sim-load --start 40001'
        )

    def test_microsphere(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/s/SkoolDaze.tzx.zip',
            'Skool Daze.tzx',
            '61d29396661cc0acfa8f3514010f641d',
            '58d31ae46b4739e7dd45f5db680ad521',
            '--sim-load --start 24288'
        )

    def test_power_load(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/d/DynamiteDan.tzx.zip',
            'Dynamite Dan - Side 1.tzx',
            '38c2a7eb6c2ed9010e700063aedd3a3e',
            '93e02b62589dcaf61df4e1bef3ef4231',
            '--sim-load --start 65392'
        )

    def test_search_loader(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/t/TechnicianTed.tzx.zip',
            'Technician Ted.tzx',
            'b55a761f7d3733bc6ac958b10fab0c43',
            'e375834a70166f774fc96a81e7c430d0',
            '--sim-load --start 35892'
        )

    def test_softlock(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/e/Elite.tzx.zip',
            'Elite - 48k.tzx',
            'f73379181e1a413ac6c22ffd4cc8122a',
            '9e97cd1fcc8c760fa26d0e82a6ba98e6',
            '--sim-load-all --start 49699'
        )

    def test_speedlock_1(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BruceLee.tzx.zip',
            'Bruce Lee.tzx',
            '51cb1a6e1fb58304a15a588b82d8e001',
            'd61f1e9e168ebf4d3d9396ab3b0e8e0f',
            '--sim-load --start 49152'
        )

    def test_speedlock_2(self):
        self._test_sim_load(
            'http://www.worldofspectrum.org/pub/sinclair/games/g/GreatEscapeThe.tzx.zip',
            'The Great Escape.tzx',
            '58d273a2c719da21a25b4af3d008c951',
            'b88e2ecec1935cb3183b95ba2b20a50c',
            '--sim-load --start 61795'
        )

    def test_speedlock_3(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/d/Dogfight-2187.tzx.zip',
            'Dogfight 2187.tzx',
            '5d73a347e27e98bb5a235eeac6470d56',
            '1957b7689fa347e86c0bb6b7cf8171c8',
            '--sim-load --start 65317'
        )

    def test_speedlock_4(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/o/OutRun.tzx.zip',
            'Outrun - Tape 1 - Side 1.tzx',
            '78fb2a6b82ca2dc7021a5762ea1491fb',
            '9c55792ec44f90b6d4717f8cceed91d2',
            '--sim-load --start 44337'
        )

    def test_speedlock_5(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/h/Hysteria.tzx.zip',
            'Hysteria.tzx',
            '2f4485c0d0e98758f7da09b322ca0a0c',
            '541444a0b93ff969bec20d013ef43932',
            '--sim-load --start 45066'
        )

    def test_speedlock_6(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/v/Vixen.tzx.zip',
            'Vixen - Side A.tzx',
            '3075d03f63d20acf2ad029265f6f1746',
            'b424bb0f28cb05dbaf84afcd1e2a744c',
            '--sim-load --start 51473'
        )

    def test_speedlock_7(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/a/Aaargh.tzx.zip',
            'Aaargh! - Side 1.tzx',
            'cfe091069af70b7ad7eae377665ce284',
            '7ddc438e3f8e3a5635b3e19615227ace',
            '--sim-load --start 65283'
        )

    def test_standard_load(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/m/ManicMiner.tzx.zip',
            'Manic Miner.tzx',
            '2750ccb6c240d14516c448e94f8d200e',
            'f108f54410e9d7047b54bfa6cd25ce00',
            '--sim-load'
        )

if __name__ == '__main__':
    unittest.main()
