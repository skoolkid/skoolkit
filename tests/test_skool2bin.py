import textwrap
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError, VERSION, skool2bin

class MockBinWriter:
    def __init__(self, skoolfile, asm_mode, fix_mode):
        global mock_bin_writer
        mock_bin_writer = self
        self.skoolfile = skoolfile
        self.asm_mode = asm_mode
        self.fix_mode = fix_mode
        self.binfile = None
        self.start = None
        self.end = None

    def write(self, binfile, start, end):
        self.binfile = binfile
        self.start = start
        self.end = end

class Skool2BinTest(SkoolKitTestCase):
    def test_no_arguments(self):
        output, error = self.run_skool2bin(catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: skool2bin.py'))

    def test_invalid_option(self):
        output, error = self.run_skool2bin('-x test.skool', catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: skool2bin.py'))

    def test_invalid_option_value(self):
        skoolfile = self.write_text_file(suffix='.skool')
        for option in ('-E ABC', '-S ='):
            output, error = self.run_skool2bin('{} {}'.format(option, skoolfile), catch_exit=2)
            self.assertEqual(output, '')
            self.assertTrue(error.startswith('usage: skool2bin.py'))

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_default_option_values(self):
        skoolfile = 'test-defaults.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        output, error = self.run_skool2bin(skoolfile)
        self.assertEqual(len(error), 0)
        self.assertEqual(mock_bin_writer.skoolfile, skoolfile)
        self.assertEqual(mock_bin_writer.asm_mode, 0)
        self.assertEqual(mock_bin_writer.fix_mode, 0)
        self.assertEqual(mock_bin_writer.binfile, exp_binfile)
        self.assertIsNone(mock_bin_writer.start)
        self.assertIsNone(mock_bin_writer.end)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_nonstandard_skool_name(self):
        skoolfile = 'nonstandard.sks'
        exp_binfile = skoolfile + '.bin'
        output, error = self.run_skool2bin(skoolfile)
        self.assertEqual(len(error), 0)
        self.assertEqual(mock_bin_writer.binfile, exp_binfile)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_skool_file_from_stdin(self):
        output, error = self.run_skool2bin('-')
        self.assertEqual(len(error), 0)
        self.assertEqual(mock_bin_writer.binfile, 'program.bin')

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_output_filename(self):
        skoolfile = 'test.skool'
        binfile = 'test-output-filename.bin'
        output, error = self.run_skool2bin('{} {}'.format(skoolfile, binfile))
        self.assertEqual(len(error), 0)
        self.assertEqual(mock_bin_writer.binfile, binfile)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_b(self):
        skoolfile = 'test-b.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option in ('-b', '--bfix'):
            output, error = self.run_skool2bin('{} {}'.format(option, skoolfile))
            self.assertEqual(len(error), 0)
            self.assertEqual(mock_bin_writer.skoolfile, skoolfile)
            self.assertEqual(mock_bin_writer.asm_mode, 0)
            self.assertEqual(mock_bin_writer.fix_mode, 2)
            self.assertEqual(mock_bin_writer.binfile, exp_binfile)
            self.assertIsNone(mock_bin_writer.start)
            self.assertIsNone(mock_bin_writer.end)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_E(self):
        skoolfile = 'test-E.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option, value in (('-E', 32768), ('--end', 49152)):
            output, error = self.run_skool2bin('{} {} {}'.format(option, value, skoolfile))
            self.assertEqual(len(error), 0)
            self.assertEqual(mock_bin_writer.skoolfile, skoolfile)
            self.assertEqual(mock_bin_writer.asm_mode, 0)
            self.assertEqual(mock_bin_writer.fix_mode, 0)
            self.assertEqual(mock_bin_writer.binfile, exp_binfile)
            self.assertIsNone(mock_bin_writer.start)
            self.assertEqual(mock_bin_writer.end, value)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_E_with_hex_address(self):
        skoolfile = 'test-E-hex.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option, value in (('-E', '0x7ff0'), ('--end', '0xA1B5')):
            output, error = self.run_skool2bin('{} {} {}'.format(option, value, skoolfile))
            self.assertEqual(len(error), 0)
            self.assertEqual(mock_bin_writer.skoolfile, skoolfile)
            self.assertEqual(mock_bin_writer.asm_mode, 0)
            self.assertEqual(mock_bin_writer.fix_mode, 0)
            self.assertEqual(mock_bin_writer.binfile, exp_binfile)
            self.assertIsNone(mock_bin_writer.start)
            self.assertEqual(mock_bin_writer.end, int(value[2:], 16))

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_i(self):
        skoolfile = 'test-i.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option in ('-i', '--isub'):
            output, error = self.run_skool2bin('{} {}'.format(option, skoolfile))
            self.assertEqual(len(error), 0)
            self.assertEqual(mock_bin_writer.skoolfile, skoolfile)
            self.assertEqual(mock_bin_writer.asm_mode, 1)
            self.assertEqual(mock_bin_writer.fix_mode, 0)
            self.assertEqual(mock_bin_writer.binfile, exp_binfile)
            self.assertIsNone(mock_bin_writer.start)
            self.assertIsNone(mock_bin_writer.end)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_o(self):
        skoolfile = 'test-o.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option in ('-o', '--ofix'):
            output, error = self.run_skool2bin('{} {}'.format(option, skoolfile))
            self.assertEqual(len(error), 0)
            self.assertEqual(mock_bin_writer.skoolfile, skoolfile)
            self.assertEqual(mock_bin_writer.asm_mode, 0)
            self.assertEqual(mock_bin_writer.fix_mode, 1)
            self.assertEqual(mock_bin_writer.binfile, exp_binfile)
            self.assertIsNone(mock_bin_writer.start)
            self.assertIsNone(mock_bin_writer.end)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_s(self):
        skoolfile = 'test-s.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option in ('-s', '--ssub'):
            output, error = self.run_skool2bin('{} {}'.format(option, skoolfile))
            self.assertEqual(len(error), 0)
            self.assertEqual(mock_bin_writer.skoolfile, skoolfile)
            self.assertEqual(mock_bin_writer.asm_mode, 2)
            self.assertEqual(mock_bin_writer.fix_mode, 0)
            self.assertEqual(mock_bin_writer.binfile, exp_binfile)
            self.assertIsNone(mock_bin_writer.start)
            self.assertIsNone(mock_bin_writer.end)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_S(self):
        skoolfile = 'test-S.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option, value in (('-S', 24576), ('--start', 32768)):
            output, error = self.run_skool2bin('{} {} {}'.format(option, value, skoolfile))
            self.assertEqual(len(error), 0)
            self.assertEqual(mock_bin_writer.skoolfile, skoolfile)
            self.assertEqual(mock_bin_writer.asm_mode, 0)
            self.assertEqual(mock_bin_writer.fix_mode, 0)
            self.assertEqual(mock_bin_writer.binfile, exp_binfile)
            self.assertEqual(mock_bin_writer.start, value)
            self.assertIsNone(mock_bin_writer.end)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_S_with_hex_address(self):
        skoolfile = 'test-S-hex.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option, value in (('-S', '0x7abc'), ('--start', '0xFA0A')):
            output, error = self.run_skool2bin('{} {} {}'.format(option, value, skoolfile))
            self.assertEqual(len(error), 0)
            self.assertEqual(mock_bin_writer.skoolfile, skoolfile)
            self.assertEqual(mock_bin_writer.asm_mode, 0)
            self.assertEqual(mock_bin_writer.fix_mode, 0)
            self.assertEqual(mock_bin_writer.binfile, exp_binfile)
            self.assertEqual(mock_bin_writer.start, int(value[2:], 16))
            self.assertIsNone(mock_bin_writer.end)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_skool2bin(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))

class BinWriterTest(SkoolKitTestCase):
    stdout_binary = True

    def _test_write(self, skool, base_address, exp_data, asm_mode=0, fix_mode=0, start=None, end=None):
        if skool is None:
            skoolfile = '-'
            binfile = self.write_bin_file(suffix='.bin')
        else:
            skoolfile = self.write_text_file(textwrap.dedent(skool).strip(), suffix='.skool')
            binfile = skoolfile[:-6] + '.bin'
            self.tempfiles.append(binfile)
        bin_writer = skool2bin.BinWriter(skoolfile, asm_mode, fix_mode)
        bin_writer.write(binfile, start, end)
        with open(binfile, 'rb') as f:
            data = list(f.read())
        self.assertEqual(exp_data, data)
        size = len(data)
        status = "Wrote {}: start={}, end={}, size={}\n".format(binfile, base_address, base_address + size, size)
        self.assertEqual(status, self.err.getvalue())
        self.err.clear()

    def test_write(self):
        skool = """
            ; Routine at 30000
            @label=START
            c30000 RET

            ; Routine at 30001
            @ssub-begin
            c30001 LD A,10  ; Load the
                            ; accumulator with 10
            @ssub+else
            c30001 LD A,11  ; Load the
                            ; accumulator with 11
            @ssub+end
             30003 RET
        """
        self._test_write(skool, 30000, [201, 62, 10, 201])

    def test_write_i_block(self):
        skool = """
            i29999 DEFB 128

            c30000 RET
        """
        self._test_write(skool, 29999, [128, 201])

    def test_nonexistent_skool_file(self):
        with self.assertRaises(SkoolKitError) as cm:
            self.run_skool2bin('nonexistent.skool')
        self.assertEqual(cm.exception.args[0], 'nonexistent.skool: file not found')

    def test_invalid_instruction_address(self):
        skoolfile = self.write_text_file('c4000d RET', suffix='.skool')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_skool2bin(skoolfile)
        self.assertEqual(cm.exception.args[0], 'Invalid address (4000d):\nc4000d RET')

    def test_invalid_instruction(self):
        skoolfile = self.write_text_file('c40000 XOR HL', suffix='.skool')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_skool2bin(skoolfile)
        self.assertEqual(cm.exception.args[0], 'Failed to assemble:\n 40000 XOR HL')

    def test_invalid_sub_instruction(self):
        skool = """
            @start
            c40000 LD A,B
            @{}=XOR HL
             40001 XOR L
             40002 RET
        """
        exp_error = 'Failed to assemble:\n 40001 XOR HL'
        for option, asm_dir in (
                ('-i', 'isub'),
                ('-s', 'ssub'),
                ('-o', 'ofix'),
                ('-b', 'bfix')
        ):
            with self.subTest(option=option, asm_dir=asm_dir):
                skoolfile = self.write_text_file(textwrap.dedent(skool.format(asm_dir)).strip(), suffix='.skool')
                with self.assertRaises(SkoolKitError) as cm:
                    self.run_skool2bin('{} {}'.format(option, skoolfile))
                self.assertEqual(cm.exception.args[0], 'Failed to assemble:\n 40001 XOR HL')

    def test_skool_file_from_stdin(self):
        self.write_stdin('c49152 RET')
        self._test_write(None, 49152, [201])

    def test_binary_file_to_stdout(self):
        skoolfile = self.write_text_file('t30000 DEFM "abc"', suffix='.skool')
        bin_writer = skool2bin.BinWriter(skoolfile)
        bin_writer.write('-', None, None)
        self.assertEqual(self.out.getvalue(), b'abc')
        self.assertEqual(self.err.getvalue(), "Wrote stdout: start=30000, end=30003, size=3\n")

    def test_start_address(self):
        skool = """
            c50000 LD A,C
             50001 XOR B
             50002 RET
        """
        self._test_write(skool, 50001, [168, 201], start=50001)

    def test_end_address(self):
        skool = """
            c60000 LD A,C
             60001 XOR B
             60002 RET
        """
        self._test_write(skool, 60000, [121, 168], end=60002)

    def test_start_address_and_end_address(self):
        skool = """
            c32768 LD A,C
             32769 XOR B
             32770 RET
        """
        self._test_write(skool, 32769, [168], start=32769, end=32770)

    def test_overlapping_instructions(self):
        skool = """
            b30000 DEFS 3,1
             30002 XOR A    ; The address of this instruction is ignored
        """
        exp_data = [1, 1, 1, 175]
        self._test_write(skool, 30000, exp_data)

    def test_isub_mode(self):
        skool = """
            c40000 XOR A
            @isub=LD B,1
            @ssub=LD B,2
             40001 LD B,n
            @isub=LD C,1 ; Set C=1
             40003 LD C,n
            @isub=|XOR A ; Test @isub replacing
            @isub=       ; one instruction with two.
            @isub=|INC A
             40005 LD A,1
            @isub=|LD A,1 ; Test @isub replacing two instructions with one.
             40007 XOR A
             40008 INC A
            @isub=       ; Test @isub replacing the comment only.
             40009 SUB B
            @if({asm})(isub=XOR D)
             40010 XOR C
            @isub=|      ; Test @isub replacing
            @isub=|OR H  ; a later instruction
             40011 OR D
             40012 OR E
            @isub=BEGIN: OR B ; Test @isub defining a label
             40013 OR A
            @isub=>LD B,A ; Test @isub inserting an instruction before
             40014 XOR A
            @isub=+XOR C  ; Test @isub inserting an instruction after
             40015 XOR B
             40016 XOR D
            @isub=!40017-40019
             40017 CP 255 ; This should be removed

            @isub+begin
            @ssub=!40019
            c40019 CP 1   ; Not removed by @isub=!40017-40019 in previous entry
            @isub+end
        """
        exp_data = [
            175,   # 40000 XOR A
            6, 1,  # 40001 LD B,1
            14, 1, # 40003 LD C,1
            175,   # 40005 XOR A
            60,    # 40006 INC A
            62, 1, # 40007 LD A,1
            144,   # 40009 SUB B
            170,   # 40010 XOR D
            178,   # 40011 OR D
            180,   # 40012 OR H
            176,   # 40013 OR B
            71,    # 40014 LD B,A (inserted)
            175,   # 40015 XOR A
            168,   # 40016 XOR B
            169,   # 40017 XOR C (inserted)
            170,   # 40018 XOR D
            254, 1 # 40019 CP 1
        ]
        self._test_write(skool, 40000, exp_data, asm_mode=1)

    def test_ssub_mode(self):
        skool = """
            @ssub-begin
            c50000 INC L
            @ssub+else
            c50000 INC HL
            @ssub+end
            @ssub=INC DE
             50001 INC E
            @ssub=INC BC ; Increment BC
             50002 INC C
            @rsub-begin
             50003 RET
            @rsub+else
            ; The following @ssub directive should be ignored.
            @ssub=RET P
             50003 JP 32768
            @rsub+end
            @ssub=|XOR A ; Test @ssub replacing one instruction with two.
            @ssub=|INC A
             50004 LD A,1
            @ssub=|LD A,1 ; Test @ssub replacing two instructions with one.
             50006 XOR A
             50007 INC A
            @ssub=       ; Test @ssub replacing the comment only.
             50008 SUB B
            @if({asm}>1)(ssub=XOR D)
             50009 XOR C
            @ssub=|      ; Test @ssub replacing
            @ssub=|OR H  ; a later instruction
             50010 OR D
             50011 OR E
            @ssub=BEGIN: ; Test @ssub defining a label
             50012 OR A
            @ssub=>LD B,A ; Test @ssub inserting an instruction before
             50013 XOR A
            @ssub=+XOR C  ; Test @ssub inserting an instruction after
             50014 XOR B
             50015 XOR D
            @ssub=!50016-50018
             50016 RET NZ ; This should be removed

            @ssub+begin
            c50018 RET    ; Not removed by @ssub=!50016-50018 in previous entry
            @ssub+end
        """
        exp_data = [
            35,    # 50000 INC L
            19,    # 50001
            3,     # 50002
            201,   # 50003
            175,   # 50004 XOR A
            60,    # 50005
            62, 1, # 50006 LD A,1
            144,   # 50008 SUB B
            170,   # 50009 XOR D
            178,   # 50010 OR D
            180,   # 50011 OR H
            183,   # 50012 OR A
            71,    # 50013 LD B,A (inserted)
            175,   # 50014 XOR A
            168,   # 50015 XOR B
            169,   # 50016 XOR C (inserted)
            170,   # 50017 XOR D
            201    # 50018 RET
        ]
        self._test_write(skool, 50000, exp_data, asm_mode=2)

    def test_ssub_overrides_isub(self):
        skool = """
            @ssub=LD A,2
            @isub=LD A,1
            c30000 LD A,0
        """
        exp_data = [62, 2]
        self._test_write(skool, 30000, exp_data, asm_mode=2)

    def test_ofix_mode(self):
        skool = """
            @ofix-begin
            c60000 LD A,1
            @ofix+else
            c60000 LD A,2
            @ofix+end
            @bfix-begin
             60002 LD B,1
            @bfix+else
             60002 LD B,2
            @bfix+end
            @rfix-begin
             60004 LD C,1
            @rfix+else
             60004 LD C,2
            @rfix+end
            @bfix=!60006
            @ofix=LD D,2
             60006 LD D,1
            @bfix=LD E,2
             60008 LD E,1
            @rfix=LD H,2
             60010 LD H,1
            @ofix=LD L,2 ; Set L=2
             60012 LD L,1
            @ofix=|XOR A ; Test @ofix replacing
            @ofix=       ; one instruction with two.
            @ofix=|INC A
             60014 LD A,1
            @ofix=|LD A,1 ; Test @ofix replacing two instructions with one.
             60016 XOR A
             60017 INC A
            @ofix=       ; Test @ofix replacing the comment only.
             60018 SUB B
            @if({fix})(ofix=XOR D)
             60019 XOR C
            @ofix=|      ; Test @ofix replacing
            @ofix=|OR H  ; a later instruction
             60020 OR D
             60021 OR E
            @ofix=BEGIN: OR B ; Test @ofix defining a label
             60022 OR A
            @ofix=>LD B,A ; Test @ofix inserting an instruction before
             60023 XOR A
            @ofix=+XOR C  ; Test @ofix inserting an instruction after
             60024 XOR B
             60025 XOR D
            @ofix=!60026-60028
             60026 RET NZ ; This should be removed

            @ofix+begin
            c60028 RET    ; Not removed by @ofix=!60026-60028 in previous entry
            @ofix+end
        """
        exp_data = [
            62, 2, # 60000
            6, 1,  # 60002
            14, 1, # 60004
            22, 2, # 60006
            30, 1, # 60008
            38, 1, # 60010
            46, 2, # 60012
            175,   # 60014
            60,    # 60015
            62, 1, # 60016
            144,   # 60018
            170,   # 60019
            178,   # 60020
            180,   # 60021
            176,   # 60022
            71,    # 60023
            175,   # 60024
            168,   # 60025
            169,   # 60026
            170,   # 60027
            201    # 60028
        ]
        self._test_write(skool, 60000, exp_data, fix_mode=1)

    def test_bfix_mode(self):
        skool = """
            @ofix-begin
            c60000 LD A,1
            @ofix+else
            c60000 LD A,2
            @ofix+end
            @bfix-begin
             60002 LD B,1
            @bfix+else
             60002 LD B,2
            @bfix+end
            @rfix-begin
             60004 LD C,1
            @rfix+else
             60004 LD C,2
            @rfix+end
            @ofix=LD D,2
             60006 LD D,1
            @bfix=LD E,2
             60008 LD E,1
            @rfix=LD H,2
             60010 LD H,1
            @bfix=LD L,2 ; Set L=2
             60012 LD L,1
            @bfix=|XOR A   ; Test @bfix replacing one instruction with two.
            @bfix=|JR 60000
             60014 JP 60000
            @bfix=|LD A,1 ; Test @bfix replacing two instructions with one.
             60017 XOR A
             60018 INC A
            @bfix=       ; Test @bfix replacing the comment only.
             60019 SUB B
            @if({fix}>1)(bfix=XOR D)
             60020 XOR C
            @bfix=|      ; Test @bfix replacing
            @bfix=|OR H  ; a later instruction
             60021 OR D
             60022 OR E
            @bfix=BEGIN: ; Test @bfix defining a label
             60023 OR A
            @bfix=>LD B,A ; Test @bfix inserting an instruction before
             60024 XOR A
            @bfix=+XOR C  ; Test @bfix inserting an instruction after
             60025 XOR B
             60026 XOR D
            @bfix=!60027-60029
             60027 RET NZ ; This should be removed

            @bfix+begin
            c60029 RET    ; Not removed by @bfix=!60027-60029 in previous entry
            @bfix+end
        """
        exp_data = [
            62, 2,   # 60000 LD A,2
            6, 2,    # 60002 LD B,2
            14, 1,   # 60004 LD C,1
            22, 2,   # 60006 LD D,2
            30, 2,   # 60008 LD E,2
            38, 1,   # 60010 LD H,1
            46, 2,   # 60012 LD L,2
            175,     # 60014 XOR A
            24, 239, # 60015 JR 60000
            62, 1,   # 60017 LD A,1
            144,     # 60019 SUB B
            170,     # 60020 XOR D
            178,     # 60021 OR D
            180,     # 60022 OR H
            183,     # 60023 OR A
            71,      # 60024 LD B,A (inserted)
            175,     # 60025 XOR A
            168,     # 60026 XOR B
            169,     # 60027 XOR C (inserted)
            170,     # 60028 XOR D
            201      # 60029 RET
        ]
        self._test_write(skool, 60000, exp_data, fix_mode=2)

    def test_bfix_overrides_ofix(self):
        skool = """
            @bfix=LD B,2
            @ofix=LD B,1
            c30000 LD B,0
        """
        exp_data = [6, 2]
        self._test_write(skool, 30000, exp_data, fix_mode=2)

    def test_bfix_block_directive_spanning_two_entries_fix_mode_0(self):
        skool = """
            ; Data
            b32768 DEFB 1
            @bfix-begin
             32769 DEFB 2

            ; Unused
            u32770 DEFB 3
            @bfix+else
             32769 DEFB 4
             32770 DEFB 8
            @bfix+end
        """
        exp_data = [1, 2, 3]
        self._test_write(skool, 32768, exp_data)

    def test_bfix_block_directive_spanning_two_entries_fix_mode_2(self):
        skool = """
            ; Data
            b32768 DEFB 1
            @bfix-begin
             32769 DEFB 2

            ; Unused
            u32770 DEFB 3
            @bfix+else
             32769 DEFB 4
             32770 DEFB 8
            @bfix+end
        """
        exp_data = [1, 4, 8]
        self._test_write(skool, 32768, exp_data, fix_mode=2)

    def test_if_directive_ignored_if_invalid(self):
        skool = """
            @if(x)(bfix=DEFB 2)
            b32768 DEFB 1
        """
        exp_data = [1]
        self._test_write(skool, 32768, exp_data, fix_mode=2)

    def test_header_is_ignored(self):
        skool = """
            ; The following instruction-like line should be ignored.
             32768 LD B,1

            ; Data
            b32770 DEFB 1,2
        """
        exp_data = [1, 2]
        self._test_write(skool, 32770, exp_data)

    def test_footer_is_ignored(self):
        skool = """
            ; Data
            b32768 DEFB 1,2

            ; The following instruction-like line should be ignored.
             32770 LD B,1
        """
        exp_data = [1, 2]
        self._test_write(skool, 32768, exp_data)
