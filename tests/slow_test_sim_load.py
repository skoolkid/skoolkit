from unittest.mock import patch

from skoolkittest import (SkoolKitTestCase, PZX, create_header_block,
                          create_data_block, create_tap_header_block,
                          create_tap_data_block, create_tzx_header_block,
                          create_tzx_data_block, create_tzx_turbo_data_block,
                          create_tzx_pure_data_block)
from skoolkit import tap2sna, ROM48, read_bin_file

def mock_write_snapshot(ram, namespace, z80):
    global snapshot, options
    options = namespace
    snapshot = [0] * 65536
    if len(ram) == 8:
        page = 0
        for spec in options.state:
            if spec.startswith('7ffd='):
                page = int(spec[5:]) % 8
                break
        snapshot[0x4000:0x8000] = ram[5]
        snapshot[0x8000:0xC000] = ram[2]
        snapshot[0xC000:] = ram[page]
    else:
        snapshot[0x4000:] = ram

def get_loader(addr, bits=(0xB0, 0xCB)):
    rom = list(read_bin_file(ROM48, 0x0605))
    ld_8_bits = addr + 0x05CA - 0x0556
    ld_edge_1 = addr + 0x05E7 - 0x0556
    ld_edge_2 = addr + 0x05E3 - 0x0556
    rom[0x05D6:0x05D8] = (ld_8_bits % 256, ld_8_bits // 256)
    for a in (0x056D, 0x0592, 0x059C, 0x05E4):
        rom[a:a + 2] = (ld_edge_1 % 256, ld_edge_1 // 256)
    for a in (0x057C, 0x0583, 0x05CB):
        rom[a:a + 2] = (ld_edge_2 % 256, ld_edge_2 // 256)
    rom[0x05A6] = bits[0]      # Timing constants for
    rom[0x05C7] = bits[0] + 2  # the byte-loading loop
    rom[0x05CF] = bits[1]      #
    rom[0x05D4] = bits[0]      #
    return rom[0x0556:]

class SimLoadTest(SkoolKitTestCase):
    def _write_tap(self, blocks):
        tap_data = []
        for block in blocks:
            tap_data.extend(block)
        return self.write_bin_file(tap_data, suffix='.tap')

    def _write_tzx(self, blocks):
        tzx_data = [ord(c) for c in "ZXTape!"]
        tzx_data.extend((26, 1, 20))
        for block in blocks:
            tzx_data.extend(block)
        return self.write_bin_file(tzx_data, suffix='.tzx')

    def _get_basic_data(self, code_start):
        code_start_str = [ord(c) for c in str(code_start)]
        return [
            0, 10,            # Line 10
            16, 0,            # Line length
            239, 34, 34, 175, # LOAD ""CODE
            58,               # :
            249, 192, 176,    # RANDOMIZE USR VAL
            34,               # "
            *code_start_str,  # start address
            34,               # "
            13                # ENTER
        ]

    def _format_output(self, text):
        out_lines = []
        for line in text.strip().split('\n'):
            if '\x08' in line:
                shown = []
                index = 0
                for c in line:
                    if c == '\x08':
                        index -= 1
                    elif index < len(shown):
                        shown[index] = c
                        index += 1
                    else:
                        shown.append(c)
                        index += 1
                out_lines.append(''.join(shown).rstrip())
            else:
                out_lines.append(line.rstrip())
        return out_lines

    def _test_sim_load(self, args, exp_data, exp_reg, exp_output, exp_state=None):
        output, error = self.run_tap2sna(args)
        for data, addr in exp_data:
            self.assertEqual(data, snapshot[addr:addr + len(data)])
        self.assertLessEqual(exp_reg, set(options.reg))
        if exp_state:
            self.assertLessEqual(exp_state, set(options.state))
        out_lines = self._format_output(output)
        self.assertEqual(exp_output, out_lines)
        self.assertEqual(error, '')

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_standard_loader_pzx(self):
        code = [201] # RET
        code_start = 32768
        code_end = code_start + len(code)
        basic_data = self._get_basic_data(code_start)
        pzx = PZX()
        pzx.add_puls(2)
        pzx.add_data(create_header_block('simloadpzx', 10, len(basic_data), 0))
        pzx.add_paus()
        pzx.add_puls(1)
        pzx.add_data(create_data_block(basic_data))
        pzx.add_paus()
        pzx.add_puls(2)
        pzx.add_data(create_header_block('simloadbyt', code_start, len(code)))
        pzx.add_paus()
        pzx.add_puls(1)
        pzx.add_data(create_data_block(code))
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        exp_data = (
            (basic_data, 23755),
            (code, code_start),
        )
        exp_reg = set(('SP=65344', f'IX={code_end}', 'IY=23610', f'PC={code_start}'))
        exp_output = [
            'Program: simloadpzx',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,1',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768'
        ]
        self._test_sim_load(f'{pzxfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_standard_loader_pzx_with_polarity_inverted(self):
        code = [201] # RET
        code_start = 32768
        code_end = code_start + len(code)
        basic_data = self._get_basic_data(code_start)
        pilot1 = ((1, 0), (3223, 2168), (1, 667), (1, 735))
        pilot2 = ((1, 0), (8063, 2168), (1, 667), (1, 735))
        pzx = PZX()
        pzx.add_puls(pulse_counts=pilot2)
        pzx.add_data(create_header_block('simloadpzx', 10, len(basic_data), 0), polarity=0)
        pzx.add_paus()
        pzx.add_puls(pulse_counts=pilot1)
        pzx.add_data(create_data_block(basic_data), polarity=0)
        pzx.add_paus()
        pzx.add_puls(pulse_counts=pilot2)
        pzx.add_data(create_header_block('simloadbyt', code_start, len(code)), polarity=0)
        pzx.add_paus()
        pzx.add_puls(pulse_counts=pilot1)
        pzx.add_data(create_data_block(code), polarity=0)
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')
        exp_data = (
            (basic_data, 23755),
            (code, code_start),
        )
        exp_reg = set(('SP=65344', f'IX={code_end}', 'IY=23610', f'PC={code_start}'))
        exp_output = [
            'Program: simloadpzx',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,1',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768'
        ]
        self._test_sim_load(f'{pzxfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_custom_standard_speed_loader(self):
        code2 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        code2_start = 49152
        code2_end = code2_start + len(code2)
        code = [
            221, 33, 0, 192,  # LD IX,49152
            17, 10, 0,        # LD DE,10
            55,               # SCF
            159,              # SBC A,A
        ]
        loader_start = 32768
        code_start = loader_start - len(code)
        code += get_loader(loader_start)
        basic_data = self._get_basic_data(code_start)
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block("simloadbyt", code_start, len(code)),
            create_tap_data_block(code),
            create_tap_data_block(code2)
        ]
        tapfile = self._write_tap(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            (code2, code2_start)
        )
        exp_reg = set(('SP=65340', f'IX={code2_end}', 'IY=23610', 'PC=32925'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32759,184',
            'Data (12 bytes)',
            'Tape finished',
            'Simulation stopped (end of tape): PC=32925'
        ]
        self._test_sim_load(f'{tapfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_custom_standard_speed_loader_with_accelerator(self):
        code2 = list(range(256))
        code2_start = 49152
        code2_end = code2_start + len(code2)
        code = [
            221, 33, 0, 192,  # LD IX,49152
            17, 0, 1,         # LD DE,256
            55,               # SCF
            159,              # SBC A,A
        ]
        loader_start = 32768
        code_start = loader_start - len(code)
        code += get_loader(loader_start)
        basic_data = self._get_basic_data(code_start)
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block("simloadbyt", code_start, len(code)),
            create_tap_data_block(code),
            create_tap_data_block(code2)
        ]
        tapfile = self._write_tap(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            (code2, code2_start)
        )
        exp_reg = set(('SP=65340', f'IX={code2_end}', 'IY=23610', 'PC=32925'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32759,184',
            'Data (258 bytes)',
            'Tape finished',
            'Simulation stopped (end of tape): PC=32925'
        ]
        self._test_sim_load(f'-c accelerator=rom {tapfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_turbo_loader_pzx(self):
        code2 = [1, 2, 4, 8, 16, 32, 64, 128, 0, 255]
        code2_start = 65280
        code2_end = code2_start + len(code2)
        code = [
            221, 33, 0, 255,  # LD IX,65280
            17, 10, 0,        # LD DE,10
            55,               # SCF
            159,              # SBC A,A
        ]
        loader_start = 32768
        code_start = loader_start - len(code)
        code += get_loader(loader_start, (0xE0, 0xEC))
        basic_data = self._get_basic_data(code_start)
        pzx = PZX()
        pzx.add_puls(2)
        pzx.add_data(create_header_block("simloadbas", 10, len(basic_data), 0))
        pzx.add_puls(1)
        pzx.add_data(create_data_block(basic_data))
        pzx.add_puls(2)
        pzx.add_data(create_header_block("simloadbyt", code_start, len(code), 3))
        pzx.add_puls(1)
        pzx.add_data(create_data_block(code))
        pzx.add_puls(1)
        pzx.add_data(create_data_block(code2), (600, 600), (1200, 1200), tail=0)
        pzxfile = self.write_bin_file(pzx.data, suffix='.pzx')

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            (code2, code2_start)
        )
        exp_reg = set(('SP=65340', f'IX={code2_end}', 'IY=23610', 'PC=32925'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32759,184',
            'Data (12 bytes)',
            'Tape finished',
            'Simulation stopped (end of tape): PC=32925'
        ]
        self._test_sim_load(f'{pzxfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_turbo_loader_tzx(self):
        code2 = [1, 2, 4, 8, 16, 32, 64, 128, 0, 255]
        code2_start = 49152
        code2_end = code2_start + len(code2)
        code = [
            221, 33, 0, 192,  # LD IX,49152
            17, 10, 0,        # LD DE,10
            55,               # SCF
            159,              # SBC A,A
        ]
        loader_start = 32768
        code_start = loader_start - len(code)
        code += get_loader(loader_start, (0xE0, 0xEC))
        basic_data = self._get_basic_data(code_start)
        blocks = [
            create_tzx_header_block("simloadbas", 10, len(basic_data), 0),
            create_tzx_data_block(basic_data),
            create_tzx_header_block("simloadbyt", code_start, len(code), 3),
            create_tzx_data_block(code),
            create_tzx_turbo_data_block(code2, 600, 1200)
        ]
        tzxfile = self._write_tzx(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            (code2, code2_start)
        )
        exp_reg = set(('SP=65340', f'IX={code2_end}', 'IY=23610', 'PC=32925'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32759,184',
            'Data (12 bytes)',
            'Tape finished',
            'Simulation stopped (end of tape): PC=32925'
        ]
        self._test_sim_load(f'{tzxfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_tzx_block_types_0x12_0x13_0x14(self):
        code2 = [1, 2, 4, 8, 16, 32, 64, 128, 0, 255]
        pdata = create_data_block(code2)
        code2_start = 49152
        code2_end = code2_start + len(code2)
        code = [
            221, 33, 0, 192,  # LD IX,49152
            17, 10, 0,        # LD DE,10
            55,               # SCF
            159,              # SBC A,A
        ]
        loader_start = 32768
        code_start = loader_start - len(code)
        code += get_loader(loader_start)
        basic_data = self._get_basic_data(code_start)
        pure_tone = [
            0x12,             # Block ID (Pure Tone)
            120, 8,           # 2168 (pulse length)
            151, 12,          # 3223 (number of pulses)
        ]
        pulse_sequence = [
            0x13,             # Block ID (Pulse Sequence)
            2,                # Number of pulses
            155, 2,           # Sync 1 (667)
            223, 2,           # Sync 2 (735)
        ]
        blocks = [
            create_tzx_header_block("simloadbas", 10, len(basic_data), 0),
            create_tzx_data_block(basic_data),
            create_tzx_header_block("simloadbyt", code_start, len(code), 3),
            create_tzx_data_block(code),
            pure_tone,
            pulse_sequence,
            create_tzx_pure_data_block(pdata),
        ]
        tzxfile = self._write_tzx(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            (code2, code2_start)
        )
        exp_reg = set(('SP=65340', f'IX={code2_end}', 'IY=23610', 'PC=32925'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32759,184',
            'Data (12 bytes)',
            'Tape finished',
            'Simulation stopped (end of tape): PC=32925'
        ]
        self._test_sim_load(f'{tzxfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_tzx_loop(self):
        code2 = [1, 2, 4, 8, 16]
        code2_start = 49152
        code2_end = code2_start + 2 * len(code2)
        code = [
            221, 33, 0, 192,  # LD IX,49152
            17, 10, 0,        # LD DE,10
            55,               # SCF
            159,              # SBC A,A
            205, 0, 128,      # CALL 32768 ; Load code2
            195, 0, 192       # JP 49152
        ]
        loader_start = 32768
        code_start = loader_start - len(code)
        code += get_loader(loader_start)
        basic_data = self._get_basic_data(code_start)
        pure_tone = [
            0x12,             # Block ID (Pure Tone)
            120, 8,           # 2168 (pulse length)
            151, 12,          # 3223 (number of pulses)
        ]
        pulse_sequence = [
            0x13,             # Block ID (Pulse Sequence)
            2,                # Number of pulses
            155, 2,           # Sync 1 (667)
            223, 2,           # Sync 2 (735)
        ]
        flag_byte = [
            0x14,             # Block ID (Pure Data)
            87, 3,            # 855 (length of 0-bit pulse)
            174, 6,           # 1710 (length of 1-bit pulse)
            8,                # Used bits in last byte
            0, 0,             # 0ms (pause)
            1, 0, 0,          # Data length (1)
            255,              # Data
        ]
        loop_start = [
            0x24,             # Block ID (Loop start)
            2, 0,             # Repetitions (2)
        ]
        loop_end = [37]
        parity_byte = [
            0x14,             # Block ID (Pure Data)
            87, 3,            # 855 (length of 0-bit pulse)
            174, 6,           # 1710 (length of 1-bit pulse)
            8,                # Used bits in last byte
            0, 0,             # 0ms (pause)
            1, 0, 0,          # Data length (1)
            255,              # Data
        ]
        blocks = [
            create_tzx_header_block("simloadbas", 10, len(basic_data), 0),
            create_tzx_data_block(basic_data),
            create_tzx_header_block("simloadbyt", code_start, len(code), 3),
            create_tzx_data_block(code),
            pure_tone,
            pulse_sequence,
            flag_byte,
            loop_start,
            create_tzx_pure_data_block(code2),
            loop_end,
            parity_byte,
        ]
        tzxfile = self._write_tzx(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            (code2 + code2, code2_start)
        )
        exp_reg = set(('SP=65344', f'IX={code2_end}', 'IY=23610', 'PC=49152'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32753,190',
            'Data (1 bytes)',
            'Data (5 bytes)',
            'Data (5 bytes)',
            'Data (1 bytes)',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=49152'
        ]
        self._test_sim_load(f'--start 49152 {tzxfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_tape_stop_option_overrides_stop_the_tape_command(self):
        code = [
            221, 33, 0, 192,  # LD IX,49152 ; Simulation should stop here
            17, 1, 0,         # LD DE,1     ; because the tape has stopped
            55,               # SCF
            159,              # SBC A,A
            195, 86, 5        # JP 1366
        ]
        code_start = 32768
        code2 = [201]
        basic_data = self._get_basic_data(code_start)
        blocks = [
            create_tzx_header_block("simloadbas", 10, len(basic_data), 0),
            create_tzx_data_block(basic_data),
            (0x20, 0, 0), # 0x20 - 'Stop the Tape' command
            create_tzx_header_block("simloadbyt", code_start, len(code), 3),
            create_tzx_data_block(code),
            create_tzx_data_block(code2) # Block 6: ignored
        ]
        tzxfile = self._write_tzx(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start)
        )
        exp_reg = set(('SP=65344', f'IX=32780', 'IY=23610', 'PC=32768'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,12',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768'
        ]
        self._test_sim_load(f'--tape-stop 6 {tzxfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_tape_stop_option_overrides_stop_the_tape_if_in_48K_mode(self):
        code = [
            221, 33, 0, 192,  # LD IX,49152 ; Simulation should stop here
            17, 1, 0,         # LD DE,1     ; because the tape has stopped
            55,               # SCF
            159,              # SBC A,A
            195, 86, 5        # JP 1366
        ]
        code_start = 32768
        code2 = [201]
        basic_data = self._get_basic_data(code_start)
        blocks = [
            create_tzx_header_block("simloadbas", 10, len(basic_data), 0),
            create_tzx_data_block(basic_data),
            (0x2A, 0, 0, 0, 0), # 0x2A - Stop the tape if in 48K mode
            create_tzx_header_block("simloadbyt", code_start, len(code), 3),
            create_tzx_data_block(code),
            create_tzx_data_block(code2) # Block 6: ignored
        ]
        tzxfile = self._write_tzx(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start)
        )
        exp_reg = set(('SP=65344', f'IX=32780', 'IY=23610', 'PC=32768'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,12',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768'
        ]
        self._test_sim_load(f'--tape-stop 6 {tzxfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_no_gap_between_data_blocks(self):
        code2 = [1, 2, 4, 8, 16, 32, 64, 128, 0, 255]
        code3 = [128, 64, 32, 16, 8, 4, 2, 1, 0, 255]
        pdata = create_data_block(code3)
        code2_start = 49152
        code3_start = code2_start + len(code2)
        code3_end = code3_start + len(code3)
        code = [
            243,              # DI
            221, 33, 0, 192,  # LD IX,49152
            17, 10, 0,        # LD DE,10
            55,               # SCF
            159,              # SBC A,A
            8,                # EX AF,AF'
            205, 98, 5,       # CALL 1378 ; Load code2
            17, 10, 0,        # LD DE,10
            55,               # SCF
            159,              # SBC A,A
            8,                # EX AF,AF'
            6, 205,           # LD B,205
            205, 231, 5,      # CALL 1511 ; LD-EDGE-1 - detect Sync 1 pulse
            208,              # RET NC
            120,              # LD A,B
            254, 212,         # CP 212
            208,              # RET NC
            205, 231, 5,      # CALL 1511 ; LD-EDGE-1 - detect Sync 2 pulse
            208,              # RET NC
            205, 159, 5,      # CALL 1439 ; Load code3
            195, 0, 192       # JP 49152
        ]
        code_start = 32768
        basic_data = self._get_basic_data(code_start)
        pulse_sequence = [
            0x13,             # Block ID (Pulse Sequence)
            2,                # Number of pulses
            155, 2,           # Sync 1 (667)
            223, 2,           # Sync 2 (735)
        ]
        blocks = [
            create_tzx_header_block("simloadbas", 10, len(basic_data), 0),
            create_tzx_data_block(basic_data),
            create_tzx_header_block("simloadbyt", code_start, len(code), 3),
            create_tzx_data_block(code),
            create_tzx_data_block(code2),
            pulse_sequence,
            create_tzx_pure_data_block(pdata),
        ]
        tzxfile = self._write_tzx(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            (code2 + code3, code2_start)
        )
        exp_reg = set(('SP=65344', f'IX={code3_end}', 'IY=23610', 'PC=49152'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,40',
            'Data (12 bytes)',
            'Data (12 bytes)',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=49152'
        ]
        self._test_sim_load(f'--start 49152 {tzxfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_required_gap_between_data_blocks(self):
        # Some loaders (e.g. Bruce Lee - Speedlock 1) require a period of
        # silence between two blocks
        code2 = [1, 2, 4, 8]
        code3 = [16, 32, 64, 128]
        pdata = create_data_block(code3)
        code2_start = 49152
        code3_start = code2_start + len(code2)
        code3_end = code3_start + len(code3)
        code = [
            221, 33, 0, 192,  # LD IX,49152
            17, 4, 0,         # LD DE,4
            55,               # SCF
            159,              # SBC A,A
            205, 86, 5,       # CALL 1366   ; Load code2
            6, 160,           # LD B,160
            205, 227, 5,      # CALL 1507   ; LD-EDGE-2 - look for 2 edges
            48, 4,            # JR NC,+4    ; Jump if not found - OK
            221, 33, 0, 193,  # LD IX,49408 ; Change load address - FAIL
            17, 4, 0,         # LD DE,4
            55,               # SCF
            159,              # SBC A,A
            205, 86, 5,       # CALL 1366   ; Load code3
            195, 0, 192       # JP 49152
        ]
        code_start = 32768
        basic_data = self._get_basic_data(code_start)
        blocks = [
            create_tzx_header_block("simloadbas", 10, len(basic_data), 0),
            create_tzx_data_block(basic_data),
            create_tzx_header_block("simloadbyt", code_start, len(code), 3),
            create_tzx_data_block(code),
            create_tzx_data_block(code2, 500), # 500ms gap before next block
            create_tzx_data_block(code3),
        ]
        tzxfile = self._write_tzx(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            (code2 + code3, code2_start)
        )
        exp_reg = set(('SP=65344', f'IX={code3_end}', 'IY=23610', 'PC=49152'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,34',
            'Fast loading data block: 49152,4',
            'Fast loading data block: 49156,4',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=49152'
        ]
        self._test_sim_load(f'--start 49152 {tzxfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_unread_data_in_middle_of_tape(self):
        code = [
            221, 33, 0, 192,   # 32757 LD IX,49152
            221, 229,          # 32761 PUSH IX
            17, 22, 0,         # 32763 LD DE,22    ; code2 is 22 bytes
            55,                # 32766 SCF
            159,               # 32767 SBC A,A
        ]
        code2 = [
            # Pause briefly while the tape continues playing the last byte
            # of the code2 data block (which is unread), and then load the
            # code3 data block
            1, 0, 3,           # 49152 LD BC,768   ; Pause for 19973 T-states,
            11,                # 49155 DEC BC      ; long enough for LoadTracer
            120,               # 49156 LD A,B      ; to move past the last
            177,               # 49157 OR C        ; (unread) byte of the code2
            32, 251,           # 49158 JR NZ,49155 ; block and on to code3
            221, 33, 255, 255, # 49160 LD IX,65535
            221, 229,          # 49164 PUSH IX
            17, 1, 0,          # 49166 LD DE,1     ; code3 is 1 byte
            55,                # 49169 SCF
            159,               # 49170 SBC A,A
            195, 0, 128,       # 49171 JP 32768
        ]
        code3 = [201]
        code2_start = 49152
        code2_len = len(code2)
        code2_end = code2_start + code2_len
        loader_start = 32768
        code_start = loader_start - len(code)
        code += get_loader(loader_start)
        basic_data = self._get_basic_data(code_start)
        code2_data_block = create_tap_data_block(code2)
        code2_data_block[0] += 1
        code2_data_block.append(0)
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block("simloadbyt", code_start, len(code)),
            create_tap_data_block(code),
            code2_data_block,
            create_tap_data_block(code3)
        ]
        tapfile = self._write_tap(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            (code2, code2_start),
            (code3, 65535)
        )
        exp_reg = set(('SP=65344', 'IX=0', 'IY=23610', 'PC=65535'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32757,186',
            'Data (25 bytes)',
            'Data (3 bytes)',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=65535'
        ]
        self._test_sim_load(f'--start 65535 {tapfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_unread_data_at_end_of_tape(self):
        code2 = [
            # This loop runs while the tape continues playing
            17, 0, 0,         # 49152 LD DE,0      [10]
            74,               # 49155 LD C,D       [4]
            19,               # 49156 INC DE       [6]     ; 26 T-states
            122,              # 49157 LD A,D       [4]     ; per
            179,              # 49158 OR E         [4]     ; iteration
            32, 251,          # 49159 JR NZ,49156  [12/7]  ;
            12,               # 49161 INC C        [4]
            24, 248,          # 49162 JR 49156     [12]
        ]
        code2_start = 49152
        code2_len = len(code2)
        code2_end = code2_start + code2_len
        code = [
            221, 33, 0, 192,  # LD IX,49152
            221, 229,         # PUSH IX
            17, code2_len, 0, # LD DE,code2_len
            55,               # SCF
            159,              # SBC A,A
        ]
        loader_start = 32768
        code_start = loader_start - len(code)
        code += get_loader(loader_start)
        basic_data = self._get_basic_data(code_start)
        code2_data_block = create_tap_data_block(code2)
        code2_data_block[0] += 1
        code2_data_block.append(0)
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block("simloadbyt", code_start, len(code)),
            create_tap_data_block(code),
            code2_data_block
        ]
        tapfile = self._write_tap(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            (code2, code2_start)
        )
        exp_reg = set(('SP=65344', f'IX={code2_end}', 'IY=23610', 'PC=49158', 'BC=45056', 'DE=648')) # CDE=648
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32757,186',
            'Data (15 bytes)',
            'Tape finished',
            'Simulation stopped (end of tape): PC=49158'
        ]
        self._test_sim_load(f'{tapfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_port_read_after_tape_end(self):
        code2 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        code2_start = 49152
        code2_end = code2_start + len(code2)
        code = [
            221, 33, 0, 192,  # LD IX,49152
            17, 10, 0,        # LD DE,10
            55,               # SCF
            159,              # SBC A,A
            205, 86, 5,       # CALL 1366  ; Load code2
            219, 254,         # IN A,(254)
            195, 0, 192,      # JP 49152
        ]
        code_start = 32768
        basic_data = self._get_basic_data(code_start)
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block("simloadbyt", code_start, len(code)),
            create_tap_data_block(code),
            create_tap_data_block(code2)
        ]
        tapfile = self._write_tap(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            (code2, code2_start)
        )
        exp_reg = set(('SP=65344', f'IX={code2_end}', 'IY=23610', 'PC=49152'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,17',
            'Fast loading data block: 49152,10',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=49152'
        ]
        self._test_sim_load(f'--start 49152 {tapfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_no_ram_execution(self):
        usr_str = [ord(c) for c in '10355'] # 10355 JR Z,10355
        basic_data = [
            0, 10,            # Line 10
            11, 0,            # Line length
            249, 192, 176,    # RANDOMIZE USR VAL
            34,               # "
            *usr_str,         # 10355
            34,               # "
            13                # ENTER
        ]
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
        ]
        tapfile = self._write_tap(blocks)

        exp_data = [(basic_data, 23755)]
        exp_reg = set(('SP=65344', 'IX=23770', 'IY=23610', 'PC=10355'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,15',
            'Tape finished',
            'Simulation stopped (tape ended 1 second ago): PC=10355',
        ]
        self._test_sim_load(f'{tapfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_tape_is_paused_between_blocks(self):
        code_start = 32768
        code_start_str = [ord(c) for c in str(code_start)]
        basic_data = [
            0, 10,                    # Line 10
            23, 0,                    # Line length
            242, 176, 34, 57, 57, 34, # PAUSE VAL "99"
            58,                       # :
            239, 34, 34, 175,         # LOAD ""CODE
            58,                       # :
            249, 192, 176,            # RANDOMIZE USR VAL
            34, *code_start_str, 34,  # "start address"
            13                        # ENTER
        ]
        code = [201]
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block("simloadbyt", code_start, len(code), 3),
            create_tap_data_block(code),
        ]
        tapfile = self._write_tap(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start)
        )
        exp_reg = set(('SP=65344', 'IX=32769', 'IY=23610', 'PC=32768'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,27',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,1',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
        ]
        self._test_sim_load(f'{tapfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_skip_data_before_fast_loading_next_block(self):
        code2 = [1, 2, 4, 8]
        code2_start = 49152
        code2_end = code2_start + len(code2)
        extra = [255] * 4
        pdata = create_data_block(extra)
        code3 = [16, 32, 64, 128]
        code3_start = 49156
        code3_end = code3_start + len(code3)
        code = [
            221, 33, 0, 192,  # LD IX,49152
            17, 4, 0,         # LD DE,4
            55,               # SCF
            159,              # SBC A,A
            8,                # EX AF,AF'
            205, 89, 5,       # CALL 1369 ; Load code2 (bypassing fast load)
            17, 4, 0,         # LD DE,4
            55,               # SCF
            159,              # SBC A,A
            205, 86, 5,       # CALL 1366 ; Load code3 (fast load)
            195, 0, 192       # JP 49152
        ]
        code_start = 32768
        basic_data = self._get_basic_data(code_start)
        pure_data = create_tzx_pure_data_block(pdata)
        blocks = [
            create_tzx_header_block("simloadbas", 10, len(basic_data), 0),
            create_tzx_data_block(basic_data),
            create_tzx_header_block("simloadbyt", code_start, len(code), 3),
            create_tzx_data_block(code),
            create_tzx_data_block(code2),
            pure_data, # Extraneous data at the end of the second code block,
                       # which should be skipped before fast loading the third
            create_tzx_data_block(code3),
        ]
        tzxfile = self._write_tzx(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            (code2, code2_start),
            (code3, code3_start)
        )
        exp_reg = set(('SP=65344', f'IX={code3_end}', 'IY=23610', 'PC=49152'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,24',
            'Data (6 bytes)',
            'Fast loading data block: 49156,4',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=49152'
        ]
        self._test_sim_load(f'--start 49152 {tzxfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_simulation_timed_out(self):
        basic_data = [
            0, 10,            # Line 10
            2, 0,             # Line length
            247,              # RUN
            13                # ENTER
        ]
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_data_block([0]),
        ]
        tapfile = self._write_tap(blocks)

        exp_data = [(basic_data, 23755)]
        exp_reg = set(('IX=23761', 'IY=23610', 'PC=1343'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,6',
            'Simulation stopped (timed out): PC=1343',
        ]
        self._test_sim_load(f'-c timeout=6 {tapfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_simulation_timed_out_with_start_address(self):
        basic_data = [
            0, 10,            # Line 10
            2, 0,             # Line length
            247,              # RUN
            13                # ENTER
        ]
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_data_block([0]),
        ]
        tapfile = self._write_tap(blocks)

        exp_data = [(basic_data, 23755)]
        exp_reg = set(('IX=23761', 'IY=23610', 'PC=1343'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,6',
            'Simulation stopped (timed out): PC=1343',
        ]
        self._test_sim_load(f'-c timeout=6 --start 32768 {tapfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_tzx_pause(self):
        code2 = [1, 2, 4, 8]
        code3 = [16, 32, 64, 128]
        pdata = create_data_block(code3)
        code2_start = 49152
        code3_start = code2_start + len(code2)
        code3_end = code3_start + len(code3)
        code = [
            243,              # DI
            221, 33, 0, 192,  # LD IX,49152
            17, 4, 0,         # LD DE,4
            55,               # SCF
            159,              # SBC A,A
            8,                # EX AF,AF'
            205, 98, 5,       # CALL 1378   ; Load code2
            6, 0,             # LD B,0
            205, 227, 5,      # CALL 1507   ; LD-EDGE-2 - look for 2 edges
            48, 4,            # JR NC,+4    ; Jump if not found - OK
            221, 33, 0, 193,  # LD IX,49408 ; Change load address - FAIL
            17, 4, 0,         # LD DE,4
            55,               # SCF
            159,              # SBC A,A
            205, 86, 5,       # CALL 1366   ; Load code3
            195, 0, 192       # JP 49152
        ]
        pause = [
            0x20,             # Block ID (Pause)
            244, 1            # Duration (500ms)
        ]
        code_start = 32768
        basic_data = self._get_basic_data(code_start)
        blocks = [
            create_tzx_header_block("simloadbas", 10, len(basic_data), 0),
            create_tzx_data_block(basic_data),
            create_tzx_header_block("simloadbyt", code_start, len(code), 3),
            create_tzx_data_block(code),
            create_tzx_data_block(code2),
            pause,
            create_tzx_data_block(code3),
        ]
        tzxfile = self._write_tzx(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            (code2 + code3, code2_start)
        )
        exp_reg = set(('SP=65344', f'IX={code3_end}', 'IY=23610', 'PC=49152'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,36',
            'Data (6 bytes)',
            'Fast loading data block: 49156,4',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=49152'
        ]
        self._test_sim_load(f'--start 49152 {tzxfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_unused_bits_in_last_byte_of_tzx_block_0x11(self):
        code2 = [1, 2, 3, 4]
        code2_start = 49152
        code2_end = code2_start + len(code2)
        turbo = create_tzx_turbo_data_block(code2, used_bits=4)
        code = [
            243,              # DI
            221, 33, 0, 192,  # LD IX,49152
            17, 4, 0,         # LD DE,4
            55,               # SCF
            159,              # SBC A,A
            8,                # EX AF,AF'
            205, 98, 5,       # CALL 1378  ; Load code2
            48, 4,            # JR NC,+4   ; Jump on LOAD error (expected)
            221, 33, 0, 0,    # LD IX,0    ; FAIL
            195, 0, 192,      # JP 49152
        ]
        code_start = 32768
        basic_data = self._get_basic_data(code_start)
        blocks = [
            create_tzx_header_block("simloadbas", 10, len(basic_data), 0),
            create_tzx_data_block(basic_data),
            create_tzx_header_block("simloadbyt", code_start, len(code)),
            create_tzx_data_block(code),
            turbo,
        ]
        tzxfile = self._write_tzx(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            (code2, code2_start)
        )
        exp_reg = set(('SP=65344', f'IX={code2_end}', 'IY=23610', 'PC=49152'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,23',
            'Data (6 bytes)',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=49152'
        ]
        self._test_sim_load(f'--start 49152 {tzxfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_unused_bits_in_last_byte_of_tzx_block_0x14(self):
        code2 = [1, 2, 3, 4]
        pdata = create_data_block(code2)
        code2_start = 49152
        code2_end = code2_start + len(code2)
        code = [
            243,              # DI
            221, 33, 0, 192,  # LD IX,49152
            17, 4, 0,         # LD DE,4
            55,               # SCF
            159,              # SBC A,A
            8,                # EX AF,AF'
            205, 98, 5,       # CALL 1378  ; Load code2
            48, 4,            # JR NC,+4   ; Jump on LOAD error (expected)
            221, 33, 0, 0,    # LD IX,0    ; FAIL
            195, 0, 192,      # JP 49152
        ]
        code_start = 32768
        basic_data = self._get_basic_data(code_start)
        pure_tone = [
            0x12,             # Block ID (Pure Tone)
            120, 8,           # 2168 (pulse length)
            151, 12,          # 3223 (number of pulses)
        ]
        pulse_sequence = [
            0x13,             # Block ID (Pulse Sequence)
            2,                # Number of pulses
            155, 2,           # Sync 1 (667)
            223, 2,           # Sync 2 (735)
        ]
        blocks = [
            create_tzx_header_block("simloadbas", 10, len(basic_data), 0),
            create_tzx_data_block(basic_data),
            create_tzx_header_block("simloadbyt", code_start, len(code)),
            create_tzx_data_block(code),
            pure_tone,
            pulse_sequence,
            create_tzx_pure_data_block(pdata, used_bits=4),
        ]
        tzxfile = self._write_tzx(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            (code2, code2_start)
        )
        exp_reg = set(('SP=65344', f'IX={code2_end}', 'IY=23610', 'PC=49152'))
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            'Fast loading data block: 32768,23',
            'Data (6 bytes)',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=49152'
        ]
        self._test_sim_load(f'--start 49152 {tzxfile} out.z80', exp_data, exp_reg, exp_output)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_trace_with_load_command(self):
        basic_data = [
            0, 10,               # Line 10
            14, 0,               # Line length
            249, 192,            # RANDOMIZE USR
            51, 50, 55, 54, 56,  # 32768 in ASCII
            14, 0, 0, 0, 128, 0, # 32768 in floating point form
            13                   # ENTER
        ]
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
        ]
        tapfile = self._write_tap(blocks)
        tracefile = '{}/sim-load.trace'.format(self.make_directory())
        output, error = self.run_tap2sna(('-c', f'trace={tracefile}', '-c', 'load=LOAD ""', tapfile, 'out.z80'))
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,18',
            'Tape finished',
            'Simulation stopped (PC in RAM): PC=32768',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        exp_reg = set(('^F=69', 'SP=65344', 'IX=23773', 'IY=23610', 'PC=32768'))
        self.assertLessEqual(exp_reg, set(options.reg))
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 134589)
        self.assertEqual(trace_lines[0], '$1200 LD ($5CB4),HL')
        self.assertEqual(trace_lines[1], '$1203 LD DE,$3EAF')
        self.assertEqual(trace_lines[2], '$1206 LD BC,$00A8')
        self.assertEqual(trace_lines[3], '$1209 EX DE,HL')
        self.assertEqual(trace_lines[126488], '$0605 POP AF')
        self.assertEqual(trace_lines[134588], '$34BB RET')

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_trace_with_load_command_and_interrupts_and_timestamps(self):
        basic_data = [
            0, 10, # Line 10
            2, 0,  # Line length
            234,   # REM
            13     # ENTER
        ]
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
        ]
        tapfile = self._write_tap(blocks)
        tracefile = 'sim-load.trace'
        args = (
            '-I', 'TraceLine={t} ${pc:04X} {i}',
            '-c', f'trace={tracefile}',
            '-c', 'load=LOAD ""',
            '--start', '0x053f',
            '-c', 'finish-tape=1',
            tapfile,
            'out.z80'
        )
        output, error = self.run_tap2sna(args)
        out_lines = output.strip().split('\n')
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,6',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=1343',
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        exp_reg = set(('^F=69', 'SP=65360', 'IX=23761', 'IY=23610', 'PC=1343'))
        self.assertLessEqual(exp_reg, set(options.reg))
        with open(tracefile, 'r') as f:
            trace_lines = f.read().rstrip().split('\n')
        self.assertEqual(len(trace_lines), 133769)
        self.assertEqual(trace_lines[2023], '5730799 $0E5C LDIR')
        self.assertEqual(trace_lines[2024], '5730833 $0038 PUSH AF')
        self.assertEqual(trace_lines[5604], '5800690 $0E5C LDIR')
        self.assertEqual(trace_lines[5605], '5800724 $0038 PUSH AF')
        self.assertEqual(trace_lines[9239], '5870587 $0E59 LD (HL),$00')
        self.assertEqual(trace_lines[9240], '5870610 $0038 PUSH AF')
        self.assertEqual(trace_lines[17129], '5940475 $15F7 LD E,(HL)')
        self.assertEqual(trace_lines[17130], '5940495 $0038 PUSH AF')
        self.assertEqual(trace_lines[24021], '6010364 $15E8 LD HL,($5C51)')
        self.assertEqual(trace_lines[24022], '6010393 $0038 PUSH AF')

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_bit_5_of_output_to_port_0x7ffd(self):
        code = [
            0xF3,             # $8000 DI
            0x21, 0x00, 0xC0, # $8001 LD HL,$C000
            0x74,             # $8004 LD (HL),H   ; POKE 49152,192
            0x01, 0xFD, 0x7F, # $8005 LD BC,$7FFD
            0x3E, 0x20,       # $8008 LD A,$20    ; Bit 5 set: disable paging
            0xED, 0x79,       # $800A OUT (C),A   ; and ignore further output.
            0x3E, 0x07,       # $800C LD A,$07
            0xED, 0x79,       # $800E OUT (C),A   ; This OUT should be ignored.
        ]
        code_start = 32768
        start = code_start + len(code)
        basic_data = self._get_basic_data(code_start)
        blocks = [
            create_tap_header_block("simloadbas", 10, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_header_block("simloadbyt", code_start, len(code)),
            create_tap_data_block(code),
        ]
        tapfile = self._write_tap(blocks)

        exp_data = (
            (basic_data, 23755),
            (code, code_start),
            ([192], 49152)
        )
        exp_reg = {f'PC={start}'}
        exp_output = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            'Bytes: simloadbyt',
            f'Fast loading data block: 32768,{len(code)}',
            'Tape finished',
            f'Simulation stopped (PC at start address): PC={start}'
        ]
        exp_state = {'7ffd=32'}
        self._test_sim_load(f'--start {start} -c machine=128 {tapfile} out.z80', exp_data, exp_reg, exp_output, exp_state)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_option_press(self):
        basic_data = [
            0, 10,                # Line 10
            21, 0,                # Line length
            234,                  # REM
            62, 247,              # 23760 LD A,247
            219, 254,             # 23762 IN A,(254)  ; Read keys 1-2-3-4-5
            31,                   # 23764 RRA         ; Is '1' being pressed?
            56, 249,              # 23765 JR C,23760  ; Jump back if not
            221, 33, 0, 128,      # 23767 LD IX,32768
            17, 1, 0,             # 23771 LD DE,1
            55,                   # 23774 SCF
            159,                  # 23775 SBC A,A
            195, 86, 5,           # 23776 JP 1366
            13,                   # ENTER
            0, 20,                # Line 20
            10, 0,                # Line length
            249, 192, 46,         # RANDOMIZE USR .
            14, 0, 0, 208, 92, 0, # 23760
            13                    # ENTER
        ]
        blocks = [
            create_tap_header_block("simloadbas", 20, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_data_block([255]),
        ]
        tapfile = self._write_tap(blocks)
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,39',
            'Tape paused',
            'Pressing keys: 1',
            'Resuming LOAD',
            'Fast loading data block: 32768,1',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=1343'
        ]
        output, error = self.run_tap2sna(f'--press 3:1 --start 1343 -c finish-tape=1 {tapfile} out.z80')
        self.assertEqual(exp_out_lines, output.strip().split('\n'))
        self.assertEqual(error, '')
        exp_reg = set(('SP=65344', 'IX=32769', 'IY=23610', 'PC=1343'))
        self.assertLessEqual(exp_reg, set(options.reg))
        self.assertEqual(snapshot[32768], 255)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_option_press_two_keys(self):
        basic_data = [
            0, 10,                # Line 10
            28, 0,                # Line length
            234,                  # REM
            62, 247,              # 23760 LD A,247
            219, 254,             # 23762 IN A,(254)  ; Read keys 1-2-3-4-5
            31,                   # 23764 RRA         ; Is '1' being pressed?
            56, 249,              # 23765 JR C,23760  ; Jump back if not
            62, 191,              # 23767 LD A,191
            219, 254,             # 23769 IN A,(254)  ; Read keys ENTER-L-K-J-H
            31,                   # 23771 RRA         ; Is ENTER being pressed?
            56, 249,              # 23772 JR C,23767  ; Jump back if not
            221, 33, 0, 128,      # 23774 LD IX,32768
            17, 1, 0,             # 23778 LD DE,1
            55,                   # 23781 SCF
            159,                  # 23782 SBC A,A
            195, 86, 5,           # 23783 JP 1366
            13,                   # ENTER
            0, 20,                # Line 20
            10, 0,                # Line length
            249, 192, 46,         # RANDOMIZE USR .
            14, 0, 0, 208, 92, 0, # 23760
            13                    # ENTER
        ]
        blocks = [
            create_tap_header_block("simloadbas", 20, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_data_block([255]),
        ]
        tapfile = self._write_tap(blocks)
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,46',
            'Tape paused',
            'Pressing keys: 1 ENTER',
            'Resuming LOAD',
            'Fast loading data block: 32768,1',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=1343'
        ]
        output, error = self.run_tap2sna(('--press', '3:1 ENTER', '--start', '1343', '-c', 'finish-tape=1', tapfile, 'out.z80'))
        self.assertEqual(exp_out_lines, output.strip().split('\n'))
        self.assertEqual(error, '')
        exp_reg = set(('SP=65344', 'IX=32769', 'IY=23610', 'PC=1343'))
        self.assertLessEqual(exp_reg, set(options.reg))
        self.assertEqual(snapshot[32768], 255)

    @patch.object(tap2sna, '_write_snapshot', mock_write_snapshot)
    def test_option_press_multiple(self):
        basic_data = [
            0, 10,              # Line 10
            40, 0,              # Line length
            234,                # REM
            62, 247,            # 23760 LD A,247
            219, 254,           # 23762 IN A,(254)  ; Read keys 1-2-3-4-5
            31,                 # 23764 RRA         ; Is '1' being pressed?
            56, 249,            # 23765 JR C,23760  ; Jump back if not
            221, 33, 0, 128,    # 23767 LD IX,32768
            17, 1, 0,           # 23771 LD DE,1
            55,                 # 23774 SCF
            159,                # 23775 SBC A,A
            205, 86, 5,         # 23776 CALL 1366
            62, 191,            # 23779 LD A,191
            219, 254,           # 23781 IN A,(254)  ; Read keys ENTER-L-K-J-H
            31,                 # 23783 RRA         ; Is 'ENTER' being pressed?
            56, 249,            # 23784 JR C,23779  ; Jump back if not
            221, 33, 0, 192,    # 23786 LD IX,49152
            17, 1, 0,           # 23790 LD DE,1
            55,                 # 23793 SCF
            159,                # 23794 SBC A,A
            195, 86, 5,         # 23795 JP 1366
            13,                 # ENTER
            0, 20,              # Line 20
            10, 0,              # Line length
            249, 192, 46,       # RANDOMIZE USR .
            14,                 # Floating-point number marker
            0, 0, 208, 92, 0,   # 23760
            13                  # ENTER
        ]
        blocks = [
            create_tap_header_block("simloadbas", 20, len(basic_data), 0),
            create_tap_data_block(basic_data),
            create_tap_data_block([255]),
            create_tap_data_block([1]),
        ]
        tapfile = self._write_tap(blocks)
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,58',
            'Tape paused',
            'Pressing keys: 1',
            'Resuming LOAD',
            'Fast loading data block: 32768,1',
            'Tape paused',
            'Pressing keys: ENTER',
            'Resuming LOAD',
            'Fast loading data block: 49152,1',
            'Tape finished',
            'Simulation stopped (PC at start address): PC=1343'
        ]
        output, error = self.run_tap2sna(f'--press 3:1 --press 4:ENTER --start 1343 -c finish-tape=1 {tapfile} out.z80')
        self.assertEqual(exp_out_lines, output.strip().split('\n'))
        self.assertEqual(error, '')
        exp_reg = set(('SP=65344', 'IX=49153', 'IY=23610', 'PC=1343'))
        self.assertLessEqual(exp_reg, set(options.reg))
        self.assertEqual(snapshot[32768], 255)
        self.assertEqual(snapshot[49152], 1)
