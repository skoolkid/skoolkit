# -*- coding: utf-8 -*-

# Copyright 2010-2013, 2015 Richard Dymond (rjdymond@gmail.com)
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

import os.path
import argparse

from skoolkit import read_bin_file, VERSION
from skoolkit.snapshot import get_snapshot

def _get_str(chars):
    return [ord(c) for c in chars]

def _get_word(word):
    return (word % 256, word // 256)

def _make_tap_block(data, header=False):
    if header:
        flag = 0
    else:
        flag = 255
    block = [0, 0, flag]
    block.extend(data)
    parity = 0
    for b in block:
        parity ^= b
    block.append(parity)
    block[:2] = _get_word(len(block) - 2)
    return block

def _get_header(title, length, start=None, line=None):
    data = _get_str(title[:10].ljust(10))   # Title padded with spaces
    data.extend(_get_word(length))          # Length of data block
    if line is None:
        data.insert(0, 3)                   # CODE block follows
        data.extend(_get_word(start))       # Start address
        data.extend((0, 0))                 # Unused
    else:
        data.insert(0, 0)                   # BASIC program follows
        data.extend(_get_word(line))        # RUN this line after LOADing
        data.extend(_get_word(length))      # Length of BASIC program only
    return _make_tap_block(data, True)

def _get_basic_loader(title, clear, start):
    data = [0, 10]                          # Line 10
    if clear is None:
        start_addr = '"23296"'
        data.extend((16, 0))                # Length of line 10
    else:
        clear_addr = '"{}"'.format(clear)
        start_addr = '"{}"'.format(start)
        line_length = 12 + len(clear_addr) + len(start_addr)
        data.extend(_get_word(line_length)) # Length of line 10
        data.extend((253, 176))             # CLEAR VAL
        data.extend(_get_str(clear_addr))   # "address"
        data.append(58)                     # :
    data.extend((239, 34, 34, 175))         # LOAD ""CODE
    data.append(58)                         # :
    data.extend((249, 192, 176))            # RANDOMIZE USR VAL
    data.extend(_get_str(start_addr))       # "address"
    data.append(13)                         # ENTER

    return _get_header(title, len(data), line=10) + _make_tap_block(data)

def _get_data_loader(title, org, length, start, stack):
    data = [221, 33]                            # LD IX,ORG
    data.extend(_get_word(org))
    data.append(17)                             # LD DE,LENGTH
    data.extend(_get_word(length))
    data.append(55)                             # SCF
    data.append(159)                            # SBC A,A
    data.append(49)                             # LD SP,STACK
    data.extend(_get_word(stack))
    data.append(1)                              # LD BC,START
    data.extend(_get_word(start))
    data.append(197)                            # PUSH BC
    data.extend((195, 86, 5))                   # JP 1366

    return _get_header(title, len(data), 23296) + _make_tap_block(data)

def run(ram, clear, org, start, stack, binfile, tapfile):
    title = os.path.basename(binfile)
    if title.lower().endswith(('.bin', '.sna', '.szx', '.z80')):
        title = title[:-4]
    tap_data = _get_basic_loader(title, clear, start)

    length = len(ram)
    if clear is None:
        stack_contents = _get_word(1343) + _get_word(start)
        stack_size = len(stack_contents)
        index = stack - org - stack_size
        if -stack_size < index < length:
            # If the main data block overwrites the stack, make sure that
            # SA/LD-RET (1343) and the start address are ready to be popped off
            # the stack when loading has finished
            for byte in stack_contents:
                if 0 <= index < length:
                    ram[index] = byte
                    index += 1
        tap_data.extend(_get_data_loader(title, org, length, start, stack))
    else:
        tap_data.extend(_get_header(title, length, org))
    tap_data.extend(_make_tap_block(ram))

    with open(tapfile, 'wb') as f:
        f.write(bytearray(tap_data))

def main(args):
    parser = argparse.ArgumentParser(
        usage='bin2tap.py [options] FILE',
        description="Convert a binary (raw memory) file or a SNA, SZX or Z80 snapshot into a TAP file.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-c', '--clear', dest='clear', metavar='N', type=int,
                       help="Use a 'CLEAR N' command in the BASIC loader and leave the stack pointer alone")
    group.add_argument('-e', '--end', dest='end', metavar='ADDR', type=int, default=65536,
                       help="Set the end address when reading a snapshot")
    group.add_argument('-o', '--org', dest='org', metavar='ORG', type=int,
                       help="Set the origin address (default: 16384 for a snapshot, otherwise 65536 minus the length of FILE)")
    group.add_argument('-p', '--stack', dest='stack', metavar='STACK', type=int,
                       help="Set the stack pointer (default: ORG)")
    group.add_argument('-s', '--start', dest='start', metavar='START', type=int,
                       help="Set the start address to JP to (default: ORG)")
    group.add_argument('-t', '--tapfile', dest='tapfile', metavar='TAPFILE',
                       help="Set the TAP filename")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit')

    namespace, unknown_args = parser.parse_known_args(args)
    infile = namespace.infile
    if unknown_args or infile is None:
        parser.exit(2, parser.format_help())
    if infile.lower().endswith(('.sna', '.szx', '.z80')):
        org = namespace.org or 16384
        ram = get_snapshot(infile)[org:namespace.end]
    else:
        ram = read_bin_file(infile)
        org = namespace.org or 65536 - len(ram)
    clear = namespace.clear
    start = namespace.start or org
    stack = namespace.stack or org
    tapfile = namespace.tapfile
    if tapfile is None:
        if infile.lower().endswith(('.bin', '.sna', '.szx', '.z80')):
            prefix = infile[:-4]
        else:
            prefix = infile
        tapfile = prefix + ".tap"
    run(ram, clear, org, start, stack, infile, tapfile)
