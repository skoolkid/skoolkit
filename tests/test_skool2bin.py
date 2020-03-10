from textwrap import dedent
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError, VERSION, components, skool2bin

class MockBinWriter:
    def __init__(self, skoolfile, asm_mode, fix_mode, start, end, data, verbose, warn):
        global mock_bin_writer
        mock_bin_writer = self
        self.skoolfile = skoolfile
        self.asm_mode = asm_mode
        self.fix_mode = fix_mode
        self.start = start
        self.end = end
        self.data = data
        self.verbose = verbose
        self.warn = warn
        self.binfile = None

    def write(self, binfile):
        self.binfile = binfile

class Skool2BinTest(SkoolKitTestCase):
    def _check_values(self, skoolfile, binfile, asm_mode=0, fix_mode=0, data=False, verbose=False, warn=True, start=-1, end=65537):
        self.assertEqual(mock_bin_writer.skoolfile, skoolfile)
        self.assertEqual(mock_bin_writer.binfile, binfile)
        self.assertEqual(mock_bin_writer.asm_mode, asm_mode)
        self.assertEqual(mock_bin_writer.fix_mode, fix_mode)
        self.assertIs(mock_bin_writer.data, data)
        self.assertIs(mock_bin_writer.verbose, verbose)
        self.assertIs(mock_bin_writer.warn, warn)
        self.assertEqual(mock_bin_writer.start, start)
        self.assertEqual(mock_bin_writer.end, end)

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
        self._check_values(skoolfile, exp_binfile)

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
            self._check_values(skoolfile, exp_binfile, fix_mode=2)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_d(self):
        skoolfile = 'test-d.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option in ('-d', '--data'):
            output, error = self.run_skool2bin('{} {}'.format(option, skoolfile))
            self.assertEqual(len(error), 0)
            self._check_values(skoolfile, exp_binfile, data=True)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_E(self):
        skoolfile = 'test-E.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option, value in (('-E', 32768), ('--end', 49152)):
            output, error = self.run_skool2bin('{} {} {}'.format(option, value, skoolfile))
            self.assertEqual(len(error), 0)
            self._check_values(skoolfile, exp_binfile, end=value)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_E_with_hex_address(self):
        skoolfile = 'test-E-hex.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option, value in (('-E', '0x7ff0'), ('--end', '0xA1B5')):
            output, error = self.run_skool2bin('{} {} {}'.format(option, value, skoolfile))
            self.assertEqual(len(error), 0)
            self._check_values(skoolfile, exp_binfile, end=int(value[2:], 16))

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_i(self):
        skoolfile = 'test-i.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option in ('-i', '--isub'):
            output, error = self.run_skool2bin('{} {}'.format(option, skoolfile))
            self.assertEqual(len(error), 0)
            self._check_values(skoolfile, exp_binfile, asm_mode=1)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_o(self):
        skoolfile = 'test-o.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option in ('-o', '--ofix'):
            output, error = self.run_skool2bin('{} {}'.format(option, skoolfile))
            self.assertEqual(len(error), 0)
            self._check_values(skoolfile, exp_binfile, fix_mode=1)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_r(self):
        skoolfile = 'test-r.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option in ('-r', '--rsub'):
            output, error = self.run_skool2bin('{} {}'.format(option, skoolfile))
            self.assertEqual(len(error), 0)
            self._check_values(skoolfile, exp_binfile, asm_mode=3)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_R(self):
        skoolfile = 'test-R.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option in ('-R', '--rfix'):
            output, error = self.run_skool2bin('{} {}'.format(option, skoolfile))
            self.assertEqual(len(error), 0)
            self._check_values(skoolfile, exp_binfile, fix_mode=3)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_s(self):
        skoolfile = 'test-s.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option in ('-s', '--ssub'):
            output, error = self.run_skool2bin('{} {}'.format(option, skoolfile))
            self.assertEqual(len(error), 0)
            self._check_values(skoolfile, exp_binfile, asm_mode=2)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_S(self):
        skoolfile = 'test-S.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option, value in (('-S', 24576), ('--start', 32768)):
            output, error = self.run_skool2bin('{} {} {}'.format(option, value, skoolfile))
            self.assertEqual(len(error), 0)
            self._check_values(skoolfile, exp_binfile, start=value)

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_S_with_hex_address(self):
        skoolfile = 'test-S-hex.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option, value in (('-S', '0x7abc'), ('--start', '0xFA0A')):
            output, error = self.run_skool2bin('{} {} {}'.format(option, value, skoolfile))
            self.assertEqual(len(error), 0)
            self._check_values(skoolfile, exp_binfile, start=int(value[2:], 16))

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_v(self):
        skoolfile = 'test-v.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option in ('-v', '--verbose'):
            output, error = self.run_skool2bin('{} {}'.format(option, skoolfile))
            self.assertEqual(len(error), 0)
            self._check_values(skoolfile, exp_binfile, verbose=True)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_skool2bin(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))

    @patch.object(skool2bin, 'BinWriter', MockBinWriter)
    def test_option_w(self):
        skoolfile = 'test-w.skool'
        exp_binfile = skoolfile[:-6] + '.bin'
        for option in ('-w', '--no-warnings'):
            output, error = self.run_skool2bin('{} {}'.format(option, skoolfile))
            self.assertEqual(len(error), 0)
            self._check_values(skoolfile, exp_binfile, warn=False)

class BinWriterTestCase(SkoolKitTestCase):
    def _test_write(self, skool, base_address, exp_data, *modes, data=False, start=-1, end=65537, warn=True, exp_output='', exp_warnings=''):
        if skool is None:
            skoolfile = '-'
            binfile = self.write_bin_file(suffix='.bin')
        else:
            skoolfile = self.write_text_file(dedent(skool).strip(), suffix='.skool')
            binfile = skoolfile[:-6] + '.bin'
            self.tempfiles.append(binfile)
        asm_mode = fix_mode = 0
        for mode in modes:
            if mode.endswith('sub'):
                asm_mode = {'isub': 1, 'ssub': 2, 'rsub': 3}[mode]
            elif mode.endswith('fix'):
                fix_mode = {'ofix': 1, 'bfix': 2, 'rfix': 3}[mode]
        bin_writer = skool2bin.BinWriter(skoolfile, asm_mode, fix_mode, start, end, data, bool(exp_output), warn)
        bin_writer.write(binfile)
        with open(binfile, 'rb') as f:
            bdata = list(f.read())
        self.assertEqual(exp_data, bdata)
        size = len(bdata)
        status = "Wrote {}: start={}, end={}, size={}\n".format(binfile, base_address, base_address + size, size)
        if exp_output:
            exp_output = dedent(exp_output).strip() + '\n' + status
        elif exp_warnings:
            exp_output = dedent(exp_warnings).strip() + '\n' + status
        else:
            exp_output = status
        self.assertEqual(exp_output, self.err.getvalue())
        self.err.clear()

