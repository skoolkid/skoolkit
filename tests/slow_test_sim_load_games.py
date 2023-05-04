import hashlib
import tempfile

from skoolkittest import SkoolKitTestCase
from skoolkit import tap2sna
from skoolkit.snapinfo import parse_snapshot
from skoolkit.snapshot import get_snapshot

class SimLoadGamesTest(SkoolKitTestCase):
    def _test_sim_load(self, url, tapname, tapsum, ramsum, reg, options=''):
        with tempfile.TemporaryDirectory() as d:
            z80file = f'{d}/{tapname[:-4]}.z80'
            tap2sna.main(('--sim-load', '--reg', 'r=0', '--tape-name', tapname, '--tape-sum', tapsum, *options.split(), url, z80file))
            ram = get_snapshot(z80file)[16384:]
            md5sum = hashlib.md5(bytes(ram)).hexdigest()
            if md5sum != ramsum:
                output = self.out.getvalue()
                self.fail(f'\n{output}\nChecksum failure for RAM in {z80file}: expected {ramsum}, got {md5sum}')
            r = parse_snapshot(z80file)[1]
            rvals = {
                "AF,BC,DE,HL": f'{r.a:02X}{r.f:02X},{r.bc:04X},{r.de:04X},{r.hl:04X}',
                "AF',BC',DE',HL'": f'{r.a2:02X}{r.f2:02X},{r.bc2:04X},{r.de2:04X},{r.hl2:04X}',
                "PC,SP,IX,IY": f'{r.pc:04X},{r.sp:04X},{r.ix:04X},{r.iy:04X}',
                "IR,iff,im,border": f'{r.i:02X}{r.r:02X},{r.iff2},{r.im},{r.border}'
            }
            self.assertEqual(reg, rvals)

    def test_alkatraz(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/f/Fairlight48V1.tzx.zip',
            'Fairlight - 48k - Release 1.tzx',
            '1dba2ac53fd25f4cc1065e18e31a7b96',
            '8f0e202556d8f0973546c9604e0cbffe',
            {
                'AF,BC,DE,HL': 'D680,0002,DCC7,DCC6',
                "AF',BC',DE',HL'": 'FFAC,0348,4022,DBDD',
                'PC,SP,IX,IY': 'C47C,DADB,DADC,5C3A',
                'IR,iff,im,border': '3F00,0,1,0'
            },
            '-c accelerator=alkatraz --start 50300'
        )

    def test_alkatraz2(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/ShadowDancer.tzx.zip',
            'Shadow Dancer - Side 1.tzx',
            '2515ea4bb465b2834a636007ed3b9138',
            '06e31baae80d22a24d3885ffee5558ba',
            {
                'AF,BC,DE,HL': '0069,0000,5DFE,E9E3',
                "AF',BC',DE',HL'": 'FF45,1621,369B,2758',
                'PC,SP,IX,IY': '5DC0,E900,5800,5C3A',
                'IR,iff,im,border': '3F00,0,1,0'
            },
            '-c accelerator=alkatraz2 --start 24000'
        )

    def test_basil_the_great_mouse_detective(self):
        # The loader for this game is polarity-sensitive
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/b/BasilTheGreatMouseDetective.tzx.zip',
            'Basil The Great Mouse Detective.tzx',
            '5e213d8a847168db2a9721f88cb1e280',
            '64f367b3cb90c4abca77026b60d42b47',
            {
                'AF,BC,DE,HL': '0042,DA00,0027,3B6A',
                "AF',BC',DE',HL'": 'FF81,00C7,369B,2758',
                'PC,SP,IX,IY': '8000,6961,DAE2,5C3A',
                'IR,iff,im,border': '0000,0,1,0'
            },
            '-c first-edge=0 --start 32768'
        )

    def test_battle_of_britain(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/b/BattleOfBritain_2.tzx.zip',
            'Battle Of Britain (PSS).tzx',
            '6b1005a547ede2687449cf11788e7dd3',
            'c838a20b3728761f4574a81069df6612',
            {
                'AF,BC,DE,HL': '0093,B021,0000,0004',
                "AF',BC',DE',HL'": '2165,1621,5CBC,0000',
                'PC,SP,IX,IY': '69C6,6588,FFDC,5C3A',
                'IR,iff,im,border': '3F00,0,1,1'
            },
            '-c pause=0 -c accelerator=rom --start 27078'
        )

    def test_cattell_iq_test(self):
        # Reads port 65531 to detect a printer
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/utils/c/CattellIQTest.tzx.zip',
            'Cattel IQ Test.tzx',
            'a3ad457e8f4b1bf9794b021678b9ce18',
            'c5d4e2ceb2cfa08dedd85587974909ac',
            {
                'AF,BC,DE,HL': '2F0B,CEFE,0100,5D7F',
                "AF',BC',DE',HL'": 'FF81,1221,369B,0000',
                'PC,SP,IX,IY': 'F7F7,D310,5B80,5C3A',
                'IR,iff,im,border': 'FD00,0,2,7'
            }
        )

    def test_chromoload2(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/Skyway.tzx.zip',
            'Skyway.tzx',
            '78bc636a3eceff22141a26a720e2c0bb',
            '66dc99668dc48298e7196eaa31be6df8',
            {
                'AF,BC,DE,HL': '0050,0021,F894,8F01',
                "AF',BC',DE',HL'": '7B69,1705,0017,2758',
                'PC,SP,IX,IY': 'FDC3,0000,EFE3,5C3A',
                'IR,iff,im,border': '3F00,1,1,0'
            },
            '-c accelerator=speedlock --start 64963'
        )

    def test_contended_in(self):
        # Has a custom loading routine in what is contended memory on a
        # standard 48K Spectrum
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/Sapper.tzx.zip',
            'sapper.tzx',
            'e8f2e39a382c56c82318e1a92dd69274',
            '038cabb1ffe56e8e9793e39b9808a597',
            {
                'AF,BC,DE,HL': '0093,B05E,0000,002E',
                "AF',BC',DE',HL'": '5E4D,1621,369B,2758',
                'PC,SP,IX,IY': '5EAB,5E87,FFE7,5C3A',
                'IR,iff,im,border': '3F00,1,1,0'
            },
            '-c contended-in=1 --start 24235'
        )

    def test_cyberlode_1_1(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/c/Cauldron(SilverbirdSoftwareLtd).tzx.zip',
            'Cauldron (Silverbird).tzx',
            'ebd4fa565c35af13f0aa3dc2f7556721',
            '8ce481286e084f0ff15bbae38e52cdb1',
            {
                'AF,BC,DE,HL': '0044,0000,18EE,4212',
                "AF',BC',DE',HL'": '0044,1621,369B,0000',
                'PC,SP,IX,IY': '5B00,0000,FF0C,3584',
                'IR,iff,im,border': 'FF00,0,2,1'
            },
            '-c accelerator=cyberlode --start 23296'
        )

    def test_digital_integration(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/t/Tomahawk.tzx.zip',
            'Tomahawk.tzx',
            '3189a34157750d9e4ad01d5a7b2e5722',
            'c4c8e907d66af45eb011f927ae58a0ed',
            {
                'AF,BC,DE,HL': 'B342,FFF1,B35C,0000',
                "AF',BC',DE',HL'": 'FF45,0000,369B,FFF2',
                'PC,SP,IX,IY': 'E005,FFFE,FC69,FFD1',
                'IR,iff,im,border': '3980,0,2,6'
            },
            '-c accelerator=digital-integration --start 57349'
        )

    def test_dinaload(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/Satan.tzx.zip',
            'Satan - Side 1.tzx',
            '18afd7805b83ebc4974ccd8637d8a7b3',
            'e361a4d0cef9278f347b8268a709ec02',
            {
                'AF,BC,DE,HL': '0044,0000,DE34,FBC4',
                "AF',BC',DE',HL'": '5E4D,1621,369B,2758',
                'PC,SP,IX,IY': 'FA1F,FFFF,FC12,5C3A',
                'IR,iff,im,border': '3F00,0,1,1'
            },
            '-c accelerator=dinaload --start 64031'
        )

    def test_edge(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/b/BrianBloodaxe.tzx.zip',
            'Brian Bloodaxe.tzx',
            '01b9b9454fc40eec0db0ba16ef2e6552',
            '914fcdc792accca76b3b269a0979e080',
            {
                'AF,BC,DE,HL': 'FF40,0000,099C,053F',
                "AF',BC',DE',HL'": 'FF69,1621,369B,2758',
                'PC,SP,IX,IY': '053F,9085,0004,5C3A',
                'IR,iff,im,border': '3F00,0,1,5'
            },
            '-c accelerator=edge'
        )

    def test_elite_uni_loader(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/b/BombJackII.tzx.zip',
            'Bomb Jack 2.tzx',
            'a481286503c7eb94a7d8e62a73088fb6',
            'f50ddae742a407cc12b5bd47b5de4743',
            {
                'AF,BC,DE,HL': '0044,0000,7147,5B16',
                "AF',BC',DE',HL'": '7E6C,0305,0004,2758',
                'PC,SP,IX,IY': '7800,5B17,E9CF,5C3A',
                'IR,iff,im,border': '3F00,0,1,2'
            },
            '-c accelerator=elite-uni-loader --start 30720',
        )

    def test_excelerator(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/l/LastMohican.tzx.zip',
            'The Last Mohican - Side 1.tzx',
            '13fd349168a4561dae88e6280b94eac9',
            '1f6fb07d9f4c6d6451fe946421fa8c82',
            {
                'AF,BC,DE,HL': '0193,D4FE,0000,00D2',
                "AF',BC',DE',HL'": '0044,1621,369B,0000',
                'PC,SP,IX,IY': 'FFD4,0000,FF10,9B21',
                'IR,iff,im,border': 'FF80,0,1,1'
            },
            '-c accelerator=excelerator --start 65492'
        )

    def test_finish_tape(self):
        # Hits the given start address (23367) before the tape has finished
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/g/Gallipoli.tzx.zip',
            'Gallipoli - 48k.tzx',
            '1cdd5f519c467f434e67b910e171052d',
            '1ba89616d2d1e9defbb68d13e8d4293e',
            {
                'AF,BC,DE,HL': '0001,0000,0000,053F',
                "AF',BC',DE',HL'": 'FFA9,0021,369B,2758',
                'PC,SP,IX,IY': '5B47,CEEA,AF01,5C3A',
                'IR,iff,im,border': '3F00,1,1,3'
            },
            '-c finish-tape=1 --start 23367'
        )

    def test_firebird_bleepload(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/b/BlackLamp.tzx.zip',
            'Black Lamp.tzx',
            'fc9dd17a32679eeff80504af26e81d9b',
            'f310acd8910eb26a3e76fc61c58aef77',
            {
                'AF,BC,DE,HL': '0050,FEFE,FFFF,4627',
                "AF',BC',DE',HL'": '0044,0E0B,3F07,2758',
                'PC,SP,IX,IY': '8000,61A7,FF09,5C3A',
                'IR,iff,im,border': '3F00,0,1,1'
            },
            '-c accelerator=bleepload --start 32768'
        )

    def test_flash_loader(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/c/CliffHanger.tzx.zip',
            'Cliff Hanger.tzx',
            '08b2d3867c9478e446c49217595239be',
            '219bc82579cb1f1cfb05b9291a095d70',
            {
                'AF,BC,DE,HL': '0093,D024,0000,0013',
                "AF',BC',DE',HL'": '2465,1621,369B,2758',
                'PC,SP,IX,IY': '643C,6424,643B,5C3A',
                'IR,iff,im,border': '3F00,1,1,0'
            },
            '-c accelerator=flash-loader --start 25660'
        )

    def test_ftl(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/h/Hydrofool.tzx.zip',
            'Hydrofool.tzx',
            'd3267bd1facb761c02efe0ddf4438ab4',
            '7bbab733e59c1aee81b8d1b2129e226d',
            {
                'AF,BC,DE,HL': '0093,B058,0000,F84A',
                "AF',BC',DE',HL'": '584D,3E01,0000,3D83',
                'PC,SP,IX,IY': '9D3C,5E23,0000,5C3A',
                'IR,iff,im,border': '3F00,1,1,0'
            },
            '-c accelerator=ftl --start 40252'
        )

    def test_gargoyle(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/h/HeavyOnTheMagick.tzx.zip',
            'Heavy On The Magick - Side 1.tzx',
            '203b36a9ffa241089cb2741043c6563a',
            'a99bf5c299015ae496b3439487fbe7df',
            {
                'AF,BC,DE,HL': '0093,B058,0000,B7B0',
                "AF',BC',DE',HL'": '584D,1E01,0000,012C',
                'PC,SP,IX,IY': 'B471,5E23,0000,5C3A',
                'IR,iff,im,border': '3F00,1,1,0'
            },
            '-c accelerator=gargoyle --start 46193'
        )

    def test_gremlin(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/SpaceCrusade.tzx.zip',
            'Space Crusade - 48K.tzx',
            '48cdfc186f94bf6382da93cbc4b70810',
            '3c16b10bfcce8973687153b3fe4c2953',
            {
                'AF,BC,DE,HL': '0093,B007,881C,0001',
                "AF',BC',DE',HL'": '0745,1621,369B,2758',
                'PC,SP,IX,IY': '68B7,0000,66D1,5C3A',
                'IR,iff,im,border': '3F00,0,1,5'
            },
            '-c accelerator=gremlin --start 26807'
        )

    def test_haxpoc_lock(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/StarWarsV1.tzx.zip',
            'Star Wars - Release 1 - Side 1.tzx',
            'e36c32fd456f65801d4abfd1af382a65',
            '9823f0a223e153cbb37edfbd8cc1a6a5',
            {
                'AF,BC,DE,HL': 'B86A,B021,E2FF,6647',
                "AF',BC',DE',HL'": '2165,1621,369B,2758',
                'PC,SP,IX,IY': 'FFAB,4006,5AFF,95E0',
                'IR,iff,im,border': '3F00,0,1,0'
            },
            '--tape-start 6 -c accelerator=rom --start 65451'
        )

    def test_headerless_block(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/g/GalacticPatrol.tzx.zip',
            'Galactic Patrol.tzx',
            '94827dbfba53fa26396d2d218990ed5b',
            'e0738cf2a2ae3bbf1a34d59dfee59bf6',
            {
                'AF,BC,DE,HL': '0040,004B,0001,053F',
                "AF',BC',DE',HL'": 'FF69,1707,0007,2758',
                'PC,SP,IX,IY': '60A3,FF40,7D8F,5C3A',
                'IR,iff,im,border': '3F00,1,1,0'
            }
        )

    def test_hewson_slowload(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/c/Cybernoid.tzx.zip',
            'Cybernoid.tzx',
            '50921a76ee625feb31c4195aac63d020',
            '03e01853b339e3a714bd75e31b44f751',
            {
                'AF,BC,DE,HL': '0093,B07F,0000,00BB',
                "AF',BC',DE',HL'": '7F6D,0001,4948,FC21',
                'PC,SP,IX,IY': 'FE51,60EC,FC00,5C3A',
                'IR,iff,im,border': '3F00,0,1,0'
            },
            '-c accelerator=hewson-slowload --start 65105'
        )

    def test_injectaload(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/o/Outcast.tzx.zip',
            'Outcast.tzx',
            'c01b3ac0075f46f6a0b16d75c163b6b3',
            'b28e41e6612787862958c3e0f00b8dc4',
            {
                'AF,BC,DE,HL': '0044,0000,0000,FFE1',
                "AF',BC',DE',HL'": '0044,1621,369B,0000',
                'PC,SP,IX,IY': '5B00,0000,FF19,9B21',
                'IR,iff,im,border': 'FF80,0,1,0'
            },
            '-c accelerator=injectaload --start 23296'
        )

    def test_load_code(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/g/Gobstopper.tzx.zip',
            'Gob Stopper (Calisto).tzx',
            '43803187b78421dfe88bbfe3aa218b8d',
            '85b1e6270f471bcdf913c7c1e7cfdc1b',
            {
                'AF,BC,DE,HL': '4154,9C41,5D2C,2D2B',
                "AF',BC',DE',HL'": 'FF81,A384,369B,2758',
                'PC,SP,IX,IY': '9C41,9C29,03D2,5C3A',
                'IR,iff,im,border': '3F00,1,1,0'
            },
            '--start 40001'
        )

    def test_mask(self):
        # The loader for this game is polarity-sensitive
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/m/MASK.tzx.zip',
            'Mask.tzx',
            'd69fa0a1d2bab53e27d4843cc129d83a',
            'b9731556bc9ca078dea167dc5b0539bf',
            {
                'AF,BC,DE,HL': 'AC6A,00AC,0000,4023',
                "AF',BC',DE',HL'": '2021,1421,8000,A9E8',
                'PC,SP,IX,IY': 'AA89,FC18,8000,AC85',
                'IR,iff,im,border': '3F00,0,1,0'
            },
            '-c first-edge=0 --start 43657'
        )

    def test_microsphere(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/SkoolDaze.tzx.zip',
            'Skool Daze.tzx',
            '61d29396661cc0acfa8f3514010f641d',
            '2ba19a83a175e834023cf5fcfd79a824',
            {
                'AF,BC,DE,HL': '7F00,E15E,8B46,8BB1',
                "AF',BC',DE',HL'": '5E4D,0017,0007,5D00',
                'PC,SP,IX,IY': '5EE0,5D1B,80D1,5C3A',
                'IR,iff,im,border': '3F00,0,1,6'
            },
            '-c accelerator=microsphere --start 24288'
        )

    def test_microsphere_2(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/c/ContactSamCruise.tzx.zip',
            'Contact Sam Cruise.tzx',
            '873cb6de4edc2aa75b40b838981c6f72',
            '10f01c72d47159bfb34da8cad47e967c',
            {
                'AF,BC,DE,HL': '1743,0000,50B8,5A00',
                "AF',BC',DE',HL'": '7E6D,00F7,0007,FFE2',
                'PC,SP,IX,IY': 'F0E7,5D5A,8169,5C3A',
                'IR,iff,im,border': '3F00,1,1,6'
            },
            '-c accelerator=rom --start 61671'
        )

    def test_out_of_the_shadows(self):
        # The last block on this tape contains pulses but no data
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/o/OutOfTheShadows.tzx.zip',
            'Out Of The Shadows.tzx',
            '40f664f094ea41868793bffa59ebae95',
            '034b7b141d4046430ac89894d1fac6ba',
            {
                'AF,BC,DE,HL': 'FC51,FEDB,5DDF,002B',
                "AF',BC',DE',HL'": 'FF81,1621,369B,2758',
                'PC,SP,IX,IY': '9010,6191,0000,5C3A',
                'IR,iff,im,border': '3F00,1,1,3'
            },
            '--start 36880'
        )

    def test_paul_owens(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/u/UntouchablesThe.tzx.zip',
            'The Untouchables - Side 1.tzx',
            '7aed7cb0aa7a9be5a4c953eec1fc0dd1',
            'fa2785b078e8f8cd53ab4ad9d1cf354b',
            {
                'AF,BC,DE,HL': '0044,B05E,0000,0013',
                "AF',BC',DE',HL'": '5E4D,0049,989B,FD97',
                'PC,SP,IX,IY': '8047,FFFD,FDE4,7FE6',
                'IR,iff,im,border': '8400,0,2,0'
            },
            '--start 32839'
        )

    def test_poliload(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/a/AstroMarineCorps.tzx.zip',
            'Astro Marine Corps - Side 1.tzx',
            'b31fd6232a865fbef93db8700ceeb931',
            'dad4b5319c06ebc076d75c39cfc2d738',
            {
                'AF,BC,DE,HL': '0044,1800,0000,F83D',
                "AF',BC',DE',HL'": '0054,0A21,369B,2758',
                'PC,SP,IX,IY': 'EE00,6400,6328,5C3A',
                'IR,iff,im,border': '3F00,0,1,0'
            },
            '-c accelerator=poliload --start 60928'
        )

    def test_power_load(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/d/DynamiteDan.tzx.zip',
            'Dynamite Dan - Side 1.tzx',
            '38c2a7eb6c2ed9010e700063aedd3a3e',
            'aabc3f7367ee3b7fe0479614a52f182b',
            {
                'AF,BC,DE,HL': '0050,007E,12E4,0101',
                "AF',BC',DE',HL'": '7E6C,9CF9,369B,2758',
                'PC,SP,IX,IY': 'FF70,FD84,FFFF,5C3A',
                'IR,iff,im,border': '3F00,0,1,6'
            },
            '-c accelerator=power-load --start 65392'
        )

    def test_sam_stoat_safebreaker(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/SamStoatSafebreaker.tzx.zip',
            'Sam Stoat Safebreaker.tzx',
            '5bbe64b84c53c148343435e000c31083',
            '2f1d92b099975c22db7a8039e4f5d3bc',
            {
                'AF,BC,DE,HL': '0042,C4DE,0000,0009',
                "AF',BC',DE',HL'": 'D30D,421A,D844,FFD8',
                'PC,SP,IX,IY': 'FCD2,FF56,FB00,FCFB',
                'IR,iff,im,border': '3F80,0,2,0'
            },
            '-c first-edge=0 -c accelerator=speedlock --start 64722'
        )

    def test_search_loader(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/b/BloodBrothers.tzx.zip',
            'Blood Brothers.tzx',
            'c4e7e151c4321b29c095abf1e547f9b5',
            'f597148bb6af12ddfeccc720ae8505f8',
            {
                'AF,BC,DE,HL': 'C928,0000,CCDD,0000',
                "AF',BC',DE',HL'": 'FFA0,0000,5AF5,B5B0',
                'PC,SP,IX,IY': '5C00,5C00,8CDD,5C3A',
                'IR,iff,im,border': '3F00,0,1,0'
            },
            '-c accelerator=search-loader --start 23552'
        )

    def test_scaramouche(self):
        # This game requires the H register to be 0 when the ROM load routine
        # exits at $05B6 because of a mismatched flag byte
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/Scaramouche.tzx.zip',
            'Scaramouche.tzx',
            '330e7b6ee3106f12d256a7874abe273d',
            'c9ce9966ae506bc68bfd656a29399649',
            {
                'AF,BC,DE,HL': '0050,0021,0000,E301',
                "AF',BC',DE',HL'": '2165,1621,0000,0000',
                'PC,SP,IX,IY': '5D42,FFFD,FFF1,5C3A',
                'IR,iff,im,border': '3F00,0,1,1'
            },
            '-c finish-tape=1 --start 23874'
        )

    def test_sinclair_user(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/p/PiecesOfEight.tzx.zip',
            'Pieces Of Eight (1992)(Pirate Software - Sinclair User)[SU Loader].tzx',
            '62da22ff8b0f6e704b4e1a509d285e40',
            '8b1d1d8b1e3b5563c4dc86421f875101',
            {
                'AF,BC,DE,HL': '0093,C900,0000,0050',
                "AF',BC',DE',HL'": '0045,1621,369B,2758',
                'PC,SP,IX,IY': '400A,4372,E978,5C3A',
                'IR,iff,im,border': '3F00,0,1,0'
            },
            '-c accelerator=bleepload --start 16394'
        )

    def test_softlock(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/e/Elite.tzx.zip',
            'Elite - 48k.tzx',
            'f73379181e1a413ac6c22ffd4cc8122a',
            'b5e2da0aedae1e1cbc3fc210ac6642de',
            {
                'AF,BC,DE,HL': '0018,1721,0000,50E0',
                "AF',BC',DE',HL'": 'FF29,0221,369B,2758',
                'PC,SP,IX,IY': 'C223,FFFD,C7B6,5C3A',
                'IR,iff,im,border': '3F80,1,1,0'
            },
            '-c accelerator=softlock --start 49699'
        )

    def test_speedlock_1(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/b/BruceLee.tzx.zip',
            'Bruce Lee.tzx',
            '51cb1a6e1fb58304a15a588b82d8e001',
            'fe07022225e2348b8d9e4d19fc6f7b9a',
            {
                'AF,BC,DE,HL': 'C340,0000,FEFE,C003',
                "AF',BC',DE',HL'": 'D309,0000,EDFA,2758',
                'PC,SP,IX,IY': 'C000,FFFF,E86C,5C3A',
                'IR,iff,im,border': 'FD80,0,2,0'
            },
            '-c accelerator=speedlock --start 49152'
        )

    def test_speedlock_2(self):
        self._test_sim_load(
            'http://www.worldofspectrum.org/pub/sinclair/games/g/GreatEscapeThe.tzx.zip',
            'The Great Escape.tzx',
            '58d273a2c719da21a25b4af3d008c951',
            'dfd038ef9de8cf512ca0cc7f2a2b3017',
            {
                'AF,BC,DE,HL': '0081,0000,FAE0,FDE0',
                "AF',BC',DE',HL'": '5E4D,0000,5B20,2758',
                'PC,SP,IX,IY': 'F163,FFFF,FF82,5C3A',
                'IR,iff,im,border': '3F00,0,1,6'
            },
            '-c accelerator=speedlock --start 61795'
        )

    def test_speedlock_3(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/d/Dogfight-2187.tzx.zip',
            'Dogfight 2187.tzx',
            '5d73a347e27e98bb5a235eeac6470d56',
            '80d0dbd263514033a2a03c7063dd29e3',
            {
                'AF,BC,DE,HL': '0044,C420,FF39,0024',
                "AF',BC',DE',HL'": '792B,0000,50AA,FF88',
                'PC,SP,IX,IY': 'FF25,FFFF,5B00,FF7F',
                'IR,iff,im,border': '3F00,0,1,0'
            },
            '-c accelerator=speedlock --start 65317'
        )

    def test_speedlock_4(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/o/OutRun.tzx.zip',
            'Outrun - Tape 1 - Side 1.tzx',
            '78fb2a6b82ca2dc7021a5762ea1491fb',
            '720fe3c658b04d10d174c467bce67639',
            {
                'AF,BC,DE,HL': '0050,00FF,0001,5CFF',
                "AF',BC',DE',HL'": 'CD02,C3FF,FE9F,2758',
                'PC,SP,IX,IY': 'AD31,ACE8,C80E,5C3A',
                'IR,iff,im,border': '3F00,0,1,0'
            },
            '-c accelerator=speedlock --start 44337'
        )

    def test_speedlock_5(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/h/Hysteria.tzx.zip',
            'Hysteria.tzx',
            '2f4485c0d0e98758f7da09b322ca0a0c',
            'd7d27aeaf2f87e247777a6cee0e9685c',
            {
                'AF,BC,DE,HL': '3F68,0000,6135,5CE9',
                "AF',BC',DE',HL'": '1303,C4FF,FE9F,2758',
                'PC,SP,IX,IY': 'B00A,62FF,FBC6,5C3A',
                'IR,iff,im,border': '3F00,1,1,0'
            },
            '-c accelerator=speedlock --start 45066'
        )

    def test_speedlock_6(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/v/Vixen.tzx.zip',
            'Vixen - Side A.tzx',
            '3075d03f63d20acf2ad029265f6f1746',
            '1fe6e6ef535524dc78c5bd7bb558e030',
            {
                'AF,BC,DE,HL': '0042,0000,A300,50E0',
                "AF',BC',DE',HL'": '0054,B200,FE9F,2758',
                'PC,SP,IX,IY': 'C911,FFF0,6200,5C3A',
                'IR,iff,im,border': '3F00,0,1,0'
            },
            '-c accelerator=speedlock --start 51473'
        )

    def test_speedlock_7(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/a/Aaargh.tzx.zip',
            'Aaargh! - Side 1.tzx',
            'cfe091069af70b7ad7eae377665ce284',
            'f4c31550705bb8eda0694a1c893be7de',
            {
                'AF,BC,DE,HL': '0044,B200,FEC3,00CC',
                "AF',BC',DE',HL'": '1F1B,0000,481F,FF88',
                'PC,SP,IX,IY': 'FF03,FFFF,5DE4,FF80',
                'IR,iff,im,border': '3F00,0,1,0'
            },
            '-c accelerator=speedlock --start 65283'
        )

    def test_square_head(self):
        # This game uses 'IN r,(C)' instructions between tape blocks 6 and 7
        # that should not be interpreted as reading the tape
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/SquareHead.tzx.zip',
            'SQR_HEAD.TZX',
            '04b1b63a321dd817a67bafe4b85ce41b',
            'f98298fd7e643737b94bf103a00ecb63',
            {
                'AF,BC,DE,HL': 'D054,5FD0,5E9B,2D2B',
                "AF',BC',DE',HL'": 'FF81,0000,369B,2758',
                'PC,SP,IX,IY': '5FD0,5F9E,0000,5C3A',
                'IR,iff,im,border': '3F00,1,1,0'
            },
            '--start 24528'
        )

    def test_standard_load(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/m/ManicMiner.tzx.zip',
            'Manic Miner.tzx',
            '2750ccb6c240d14516c448e94f8d200e',
            'c0a196c2acccb5b03113b18e596fa575',
            {
                'AF,BC,DE,HL': '0054,8400,5D1F,2D2B',
                "AF',BC',DE',HL'": 'FF81,1421,369B,2758',
                'PC,SP,IX,IY': '8400,7519,0000,5C3A',
                'IR,iff,im,border': '3F00,1,1,0'
            },
        )

    def test_street_gang(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/StreetGang.tzx.zip',
            'Street Gang.tzx',
            '04a0a6b5c286a34b33285134903e9128',
            'de9f05abca3028c55e4bc9fff2ede79a',
            {
                'AF,BC,DE,HL': 'BF80,92A0,0000,D3E9',
                "AF',BC',DE',HL'": '594D,1621,369B,2758',
                'PC,SP,IX,IY': 'FFD6,5FF9,FE80,5C3A',
                'IR,iff,im,border': '3F00,0,1,0'
            },
            '--tape-stop 8 -c accelerator=speedlock'
        )

    def test_technician_ted(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/t/TechnicianTed.tzx.zip',
            'Technician Ted.tzx',
            'b55a761f7d3733bc6ac958b10fab0c43',
            '030e5e9a2d555833296ba3a1ce5fb35e',
            {
                'AF,BC,DE,HL': '5C0C,D348,5C92,4DBD',
                "AF',BC',DE',HL'": '5D4D,0001,806B,806B',
                'PC,SP,IX,IY': '8C34,5C00,FEF4,5C3A',
                'IR,iff,im,border': '3F00,0,1,0'
            },
            '-c accelerator=rom --start 35892'
        )

    def test_zydroload(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/l/LightCorridorThe.tzx.zip',
            'The Light Corridor.tzx',
            '66674ee9c6b696404c5847be32796af4',
            '43046b049d10640009a9d3656c3e87e3',
            {
                'AF,BC,DE,HL': '0093,C07F,0000,0092',
                "AF',BC',DE',HL'": '7F6D,7FFD,369B,2758',
                'PC,SP,IX,IY': '806F,8300,0000,5C3A',
                'IR,iff,im,border': '0000,0,2,0'
            },
            '-c accelerator=zydroload --start 32879'
        )
