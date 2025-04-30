import hashlib
import tempfile

from skoolkittest import SkoolKitTestCase
from skoolkit import tap2sna
from skoolkit.snapshot import Snapshot

class SimLoadGamesTest(SkoolKitTestCase):
    def _test_sim_load(self, url, tapname, tapsum, reg, options=''):
        with tempfile.TemporaryDirectory() as d:
            if isinstance(options, str):
                options = options.split()
            z80file = f'{d}/{tapname[:-4]}.z80'
            if isinstance(tapname, str):
                tap2sna.main(('--tape-name', tapname, '--tape-sum', tapsum, *options, url, z80file))
            else:
                tap2sna.main(('--tape-name', tapname[0], '--tape-sum', tapsum[0], '--tape-name', tapname[1], '--tape-sum', tapsum[1], *options, url, z80file))
            r = Snapshot.get(z80file)
            ram = r.ram(-1)
            md5sum = hashlib.md5(bytes(ram)).hexdigest()
            rvals = {
                "AF,BC,DE,HL": f'{r.a:02X}{r.f:02X},{r.bc:04X},{r.de:04X},{r.hl:04X}',
                "AF',BC',DE',HL'": f'{r.a2:02X}{r.f2:02X},{r.bc2:04X},{r.de2:04X},{r.hl2:04X}',
                "PC,SP,IX,IY": f'{r.pc:04X},{r.sp:04X},{r.ix:04X},{r.iy:04X}',
                "IR,iff,im,border": f'{r.i:02X}{r.r:02X},{r.iff2},{r.im},{r.border}',
                "ram": md5sum
            }
            self.assertEqual(reg, rvals)

    def test_accelerate_dec_a(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/c/CostaCapers.tzx.zip',
            'Costa Capers.tzx',
            '79a56e80c6262f059808b1e7a1c83d63',
            {
                'AF,BC,DE,HL': '0202,B140,0000,00A5',
                "AF',BC',DE',HL'": 'FF45,0017,5AFD,EBB5',
                'PC,SP,IX,IY': '6802,5C00,EAEF,5C3A',
                'IR,iff,im,border': '3F56,0,1,4',
                'ram': '89c0d86319337b23ab6c90d5a5202118'
            },
            '-c accelerate-dec-a=2 --start 26626'
        )

    def test_alkatraz(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/f/Fairlight48V1.tzx.zip',
            'Fairlight - 48k - Release 1.tzx',
            '1dba2ac53fd25f4cc1065e18e31a7b96',
            {
                'AF,BC,DE,HL': '0044,0600,0000,2E2E',
                "AF',BC',DE',HL'": 'FFAC,0348,4022,DBDD',
                'PC,SP,IX,IY': 'DCB2,DAD9,DADC,5C3A',
                'IR,iff,im,border': '3F0A,0,1,0',
                'ram': '6e2832ada7a9edd6453de22622b60e51'
            },
            '-c accelerator=alkatraz --start 56498'
        )

    def test_alkatraz2(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/SuperMonacoGP.tzx.zip',
            'Super Monaco GP.tzx',
            '5f656642c8df324f287777ff06eb1a30',
            {
                'AF,BC,DE,HL': '0045,00FC,0000,41CC',
                "AF',BC',DE',HL'": 'FF45,1621,369B,2758',
                'PC,SP,IX,IY': 'FD81,0000,41CC,5C3A',
                'IR,iff,im,border': '3F74,0,1,0',
                'ram': '363c66bdbcc5d1185e09ca63a012a411'
            },
            '-c accelerator=alkatraz2 --start 64897'
        )

    def test_alternative(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/f/FiremanSam.tzx.zip',
            'Fireman Sam - Side 1.tzx',
            '4f0c905c6cefa573e7705de0f0735d4f',
            {
                'AF,BC,DE,HL': '0093,B07D,0000,0017',
                "AF',BC',DE',HL'": '7D6D,1621,369B,2758',
                'PC,SP,IX,IY': 'FCD3,FFFF,FBFF,0000',
                'IR,iff,im,border': '3F2E,0,1,0',
                'ram': '012a543a3db1a9c0487d564dc5bcaf57'
            },
            '-c accelerator=alternative --start 64723'
        )

    def test_alternative2(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/k/KentuckyRacing.tzx.zip',
            'Kentucky Racing.tzx',
            'ff94b9f96368ad69e684c6f478d5dc6f',
            {
                'AF,BC,DE,HL': '0093,B07D,0000,008F',
                "AF',BC',DE',HL'": '7D6D,1621,369B,2758',
                'PC,SP,IX,IY': 'FB8C,FFFF,E800,5C3A',
                'IR,iff,im,border': '3F5C,0,1,0',
                'ram': 'bcde90e45c9bee39a00b7c5da07b5fb3'
            },
            '-c accelerator=alternative2 --start 64396'
        )

    def test_alternative3(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/d/DoubleDare.tzx.zip',
            'Double Dare.tzx',
            'f23fdd08b6e188ee3ce9f677d42dce41',
            {
                'AF,BC,DE,HL': '0093,B022,0000,00B9',
                "AF',BC',DE',HL'": '2265,1621,369B,2758',
                'PC,SP,IX,IY': 'F000,FFFA,FD40,5C3A',
                'IR,iff,im,border': '3F5D,0,1,0',
                'ram': '4697ad052eebe1aafb3345764a23aafd'
            },
            '--press 6:SPACE --tape-stop 8 -c accelerator=alternative3 --start 61440'
        )

    def test_basil_the_great_mouse_detective(self):
        # The loader for this game is polarity-sensitive
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/b/BasilTheGreatMouseDetective.tzx.zip',
            'Basil The Great Mouse Detective.tzx',
            '5e213d8a847168db2a9721f88cb1e280',
            {
                'AF,BC,DE,HL': 'C742,00C7,0000,4051',
                "AF',BC',DE',HL'": '3421,DA00,0027,3B6A',
                'PC,SP,IX,IY': 'DA0E,6955,0000,C730',
                'IR,iff,im,border': '3F51,0,1,0',
                'ram': '64f367b3cb90c4abca77026b60d42b47'
            },
            '-c accelerator=none --start 55822'
        )

    def test_battle_of_britain(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/b/BattleOfBritain_2.tzx.zip',
            'Battle Of Britain (PSS).tzx',
            '6b1005a547ede2687449cf11788e7dd3',
            {
                'AF,BC,DE,HL': '0093,B001,0000,0004',
                "AF',BC',DE',HL'": '0145,1621,5CBC,0000',
                'PC,SP,IX,IY': '6687,6588,FFDC,5C3A',
                'IR,iff,im,border': '3F2E,0,1,1',
                'ram': 'c838a20b3728761f4574a81069df6612'
            },
            '-c pause=0 -c accelerator=rom --start 26247'
        )

    def test_bleepload(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/b/BlackLamp.tzx.zip',
            'Black Lamp.tzx',
            'fc9dd17a32679eeff80504af26e81d9b',
            {
                'AF,BC,DE,HL': '0050,FEFE,FFFF,4627',
                "AF',BC',DE',HL'": '0044,0E0B,3F07,2758',
                'PC,SP,IX,IY': '60CF,61A7,FF09,5C3A',
                'IR,iff,im,border': '3F43,0,1,1',
                'ram': 'c8f7169b85152830d23537d486fb5704'
            },
            '-c accelerator=bleepload --start 24783'
        )

    def test_boguslaw_juza(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/e/EuroBiznes.tzx.zip',
            'EuroBiznes.tzx',
            '9c2455c074bd1478bd3f6c624344b461',
            {
                'AF,BC,DE,HL': '0093,B05E,0000,0050',
                "AF',BC',DE',HL'": '5E4D,0614,FF38,2758',
                'PC,SP,IX,IY': '5DF8,61A8,0000,5C3A',
                'IR,iff,im,border': '3F7A,1,1,1',
                'ram': 'd802044c00541ea2cb62c5078a9c0ecd'
            },
            '-c accelerator=boguslaw-juza --start 24056'
        )

    def test_cattell_iq_test(self):
        # Reads port 65531 to detect a printer
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/utils/c/CattellIQTest.tzx.zip',
            'Cattel IQ Test.tzx',
            'a3ad457e8f4b1bf9794b021678b9ce18',
            {
                'AF,BC,DE,HL': '3A38,CEFF,0100,5D6F',
                "AF',BC',DE',HL'": 'FF81,1221,369B,0000',
                'PC,SP,IX,IY': 'F7F7,D310,5B80,5C3A',
                'IR,iff,im,border': 'FD19,0,2,7',
                'ram': 'df050539cd0d8d0222b564751fad40d0'
            }
        )

    def test_cmio(self):
        # After the first CODE block has loaded, this line of BASIC is run:
        #
        #   3 LET I=USR 23328: IF I<1200 OR I>3000 THEN RANDOMIZE USR O
        #
        # The code at 23328 listens for the pilot tone of the next block on the
        # tape:
        #
        #   23328 LD H,50     ; Detect 50 edges of the pilot tone.
        #   23330 LD BC,0     ; BC will count the port readings.
        #   23333 IN A,(254)  ; Take an initial port reading.
        #   23335 LD L,A      ; Save the current port reading in L.
        #   23336 IN A,(254)  ; Take another port reading.
        #   23338 INC BC      ; Increment the counter.
        #   23339 CP L        ; Detected an edge yet?
        #   23340 JR Z,23336  ; If not, jump back to take another port reading.
        #   23342 DEC H       ; Detected 50 edges yet?
        #   23343 JR NZ,23335 ; Jump back if not.
        #   23345 RET         ; Return to BASIC.
        #
        # If memory and I/O contention delays are not simulated, this routine
        # returns to BASIC with BC=3208, which is too high a value, and
        # triggers the 'RANDOMIZE USR O' (where the variable 'O' equals 0).
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/g/GoldMine.tzx.zip',
            'Gold Mine - Main Game.tzx',
            '611fbfd3d6982496eadb2e2b663cc27f',
            {
                'AF,BC,DE,HL': '0001,0009,0000,7F58',
                "AF',BC',DE',HL'": 'FF81,0F21,0000,0000',
                'PC,SP,IX,IY': '053F,FF50,8000,5C3A',
                'IR,iff,im,border': '3F66,0,1,7',
                'ram': '935419fe52d5a0e629769e59a2472194'
            },
            '-c cmio=1 -c first-edge=30000 -c in-flags=1 -c finish-tape=1 --start 1343'
        )

    def test_crl(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/b/BallbreakerII.tzx.zip',
            'Ballbreaker II.tzx',
            'c8ea2110721c9e5955e779caaf0dfea2',
            {
                'AF,BC,DE,HL': '0093,B000,0000,00C8',
                "AF',BC',DE',HL'": '0044,0B21,369B,2758',
                'PC,SP,IX,IY': 'FE76,0000,F4C3,5C3A',
                'IR,iff,im,border': '3F21,0,1,0',
                'ram': '7e2279cda73fec7094a88e53fd0687e5'
            },
            '-c accelerator=crl --start 65142'
        )

    def test_crl2(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/t/Terrahawks.tzx.zip',
            'Terrahawks.tzx',
            '40a3dc51627dca710eaec1107cbcbca7',
            {
                'AF,BC,DE,HL': '0093,BEFA,0000,0020',
                "AF',BC',DE',HL'": '0044,7F00,369B,2758',
                'PC,SP,IX,IY': 'EFFD,FFDC,FF1C,5C3A',
                'IR,iff,im,border': '3F39,0,1,2',
                'ram': '7f25025e7d0eca5a252edc4ed3c36dd2'
            },
            '-c accelerator=crl2 --start 61437'
        )

    def test_crl3(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/o/Oink.tzx.zip',
            'Oink.tzx',
            '504ce9f5cdb173aaa523098842e9814d',
            {
                'AF,BC,DE,HL': '0093,B07F,0000,00CB',
                "AF',BC',DE',HL'": '7F6D,0100,48B6,59B5',
                'PC,SP,IX,IY': '8045,0000,B537,5C3A',
                'IR,iff,im,border': '3F28,0,1,0',
                'ram': 'cc927bd96ee464334ee87dcb449c58e4'
            },
            '-c accelerator=crl3 --tape-stop 8 --start 32837'
        )

    def test_crl4(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/q/QuannTulla(Federation)(CRLGroupPLC).tzx.zip',
            'Federation.tzx',
            '0a2a9400b9f131f2b5f69e2d2b396924',
            {
                'AF,BC,DE,HL': '0093,B05F,0000,0097',
                "AF',BC',DE',HL'": '5F4D,0721,369B,2758',
                'PC,SP,IX,IY': '5B3E,5DA8,0000,5C3A',
                'IR,iff,im,border': '3F38,1,1,7',
                'ram': '1f4930e3c7bdf0b97d4fa19882dfe97b'
            },
            '-c accelerator=crl4 --start 23358'
        )

    def test_cybexlab(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/123/17.11.1989.tzx.zip',
            '17.11.1989.tzx',
            '251a73d47759918ee9223d9042558064',
            {
                'AF,BC,DE,HL': '0001,6646,0000,0000',
                "AF',BC',DE',HL'": 'FF45,0021,0000,0000',
                'PC,SP,IX,IY': '053F,FF4E,C311,5C3A',
                'IR,iff,im,border': '3F11,0,1,7',
                'ram': '622a38d517447d4686bbedc8093313f2'
            },
            '-c accelerator=cybexlab -c finish-tape=1 --start 1343'
        )

    def test_d_and_h(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/m/Multi-PlayerSoccerManager.tzx.zip',
            'Multi-Player Soccer Manager.tzx',
            'fb7990e3321646e5e8ec803a085bdd6c',
            {
                'AF,BC,DE,HL': '0093,C478,0000,0039',
                "AF',BC',DE',HL'": '786D,1621,369B,2758',
                'PC,SP,IX,IY': 'FE0E,0000,FDFD,5C3A',
                'IR,iff,im,border': '3F9C,0,1,0',
                'ram': '1acb3679890cd1eafb79c11ed5c4ca45'
            },
            '-c accelerator=d-and-h --start 65038'
        )

    def test_design_design(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/r/RommelsRevenge.tzx.zip',
            "Rommel's Revenge.tzx",
            '78113a380e8ddb08a5b0aa436286bac8',
            {
                'AF,BC,DE,HL': '0044,B078,0020,5B00',
                "AF',BC',DE',HL'": '0044,1621,369B,2758',
                'PC,SP,IX,IY': '5B00,FFFE,A000,0000',
                'IR,iff,im,border': '3F6A,0,1,0',
                'ram': '38e4a770af5e0bfb47b2993a6e06d7e8'
            },
            '-c accelerator=design-design --start 23296'
        )

    def test_digital_integration(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/t/Tomahawk.tzx.zip',
            'Tomahawk.tzx',
            '3189a34157750d9e4ad01d5a7b2e5722',
            {
                'AF,BC,DE,HL': '0044,DE0E,4C00,F986',
                "AF',BC',DE',HL'": 'FF45,0000,369B,FFF2',
                'PC,SP,IX,IY': 'E027,FFFC,FC69,FFD1',
                'IR,iff,im,border': '39C8,0,2,6',
                'ram': 'e61e33943ac6a920e487414007efb832'
            },
            '-c accelerator=digital-integration --start 57383'
        )

    def test_finish_tape(self):
        # Hits the given start address (23367) before the tape has finished
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/g/Gallipoli.tzx.zip',
            'Gallipoli - 48k.tzx',
            '1cdd5f519c467f434e67b910e171052d',
            {
                'AF,BC,DE,HL': '0001,0000,0000,AF01',
                "AF',BC',DE',HL'": 'FFA9,0021,369B,2758',
                'PC,SP,IX,IY': '5B47,CEEA,AF01,5C3A',
                'IR,iff,im,border': '3F12,1,1,3',
                'ram': 'abebb8526aaabefde79c9ade15864cd6'
            },
            '-c finish-tape=1 --start 23367'
        )

    def test_gremlin(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/SpaceCrusade.tzx.zip',
            'Space Crusade - 48K.tzx',
            '48cdfc186f94bf6382da93cbc4b70810',
            {
                'AF,BC,DE,HL': '0093,B047,881C,0001',
                "AF',BC',DE',HL'": '4745,1621,369B,2758',
                'PC,SP,IX,IY': 'EF2D,0000,66D1,5C3A',
                'IR,iff,im,border': '3F70,0,1,5',
                'ram': 'e15e37cae1b17e64eb2b8e72529d34b4'
            },
            '-c accelerator=gremlin --tape-stop 10 --start 61229'
        )

    def test_headerless_block(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/g/GalacticPatrol.tzx.zip',
            'Galactic Patrol.tzx',
            '94827dbfba53fa26396d2d218990ed5b',
            {
                'AF,BC,DE,HL': '0040,004B,0001,5DB3',
                "AF',BC',DE',HL'": 'FF69,1707,0007,2758',
                'PC,SP,IX,IY': '60A3,FF40,7D8F,5C3A',
                'IR,iff,im,border': '3F14,1,1,0',
                'ram': '4f2ab54dfa4d1d16f3124a629e2a5685'
            }
        )

    def test_in_flags_1(self):
        # Has a custom loading routine in what is contended memory on a
        # standard 48K Spectrum.
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/Sapper.tzx.zip',
            'sapper.tzx',
            'e8f2e39a382c56c82318e1a92dd69274',
            {
                'AF,BC,DE,HL': '0093,B07E,0000,002E',
                "AF',BC',DE',HL'": '7E6D,1621,369B,2758',
                'PC,SP,IX,IY': '5EAB,5E87,FFE7,5C3A',
                'IR,iff,im,border': '3F0E,1,1,0',
                'ram': 'db755f6f3f27dfbcd6741ba8b96c64f5'
            },
            '-c in-flags=1 --start 24235'
        )

    def test_in_flags_4(self):
        # Exercises the routine at 0x08A3 in the 128K Spectrum ROM, which uses
        # an 'IN A,(C)' instruction to probe the RS232 port. 'in-flags=4' is
        # required to avoid an infinite loop in that routine.
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/Sokoban_3.tap.zip',
            'SOKOBAN.TAP',
            'e1ca546008696c2f53699683874b0717',
            {
                'AF,BC,DE,HL': '0001,0000,0000,5F58',
                "AF',BC',DE',HL'": 'FF81,7FFD,0009,0038',
                'PC,SP,IX,IY': '5B14,5F52,C654,5C3A',
                'IR,iff,im,border': '3F64,1,1,0',
                'ram': '2b6b7f6e2c9dd6411967f2531a173077'
            },
            '-c in-flags=4 -c machine=128 -c finish-tape=1 --start 23316'
        )

    def test_load_code(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/g/Gobstopper.tzx.zip',
            'Gob Stopper (Calisto).tzx',
            '43803187b78421dfe88bbfe3aa218b8d',
            {
                'AF,BC,DE,HL': '4154,9C41,5D2C,2D2B',
                "AF',BC',DE',HL'": 'FF81,A384,369B,2758',
                'PC,SP,IX,IY': '9C41,9C29,03D2,5C3A',
                'IR,iff,im,border': '3F51,1,1,0',
                'ram': '85b1e6270f471bcdf913c7c1e7cfdc1b'
            },
            '--start 40001'
        )

    def test_load_configuration_parameter(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/t/Tridex.tzx.zip',
            'Tridex.tzx',
            '5141d234263b0255e8d4008eb1c2eec8',
            {
                'AF,BC,DE,HL': '0001,0004,0000,88B8',
                "AF',BC',DE',HL'": 'FF81,0221,0000,0000',
                'PC,SP,IX,IY': '053F,88B1,FFFE,5C3A',
                'IR,iff,im,border': '3F63,0,1,7',
                'ram': 'a7824496a22358ff430fe29e9fe691da'
            },
            ('--start', '1343', '-c', 'finish-tape=1', '-c', 'load=CLEAR 35000: LOAD ""')
        )

    def test_microprose(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/f/F-15StrikeEagle.tzx.zip',
            'F15 Strike Eagle.tzx',
            'c1283db376aef223855ca945af63686a',
            {
                'AF,BC,DE,HL': '0050,0001,0000,AE01',
                "AF',BC',DE',HL'": '0042,1421,0000,0000',
                'PC,SP,IX,IY': 'F6A6,FF50,E080,5C3A',
                'IR,iff,im,border': '3F0E,0,1,1',
                'ram': '5b0007ebb7110d5463420b7f95e53cc1'
            },
            '-c accelerator=microprose --start 63142'
        )

    def test_microsphere(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/SkoolDaze.tzx.zip',
            'Skool Daze.tzx',
            '61d29396661cc0acfa8f3514010f641d',
            {
                'AF,BC,DE,HL': '7F00,E17E,8B46,8BB1',
                "AF',BC',DE',HL'": '7E6D,0017,0007,5D00',
                'PC,SP,IX,IY': '5EE0,5D1B,80D1,5C3A',
                'IR,iff,im,border': '3F2B,0,1,6',
                'ram': '2ba19a83a175e834023cf5fcfd79a824'
            },
            '-c accelerator=microsphere --start 24288'
        )

    def test_micro_style(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/x/Xenophobe.tzx.zip',
            'Xenophobe - Side A.tzx',
            '0154dc65b6395b35b2dd8bd9f9394c20',
            {
                'AF,BC,DE,HL': '0044,BCD8,8900,0000',
                "AF',BC',DE',HL'": 'FF45,1621,369B,2758',
                'PC,SP,IX,IY': 'FE66,FFFE,6300,9600',
                'IR,iff,im,border': '3F65,0,1,0',
                'ram': '8ab87d9b2ea6375d5da696802e5ff6b2'
            },
            '-c accelerator=micro-style --start 65126'
        )

    def test_out_of_the_shadows(self):
        # The last block on this tape contains pulses but no data
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/o/OutOfTheShadows.tzx.zip',
            'Out Of The Shadows.tzx',
            '40f664f094ea41868793bffa59ebae95',
            {
                'AF,BC,DE,HL': 'FC51,FEFB,5DDF,002B',
                "AF',BC',DE',HL'": 'FF81,1621,369B,2758',
                'PC,SP,IX,IY': '9010,6191,0000,5C3A',
                'IR,iff,im,border': '3F4E,1,1,3',
                'ram': '98df76e22d91c7d5a8bf7a3c845bc411'
            },
            '--start 36880'
        )

    def test_paul_owens(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/u/UntouchablesThe.tzx.zip',
            'The Untouchables - Side 1.tzx',
            '7aed7cb0aa7a9be5a4c953eec1fc0dd1',
            {
                'AF,BC,DE,HL': '0044,B07E,0000,0013',
                "AF',BC',DE',HL'": '7E6D,0049,989B,FD97',
                'PC,SP,IX,IY': '8047,FFFD,FDE4,7FE6',
                'IR,iff,im,border': '8402,0,2,0',
                'ram': 'fa2785b078e8f8cd53ab4ad9d1cf354b'
            },
            '--start 32839'
        )

    def test_raxoft(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/p/Podraz4.tzx.zip',
            'PODRAZ4R.TZX',
            '21cb4ea8ce5dbdfc2b5ef039e4ed6c77',
            {
                'AF,BC,DE,HL': '5354,FD53,A1C9,2D2B',
                "AF',BC',DE',HL'": '0044,1721,369B,2758',
                'PC,SP,IX,IY': 'FD53,F72D,03D4,5C3A',
                'IR,iff,im,border': '3F7B,1,1,5',
                'ram': '3aa858ab90ea0fbfeabce045d62b3d0e'
            },
            '-c accelerator=raxoft --start 64851'
        )

    def test_realtime(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/StarstrikeII.tzx.zip',
            'Starstrike II.tzx',
            'f0f757d9b9879227d729d45c786a09dc',
            {
                'AF,BC,DE,HL': '0093,B05F,0000,0025',
                "AF',BC',DE',HL'": '0809,1221,0000,0000',
                'PC,SP,IX,IY': 'FFC0,0000,FF00,5C3A',
                'IR,iff,im,border': '3F2E,0,1,0',
                'ram': '3e26307a6e09789f106846b30e1d0b43'
            },
            '-c accelerator=realtime --start 65472'
        )

    def test_sam_stoat_safebreaker(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/SamStoatSafebreaker.tzx.zip',
            'Sam Stoat Safebreaker.tzx',
            '5bbe64b84c53c148343435e000c31083',
            {
                'AF,BC,DE,HL': '0042,C4DE,0000,0009',
                "AF',BC',DE',HL'": 'D30D,421A,D844,FFD8',
                'PC,SP,IX,IY': 'FCD2,FF56,FB00,FCFB',
                'IR,iff,im,border': '3FB3,0,2,0',
                'ram': '2f1d92b099975c22db7a8039e4f5d3bc'
            },
            '-c accelerator=speedlock --start 64722'
        )

    def test_scaramouche(self):
        # This game requires the H register to be 0 when the ROM load routine
        # exits at $05B6 because of a mismatched flag byte
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/Scaramouche.tzx.zip',
            'Scaramouche.tzx',
            '330e7b6ee3106f12d256a7874abe273d',
            {
                'AF,BC,DE,HL': '0050,005E,0000,E301',
                "AF',BC',DE',HL'": '5E4D,1621,0000,0000',
                'PC,SP,IX,IY': '5D42,FFFD,FFF1,5C3A',
                'IR,iff,im,border': '3F0B,0,1,6',
                'ram': 'c9ce9966ae506bc68bfd656a29399649'
            },
            '-c finish-tape=1 --start 23874'
        )

    def test_search_loader(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/b/BloodBrothers.tzx.zip',
            'Blood Brothers.tzx',
            'c4e7e151c4321b29c095abf1e547f9b5',
            {
                'AF,BC,DE,HL': '0202,B040,0000,0006',
                "AF',BC',DE',HL'": 'FF45,0000,5AF5,B5B0',
                'PC,SP,IX,IY': 'BAE7,5BFC,8CDD,5C3A',
                'IR,iff,im,border': '3F67,0,1,0',
                'ram': '122ad7a2e57ed1eab06af2eabc602914'
            },
            '-c accelerator=search-loader --start 47847'
        )

    def test_silverbird(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/h/Halloween.tzx.zip',
            'Olli & Lissa 2 - Halloween.tzx',
            '476b60c17a8636eaebf7e3b67915a5e2',
            {
                'AF,BC,DE,HL': '0054,B07E,0000,002E',
                "AF',BC',DE',HL'": '0044,1621,369B,2758',
                'PC,SP,IX,IY': 'D9E9,D9B7,0000,D9D4',
                'IR,iff,im,border': '3F7E,0,1,0',
                'ram': '30572b5fdfa08dea33ad1cd91bd46ef6'
            },
            '-c accelerator=silverbird --start 55785'
        )

    def test_sparklers(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/b/BargainBasement.tzx.zip',
            'Bargain Basement.tzx',
            'f9386e944959edc4b732734ab1f0ea6c',
            {
                'AF,BC,DE,HL': '0093,C421,0000,00F4',
                "AF',BC',DE',HL'": '2164,C9AC,369B,0000',
                'PC,SP,IX,IY': 'FE99,6393,E54C,3E00',
                'IR,iff,im,border': '3F64,0,1,1',
                'ram': 'c78140ffaeb662bd6d221ca845caaed1'
            },
            '-c accelerator=sparklers --start 65177'
        )

    def test_speedlock(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/b/BruceLee.tzx.zip',
            'Bruce Lee.tzx',
            '51cb1a6e1fb58304a15a588b82d8e001',
            {
                'AF,BC,DE,HL': '0093,C401,0000,008F',
                "AF',BC',DE',HL'": 'D309,421A,D844,FFD8',
                'PC,SP,IX,IY': 'EDF1,FF56,E86C,EE1A',
                'IR,iff,im,border': '3FA1,0,2,0',
                'ram': 'e2c7f0aa6fc546c1968e99886fd594e6'
            },
            '-c accelerator=speedlock --start 60913'
        )

    def test_square_head(self):
        # This game uses 'IN r,(C)' instructions between tape blocks 6 and 7
        # that should not be interpreted as reading the tape
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/SquareHead.tzx.zip',
            'SQR_HEAD.TZX',
            '04b1b63a321dd817a67bafe4b85ce41b',
            {
                'AF,BC,DE,HL': 'D054,5FD0,5E9B,2D2B',
                "AF',BC',DE',HL'": 'FF81,0000,369B,2758',
                'PC,SP,IX,IY': '5FD0,5F9E,0000,5C3A',
                'IR,iff,im,border': '3F58,1,1,0',
                'ram': '7e3efedcc012dec47c9afdcf86c0ebfc'
            },
            '--start 24528'
        )

    def test_standard_load(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/m/ManicMiner.tzx.zip',
            'Manic Miner.tzx',
            '2750ccb6c240d14516c448e94f8d200e',
            {
                'AF,BC,DE,HL': '0054,8400,5D1F,2D2B',
                "AF',BC',DE',HL'": 'FF81,1421,369B,2758',
                'PC,SP,IX,IY': '8400,7519,0000,5C3A',
                'IR,iff,im,border': '3F14,1,1,0',
                'ram': 'd32458fe7433ea7d9e6de98437b9810b'
            },
        )

    def test_tape_start(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/s/StarWarsV1.tzx.zip',
            'Star Wars - Release 1 - Side 1.tzx',
            'e36c32fd456f65801d4abfd1af382a65',
            {
                'AF,BC,DE,HL': 'B86A,B001,E2FF,6647',
                "AF',BC',DE',HL'": '0145,1621,369B,2758',
                'PC,SP,IX,IY': 'FFAB,4006,5AFF,95E0',
                'IR,iff,im,border': '3F16,0,1,0',
                'ram': '9823f0a223e153cbb37edfbd8cc1a6a5'
            },
            '--tape-start 6 -c accelerator=rom --start 65451'
        )

    def test_tiny(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/p/ParaCimaOuParaBaixo.tzx.zip',
            'Para Cima ou Para Baixo.tzx',
            '679e385bfaac090402c589c23ca12095',
            {
                'AF,BC,DE,HL': '0054,0000,0001,0000',
                "AF',BC',DE',HL'": '0445,8A97,369B,5A9E',
                'PC,SP,IX,IY': 'BD6F,C000,BE74,0001',
                'IR,iff,im,border': '3F59,0,1,4',
                'ram': '25461848f0ae0b85b136a50131d1231a'
            },
            '-c accelerator=tiny --start 48495'
        )

    def test_two_tapes(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/r/RallyCross.tzx.zip',
            ('Rally Cross - Side 1.tzx', 'Rally Cross - Side 2.tzx'),
            ('59eb4b57e102b0f2dfde44e6a9e23694', 'cb5cb6e607b959558741ee6b70f3d662'),
            {
                'AF,BC,DE,HL': '0001,0F18,0000,BEFB',
                "AF',BC',DE',HL'": 'FF69,1621,369B,2758',
                'PC,SP,IX,IY': '9DEE,5DBD,0000,5C3A',
                'IR,iff,im,border': '3F3F,1,1,7',
                'ram': 'c8cc50e7c818fd80cadd53117ee4edcc'
            },
            '--start 40430'
        )

    def test_weird_science(self):
        self._test_sim_load(
            'https://worldofspectrum.net/pub/sinclair/games/f/FlashBeerTrilogy.tzx.zip',
            'Flash Beer.tzx',
            '7d4ba1bad9ed7834be786cee88b8bae5',
            {
                'AF,BC,DE,HL': '0093,B0FA,0000,0021',
                "AF',BC',DE',HL'": '0044,0001,57FF,FED3',
                'PC,SP,IX,IY': 'F00A,FFFF,9173,F280',
                'IR,iff,im,border': '3F1C,0,1,2',
                'ram': 'b6708242713704a2e93eacc07f77aa68'
            },
            '-c accelerator=weird-science --tape-stop 5 --start 61450'
        )
