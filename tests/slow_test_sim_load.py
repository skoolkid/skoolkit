from unittest.mock import patch

from skoolkittest import (SkoolKitTestCase, create_data_block,
                          create_tap_header_block, create_tap_data_block,
                          create_tzx_header_block, create_tzx_data_block)
from skoolkit import tap2sna, ROM48, read_bin_file

def mock_write_z80(ram, namespace, z80):
    global snapshot, options
    snapshot = [0] * 16384 + ram
    options = namespace

def create_tzx_turbo_data_block(data, zero, one):
    block = [
        17,                      # Block ID
        120, 8,                  # Length of PILOT pulse (2168)
        155, 2,                  # Length of first SYNC pulse (667)
        223, 2,                  # Length of second SYNC pulse (735)
        zero % 256, zero // 256, # Length of ZERO bit pulse
        one % 256, one // 256,   # Length of ONE bit pulse
        151, 12,                 # Length of PILOT tone (3223)
        8,                       # Used bits in the last byte
        0, 0,                    # Pause after this block (0)
    ]
    data_block = create_data_block(data)
    block.extend((len(data_block) % 256, len(data_block) // 256, 0))
    block.extend(data_block)
    return block

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

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
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
        z80file = 'out.z80'
        output, error = self.run_tap2sna(f'--sim-load {tapfile} {z80file}')

        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        self.assertEqual(code2, snapshot[code2_start:code2_end])
        exp_reg = set(('SP=65340', f'IX={code2_end}', 'IY=23610', 'PC=32925'))
        self.assertLessEqual(exp_reg, set(options.reg))

        out_lines = self._format_output(output)
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            '',
            'Bytes: simloadbyt',
            'Fast loading data block: 32759,184',
            '',
            'Pilot tone',
            'Sync pulses',
            'Data (12 bytes)',
            'Loaded bytes: 49152,10',
            '',
            'Tape finished',
            'Simulation ended: PC=32925'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
    def test_turbo_loader(self):
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
        z80file = 'out.z80'
        output, error = self.run_tap2sna(f'--sim-load {tzxfile} {z80file}')

        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        self.assertEqual(code2, snapshot[code2_start:code2_end])
        exp_reg = set(('SP=65340', f'IX={code2_end}', 'IY=23610', 'PC=32925'))
        self.assertLessEqual(exp_reg, set(options.reg))

        out_lines = self._format_output(output)
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            '',
            'Bytes: simloadbyt',
            'Fast loading data block: 32759,184',
            '',
            'Pilot tone',
            'Sync pulses',
            'Data (12 bytes)',
            'Loaded bytes: 49152,10',
            '',
            'Tape finished',
            'Simulation ended: PC=32925'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')

    @patch.object(tap2sna, '_write_z80', mock_write_z80)
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
        pure_data = [
            0x14,             # Block ID (Pure Data)
            87, 3,            # 855 (length of 0-bit pulse)
            174, 6,           # 1710 (length of 1-bit pulse)
            8,                # Used bits in last byte
            0, 0,             # 0ms (pause)
            len(pdata), 0, 0, # Data length
            *pdata,           # Data
        ]
        blocks = [
            create_tzx_header_block("simloadbas", 10, len(basic_data), 0),
            create_tzx_data_block(basic_data),
            create_tzx_header_block("simloadbyt", code_start, len(code), 3),
            create_tzx_data_block(code),
            pure_tone,
            pulse_sequence,
            pure_data,
        ]
        tzxfile = self._write_tzx(blocks)
        z80file = 'out.z80'
        output, error = self.run_tap2sna(f'--sim-load {tzxfile} {z80file}')

        self.assertEqual(basic_data, snapshot[23755:23755 + len(basic_data)])
        self.assertEqual(code, snapshot[code_start:code_start + len(code)])
        self.assertEqual(code2, snapshot[code2_start:code2_end])
        exp_reg = set(('SP=65340', f'IX={code2_end}', 'IY=23610', 'PC=32925'))
        self.assertLessEqual(exp_reg, set(options.reg))

        out_lines = self._format_output(output)
        exp_out_lines = [
            'Program: simloadbas',
            'Fast loading data block: 23755,20',
            '',
            'Bytes: simloadbyt',
            'Fast loading data block: 32759,184',
            '',
            'Pilot tone',
            'Sync pulses',
            'Data (12 bytes)',
            'Loaded bytes: 49152,10',
            '',
            'Tape finished',
            'Simulation ended: PC=32925'
        ]
        self.assertEqual(exp_out_lines, out_lines)
        self.assertEqual(error, '')
