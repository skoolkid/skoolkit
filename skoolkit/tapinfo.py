# -*- coding: utf-8 -*-

# Copyright 2013, 2015 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import SkoolKitError, get_word, get_word3, get_dword, VERSION

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

def _bytes_to_str(data):
    return ', '.join(str(b) for b in data)

def _get_str(data):
    text = ''
    for b in data:
        if b == 13:
            char = '\n'
        elif b == 94:
            char = '↑'
        elif b == 96:
            char = '£'
        elif b == 127:
            char = '©'
        elif 32 <= b < 127:
            char = chr(b)
        else:
            char = '?'
        text += char
    return text

def _format_text(prefix, data, start, length):
    text = _get_str(data[start:start + length]).split('\n')
    lines = ['{}: {}'.format(prefix, text[0])]
    if len(text) > 1:
        indent = ' ' * len(prefix)
        for line in text[1:]:
            lines.append('{}  {}'.format(indent, line))
    return lines

def _get_block_info(data, i, block_num):
    # http://www.worldofspectrum.org/TZXformat.html
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
        info.append('Pulses: {}'.format(data[i]))
        i += 2 * data[i] + 1
    elif block_id == 20:
        header = 'Pure data'
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
        i += data[i] * 3 + 1
    elif block_id == 53:
        header = 'Custom info'
        i += get_dword(data, i + 16) + 20
    elif block_id == 90:
        header = '"Glue" block'
        i += 9
    else:
        raise SkoolKitError('Unknown block ID: 0x{:02X}'.format(block_id))
    return i, block_id, header, info, tape_data

def _print_info(text):
    print('  ' + text)

def _print_block(index, data, info=(), block_id=None, header=None):
    if block_id is None:
        print("{}:".format(index))
    else:
        print("{}: {} (0x{:02X})".format(index, header, block_id))
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
        if len(data) > 14:
            data_summary = "{} ... {}".format(_bytes_to_str(data[:7]), _bytes_to_str(data[-7:]))
        else:
            data_summary = _bytes_to_str(data)
        _print_info("Data: {}".format(data_summary))
    for line in info:
        _print_info(line)

def _analyse_tzx(tzx, options):
    if tzx[:8] != bytearray((90, 88, 84, 97, 112, 101, 33, 26)):
        raise SkoolKitError("Not a TZX file")

    try:
        print('Version: {}.{}'.format(tzx[8], tzx[9]))
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
        if not block_ids or block_id in block_ids:
            _print_block(block_num, tape_data, info, block_id, header)
        block_num += 1

def _analyse_tap(tap):
    i = 0
    block_num = 1
    while i < len(tap):
        block_len = get_word(tap, i)
        _print_block(block_num, tap[i + 2:i + 2 + block_len])
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
                       help="Show TZX blocks with these IDs only; "
                            "'IDs' is a comma-separated list of hexadecimal block IDs, e.g. 10,11,2a")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit')
    namespace, unknown_args = parser.parse_known_args(args)
    if unknown_args or namespace.infile is None:
        parser.exit(2, parser.format_help())
    infile = namespace.infile
    tape_type = infile[-4:].lower()
    if tape_type not in ('.tap', '.tzx'):
        raise SkoolKitError('Unrecognised tape type')

    with open(infile, 'rb') as f:
        tape = bytearray(f.read()) # PY: 'tape = f.read()' in Python 3

    if tape_type == '.tap':
        _analyse_tap(tape)
    else:
        _analyse_tzx(tape, namespace)
