# Copyright 2013, 2015, 2017, 2020 Richard Dymond (rjdymond@gmail.com)
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

import argparse

from skoolkit import SkoolKitError, get_word, get_word3, get_dword, get_int_param, VERSION
from skoolkit.basic import BasicLister, get_char

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

def _bytes_to_str(data):
    return ', '.join(str(b) for b in data)

def _hex_dump(data, as_lines=True, row_size=16):
    lines = []
    for index in range(0, len(data), row_size):
        values = data[index:index + row_size]
        values_hex = ' '.join('{:02X}'.format(b) for b in values).ljust(row_size * 3)
        values_text = ''.join(get_char(b, '.', '.') for b in values)
        lines.append('{:04X}  {} {}'.format(index, values_hex, values_text))
    if as_lines:
        return lines
    return '\n'.join(lines)

def _get_str(data, dump=False):
    if dump and any(b > 127 or (b < 31 and b not in CHARS) for b in data):
        return _hex_dump(data, False)
    text = ''
    for b in data:
        if b in CHARS:
            text += CHARS[b]
        else:
            text += get_char(b, '?', '?')
    return text

def _format_text(prefix, data, start, length, dump=False):
    text = _get_str(data[start:start + length], dump).split('\n')
    lines = ['{}: {}'.format(prefix, text[0])]
    if len(text) > 1:
        indent = ' ' * len(prefix)
        for line in text[1:]:
            lines.append('{}  {}'.format(indent, line))
    return lines

def _get_block_info(data, i, block_num):
    # https://worldofspectrum.net/features/TZXformat.html
    block_id = data[i]
    info = []
    tape_data = []
    i += 1
    if block_id == 16:
        header = 'Standard speed data'
        length = get_word(data, i + 2)
        tape_data = data[i + 4:i + 4 + length]
        i += 4 + length
    elif block_id == 17:
        header = 'Turbo speed data'
        length = get_word3(data, i + 15)
        tape_data = data[i + 18:i + 18 + length]
        i += 18 + length
    elif block_id == 18:
        header = 'Pure tone'
        info.append('Pulse length: {} T-states'.format(get_word(data, i)))
        info.append('Pulses: {}'.format(get_word(data, i + 2)))
        i += 4
    elif block_id == 19:
        header = 'Pulse sequence'
        num_pulses = data[i]
        i += 1
        for pulse in range(num_pulses):
            info.append('Pulse {}/{}: {}'.format(pulse + 1, num_pulses, get_word(data, i)))
            i += 2
    elif block_id == 20:
        header = 'Pure data'
        info.append('0-pulse: {}'.format(get_word(data, i)))
        info.append('1-pulse: {}'.format(get_word(data, i + 2)))
        info.append('Used bits in last byte: {}'.format(data[i + 4]))
        info.append('Pause: {}ms'.format(get_word(data, i + 5)))
        length = get_word3(data, i + 7)
        tape_data = data[i + 10:i + 10 + length]
        i += length + 10
    elif block_id == 21:
        header = 'Direct recording'
        i += get_word3(data, i + 5) + 8
    elif block_id == 24:
        header = 'CSW recording'
        i += get_dword(data, i) + 4
    elif block_id == 25:
        header = 'Generalized data'
        i += get_dword(data, i) + 4
    elif block_id == 32:
        duration = get_word(data, i)
        if duration:
            header = "Pause (silence)"
            info.append('Duration: {}ms'.format(duration))
        else:
            header = "'Stop the tape' command"
        i += 2
    elif block_id == 33:
        header = 'Group start'
        length = data[i]
        info.extend(_format_text('Name', data, i + 1, length))
        i += length + 1
    elif block_id == 34:
        header = 'Group end'
    elif block_id == 35:
        header = 'Jump to block'
        offset = get_word(data, i)
        if offset > 32767:
            offset -= 65536
        info.append('Destination block: {}'.format(block_num + offset))
        i += 2
    elif block_id == 36:
        header = 'Loop start'
        info.append('Repetitions: {}'.format(get_word(data, i)))
        i += 2
    elif block_id == 37:
        header = 'Loop end'
    elif block_id == 38:
        header = 'Call sequence'
        i += get_word(data, i) * 2 + 2
    elif block_id == 39:
        header = 'Return from sequence'
    elif block_id == 40:
        header = 'Select block'
        index = i + 3
        for j in range(data[i + 2]):
            offset = get_word(data, index)
            length = data[index + 2]
            prefix = 'Option {} (block {})'.format(j + 1, block_num + offset)
            info.extend(_format_text(prefix, data, index + 3, length))
            index += length + 3
        i += get_word(data, i) + 2
    elif block_id == 42:
        header = 'Stop the tape if in 48K mode'
        i += 4
    elif block_id == 43:
        header = 'Set signal level'
        i += 5
    elif block_id == 48:
        header = 'Text description'
        length = data[i]
        info.extend(_format_text('Text', data, i + 1, length))
        i += length + 1
    elif block_id == 49:
        header = 'Message'
        length = data[i + 1]
        info.extend(_format_text('Message', data, i + 2, length))
        i += length + 2
    elif block_id == 50:
        header = 'Archive info'
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
    elif block_id == 51:
        header = 'Hardware type'
        i += 1
        for j in range(data[i - 1]):
            hw_type, hw_ids = HARDWARE_TYPE.get(data[i], ('Unknown', {}))
            info.extend((
                '- Type: {}'.format(hw_type),
                '  Name: {}'.format(hw_ids.get(data[i + 1], 'Unknown')),
                '  Info: {}'.format(HARDWARE_INFO[data[i] > 0].get(data[i + 2], 'Unknown'))
            ))
            i += 3
    elif block_id == 53:
        header = 'Custom info'
        ident = _get_str(data[i:i + 16]).strip()
        length = get_dword(data, i + 16)
        info.extend(_format_text(ident, data, i + 20, length, True))
        i += length + 20
    elif block_id == 90:
        header = '"Glue" block'
        i += 9
    else:
        raise SkoolKitError('Unknown block ID: 0x{:02X}'.format(block_id))
    return i, block_id, header, info, tape_data

