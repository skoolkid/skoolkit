# Copyright 2013, 2015-2018, 2020-2024 Richard Dymond (rjdymond@gmail.com)
#
# This file is part of SkoolKit.
#
# SkoolKit is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# SkoolKit is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# SkoolKit. If not, see <http://www.gnu.org/licenses/>.

from skoolkit import SkoolKitError, as_dword, get_word, get_word3, get_dword, read_bin_file
from skoolkit.basic import get_char

ARCHIVE_INFO = {
    0: "Full title",
    1: "Software house/publisher",
    2: "Author(s)",
    3: "Year of publication",
    4: "Language",
    5: "Game/utility type",
    6: "Price",
    7: "Protection scheme/loader",
    8: "Origin",
    255: "Comment(s)"
}

HARDWARE_TYPE = {
    0: ('Computer', {
        0x00: 'ZX Spectrum 16K',
        0x01: 'ZX Spectrum 48K Plus',
        0x02: 'ZX Spectrum 48K Issue 1',
        0x03: 'ZX Spectrum 128K + (Sinclair)',
        0x04: 'ZX Spectrum 128K +2 (grey case)',
        0x05: 'ZX Spectrum 128K +2A, +3',
        0x06: 'Timex Sinclair TC-2048',
        0x07: 'Timex Sinclair TS-2068',
        0x08: 'Pentagon 128',
        0x09: 'Sam Coupe',
        0x0A: 'Didaktik M',
        0x0B: 'Didaktik Gama',
        0x0C: 'ZX-80',
        0x0D: 'ZX-81',
        0x0E: 'ZX Spectrum 128K, Spanish version',
        0x0F: 'ZX Spectrum, Arabic version',
        0x10: 'Microdigital TK 90-X',
        0x11: 'Microdigital TK 95',
        0x12: 'Byte',
        0x13: 'Elwro 800-3',
        0x14: 'ZS Scorpion 256',
        0x15: 'Amstrad CPC 464',
        0x16: 'Amstrad CPC 664',
        0x17: 'Amstrad CPC 6128',
        0x18: 'Amstrad CPC 464+',
        0x19: 'Amstrad CPC 6128+',
        0x1A: 'Jupiter ACE',
        0x1B: 'Enterprise',
        0x1C: 'Commodore 64',
        0x1D: 'Commodore 128',
        0x1E: 'Inves Spectrum+',
        0x1F: 'Profi',
        0x20: 'GrandRomMax',
        0x21: 'Kay 1024',
        0x22: 'Ice Felix HC 91',
        0x23: 'Ice Felix HC 2000',
        0x24: 'Amaterske RADIO Mistrum',
        0x25: 'Quorum 128',
        0x26: 'MicroART ATM',
        0x27: 'MicroART ATM Turbo 2',
        0x28: 'Chrome',
        0x29: 'ZX Badaloc',
        0x2A: 'TS-1500',
        0x2B: 'Lambda',
        0x2C: 'TK-65',
        0x2D: 'ZX-97'
    }),
    1: ('External storage', {
        0x00: 'ZX Microdrive',
        0x01: 'Opus Discovery',
        0x02: 'MGT Disciple',
        0x03: 'MGT Plus-D',
        0x04: 'Rotronics Wafadrive',
        0x05: 'TR-DOS (BetaDisk)',
        0x06: 'Byte Drive',
        0x07: 'Watsford',
        0x08: 'FIZ',
        0x09: 'Radofin',
        0x0A: 'Didaktik disk drives',
        0x0B: 'BS-DOS (MB-02)',
        0x0C: 'ZX Spectrum +3 disk drive',
        0x0D: 'JLO (Oliger) disk interface',
        0x0E: 'Timex FDD3000',
        0x0F: 'Zebra disk drive',
        0x10: 'Ramex Millenia',
        0x11: 'Larken',
        0x12: 'Kempston disk interface',
        0x13: 'Sandy',
        0x14: 'ZX Spectrum +3e hard disk',
        0x15: 'ZXATASP',
        0x16: 'DivIDE',
        0x17: 'ZXCF'
    }),
    2: ('ROM/RAM add-on', {
        0x00: 'Sam Ram',
        0x01: 'Multiface ONE',
        0x02: 'Multiface 128k',
        0x03: 'Multiface +3',
        0x04: 'MultiPrint',
        0x05: 'MB-02 ROM/RAM expansion',
        0x06: 'SoftROM',
        0x07: '1k',
        0x08: '16k',
        0x09: '48k',
        0x0A: 'Memory in 8-16k used'
    }),
    3: ('Sound device', {
        0x00: 'Classic AY hardware (compatible with 128k ZXs)',
        0x01: 'Fuller Box AY sound hardware',
        0x02: 'Currah microSpeech',
        0x03: 'SpecDrum',
        0x04: 'AY ACB stereo (A+C=left, B+C=right); Melodik',
        0x05: 'AY ABC stereo (A+B=left, B+C=right)',
        0x06: 'RAM Music Machine',
        0x07: 'Covox',
        0x08: 'General Sound',
        0x09: 'Intec Electronics Digital Interface B8001',
        0x0A: 'Zon-X AY',
        0x0B: 'QuickSilva AY',
        0x0C: 'Jupiter ACE'
    }),
    4: ('Joystick', {
        0x00: 'Kempston',
        0x01: 'Cursor, Protek, AGF',
        0x02: 'Sinclair 2 Left (12345)',
        0x03: 'Sinclair 1 Right (67890)',
        0x04: 'Fuller'
    }),
    5: ('Mouse', {
        0x00: 'AMX mouse',
        0x01: 'Kempston mouse'
    }),
    6: ('Other controller', {
        0x00: 'Trickstick',
        0x01: 'ZX Light Gun',
        0x02: 'Zebra Graphics Tablet',
        0x03: 'Defender Light Gun'
    }),
    7: ('Serial port', {
        0x00: 'ZX Interface 1',
        0x01: 'ZX Spectrum 128k'
    }),
    8: ('Parallel port', {
        0x00: 'Kempston S',
        0x01: 'Kempston E',
        0x02: 'ZX Spectrum +3',
        0x03: 'Tasman',
        0x04: "DK'Tronics",
        0x05: 'Hilderbay',
        0x06: 'INES Printerface',
        0x07: 'ZX LPrint Interface 3',
        0x08: 'MultiPrint',
        0x09: 'Opus Discovery',
        0x0A: 'Standard 8255 chip with ports 31,63,95',
    }),
    9: ('Printer', {
        0x00: 'ZX Printer, Alphacom 32 & compatibles',
        0x01: 'Generic printer',
        0x02: 'EPSON compatible'
    }),
    10: ('Modem', {
        0x00: 'Prism VTX 5000',
        0x01: 'T/S 2050 or Westridge 2050'
    }),
    11: ('Digitizer', {
        0x00: 'RD Digital Tracer',
        0x01: "DK'Tronics Light Pen",
        0x02: 'British MicroGraph Pad',
        0x03: 'Romantic Robot Videoface'
    }),
    12: ('Network adapter', {
        0x00: 'ZX Interface 1'
    }),
    13: ('Keypad', {
        0x00: 'Keypad for ZX Spectrum 128k'
    }),
    14: ('AD/DA converter', {
        0x00: 'Harley Systems ADC 8.2',
        0x01: 'Blackboard Electronics'
    }),
    15: ('EPROM programmer', {
        0x00: 'Orme Electronics'
    }),
    16: ('Graphics', {
        0x00: 'WRX Hi-Res',
        0x01: 'G007',
        0x02: 'Memotech',
        0x03: 'Lambda Colour'
    })
}

