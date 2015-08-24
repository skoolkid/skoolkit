# -*- coding: utf-8 -*-
import re
import unittest
try:
    from mock import patch, Mock
except ImportError:
    from unittest.mock import patch, Mock

from skoolkittest import SkoolKitTestCase
from skoolkit import sna2skool, SkoolKitError, VERSION

# Binary data designed to test the default static code analysis algorithm:
#   1. Insert block separators after byte sequences 201 ('RET'), 195,n,n
#      ('JP nn') and 24,d ('JR d').
#   2. Scan for adjacent blocks A and B that overlap (i.e. B starts in the
#      middle of the last instruction in A), and join them.
#   3. Scan the disassembly for blocks that don't end in a 'RET', 'JP nn' or
#      'JR d' instruction, and join them to the following block.
#   4. Scan the disassembly for pairs of adjacent blocks where the start
#      address of the second block is JRed or JPed to from the first block, and
#      join such pairs.
#   5. Mark any sequence of NOPs at the beginning of a block as a separate zero
#      block.
#   6. Examine code blocks for text or data; if text is found, mark any blocks
#      larger than 8 bytes in between as code.
#   7. Scan the disassembly for pairs of adjacent blocks that overlap, and mark
#      the first block in each pair as data; also mark code blocks that have no
#      terminal instruction as data.
#   8. Mark any sequence of NOPs at the beginning of a code block as a separate
#      zero block.
TEST_BIN = (
    # Test that 'RET', 'JP nn' and 'JR d' create block boundaries.
    120,           # 65400 LD A,B
    195, 126, 255, # 65401 JP 65406
    175,           # 65404 XOR A
    201,           # 65405 RET
    65,            # 65406 LD B,C
    24, 247,       # 65407 JR 65400

    # Test that byte sequences (201), (195,n,n) and (24,d) don't create block
    # boundaries when they do not correspond to 'RET', 'JP nn' or 'JR d'
    # instructions.
    62, 201,       # 65409 LD A,201
    6, 195,        # 65411 LD B,195
    14, 128,       # 65413 LD C,128
    62, 24,        # 65415 LD A,24
    201,           # 65417 RET

    # Test that two adjacent blocks are joined when the first block JPs into
    # the second block.
    167,           # 65418 AND A
    194, 144, 255, # 65419 JP NZ,65424
    60,            # 65422 INC A
    201,           # 65423 RET
    61,            # 65424 DEC A
    201,           # 65425 RET

    # Test that two adjacent blocks are joined when the first block JRs into
    # the second block.
    167,           # 65426 AND A
    40, 2,         # 65427 JR Z,65431
    61,            # 65429 DEC A
    201,           # 65430 RET
    60,            # 65431 INC A
    201,           # 65432 RET

    # Test that a sequence of NOPs at the beginning of a block is marked as a
    # separate zero block.
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 65433 DEFS 10
    167,                          # 65443 AND A
    201,                          # 65444 RET

    # Test that overlapping blocks are joined.
    33, 201, 0,    # 65445 LD HL,201
    201,           # 65448 RET

    # Test that text-like data is marked as such, and that any block of 9 or
    # more bytes in between is marked as code if it doesn't overlap and has a
    # terminal instruction, or data otherwise.
    72, 101, 108, 108, 111, 46,   # 65449 DEFM "Hello."
    33, 0, 0, 1, 0, 0, 17, 0, 0,  # 65455 DEFB 33,0,0,1,0,0,17,0,0
    72, 97, 108, 108, 111, 46,    # 65464 DEFM "Hallo."
    1, 0, 0, 1, 0, 0, 221, 33, 0, # 65470 DEFB 1,0,0,1,0,0,221,33,0
    72, 117, 108, 108, 111, 46,   # 65479 DEFM "Hullo."
    1, 0, 0,                      # 65485 LD BC,0
    17, 0, 0,                     # 65488 LD DE,0
    62, 0,                        # 65491 LD A,0
    201,                          # 65493 RET
    72, 97, 108, 108, 111, 46,    # 65494 DEFM "Hallo."

    0, 0,                         # 65500 DEFB 0,0
    201,                          # 65502 RET

    # Test that a data-like block is marked as such.
    7, 7, 7, 7,    # 65503 DEFB 7,7,7,7
    201,           # 65507 RET

    # Some code to separate the data blocks.
    201,           # 65508 RET

    # Test that another data-like block is marked as such.
    1, 2, 2, 1, 2, 2, 1, 2, 2, 2, # 65509 DEFB 1,2,2,1,2,2,1,2,2,2
    201,                          # 65519 RET
)

