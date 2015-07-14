#!/usr/bin/env python
import sys
import argparse

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

def _get_word(data, index):
    return data[index] + 256 * data[index + 1]

def _get_word3(data, index):
    return _get_word(data, index) + 65536 * data[index + 2]

def _get_dword(data, index):
    return _get_word3(data, index) + 16777216 * data[index + 3]

def _bytes_to_str(data):
    return ', '.join(str(b) for b in data)

def _get_str(data):
    return ''.join(chr(b) for b in data)

def _get_block_info(data, i):
    # http://www.worldofspectrum.org/TZXformat.html
    block_id = data[i]
    info = []
    tape_data = []
    i += 1
    if block_id == 16:
        header = 'Standard speed data'
        length = _get_word(data, i + 2)
        tape_data = data[i + 4:i + 4 + length]
        i += 4 + length
    elif block_id == 17:
        header = 'Turbo speed data'
        length = _get_word3(data, i + 15)
        tape_data = data[i + 18:i + 18 + length]
        i += 18 + length
    elif block_id == 18:
        header = 'Pure tone'
        info.append('Pulse length: {} T-states'.format(_get_word(data, i)))
        info.append('Pulses: {}'.format(_get_word(data, i + 2)))
        i += 4
    elif block_id == 19:
        header = 'Pulse sequence'
        info.append('Pulses: {}'.format(data[i]))
        i += 2 * data[i] + 1
    elif block_id == 20:
        header = 'Pure data'
        length = _get_word3(data, i + 7)
        tape_data = data[i + 10:i + 10 + length]
        i += length + 10
    elif block_id == 21:
        header = 'Direct recording'
        i += _get_word3(data, i + 5) + 8
    elif block_id == 24:
        header = 'CSW recording'
        i += _get_dword(data, i) + 4
    elif block_id == 25:
        header = 'Generalized data'
        i += _get_dword(data, i) + 4
    elif block_id == 32:
        header = "Pause (silence) or 'Stop the tape' command"
        i += 2
    elif block_id == 33:
        header = 'Group start'
        length = data[i]
        name = ''.join([chr(b) for b in data[i + 1:i + 1 + length]])
        info.append("Name: {}".format(name.rstrip()))
        i += length + 1
    elif block_id == 34:
        header = 'Group end'
    elif block_id == 35:
        header = 'Jump to block'
        i += 2
    elif block_id == 36:
        header = 'Loop start'
        i += 2
    elif block_id == 37:
        header = 'Loop end'
    elif block_id == 38:
        header = 'Call sequence'
        i += _get_word(data, i) * 2 + 2
    elif block_id == 39:
        header = 'Return from sequence'
    elif block_id == 40:
        header = 'Select block'
        i += _get_word(data, i) + 2
    elif block_id == 42:
        header = 'Stop the tape if in 48K mode'
        i += 4
    elif block_id == 43:
        header = 'Set signal level'
        i += 5
    elif block_id == 48:
        header = 'Text description'
        i += data[i] + 1
    elif block_id == 49:
        header = 'Message'
        i += data[i + 1] + 2
    elif block_id == 50:
        header = 'Archive info'
        num_strings = data[i + 2]
        j = i + 3
        for k in range(num_strings):
            str_len = data[j + 1]
            info.append("{}: {}".format(ARCHIVE_INFO.get(data[j], data[j]), _get_str(data[j + 2:j + 2 + str_len])))
            j += 2 + str_len
        i += _get_word(data, i) + 2
    elif block_id == 51:
        header = 'Hardware type'
        i += data[i] * 3 + 1
    elif block_id == 53:
        header = 'Custom info'
        i += _get_dword(data, i + 16) + 20
    elif block_id == 90:
        header = '"Glue" block'
        i += 9
    else:
        sys.stderr.write('Unknown block ID {} at index {}\n'.format(block_id, i - 1))
        sys.exit(1)
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
        name = ""
        if data[0] == 0:
            data_type = "Header block"
            name = _get_str(data[2:12])
        elif data[0] == 255:
            data_type = "Data block"
        _print_info("Type: {}".format(data_type))
        if name:
            _print_info("Name: {}".format(name))
    if data:
        _print_info("Length: {}".format(len(data)))
        if len(data) > 14:
            data_summary = "{} ... {}".format(_bytes_to_str(data[:7]), _bytes_to_str(data[-7:]))
        else:
            data_summary = _bytes_to_str(tape_data)
        _print_info("Data: {}".format(data_summary))
    for line in info:
        _print_info(line)

def _analyse_tzx(tzx):
    signature = _get_str(tzx[:7])
    if signature != 'ZXTape!':
        sys.stderr.write("Error: not a TZX file\n")
        sys.exit(1)

    print('Version: {}.{}'.format(tzx[8], tzx[9]))
    block_num = 1
    i = 10
    while i < len(tzx):
        i, block_id, header, info, tape_data = _get_block_info(tzx, i)
        _print_block(block_num, tape_data, info, block_id, header)
        block_num += 1

def _analyse_tap(tap):
    i = 0
    block_num = 1
    indent = '   '
    while i < len(tap):
        block_len = _get_word(tap, i)
        _print_block(block_num, tap[i + 2:i + 2 + block_len])
        i += block_len + 2
        block_num += 1

def main(args):
    parser = argparse.ArgumentParser(
        usage="tapinfo.py file",
        description="Show the blocks in a TAP or TZX file.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    namespace, unknown_args = parser.parse_known_args(args)
    if unknown_args or namespace.infile is None:
        parser.exit(2, parser.format_help())
    infile = namespace.infile
    tape_type = infile[-4:].lower()
    if tape_type not in ('.tap', '.tzx'):
        sys.stderr.write('Error: unrecognized tape type\n')
        sys.exit(1)

    with open(infile, 'rb') as f:
        tape = bytearray(f.read())

    if tape_type == '.tap':
        _analyse_tap(tape)
    else:
        _analyse_tzx(tape)

main(sys.argv[1:])
