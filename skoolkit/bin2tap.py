# Copyright 2010-2013, 2015-2017, 2019-2020, 2023, 2024
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

import os.path
import argparse

from skoolkit import SkoolKitError, integer, parse_int, read_bin_file, VERSION
from skoolkit.components import get_snapshot_reader
from skoolkit.tape import write_pzx, write_tap

def _get_str(chars):
    return [ord(c) for c in chars]

def _get_word(word):
    return (word % 256, word // 256)

def _make_block(data, header=False):
    if header:
        flag = 0
    else:
        flag = 255
    block = [flag]
    block.extend(data)
    parity = 0
    for b in block:
        parity ^= b
    block.append(parity)
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
    return _make_block(data, True)

def _get_basic_loader(title, clear, start, scr, banks=None):
    data = [0, 10]                          # Line 10
    if clear is None:
        start_addr = '"23296"'
        data.extend((16, 0))                # Length of line 10
    else:
        clear_addr = '"{}"'.format(clear)
        start_addr = '"{}"'.format(start)
        line_length = 12 + len(clear_addr) + len(start_addr)
        if scr:
            line_length += 20
        if banks is not None:
            line_length += 5
        data.extend(_get_word(line_length)) # Length of line 10
        data.extend((253, 176))             # CLEAR VAL
        data.extend(_get_str(clear_addr))   # "address"
        data.append(58)                     # :
        if scr:
            poke_addr = _get_str('"23739"')
            data.extend((239, 34, 34, 170)) # LOAD ""SCREEN$
            data.append(58)                 # :
            data.extend((244, 176))         # POKE VAL
            data.extend(poke_addr)          # "23739"
            data.append(44)                 # ,
            data.extend((175, 34, 111, 34)) # CODE "o"
            data.append(58)                 # :
        if banks is not None:
            data.extend((239, 34, 34, 175)) # LOAD ""CODE
            data.append(58)                 # :
    data.extend((239, 34, 34, 175))         # LOAD ""CODE
    data.append(58)                         # :
    data.extend((249, 192, 176))            # RANDOMIZE USR VAL
    data.extend(_get_str(start_addr))       # "address"
    data.append(13)                         # ENTER

    return [_get_header(title, len(data), line=10), _make_block(data)]

def _get_data_loader(title, org, length, start, stack, scr):
    if scr:
        data = list(scr)
        data.extend((0,) * (6912 - len(data)))
    else:
        data = []
    address = 23296 - len(data)
    data.extend((221, 33))                  # LD IX,ORG
    data.extend(_get_word(org))
    data.append(17)                         # LD DE,LENGTH
    data.extend(_get_word(length))
    data.append(55)                         # SCF
    data.append(159)                        # SBC A,A
    data.append(49)                         # LD SP,STACK
    data.extend(_get_word(stack))
    data.append(1)                          # LD BC,START
    data.extend(_get_word(start))
    data.append(197)                        # PUSH BC
    data.extend((195, 86, 5))               # JP 1366

    return (_get_header(title, len(data), address), _make_block(data))

def _get_bank_loader(title, address, start_addr, banks, out7ffd):
    table_addr = address + 38
    table = (table_addr % 256, table_addr // 256)
    start = (start_addr % 256, start_addr // 256)
    data = [
        0x21, *table,           #      LD HL,TABLE
        0x01, 0xFD, 0x7F,       # LOOP LD BC,$7FFD
        0x7E,                   #      LD A,(HL)
        0xE6, 0x3F,             #      AND $3F
        0xF3,                   #      DI
        0xED, 0x79,             #      OUT (C),A
        0x32, 0x5C, 0x5B,       #      LD ($5B5C),A
        0xFB,                   #      EI
        0xCB, 0x7E,             #      BIT 7,(HL)
        0xC2, *start,           #      JP NZ,START
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
    data.extend(b + 0x10 for b in sorted(banks))
    data.append(0x80 | out7ffd) # End marker
    return (_get_header(title, len(data), address), _make_block(data))

def run(ram, clear, org, start, stack, tape_file, scr, banks, out7ffd, loader_addr):
    title = os.path.basename(tape_file)
    if title.lower().endswith(('.tap', '.pzx')):
        title = title[:-4]
    if banks is None:
        blocks = _get_basic_loader(title, clear, start, scr)
    else:
        blocks = _get_basic_loader(title, clear, loader_addr, scr, banks)

    length = len(ram)
    if clear is None:
        stack_contents = _get_word(1343) + _get_word(start)
        stack_size = len(stack_contents)
        index = stack - org - stack_size
        if -stack_size < index < length:
            # If the main data block overwrites the stack, make sure that
            # SA/LD-RET (1343) and the start address are ready to be popped off
            # the stack when loading has finished
            ram = list(ram)
            for byte in stack_contents:
                if 0 <= index < length:
                    ram[index] = byte
                    index += 1
        blocks.extend(_get_data_loader(title, org, length, start, stack, scr))
    else:
        if scr:
            blocks.append(_get_header(title, 6912, 16384))
            blocks.append(_make_block(scr))
        blocks.append(_get_header(title, length, org))
    blocks.append(_make_block(ram))

    if banks is not None:
        blocks.extend(_get_bank_loader(title, loader_addr, start, banks, out7ffd))
        for b in sorted(banks):
            blocks.append(_make_block(banks[b]))

    if tape_file.lower().endswith('.pzx'):
        write_pzx(tape_file, blocks)
    else:
        write_tap(tape_file, blocks)

def main(args):
    parser = argparse.ArgumentParser(
        usage='bin2tap.py [options] FILE [OUTFILE]',
        description="Convert a binary (raw memory) file or a SNA, SZX or Z80 snapshot into a PZX or TAP file. "
                    "FILE may be a regular file, or '-' to read a binary file from standard input. "
                    "If OUTFILE is not given, a TAP file is created.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('outfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('--7ffd', metavar='N', dest='out7ffd', type=integer,
                       help="Add 128K RAM banks to the tape file and write N to port 0x7ffd after they've loaded.")
    group.add_argument('--banks', metavar='N[,N...]',
                       help="Add only these 128K RAM banks to the tape file (default: 0,1,3,4,6,7).")
    group.add_argument('-b', '--begin', dest='begin', metavar='BEGIN', type=integer,
                       help="Begin conversion at this address (default: ORG for a binary file, 16384 for a snapshot).")
    group.add_argument('-c', '--clear', dest='clear', metavar='N', type=integer,
                       help="Use a 'CLEAR N' command in the BASIC loader and leave the stack pointer alone.")
    group.add_argument('-e', '--end', dest='end', metavar='END', type=integer,
                       help="End conversion at this address.")
    group.add_argument('--loader', metavar='ADDR', type=integer,
                       help="Place the 128K RAM bank loader at this address (default: CLEAR address + 1).")
    group.add_argument('-o', '--org', dest='org', metavar='ORG', type=integer,
                       help="Set the origin address for a binary file (default: 65536 minus the length of FILE).")
    group.add_argument('-p', '--stack', dest='stack', metavar='STACK', type=integer,
                       help="Set the stack pointer (default: BEGIN).")
    group.add_argument('-s', '--start', dest='start', metavar='START', type=integer,
                       help="Set the start address to JP to (default: BEGIN).")
    group.add_argument('-S', '--screen', dest='screen', metavar='FILE',
                       help="Add a loading screen to the tape file. FILE may be a snapshot or a 6912-byte SCR file.")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')

    namespace, unknown_args = parser.parse_known_args(args)
    infile = namespace.infile
    if unknown_args or infile is None:
        parser.exit(2, parser.format_help())
    snapshot_reader = get_snapshot_reader()
    banks = None
    clear = namespace.clear
    out7ffd = namespace.out7ffd
    loader_addr = namespace.loader
    if loader_addr is None and clear is not None:
        loader_addr = clear + 1
    has_128k_options = out7ffd is not None and clear is not None and namespace.begin is not None
    if snapshot_reader.can_read(infile):
        org = 0
        begin = namespace.begin or 16384
        if has_128k_options:
            snapshot = snapshot_reader.get_snapshot(infile, -1)
            if len(snapshot) == 0x20000:
                banks = {b: snapshot[b * 0x4000:(b + 1) * 0x4000] for b in (0, 1, 3, 4, 6, 7)}
                end = namespace.end or 49152
        else:
            end = namespace.end or 65536
        ram = snapshot_reader.get_snapshot(infile)[begin:end]
    else:
        snapshot = read_bin_file(infile, 0x20000)
        if len(snapshot) == 0x20000 and has_128k_options:
            banks = {b: snapshot[b * 0x4000:(b + 1) * 0x4000] for b in range(8)}
            ram = list(banks.pop(5) + banks.pop(2)) + [0] * 16384
            org = 16384
            end = namespace.end or 49152
        elif snapshot:
            ram = snapshot[:49152]
            org = namespace.org or 65536 - len(ram)
            end = namespace.end or org + len(ram)
        else:
            raise SkoolKitError(f'{infile} is empty')
        begin = namespace.begin or org
        ram = ram[begin - org:end - org]
    if not ram:
        raise SkoolKitError('Input is empty (ORG={}, BEGIN={}, END={})'.format(org, begin, end))
    if banks and namespace.banks:
        for b in set(banks) - set(parse_int(b) for b in namespace.banks.split(',')):
            del banks[b]
    start = namespace.start or begin
    stack = namespace.stack or begin
    tape_file = namespace.outfile
    if tape_file is None:
        if infile.lower().endswith(('.bin', '.sna', '.szx', '.z80')):
            prefix = os.path.basename(infile)[:-4]
        elif infile == '-':
            prefix = 'program'
        else:
            prefix = os.path.basename(infile)
        tape_file = prefix + ".tap"
    scr = namespace.screen
    if scr is not None:
        if snapshot_reader.can_read(scr):
            scr = snapshot_reader.get_snapshot(scr)[16384:23296]
        else:
            scr = read_bin_file(scr, 6912)
    run(ram, clear, begin, start, stack, tape_file, scr, banks, out7ffd, loader_addr)
