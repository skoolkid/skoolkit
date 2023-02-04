import hashlib
import tempfile
from urllib.request import Request, urlopen
import zipfile

from skoolkittest import SkoolKitTestCase
from skoolkit import tap2sna

class SimLoadGamesTest(SkoolKitTestCase):
    def _test_sim_load(self, url, tapname, tapsum, z80sum, options=''):
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
            tap2sna.main(('--sim-load', '--reg', 'r=0', *options.split(), tapfile, z80file))
            with open(z80file, 'rb') as z:
                data = z.read()
            md5sum = hashlib.md5(data).hexdigest()
            if md5sum != z80sum:
                output = self.out.getvalue()
                self.fail(f'\n{output}\nChecksum failure for {z80file}: expected {z80sum}, got {md5sum}')

    def test_alkatraz(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/f/Fairlight48V1.tzx.zip',
            'Fairlight - 48k - Release 1.tzx',
            '1dba2ac53fd25f4cc1065e18e31a7b96',
            '551cd2d5ba4bf912987ccb1733c8e144',
            '-c accelerator=alkatraz --start 50300'
        )

    def test_alkatraz2(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/s/ShadowDancer.tzx.zip',
            'Shadow Dancer - Side 1.tzx',
            '2515ea4bb465b2834a636007ed3b9138',
            '19fdd84ecb94724ad95f5983298fe90a',
            '-c accelerator=alkatraz2 --start 24000'
        )

    def test_basil_the_great_mouse_detective(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BasilTheGreatMouseDetective.tzx.zip',
            'Basil The Great Mouse Detective.tzx',
            '5e213d8a847168db2a9721f88cb1e280',
            '1bafcd0202d96db61dc8432ef68eeb7d',
            '-c polarity=1 --start 32768'
        )

    def test_battle_of_britain(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BattleOfBritain_2.tzx.zip',
            'Battle Of Britain (PSS).tzx',
            '6b1005a547ede2687449cf11788e7dd3',
            '2d0fb4ba5ff954644da46dc468ca2d3d',
            '-c pause=0 -c accelerator=rom --start 27078'
        )

    def test_cattell_iq_test(self):
        # Reads port 65531 to detect a printer
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/utils/CattellIQTest.tzx.zip',
            'Cattel IQ Test.tzx',
            'a3ad457e8f4b1bf9794b021678b9ce18',
            'b870c1f58f3a6f5327b14b3186ede694'
        )

    def test_chromoload2(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/s/Skyway.tzx.zip',
            'Skyway.tzx',
            '78bc636a3eceff22141a26a720e2c0bb',
            'beff4e5a1317d1054cf01a9692fd942b',
            '-c accelerator=speedlock --start 64963'
        )

    def test_cyberlode_1_1(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/c/Cauldron(SilverbirdSoftwareLtd).tzx.zip',
            'Cauldron (Silverbird).tzx',
            'ebd4fa565c35af13f0aa3dc2f7556721',
            'ccbbb5b5964fe071b7a87d7af6e0fad0',
            '-c accelerator=cyberlode --start 23296'
        )

    def test_digital_integration(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/t/Tomahawk.tzx.zip',
            'Tomahawk.tzx',
            '3189a34157750d9e4ad01d5a7b2e5722',
            '8f7492f7f6030ef945b4045f2f2eefab',
            '-c accelerator=digital-integration --start 57349'
        )

    def test_dinaload(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/s/Satan.tzx.zip',
            'Satan - Side 1.tzx',
            '18afd7805b83ebc4974ccd8637d8a7b3',
            '81a50399217957c91fd04334b099b7df',
            '-c accelerator=dinaload --start 64031'
        )

    def test_edge(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BrianBloodaxe.tzx.zip',
            'Brian Bloodaxe.tzx',
            '01b9b9454fc40eec0db0ba16ef2e6552',
            '15f9b29d0e807d25f40a3c5d7815d539',
            '-c accelerator=edge'
        )

    def test_elite_uni_loader(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BombJackII.tzx.zip',
            'Bomb Jack 2.tzx',
            'a481286503c7eb94a7d8e62a73088fb6',
            '281deba8be7dd833d03fa00c97e206ff',
            '-c accelerator=elite-uni-loader --start 30720',
        )

    def test_excelerator(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/l/LastMohican.tzx.zip',
            'The Last Mohican - Side 1.tzx',
            '13fd349168a4561dae88e6280b94eac9',
            '6eb14a6122658245b7adf0a9003eee7e',
            '-c accelerator=excelerator --start 65492'
        )

    def test_firebird_bleepload(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BlackLamp.tzx.zip',
            'Black Lamp.tzx',
            'fc9dd17a32679eeff80504af26e81d9b',
            'cc8feba825f1ff5325ecd29b5bfaa58b',
            '-c accelerator=bleepload --start 32768'
        )

    def test_flash_loader(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/c/CliffHanger.tzx.zip',
            'Cliff Hanger.tzx',
            '08b2d3867c9478e446c49217595239be',
            '325b4b3eb08a2099eef495b1a41734b0',
            '-c accelerator=flash-loader --start 25660'
        )

    def test_ftl(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/h/Hydrofool.tzx.zip',
            'Hydrofool.tzx',
            'd3267bd1facb761c02efe0ddf4438ab4',
            '45c4c04e69303c97d44f962474dfaf73',
            '-c accelerator=ftl --start 40252'
        )

    def test_gargoyle(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/h/HeavyOnTheMagick.tzx.zip',
            'Heavy On The Magick - Side 1.tzx',
            '203b36a9ffa241089cb2741043c6563a',
            'bf0240ba95a094e1c853c34907f136ad',
            '-c accelerator=gargoyle --start 46193'
        )

    def test_gremlin(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/s/SpaceCrusade.tzx.zip',
            'Space Crusade - 48K.tzx',
            '48cdfc186f94bf6382da93cbc4b70810',
            '17e91ab06a5a952661aa83f5ad06d18b',
            '-c accelerator=gremlin --start 26807'
        )

    def test_haxpoc_lock(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/s/StarWarsV1.tzx.zip',
            'Star Wars - Release 1 - Side 1.tzx',
            'e36c32fd456f65801d4abfd1af382a65',
            '3099ce51ae2b2dad4c9d0fc01e8109d9',
            '--tape-start 6 -c accelerator=rom --start 65451'
        )

    def test_headerless_block(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/g/GalacticPatrol.tzx.zip',
            'Galactic Patrol.tzx',
            '94827dbfba53fa26396d2d218990ed5b',
            '16bdfebafd6a2700e7936620f920e9ba'
        )

    def test_hewson_slowload(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/c/Cybernoid.tzx.zip',
            'Cybernoid.tzx',
            '50921a76ee625feb31c4195aac63d020',
            '2e00d53a761c1169ddefd078519e0438',
            '-c accelerator=hewson-slowload --start 65105'
        )

    def test_injectaload(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/o/Outcast.tzx.zip',
            'Outcast.tzx',
            'c01b3ac0075f46f6a0b16d75c163b6b3',
            '8326a1ad896440cb476acbd73830e56a',
            '-c accelerator=injectaload --start 23296'
        )

    def test_load_code(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/g/Gobstopper.tzx.zip',
            'Gob Stopper (Calisto).tzx',
            '43803187b78421dfe88bbfe3aa218b8d',
            'e2f9a35c6df859fa42ec518becfddc11',
            '--start 40001'
        )

    def test_microsphere(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/s/SkoolDaze.tzx.zip',
            'Skool Daze.tzx',
            '61d29396661cc0acfa8f3514010f641d',
            '58d31ae46b4739e7dd45f5db680ad521',
            '-c accelerator=microsphere --start 24288'
        )

    def test_microsphere_2(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/c/ContactSamCruise.tzx.zip',
            'Contact Sam Cruise.tzx',
            '873cb6de4edc2aa75b40b838981c6f72',
            '0d253fcd2757a22c30b98bebcb7a957e',
            '-c accelerator=rom --start 61671'
        )

    def test_paul_owens(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/u/UntouchablesThe.tzx.zip',
            'The Untouchables - Side 1.tzx',
            '7aed7cb0aa7a9be5a4c953eec1fc0dd1',
            '3ddab5e5ade1fc259b8f64369698a077',
            '--start 32839'
        )

    def test_poliload(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/a/AstroMarineCorps.tzx.zip',
            'Astro Marine Corps - Side 1.tzx',
            'b31fd6232a865fbef93db8700ceeb931',
            'ae8d096824184308a7ecac0be1cd09f7',
            '-c accelerator=poliload --start 60928'
        )

    def test_power_load(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/d/DynamiteDan.tzx.zip',
            'Dynamite Dan - Side 1.tzx',
            '38c2a7eb6c2ed9010e700063aedd3a3e',
            '93e02b62589dcaf61df4e1bef3ef4231',
            '-c accelerator=power-load --start 65392'
        )

    def test_search_loader(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BloodBrothers.tzx.zip',
            'Blood Brothers.tzx',
            'c4e7e151c4321b29c095abf1e547f9b5',
            '28548a9187bb63526cb5c06fe7ecfd5f',
            '-c accelerator=search-loader --start 23552'
        )

    def test_sinclair_user(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/p/PiecesOfEight.tzx.zip',
            'Pieces Of Eight (1992)(Pirate Software - Sinclair User)[SU Loader].tzx',
            '62da22ff8b0f6e704b4e1a509d285e40',
            'e51a28f2efb4882055d091fe4c8c2911',
            '-c accelerator=bleepload --start 16394'
        )

    def test_softlock(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/e/Elite.tzx.zip',
            'Elite - 48k.tzx',
            'f73379181e1a413ac6c22ffd4cc8122a',
            '89d40a5c08bf1156a2201b5262b8bf8e',
            '-c accelerator=softlock --start 49699'
        )

    def test_speedlock_1(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/b/BruceLee.tzx.zip',
            'Bruce Lee.tzx',
            '51cb1a6e1fb58304a15a588b82d8e001',
            '55d57a83133f75e5a62e18ec2b9a0661',
            '-c accelerator=speedlock --start 49152'
        )

    def test_speedlock_2(self):
        self._test_sim_load(
            'http://www.worldofspectrum.org/pub/sinclair/games/g/GreatEscapeThe.tzx.zip',
            'The Great Escape.tzx',
            '58d273a2c719da21a25b4af3d008c951',
            'b88e2ecec1935cb3183b95ba2b20a50c',
            '-c accelerator=speedlock --start 61795'
        )

    def test_speedlock_3(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/d/Dogfight-2187.tzx.zip',
            'Dogfight 2187.tzx',
            '5d73a347e27e98bb5a235eeac6470d56',
            '1957b7689fa347e86c0bb6b7cf8171c8',
            '-c accelerator=speedlock --start 65317'
        )

    def test_speedlock_4(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/o/OutRun.tzx.zip',
            'Outrun - Tape 1 - Side 1.tzx',
            '78fb2a6b82ca2dc7021a5762ea1491fb',
            '96fea752c0043da70211811ed234d1f6',
            '-c accelerator=speedlock --start 44337'
        )

    def test_speedlock_5(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/h/Hysteria.tzx.zip',
            'Hysteria.tzx',
            '2f4485c0d0e98758f7da09b322ca0a0c',
            '561c6e8b4000e9c9817c0033a73d00e1',
            '-c accelerator=speedlock --start 45066'
        )

    def test_speedlock_6(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/v/Vixen.tzx.zip',
            'Vixen - Side A.tzx',
            '3075d03f63d20acf2ad029265f6f1746',
            'e51a85f6d3c043d1a62d09fad3a61b97',
            '-c accelerator=speedlock --start 51473'
        )

    def test_speedlock_7(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/a/Aaargh.tzx.zip',
            'Aaargh! - Side 1.tzx',
            'cfe091069af70b7ad7eae377665ce284',
            '41a96f08fbab265954501658e00ab43a',
            '-c accelerator=speedlock --start 65283'
        )

    def test_standard_load(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/m/ManicMiner.tzx.zip',
            'Manic Miner.tzx',
            '2750ccb6c240d14516c448e94f8d200e',
            '24bb22d264e97d3abf9117598ed83587'
        )

    def test_technician_ted(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/t/TechnicianTed.tzx.zip',
            'Technician Ted.tzx',
            'b55a761f7d3733bc6ac958b10fab0c43',
            '6e5a843057270e4a84c74de609facd61',
            '-c accelerator=rom --start 35892'
        )

    def test_zydroload(self):
        self._test_sim_load(
            'https://www.worldofspectrum.org/pub/sinclair/games/l/LightCorridorThe.tzx.zip',
            'The Light Corridor.tzx',
            '66674ee9c6b696404c5847be32796af4',
            '00bd9804e8fb80d97f81b7f9dec1f5fd',
            '-c accelerator=zydroload --start 32879'
        )