TEST_BIN_ORG = 65400

TEST_CTL_G = """c 65400
c 65404
c 65406
c 65409
c 65418
c 65426
s 65433
c 65443
c 65445
t 65449
b 65455
t 65464
b 65470
t 65479
c 65485
t 65494
s 65500
c 65502
b 65503
c 65508
b 65509
i 65520"""

TEST_CTL_G_HEX = '\n'.join(['{0} ${1:04X}'.format(line[0], int(line[2:7])) for line in TEST_CTL_G.split('\n')])

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

TEST_MAP_CTL_G = """c 65400
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
b 65470
t 65479
c 65485
s 65486
c 65491
b 65492
c 65498
i 65499"""

mock_get_snapshot = Mock(return_value=[0] * 65536)

class MockCtlParser:
    def __init__(self, ctls=None):
        global mock_ctl_parser
        self.ctls = ctls
        mock_ctl_parser = self

    def parse_ctl(self, ctlfile, min_address, max_address):
        self.ctlfile = ctlfile
        self.min_address = min_address
        self.max_address = max_address

class MockSftParser:
    def __init__(self, snapshot, sftfile, zfill, asm_hex, asm_lower):
        global mock_sft_parser
        mock_sft_parser = self
        self.snapshot = snapshot
        self.sftfile = sftfile
        self.zfill = zfill
        self.asm_hex = asm_hex
        self.asm_lower = asm_lower
        self.wrote_skool = False

    def write_skool(self, min_address, max_address):
        self.min_address = min_address
        self.max_address = max_address
        self.wrote_skool = True

class MockSkoolWriter:
    def __init__(self, snapshot, ctl_parser, options):
        global mock_skool_writer
        mock_skool_writer = self
        self.snapshot = snapshot
        self.ctl_parser = ctl_parser
        self.options = options
        self.wrote_skool = False

    def write_skool(self, write_refs, text):
        self.write_refs = write_refs
        self.text = text
        self.wrote_skool = True

def mock_run(*args):
    global run_args
    run_args = args