HARDWARE_INFO = {
    0: {
        0: 'Runs on this machine, but may not use its special features',
        1: 'Uses special features of this machine',
        2: 'Runs on this machine, but does not use its special features',
        3: 'Does not run on this machine'
    },
    1: {
        0: 'Runs with this hardware, but may not use it',
        1: 'Uses this hardware',
        2: 'Runs but does not use this hardware',
        3: 'Does not run with this hardware'
    }
}

CHARS = {9: '\t', 13: '\n'}

class Tape:
    def __init__(self, blocks, version=None, warnings=()):
        self.blocks = blocks
        self.version = version
        self.warnings = warnings

class TapeBlock:
    def __init__(self, number, tape_data, timings=None, block_id=None, name=None, info=(), standard=True, block_data=None):
        self.number = number
        self.data = tape_data
        self.timings = timings
        self.block_id = block_id
        self.name = name
        self.info = info
        self.standard = standard
        self.block_data = block_data

class TapeBlockTimings:
    def __init__(self, pulses=(), zero=None, one=None, pause=0, used_bits=8,
                 data=False, tail=0, polarity=None, error=None):
        self.pulses = pulses
        self.zero = zero
        self.one = one
        self.pause = pause
        self.used_bits = used_bits
        self.data = data
        self.tail = tail
        self.polarity = polarity
        self.error = error

