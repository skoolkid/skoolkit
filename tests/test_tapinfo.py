from textwrap import dedent
from unittest.mock import patch

from skoolkittest import (SkoolKitTestCase, create_data_block,
                          create_tap_header_block, create_tap_data_block,
                          create_tzx_header_block, create_tzx_data_block)
from skoolkit import SkoolKitError, tapinfo, get_word, VERSION

TZX_DATA_BLOCK = (16, 0, 0, 3, 0, 255, 0, 0)

TZX_DATA_BLOCK_DESC = """
{}: Standard speed data (0x10)
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
    def _write_tzx(self, blocks):
        tzx_data = [ord(c) for c in "ZXTape!"]
        tzx_data.extend((26, 1, 20))
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

    def test_tap_file(self):
        data = [1, 2, 4]
        tap_data = create_tap_header_block('test_tap01', 32768, len(data))
        tap_data.extend(create_tap_data_block(data))
        tap_data.extend(create_tap_header_block('numbers_01', data_type=1))
        tap_data.extend(create_tap_data_block([8, 16, 32]))
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        output, error = self.run_tapinfo(tapfile)
        self.assertEqual(error, '')
        exp_output = """
            1:
              Type: Header block
              Bytes: test_tap01
              CODE: 32768,3
              Length: 19
              Data: 0, 3, 116, 101, 115, 116, 95 ... 3, 0, 0, 128, 0, 0, 173
            2:
              Type: Data block
              Length: 5
              Data: 255, 1, 2, 4, 7
            3:
              Type: Header block
              Number array: numbers_01
              Length: 19
              Data: 0, 1, 110, 117, 109, 98, 101 ... 0, 0, 0, 0, 0, 0, 47
            4:
              Type: Data block
              Length: 5
              Data: 255, 8, 16, 32, 56
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_tzx_file(self):
        blocks = []
        blocks.append(create_tzx_header_block('<TEST_tzx>', data_type=0))
        blocks.append(create_tzx_data_block([1, 4, 16]))
        blocks.append(create_tzx_header_block('characters', data_type=2))
        blocks.append(create_tzx_data_block([64, 0]))

        tzxfile = self._write_tzx(blocks)
        output, error = self.run_tapinfo(tzxfile)
        self.assertEqual(error, '')
        exp_output = """
            Version: 1.20
            1: Standard speed data (0x10)
              Type: Header block
              Program: <TEST_tzx>
              Length: 19
              Data: 0, 0, 60, 84, 69, 83, 84 ... 0, 0, 0, 0, 0, 0, 61
            2: Standard speed data (0x10)
              Type: Data block
              Length: 5
              Data: 255, 1, 4, 16, 21
            3: Standard speed data (0x10)
              Type: Header block
              Character array: characters
              Length: 19
              Data: 0, 2, 99, 104, 97, 114, 97 ... 0, 0, 0, 0, 0, 0, 8
            4: Standard speed data (0x10)
              Type: Data block
              Length: 4
              Data: 255, 64, 0, 64
        """
        self.assertEqual(dedent(exp_output).lstrip(), output)

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
        self.assertEqual(cm.exception.args[0], 'Unknown block ID: 0x{:02X}'.format(block_id))

    def test_tzx_block_0x11(self):
        data = [0, 1, 2]
        block = [17] # Block ID
        block.extend([0] * 15)
        data_block = create_data_block(data)
        block.extend((len(data_block), 0, 0))
        block.extend(data_block)
        exp_output = """
            1: Turbo speed data (0x11)
              Length: 5
              Data: 255, 0, 1, 2, 3
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
        block = [21] # Block ID
        block.extend([0] * 5)
        block.extend((2, 0, 0)) # Length of samples
        block.extend((128, 12)) # Samples
        exp_output = '1: Direct recording (0x15)'
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x18(self):
        block = [24] # Block ID
        block.extend((12, 0, 0, 0)) # Block length
        block.extend([0] * 10)
        block.extend((1, 1)) # CSW data
        exp_output = '1: CSW recording (0x18)'
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

    def test_tzx_block_0x2B(self):
        block = [43] # Block ID
        block.extend((1, 0, 0, 0))
        block.append(0) # Signal level
        exp_output = '1: Set signal level (0x2B)'
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
        block = [51] # Block ID
        block.append(2) # Number of machines
        block.extend([0] * (3 * block[1]))
        exp_output = '1: Hardware type (0x33)'
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x35(self):
        block = [53] # Block ID
        info_id = 'Custom Info'
        block.extend([ord(c) for c in info_id[:16].ljust(16)])
        block.extend((1, 0, 0, 0)) # Length of custom info
        block.append(0) # Custom info
        exp_output = '1: Custom info (0x35)'
        self._test_tzx_block(block, exp_output)

    def test_tzx_block_0x5A(self):
        block = [90] # Block ID
        block.extend([0] * 9)
        exp_output = '1: "Glue" block (0x5A)'
        self._test_tzx_block(block, exp_output)

    def test_option_b(self):
        blocks = []

        blocks.append(create_tzx_data_block([0, 1]))

        block2 = [17] # Block ID (0x11)
        block2.extend([0] * 15)
        data = [2, 3]
        data_block = create_data_block(data)
        block2.extend((len(data_block), 0, 0))
        block2.extend(data_block)
        blocks.append(block2)

        block3 = [42] # Block ID (0x2A)
        block3.extend((0, 0, 0, 0))
        blocks.append(block3)

        tzxfile = self._write_tzx(blocks)
        exp_output = """
            Version: 1.20
            1: Standard speed data (0x10)
              Type: Data block
              Length: 4
              Data: 255, 0, 1, 1
            3: Stop the tape if in 48K mode (0x2A)
        """

        for option in ('-b', '--tzx-blocks'):
            output, error = self.run_tapinfo('{} 10,2a {}'.format(option, tzxfile))
            self.assertEqual(error, '')
            self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_b_with_invalid_block_id(self):
        blocks = []

        blocks.append(create_tzx_data_block([0, 1]))

        block2 = [42] # Block ID (0x2A)
        block2.extend((0, 0, 0, 0))
        blocks.append(block2)

        tzxfile = self._write_tzx(blocks)
        exp_output = """
            Version: 1.20
            1: Standard speed data (0x10)
              Type: Data block
              Length: 4
              Data: 255, 0, 1, 1
        """

        output, error = self.run_tapinfo('-b 10,2z {}'.format(tzxfile))
        self.assertEqual(error, '')
        self.assertEqual(dedent(exp_output).lstrip(), output)

    def test_option_b_with_single_invalid_block_id(self):
        blocks = []

        block1 = [42] # Block ID (0x2A)
        block1.extend((0, 0, 0, 0))
        blocks.append(block1)

        tzxfile = self._write_tzx(blocks)

        output, error = self.run_tapinfo('-b 2z {}'.format(tzxfile))
        self.assertEqual(error, '')
        self.assertEqual(output, 'Version: 1.20\n')

    @patch.object(tapinfo, 'BasicLister', MockBasicLister)
    def test_option_B_tap(self):
        prog = [10] * 10
        tap_data = create_tap_data_block(prog)
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        exp_snapshot = [0] * 23755 + prog
        output, error = self.run_tapinfo('-B 1 {}'.format(tapfile))
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
    def test_option_B_tap_with_hex_address(self):
        prefix = [4] * 4
        address = 23755 - len(prefix)
        prog = [9] * 9
        data = prefix + prog
        tap_data = create_tap_data_block(data)
        tapfile = self.write_bin_file(tap_data, suffix='.tap')
        exp_snapshot = [0] * address + data
        output, error = self.run_tapinfo('-B 1,0x{:04x} {}'.format(address, tapfile))
        self.assertEqual(error, '')
        self.assertEqual(output, 'BASIC DONE!\n')
        self.assertEqual(exp_snapshot, mock_basic_lister.snapshot)

    def test_option_B_with_invalid_block_spec(self):
        exp_error = 'Invalid block specification'
        self._test_bad_spec('-B', 'q', exp_error)
        self._test_bad_spec('--basic', '1,z', exp_error)
        self._test_bad_spec('-B', '1,2,3', exp_error)
        self._test_bad_spec('--basic', '?,+', exp_error)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_tapinfo(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))