def _print_info(text):
    print('  ' + text)

def _print_block(index, data, show_data, info=(), block_id=None, header=None):
    if block_id is None:
        print("{}:".format(index))
    else:
        print("{}: {} (0x{:02X})".format(index, header, block_id))
    for line in info:
        _print_info(line)
    if data and block_id in (None, 16):
        data_type = "Unknown"
        name_str = None
        start = None
        if len(data) == 19 and data[0] == 0:
            block_type = data[1]
            if block_type == 0:
                name_str = 'Program'
            elif block_type == 1:
                name_str = 'Number array'
            elif block_type == 2:
                name_str = 'Character array'
            elif block_type == 3:
                name_str = 'Bytes'
                size = get_word(data, 12)
                start = get_word(data, 14)
            if name_str:
                data_type = "Header block"
                name = _get_str(data[2:12])
        elif data[0] == 255:
            data_type = "Data block"
        _print_info("Type: {}".format(data_type))
        if name_str:
            _print_info("{}: {}".format(name_str, name))
        if start is not None:
            _print_info("CODE: {},{}".format(start, size))
    if data:
        _print_info("Length: {}".format(len(data)))
        if show_data:
            for line in _hex_dump(data):
                _print_info(line)
        else:
            if len(data) > 14:
                data_summary = "{} ... {}".format(_bytes_to_str(data[:7]), _bytes_to_str(data[-7:]))
            else:
                data_summary = _bytes_to_str(data)
            _print_info("Data: {}".format(data_summary))

def _list_basic(cur_block_num, data, block_num, address):
    if block_num == cur_block_num:
        snapshot = [0] * address + list(data[1:-1])
        print(BasicLister().list_basic(snapshot))

def _get_basic_block(spec):
    if spec:
        try:
            if ',' in spec:
                params = spec.split(',', 1)
                return get_int_param(params[0]), get_int_param(params[1], True)
            return get_int_param(spec), 23755
        except ValueError:
            raise SkoolKitError('Invalid block specification: {}'.format(spec))

def _analyse_tzx(tzx, basic_block, options):
    if tzx[:8] != bytearray((90, 88, 84, 97, 112, 101, 33, 26)):
        raise SkoolKitError("Not a TZX file")

    try:
        version = 'Version: {}.{}'.format(tzx[8], tzx[9])
        if not basic_block:
            print(version)
    except IndexError:
        raise SkoolKitError('TZX version number not found')

    block_ids = set()
    if options.block_ids:
        for block_id in options.block_ids.split(','):
            try:
                block_ids.add(int(block_id, 16))
            except ValueError:
                block_ids.add(-1)

    block_num = 1
    i = 10
    while i < len(tzx):
        i, block_id, header, info, tape_data = _get_block_info(tzx, i, block_num)
        if basic_block:
            _list_basic(block_num, tape_data, *basic_block)
        elif not block_ids or block_id in block_ids:
            _print_block(block_num, tape_data, options.data, info, block_id, header)
        block_num += 1

def _analyse_tap(tap, basic_block, show_data):
    i = 0
    block_num = 1
    while i < len(tap):
        block_len = get_word(tap, i)
        data = tap[i + 2:i + 2 + block_len]
        if basic_block:
            _list_basic(block_num, data, *basic_block)
        else:
            _print_block(block_num, data, show_data)
        i += block_len + 2
        block_num += 1

def main(args):
    parser = argparse.ArgumentParser(
        usage="tapinfo.py FILE",
        description="Show the blocks in a TAP or TZX file.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-b', '--tzx-blocks', dest='block_ids', metavar='IDs',
                       help="Show TZX blocks with these IDs only. "
                            "'IDs' is a comma-separated list of hexadecimal block IDs, e.g. 10,11,2a.")
    group.add_argument('-B', '--basic', metavar='N[,A]',
                       help='List the BASIC program in block N loaded at address A (default 23755).')
    group.add_argument('-d', '--data', action='store_true',
                       help='Show the entire contents of header and data blocks.')
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    namespace, unknown_args = parser.parse_known_args(args)
    if unknown_args or namespace.infile is None:
        parser.exit(2, parser.format_help())
    infile = namespace.infile
    tape_type = infile[-4:].lower()
    if tape_type not in ('.tap', '.tzx'):
        raise SkoolKitError('Unrecognised tape type')

    basic_block = _get_basic_block(namespace.basic)

    with open(infile, 'rb') as f:
        tape = f.read()

    if tape_type == '.tap':
        _analyse_tap(tape, basic_block, namespace.data)
    else:
        _analyse_tzx(tape, basic_block, namespace)