class BinWriterTest(BinWriterTestCase):
    stdout_binary = True

    def test_nonexistent_skool_file(self):
        skoolfile = '{}/nonexistent.skool'.format(self.make_directory())
        with self.assertRaises(SkoolKitError) as cm:
            self.run_skool2bin(skoolfile)
        self.assertEqual(cm.exception.args[0], '{}: file not found'.format(skoolfile))

    def test_first_instruction_address_invalid(self):
        skoolfile = self.write_text_file('c4000d RET', suffix='.skool')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_skool2bin(skoolfile)
        self.assertEqual(cm.exception.args[0], 'Invalid address (4000d):\nc4000d RET')

    def test_second_instruction_address_invalid(self):
        skoolfile = self.write_text_file('c40000 XOR A\n 4000x RET', suffix='.skool')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_skool2bin(skoolfile)
        self.assertEqual(cm.exception.args[0], 'Invalid address (4000x):\n 4000x RET')

    def test_invalid_instruction(self):
        skoolfile = self.write_text_file('c40000 XOR HL', suffix='.skool')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_skool2bin(skoolfile)
        self.assertEqual(cm.exception.args[0], 'Failed to assemble:\n 40000 XOR HL')

    def test_skool_file_from_stdin(self):
        self.write_stdin('c49152 RET')
        self._test_write(None, 49152, [201])

    def test_output_file_is_written_to_current_directory_by_default(self):
        binfile = self.write_bin_file(suffix='.bin')
        skoolfile = self.write_text_file('t30000 DEFM "abc"', '{}/{}.skool'.format(self.make_directory(), binfile[:-4]))
        output, error = self.run_skool2bin(skoolfile)
        self.assertEqual(output, b'')
        self.assertEqual(error, "Wrote {}: start=30000, end=30003, size=3\n".format(binfile))
        with open(binfile) as f:
            self.assertEqual(f.read(), 'abc')

    def test_binary_file_to_stdout(self):
        skoolfile = self.write_text_file('t30000 DEFM "abc"', suffix='.skool')
        bin_writer = skool2bin.BinWriter(skoolfile)
        bin_writer.write('-')
        self.assertEqual(self.out.getvalue(), b'abc')
        self.assertEqual(self.err.getvalue(), "Wrote stdout: start=30000, end=30003, size=3\n")

    def test_blank_i_block(self):
        skool = """
            b30000 DEFB 1

            i30001

            @org
            b30002 DEFB 2
        """
        self._test_write(skool, 30000, [1, 0, 2])

    def test_i_block(self):
        skool = """
            i29999 DEFB 128

            c30000 RET
        """
        self._test_write(skool, 29999, [128, 201])

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

    def test_start_address_before_first_instruction(self):
        skool = "c32768 RET"
        self._test_write(skool, 32768, [201], start=32767)

    def test_end_address_after_last_instruction(self):
        skool = "c32768 RET"
        self._test_write(skool, 32768, [201], end=32770)

    def test_start_address_after_last_instruction(self):
        skool = "c32768 RET"
        self._test_write(skool, 0, [], start=32769)

    def test_end_address_before_first_instruction(self):
        skool = "c32768 RET"
        self._test_write(skool, 0, [], end=32767)

    def test_start_address_after_end_address(self):
        skool = "c32768 RET"
        self._test_write(skool, 0, [], start=32769, end=32767)

    def test_overlapping_instructions(self):
        skool = """
            b30000 DEFS 3,1
             30002 XOR A    ; The address of this instruction is ignored
        """
        exp_data = [1, 1, 1, 175]
        self._test_write(skool, 30000, exp_data)

    def test_data_directives_ignored(self):
        skool = """
            @defb=30001:1
            @defs=30002:2,2
            @defw=30004:771
            b30000 DEFB 0
        """
        exp_data = [0]
        self._test_write(skool, 30000, exp_data, data=False)

    def test_data_directives_processed(self):
        skool = """
            @defb=30001:1
            @defs=30002:2,2
            @defw=30004:771
            b30000 DEFB 0
        """
        exp_data = [0, 1, 2, 2, 3, 3]
        self._test_write(skool, 30000, exp_data, data=True)

    def test_data_directive_does_not_overwrite_next_instruction(self):
        skool = """
            @defb=0
            c30000 XOR A
        """
        exp_data = [175]
        self._test_write(skool, 30000, exp_data, data=True)

    def test_data_directive_overwriting_previous_instruction(self):
        skool = """
            c30000 XOR A
            @defb=30000:0
             30001 XOR B
        """
        exp_data = [0, 168]
        self._test_write(skool, 30000, exp_data, data=True)

    def test_data_directive_overriding_previous_one(self):
        skool = """
            @defb=3,3,3
            b30000 DEFB 1
            @defb=4,4
             30001 DEFB 2
        """
        exp_data = [1, 2, 4]
        self._test_write(skool, 30000, exp_data, data=True)

    def test_data_directives_do_not_override_start_and_end_addresses(self):
        skool = """
            @defb=29999:1,1
            @defs=2,2
            @defw=771
            b30000 DEFB 0
        """
        exp_data = [0, 2]
        self._test_write(skool, 30000, exp_data, data=True, start=30000, end=30002)

    def test_if_directive_ignored_if_invalid(self):
        skool = """
            @if(x)(defb=2)
            b32768 DEFB 1
        """
        exp_data = [1]
        self._test_write(skool, 32768, exp_data, data=True)

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

    def test_verbose(self):
        skool = """
            ; Routine
            c30000 LD A,B
             30001 XOR C
             30002 ADD A,D
             30003 RET
        """
        exp_data = [120, 169, 130, 201]
        exp_output = """
            30000 7530   LD A,B
            30001 7531   XOR C
            30002 7532   ADD A,D
            30003 7533   RET
        """
        self._test_write(skool, 30000, exp_data, exp_output=exp_output)

    def test_verbose_with_addresses_below_10(self):
        skool = """
            c00000 LD A,B
             00001 RET
        """
        exp_data = [120, 201]
        exp_output = """
            00000 0000   LD A,B
            00001 0001   RET
        """
        self._test_write(skool, 0, exp_data, exp_output=exp_output)

    def test_verbose_shows_subbed_instructions(self):
        skool = """
            @ssub=LD A,C
            c40000 LD A,B
            @ssub=XOR D
             40001 XOR C
             40002 RET
        """
        exp_data = [121, 170, 201]
        exp_output = """
            40000 9C40   LD A,C
            40001 9C41   XOR D
            40002 9C42   RET
        """
        self._test_write(skool, 40000, exp_data, 'ssub', exp_output=exp_output)

    def test_verbose_shows_inserted_instructions(self):
        skool = """
            @rsub=>XOR A
            @rsub=LD B,A
            c40000 LD B,0
            @rsub=+RET
             40002 XOR C
        """
        exp_data = [175, 71, 169, 201]
        exp_output = """
            40000 9C40 > XOR A
            40001 9C41   LD B,A        : 40000 9C40 LD B,A
            40002 9C42   XOR C
            40003 9C43 + RET
        """
        self._test_write(skool, 40000, exp_data, 'rsub', exp_output=exp_output)

    def test_verbose_shows_one_instruction_replacing_two(self):
        skool = """
            @ssub=|LD A,1
            c60000 XOR A
             60001 INC A
             60002 RET
        """
        exp_data = [62, 1, 201]
        exp_output = """
            60000 EA60 | LD A,1
            60002 EA62   RET
        """
        self._test_write(skool, 60000, exp_data, 'ssub', exp_output=exp_output)

    def test_verbose_shows_two_instructions_replacing_one(self):
        skool = """
            @ssub=|XOR A
            @ssub=|INC A
            c60000 LD A,1
             60002 RET
        """
        exp_data = [175, 60, 201]
        exp_output = """
            60000 EA60 | XOR A
            60001 EA61 | INC A
            60002 EA62   RET
        """
        self._test_write(skool, 60000, exp_data, 'ssub', exp_output=exp_output)

    def test_verbose_omits_removed_instruction(self):
        skool = """
            @rsub=!40001
            c40000 XOR A
             40001 RET
        """
        exp_data = [175]
        exp_output = """
            40000 9C40   XOR A
        """
        self._test_write(skool, 40000, exp_data, 'rsub', exp_output=exp_output)

    def test_verbose_shows_original_address_of_moved_instructions(self):
        skool = """
            @rsub=LD A,0
            c40000 LD A,B
            @rsub=XOR 25
             40001 XOR C
             40002 RET
        """
        exp_data = [62, 0, 238, 25, 201]
        exp_output = """
            40000 9C40   LD A,0
            40002 9C42   XOR 25        : 40001 9C41 XOR 25
            40004 9C44   RET           : 40002 9C42 RET
        """
        self._test_write(skool, 40000, exp_data, 'rsub', exp_output=exp_output)

    def test_verbose_shows_original_value_of_adjusted_operands(self):
        skool = """
            c50000 CALL 50005
            @rsub=LD A,0
             50003 XOR A
             50004 RET

            @nowarn
            c50005 LD HL,(50004)
        """
        exp_data = [205, 86, 195, 62, 0, 201, 42, 85, 195]
        exp_output = """
            50000 C350   CALL 50006    : 50000 C350 CALL 50005
            50003 C353   LD A,0
            50005 C355   RET           : 50004 C354 RET
            50006 C356   LD HL,(50005) : 50005 C355 LD HL,(50004)
        """
        self._test_write(skool, 50000, exp_data, 'rsub', exp_output=exp_output)

    def test_verbose_shows_original_value_of_adjusted_operand_for_inserted_instruction(self):
        skool = """
            @rsub=+JR 50001
            c50000 XOR A
             50001 RET
        """
        exp_data = [175, 24, 0, 201]
        exp_output = """
            50000 C350   XOR A
            50001 C351 + JR 50003      :            JR 50001
            50003 C353   RET           : 50001 C351 RET
        """
        self._test_write(skool, 50000, exp_data, 'rsub', exp_output=exp_output)

    def test_verbose_shows_instructions_inserted_by_block_directive(self):
        skool = """
            c60000 XOR A
            @rsub+begin
                   INC A
                   SUB B
            @rsub+end
             60001 RET
        """
        exp_data = [175, 60, 144, 201]
        exp_output = """
            60000 EA60   XOR A
            60001 EA61   INC A
            60002 EA62   SUB B
            60003 EA63   RET           : 60001 EA61 RET
        """
        self._test_write(skool, 60000, exp_data, 'rsub', exp_output=exp_output)

    def test_verbose_omits_instructions_outside_disassembly_range(self):
        skool = """
            c40000 XOR A
             40001 INC A
             40002 DEC A
             40003 RET
        """
        exp_data = [60, 61]
        exp_output = """
            40001 9C41   INC A
            40002 9C42   DEC A
        """
        self._test_write(skool, 40001, exp_data, start=40001, end=40003, exp_output=exp_output)

    def test_verbose_omits_relocated_instructions_outside_disassembly_range(self):
        skool = """
            c40000 XOR A
            @rsub=!40001
             40001 XOR B
             40002 XOR C ; Moved to 40001
            @rsub=>XOR 1 ; Inserted at 40002
             40003 RET   ; Moved to 40004
        """
        exp_data = [169, 238, 1]
        exp_output = """
            40001 9C41   XOR C         : 40002 9C42 XOR C
            40002 9C42 > XOR 1
        """
        self._test_write(skool, 40001, exp_data, 'rsub', start=40001, end=40004, exp_output=exp_output)

    def test_verbose_showing_defb_defs_defw_directives(self):
        skool = """
            @defb=50000:1
            @defs=2,2
            @defw=3
            b50005 DEFB 255
        """
        exp_data = [1, 2, 2, 3, 0, 255]
        exp_output = """
            50000 C350   @defb=50000:1
            50001 C351   @defs=2,2
            50003 C353   @defw=3
            50005 C355   DEFB 255
        """
        self._test_write(skool, 50000, exp_data, data=True, exp_output=exp_output)

    @patch.object(components, 'SK_CONFIG', None)
    def test_custom_assembler(self):
        custom_assembler = """
            def assemble(operation, address):
                return (1, 1)
            def get_size(operation, address):
                return 2
        """
        self.write_component_config('Assembler', '*', custom_assembler)
        skool = "b60000 RET"
        exp_data = [1, 1]
        self._test_write(skool, 60000, exp_data)

    @patch.object(components, 'SK_CONFIG', None)
    def test_custom_address_adjuster(self):
        custom_adjuster = """
            from skoolkit.skoolparser import InstructionUtility
            class CustomUtility(InstructionUtility):
                def substitute_labels(self, entries, remote_entries, labels, mode, warn):
                    entries[0].instructions[0].operation = 'JP 50001'
        """
        self.write_component_config('InstructionUtility', '*.CustomUtility', custom_adjuster)
        skool = "c50000 JP 50000"
        exp_data = [195, 81, 195]
        self._test_write(skool, 50000, exp_data)

    @patch.object(components, 'SK_CONFIG', None)
    def test_custom_address_adjuster_with_warning_for_inserted_instruction(self):
        custom_adjuster = """
            from skoolkit.skoolparser import InstructionUtility
            class CustomUtility(InstructionUtility):
                def substitute_labels(self, entries, remote_entries, labels, mode, warn):
                    warn('Generic warning', entries[0].instructions[1])
        """
        self.write_component_config('InstructionUtility', '*.CustomUtility', custom_adjuster)
        skool = """
            @rsub=+RET
            c50000 XOR A
        """
        exp_data = [175, 201]
        exp_warnings = """
            WARNING: Generic warning:
              50001 C351 + RET
        """
        self._test_write(skool, 50000, exp_data, 'rsub', exp_warnings=exp_warnings)