def _get_tape_block_timings(first_byte, pause=3500000):
    pulses = ((3223 + 4840 * (first_byte == 0), 2168), (1, 667), (1, 735))
    return TapeBlockTimings(pulses, (855, 855), (1710, 1710), pause)

def _get_str(data, dump=False):
    if dump and any(b > 127 or (b < 31 and b not in CHARS) for b in data):
        return '\n'.join(hex_dump(data))
    text = ''
    for b in data:
        if b in CHARS:
            text += CHARS[b]
        else:
            text += get_char(b, '?', '?')
    return text

def _format_text(prefix, data, start, length, dump=False):
    text = _get_str(data[start:start + length], dump).split('\n')
    lines = [f'{prefix}: {text[0]}']
    if len(text) > 1:
        indent = ' ' * len(prefix)
        for line in text[1:]:
            lines.append(f'{indent}  {line}')
    return lines

def _get_pzx_block(data, i, block_num, prev_rom_pilot):
    # http://zxds.raxoft.cz/docs/pzx.txt
    block_id = ''.join(chr(b) for b in data[i:i + 4])
    block_len = get_dword(data, i + 4)
    block_data = None
    tape_data = None
    timings = None
    standard = False
    rom_pilot = False
    info = []
    if block_id == 'PZXT':
        name = 'PZX header block'
        info.append(f'Version: {data[i + 8]}.{data[i + 9]}')
        pairs = ['Title', '']
        j = i + 10
        while j < i + 8 + block_len:
            b = data[j]
            if b:
                pairs[-1] += chr(b)
            else:
                if len(pairs) == 2:
                    info.append(f'{pairs[0]}: {pairs[1]}')
                    pairs.clear()
                pairs.append('')
            j += 1
        if len(pairs) == 2 and pairs[1]:
            info.append(f'{pairs[0]}: {pairs[1]}')
    elif block_id == 'PULS':
        name = 'Pulse sequence'
        pulses = []
        j = i + 8
        while j < i + 8 + block_len:
            count = 1
            duration = get_word(data, j)
            j += 2
            if duration > 0x8000:
                count = duration % 0x8000
                duration = get_word(data, j)
                j += 2
            if duration >= 0x8000:
                duration = (duration % 0x8000) * 65536 + get_word(data, j)
                j += 2
            info.append(f'{count} x {duration} T-states')
            pulses.append((count, duration))
        rom_pilot = len(pulses) == 3 and pulses[0] in ((3223, 2168), (8063, 2168)) and pulses[1:] == [(1, 667), (1, 735)]
        if pulses and pulses[0][0] % 2 and pulses[0][1] == 0:
            pulses.pop(0)
            polarity = 1
        else:
            polarity = 0
        timings = TapeBlockTimings(pulses, polarity=polarity)
    elif block_id == 'DATA':
        name = 'Data block'
        count = get_dword(data, i + 8)
        bits = count % 0x80000000
        polarity = count >> 31
        num_bytes = bits // 8
        used_bits = (bits % 8) or 8
        tail = get_word(data, i + 12)
        p0, p1 = data[i + 14:i + 16]
        j = i + 16
        s0 = [get_word(data, k) for k in range(j, j + 2 * p0, 2)]
        j += 2 * p0
        s1 = [get_word(data, k) for k in range(j, j + 2 * p1, 2)]
        j += 2 * p1
        tape_data = data[j:j + num_bytes + int(used_bits < 8)]
        standard = prev_rom_pilot and p0 == 2 and p1 == 2 and s0 == [855, 855] and s1 == [1710, 1710]
        if used_bits < 8:
            info.append(f'Bits: {bits} ({num_bytes} bytes + {used_bits} bits)')
        else:
            info.append(f'Bits: {bits} ({num_bytes} bytes)')
        info.extend((
            f'Initial pulse level: {polarity}',
            '0-bit pulse sequence: {} (T-states)'.format(', '.join(str(p) for p in s0)),
            '1-bit pulse sequence: {} (T-states)'.format(', '.join(str(p) for p in s1)),
            f'Tail pulse: {tail} T-states'
        ))
        timings = TapeBlockTimings(zero=s0, one=s1, used_bits=used_bits, tail=tail, polarity=polarity)
    elif block_id == 'PAUS':
        name = 'Pause'
        duration = get_dword(data, i + 8)
        polarity = duration >> 31
        info.extend((
            f'Duration: {duration % 0x80000000} T-states',
            f'Initial pulse level: {polarity}',
        ))
        timings = TapeBlockTimings(pause=duration % 0x80000000, polarity=polarity)
    elif block_id == 'BRWS':
        name = 'Browse point'
        info.append(''.join(chr(b) for b in data[i + 8:i + 8 + block_len]))
    elif block_id == 'STOP':
        name = 'Stop tape command'
        flags = get_word(data, i + 8)
        mode = ('Always', '48K only')[flags & 1]
        info.append(f'Mode: {mode}')
        block_data = data[i + 8:i + 8 + block_len]
    else:
        name = block_id
    block = TapeBlock(block_num, tape_data, timings, block_id, name, info, standard, block_data)
    return i + 8 + block_len, block, rom_pilot

