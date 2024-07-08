from textwrap import dedent
from unittest.mock import patch

from skoolkittest import (SkoolKitTestCase, PZX, create_header_block,
                          create_data_block, create_tap_header_block,
                          create_tap_data_block, create_tzx_header_block,
                          create_tzx_data_block)
from skoolkit import SkoolKitError, tapinfo, get_word, VERSION

TZX_DATA_BLOCK = (16, 0, 0, 3, 0, 255, 0, 0)

TZX_DATA_BLOCK_DESC = """
{}: Standard speed data (0x10)
  Pause: 0ms
  Type: Data block
  Length: 3
  Data: 255, 0, 0
"""

def _get_archive_info(text_id, text):
    return [text_id, len(text)] + [ord(c) for c in text]

class MockBasicLister:
    def list_basic(self, snapshot):
        global mock_basic_lister
        mock_basic_lister = self
        self.snapshot = snapshot
        return 'BASIC DONE!'

class TapinfoTest(SkoolKitTestCase):
    def _write_tzx(self, blocks, minor_version=20):
        tzx_data = [ord(c) for c in "ZXTape!"]
        tzx_data.extend((26, 1, minor_version))
        for block in blocks:
            tzx_data.extend(block)
        return self.write_bin_file(tzx_data, suffix='.tzx')

    def _test_tzx_block(self, data, exp_output, blocks=1):
        tzxfile = self._write_tzx([data, TZX_DATA_BLOCK])
        output, error = self.run_tapinfo(tzxfile)
        self.assertEqual(error, '')
        final_block = TZX_DATA_BLOCK_DESC.format(blocks + 1)
        self.assertEqual('Version: 1.20\n' + dedent(exp_output).strip() + final_block, output)

    def _test_bad_spec(self, option, bad_spec, exp_error):
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tapinfo('{} {} test.tap'.format(option, bad_spec))
        self.assertEqual(cm.exception.args[0], '{}: {}'.format(exp_error, bad_spec))

    def test_no_arguments(self):
        output, error = self.run_tapinfo(catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: tapinfo.py'))

    def test_invalid_option(self):
        output, error = self.run_tapinfo('-x test.tap', catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: tapinfo.py'))

    def test_unrecognised_tape_type(self):
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tapinfo('unknown.tape')
        self.assertEqual(cm.exception.args[0], 'Unrecognised tape type')

    def test_pzx_file(self):
        info = (
            ('', 'Flip Flap'),
            ('Publisher', 'Software Inc.'),
            ('Author', 'J. Bloggs'),
            ('Author', 'J. Doe'),
            ('Year', '1982'),
            ('Language', 'Strong'),
            ('Type', 'Game'),
            ('Price', '5.99'),
            ('Protection', 'None'),
            ('Origin', 'Uncertain'),
            ('Comment', 'No comment')
        )
        pzx = PZX(0, 3, info, False)
        pzx.add_puls(pulses=[40, 40000, 400000])
        pzx.add_data([1, 2, 3, 4], s0=(400, 405), s1=(800, 807), tail=1024, used_bits=5, polarity=1)
        pzx.add_paus(1234567, polarity=1)
        pzx.add_brws('End of tape')
        pzx.add_stop(False)
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tapinfo(pzxfile)
        self.assertEqual(error, '')
        exp_output = """
            1: PZX header block
              Version: 0.3
              Title: Flip Flap
              Publisher: Software Inc.
              Author: J. Bloggs
              Author: J. Doe
              Year: 1982
              Language: Strong
              Type: Game
              Price: 5.99
              Protection: None
              Origin: Uncertain
              Comment: No comment
            2: Pulse sequence
              1 x 40 T-states
              1 x 40000 T-states
              1 x 400000 T-states
            3: Data block
              Bits: 29 (3 bytes + 5 bits)
              Initial pulse level: 1
              0-bit pulse sequence: 400, 405 (T-states)
              1-bit pulse sequence: 800, 807 (T-states)
              Tail pulse: 1024 T-states
              Length: 4
              Data: 1, 2, 3, 4
            4: Pause
              Duration: 1234567 T-states
              Initial pulse level: 1
            5: Browse point
              End of tape
            6: Stop tape command
              Mode: 48K only
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_pzx_with_standard_speed_blocks(self):
        data0 = create_header_block('test_pzx00', 100, 200, 0)
        data1 = create_header_block('test_pzx01', length=4, data_type=1)
        data2 = create_header_block('test_pzx02', length=5, data_type=2)
        data3 = create_header_block('test_pzx03', 32768, 3, 3)
        data4 = create_data_block([1, 2, 3])
        pzx = PZX()
        for standard, data in ((2, data0), (2, data1), (2, data2), (2, data3), (1, data4)):
            pzx.add_puls(standard)
            pzx.add_data(data)
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tapinfo(pzxfile)
        self.assertEqual(error, '')
        exp_output = """
            1: PZX header block
              Version: 1.0
            2: Pulse sequence
              8063 x 2168 T-states
              1 x 667 T-states
              1 x 735 T-states
            3: Data block
              Bits: 152 (19 bytes)
              Initial pulse level: 1
              0-bit pulse sequence: 855, 855 (T-states)
              1-bit pulse sequence: 1710, 1710 (T-states)
              Tail pulse: 945 T-states
              Type: Header block
              Program: test_pzx00
              LINE: 100
              Length: 19
              Data: 0, 0, 116, 101, 115, 116, 95 ... 200, 0, 100, 0, 200, 0, 95
            4: Pulse sequence
              8063 x 2168 T-states
              1 x 667 T-states
              1 x 735 T-states
            5: Data block
              Bits: 152 (19 bytes)
              Initial pulse level: 1
              0-bit pulse sequence: 855, 855 (T-states)
              1-bit pulse sequence: 1710, 1710 (T-states)
              Tail pulse: 945 T-states
              Type: Header block
              Number array: test_pzx01
              Length: 19
              Data: 0, 1, 116, 101, 115, 116, 95 ... 4, 0, 0, 0, 0, 0, 63
            6: Pulse sequence
              8063 x 2168 T-states
              1 x 667 T-states
              1 x 735 T-states
            7: Data block
              Bits: 152 (19 bytes)
              Initial pulse level: 1
              0-bit pulse sequence: 855, 855 (T-states)
              1-bit pulse sequence: 1710, 1710 (T-states)
              Tail pulse: 945 T-states
              Type: Header block
              Character array: test_pzx02
              Length: 19
              Data: 0, 2, 116, 101, 115, 116, 95 ... 5, 0, 0, 0, 0, 0, 62
            8: Pulse sequence
              8063 x 2168 T-states
              1 x 667 T-states
              1 x 735 T-states
            9: Data block
              Bits: 152 (19 bytes)
              Initial pulse level: 1
              0-bit pulse sequence: 855, 855 (T-states)
              1-bit pulse sequence: 1710, 1710 (T-states)
              Tail pulse: 945 T-states
              Type: Header block
              Bytes: test_pzx03
              CODE: 32768,3
              Length: 19
              Data: 0, 3, 116, 101, 115, 116, 95 ... 3, 0, 0, 128, 0, 0, 184
            10: Pulse sequence
              3223 x 2168 T-states
              1 x 667 T-states
              1 x 735 T-states
            11: Data block
              Bits: 40 (5 bytes)
              Initial pulse level: 1
              0-bit pulse sequence: 855, 855 (T-states)
              1-bit pulse sequence: 1710, 1710 (T-states)
              Tail pulse: 945 T-states
              Type: Data block
              Length: 5
              Data: 255, 1, 2, 3, 255
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_pzx_with_unknown_block(self):
        pzx = PZX()
        pzx.add_block('????', [255])
        pzx.add_stop()
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tapinfo(pzxfile)
        self.assertEqual(error, '')
        exp_output = """
            1: PZX header block
              Version: 1.0
            2: ????
            3: Stop tape command
              Mode: Always
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_invalid_pzx_file(self):
        invalid_pzx = self.write_text_file('This is not a PZX file', suffix='.pzx')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tapinfo(invalid_pzx)
        self.assertEqual(cm.exception.args[0], 'Not a PZX file')

    def test_tap_file(self):
        tap_data = create_tap_header_block('program_01', 100, 200, 0)
        data = [1, 2, 4]
        tap_data.extend(create_tap_header_block('test_tap01', 32768, len(data)))
        tap_data.extend(create_tap_data_block(data))
        tap_data.extend(create_tap_header_block('numbers_01', length=5, data_type=1))
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        output, error = self.run_tapinfo(tapfile)
        self.assertEqual(error, '')
        exp_output = """
            1:
              Type: Header block
              Program: program_01
              LINE: 100
              Length: 19
              Data: 0, 0, 112, 114, 111, 103, 114 ... 200, 0, 100, 0, 200, 0, 78
            2:
              Type: Header block
              Bytes: test_tap01
              CODE: 32768,3
              Length: 19
              Data: 0, 3, 116, 101, 115, 116, 95 ... 3, 0, 0, 128, 0, 0, 173
            3:
              Type: Data block
              Length: 5
              Data: 255, 1, 2, 4, 248
            4:
              Type: Header block
              Number array: numbers_01
              Length: 19
              Data: 0, 1, 110, 117, 109, 98, 101 ... 5, 0, 0, 0, 0, 0, 42
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_tap_file_with_empty_block(self):
        tap_data = create_tap_header_block('test_tap02', 32768, 3)
        tap_data.extend(create_tap_data_block([1, 2, 3]))
        tap_data.extend((0, 0))
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        output, error = self.run_tapinfo(tapfile)
        self.assertEqual(error, '')
        exp_output = """
            1:
              Type: Header block
              Bytes: test_tap02
              CODE: 32768,3
              Length: 19
              Data: 0, 3, 116, 101, 115, 116, 95 ... 3, 0, 0, 128, 0, 0, 174
            2:
              Type: Data block
              Length: 5
              Data: 255, 1, 2, 3, 255
            3:
              Length: 0
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_tap_file_with_extraneous_byte(self):
        data = [1, 2, 4]
        tap_data = create_tap_data_block(data)
        tap_data.append(0)
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        output, error = self.run_tapinfo(tapfile)
        self.assertEqual(error, 'WARNING: Extraneous byte at end of file\n')
        exp_output = """
            1:
              Type: Data block
              Length: 5
              Data: 255, 1, 2, 4, 248
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_tap_file_with_missing_bytes(self):
        data = [1, 2, 4]
        tap_data = create_tap_data_block(data)[:-2]
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        output, error = self.run_tapinfo(tapfile)
        self.assertEqual(error, 'WARNING: Missing 2 data byte(s) at end of file\n')
        exp_output = """
            1:
              Type: Data block
              Length: 3
              Data: 255, 1, 2
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_tzx_file(self):
        blocks = []
        blocks.append(create_tzx_header_block('<TEST_tzx>', start=10, data_type=0, pause=1000))
        blocks.append(create_tzx_data_block([1, 4, 16], pause=500))
        blocks.append(create_tzx_header_block('characters', data_type=2))
        blocks.append(create_tzx_data_block([64, 0]))

        tzxfile = self._write_tzx(blocks)
        output, error = self.run_tapinfo(tzxfile)
        self.assertEqual(error, '')
        exp_output = """
            Version: 1.20
            1: Standard speed data (0x10)
              Pause: 1000ms
              Type: Header block
              Program: <TEST_tzx>
              LINE: 10
              Length: 19
              Data: 0, 0, 60, 84, 69, 83, 84 ... 0, 0, 10, 0, 0, 0, 55
            2: Standard speed data (0x10)
              Pause: 500ms
              Type: Data block
              Length: 5
              Data: 255, 1, 4, 16, 234
            3: Standard speed data (0x10)
              Pause: 0ms
              Type: Header block
              Character array: characters
              Length: 19
              Data: 0, 2, 99, 104, 97, 114, 97 ... 0, 0, 0, 0, 0, 0, 8
            4: Standard speed data (0x10)
              Pause: 0ms
              Type: Data block
              Length: 4
              Data: 255, 64, 0, 191
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_tzx_with_minor_version_less_than_10(self):
        blocks = [create_tzx_data_block([0])]
        tzxfile = self._write_tzx(blocks, 3)
        output, error = self.run_tapinfo(tzxfile)
        self.assertEqual(error, '')
        self.assertEqual(output.split('\n')[0], 'Version: 1.03')

    def test_invalid_tzx_file(self):
        invalid_tzx = self.write_text_file('This is not a TZX file', suffix='.tzx')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tapinfo(invalid_tzx)
        self.assertEqual(cm.exception.args[0], 'Not a TZX file')

    def test_tzx_with_no_version_number(self):
        tzx = self.write_text_file('ZXTape!\x1a', suffix='.tzx')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tapinfo(tzx)
        self.assertEqual(cm.exception.args[0], 'TZX version number not found')

    def test_tzx_with_unknown_block(self):
        block_id = 26
        block = [block_id, 0]
        tzxfile = self._write_tzx([block])
        with self.assertRaises(SkoolKitError) as cm:
            self.run_tapinfo(tzxfile)
        self.assertEqual(cm.exception.args[0], f'Unknown TZX block ID: 0x{block_id:02X}')

    def test_tzx_block_0x11(self):
        data = [0, 1, 2]
        block = [
            17,      # Block ID
            119, 8,  # Pilot pulse length
            154, 2,  # Sync pulse 1 length
            224, 2,  # Sync pulse 2 length
            170, 1,  # 0-pulse length
            71, 3,   # 1-pulse length
            152, 12, # Pilot tone pulses
            5,       # Used bits in last byte
            234, 3   # Pause
        ]
        data_block = create_data_block(data)
        block.extend((len(data_block), 0, 0))
        block.extend(data_block)
        exp_output = """
            1: Turbo speed data (0x11)
              Pilot pulse: 2167
              Sync pulse 1: 666
              Sync pulse 2: 736
              0-pulse: 426
              1-pulse: 839
              Pilot length: 3224 pulses
              Used bits in last byte: 5
              Pause: 1002ms
              Length: 5
              Data: 255, 0, 1, 2, 252
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x12(self):
        block = [18] # Block ID
        block.extend((2, 2)) # Pulse length
        block.extend((3, 3)) # Number of pulses
        exp_output = """
            1: Pure tone (0x12)
              Pulse length: {} T-states
              Pulses: {}
        """.format(get_word(block, 1), get_word(block, 3))
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x13(self):
        block = [19] # Block ID
        block.append(2) # Number of pulses
        block.extend((0, 1, 0, 2)) # Pulse lengths
        exp_output = """
            1: Pulse sequence (0x13)
              Pulse 1/2: 256
              Pulse 2/2: 512
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x14(self):
        data = [1, 2, 3]
        block = [20] # Block ID
        block.extend((1, 1)) # Length of 0-pulse
        block.extend((2, 2)) # Length of 1-pulse
        block.append(6) # Used bits in last byte
        block.extend((232, 3)) # Pause length
        block.extend((len(data), 0, 0))
        block.extend(data)
        exp_output = """
            1: Pure data (0x14)
              0-pulse: 257
              1-pulse: 514
              Used bits in last byte: 6
              Pause: 1000ms
              Length: 3
              Data: 1, 2, 3
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x15(self):
        block = (
            21,      # Block ID
            80, 0,   # T-states per sample
            100, 0,  # Pause
            4,       # Used bits in last byte
            2, 0, 0, # Length of samples data
            128, 12  # Samples
        )
        exp_output = """
            1: Direct recording (0x15)
              T-states per sample: 80
              Pause: 100ms
              Used bits in last byte: 4
              Length: 2
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x16(self):
        block = [22] # Block ID
        block.extend((5, 0, 0, 0)) # Block length
        block.extend((1, 2, 3, 4, 5)) # Data
        exp_output = '1: C64 ROM type data (0x16)'
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x17(self):
        block = [23] # Block ID
        block.extend((4, 0, 0, 0)) # Block length
        block.extend((1, 2, 3, 4)) # Data
        exp_output = '1: C64 turbo tape data (0x17)'
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x18_rle_compression(self):
        block = (
            24,          # Block ID
            12, 0, 0, 0, # Block length
            100, 0,      # Pause
            68, 172, 0,  # Sampling rate
            1,           # Compression type
            2, 0, 0, 0,  # Number of pulses
            1, 1         # CSW data
        )
        exp_output = """
            1: CSW recording (0x18)
              Number of pulses: 2
              Sampling rate: 44100 Hz
              Compression type: RLE
              Pause: 100ms
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x18_zrle_compression(self):
        block = (
            24,          # Block ID
            13, 0, 0, 0, # Block length
            200, 0,      # Pause
            34, 86, 0,   # Sampling rate
            2,           # Compression type
            3, 0, 0, 0,  # Number of pulses
            1, 2, 1      # CSW data
        )
        exp_output = """
            1: CSW recording (0x18)
              Number of pulses: 3
              Sampling rate: 22050 Hz
              Compression type: Z-RLE
              Pause: 200ms
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x18_unknown_compression(self):
        block = (
            24,          # Block ID
            14, 0, 0, 0, # Block length
            232, 3,      # Pause
            128, 187, 0, # Sampling rate
            3,           # Compression type
            4, 0, 0, 0,  # Number of pulses
            1, 2, 1, 3   # CSW data
        )
        exp_output = """
            1: CSW recording (0x18)
              Number of pulses: 4
              Sampling rate: 48000 Hz
              Compression type: Unknown
              Pause: 1000ms
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x19(self):
        block = [25] # Block ID
        block.extend((20, 0, 0, 0)) # Block length
        block.extend([0] * block[1])
        exp_output = '1: Generalized data (0x19)'
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x20_stop_the_tape(self):
        block = [32] # Block ID
        block.extend((0, 0))
        exp_output = "1: 'Stop the tape' command (0x20)"
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x20_pause(self):
        block = [32] # Block ID
        block.extend((100, 0)) # Pause duration
        exp_output = """
            1: Pause (silence) (0x20)
              Duration: 100ms
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x21(self):
        block = [33] # Block ID
        name = 'groupname'
        block.append(len(name))
        block.extend([ord(c) for c in name])
        exp_output = """
            1: Group start (0x21)
              Name: groupname
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x22(self):
        block = [34] # Block ID
        exp_output = '1: Group end (0x22)'
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x23(self):
        blocks = [35] # Block ID
        blocks.extend((1, 0)) # Jump offset (1)
        blocks.append(35) # Block ID
        blocks.extend((255, 255)) # Jump offset (-1)
        exp_output = """
            1: Jump to block (0x23)
              Destination block: 2
            2: Jump to block (0x23)
              Destination block: 1
        """
        self._test_tzx_block(blocks, exp_output, 2)

    def test_tzx_block_0x24(self):
        block = [36] # Block ID
        block.extend((7, 0)) # Number of repetitions
        exp_output = """
            1: Loop start (0x24)
              Repetitions: 7
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x25(self):
        block = [37] # Block ID
        exp_output = '1: Loop end (0x25)'
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x26(self):
        block = [38] # Block ID
        block.extend((2, 0)) # Number of calls
        block.extend((1, 0, 1, 0)) # Blocks to call
        exp_output = '1: Call sequence (0x26)'
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x27(self):
        block = [39] # Block ID
        exp_output = '1: Return from sequence (0x27)'
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x28(self):
        block = [40] # Block ID
        block.extend((0, 0))
        block.append(2) # Number of selections

        block.extend((1, 0)) # Offset
        text = '48K'
        block.append(len(text))
        block.extend([ord(c) for c in text])

        block.extend((2, 0)) # Offset
        text = '128K'
        block.append(len(text))
        block.extend([ord(c) for c in text])

        block[1] = len(block) - 3 # Length

        exp_output = """
            1: Select block (0x28)
              Option 1 (block 2): 48K
              Option 2 (block 3): 128K
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x2A(self):
        block = [42] # Block ID
        block.extend((0, 0, 0, 0))
        exp_output = '1: Stop the tape if in 48K mode (0x2A)'
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x2B_low(self):
        block = [43] # Block ID
        block.extend((1, 0, 0, 0))
        block.append(0) # Signal level
        exp_output = """
            1: Set signal level (0x2B)
              Signal level: 0 (low)
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x2B_high(self):
        block = [43] # Block ID
        block.extend((1, 0, 0, 0))
        block.append(1) # Signal level
        exp_output = """
            1: Set signal level (0x2B)
              Signal level: 1 (high)
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x30(self):
        block = [48] # Block ID
        block.extend((0, 65, 94, 67, 13, 33))
        block[1] = len(block) - 2
        exp_output = """
            1: Text description (0x30)
              Text: A↑C
                    !
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x31(self):
        block = [49] # Block ID
        block.extend((1, 0, 127, 32, 49, 57, 56, 53, 8, 54, 13, 77, 101))
        block[2] = len(block) - 3
        exp_output = """
            1: Message (0x31)
              Message: © 1985?6
                       Me
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x32(self):
        block = [50] # Block ID
        strings = (
            (0, 'Awesome game'),
            (1, 'Awesome Software'),
            (2, 'A. Wesome'),
            (3, '1985'),
            (4, 'English'),
            (5, 'Arcade'),
            (6, '\x605.95'),
            (7, 'None'),
            (8, 'Big bang'),
            (255, 'This is an awesome game\x0dYes it is!'),
            (128, 'Unknown')
        )
        archive_info = [len(strings)]
        for text_id, text in strings:
            archive_info.extend(_get_archive_info(text_id, text))
        length = len(archive_info)
        block.extend((length % 256, length // 256))
        block.extend(archive_info)
        exp_output = """
            1: Archive info (0x32)
              Full title: Awesome game
              Software house/publisher: Awesome Software
              Author(s): A. Wesome
              Year of publication: 1985
              Language: English
              Game/utility type: Arcade
              Price: £5.95
              Protection scheme/loader: None
              Origin: Big bang
              Comment(s): This is an awesome game
                          Yes it is!
              128: Unknown
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x32_truncated(self):
        block = [50] # Block ID
        strings = (
            (0, 'Awesome game'),
            (1, 'Awesome Software')
        )
        archive_info = [len(strings)]
        for text_id, text in strings:
            archive_info.extend(_get_archive_info(text_id, text))
        length = len(archive_info)
        block.extend((length % 256, length // 256))
        block.extend(archive_info[:10])

        with self.assertRaises(SkoolKitError) as cm:
            self.run_tapinfo(self._write_tzx([block]))
        self.assertEqual(cm.exception.args[0], 'Unexpected end of file')

    def test_tzx_block_0x33(self):
        block = [0x33] # Block ID
        entries = (
            0, 3, 2,
            0, 2, 0,
            0, 1, 1,
            0, 0, 3,
            3, 3, 1,
            4, 0, 2,
            6, 1, 0,
            8, 0, 3
        )
        block.append(len(entries) // 3) # Number of entries
        block.extend(entries)
        exp_output = """
            1: Hardware type (0x33)
              - Type: Computer
                Name: ZX Spectrum 128K + (Sinclair)
                Info: Runs on this machine, but does not use its special features
              - Type: Computer
                Name: ZX Spectrum 48K Issue 1
                Info: Runs on this machine, but may not use its special features
              - Type: Computer
                Name: ZX Spectrum 48K Plus
                Info: Uses special features of this machine
              - Type: Computer
                Name: ZX Spectrum 16K
                Info: Does not run on this machine
              - Type: Sound device
                Name: SpecDrum
                Info: Uses this hardware
              - Type: Joystick
                Name: Kempston
                Info: Runs but does not use this hardware
              - Type: Other controller
                Name: ZX Light Gun
                Info: Runs with this hardware, but may not use it
              - Type: Parallel port
                Name: Kempston S
                Info: Does not run with this hardware
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x34(self):
        block = [52] # Block ID
        block.extend((1, 2, 3, 4, 5, 6, 7, 8)) # Data
        exp_output = '1: Emulation info (0x34)'
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x35_pure_text(self):
        block = [0x35] # Block ID
        info_id = 'Instructions'
        block.extend([ord(c) for c in info_id[:16].ljust(16)])
        info = [ord(c) for c in 'Try to win \x60\x60\x60s\r*\tUse keys QAOP']
        block.extend((len(info), 0, 0, 0)) # Length of custom info
        block.extend(info) # Custom info
        exp_output = """
            1: Custom info (0x35)
              Instructions: Try to win £££s
                            *\tUse keys QAOP
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x35_text_and_binary(self):
        block = [0x35] # Block ID
        info_id = 'Some POKEs'
        block.extend([ord(c) for c in info_id[:16].ljust(16)])
        info = [ord(c) for c in 'Infinite lives'] + [0, 1, 2, 3, 13]
        info.extend([ord(c) for c in 'Invincibility'] + [0, 14, 15, 16])
        block.extend((len(info), 0, 0, 0)) # Length of custom info
        block.extend(info) # Custom info
        exp_output = """
            1: Custom info (0x35)
              Some POKEs: 0000  49 6E 66 69 6E 69 74 65 20 6C 69 76 65 73 00 01  Infinite lives..
                          0010  02 03 0D 49 6E 76 69 6E 63 69 62 69 6C 69 74 79  ...Invincibility
                          0020  00 0E 0F 10                                      ....
        """
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x40(self):
        block = [64] # Block ID
        block.append(0) # Snapshot type
        block.extend((1, 0, 0)) # Snapshot length
        block.append(0) # Snapshot data
        exp_output = '1: Snapshot (0x40)'
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x5A(self):
        block = [90] # Block ID
        block.extend([0] * 9)
        exp_output = '1: "Glue" block (0x5A)'
        self._test_tzx_block(block, exp_output)

    def test_basic_line_number_over_32767(self):
        tap_data = create_tap_header_block('LINE-32768', 32768, 200, 0)
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        output, error = self.run_tapinfo(tapfile)
        self.assertEqual(error, '')
        exp_output = """
            1:
              Type: Header block
              Program: LINE-32768
              Length: 19
              Data: 0, 0, 76, 73, 78, 69, 45 ... 200, 0, 0, 128, 200, 0, 155
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_names_containing_basic_tokens(self):
        tap_data = create_tap_header_block('\xef\xcb\xf7\xebFUN...', 32768, data_type=0)
        tap_data.extend(create_tap_header_block('\xc6\xaf\xc6\xe4\xcc\xe3....', 32768, 200))
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        output, error = self.run_tapinfo(tapfile)
        self.assertEqual(error, '')
        exp_output = """
            1:
              Type: Header block
              Program: LOAD THEN RUN FOR FUN...
              Length: 19
              Data: 0, 0, 239, 203, 247, 235, 70 ... 0, 0, 0, 128, 0, 0, 203
            2:
              Type: Header block
              Bytes: AND CODE AND DATA TO READ ....
              CODE: 32768,200
              Length: 19
              Data: 0, 3, 198, 175, 198, 228, 204 ... 200, 0, 0, 128, 0, 0, 47
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    @patch.object(tapinfo, 'BasicLister', MockBasicLister)
    def test_option_b_pzx(self):
        prog = [10] * 10
        pzx = PZX()
        pzx.add_data(create_data_block(prog))
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        exp_snapshot = [0] * 23755 + prog
        output, error = self.run_tapinfo(f'-b 2 {pzxfile}')
        self.assertEqual(error, '')
        self.assertEqual(output, 'BASIC DONE!\n')
        self.assertEqual(exp_snapshot, mock_basic_lister.snapshot)

    @patch.object(tapinfo, 'BasicLister', MockBasicLister)
    def test_option_b_tap(self):
        prog = [10] * 10
        tap_data = create_tap_data_block(prog)
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        exp_snapshot = [0] * 23755 + prog
        output, error = self.run_tapinfo('-b 1 {}'.format(tapfile))
        self.assertEqual(error, '')
        self.assertEqual(output, 'BASIC DONE!\n')
        self.assertEqual(exp_snapshot, mock_basic_lister.snapshot)

    @patch.object(tapinfo, 'BasicLister', MockBasicLister)
    def test_option_basic_tzx_with_address(self):
        prefix = [1] * 5
        address = 23755 - len(prefix)
        prog = [12] * 12
        data = prefix + prog
        blocks = [create_tzx_data_block(data)]
        tzxfile = self._write_tzx(blocks)
        exp_snapshot = [0] * address + data
        output, error = self.run_tapinfo('--basic 1,{} {}'.format(address, tzxfile))
        self.assertEqual(error, '')
        self.assertEqual(output, 'BASIC DONE!\n')
        self.assertEqual(exp_snapshot, mock_basic_lister.snapshot)

    @patch.object(tapinfo, 'BasicLister', MockBasicLister)
    def test_option_b_tap_with_hex_address(self):
        prefix = [4] * 4
        address = 23755 - len(prefix)
        prog = [9] * 9
        data = prefix + prog
        tap_data = create_tap_data_block(data)
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        exp_snapshot = [0] * address + data
        output, error = self.run_tapinfo('-b 1,0x{:04x} {}'.format(address, tapfile))
        self.assertEqual(error, '')
        self.assertEqual(output, 'BASIC DONE!\n')
        self.assertEqual(exp_snapshot, mock_basic_lister.snapshot)

    def test_option_b_with_invalid_block_spec(self):
        exp_error = 'Invalid block specification'
        self._test_bad_spec('-b', 'q', exp_error)
        self._test_bad_spec('--basic', '1,z', exp_error)
        self._test_bad_spec('-b', '1,2,3', exp_error)
        self._test_bad_spec('--basic', '?,+', exp_error)

    def test_option_data_with_pzx_file(self):
        pzx = PZX()
        pzx.add_data(list(range(32, 94)))
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tapinfo(f'--data {pzxfile}')
        self.assertEqual(error, '')
        exp_output = r"""
            1: PZX header block
              Version: 1.0
            2: Data block
              Bits: 496 (62 bytes)
              Initial pulse level: 1
              0-bit pulse sequence: 855, 855 (T-states)
              1-bit pulse sequence: 1710, 1710 (T-states)
              Tail pulse: 945 T-states
              Length: 62
              0000  20 21 22 23 24 25 26 27 28 29 2A 2B 2C 2D 2E 2F   !"#$%&'()*+,-./
              0010  30 31 32 33 34 35 36 37 38 39 3A 3B 3C 3D 3E 3F  0123456789:;<=>?
              0020  40 41 42 43 44 45 46 47 48 49 4A 4B 4C 4D 4E 4F  @ABCDEFGHIJKLMNO
              0030  50 51 52 53 54 55 56 57 58 59 5A 5B 5C 5D        PQRSTUVWXYZ[\]
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_d_with_tap_file(self):
        data = [1, 2, 4, 8]
        tap_data = create_tap_header_block('test_tap02', 49152, len(data))
        tap_data.extend(create_tap_data_block(data))
        tap_data.extend(create_tap_header_block('characters', data_type=2))
        tap_data.extend(create_tap_data_block(list(range(32, 94))))
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        output, error = self.run_tapinfo('-d {}'.format(tapfile))
        self.assertEqual(error, '')
        exp_output = r"""
            1:
              Type: Header block
              Bytes: test_tap02
              CODE: 49152,4
              Length: 19
              0000  00 03 74 65 73 74 5F 74 61 70 30 32 04 00 00 C0  ..test_tap02....
              0010  00 00 E9                                         ...
            2:
              Type: Data block
              Length: 6
              0000  FF 01 02 04 08 F0                                ......
            3:
              Type: Header block
              Character array: characters
              Length: 19
              0000  00 02 63 68 61 72 61 63 74 65 72 73 00 00 00 00  ..characters....
              0010  00 00 08                                         ...
            4:
              Type: Data block
              Length: 64
              0000  FF 20 21 22 23 24 25 26 27 28 29 2A 2B 2C 2D 2E  . !"#$%&'()*+,-.
              0010  2F 30 31 32 33 34 35 36 37 38 39 3A 3B 3C 3D 3E  /0123456789:;<=>
              0020  3F 40 41 42 43 44 45 46 47 48 49 4A 4B 4C 4D 4E  ?@ABCDEFGHIJKLMN
              0030  4F 50 51 52 53 54 55 56 57 58 59 5A 5B 5C 5D FE  OPQRSTUVWXYZ[\].
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_data_with_tzx_file(self):
        blocks = []
        blocks.append(create_tzx_header_block('test_tzx02', data_type=0))
        blocks.append(create_tzx_data_block([1, 4, 16]))

        # Turbo speed data
        data = list(range(48, 94))
        block = [0x11] # Block ID
        block.extend([1] * 15)
        data_block = create_data_block(data)
        block.extend((len(data_block), 0, 0))
        block.extend(data_block)
        blocks.append(block)

        # Pure data
        data = [65, 66, 67, 68]
        block = [0x14]       # Block ID
        block.extend((1, 2)) # Length of 0-pulse
        block.extend((3, 4)) # Length of 1-pulse
        block.append(4)      # Used bits in last byte
        block.extend((5, 6)) # Pause length
        block.extend((len(data), 0, 0))
        block.extend(data)
        blocks.append(block)

        tzxfile = self._write_tzx(blocks)
        output, error = self.run_tapinfo('-d {}'.format(tzxfile))
        self.assertEqual(error, '')
        exp_output = r"""
            Version: 1.20
            1: Standard speed data (0x10)
              Pause: 0ms
              Type: Header block
              Program: test_tzx02
              LINE: 0
              Length: 19
              0000  00 00 74 65 73 74 5F 74 7A 78 30 32 00 00 00 00  ..test_tzx02....
              0010  00 00 3D                                         ..=
            2: Standard speed data (0x10)
              Pause: 0ms
              Type: Data block
              Length: 5
              0000  FF 01 04 10 EA                                   .....
            3: Turbo speed data (0x11)
              Pilot pulse: 257
              Sync pulse 1: 257
              Sync pulse 2: 257
              0-pulse: 257
              1-pulse: 257
              Pilot length: 257 pulses
              Used bits in last byte: 1
              Pause: 257ms
              Length: 48
              0000  FF 30 31 32 33 34 35 36 37 38 39 3A 3B 3C 3D 3E  .0123456789:;<=>
              0010  3F 40 41 42 43 44 45 46 47 48 49 4A 4B 4C 4D 4E  ?@ABCDEFGHIJKLMN
              0020  4F 50 51 52 53 54 55 56 57 58 59 5A 5B 5C 5D FE  OPQRSTUVWXYZ[\].
            4: Pure data (0x14)
              0-pulse: 513
              1-pulse: 1027
              Used bits in last byte: 4
              Pause: 1541ms
              Length: 4
              0000  41 42 43 44                                      ABCD
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_start_with_pzx_file(self):
        pzx = PZX()
        pzx.add_puls()
        pzx.add_data(create_header_block('test_start', 32768, 3))
        pzx.add_puls()
        pzx.add_data(create_data_block([1, 2, 3]))
        pzx.add_puls()
        pzx.add_data(create_data_block([4, 5, 6]))
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tapinfo(f'--tape-start 4 {pzxfile}')
        self.assertEqual(error, '')
        exp_output = """
            4: Pulse sequence
              3223 x 2168 T-states
              1 x 667 T-states
              1 x 735 T-states
            5: Data block
              Bits: 40 (5 bytes)
              Initial pulse level: 1
              0-bit pulse sequence: 855, 855 (T-states)
              1-bit pulse sequence: 1710, 1710 (T-states)
              Tail pulse: 945 T-states
              Type: Data block
              Length: 5
              Data: 255, 1, 2, 3, 255
            6: Pulse sequence
              3223 x 2168 T-states
              1 x 667 T-states
              1 x 735 T-states
            7: Data block
              Bits: 40 (5 bytes)
              Initial pulse level: 1
              0-bit pulse sequence: 855, 855 (T-states)
              1-bit pulse sequence: 1710, 1710 (T-states)
              Tail pulse: 945 T-states
              Type: Data block
              Length: 5
              Data: 255, 4, 5, 6, 248
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_stop_with_pzx_file(self):
        pzx = PZX()
        pzx.add_puls()
        pzx.add_data(create_header_block('test__stop', 32768, 3))
        pzx.add_puls()
        pzx.add_data(create_data_block([1, 2, 3]))
        pzx.add_puls()
        pzx.add_data(create_data_block([4, 5, 6]))
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tapinfo(f'--tape-stop 6 {pzxfile}')
        self.assertEqual(error, '')
        exp_output = """
            1: PZX header block
              Version: 1.0
            2: Pulse sequence
              3223 x 2168 T-states
              1 x 667 T-states
              1 x 735 T-states
            3: Data block
              Bits: 152 (19 bytes)
              Initial pulse level: 1
              0-bit pulse sequence: 855, 855 (T-states)
              1-bit pulse sequence: 1710, 1710 (T-states)
              Tail pulse: 945 T-states
              Type: Header block
              Bytes: test__stop
              CODE: 32768,3
              Length: 19
              Data: 0, 3, 116, 101, 115, 116, 95 ... 3, 0, 0, 128, 0, 0, 142
            4: Pulse sequence
              3223 x 2168 T-states
              1 x 667 T-states
              1 x 735 T-states
            5: Data block
              Bits: 40 (5 bytes)
              Initial pulse level: 1
              0-bit pulse sequence: 855, 855 (T-states)
              1-bit pulse sequence: 1710, 1710 (T-states)
              Tail pulse: 945 T-states
              Type: Data block
              Length: 5
              Data: 255, 1, 2, 3, 255
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_options_tape_start_and_tape_stop_with_pzx_file(self):
        pzx = PZX()
        pzx.add_puls()
        pzx.add_data(create_header_block('test__both', 32768, 3))
        pzx.add_puls()
        pzx.add_data(create_data_block([1, 2, 3]))
        pzx.add_puls()
        pzx.add_data(create_data_block([4, 5, 6]))
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        output, error = self.run_tapinfo(f'--tape-start 4 --tape-stop 6 {pzxfile}')
        self.assertEqual(error, '')
        exp_output = """
            4: Pulse sequence
              3223 x 2168 T-states
              1 x 667 T-states
              1 x 735 T-states
            5: Data block
              Bits: 40 (5 bytes)
              Initial pulse level: 1
              0-bit pulse sequence: 855, 855 (T-states)
              1-bit pulse sequence: 1710, 1710 (T-states)
              Tail pulse: 945 T-states
              Type: Data block
              Length: 5
              Data: 255, 1, 2, 3, 255
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_start_with_tap_file(self):
        tap_data = create_tap_header_block('test_start', 32768, 3)
        tap_data.extend(create_tap_data_block([1, 2, 3]))
        tap_data.extend(create_tap_data_block([4, 5, 6]))
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        output, error = self.run_tapinfo(f'--tape-start 2 {tapfile}')
        self.assertEqual(error, '')
        exp_output = """
            2:
              Type: Data block
              Length: 5
              Data: 255, 1, 2, 3, 255
            3:
              Type: Data block
              Length: 5
              Data: 255, 4, 5, 6, 248
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_stop_with_tap_file(self):
        tap_data = create_tap_header_block('test__stop', 32768, 3)
        tap_data.extend(create_tap_data_block([1, 2, 3]))
        tap_data.extend(create_tap_data_block([4, 5, 6]))
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        output, error = self.run_tapinfo(f'--tape-stop 3 {tapfile}')
        self.assertEqual(error, '')
        exp_output = """
            1:
              Type: Header block
              Bytes: test__stop
              CODE: 32768,3
              Length: 19
              Data: 0, 3, 116, 101, 115, 116, 95 ... 3, 0, 0, 128, 0, 0, 142
            2:
              Type: Data block
              Length: 5
              Data: 255, 1, 2, 3, 255
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_options_tape_start_and_tape_stop_with_tap_file(self):
        tap_data = create_tap_header_block('test__both', 32768, 3)
        tap_data.extend(create_tap_data_block([1, 2, 3]))
        tap_data.extend(create_tap_data_block([4, 5, 6]))
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        output, error = self.run_tapinfo(f'--tape-start 2 --tape-stop 3 {tapfile}')
        self.assertEqual(error, '')
        exp_output = """
            2:
              Type: Data block
              Length: 5
              Data: 255, 1, 2, 3, 255
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_start_with_tzx_file(self):
        tzxfile = self._write_tzx((
            create_tzx_header_block('test_start', 32768, 3),
            create_tzx_data_block([1, 2, 3]),
            create_tzx_data_block([4, 5, 6])
        ))
        output, error = self.run_tapinfo(f'--tape-start 2 {tzxfile}')
        self.assertEqual(error, '')
        exp_output = """
            Version: 1.20
            2: Standard speed data (0x10)
              Pause: 0ms
              Type: Data block
              Length: 5
              Data: 255, 1, 2, 3, 255
            3: Standard speed data (0x10)
              Pause: 0ms
              Type: Data block
              Length: 5
              Data: 255, 4, 5, 6, 248
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_tape_stop_with_tzx_file(self):
        tzxfile = self._write_tzx((
            create_tzx_header_block('test__stop', 32768, 3),
            create_tzx_data_block([1, 2, 3]),
            create_tzx_data_block([4, 5, 6])
        ))
        output, error = self.run_tapinfo(f'--tape-stop 3 {tzxfile}')
        self.assertEqual(error, '')
        exp_output = """
            Version: 1.20
            1: Standard speed data (0x10)
              Pause: 0ms
              Type: Header block
              Bytes: test__stop
              CODE: 32768,3
              Length: 19
              Data: 0, 3, 116, 101, 115, 116, 95 ... 3, 0, 0, 128, 0, 0, 142
            2: Standard speed data (0x10)
              Pause: 0ms
              Type: Data block
              Length: 5
              Data: 255, 1, 2, 3, 255
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_options_tape_start_and_tape_stop_with_tzx_file(self):
        tzxfile = self._write_tzx((
            create_tzx_header_block('test__both', 32768, 3),
            create_tzx_data_block([1, 2, 3]),
            create_tzx_data_block([4, 5, 6])
        ))
        output, error = self.run_tapinfo(f'--tape-start 2 --tape-stop 3 {tzxfile}')
        self.assertEqual(error, '')
        exp_output = """
            Version: 1.20
            2: Standard speed data (0x10)
              Pause: 0ms
              Type: Data block
              Length: 5
              Data: 255, 1, 2, 3, 255
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_tapinfo(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))