class DirectiveTestCase:
    def test_mode_applies_directives(self):
        skool = """
            @{0}=XOR A
            c30000 XOR B
            @{0}-begin
             30001 XOR C
            @{0}+else
             30001 XOR D
            @{0}+end
        """
        exp_data = [175, 170]
        for d in self.applies:
            with self.subTest(directive=d):
                self._test_write(skool.format(d), 30000, exp_data, self.mode)

    def test_directive_overrides_other_directives(self):
        skool = """
            @{}=LD A,2
            @{}=LD A,1
            c30000 LD A,0
        """
        exp_data = [62, 2]
        for d in self.overrides:
            with self.subTest(directive=d):
                self._test_write(skool.format(self.mode, d), 30000, exp_data, self.mode)

    def test_mode_ignores_other_directives(self):
        skool = """
            @{0}=XOR A
            c30000 XOR B
            @{0}-begin
             30001 XOR C
            @{0}+else
             30001 XOR D
            @{0}+end
        """
        exp_data = [168, 169]
        ignores = {'isub', 'ssub', 'rsub', 'ofix', 'bfix', 'rfix'} - set(self.applies)
        for d in ignores:
            with self.subTest(directive=d):
                self._test_write(skool.format(d), 30000, exp_data, self.mode)

    def test_mode_combined_with_other_modes(self):
        skool = """
            @{}=XOR A
            c30000 XOR B
            @{}=XOR C
             30001 XOR D
        """
        exp_data = [175, 169]
        if self.mode.endswith('sub'):
            other_modes = ('ofix', 'bfix', 'rfix')
        else:
            other_modes = ('isub', 'ssub', 'rsub')
        for m in other_modes:
            with self.subTest(directive=m):
                self._test_write(skool.format(self.mode, m), 30000, exp_data, self.mode, m)

    def test_mode_adjusts_call_operands(self):
        skool = """
            c30000 CALL 30016
             30003 CALL NZ,30016
             30006 CALL Z,30016
             30009 CALL NC,30016
             30012 CALL C,30016
            @{0}=LD A,0
             30015 XOR A
             30016 RET ; This instruction is moved to 30017

            @org
            c30020 CALL PO,30034
             30023 CALL PE,30034
             30026 CALL P,30034
             30029 CALL M,30034
            @{0}=XOR A
             30032 LD A,0
             30034 RET ; This instruction is moved to 30033
        """.format(self.mode)
        exp_data = [
            205, 65, 117, # 30000 CALL 30017
            196, 65, 117, # 30003 CALL NZ,30017
            204, 65, 117, # 30006 CALL Z,30017
            212, 65, 117, # 30009 CALL NC,30017
            220, 65, 117, # 30012 CALL C,30017
            62, 0,        # 30015 LD A,0
            201,          # 30017 RET
            0, 0,
            228, 81, 117, # 30020 CALL PO,30033
            236, 81, 117, # 30023 CALL PE,30033
            244, 81, 117, # 30026 CALL P,30033
            252, 81, 117, # 30029 CALL M,30033
            175,          # 30032 XOR A
            201,          # 30033 RET
        ]
        self._test_write(skool, 30000, exp_data, self.mode)

    def test_mode_adjusts_defb_operands(self):
        skool = """
            @{0}=LD A,0
            c30000 XOR A
             30001 INC A      ; This instruction is moved to 30002
            @{0}=LD B,A
             30002 LD BC,0
             30005 RET        ; This instruction is moved to 30004

            @org
            b30006 DEFB 30001%256
             30007 DEFB 30005%256
             30008 DEFB "30001"
        """.format(self.mode)
        exp_data = [
            62, 0,             # 30000 LD A,0
            60,                # 30002 INC A
            71,                # 30003 LD B,A
            201,               # 30004 RET
            0,
            50,                # 30006 DEFB 30002%256
            52,                # 30007 DEFB 30004%256
            51, 48, 48, 48, 49 # 30008 DEFB "30001"
        ]
        self._test_write(skool, 30000, exp_data, self.mode)

    def test_mode_adjusts_defm_operands(self):
        skool = """
            @{0}=LD A,0
            c30000 XOR A
             30001 INC A      ; This instruction is moved to 30002
            @{0}=LD B,A
             30002 LD BC,0
             30005 RET        ; This instruction is moved to 30004

            @org
            b30006 DEFM 30001%256
             30007 DEFM 30005%256
             30008 DEFM "30005"
        """.format(self.mode)
        exp_data = [
            62, 0,             # 30000 LD A,0
            60,                # 30002 INC A
            71,                # 30003 LD B,A
            201,               # 30004 RET
            0,
            50,                # 30006 DEFM 30002%256
            52,                # 30007 DEFM 30004%256
            51, 48, 48, 48, 53 # 30008 DEFM "30005"
        ]
        self._test_write(skool, 30000, exp_data, self.mode)

    def test_mode_adjusts_defw_operands(self):
        skool = """
            @{0}=LD A,0
            c30000 XOR A
             30001 INC A      ; This instruction is moved to 30002
            @{0}=LD B,A
             30002 LD BC,0
             30005 RET        ; This instruction is moved to 30004

            @org
            b30006 DEFW 30001
             30008 DEFW 30005
        """.format(self.mode)
        exp_data = [
            62, 0,   # 30000 LD A,0
            60,      # 30002 INC A
            71,      # 30003 LD B,A
            201,     # 30004 RET
            0,
            50, 117, # 30006 DEFW 30002
            52, 117  # 30008 DEFW 30004
        ]
        self._test_write(skool, 30000, exp_data, self.mode)

    def test_mode_adjusts_djnz_operands(self):
        skool = """
            @{0}=LD A,0
            c30000 XOR A
             30001 INC A      ; This instruction is moved to 30002
             30002 DJNZ 30001
             30004 RET

            @org
            @{0}=XOR A
            c30006 LD A,0
             30008 INC A      ; This instruction is moved to 30007
             30009 DJNZ 30008
             30011 RET
        """.format(self.mode)
        exp_data = [62, 0, 60, 16, 253, 201, 175, 60, 16, 253, 201]
        self._test_write(skool, 30000, exp_data, self.mode)

    def test_mode_adjusts_jp_operands(self):
        skool = """
            c30000 JP 30016
             30003 JP NZ,30016
             30006 JP Z,30016
             30009 JP NC,30016
             30012 JP C,30016
            @{0}=LD A,0
             30015 XOR A
             30016 RET ; This instruction is moved to 30017

            @org
            c30020 JP PO,30034
             30023 JP PE,30034
             30026 JP P,30034
             30029 JP M,30034
            @{0}=XOR A
             30032 LD A,0
             30034 RET ; This instruction is moved to 30033
        """.format(self.mode)
        exp_data = [
            195, 65, 117, # 30000 JP 30017
            194, 65, 117, # 30003 JP NZ,30017
            202, 65, 117, # 30006 JP Z,30017
            210, 65, 117, # 30009 JP NC,30017
            218, 65, 117, # 30012 JP C,30017
            62, 0,        # 30015 LD A,0
            201,          # 30017 RET
            0, 0,
            226, 81, 117, # 30020 JP PO,30033
            234, 81, 117, # 30023 JP PE,30033
            242, 81, 117, # 30026 JP P,30033
            250, 81, 117, # 30029 JP M,30033
            175,          # 30032 XOR A
            201,          # 30033 RET
        ]
        self._test_write(skool, 30000, exp_data, self.mode)

    def test_mode_adjusts_jr_operands(self):
        skool = """
            c30000 JR 30007
             30002 JR Z,30007
             30004 JR NZ,30007
            @{0}=LD A,0
             30006 XOR A
             30007 RET ; This instruction is moved to 30008

            @org
            c30010 JR C,30016
             30012 JR NC,30016
            @{0}=XOR A
             30014 LD A,0
             30016 RET ; This instruction is moved to 30015
        """.format(self.mode)
        exp_data = [
            24, 6, # 30000 JR 30008
            40, 4, # 30002 JR Z,30008
            32, 2, # 30004 JR NZ,30008
            62, 0, # 30006 LD A,0
            201,   # 30008 RET
            0,
            56, 3, # 30010 JR C,30015
            48, 1, # 30012 JR NC,30015
            175,   # 30014 XOR A
            201    # 30015 RET
        ]
        self._test_write(skool, 30000, exp_data, self.mode)

    def test_mode_adjusts_ld_operands(self):
        skool = """
            c30000 LD BC,30021
             30003 LD DE,30021
             30006 LD HL,30021
             30009 LD SP,30021
             30012 LD IX,30021
             30016 LD IY,30021
            @{0}=LD A,0
             30020 XOR A
             30021 RET ; This instruction is moved to 30022

            @org
            c30023 LD BC,(30048)
             30027 LD DE,(30048)
             30031 LD HL,(30048)
             30034 LD SP,(30048)
             30038 LD IX,(30048)
             30042 LD IY,(30048)
            @{0}=XOR A
             30046 LD A,0
             30048 RET ; This instruction is moved to 30047

            @org
            c30049 LD (30073),BC
             30053 LD (30073),DE
             30057 LD (30073),HL
             30060 LD (30073),SP
             30064 LD (30073),IX
             30068 LD (30073),IY
            @{0}=LD A,0
             30072 XOR A
             30073 RET ; This instruction is moved to 30074
        """.format(self.mode)
        exp_data = [
            1, 70, 117,         # 30000 LD BC,30022
            17, 70, 117,        # 30003 LD DE,30022
            33, 70, 117,        # 30006 LD HL,30022
            49, 70, 117,        # 30009 LD SP,30022
            221, 33, 70, 117,   # 30012 LD IX,30022
            253, 33, 70, 117,   # 30016 LD IY,30022
            62, 0,              # 30020 LD A,0
            201,                # 30022 RET
            237, 75, 95, 117,   # 30023 LD BC,(30047)
            237, 91, 95, 117,   # 30027 LD DE,(30047)
            42, 95, 117,        # 30031 LD HL,(30047)
            237, 123, 95, 117,  # 30034 LD SP,(30047)
            221, 42, 95, 117,   # 30038 LD IX,(30047)
            253, 42, 95, 117,   # 30042 LD IY,(30047)
            175,                # 30046 XOR A
            201,                # 30047 RET
            0,
            237, 67, 122, 117,  # 30049 LD (30074),BC
            237, 83, 122, 117,  # 30053 LD (30074),DE
            34, 122, 117,       # 30057 LD (30074),HL
            237, 115, 122, 117, # 30060 LD (30074),SP
            221, 34, 122, 117,  # 30064 LD (30074),IX
            253, 34, 122, 117,  # 30068 LD (30074),IY
            62, 0,              # 30072 LD A,0
            201,                # 30074 RET
        ]
        self._test_write(skool, 30000, exp_data, self.mode, warn=False)

    def test_mode_preserves_original_address_mapping(self):
        skool = """
            c30000 JP 30003 ; This address operand should be left alone

            @{0}+begin
            ; This is the routine at 30003
            c30003 XOR A    ; Address 30003 maps to 30003 (i.e. no change);
             30004 RET      ; this mapping should be preserved.
            @{0}+end

            @{0}=!30003
            ; The stated address of this routine (30003) should not be mapped
            ; to the actual address it would have if not removed (30005),
            ; because a mapping for address 30003 already exists.
            c30003 RET
        """.format(self.mode)
        exp_data = [195, 51, 117, 175, 201]
        self._test_write(skool, 30000, exp_data, self.mode)

    def test_mode_processes_org_directives(self):
        skool = """
            @{0}=LD A,1
            c50000 LD A,0

            @org
            @{0}=LD A,2
            c50005 LD A,1 ; This instruction should be at 50005

            @if(1>0)(org=50010)
            @{0}=LD A,3
            c50010 LD A,2 ; This instruction should be at 50010
        """.format(self.mode)
        exp_data = [62, 1, 0, 0, 0, 62, 2, 0, 0, 0, 62, 3]
        self._test_write(skool, 50000, exp_data, self.mode)

    def test_mode_processes_keep_directives(self):
        skool = """
            @{}=XOR A
            c50000 LD A,0
            @keep
             50002 LD HL,50005           ; This instruction is moved to 50001
            @keep=50002
            @nowarn
             50005 LD HL,50002%256+50008 ; This instruction is moved to 50004
             50008 RET                   ; This instruction is moved to 50007
        """.format(self.mode)
        exp_data = [
            175,          # 50000 XOR A
            33, 85, 195,  # 50001 LD HL,50005
            33, 169, 195, # 50004 LD HL,50002%256+50007
            201           # 50007 RET
        ]
        self._test_write(skool, 50000, exp_data, self.mode)

    def test_mode_processes_nowarn_directives(self):
        skool = """
            @nowarn
            c50000 LD HL,50001 ; Unreplaced address (50001), suppressed
            @nowarn=50009
             50003 LD DE,50009 ; Address 50009 replaced with 50010, suppressed
            @nowarn=50000
             50006 LD BC,50001 ; Unreplaced address (50001)
            @{}=>XOR A
             50009 RET
        """.format(self.mode)
        exp_data = [33, 81, 195, 17, 90, 195, 1, 81, 195, 175, 201]
        if self.mode in ('ssub', 'rsub', 'rfix'):
            exp_warnings = """
                WARNING: Unreplaced address (50001):
                  50006 C356   LD BC,50001
            """
        else:
            exp_warnings = ''
        self._test_write(skool, 50000, exp_data, self.mode, exp_warnings=exp_warnings)

    def test_warnings(self):
        skool = """
            c50000 LD HL,50001 ; Unreplaced address (50001)
             50003 LD DE,50006 ; Address 50006 replaced with 50007
            @{}=>XOR A
             50006 RET
        """.format(self.mode)
        exp_data = [33, 81, 195, 17, 87, 195, 175, 201]
        if self.mode in ('ssub', 'rsub', 'rfix'):
            exp_warnings = """
                WARNING: Unreplaced address (50001):
                  50000 C350   LD HL,50001
                WARNING: Address 50006 replaced with 50007 in unsubbed LD operation:
                  50003 C353   LD DE,50006
            """
        else:
            exp_warnings = """
                WARNING: Address 50006 replaced with 50007 in unsubbed LD operation:
                  50003 C353   LD DE,50006
            """
        self._test_write(skool, 50000, exp_data, self.mode, exp_warnings=exp_warnings)

    def test_warnings_for_relocated_instructions(self):
        skool = """
            @{}=>XOR A
            c50000 LD HL,50001 ; Unreplaced address (50001)
             50003 LD DE,50006 ; Address 50006 replaced with 50007
             50006 RET
        """.format(self.mode)
        exp_data = [175, 33, 81, 195, 17, 87, 195, 201]
        if self.mode in ('ssub', 'rsub', 'rfix'):
            exp_warnings = """
                WARNING: Unreplaced address (50001):
                  50001 C351   LD HL,50001   : 50000 C350 LD HL,50001
                WARNING: Address 50006 replaced with 50007 in unsubbed LD operation:
                  50004 C354   LD DE,50006   : 50003 C353 LD DE,50006
            """
        else:
            exp_warnings = """
                WARNING: Address 50006 replaced with 50007 in unsubbed LD operation:
                  50004 C354   LD DE,50006   : 50003 C353 LD DE,50006
            """
        self._test_write(skool, 50000, exp_data, self.mode, exp_warnings=exp_warnings)

    def test_no_warnings(self):
        skool = """
            c50000 LD HL,50001 ; Unreplaced address (50001)
             50003 LD DE,50006 ; Address 50006 replaced with 50007
            @{}=>XOR A
             50006 RET
        """.format(self.mode)
        exp_data = [33, 81, 195, 17, 87, 195, 175, 201]
        self._test_write(skool, 50000, exp_data, self.mode, warn=False, exp_warnings='')

    def test_no_warnings_for_subbed_ld_operations(self):
        skool = """
            @{0}=>LD BC,50006 ; Address replaced with 50009, but no warning
            @{0}=LD DE,50006  ; Address replaced with 50009, but no warning
            c50000 LD DE,50006
            @{0}=|LD HL,50006 ; Address replaced with 50009, but no warning
            @{0}=LD SP,50006  ; Address replaced with 50009, but no warning
             50003 LD HL,50000
             50006 RET
        """.format(self.mode)
        exp_data = [1, 92, 195, 17, 92, 195, 33, 92, 195, 49, 92, 195, 201]
        self._test_write(skool, 50000, exp_data, self.mode, exp_warnings='')

    def test_no_warning_for_address_in_data_block(self):
        skool = """
            c50000 LD HL,50003 ; Address 50003 replaced with 50004, but no warning

            @{}=>DEFB 1
            b50003 DEFB 2
        """.format(self.mode)
        exp_data = [33, 84, 195, 1, 2]
        self._test_write(skool, 50000, exp_data, self.mode, exp_warnings='')

    def test_no_warning_for_addresses_outside_disassembly_range(self):
        skool = """
            b29998 DEFB 1,1    ; This is outside the disassembly range

            c30000 LD HL,29999 ; Unreplaced address, but no warning
             30003 LD HL,30007 ; Unreplaced address, but no warning

            b30006 DEFB 2,2    ; This is outside the disassembly range
        """
        exp_data = [33, 47, 117, 33, 55, 117]
        self._test_write(skool, 30000, exp_data, self.mode, start=30000, end=30006, exp_warnings='')

    def test_no_warning_for_remote_entry_address_inside_disassembly_address_range(self):
        skool = """
            @remote=save:30001
            c30000 JP 30001
        """
        exp_data = [195, 49, 117]
        self._test_write(skool, 30000, exp_data, self.mode, exp_warnings='')

    def test_directive_defining_label_only(self):
        skool = """
            @{}=DONE:
            c50000 RET
        """.format(self.mode)
        exp_data = [201]
        self._test_write(skool, 50000, exp_data, self.mode)

    def test_directive_defining_label(self):
        skool = """
            @{}=START: INC A
            c50000 DEC A
        """.format(self.mode)
        exp_data = [60]
        self._test_write(skool, 50000, exp_data, self.mode)

    def test_directive_replacing_comment_only(self):
        skool = """
            @{}=       ; Finished
            c50000 RET ; Done
        """.format(self.mode)
        exp_data = [201]
        self._test_write(skool, 50000, exp_data, self.mode)

    def test_directive_replacing_comment(self):
        skool = """
            @{}=DEC A    ; Finished
            c50000 INC A ; Done
        """.format(self.mode)
        exp_data = [61]
        self._test_write(skool, 50000, exp_data, self.mode)

    def test_directive_increasing_address_of_next_entry(self):
        skool = """
            @{}=LD HL,0
            c50000 LD L,0

            c50002 RET ; This instruction should be at 50003
        """.format(self.mode)
        exp_data = [33, 0, 0, 201]
        self._test_write(skool, 50000, exp_data, self.mode)

    def test_directive_decreasing_address_of_next_entry(self):
        skool = """
            @{}=LD L,0
            c50000 LD HL,0

            c50003 RET ; This instruction should be at 50002
        """.format(self.mode)
        exp_data = [46, 0, 201]
        self._test_write(skool, 50000, exp_data, self.mode)

    def test_directive_replacing_one_instruction_with_two(self):
        skool = """
            @{0}=|XOR A
            @{0}=|INC A
            c49152 LD A,1
        """.format(self.mode)
        exp_data = [175, 60]
        self._test_write(skool, 49152, exp_data, self.mode)

    def test_directive_replacing_two_instructions_with_one(self):
        skool = """
            @{}=|LD A,1
            c49152 XOR A
             49153 INC A
        """.format(self.mode)
        exp_data = [62, 1]
        self._test_write(skool, 49152, exp_data, self.mode)

    def test_directive_replacing_later_instruction(self):
        skool = """
            @{0}=|
            @{0}=|DEC A
            c49152 XOR A
             49153 INC A
        """.format(self.mode)
        exp_data = [175, 61]
        self._test_write(skool, 49152, exp_data, self.mode)

    def test_directive_replacing_two_moved_instructions_with_one(self):
        skool = """
            @{0}=+INC A
            c50000 XOR A
            @{0}=|LD BC,256
             50001 LD C,0  ; This is moved to 50002
             50003 LD B,A  ; This is moved to 50004
             50004 RET     ; This is moved to 50005
        """.format(self.mode)
        exp_data = [175, 60, 1, 0, 1, 201]
        self._test_write(skool, 50000, exp_data, self.mode)

    def test_directive_replacing_three_moved_instructions(self):
        skool = """
            @{0}=+INC A
            c50000 XOR A
            @{0}=|LD D,A
            @{0}=|LD B,A
            @{0}=|LD C,A
             50001 LD B,A  ; This is moved to 50002
             50002 LD C,A  ; This is moved to 50003
             50003 LD D,A  ; This is moved to 50004
             50004 RET     ; This is moved to 50005
        """.format(self.mode)
        exp_data = [175, 60, 87, 71, 79, 201]
        self._test_write(skool, 50000, exp_data, self.mode)

    def test_directive_inserting_instruction_before(self):
        skool = """
            @{}=>XOR A
            c24576 RET
        """.format(self.mode)
        exp_data = [175, 201]
        self._test_write(skool, 24576, exp_data, self.mode)

    def test_directive_inserting_instruction_after(self):
        skool = """
            @{}=+RET
            c24576 XOR A
        """.format(self.mode)
        exp_data = [175, 201]
        self._test_write(skool, 24576, exp_data, self.mode)

    def test_directive_removing_instruction(self):
        skool = """
            @{}=!30001
            c30000 XOR A
             30001 RET
        """.format(self.mode)
        exp_data = [175]
        self._test_write(skool, 30000, exp_data, self.mode)

    def test_directive_removing_instruction_adjusts_relative_jump_operand(self):
        skool = """
            @{}=!30000
            c30000 DEFS 130   ; This is removed
             30130 DJNZ 30130 ; At 30000, 'DJNZ 30130' would fail to assemble
             30132 JR 30134   ; At 30002, 'JR 30134' would fail to assemble
             30134 RET
        """.format(self.mode)
        exp_data = [16, 254, 24, 0, 201]
        self._test_write(skool, 30000, exp_data, self.mode)

    def test_directive_removes_instructions_in_current_entry_only(self):
        skool = """
            @{}=!30001-30002
            c30000 XOR A
             30001 RET

            c30002 INC A
        """.format(self.mode)
        exp_data = [175, 60]
        self._test_write(skool, 30000, exp_data, self.mode)

    def test_ignoring_prepend_directive_on_removed_instruction(self):
        skool = """
            @{0}=!50000
            @{0}=>XOR A
            c50000 INC A

            @{0}+begin
            c50000 RET
            @{0}+end
        """.format(self.mode)
        exp_data = [201]
        self._test_write(skool, 50000, exp_data, self.mode)

    def test_ignoring_overwrite_directives_on_removed_instruction(self):
        skool = """
            @{0}=!50000
            @{0}=|XOR A
            @{0}=|INC A
            c50000 LD A,1

            @{0}+begin
            c50000 RET
            @{0}+end
        """.format(self.mode)
        exp_data = [201]
        self._test_write(skool, 50000, exp_data, self.mode)

    def test_ignoring_append_directive_on_removed_instruction(self):
        skool = """
            @{0}=!50000
            @{0}=+INC A
            c50000 XOR A

            @{0}+begin
            c50000 RET
            @{0}+end
        """.format(self.mode)
        exp_data = [201]
        self._test_write(skool, 50000, exp_data, self.mode)

    def test_ignoring_data_directive_on_removed_instruction(self):
        skool = """
            @{0}=!50000
            @defb=1,2,3
            c50000 XOR A
             50001 RET
        """.format(self.mode)
        exp_data = [201]
        self._test_write(skool, 50000, exp_data, self.mode, data=True)

    def test_ignoring_keep_directive_on_removed_instruction(self):
        skool = """
            @{0}=!50000
            @keep=50004
            c50000 XOR A
             50001 LD HL,50004
             50004 RET
        """.format(self.mode)
        exp_data = [33, 83, 195, 201]
        exp_warnings = """
            WARNING: Address 50004 replaced with 50003 in unsubbed LD operation:
              50000 C350   LD HL,50004   : 50001 C351 LD HL,50004
        """
        self._test_write(skool, 50000, exp_data, self.mode, exp_warnings=exp_warnings)

    def test_ignoring_nowarn_directive_on_removed_instruction(self):
        skool = """
            @{0}=!50000
            @nowarn
            c50000 XOR A
             50001 LD HL,50004
             50004 RET
        """.format(self.mode)
        exp_data = [33, 83, 195, 201]
        exp_warnings = """
            WARNING: Address 50004 replaced with 50003 in unsubbed LD operation:
              50000 C350   LD HL,50004   : 50001 C351 LD HL,50004
        """
        self._test_write(skool, 50000, exp_data, self.mode, exp_warnings=exp_warnings)

    def test_block_directive_minus_no_else_inactive(self):
        skool = """
            b32768 DEFB 1
            @{0}-begin
             32769 DEFB 2
            @{0}-end
        """.format(self.mode)
        exp_data = [1, 2]
        self._test_write(skool, 32768, exp_data)

    def test_block_directive_plus_no_else_inactive(self):
        skool = """
            b32768 DEFB 1
            @{0}+begin
             32769 DEFB 2
            @{0}+end
        """.format(self.mode)
        exp_data = [1]
        self._test_write(skool, 32768, exp_data)

    def test_block_directive_minus_no_else_active(self):
        skool = """
            b32768 DEFB 1
            @{0}-begin
             32769 DEFB 2
            @{0}-end
        """.format(self.mode)
        exp_data = [1]
        self._test_write(skool, 32768, exp_data, self.mode)

    def test_block_directive_plus_no_else_active(self):
        skool = """
            b32768 DEFB 1
            @{0}+begin
             32769 DEFB 2
            @{0}+end
        """.format(self.mode)
        exp_data = [1, 2]
        self._test_write(skool, 32768, exp_data, self.mode)

    def test_block_directive_with_else_inactive(self):
        skool = """
            b32768 DEFB 1
            @{0}-begin
             32769 DEFB 2
            @{0}+else
             32769 DEFB 3
            @{0}+end
        """.format(self.mode)
        exp_data = [1, 2]
        self._test_write(skool, 32768, exp_data)

    def test_block_directive_with_else_active(self):
        skool = """
            b32768 DEFB 1
            @{0}-begin
             32769 DEFB 2
            @{0}+else
             32769 DEFB 3
            @{0}+end
        """.format(self.mode)
        exp_data = [1, 3]
        self._test_write(skool, 32768, exp_data, self.mode)

    def test_block_directive_spanning_two_entries_inactive(self):
        skool = """
            b32768 DEFB 1
            @{0}-begin
             32769 DEFB 2

            u32770 DEFB 3
            @{0}+else
             32769 DEFB 4
             32770 DEFB 8
            @{0}+end
        """.format(self.mode)
        exp_data = [1, 2, 3]
        self._test_write(skool, 32768, exp_data)

    def test_block_directive_spanning_two_entries_active(self):
        skool = """
            b32768 DEFB 1
            @{0}-begin
             32769 DEFB 2

            u32770 DEFB 3
            @{0}+else
             32769 DEFB 4
             32770 DEFB 8
            @{0}+end
        """.format(self.mode)
        exp_data = [1, 4, 8]
        self._test_write(skool, 32768, exp_data, self.mode)

    def test_addressless_instruction_in_block_directive(self):
        skool = """
            b32768 DEFB 1
            @{0}-begin
             32769 DEFB 2
            @{0}+else
                   DEFB 3
            @{0}+end
        """.format(self.mode)
        exp_data = [1, 3]
        self._test_write(skool, 32768, exp_data, self.mode)

    def test_invalid_sub_instruction(self):
        skool = """
            c40000 LD A,B
            @{}=XOR HL
             40001 XOR L
             40002 RET
        """.format(self.mode)
        exp_error = 'Failed to assemble:\n 40001 XOR HL'
        skoolfile = self.write_text_file(dedent(skool).strip(), suffix='.skool')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_skool2bin('--{} {}'.format(self.mode, skoolfile))
        self.assertEqual(cm.exception.args[0], 'Failed to assemble:\n 40001 XOR HL')

    def test_invalid_org_address(self):
        skoolfile = self.write_text_file('@org=?\nc40000 RET', suffix='.skool')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_skool2bin('--{} {}'.format(self.mode, skoolfile))
        self.assertEqual(cm.exception.args[0], 'Invalid org address: ?')

class isubTest(BinWriterTestCase, DirectiveTestCase):
    mode = 'isub'
    applies = ('isub',)
    overrides = ()

class ssubTest(BinWriterTestCase, DirectiveTestCase):
    mode = 'ssub'
    applies = ('isub', 'ssub')
    overrides = ('isub',)

class rsubTest(BinWriterTestCase, DirectiveTestCase):
    mode = 'rsub'
    applies = ('isub', 'ssub', 'rsub', 'ofix')
    overrides = ('isub', 'ssub')

class ofixTest(BinWriterTestCase, DirectiveTestCase):
    mode = 'ofix'
    applies = ('ofix',)
    overrides = ('isub', 'ssub', 'rsub')

class bfixTest(BinWriterTestCase, DirectiveTestCase):
    mode = 'bfix'
    applies = ('ofix', 'bfix')
    overrides = ('ofix', 'isub', 'ssub', 'rsub')

class rfixTest(BinWriterTestCase, DirectiveTestCase):
    mode = 'rfix'
    applies = ('isub', 'ssub', 'rsub', 'ofix', 'bfix', 'rfix')
    overrides = ('ofix', 'bfix', 'isub', 'ssub', 'rsub')
