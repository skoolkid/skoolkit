import os.path
import re
from textwrap import dedent
from unittest.mock import patch, Mock

from skoolkittest import SkoolKitTestCase
from skoolkit import sna2ctl, snapshot, SkoolKitError, VERSION
from skoolkit.config import COMMANDS

# Binary data designed to test the static code analysis algorithm that is used
# when a code map is provided:
#  1. Use the code map to create an initial set of 'c' ctls, and mark all
#     unexecuted blocks as 'U' (unknown).
#  2. Where a 'c' block doesn't end with a RET/JP/JR, extend it up to the next
#     RET/JP/JR in the following 'U' blocks, or up to the next 'c' block.
#  3. Mark entry points in 'U' blocks that are CALLed or JPed to from 'c'
#     blocks with 'c'.
#  4. Split 'c' blocks on RET/JP/JR.
#  5. Scan the disassembly for pairs of adjacent blocks where the start
#     address of the second block is JRed or JPed to from the first block,
#     and join such pairs.
#  6. Examine the remaining 'U' blocks for text.
#  7. Mark data blocks of all zeroes with 's'.
#  8. Join any adjacent data and zero blocks.
TEST_MAP_BIN = (
    # Test that a 'c' block that doesn't end with a RET/JP/JR is extended up to
    # the next RET/JP/JR.
    175,           # 65400 XOR A
    32, 1,         # 65401 JR NZ,65404
    36,            # 65403 INC H
    201,           # 65404 RET

    # Test that a 'c' block is split on RET/JP/JR.
    55,            # 65405 SCF
    201,           # 65406 RET
    63,            # 65407 CCF
    195, 0, 128,   # 65408 JP 32768
    70,            # 65411 LD B,(HL)
    24, 249,       # 65412 JR 65407
    144,           # 65414 SUB B
    233,           # 65415 JP (HL)
    176,           # 65416 OR B
    221, 233,      # 65417 JP (IX)
    65,            # 65419 LD B,C
    253, 233,      # 65420 JP (IY)
    92,            # 65422 LD E,H
    237, 69,       # 65423 RETN
    45,            # 65425 DEC L
    237, 77,       # 65426 RETI

    # Test that two adjacent blocks are joined when the first block JPs into
    # the second block.
    167,           # 65428 AND A
    194, 154, 255, # 65429 JP NZ,65434
    60,            # 65432 INC A
    201,           # 65433 RET
    61,            # 65434 DEC A
    201,           # 65435 RET

    # Test that two adjacent blocks are joined when the first block JRs into
    # the second block.
    167,           # 65436 AND A
    40, 2,         # 65437 JR Z,65441
    61,            # 65439 DEC A
    201,           # 65440 RET
    60,            # 65441 INC A
    201,           # 65442 RET

    # Test that an address not in the map is marked as code if it's CALLed or
    # JPed to from a known code block.
    196, 171, 255, # 65443 CALL NZ,65451
    201,           # 65446 RET
    210, 163, 255, # 65447 JP NC,65443
    201,           # 65450 RET
    39,            # 65451 DAA
    201,           # 65452 RET

    # Test that text-like data is marked as such.
    72, 101, 108, 108, 111, 46, # 65453 DEFM "Hello."
    0, 0, 0, 0, 0,              # 65459 DEFB 0,0,0,0,0
    72, 101, 108, 108, 111, 46, # 65464 DEFM "Hello."
    1, 2, 3, 4, 5, 6, 7, 8, 9,  # 65470 DEFB 1,2,3,4,5,6,7,8,9
    72, 101, 108, 108, 111, 46, # 65479 DEFM "Hello."
    201,                        # 65485 RET

    # Test that a data block of all zeroes is marked with 's'
    0, 0, 0, 0, 0, # 65486 DEFS 5
    201,           # 65491 RET

    # Test that adjacent 's' and 'b' blocks are joined
    0, 0, 0,       # 65492 DEFS 3
    1, 2, 3,       # 65495 DEFB 1,2,3
    201            # 65498 RET
)

TEST_MAP_BIN_ORG = 65400

# Addresses of executed instructions
TEST_MAP = (
    65400, 65401,
    65405, 65406,
    65407, 65408,
    65411, 65412,
    65414, 65415,
    65416, 65417,
    65419, 65420,
    65422, 65423,
    65425, 65426,
    65428, 65429, 65432, 65433, 65434, 65435,
    65436, 65437, 65439, 65440, 65441, 65442,
    65447, 65450,
    65485,
    65491,
    65498
)

