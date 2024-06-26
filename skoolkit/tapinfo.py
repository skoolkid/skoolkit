# Copyright 2013, 2015, 2017, 2020, 2022-2024
# Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import SkoolKitError, get_word, get_int_param, warn, VERSION
from skoolkit.basic import BasicLister, TextReader
from skoolkit.tape import hex_dump, parse_pzx, parse_tap, parse_tzx

def _bytes_to_str(data):
    return ', '.join(str(b) for b in data)

def _print_info(text):
    print('  ' + text)

def _print_block(index, data, show_data, text_reader, info, block_id, header, standard):
    if block_id is None:
        print(f'{index}:')
    elif isinstance(block_id, int):
        print(f'{index}: {header} (0x{block_id:02X})')
    else:
        print(f'{index}: {header}')
    for line in info:
        _print_info(line)
    if data and standard:
        data_type = "Unknown"
        name_str = None
        line = 0xC000
        start = None
        if len(data) == 19 and data[0] == 0:
            block_type = data[1]
            if block_type == 0:
                name_str = 'Program'
                line = get_word(data, 14)
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
                text_reader.lspace = False
                name = text_reader.get_text(data[2:12])
        elif data[0] == 255:
            data_type = "Data block"
        _print_info("Type: {}".format(data_type))
        if name_str:
            _print_info("{}: {}".format(name_str, name))
        if line < 0x8000:
            _print_info(f'LINE: {line}')
        if start is not None:
            _print_info("CODE: {},{}".format(start, size))
    if data:
        _print_info("Length: {}".format(len(data)))
        if show_data:
            for line in hex_dump(data):
                _print_info(line)
        else:
            if len(data) > 14:
                data_summary = "{} ... {}".format(_bytes_to_str(data[:7]), _bytes_to_str(data[-7:]))
            else:
                data_summary = _bytes_to_str(data)
            _print_info("Data: {}".format(data_summary))
    elif data is not None:
        _print_info('Length: 0')

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

def _analyse_tape(tape, basic_block, text_reader, show_data):
    if not basic_block and tape.version:
        print(f'Version: {tape.version}')
    for block in tape.blocks:
        if basic_block:
            _list_basic(block.number, block.data, *basic_block)
        else:
            _print_block(block.number, block.data, show_data, text_reader, block.info, block.block_id, block.name, block.standard)
    for msg in tape.warnings:
        warn(msg)

def main(args):
    parser = argparse.ArgumentParser(
        usage="tapinfo.py FILE",
        description="Show the blocks in a PZX, TAP or TZX file.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-b', '--basic', metavar='N[,A]',
                       help='List the BASIC program in block N loaded at address A (default 23755).')
    group.add_argument('-d', '--data', action='store_true',
                       help='Show the entire contents of header and data blocks.')
    group.add_argument('--tape-start', metavar='BLOCK', type=int, default=1,
                       help="Start at this tape block number.")
    group.add_argument('--tape-stop', metavar='BLOCK', type=int, default=0,
                       help="Stop at this tape block number.")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    namespace, unknown_args = parser.parse_known_args(args)
    if unknown_args or namespace.infile is None:
        parser.exit(2, parser.format_help())
    basic_block = _get_basic_block(namespace.basic)
    text_reader = TextReader()
    tape_type = namespace.infile.lower()[-4:]
    if tape_type == '.pzx':
        tape = parse_pzx(namespace.infile, namespace.tape_start, namespace.tape_stop)
    elif tape_type == '.tap':
        tape = parse_tap(namespace.infile, namespace.tape_start, namespace.tape_stop)
    elif tape_type == '.tzx':
        tape = parse_tzx(namespace.infile, namespace.tape_start, namespace.tape_stop)
    else:
        raise SkoolKitError('Unrecognised tape type')
    _analyse_tape(tape, basic_block, text_reader, namespace.data)
