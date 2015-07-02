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

def get_word(data, index):
    return data[index] + 256 * data[index + 1]

def get_word3(data, index):
    return get_word(data, index) + 65536 * data[index + 2]

def get_dword(data, index):
    return get_word3(data, index) + 16777216 * data[index + 3]

def bytes_to_str(data):
    return ', '.join(str(b) for b in data)

def get_str(data):
    return ''.join(chr(b) for b in data)

def get_block_info(data, i):
    # http://www.worldofspectrum.org/TZXformat.html
    block_id = data[i]
    info = []
    tape_data = []
    i += 1
    if block_id == 16:
        header = 'Standard speed data'
        length = get_word(data, i + 2)
        tape_data = data[i + 4:i + 4 + length]
        data_type = "Unknown"
        name = ""
        if tape_data[0] == 0:
            data_type = "Header block"
            name = get_str(tape_data[2:12])
        elif tape_data[0] == 255:
            data_type = "Data block"
        info.append("Type: {}".format(data_type))
        if name:
            info.append("Name: {}".format(name))
        info.append("Length: {}".format(length))
        i += 4 + length
    elif block_id == 17:
        header = 'Turbo speed data'
        length = get_word3(data, i + 15)
        tape_data = data[i + 18:i + 18 + length]
        info.append("Length: {}".format(length))
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
        info.append("Length: {}".format(length))
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
        i += get_word(data, i) * 2 + 2
    elif block_id == 39:
        header = 'Return from sequence'
    elif block_id == 40:
        header = 'Select block'
        i += get_word(data, i) + 2
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
            info.append("{}: {}".format(ARCHIVE_INFO.get(data[j], data[j]), get_str(data[j + 2:j + 2 + str_len])))
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
        sys.stderr.write('Unknown block ID {} at index {}\n'.format(block_id, i - 1))
        sys.exit(1)
    if tape_data:
        if len(tape_data) > 14:
            tape_data_summary = "{} ... {}".format(bytes_to_str(tape_data[:7]), bytes_to_str(tape_data[-7:]))
        else:
            tape_data_summary = bytes_to_str(tape_data)
        info.append("Data: {}".format(tape_data_summary))
    return i, block_id, header, info

def analyse_tzx(tzx):
    signature = get_str(tzx[:7])
    if signature != 'ZXTape!':
        sys.stderr.write("Error: not a TZX file\n")
        sys.exit(1)

    print('Version: {}.{}'.format(tzx[8], tzx[9]))
    block_num = 1
    i = 10
    while i < len(tzx):
        i, block_id, header, info = get_block_info(tzx, i)
        print("{}: {} (0x{:02X})".format(block_num, header, block_id))
        for line in info:
            print('  ' + line)
        block_num += 1

def analyse_tap(tap):
    i = 0
    block_num = 1
    indent = '   '
    while i < len(tap):
        block_len = tap[i] + 256 * tap[i + 1]
        marker = tap[i + 2]
        header = marker == 0
        print("{:02} {} ({})".format(block_num, 'Header' if header else 'Data', i))
        print("{}Block length: {}".format(indent, block_len))
        print("{}Marker byte: {}".format(indent, marker))
        if header:
            block_type = tap[i + 3]
            title = ''.join(chr(b) for b in tap[i + 4:i + 14])
            if block_type == 3:
                # Bytes
                print("{}Bytes: {}".format(indent, title))
                start = tap[i + 16] + 256 * tap[i + 17]
                print("{}Start: {}".format(indent, start))
            elif block_type == 0:
                # Program
                print("{}Program: {}".format(indent, title))
                line = tap[i + 16] + 256 * tap[i + 17]
                print("{}LINE: {}".format(indent, line))
            else:
                print('ERROR: Unknown block type ({}) in header at {}'.format(block_type, i))
                sys.exit(1)
            length = tap[i + 14] + 256 * tap[i + 15]
            print("{}Length: {}".format(indent, length))
        print("{}Parity byte: {}".format(indent, tap[i + block_len + 1]))
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
        analyse_tap(tape)
    else:
        analyse_tzx(tape)

main(sys.argv[1:])