def _get_tzx_block(data, i, block_num, get_info, get_timings):
    # https://worldofspectrum.net/features/TZXformat.html
    block_id = data[i]
    block_data = None
    tape_data = None
    info = []
    timings = None
    standard = False
    i += 1
    if block_id == 0x10:
        # Standard speed data block
        header = 'Standard speed data'
        pause = get_word(data, i)
        length = get_word(data, i + 2)
        tape_data = data[i + 4:i + 4 + length]
        standard = True
        if get_info:
            info.append(f'Pause: {pause}ms')
        if get_timings and tape_data:
            timings = _get_tape_block_timings(tape_data[0], pause * 3500)
        i += 4 + length
    elif block_id == 0x11:
        # Turbo speed data block
        header = 'Turbo speed data'
        pilot = get_word(data, i)
        sync1 = get_word(data, i + 2)
        sync2 = get_word(data, i + 4)
        zero = get_word(data, i + 6)
        one = get_word(data, i + 8)
        pilot_len = get_word(data, i + 10)
        used_bits = data[i + 12]
        pause = get_word(data, i + 13)
        if get_info:
            info.extend((
                f'Pilot pulse: {pilot}',
                f'Sync pulse 1: {sync1}',
                f'Sync pulse 2: {sync2}',
                f'0-pulse: {zero}',
                f'1-pulse: {one}',
                f'Pilot length: {pilot_len} pulses',
                f'Used bits in last byte: {used_bits}',
                f'Pause: {pause}ms'
            ))
        if get_timings:
            pulses = ((pilot_len, pilot), (1, sync1), (1, sync2))
            timings = TapeBlockTimings(pulses, (zero, zero), (one, one), pause * 3500, used_bits)
        length = get_word3(data, i + 15)
        tape_data = data[i + 18:i + 18 + length]
        i += 18 + length
    elif block_id == 0x12:
        # Pure tone
        header = 'Pure tone'
        pulse_len = get_word(data, i)
        num_pulses = get_word(data, i + 2)
        if get_info:
            info.extend((
                f'Pulse length: {pulse_len} T-states',
                f'Pulses: {num_pulses}'
            ))
        if get_timings:
            timings = TapeBlockTimings([(num_pulses, pulse_len)])
        i += 4
    elif block_id == 0x13:
        # Sequence of pulses of various lengths
        header = 'Pulse sequence'
        num_pulses = data[i]
        i += 1
        pulses = []
        for pulse in range(num_pulses):
            pulse_len = get_word(data, i)
            if get_info:
                info.append('Pulse {}/{}: {}'.format(pulse + 1, num_pulses, pulse_len))
            if get_timings:
                pulses.append((1, pulse_len))
            i += 2
        if get_timings:
            timings = TapeBlockTimings(pulses)
    elif block_id == 0x14:
        # Pure data block
        header = 'Pure data'
        zero = get_word(data, i)
        one = get_word(data, i + 2)
        used_bits = data[i + 4]
        pause = get_word(data, i + 5)
        if get_info:
            info.extend((
                f'0-pulse: {zero}',
                f'1-pulse: {one}',
                f'Used bits in last byte: {used_bits}',
                f'Pause: {pause}ms'
            ))
        if get_timings:
            timings = TapeBlockTimings((), (zero, zero), (one, one), pause * 3500, used_bits)
        length = get_word3(data, i + 7)
        tape_data = data[i + 10:i + 10 + length]
        i += length + 10
    elif block_id == 0x15:
        # Direct recording block
        header = 'Direct recording'
        tps = get_word(data, i)
        pause = get_word(data, i + 2)
        used_bits = data[i + 4]
        num_bytes = get_word3(data, i + 5)
        if get_info:
            info.extend((
                f'T-states per sample: {tps}',
                f'Pause: {pause}ms',
                f'Used bits in last byte: {used_bits}',
                f'Length: {num_bytes}'
            ))
        if get_timings:
            j = 0
            pulses = []
            prev_bit = data[i + 8] & 0x80
            if prev_bit:
                pulses.append((1, 0))
            bit_count = 0
            for j, b in enumerate(data[i + 8:i + 8 + num_bytes], 1):
                if j < num_bytes:
                    num_bits = 8
                else:
                    num_bits = used_bits
                for k in range(num_bits):
                    bit = b & 0x80
                    if bit == prev_bit:
                        bit_count += 1
                    else:
                        pulses.append((1, bit_count * tps))
                        prev_bit = bit
                        bit_count = 1
                    b *= 2
            pulses.append((1, bit_count * tps))
            tape_data = []
            timings = TapeBlockTimings(pulses, pause=pause * 3500, data=True)
        i += 8 + num_bytes
    elif block_id == 0x16:
        # C64 ROM type data
        header = 'C64 ROM type data'
        if get_timings:
            timings = TapeBlockTimings(error="TZX C64 ROM type data (0x16) not supported")
        i += get_dword(data, i) + 4
    elif block_id == 0x17:
        # C64 turbo tape data
        header = 'C64 turbo tape data'
        if get_timings:
            timings = TapeBlockTimings(error="TZX C64 turbo tape data (0x17) not supported")
        i += get_dword(data, i) + 4
    elif block_id == 0x18:
        # CSW recording block
        header = 'CSW recording'
        if get_info:
            info.extend((
                'Number of pulses: {}'.format(get_dword(data, i + 10)),
                'Sampling rate: {} Hz'.format(get_word3(data, i + 6)),
                'Compression type: {}'.format({1: 'RLE', 2: 'Z-RLE'}.get(data[i + 9], 'Unknown')),
                'Pause: {}ms'.format(get_word(data, i + 4))
            ))
        if get_timings:
            timings = TapeBlockTimings(error='TZX CSW Recording (0x18) not supported')
        i += get_dword(data, i) + 4
    elif block_id == 0x19:
        # Generalized data block
        header = 'Generalized data'
        if get_timings:
            timings = TapeBlockTimings(error='TZX Generalized Data Block (0x19) not supported')
        i += get_dword(data, i) + 4
    elif block_id == 0x20:
        # Pause (silence) or 'Stop the tape' command
        pause = get_word(data, i)
        if pause:
            header = "Pause (silence)"
            if get_info:
                info.append(f'Duration: {pause}ms')
        else:
            header = "'Stop the tape' command"
        if get_timings:
            timings = TapeBlockTimings(pause=pause * 3500)
        i += 2
    elif block_id == 0x21:
        # Group start
        header = 'Group start'
        length = data[i]
        if get_info:
            info.extend(_format_text('Name', data, i + 1, length))
        i += length + 1
    elif block_id == 0x22:
        # Group end
        header = 'Group end'
    elif block_id == 0x23:
        # Jump to block
        header = 'Jump to block'
        offset = get_word(data, i)
        if offset > 32767:
            offset -= 65536
        if get_info:
            info.append('Destination block: {}'.format(block_num + offset))
        i += 2
    elif block_id == 0x24:
        # Loop start
        header = 'Loop start'
        block_data = data[i:i + 2]
        if get_info:
            info.append('Repetitions: {}'.format(get_word(data, i)))
        i += 2
    elif block_id == 0x25:
        # Loop end
        header = 'Loop end'
    elif block_id == 0x26:
        # Call sequence
        header = 'Call sequence'
        i += get_word(data, i) * 2 + 2
    elif block_id == 0x27:
        # Return from sequence
        header = 'Return from sequence'
    elif block_id == 0x28:
        # Select block
        header = 'Select block'
        if get_info:
            index = i + 3
            for j in range(data[i + 2]):
                offset = get_word(data, index)
                length = data[index + 2]
                prefix = 'Option {} (block {})'.format(j + 1, block_num + offset)
                info.extend(_format_text(prefix, data, index + 3, length))
                index += length + 3
        i += get_word(data, i) + 2
    elif block_id == 0x2A:
        # Stop the tape if in 48K mode
        header = 'Stop the tape if in 48K mode'
        i += 4
    elif block_id == 0x2B:
        # Set signal level
        header = 'Set signal level'
        if get_info:
            level = data[i + 4]
            level_desc = ('low', 'high')[level > 0]
            info.append(f'Signal level: {level} ({level_desc})')
        i += 5
    elif block_id == 0x30:
        # Text description
        header = 'Text description'
        length = data[i]
        if get_info:
            info.extend(_format_text('Text', data, i + 1, length))
        i += length + 1
    elif block_id == 0x31:
        # Message block
        header = 'Message'
        length = data[i + 1]
        if get_info:
            info.extend(_format_text('Message', data, i + 2, length))
        i += length + 2
    elif block_id == 0x32:
        # Archive info
        header = 'Archive info'
        if get_info:
            num_strings = data[i + 2]
            j = i + 3
            for k in range(num_strings):
                try:
                    str_len = data[j + 1]
                except IndexError:
                    raise SkoolKitError('Unexpected end of file')
                info.extend(_format_text(ARCHIVE_INFO.get(data[j], str(data[j])), data, j + 2, str_len))
                j += 2 + str_len
        i += get_word(data, i) + 2
    elif block_id == 0x33:
        # Hardware type
        header = 'Hardware type'
        if get_info:
            i += 1
            for j in range(data[i - 1]):
                hw_type, hw_ids = HARDWARE_TYPE.get(data[i], ('Unknown', {}))
                info.extend((
                    '- Type: {}'.format(hw_type),
                    '  Name: {}'.format(hw_ids.get(data[i + 1], 'Unknown')),
                    '  Info: {}'.format(HARDWARE_INFO[data[i] > 0].get(data[i + 2], 'Unknown'))
                ))
                i += 3
        else:
            i += data[i] * 3 + 1
    elif block_id == 0x34:
        # Emulation info
        header = 'Emulation info'
        i += 8
    elif block_id == 0x35:
        # Custom info block
        header = 'Custom info'
        length = get_dword(data, i + 16)
        if get_info:
            ident = _get_str(data[i:i + 16]).strip()
            info.extend(_format_text(ident, data, i + 20, length, True))
        i += length + 20
    elif block_id == 0x40:
        # Snapshot block
        header = 'Snapshot'
        i += get_word3(data, i + 1) + 4
    elif block_id == 0x5A:
        # "Glue" block
        header = '"Glue" block'
        i += 9
    else:
        raise SkoolKitError(f'Unknown TZX block ID: 0x{block_id:02X}')
    return i, TapeBlock(block_num, tape_data, timings, block_id, header, info, standard, block_data)