TEST_MAP_CTL_G = """@ 65400 start
@ 65400 org
c 65400
c 65405
c 65407
c 65411
c 65414
c 65416
c 65419
c 65422
c 65425
c 65428
c 65436
c 65443
c 65447
c 65451
t 65453
s 65459
t 65464
b 65470
t 65479
c 65485
s 65486
c 65491
b 65492
c 65498
i 65499
"""

def mock_make_snapshot(fname, org, start, end, page):
    global make_snapshot_args
    make_snapshot_args = fname, org, start, end, page
    return [0] * 65536, max(16384, start), end

def mock_run(*args):
    global run_args
    run_args = args

def mock_config(name):
    return {k: v[0] for k, v in COMMANDS[name].items()}

class Sna2CtlTest(SkoolKitTestCase):
    def _create_z80_map(self, addresses):
        bits = []
        map_data = []
        for a in range(65536):
            bits.append('1' if a in addresses else '0')
            if len(bits) == 8:
                map_data.append(int(''.join(reversed(bits)), 2))
                bits = []
        return map_data

    def _create_specemu_map(self, addresses):
        map_data = [0] * 65536
        for address in addresses:
            map_data[address] = 1
        return map_data

    def _create_fuse_profile(self, addresses):
        profile = []
        for a in addresses:
            profile.append('0x{0:X},1'.format(a))
        return profile

    def _create_specemu_log(self, addresses):
        registers = [
            "PC: 0x8492\tSP: 0x5E83"
            "IX: 0x304E\tIY: 0x5C3A",
            "HL: 0x3918\tHL': 0x2758",
            "DE: 0x1023\tDE': 0x369B",
            "BC: 0xA3EA\tBC': 0x1521",
            "AF: 0x0022\tAF': 0x000A",
        ]
        log = []
        log.extend(registers)
        log.append('')
        t_states = 56789
        for a in addresses:
            log.append('{0:04X}  {1:>5}\tNOP'.format(a, t_states))
            t_states = (t_states + 4) % 69888
        log.append('')
        log.extend(registers)
        return log

    def _create_spud_log(self, addresses):
        log = []
        t_states = 12345
        for a in addresses:
            log.append('PC = {0:X}  HL = 0000  tstate = {1:05}  NOP'.format(a, t_states))
            t_states = (t_states + 4) % 70908
        return log

    def _create_zero_log(self, addresses, decimal):
        log = ['All numbers are in {}decimal'.format('' if decimal else 'hexa')]
        log.append('')
        addr_fmt = '{0}' if decimal else '{0:x}'
        t_states = 47
        for a in addresses:
            log.append('{0}\t{1:<5}\tNOP'.format(addr_fmt.format(a), t_states))
            t_states = (t_states + 4) % 69888
        return log

    @patch.object(sna2ctl, 'run', mock_run)
    @patch.object(sna2ctl, 'get_config', mock_config)
    def test_default_option_values(self):
        sna2ctl.main(('test.sna',))
        snafile, options = run_args[:2]
        self.assertEqual(snafile, 'test.sna')
        self.assertEqual(options.ctl_hex, 0)
        self.assertEqual(options.start, 0)
        self.assertEqual(options.end, 65536)
        self.assertIsNone(options.code_map)
        self.assertIsNone(options.org)
        self.assertIsNone(options.page)
        self.assertEqual([], options.params)

    @patch.object(sna2ctl, 'run', mock_run)
    def test_config_read_from_file(self):
        ini = """
            [sna2ctl]
            Hex=1
            TextChars=abcdefghijklmnopqrstuvwxyz
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        sna2ctl.main(('test.sna',))
        snafile, options, config = run_args
        self.assertEqual(snafile, 'test.sna')
        self.assertEqual(options.ctl_hex, 1)
        self.assertEqual(options.start, 0)
        self.assertEqual(options.end, 65536)
        self.assertIsNone(options.code_map)
        self.assertIsNone(options.org)
        self.assertIsNone(options.page)
        self.assertEqual(config['Hex'], 1)
        self.assertEqual(config['TextChars'], 'abcdefghijklmnopqrstuvwxyz')

    @patch.object(sna2ctl, 'run', mock_run)
    def test_invalid_option_values_read_from_file(self):
        ini = """
            [sna2ctl]
            Hex=?
            TextMinLengthCode=x
            TextMinLengthData=!
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        sna2ctl.main(('test.sna',))
        snafile, options, config = run_args
        self.assertEqual(snafile, 'test.sna')
        self.assertEqual(options.ctl_hex, 0)
        self.assertEqual(config['Hex'], 0)
        self.assertEqual(config['TextMinLengthCode'], 12)
        self.assertEqual(config['TextMinLengthData'], 3)

    def test_invalid_option(self):
        output, error = self.run_sna2ctl('-x dummy.bin', catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: sna2ctl.py'))

    def test_invalid_option_value(self):
        for option in (('-e q'), ('-o +'), ('-p ='), ('-s ABC')):
            output, error = self.run_sna2ctl(option, catch_exit=2)
            self.assertEqual(output, '')
            self.assertTrue(error.startswith('usage: sna2ctl.py'))

    def test_no_arguments(self):
        output, error = self.run_sna2ctl(catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: sna2ctl.py'))

    def test_nonexistent_files(self):
        error_tp = '{}: file not found'

        nonexistent_bin = 'nonexistent.bin'
        with self.assertRaisesRegex(SkoolKitError, error_tp.format(nonexistent_bin)):
            self.run_sna2ctl(nonexistent_bin)

        binfile = self.write_bin_file(suffix='.bin')

        nonexistent_map = 'nonexistent.map'
        with self.assertRaisesRegex(SkoolKitError, error_tp.format(nonexistent_map)):
            self.run_sna2ctl('-m {} {}'.format(nonexistent_map, binfile))

        nonexistent_map = self.make_directory()
        with self.assertRaisesRegex(SkoolKitError, '{} is a directory'.format(nonexistent_map)):
            self.run_sna2ctl('-m {} {}'.format(nonexistent_map, binfile))

    def _test_generation(self, data, exp_ctl, code_map=None, options='', exp_err=''):
        if isinstance(data, str):
            infile = data
        else:
            infile = self.write_bin_file(data)
        mapfile = None
        if code_map:
            mapfile = self.write_bin_file(self._create_z80_map(code_map))
            options = '-m {} '.format(mapfile) + options
        output, error = self.run_sna2ctl('{} {}'.format(options, infile))
        if mapfile:
            self.assertEqual(error, 'Reading {}\n'.format(mapfile))
        else:
            self.assertEqual(error, exp_err)
        ctl = dedent(exp_ctl).strip()
        org = ctl[2:7]
        ctl = '@ {0} start\n@ {0} org\n'.format(org) + ctl + '\n'
        self.assertEqual(ctl, output)

    def test_terminal_instructions(self):
        data = [
            120,             # 65415 LD A,B
            195, 126, 255,   # 65416 JP 65406
            175,             # 65419 XOR A
            201,             # 65420 RET
            65,              # 65421 LD B,C
            24, 247,         # 65422 JR 65400
            175,             # 65424 XOR A
            233,             # 65425 JP (HL)
            175,             # 65426 XOR A
            221, 233,        # 65427 JP (IX)
            253, 203, 0, 6,  # 65429 RLC (IY+0)
            253, 233,        # 65433 JP (IY)
            221, 203, 0, 70, # 65435 BIT 0,(IX+0)
            237, 69,         # 65439 RETN
            203, 64,         # 65441 BIT 0,B
            237, 77          # 65443 RETI
        ]
        exp_ctl = """
            c 65415
            c 65419
            c 65421
            c 65424
            c 65426
            c 65429
            c 65435
            c 65441
            i 65445
        """
        self._test_generation(data, exp_ctl, options='-o 65415')

    def test_terminal_bytes(self):
        # Test that byte sequences (201), (195,n,n) and (24,d) don't create
        # block boundaries when they do not correspond to 'RET', 'JP nn' or
        # 'JR d' instructions
        data = [
            62, 201, # 65527 LD A,201
            6, 195,  # 65529 LD B,195
            14, 128, # 65531 LD C,128
            62, 24,  # 65533 LD A,24
            201      # 65535 RET
        ]
        exp_ctl = "c 65527"
        self._test_generation(data, exp_ctl)

    def test_nop_sequence_before_code_block(self):
        data = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 65524 DEFS 10
            167,                          # 65534 AND A
            201                           # 65535 RET
        ]
        exp_ctl = """
            s 65524
            c 65534
        """
        self._test_generation(data, exp_ctl)

    def test_text_in_code_block(self):
        data = [
            175,                # 65522 XOR A
            115, 111, 77, 101,  # 65523 DEFM "soMe"
            116, 101, 120, 116, # 65527 DEFM "text"
            104, 101, 114, 101, # 65531 DEFM "here"
            201                 # 65535 RET
        ]
        exp_ctl = """
            b 65522
            t 65523
            c 65535
        """
        self._test_generation(data, exp_ctl)

    def test_text_too_short_in_code_block(self):
        data = [
            175,                        # 65527 XOR A
            49, 50, 51, 52, 53, 54, 55, # 65528 DEFM "1234567"
            201                         # 65535 RET
        ]
        exp_ctl = "c 65527"
        self._test_generation(data, exp_ctl)

    def test_text_in_data_block(self):
        data = [
            0,                      # 65529 DEFB 0
            72, 101, 108, 108, 111, # 65530 DEFM "Hello"
            0                       # 65535 DEFB 0
        ]
        exp_ctl = """
            b 65529
            t 65530
            b 65535
        """
        self._test_generation(data, exp_ctl)

    def test_text_too_short_in_data_block(self):
        data = [
            0,       # 65532 DEFB 0
            72, 101, # 65533 DEFM "He"
            0        # 65535 DEFB 0
        ]
        exp_ctl = "b 65532"
        self._test_generation(data, exp_ctl)

    def test_instructions_marked_as_data(self):
        data = [
            64, 201,       # 65510 LD B,B; RET
            73, 201,       # 65512 LD C,C; RET
            82, 201,       # 65514 LD D,D; RET
            91, 201,       # 65516 LD E,E; RET
            100, 201,      # 65518 LD H,H; RET
            109, 201,      # 65520 LD L,L; RET
            127, 201,      # 65522 LD A,A; RET
            221, 100, 201, # 65524 LD IXh,IXh; RET
            221, 109, 201, # 65527 LD IXl,IXl; RET
            253, 100, 201, # 65530 LD IYh,IYh; RET
            253, 109, 201  # 65533 LD IYl,IYl; RET
        ]
        exp_ctl = """
            b 65510
            c 65511
            b 65512
            c 65513
            b 65514
            c 65515
            b 65516
            c 65517
            b 65518
            c 65519
            b 65520
            c 65521
            b 65522
            c 65523
            b 65524
            c 65526
            b 65527
            c 65529
            b 65530
            c 65532
            b 65533
            c 65535
        """
        self._test_generation(data, exp_ctl)

    def test_an_instruction_allowed_once(self):
        data = [
            2,   # 65531 LD (BC),A
            201, # 65532 RET
            2,   # 65533 LD (BC),A
            2,   # 65534 LD (BC),A
            201  # 65535 RET
        ]
        exp_ctl = """
            c 65531
            b 65533
            c 65535
        """
        self._test_generation(data, exp_ctl)

    def test_two_ld_h_instructions(self):
        data = [
            96,  # 65530 LD H,B
            97,  # 65531 LD H,C    ; Not allowed
            201, # 65532 RET
            96,  # 65533 LD H,B
            102, # 65534 LD H,(HL) ; This is OK
            201  # 65535 RET
        ]
        exp_ctl = """
            b 65530
            c 65532
            c 65533
        """
        self._test_generation(data, exp_ctl)

    def test_two_ld_l_instructions(self):
        data = [
            104, # 65530 LD L,B
            105, # 65531 LD L,C    ; Not allowed
            201, # 65532 RET
            104, # 65533 LD L,B
            110, # 65534 LD L,(HL) ; This is OK
            201  # 65535 RET
        ]
        exp_ctl = """
            b 65530
            c 65532
            c 65533
        """
        self._test_generation(data, exp_ctl)

    def test_an_instruction_allowed_four_times(self):
        data = [
            4, 4, 4, 4,     # 65525 INC B (x4)
            201,            # 65529 RET
            4, 4, 4, 4, 4,  # 65530 INC B (x5)
            201             # 65535 RET
        ]
        exp_ctl = """
            c 65525
            b 65530
            c 65535
        """
        self._test_generation(data, exp_ctl)

    def test_an_instruction_allowed_seven_times(self):
        data = [
            7, 7, 7, 7, 7, 7, 7,    # 65519 RLCA (x7)
            201,                    # 65526 RET
            7, 7, 7, 7, 7, 7, 7, 7, # 65527 RLCA (x8)
            201                     # 65535 RET
        ]
        exp_ctl = """
            c 65519
            b 65527
            c 65535
        """
        self._test_generation(data, exp_ctl)

    def test_config_TextChars(self):
        data = [
            104, 101, 108, 108, 111, # 65526 DEFM "hello"
            72, 69, 76, 76, 79       # 65531 DEFM "HELLO"
        ]
        exp_ctl = """
            t 65526
            b 65531
        """
        self._test_generation(data, exp_ctl, options='-I TextChars=abcdefghijklmnopqrstuvwxyz')

    def test_config_TextMinLengthCode(self):
        data = [
            175,               # 65530 XOR A
            119, 111, 114, 68, # 65531 DEFM "worD"
            201                # 65535 RET
        ]
        exp_ctl = """
            b 65530
            t 65531
            c 65535
        """
        self._test_generation(data, exp_ctl, options='-I TextMinLengthCode=4')

    def test_config_TextMinLengthData(self):
        data = [
            72, 69, 76, 76, 79,    # 65524 DEFM "hello"
            0,
            72, 69, 76, 76, 79, 46 # 65530 DEFM "hello."
        ]
        exp_ctl = """
            b 65524
            t 65530
        """
        self._test_generation(data, exp_ctl, options='-I TextMinLengthData=6')

    def test_config_Dictionary(self):
        words = '\n'.join(('lives', 'score'))
        wordfile = self.write_text_file(words)
        data = [
            73, 103, 110, 111, 114, 101, 100, 0,         # 65512 DEFM "Ignored",0
            108, 105, 118, 101, 115, 0,                  # 65520 DEFM "lives",0
            72, 105, 103, 104, 32, 83, 99, 111, 114, 101 # 65526 DEFM "High Score"
        ]
        exp_ctl = """
            b 65512
            t 65520
            b 65525
            t 65526
        """
        exp_err = 'Using dictionary file: {}\n'.format(wordfile)
        self._test_generation(data, exp_ctl, options='-I Dictionary={}'.format(wordfile), exp_err=exp_err)

    def test_config_Dictionary_non_existent_file(self):
        data = [72, 101, 108, 108, 111] # 65531 DEFM "Hello"
        exp_ctl = "t 65531"
        exp_err = "Dictionary file 'non-existent.txt' not found\n"
        self._test_generation(data, exp_ctl, options='--ini Dictionary=non-existent.txt', exp_err=exp_err)

    def test_jr_across_64k_boundary(self):
        data = [24]
        exp_ctl = "b 65535"
        self._test_generation(data, exp_ctl)

    def test_CB_at_65535(self):
        data = [203]
        exp_ctl = "b 65535"
        self._test_generation(data, exp_ctl)

    def test_DD_at_65535(self):
        data = [221]
        exp_ctl = "b 65535"
        self._test_generation(data, exp_ctl)

    def test_ED_at_65535(self):
        data = [237]
        exp_ctl = "b 65535"
        self._test_generation(data, exp_ctl)

    def test_FD_at_65535(self):
        data = [253]
        exp_ctl = "b 65535"
        self._test_generation(data, exp_ctl)

    def test_DDCB_at_65534(self):
        data = [221, 203]
        exp_ctl = "b 65534"
        self._test_generation(data, exp_ctl)

    def test_FDCB_at_65534(self):
        data = [253, 203]
        exp_ctl = "b 65534"
        self._test_generation(data, exp_ctl)

    def test_invalid_DDCB_prefix(self):
        data = [221, 203, 0, 0]
        exp_ctl = "b 65532"
        self._test_generation(data, exp_ctl)

    def test_invalid_ED_prefix(self):
        data = [237, 0]
        exp_ctl = "b 65534"
        self._test_generation(data, exp_ctl)

    def test_invalid_FDCB_prefix(self):
        data = [253, 203, 0, 0]
        exp_ctl = "b 65532"
        self._test_generation(data, exp_ctl)

    def test_invalid_ix_prefix(self):
        data = [
            221,       # DEFB 221 (IX prefix, no suffix)
            50, 53, 53 # DEFM "255"
        ]
        exp_ctl = """
            b 65532
            t 65533
        """
        self._test_generation(data, exp_ctl)

    def test_invalid_iy_prefix(self):
        data = [
            253,       # DEFB 253 (IY prefix, no suffix)
            50, 53, 53 # DEFM "255"
        ]
        exp_ctl = """
            b 65532
            t 65533
        """
        self._test_generation(data, exp_ctl)

    def test_end_address_after_ret(self):
        data = [
            62, 7, # 30000 LD A,7
            201,   # 30002 RET
            6, 8,  # 30003 LD B,8
            201    # 30005 RET
        ]
        exp_ctl = """
            c 30000
            i 30003
        """
        self._test_generation(data, exp_ctl, options='-o 30000 -e 30003')

    def test_end_address_not_after_ret(self):
        data = [
            62, 7, # 30000 LD A,7
            201,   # 30002 RET
            6, 8,  # 30003 LD B,8
            201    # 30005 RET
        ]
        exp_ctl = """
            c 30000
            b 30003
            i 30005
        """
        self._test_generation(data, exp_ctl, options='-o 30000 -e 30005')

    def test_end_address_after_text(self):
        data = [
            72, 101, 121, # 30000 DEFM "Hey"
            175,          # 30003 XOR A
            201           # 30004 RET
        ]
        exp_ctl = """
            t 30000
            i 30003
        """
        self._test_generation(data, exp_ctl, options='-o 30000 -e 30003')

    def test_data_block_starting_and_ending_with_zero(self):
        data = [0, 255, 0] # DEFB 0,255,0
        exp_ctl = """
            b 30000
            i 30003
        """
        self._test_generation(data, exp_ctl, options='-o 30000')

    def test_decimal_addresses_below_10000(self):
        data = [0] * 1001
        data[0] = 201
        data[1] = 201
        data[22] = 201
        data[333] = 201
        data[1000] = 201
        exp_ctl = """
            c 00000
            c 00001
            s 00002
            c 00022
            s 00023
            c 00333
            s 00334
            c 01000
            i 01001
        """
        self._test_generation(data, exp_ctl, options='-o 0')

    def test_unrecognised_snapshot_format_is_treated_as_binary(self):
        data = [62, 0, 201]
        exp_ctl = "c 65533"
        binfile = self.write_bin_file(data, suffix='.qux')
        self._test_generation(binfile, exp_ctl)

    def test_terminal_unknown_block(self):
        data = (
            205, 255, 255, # 65531 CALL 65535
            201,           # 65534 RET
            233            # 65535 JP (HL)
        )
        exp_ctl = """
            c 65531
            c 65535
        """
        code_map = (65531, 65534)
        self._test_generation(data, exp_ctl, code_map)

    @patch.object(sna2ctl, 'make_snapshot', mock_make_snapshot)
    def test_option_e(self):
        exp_ctl = """
            s 16384
            i 16386
        """
        for option in ('-e', '--end'):
            self._test_generation('test_e.sna', exp_ctl, options='{} 16386'.format(option))

    @patch.object(sna2ctl, 'make_snapshot', mock_make_snapshot)
    def test_option_e_with_hex_address(self):
        exp_ctl = """
            s 16384
            i 16386
        """
        for option in ('-e', '--end'):
            self._test_generation('test_e.sna', exp_ctl, options='{} 0x4002'.format(option))

    @patch.object(snapshot, 'read_bin_file', Mock(return_value=[201]))
    def test_option_h(self):
        exp_ctl = """
            c $FACE
            i $FACF
        """
        for option in ('-h', '--hex'):
            self._test_generation('test-h.bin', exp_ctl, options='{} -o 64206'.format(option))

    @patch.object(sna2ctl, 'run', mock_run)
    @patch.object(sna2ctl, 'get_config', mock_config)
    def test_option_I(self):
        self.run_sna2ctl('-I Hex=1 test-I.sna')
        options, config = run_args[1:]
        self.assertEqual(['Hex=1'], options.params)
        self.assertEqual(options.ctl_hex, 1)
        self.assertEqual(config['Hex'], 1)

    @patch.object(sna2ctl, 'run', mock_run)
    @patch.object(sna2ctl, 'get_config', mock_config)
    def test_option_I_overrides_other_options(self):
        self.run_sna2ctl('-h -I Hex=1 test.sna')
        options, config = run_args[1:]
        self.assertEqual(['Hex=1'], options.params)
        self.assertEqual(options.ctl_hex, 1)
        self.assertEqual(config['Hex'], 1)

    @patch.object(sna2ctl, 'run', mock_run)
    def test_option_I_overrides_config_read_from_file(self):
        ini = """
            [sna2ctl]
            Hex=2
            TextChars=abc
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        self.run_sna2ctl('--ini Hex=1 -I TextChars=xyz test.bin')
        options, config = run_args[1:]
        self.assertEqual(['Hex=1', 'TextChars=xyz'], options.params)
        self.assertEqual(options.ctl_hex, 1)
        self.assertEqual(config['Hex'], 1)
        self.assertEqual(config['TextChars'], 'xyz')

    @patch.object(sna2ctl, 'run', mock_run)
    @patch.object(sna2ctl, 'get_config', mock_config)
    def test_option_I_multiple(self):
        self.run_sna2ctl('-I Hex=1 --ini TextChars=abc test-I-multiple.bin')
        options, config = run_args[1:]
        self.assertEqual(['Hex=1', 'TextChars=abc'], options.params)
        self.assertEqual(options.ctl_hex, 1)
        self.assertEqual(config['Hex'], 1)
        self.assertEqual(config['TextChars'], 'abc')

    @patch.object(sna2ctl, 'run', mock_run)
    @patch.object(sna2ctl, 'get_config', mock_config)
    def test_option_I_invalid_value(self):
        self.run_sna2ctl('-I Hex=x test-I-invalid.sna')
        options = run_args[1]
        self.assertEqual(options.ctl_hex, 0)

    @patch.object(snapshot, 'read_bin_file', Mock(return_value=[201]))
    def test_option_l(self):
        exp_ctl = """
            c $face
            i $facf
        """
        for option in ('-l', '--hex-lower'):
            self._test_generation('test-l.bin', exp_ctl, options='{} -o 64206'.format(option))

    def test_option_m_with_jr_across_64k_boundary(self):
        code_map = [65535]
        data = [24]
        exp_ctl = "c 65535"
        self._test_generation(data, exp_ctl, code_map)

    def test_option_m_with_237_at_65535(self):
        code_map = [65535]
        data = [237]
        exp_ctl = "c 65535"
        self._test_generation(data, exp_ctl, code_map)

    def test_option_m_with_end_address_after_ret(self):
        code_map = [30000, 30002, 30003, 30005]
        data = [
            62, 7, # 30000 LD A,7
            201,   # 30002 RET
            6, 8,  # 30003 LD B,8
            201    # 30005 RET
        ]
        exp_ctl = """
            c 30000
            i 30003
        """
        self._test_generation(data, exp_ctl, code_map, '-o 30000 -e 30003')

    def test_option_m_with_end_address_not_after_ret(self):
        code_map = [30000, 30002, 30003, 30005]
        data = [
            62, 7, # 30000 LD A,7
            201,   # 30002 RET
            6, 8,  # 30003 LD B,8
            201    # 30005 RET
        ]
        exp_ctl = """
            c 30000
            c 30003
            i 30005
        """
        self._test_generation(data, exp_ctl, code_map, '-o 30000 -e 30005')

    def test_option_m_with_end_address_65536(self):
        code_map = [65533, 65535]
        data = [
            62, 7, # 65533 LD A,7
            201,   # 65535 RET
        ]
        exp_ctl = "c 65533"
        self._test_generation(data, exp_ctl, code_map)

    def _test_option_m(self, code_map, option, map_file=False):
        binfile = self.write_bin_file(TEST_MAP_BIN, suffix='.bin')
        if map_file:
            code_map_file = self.write_bin_file(code_map, suffix='.map')
            exp_error = 'Reading {}\n'.format(code_map_file)
        else:
            code_map_file = self.write_text_file('\n'.join(code_map), suffix='.log')
            exp_error = 'Reading {}: .*100%\x08\x08\x08\x08\n'.format(code_map_file)
        output, error = self.run_sna2ctl('{} {} -o {} {}'.format(option, code_map_file, TEST_MAP_BIN_ORG, binfile))
        match = re.match(exp_error, error)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(), error)
        self.assertEqual(TEST_MAP_CTL_G, output)

    def test_option_m_z80(self):
        self._test_option_m(self._create_z80_map(TEST_MAP), '-m', True)

    def test_option_m_fuse(self):
        self._test_option_m(self._create_fuse_profile(TEST_MAP), '--map')

    def test_option_m_specemu_log(self):
        self._test_option_m(self._create_specemu_log(TEST_MAP), '-m')

    def test_option_m_specemu_map(self):
        self._test_option_m(self._create_specemu_map(TEST_MAP), '-m', True)

    def test_option_m_spud(self):
        self._test_option_m(self._create_spud_log(TEST_MAP), '--map')

    def test_option_m_zero_decimal(self):
        self._test_option_m(self._create_zero_log(TEST_MAP, True), '-m')

    def test_option_m_zero_hexadecimal(self):
        self._test_option_m(self._create_zero_log(TEST_MAP, False), '--map')

    @patch.object(os.path, 'getsize', Mock(side_effect=OSError(1, "Not allowed")))
    def test_option_m_getsize_failure(self):
        mapfile = self.write_bin_file()
        binfile = self.write_bin_file()
        error = "Failed to get size of {}: Not allowed".format(mapfile)
        with self.assertRaisesRegex(SkoolKitError, error):
            self.run_sna2ctl('-m {} {}'.format(mapfile, binfile))

    @patch.object(snapshot, 'read_bin_file', Mock(return_value=[]))
    def _test_option_m_invalid_map(self, code_map, line_no, invalid_line, error):
        code_map_file = self.write_text_file('\n'.join(code_map), suffix='.log')
        with self.assertRaisesRegex(SkoolKitError, '{}, line {}: {}: {}'.format(code_map_file, line_no, error, invalid_line)):
            self.run_sna2ctl('-m {} test-invalid-map.bin'.format(code_map_file))

    def test_option_m_unparseable_address(self):
        invalid_line = '0xABCG,4'
        code_map = ['0xABCF,8', invalid_line, '0xABD2,5']
        self._test_option_m_invalid_map(code_map, 2, invalid_line, 'Cannot parse address')

    def test_option_m_address_out_of_range(self):
        invalid_line = '12345\t11113\tNOP'
        code_map = ['All numbers are in hexadecimal', '8000\t11111\tNOP', invalid_line, '8002\t11117\tNOP']
        self._test_option_m_invalid_map(code_map, 3, invalid_line, 'Address out of range')

    @patch.object(snapshot, 'read_bin_file', Mock(return_value=[]))
    def test_option_m_unrecognised_format(self):
        for code_map in ('', 'PC=FEDC'):
            code_map_file = self.write_text_file(code_map, suffix='.log')
            with self.assertRaisesRegex(SkoolKitError, '{}: Unrecognised format'.format(code_map_file)):
                self.run_sna2ctl('-m {} test-unrecognised-map.bin'.format(code_map_file))

    @patch.object(snapshot, 'read_bin_file', Mock(return_value=[201]))
    def test_option_o(self):
        for option, value in (('-o', 49152), ('--org', 32768)):
            exp_ctl = """
                c {}
                i {}
            """.format(value, value + 1)
            self._test_generation('test.bin', exp_ctl, options='{} {}'.format(option, value))

    @patch.object(snapshot, 'read_bin_file', Mock(return_value=[201]))
    def test_option_o_with_hex_address(self):
        for option, value in (('-o', '0x7f00'), ('--org', '0xAB0C')):
            org = int(value[2:], 16)
            exp_ctl = """
                c {}
                i {}
            """.format(org, org + 1)
            self._test_generation('test.bin', exp_ctl, options='{} {}'.format(option, value))

    @patch.object(sna2ctl, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2ctl, 'generate_ctls', Mock(return_value={0: 'i'}))
    def test_option_p(self):
        for option, exp_page in (('-p', 3), ('--page', 5)):
            output, error = self.run_sna2ctl('{} {} test_p.sna'.format(option, exp_page))
            self.assertEqual(error, '')
            page = make_snapshot_args[4]
            self.assertEqual(page, exp_page)

    @patch.object(sna2ctl, 'get_config', mock_config)
    def test_option_show_config(self):
        output, error = self.run_sna2ctl('--show-config', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            [sna2ctl]
            Dictionary=
            Hex=0
            TextChars=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ !"$%&'()*+,-./:;<=>?[]
            TextMinLengthCode=12
            TextMinLengthData=3
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_show_config_read_from_file(self):
        ini = """
            [sna2ctl]
            Dictionary=words.txt
            Hex=1
            TextChars=abcdefghijklmnopqrstuvwxyz
            TextMinLengthCode=12
            TextMinLengthData=2
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        output, error = self.run_sna2ctl('--show-config', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            [sna2ctl]
            Dictionary=words.txt
            Hex=1
            TextChars=abcdefghijklmnopqrstuvwxyz
            TextMinLengthCode=12
            TextMinLengthData=2
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    @patch.object(sna2ctl, 'make_snapshot', mock_make_snapshot)
    def test_option_s(self):
        exp_ctl = 's 65534'
        for option in ('-s', '--start'):
            self._test_generation('test.sna', exp_ctl, options='{} 65534'.format(option))

    @patch.object(sna2ctl, 'make_snapshot', mock_make_snapshot)
    def test_option_s_with_hex_address(self):
        exp_ctl = 's 65534'
        for option in ('-s', '--start'):
            self._test_generation('test.sna', exp_ctl, options='{} 0xfffe'.format(option))

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_sna2ctl(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))
