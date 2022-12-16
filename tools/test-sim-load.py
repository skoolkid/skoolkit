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

    def test_alkatraz(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/f/Fairlight48V1.tzx.zip',
            'Fairlight - 48k - Release 1.tzx',
            '1dba2ac53fd25f4cc1065e18e31a7b96',
            '551cd2d5ba4bf912987ccb1733c8e144',
            '--sim-load --start 50300'
        )

    def test_alkatraz2_accelerator(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/s/ShadowDancer.tzx.zip',
            'Shadow Dancer - Side 1.tzx',
            '2515ea4bb465b2834a636007ed3b9138',
            'bfa6fa51d5509dd3f278dd6cd6564195',
            '--sim-load --accelerator alkatraz2 --start 24000'
        )

    def test_cyberlode_1_1(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/c/Cauldron(SilverbirdSoftwareLtd).tzx.zip',
            'Cauldron (Silverbird).tzx',
            'ebd4fa565c35af13f0aa3dc2f7556721',
            'ccbbb5b5964fe071b7a87d7af6e0fad0',
            '--sim-load --accelerator cyberlode --start 23296'
        )

    def test_digital_integration(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/t/Tomahawk.tzx.zip',
            'Tomahawk.tzx',
            '3189a34157750d9e4ad01d5a7b2e5722',
            '8f7492f7f6030ef945b4045f2f2eefab',
            '--sim-load --accelerator digital-integration --start 57349'
        )

    def test_dinaload(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/s/Satan.tzx.zip',
            'Satan - Side 1.tzx',
            '18afd7805b83ebc4974ccd8637d8a7b3',
            'b4ef1345a3dee1efd27c11e1fc590ace',
            '--sim-load --accelerator dinaload --start 64031'
        )

    def test_edge(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BrianBloodaxe.tzx.zip',
            'Brian Bloodaxe.tzx',
            '01b9b9454fc40eec0db0ba16ef2e6552',
            '423156b42f6f4ca4f50aa47a099c7432',
            '--sim-load --accelerator edge'
        )

    def test_elite_uni_loader(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BombJackII.tzx.zip',
            'Bomb Jack 2.tzx',
            'a481286503c7eb94a7d8e62a73088fb6',
            '5addc5d94939d579cd8205a082329ad1',
            '--sim-load --accelerator elite-uni-loader --start 30720',
        )

    def test_excelerator(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/l/LastMohican.tzx.zip',
            'The Last Mohican - Side 1.tzx',
            '13fd349168a4561dae88e6280b94eac9',
            '6eb14a6122658245b7adf0a9003eee7e',
            '--sim-load --accelerator excelerator --start 65492'
        )

    def test_firebird_bleepload(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BlackLamp.tzx.zip',
            'Black Lamp.tzx',
            'fc9dd17a32679eeff80504af26e81d9b',
            '88fa2befca525004ae0aec8e6ac25ab6',
            '--sim-load --accelerator bleepload --start 32768'
        )

    def test_flash_loader(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/c/CliffHanger.tzx.zip',
            'Cliff Hanger.tzx',
            '08b2d3867c9478e446c49217595239be',
            '9a899546787a31eae484b360c5e8b0ae',
            '--sim-load --accelerator flash-loader --start 25660'
        )

    def test_ftl(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/h/Hydrofool.tzx.zip',
            'Hydrofool.tzx',
            'd3267bd1facb761c02efe0ddf4438ab4',
            '45c4c04e69303c97d44f962474dfaf73',
            '--sim-load --accelerator ftl --start 40252'
        )

    def test_gargoyle(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/h/HeavyOnTheMagick.tzx.zip',
            'Heavy On The Magick - Side 1.tzx',
            '203b36a9ffa241089cb2741043c6563a',
            'bf0240ba95a094e1c853c34907f136ad',
            '--sim-load --accelerator gargoyle --start 46193'
        )

    def test_gremlin_accelerator(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/s/SpaceCrusade.tzx.zip',
            'Space Crusade - 48K.tzx',
            '48cdfc186f94bf6382da93cbc4b70810',
            '14fcd61588554a50a96e4d1988a8e798',
            '--sim-load --accelerator gremlin --start 26807'
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
            '--sim-load --accelerator hewson-slowload --start 65105'
        )

    def test_injectaload(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/o/Outcast.tzx.zip',
            'Outcast.tzx',
            'c01b3ac0075f46f6a0b16d75c163b6b3',
            '8326a1ad896440cb476acbd73830e56a',
            '--sim-load --accelerator injectaload --start 23296'
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
            '--sim-load --accelerator microsphere --start 24288'
        )

    def test_microsphere_2(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/c/ContactSamCruise.tzx.zip',
            'Contact Sam Cruise.tzx',
            '873cb6de4edc2aa75b40b838981c6f72',
            '403cfc4f5e3a1f3161e6398d39d4d797',
            '--sim-load --accelerator rom --start 61671'
        )

    def test_paul_owens(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/u/UntouchablesThe.tzx.zip',
            'The Untouchables - Side 1.tzx',
            '7aed7cb0aa7a9be5a4c953eec1fc0dd1',
            '3ddab5e5ade1fc259b8f64369698a077',
            '--sim-load-all --accelerator paul-owens --start 32839'
        )

    def test_poliload(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/a/AstroMarineCorps.tzx.zip',
            'Astro Marine Corps - Side 1.tzx',
            'b31fd6232a865fbef93db8700ceeb931',
            '0f8710bdf41fe3235a5cf4d8d8bbdd76',
            '--sim-load --accelerator poliload --start 60928'
        )

    def test_power_load(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/d/DynamiteDan.tzx.zip',
            'Dynamite Dan - Side 1.tzx',
            '38c2a7eb6c2ed9010e700063aedd3a3e',
            '93e02b62589dcaf61df4e1bef3ef4231',
            '--sim-load --accelerator power-load --start 65392'
        )

    def test_search_loader(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BloodBrothers.tzx.zip',
            'Blood Brothers.tzx',
            'c4e7e151c4321b29c095abf1e547f9b5',
            '28548a9187bb63526cb5c06fe7ecfd5f',
            '--sim-load --accelerator search-loader --start 23552'
        )

    def test_softlock(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/e/Elite.tzx.zip',
            'Elite - 48k.tzx',
            'f73379181e1a413ac6c22ffd4cc8122a',
            '736305fea2616efdc80109d23fd46ea3',
            '--sim-load-all --accelerator softlock --start 49699'
        )

    def test_speedlock_1(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BruceLee.tzx.zip',
            'Bruce Lee.tzx',
            '51cb1a6e1fb58304a15a588b82d8e001',
            'd61f1e9e168ebf4d3d9396ab3b0e8e0f',
            '--sim-load --accelerator speedlock --start 49152'
        )

    def test_speedlock_2(self):
        self._test_sim_load(
            'http://www.worldofspectrum.org/pub/sinclair/games/g/GreatEscapeThe.tzx.zip',
            'The Great Escape.tzx',
            '58d273a2c719da21a25b4af3d008c951',
            'b88e2ecec1935cb3183b95ba2b20a50c',
            '--sim-load --accelerator speedlock --start 61795'
        )

    def test_speedlock_3(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/d/Dogfight-2187.tzx.zip',
            'Dogfight 2187.tzx',
            '5d73a347e27e98bb5a235eeac6470d56',
            '1957b7689fa347e86c0bb6b7cf8171c8',
            '--sim-load --accelerator speedlock --start 65317'
        )

    def test_speedlock_4(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/o/OutRun.tzx.zip',
            'Outrun - Tape 1 - Side 1.tzx',
            '78fb2a6b82ca2dc7021a5762ea1491fb',
            '9c55792ec44f90b6d4717f8cceed91d2',
            '--sim-load --accelerator speedlock --start 44337'
        )

    def test_speedlock_5(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/h/Hysteria.tzx.zip',
            'Hysteria.tzx',
            '2f4485c0d0e98758f7da09b322ca0a0c',
            '541444a0b93ff969bec20d013ef43932',
            '--sim-load --accelerator speedlock --start 45066'
        )

    def test_speedlock_6(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/v/Vixen.tzx.zip',
            'Vixen - Side A.tzx',
            '3075d03f63d20acf2ad029265f6f1746',
            'b424bb0f28cb05dbaf84afcd1e2a744c',
            '--sim-load --accelerator speedlock --start 51473'
        )

    def test_speedlock_7(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/a/Aaargh.tzx.zip',
            'Aaargh! - Side 1.tzx',
            'cfe091069af70b7ad7eae377665ce284',
            '7ddc438e3f8e3a5635b3e19615227ace',
            '--sim-load --accelerator speedlock --start 65283'
        )

    def test_standard_load(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/m/ManicMiner.tzx.zip',
            'Manic Miner.tzx',
            '2750ccb6c240d14516c448e94f8d200e',
            'f108f54410e9d7047b54bfa6cd25ce00',
            '--sim-load'
        )

    def test_zydroload(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/l/LightCorridorThe.tzx.zip',
            'The Light Corridor.tzx',
            '66674ee9c6b696404c5847be32796af4',
            'af4a82be85d882064cdc30c7e336065a',
            '--sim-load --accelerator zydroload --start 32879'
        )

if __name__ == '__main__':
    unittest.main()
