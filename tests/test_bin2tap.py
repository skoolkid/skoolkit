import os
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import components, bin2tap, SkoolKitError, VERSION

def mock_run(*args):
    global run_args
    run_args = args

def mock_write_tape(fname, blocks):
    global tape_fname, tape_blocks
    tape_fname = fname
    tape_blocks = blocks

class Bin2TapTest(SkoolKitTestCase):
    @patch.object(bin2tap, 'write_tap', mock_write_tape)
    def _run(self, args, tape_file=None):
        if tape_file is None:
            tape_file = args.split()[-1][:-4] + '.tap'
        output, error = self.run_bin2tap(args)
        self.assertEqual(output, '')
        self.assertEqual(error, '')
        self.assertEqual(tape_fname, tape_file)
        return tape_blocks

    def _get_word(self, num):
        return (num % 256, num // 256)

    def _get_parity(self, data):
        parity = 0
        for b in data:
            parity ^= b
        return parity

    def _get_str(self, chars):
        return [ord(c) for c in chars]

    def _check_tape(self, blocks, bin_data, infile, org=None, start=None, stack=None, name=None, scr=None):
        if org is None:
            org = 65536 - len(bin_data)
        if start is None:
            start = org
        if stack is None:
            stack = org
        if name is None:
            if infile == '-':
                name = 'program'
            else:
                name = os.path.basename(infile)
                if name.lower().endswith(('.bin', '.sna', '.szx', '.z80')):
                    name = name[:-4]
        title = [ord(c) for c in name[:10].ljust(10)]

        # BASIC loader header
        loader_length = 20
        exp_header = [0, 0]
        exp_header += title
        exp_header += [loader_length, 0, 10, 0, loader_length, 0]
        exp_header.append(self._get_parity(exp_header))
        self.assertEqual(exp_header, blocks[0])

        # BASIC loader data
        start_addr = self._get_str('"23296"')
        exp_data = [255, 0, 10, 16, 0]
        exp_data += [239, 34, 34, 175, 58]        # LOAD ""CODE :
        exp_data += [249, 192, 176] + start_addr  # RANDOMIZE USR VAL "23296"
        exp_data.append(13)                       # ENTER
        exp_data.append(self._get_parity(exp_data))
        self.assertEqual(exp_data, blocks[1])

        # Code loader header
        exp_header = [0, 3] + title
        if scr:
            exp_header += [19, 27, 0, 64]
        else:
            exp_header += [19, 0, 0, 91]
        exp_header += [0, 0]
        exp_header.append(self._get_parity(exp_header))
        self.assertEqual(exp_header, blocks[2])

        # Code loader data
        exp_data = [255]
        if scr:
            exp_data.extend(scr)
        exp_data += [221, 33]
        exp_data.extend(self._get_word(org))
        exp_data.append(17)
        exp_data.extend(self._get_word(len(bin_data)))
        exp_data += [55, 159, 49]
        exp_data.extend(self._get_word(stack))
        exp_data.append(1)
        exp_data.extend(self._get_word(start))
        exp_data += [197, 195, 86, 5]
        exp_data.append(self._get_parity(exp_data))
        self.assertEqual(exp_data, blocks[3])

        # Data
        exp_data = [255]
        exp_data.extend(bin_data)
        exp_data.append(self._get_parity(exp_data))
        self.assertEqual(exp_data, blocks[4])

    def _check_tape_with_clear_command(self, blocks, bin_data, infile, clear, org=None, start=None, scr=None):
        if org is None:
            org = 65536 - len(bin_data)
        if start is None:
            start = org

        name = os.path.basename(infile)
        if name.lower().endswith(('.bin', '.sna', '.szx', '.z80')):
            name = name[:-4]
        title = self._get_str(name[:10].ljust(10))

        # BASIC loader data
        exp_data = [255]
        clear_addr = self._get_str('"{}"'.format(clear))
        start_addr = self._get_str('"{}"'.format(start))
        line_length = 12 + len(clear_addr) + len(start_addr)
        if scr:
            line_length += 20
        exp_data += [0, 10, line_length, 0]
        exp_data += [253, 176] + clear_addr       # CLEAR VAL "address"
        exp_data.append(58)                       # :
        if scr:
            poke_addr = self._get_str('"23739"')
            exp_data.extend((239, 34, 34, 170))   # LOAD ""SCREEN$
            exp_data.append(58)                   # :
            exp_data.extend((244, 176))           # POKE VAL
            exp_data.extend(poke_addr)            # "23739"
            exp_data.append(44)                   # ,
            exp_data.extend((175, 34, 111, 34))   # CODE "o"
            exp_data.append(58)                   # :
        exp_data += [239, 34, 34, 175]            # LOAD ""CODE
        exp_data.append(58)                       # :
        exp_data += [249, 192, 176] + start_addr  # RANDOMIZE USR VAL "address"
        exp_data.append(13)                       # ENTER
        exp_data.append(self._get_parity(exp_data))
        loader_length = len(exp_data) - 2
        self.assertEqual(exp_data, blocks[1])

        # BASIC loader header
        exp_header = [0, 0]
        exp_header += title
        exp_header += self._get_word(loader_length)
        exp_header += [10, 0]
        exp_header += self._get_word(loader_length)
        exp_header.append(self._get_parity(exp_header))
        self.assertEqual(exp_header, blocks[0])

        index = 2
        if scr:
            # Loading screen header
            exp_header = [0, 3]
            exp_header.extend(title)
            exp_header.extend(self._get_word(6912))
            exp_header.extend(self._get_word(16384))
            exp_header.extend((0, 0))
            exp_header.append(self._get_parity(exp_header))
            self.assertEqual(exp_header, blocks[2])

            # Loading screen data
            exp_data = [255]
            exp_data.extend(scr)
            exp_data.append(self._get_parity(exp_data))
            self.assertEqual(exp_data, blocks[3])
            index = 4

        # Code loader header
        exp_header = [0, 3]
        exp_header += title
        exp_header += self._get_word(len(bin_data))
        exp_header += self._get_word(org)
        exp_header += [0, 0]
        exp_header.append(self._get_parity(exp_header))
        self.assertEqual(exp_header, blocks[index])
        index += 1

        # Data
        exp_data = [255]
        exp_data.extend(bin_data)
        exp_data.append(self._get_parity(exp_data))
        self.assertEqual(exp_data, blocks[index])

    def _check_tape_with_ram_banks(self, blocks, bin_data, banks, out7ffd, infile, clear, begin, start=None, loader=None, scr=None):
        if start is None:
            start = begin
        if loader is None:
            loader = clear + 1

        name = os.path.basename(infile)
        if name.lower().endswith(('.bin', '.sna', '.szx', '.z80')):
            name = name[:-4]
        title = self._get_str(name[:10].ljust(10))

        # BASIC loader data
        exp_data = [255]
        clear_addr = self._get_str(f'"{clear}"')
        loader_addr = self._get_str(f'"{loader}"')
        line_length = 17 + len(clear_addr) + len(loader_addr)
        if scr:
            line_length += 20
        exp_data += [0, 10, line_length, 0]
        exp_data += [253, 176] + clear_addr       # CLEAR VAL "address"
        exp_data.append(58)                       # :
        if scr:
            poke_addr = self._get_str('"23739"')
            exp_data.extend((239, 34, 34, 170))   # LOAD ""SCREEN$
            exp_data.append(58)                   # :
            exp_data.extend((244, 176))           # POKE VAL
            exp_data.extend(poke_addr)            # "23739"
            exp_data.append(44)                   # ,
            exp_data.extend((175, 34, 111, 34))   # CODE "o"
            exp_data.append(58)                   # :
        exp_data += [239, 34, 34, 175]            # LOAD ""CODE
        exp_data.append(58)                       # :
        exp_data += [239, 34, 34, 175]            # LOAD ""CODE
        exp_data.append(58)                       # :
        exp_data += [249, 192, 176] + loader_addr # RANDOMIZE USR VAL "address"
        exp_data.append(13)                       # ENTER
        exp_data.append(self._get_parity(exp_data))
        loader_length = len(exp_data) - 2
        self.assertEqual(exp_data, blocks[1])

        # BASIC loader header
        exp_header = [0, 0]
        exp_header.extend(title)
        exp_header.extend(self._get_word(loader_length))
        exp_header.extend((10, 0))
        exp_header.extend(self._get_word(loader_length))
        exp_header.append(self._get_parity(exp_header))
        self.assertEqual(exp_header, blocks[0])

        index = 2
        if scr:
            # Loading screen header
            exp_header = [0, 3]
            exp_header.extend(title)
            exp_header.extend(self._get_word(6912))
            exp_header.extend(self._get_word(16384))
            exp_header.extend((0, 0))
            exp_header.append(self._get_parity(exp_header))
            self.assertEqual(exp_header, blocks[2])

            # Loading screen data
            exp_data = [255]
            exp_data.extend(scr)
            exp_data.append(self._get_parity(exp_data))
            self.assertEqual(exp_data, blocks[3])
            index = 4

        # Main code header
        exp_header = [0, 3]
        exp_header.extend(title)
        exp_header.extend(self._get_word(len(bin_data)))
        exp_header.extend(self._get_word(begin))
        exp_header.extend((0, 0))
        exp_header.append(self._get_parity(exp_header))
        self.assertEqual(exp_header, blocks[index])
        index += 1

        # Main code data
        exp_data = [255]
        exp_data.extend(bin_data)
        exp_data.append(self._get_parity(exp_data))
        self.assertEqual(exp_data, blocks[index])
        index += 1

        table_addr = ((loader + 38) % 256, (loader + 38) // 256)
        start_addr = (start % 256, start // 256)
        exp_loader = [
            0x21, *table_addr,      #      LD HL,TABLE
            0x01, 0xFD, 0x7F,       # LOOP LD BC,$7FFD
            0x7E,                   #      LD A,(HL)
            0xE6, 0x3F,             #      AND $3F
            0xF3,                   #      DI
            0xED, 0x79,             #      OUT (C),A
            0x32, 0x5C, 0x5B,       #      LD ($5B5C),A
            0xFB,                   #      EI
            0xCB, 0x7E,             #      BIT 7,(HL)
            0xC2, *start_addr,      #      JP NZ,START
            0xE5,                   #      PUSH HL
            0xDD, 0x21, 0x00, 0xC0, #      LD IX,$C000
            0x11, 0x00, 0x40,       #      LD DE,$4000
            0x37,                   #      SCF
            0x9F,                   #      SBC A,A
            0xCD, 0x56, 0x05,       #      CALL $0556
            0xE1,                   #      POP HL
            0x23,                   #      INC HL
            0x18, 0xDD,             #      JR LOOP
        ]
        for bank, bank_data in banks:
            exp_loader.append(bank | 0x10)
        exp_loader.append(out7ffd | 0x80)

        # RAM bank loader header
        exp_header = [0, 3]
        exp_header.extend(title)
        exp_header.extend(self._get_word(len(exp_loader)))
        exp_header.extend(self._get_word(loader))
        exp_header.extend((0, 0))
        exp_header.append(self._get_parity(exp_header))
        self.assertEqual(exp_header, blocks[index])
        index += 1

        # RAM bank loader data
        exp_data = [255]
        exp_data.extend(exp_loader)
        exp_data.append(self._get_parity(exp_data))
        self.assertEqual(exp_data, blocks[index])
        index += 1

        # RAM banks
        for bank, bank_data in banks:
            exp_data = [255]
            exp_data.extend(bank_data)
            exp_data.append(self._get_parity(exp_data))
            self.assertEqual(exp_data, blocks[index])
            index += 1

    @patch.object(bin2tap, 'run', mock_run)
    def test_default_option_values(self):
        data = [0] * 10
        binfile = self.write_bin_file(data, suffix='.bin')
        bin2tap.main((binfile,))
        ram, clear, org, start, stack, tapfile, scr, banks, out7ffd, loader_addr = run_args
        self.assertEqual(ram, bytearray(data))
        self.assertIsNone(clear)
        self.assertEqual(org, 65536 - len(data))
        self.assertEqual(start, org)
        self.assertEqual(stack, org)
        self.assertEqual(tapfile, binfile[:-4] + '.tap')
        self.assertIsNone(scr)
        self.assertIsNone(banks)
        self.assertIsNone(out7ffd)
        self.assertIsNone(loader_addr)

    def test_no_arguments(self):
        output, error = self.run_bin2tap(catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: bin2tap.py'))

    def test_invalid_option(self):
        output, error = self.run_bin2tap('-x test_invalid_option.bin', catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: bin2tap.py'))

    def test_invalid_option_value(self):
        binfile = self.write_bin_file(suffix='.bin')
        for option in ('-o ABC', '-s =', '-p q'):
            output, error = self.run_bin2tap('{0} {1}'.format(option, binfile), catch_exit=2)
            self.assertEqual(output, '')
            self.assertTrue(error.startswith('usage: bin2tap.py'))

    def test_empty_bin(self):
        binfile = self.write_bin_file(suffix='.bin')
        with self.assertRaisesRegex(SkoolKitError, '^{} is empty$'.format(binfile)):
            self.run_bin2tap(binfile)

    def test_bin_with_invalid_org_and_begin_and_end_addresses(self):
        binfile = self.write_bin_file([0], suffix='.bin')
        with self.assertRaisesRegex(SkoolKitError, r'^Input is empty \(ORG=32768, BEGIN=65535, END=32769\)$'):
            self.run_bin2tap('-o 32768 -b 65535 {}'.format(binfile))
        with self.assertRaisesRegex(SkoolKitError, r'^Input is empty \(ORG=32768, BEGIN=32768, END=24576\)$'):
            self.run_bin2tap('-o 32768 -e 24576 {}'.format(binfile))
        with self.assertRaisesRegex(SkoolKitError, r'^Input is empty \(ORG=32768, BEGIN=32768, END=32768\)$'):
            self.run_bin2tap('-o 32768 -b 32768 -e 32768 {}'.format(binfile))
        with self.assertRaisesRegex(SkoolKitError, r'^Input is empty \(ORG=32768, BEGIN=23296, END=23297\)$'):
            self.run_bin2tap('-o 32768 -b 23296 -e 23297 {}'.format(binfile))
        with self.assertRaisesRegex(SkoolKitError, r'^Input is empty \(ORG=32768, BEGIN=49152, END=49153\)$'):
            self.run_bin2tap('-o 32768 -b 49152 -e 49153 {}'.format(binfile))

    def test_snapshot_with_invalid_begin_and_end_addresses(self):
        snafile = self.write_bin_file([0] * 49179, suffix='.sna')
        with self.assertRaisesRegex(SkoolKitError, r'^Input is empty \(ORG=0, BEGIN=65536, END=65536\)$'):
            self.run_bin2tap('-b 65536 {}'.format(snafile))
        with self.assertRaisesRegex(SkoolKitError, r'^Input is empty \(ORG=0, BEGIN=16384, END=16384\)$'):
            self.run_bin2tap('-e 16384 {}'.format(snafile))
        with self.assertRaisesRegex(SkoolKitError, r'^Input is empty \(ORG=0, BEGIN=32768, END=24576\)$'):
            self.run_bin2tap('-b 32768 -e 24576 {}'.format(snafile))

    def test_no_options(self):
        bin_data = [1, 2, 3, 4, 5]
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        blocks = self._run(binfile)
        self._check_tape(blocks, bin_data, binfile)

    @patch.object(bin2tap, 'write_pzx', mock_write_tape)
    def test_write_pzx(self):
        bin_data = [1, 2, 3, 4, 5]
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        pzxfile = 'out.pzx'
        blocks = self._run(f'{binfile} {pzxfile}', pzxfile)
        self._check_tape(blocks, bin_data, binfile, name=pzxfile[:-4])

    def test_nonstandard_bin_name(self):
        bin_data = [0]
        binfile = self.write_bin_file(bin_data, suffix='.ram')
        tapfile = '{0}.tap'.format(binfile)
        blocks = self._run(binfile, tapfile)
        self._check_tape(blocks, bin_data, binfile)

    @patch.object(bin2tap, 'write_tap', mock_write_tape)
    def test_bin_in_subdirectory(self):
        tapfile = self.write_bin_file(suffix='.tap')
        bin_data = [1]
        binfile = self.write_bin_file(bin_data, '{}/{}.bin'.format(self.make_directory(), tapfile[:-4]))
        output, error = self.run_bin2tap(binfile)
        self.assertEqual(output, '')
        self.assertEqual(error, '')
        self._check_tape(tape_blocks, bin_data, binfile)

    @patch.object(bin2tap, 'write_tap', mock_write_tape)
    def test_nonstandard_bin_name_in_subdirectory(self):
        tapfile = self.write_bin_file(suffix='.ram.tap')
        bin_data = [1]
        binfile = self.write_bin_file(bin_data, '{}/{}'.format(self.make_directory(), tapfile[:-4]))
        output, error = self.run_bin2tap(binfile)
        self.assertEqual(output, '')
        self.assertEqual(error, '')
        self._check_tape(tape_blocks, bin_data, binfile)

    def test_read_from_standard_input(self):
        bin_data = [1, 2, 3]
        self.write_stdin(bytearray(bin_data))
        binfile = '-'
        blocks = self._run(binfile, 'program.tap')
        self._check_tape(blocks, bin_data, binfile)

    def test_specified_tapfile(self):
        bin_data = [4, 5, 6]
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        tapfile = '{}.tap'.format(os.getpid())
        blocks = self._run('{} {}'.format(binfile, tapfile), tapfile)
        self._check_tape(blocks, bin_data, binfile, name=tapfile[:-4])

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_bin2tap(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))

    def test_option_7ffd(self):
        data = [1, 2, 3]
        begin = 40000
        end = begin + len(data)
        clear = 32767
        out7ffd = 0
        ram = [0] * 49152
        ram[begin - 16384:begin - 16384 + len(data)] = data
        sna_data = [0] * 27 + ram
        sna_data.extend((
            0, 0,    # PC
            out7ffd, # Port 0x7ffd
            0        # TR-DOS ROM
        ))
        banks = []
        for bank in (0, 1, 3, 4, 6, 7):
            if bank == out7ffd % 8:
                banks.append((bank, ram[32768:]))
            else:
                banks.append((bank, [bank] * 16384))
                sna_data.extend(banks[-1][1])
        sna = self.write_bin_file(sna_data, suffix='.sna')
        blocks = self._run(f'-b {begin} -e {end} -c {clear} --7ffd {out7ffd} {sna}')
        self._check_tape_with_ram_banks(blocks, data, banks, out7ffd, sna, clear, begin)

    def test_option_7ffd_with_start_address(self):
        data = [128, 129, 130]
        begin = 40000
        end = begin + len(data)
        clear = 32767
        start = 50000
        out7ffd = 4
        ram = [0] * 32768 + [4] * 16384
        ram[begin - 16384:begin - 16384 + len(data)] = data
        sna_data = [0] * 27 + ram
        sna_data.extend((
            0, 0,    # PC
            out7ffd, # Port 0x7ffd
            0        # TR-DOS ROM
        ))
        banks = []
        for bank in (0, 1, 3, 4, 6, 7):
            if bank == out7ffd % 8:
                banks.append((bank, ram[32768:]))
            else:
                banks.append((bank, [bank] * 16384))
                sna_data.extend(banks[-1][1])
        sna = self.write_bin_file(sna_data, suffix='.sna')
        blocks = self._run(f'-b {begin} -e {end} -c {clear} -s {start} --7ffd {out7ffd} {sna}')
        self._check_tape_with_ram_banks(blocks, data, banks, out7ffd, sna, clear, begin, start)

    def test_option_7ffd_with_loader_address(self):
        data = [255, 254, 253]
        begin = 40000
        end = begin + len(data)
        clear = 32767
        loader = 35000
        out7ffd = 6
        ram = [0] * 32768 + [6] * 16384
        ram[begin - 16384:begin - 16384 + len(data)] = data
        sna_data = [0] * 27 + ram
        sna_data.extend((
            0, 0,    # PC
            out7ffd, # Port 0x7ffd
            0        # TR-DOS ROM
        ))
        banks = []
        for bank in (0, 1, 3, 4, 6, 7):
            if bank == out7ffd % 8:
                banks.append((bank, ram[32768:]))
            else:
                banks.append((bank, [bank] * 16384))
                sna_data.extend(banks[-1][1])
        sna = self.write_bin_file(sna_data, suffix='.sna')
        blocks = self._run(f'-b {begin} -e {end} -c {clear} --loader {loader} --7ffd {out7ffd} {sna}')
        self._check_tape_with_ram_banks(blocks, data, banks, out7ffd, sna, clear, begin, loader=loader)

    def test_option_7ffd_with_loading_screen(self):
        data = [50, 100, 150]
        begin = 40000
        end = begin + len(data)
        clear = 24576
        out7ffd = 3
        ram = [85] * 6912 + [0] * 25856 + [3] * 16384
        ram[begin - 16384:begin - 16384 + len(data)] = data
        sna_data = [0] * 27 + ram
        sna_data.extend((
            0, 0,    # PC
            out7ffd, # Port 0x7ffd
            0        # TR-DOS ROM
        ))
        banks = []
        for bank in (0, 1, 3, 4, 6, 7):
            if bank == out7ffd % 8:
                banks.append((bank, ram[32768:]))
            else:
                banks.append((bank, [bank] * 16384))
                sna_data.extend(banks[-1][1])
        sna = self.write_bin_file(sna_data, suffix='.sna')
        blocks = self._run(f'-b {begin} -e {end} -c {clear} -S {sna} --7ffd {out7ffd} {sna}')
        scr = ram[:6912]
        self._check_tape_with_ram_banks(blocks, data, banks, out7ffd, sna, clear, begin, scr=scr)

    def test_option_7ffd_with_128k_binary_file(self):
        data = [1, 2, 3]
        begin = 40000
        end = begin + len(data)
        clear = 32767
        out7ffd = 0
        ram = [0] * 49152
        ram[begin - 16384:begin - 16384 + len(data)] = data
        bin_data = []
        banks = []
        for bank in range(8):
            if bank == 2:
                bin_data += ram[16384:32768]
            elif bank == 5:
                bin_data += ram[:16384]
            elif bank == out7ffd % 8:
                banks.append((bank, ram[32768:]))
                bin_data += banks[-1][1]
            else:
                banks.append((bank, [bank] * 16384))
                bin_data += banks[-1][1]
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        blocks = self._run(f'-b {begin} -e {end} -c {clear} --7ffd {out7ffd} {binfile}')
        self._check_tape_with_ram_banks(blocks, data, banks, out7ffd, binfile, clear, begin)

    def test_option_7ffd_with_snapshot_and_no_end_option(self):
        data = [200, 201, 202]
        begin = 49152 - len(data)
        clear = 32767
        out7ffd = 1
        ram = [0] * 49152
        ram[begin - 16384:begin - 16384 + len(data)] = data
        sna_data = [0] * 27 + ram
        sna_data.extend((
            0, 0,    # PC
            out7ffd, # Port 0x7ffd
            0        # TR-DOS ROM
        ))
        banks = []
        for bank in (0, 1, 3, 4, 6, 7):
            if bank == out7ffd % 8:
                banks.append((bank, ram[32768:]))
            else:
                banks.append((bank, [bank] * 16384))
                sna_data.extend(banks[-1][1])
        sna = self.write_bin_file(sna_data, suffix='.sna')
        blocks = self._run(f'-b {begin} -c {clear} --7ffd {out7ffd} {sna}')
        self._check_tape_with_ram_banks(blocks, data, banks, out7ffd, sna, clear, begin)

    def test_option_7ffd_with_128k_binary_file_and_no_end_option(self):
        data = [128, 129, 130]
        begin = 49152 - len(data)
        clear = 32767
        out7ffd = 7
        ram = [0] * 49152
        ram[begin - 16384:begin - 16384 + len(data)] = data
        bin_data = []
        banks = []
        for bank in range(8):
            if bank == 2:
                bin_data += ram[16384:32768]
            elif bank == 5:
                bin_data += ram[:16384]
            elif bank == out7ffd % 8:
                banks.append((bank, ram[32768:]))
                bin_data += banks[-1][1]
            else:
                banks.append((bank, [bank] * 16384))
                bin_data += banks[-1][1]
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        blocks = self._run(f'-b {begin} -c {clear} --7ffd {out7ffd} {binfile}')
        self._check_tape_with_ram_banks(blocks, data, banks, out7ffd, binfile, clear, begin)

    def test_option_banks(self):
        data = [128, 129, 130]
        begin = 49152 - len(data)
        clear = 32767
        out7ffd = 7
        ram = [0] * 49152
        ram[begin - 16384:begin - 16384 + len(data)] = data
        bin_data = []
        for bank in range(8):
            if bank == 2:
                bin_data += ram[16384:32768]
            elif bank == 5:
                bin_data += ram[:16384]
            elif bank == out7ffd % 8:
                bin_data += ram[32768:]
            else:
                bin_data += [bank] * 16384
        banks = []
        bank_nums = (1, 4, 7)
        for bank in bank_nums:
            banks.append((bank, bin_data[bank * 0x4000:(bank + 1) * 0x4000]))
        pages = ','.join(str(b) for b in bank_nums)
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        blocks = self._run(f'-b {begin} -c {clear} --7ffd {out7ffd} --banks {pages} {binfile}')
        self._check_tape_with_ram_banks(blocks, data, banks, out7ffd, binfile, clear, begin)

    def test_option_banks_with_no_banks(self):
        data = [128, 129, 130]
        begin = 49152 - len(data)
        clear = 32767
        out7ffd = 4
        ram = [0] * 49152
        ram[begin - 16384:begin - 16384 + len(data)] = data
        bin_data = []
        for bank in range(8):
            if bank == 2:
                bin_data += ram[16384:32768]
            elif bank == 5:
                bin_data += ram[:16384]
            elif bank == out7ffd % 8:
                bin_data += ram[32768:]
            else:
                bin_data += [bank] * 16384
        banks = []
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        blocks = self._run(f'-b {begin} -c {clear} --7ffd {out7ffd} --banks , {binfile}')
        self._check_tape_with_ram_banks(blocks, data, banks, out7ffd, binfile, clear, begin)

    def test_option_b(self):
        bin_data = range(30)
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        org = 50000
        for option, begin in (('-b', 50010), ('--begin', 50020)):
            blocks = self._run('-o {} {} {} {}'.format(org, option, begin, binfile))
            self._check_tape(blocks, bin_data[begin - org:], binfile, org=begin)

    def test_option_b_with_z80(self):
        ram = [0] * 49152
        data = range(20)
        begin = 65536 - len(data)
        ram[begin - 16384:] = data
        z80 = self.write_z80(ram)[1]
        blocks = self._run('-b {} {}'.format(begin, z80))
        self._check_tape(blocks, data, z80, begin)

    def test_option_begin_with_szx(self):
        ram = [0] * 49152
        data = range(17)
        begin = 65536 - len(data)
        ram[begin - 16384:] = data
        szx = self.write_szx(ram)
        blocks = self._run('--begin {} {}'.format(begin, szx))
        self._check_tape(blocks, data, szx, begin)

    def test_option_begin_with_sna(self):
        ram = [0] * 49152
        data = range(15)
        begin = 65536 - len(data)
        ram[begin - 16384:] = data
        sna = self.write_bin_file([0] * 27 + ram, suffix='.sna')
        blocks = self._run('--begin {} {}'.format(begin, sna))
        self._check_tape(blocks, data, sna, begin)

    def test_option_b_with_hex_address(self):
        ram = [0] * 49152
        data = range(11)
        begin = 65536 - len(data)
        ram[begin - 16384:] = data
        sna = self.write_bin_file([0] * 27 + ram, suffix='.sna')
        blocks = self._run('-b 0x{:04X} {}'.format(begin, sna))
        self._check_tape(blocks, data, sna, begin)

    def test_option_c(self):
        org = 40000
        bin_data = range(25)
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        clear = org - 1
        start = org + 10
        for option in ('-c', '--clear'):
            blocks = self._run('{} {} -o {} -s {} {}'.format(option, clear, org, start, binfile))
            self._check_tape_with_clear_command(blocks, bin_data, binfile, clear, org, start)

    def test_option_c_with_hex_address(self):
        org = 50000
        bin_data = range(25)
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        clear = org - 1
        start = org + 10
        for option in ('-c', '--clear'):
            blocks = self._run('{} 0x{:04x} -o {} -s {} {}'.format(option, clear, org, start, binfile))
            self._check_tape_with_clear_command(blocks, bin_data, binfile, clear, org, start)

    def test_option_o(self):
        org = 40000
        bin_data = range(50)
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        for option in ('-o', '--org'):
            blocks = self._run('{} {} {}'.format(option, org, binfile))
            self._check_tape(blocks, bin_data, binfile, org=org)

    def test_option_o_with_hex_address(self):
        bin_data = range(50)
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        for option, org in (('-o', '0x800f'), ('--org', '0xAB00')):
            blocks = self._run('{} {} {}'.format(option, org, binfile))
            self._check_tape(blocks, bin_data, binfile, org=int(org[2:], 16))

    def test_option_s(self):
        bin_data = range(100)
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        start = 65536 - len(bin_data) // 2
        for option in ('-s', '--start'):
            blocks = self._run('{} {} {}'.format(option, start, binfile))
            self._check_tape(blocks, bin_data, binfile, start=start)

    def test_option_s_with_hex_address(self):
        bin_data = range(75)
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        start = 65536 - len(bin_data) // 2
        for option in ('-s', '--start'):
            blocks = self._run('{} 0x{:04X} {}'.format(option, start, binfile))
            self._check_tape(blocks, bin_data, binfile, start=start)

    def test_option_p(self):
        stack = 32768
        bin_data = range(64)
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        for option in ('-p', '--stack'):
            blocks = self._run('{} {} {}'.format(option, stack, binfile))
            self._check_tape(blocks, bin_data, binfile, stack=stack)

    def test_option_p_with_hex_address(self):
        stack = 32768
        bin_data = range(64)
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        for option in ('-p', '--stack'):
            blocks = self._run('{} 0x{:04x} {}'.format(option, stack, binfile))
            self._check_tape(blocks, bin_data, binfile, stack=stack)

    def test_data_overwrites_stack(self):
        bin_data = [0] * 10
        binfile = self.write_bin_file(bin_data, suffix='.bin')
        org = 65536 - len(bin_data)
        index = 5
        stack = org + index
        blocks = self._run('-p {} {}'.format(stack, binfile))
        bin_data[index - 4:index] = [
            63, 5,                # 1343 (SA/LD-RET)
            org % 256, org // 256 # start=org
        ]
        self._check_tape(blocks, bin_data, binfile, stack=stack)

    def test_option_end(self):
        org, end = 49152, 49162
        data = range(end - org + 2)
        binfile = self.write_bin_file(data, suffix='.bin')
        blocks = self._run('-o {} --end {} {}'.format(org, end, binfile))
        self._check_tape(blocks, data[:end - org], binfile, org)

    def test_option_e_with_z80(self):
        ram = [0] * 49152
        data = range(20)
        begin = 32768
        end = begin + len(data)
        ram[begin - 16384:end - 16384] = data
        z80 = self.write_z80(ram)[1]
        blocks = self._run('-b {} -e {} {}'.format(begin, end, z80))
        self._check_tape(blocks, data, z80, begin)

    def test_option_e_with_szx(self):
        ram = [0] * 49152
        data = range(17)
        begin = 50000
        end = begin + len(data)
        ram[begin - 16384:end - 16384] = data
        szx = self.write_szx(ram)
        blocks = self._run('-b {} -e {} {}'.format(begin, end, szx))
        self._check_tape(blocks, data, szx, begin)

    def test_option_end_with_sna(self):
        ram = [0] * 49152
        data = range(15)
        begin = 40000
        end = begin + len(data)
        ram[begin - 16384:end - 16384] = data
        sna = self.write_bin_file([0] * 27 + ram, suffix='.sna')
        blocks = self._run('-b {} --end {} {}'.format(begin, end, sna))
        self._check_tape(blocks, data, sna, begin)

    def test_option_e_with_hex_address(self):
        ram = [0] * 49152
        data = range(15)
        begin = 40000
        end = begin + len(data)
        ram[begin - 16384:end - 16384] = data
        sna = self.write_bin_file([0] * 27 + ram, suffix='.sna')
        blocks = self._run('-b {} -e 0x{:04X} {}'.format(begin, end, sna))
        self._check_tape(blocks, data, sna, begin)

    def test_options_b_and_e(self):
        org, begin, end = 60000, 60005, 60010
        data = range(end - org + 2)
        binfile = self.write_bin_file(data, suffix='.bin')
        blocks = self._run('-o {} -b {} -e {} {}'.format(org, begin, end, binfile))
        self._check_tape(blocks, data[begin - org:end - org], binfile, begin)

    def test_option_S_with_scr(self):
        scr = [85] * 6912
        scrfile = self.write_bin_file(scr, suffix='.scr')
        data = [35]
        binfile = self.write_bin_file(data, suffix='.bin')
        blocks = self._run('-S {} {}'.format(scrfile, binfile))
        self._check_tape(blocks, data, binfile, scr=scr)

    def test_option_screen_with_sna(self):
        scr = [170] * 6912
        sna = self.write_bin_file([0] * 27 + scr + [0] * 42240, suffix='.sna')
        data = [27]
        binfile = self.write_bin_file(data, suffix='.bin')
        blocks = self._run('--screen {} {}'.format(sna, binfile))
        self._check_tape(blocks, data, binfile, scr=scr)

    def test_option_S_with_szx(self):
        scr = [254] * 6912
        szx = self.write_szx(scr + [0] * 42240)
        data = [18]
        binfile = self.write_bin_file(data, suffix='.bin')
        blocks = self._run('-S {} {}'.format(szx, binfile))
        self._check_tape(blocks, data, binfile, scr=scr)

    def test_option_screen_with_z80(self):
        scr = [129] * 6912
        z80 = self.write_z80(scr + [0] * 42240)[1]
        data = [51]
        binfile = self.write_bin_file(data, suffix='.bin')
        blocks = self._run('--screen {} {}'.format(z80, binfile))
        self._check_tape(blocks, data, binfile, scr=scr)

    def test_option_S_with_option_c(self):
        scr = [144] * 6912
        scrfile = self.write_bin_file(scr, suffix='.scr')
        data = [147]
        binfile = self.write_bin_file(data, suffix='.bin')
        clear = 32768
        blocks = self._run('-S {} -c {} {}'.format(scrfile, clear, binfile))
        self._check_tape_with_clear_command(blocks, data, binfile, clear, scr=scr)

    @patch.object(components, 'SK_CONFIG', None)
    def test_custom_snapshot_reader(self):
        custom_snapshot_reader = """
            def can_read(fname):
                return fname.endswith('.sna')
            def get_snapshot(fname, page=None):
                return [128] * 65536
        """
        self.write_component_config('SnapshotReader', '*', custom_snapshot_reader)
        snafile = self.write_bin_file(suffix='.sna')
        blocks = self._run('-b 65535 {}'.format(snafile))
        self._check_tape(blocks, [128], snafile)

    @patch.object(components, 'SK_CONFIG', None)
    def test_option_S_with_custom_snapshot_reader(self):
        custom_snapshot_reader = """
            def can_read(fname):
                return fname.endswith('.snap')
            def get_snapshot(fname, page=None):
                return [192] * 23296
        """
        self.write_component_config('SnapshotReader', '*', custom_snapshot_reader)
        scrfile = self.write_bin_file(suffix='.snap')
        data = [64]
        binfile = self.write_bin_file(data, suffix='.bin')
        blocks = self._run('-S {} {}'.format(scrfile, binfile))
        exp_scr = [192] * 6912
        self._check_tape(blocks, data, binfile, scr=exp_scr)