class OptionsTest(SkoolKitTestCase):
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

    @patch.object(sna2skool, 'run', mock_run)
    def test_default_option_values(self):
        sna2skool.main(('test.sna',))
        snafile, options = run_args
        self.assertEqual(snafile, 'test.sna')
        self.assertIsNone(options.ctlfile)
        self.assertIsNone(options.sftfile)
        self.assertIsNone(options.genctlfile)
        self.assertFalse(options.ctl_hex)
        self.assertFalse(options.asm_hex)
        self.assertFalse(options.asm_lower)
        self.assertEqual(options.start, 0)
        self.assertEqual(options.end, 65536)
        self.assertIsNone(options.org)
        self.assertIsNone(options.page)
        self.assertFalse(options.text)
        self.assertEqual(options.write_refs, 0)
        self.assertEqual(options.defb_size, 8)
        self.assertEqual(options.defb_mod, 1)
        self.assertEqual(options.line_width, 79)
        self.assertFalse(options.zfill)

    def test_invalid_option(self):
        output, error = self.run_sna2skool('-x dummy.bin', catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: sna2skool.py'))

    def test_invalid_option_value(self):
        for option in (('-s ABC'), ('-o +'), ('-p ='), ('-n q'), ('-m .'), ('-l ?')):
            output, error = self.run_sna2skool(option, catch_exit=2)
            self.assertEqual(len(output), 0)
            self.assertTrue(error.startswith('usage: sna2skool.py'))

    def test_no_arguments(self):
        output, error = self.run_sna2skool(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: sna2skool.py'))

    def test_nonexistent_files(self):
        error_tp = '{0}: file not found'

        nonexistent_bin = 'nonexistent.bin'
        with self.assertRaisesRegexp(SkoolKitError, error_tp.format(nonexistent_bin)):
            self.run_sna2skool(nonexistent_bin)

        binfile = self.write_bin_file(suffix='.bin')

        nonexistent_ctl = 'nonexistent.ctl'
        with self.assertRaisesRegexp(SkoolKitError, error_tp.format(nonexistent_ctl)):
            self.run_sna2skool('-c {0} {1}'.format(nonexistent_ctl, binfile))

        nonexistent_sft = 'nonexistent.sft'
        with self.assertRaisesRegexp(SkoolKitError, error_tp.format(nonexistent_sft)):
            self.run_sna2skool('-T {0} {1}'.format(nonexistent_sft, binfile))

        ctlfile = self.write_text_file()
        nonexistent_map = 'nonexistent.map'
        with self.assertRaisesRegexp(SkoolKitError, error_tp.format(nonexistent_map)):
            self.run_sna2skool('-g {0} -M {1} {2}'.format(ctlfile, nonexistent_map, binfile))

        nonexistent_map = self.make_directory()
        with self.assertRaisesRegexp(SkoolKitError, '{} is a directory'.format(nonexistent_map)):
            self.run_sna2skool('-g {0} -M {1} {2}'.format(ctlfile, nonexistent_map, binfile))

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_sna2skool(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_H(self):
        for option in ('-H', '--skool-hex'):
            output, error = self.run_sna2skool('{} test.sna'.format(option))
            self.assertEqual(error, '')
            self.assertTrue(mock_skool_writer.options.asm_hex)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_L(self):
        for option in ('-L', '--lower'):
            output, error = self.run_sna2skool('{} test.sna'.format(option))
            self.assertEqual(error, '')
            self.assertTrue(mock_skool_writer.options.asm_lower)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'SftParser', MockSftParser)
    def test_option_T(self):
        sftfile = 'test-T.ctl'
        for option in ('-T', '--sft'):
            output, error = self.run_sna2skool('{} {} test.sna'.format(option, sftfile), err_lines=True)
            self.assertEqual(['Using skool file template: {}'.format(sftfile)], error)
            self.assertEqual(mock_sft_parser.sftfile, sftfile)
            self.assertTrue(mock_sft_parser.wrote_skool)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_c(self):
        ctlfile = 'test-c.ctl'
        for option in ('-c', '--ctl'):
            output, error = self.run_sna2skool('{} {} test.sna'.format(option, ctlfile), err_lines=True)
            self.assertEqual(['Using control file: {}'.format(ctlfile)], error)
            self.assertEqual(mock_ctl_parser.ctlfile, ctlfile)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_e(self):
        binfile = self.write_bin_file([0] * 3)
        for option, value in (('-e', 65534), ('--end', 65535)):
            output, error = self.run_sna2skool('{} {} {}'.format(option, value, binfile))
            self.assertEqual(error, '')
            ctls = mock_skool_writer.ctl_parser.ctls
            self.assertIn(value, ctls)
            self.assertEqual(ctls[value], 'i')
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_options_e_and_c(self):
        ctlfile = 'test.ctl'
        end = 34576
        output, error = self.run_sna2skool('-c {} -e {} test.sna'.format(ctlfile, end), err_lines=True)
        self.assertEqual(['Using control file: {}'.format(ctlfile)], error)
        self.assertEqual(mock_ctl_parser.ctlfile, ctlfile)
        self.assertEqual(mock_ctl_parser.min_address, 0)
        self.assertEqual(mock_ctl_parser.max_address, end)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'SftParser', MockSftParser)
    def test_options_e_and_T(self):
        sftfile = 'test.sft'
        end = 45678
        output, error = self.run_sna2skool('-T {} -e {} test.sna'.format(sftfile, end), err_lines=True)
        self.assertEqual(['Using skool file template: {}'.format(sftfile)], error)
        self.assertEqual(mock_sft_parser.sftfile, sftfile)
        self.assertEqual(mock_sft_parser.min_address, 0)
        self.assertEqual(mock_sft_parser.max_address, end)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_g(self):
        ctlfile = self.write_text_file()
        binfile = self.write_bin_file(TEST_BIN, suffix='.bin')
        for option in ('-g', '--generate-ctl'):
            output, error = self.run_sna2skool('{} {} -o {} {}'.format(option, ctlfile, TEST_BIN_ORG, binfile))
            self.assertEqual(error, '')
            with open(ctlfile, 'r') as f:
                lines = [line.rstrip() for line in f]
            self.assertEqual(TEST_CTL_G.split('\n'), lines)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_g_with_end_address_after_ret(self):
        ctlfile = self.write_text_file()
        data = [
            62, 7, # 30000 LD A,7
            201,   # 30002 RET
            6, 8,  # 30003 LD B,8
            201    # 30005 RET
        ]
        binfile = self.write_bin_file(data)
        output, error = self.run_sna2skool('-g {} -o 30000 -e 30003 {}'.format(ctlfile, binfile))
        self.assertEqual(error, '')
        with open(ctlfile, 'r') as f:
            gen_ctl = [line.rstrip() for line in f]
        self.assertEqual(['c 30000', 'i 30003'], gen_ctl)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_g_with_end_address_not_after_ret(self):
        ctlfile = self.write_text_file()
        data = [
            62, 7, # 30000 LD A,7
            201,   # 30002 RET
            6, 8,  # 30003 LD B,8
            201    # 30005 RET
        ]
        binfile = self.write_bin_file(data)
        output, error = self.run_sna2skool('-g {} -o 30000 -e 30005 {}'.format(ctlfile, binfile))
        self.assertEqual(error, '')
        with open(ctlfile, 'r') as f:
            gen_ctl = [line.rstrip() for line in f]
        self.assertEqual(['c 30000', 'b 30003', 'i 30005'], gen_ctl)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_options_g_and_M_with_end_address_after_ret(self):
        ctlfile = self.write_text_file()
        data = [
            62, 7, # 30000 LD A,7
            201,   # 30002 RET
            6, 8,  # 30003 LD B,8
            201    # 30005 RET
        ]
        binfile = self.write_bin_file(data)
        mapfile = self.write_bin_file(self._create_z80_map([30000, 30002, 30003, 30005]))
        output, error = self.run_sna2skool('-g {} -M {} -o 30000 -e 30003 {}'.format(ctlfile, mapfile, binfile))
        self.assertEqual(error, 'Reading {}\n'.format(mapfile))
        with open(ctlfile, 'r') as f:
            gen_ctl = [line.rstrip() for line in f]
        self.assertEqual(['c 30000', 'i 30003'], gen_ctl)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_options_g_and_M_with_end_address_not_after_ret(self):
        ctlfile = self.write_text_file()
        data = [
            62, 7, # 30000 LD A,7
            201,   # 30002 RET
            6, 8,  # 30003 LD B,8
            201    # 30005 RET
        ]
        binfile = self.write_bin_file(data)
        mapfile = self.write_bin_file(self._create_z80_map([30000, 30002, 30003, 30005]))
        output, error = self.run_sna2skool('-g {} -M {} -o 30000 -e 30005 {}'.format(ctlfile, mapfile, binfile))
        self.assertEqual(error, 'Reading {}\n'.format(mapfile))
        with open(ctlfile, 'r') as f:
            gen_ctl = [line.rstrip() for line in f]
        self.assertEqual(['c 30000', 'c 30003', 'i 30005'], gen_ctl)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_options_g_and_M_with_end_address_65536(self):
        ctlfile = self.write_text_file()
        data = [
            62, 7, # 65533 LD A,7
            201,   # 65535 RET
        ]
        binfile = self.write_bin_file(data)
        mapfile = self.write_bin_file(self._create_z80_map([65533, 65535]))
        output, error = self.run_sna2skool('-g {} -M {} {}'.format(ctlfile, mapfile, binfile))
        self.assertEqual(error, 'Reading {}\n'.format(mapfile))
        with open(ctlfile, 'r') as f:
            gen_ctl = [line.rstrip() for line in f]
        self.assertEqual(['c 65533'], gen_ctl)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def _test_option_M(self, code_map, option, map_file=False):
        ctlfile = self.write_text_file()
        binfile = self.write_bin_file(TEST_MAP_BIN, suffix='.bin')
        if map_file:
            code_map_file = self.write_bin_file(code_map, suffix='.map')
            exp_error = 'Reading {}\n'.format(code_map_file)
        else:
            code_map_file = self.write_text_file('\n'.join(code_map), suffix='.log')
            exp_error = 'Reading {}: .*100%\x08\x08\x08\x08\n'.format(code_map_file)
        output, error = self.run_sna2skool('-g {} {} {} -o {} {}'.format(ctlfile, option, code_map_file, TEST_MAP_BIN_ORG, binfile), out_lines=False)
        match = re.match(exp_error, error)
        if match is None or match.group() != error:
            self.fail('"{}" != "{}"'.format(error, exp_error))
        with open(ctlfile, 'r') as f:
            lines = [line.rstrip() for line in f]
        self.assertEqual(TEST_MAP_CTL_G.split('\n'), lines)
        self.assertTrue(mock_skool_writer.wrote_skool)

    def test_option_M_z80(self):
        self._test_option_M(self._create_z80_map(TEST_MAP), '-M', True)

    def test_option_M_fuse(self):
        self._test_option_M(self._create_fuse_profile(TEST_MAP), '--map')

    def test_option_M_specemu_log(self):
        self._test_option_M(self._create_specemu_log(TEST_MAP), '-M')

    def test_option_M_specemu_map(self):
        self._test_option_M(self._create_specemu_map(TEST_MAP), '-M', True)

    def test_option_M_spud(self):
        self._test_option_M(self._create_spud_log(TEST_MAP), '--map')

    def test_option_M_zero_decimal(self):
        self._test_option_M(self._create_zero_log(TEST_MAP, True), '-M')

    def test_option_M_zero_hexadecimal(self):
        self._test_option_M(self._create_zero_log(TEST_MAP, False), '--map')

    @patch.object(sna2skool, 'read_bin_file', Mock(return_value=[]))
    def _test_option_M_invalid_map(self, code_map, line_no, invalid_line, error):
        ctlfile = self.write_text_file()
        code_map_file = self.write_text_file('\n'.join(code_map), suffix='.log')
        with self.assertRaisesRegexp(SkoolKitError, '{}, line {}: {}: {}'.format(code_map_file, line_no, error, invalid_line)):
            self.run_sna2skool('-g {} -M {} test-invalid-map.bin'.format(ctlfile, code_map_file))

    def test_option_M_unparseable_address(self):
        invalid_line = '0xABCG,4'
        code_map = ['0xABCF,8', invalid_line, '0xABD2,5']
        self._test_option_M_invalid_map(code_map, 2, invalid_line, 'Cannot parse address')

    def test_option_M_address_out_of_range(self):
        invalid_line = '12345\t11113\tNOP'
        code_map = ['All numbers are in hexadecimal', '8000\t11111\tNOP', invalid_line, '8002\t11117\tNOP']
        self._test_option_M_invalid_map(code_map, 3, invalid_line, 'Address out of range')

    @patch.object(sna2skool, 'read_bin_file', Mock(return_value=[]))
    def test_option_M_unrecognised_format(self):
        ctlfile = self.write_text_file()
        for code_map in ('', 'PC=FEDC'):
            code_map_file = self.write_text_file(code_map, suffix='.log')
            with self.assertRaisesRegexp(SkoolKitError, '{}: Unrecognised format'.format(code_map_file)):
                self.run_sna2skool('-g {} -M {} test-unrecognised-map.bin'.format(ctlfile, code_map_file))

    @patch.object(sna2skool, 'read_bin_file', Mock(return_value=[201]))
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_h(self):
        for option in ('-h', '--ctl-hex'):
            ctlfile = self.write_text_file()
            self.run_sna2skool('-g {} {} -o 64206 test-h.bin'.format(ctlfile, option))
            with open(ctlfile, 'r') as f:
                gen_ctl = [line.rstrip() for line in f]
            self.assertEqual(['c $FACE', 'i $FACF'], gen_ctl)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_i(self):
        data = [
            62, 7, # 65533 LD A,7
            201,   # 65535 RET
        ]
        binfile = self.write_bin_file(data)
        for option in ('-i', '--ctl-hex-lower'):
            ctlfile = self.write_text_file()
            self.run_sna2skool('-g {} {} {}'.format(ctlfile, option, binfile))
            with open(ctlfile, 'r') as f:
                gen_ctl = [line.rstrip() for line in f]
            self.assertEqual(['c $fffd'], gen_ctl)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_l(self):
        for option, value in (('-l', 5), ('--defm-size', 8)):
            output, error = self.run_sna2skool('{} {} test.sna'.format(option, value))
            self.assertEqual(error, '')
            self.assertEqual(mock_skool_writer.options.defm_width, value)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_m(self):
        for option, value in (('-m', 5), ('--defb-mod', 6)):
            output, error = self.run_sna2skool('{} {} test.sna'.format(option, value))
            self.assertEqual(error, '')
            self.assertEqual(mock_skool_writer.options.defb_mod, value)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_n(self):
        for option, value in (('-n', 3), ('--defb-size', 7)):
            output, error = self.run_sna2skool('{} {} test.sna'.format(option, value))
            self.assertEqual(error, '')
            self.assertEqual(mock_skool_writer.options.defb_size, value)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'read_bin_file', Mock(return_value=[201]))
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_o(self):
        for option, value in (('-o', 49152), ('--org', 32768)):
            output, error = self.run_sna2skool('{} {} test.bin'.format(option, value))
            self.assertEqual(error, '')
            self.assertEqual({value: 'c', value + 1: 'i'}, mock_ctl_parser.ctls)
            self.assertEqual(mock_skool_writer.snapshot[value], 201)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_p(self):
        ram = [0] * 49152
        pages = {3: [201] + [0] * 16383}
        ctlfile = self.write_text_file('c49152\ni49153', suffix='.ctl')
        z80file = self.write_z80(ram, version=3, machine_id=4, pages=pages)[1]
        for option in ('-p', '--page'):
            self.run_sna2skool('-c {} {} 3 {}'.format(ctlfile, option, z80file))
            self.assertEqual(mock_skool_writer.snapshot[49152], 201)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_r(self):
        binfile = self.write_bin_file(suffix='.bin')
        for option in ('-r', '--no-erefs'):
            output, error = self.run_sna2skool('{} {}'.format(option, binfile))
            self.assertEqual(error, '')
            self.assertEqual(mock_skool_writer.write_refs, -1)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_R(self):
        binfile = self.write_bin_file(suffix='.bin')
        for option in ('-R', '--erefs'):
            output, error = self.run_sna2skool('{} {}'.format(option, binfile))
            self.assertEqual(error, '')
            self.assertEqual(mock_skool_writer.write_refs, 1)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_s(self):
        start = 65534
        exp_ctls = {start: 'c', 65536: 'i'}
        for option in ('-s', '--start'):
            output, error = self.run_sna2skool('{} {} test.sna'.format(option, start))
            self.assertEqual(error, '')
            self.assertEqual(exp_ctls, mock_ctl_parser.ctls)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_options_s_and_c(self):
        ctlfile = 'test.ctl'
        start = 12345
        output, error = self.run_sna2skool('-c {} -s {} test.sna'.format(ctlfile, start), err_lines=True)
        self.assertEqual(['Using control file: {}'.format(ctlfile)], error)
        self.assertEqual(mock_ctl_parser.ctlfile, ctlfile)
        self.assertEqual(mock_ctl_parser.min_address, start)
        self.assertEqual(mock_ctl_parser.max_address, 65536)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_options_s_and_e_and_c(self):
        ctlfile = 'test.ctl'
        start = 12345
        end = 23456
        output, error = self.run_sna2skool('-c {} -s {} -e {} test.z80'.format(ctlfile, start, end), err_lines=True)
        self.assertEqual(['Using control file: {}'.format(ctlfile)], error)
        self.assertEqual(mock_ctl_parser.ctlfile, ctlfile)
        self.assertEqual(mock_ctl_parser.min_address, start)
        self.assertEqual(mock_ctl_parser.max_address, end)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'SftParser', MockSftParser)
    def test_options_s_and_T(self):
        sftfile = 'test.sft'
        start = 45678
        output, error = self.run_sna2skool('-T {} -s {} test.sna'.format(sftfile, start), err_lines=True)
        self.assertEqual(['Using skool file template: {}'.format(sftfile)], error)
        self.assertEqual(mock_sft_parser.sftfile, sftfile)
        self.assertEqual(mock_sft_parser.min_address, start)
        self.assertEqual(mock_sft_parser.max_address, 65536)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'SftParser', MockSftParser)
    def test_options_s_and_e_and_T(self):
        sftfile = 'test.sft'
        start = 23456
        end = 34567
        output, error = self.run_sna2skool('-T {} -s {} -e {} test.sna'.format(sftfile, start, end), err_lines=True)
        self.assertEqual(['Using skool file template: {}'.format(sftfile)], error)
        self.assertEqual(mock_sft_parser.sftfile, sftfile)
        self.assertEqual(mock_sft_parser.min_address, start)
        self.assertEqual(mock_sft_parser.max_address, end)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_t(self):
        for option in ('-t', '--text'):
            output, error = self.run_sna2skool('{} test.sna'.format(option))
            self.assertEqual(error, '')
            self.assertTrue(mock_skool_writer.text)
            mock_skool_writer.text = None
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_w(self):
        binfile = self.write_bin_file(suffix='.bin')
        line_width = 120
        for option in ('-w', '--line-width'):
            output, error = self.run_sna2skool('{} {} {}'.format(option, line_width, binfile))
            self.assertEqual(error, '')
            self.assertEqual(mock_skool_writer.options.line_width, line_width)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'get_snapshot', mock_get_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_z(self):
        for option in ('-z', '--defb-zfill'):
            self.run_sna2skool('{} test-z.sna'.format(option))
            self.assertTrue(mock_skool_writer.options.zfill)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_unrecognised_snapshot_format_is_treated_as_binary(self):
        data = [1, 2, 3]
        binfile = self.write_bin_file(data, suffix='.qux')
        self.run_sna2skool(binfile)
        self.assertEqual(data, mock_skool_writer.snapshot[65533:65536])
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'run', mock_run)
    def test_default_sft(self):
        # Test that the default skool file template is used if present
        snafile = 'test-default-sft.sna'
        sftfile = '{}.sft'.format(snafile[:-4])
        self.write_text_file(path=sftfile)
        sna2skool.main((snafile,))
        snafile, options = run_args
        self.assertEqual(options.sftfile, sftfile)

        # Test that a control file specified by the '-c' option takes
        # precedence over the default skool file template
        ctlfile = self.write_text_file(suffix='.ctl')
        sna2skool.main(('-c', ctlfile, snafile))
        options = run_args[1]
        self.assertIsNone(options.sftfile)
        self.assertEqual(options.ctlfile, ctlfile)

    @patch.object(sna2skool, 'run', mock_run)
    def test_default_sft_for_unrecognised_snapshot_format(self):
        binfile = 'snapshot.foo'
        sftfile = self.write_text_file(path='{}.sft'.format(binfile))
        sna2skool.main((binfile,))
        options = run_args[1]
        self.assertEqual(options.sftfile, sftfile)

    @patch.object(sna2skool, 'run', mock_run)
    def test_default_ctl(self):
        # Test that the default control file is used if present
        snafile = 'test-default-ctl.sna'
        ctlfile = '{}.ctl'.format(snafile[:-4])
        self.write_text_file(path=ctlfile)
        sna2skool.main((snafile,))
        options = run_args[1]
        self.assertEqual(options.ctlfile, ctlfile)

        # Test that a skool file template specified by the '-T' option takes
        # precedence over the default control file
        sftfile = self.write_text_file(suffix='.sft')
        sna2skool.main(('-T', sftfile, snafile))
        options = run_args[1]
        self.assertIsNone(options.ctlfile)
        self.assertEqual(options.sftfile, sftfile)

    @patch.object(sna2skool, 'run', mock_run)
    def test_default_ctl_for_unrecognised_snapshot_format(self):
        binfile = 'input.bar'
        ctlfile = self.write_text_file(path='{}.ctl'.format(binfile))
        sna2skool.main((binfile,))
        snafile, options = run_args
        self.assertEqual(options.ctlfile, ctlfile)

    @patch.object(sna2skool, 'write_ctl', Mock())
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_terminal_unknown_block(self):
        data = (
            205, 255, 255, # 65531 CALL 65535
            201,           # 65534 RET
            233            # 65535 JP (HL)
        )
        code_map = self._create_z80_map((65531, 65534))
        code_map_file = self.write_bin_file(code_map, suffix='.map')
        binfile = self.write_bin_file(data, suffix='.bin')
        self.run_sna2skool('-g test.ctl -M {} {}'.format(code_map_file, binfile))
        self.assertEqual({65531: 'c', 65535: 'c', 65536: 'i'}, mock_ctl_parser.ctls)
        self.assertTrue(mock_skool_writer.wrote_skool)

if __name__ == '__main__':
    unittest.main()