def hex_dump(data, row_size=16):
    lines = []
    for index in range(0, len(data), row_size):
        values = data[index:index + row_size]
        values_hex = ' '.join('{:02X}'.format(b) for b in values).ljust(row_size * 3)
        values_text = ''.join(get_char(b, '.', '.') for b in values)
        lines.append(f'{index:04X}  {values_hex} {values_text}')
    return lines

def parse_pzx(pzx, start=1, stop=0):
    if isinstance(pzx, str):
        pzx = read_bin_file(pzx)
    if pzx[:4] != b'PZXT':
        raise SkoolKitError('Not a PZX file')
    blocks = []
    block_num = 1
    rom_pilot = False
    i = 0
    while i < len(pzx):
        if block_num >= stop > 0:
            break
        i, block, rom_pilot = _get_pzx_block(pzx, i, block_num, rom_pilot)
        if block_num >= start:
            blocks.append(block)
        block_num += 1
    return Tape(blocks)

def parse_tap(tap, start=1, stop=0):
    if isinstance(tap, str):
        tap = read_bin_file(tap)
    blocks = []
    block_num = 1
    i = 0
    while i + 1 < len(tap):
        if block_num >= stop > 0:
            break
        block_len = get_word(tap, i)
        if block_num >= start:
            data = tap[i + 2:i + 2 + block_len]
            if data:
                timings = _get_tape_block_timings(data[0])
            else:
                timings = None
            blocks.append(TapeBlock(block_num, data, timings))
        i += block_len + 2
        block_num += 1
    warnings = []
    if block_num != stop:
        if i < len(tap):
            warnings.append('Extraneous byte at end of file')
        elif i > len(tap):
            warnings.append(f'Missing {i - len(tap)} data byte(s) at end of file')
    return Tape(blocks, warnings=warnings)

def parse_tzx(tzx, start=1, stop=0, info=True, timings=False):
    if isinstance(tzx, str):
        tzx = read_bin_file(tzx)
    if tzx[:8] != b'ZXTape!\x1a':
        raise SkoolKitError('Not a TZX file')
    try:
        version = f'{tzx[8]}.{tzx[9]:02}'
    except IndexError:
        raise SkoolKitError('TZX version number not found')
    blocks = []
    block_num = 1
    i = 10
    while i < len(tzx):
        if block_num >= stop > 0:
            break
        i, block = _get_tzx_block(tzx, i, block_num, info, timings)
        if block_num >= start:
            blocks.append(block)
        block_num += 1
    return Tape(blocks, version)

def write_tap(fname, blocks):
    with open(fname, 'wb') as f:
        for data in blocks:
            length = len(data)
            f.write(bytes((length % 256, length // 256)))
            f.write(bytes(data))

def write_pzx(fname, blocks):
    with open(fname, 'wb') as f:
        f.write(b'PZXT\x02\x00\x00\x00\x01\x00')
        for i, data in enumerate(blocks):
            if i:
                f.write(b'PAUS\x04\x00\x00\x00\xe0\x67\x35\x00')
            if data[0]:
                f.write(b'PULS\x08\x00\x00\x00\x97\x8c\x78\x08\x9b\x02\xdf\x02')
            else:
                f.write(b'PULS\x08\x00\x00\x00\x7f\x9f\x78\x08\x9b\x02\xdf\x02')
            length = len(data)
            bits = 0x80000000 + length * 8
            f.write(bytes((
                68, 65, 84, 65,         # DATA
                *as_dword(length + 16), # Block length
                *as_dword(bits),        # Polarity and bit count
                177, 3,                 # Tail pulse (945)
                2,                      # p0
                2,                      # p1
                87, 3, 87, 3,           # s0 (855, 855)
                174, 6, 174, 6,         # s1 (1710, 1710)
                *data                   # Data
            )))
